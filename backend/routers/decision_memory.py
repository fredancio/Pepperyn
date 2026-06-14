"""
Decision Memory routes — Pepperyn.

GET  /api/decision-feedback/previous — recommandations du dernier rapport
                                        + feedback déjà enregistré (écran
                                        pré-analyse et cartes post-rapport).
POST /api/decision-feedback          — enregistrer l'intention/le retour de
                                        l'utilisateur sur une recommandation.

Aucun appel à Claude ici — lecture/écriture Supabase uniquement.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from routers.analyze import _resolve_auth
from services.decision_memory_service import DecisionMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["decision-memory"])

_decision_memory_service = DecisionMemoryService()

VALID_STATUSES = {
    "planned", "done", "partially_done", "not_done", "rejected", "no_longer_relevant",
}


class DecisionFeedbackRequest(BaseModel):
    report_id: str
    recommendation_id: str
    recommendation_text: str
    recommendation_source: Optional[str] = None
    status: str
    comment: Optional[str] = Field(default=None, max_length=1000)


@router.get("/decision-feedback/previous")
async def get_previous_recommendations(
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Renvoie les recommandations du dernier rapport complété, avec le statut/
    commentaire déjà enregistré pour chacune (ou null si pas encore de
    feedback). Utilisé pour :
      - l'écran "Avant de relancer l'analyse, faisons le point..."
      - les cartes de feedback affichées après un rapport.
    """
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    latest = _decision_memory_service.get_latest_report_with_feedback(company_id)
    if not latest:
        return {"has_previous": False, "report_id": None, "recommendations": []}

    return {
        "has_previous": True,
        "report_id": latest["report_id"],
        "fichier_nom": latest.get("fichier_nom"),
        "created_at": latest.get("created_at"),
        "recommendations": latest["recommendations"],
    }


@router.post("/decision-feedback")
async def submit_decision_feedback(
    request: DecisionFeedbackRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Enregistre (ou met à jour) le feedback de l'utilisateur sur une recommandation."""
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    if request.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status invalide : {request.status}")

    ok = _decision_memory_service.upsert_feedback(
        company_id=company_id,
        report_id=request.report_id,
        recommendation_id=request.recommendation_id,
        recommendation_text=request.recommendation_text,
        recommendation_source=request.recommendation_source,
        status=request.status,
        comment=request.comment,
    )

    if not ok:
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement du feedback")

    return {"success": True}
