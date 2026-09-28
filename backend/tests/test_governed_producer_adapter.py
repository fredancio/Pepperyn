"""Local-only falsification of the backend-owned V40 producer composition."""

import copy
import json
import socket
from dataclasses import replace
from uuid import uuid4

import pytest

from services.durable_producer_admission import ClaimedExecution
from services.governed_analysis_persistence import _digest
from services.governed_producer_adapter import (
    GovernedProducerAdapter,
    GovernedProducerCoordinator,
    ProducerAdapterRefused,
)
from sandbox.heterogeneous_workbooks import _mock_response
from test_durable_producer_admission import adapter as durable_adapter
from test_governed_producer_admission import RAW, system as admission_system

_REAL_SOCKET_CONNECT = socket.socket.connect


@pytest.fixture
def system(admission_system):
    """Expose the existing admission fixture under its original dependency name."""
    return admission_system


def _adapter(prepared, producer):
    b = prepared.bindings
    return GovernedProducerAdapter(
        producer=producer,
        producer_id=b.producer_id,
        producer_version=b.producer_version,
        task_id=b.task_id,
        task_version=b.task_version,
        admission_contract_sha256=b.admission_contract_sha256,
    )


def _valid_output(invocation):
    response = _mock_response(invocation.source_facts, invocation.invocation_nonce)
    return json.loads(response["output"][0]["content"][0]["text"])


def _run_async(coroutine):
    """Allow asyncio's Windows loopback self-pipe, never product egress."""
    import asyncio
    current = socket.socket.connect
    socket.socket.connect = _REAL_SOCKET_CONNECT
    try:
        return asyncio.run(coroutine)
    finally:
        socket.socket.connect = current


async def _run_happy(adapter_fixture):
    db, admission, prepared, calls, _ = adapter_fixture
    seen = []

    async def producer(invocation):
        seen.append(invocation)
        return _valid_output(invocation)

    bounded = _adapter(prepared, producer)
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    result = await GovernedProducerCoordinator(admission=admission, adapter=bounded).execute(
        reservation, authorization="Bearer owner"
    )
    return db, prepared, calls, seen, result


def test_exact_bounded_invocation_then_backend_owned_completion(durable_adapter):
    db, prepared, calls, seen, result = _run_async(_run_happy(durable_adapter))
    assert result == {
        "analysis_id": str(prepared.bindings.analysis_id),
        "status": "LOCAL_SYNTHETIC_PERSISTED",
        "generic_producer_admitted": False,
    }
    assert [name for name, _ in calls] == [
        "reserve_execution_v2", "claim_execution_v2", "complete_execution_v2"
    ]
    assert len(seen) == 1
    visible = seen[0].model_dump(mode="json")
    assert set(visible) == {
        "schema_version", "task_id", "task_version", "invocation_nonce", "source_facts"
    }
    serialized = json.dumps(visible)
    for forbidden in (
        prepared.bindings.actor_id, prepared.bindings.company_id,
        prepared.bindings.entity_id, prepared.bindings.engagement_id,
        prepared.bindings.analysis_id, prepared.bindings.execution_id,
    ):
        assert str(forbidden) not in serialized


def test_adapter_performs_no_network_egress(durable_adapter):
    attempts = []

    def blocked(*args, **kwargs):
        attempts.append((args, kwargs))
        raise AssertionError("NETWORK_FORBIDDEN")

    async def run_after_loop_exists():
        current = socket.socket.connect
        socket.socket.connect = blocked
        try:
            return await _run_happy(durable_adapter)
        finally:
            socket.socket.connect = current

    _run_async(run_after_loop_exists())
    assert attempts == []


@pytest.mark.parametrize("field", [
    "producer_id", "producer_version", "task_id", "task_version",
    "admission_contract_sha256",
])
def test_backend_profile_mismatch_refuses_before_claim_or_invocation(durable_adapter, field):
    _, admission, prepared, calls, _ = durable_adapter
    invoked = []

    async def producer(value):
        invoked.append(value)
        return {}

    b = prepared.bindings
    configuration = dict(
        producer=producer,
        producer_id=b.producer_id,
        producer_version=b.producer_version,
        task_id=b.task_id,
        task_version=b.task_version,
        admission_contract_sha256=b.admission_contract_sha256,
    )
    configuration[field] = "0" * 64 if field.endswith("sha256") else "different-version"
    bounded = GovernedProducerAdapter(**configuration)
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    before = list(calls)
    with __import__("pytest").raises(ProducerAdapterRefused, match="BINDING_REFUSED"):
        _run_async(GovernedProducerCoordinator(admission=admission, adapter=bounded).execute(
            reservation, authorization="Bearer owner"
        ))
    assert calls == before and invoked == []


