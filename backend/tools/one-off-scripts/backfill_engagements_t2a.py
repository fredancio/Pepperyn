"""
backfill_engagements_t2a.py — script d'exécution unique (T2A, ADR-002).

Exécute une seule fois services.engagement_service.backfill_engagements()
contre la base réelle, pour créer les Engagements des Entities déjà
existantes avant l'introduction de l'agrégat (T2A_Implementation_Plan.md §4).

Idempotent par construction (voir engagement_service.backfill_engagements) :
peut être relancé sans risque si une exécution précédente a été interrompue.

À exécuter une seule fois, en conditions réelles, après que la migration
v19_engagements.sql a été appliquée. Comme les 12 scripts de déploiement
ponctuel archivés lors du Sprint 0 (tools/archive/one-off-scripts/), ce
script doit être déplacé vers cette même archive une fois son exécution
confirmée — il ne fait pas partie de l'outillage réutilisable du produit.

Usage :
    python backend/tools/one-off-scripts/backfill_engagements_t2a.py
"""
from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from main import get_supabase_service
    from services.engagement_service import backfill_engagements

    supabase = get_supabase_service()

    logger.info("[BACKFILL T2A] Démarrage du backfill des Engagements...")
    stats = backfill_engagements(supabase)
    logger.info(
        "[BACKFILL T2A] Terminé — créés=%s, déjà présents=%s, erreurs=%s",
        stats.get("created", 0),
        stats.get("already_present", 0),
        stats.get("errors", 0),
    )

    if stats.get("errors", 0) > 0:
        logger.error(
            "[BACKFILL T2A] %s erreur(s) rencontrée(s) — voir les logs "
            "ci-dessus pour le détail par entity_id. Le script peut être "
            "relancé sans risque (idempotent).", stats["errors"],
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
