"""Unadmitted v2 execution candidates: consistency checking, NEVER admission.

No issuer, route, transport, database adapter or grant is supplied here. A hash
or a successful validation cannot establish ownership, source truth, permission,
producer trust, privacy compliance or replay protection. Expected bindings must
eventually come from the trusted execution coordinator, not the HTTP caller.
V39 and execution-provenance-1 deliberately do not accept this contract.
"""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.governed_analysis_persistence import _digest
from services.v1_analysis_contract import GovernedAnalysisEnvelope


Digest = Annotated[str, Field(pattern=r"^[A-F0-9]{64}$")]
VersionedName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{2,95}$")]


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class ExecutionBindingsV2(_Closed):
    """Description of the exact prospective execution, not an authority token."""

    request_id: UUID
    actor_id: UUID
    execution_id: UUID
    analysis_id: UUID
    company_id: UUID
    entity_id: UUID
    engagement_id: UUID
    producer_id: VersionedName
    producer_version: VersionedName
    task_id: VersionedName
    task_version: VersionedName
    admission_contract_sha256: Digest
    raw_source_sha256: Digest
    source_representation_sha256: Digest
    producer_input_sha256: Digest

    @model_validator(mode="after")
    def distinct_from_registered_mock(self):
        if self.producer_id == "registered-workbook-mock-v1":
            raise ValueError("V1_MOCK_ID_RESERVED")
        return self


class ProducerExecutionCandidateV2(_Closed):
    schema_version: Literal["producer-execution-candidate-2"] = "producer-execution-candidate-2"
    evidence_status: Literal["UNADMITTED_CANDIDATE"] = "UNADMITTED_CANDIDATE"
    bindings: ExecutionBindingsV2
    envelope_sha256: Digest
    started_at: datetime
    completed_at: datetime

    @model_validator(mode="after")
    def chronological(self):
        if (self.started_at.utcoffset() is None or self.completed_at.utcoffset() is None
                or self.completed_at < self.started_at):
            raise ValueError("EXECUTION_TIME_REFUSED")
        return self


def validate_candidate_consistency(candidate, *, expected_bindings, envelope):
    """Return an UNADMITTED candidate, not a persistable execution receipt.

    The caller cannot establish authority by supplying matching expected data.
    This function only rejects internal inconsistencies. It intentionally does
    not mark a candidate as admitted, verified, persisted, synthetic or real.
    """
    try:
        record = ProducerExecutionCandidateV2.model_validate(candidate)
        expected = ExecutionBindingsV2.model_validate(expected_bindings)
        # JSON round-trip forces nested envelope revalidation, including models
        # built using model_construct/model_copy (not trusted just for their type).
        payload = envelope.model_dump(mode="json") if isinstance(envelope, BaseModel) else envelope
        checked_envelope = GovernedAnalysisEnvelope.model_validate(payload)
        if (record.bindings != expected
                or record.bindings.source_representation_sha256
                != checked_envelope.source_facts.source_representation_sha256
                or record.envelope_sha256 != _digest(checked_envelope.model_dump(mode="json"))):
            raise ValueError("binding")
    except Exception:
        # Do not surface source contents, scope identifiers or provider payloads.
        raise ValueError("PRODUCER_CANDIDATE_INCONSISTENT") from None
    return record
