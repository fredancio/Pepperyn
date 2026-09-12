from pathlib import Path


SQL = (Path(__file__).parents[1] / "migrations" / "v31_explicit_governed_decision_execution.sql").read_text()


def test_v31_is_explicit_scoped_and_immutable():
    assert "confirmation_source = 'explicit'" in SQL
    assert "UNIQUE (decision_feedback_id)" in SQL
    assert "BEFORE UPDATE OR DELETE" in SQL
    assert "executed_on DATE NOT NULL" in SQL
    assert "professional_note" in SQL
    assert "CHECK (prerequisites_confirmed_complete)" in SQL
    assert "BEFORE INSERT" in SQL
    assert "df.company_id = NEW.company_id" in SQL
    assert "df.report_id = NEW.report_id" in SQL
    assert "df.recommendation_id = NEW.recommendation_id" in SQL
    assert "NEW.executed_on >= df.decision_confirmed_at::date" in SQL
    assert "governed_decision_followups" in SQL


def test_v31_does_not_create_outcome_learning_or_decision_arc():
    lowered = SQL.lower()
    assert "decision_arcs" not in lowered
    assert "actual_outcome" not in lowered
    assert "GRANT SELECT, INSERT" in SQL
