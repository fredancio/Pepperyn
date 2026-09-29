"""Unadmitted candidate for the bounded V1 financial-analysis producer.

The module composes an exact OpenAI Responses request from a claimed governed
snapshot, but contains no SDK, credential, URL or network operation.  Its
transport is injected for local conformance only.  The candidate is not a
provider admission, a real-data admission or a persistable execution receipt.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from typing import Any, Literal

from pydantic import Field, model_validator

from services.governed_analysis_persistence import _digest
from services.governed_producer_adapter import GovernedProducerInvocationV2
from services.producer_execution_contract import Digest, ExecutionBindingsV2, _Closed
from services.v1_analysis_contract import (
    GovernedFinancialAnalysis,
    UnderstandingResult,
    V1_FACT_SCHEMA_ID,
    V1_FACT_SCHEMA_VERSION,
    V1_OUTPUT_CONTRACT_ID,
    V1_OUTPUT_CONTRACT_VERSION,
    V1_POSITIVE_PROJECTION_POLICY_ID,
    V1_POSITIVE_PROJECTION_POLICY_VERSION,
    V1_TASK_ID,
    V1_TASK_INSTRUCTIONS,
    V1_TASK_VERSION,
    build_openai_request_from_understanding,
    parse_openai_response,
)


PRODUCER_ID = "openai-responses-financial-analysis"
PRODUCER_VERSION = "gpt-5-contract-v1"
TASK_ID = V1_TASK_ID
TASK_VERSION = V1_TASK_VERSION
MODEL = "gpt-5"
RECEIPT_CONTRACT_VERSION = "governed-generic-producer-receipt-3"


class GenericProducerCandidateRefused(RuntimeError):
    """Content-free refusal at the unadmitted candidate boundary."""


class GenericProducerCandidateProfile(_Closed):
    schema_version: Literal["generic-producer-candidate-profile-1"] = (
        "generic-producer-candidate-profile-1"
    )
    admission_state: Literal["UNADMITTED"] = "UNADMITTED"
    producer_id: Literal[PRODUCER_ID] = PRODUCER_ID
    producer_version: Literal[PRODUCER_VERSION] = PRODUCER_VERSION
    task_id: Literal[TASK_ID] = TASK_ID
    task_version: Literal[TASK_VERSION] = TASK_VERSION
    model: Literal[MODEL] = MODEL
    provider_origin: Literal["EXTERNAL_PROVIDER_PENDING"] = "EXTERNAL_PROVIDER_PENDING"
    data_origin: Literal["SYNTHETIC_ONLY"] = "SYNTHETIC_ONLY"
    egress_state: Literal["CLOSED"] = "CLOSED"
    allowed_data_classes: tuple[str, ...] = (
        "GOVERNED_SOURCE_FACTS",
        "INVOCATION_NONCE",
        "STATIC_TASK_INSTRUCTIONS",
    )
    forbidden_data_classes: tuple[str, ...] = (
        "RAW_SOURCE_BYTES",
        "REAL_WORLD_IDENTITY",
        "CORRESPONDENCE_MAPPING",
        "FREE_FORM_CLIENT_CONTEXT",
        "AUTHORIZATION_TOKEN",
        "TENANT_SCOPE_IDENTIFIERS",
        "PERSISTENCE_CAPABILITY",
    )
    receipt_contract_version: Literal[RECEIPT_CONTRACT_VERSION] = RECEIPT_CONTRACT_VERSION


PROFILE = GenericProducerCandidateProfile()
PROFILE_SHA256: Digest = _digest(PROFILE.model_dump(mode="json"))


FACT_SCHEMA_SHA256: Digest = _digest(UnderstandingResult.model_json_schema())
OUTPUT_CONTRACT_SHA256: Digest = _digest(GovernedFinancialAnalysis.model_json_schema())
POSITIVE_PROJECTION_POLICY_SHA256: Digest = _digest({
    "policy_id": V1_POSITIVE_PROJECTION_POLICY_ID,
    "policy_version": V1_POSITIVE_PROJECTION_POLICY_VERSION,
    "allowed_data_classes": PROFILE.allowed_data_classes,
    "forbidden_data_classes": PROFILE.forbidden_data_classes,
    "payload_keys": ("invocation_nonce", "source_facts"),
})
TASK_CONTRACT_SHA256: Digest = _digest({
    "task_id": TASK_ID,
    "task_version": TASK_VERSION,
    "instructions": V1_TASK_INSTRUCTIONS,
    "input_schema_sha256": FACT_SCHEMA_SHA256,
    "projection_policy_sha256": POSITIVE_PROJECTION_POLICY_SHA256,
    "output_contract_sha256": OUTPUT_CONTRACT_SHA256,
})


class DurableContractBindingV1(_Closed):
    """One immutable meaning for the bounded V1 producer contract."""

    schema_version: Literal["generic-durable-contract-binding-1"] = (
        "generic-durable-contract-binding-1"
    )
    producer_id: Literal[PRODUCER_ID] = PRODUCER_ID
    producer_version: Literal[PRODUCER_VERSION] = PRODUCER_VERSION
    fact_schema_id: Literal[V1_FACT_SCHEMA_ID] = V1_FACT_SCHEMA_ID
    fact_schema_version: Literal[V1_FACT_SCHEMA_VERSION] = V1_FACT_SCHEMA_VERSION
    fact_schema_sha256: Digest = FACT_SCHEMA_SHA256
    positive_projection_policy_id: Literal[V1_POSITIVE_PROJECTION_POLICY_ID] = (
        V1_POSITIVE_PROJECTION_POLICY_ID
    )
    positive_projection_policy_version: Literal[V1_POSITIVE_PROJECTION_POLICY_VERSION] = (
        V1_POSITIVE_PROJECTION_POLICY_VERSION
    )
    positive_projection_policy_sha256: Digest = POSITIVE_PROJECTION_POLICY_SHA256
    task_id: Literal[TASK_ID] = TASK_ID
    task_version: Literal[TASK_VERSION] = TASK_VERSION
    task_contract_sha256: Digest = TASK_CONTRACT_SHA256
    output_contract_id: Literal[V1_OUTPUT_CONTRACT_ID] = V1_OUTPUT_CONTRACT_ID
    output_contract_version: Literal[V1_OUTPUT_CONTRACT_VERSION] = V1_OUTPUT_CONTRACT_VERSION
    output_contract_sha256: Digest = OUTPUT_CONTRACT_SHA256
    receipt_contract_version: Literal[RECEIPT_CONTRACT_VERSION] = RECEIPT_CONTRACT_VERSION
    profile_sha256: Digest = PROFILE_SHA256


# This is a historical descriptor, not an alias for whatever the current Python
# models happen to become.  A later schema/task version must add a new entry;
# changing a model in place can therefore neither rewrite V1 nor make reread
# silently resolve to "latest".
_V1_HISTORICAL_BINDING = {
    "schema_version": "generic-durable-contract-binding-1",
    "producer_id": PRODUCER_ID,
    "producer_version": PRODUCER_VERSION,
    "fact_schema_id": "governed-source-facts",
    "fact_schema_version": "v1-understanding-result-1",
    "fact_schema_sha256": "1DA5F3CEB05FF5B856772BFE348CFF2AFF46C91E1E09275696BF8FB34BE34FC2",
    "positive_projection_policy_id": "governed-source-facts-positive-projection",
    "positive_projection_policy_version": "v1",
    "positive_projection_policy_sha256": "77EA1CD44A3F4F120A4DEF008EF4C708905CD5367509D16AB882E9A9B1EA093C",
    "task_id": TASK_ID,
    "task_version": TASK_VERSION,
    "task_contract_sha256": "6C9D7D766FA88E5EB1D981622177E616148448519DA76D794F6CE75BA236224E",
    "output_contract_id": "pepperyn-v1-governed-financial-analysis",
    "output_contract_version": "v1",
    "output_contract_sha256": "5CBCC0DA72BC154CF71A7B4D1832C54FE93C671A39D0CD3CF318DCCCA5906D61",
    "receipt_contract_version": RECEIPT_CONTRACT_VERSION,
    "profile_sha256": "2C371E0BA997BA7D8496C8F5AB2FC4BBB94D54ECADF897CB2AEAA3B966991F73",
}
CONTRACT_BINDING = DurableContractBindingV1.model_validate(_V1_HISTORICAL_BINDING)
GENERIC_ADMISSION_CONTRACT_SHA256: Digest = (
    "CDC4BC07EA6F67275B985E76B24467CC3A1A11891EFA1953E0F6137344F73645"
)
SUPPORTED_CONTRACT_BINDINGS = {GENERIC_ADMISSION_CONTRACT_SHA256: CONTRACT_BINDING}


def assert_current_v1_contract_is_pinned() -> None:
    """Refuse candidate execution after an unversioned contract mutation."""

    current = DurableContractBindingV1(
        fact_schema_sha256=FACT_SCHEMA_SHA256,
        positive_projection_policy_sha256=POSITIVE_PROJECTION_POLICY_SHA256,
        task_contract_sha256=TASK_CONTRACT_SHA256,
        output_contract_sha256=OUTPUT_CONTRACT_SHA256,
        profile_sha256=PROFILE_SHA256,
    )
    if (current != CONTRACT_BINDING
            or _digest(current.model_dump(mode="json"))
            != GENERIC_ADMISSION_CONTRACT_SHA256):
        raise GenericProducerCandidateRefused("GENERIC_CURRENT_CONTRACT_UNVERSIONED")


class CandidateTransportEvidence(_Closed):
    """Local conformance evidence, explicitly not a durable receipt."""

    schema_version: Literal["generic-producer-local-conformance-1"] = (
        "generic-producer-local-conformance-1"
    )
    evidence_status: Literal["UNADMITTED_LOCAL_CONFORMANCE"] = (
        "UNADMITTED_LOCAL_CONFORMANCE"
    )
    profile_sha256: Digest = PROFILE_SHA256
    request_sha256: Digest
    response_sha256: Digest
    source_representation_sha256: Digest
    invocation_nonce: str = Field(pattern=r"^[A-F0-9]{32}$")
    contract_binding_sha256: Literal[GENERIC_ADMISSION_CONTRACT_SHA256] = (
        GENERIC_ADMISSION_CONTRACT_SHA256
    )
    transport_mode: Literal["INJECTED_LOCAL_ONLY"] = "INJECTED_LOCAL_ONLY"
    provider_execution_attested: Literal[False] = False
    response_capture_sha256: Digest


class FrozenGenericProducerRequest(_Closed):
    """Backend-built request committed before any transport can see it."""

    schema_version: Literal["frozen-generic-producer-request-1"] = (
        "frozen-generic-producer-request-1"
    )
    contract_binding_sha256: Literal[GENERIC_ADMISSION_CONTRACT_SHA256] = (
        GENERIC_ADMISSION_CONTRACT_SHA256
    )
    invocation_nonce: str = Field(pattern=r"^[A-F0-9]{32}$")
    source_representation_sha256: Digest
    canonical_request: str
    request_sha256: Digest

    @model_validator(mode="after")
    def exact_request_digest(self) -> "FrozenGenericProducerRequest":
        if sha256(self.canonical_request.encode("utf-8")).hexdigest().upper() != self.request_sha256:
            raise ValueError("GENERIC_FROZEN_REQUEST_DIGEST_REFUSED")
        return self


class GenericProducerReceiptContractV3(_Closed):
    """Shape required from a future admitted durable receipt.

    No constructor in this module can mint ``ADMITTED_EXECUTION``.  The type is
    a versioned contract for the future database authority, not local authority.
    """

    schema_version: Literal[RECEIPT_CONTRACT_VERSION] = RECEIPT_CONTRACT_VERSION
    evidence_status: Literal["ADMITTED_EXECUTION"]
    bindings: ExecutionBindingsV2
    contract_binding: DurableContractBindingV1
    contract_binding_sha256: Digest
    request_sha256: Digest
    response_sha256: Digest
    projection_sha256: Digest
    envelope_sha256: Digest
    provider_policy_evidence_sha256: Digest

    @model_validator(mode="after")
    def exact_profile(self) -> "GenericProducerReceiptContractV3":
        if (
            self.bindings.producer_id != PRODUCER_ID
            or self.bindings.producer_version != PRODUCER_VERSION
            or self.bindings.task_id != TASK_ID
            or self.bindings.task_version != TASK_VERSION
            or self.bindings.admission_contract_sha256 != GENERIC_ADMISSION_CONTRACT_SHA256
            or _digest(self.contract_binding.model_dump(mode="json"))
               != self.contract_binding_sha256
        ):
            raise ValueError("GENERIC_RECEIPT_PROFILE_REFUSED")
        return self


def verify_generic_receipt_contract_v3(
    value: Mapping[str, Any] | GenericProducerReceiptContractV3,
    *,
    supported_contracts: Mapping[str, DurableContractBindingV1] = SUPPORTED_CONTRACT_BINDINGS,
) -> GenericProducerReceiptContractV3:
    """Reread one persisted receipt against its exact historical contract.

    Unknown bindings refuse.  There is deliberately no ``latest`` lookup and no
    reconstruction from the current task/profile constants.
    """

    try:
        payload = value.model_dump(mode="json") if isinstance(value, _Closed) else value
        receipt = GenericProducerReceiptContractV3.model_validate(payload)
        historical = supported_contracts.get(receipt.contract_binding_sha256)
        if historical is None or historical != receipt.contract_binding:
            raise ValueError("unsupported binding")
        return receipt
    except Exception:
        raise GenericProducerCandidateRefused("GENERIC_RECEIPT_CONTRACT_UNAVAILABLE") from None


InjectedTransport = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class InjectedOpenAIResponsesCandidate:
    """One-call local adapter around an injected, non-network transport."""

    def __init__(self, transport: InjectedTransport) -> None:
        if not callable(transport):
            raise GenericProducerCandidateRefused("GENERIC_TRANSPORT_CONFIGURATION_REFUSED")
        assert_current_v1_contract_is_pinned()
        self.__transport = transport
        self.__used = False
        self.__evidence: CandidateTransportEvidence | None = None

    def __call__(self, invocation: GovernedProducerInvocationV2) -> GovernedFinancialAnalysis:
        return self.execute_frozen(freeze_generic_producer_request(invocation), invocation)

    def execute_frozen(
        self,
        frozen: FrozenGenericProducerRequest,
        invocation: GovernedProducerInvocationV2,
    ) -> GovernedFinancialAnalysis:
        """Consume exactly the backend-frozen request; never rebuild after admission."""

        if self.__used:
            raise GenericProducerCandidateRefused("GENERIC_TRANSPORT_REPLAY_REFUSED")
        self.__used = True
        try:
            invocation = GovernedProducerInvocationV2.model_validate_json(
                invocation.model_dump_json()
            )
            if invocation.task_id != TASK_ID or invocation.task_version != TASK_VERSION:
                raise ValueError("task")
            frozen = FrozenGenericProducerRequest.model_validate_json(frozen.model_dump_json())
            expected = freeze_generic_producer_request(invocation)
            if frozen != expected:
                raise ValueError("reserved request mismatch")
            request_bytes = frozen.canonical_request.encode("utf-8")
            request = json.loads(request_bytes)
            response = self.__transport(json.loads(request_bytes))
            response_bytes = _canonical_bytes(response)
            analysis = parse_openai_response(
                json.loads(response_bytes), invocation.source_facts,
                invocation.invocation_nonce,
            )
            request_sha256 = sha256(request_bytes).hexdigest().upper()
            response_sha256 = sha256(response_bytes).hexdigest().upper()
            capture = _digest({
                "contract_binding_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
                "invocation_nonce": invocation.invocation_nonce,
                "request_sha256": request_sha256,
                "response_sha256": response_sha256,
                "source_representation_sha256": invocation.source_facts.source_representation_sha256,
                "transport_mode": "INJECTED_LOCAL_ONLY",
            })
            self.__evidence = CandidateTransportEvidence(
                request_sha256=request_sha256,
                response_sha256=response_sha256,
                source_representation_sha256=invocation.source_facts.source_representation_sha256,
                invocation_nonce=invocation.invocation_nonce,
                response_capture_sha256=capture,
            )
            return analysis
        except GenericProducerCandidateRefused:
            raise
        except Exception:
            raise GenericProducerCandidateRefused("GENERIC_PRODUCER_OUTPUT_REFUSED") from None

    def consume_local_evidence(self) -> CandidateTransportEvidence:
        evidence, self.__evidence = self.__evidence, None
        if evidence is None:
            raise GenericProducerCandidateRefused("GENERIC_CONFORMANCE_EVIDENCE_UNAVAILABLE")
        return evidence


def _assert_minimal_request(
    request: Mapping[str, Any], invocation: GovernedProducerInvocationV2,
) -> None:
    if request.get("model") != MODEL or request.get("store") is not False:
        raise ValueError("provider configuration")
    payload = json.loads(request["input"])
    if set(payload) != {"invocation_nonce", "source_facts"}:
        raise ValueError("projection widened")
    if payload["invocation_nonce"] != invocation.invocation_nonce:
        raise ValueError("nonce")
    if payload["source_facts"] != invocation.source_facts.model_dump(mode="json"):
        raise ValueError("source snapshot")
    serialized = json.dumps(request, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "actor_id", "company_id", "entity_id", "engagement_id", "analysis_id",
        "execution_id", "authorization", "correspondence_id", "real_identity",
    ):
        if forbidden in serialized:
            raise ValueError("forbidden data class")


def freeze_generic_producer_request(
    invocation: GovernedProducerInvocationV2,
) -> FrozenGenericProducerRequest:
    """Create the sole request eligible for later reservation and execution."""

    try:
        assert_current_v1_contract_is_pinned()
        invocation = GovernedProducerInvocationV2.model_validate_json(
            invocation.model_dump_json()
        )
        if invocation.task_id != TASK_ID or invocation.task_version != TASK_VERSION:
            raise ValueError("task")
        request = build_openai_request_from_understanding(
            invocation.source_facts,
            invocation_nonce=invocation.invocation_nonce,
            model=MODEL,
        )
        _assert_minimal_request(request, invocation)
        canonical = _canonical_bytes(request).decode("utf-8")
        return FrozenGenericProducerRequest(
            invocation_nonce=invocation.invocation_nonce,
            source_representation_sha256=invocation.source_facts.source_representation_sha256,
            canonical_request=canonical,
            request_sha256=sha256(canonical.encode("utf-8")).hexdigest().upper(),
        )
    except GenericProducerCandidateRefused:
        raise
    except Exception:
        raise GenericProducerCandidateRefused("GENERIC_REQUEST_FREEZE_REFUSED") from None


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
