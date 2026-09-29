"""Unmounted V41 coordinator for one backend-controlled generic composition.

The only implemented transport path is explicitly injected/local.  This module
does not register a policy, select an arbitrary producer, mint Auth, or grant
egress.  Database acknowledgements are checked once and uncertain outcomes are
never retried under replacement identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Callable
from uuid import UUID

from services.generic_producer_candidate import (
    CONTRACT_BINDING,
    GENERIC_ADMISSION_CONTRACT_SHA256,
    CandidateTransportEvidence,
    FrozenGenericProducerRequest,
    GenericProducerReceiptContractV3,
    InjectedOpenAIResponsesCandidate,
    assert_current_v1_contract_is_pinned,
)
from services.governed_analysis_persistence import _binding, _canonical_bytes, _digest
from services.governed_producer_adapter import GovernedProducerInvocationV2
from services.producer_execution_contract import ExecutionBindingsV2
from services.v1_analysis_contract import (
    GovernedAnalysisEnvelope,
    UnderstandingResult,
    to_analysis_result,
)


class DurableGenericAdmissionRefused(RuntimeError):
    """Content-free terminal refusal; callers must inspect before any retry."""


@dataclass(frozen=True)
class PreparedGenericExecution:
    policy_id: UUID
    bindings: ExecutionBindingsV2
    source_facts: UnderstandingResult
    frozen_request: FrozenGenericProducerRequest
    filename: str


@dataclass(frozen=True)
class ReservedGenericExecution:
    prepared: PreparedGenericExecution
    composition_sha256: str
    provider_policy_evidence_sha256: str


@dataclass(frozen=True)
class ClaimedGenericExecution:
    reservation: ReservedGenericExecution
    claim_id: UUID
    claimed_at: datetime


PrincipalResolver = Callable[[str], object]


class DurableGenericProducerAdmission:
    """One exact V41 admission path; all authority remains backend-side."""

    def __init__(self, db, *, principal_resolver: PrincipalResolver) -> None:
        if not callable(principal_resolver):
            raise DurableGenericAdmissionRefused("V41_PRINCIPAL_RESOLVER_REFUSED")
        self._db = db
        self._principal_resolver = principal_resolver

    def _actor(self, authorization: str, bindings: ExecutionBindingsV2) -> str:
        principal = self._principal_resolver(authorization)
        if (getattr(principal, "principal_id", None) != str(bindings.actor_id)
                or getattr(principal, "company_id", None) != str(bindings.company_id)):
            raise DurableGenericAdmissionRefused("V41_ACTOR_REFUSED")
        return str(bindings.actor_id)

    @staticmethod
    def _prepared(value: PreparedGenericExecution, raw_source: bytes) -> PreparedGenericExecution:
        assert_current_v1_contract_is_pinned()
        if not isinstance(value, PreparedGenericExecution) or type(raw_source) is not bytes:
            raise ValueError("prepared input")
        bindings = ExecutionBindingsV2.model_validate_json(value.bindings.model_dump_json())
        facts = UnderstandingResult.model_validate_json(value.source_facts.model_dump_json())
        frozen = FrozenGenericProducerRequest.model_validate_json(
            value.frozen_request.model_dump_json())
        if (bindings.admission_contract_sha256 != GENERIC_ADMISSION_CONTRACT_SHA256
                or bindings.producer_input_sha256 != frozen.request_sha256
                or bindings.source_representation_sha256 != facts.source_representation_sha256
                or frozen.source_representation_sha256 != facts.source_representation_sha256
                or frozen.invocation_nonce != bindings.request_id.hex.upper()
                or facts.status != "UNDERSTOOD"
                or sha256(raw_source).hexdigest().upper() != bindings.raw_source_sha256):
            raise ValueError("whole composition")
        return PreparedGenericExecution(
            policy_id=UUID(str(value.policy_id)), bindings=bindings, source_facts=facts,
            frozen_request=frozen, filename=value.filename,
        )

    def reserve(self, prepared: PreparedGenericExecution, *, authorization: str,
                raw_source: bytes) -> ReservedGenericExecution:
        try:
            prepared = self._prepared(prepared, raw_source)
            self._actor(authorization, prepared.bindings)
            response = self._db.rpc("reserve_generic_execution_v3", {
                "p_policy": str(prepared.policy_id),
                "p_bindings": prepared.bindings.model_dump(mode="json"),
                "p_contract_binding": CONTRACT_BINDING.model_dump(mode="json"),
                "p_source_facts": prepared.source_facts.model_dump(mode="json"),
                "p_projection_text": prepared.frozen_request.canonical_request,
                "p_filename": prepared.filename,
                "p_ttl": 300,
            }).execute().data
            composition = response.get("composition_sha256", "")
            policy_evidence = response.get("provider_policy_evidence_sha256", "")
            if (response.get("status") != "RESERVED"
                    or response.get("execution_id") != str(prepared.bindings.execution_id)
                    or response.get("contract_binding_sha256") != GENERIC_ADMISSION_CONTRACT_SHA256
                    or not _digest_text(composition) or not _digest_text(policy_evidence)):
                raise ValueError("reservation acknowledgment")
            return ReservedGenericExecution(prepared, composition, policy_evidence)
        except DurableGenericAdmissionRefused:
            raise
        except Exception:
            raise DurableGenericAdmissionRefused(
                "V41_RESERVATION_UNCERTAIN_NO_RETRY") from None

    def claim(self, reservation: ReservedGenericExecution, *, authorization: str) -> ClaimedGenericExecution:
        try:
            if not isinstance(reservation, ReservedGenericExecution):
                raise ValueError("reservation")
            bindings = reservation.prepared.bindings
            actor = self._actor(authorization, bindings)
            response = self._db.rpc("claim_generic_execution_v3", {
                "p_execution": str(bindings.execution_id), "p_actor": actor,
                "p_composition": reservation.composition_sha256,
            }).execute().data
            stamp = datetime.fromisoformat(response["claimed_at"])
            if (response.get("status") != "CLAIMED"
                    or response.get("execution_id") != str(bindings.execution_id)
                    or response.get("composition_sha256") != reservation.composition_sha256
                    or ExecutionBindingsV2.model_validate(response.get("bindings")) != bindings
                    or response.get("contract_binding") != CONTRACT_BINDING.model_dump(mode="json")
                    or response.get("source_facts") != reservation.prepared.source_facts.model_dump(mode="json")
                    or response.get("projection_text") != reservation.prepared.frozen_request.canonical_request
                    or stamp.utcoffset() is None):
                raise ValueError("claim acknowledgment")
            return ClaimedGenericExecution(reservation, UUID(response["claim_id"]), stamp)
        except DurableGenericAdmissionRefused:
            raise
        except Exception:
            raise DurableGenericAdmissionRefused(
                "V41_CLAIM_UNCERTAIN_DO_NOT_EXECUTE") from None

    def execute_local_injected(
        self, claimed: ClaimedGenericExecution, *, authorization: str,
        producer: InjectedOpenAIResponsesCandidate,
    ) -> dict:
        """Execute and persist once; never label injected evidence as OpenAI-attested."""

        try:
            if not isinstance(claimed, ClaimedGenericExecution):
                raise ValueError("claim")
            # Producer selection is backend code, never caller-controlled duck
            # typing.  A subclass could replace capture/validation semantics.
            if type(producer) is not InjectedOpenAIResponsesCandidate:
                raise ValueError("producer identity")
            prepared, bindings = claimed.reservation.prepared, claimed.reservation.prepared.bindings
            actor = self._actor(authorization, bindings)
            invocation = GovernedProducerInvocationV2(
                task_id=bindings.task_id, task_version=bindings.task_version,
                invocation_nonce=bindings.request_id.hex.upper(),
                source_facts=prepared.source_facts,
            )
            analysis = producer.execute_frozen(prepared.frozen_request, invocation)
            evidence = CandidateTransportEvidence.model_validate(
                producer.consume_local_evidence())
            if (evidence.request_sha256 != bindings.producer_input_sha256
                    or evidence.source_representation_sha256
                       != bindings.source_representation_sha256
                    or evidence.invocation_nonce != bindings.request_id.hex.upper()
                    or evidence.provider_execution_attested is not False
                    or evidence.transport_mode != "INJECTED_LOCAL_ONLY"):
                raise ValueError("capture binding")
            analysis.validate_against(prepared.source_facts)
            envelope = GovernedAnalysisEnvelope(
                governed_analysis=analysis, source_facts=prepared.source_facts)
            payload = envelope.model_dump(mode="json")
            envelope_sha = _digest(payload)
            receipt = GenericProducerReceiptContractV3(
                evidence_status="ADMITTED_EXECUTION", bindings=bindings,
                contract_binding=CONTRACT_BINDING,
                contract_binding_sha256=GENERIC_ADMISSION_CONTRACT_SHA256,
                request_sha256=evidence.request_sha256,
                response_sha256=evidence.response_sha256,
                projection_sha256=prepared.frozen_request.request_sha256,
                envelope_sha256=envelope_sha,
                provider_policy_evidence_sha256=(
                    claimed.reservation.provider_policy_evidence_sha256),
            )
            result = to_analysis_result(analysis, prepared.source_facts).model_dump(mode="json")
            result["id"] = str(bindings.analysis_id)
            analysis_row = {
                "id": str(bindings.analysis_id), "company_id": str(bindings.company_id),
                "entity_id": str(bindings.entity_id), "fichier_nom": prepared.filename,
                "fichier_type": "xlsx", "type_document": "AUTRE",
                "analyse_json": result, "source_data_hash": bindings.raw_source_sha256.lower(),
                "status": "completed",
            }
            envelope_row = {
                "analysis_id": str(bindings.analysis_id),
                "company_id": str(bindings.company_id), "entity_id": str(bindings.entity_id),
                "engagement_id": str(bindings.engagement_id), "envelope_json": payload,
                "envelope_sha256": envelope_sha,
                "source_representation_sha256": bindings.source_representation_sha256,
                "envelope_schema_version": "v1-governed-analysis-1",
                "binding_sha256": _binding(
                    analysis_id=str(bindings.analysis_id), company_id=str(bindings.company_id),
                    entity_id=str(bindings.entity_id), engagement_id=str(bindings.engagement_id),
                    envelope_sha256=envelope_sha,
                    source_sha256=bindings.source_representation_sha256,
                ),
            }
            response = self._db.rpc("complete_generic_execution_v3", {
                "p_execution": str(bindings.execution_id), "p_actor": actor,
                "p_claim": str(claimed.claim_id), "p_receipt": receipt.model_dump(mode="json"),
                "p_analysis": analysis_row, "p_envelope": envelope_row,
                "p_envelope_text": _canonical_bytes(payload).decode("utf-8"),
            }).execute().data
            if (response.get("status") != "COMPLETE"
                    or response.get("analysis_id") != str(bindings.analysis_id)):
                raise ValueError("completion acknowledgment")
            return {
                "analysis_id": str(bindings.analysis_id),
                "status": "LOCAL_INJECTED_V41_PERSISTED",
                "provider_execution_attested": False,
                "external_provider_used": False,
            }
        except DurableGenericAdmissionRefused:
            raise
        except Exception:
            raise DurableGenericAdmissionRefused(
                "V41_COMPLETION_REFUSED_OR_UNCERTAIN_NO_RETRY") from None


def _digest_text(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789ABCDEF" for character in value))
