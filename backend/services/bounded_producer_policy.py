"""Exact bounded policy contract for the synthetic V41 rehearsal.

The candidate profile is immutable historical identity, not current authority.
Authority for one execution comes from an immutable, enabled V41 policy created
under the named governance decision. This module grants no egress, provider
attestation, real-data admission or global producer admission.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from services.generic_producer_candidate import (
    CONTRACT_BINDING,
    GENERIC_ADMISSION_CONTRACT_SHA256,
    PROFILE_SHA256,
    PRODUCER_ID,
    PRODUCER_VERSION,
    TASK_ID,
    TASK_VERSION,
)
from services.producer_execution_contract import Digest, ExecutionBindingsV2, _Closed


POLICY_SCHEMA_VERSION = "bounded-producer-policy-1"
GOVERNANCE_DECISION_ID = "DEC-035"
GOVERNANCE_DECISION_VERSION = "1"


class BoundedLocalTestPolicyV1(_Closed):
    """One exact synthetic/no-egress policy; never global admission."""

    schema_version: Literal[POLICY_SCHEMA_VERSION] = POLICY_SCHEMA_VERSION
    governance_decision_id: Literal[GOVERNANCE_DECISION_ID] = GOVERNANCE_DECISION_ID
    governance_decision_version: Literal[GOVERNANCE_DECISION_VERSION] = (
        GOVERNANCE_DECISION_VERSION
    )
    admission_scope: Literal["LOCAL_TEST_ADMISSION"] = "LOCAL_TEST_ADMISSION"
    candidate_profile_state: Literal["UNADMITTED"] = "UNADMITTED"
    producer_global_status: Literal["UNADMITTED"] = "UNADMITTED"
    company_id: UUID
    entity_id: UUID
    engagement_id: UUID
    producer_id: Literal[PRODUCER_ID] = PRODUCER_ID
    producer_version: Literal[PRODUCER_VERSION] = PRODUCER_VERSION
    task_id: Literal[TASK_ID] = TASK_ID
    task_version: Literal[TASK_VERSION] = TASK_VERSION
    source_sha256: Digest
    filename: str
    data_origin: Literal["SYNTHETIC_ONLY"] = "SYNTHETIC_ONLY"
    transport_mode: Literal["INJECTED_LOCAL_ONLY"] = "INJECTED_LOCAL_ONLY"
    provider_execution_attested: Literal[False] = False
    egress_authorization: Literal["CLOSED"] = "CLOSED"
    real_data_admission: Literal["CLOSED"] = "CLOSED"
    profile_sha256: Literal[PROFILE_SHA256] = PROFILE_SHA256
    contract_binding_sha256: Literal[GENERIC_ADMISSION_CONTRACT_SHA256] = (
        GENERIC_ADMISSION_CONTRACT_SHA256
    )
    policy_evidence_sha256: Digest


def verify_bounded_local_test_policy(
    policy: object,
    *,
    bindings: ExecutionBindingsV2,
    filename: str,
    require_enabled: bool,
) -> BoundedLocalTestPolicyV1:
    """Validate policy authority and exact execution scope, fail closed."""

    if not isinstance(policy, dict) or type(policy.get("enabled")) is not bool:
        raise ValueError("policy row")
    if require_enabled and policy.get("enabled") is not True:
        raise ValueError("policy disabled")
    if (
        policy.get("contract_binding") != CONTRACT_BINDING.model_dump(mode="json")
        or policy.get("contract_binding_sha256") != GENERIC_ADMISSION_CONTRACT_SHA256
    ):
        raise ValueError("policy contract")
    specification = BoundedLocalTestPolicyV1.model_validate(policy.get("specification"))
    expected = {
        "company_id": bindings.company_id,
        "entity_id": bindings.entity_id,
        "engagement_id": bindings.engagement_id,
        "producer_id": bindings.producer_id,
        "producer_version": bindings.producer_version,
        "task_id": bindings.task_id,
        "task_version": bindings.task_version,
        "source_sha256": bindings.raw_source_sha256,
    }
    for field, value in expected.items():
        if str(getattr(specification, field)) != str(value):
            raise ValueError("policy scope")
    if specification.filename != filename:
        raise ValueError("policy filename")
    return specification
