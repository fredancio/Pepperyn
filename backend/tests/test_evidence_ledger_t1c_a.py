"""
test_evidence_ledger_t1c_a.py — Tests T1C-A : capture + persistance Evidence Ledger.

Périmètre couvert (T1C-A uniquement — ADR-001, ADR-001A) :
  - services/evidence_capture.py : pur, sans I/O. Vérifie que rien n'est
    inventé (UNKNOWN ≠ 0), que la fuite documentée en T1B (quantified_impact
    perdu avant AnalysisResult) est bien contournée, et que la capture ne
    plante jamais sur une entrée malformée ou vide.
  - services/evidence_ledger_service.py : persistance non-bloquante, mockée
    (aucune connexion réseau réelle — Supabase est en pause au moment de ce
    commit, cf. mémoire Phase 1B).

RÈGLE ABSOLUE de ces tests : ne vérifient PAS le comportement de production
existant (schemas.py / AnalysisResult / exports) — celui-ci est déjà couvert
par la suite existante et ne doit strictement pas changer (One New Truth
Rule : AnalysisResult reste une projection narrative inchangée).
"""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from services.evidence_capture import capture_evidence, _capture_one_impact
from services.evidence_ledger_service import save_evidence_capture


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — formes réalistes des dicts produits par le pipeline aujourd'hui
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def evidence_graph_sample():
    return {
        "facts": [
            {
                "id": "F001",
                "category": "observation",
                "claim": "CA total exercice = 1 200 000 €",
                "source_sheet": "P&L",
                "source_context": "Ligne 'Total CA', valeur = 1200000",
                "calculation": "Lecture directe",
                "confidence": 1.0,
            },
            {
                "id": "F002",
                "category": "deduction",
                "claim": "Baisse CA de 8% entre S1 et S2",
                "source_sheet": "P&L",
                "source_context": "CA S1 = 650000, CA S2 = 598000",
                "calculation": "(598000 - 650000) / 650000",
                "confidence": 0.95,
            },
        ],
        "unavailable_data": [
            {"data": "Marge par produit", "reason": "Aucune feuille ne la détaille"}
        ],
        "sheets_verified": ["P&L", "Bilan"],
    }


@pytest.fixture
def analysis_dict_sample():
    """
    Reproduit exactement la forme produite par _parse_v3_text, AVANT toute
    coercition Pydantic — c'est-à-dire avant que quantified_impact ne soit
    perdu (fuite documentée en T1B).
    """
    return {
        "value_destroyers": [
            {
                "name": "Retard de facturation clients",
                "impact_annuel": "120 000 €",
                "tendance": "hausse",
                "commentaire": "Délai moyen +12 jours",
                "quantified_impact": {
                    "metric_type": "REVENUE",
                    "period_basis": "ANNUAL",
                    "nature": "RECURRING",
                    "confidence": 0.9,
                    "source_period": "FY 2025",
                    "is_current_period": True,
                    "gross_margin": None,
                    "annualization": None,
                    "amount": None,  # jamais fourni côté LLM V3 (T1B)
                },
            },
            {
                # Cas réaliste : aucune donnée exploitable — le LLM ne doit
                # jamais inventer, donc pas de bloc quantified_impact du tout.
                "name": "Dépendance fournisseur unique",
                "impact_annuel": "Données insuffisantes",
                "tendance": None,
                "commentaire": None,
            },
        ],
        "quick_wins": [
            {
                "description": "Renégocier le contrat fournisseur X",
                "roi_estime": "30 000 €",
                "temps_mise_en_oeuvre": "2 semaines",
                "difficulte": "faible",
                "quantified_impact": {
                    "metric_type": "COST_SAVING",
                    "period_basis": "ANNUAL",
                    "nature": "ONE_TIME",
                    "confidence": 0.7,
                    "amount": None,
                },
            },
        ],
        # Champs narratifs qui ne doivent jamais être lus par ce module —
        # présents ici uniquement pour prouver qu'ils sont ignorés.
        "resume_executif": "Ce texte ne doit jamais apparaître dans la capture.",
        "score_confiance": 82,
    }


# ─────────────────────────────────────────────────────────────────────────────
# capture_evidence — comportement nominal
# ─────────────────────────────────────────────────────────────────────────────

