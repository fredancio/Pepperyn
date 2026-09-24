"""Local application proof; not real sessions, RLS or Beta admission."""
import copy
import pytest

from services.governed_analysis_read import GovernedReadRefused, read_owned_analysis
from services.governed_analysis_persistence import save_governed_analysis
from test_governed_analysis_persistence import (
    _db, _save, ANALYSIS, COMPANY_A, COMPANY_B, ENTITY_B, ENGAGEMENT_B,
)


def test_two_owned_reads_without_sandbox_flags_and_cross_scope_refusal(monkeypatch):
    monkeypatch.delenv("PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO", raising=False)
    monkeypatch.delenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", raising=False)
    db = _db(); envelope = _save(db)
    other_id = "10000000-0000-0000-0000-000000000002"
    db.tables["entities"].append({"id": ENTITY_B, "company_id": COMPANY_B})
    db.tables["engagements"].append({"id": ENGAGEMENT_B, "entity_id": ENTITY_B})
    save_governed_analysis(db, analysis_row={
        "id": other_id, "company_id": COMPANY_B, "entity_id": ENTITY_B,
    }, engagement_id=ENGAGEMENT_B, envelope=envelope)
    before = copy.deepcopy(db.tables)
    for own_id, own_company, foreign in ((ANALYSIS, COMPANY_A, COMPANY_B),
                                          (other_id, COMPANY_B, COMPANY_A)):
        response = read_owned_analysis(db, analysis_id=own_id, company_id=own_company)
        assert response.analyse_id == own_id
        assert response.result.id == own_id
        assert all(r["memory_read_state"] == "AVAILABLE" for r in response.recommendations_tracking)
        with pytest.raises(GovernedReadRefused, match="NOT_FOUND"):
            read_owned_analysis(db, analysis_id=own_id, company_id=foreign)
    assert db.tables == before


@pytest.mark.parametrize("table", ["analyses", "entities", "engagements", "governed_analysis_envelopes"])
def test_read_failure_is_not_not_found_or_empty(table, monkeypatch):
    db = _db(); _save(db)
    original = db.from_
    def query(name):
        if name == table:
            raise RuntimeError("sensitive database detail")
        return original(name)
    monkeypatch.setattr(db, "from_", query)
    with pytest.raises(GovernedReadRefused, match="^UNAVAILABLE$"):
        read_owned_analysis(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


def test_integrity_failure_never_rehydrates_legacy_analysis_json():
    db = _db(); _save(db)
    db.tables["analyses"][0]["analyse_json"] = {"invented": "fallback"}
    db.tables["governed_analysis_envelopes"][0]["envelope_sha256"] = "0" * 64
    with pytest.raises(GovernedReadRefused, match="UNAVAILABLE"):
        read_owned_analysis(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


def test_invalid_ids_refused_before_database_access():
    with pytest.raises(GovernedReadRefused, match="NOT_FOUND"):
        read_owned_analysis(object(), analysis_id="bad", company_id=COMPANY_A)


def test_duplicate_engagement_does_not_select_first():
    db = _db(); _save(db)
    db.tables["engagements"].append(copy.deepcopy(db.tables["engagements"][0]))
    with pytest.raises(GovernedReadRefused, match="NOT_FOUND"):
        read_owned_analysis(db, analysis_id=ANALYSIS, company_id=COMPANY_A)
