"""
Analysis routes for Pepperyn.
POST /api/analyze      — Analyze an uploaded financial file
POST /api/analyze/text — Text question (no file)
"""
import asyncio
import hashlib
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError

from models.schemas import AnalyzeResponse, TextQueryRequest, TextQueryResponse, DataQualityInfo
from connectors import FileConnector
from services.llm_service import run_full_pipeline, get_anthropic_client, call_chat_intelligent
from services.excel_export import generate_excel_report
# WP5C Commit 6 — compute_decision_fingerprint / FINGERPRINT_VERSION retirés de analyze.py.
# Le fingerprint est désormais calculé dans l'extracteur (Phase 9, KERNEL-INV-013)
# et lu depuis decision_kernel.decision_fingerprint. Aucun calcul dans ce fichier.
from services.decision_kernel_extractor import extract_decision_kernel  # WP5C
from services.usage_service import UsageService
from services.data_quality_gate import validate_excel_before_analysis
from services.anonymization_service import (
    CorrespondenceTable,
    anonymize_parsed_data,
    anonymize_text,
    deanonymize_recursive,
)
from security_config import get_jwt_guest_secret
try:
    from services.memory_service import MemoryService
    _memory_service = MemoryService()
except ImportError:
    _memory_service = None

try:
    from services.decision_memory_service import DecisionMemoryService, extract_recommendations
    _decision_memory_service = DecisionMemoryService()
except ImportError:
    _decision_memory_service = None
    extract_recommendations = None

_usage_service = UsageService()

router = APIRouter(prefix="/api", tags=["analyze"])

JWT_ALGORITHM = "HS256"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf'}

# In-memory export caches  (replace with object storage in production)
_export_cache: dict[str, bytes] = {}          # analyse_id → excel bytes
_pdf_cache:    dict[str, bytes] = {}          # analyse_id → pdf bytes
_pptx_cache:   dict[str, bytes] = {}          # analyse_id → pptx bytes
_export_format_chosen: dict[str, str] = {}    # analyse_id → "excel"|"pdf"|"pptx"
_analysis_result_cache: dict[str, dict] = {}  # analyse_id → result dict (pour PDF/PPTX à la demande)
_anonymization_cache: dict[str, CorrespondenceTable] = {}  # analyse_id → table de correspondance (jamais envoyée à l'IA)
_analysis_owner: dict[str, str] = {}          # analyse_id → company_id (contrôle d'accès aux exports)
_analysis_params_cache: dict[str, dict] = {}  # analyse_id → {target_date, analysis_period_months}

# ── V2 : Executive Case JSON cache ───────────────────────────────────────────
# Source unique de vérité pour PDF, PPTX et Excel.
# Produit lazily par l'Executive Case Builder (Agent 1 — Claude Opus)
# lors du premier export. Réutilisé pour tous les exports suivants.
from models.executive_case import ExecutiveCaseJSON as _ExecutiveCaseJSON
_executive_case_cache: dict[str, _ExecutiveCaseJSON] = {}  # analyse_id → ExecutiveCaseJSON

# ── V2 Conversation Engine cache ──────────────────────────────────────────────
# Source de vérité pour le Conversation Engine (chat).
# Produit lazily par executive_case_v2_builder (Python pur, sans LLM).
# Construit UNIQUEMENT sur demande d'un endpoint ou du chat.
# JAMAIS dans le pipeline d'analyse principal.
from models.executive_case_v2 import ExecutiveCase as _ExecutiveCase
_executive_case_v2_cache: dict[str, _ExecutiveCase] = {}  # analyse_id → ExecutiveCase V2


def _build_relation_section(entity_name: str, is_primary: bool, relation_type: Optional[str]) -> str:
    """
    Construit une courte section de contexte relationnel à injecter dans le
    prompt d'entrée (Call 1), selon que l'entité analysée est une filiale du
    groupe ou un client suivi par l'utilisateur. N'a aucun effet sur la
    structure du rapport (AnalysisResult / analyse_json) — uniquement sur le
    cadrage du diagnostic et des recommandations.
    """
    if is_primary or not relation_type:
        return ""

    name = entity_name or "Cette entité"

    if relation_type == "filiale":
        return f"""CONTEXTE RELATIONNEL
"{name}" est une FILIALE du groupe piloté par l'utilisateur (l'entité principale).
Si cette filiale présente des signes de dégradation et/ou si les recommandations
précédentes (voir mémoire décisionnelle ci-dessus) n'ont pas été suivies :
- Situe explicitement le poids de cette filiale dans le résultat global du groupe
  (ex : "représente X% du chiffre d'affaires/des pertes du groupe" si chiffrable,
  sinon "poids significatif pour le groupe").
- Formule la décision prioritaire comme une consigne que le groupe doit faire
  appliquer à cette filiale, en précisant le risque encouru par le groupe en cas
  d'inaction (ex : "si la situation persiste, le groupe risque...").
- Si la situation est saine et les recommandations suivies, ne force rien : reste
  factuel."""

    if relation_type == "client":
        return f"""CONTEXTE RELATIONNEL
"{name}" est un CLIENT suivi par l'utilisateur (expert-comptable / fractional CFO
/ consultant). Si ce client présente des signes de dégradation et/ou si les
recommandations précédentes (voir mémoire décisionnelle ci-dessus) n'ont pas été
suivies :
- Aide l'utilisateur à évaluer la relation avec ce client : signale si ce client
  devient un poids dans son portefeuille (temps passé, recommandations ignorées,
  risque pour le client lui-même).
- Formule la décision prioritaire comme une action que l'utilisateur doit porter
  fermement auprès de ce client (ex : "à recadrer lors du prochain point" ou
  "relation à réévaluer si la situation persiste").
- Si la situation est saine et les recommandations suivies, ne force rien : reste
  factuel."""

    return ""