class TestCaptureEvidenceNominal:

    def test_facts_passthrough_unmodified(self, evidence_graph_sample, analysis_dict_sample):
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        assert result["facts"] == evidence_graph_sample["facts"]
        assert result["unavailable_data"] == evidence_graph_sample["unavailable_data"]
        assert result["sheets_verified"] == evidence_graph_sample["sheets_verified"]

    def test_quantified_impacts_count_matches_source_lists(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        # 2 value_destroyers + 1 quick_win = 3 entrées, même si l'une des
        # deux destroyers n'a pas de quantified_impact exploitable.
        assert len(result["quantified_impacts"]) == 3

    def test_amount_correctly_injected_from_legacy_text(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        destroyer_0 = result["quantified_impacts"][0]
        assert destroyer_0["origin"] == "destroyer"
        assert destroyer_0["index"] == 0
        assert destroyer_0["impact"]["amount"] == 120_000.0
        assert destroyer_0["impact"]["currency"] == "EUR"

    def test_legacy_amount_source_is_explicitly_tagged(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        """
        Invariant ADR-001 §6 : 'Une preuve reconstruite après coup [...] n'est
        jamais traitée avec le même niveau de confiance qu'une preuve
        directement ancrée à sa source ; elle est explicitement distinguée.'
        """
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        refs = result["quantified_impacts"][0]["impact"]["source_references"]
        assert refs[0]["source_type"] == "LEGACY_PARSE"
        assert "legacy fallback" in refs[0]["source_quote"]

    def test_quick_win_captured_with_correct_origin(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        quick_win_entries = [e for e in result["quantified_impacts"] if e["origin"] == "quick_win"]
        assert len(quick_win_entries) == 1
        assert quick_win_entries[0]["impact"]["amount"] == 30_000.0
        assert quick_win_entries[0]["impact"]["metric_type"] == "COST_SAVING"

    def test_narrative_fields_never_leak_into_capture(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        """La capture ne doit jamais absorber de texte narratif (resume_executif,
        score_confiance) — seulement des faits et des impacts quantifiés."""
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        serialized = str(result)
        assert "Ce texte ne doit jamais apparaître" not in serialized


# ─────────────────────────────────────────────────────────────────────────────
# capture_evidence — invariant "absence ≠ zéro" (ADR-001 §6, cas critique)
# ─────────────────────────────────────────────────────────────────────────────

class TestCaptureEvidenceAbsenceNeverBecomesZero:

    def test_destroyer_without_quantified_impact_yields_none_not_zero(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        result = capture_evidence(evidence_graph_sample, analysis_dict_sample)
        destroyer_1 = result["quantified_impacts"][1]
        assert destroyer_1["origin"] == "destroyer"
        assert destroyer_1["index"] == 1
        # C'est le test inverse exact de la fuite documentée en T1B : une
        # absence de donnée doit rester visible comme absence (None), jamais
        # silencieusement disparaître ni devenir 0.
        assert destroyer_1["impact"] is None

    def test_unparsable_amount_text_yields_none_amount_not_zero(self):
        item = {
            "impact_annuel": "non chiffrable",
            "quantified_impact": {
                "metric_type": "REVENUE",
                "period_basis": "ANNUAL",
                "nature": "RECURRING",
                "amount": None,
            },
        }
        qi = _capture_one_impact(item, amount_field="impact_annuel")
        assert qi is not None
        assert qi.amount is None  # jamais 0.0


# ─────────────────────────────────────────────────────────────────────────────
# capture_evidence — robustesse (ne doit jamais lever d'exception)
# ─────────────────────────────────────────────────────────────────────────────

class TestCaptureEvidenceRobustness:

    def test_none_inputs_do_not_raise(self):
        result = capture_evidence(None, {})
        assert result == {
            "facts": [],
            "unavailable_data": [],
            "sheets_verified": [],
            "quantified_impacts": [],
        }

    def test_empty_evidence_graph_dict(self):
        result = capture_evidence({}, {"value_destroyers": [], "quick_wins": []})
        assert result["facts"] == []
        assert result["quantified_impacts"] == []

    def test_missing_keys_in_analysis_dict_do_not_raise(self):
        # analysis_dict sans value_destroyers/quick_wins du tout (V3 ancien
        # format, ou parsing partiel) — ne doit jamais lever.
        result = capture_evidence({}, {"resume_executif": "texte"})
        assert result["quantified_impacts"] == []

    def test_malformed_items_are_skipped_not_raised(self):
        analysis_dict = {
            "value_destroyers": ["pas un dict", None, 42],
            "quick_wins": [{"description": "ok", "roi_estime": None}],
        }
        result = capture_evidence({}, analysis_dict)
        # Les 3 entrées malformées de value_destroyers sont ignorées ;
        # seul le quick_win valide (sans quantified_impact -> impact=None) reste.
        assert len(result["quantified_impacts"]) == 1
        assert result["quantified_impacts"][0]["origin"] == "quick_win"
        assert result["quantified_impacts"][0]["impact"] is None

    def test_malformed_quantified_impact_dict_does_not_raise(self):
        item = {
            "impact_annuel": "120 000 €",
            "quantified_impact": {"metric_type": 12345, "nature": ["invalide"]},
        }
        # _try_deserialize_qi (executive_decision_model.py) garantit déjà
        # qu'aucune exception n'est levée — ce test vérifie que la
        # composition dans evidence_capture.py hérite bien de cette garantie.
        qi = _capture_one_impact(item, amount_field="impact_annuel")
        assert qi is not None  # dégradé proprement vers UNKNOWN, pas de crash
        assert qi.amount == 120_000.0


# ─────────────────────────────────────────────────────────────────────────────
# save_evidence_capture — persistance non-bloquante (Supabase mocké)
# ─────────────────────────────────────────────────────────────────────────────

def make_supabase_mock():
    """Mock Supabase minimaliste chaînable (même helper que test_arc_service.py)."""
    mock = MagicMock()
    for method in ("from_", "insert", "select", "eq", "single"):
        getattr(mock, method).return_value = mock
    mock.execute.return_value = MagicMock(data=[{"id": "evidence-row-uuid"}])
    return mock


class TestSaveEvidenceCaptureNonBlocking:

    def test_valid_capture_is_inserted(self, evidence_graph_sample, analysis_dict_sample):
        sb = make_supabase_mock()
        capture = capture_evidence(evidence_graph_sample, analysis_dict_sample)

        with patch("main.get_supabase_service", return_value=sb):
            save_evidence_capture(
                analyse_id="analyse-uuid-1",
                company_id="company-uuid-1",
                entity_id="entity-uuid-1",
                evidence_capture=capture,
            )

        sb.from_.assert_called_with("evidence_ledger_entries")
        insert_call_args = sb.insert.call_args[0][0]
        assert insert_call_args["analyse_id"] == "analyse-uuid-1"
        assert insert_call_args["company_id"] == "company-uuid-1"
        assert insert_call_args["entity_id"] == "entity-uuid-1"
        assert insert_call_args["capture_schema_version"] == "T1C-A-v1"
        assert len(insert_call_args["quantified_impacts"]) == 3

    def test_none_entity_id_is_omitted_not_inserted_as_null(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        """entity_id est optionnel (nullable côté DB) — ne doit pas être forcé
        à None explicitement si absent, cohérent avec le pattern déjà utilisé
        pour entity_id dans _save_to_db (routers/analyze.py)."""
        sb = make_supabase_mock()
        capture = capture_evidence(evidence_graph_sample, analysis_dict_sample)

        with patch("main.get_supabase_service", return_value=sb):
            save_evidence_capture(
                analyse_id="analyse-uuid-2",
                company_id="company-uuid-1",
                entity_id=None,
                evidence_capture=capture,
            )

        insert_call_args = sb.insert.call_args[0][0]
        assert "entity_id" not in insert_call_args

    def test_empty_capture_is_not_inserted(self):
        sb = make_supabase_mock()
        empty_capture = {
            "facts": [], "unavailable_data": [], "sheets_verified": [], "quantified_impacts": [],
        }
        with patch("main.get_supabase_service", return_value=sb):
            save_evidence_capture(
                analyse_id="analyse-uuid-3",
                company_id="company-uuid-1",
                entity_id=None,
                evidence_capture=empty_capture,
            )
        sb.from_.assert_not_called()
        sb.insert.assert_not_called()

    def test_none_capture_is_not_inserted(self):
        sb = make_supabase_mock()
        with patch("main.get_supabase_service", return_value=sb):
            save_evidence_capture(
                analyse_id="analyse-uuid-4",
                company_id="company-uuid-1",
                entity_id=None,
                evidence_capture=None,
            )
        sb.from_.assert_not_called()

    def test_supabase_exception_is_swallowed_not_raised(
        self, evidence_graph_sample, analysis_dict_sample
    ):
        """
        Contrat non-bloquant : l'échec de cette écriture ne doit JAMAIS
        remonter à l'appelant (même garantie que l'insert usage_logs
        existant dans routers/analyze.py:_save_to_db).
        """
        sb = MagicMock()
        sb.from_.side_effect = RuntimeError("Supabase injoignable (projet en pause)")
        capture = capture_evidence(evidence_graph_sample, analysis_dict_sample)

        with patch("main.get_supabase_service", return_value=sb):
            # Ne doit lever aucune exception.
            save_evidence_capture(
                analyse_id="analyse-uuid-5",
                company_id="company-uuid-1",
                entity_id=None,
                evidence_capture=capture,
            )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
