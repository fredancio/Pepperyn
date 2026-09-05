from pathlib import Path


SQL = (Path(__file__).parents[1] / "migrations" / "v27_governed_analysis_envelopes.sql").read_text(encoding="utf-8")


def test_v27_is_immutable_triple_scoped_and_service_role_only():
    assert "FOREIGN KEY (analysis_id, company_id, entity_id)" in SQL
    assert "FOREIGN KEY (entity_id, company_id)" in SQL
    assert "analysis_id UUID PRIMARY KEY" in SQL
    assert "entity_id UUID NOT NULL" in SQL
    assert "engagement_id UUID NOT NULL" in SQL
    assert "ENABLE ROW LEVEL SECURITY" in SQL
    assert "CREATE POLICY" not in SQL
    assert "BEFORE UPDATE" in SQL and "reject_governed_analysis_update" in SQL
    assert "ON CONFLICT" not in SQL
    assert "FOREIGN KEY (engagement_id, entity_id)" in SQL
    assert "persist_governed_analysis_v1" in SQL
    assert "REVOKE ALL" in SQL and "service_role" in SQL


def test_v27_has_live_schema_preflight_and_integrity_hash_constraints():
    assert "v27 preflight failed" in SQL
    assert "partial governed envelope table" in SQL
    assert "c.data_type = 'uuid'" in SQL
    assert "envelope_sha256 ~ '^[A-F0-9]{64}$'" in SQL
    assert "binding_sha256 ~ '^[A-F0-9]{64}$'" in SQL
    assert "source_representation_sha256 ~ '^[A-F0-9]{64}$'" in SQL
    assert "v27 convergence failed: governed envelope column contract mismatch" in SQL
    assert "character_maximum_length = 64" in SQL
    assert "v_required_constraints <> 8" in SQL
    assert "relrowsecurity" in SQL
    assert "trg_reject_governed_analysis_update" in SQL and "NOT tgisinternal" in SQL
