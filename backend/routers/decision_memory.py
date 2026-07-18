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
    "planned",           # Intention ferme : "Je vais appliquer"     → Arc créé
    "unsure",            # Indécision      : "Je ne sais pas encore" → pas d'Arc
    "done",
    "partially_done",
    "not_done",
    "rejected",
    "no_longer_relevant",
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

    # Recalcul des patterns comportementaux (Phase 2) — SQL/Python uniquement,
    # aucun appel Claude. Best-effort : ne bloque pas la réponse si ça échoue.
    try:
        _decision_memory_service.compute_user_patterns(company_id)
    except Exception as e:
        logger.warning(f"[DECISION MEMORY] compute_user_patterns failed: {e}")

    # ── Arc Décisionnel MVP v16 — création d'arc si intention déclarée ────────
    # Source de vérité unique : le backend crée l'arc. Le frontend lit le résultat.
    # Non-bloquant : un échec ici ne doit jamais empêcher le retour du feedback.
    # Reconstruction possible via POST /api/admin/arcs/backfill (idempotent).
    arc_created = False
    arc_id = None
    arc_status = None

    if request.status == "planned":
        try:
            from services.arc_service import arc_service
            arc_result = arc_service.create_arc_from_feedback(
                company_id=company_id,
                origin_analysis_id=request.report_id,
                recommendation_id=request.recommendation_id,
                decision_source=request.recommendation_source or "plan_action",
                recommendation_text=request.recommendation_text,
            )
            arc_created = arc_result.get("created", False)
            arc_id = arc_result.get("arc_id")
            arc_status = arc_result.get("arc_status")
        except ValueError as e:
            # Guard DCT : analyse sans DecisionKernel valide — log et continue
            logger.warning(
                "[ARC] Arc non créé (guard DCT) — company=%s report=%s : %s",
                company_id, request.report_id, e,
            )
        except Exception as e:
            # Erreur inattendue — log structuré + continue (feedback déjà sauvé)
            logger.error(
                "[ARC] Échec création arc — company=%s report=%s recommendation=%s : %s",
                company_id, request.report_id, request.recommendation_id, e,
                exc_info=True,
            )
            # L'arc peut être reconstruit via : POST /api/admin/arcs/backfill?company_id=...
            # Reconstruction sûre car UNIQUE(origin_analysis_id, recommendation_id).

    return {
        "success": True,
        "arc_created": arc_created,
        "arc_id": arc_id,
        "arc_status": arc_status,
    }
