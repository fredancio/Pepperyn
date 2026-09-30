"""Actual isolated-PostgreSQL checks for the V41 successor handoff."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sandbox.v41_injected_rehearsal import (
    FAILED_POLICY_CONTRACT_BINDING_SHA256,
    FAILED_POLICY_EVIDENCE_SHA256,
    FAILED_POLICY_ID,
    SCOPE,
    canonical_bytes,
    policy_insert_sql,
    specification_without_evidence,
)
from services.generic_producer_candidate import CONTRACT_BINDING
from test_generic_receipt_v3_postgres import v3sql  # noqa: F401
from test_v40_postgres import js, literal, sql  # noqa: F401


def manifest(deadline: datetime) -> dict:
    return {
        "identities": {
            "policy_id": str(uuid4()),
            "request_id": str(uuid4()),
            "execution_id": str(uuid4()),
            "analysis_id": str(uuid4()),
        },
        "scope": SCOPE,
        "owner_action_deadline": deadline.isoformat(),
    }


def test_successor_sql_refuses_late_insert_then_accepts_exact_history(v3sql):
    failed_manifest = manifest(datetime.now(timezone.utc) + timedelta(minutes=5))
    failed_spec = specification_without_evidence(failed_manifest)
    failed_spec["policy_evidence_sha256"] = FAILED_POLICY_EVIDENCE_SHA256
    binding = CONTRACT_BINDING.model_dump(mode="json")
    binding_text = canonical_bytes(binding).decode("utf-8")
    v3sql(
        "INSERT INTO generic_producer_policies_v3("
        "id,specification,contract_binding,contract_binding_text,"
        "contract_binding_sha256,enabled) VALUES ("
        f"{literal(FAILED_POLICY_ID)},{js(failed_spec)},{js(binding)},"
        f"{literal(binding_text)},{literal(FAILED_POLICY_CONTRACT_BINDING_SHA256)},true)"
    )
    v3sql(
        "UPDATE generic_producer_policies_v3 SET enabled=false WHERE id="
        + literal(FAILED_POLICY_ID)
    )

    expired = manifest(datetime.now(timezone.utc) - timedelta(seconds=1))
    error = v3sql(policy_insert_sql(expired), fail=True)
    assert "V41_OWNER_ACTION_DEADLINE_EXPIRED" in error
    assert v3sql("SELECT count(*) FROM generic_producer_policies_v3") == "1"

    successor = manifest(datetime.now(timezone.utc) + timedelta(minutes=5))
    v3sql(policy_insert_sql(successor))
    assert v3sql("SELECT count(*) FROM generic_producer_policies_v3") == "2"
    assert v3sql(
        "SELECT enabled FROM generic_producer_policies_v3 WHERE id="
        + literal(FAILED_POLICY_ID)
    ) == "f"
    assert v3sql(
        "SELECT enabled FROM generic_producer_policies_v3 WHERE id="
        + literal(successor["identities"]["policy_id"])
    ) == "t"