async def _resolve_auth(
    authorization: Optional[str],
    x_auth_type: Optional[str],
) -> tuple[str, str, str]:
    """
    Resolve authorization header to (company_id, plan, auth_type).
    Supports both guest JWT and Supabase admin JWT.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification requis")

    token = authorization.split(" ", 1)[1]

    # Try guest JWT first (our own format)
    try:
        payload = jwt.decode(token, get_jwt_guest_secret(), algorithms=[JWT_ALGORITHM])
        logger.debug("[AUTH] Guest JWT décodé (type=%s)", payload.get("type"))
        if payload.get("type") == "guest":
            return payload["company_id"], payload.get("plan", "free"), "guest"
    except JWTError:
        pass

    # Try Supabase admin JWT
    from main import get_supabase_service
    supabase = get_supabase_service()
    try:
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            user_id = user_response.user.id
            logger.debug("[AUTH] Admin authentifié")

            # Step 1: get company_id from profiles
            company_id = None
            try:
                profile_response = (
                    supabase.from_("profiles")
                    .select("company_id")
                    .eq("id", user_id)
                    .limit(1)
                    .execute()
                )
                if profile_response.data:
                    company_id = profile_response.data[0].get("company_id")
            except Exception as e:
                logger.debug("[AUTH] Profile lookup failed: %s", e)

            # Step 2: fallback — lookup company directly by admin_user_id
            if not company_id:
                try:
                    company_response = (
                        supabase.from_("companies")
                        .select("id, plan")
                        .eq("admin_user_id", user_id)
                        .limit(1)
                        .execute()
                    )
                    if company_response.data:
                        company_id = company_response.data[0]["id"]
                        plan = company_response.data[0].get("plan", "free")
                        return company_id, plan, "admin"
                except Exception as e:
                    logger.debug("[AUTH] Companies lookup failed: %s", e)

            if company_id:
                # Get plan from companies
                plan = "free"
                try:
                    plan_response = (
                        supabase.from_("companies")
                        .select("plan")
                        .eq("id", company_id)
                        .limit(1)
                        .execute()
                    )
                    if plan_response.data:
                        plan = plan_response.data[0].get("plan", "free")
                except Exception:
                    pass
                return company_id, plan, "admin"
    except Exception as e:
        logger.debug("[AUTH] Admin auth exception: %s", e)

    raise HTTPException(status_code=401, detail="Token invalide ou expiré")


@router.get("/analyses/history")
async def get_analyses_history(
    entity_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Return the last 20 completed analyses for the authenticated company, optionally filtered by entity."""
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        query = (
            supabase.from_("analyses")
            .select("id, fichier_nom, type_document, created_at, score_confiance, entity_id")
            .eq("company_id", company_id)
            .eq("status", "completed")
        )
        if entity_id:
            query = query.eq("entity_id", entity_id)
        result = (
            query
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return {"analyses": result.data or []}
    except Exception:
        return {"analyses": []}


@router.delete("/analyses/history")
async def delete_analyses_history(
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Supprime tout l'historique d'analyses de la company connectée.
    Supprime aussi les messages associés (cascade) et remet les compteurs à zéro.
    """
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()

        # Compter avant suppression pour le retour
        count_res = (
            supabase.from_("analyses")
            .select("id", count="exact")
            .eq("company_id", company_id)
            .execute()
        )
        deleted_count = count_res.count or 0

        # Supprimer les analyses (ON DELETE CASCADE supprime financial_metrics liés)
        supabase.from_("analyses").delete().eq("company_id", company_id).execute()

        # Supprimer les sessions + messages (messages cascadent avec sessions)
        supabase.from_("sessions").delete().eq("company_id", company_id).execute()

        return {"success": True, "deleted": deleted_count}
    except Exception as e:
        logger.error("[ANALYZE] Erreur suppression historique: %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'historique.")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    context: str = Form(default=""),
    mode: str = Form(default="complete"),
    session_id: Optional[str] = Form(default=None),
    entity_id: Optional[str] = Form(default=None),
    analysis_period_months: Optional[int] = Form(default=None),
    target_date: Optional[str] = Form(default=None),
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Analyze an uploaded financial file (xlsx, xls, csv, pdf)."""
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)
    start_time = time.time()

    # Check analysis quota (server-side, non-bypassable)
    allowed, reason = _usage_service.can_run_analysis(company_id, plan)
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    # Track file_uploaded event
    _usage_service.track_activity(company_id, "file_uploaded", {
        "filename": file.filename if file.filename else "unknown",
        "plan": plan,
    })

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté: .{ext}. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux ({len(file_bytes)//1024}KB). Maximum: {MAX_FILE_SIZE_MB}MB"
        )

    # ── DATA QUALITY GATE (obligatoire, avant toute analyse) ────────────────
    quality_gate = validate_excel_before_analysis(file_bytes, file.filename)
    logger.warning(
        f"[QUALITY GATE] {file.filename} → status={quality_gate.status} "
        f"score={quality_gate.score_data} format={quality_gate.document_format}"
    )

    if not quality_gate.can_analyze:
        # Fichier bloqué : retourner un message de coaching actionnable
        from models.schemas import AnalysisResult
        coaching_msg = quality_gate.build_coaching_message(file.filename)
        blocked_result = AnalysisResult(
            type_document="COACHING_QUALITE",
            score_confiance=0,
            resume_executif=coaching_msg,
            problemes_critiques=quality_gate.anomalies or [quality_gate.blocking_reason or "Structure insuffisante"],
            decision="Restructurez votre fichier en suivant le guide ou le prompt Copilot fourni, puis re-uploadez.",
            copilot_prompt=quality_gate._generate_copilot_prompt(),
            coaching_issues=quality_gate.anomalies or [],
            data_quality=DataQualityInfo(
                score_data=quality_gate.score_data,
                score_completude=quality_gate.score_completude,
                score_confiance_conclusions=quality_gate.score_confiance,
                status="blocked",
                document_format=quality_gate.document_format,
                mapping_summary=quality_gate.mapping_summary,
                anomalies=quality_gate.anomalies,
                assumptions=quality_gate.assumptions,
                sheets_detected=quality_gate.sheets_detected,
            ),
        )
        return AnalyzeResponse(
            success=False,
            message="coaching_qualite",
            result=blocked_result,
            tokens_used=0,
            cout_estime=0.0,
        )

    # ── À partir d'ici, le traitement peut prendre 1-2 minutes (2 appels
    # Claude + génération des exports). Pour éviter qu'un proxy/passerelle
    # ne coupe la connexion par inactivité avant la fin (→ "NetworkError"
    # côté client alors que le traitement a réussi côté serveur, données
    # déjà sauvegardées), on répond en flux : quelques octets "heartbeat"
    # sont envoyés pendant que l'analyse tourne, suivis du JSON final.
    # Le frontend (api.ts) tolère cet espace de tête (JSON.parse l'ignore).
    return StreamingResponse(
        _stream_analysis_response(
            file_bytes=file_bytes,
            file=file,
            context=context,
            mode=mode,
            session_id=session_id,
            entity_id=entity_id,
            company_id=company_id,
            plan=plan,
            auth_type=auth_type,
            start_time=start_time,
            ext=ext,
            quality_gate=quality_gate,
            analysis_period_months=analysis_period_months,
            target_date=target_date,
        ),
        media_type="application/json",
        # Désactive le buffering nginx (Railway) pour que les heartbeats
        # arrivent immédiatement au client et ne soient pas retenus jusqu'à
        # la fin de la réponse (évite les timeouts proxy sur analyses longues).
        headers={"X-Accel-Buffering": "no"},
    )


async def _stream_analysis_response(**kwargs):
    """
    Exécute `_run_analysis_pipeline` en tâche de fond et envoie un octet
    "heartbeat" (espace) toutes les ~8s tant qu'elle n'est pas terminée,
    afin de garder la connexion active pendant les analyses longues.

    En cas d'erreur dans le pipeline, on encode une `AnalyzeResponse`
    `success=False` plutôt que de lever une HTTPException (impossible une
    fois le flux démarré avec un statut 200).

    Note : `_run_analysis_pipeline` est `async def` mais effectue ses appels
    Claude/Supabase de façon synchrone (bloquante). Si on l'exécutait via
    `asyncio.create_task` sur la boucle principale, ces appels bloqueraient
    aussi l'envoi des heartbeats — on l'exécute donc dans un thread séparé
    (avec sa propre boucle asyncio) pour que la boucle principale reste
    libre d'envoyer les heartbeats pendant ce temps.
    """
    loop = asyncio.get_running_loop()

    def _run_sync() -> AnalyzeResponse:
        return asyncio.run(_run_analysis_pipeline(**kwargs))

    future = loop.run_in_executor(None, _run_sync)

    # Heartbeat toutes les 8 s (réduit de 15 s) pour éviter les timeouts
    # de proxies stricts (nginx Railway coupe après ~60 s sans données).
    while not future.done():
        done, _ = await asyncio.wait({future}, timeout=8)
        if not done:
            yield b" "

    try:
        result = future.result()
    except HTTPException as e:
        result = AnalyzeResponse(success=False, message=str(e.detail))
    except BaseException as e:
        # BaseException (pas seulement Exception) pour attraper CancelledError
        # et tout autre sous-type qui pourrait terminer silencieusement.
        logger.error(f"[ANALYZE STREAM] erreur pipeline: {type(e).__name__}: {e}")
        result = AnalyzeResponse(success=False, message="Erreur lors de l'analyse")

    try:
        yield result.model_dump_json().encode("utf-8")
    except BaseException as _ser_exc:
        logger.error("[ANALYZE STREAM] Erreur sérialisation finale: %s", _ser_exc)
        _fallback = AnalyzeResponse(success=False, message="Erreur interne lors de la sérialisation")
        yield _fallback.model_dump_json().encode("utf-8")


async def _run_analysis_pipeline(
    file_bytes: bytes,
    file: UploadFile,
    context: str,
    mode: str,
    session_id: Optional[str],
    entity_id: Optional[str],
    company_id: str,
    plan: str,
    auth_type: str,
    start_time: float,
    ext: str,
    quality_gate,
    analysis_period_months: Optional[int] = None,
    target_date: Optional[str] = None,
) -> AnalyzeResponse:
    # Parse file (Step 1: pre-processing, 0 tokens)
    try:
        parsed_data = FileConnector(file_bytes, file.filename).fetch()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[ANALYZE] Erreur lecture fichier: %s", e)
        raise HTTPException(status_code=500, detail="Impossible de lire le fichier.")

    # ── CONFIDENTIALITÉ : anonymisation avant tout traitement IA ─────────────
    # Les noms de clients, fournisseurs, collaborateurs, emails, IBAN, n° TVA,
    # etc. sont remplacés par des identifiants anonymes (CLIENT_001, ...)
    # avant d'être transmis aux modèles d'IA. La table de correspondance reste
    # côté serveur et sert à rétablir les noms réels dans les résultats.
    anonymized_data, correspondence_table = anonymize_parsed_data(parsed_data)

    # Retrieve user profile for context
    industry = ""
    business_model = ""
    try:
        from main import get_supabase_service as _get_supabase
        _sb = _get_supabase()
        _profile_res = _sb.from_("profiles").select("industry, business_model").eq("company_id", company_id).limit(1).execute()
        if _profile_res.data:
            industry = _profile_res.data[0].get("industry") or ""
            business_model = _profile_res.data[0].get("business_model") or ""
    except Exception:
        pass

    # Contexte relationnel de l'entité (filiale du groupe / client suivi).
    # Lecture Supabase uniquement — aucun appel Claude. N'influence que le
    # prompt d'entrée (relation_section), jamais la structure du rapport.
    relation_section = ""
    if entity_id:
        try:
            from main import get_supabase_service as _get_supabase_rel
            _sb_rel = _get_supabase_rel()
            _ent_res = (
                _sb_rel.from_("entities")
                .select("name, is_primary, relation_type")
                .eq("id", entity_id)
                .limit(1)
                .execute()
            )
            if _ent_res.data:
                _ent = _ent_res.data[0]
                relation_section = _build_relation_section(
                    entity_name=_ent.get("name") or "",
                    is_primary=bool(_ent.get("is_primary")),
                    relation_type=_ent.get("relation_type"),
                )
        except Exception:
            pass

    # Retrieve memory context
    memory_section = ""
    actions_section = ""
    memory_ctx: dict = {}
    if _memory_service:
        try:
            memory_ctx = _memory_service.get_memory_context(company_id)
            memory_section = _memory_service.build_memory_prompt_section(memory_ctx)
        except Exception:
            pass

    # Retrieve decision memory context (mémoire décisionnelle — feedback utilisateur)
    if _decision_memory_service:
        try:
            actions_section = _decision_memory_service.build_decision_memory_prompt_section(company_id)
        except Exception:
            pass

    # Inject data quality context into LLM prompt
    quality_section = quality_gate.to_prompt_section()

    # Si warning : préparer la note de coaching à afficher au-dessus de l'analyse
    quality_coaching_preamble = None
    if quality_gate.status == "warning":
        quality_coaching_preamble = quality_gate.build_warning_note(file.filename)

    # Track analysis_started event
    _usage_service.track_activity(company_id, "analysis_started", {
        "filename": file.filename,
        "mode": mode,
        "plan": plan,
    })

    # Run LLM pipeline v3 (2 calls Claude) — sur données anonymisées
    try:
        analysis_result, total_tokens, cost = await run_full_pipeline(
            anonymized_data, context,
            industry=industry,
            business_model=business_model,
            memory_section=memory_section,
            actions_section=actions_section,
            quality_section=quality_section,
            relation_section=relation_section,
            plan_tier=plan,
        )
    except ValueError as e:
        logger.error("[ANALYZE] Erreur pipeline IA (ValueError): %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'analyse.")
    except Exception as e:
        logger.error("[ANALYZE] Erreur analyse IA: %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'analyse.")

    # ── CONFIDENTIALITÉ : ré-identification ──────────────────────────────────
    # Les alias (CLIENT_001, FOURNISSEUR_001, ...) renvoyés par l'IA sont
    # remplacés par les noms réels avant d'être présentés à l'utilisateur.
    if not correspondence_table.is_empty:
        analysis_result.__dict__.update(
            deanonymize_recursive(dict(analysis_result.__dict__), correspondence_table)
        )

    # Build memory insight (if previous analyses exist)
    memory_insight: Optional[str] = None
    if _memory_service and memory_ctx:
        try:
            memory_insight = _memory_service.build_memory_insight(
                analysis_result.model_dump(), memory_ctx
            )
            if memory_insight:
                analysis_result.memory_insight = memory_insight
        except Exception:
            pass

    # A2 fix — aligner plan_action_haute ET plan_action avec les décisions EDM
    # Racine du bug C1/C2 : le frontend lit result.plan_action (= haute + secondaire),
    # pas plan_action_haute. On met à jour les DEUX champs pour cohérence chat ↔ docs.
    try:
        import re as _re
        from services.executive_decision_model import build_executive_decision_model as _build_edm
        _edm_tmp = _build_edm(analysis_result.model_dump())
        if _edm_tmp.executive_decisions:
            _edm_decisions = [
                _re.sub(r'\*+', '', d.decision or '').strip()
                for d in _edm_tmp.executive_decisions
            ]
            analysis_result.plan_action_haute = _edm_decisions
            # C1/C2 fix : le frontend affiche plan_action (haute + secondaire),
            # non plan_action_haute seul — synchroniser les deux.
            analysis_result.plan_action = _edm_decisions
    except Exception:
        pass  # non-bloquant — le plan d'action LLM original reste en fallback

    # Attach data quality info to result (RÈGLE N°9 : 3 scores distincts)
    analysis_result.data_quality = DataQualityInfo(
        score_data=quality_gate.score_data,
        score_completude=quality_gate.score_completude,
        score_confiance_conclusions=quality_gate.score_confiance,
        status=quality_gate.status,
        document_format=quality_gate.document_format,
        mapping_summary=quality_gate.mapping_summary,
        anomalies=quality_gate.anomalies,
        assumptions=quality_gate.assumptions,
        sheets_detected=quality_gate.sheets_detected,
    )
    # RÈGLE N°9 — quality_gate.score_confiance est un PLAFOND dur sur la confiance.
    # Si le LLM a déjà parsé un score depuis "# FIABILITÉ ANALYSE" (< 70 par défaut),
    # on conserve le minimum entre les deux pour éviter toute sur-confiance.
    analysis_result.score_confiance = min(
        analysis_result.score_confiance,
        quality_gate.score_confiance,
    )

    # Pour les fichiers en warning : attacher la note coaching + prompt Copilot
    if quality_coaching_preamble and quality_gate.status == "warning":
        analysis_result.copilot_prompt = quality_gate._generate_copilot_prompt()
        analysis_result.coaching_issues = quality_gate.anomalies or []

    # Assign the analyse_id to the result object so the frontend can use it
    analyse_id = str(uuid.uuid4())
    analysis_result.id = analyse_id

    # Contrôle d'accès : mémoriser à quelle company appartient cette analyse,
    # pour que seuls ses membres puissent télécharger les exports (anti-IDOR).
    _analysis_owner[analyse_id] = company_id

    # Mémoriser les paramètres de période/objectif pour la génération des exports.
    _analysis_params_cache[analyse_id] = {
        "target_date": target_date or "",
        "analysis_period_months": analysis_period_months or 12,
    }

    # Conserver la table de correspondance (jamais envoyée à l'IA) pour le
    # chat de suivi sur cette analyse.
    if not correspondence_table.is_empty:
        _anonymization_cache[analyse_id] = correspondence_table

    # Extraire les recommandations pour le suivi décisionnel (mémoire
    # décisionnelle) — annexe séparée, n'altère pas analysis_result/le rapport.
    recommendations_tracking: Optional[list] = None
    if extract_recommendations:
        try:
            recommendations_tracking = extract_recommendations(analysis_result.model_dump(), analyse_id)
        except Exception:
            recommendations_tracking = None

    # Cache analysis result dict for on-demand PDF/PPTX generation
    _analysis_result_cache[analyse_id] = analysis_result.model_dump()

    # Generate Excel export — all plans
    # Note V2 : l'Excel est généré ici avec le result_dict (pipeline legacy).
    # L'ExecutiveCaseJSON est construit lazily lors du premier export PDF/PPTX
    # à la demande — évite d'ajouter un appel Opus supplémentaire dans ce pipeline
    # principal (risque de timeout Railway).
    try:
        excel_bytes = generate_excel_report(analysis_result, analysis_result.model_dump(), file.filename)
        _export_cache[analyse_id] = excel_bytes
        analysis_result.excel_export_url = f"/api/export/{analyse_id}"
        analysis_result.excel_export_nom = (
            f"pepperyn_analyse_{file.filename.rsplit('.', 1)[0]}_{analyse_id[:8]}.xlsx"
        )
    except Exception:
        pass  # Export failure is non-blocking

    # ── SÉCURITÉ : suppression fichier source ───────────────────────────────
    # Le fichier uploadé (file_bytes) est en mémoire Python uniquement —
    # il n'est jamais écrit sur disque. Il sera libéré par le GC Python
    # à la fin de cette requête. Conforme au master plan "auto-delete source file".
    file_size_bytes = len(file_bytes)  # stocker avant suppression
    # FIN-001 — SHA-256 du fichier brut (identité source, octet pour octet).
    # Calculé ici, avant del file_bytes, et transmis à _save_to_db().
    # Distinct du decision_fingerprint (données sources ≠ conclusions décisionnelles).
    source_data_hash = hashlib.sha256(file_bytes).hexdigest()
    del file_bytes  # libération explicite immédiate
    logger.info(f"[SECURITY] Fichier source supprimé de la mémoire après analyse — {analyse_id}")

    # ── WP5C — Decision Kernel extraction (additive, non-bloquant) ───────────
    # Appelé après l'overwrite EDM (plan_action_haute final, L586-601) et après
    # l'attachement de data_quality (L603-621). Ne lit que analysis_result —
    # jamais modifié, jamais persisté via ce pointeur. Retourne None si CA-2
    # échoue (toutes les Decisions insufficient_data) ou sur toute erreur interne.
    # Non-bloquant par conception : un Kernel None ne compromet pas la persistance
    # de l'analyse ni aucun export existant.
    _decision_kernel = extract_decision_kernel(
        analysis_result=analysis_result,
        analyse_id=analyse_id,
        source_data_hash=source_data_hash,
    )

    # Increment analysis usage counter (server-side, after success)
    _usage_service.increment_analysis(company_id)

    # Sync to Airtable CRM (non-blocking)
    duration_ms = int((time.time() - start_time) * 1000)
    try:
        from services.crm_service import log_analysis as crm_log
        logger.debug("[CRM] log_analysis (plan=%s, auth_type=%s)", plan, auth_type)
        # Resolve user email from Supabase (optional — enrichit la fiche CRM)
        _user_email = ""
        try:
            from main import get_supabase_service as _gsb
            _sb2 = _gsb()
            _prof = _sb2.from_("profiles").select("email").eq("company_id", company_id).limit(1).execute()
            if _prof.data:
                _user_email = _prof.data[0].get("email", "")
        except Exception:
            pass
        crm_log(
            user_id=company_id,
            analyse_id=analyse_id,
            filename=file.filename,
            analysis_result=analysis_result.model_dump(),
            model_used="claude-opus-4-6",
            tokens_used=total_tokens,
            cost_estimate=cost,
            email=_user_email,
            industry=industry,
            business_model=business_model,
            plan=plan,
        )
    except Exception:
        pass  # CRM sync is non-blocking

    # Persist to Supabase (non-blocking) — DOIT être avant save_analysis_memory
    # car financial_metrics.analyse_id référence analyses.id (FK constraint)
    _save_to_db(
        analyse_id=analyse_id,
        company_id=company_id,
        session_id=session_id,
        filename=file.filename,
        ext=ext,
        file_size=file_size_bytes,
        analysis_result=analysis_result,
        context=context,
        mode=mode,
        entity_id=entity_id,
        total_tokens=total_tokens,
        cost=cost,
        duration_ms=duration_ms,
        plan=plan,
        source_data_hash=source_data_hash,
        decision_kernel=_decision_kernel,  # WP5C — None si extraction échouée/CA-2
    )

    # Save memory APRÈS _save_to_db (FK: financial_metrics.analyse_id → analyses.id)
    if _memory_service:
        try:
            _memory_service.save_analysis_memory(company_id, analyse_id, analysis_result.model_dump())
        except Exception as e:
            logger.error(f"[MEMORY] save_analysis_memory failed: {e}")

    return AnalyzeResponse(
        success=True,
        message=f"Analyse complète — {duration_ms}ms",
        analyse_id=analyse_id,
        result=analysis_result,
        tokens_used=total_tokens,
        cout_estime=cost,
        memory_insight=memory_insight,
        recommendations_tracking=recommendations_tracking,
    )


def _save_to_db(
    analyse_id: str,
    company_id: str,
    session_id: Optional[str],
    filename: str,
    ext: str,
    file_size: int,
    analysis_result,
    context: str,
    mode: str,
    total_tokens: int,
    cost: float,
    duration_ms: int,
    plan: str,
    entity_id: Optional[str] = None,
    source_data_hash: Optional[str] = None,
    decision_kernel=None,  # Optional[DecisionKernel] — WP5C
):
    """Save analysis record to Supabase. Errors are logged but non-blocking."""
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()

        insert_payload = {
            "id": analyse_id,
            "company_id": company_id,
            "fichier_nom": filename,
            "fichier_type": ext,
            "type_document": analysis_result.type_document,
            "contexte_utilisateur": context,
            "mode": mode,
            "analyse_json": analysis_result.model_dump(),
            "score_confiance": analysis_result.score_confiance,
            "tokens_input": total_tokens,
            "cout_estime_euros": cost,
            "duree_traitement_ms": duration_ms,
            "status": "completed",
            "chat_count": 0,
        }
        # Only add optional fields if not None (avoids schema mismatch on older tables)
        if session_id is not None:
            insert_payload["session_id"] = session_id
        if file_size is not None:
            insert_payload["fichier_taille_bytes"] = file_size
        if entity_id is not None:
            insert_payload["entity_id"] = entity_id

        # source_data_hash : SHA-256(file_bytes bruts), calculé avant del file_bytes.
        # Identité du fichier source — distinct et indépendant du fingerprint décisionnel.
        if source_data_hash is not None:
            insert_payload["source_data_hash"] = source_data_hash

        # WP5C — Decision Kernel + Decision Fingerprint (Commit 5 & 6)
        # Persistance additive : aucun flux existant ne dépend de ces colonnes.
        # decision_kernel_version est lu depuis l'objet Kernel (jamais hardcodé 'dk-1').
        # Si decision_kernel est None (CA-2 ou erreur interne), les colonnes restent NULL.
        # WP5C Commit 6 (KERNEL-INV-013) : le fingerprint est embarqué dans le Kernel
        # (Phase 9 de l'extracteur). Il n'est jamais recalculé ici depuis AnalysisResult.
        if decision_kernel is not None:
            insert_payload["decision_kernel"] = decision_kernel.model_dump(mode="json")
            insert_payload["decision_kernel_version"] = decision_kernel.kernel_version
            # Fingerprint : lu depuis le Kernel (posé en Phase 9, après canonicalisation).
            # None possible si le proxy ne contient pas de champ décisionnel significatif
            # (cas théorique pour un Kernel non-CA-2 — normalement toujours set).
            if decision_kernel.decision_fingerprint is not None:
                insert_payload["decision_fingerprint"] = decision_kernel.decision_fingerprint
                insert_payload["decision_fingerprint_version"] = decision_kernel.decision_fingerprint_version

        logger.debug("[DB] Insert analyse %s", analyse_id)
        result = supabase.from_("analyses").insert(insert_payload).execute()

    except Exception as e:
        logger.error(f"[DB ERROR] _save_to_db failed — analyse_id={analyse_id} | error={type(e).__name__}: {e}")

    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        supabase.from_("usage_logs").insert({
            "company_id": company_id,
            "analyse_id": analyse_id,
            "action": "analyze_file",
            "model": "claude-opus-4-6",
            "tokens_input": total_tokens,
            "cout_estime_euros": cost,
            "duree_ms": duration_ms,
        }).execute()
    except Exception as e:
        logger.error(f"[DB ERROR] usage_logs insert failed — {type(e).__name__}: {e}")


@router.post("/analyze/text", response_model=TextQueryResponse)
async def analyze_text(
    request: TextQueryRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Answer a financial question without file upload."""
    await _resolve_auth(authorization, x_auth_type)

    client = get_anthropic_client()

    system_prompt = """Tu es Pepperyn, un assistant financier IA expert de niveau consultant McKinsey.
Tu réponds aux questions financières de manière précise, structurée et professionnelle.
Tu peux expliquer des concepts financiers, analyser des situations décrites, donner des recommandations générales.
Si une question nécessite des données chiffrées spécifiques (les chiffres réels de l'entreprise), invite l'utilisateur à uploader son fichier Excel pour une analyse complète.
Sois concis mais complet. Utilise des listes structurées quand c'est pertinent.
Réponds toujours en français."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": request.query}]
        )
        response_text = message.content[0].text
    except Exception as e:
        logger.error("[ANALYZE] Erreur IA (texte): %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de la réponse.")

    return TextQueryResponse(
        success=True,
        message="Réponse générée",
        response=response_text
    )


class ChatRequest(TextQueryRequest):
    analysis_id: Optional[str] = None
    analysis_context: Optional[str] = None
    history: Optional[list] = None


class ChatResponse(TextQueryResponse):
    model_used: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_analysis(
    request: ChatRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Chat endpoint with server-side limit enforcement.
    Modèle : Haiku sur tous les plans (décision financière — voir llm_service.py).
    Limites : FREE 3 msg/analyse · PRO 300 msg/mois · POWER 1500 msg/mois · SCALE illimité.
    """
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Server-side chat limit check (non-bypassable)
    allowed, reason, model_tier = _usage_service.can_chat(
        company_id, request.analysis_id, plan
    )
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    # ── CONFIDENTIALITÉ : anonymisation du contexte de chat ──────────────────
    # Si une table de correspondance existe pour cette analyse, le contexte,
    # l'historique et le message de l'utilisateur sont anonymisés avant
    # l'appel IA, et la réponse est ré-identifiée avant d'être renvoyée.
    correspondence_table = (
        _anonymization_cache.get(request.analysis_id) if request.analysis_id else None
    )

    chat_message = request.query
    chat_context = request.analysis_context or ""
    chat_history = request.history or []

    if correspondence_table and not correspondence_table.is_empty:
        chat_message = anonymize_text(chat_message, correspondence_table)
        chat_context = anonymize_text(chat_context, correspondence_table)
        chat_history = [
            {**h, "content": anonymize_text(h.get("content", ""), correspondence_table)}
            if isinstance(h, dict) and isinstance(h.get("content"), str) else h
            for h in chat_history
        ]

    try:
        # ── V2 Conversation Engine — routage conditionnel ─────────────────────
        # Si analyse_id présent ET ExecutiveCase V2 disponible → Conversation Engine.
        # Sinon → comportement legacy (call_chat_intelligent) strictement inchangé.
        _case_v2 = None
        if request.analysis_id:
            try:
                _case_v2 = await _get_or_build_executive_case_v2(request.analysis_id)
            except Exception as _v2_exc:
                logger.warning("[V2-CE] Échec construction V2 — fallback legacy: %s", _v2_exc)

        if _case_v2 is not None:
            logger.info(
                "[V2-CE] Conversation Engine utilisé (id=%s)",
                (request.analysis_id or "")[:8],
            )
            from services.conversation_engine import get_chat_response as _ce_chat
            response_text, model_used = await _ce_chat(
                executive_case_v2=_case_v2,
                user_message=chat_message,
                history=chat_history,
            )
        else:
            # ── Legacy path (comportement original inchangé) ──────────────────
            response_text, model_used = await call_chat_intelligent(
                message=chat_message,
                analysis_context=chat_context,
                history=chat_history,
                model_tier=model_tier,
            )
    except Exception as e:
        logger.error("[ANALYZE] Erreur IA (chat): %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de la réponse.")

    if correspondence_table and not correspondence_table.is_empty:
        response_text = deanonymize_recursive(response_text, correspondence_table)

    # Increment chat count after successful response (per-analysis + monthly)
    _usage_service.increment_chat(request.analysis_id, company_id)

    # Track chat_message event (Supabase)
    _usage_service.track_activity(company_id, "chat_message", {
        "analysis_id": request.analysis_id,
        "model": model_used,
        "plan": plan,
        "model_tier": model_tier,
    })

    # Sync chat to Airtable CRM (non-blocking)
    try:
        from services.crm_service import log_chat as crm_log_chat
        crm_log_chat(
            user_id=company_id,
            analysis_id=request.analysis_id,
            model_used=model_used,
        )
    except Exception:
        pass

    return ChatResponse(
        success=True,
        message="Réponse générée",
        response=response_text,
        model_used=model_used,
    )


def _resolve_entity_name(analyse_id: str) -> Optional[str]:
    """
    Retourne le nom de l'entité liée à cette analyse (filiale ou client),
    ou None si aucune entité n'est associée.
    Priorité sur le nom du compte utilisateur dans les en-têtes de rapports.
    """
    try:
        from main import get_supabase_service as _gsvc
        _sb = _gsvc()
        _row = (
            _sb.from_("analyses")
            .select("entity_id")
            .eq("id", analyse_id)
            .single()
            .execute()
        )
        if _row.data and _row.data.get("entity_id"):
            _eid = _row.data["entity_id"]
            _ent = (
                _sb.from_("entities")
                .select("name")
                .eq("id", _eid)
                .single()
                .execute()
            )
            if _ent.data and _ent.data.get("name"):
                return _ent.data["name"]
    except Exception:
        pass
    return None


def _verify_export_access(analyse_id: str, company_id: str) -> None:
    """
    Vérifie que l'analyse demandée appartient bien à la company authentifiée
    avant de servir un export (anti-IDOR / BOLA).
    1) cache en mémoire `_analysis_owner` ;
    2) repli base de données (après redémarrage) en filtrant sur company_id.
    Lève 404 si l'analyse n'existe pas ou n'appartient pas à la company.
    """
    owner = _analysis_owner.get(analyse_id)
    if owner is not None:
        if owner != company_id:
            raise HTTPException(status_code=404, detail="Analyse introuvable")
        return

    # Repli DB : l'analyse n'est plus en cache mémoire
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        row = (
            supabase.from_("analyses")
            .select("id")
            .eq("id", analyse_id)
            .eq("company_id", company_id)
            .limit(1)
            .execute()
        )
        if row.data:
            _analysis_owner[analyse_id] = company_id
            return
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Analyse introuvable")


_MULTI_EXPORT_PLANS = {"pro", "power", "scale"}


def _check_and_lock_format(analyse_id: str, requested_format: str, plan: str = "free") -> None:
    """
    Enforce "one export format per analysis" rule — FREE plans only.
    PRO / POWER / SCALE : tous les formats sont disponibles sans restriction.
    Raises HTTPException 409 uniquement si plan FREE et format déjà choisi.
    """
    if (plan or "").strip().lower() in _MULTI_EXPORT_PLANS:
        # Aucune restriction sur les plans payants
        return

    existing = _export_format_chosen.get(analyse_id)
    if existing and existing != requested_format:
        raise HTTPException(
            status_code=409,
            detail=f"Ce rapport a déjà été exporté en {existing.upper()}. Un seul format d'export est possible par analyse (plan gratuit)."
        )
    if not existing:
        _export_format_chosen[analyse_id] = requested_format
        # Persist to DB (non-blocking)
        try:
            from main import get_supabase_service
            supabase = get_supabase_service()
            supabase.from_("analyses").update(
                {"export_format": requested_format}
            ).eq("id", analyse_id).execute()
        except Exception:
            pass


@router.get("/export/{analyse_id}")
async def download_excel(
    analyse_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Download the Excel report for a given analysis."""
    from fastapi.responses import Response

    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Contrôle d'accès : l'analyse doit appartenir à la company authentifiée
    _verify_export_access(analyse_id, company_id)

    # Enforce one-format rule (bypassé pour PRO / POWER / SCALE)
    _check_and_lock_format(analyse_id, "excel", plan)

    # Track export event
    _usage_service.track_activity(company_id, "export_generated", {
        "analyse_id": analyse_id,
        "format": "excel",
    })

    excel_bytes = _export_cache.get(analyse_id)
    if not excel_bytes:
        raise HTTPException(
            status_code=404,
            detail="Fichier d'export non disponible. Les exports sont disponibles pendant la session active."
        )

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="pepperyn_analyse_{analyse_id[:8]}.xlsx"',
            "Content-Length": str(len(excel_bytes)),
        }
    )


