"""Local-only V41 coordinator proof; no network, Auth or remote database."""

from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest

from sandbox.heterogeneous_workbooks import _mock_response
from services.durable_generic_producer_admission import (
    DurableGenericAdmissionRefused,
    DurableGenericProducerAdmission,
    PreparedGenericExecution,
)
from services.bounded_producer_policy import BoundedLocalTestPolicyV1
from services.generic_producer_candidate import (
    CONTRACT_BINDING, GENERIC_ADMISSION_CONTRACT_SHA256,
    InjectedOpenAIResponsesCandidate,
    PRODUCER_ID,
    PRODUCER_VERSION,
    TASK_ID,
    TASK_VERSION,
    freeze_generic_producer_request,
)
from services.governed_producer_adapter import GovernedProducerInvocationV2
from services.v1_analysis_contract import UnderstandingResult
from test_governed_producer_admission import RAW, prepare, system as admission_system


POLICY = "85000000-0000-0000-0000-000000000001"
POLICY_EVIDENCE = "E" * 64


class Rpc:
    def __init__(self, db, name, params):
        self.db, self.name, self.params = db, name, deepcopy(params)

    def execute(self):
        self.db.calls.append((self.name, self.params))
        if self.name in self.db.fail:
            raise RuntimeError("uncertain")
        bindings = self.db.prepared.bindings
        if self.name == "reserve_generic_execution_v3":
            return SimpleNamespace(data={
                "status": "RESERVED", "execution_id": str(bindings.execution_id),
                "composition_sha256": "C" * 64,
                "contract_binding_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
                "provider_policy_evidence_sha256": POLICY_EVIDENCE,
            } | self.db.mutations.get(self.name, {}))
        if self.name == "claim_generic_execution_v3":
            return SimpleNamespace(data={
                "status": "CLAIMED", "execution_id": str(bindings.execution_id),
                "claim_id": str(uuid4()), "claimed_at": "2026-09-29T12:00:00+00:00",
                "composition_sha256": "C" * 64,
                "bindings": bindings.model_dump(mode="json"),
                "contract_binding": self.db.contract,
                "source_facts": self.db.prepared.source_facts.model_dump(mode="json"),
                "projection_text": self.db.prepared.frozen_request.canonical_request,
            } | self.db.mutations.get(self.name, {}))
        if self.name == "complete_generic_execution_v3":
            return SimpleNamespace(data={
                "status": "COMPLETE", "analysis_id": str(bindings.analysis_id),
            } | self.db.mutations.get(self.name, {}))
        raise AssertionError(self.name)


class Db:
    def __init__(self):
        self.calls, self.fail, self.mutations = [], set(), {}
        self.prepared = None
        from services.generic_producer_candidate import CONTRACT_BINDING
        self.contract = CONTRACT_BINDING.model_dump(mode="json")
        self.policy = None

    def rpc(self, name, params):
        return Rpc(self, name, params)

    def from_(self, name):
        assert name == "generic_producer_policies_v3"
        return PolicyQuery(self)


class PolicyQuery:
    def __init__(self, db):
        self.db, self.policy_id = db, None

    def select(self, fields):
        return self

    def eq(self, field, value):
        assert field == "id"
        self.policy_id = value
        return self

    def limit(self, value):
        assert value == 2
        return self

    def execute(self):
        rows = [] if self.db.policy is None else [deepcopy(self.db.policy)]
        if rows and rows[0]["id"] != self.policy_id:
            rows = []
        return SimpleNamespace(data=rows)


@pytest.fixture
def composed(admission_system):
    _, _, service = admission_system
    base = prepare(service)
    source = UnderstandingResult.model_validate_json(base.input_json)
    bindings = base.bindings.model_copy(update={
        "producer_id": PRODUCER_ID, "producer_version": PRODUCER_VERSION,
        "task_id": TASK_ID, "task_version": TASK_VERSION,
        "admission_contract_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
        "raw_source_sha256": sha256(RAW).hexdigest().upper(),
    })
    invocation = GovernedProducerInvocationV2(
        task_id=TASK_ID, task_version=TASK_VERSION,
        invocation_nonce=bindings.request_id.hex.upper(), source_facts=source,
    )
    frozen = freeze_generic_producer_request(invocation)
    bindings = bindings.model_copy(update={"producer_input_sha256": frozen.request_sha256})
    prepared = PreparedGenericExecution(
        policy_id=POLICY, bindings=bindings, source_facts=source,
        frozen_request=frozen, filename="synthetic.xlsx",
    )
    db = Db(); db.prepared = prepared
    specification = BoundedLocalTestPolicyV1(
        company_id=bindings.company_id, entity_id=bindings.entity_id,
        engagement_id=bindings.engagement_id,
        source_sha256=bindings.raw_source_sha256, filename=prepared.filename,
        policy_evidence_sha256=POLICY_EVIDENCE,
    ).model_dump(mode="json")
    db.policy = {
        "id": POLICY, "specification": specification,
        "contract_binding": CONTRACT_BINDING.model_dump(mode="json"),
        "contract_binding_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
        "enabled": True,
    }
    principal = lambda authorization: SimpleNamespace(
        principal_id=str(bindings.actor_id), company_id=str(bindings.company_id))
    return db, DurableGenericProducerAdmission(db, principal_resolver=principal), prepared


