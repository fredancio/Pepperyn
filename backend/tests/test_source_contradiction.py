"""General source-conflict falsification, no financial review oracle dependency."""
import pytest

from services.v1_analysis_contract import UnderstandingResult, build_financial_understanding, build_openai_request
from sandbox.heterogeneous_workbooks import summarize_understanding


def payload(values):
    return {"temporal_context": {"columns_by_role": {"CURRENT_ACTUAL": ["2031"]}},
            "sheets": [{"sheet_name": "Source", "columns": ["Label", "2031"],
                        "full_table": [{"Label": label, "2031": value} for label, value in values]}]}


@pytest.mark.parametrize("left,right", [(721, 804), (-32, 0), (0.25, 0.5)])
@pytest.mark.parametrize("reverse", [False, True])
def test_conflict_preserves_unselected_claims_and_unrelated_observation(left, right, reverse):
    rows = [("Revenue", left), ("Net sales", right), ("Cash", 19)]
    parsed = payload(list(reversed(rows)) if reverse else rows)
    result = build_financial_understanding(parsed)
    assert result.status == "CONTRADICTION"
    assert result.conflicting_metrics == ("REVENUE",)
    assert sorted((f.metric, f.value) for f in result.facts) == sorted([
        ("REVENUE", left), ("REVENUE", right), ("CASH", 19)])
    assert len({f.fact_id for f in result.facts}) == 3
    assert len({f.source_field for f in result.facts}) == 3
    assert all(f.period == "2031" for f in result.facts)
    with pytest.raises(ValueError, match="dispatch forbidden"):
        build_openai_request(parsed, model="mock-local")


def test_equal_repeated_claims_are_not_a_contradiction_and_serialization_is_unchanged():
    result = build_financial_understanding(payload([("Revenue", 721), ("Net sales", 721)]))
    assert result.status == "UNDERSTOOD" and not result.conflicting_metrics
    assert set(result.model_dump()) == {"status", "current_period", "facts", "unknowns", "source_representation_sha256"}
    with pytest.raises(ValueError, match="requires incompatible"):
        UnderstandingResult.model_validate({**result.model_dump(), "status": "CONTRADICTION", "unknowns": ["forged"]})


def test_ambiguity_is_not_silently_resolved_when_a_separate_conflict_exists():
    result = build_financial_understanding(payload([
        ("Revenue", 721), ("Revenue", 804), ("EBITDA", "1,234")]))
    assert result.status == "CONTRADICTION"
    assert any("numeric representation" in reason for reason in result.unknowns)
    assert all(f.metric != "EBITDA" for f in result.facts)


def test_oversized_claim_set_is_not_truncated_into_a_resolved_result():
    result = build_financial_understanding(payload([("Revenue", i) for i in range(251)]))
    assert result.status == "AMBIGUOUS" and not result.facts
    assert any("250" in reason for reason in result.unknowns)


def test_discrepancy_measurement_retains_decimal_precision_and_claim_references():
    understanding = build_financial_understanding(payload([("Revenue", 10**35), ("Revenue", 1)]))
    item = summarize_understanding(understanding)["discrepancies"][0]
    assert int(item["absolute_spread"]) == 10**35 - 1
    assert set(item["claim_ids"]) == {f.fact_id for f in understanding.facts}
