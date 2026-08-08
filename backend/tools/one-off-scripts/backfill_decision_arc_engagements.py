"""
backfill_decision_arc_engagements.py — script d'exécution unique
(mission DecisionArc ↔ Engagement, 2026-08-07).

Exécute une seule fois services.arc_service.arc_service.backfill_decision_arc_engagements()
contre la base réelle, pour rattacher engagement_id aux DecisionArc déjà
existants avant cette migration (v21_decision_arc_engagement.sql doit être
appliquée avant d'exécuter ce script).

Idempotent par construction (voir ArcService.backfill_decision_arc_engagements) :
peut être relancé sans risque si une exécution précédente a été interrompue —
un arc portant déjà engagement_id n'est jamais relu ni recalculé.

Prérequis : migration v21_decision_arc_engagement.sql appliquée (colonne
engagement_id + carve-out d'immutabilité pour les arcs CLOSED).

Comme backfill_engagements_t2a.py (T2A), ce script doit être déplacé vers
tools/archive/one-off-scripts/ une fois son exécution confirmée — il ne fait
pas partie de l'outillage réutilisable du produit.

Usage :
    python backend/tools/one-off-scripts/backfill_decision_arc_engagements.py
"""
from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from main import get_supabase_service
    from services.arc_service import arc_service

    arc_service._supabase = get_supabase_service()

    logger.info("[BACKFILL DECISIONARC-ENGAGEMENT] Démarrage du backfill...")
    stats = arc_service.backfill_decision_arc_engagements()
    logger.info(
        "[BACKFILL DECISIONARC-ENGAGEMENT] Terminé — résolus=%s, non-résolus=%s, "
        "déjà présents=%s, erreurs=%s",
        stats.get("resolved", 0),
        stats.get("unresolved", 0),
        stats.get("already_present", 0),
        stats.get("errors", 0),
    )

    if stats.get("unresolved", 0) > 0:
        logger.info(
            "[BACKFILL DECISIONARC-ENGAGEMENT] %s arc(s) restent non résolus "
            "(entity_id absent sur l'analyse d'origine, ou Entity sans "
            "Engagement) — engagement_id reste NULL pour ceux-ci, "
            "conformément à la règle 'jamais deviné'. Pas une erreur.",
            stats["unresolved"],
        )

    if stats.get("errors", 0) > 0:
        logger.error(
            "[BACKFILL DECISIONARC-ENGAGEMENT] %s erreur(s) rencontrée(s) — "
            "voir les logs ci-dessus pour le détail par arc_id. Le script "
            "peut être relancé sans risque (idempotent).", stats["errors"],
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
