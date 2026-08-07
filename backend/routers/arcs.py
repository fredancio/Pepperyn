"""
Arc Décisionnel routes — Pepperyn MVP v16.

GET  /api/arcs/{arc_id}           — lire un arc et ses liens
POST /api/arcs/{arc_id}/consequence — confirmer/rejeter un lien conséquence
POST /api/arcs/{arc_id}/learning    — valider le learning et fermer l'arc
POST /api/arcs/{arc_id}/abandon     — "Ne plus suivre" (Review Briefing)

GET  /api/review-briefing         — Briefing de revue (Capability 3)
GET  /api/portfolio                — Portfolio Intelligence, Incrément 1 (Capability 7)
GET  /api/admin/arcs/integrity    — compter les feedbacks sans arc (monitoring)
POST /api/admin/arcs/backfill     — créer les arcs manquants (reconstruction idempotente)
GET  /api/admin/evidence/integrity — compter les analyses sans Evidence Ledger (monitoring,
                                      Evidence Consumer #1 — observabilité de persistance,
                                      pas une garantie d'intégrité, voir
                                      services/evidence_integrity_service.py)
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
    # Borné littéralement à [0, 5] — corrige le même piège que Mission 5
    # (Incrément 2 Portfolio) à ce niveau : `limit=0` demandé explicitement
    # doit renvoyer zéro résultat, jamais retomber sur la valeur par défaut
    # (l'ancien `if limit else 5` traitait 0 comme "non fourni", 0 étant
    # falsy en Python).
    items = arc_service.build_review_briefing(
        company_id=company_id,
        entity_id=entity_id,
        limit=max(0, min(limit, 5)),
    )
    return {"items": items}


@router.get("/portfolio")
async def get_portfolio(
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Portfolio Intelligence (Incrément 1, Capability 7) — une carte par
    client, triée par priorité, portant son point le plus prioritaire du
    Briefing de revue.

    Regroupement pur du Briefing de revue existant — aucune nouvelle donnée,
    aucun nouveau calcul.

    Périmètre Incrément 1 (voir PORTFOLIO_HOME_IMPLEMENTATION_PLAN.md) :
    nom du client + titre du point prioritaire + action "Préparer cette
    revue" seulement. why_it_matters / temporal_context / compteur sont
    prévus pour l'Incrément 2 — déjà présents sur chaque carte (via
    top_item) mais volontairement non affichés côté frontend avant.
    """
    company_id, _plan, _auth_type = await _resolve_auth(authorization, x_auth_type)
    cards = arc_service.build_portfolio_briefing(company_id=company_id)
    return {"cards": cards}


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


@router.get("/admin/evidence/integrity")
async def evidence_integrity(
    company_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Persistence Observability (Evidence Ledger Consumer #1) — compte les
    analyses sans ligne evidence_ledger_entries correspondante.

    Correction post-revue adversariale : ce endpoint n'est PAS une garantie
    d'intégrité ("gate") — il ne bloque rien, ne corrige rien, ne rattrape
    rien. C'est un signal d'observabilité agrégé, PAS une classification par
    ligne : ne distingue jamais analyse pré-Ledger / capture vide légitime /
    échec d'écriture (structurellement indiscernables depuis cette seule
    table — voir docs/Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md, gap
    "Evidence Capture Outcome Semantics"). Sert à détecter une régression
    d'écriture silencieuse via l'évolution de ce compteur dans le temps
    (ex. pic après un déploiement), pas à diagnostiquer un cas individuel.
    Même pattern que /api/admin/arcs/integrity — aucune nouvelle
    infrastructure.

    Ne crée jamais d'Evidence manquante — lecture seule, contrairement à
    /api/admin/arcs/backfill qui a un équivalent en écriture. Un backfill
    Evidence depuis analyse_json inventerait une preuve que le pipeline
    T1C-A/T1C-B n'a jamais produite — explicitement hors périmètre.
    """
    await _resolve_auth(authorization, x_auth_type)
    from main import get_supabase_service
    from services.evidence_integrity_service import count_missing_evidence

    supabase = get_supabase_service()
    return count_missing_evidence(supabase=supabase, company_id=company_id)