def test_exact_reserved_request_capture_builds_backend_receipt(composed):
    db, service, prepared = composed
    reserved = service.reserve(prepared, authorization="local", raw_source=RAW)
    claimed = service.claim(reserved, authorization="local")
    seen = []
    producer = InjectedOpenAIResponsesCandidate(
        lambda request: seen.append(request) or _mock_response(
            prepared.source_facts, prepared.bindings.request_id.hex.upper()))
    result = service.execute_local_injected(
        claimed, authorization="local", producer=producer)
    assert result == {
        "analysis_id": str(prepared.bindings.analysis_id),
        "status": "LOCAL_INJECTED_V41_PERSISTED",
        "provider_execution_attested": False,
        "external_provider_used": False,
    }
    assert len(seen) == 1
    complete = db.calls[-1][1]
    receipt = complete["p_receipt"]
    assert receipt["request_sha256"] == prepared.frozen_request.request_sha256
    assert receipt["provider_policy_evidence_sha256"] == POLICY_EVIDENCE
    assert receipt["response_sha256"] != receipt["request_sha256"]
    assert complete["p_envelope"]["envelope_json"]["source_facts"] == prepared.source_facts.model_dump(mode="json")
    assert [name for name, _ in db.calls] == [
        "reserve_generic_execution_v3", "claim_generic_execution_v3",
        "complete_generic_execution_v3",
    ]


@pytest.mark.parametrize("fault", ["raw", "request", "source", "actor"])
def test_pre_admission_substitution_refuses_without_rpc(composed, fault):
    db, service, prepared = composed
    raw = RAW
    if fault == "raw":
        raw += b"x"
    elif fault == "request":
        prepared = PreparedGenericExecution(
            prepared.policy_id,
            prepared.bindings.model_copy(update={"producer_input_sha256": "A" * 64}),
            prepared.source_facts, prepared.frozen_request, prepared.filename)
    elif fault == "source":
        prepared = PreparedGenericExecution(
            prepared.policy_id, prepared.bindings,
            prepared.source_facts.model_copy(update={"source_representation_sha256": "B" * 64}),
            prepared.frozen_request, prepared.filename)
    else:
        service = DurableGenericProducerAdmission(db, principal_resolver=lambda authorization:
            SimpleNamespace(principal_id=str(uuid4()), company_id=str(prepared.bindings.company_id)))
    with pytest.raises(DurableGenericAdmissionRefused):
        service.reserve(prepared, authorization="local", raw_source=raw)
    assert db.calls == []


@pytest.mark.parametrize("fault", [
    "decision", "admission_scope", "candidate_state", "global_status",
    "transport", "attestation", "egress", "scope", "disabled",
])
def test_policy_cannot_claim_global_admission_or_egress(composed, fault):
    db, service, prepared = composed
    specification = db.policy["specification"]
    if fault == "decision":
        specification["governance_decision_id"] = "DEC-UNKNOWN"
    elif fault == "admission_scope":
        specification["admission_scope"] = "GENERIC_PRODUCER_ADMITTED"
    elif fault == "candidate_state":
        specification["candidate_profile_state"] = "ADMITTED"
    elif fault == "global_status":
        specification["producer_global_status"] = "ADMITTED"
    elif fault == "transport":
        specification["transport_mode"] = "OPENAI_RESPONSES"
    elif fault == "attestation":
        specification["provider_execution_attested"] = True
    elif fault == "egress":
        specification["egress_authorization"] = "OPEN"
    elif fault == "scope":
        specification["company_id"] = str(uuid4())
    else:
        db.policy["enabled"] = False
    with pytest.raises(DurableGenericAdmissionRefused, match="NO_RETRY"):
        service.reserve(prepared, authorization="local", raw_source=RAW)
    assert db.calls == []


def test_claim_substitution_refuses_before_producer(composed):
    db, service, prepared = composed
    reserved = service.reserve(prepared, authorization="local", raw_source=RAW)
    db.mutations["claim_generic_execution_v3"] = {"projection_text": "substituted"}
    with pytest.raises(DurableGenericAdmissionRefused, match="DO_NOT_EXECUTE"):
        service.claim(reserved, authorization="local")
    assert [name for name, _ in db.calls] == [
        "reserve_generic_execution_v3", "claim_generic_execution_v3"]


def test_invalid_response_never_reaches_completion(composed):
    db, service, prepared = composed
    claimed = service.claim(service.reserve(
        prepared, authorization="local", raw_source=RAW), authorization="local")
    producer = InjectedOpenAIResponsesCandidate(lambda request: {"status": "incomplete"})
    with pytest.raises(DurableGenericAdmissionRefused, match="NO_RETRY"):
        service.execute_local_injected(
            claimed, authorization="local", producer=producer)
    assert [name for name, _ in db.calls].count("complete_generic_execution_v3") == 0


def test_producer_cannot_be_substituted_by_duck_typed_authority(composed):
    db, service, prepared = composed
    claimed = service.claim(service.reserve(
        prepared, authorization="local", raw_source=RAW), authorization="local")

    class SelfAdmittingProducer:
        def execute_frozen(self, frozen, invocation):
            raise AssertionError("substituted producer must never execute")

    with pytest.raises(DurableGenericAdmissionRefused, match="NO_RETRY"):
        service.execute_local_injected(
            claimed, authorization="local", producer=SelfAdmittingProducer())
    assert [name for name, _ in db.calls].count("complete_generic_execution_v3") == 0


def test_uncertain_completion_is_not_retried(composed):
    db, service, prepared = composed
    claimed = service.claim(service.reserve(
        prepared, authorization="local", raw_source=RAW), authorization="local")
    db.fail.add("complete_generic_execution_v3")
    producer = InjectedOpenAIResponsesCandidate(lambda request: _mock_response(
        prepared.source_facts, prepared.bindings.request_id.hex.upper()))
    with pytest.raises(DurableGenericAdmissionRefused, match="NO_RETRY"):
        service.execute_local_injected(
            claimed, authorization="local", producer=producer)
    assert [name for name, _ in db.calls].count("complete_generic_execution_v3") == 1
