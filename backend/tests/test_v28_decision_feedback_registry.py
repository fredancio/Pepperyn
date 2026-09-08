from pathlib import Path


SQL = (
    Path(__file__).parents[1] / "migrations" / "v28_repair_decision_feedback_registry.sql"
).read_text(encoding="utf-8")


def test_v28_is_narrow_idempotent_and_supports_unsure_without_creating_arcs():
    normalized = " ".join(SQL.lower().split())

    assert "create table if not exists public.decision_feedback" in normalized
    assert "unique (report_id, recommendation_id)" in normalized
    assert "'unsure'" in normalized
    assert "enable row level security" in normalized
    assert "with check" in normalized
    assert "create table public.decision_arcs" not in normalized
    assert "insert into" not in normalized
    assert "update public.analyses" not in normalized
    assert "governed_analysis_envelopes" not in normalized
