from pathlib import Path


SQL = (Path(__file__).parents[1] / "migrations" / "v30_governed_decision_followup_checkpoint.sql").read_text()


def test_v30_is_explicit_scoped_and_immutable():
    assert "confirmation_source = 'explicit'" in SQL
    assert "UNIQUE (decision_feedback_id)" in SQL
    assert "BEFORE UPDATE OR DELETE" in SQL
    assert "professional_note" in SQL
    assert "prerequisites_confirmed_complete" in SQL


def test_v30_does_not_create_or_modify_decision_arcs():
    assert "decision_arcs" not in SQL.lower()
    assert "GRANT SELECT, INSERT" in SQL
