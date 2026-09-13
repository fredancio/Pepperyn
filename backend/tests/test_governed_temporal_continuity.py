"""Falsification tests for deterministic governed temporal continuity."""

from services.v1_analysis_contract import GovernedAnalysisEnvelope, SourceFact, UnderstandingResult
import services.governed_temporal_continuity as temporal


def fact(metric, value, period, suffix, unit="EUR"):
    return SourceFact(
        fact_id=f"F{suffix:0<12}"[:13], metric=metric, value=value, unit=unit, period=period,
        source_sheet_ref=f"S{suffix:0<12}"[:13], source_field=f"R{suffix:0<12}"[:13],
    )


def envelope(period, facts):
    understanding = UnderstandingResult(
        status="UNDERSTOOD", current_period=period, facts=tuple(facts),
        source_representation_sha256="A" * 64,
    )
    return GovernedAnalysisEnvelope.model_construct(governed_analysis=None, source_facts=understanding)


def test_change_is_arithmetic_source_referenced_and_never_causal():
    result = temporal.compare_governed_envelopes(
        envelope("2025", [fact("REVENUE", 100, "2025", "A"), fact("CASH", 40, "2025", "B")]),
        envelope("2026", [fact("REVENUE", 125, "2026", "C"), fact("CASH", 30, "2026", "D")]),
        previous_analysis_id="old", current_analysis_id="new",
    )
    assert result["status"] == "COMPARABLE"
    assert [(item["metric"], item["absolute_change"]) for item in result["changes"]] == [
        ("CASH", -10), ("REVENUE", 25),
    ]
    assert all(item["previous_fact_id"] and item["current_fact_id"] for item in result["changes"])
    assert result["causal_interpretation"] is None


def test_missing_metric_and_unit_mismatch_remain_unknown():
    result = temporal.compare_governed_envelopes(
        envelope("FY25 ACTUAL", [fact("REVENUE", 100, "FY25 ACTUAL", "A"), fact("CASH", 2, "FY25 ACTUAL", "B")]),
        envelope("FY26 ACTUAL", [fact("REVENUE", 110, "FY26 ACTUAL", "C", "RATIO")]),
        previous_analysis_id="old", current_analysis_id="new",
    )
    assert result["status"] == "UNKNOWN"
    assert "Unité non comparable pour REVENUE." in result["unknowns"]
    assert "CASH est absent de la période courante." in result["unknowns"]
    assert result["changes"] == []


def test_partial_comparison_does_not_hide_unknown_metrics():
    result = temporal.compare_governed_envelopes(
        envelope("2025", [fact("REVENUE", 100, "2025", "A"), fact("CASH", 20, "2025", "B")]),
        envelope("2026", [fact("REVENUE", 105, "2026", "C")]),
        previous_analysis_id="old", current_analysis_id="new",
    )
    assert result["status"] == "PARTIALLY_COMPARABLE"
    assert result["changes"][0]["absolute_change"] == 5
    assert result["unknowns"] == ["CASH est absent de la période courante."]


def test_non_earlier_period_is_a_named_contradiction():
    result = temporal.compare_governed_envelopes(
        envelope("2026", [fact("CASH", 1, "2026", "A")]),
        envelope("2026", [fact("CASH", 2, "2026", "B")]),
        previous_analysis_id="old", current_analysis_id="new",
    )
    assert result["status"] == "CONTRADICTION"
    assert result["changes"] == []


class Query:
    def __init__(self, rows, calls): self.rows = list(rows); self.calls = calls
    def select(self, *_args): self.calls.append("select"); return self
    def eq(self, key, value): self.rows = [row for row in self.rows if row.get(key) == value]; return self
    def limit(self, _value): return self
    def execute(self): return type("Result", (), {"data": self.rows})()


class ReadOnlyDatabase:
    def __init__(self, rows): self.rows = rows; self.calls = []
    def from_(self, table):
        assert table == "governed_analysis_envelopes"
        return Query(self.rows, self.calls)


def row(identifier, company, entity, engagement, period):
    return {"analysis_id": identifier, "company_id": company, "entity_id": entity,
            "engagement_id": engagement, "envelope_json": {"source_facts": {"current_period": period}}}


def test_loader_selects_nearest_prior_in_exact_scope_without_writes():
    rows = [row("target", "tenant-a", "entity-a", "eng-a", "2026"),
            row("nearest", "tenant-a", "entity-a", "eng-a", "2025"),
            row("older", "tenant-a", "entity-a", "eng-a", "2024"),
            row("other-entity", "tenant-a", "entity-b", "eng-b", "2025"),
            row("foreign", "tenant-b", "entity-a", "eng-a", "2025")]
    database = ReadOnlyDatabase(rows)
    original = temporal.load_governed_envelope
    loaded = []
    try:
        def fake_load(_database, **scope):
            loaded.append(scope)
            period = {"target": "2026", "nearest": "2025", "older": "2024"}[scope["analysis_id"]]
            suffix = {"2026": "A", "2025": "B", "2024": "C"}[period]
            return envelope(period, [fact("REVENUE", 120 if period == "2026" else 100, period, suffix)])
        temporal.load_governed_envelope = fake_load
        result = temporal.load_governed_temporal_comparison(
            database, analysis_id="target", company_id="tenant-a",
        )
    finally:
        temporal.load_governed_envelope = original
    assert result["previous_analysis_id"] == "nearest"
    assert all(scope["company_id"] == "tenant-a" and scope["entity_id"] == "entity-a" for scope in loaded)
    assert database.calls and set(database.calls) == {"select"}


def test_duplicate_nearest_period_fails_as_contradiction_before_loading():
    rows = [row("target", "tenant-a", "entity-a", "eng-a", "2026"),
            row("prior-a", "tenant-a", "entity-a", "eng-a", "2025"),
            row("prior-b", "tenant-a", "entity-a", "eng-a", "FY25 ACTUAL")]
    original = temporal.load_governed_envelope
    try:
        def fake_load(_database, **scope):
            periods = {"target": "2026", "prior-a": "2025", "prior-b": "FY25 ACTUAL"}
            suffixes = {"target": "A", "prior-a": "B", "prior-b": "C"}
            period = periods[scope["analysis_id"]]
            return envelope(period, [fact("REVENUE", 100, period, suffixes[scope["analysis_id"]])])
        temporal.load_governed_envelope = fake_load
        result = temporal.load_governed_temporal_comparison(
            ReadOnlyDatabase(rows), analysis_id="target", company_id="tenant-a",
        )
    finally:
        temporal.load_governed_envelope = original
    assert result["status"] == "CONTRADICTION"
    assert result["previous_analysis_id"] is None
