"""
Analysis routes for Pepperyn.
POST /api/analyze      — Analyze an uploaded financial file
POST /api/analyze/text — Text question (no file)
"""
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from jose import jwt, JWTError

from models.schemas import AnalyzeResponse, TextQueryRequest, TextQueryResponse
from connectors import FileConnector
from services.llm_service import run_full_pipeline, get_anthropic_client, call_chat_intelligent
from services.excel_export import generate_excel_report
from services.usage_service import UsageService
try:
    from services.memory_service import MemoryService
    _memory_service = MemoryService()
except ImportError:
    _memory_service = None

_usage_service = UsageService()

router = APIRouter(prefix="/api", tags=["analyze"])

JWT_SECRET = os.getenv("JWT_GUEST_SECRET", "pepperyn_guest_secret_key_change_in_prod")
JWT_ALGORITHM = "HS256"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf'}

# In-memory export caches  (replace with object storage in production)
_export_cache: dict[str, bytes] = {}          # analyse_id → excel bytes
_pdf_cache:    dict[str, bytes] = {}          # analyse_id → pdf bytes
_pptx_cache:   dict[str, bytes] = {}          # analyse_id → pptx bytes
_export_format_chosen: dict[str, str] = {}    # analyse_id → "excel"|"pdf"|"pptx"
_analysis_result_cache: dict[str, dict] = {}  # analyse_id → result dict (pour PDF/PPTX à la demande)


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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.warning(f"[AUTH DEBUG] JWT decoded — type={payload.get('type')!r} | company_id={payload.get('company_id')!r} | plan={payload.get('plan')!r}")
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
            profile_response = (
                supabase.from_("profiles")
                .select("company_id, company:companies(plan)")
                .eq("id", user_response.user.id)
                .single()
                .execute()
            )
            if profile_response.data:
                company_id = profile_response.data["company_id"]
                company_data = profile_response.data.get("company") or {}
                plan = company_data.get("plan", "free") if isinstance(company_data, dict) else "free"
                return company_id, plan, "admin"
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Token invalide ou expiré")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    context: str = Form(default=""),
    mode: str = Form(default="complete"),
    session_id: Optional[str] = Form(default=None),
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

    # Parse file (Step 1: pre-processing, 0 tokens)
    try:
        parsed_data = FileConnector(file_bytes, file.filename).fetch()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {str(e)}")

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

    # Retrieve memory context
    memory_section = ""
    actions_section = ""
    memory_ctx: list = []
    if _memory_service:
        try:
            memory_ctx = _memory_service.get_memory_context(company_id)
            memory_section = _memory_service.build_memory_prompt_section(memory_ctx)
        except Exception:
            pass

    # Track analysis_started event
    _usage_service.track_activity(company_id, "analysis_started", {
        "filename": file.filename,
        "mode": mode,
        "plan": plan,
    })

    # Run LLM pipeline v3 (2 calls Claude)
    try:
        analysis_result, total_tokens, cost = await run_full_pipeline(
            parsed_data, context,
            industry=industry,
            business_model=business_model,
            memory_section=memory_section,
            actions_section=actions_section,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse IA: {str(e)}")

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

    # Assign the analyse_id to the result object so the frontend can use it
    analyse_id = str(uuid.uuid4())
    analysis_result.id = analyse_id

    # Generate Excel export — all plans
    try:
        excel_bytes = generate_excel_report(analysis_result, parsed_data, file.filename)
        _export_cache[analyse_id] = excel_bytes
        analysis_result.excel_export_url = f"/api/export/{analyse_id}"
        analysis_result.excel_export_nom = (
            f"pepperyn_analyse_{file.filename.rsplit('.', 1)[0]}_{analyse_id[:8]}.xlsx"
        )
    except Exception:
        pass  # Export failure is non-blocking

    # Cache analysis result dict for on-demand PDF/PPTX generation
    _analysis_result_cache[analyse_id] = analysis_result.model_dump()

    # Save memory after analysis
    if _memory_service:
        try:
            _memory_service.save_analysis_memory(company_id, analysis_result.model_dump())
        except Exception:
            pass

    # Increment analysis usage counter (server-side, after success)
    _usage_service.increment_analysis(company_id)

    # Sync to Airtable CRM (non-blocking)
    duration_ms = int((time.time() - start_time) * 1000)
    try:
        from services.crm_service import log_analysis as crm_log
        # Debug: log company_id before CRM call to diagnose None issue
        logger.warning(f"[CRM DEBUG] company_id={company_id!r} | type={type(company_id).__name__} | plan={plan!r} | auth_type={auth_type!r}")
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

    # Persist to Supabase (non-blocking)
    _save_to_db(
        analyse_id=analyse_id,
        company_id=company_id,
        session_id=session_id,
        filename=file.filename,
        ext=ext,
        file_size=len(file_bytes),
        analysis_result=analysis_result,
        context=context,
        mode=mode,
        total_tokens=total_tokens,
        cost=cost,
        duration_ms=duration_ms,
        plan=plan,
    )

    return AnalyzeResponse(
        success=True,
        message=f"Analyse complète — {duration_ms}ms",
        analyse_id=analyse_id,
        result=analysis_result,
        tokens_used=total_tokens,
        cout_estime=cost,
        memory_insight=memory_insight,
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
):
    """Save analysis record to Supabase. Errors are silently ignored."""
    try:
        from main import get_supabase_service
        supabase = get_supabase_service()

        supabase.from_("analyses").insert({
            "id": analyse_id,
            "company_id": company_id,
            "session_id": session_id,
            "fichier_nom": filename,
            "fichier_type": ext,
            "fichier_taille_bytes": file_size,
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
        }).execute()

        supabase.from_("usage_logs").insert({
            "company_id": company_id,
            "analyse_id": analyse_id,
            "action": "analyze_file",
            "model": "claude-opus-4-6",
            "tokens_input": total_tokens,
            "cout_estime_euros": cost,
            "duree_ms": duration_ms,
        }).execute()

    except Exception:
        pass


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
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

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
    Enforces FREE plan (5 msg/analysis) and PRO soft cap (200 → Sonnet downgrade).
    """
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    # Server-side chat limit check (non-bypassable)
    allowed, reason, model_tier = _usage_service.can_chat(
        company_id, request.analysis_id, plan
    )
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    try:
        response_text, model_used = await call_chat_intelligent(
            message=request.query,
            analysis_context=request.analysis_context or "",
            history=request.history or [],
            model_tier=model_tier,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

    # Increment chat count after successful response
    _usage_service.increment_chat(request.analysis_id)

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


def _check_and_lock_format(analyse_id: str, requested_format: str) -> None:
    """
    Enforce "one export format per analysis" rule.
    Raises HTTPException 409 if a different format was already chosen.
    Sets the chosen format on first call.
    Also persists to DB (non-blocking).
    """
    existing = _export_format_chosen.get(analyse_id)
    if existing and existing != requested_format:
        raise HTTPException(
            status_code=409,
            detail=f"Ce rapport a déjà été exporté en {existing.upper()}. Un seul format d'export est possible par analyse."
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

    # Enforce one-format rule
    _check_and_lock_format(analyse_id, "excel")

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

    # Enforce one-format rule
    _check_and_lock_format(analyse_id, "pdf")

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
        # Generate on demand from cached result
        result_dict = _analysis_result_cache.get(analyse_id)
        if not result_dict:
            # Try to fetch from DB
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

        try:
            pdf_bytes = generate_pdf_report(result_dict)
            _pdf_cache[analyse_id] = pdf_bytes
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur génération PDF: {str(e)}")

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

    # Enforce one-format rule
    _check_and_lock_format(analyse_id, "pptx")

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

        try:
            pptx_bytes = generate_pptx_report(result_dict)
            _pptx_cache[analyse_id] = pptx_bytes
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur génération PowerPoint: {str(e)}")

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="pepperyn_analyse_{analyse_id[:8]}.pptx"',
            "Content-Length": str(len(pptx_bytes)),
        }
    )