def test_claimed_input_substitution_refuses_before_invocation(durable_adapter):
    db, admission, prepared, calls, _ = durable_adapter
    invoked = []
    bounded = _adapter(prepared, lambda value: invoked.append(value))
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    claimed = admission.claim(reservation, authorization="Bearer owner")
    forged = replace(claimed, input_text="{}")
    before = copy.deepcopy(db.tables)
    with __import__("pytest").raises(ProducerAdapterRefused, match="BEFORE_INVOCATION"):
        _run_async(bounded.invoke(forged))
    assert invoked == [] and db.tables == before and len(calls) == 2


def test_output_scope_injection_or_missing_contract_is_refused_without_completion(durable_adapter):
    db, admission, prepared, calls, _ = durable_adapter

    async def producer(invocation):
        return _valid_output(invocation) | {"company_id": str(uuid4())}

    bounded = _adapter(prepared, producer)
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    before = copy.deepcopy(db.tables)
    with pytest.raises(ProducerAdapterRefused, match="AFTER_INVOCATION"):
        _run_async(GovernedProducerCoordinator(admission=admission, adapter=bounded).execute(
            reservation, authorization="Bearer owner"
        ))
    assert [name for name, _ in calls] == ["reserve_execution_v2", "claim_execution_v2"]
    assert db.tables == before


@pytest.mark.parametrize("fault", ["nonce", "source", "fact"])
def test_output_nonce_source_or_fact_substitution_is_refused(
    durable_adapter, fault
):
    db, admission, prepared, calls, _ = durable_adapter

    async def producer(invocation):
        value = _valid_output(invocation)
        if fault == "nonce":
            value["invocation_nonce"] = "0" * 32
        elif fault == "source":
            value["source_representation_sha256"] = "0" * 64
        else:
            value["diagnosis_fact_ids"] = ["F000000000000"]
        return value

    bounded = _adapter(prepared, producer)
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    before = copy.deepcopy(db.tables)
    with pytest.raises(ProducerAdapterRefused, match="AFTER_INVOCATION"):
        _run_async(GovernedProducerCoordinator(admission=admission, adapter=bounded).execute(
            reservation, authorization="Bearer owner"
        ))
    assert [name for name, _ in calls] == ["reserve_execution_v2", "claim_execution_v2"]
    assert db.tables == before


def test_producer_error_is_sanitized_and_not_retried(durable_adapter):
    db, admission, prepared, calls, _ = durable_adapter
    invoked = []

    async def producer(invocation):
        invoked.append(invocation)
        raise RuntimeError("SECRET_PROVIDER_DIAGNOSTIC")

    bounded = _adapter(prepared, producer)
    reservation = admission.reserve(prepared, authorization="Bearer owner", raw=RAW)
    before = copy.deepcopy(db.tables)
    with pytest.raises(ProducerAdapterRefused) as error:
        _run_async(GovernedProducerCoordinator(admission=admission, adapter=bounded).execute(
            reservation, authorization="Bearer owner"
        ))
    assert str(error.value) == "PRODUCER_OUTPUT_REFUSED_AFTER_INVOCATION"
    assert len(invoked) == 1 and len(calls) == 2 and db.tables == before


def test_envelope_digest_remains_backend_constructed(durable_adapter):
    db, prepared, calls, _, _ = _run_async(_run_happy(durable_adapter))
    complete = calls[-1][1]
    envelope = complete["p_envelope"]["envelope_json"]
    assert complete["p_candidate"]["envelope_sha256"] == _digest(envelope)
    assert complete["p_candidate"]["bindings"] == prepared.bindings.model_dump(mode="json")
    assert complete["p_envelope"]["analysis_id"] == str(prepared.bindings.analysis_id)
