from pathlib import Path


SQL = (Path(__file__).parents[1] / "migrations" / "v29_explicit_governed_decision.sql").read_text()


def test_v29_requires_explicit_coherent_immutable_decision():
    assert "decision_confirmation_source = 'explicit'" in SQL
    assert "status = 'decided'" in SQL
    assert "prevent_confirmed_decision_mutation" in SQL
    assert "BEFORE UPDATE OR DELETE" in SQL
    assert "decision_kind IS NULL" in SQL
    assert "decision_text IS NOT NULL" in SQL
    assert "prerequisites_acknowledged IS NOT NULL" in SQL


def test_v29_never_creates_or_updates_a_decision_arc():
    assert "decision_arcs" not in SQL.lower()