async def _get_or_build_executive_case(
    analyse_id: str,
    result_dict: dict,
    company_name: Optional[str] = None,
) -> "_ExecutiveCaseJSON":
    """
    Retourne l'ExecutiveCaseJSON pour une analyse — V2 Pipeline.

    Ordre de priorité :
      1. Cache mémoire (_executive_case_cache) — le plus rapide.
      2. Appel Agent 1 (Claude Opus via executive_case_builder).
         Le résultat est mis en cache mémoire pour les exports suivants.

    Ce JSON est la source unique de vérité : PDF, PPTX et Excel reçoivent
    tous le même objet — aucun recalcul, aucune divergence possible.
    """
    if analyse_id in _executive_case_cache:
        logger.info("[V2] ExecutiveCaseJSON depuis cache mémoire (id=%s)", analyse_id[:8])
        return _executive_case_cache[analyse_id]

    logger.info("[V2] Construction ExecutiveCaseJSON via Agent 1 (id=%s)", analyse_id[:8])
    try:
        from services.executive_case_builder import build_executive_case
        case = await build_executive_case(result_dict, company_name=company_name or "")
    except Exception as exc:
        logger.error("[V2] Échec Agent 1 (%s) — fallback Python pur.", exc)
        from services.executive_case_builder import _python_mapper
        from services.executive_decision_model import build_executive_decision_model
        edm  = build_executive_decision_model(result_dict)
        case = _python_mapper(result_dict, edm, company_name or "")

    _executive_case_cache[analyse_id] = case
    return case


