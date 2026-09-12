"""Registered synthetic prerequisite evidence for the V1 execution rehearsal."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURE_ID = "PEPPERYN_V1_EXECUTION_PREREQUISITES"
FIXTURE_SHA256 = "9CBEFC35330E9503379E9C13524C6C868B276CD5BDF91AA48889D30F7DE716B9"
_FIXTURE = Path(__file__).parents[1] / "tests" / "golden" / "fixtures" / "pepperyn_v1_execution_prerequisites.json"


class PrerequisiteEvidenceRefused(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatedPrerequisiteEvidence:
    fixture_id: str
    payload_sha256: str
    period_start: date
    period_end: date
    provenance: str
    payload: dict[str, Any]


def load_validated_prerequisite_evidence() -> ValidatedPrerequisiteEvidence:
    try:
        payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest().upper()
        if digest != FIXTURE_SHA256:
            raise PrerequisiteEvidenceRefused("PREREQUISITE_FIXTURE_HASH_MISMATCH")
        period_start = date.fromisoformat(payload["period"]["start"])
        period_end = date.fromisoformat(payload["period"]["end"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_FIXTURE_INVALID") from exc

    provenance = payload.get("provenance", {})
    boundaries = payload.get("semantic_boundaries", {})
    if payload.get("fixture_id") != FIXTURE_ID or payload.get("synthetic") is not True:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_FIXTURE_IDENTITY_INVALID")
    if payload.get("evidence_role") != "DECISION_PREREQUISITE_ONLY":
        raise PrerequisiteEvidenceRefused("PREREQUISITE_ROLE_INVALID")
    if provenance.get("external_network_used") is not False or provenance.get("real_client_data_used") is not False:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_PROVENANCE_INVALID")
    if set(boundaries) != {"later_evidence", "actual_outcome", "learning", "expected_impact"}:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_BOUNDARY_INCOMPLETE")
    if any(value is not False for value in boundaries.values()):
        raise PrerequisiteEvidenceRefused("PREREQUISITE_BOUNDARY_VIOLATION")
    if payload.get("period", {}).get("frequency") != "MONTHLY" or period_end < period_start:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_PERIOD_INVALID")

    flows = payload.get("monthly_cash_flows")
    schedules = payload.get("customer_schedules")
    if not isinstance(flows, list) or len(flows) != 12 or not isinstance(schedules, list) or not schedules:
        raise PrerequisiteEvidenceRefused("PREREQUISITE_TABLES_INCOMPLETE")
    receipts_by_month: dict[str, int] = defaultdict(int)
    refs: set[str] = set()
    for row in schedules:
        ref = row.get("invoice_ref")
        if not isinstance(ref, str) or ref in refs or row.get("currency") != "EUR":
            raise PrerequisiteEvidenceRefused("PREREQUISITE_SCHEDULE_INVALID")
        refs.add(ref)
        collection_date = date.fromisoformat(row["projected_collection_date"])
        amount = row.get("amount")
        if not isinstance(amount, int) or amount <= 0:
            raise PrerequisiteEvidenceRefused("PREREQUISITE_SCHEDULE_INVALID")
        receipts_by_month[collection_date.strftime("%Y-%m")] += amount

    previous_close = None
    for row in flows:
        month = row.get("month")
        required = ("opening_cash", "customer_receipts", "other_operating_inflows", "payroll",
                    "supplier_payments", "taxes", "other_operating_outflows", "net_cash_flow", "closing_cash")
        if not isinstance(month, str) or any(not isinstance(row.get(key), int) for key in required):
            raise PrerequisiteEvidenceRefused("PREREQUISITE_CASH_FLOW_INVALID")
        calculated = (row["customer_receipts"] + row["other_operating_inflows"] - row["payroll"]
                      - row["supplier_payments"] - row["taxes"] - row["other_operating_outflows"])
        if calculated != row["net_cash_flow"] or row["opening_cash"] + calculated != row["closing_cash"]:
            raise PrerequisiteEvidenceRefused("PREREQUISITE_CASH_FLOW_NOT_RECONCILED")
        if previous_close is not None and row["opening_cash"] != previous_close:
            raise PrerequisiteEvidenceRefused("PREREQUISITE_CASH_ROLLFORWARD_INVALID")
        if row["customer_receipts"] != receipts_by_month.get(month):
            raise PrerequisiteEvidenceRefused("PREREQUISITE_SCHEDULE_NOT_RECONCILED")
        previous_close = row["closing_cash"]

    return ValidatedPrerequisiteEvidence(
        fixture_id=FIXTURE_ID, payload_sha256=digest.lower(), period_start=period_start,
        period_end=period_end, provenance=provenance["source"], payload=payload,
    )
