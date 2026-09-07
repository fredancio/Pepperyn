"""Fail-closed provider-policy authorization for the LLM egress boundary.

This module proves deployment policy, not provider account state. Effective
account evidence remains an external Provider Gate requirement. No function in
this module performs network I/O or enables real-data admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import threading
from typing import Any, Mapping


PROVIDER_POLICY_VERSION = "OPENAI_PROVIDER_GATE_V1_PG8"
_ALLOWED_TASKS = frozenset({"FINANCIAL_ANALYSIS", "FOUNDER_REVIEW"})
_ALLOWED_MODELS = frozenset({"gpt-5"})
_MAX_EVIDENCE_AGE_SECONDS = 90 * 24 * 60 * 60
_SEAL = object()


class ProviderPolicyRefused(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderPolicyAuthorization:
    policy_version: str
    provider: str
    project_id: str
    base_url: str
    endpoint: str
    model: str
    region: str
    retention: str
    task: str
    request_hash: str
    evidence_sha256: str
    expires_at: float
    capability_id: str
    _issuer_kind: str
    _seal: object


def _authorization_tuple(value: ProviderPolicyAuthorization) -> tuple[Any, ...]:
    return (
        value.policy_version, value.provider, value.project_id, value.base_url,
        value.endpoint, value.model, value.region, value.retention, value.task,
        value.request_hash, value.evidence_sha256, value.expires_at,
    )


class _ProviderPolicyIssuer:
    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._issued: dict[str, tuple[Any, ...]] = {}
        self._lock = threading.Lock()

    def _prune(self) -> None:
        now = datetime.now(timezone.utc).timestamp()
        self._issued = {key: value for key, value in self._issued.items() if value[11] > now}

    def mint(self, *values: Any) -> ProviderPolicyAuthorization:
        capability_id = secrets.token_urlsafe(24)
        authorization = ProviderPolicyAuthorization(
            *values, capability_id, self._kind, _SEAL,
        )
        with self._lock:
            self._prune()
            self._issued[capability_id] = _authorization_tuple(authorization)
        return authorization

    def verify(self, authorization: ProviderPolicyAuthorization) -> bool:
        with self._lock:
            self._prune()
            return self._issued.get(authorization.capability_id) == _authorization_tuple(authorization)


_CONFIGURED_POLICY_ISSUER = _ProviderPolicyIssuer("configured")
_SYNTHETIC_TEST_POLICY_ISSUER = _ProviderPolicyIssuer("synthetic-test")


def _canonical_hash(body: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(
            dict(body), ensure_ascii=False, allow_nan=False,
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProviderPolicyRefused("PROVIDER_POLICY_NON_CANONICAL_REQUEST") from exc
    return hashlib.sha256(encoded).hexdigest()


def _parse_expiry(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProviderPolicyRefused("PROVIDER_POLICY_INVALID_EXPIRY") from exc
    if parsed.tzinfo is None:
        raise ProviderPolicyRefused("PROVIDER_POLICY_INVALID_EXPIRY")
    return parsed.astimezone(timezone.utc).timestamp()


def authorize_configured_provider_request(
    *, task: str, request_body: Mapping[str, Any], now: float | None = None,
) -> ProviderPolicyAuthorization:
    """Mint from deployment-only evidence configuration, never caller fields."""

    configured = {
        "approved": os.getenv("PEPPERYN_PROVIDER_APPROVED", ""),
        "policy_version": os.getenv("PEPPERYN_PROVIDER_POLICY_VERSION", ""),
        "provider": os.getenv("PEPPERYN_PROVIDER", ""),
        "project_id": os.getenv("PEPPERYN_PROVIDER_PROJECT_ID", ""),
        "base_url": os.getenv("PEPPERYN_PROVIDER_BASE_URL", ""),
        "endpoint": os.getenv("PEPPERYN_PROVIDER_ENDPOINT", ""),
        "model": os.getenv("PEPPERYN_PROVIDER_MODEL", ""),
        "region": os.getenv("PEPPERYN_PROVIDER_REGION", ""),
        "retention": os.getenv("PEPPERYN_PROVIDER_RETENTION", ""),
        "data_sharing": os.getenv("PEPPERYN_PROVIDER_DATA_SHARING", ""),
        "dpa_status": os.getenv("PEPPERYN_PROVIDER_DPA_STATUS", ""),
        "evidence_sha256": os.getenv("PEPPERYN_PROVIDER_EVIDENCE_SHA256", ""),
        "evidence_path": os.getenv("PEPPERYN_PROVIDER_EVIDENCE_PATH", ""),
        "evidence_verified_at": os.getenv("PEPPERYN_PROVIDER_EVIDENCE_VERIFIED_AT", ""),
        "evidence_expires_at": os.getenv("PEPPERYN_PROVIDER_EVIDENCE_EXPIRES_AT", ""),
    }
    required = tuple(configured)
    if any(not configured[key] for key in required):
        raise ProviderPolicyRefused("PROVIDER_POLICY_CONFIGURATION_INCOMPLETE")
    if configured["approved"] != "1" or configured["policy_version"] != PROVIDER_POLICY_VERSION:
        raise ProviderPolicyRefused("PROVIDER_POLICY_NOT_APPROVED")
    if (
        configured["provider"] != "openai"
        or configured["base_url"] != "https://eu.api.openai.com/v1"
        or configured["endpoint"] != "/responses"
        or configured["region"] != "europe"
        or configured["retention"] != "zero_data_retention"
        or configured["data_sharing"] != "disabled"
        or configured["dpa_status"] != "effective"
        or configured["model"] not in _ALLOWED_MODELS
        or task not in _ALLOWED_TASKS
        or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", configured["project_id"])
    ):
        raise ProviderPolicyRefused("PROVIDER_POLICY_SCOPE_NOT_APPROVED")
    evidence = configured["evidence_sha256"]
    if not re.fullmatch(r"[a-f0-9]{64}", evidence):
        raise ProviderPolicyRefused("PROVIDER_POLICY_INVALID_EVIDENCE")
    try:
        evidence_path = Path(configured["evidence_path"])
        raw_evidence = evidence_path.read_bytes()
    except OSError as exc:
        raise ProviderPolicyRefused("PROVIDER_POLICY_EVIDENCE_UNAVAILABLE") from exc
    if len(raw_evidence) > 65_536 or hashlib.sha256(raw_evidence).hexdigest() != evidence:
        raise ProviderPolicyRefused("PROVIDER_POLICY_INVALID_EVIDENCE")
    try:
        manifest = json.loads(raw_evidence)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderPolicyRefused("PROVIDER_POLICY_INVALID_EVIDENCE") from exc
    expected_manifest = {
        "policy_version": configured["policy_version"], "provider": configured["provider"],
        "project_id": configured["project_id"], "base_url": configured["base_url"],
        "endpoint": configured["endpoint"], "model": configured["model"],
        "region": configured["region"], "retention": configured["retention"],
        "data_sharing": configured["data_sharing"], "dpa_status": configured["dpa_status"],
        "verified_at": configured["evidence_verified_at"],
        "expires_at": configured["evidence_expires_at"],
    }
    if manifest != expected_manifest:
        raise ProviderPolicyRefused("PROVIDER_POLICY_EVIDENCE_SCOPE_MISMATCH")
    verified = _parse_expiry(configured["evidence_verified_at"])
    expiry = _parse_expiry(configured["evidence_expires_at"])
    current = datetime.now(timezone.utc).timestamp() if now is None else now
    if (
        not math.isfinite(current) or verified > current or current >= expiry
        or current - verified > _MAX_EVIDENCE_AGE_SECONDS
        or expiry - verified > _MAX_EVIDENCE_AGE_SECONDS
    ):
        raise ProviderPolicyRefused("PROVIDER_POLICY_EVIDENCE_EXPIRED")
    if request_body.get("model") != configured["model"] or request_body.get("store") is not False:
        raise ProviderPolicyRefused("PROVIDER_POLICY_REQUEST_NOT_APPROVED")
    return _CONFIGURED_POLICY_ISSUER.mint(
        configured["policy_version"], configured["provider"], configured["project_id"],
        configured["base_url"], configured["endpoint"], configured["model"],
        configured["region"], configured["retention"], task, _canonical_hash(request_body),
        evidence, expiry,
    )


def verify_provider_policy_authorization(
    authorization: ProviderPolicyAuthorization | None,
    *, task: str, request_hash: str, now: float | None = None,
) -> ProviderPolicyAuthorization:
    if (
        not isinstance(authorization, ProviderPolicyAuthorization)
        or authorization._seal is not _SEAL
        or authorization._issuer_kind not in {"configured", "synthetic-test"}
    ):
        raise ProviderPolicyRefused("PROVIDER_POLICY_AUTHORIZATION_REQUIRED")
    issuer = (
        _CONFIGURED_POLICY_ISSUER if authorization._issuer_kind == "configured"
        else _SYNTHETIC_TEST_POLICY_ISSUER
    )
    if not issuer.verify(authorization):
        raise ProviderPolicyRefused("PROVIDER_POLICY_AUTHORIZATION_REQUIRED")
    current = datetime.now(timezone.utc).timestamp() if now is None else now
    if (
        not math.isfinite(current) or current >= authorization.expires_at
        or authorization.policy_version != PROVIDER_POLICY_VERSION
        or authorization.task != task or authorization.request_hash != request_hash
    ):
        raise ProviderPolicyRefused("PROVIDER_POLICY_AUTHORIZATION_MISMATCH")
    return authorization


def _mint_synthetic_test_provider_authorization(
    *, task: str, request_body: Mapping[str, Any], expires_at: float = 4_102_444_800.0,
) -> ProviderPolicyAuthorization:
    """Test-only capability; production-source use is prohibited by static policy."""

    try:
        request_hash = _canonical_hash(request_body)
    except ProviderPolicyRefused:
        # The egress authority must remain responsible for rejecting malformed
        # or tainted bodies before provider-policy verification.
        request_hash = "0" * 64
    return _SYNTHETIC_TEST_POLICY_ISSUER.mint(
        PROVIDER_POLICY_VERSION, "synthetic-test", "synthetic-project",
        "https://provider.invalid/v1", "/synthetic", str(request_body.get("model", "")),
        "synthetic", "no_transport", task, request_hash, "0" * 64,
        expires_at,
    )
