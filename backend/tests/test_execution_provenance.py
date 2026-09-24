"""Local synthetic adapters and persistence protocol; no live database proof."""
import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
from sandbox.synthetic_product import SandboxRefused
from services.governed_analysis_persistence import (
    GovernedPersistenceRefused, _digest, load_execution_provenance, save_governed_analysis,
)
from services.execution_provenance import validate_execution
from test_governed_analysis_persistence import (
    _db, _save, _analysis, ANALYSIS, COMPANY_A, ENTITY_A, ENGAGEMENT_A,
)


@pytest.fixture
def execution(monkeypatch):
    import socket
    def no_network(*args, **kwargs):
        raise AssertionError("Network forbidden in local mock")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    name = "pepperyn_v1_heterogeneous_english.xlsx"
    raw = (Path(__file__).parent / "golden" / "fixtures" / name).read_bytes()
    return run_recorded_registered_mock_analysis(raw, name)


def test_record_is_issued_after_local_mock_and_rejects_unregistered_bytes(execution):
    r = execution.provenance
    assert r.provider_mode == "LOCAL_MOCK" and r.transport == "NONE"
    assert r.data_origin == "REGISTERED_SYNTHETIC"
    assert r.envelope_sha256 == _digest(execution.analysis.envelope.model_dump(mode="json"))
    with pytest.raises(SandboxRefused):
        run_recorded_registered_mock_analysis(b"not registered", execution.analysis.filename)


@pytest.mark.parametrize("field,value", [
    ("raw_source_sha256", "0" * 64), ("envelope_sha256", "0" * 64),
    ("source_representation_sha256", "0" * 64), ("provider_mode", "OPENAI"),
    ("data_origin", "REAL"), ("transport", "NETWORK"),
])
def test_substitution_refused_before_any_rpc(execution, field, value):
    data = execution.provenance.model_dump(mode="json"); data[field] = value
    db = _db()
    row = _analysis(); row["source_data_hash"] = execution.analysis.source_sha256.lower()
    with pytest.raises(GovernedPersistenceRefused):
        save_governed_analysis(db, analysis_row=row, engagement_id=ENGAGEMENT_A,
                              envelope=execution.analysis.envelope, execution_provenance=data)
    assert not any(entry[0] == "rpc" for entry in db.log)


def test_single_rpc_carries_bound_analysis_envelope_and_receipt(execution):
    calls = []
    class Db:
        def rpc(self, name, params):
            calls.append((name, copy.deepcopy(params)))
            return SimpleNamespace(execute=lambda: SimpleNamespace(data=ANALYSIS))
    row = _analysis(); row["source_data_hash"] = execution.analysis.source_sha256.lower()
    save_governed_analysis(Db(), analysis_row=row, engagement_id=ENGAGEMENT_A,
                          envelope=execution.analysis.envelope, execution_provenance=execution.provenance)
    assert len(calls) == 1 and calls[0][0] == "persist_governed_execution_v1"
    params = calls[0][1]; receipt = params["p_receipt"]
    assert receipt["sha256"] == _digest(receipt["payload"])
    assert receipt["payload"]["analysis_id"] == ANALYSIS
    assert receipt["payload"]["company_id"] == COMPANY_A
    assert receipt["payload"]["envelope_sha256"] == params["p_envelope"]["envelope_sha256"]


def test_legacy_absence_is_not_mock_attestation():
    db = _db(); _save(db)
    assert load_execution_provenance(db, analysis_id=ANALYSIS, company_id=COMPANY_A,
                                    entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A) is None


def test_uncertain_ack_does_not_retry_or_fall_back(execution):
    calls = []
    class Db:
        def rpc(self, name, params):
            calls.append(name)
            return SimpleNamespace(execute=lambda: SimpleNamespace(data=None))
    row = _analysis(); row["source_data_hash"] = execution.analysis.source_sha256.lower()
    with pytest.raises(GovernedPersistenceRefused, match="ACK_UNCERTAIN"):
        save_governed_analysis(Db(), analysis_row=row, engagement_id=ENGAGEMENT_A,
                              envelope=execution.analysis.envelope, execution_provenance=execution.provenance)
    assert calls == ["persist_governed_execution_v1"]


def test_copied_model_with_forged_mode_is_revalidated(execution):
    forged = execution.provenance.model_copy(update={"provider_mode": "OPENAI"})
    with pytest.raises(ValueError):
        validate_execution(forged, envelope=execution.analysis.envelope,
                           raw_source_sha256=execution.analysis.source_sha256)


def test_receipt_reload_and_tamper_refusal(execution):
    db = _db()
    row = _analysis(); row["source_data_hash"] = execution.analysis.source_sha256.lower()
    save_governed_analysis(db, analysis_row=row, engagement_id=ENGAGEMENT_A, envelope=execution.analysis.envelope)
    scope = dict(analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A)
    payload = execution.provenance.model_dump(mode="json") | scope
    db.tables["governed_execution_receipts"] = [scope | {"payload": payload, "sha256": _digest(payload)}]
    assert load_execution_provenance(db, **scope) == execution.provenance
    payload["transport"] = "NETWORK"
    with pytest.raises(GovernedPersistenceRefused):
        load_execution_provenance(db, **scope)


def test_receipt_read_failure_is_not_legacy_absence(monkeypatch):
    db = _db(); _save(db)
    original = db.from_
    def query(table):
        if table == "governed_execution_receipts":
            raise RuntimeError("unavailable")
        return original(table)
    monkeypatch.setattr(db, "from_", query)
    with pytest.raises(GovernedPersistenceRefused, match="GOVERNED_EXECUTION_READ_REFUSED"):
        load_execution_provenance(db, analysis_id=ANALYSIS, company_id=COMPANY_A,
                                 entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A)


def test_v39_static_transaction_and_privilege_contract():
    sql = (Path(__file__).parents[1] / "migrations" / "v39_governed_execution_receipts.sql").read_text(encoding="utf-8")
    assert "BEGIN;" in sql and sql.rstrip().endswith("COMMIT;")
    assert "ENABLE ROW LEVEL SECURITY" in sql and "CREATE POLICY" not in sql
    assert "FROM PUBLIC, anon, authenticated, service_role" in sql
    assert "GRANT SELECT ON public.governed_execution_receipts TO service_role" in sql
    assert "BEFORE UPDATE OR DELETE" in sql and "ON DELETE RESTRICT" in sql
    assert "execution_id UUID NOT NULL UNIQUE" in sql
    assert "a := public.persist_governed_analysis_v1" in sql
    assert "ON CONFLICT" not in sql and "UPDATE public." not in sql
    assert "already or partially installed" in sql
