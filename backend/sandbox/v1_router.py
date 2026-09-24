"""Non-production HTTP surface for the fixed V1 synthetic Golden Case."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from models.schemas import AnalyzeResponse
import routers.analyze as analyze_routes
from sandbox.v1_golden_case import run_v1_golden_case
from sandbox.governed_exports import generate_governed_excel, generate_governed_pdf, generate_governed_pptx
from services.governed_analysis_persistence import save_governed_analysis
from services.governed_temporal_continuity import (
    GovernedTemporalContinuityRefused, load_governed_temporal_comparison,
)
from services.decision_memory_service import DecisionMemoryService
from services.governed_memory_read import GovernedMemoryUnavailable, recommendations_tracking
from services.governed_analysis_read import GovernedReadRefused, load_owned_analysis, read_owned_analysis
from sandbox.heterogeneous_workbooks import inspect_registered_workbook, run_registered_mock_analysis
from sandbox.v1_prerequisite_evidence import (
    PrerequisiteEvidenceRefused, load_validated_prerequisite_evidence,
)
from sandbox.synthetic_product import SandboxRefused
from sandbox import source_dossiers

router = APIRouter(prefix="/api/v1", tags=["v1-synthetic"])
logger = logging.getLogger(__name__)
_EXECUTION_PREREQUISITES = ["Obtenir le tableau des flux mensuel et les échéanciers clients."]


def _recommendations_tracking(envelope, analysis_id, supabase=None, *, feedback_required=False):
    try:
        return recommendations_tracking(
            envelope, analysis_id, supabase, feedback_required=feedback_required,
        )
    except GovernedMemoryUnavailable:
        raise HTTPException(
            status_code=503, detail="État décisionnel indisponible : export gouverné refusé.",
        ) from None


class GovernedIntentionRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    status: str
    comment: Optional[str] = Field(default=None, max_length=1000)


class GovernedDecisionRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    decision_kind: str
    decision_text: str = Field(min_length=1, max_length=2000)
    prerequisites_acknowledged: bool


class GovernedFollowupRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    followup_status: str
    professional_note: str = Field(min_length=1, max_length=2000)
    prerequisites_confirmed_complete: bool = False


class GovernedExecutionRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    executed_on: date
    professional_note: str = Field(min_length=1, max_length=2000)
    prerequisites_confirmed_complete: bool


class GovernedPrerequisiteEvidenceRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)


@router.post("/synthetic-workbook-inspection")
async def inspect_v1_synthetic_workbook(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    raw = await file.read(1_000_001)
    if len(raw) > 1_000_000:
        raise HTTPException(status_code=413, detail="Classeur synthétique trop volumineux")
    try:
        return inspect_registered_workbook(raw, file.filename or "")
    except SandboxRefused as exc:
        raise HTTPException(
            status_code=400,
            detail="Fichier refusé : sélectionnez uniquement un classeur synthétique V1 enregistré.",
        ) from exc


async def _source_dossier_access(authorization, x_auth_type):
    if os.getenv("ENVIRONMENT") != "development" or os.getenv("PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO") != "1":
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    try:
        return get_supabase_service(), company_id
    except Exception:
        raise HTTPException(status_code=503, detail="Dossiers sources indisponibles") from None


def _source_dossier_error(exc):
    code = 404 if str(exc) == "NOT_FOUND" else 503
    return HTTPException(status_code=code, detail="Dossier source introuvable" if code == 404 else "Dossiers sources indisponibles")


@router.post("/synthetic-source-dossiers")
async def capture_source_dossier(
    file: UploadFile = File(...), entity_id: str = Form(...),
    authorization: Optional[str] = Header(default=None), x_auth_type: Optional[str] = Header(default=None),
):
    db, company_id = await _source_dossier_access(authorization, x_auth_type)
    raw = await file.read(1_000_001)
    if len(raw) > 1_000_000:
        raise HTTPException(status_code=413, detail="Classeur synthétique trop volumineux")
    try:
        return source_dossiers.capture_dossier(db, company_id=company_id, entity_id=entity_id,
                                              raw=raw, filename=file.filename or "")
    except source_dossiers.SourceDossierRefused as exc:
        raise _source_dossier_error(exc) from None
    except SandboxRefused:
        raise HTTPException(status_code=400, detail="Classeur synthétique enregistré requis") from None


@router.get("/synthetic-source-dossiers")
async def list_source_dossiers(entity_id: str, authorization: Optional[str] = Header(default=None),
                              x_auth_type: Optional[str] = Header(default=None)):
    db, company_id = await _source_dossier_access(authorization, x_auth_type)
    try:
        return source_dossiers.list_dossiers(db, company_id=company_id, entity_id=entity_id)
    except source_dossiers.SourceDossierRefused as exc:
        raise _source_dossier_error(exc) from None


@router.get("/synthetic-source-dossiers/{dossier_id}")
async def read_source_dossier(dossier_id: str, entity_id: str,
                              authorization: Optional[str] = Header(default=None),
                              x_auth_type: Optional[str] = Header(default=None)):
    db, company_id = await _source_dossier_access(authorization, x_auth_type)
    try:
        return source_dossiers.load_dossier(db, company_id=company_id, entity_id=entity_id, dossier_id=dossier_id)
    except source_dossiers.SourceDossierRefused as exc:
        raise _source_dossier_error(exc) from None


@router.get("/synthetic-source-attention")
async def source_attention(authorization: Optional[str] = Header(default=None),
                           x_auth_type: Optional[str] = Header(default=None)):
    db, company_id = await _source_dossier_access(authorization, x_auth_type)
    try:
        return source_dossiers.list_source_attention(db, company_id=company_id)
    except source_dossiers.SourceDossierRefused as exc:
        raise _source_dossier_error(exc) from None


@router.post("/synthetic-workbook-analysis", response_model=AnalyzeResponse)
async def analyze_v1_synthetic_workbook(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
    entity_id: Annotated[Optional[str], Form()] = None,
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    # An explicit client never falls back to the primary entity on refusal.
    if entity_id is None:
        _, entity_id, engagement_id = _resolve_primary_scope(supabase, company_id)
    else:
        _, entity_id, engagement_id = analyze_routes._resolve_analysis_entity_scope(
            supabase, company_id=company_id, entity_id=entity_id,
        )[0]
    raw = await file.read(1_000_001)
    if len(raw) > 1_000_000:
        raise HTTPException(status_code=413, detail="Classeur synthétique trop volumineux")
    try:
        mock = await asyncio.to_thread(run_registered_mock_analysis, raw, file.filename or "")
    except SandboxRefused as exc:
        raise HTTPException(
            status_code=400,
            detail="Analyse simulée refusée : utilisez le classeur synthétique English enregistré.",
        ) from exc

    analysis_id = str(uuid.uuid4())
    result = mock.envelope.analysis_result
    result.id = analysis_id
    save_governed_analysis(
        supabase,
        analysis_row={
            "id": analysis_id, "company_id": company_id, "entity_id": entity_id,
            "fichier_nom": mock.filename, "fichier_type": "xlsx",
            "type_document": "AUTRE", "contexte_utilisateur": "",
            "mode": "complete", "analyse_json": result.model_dump(mode="json"),
            "score_confiance": 0, "tokens_input": 0, "cout_estime_euros": 0,
            "duree_traitement_ms": 0, "status": "completed", "chat_count": 0,
            "source_data_hash": mock.source_sha256.lower(),
        },
        engagement_id=engagement_id,
        envelope=mock.envelope,
    )
    return AnalyzeResponse(
        success=True,
        message="Analyse V1 synthétique via fournisseur simulé local terminée",
        analyse_id=analysis_id,
        result=result,
        tokens_used=0,
        cout_estime=0,
        recommendations_tracking=_recommendations_tracking(mock.envelope, analysis_id),
    )


def _require_designated_company(company_id: str) -> None:
    if not company_id or company_id != os.getenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", ""):
        raise HTTPException(status_code=404, detail="Ressource introuvable")


def _resolve_primary_scope(supabase, company_id: str) -> tuple[str, str, str]:
    try:
        entities = (
            supabase.from_("entities").select("id")
            .eq("company_id", company_id).eq("is_primary", True).limit(2).execute()
        ).data or []
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Validation de l'entité indisponible") from exc
    if len(entities) != 1 or not entities[0].get("id"):
        raise HTTPException(status_code=404, detail="Entité synthétique indisponible")
    return analyze_routes._resolve_analysis_entity_scope(
        supabase, company_id=company_id, entity_id=entities[0]["id"],
    )[0]


def _load_for_company(supabase, *, analysis_id: str, company_id: str):
    try:
        return load_owned_analysis(supabase, analysis_id=analysis_id, company_id=company_id)
    except GovernedReadRefused as exc:
        raise _read_error(exc) from None


def _read_error(exc):
    if str(exc) == "NOT_FOUND":
        return HTTPException(status_code=404, detail="Analyse introuvable")
    return HTTPException(status_code=503, detail="Lecture gouvernée indisponible")


@router.post("/synthetic-demo", response_model=AnalyzeResponse)
async def run_v1_synthetic_demo(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    if await request.body():
        raise HTTPException(status_code=400, detail="La démonstration n'accepte aucun contenu")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    _, entity_id, engagement_id = _resolve_primary_scope(supabase, company_id)
    golden = await asyncio.to_thread(run_v1_golden_case)
    analysis_id = str(uuid.uuid4())
    result = golden.envelope.analysis_result
    result.id = analysis_id
    save_governed_analysis(
        supabase,
        analysis_row={
            "id": analysis_id, "company_id": company_id, "entity_id": entity_id,
            "fichier_nom": "optilux_m1c_raw_workbook.xlsx", "fichier_type": "xlsx",
            # The governed contract identifies the source precisely as a
            # FINANCIAL_WORKBOOK. The legacy analyses column has a closed,
            # statement-oriented vocabulary and this workbook combines more
            # than one statement, so AUTRE is its honest compatibility view.
            "type_document": "AUTRE", "contexte_utilisateur": "",
            # ``analyses.mode`` is the analysis-depth contract enforced by the
            # canonical database (quick | complete). Synthetic provenance is
            # carried by the immutable governed envelope and source hash, not
            # overloaded into this legacy field.
            "mode": "complete", "analyse_json": result.model_dump(mode="json"),
            "score_confiance": 0, "tokens_input": 0, "cout_estime_euros": 0,
            "duree_traitement_ms": 0, "status": "completed", "chat_count": 0,
            "source_data_hash": golden.source_workbook_sha256.lower(),
        }, engagement_id=engagement_id, envelope=golden.envelope,
    )
    return AnalyzeResponse(
        success=True, message="Démonstration V1 synthétique terminée",
        analyse_id=analysis_id, result=result, tokens_used=0, cout_estime=0,
        recommendations_tracking=_recommendations_tracking(golden.envelope, analysis_id, supabase),
    )


@router.get("/governed-analyses/{analysis_id}", response_model=AnalyzeResponse)
async def get_v1_governed_analysis(
    analysis_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    try:
        return read_owned_analysis(supabase, analysis_id=analysis_id, company_id=company_id)
    except GovernedReadRefused as exc:
        raise _read_error(exc) from None


@router.get("/governed-analyses/{analysis_id}/temporal-comparison")
async def get_v1_governed_temporal_comparison(
    analysis_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Describe source-fact changes without inferring causes or outcomes."""
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    try:
        return load_governed_temporal_comparison(
            get_supabase_service(), analysis_id=analysis_id, company_id=company_id,
        )
    except GovernedTemporalContinuityRefused as exc:
        logger.warning("[V1 TEMPORAL] comparison refused analysis=%s: %s", analysis_id, exc)
        raise HTTPException(status_code=503, detail="Continuité temporelle indisponible") from exc


