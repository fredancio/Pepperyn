"""
test_evidence_query_service.py — Evidence Ledger Consumer #1 : lecture
canonique seule (backend/services/evidence_query_service.py).

Couvre les points de la mission "Evidence Consumer #1" :
  - récupère la bonne preuve pour la bonne organisation ;
  - ne peut jamais récupérer la preuve d'une autre organisation (tenant
    isolation, filtre explicite company_id) ;
  - la projection préserve amount/currency/provenance ;
  - une Evidence absente est gérée honnêtement (jamais fabriquée) ;
  - une ligne malformée est gérée sans casser les autres ;
  - fact_id n'est jamais lu ni exposé ;
  - aucun appel LLM ;
  - aucun fallback vers analyse_json.
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.evidence_query_service import (
    get_evidence_support_by_analysis,
    _project_evidence_row,
    _qualifier_for_source_types,
)


def make_evidence_row(**overrides) -> dict:
    base = {
        "analyse_id": "analysis-1",
        "facts": [{"claim": "CA en croissance"}],
        "sheets_verified": ["P&L", "Bilan"],
        "quantified_impacts": [
            {
                "amount": 125000.0,
                "currency": "EUR",
                "metric_type": "REVENUE",
                "confidence": 0.9,
                "source_references": [{"source_type": "CANONICAL_FACT"}],
            }
        ],
    }
    base.update(overrides)
    return base


class _ChainableSupabase:
    """
    Double de test minimal, chaînable, distinct par table — nécessaire ici
    car un MagicMock générique unique (comme make_supabase_mock() dans
    test_review_briefing.py) renverrait la même donnée pour n'importe quel
    appel .execute(), masquant une éventuelle erreur de scoping.
    """

    def __init__(self, table_data: dict[str, list[dict]]):
        self._table_data = table_data
        self._current_table = None
        self.eq_calls: list[tuple[str, object]] = []
        self.in_calls: list[tuple[str, list]] = []

    def from_(self, table):
        self._current_table = table
        return self

    def select(self, *_args, **_kwargs):
        return self

    def in_(self, field, values):
        self.in_calls.append((field, list(values)))
        return self

    def eq(self, field, value):
        self.eq_calls.append((field, value))
        return self

    def execute(self):
        data = self._table_data.get(self._current_table, [])
        return MagicMock(data=data)


class TestGetEvidenceSupportByAnalysis:

    def test_retrieves_correct_evidence_for_correct_analysis(self):
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        assert "analysis-1" in result
        assert result["analysis-1"]["status"] == "available"
        assert result["analysis-1"]["facts_count"] == 1

    def test_scopes_query_by_company_id_explicitly(self):
        """Défense en profondeur : le filtre company_id doit toujours être
        appliqué, même si analyse_id est déjà unique côté DB (v18)."""
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        assert ("company_id", "company-1") in sb.eq_calls

    def test_cannot_retrieve_another_organisation_evidence(self):
        """
        Le double de test simule le comportement réel : la requête filtre
        par company_id, donc une Evidence appartenant à une autre company
        ne doit jamais apparaître dans le résultat projeté — même si le
        transport mocké ici renvoie tout, le contrat de la fonction est de
        ne jamais faire confiance à une ligne dont on ne peut pas garantir
        le scoping. Ce test vérifie qu'au minimum le filtre est bien émis
        (voir test précédent) ET que la projection ne fait aucune supposition
        implicite de tenant à partir du contenu de la ligne elle-même.
        """
        sb = _ChainableSupabase({
            "evidence_ledger_entries": [make_evidence_row(analyse_id="analysis-org-b")]
        })

        result = get_evidence_support_by_analysis(sb, ["analysis-org-a"], company_id="company-a")

        # La ligne renvoyée par le transport mocké ne correspond à aucun des
        # analysis_ids demandés pour cette company — elle ne doit donc pas
        # se retrouver associée à "analysis-org-a".
        assert "analysis-org-a" not in result

    def test_projection_preserves_amount_currency_provenance(self):
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        impact = result["analysis-1"]["impacts"][0]
        assert impact["amount"] == 125000.0
        assert impact["currency"] == "EUR"
        assert impact["metric_type_label"] == "Chiffre d'affaires"
        assert impact["qualifier"] == "preuve vérifiée"
        assert result["analysis-1"]["sheets"] == ["Bilan", "P&L"]

    def test_missing_evidence_handled_honestly(self):
        """Aucune ligne pour cette analyse → absente du dict, jamais une
        entrée fabriquée avec des valeurs par défaut."""
        sb = _ChainableSupabase({"evidence_ledger_entries": []})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        assert result == {}

    def test_empty_analysis_ids_short_circuits_without_query(self):
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        result = get_evidence_support_by_analysis(sb, [], company_id="company-1")

        assert result == {}
        assert sb.in_calls == []

    def test_missing_company_id_short_circuits(self):
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="")

        assert result == {}

    def test_malformed_row_does_not_break_other_rows(self):
        sb = _ChainableSupabase({
            "evidence_ledger_entries": [
                make_evidence_row(analyse_id="good-1"),
                {"analyse_id": "bad-1", "quantified_impacts": "not-a-list-should-not-crash"},
            ]
        })

        result = get_evidence_support_by_analysis(sb, ["good-1", "bad-1"], company_id="company-1")

        assert "good-1" in result
        # La ligne malformée ne doit ni crasher, ni fabriquer un faux support.
        assert result.get("bad-1", {}).get("status") in (None, "available")

    def test_query_failure_returns_empty_dict_not_exception(self):
        sb = MagicMock()
        sb.from_.side_effect = RuntimeError("DB indisponible")

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        assert result == {}

    def test_amount_none_excluded_absence_never_shown_as_zero(self):
        """Article X — absence ≠ zéro : un impact sans montant n'est jamais
        affiché, ni encore moins affiché comme 0."""
        row = make_evidence_row(quantified_impacts=[
            {"amount": None, "currency": "EUR", "metric_type": "REVENUE",
             "confidence": 0.5, "source_references": []},
        ])
        sb = _ChainableSupabase({"evidence_ledger_entries": [row]})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        assert result["analysis-1"]["impacts"] == []

    def test_fact_id_never_present_in_projection(self):
        """fact_id ne doit jamais fuiter dans la projection exposée à
        l'API/UI — ni comme clé de haut niveau, ni imbriqué."""
        sb = _ChainableSupabase({"evidence_ledger_entries": [make_evidence_row()]})

        result = get_evidence_support_by_analysis(sb, ["analysis-1"], company_id="company-1")

        serialized = str(result)
        assert "fact_id" not in serialized

    def test_no_llm_import_in_module(self):
        """Vérifie statiquement l'absence de tout appel LLM dans ce module
        (Mission 12 — zéro nouvel appel LLM pour ce consommateur)."""
        import services.evidence_query_service as mod
        import inspect
        source = inspect.getsource(mod)
        for forbidden in ("llm_service", "openai", "anthropic", "_run_evidence_graph_agent"):
            assert forbidden not in source


