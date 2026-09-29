"""Local contract tests for the genuine-producer candidate; never egress."""

import json
import socket

import pytest

from sandbox.heterogeneous_workbooks import _mock_response
from services.generic_producer_candidate import (
    GenericProducerCandidateRefused,
    GenericProducerReceiptContractV3,
    GENERIC_ADMISSION_CONTRACT_SHA256,
    InjectedOpenAIResponsesCandidate,
    MODEL,
    PRODUCER_ID,
    PRODUCER_VERSION,
    PROFILE,
    PROFILE_SHA256,
    RECEIPT_CONTRACT_VERSION,
    TASK_ID,
    TASK_VERSION,
)
from services.governed_producer_adapter import GovernedProducerInvocationV2
from services.producer_execution_contract import ExecutionBindingsV2
from services.v1_analysis_contract import UnderstandingResult
from test_governed_producer_admission import RAW, prepare, system as admission_system


@pytest.fixture
def invocation(admission_system):
    _, _, service = admission_system
    prepared = prepare(service)
    understanding = UnderstandingResult.model_validate_json(prepared.input_json)
    return GovernedProducerInvocationV2(
        task_id=TASK_ID,
        task_version=TASK_VERSION,
        invocation_nonce=prepared.bindings.request_id.hex.upper(),
        source_facts=understanding,
    )


def response(invocation):
    return _mock_response(invocation.source_facts, invocation.invocation_nonce)


def test_profile_is_exact_closed_and_unadmitted():
    assert PROFILE.admission_state == "UNADMITTED"
    assert PROFILE.egress_state == "CLOSED"
    assert PROFILE.data_origin == "SYNTHETIC_ONLY"
    assert PROFILE.model == MODEL == "gpt-5"
    assert PROFILE.producer_id == PRODUCER_ID
    assert PROFILE.producer_version == PRODUCER_VERSION
    assert PROFILE.task_id == TASK_ID
    assert PROFILE.task_version == TASK_VERSION
    assert len(PROFILE_SHA256) == 64
    assert "RAW_SOURCE_BYTES" in PROFILE.forbidden_data_classes
    assert "REAL_WORLD_IDENTITY" in PROFILE.forbidden_data_classes


def test_injected_candidate_sees_only_positive_minimal_projection(invocation):
    seen = []
    producer = InjectedOpenAIResponsesCandidate(
        lambda request: seen.append(request) or response(invocation)
    )
    result = producer(invocation)
    assert result.invocation_nonce == invocation.invocation_nonce
    assert len(seen) == 1
    request = seen[0]
    assert request["model"] == MODEL and request["store"] is False
    payload = json.loads(request["input"])
    assert set(payload) == {"invocation_nonce", "source_facts"}
    assert payload["source_facts"] == invocation.source_facts.model_dump(mode="json")
    serialized = json.dumps(request)
    for forbidden in (
        "actor_id", "company_id", "entity_id", "engagement_id",
        "analysis_id", "execution_id", "authorization", "real_identity",
    ):
        assert forbidden not in serialized
    evidence = producer.consume_local_evidence()
    assert evidence.evidence_status == "UNADMITTED_LOCAL_CONFORMANCE"
    assert evidence.profile_sha256 == PROFILE_SHA256
    with pytest.raises(GenericProducerCandidateRefused, match="EVIDENCE_UNAVAILABLE"):
        producer.consume_local_evidence()


def test_transport_is_single_use_and_no_fallback(invocation):
    producer = InjectedOpenAIResponsesCandidate(lambda request: response(invocation))
    producer(invocation)
    with pytest.raises(GenericProducerCandidateRefused, match="REPLAY_REFUSED"):
        producer(invocation)


@pytest.mark.parametrize("fault", ["nonce", "source", "shape", "status"])
def test_response_substitution_refuses_without_evidence(invocation, fault):
    def transport(request):
        value = response(invocation)
        if fault == "status":
            value["status"] = "incomplete"
            value["incomplete_details"] = {"reason": "max_output_tokens"}
        elif fault == "shape":
            value["output"] = []
        else:
            payload = json.loads(value["output"][0]["content"][0]["text"])
            payload["invocation_nonce" if fault == "nonce" else "source_representation_sha256"] = (
                "0" * (32 if fault == "nonce" else 64)
            )
            value["output"][0]["content"][0]["text"] = json.dumps(payload)
        return value

    producer = InjectedOpenAIResponsesCandidate(transport)
    with pytest.raises(GenericProducerCandidateRefused, match="OUTPUT_REFUSED"):
        producer(invocation)
    with pytest.raises(GenericProducerCandidateRefused, match="EVIDENCE_UNAVAILABLE"):
        producer.consume_local_evidence()


def test_candidate_performs_no_network_egress(invocation, monkeypatch):
    attempts = []

    def blocked(*args, **kwargs):
        attempts.append((args, kwargs))
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    InjectedOpenAIResponsesCandidate(lambda request: response(invocation))(invocation)
    assert attempts == []


def test_future_receipt_contract_rejects_wrong_profile(admission_system):
    _, _, service = admission_system
    prepared = prepare(service)
    b = prepared.bindings.model_copy(update={
        "producer_id": PRODUCER_ID,
        "producer_version": PRODUCER_VERSION,
        "task_id": TASK_ID,
        "task_version": TASK_VERSION,
        "admission_contract_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
    })
    values = dict(
        evidence_status="ADMITTED_EXECUTION",
        bindings=b,
        profile_sha256=PROFILE_SHA256,
        request_sha256="1" * 64,
        response_sha256="2" * 64,
        projection_sha256="3" * 64,
        envelope_sha256="4" * 64,
        provider_policy_evidence_sha256="5" * 64,
    )
    receipt = GenericProducerReceiptContractV3(**values)
    assert receipt.schema_version == RECEIPT_CONTRACT_VERSION
    with pytest.raises(ValueError, match="GENERIC_RECEIPT_PROFILE_REFUSED"):
        GenericProducerReceiptContractV3(**{
            **values,
            "bindings": b.model_copy(update={"producer_version": "foreign-version"}),
        })
