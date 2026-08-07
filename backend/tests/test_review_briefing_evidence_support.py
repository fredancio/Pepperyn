"""
test_review_briefing_evidence_support.py — Evidence Ledger Consumer #1 :
intégration ArcService.build_review_briefing() ↔ evidence_query_service.

Couvre :
  - un BriefingItem dont l'analyse d'origine a une capture Evidence reçoit
    evidence_support ;
  - un BriefingItem sans capture Evidence reçoit evidence_support=None,
    jamais une valeur fabriquée ;
  - aucun fallback vers analyse_json pour cette capacité ;
  - le comportement existant du Briefing de revue (tri, filtre abandoned,
    structure) reste intact — non-régression sur test_review_briefing.py ;
  - un échec de la recherche Evidence ne casse jamais le Briefing.

Double de test distinct par table (comme test_evidence_query_service.py) —
délibérément PAS le MagicMock générique unique de test_review_briefing.py,
qui masquerait un mélange accidentel entre les deux requêtes
(decision_arcs vs evidence_ledger_entries).
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class _ChainableSupabase:
    def __init__(self, table_data: dict[str, list[dict]]):
        self._table_data = table_data
        self._current_table = None

    def from_(self, table):
        self._current_table = table
        return self

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def neq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return MagicMock(data=self._table_data.get(self._current_table, []))


def make_arc(**overrides) -> dict:
    base = {
        "id": "arc-1",
        "status": "execution",
        "execution_status": "in_progress",
        "recommendation_text": "Renégocier le contrat d'assurance flotte.",
        "decision_text": None,
        "execution_notes": None,
        "learning_text": None,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "decision_confirmed_at": "2026-06-01T00:00:00Z",
        "execution_updated_at": None,
        "closed_at": None,
        "entity_id": None,
        "origin_analysis_id": "analysis-1",
    }
    base.update(overrides)
    return base


def make_evidence_row(**overrides) -> dict:
    base = {
        "analyse_id": "analysis-1",
        "facts": [{"claim": "CA en croissance"}],
        "sheets_verified": ["P&L"],
        "quantified_impacts": [
            {
                "amount": 50000.0,
                "currency": "EUR",
                "metric_type": "REVENUE",
                "confidence": 0.8,
                "source_references": [{"source_type": "CANONICAL_FACT"}],
            }
        ],
    }
    base.update(overrides)
    return base


def make_service(supabase):
    from services.arc_service import ArcService
    svc = ArcService()
    svc._supabase = supabase
    return svc


class TestEvidenceSupportAttachment:

    def test_item_with_ledger_backed_analysis_gets_evidence_support(self):
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1", origin_analysis_id="analysis-1")],
            "evidence_ledger_entries": [make_evidence_row(analyse_id="analysis-1")],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["evidence_support"] is not None
        assert items[0]["evidence_support"]["status"] == "available"
        assert items[0]["evidence_support"]["impacts"][0]["amount"] == 50000.0

    def test_item_without_ledger_row_gets_none_never_fabricated(self):
        """Analyse sans capture Evidence (pré-Ledger, capture vide, ou
        échec d'écriture — indiscernables ici) → evidence_support=None,
        jamais une valeur inventée."""
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1", origin_analysis_id="analysis-no-evidence")],
            "evidence_ledger_entries": [],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["evidence_support"] is None

    def test_arc_without_origin_analysis_id_gets_none(self):
        """Ancien arc sans origin_analysis_id (ne devrait pas arriver vu la
        contrainte NOT NULL de v16, mais défense en profondeur côté lecture)."""
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1", origin_analysis_id=None)],
            "evidence_ledger_entries": [make_evidence_row(analyse_id="analysis-1")],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["evidence_support"] is None

    def test_internal_origin_analysis_id_key_never_leaks_to_final_item(self):
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1")],
            "evidence_ledger_entries": [make_evidence_row()],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert "_origin_analysis_id" not in items[0]

    def test_no_analyse_json_fallback_for_evidence_support(self):
        """
        Règle fondamentale de la mission : si le Ledger ne supporte pas
        l'information, on ne va JAMAIS la chercher dans analyses.analyse_json.
        Vérifié ici en confirmant qu'aucune requête n'est faite sur la
        table `analyses` pendant l'attachement de la preuve.
        """
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1", origin_analysis_id="analysis-1")],
            "evidence_ledger_entries": [],
        })
        queried_tables = []
        original_from_ = sb.from_

        def tracking_from_(table):
            queried_tables.append(table)
            return original_from_(table)
        sb.from_ = tracking_from_

        svc = make_service(sb)
        svc.build_review_briefing(company_id="company-1")

        assert "analyses" not in queried_tables

    def test_evidence_lookup_failure_does_not_break_briefing(self):
        """Un échec de la recherche Evidence est un enrichissement raté,
        jamais un blocage du Briefing de revue (même discipline que le
        reste du composant — échec silencieux, jamais de crash)."""
        sb = _ChainableSupabase({
            "decision_arcs": [make_arc(id="arc-1")],
        })

        def broken_from_(table):
            if table == "evidence_ledger_entries":
                raise RuntimeError("DB indisponible")
            sb._current_table = table
            return sb
        sb.from_ = broken_from_

        svc = make_service(sb)
        items = svc.build_review_briefing(company_id="company-1")

        assert len(items) == 1
        assert items[0]["evidence_support"] is None

    def test_multiple_items_batched_in_single_evidence_query(self):
        """Une seule requête batch pour tous les items, pas N requêtes —
        vérifié indirectement par la présence correcte du support pour
        chaque item distinct."""
        sb = _ChainableSupabase({
            "decision_arcs": [
                make_arc(id="arc-1", origin_analysis_id="analysis-1"),
                make_arc(id="arc-2", origin_analysis_id="analysis-2"),
            ],
            "evidence_ledger_entries": [
                make_evidence_row(analyse_id="analysis-1"),
                make_evidence_row(analyse_id="analysis-2", quantified_impacts=[]),
            ],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")
        by_id = {i["arc_id"]: i for i in items}

        assert by_id["arc-1"]["evidence_support"]["impacts"][0]["amount"] == 50000.0
        assert by_id["arc-2"]["evidence_support"]["impacts"] == []


class TestExistingBehaviorUnaffected:
    """Non-régression — même structure/tri/filtre qu'avant l'ajout
    d'evidence_support (miroir des tests existants de test_review_briefing.py
    avec le nouveau double de test)."""

    def test_excludes_abandoned_arcs(self):
        sb = _ChainableSupabase({
            "decision_arcs": [
                make_arc(id="arc-active", status="execution"),
                make_arc(id="arc-abandoned", status="abandoned"),
            ],
            "evidence_ledger_entries": [],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert len(items) == 1
        assert items[0]["arc_id"] == "arc-active"

    def test_priority_order_preserved(self):
        sb = _ChainableSupabase({
            "decision_arcs": [
                make_arc(id="arc-done", status="consequences_linked"),
                make_arc(id="arc-urgent", status="intention", created_at="2020-01-01T00:00:00Z"),
            ],
            "evidence_ledger_entries": [],
        })
        svc = make_service(sb)

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["priority"] == "urgent"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
