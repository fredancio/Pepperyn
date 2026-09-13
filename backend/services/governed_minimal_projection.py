"""Deterministic task-specific minimization before any model-provider egress.

This kernel does not call a provider and does not claim anonymization. It
creates an unforgeable in-process receipt binding one closed policy to the
exact canonical payload that the egress authority may serialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
import threading
from typing import Any, Iterable, Mapping

from services.information_state import TerminalOnlyReidentified

from services.ownership_authority import (
    OwnershipAuthority, OwnershipRefused, ProtectedReadGrant,
    ProtectedReadReceipt, ProjectionSourceAuthorization,
)
from services.pseudonymous_correspondence import (
    CorrespondenceRefused, CorrespondenceScope, GovernedCorrespondenceRegistry,
    ProjectionCorrespondenceBinding, PseudonymousReference,
    verify_projection_correspondence_binding,
)


POLICY_ID = "FINANCIAL_CHANGE_MINIMAL_V1"
TASK = "FINANCIAL_CHANGE_INTERPRETATION_V1"
_PSEUDONYM = re.compile(r"^(CUSTOMER|COUNTERPARTY|ENTITY)-[A-F0-9]{16}$")
_METRICS = frozenset({"REVENUE", "EBITDA", "NET_RESULT", "CASH"})
_SEAL = object()
_ISSUED: dict[int, "GovernedProjection"] = {}
_ISSUED_LOCK = threading.Lock()


class MinimalProjectionRefused(RuntimeError):
    """Content-free refusal; source values never enter the exception."""


@dataclass(frozen=True)
class ReceiptedFinancialChangeFact:
    metric_code: str
    metric_receipt: ProtectedReadReceipt
    previous_value: Decimal | int | float | str
    previous_receipt: ProtectedReadReceipt
    current_value: Decimal | int | float | str
    current_receipt: ProtectedReadReceipt


@dataclass(frozen=True)
class ProjectionLineage:
    company_id: str
    entity_id: str
    engagement_id: str
    analysis_id: str
    request_id: str
    correspondence_id: str
    mapping_version: int
    source_receipt_ids: frozenset[str]
    source_hashes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GovernedProjection:
    task: str
    policy_id: str
    payload: Mapping[str, Any]
    payload_hash: str
    identity_state: str
    residual_risk: str
    lineage: ProjectionLineage | None
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise MinimalProjectionRefused("PROJECTION_FORGED")


def compose_financial_change_v1(
    *, registry: GovernedCorrespondenceRegistry,
    correspondence_reference: PseudonymousReference,
    correspondence_scope: CorrespondenceScope,
    ownership_authority: OwnershipAuthority,
    read_grant: ProtectedReadGrant,
    request_id: str,
    facts: Iterable[ReceiptedFinancialChangeFact],
) -> GovernedProjection:
    """Coarsen exact two-period facts into a bounded qualitative projection.

    Exact amounts, dates, filenames, geography, sector, free text and mapping
    handles are not represented in the output schema.
    """

    rows = tuple(facts)
    if not rows or len(rows) > len(_METRICS):
        raise MinimalProjectionRefused("FACT_COUNT_INVALID")
    seen: set[str] = set()
    projected = []
    source_inputs: dict[str, tuple[Any, ProtectedReadReceipt]] = {}
    for index, fact in enumerate(rows):
        if not isinstance(fact, ReceiptedFinancialChangeFact):
            raise MinimalProjectionRefused("FACT_SCHEMA_INVALID")
        metric = fact.metric_code.strip().upper()
        if metric not in _METRICS or metric in seen:
            raise MinimalProjectionRefused("METRIC_NOT_ALLOWED")
        seen.add(metric)
        previous = _decimal(fact.previous_value)
        current = _decimal(fact.current_value)
        source_inputs[f"{index}.metric"] = (fact.metric_code, fact.metric_receipt)
        source_inputs[f"{index}.previous"] = (fact.previous_value, fact.previous_receipt)
        source_inputs[f"{index}.current"] = (fact.current_value, fact.current_receipt)
        projected.append({
            "metric": metric,
            "direction": _direction(previous, current),
            "change_band": _change_band(previous, current),
        })
    try:
        correspondence = registry.authorize_projection_reference(
            correspondence_reference, scope=correspondence_scope)
        source_authorization = ownership_authority.authorize_projection_sources(
            grant=read_grant, request_id=request_id, task=TASK,
            policy_id=POLICY_ID, inputs=source_inputs,
        )
        verify_projection_correspondence_binding(
            correspondence, company_id=source_authorization.scope.company_id,
            entity_id=source_authorization.scope.entity_id,
        )
    except (CorrespondenceRefused, OwnershipRefused) as exc:
        raise MinimalProjectionRefused("AUTHORITATIVE_COMPOSITION_REQUIRED") from exc
    subject_pseudonym = correspondence.pseudonym
    if not _PSEUDONYM.fullmatch(subject_pseudonym):
        raise MinimalProjectionRefused("PSEUDONYM_REQUIRED")
    payload = {
        "schema": POLICY_ID,
        "subject": subject_pseudonym,
        "periods": ["PREVIOUS", "CURRENT"],
        "metrics": sorted(projected, key=lambda row: row["metric"]),
    }
    lineage = _lineage(correspondence, source_authorization)
    return _mint(TASK, POLICY_ID, payload, "PSEUDONYMOUS",
        "D10_REDUCED_NOT_ANONYMOUS", lineage)


def verify_governed_projection(
    projection: GovernedProjection | None, *, task: str, payload: Mapping[str, Any],
    identity_state: str,
) -> None:
    if not isinstance(projection, GovernedProjection) or projection._seal is not _SEAL:
        raise MinimalProjectionRefused("MINIMAL_PROJECTION_REQUIRED")
    with _ISSUED_LOCK:
        if _ISSUED.pop(id(projection), None) is not projection:
            raise MinimalProjectionRefused("PROJECTION_FORGED_OR_REPLAYED")
    if (projection.task != task or projection.payload_hash != _canonical_hash(payload)
            or projection.identity_state != identity_state):
        raise MinimalProjectionRefused("PROJECTION_SCOPE_MISMATCH")
    if projection.policy_id != POLICY_ID and projection.policy_id != "SYNTHETIC_TEST_ONLY":
        raise MinimalProjectionRefused("PROJECTION_POLICY_UNKNOWN")
    if projection.policy_id == POLICY_ID and projection.lineage is None:
        raise MinimalProjectionRefused("PROJECTION_LINEAGE_REQUIRED")


def projection_binding_hash(projection: GovernedProjection) -> str:
    """Stable non-secret binding for the complete governed projection receipt."""

    if not isinstance(projection, GovernedProjection) or projection._seal is not _SEAL:
        raise MinimalProjectionRefused("MINIMAL_PROJECTION_REQUIRED")
    lineage = projection.lineage
    if lineage is None and projection.policy_id != "SYNTHETIC_TEST_ONLY":
        raise MinimalProjectionRefused("PROJECTION_LINEAGE_REQUIRED")
    material = {
        "task": projection.task,
        "policy_id": projection.policy_id,
        "payload_hash": projection.payload_hash,
        "identity_state": projection.identity_state,
        "lineage": None if lineage is None else {
            "company_id": lineage.company_id,
            "entity_id": lineage.entity_id,
            "engagement_id": lineage.engagement_id,
            "analysis_id": lineage.analysis_id,
            "request_id": lineage.request_id,
            "correspondence_id": lineage.correspondence_id,
            "mapping_version": lineage.mapping_version,
            "source_receipt_ids": sorted(lineage.source_receipt_ids),
            "source_hashes": list(lineage.source_hashes),
        },
    }
    return hashlib.sha256(_canonical_bytes(material)).hexdigest()


def _mint_synthetic_test_projection(*, task: str, payload: Mapping[str, Any]) -> GovernedProjection:
    """Compatibility for closed synthetic tests; never a real-data policy."""

    return _mint(task, "SYNTHETIC_TEST_ONLY", payload, "PSEUDONYMOUS", "TEST_ONLY_UNASSESSED", None)


def _mint(task: str, policy_id: str, payload: Mapping[str, Any], identity: str,
        risk: str, lineage: ProjectionLineage | None) -> GovernedProjection:
    frozen = json.loads(_canonical_bytes(payload))
    projection = GovernedProjection(task, policy_id, frozen, _canonical_hash(frozen),
        identity, risk, lineage, _SEAL)
    with _ISSUED_LOCK:
        _ISSUED[id(projection)] = projection
    return projection


def _lineage(
    correspondence: ProjectionCorrespondenceBinding,
    sources: ProjectionSourceAuthorization,
) -> ProjectionLineage:
    return ProjectionLineage(
        sources.scope.company_id, sources.scope.entity_id,
        sources.scope.engagement_id, sources.scope.analysis_id,
        sources.request_id, correspondence.correspondence_id,
        correspondence.mapping_version, sources.input_receipt_ids,
        sources.input_hashes,
    )


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    _reject_terminal_only(value)
    try:
        return json.dumps(dict(value), ensure_ascii=False, allow_nan=False,
            sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MinimalProjectionRefused("PROJECTION_NOT_CANONICAL") from exc


def _reject_terminal_only(value: Any) -> None:
    if isinstance(value, TerminalOnlyReidentified):
        raise MinimalProjectionRefused("REIDENTIFIED_TERMINAL_ONLY")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_terminal_only(key)
            _reject_terminal_only(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_terminal_only(nested)


def _canonical_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, bool):
        raise MinimalProjectionRefused("FINANCIAL_VALUE_INVALID")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MinimalProjectionRefused("FINANCIAL_VALUE_INVALID") from exc
    if not result.is_finite() or (isinstance(value, float) and not math.isfinite(value)):
        raise MinimalProjectionRefused("FINANCIAL_VALUE_INVALID")
    return result


def _direction(previous: Decimal, current: Decimal) -> str:
    return "UP" if current > previous else "DOWN" if current < previous else "FLAT"


def _change_band(previous: Decimal, current: Decimal) -> str:
    if previous == 0:
        return "NOT_COMPARABLE"
    magnitude = abs((current - previous) / abs(previous)) * Decimal(100)
    if magnitude < 2:
        return "LT_2_PERCENT"
    if magnitude < 5:
        return "2_TO_5_PERCENT"
    if magnitude < 10:
        return "5_TO_10_PERCENT"
    if magnitude < 20:
        return "10_TO_20_PERCENT"
    return "GE_20_PERCENT"
