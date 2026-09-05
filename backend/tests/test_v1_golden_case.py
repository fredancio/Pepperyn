from __future__ import annotations

import inspect

from sandbox.synthetic_raw_ingestion import OPTILUX_RAW_WORKBOOK_SHA256
from sandbox.v1_golden_case import restart_round_trip, run_v1_golden_case


def test_v1_golden_case_has_no_runtime_input_and_invokes_legacy_projections_honestly():
    assert tuple(inspect.signature(run_v1_golden_case).parameters) == ()
    result = run_v1_golden_case()
    assert result.source_workbook_sha256 == OPTILUX_RAW_WORKBOOK_SHA256
    assert result.provider_mode == "DETERMINISTIC_TEST_DOUBLE_NO_NETWORK"
    assert result.provider_request["store"] is False
    assert result.envelope.analysis_result.verification_tag == "V1_GOVERNED_SINGLE_CALL"
    assert result.executive_decision_model["ebitda"] == "-145 000 €"
    assert result.executive_decision_model["available_cash"] == "336 000 €"
    assert result.executive_decision_model["executive_decision"] is None
    # No provider-inferred score is promoted to canonical truth merely to make
    # the legacy kernel pass; the existing extractor therefore fails closed.
    assert result.decision_kernel is None


def test_v1_golden_case_serialization_round_trip_preserves_lineage_and_epistemic_state():
    before = run_v1_golden_case()
    after = restart_round_trip(before)
    assert after == before.envelope
    assert after.governed_analysis.source_representation_sha256 == after.source_facts.source_representation_sha256
    assert after.analysis_result.resume_executif.startswith("INFERENCE —")


def test_v1_golden_case_contains_professional_prerequisite_before_action():
    result = run_v1_golden_case().envelope.analysis_result
    assert result.plan_action_haute == []
    assert "Prérequis:" in result.plan_action[0]
    assert any(item.startswith("UNKNOWN:") for item in result.alertes)
