"""Local harness falsifications only; these do NOT prove PostgreSQL behavior."""
import copy
import json
from types import SimpleNamespace

import pytest

from sandbox import rehearse_execution_receipt_v39 as r

SCOPE = dict(company_id="20000000-0000-0000-0000-000000000001",
             entity_id="30000000-0000-0000-0000-000000000001",
             engagement_id="40000000-0000-0000-0000-000000000001")


class Response:
    def __init__(self, status, data):
        self.status_code, self.data = status, data

    def json(self):
        return self.data


class Fake(r.Database):
    def __init__(self, failure=None):
        self.tables = {t: [] for t in r.TABLES}
        self.client = self
        self.calls = []
        self.failure = failure

    def get(self, table, params):
        rows = copy.deepcopy(self.tables[table])
        for key, value in params.items():
            if key not in ("select", "limit"):
                rows = [x for x in rows if str(x.get(key)) == value[3:]]
        return rows[:int(params.get("limit", "101"))]

    def post(self, path, *, json):
        self.calls.append(copy.deepcopy(json))
        n = len(self.calls)
        if self.failure == (n, "timeout"):
            raise TimeoutError()
        if self.failure == (n, "unexpected_success"):
            return Response(200, json["p_analysis"]["id"])
        if n == 1:
            return Response(400, dict(code="P0001", message="V39 execution binding refused"))
        if n == 2:
            if self.failure == (2, "partial"):
                self.tables["analyses"].append(copy.deepcopy(json["p_analysis"]))
            return Response(400, dict(code="23514", message='constraint "governed_execution_receipts_sha256_check"'))
        if n == 3:
            self.tables["analyses"].append(copy.deepcopy(json["p_analysis"]))
            self.tables["governed_analysis_envelopes"].append(copy.deepcopy(json["p_envelope"]))
            receipt = copy.deepcopy(json["p_receipt"])
            receipt.update({k: receipt["payload"][k] for k in (*SCOPE, "analysis_id")})
            self.tables["governed_execution_receipts"].append(receipt)
            return Response(200, None if self.failure == (3, "ack") else json["p_analysis"]["id"])
        return Response(409, dict(code="23505", message='constraint "analyses_pkey"'))


def test_full_local_harness_then_independent_read(tmp_path):
    db = Fake()
    state = r.persist(db, SCOPE, tmp_path / "manifest.json")
    assert state["attempts"] == len(db.calls) == 4
    assert sum(len(x) for x in db.tables.values()) == 3
    assert state["status"] == "V39_PERSISTED_PENDING_SECOND_PROCESS"
    assert r.verify_read(db, json.loads((tmp_path / "manifest.json").read_text())) == state["after"]
    assert len(db.calls) == 4  # reading never calls RPC
    assert db.calls[2] == db.calls[3]


@pytest.mark.parametrize("failure", [(1,"unexpected_success"), (2,"unexpected_success"),
                                     (2,"partial"), (3,"ack"), (4,"unexpected_success"),
                                     (1,"timeout"), (3,"timeout"), (4,"timeout")])
def test_fail_closed_without_retry_or_cleanup(tmp_path, failure):
    db = Fake(failure)
    path = tmp_path / "manifest.json"
    with pytest.raises(Exception):
        r.persist(db, SCOPE, path)
    state = json.loads(path.read_text())
    assert len(db.calls) == state["attempts"] == failure[0]
    assert state["status"] == "REFUSED"
    if failure[0] == 4 or failure == (3,"ack"):
        assert sum(len(x) for x in db.tables.values()) == 3
    with pytest.raises(FileExistsError):
        r.persist(db, SCOPE, path)
    assert len(db.calls) == failure[0]


def test_budget_stops_fifth_call_before_transport(tmp_path):
    db = Fake()
    state = {"attempts":4,"scope":SCOPE,"ids":r.ids(SCOPE)}
    with pytest.raises(ValueError):
        r.Budget(db,state,tmp_path/"manifest.json").call({})
    assert not db.calls


def test_existing_row_change_and_extra_row_rejected():
    before = {t:{"old":"hash"} for t in r.TABLES}
    after = copy.deepcopy(before)
    after["analyses"]["old"] = "changed"
    with pytest.raises(ValueError): r.expected_delta(before,after)
    after = copy.deepcopy(before)
    after["analyses"]["extra"] = "hash"
    with pytest.raises(ValueError): r.expected_delta(before,after)


def test_wrong_sql_error_is_not_atomicity_proof():
    with pytest.raises(ValueError):
        r.refused(Response(400,dict(code="23514",message="another constraint")),
                  "23514","governed_execution_receipts_sha256_check")


def test_tampered_receipt_refuses_read(tmp_path):
    db = Fake()
    state = r.persist(db,SCOPE,tmp_path/"manifest.json")
    db.tables["governed_execution_receipts"][0]["payload"]["provider_mode"] = "OPENAI"
    with pytest.raises(Exception): r.verify_read(db,state)