async def _get_or_build_executive_case_v2(
    analyse_id: str,
) -> Optional["_ExecutiveCase"]:
    """
    Retourne l'ExecutiveCase V2 pour une analyse — Conversation Engine.

    Ordre de priorité :
      1. Cache mémoire (_executive_case_v2_cache) — cache hit, retour immédiat.
      2. Construction Python déterministe (executive_case_v2_builder) depuis
         _analysis_result_cache. Aucun appel LLM, aucun ralentissement du pipeline.

    Retourne None si aucun résultat d'analyse n'est disponible pour cet analyse_id.
    Ne modifie PAS le pipeline d'analyse, les exports PDF/PPTX/XLSX, ni le chat.
    """
    # ── 1. Cache hit ──────────────────────────────────────────────────────────
    if analyse_id in _executive_case_v2_cache:
        logger.info("[V2-CE] ExecutiveCase V2 depuis cache mémoire (id=%s)", analyse_id[:8])
        return _executive_case_v2_cache[analyse_id]

    # ── 2. Vérifier disponibilité du résultat d'analyse ──────────────────────
    result_dict = _analysis_result_cache.get(analyse_id)
    if not result_dict:
        logger.warning(
            "[V2-CE] Aucun résultat d'analyse disponible pour id=%s — "
            "le pipeline d'analyse doit avoir été exécuté en premier.",
            analyse_id[:8],
        )
        return None

    # ── 3. Cache miss — construction déterministe (Python pur, sans LLM) ─────
    logger.info("[V2-CE] Construction ExecutiveCase V2 (id=%s)", analyse_id[:8])
    try:
        from services.executive_case_v2_builder import build_executive_case_v2
        company_name = result_dict.get("company_name", "")
        case_v2 = build_executive_case_v2(
            result_dict=result_dict,
            company_name=company_name,
            analyse_id=analyse_id,
        )
        _executive_case_v2_cache[analyse_id] = case_v2
        logger.info("[V2-CE] ExecutiveCase V2 construit et mis en cache (id=%s)", analyse_id[:8])
        return case_v2
    except Exception as exc:
        logger.error(
            "[V2-CE] Échec construction ExecutiveCase V2 (id=%s) : %s",
            analyse_id[:8], exc,
        )
        return None