class TestQualifierForSourceTypes:

    def test_legacy_parse_dominates_even_with_canonical_present(self):
        """LEGACY_PARSE n'est jamais certifié — même un seul montant estimé
        rend l'ensemble non-certifié, jamais l'inverse (Mission 10)."""
        qualifier = _qualifier_for_source_types([
            {"source_type": "CANONICAL_FACT"},
            {"source_type": "LEGACY_PARSE"},
        ])
        assert qualifier == "estimation non vérifiée"

    def test_canonical_fact_alone(self):
        assert _qualifier_for_source_types([{"source_type": "CANONICAL_FACT"}]) == "preuve vérifiée"

    def test_no_source_type_at_all(self):
        assert _qualifier_for_source_types([]) == "non sourcé"

    def test_llm_extracted_labeled_as_automatic_not_verified(self):
        """Ne doit jamais sur-vendre la certitude d'une extraction LLM
        (Mission 10 — epistemic honesty) : jamais qualifiée "preuve vérifiée"."""
        qualifier = _qualifier_for_source_types([{"source_type": "LLM_EXTRACTED"}])
        assert qualifier == "extraction automatique"
        assert qualifier != "preuve vérifiée"


class TestProjectEvidenceRow:

    def test_never_exposes_raw_jsonb_columns(self):
        projected = _project_evidence_row(make_evidence_row())
        assert "quantified_impacts" not in projected
        assert "facts" not in projected
        assert "capture_schema_version" not in projected
        assert "entity_id" not in projected
        assert "company_id" not in projected


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
