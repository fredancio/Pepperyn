"""Non-production HTTP surface for the fixed V1 synthetic Golden Case."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from models.schemas import AnalyzeResponse
import routers.analyze as analyze_routes
from sandbox.v1_golden_case import run_v1_golden_case
from sandbox.governed_exports import generate_governed_excel, generate_governed_pdf, generate_governed_pptx
from services.governed_analysis_persistence import (
    GovernedPersistenceRefused, load_governed_envelope, save_governed_analysis,
)
from services.decision_memory_service import DecisionMemoryService, make_recommendation_id
from sandbox.heterogeneous_workbooks import inspect_registered_workbook, run_registered_mock_analysis
from sandbox.synthetic_product import SandboxRefused

router = APIRouter(prefix="/api/v1", tags=["v1-synthetic"])
logger = logging.getLogger(__name__)


def _recommendations_tracking(
    envelope, analysis_id: str, supabase=None, *, feedback_required: bool = False,
) -> list[dict]:
    """Project governed recommendations into the existing intention UI contract.

    This is deliberately an intention/feedback projection only. It neither
    creates a DecisionKernel nor represents a recommendation as a confirmed
    professional decision.
    """
    priority = {"P1": "haute", "P2": "moyenne", "P3": "basse"}
    items = [
        {
            "id": make_recommendation_id(analysis_id, "plan_action", index),
            "text": item.action,
            "rationale": item.rationale,
            "fact_ids": list(item.fact_ids),
            "prerequisite_validation": list(item.prerequisite_validation),
            "source": "plan_action",
            "priority": priority[item.priority],
            "index": index,
        }
        for index, item in enumerate(envelope.governed_analysis.recommendations)
    ]
    if supabase is None:
        return items
    try:
        rows = (
            supabase.from_("decision_feedback").select(
                "recommendation_id,status,comment,decision_kind,decision_text,"
                "decision_confirmed_at,decision_confirmation_source,prerequisites_acknowledged"
            )
            .eq("report_id", analysis_id).execute()
        ).data or []
    except Exception as exc:
        if feedback_required:
            raise HTTPException(
                status_code=503,
                detail="État décisionnel indisponible : export gouverné refusé.",
            ) from exc
        # The governed analysis is authoritative and already integrity-checked.
        # A secondary feedback-registry outage must not make that analysis
        # disappear. Absence is represented as UNKNOWN; writes remain
        # independently fail-closed in record_v1_governed_intention().
        logger.warning(
            "[V1 INTENTION] feedback state unavailable for analysis=%s: %s",
            analysis_id, exc,
        )
        rows = []
    feedback = {row["recommendation_id"]: row for row in rows}
    for item in items:
        saved = feedback.get(item["id"])
        item["status"] = saved.get("status") if saved else None
        item["comment"] = saved.get("comment") if saved else None
        item["decision_kind"] = saved.get("decision_kind") if saved else None
        item["decision_text"] = saved.get("decision_text") if saved else None
        item["decision_confirmed_at"] = saved.get("decision_confirmed_at") if saved else None
        item["decision_confirmation_source"] = (
            saved.get("decision_confirmation_source") if saved else None
        )
        item["prerequisites_acknowledged"] = (
            saved.get("prerequisites_acknowledged") if saved else None
        )
    return items


class GovernedIntentionRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    status: str
    comment: Optional[str] = Field(default=None, max_length=1000)


class GovernedDecisionRequest(BaseModel):
    recommendation_id: str = Field(min_length=12, max_length=12)
    decision_kind: str
    decision_text: str = Field(min_length=1, max_length=2000)
    prerequisites_acknowledged: bool


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


@router.post("/synthetic-workbook-analysis", response_model=AnalyzeResponse)
async def analyze_v1_synthetic_workbook(
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
        mock = await asyncio.to_thread(run_registered_mock_analysis, raw, file.filename or "")
    except SandboxRefused as exc:
        raise HTTPException(
            status_code=400,
            detail="Analyse simulée refusée : utilisez le classeur synthétique English enregistré.",
        ) from exc

    from main import get_supabase_service
    supabase = get_supabase_service()
    _, entity_id, engagement_id = _resolve_primary_scope(supabase, company_id)
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
        rows = (
            supabase.from_("analyses").select("id,entity_id")
            .eq("id", analysis_id).eq("company_id", company_id).limit(2).execute()
        ).data or []
        if len(rows) != 1 or not rows[0].get("entity_id"):
            raise GovernedPersistenceRefused("GOVERNED_ANALYSIS_NOT_FOUND")
        _, entity_id, engagement_id = analyze_routes._resolve_analysis_entity_scope(
            supabase, company_id=company_id, entity_id=rows[0]["entity_id"],
        )[0]
        return load_governed_envelope(
            supabase, analysis_id=analysis_id, company_id=company_id,
            entity_id=entity_id, engagement_id=engagement_id,
        )
    except (GovernedPersistenceRefused, HTTPException):
        raise HTTPException(status_code=404, detail="Analyse introuvable")


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
    envelope = _load_for_company(supabase, analysis_id=analysis_id, company_id=company_id)
    result = envelope.analysis_result
    result.id = analysis_id
    return AnalyzeResponse(
        success=True, message="Analyse gouvernée rechargée", analyse_id=analysis_id,
        result=result, tokens_used=0, cout_estime=0,
        recommendations_tracking=_recommendations_tracking(envelope, analysis_id, supabase),
    )


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
    content = generate_governed_excel(envelope, analysis_id, decisions)
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
    content = generate_governed_pdf(envelope, analysis_id, decisions)
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
    content = generate_governed_pptx(envelope, analysis_id, decisions)
    return Response(content=content,
                    media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    headers={"Content-Disposition": f'attachment; filename="pepperyn_v1_{analysis_id[:8]}.pptx"'})
