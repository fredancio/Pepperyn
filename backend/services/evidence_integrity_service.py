"""
evidence_integrity_service.py — Persistence Integrity Gate (Evidence Ledger
Consumer #1, Mission 14).

T1C-A accepted non-blocking Evidence persistence
(services/evidence_ledger_service.py:save_evidence_capture — try/except,
log, never raise) ONLY because evidence_ledger_entries had zero real
consumers (ADR-001 §8). Review Briefing becoming a real consumer ends that
justification: Evidence loss must no longer be silent.

Chosen minimal strategy (Mission 14, option C — "another existing
repository-native reliability pattern", no new infrastructure): mirror the
integrity/count pattern already established for Decision Arcs
(ArcService.count_missing_arcs, GET /api/admin/arcs/integrity) rather than
introducing blocking writes, retries, or an outbox. Blocking the Evidence
write would make analysis creation itself depend on Evidence Ledger
availability — disproportionate for what remains an enhancement feature,
not yet a hard requirement (Review Briefing degrades honestly when Evidence
is absent, per Mission 8).

This module does NOT fix silent failures — it makes them observable and
countable, which is the realistic minimum this mission asked for. Turning
this signal into an alert/dashboard is future operational work, not part
of this increment.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def count_missing_evidence(supabase: Any, company_id: Optional[str] = None) -> dict:
    """
    Compte les analyses sans ligne evidence_ledger_entries correspondante.

    Signal d'observabilité AGRÉGÉ, jamais une classification par ligne :
    ne distingue pas analyse pré-Ledger / capture vide légitime / échec
    d'écriture — structurellement indiscernables depuis ces seules données
    (voir docs/Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md, gap nommé). Sert
    à détecter une régression d'écriture silencieuse via l'évolution de ce
    compteur dans le temps (ex. pic après un déploiement) — pas à
    diagnostiquer un cas individuel.

    Lecture seule : ne crée, ne corrige, ne backfill jamais aucune Evidence
    manquante — contrairement à /api/admin/arcs/backfill, qui a un
    équivalent en écriture pour les arcs. Un backfill Evidence depuis
    analyse_json inventerait une preuve que le pipeline T1C-A/T1C-B n'a
    jamais réellement produite (Mission 16 — hors périmètre).

    Returns:
        {"total_analyses": int, "with_evidence": int, "without_evidence": int}
        ou la même forme avec une clé "error" en cas d'échec de lecture
        (jamais d'exception levée — enrichissement de monitoring, ne doit
        jamais casser l'appelant).
    """
    try:
        analyses_query = supabase.from_("analyses").select("id")
        if company_id:
            analyses_query = analyses_query.eq("company_id", company_id)
        analyses_result = analyses_query.execute()
        analysis_ids = [
            a.get("id") for a in (analyses_result.data or [])
            if isinstance(a, dict) and a.get("id")
        ]

        if not analysis_ids:
            return {"total_analyses": 0, "with_evidence": 0, "without_evidence": 0}

        evidence_query = (
            supabase.from_("evidence_ledger_entries")
            .select("analyse_id")
            .in_("analyse_id", analysis_ids)
        )
        if company_id:
            evidence_query = evidence_query.eq("company_id", company_id)
        evidence_result = evidence_query.execute()
        analyses_with_evidence = {
            r.get("analyse_id") for r in (evidence_result.data or [])
            if isinstance(r, dict) and r.get("analyse_id")
        }

        total = len(analysis_ids)
        with_evidence = len({a for a in analysis_ids if a in analyses_with_evidence})
        return {
            "total_analyses": total,
            "with_evidence": with_evidence,
            "without_evidence": total - with_evidence,
        }
    except Exception as e:
        logger.error(
            "[EVIDENCE INTEGRITY] count_missing_evidence failed — %s: %s",
            type(e).__name__, e,
        )
        return {"total_analyses": 0, "with_evidence": 0, "without_evidence": 0, "error": str(e)}
