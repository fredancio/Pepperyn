"""Non-production HTTP surface for the fixed V1 synthetic Golden Case."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from models.schemas import AnalyzeResponse
import routers.analyze as analyze_routes
from sandbox.v1_golden_case import run_v1_golden_case
from services.governed_analysis_persistence import (
    GovernedPersistenceRefused, load_governed_envelope, save_governed_analysis,
)

router = APIRouter(prefix="/api/v1", tags=["v1-synthetic"])


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
            "type_document": result.type_document, "contexte_utilisateur": "",
            "mode": "V1_SYNTHETIC_GOLDEN", "analyse_json": result.model_dump(mode="json"),
            "score_confiance": 0, "tokens_input": 0, "cout_estime_euros": 0,
            "duree_traitement_ms": 0, "status": "completed", "chat_count": 0,
            "source_data_hash": golden.source_workbook_sha256.lower(),
        }, engagement_id=engagement_id, envelope=golden.envelope,
    )
    return AnalyzeResponse(
        success=True, message="Démonstration V1 synthétique terminée",
        analyse_id=analysis_id, result=result, tokens_used=0, cout_estime=0,
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
        rows = (
            supabase.from_("analyses").select("id,entity_id")
            .eq("id", analysis_id).eq("company_id", company_id).limit(2).execute()
        ).data or []
        if len(rows) != 1 or not rows[0].get("entity_id"):
            raise GovernedPersistenceRefused("GOVERNED_ANALYSIS_NOT_FOUND")
        _, entity_id, engagement_id = analyze_routes._resolve_analysis_entity_scope(
            supabase, company_id=company_id, entity_id=rows[0]["entity_id"],
        )[0]
        envelope = load_governed_envelope(
            supabase, analysis_id=analysis_id, company_id=company_id,
            entity_id=entity_id, engagement_id=engagement_id,
        )
    except (GovernedPersistenceRefused, HTTPException):
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    result = envelope.analysis_result
    result.id = analysis_id
    return AnalyzeResponse(
        success=True, message="Analyse gouvernée rechargée", analyse_id=analysis_id,
        result=result, tokens_used=0, cout_estime=0,
    )
