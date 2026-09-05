from __future__ import annotations

import copy
import pytest

from sandbox.v1_golden_case import run_v1_golden_case
from services.governed_analysis_persistence import (
    GovernedPersistenceRefused, load_governed_envelope, save_governed_analysis,
)

ANALYSIS = "10000000-0000-0000-0000-000000000001"
COMPANY_A = "20000000-0000-0000-0000-000000000001"
COMPANY_B = "20000000-0000-0000-0000-000000000002"
ENTITY_A = "30000000-0000-0000-0000-000000000001"
ENTITY_B = "30000000-0000-0000-0000-000000000002"
ENGAGEMENT_A = "40000000-0000-0000-0000-000000000001"
ENGAGEMENT_B = "40000000-0000-0000-0000-000000000002"


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, db, table): self.db, self.table, self.rows = db, table, list(db.tables.get(table, ()))
    def select(self, fields): self.db.log.append((self.table, "select", fields)); return self
    def eq(self, field, value):
        self.db.log.append((self.table, "eq", field, value)); self.rows = [r for r in self.rows if r.get(field) == value]; return self
    def limit(self, value): self.rows = self.rows[:value]; return self
    def execute(self): return _Response(self.rows)


class _Rpc:
    def __init__(self, db, params): self.db, self.params = db, copy.deepcopy(params)
    def execute(self):
        if self.db.fail_rpc: raise RuntimeError("database error")
        analysis, envelope = self.params["p_analysis"], self.params["p_envelope"]
        entity_ok = any(e["id"] == analysis["entity_id"] and e["company_id"] == analysis["company_id"]
                        for e in self.db.tables.get("entities", ()))
        engagement_ok = any(e["id"] == envelope["engagement_id"] and e["entity_id"] == analysis["entity_id"]
                            for e in self.db.tables.get("engagements", ()))
        if not entity_ok or not engagement_ok or any(r["id"] == analysis["id"] for r in self.db.tables.get("analyses", ())):
            raise RuntimeError("constraint")
        if any(r["analysis_id"] == analysis["id"] for r in self.db.tables.get("governed_analysis_envelopes", ())):
            raise RuntimeError("duplicate")
        self.db.tables.setdefault("analyses", []).append(analysis)
        self.db.tables.setdefault("governed_analysis_envelopes", []).append(envelope)
        return _Response(analysis["id"])


class _Db:
    def __init__(self, tables=None, *, fail_rpc=False):
        self.tables, self.fail_rpc, self.log = copy.deepcopy(tables or {}), fail_rpc, []
    def from_(self, table): return _Query(self, table)
    def rpc(self, name, params):
        self.log.append(("rpc", name)); assert name == "persist_governed_analysis_v1"; return _Rpc(self, params)


def _db(): return _Db({
    "entities": [{"id": ENTITY_A, "company_id": COMPANY_A}],
    "engagements": [{"id": ENGAGEMENT_A, "entity_id": ENTITY_A}],
})
def _analysis(company=COMPANY_A, entity=ENTITY_A):
    return {"id": ANALYSIS, "company_id": company, "entity_id": entity,
            "analyse_json": {}, "fichier_nom": "synthetic.xlsx", "status": "completed"}


def _save(db):
    envelope = run_v1_golden_case().envelope
    save_governed_analysis(db, analysis_row=_analysis(), engagement_id=ENGAGEMENT_A, envelope=envelope)
    return envelope


def test_atomic_save_and_repository_reload_after_state_reconstruction():
    db = _db(); envelope = _save(db)
    assert len(db.tables["analyses"]) == len(db.tables["governed_analysis_envelopes"]) == 1
    reconstructed = _Db(db.tables)
    loaded = load_governed_envelope(
        reconstructed, analysis_id=ANALYSIS, company_id=COMPANY_A,
        entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
    )
    assert loaded == envelope
    assert ("governed_analysis_envelopes", "eq", "company_id", COMPANY_A) in reconstructed.log
    assert ("governed_analysis_envelopes", "eq", "entity_id", ENTITY_A) in reconstructed.log


@pytest.mark.parametrize("company,entity,engagement,analysis", [
    (COMPANY_B, ENTITY_A, ENGAGEMENT_A, ANALYSIS), (COMPANY_A, ENTITY_B, ENGAGEMENT_A, ANALYSIS),
    (COMPANY_A, ENTITY_A, ENGAGEMENT_B, ANALYSIS),
    (COMPANY_A, ENTITY_A, ENGAGEMENT_A, "10000000-0000-0000-0000-000000000002"),
])
def test_cross_client_entity_engagement_or_analysis_swap_refuses(company, entity, engagement, analysis):
    db = _db(); _save(db)
    with pytest.raises(GovernedPersistenceRefused):
        load_governed_envelope(
            db, analysis_id=analysis, company_id=company,
            entity_id=entity, engagement_id=engagement,
        )


def test_forged_scope_rolls_back_and_duplicate_is_refused():
    envelope = run_v1_golden_case().envelope; db = _db()
    with pytest.raises(GovernedPersistenceRefused):
        save_governed_analysis(
            db, analysis_row=_analysis(company=COMPANY_B), engagement_id=ENGAGEMENT_A,
            envelope=envelope,
        )
    assert not db.tables.get("analyses") and not db.tables.get("governed_analysis_envelopes")
    _save(db)
    with pytest.raises(GovernedPersistenceRefused):
        save_governed_analysis(
            db, analysis_row=_analysis(), engagement_id=ENGAGEMENT_A, envelope=envelope,
        )


@pytest.mark.parametrize("field,value", [
    ("envelope_sha256", "0" * 64), ("binding_sha256", "0" * 64),
    ("source_representation_sha256", "0" * 64), ("envelope_schema_version", "future"),
])
def test_tamper_and_version_drift_fail_closed(field, value):
    db = _db(); _save(db); db.tables["governed_analysis_envelopes"][0][field] = value
    with pytest.raises(GovernedPersistenceRefused):
        load_governed_envelope(
            db, analysis_id=ANALYSIS, company_id=COMPANY_A,
            entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        )


def test_modified_envelope_and_database_failure_fail_closed():
    db = _db(); envelope = _save(db)
    db.tables["governed_analysis_envelopes"][0]["envelope_json"]["governed_analysis"]["executive_diagnosis"] = "tampered"
    with pytest.raises(GovernedPersistenceRefused):
        load_governed_envelope(
            db, analysis_id=ANALYSIS, company_id=COMPANY_A,
            entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        )
    with pytest.raises(GovernedPersistenceRefused):
        save_governed_analysis(
            _Db(_db().tables, fail_rpc=True), analysis_row=_analysis(),
            engagement_id=ENGAGEMENT_A, envelope=envelope,
        )


def test_loader_has_no_legacy_analysis_json_fallback():
    db = _Db({"analyses": [{"id": ANALYSIS, "company_id": COMPANY_A, "entity_id": ENTITY_A, "analyse_json": {"unsafe": True}}]})
    with pytest.raises(GovernedPersistenceRefused):
        load_governed_envelope(
            db, analysis_id=ANALYSIS, company_id=COMPANY_A,
            entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        )
    assert not any(entry[0] == "analyses" for entry in db.log)
