"""
test_evidence_integrity_service.py — Persistence Integrity Gate
(backend/services/evidence_integrity_service.py, Mission 14).

Couvre :
  - comptage correct total / avec preuve / sans preuve ;
  - scoping par company_id quand fourni ;
  - aucun crash sur base vide ;
  - échec de lecture retourne une forme sûre, jamais une exception ;
  - ne crée, ne modifie, n'insère jamais aucune ligne (lecture pure).
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.evidence_integrity_service import count_missing_evidence


class _ChainableSupabase:
    def __init__(self, table_data: dict[str, list[dict]]):
        self._table_data = table_data
        self._current_table = None
        self.write_calls: list[str] = []

    def from_(self, table):
        self._current_table = table
        return self

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def insert(self, *_args, **_kwargs):
        self.write_calls.append(f"insert:{self._current_table}")
        return self

    def update(self, *_args, **_kwargs):
        self.write_calls.append(f"update:{self._current_table}")
        return self

    def execute(self):
        return MagicMock(data=self._table_data.get(self._current_table, []))


class TestCountMissingEvidence:

    def test_counts_total_with_and_without_evidence(self):
        sb = _ChainableSupabase({
            "analyses": [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}],
            "evidence_ledger_entries": [{"analyse_id": "a1"}],
        })

        result = count_missing_evidence(sb)

        assert result == {"total_analyses": 3, "with_evidence": 1, "without_evidence": 2}

    def test_empty_database_returns_zeroes_no_crash(self):
        sb = _ChainableSupabase({"analyses": [], "evidence_ledger_entries": []})

        result = count_missing_evidence(sb)

        assert result == {"total_analyses": 0, "with_evidence": 0, "without_evidence": 0}

    def test_all_analyses_have_evidence(self):
        sb = _ChainableSupabase({
            "analyses": [{"id": "a1"}, {"id": "a2"}],
            "evidence_ledger_entries": [{"analyse_id": "a1"}, {"analyse_id": "a2"}],
        })

        result = count_missing_evidence(sb)

        assert result["without_evidence"] == 0

    def test_query_failure_returns_safe_shape_not_exception(self):
        sb = MagicMock()
        sb.from_.side_effect = RuntimeError("DB indisponible")

        result = count_missing_evidence(sb)

        assert result["total_analyses"] == 0
        assert "error" in result

    def test_never_performs_a_write(self):
        """Lecture pure — jamais d'insert/update, contrairement à
        /api/admin/arcs/backfill qui a un équivalent en écriture pour les arcs."""
        sb = _ChainableSupabase({
            "analyses": [{"id": "a1"}],
            "evidence_ledger_entries": [],
        })

        count_missing_evidence(sb)

        assert sb.write_calls == []

    def test_company_id_scoping_applied_when_provided(self):
        eq_calls = []
        sb = _ChainableSupabase({
            "analyses": [{"id": "a1"}],
            "evidence_ledger_entries": [],
        })
        original_eq = sb.eq

        def tracking_eq(field, value):
            eq_calls.append((field, value))
            return original_eq(field, value)
        sb.eq = tracking_eq

        count_missing_evidence(sb, company_id="company-1")

        assert ("company_id", "company-1") in eq_calls


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
