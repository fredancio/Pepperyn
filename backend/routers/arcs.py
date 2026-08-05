"""
Arc Décisionnel routes — Pepperyn MVP v16.

GET  /api/arcs/{arc_id}           — lire un arc et ses liens
POST /api/arcs/{arc_id}/consequence — confirmer/rejeter un lien conséquence
POST /api/arcs/{arc_id}/learning    — valider le learning et fermer l'arc
POST /api/arcs/{arc_id}/abandon     — "Ne plus suivre" (Review Briefing)

GET  /api/review-briefing         — Briefing de revue (Capability 3)
GET  /api/admin/arcs/integrity    — compter les feedbacks sans arc (monitoring)
POST /api/admin/arcs/backfill     — créer les arcs manquants (reconstruction idempotente)
"""
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from models.decision_arc import ArcConsequenceRequest, ArcLearningRequest, ArcAbandonRequest
from routers.analyze import _resolve_auth
from services.arc_service import arc_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["arcs"])


@router.get("/review-briefing")
async def get_review_briefing(
    entity_id: Optional[str] = None,
    limit: int = 5,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Briefing de revue — synthèse opérationnelle des décisions actives d'un
    client, priorisées, avec questions prêtes à poser pendant la revue.

    entity_id optionnel : scope sur le client actuellement sélectionné côté
    frontend (mêmes conventions que GET /api/analyses/history). Sans lui,
    renvoie les arcs actifs de toute la company.

    Périmètre : uniquement les décisions et recommandations suivies via
    DecisionArc — jamais d'échéances comptables, fiscales ou administratives.
    """
    company_id, _plan, _auth_type = await _resolve_auth(authorization, x_auth_type)
    items = arc_service.build_review_briefing(
        company_id=company_id,
        entity_id=entity_id,
        limit=min(limit, 5) if limit else 5,
    )
    return {"items": items}


@router.post("/arcs/{arc_id}/abandon")
async def abandon_arc(
    arc_id: str,
    request: ArcAbandonRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    "Ne plus suivre" — retire un arc du Briefing de revue actif.

    RÈGLE SÉMANTIQUE : ne signifie jamais que le sujet est réglé, résolu ou
    exécuté — uniquement que le suivi s'arrête. L'arc n'est jamais supprimé ;
    historique et liens (arc_analysis_links) restent intacts.
    """
    company_id, _plan, _auth_type = await _resolve_auth(authorization, x_auth_type)

    try:
        result = arc_service.abandon_arc(
            arc_id=arc_id,
            company_id=company_id,
            reason=request.reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("[ARC] abandon_arc route — arc_id=%s : %s", arc_id, e)
        raise HTTPException(
            status_code=500, detail="Erreur lors du retrait du briefing actif."
        )


@router.get("/arcs/{arc_id}")
async def get_arc(
    arc_id: str,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """Retourne un arc et ses liens d'analyse."""
    company_id, _plan, _auth_type = await _resolve_auth(authorization, x_auth_type)

    try:
        from main import get_supabase_service
        supabase = get_supabase_service()
        result = (
            supabase.from_("decision_arcs")
            .select("*, arc_analysis_links(*)")
            .eq("id", arc_id)
            .eq("company_id", company_id)  # contrôle d'accès
            .single()
            .execute()
        )
    except Exception as e:
        logger.error("[ARC] get_arc — %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la lecture de l'arc.")

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Arc {arc_id} introuvable.")

    return result.data


@router.post("/arcs/{arc_id}/consequence")
async def confirm_consequence(
    arc_id: str,
    request: ArcConsequenceRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Confirme ou rejette un lien conséquence candidate.

    Si confirmé : arc → CONSEQUENCES_LINKED → LEARNING_PROPOSED (automatique).
    Si rejeté   : lien marqué rejected, arc reste en EXECUTION.

    RÈGLE : refuser un lien ≠ abandonner l'arc.
    """
    await _resolve_auth(authorization, x_auth_type)

    try:
        result = arc_service.confirm_consequence_link(
            arc_id=arc_id,
            analysis_id=request.analysis_id,
            confirmed=request.confirmed,
            rejection_reason=request.rejection_reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("[ARC] confirm_consequence — arc_id=%s : %s", arc_id, e)
        raise HTTPException(status_code=500, detail="Erreur lors de la confirmation du lien.")


@router.post("/arcs/{arc_id}/learning")
async def validate_learning(
    arc_id: str,
    request: ArcLearningRequest,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Valide le learning et ferme l'arc (CLOSED).

    GUARD : decision_text IS NOT NULL requis pour CLOSED.
    Si decision_text est NULL et non fourni dans la requête → HTTP 422.

    Si decision_text fourni : confirmation rétrospective → decision_confirmation_source='explicit'.
    """
    await _resolve_auth(authorization, x_auth_type)

    if request.action not in ("validate", "modify"):
        raise HTTPException(
            status_code=400,
            detail="action doit être 'validate' ou 'modify'."
        )

    learning_text = request.learning_text or ""

    try:
        result = arc_service.validate_learning(
            arc_id=arc_id,
            learning_text=learning_text,
            decision_text=request.decision_text,
        )
        return result
    except ValueError as e:
        # Guard decision_text IS NOT NULL
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("[ARC] validate_learning — arc_id=%s : %s", arc_id, e)
        raise HTTPException(
            status_code=500, detail="Erreur lors de la validation du learning."
        )


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/arcs/integrity")
async def arc_integrity(
    company_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Compte les decision_feedback 'planned' sans arc correspondant.
    Utilisé pour le monitoring de la santé du système d'arcs.
    """
    await _resolve_auth(authorization, x_auth_type)
    return arc_service.count_missing_arcs(company_id=company_id)


@router.post("/admin/arcs/backfill")
async def backfill_arcs(
    company_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Crée les arcs manquants depuis decision_feedback 'planned'.
    Idempotent — peut être relancé sans effet de bord.
    """
    await _resolve_auth(authorization, x_auth_type)
    result = arc_service.backfill_missing_arcs(company_id=company_id)
    return result
