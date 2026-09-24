"""Durable execution description, not a provider/admission authorization.

Only trusted backend execution adapters issue records. These are not accepted
from HTTP callers. Hashes bind content; they are not signatures or proof against
a compromised service-role backend. Legacy absence is never retro-certified.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from services.governed_analysis_persistence import _digest


class ExecutionProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")
    schema_version: Literal["execution-provenance-1"] = "execution-provenance-1"
    execution_id: UUID
    executor: Literal["registered-workbook-mock-v1"]
    data_origin: Literal["REGISTERED_SYNTHETIC"]
    provider_mode: Literal["LOCAL_MOCK"]
    transport: Literal["NONE"]
    raw_source_sha256: str = Field(pattern=r"^[A-F0-9]{64}$")
    source_representation_sha256: str = Field(pattern=r"^[A-F0-9]{64}$")
    envelope_sha256: str = Field(pattern=r"^[A-F0-9]{64}$")
    completed_at: datetime


def validate_execution(provenance, *, envelope, raw_source_sha256):
    record = ExecutionProvenance.model_validate(provenance)
    if (record.completed_at.tzinfo is None
            or record.raw_source_sha256 != raw_source_sha256.upper()
            or record.source_representation_sha256 != envelope.source_facts.source_representation_sha256
            or record.envelope_sha256 != _digest(envelope.model_dump(mode="json"))):
        raise ValueError("EXECUTION_BINDING_REFUSED")
    return record
