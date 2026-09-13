"""Governed return path for one bounded mock-provider task.

Provider material remains non-canonical. Re-identification is a local,
single-use, ownership-authorized terminal transformation with no egress type.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import threading
from collections.abc import Iterator
from typing import Any, Mapping

from services.governed_minimal_projection import (
    GovernedProjection, POLICY_ID, TASK, projection_binding_hash,
)
from services.llm_egress import (
    EgressRefused, EgressResult,
    consume_egress_result_receipt,
)
from services.information_state import TerminalOnlyReidentified
from services.ownership_authority import (
    OwnershipRefused, OwnershipScope, RehydrationAuthorization,
    consume_rehydration_authorization,
)
from services.pseudonymous_correspondence import (
    CorrespondenceRefused, CorrespondenceScope, GovernedCorrespondenceRegistry,
    PseudonymousReference, verify_projection_correspondence_binding,
)


_SEAL = object()
_ISSUED: dict[int, "ValidatedProviderInference"] = {}
_LOCK = threading.Lock()
_ASSESSMENTS = frozenset({"MATERIAL_CHANGE", "LIMITED_CHANGE", "NOT_COMPARABLE"})


class ProviderResponseRefused(RuntimeError):
    """Content-free refusal for all untrusted return-path failures."""


@dataclass(frozen=True)
class ValidatedProviderInference:
    task: str
    request_id: str
    projection_binding_hash: str
    projection_payload_hash: str
    response_hash: str
    payload: Mapping[str, Any]
    epistemic_state: str
    correspondence_id: str
    mapping_version: int
    scope: OwnershipScope
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise ProviderResponseRefused("PROVIDER_INFERENCE_FORGED")


class AuthorizedTerminalOutput(TerminalOnlyReidentified):
    """Opaque terminal-only result; cannot be serialized by LLM egress."""

    __slots__ = ("__content", "response_hash", "projection_binding_hash")

    def __init__(self, content: Mapping[str, Any], *, response_hash: str,
                 projection_binding_hash: str) -> None:
        self.__content = _freeze_copy(content)
        self.response_hash = response_hash
        self.projection_binding_hash = projection_binding_hash

    def render_terminal(self) -> "TerminalRenderView":
        return TerminalRenderView(self.__content)

    def __repr__(self) -> str:
        return "<AUTHORIZED_TERMINAL_REIDENTIFIED>"


class TerminalRenderView(TerminalOnlyReidentified, Mapping[str, Any]):
    """Read-only UI view that retains the terminal-only information state."""

    __slots__ = ("__content",)

    def __init__(self, content: Mapping[str, Any]) -> None:
        self.__content = _freeze_copy(content)

    def __getitem__(self, key: str) -> Any:
        return self.__content[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__content)

    def __len__(self) -> int:
        return len(self.__content)

    def __repr__(self) -> str:
        return "<TERMINAL_RENDER_VIEW>"


def quarantine_and_validate_mock_response(
    *, result: EgressResult, projection: GovernedProjection,
) -> ValidatedProviderInference:
    """Consume the response receipt and accept only one closed response schema."""

    if (
        projection.task != TASK or projection.policy_id != POLICY_ID
        or projection.lineage is None
    ):
        raise ProviderResponseRefused("RESPONSE_PROJECTION_REQUIRED")
    binding_hash = projection_binding_hash(projection)
    try:
        raw = consume_egress_result_receipt(
            result, task=projection.task, request_id=projection.lineage.request_id,
            payload_hash=projection.payload_hash,
            expected_projection_binding_hash=binding_hash,
        )
    except EgressRefused as exc:
        raise ProviderResponseRefused("RESPONSE_RECEIPT_INVALID") from exc
    normalized = _validate_schema(raw, projection.payload)
    response_hash = _canonical_hash(normalized)
    lineage = projection.lineage
    validated = ValidatedProviderInference(
        TASK, lineage.request_id, binding_hash, projection.payload_hash,
        response_hash, normalized, "PROVIDER_INFERENCE_NOT_CANONICAL",
        lineage.correspondence_id, lineage.mapping_version,
        OwnershipScope(lineage.company_id, lineage.entity_id,
                       lineage.engagement_id, lineage.analysis_id), _SEAL,
    )
    with _LOCK:
        _ISSUED[id(validated)] = validated
    return validated


def rehydrate_for_authorized_terminal(
    *, validated: ValidatedProviderInference,
    registry: GovernedCorrespondenceRegistry,
    reference: PseudonymousReference,
    authorization: RehydrationAuthorization,
) -> AuthorizedTerminalOutput:
    """Resolve one proven pseudonym locally after exact ownership authorization."""

    if not isinstance(validated, ValidatedProviderInference) or validated._seal is not _SEAL:
        raise ProviderResponseRefused("PROVIDER_INFERENCE_INVALID")
    with _LOCK:
        if _ISSUED.pop(id(validated), None) is not validated:
            raise ProviderResponseRefused("PROVIDER_INFERENCE_FORGED_OR_REPLAYED")
    scope = validated.scope
    correspondence_scope = CorrespondenceScope(scope.company_id, scope.entity_id)
    try:
        binding = registry.authorize_projection_reference(
            reference, scope=correspondence_scope)
        verify_projection_correspondence_binding(
            binding, company_id=scope.company_id, entity_id=scope.entity_id)
        if (
            binding.correspondence_id != validated.correspondence_id
            or binding.mapping_version != validated.mapping_version
            or binding.pseudonym != validated.payload["subject"]
        ):
            raise CorrespondenceRefused("CORRESPONDENCE_REFERENCE_MISMATCH")
        consume_rehydration_authorization(
            authorization, scope=scope, request_id=validated.request_id,
            task=validated.task,
            projection_binding_hash=validated.projection_binding_hash,
            correspondence_id=validated.correspondence_id,
        )
        reidentified = registry.rehydrate(
            validated.payload, scope=correspondence_scope,
            handles=[reference.handle],
        )
    except (CorrespondenceRefused, OwnershipRefused, KeyError) as exc:
        raise ProviderResponseRefused("AUTHORIZED_REHYDRATION_REFUSED") from exc
    return AuthorizedTerminalOutput(
        reidentified, response_hash=validated.response_hash,
        projection_binding_hash=validated.projection_binding_hash,
    )


def _validate_schema(raw: Any, projection: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != {"schema", "subject", "interpretations"}:
        raise ProviderResponseRefused("PROVIDER_RESPONSE_SCHEMA_INVALID")
    if raw["schema"] != "FINANCIAL_CHANGE_RESPONSE_V1" or raw["subject"] != projection["subject"]:
        raise ProviderResponseRefused("PROVIDER_RESPONSE_BINDING_MISMATCH")
    rows = raw["interpretations"]
    if not isinstance(rows, list) or not rows or len(rows) != len(projection["metrics"]):
        raise ProviderResponseRefused("PROVIDER_RESPONSE_SCHEMA_INVALID")
    projected = {row["metric"]: row["direction"] for row in projection["metrics"]}
    seen: set[str] = set()
    normalized = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"metric", "direction", "assessment"}:
            raise ProviderResponseRefused("PROVIDER_RESPONSE_SCHEMA_INVALID")
        metric, direction, assessment = row["metric"], row["direction"], row["assessment"]
        if (
            not isinstance(metric, str) or metric in seen
            or projected.get(metric) != direction or assessment not in _ASSESSMENTS
        ):
            raise ProviderResponseRefused("PROVIDER_RESPONSE_BINDING_MISMATCH")
        seen.add(metric)
        normalized.append({"metric": metric, "direction": direction, "assessment": assessment})
    if seen != set(projected):
        raise ProviderResponseRefused("PROVIDER_RESPONSE_BINDING_MISMATCH")
    return {
        "schema": "FINANCIAL_CHANGE_RESPONSE_V1",
        "subject": raw["subject"],
        "interpretations": sorted(normalized, key=lambda row: row["metric"]),
    }


def _canonical_hash(value: Mapping[str, Any]) -> str:
    try:
        body = json.dumps(dict(value), ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProviderResponseRefused("PROVIDER_RESPONSE_SCHEMA_INVALID") from exc
    return hashlib.sha256(body).hexdigest()


def _freeze_copy(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return json.loads(json.dumps(dict(value), ensure_ascii=False, allow_nan=False,
                                 sort_keys=True, separators=(",", ":")))
