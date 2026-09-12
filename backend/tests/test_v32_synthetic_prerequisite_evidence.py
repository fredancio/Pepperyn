from pathlib import Path

import pytest

from sandbox.v1_prerequisite_evidence import (
    PrerequisiteEvidenceRefused, load_validated_prerequisite_evidence,
)


SQL = (Path(__file__).parents[1] / "migrations" / "v32_synthetic_decision_prerequisite_evidence.sql").read_text()


def test_registered_package_is_synthetic_reconciled_and_boundary_closed():
    package = load_validated_prerequisite_evidence()
    assert package.fixture_id == "PEPPERYN_V1_EXECUTION_PREREQUISITES"
    assert package.period_start.isoformat() == "2026-09-01"
    assert package.period_end.isoformat() == "2027-08-31"
    assert package.payload["semantic_boundaries"] == {
        "later_evidence": False, "actual_outcome": False,
        "learning": False, "expected_impact": False,
    }


def test_tampered_package_is_refused_before_persistence(monkeypatch, tmp_path):
    source = Path(__file__).parents[1] / "tests" / "golden" / "fixtures" / "pepperyn_v1_execution_prerequisites.json"
    tampered = tmp_path / "tampered.json"
    content = source.read_text(encoding="utf-8").replace('"amount": 120000', '"amount": 120001', 1)
    tampered.write_text(content, encoding="utf-8")
    monkeypatch.setattr("sandbox.v1_prerequisite_evidence._FIXTURE", tampered)
    with pytest.raises(PrerequisiteEvidenceRefused, match="HASH_MISMATCH"):
        load_validated_prerequisite_evidence()


def test_v32_is_scoped_immutable_and_semantically_closed():
    assert "UNIQUE (decision_feedback_id)" in SQL
    assert "BEFORE UPDATE OR DELETE" in SQL
    assert "df.company_id = NEW.company_id" in SQL
    assert "prerequisite_evidence_id SET NOT NULL" in SQL
    assert "NOT later_evidence" in SQL
    assert "NOT actual_outcome_created" in SQL
    assert "NOT learning_created" in SQL
    assert "NOT expected_impact_created" in SQL
    assert "decision_arcs" not in SQL.lower()