@router.post("/governed-analyses/{analysis_id}/intention")
async def record_v1_governed_intention(
    analysis_id: str,
    request: GovernedIntentionRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Record explicit Founder intent without promoting it to a decision."""
    if request.status not in {"planned", "unsure", "rejected", "no_longer_relevant"}:
        raise HTTPException(status_code=400, detail="Intention invalide")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    recommendations = _recommendations_tracking(envelope, analysis_id)
    recommendation = next(
        (item for item in recommendations if item["id"] == request.recommendation_id), None,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommandation gouvernée introuvable")
    if not DecisionMemoryService(supabase).upsert_feedback(
        company_id=company_id,
        report_id=analysis_id,
        recommendation_id=recommendation["id"],
        recommendation_text=recommendation["text"],
        recommendation_source=recommendation["source"],
        status=request.status,
        comment=request.comment,
    ):
        raise HTTPException(status_code=503, detail="Enregistrement de l’intention indisponible")
    return {
        "success": True,
        "intention_recorded": True,
        "decision_confirmed": False,
        "arc_created": False,
    }


@router.post("/governed-analyses/{analysis_id}/decision")
async def record_v1_governed_decision(
    analysis_id: str,
    request: GovernedDecisionRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Confirm one explicit professional decision without creating an arc."""
    if request.decision_kind not in {"accepted_conditional", "modified", "rejected"}:
        raise HTTPException(status_code=400, detail="Type de décision invalide")
    decision_text = request.decision_text.strip()
    if not decision_text:
        raise HTTPException(status_code=400, detail="Texte de décision requis")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    recommendation = next(
        (item for item in _recommendations_tracking(envelope, analysis_id)
         if item["id"] == request.recommendation_id), None,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommandation gouvernée introuvable")
    if (request.decision_kind in {"accepted_conditional", "modified"}
            and recommendation["prerequisite_validation"]
            and not request.prerequisites_acknowledged):
        raise HTTPException(
            status_code=422,
            detail="Les validations requises doivent rester explicitement attachées à cette décision.",
        )
    try:
        existing = (
            supabase.from_("decision_feedback")
            .select("id,status,decision_confirmed_at")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("recommendation_id", recommendation["id"]).limit(2).execute()
        ).data or []
        if len(existing) != 1:
            raise HTTPException(status_code=409, detail="Enregistrez d’abord une intention explicite.")
        if existing[0].get("decision_confirmed_at"):
            raise HTTPException(status_code=409, detail="Cette décision est déjà confirmée et immuable.")
        if existing[0].get("status") not in {"planned", "unsure", "rejected", "no_longer_relevant"}:
            raise HTTPException(status_code=409, detail="L’état existant n’est pas une intention confirmable.")
        prerequisites_acknowledged = (
            request.prerequisites_acknowledged if request.decision_kind != "rejected" else False
        )
        updated = (
            supabase.from_("decision_feedback").update({
                "status": "decided",
                "decision_kind": request.decision_kind,
                "decision_text": decision_text,
                "decision_confirmed_at": datetime.now(timezone.utc).isoformat(),
                "decision_confirmation_source": "explicit",
                "prerequisites_acknowledged": prerequisites_acknowledged,
            }).eq("id", existing[0]["id"]).eq("company_id", company_id)
            .is_("decision_confirmed_at", "null").execute()
        ).data or []
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("[V1 DECISION] explicit confirmation failed analysis=%s: %s", analysis_id, exc)
        raise HTTPException(status_code=503, detail="Confirmation de la décision indisponible") from exc
    if len(updated) != 1:
        raise HTTPException(status_code=409, detail="La décision n’a pas pu être confirmée atomiquement.")
    return {
        "success": True,
        "decision_confirmed": True,
        "decision_confirmation_source": "explicit",
        "arc_created": False,
    }


@router.post("/governed-analyses/{analysis_id}/followup")
async def record_v1_governed_followup(
    analysis_id: str,
    request: GovernedFollowupRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Record one explicit checkpoint without mutating the confirmed decision."""
    allowed = {"pending_validation", "in_progress", "blocked", "completed", "not_pursued"}
    if request.followup_status not in allowed:
        raise HTTPException(status_code=400, detail="État de suivi invalide")
    note = request.professional_note.strip()
    if not note:
        raise HTTPException(status_code=400, detail="Note professionnelle requise")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    recommendation = next(
        (item for item in _recommendations_tracking(envelope, analysis_id)
         if item["id"] == request.recommendation_id), None,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommandation gouvernée introuvable")
    if (request.followup_status == "completed" and recommendation["prerequisite_validation"]
            and not request.prerequisites_confirmed_complete):
        raise HTTPException(
            status_code=422,
            detail="Un suivi terminé exige la confirmation explicite des validations préalables.",
        )
    try:
        decisions = (
            supabase.from_("decision_feedback").select("id,decision_confirmed_at")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("recommendation_id", recommendation["id"]).limit(2).execute()
        ).data or []
        if len(decisions) != 1 or not decisions[0].get("decision_confirmed_at"):
            raise HTTPException(status_code=409, detail="Une décision explicite est requise avant son suivi.")
        existing = (
            supabase.from_("governed_decision_followups").select("id")
            .eq("decision_feedback_id", decisions[0]["id"]).limit(2).execute()
        ).data or []
        if existing:
            raise HTTPException(status_code=409, detail="Le point de suivi initial est déjà enregistré.")
        inserted = (
            supabase.from_("governed_decision_followups").insert({
                "company_id": company_id,
                "report_id": analysis_id,
                "decision_feedback_id": decisions[0]["id"],
                "recommendation_id": recommendation["id"],
                "followup_status": request.followup_status,
                "professional_note": note,
                "prerequisites_confirmed_complete": request.prerequisites_confirmed_complete,
                "confirmation_source": "explicit",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        ).data or []
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("[V1 FOLLOW-UP] checkpoint failed analysis=%s: %s", analysis_id, exc)
        raise HTTPException(status_code=503, detail="Enregistrement du suivi indisponible") from exc
    if len(inserted) != 1:
        raise HTTPException(status_code=503, detail="Le suivi n’a pas été enregistré.")
    return {"success": True, "followup_recorded": True, "arc_created": False}


@router.post("/governed-analyses/{analysis_id}/prerequisite-evidence")
async def record_v1_prerequisite_evidence(
    analysis_id: str,
    request: GovernedPrerequisiteEvidenceRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Validate and bind the registered local prerequisite package only."""
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    recommendation = next(
        (item for item in _recommendations_tracking(envelope, analysis_id)
         if item["id"] == request.recommendation_id), None,
    )
    if (recommendation is None
            or recommendation["prerequisite_validation"] != _EXECUTION_PREREQUISITES):
        raise HTTPException(status_code=404, detail="Prérequis gouvernés introuvables")
    try:
        package = load_validated_prerequisite_evidence()
        decisions = (
            supabase.from_("decision_feedback").select("id,decision_kind,decision_confirmed_at")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("recommendation_id", recommendation["id"]).limit(2).execute()
        ).data or []
        if (len(decisions) != 1 or not decisions[0].get("decision_confirmed_at")
                or decisions[0].get("decision_kind") not in {"accepted_conditional", "modified"}):
            raise HTTPException(status_code=409, detail="Une décision exécutable explicite est requise.")
        followups = (
            supabase.from_("governed_decision_followups").select("id")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("decision_feedback_id", decisions[0]["id"]).limit(2).execute()
        ).data or []
        if len(followups) != 1:
            raise HTTPException(status_code=409, detail="Un suivi gouverné est requis.")
        existing = (
            supabase.from_("governed_decision_prerequisite_evidence").select("id")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("decision_feedback_id", decisions[0]["id"]).limit(2).execute()
        ).data or []
        if existing:
            raise HTTPException(status_code=409, detail="Les preuves préalables sont déjà enregistrées.")
        inserted = (
            supabase.from_("governed_decision_prerequisite_evidence").insert({
                "company_id": company_id, "report_id": analysis_id,
                "decision_feedback_id": decisions[0]["id"], "recommendation_id": recommendation["id"],
                "fixture_id": package.fixture_id, "payload_sha256": package.payload_sha256,
                "period_start": package.period_start.isoformat(), "period_end": package.period_end.isoformat(),
                "provenance": package.provenance, "payload": package.payload,
                "evidence_role": "DECISION_PREREQUISITE_ONLY", "synthetic": True,
                "external_network_used": False, "real_client_data_used": False,
                "later_evidence": False, "actual_outcome_created": False,
                "learning_created": False, "expected_impact_created": False,
                "validation_source": "registered_local_fixture",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        ).data or []
    except HTTPException:
        raise
    except PrerequisiteEvidenceRefused as exc:
        raise HTTPException(status_code=409, detail="Paquet synthétique préalable refusé.") from exc
    except Exception as exc:
        logger.warning("[V1 PREREQUISITES] registration failed analysis=%s: %s", analysis_id, exc)
        raise HTTPException(status_code=503, detail="Validation des preuves préalables indisponible") from exc
    if len(inserted) != 1:
        raise HTTPException(status_code=503, detail="Les preuves préalables n’ont pas été enregistrées.")
    return {"success": True, "prerequisite_evidence_recorded": True,
            "later_evidence_created": False, "outcome_created": False,
            "learning_created": False, "arc_created": False}


@router.post("/governed-analyses/{analysis_id}/execution")
async def record_v1_governed_execution(
    analysis_id: str,
    request: GovernedExecutionRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Record execution explicitly; never infer outcome or learning."""
    note = request.professional_note.strip()
    if not note:
        raise HTTPException(status_code=400, detail="Note professionnelle d’exécution requise")
    if not request.prerequisites_confirmed_complete:
        raise HTTPException(status_code=422, detail="Confirmez explicitement les validations préalables.")
    if request.executed_on > datetime.now(timezone.utc).date():
        raise HTTPException(status_code=422, detail="La date d’exécution ne peut pas être future.")
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    recommendation = next(
        (item for item in _recommendations_tracking(envelope, analysis_id)
         if item["id"] == request.recommendation_id), None,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommandation gouvernée introuvable")
    try:
        decisions = (
            supabase.from_("decision_feedback").select("id,decision_kind,decision_confirmed_at")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("recommendation_id", recommendation["id"]).limit(2).execute()
        ).data or []
        if len(decisions) != 1 or not decisions[0].get("decision_confirmed_at"):
            raise HTTPException(status_code=409, detail="Une décision explicite est requise avant son exécution.")
        if decisions[0].get("decision_kind") not in {"accepted_conditional", "modified"}:
            raise HTTPException(status_code=409, detail="Cette décision ne peut pas être déclarée exécutée.")
        confirmed_on = datetime.fromisoformat(
            decisions[0]["decision_confirmed_at"].replace("Z", "+00:00")
        ).date()
        if request.executed_on < confirmed_on:
            raise HTTPException(status_code=422, detail="L’exécution ne peut pas précéder la décision confirmée.")
        followups = (
            supabase.from_("governed_decision_followups").select("id")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("decision_feedback_id", decisions[0]["id"]).limit(2).execute()
        ).data or []
        if len(followups) != 1:
            raise HTTPException(status_code=409, detail="Un suivi gouverné est requis avant l’exécution.")
        evidence = (
            supabase.from_("governed_decision_prerequisite_evidence").select("id")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("decision_feedback_id", decisions[0]["id"])
            .eq("recommendation_id", recommendation["id"]).limit(2).execute()
        ).data or []
        if len(evidence) != 1:
            raise HTTPException(status_code=409, detail="Les preuves synthétiques préalables sont requises.")
        existing = (
            supabase.from_("governed_decision_executions").select("id")
            .eq("company_id", company_id).eq("report_id", analysis_id)
            .eq("decision_feedback_id", decisions[0]["id"]).limit(2).execute()
        ).data or []
        if existing:
            raise HTTPException(status_code=409, detail="L’exécution est déjà enregistrée.")
        inserted = (
            supabase.from_("governed_decision_executions").insert({
                "company_id": company_id, "report_id": analysis_id,
                "decision_feedback_id": decisions[0]["id"],
                "recommendation_id": recommendation["id"],
                "executed_on": request.executed_on.isoformat(),
                "professional_note": note,
                "prerequisites_confirmed_complete": True,
                "confirmation_source": "explicit",
                "prerequisite_evidence_id": evidence[0]["id"],
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        ).data or []
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("[V1 EXECUTION] checkpoint failed analysis=%s: %s", analysis_id, exc)
        raise HTTPException(status_code=503, detail="Enregistrement de l’exécution indisponible") from exc
    if len(inserted) != 1:
        raise HTTPException(status_code=503, detail="L’exécution n’a pas été enregistrée.")
    return {"success": True, "execution_recorded": True, "outcome_created": False,
            "learning_created": False, "arc_created": False}


def _export_temporal_context(supabase, analysis_id: str, company_id: str) -> dict:
    """History outage/integrity failure must not look like absent history."""
    try:
        return load_governed_temporal_comparison(
            supabase, analysis_id=analysis_id, company_id=company_id,
        )
    except GovernedTemporalContinuityRefused as exc:
        raise HTTPException(status_code=503, detail="Continuité temporelle indisponible pour l'export") from exc


@router.get("/governed-analyses/{analysis_id}/export.xlsx")
async def export_v1_governed_excel(
    analysis_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    decisions = [item for item in _recommendations_tracking(
        envelope, analysis_id, supabase, feedback_required=True,
    )
                 if item.get("decision_confirmed_at")]
    content = generate_governed_excel(envelope, analysis_id, decisions,
                                     temporal_comparison=_export_temporal_context(supabase, analysis_id, company_id))
    return Response(content=content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="pepperyn_v1_{analysis_id[:8]}.xlsx"'})


@router.get("/governed-analyses/{analysis_id}/export.pdf")
async def export_v1_governed_pdf(
    analysis_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    decisions = [item for item in _recommendations_tracking(
        envelope, analysis_id, supabase, feedback_required=True,
    )
                 if item.get("decision_confirmed_at")]
    content = generate_governed_pdf(envelope, analysis_id, decisions,
                                   temporal_comparison=_export_temporal_context(supabase, analysis_id, company_id))
    return Response(content=content, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="pepperyn_v1_{analysis_id[:8]}.pdf"'})


@router.get("/governed-analyses/{analysis_id}/export.pptx")
async def export_v1_governed_pptx(
    analysis_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    company_id, _, _ = await analyze_routes._resolve_auth(authorization, x_auth_type)
    _require_designated_company(company_id)
    from main import get_supabase_service
    supabase = get_supabase_service()
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    decisions = [item for item in _recommendations_tracking(
        envelope, analysis_id, supabase, feedback_required=True,
    )
                 if item.get("decision_confirmed_at")]
    content = generate_governed_pptx(envelope, analysis_id, decisions,
                                    temporal_comparison=_export_temporal_context(supabase, analysis_id, company_id))
    return Response(content=content,
                    media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    headers={"Content-Disposition": f'attachment; filename="pepperyn_v1_{analysis_id[:8]}.pptx"'})
