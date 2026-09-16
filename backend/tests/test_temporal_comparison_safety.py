"""Synthetic arithmetic/refusal proof, not professional reliability certification."""

import pytest

from test_governed_temporal_continuity import ReadOnlyDatabase, envelope, fact, row
import services.governed_temporal_continuity as temporal


def compare(before_period="2025", after_period="2026", before=100, after=110):
    return temporal.compare_governed_envelopes(
        envelope(before_period, [fact("REVENUE", before, before_period, "A")]),
        envelope(after_period, [fact("REVENUE", after, after_period, "B")]),
        previous_analysis_id="old", current_analysis_id="new",
    )


@pytest.mark.parametrize("before,after", [("2025", "FY26 ACTUAL"), ("FY25", "2026"), ("2024", "2026")])
def test_unestablished_calendar_or_missing_year_refuses_delta(before, after):
    result = compare(before, after)
    assert result["status"] == "UNKNOWN"
    assert result["changes"] == []
    assert result["unknowns"]


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_fact_never_becomes_a_numeric_change(value):
    result = compare(before=value)
    assert result["status"] == "UNKNOWN"
    assert result["changes"] == []
    assert result["unknowns"]


@pytest.mark.parametrize("before,after,delta", [(0.1, 0.3, 0.2), (-10, -5, 5), (10, -5, -15)])
def test_decimal_and_sign_arithmetic_preserved_without_cause(before, after, delta):
    result = compare(before=before, after=after)
    assert result["changes"][0]["absolute_change"] == delta
    assert result["causal_interpretation"] is None
    assert result["comparison_scope"] == "ANNUAL_LABEL_ARITHMETIC_ONLY"
    assert result["financial_comparability"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("label", ["0000", "25", "2025 ACTUAL", "FY0000"])
def test_invalid_or_unbound_year_label_is_not_invented(label):
    assert temporal._period_key(label) is None


def test_large_integer_delta_does_not_use_default_decimal_rounding():
    result = compare(before=10**30 + 1, after=0)
    assert result["changes"][0]["absolute_change"] == -(10**30 + 1)


def test_ununderstood_source_facts_cannot_authorize_comparison():
    before = envelope("2025", [fact("REVENUE", 100, "2025", "A")])
    before = before.model_copy(update={"source_facts": before.source_facts.model_copy(update={"status": "AMBIGUOUS"})})
    after = envelope("2026", [fact("REVENUE", 110, "2026", "B")])
    result = temporal.compare_governed_envelopes(before, after, previous_analysis_id="old", current_analysis_id="new")
    assert result["status"] == "UNKNOWN"
    assert result["changes"] == []


@pytest.mark.parametrize("other_period,status", [("2026", "CONTRADICTION"), ("FY202", "UNKNOWN")])
def test_loader_does_not_silently_select_around_ambiguous_history(monkeypatch, other_period, status):
    periods = {"target": "2026", "prior": "2025", "other": other_period}
    database = ReadOnlyDatabase([row(key, "tenant", "entity", "eng", period) for key, period in periods.items()])

    def load(_database, **scope):
        period = periods[scope["analysis_id"]]
        return envelope(period, [fact("REVENUE", 100, period, "A")])

    monkeypatch.setattr(temporal, "load_governed_envelope", load)
    result = temporal.load_governed_temporal_comparison(database, analysis_id="target", company_id="tenant")
    assert result["status"] == status
    assert result["previous_analysis_id"] is None
    assert result["changes"] == []
    assert set(database.calls) == {"select"}