@router.get("/conversation-context/{analyse_id}")
async def get_conversation_context(
    analyse_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Retourne le contexte conversationnel V2 pour un analyse_id donné.

    Payload retourné (3 champs uniquement) :
      - auto_opening_message : str
      - suggested_quick_prompts : list[str]
      - sacred_sentence : str (Literal "Aucune question n'est trop simple.")

    L'ExecutiveCase complet n'est JAMAIS exposé par cet endpoint.
    Aucun appel LLM — construction Python déterministe uniquement.
    """
    from fastapi.responses import JSONResponse

    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Contrôle d'accès : l'analyse doit appartenir à la company authentifiée
    _verify_export_access(analyse_id, company_id)

    # Construire / récupérer l'ExecutiveCase V2 (lazy, Python pur, sans LLM)
    case_v2 = await _get_or_build_executive_case_v2(analyse_id)

    if case_v2 is None:
        raise HTTPException(
            status_code=404,
            detail="Contexte conversationnel non disponible — lancez d'abord une analyse.",
        )

    ce = case_v2.conversation_engine
    return JSONResponse({
        "auto_opening_message":   ce.auto_opening_message,
        "suggested_quick_prompts": ce.suggested_quick_prompts,
        "sacred_sentence":        ce.sacred_sentence,
    })


@router.get("/export-pdf/{analyse_id}")
async def download_pdf(
    analyse_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Download a PDF report for a given analysis."""
    from fastapi.responses import Response
    from services.export_pdf_service import generate_pdf_report

    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Contrôle d'accès : l'analyse doit appartenir à la company authentifiée
    _verify_export_access(analyse_id, company_id)

    # Enforce one-format rule (bypassé pour PRO / POWER / SCALE)
    _check_and_lock_format(analyse_id, "pdf", plan)

    # Nom pour la couverture du rapport :
    # 1. Nom du compte (fallback)
    # 2. Nom de l'entité analysée si filiale/client sélectionné (priorité)
    company_name = None
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        company_row = (
            supabase.from_("companies").select("name").eq("id", company_id).single().execute()
        )
        if company_row.data:
            company_name = company_row.data.get("name")
    except Exception:
        pass
    entity_name = _resolve_entity_name(analyse_id)
    if entity_name:
        company_name = entity_name

    # Track export event (Supabase + Airtable)
    _usage_service.track_activity(company_id, "export_generated", {
        "analyse_id": analyse_id,
        "format": "pdf",
    })
    try:
        from services.crm_service import log_event as crm_log_event
        crm_log_event(company_id, "export_generated", {"analyse_id": analyse_id, "format": "pdf"})
    except Exception:
        pass

    # Return cached PDF if available
    pdf_bytes = _pdf_cache.get(analyse_id)
    if not pdf_bytes:
        # Charger le result_dict depuis cache mémoire ou DB
        result_dict = _analysis_result_cache.get(analyse_id)
        if not result_dict:
            try:
                from main import get_supabase_service
                supabase = get_supabase_service()
                row = supabase.from_("analyses").select("analyse_json").eq("id", analyse_id).single().execute()
                if row.data:
                    result_dict = row.data.get("analyse_json", {})
            except Exception:
                pass

        if not result_dict:
            raise HTTPException(
                status_code=404,
                detail="Données d'analyse non disponibles pour générer le PDF."
            )

        # Priorité au nom de la société cible extrait du fichier analysé (ex: Optilux),
        # pas au nom du compte utilisateur (ex: Finflate).
        if result_dict.get("company_name"):
            company_name = result_dict["company_name"]

        try:
            # ── V2 : construire/charger l'ExecutiveCaseJSON (source unique de vérité)
            executive_case = await _get_or_build_executive_case(
                analyse_id, result_dict, company_name
            )
            _params = _analysis_params_cache.get(analyse_id, {})
            pdf_bytes = generate_pdf_report(executive_case, company_name=company_name,
                                            target_date=_params.get("target_date") or None)
            _pdf_cache[analyse_id] = pdf_bytes
        except Exception as e:
            logger.error("[ANALYZE] Erreur génération PDF: %s", e)
            raise HTTPException(status_code=500, detail="Erreur lors de la génération du PDF.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="pepperyn_analyse_{analyse_id[:8]}.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


@router.get("/export-pptx/{analyse_id}")
async def download_pptx(
    analyse_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Download a PowerPoint report for a given analysis."""
    from fastapi.responses import Response
    from services.export_pptx_service import generate_pptx_report

    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Contrôle d'accès : l'analyse doit appartenir à la company authentifiée
    _verify_export_access(analyse_id, company_id)

    # Enforce one-format rule (bypassé pour PRO / POWER / SCALE)
    _check_and_lock_format(analyse_id, "pptx", plan)

    # Nom pour la couverture du Board Deck :
    # 1. Nom du compte (fallback)
    # 2. Nom de l'entité analysée si filiale/client sélectionné (priorité)
    company_name = None
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        company_row = (
            supabase.from_("companies").select("name").eq("id", company_id).single().execute()
        )
        if company_row.data:
            company_name = company_row.data.get("name")
    except Exception:
        pass
    entity_name = _resolve_entity_name(analyse_id)
    if entity_name:
        company_name = entity_name

    # Track export event (Supabase + Airtable)
    _usage_service.track_activity(company_id, "export_generated", {
        "analyse_id": analyse_id,
        "format": "pptx",
    })
    try:
        from services.crm_service import log_event as crm_log_event
        crm_log_event(company_id, "export_generated", {"analyse_id": analyse_id, "format": "pptx"})
    except Exception:
        pass

    # Return cached PPTX if available
    pptx_bytes = _pptx_cache.get(analyse_id)
    if not pptx_bytes:
        result_dict = _analysis_result_cache.get(analyse_id)
        if not result_dict:
            try:
                from main import get_supabase_service
                supabase = get_supabase_service()
                row = supabase.from_("analyses").select("analyse_json").eq("id", analyse_id).single().execute()
                if row.data:
                    result_dict = row.data.get("analyse_json", {})
            except Exception:
                pass

        if not result_dict:
            raise HTTPException(
                status_code=404,
                detail="Données d'analyse non disponibles pour générer le PowerPoint."
            )

        # Priorité au nom de la société cible extrait du fichier analysé (ex: Optilux),
        # pas au nom du compte utilisateur (ex: Finflate).
        if result_dict.get("company_name"):
            company_name = result_dict["company_name"]

        try:
            # ── V2 : réutiliser l'ExecutiveCaseJSON déjà construit (source unique de vérité)
            # Si le PDF a déjà été généré, le cache évite un second appel Opus.
            executive_case = await _get_or_build_executive_case(
                analyse_id, result_dict, company_name
            )
            _params = _analysis_params_cache.get(analyse_id, {})
            pptx_bytes = generate_pptx_report(executive_case, company_name=company_name,
                                              target_date=_params.get("target_date") or None)
            _pptx_cache[analyse_id] = pptx_bytes
        except Exception as e:
            logger.error("[ANALYZE] Erreur génération PowerPoint: %s", e)
            raise HTTPException(status_code=500, detail="Erreur lors de la génération du PowerPoint.")

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="pepperyn_analyse_{analyse_id[:8]}.pptx"',
            "Content-Length": str(len(pptx_bytes)),
        }
    )
