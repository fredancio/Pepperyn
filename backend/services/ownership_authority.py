"""Scoped ownership capabilities for protected LLM-context reads.

This module is deliberately not a repository or an inference service.  It
resolves an authoritative ownership graph, mints opaque in-process
capabilities, and validates their narrowly bound use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import secrets
import threading
import time
from typing import Any, Iterable, Mapping, Protocol


class OwnershipRefused(RuntimeError):
    pass


class ProtectedResource(str, Enum):
    ANALYSIS_RESULT = "ANALYSIS_RESULT"
    CORRESPONDENCE = "CORRESPONDENCE"
    EXECUTIVE_CASE = "EXECUTIVE_CASE"
    RELATIONSHIP_CONTEXT = "RELATIONSHIP_CONTEXT"
    MEMORY = "MEMORY"
    DECISIONS_ACTIONS = "DECISIONS_ACTIONS"
    ENTITY_CONTEXT = "ENTITY_CONTEXT"
    ENGAGEMENT_CONTEXT = "ENGAGEMENT_CONTEXT"


_MINT_SEAL = object()


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    principal_id: str
    company_id: str
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_PRINCIPAL")


@dataclass(frozen=True)
class OwnershipScope:
    company_id: str
    entity_id: str
    engagement_id: str
    analysis_id: str


@dataclass(frozen=True)
class ProtectedReadGrant:
    principal: AuthenticatedPrincipal
    scope: OwnershipScope
    request_id: str
    allowed_resources: frozenset[ProtectedResource]
    expires_at: float
    capability_id: str
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_READ_GRANT")


@dataclass(frozen=True)
class EgressAuthorization:
    scope: OwnershipScope
    task: str
    request_id: str
    disclosure_resources: frozenset[ProtectedResource]
    disclosure_hash: str
    capability_id: str
    expires_at: float
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_EGRESS_AUTHORIZATION")


@dataclass(frozen=True)
class OwnershipRecord:
    analysis_id: str
    company_id: str
    entity_id: str | None
    engagement_id: str | None
    entity_company_id: str | None = None
    engagement_entity_id: str | None = None
    ambiguous: bool = False


@dataclass(frozen=True)
class DisclosureReceipt:
    scope: OwnershipScope
    request_id: str
    resources: frozenset[ProtectedResource]
    disclosure_hash: str
    grant_id: str
    input_receipt_ids: frozenset[str]
    receipt_id: str
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_DISCLOSURE_RECEIPT")


@dataclass(frozen=True)
class ProtectedReadReceipt:
    scope: OwnershipScope
    request_id: str
    resource: ProtectedResource
    value_hash: str
    grant_id: str
    receipt_id: str
    projection_path: tuple[str | int, ...] | None
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_READ_RECEIPT")


@dataclass(frozen=True)
class ScopedContextRecord:
    resource: ProtectedResource
    company_id: str
    entity_id: str | None
    engagement_id: str | None
    analysis_id: str | None
    value: Any


class OwnershipRepository(Protocol):
    def resolve_analysis(self, analysis_id: str) -> OwnershipRecord | None: ...


class ScopedContextRepository(Protocol):
    def read_scoped(self, resource: ProtectedResource) -> Iterable[ScopedContextRecord]: ...


def _new_id() -> str:
    return secrets.token_urlsafe(24)


def _validate_read_grant(
    grant: ProtectedReadGrant,
    *,
    request_id: str,
    resource: ProtectedResource,
) -> OwnershipScope:
    if not isinstance(grant, ProtectedReadGrant) or grant._seal is not _MINT_SEAL:
        raise OwnershipRefused("INVALID_READ_GRANT")
    if not isinstance(grant._issuer, OwnershipAuthority):
        raise OwnershipRefused("INVALID_READ_GRANT")
    registered = grant._issuer._read_registry.get(grant.capability_id)
    expected = (grant.scope, grant.request_id, grant.allowed_resources, grant.expires_at)
    if registered != expected or request_id != grant.request_id:
        raise OwnershipRefused("READ_GRANT_SCOPE_MISMATCH")
    if time.monotonic() >= grant.expires_at:
        raise OwnershipRefused("READ_GRANT_EXPIRED")
    if resource not in grant.allowed_resources:
        raise OwnershipRefused("READ_RESOURCE_NOT_AUTHORIZED")
    return grant.scope


def consume_egress_authorization(
    authorization: EgressAuthorization | None,
    *,
    task: str,
    request_id: str,
    disclosure_hash: str,
) -> OwnershipScope:
    """Validate and atomically consume a resolver-minted authorization."""

    if not isinstance(authorization, EgressAuthorization) or authorization._seal is not _MINT_SEAL:
        raise OwnershipRefused("INVALID_EGRESS_AUTHORIZATION")
    if not isinstance(authorization._issuer, OwnershipAuthority):
        raise OwnershipRefused("INVALID_EGRESS_AUTHORIZATION")
    return authorization._issuer._consume_egress(
        authorization, task=task, request_id=request_id, disclosure_hash=disclosure_hash
    )


def _canonical_hash(value: Any) -> str:
    try:
        body = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()
    except (TypeError, ValueError) as exc:
        raise OwnershipRefused("NON_CANONICAL_DISCLOSURE") from exc
    return hashlib.sha256(body).hexdigest()


def _nested_hashes(value: Any) -> set[str]:
    hashes = {_canonical_hash(value)}
    if isinstance(value, Mapping):
        for nested in value.values():
            hashes.update(_nested_hashes(nested))
    elif isinstance(value, (list, tuple)):
        for nested in value:
            hashes.update(_nested_hashes(nested))
    return hashes


def _payload_coverage(value: Any) -> tuple[set[str], set[str]]:
    keys: set[str] = set()
    leaves: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise OwnershipRefused("NON_STRING_DISCLOSURE_KEY")
            keys.add(key)
            nested_keys, nested_leaves = _payload_coverage(nested)
            keys.update(nested_keys)
            leaves.update(nested_leaves)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            nested_keys, nested_leaves = _payload_coverage(nested)
            keys.update(nested_keys)
            leaves.update(nested_leaves)
    else:
        leaves.add(_canonical_hash(value))
    return keys, leaves


class OwnershipAuthority:
    """Resolve authoritative scope and mint capabilities after verification."""

    def __init__(
        self,
        repository: OwnershipRepository,
        *,
        ttl_seconds: float = 30.0,
        projection_policy: Mapping[ProtectedResource, frozenset[tuple[str | int, ...]]] | None = None,
        allowed_payload_keys: frozenset[str] = frozenset(),
        allowed_static_values: frozenset[Any] = frozenset(),
    ) -> None:
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0 or ttl_seconds > 300:
            raise OwnershipRefused("INVALID_CAPABILITY_TTL")
        self._repository = repository
        self._ttl_seconds = ttl_seconds
        self._read_registry: dict[str, tuple[OwnershipScope, str, frozenset[ProtectedResource], float]] = {}
        self._egress_registry: dict[str, tuple[OwnershipScope, str, str, frozenset[ProtectedResource], str, float, bool]] = {}
        self._lock = threading.Lock()
        self._read_receipts: dict[str, tuple[str, OwnershipScope, str, ProtectedResource, Any, str, tuple | None]] = {}
        self._disclosure_receipts: dict[str, tuple[str, frozenset[str], str, bool]] = {}
        self._projection_policy = dict(projection_policy or {})
        self._allowed_payload_keys = allowed_payload_keys
        self._allowed_static_hashes = frozenset(_canonical_hash(value) for value in allowed_static_values)

    def _prune(self) -> None:
        now = time.monotonic()
        self._read_registry = {key: value for key, value in self._read_registry.items() if value[3] > now}
        self._egress_registry = {
            key: value for key, value in self._egress_registry.items()
            if value[5] > now and not value[6]
        }

    def _accept_authenticated_principal(self, principal_id: str, company_id: str) -> AuthenticatedPrincipal:
        """Authentication-adapter boundary; never accepts HTTP caller fields."""
        if not principal_id or not company_id:
            raise OwnershipRefused("MISSING_AUTHENTICATED_PRINCIPAL")
        return AuthenticatedPrincipal(principal_id, company_id, _MINT_SEAL)

    def resolve_and_mint_read_grant(
        self,
        *,
        principal: AuthenticatedPrincipal,
        analysis_id: str,
        request_id: str,
        resources: Iterable[ProtectedResource],
        expected_entity_id: str | None = None,
        expected_engagement_id: str | None = None,
    ) -> ProtectedReadGrant:
        if not isinstance(principal, AuthenticatedPrincipal) or principal._seal is not _MINT_SEAL:
            raise OwnershipRefused("INVALID_PRINCIPAL")
        record = self._repository.resolve_analysis(analysis_id)
        if record is None or record.ambiguous:
            raise OwnershipRefused("OWNERSHIP_UNRESOLVED")
        if record.company_id != principal.company_id:
            raise OwnershipRefused("COMPANY_MISMATCH")
        if not record.entity_id or not record.engagement_id:
            raise OwnershipRefused("REQUIRED_SCOPE_MISSING")
        if record.entity_company_id != record.company_id:
            raise OwnershipRefused("ENTITY_COMPANY_MISMATCH")
        if record.engagement_entity_id != record.entity_id:
            raise OwnershipRefused("ENGAGEMENT_ENTITY_MISMATCH")
        if expected_entity_id is not None and expected_entity_id != record.entity_id:
            raise OwnershipRefused("ENTITY_MISMATCH")
        if expected_engagement_id is not None and expected_engagement_id != record.engagement_id:
            raise OwnershipRefused("ENGAGEMENT_MISMATCH")
        allowed = frozenset(resources)
        if not allowed or not request_id:
            raise OwnershipRefused("EMPTY_CAPABILITY_SCOPE")
        scope = OwnershipScope(record.company_id, record.entity_id, record.engagement_id, record.analysis_id)
        expiry = time.monotonic() + self._ttl_seconds
        capability_id = _new_id()
        self._prune()
        grant = ProtectedReadGrant(principal, scope, request_id, allowed, expiry, capability_id, self, _MINT_SEAL)
        self._read_registry[capability_id] = (scope, request_id, allowed, expiry)
        return grant

    def receipt_disclosure(
        self,
        *,
        grant: ProtectedReadGrant,
        request_id: str,
        protected_reads: Iterable[ProtectedReadReceipt],
        disclosure_payload: Mapping[str, Any],
    ) -> DisclosureReceipt:
        reads = tuple(protected_reads)
        disclosed = frozenset(read.resource for read in reads)
        if not reads:
            raise OwnershipRefused("EMPTY_DISCLOSURE")
        payload_keys, payload_leaf_hashes = _payload_coverage(disclosure_payload)
        if not payload_keys.issubset(self._allowed_payload_keys):
            raise OwnershipRefused("UNAPPROVED_DISCLOSURE_KEY")
        projected_hashes: set[str] = set()
        receipt_ids: set[str] = set()
        for read in reads:
            _validate_read_grant(grant, request_id=request_id, resource=read.resource)
            registered = self._read_receipts.get(read.receipt_id)
            if (
                read._seal is not _MINT_SEAL or read._issuer is not self
                or read.scope != grant.scope or read.request_id != request_id
                or read.grant_id != grant.capability_id or read.projection_path is None
                or registered is None
            ):
                raise OwnershipRefused("INVALID_READ_RECEIPT")
            projected_hashes.add(read.value_hash)
            receipt_ids.add(read.receipt_id)
        if not payload_leaf_hashes.issubset(projected_hashes | self._allowed_static_hashes):
            raise OwnershipRefused("UNCOVERED_DISCLOSURE_VALUE")
        if not projected_hashes.issubset(payload_leaf_hashes):
            raise OwnershipRefused("UNUSED_READ_RECEIPT")
        receipt_id = _new_id()
        receipt = DisclosureReceipt(
            grant.scope, request_id, disclosed, _canonical_hash(disclosure_payload),
            grant.capability_id, frozenset(receipt_ids), receipt_id, self, _MINT_SEAL
        )
        self._disclosure_receipts[receipt_id] = (
            grant.capability_id, frozenset(receipt_ids), receipt.disclosure_hash, False
        )
        return receipt

    def mint_egress_authorization(
        self,
        *,
        grant: ProtectedReadGrant,
        receipt: DisclosureReceipt,
        task: str,
    ) -> EgressAuthorization:
        if not isinstance(receipt, DisclosureReceipt) or receipt._seal is not _MINT_SEAL:
            raise OwnershipRefused("INVALID_DISCLOSURE_RECEIPT")
        registered_receipt = self._disclosure_receipts.get(receipt.receipt_id)
        if (
            receipt._issuer is not self or receipt.scope != grant.scope
            or receipt.request_id != grant.request_id or receipt.grant_id != grant.capability_id
            or registered_receipt is None or registered_receipt[3]
        ):
            raise OwnershipRefused("DISCLOSURE_SCOPE_MISMATCH")
        for resource in receipt.resources:
            _validate_read_grant(grant, request_id=receipt.request_id, resource=resource)
        expiry = min(grant.expires_at, time.monotonic() + self._ttl_seconds)
        capability_id = _new_id()
        authorization = EgressAuthorization(
            grant.scope, task, receipt.request_id, receipt.resources, receipt.disclosure_hash,
            capability_id, expiry, self, _MINT_SEAL
        )
        self._prune()
        self._egress_registry[capability_id] = (
            grant.scope, task, receipt.request_id, receipt.resources,
            receipt.disclosure_hash, expiry, False
        )
        self._disclosure_receipts[receipt.receipt_id] = (
            registered_receipt[0], registered_receipt[1], registered_receipt[2], True
        )
        return authorization

    def project_read(self, receipt: ProtectedReadReceipt, path: tuple[str | int, ...]) -> ProtectedReadReceipt:
        registered = self._read_receipts.get(receipt.receipt_id)
        if (
            receipt._issuer is not self or registered is None or receipt.projection_path is not None
            or path not in self._projection_policy.get(receipt.resource, frozenset())
        ):
            raise OwnershipRefused("PROJECTION_NOT_AUTHORIZED")
        value = registered[4]
        try:
            for component in path:
                value = value[component]
        except (KeyError, IndexError, TypeError) as exc:
            raise OwnershipRefused("PROJECTION_PATH_MISSING") from exc
        receipt_id = _new_id()
        value_hash = _canonical_hash(value)
        projected = ProtectedReadReceipt(
            receipt.scope, receipt.request_id, receipt.resource, value_hash,
            receipt.grant_id, receipt_id, path, self, _MINT_SEAL,
        )
        self._read_receipts[receipt_id] = (
            receipt.grant_id, receipt.scope, receipt.request_id, receipt.resource,
            value, value_hash, path,
        )
        return projected

    def _consume_egress(self, authorization, *, task: str, request_id: str, disclosure_hash: str) -> OwnershipScope:
        with self._lock:
            registered = self._egress_registry.get(authorization.capability_id)
            if registered is None:
                raise OwnershipRefused("INVALID_EGRESS_AUTHORIZATION")
            scope, expected_task, expected_request, resources, expected_hash, expiry, consumed = registered
            if consumed:
                raise OwnershipRefused("EGRESS_AUTHORIZATION_REPLAYED")
            if time.monotonic() >= expiry:
                raise OwnershipRefused("EGRESS_AUTHORIZATION_EXPIRED")
            if task != expected_task or request_id != expected_request or disclosure_hash != expected_hash:
                raise OwnershipRefused("EGRESS_AUTHORIZATION_SCOPE_MISMATCH")
            self._egress_registry[authorization.capability_id] = (
                scope, expected_task, expected_request, resources, expected_hash, expiry, True
            )
            return scope


class ProtectedContextReader:
    """Only read records whose full authoritative scope matches the grant."""

    def __init__(self, repository: ScopedContextRepository) -> None:
        self._repository = repository

    def read(
        self,
        grant: ProtectedReadGrant,
        *,
        request_id: str,
        resource: ProtectedResource,
    ) -> tuple[Any, ...]:
        scope = _validate_read_grant(grant, request_id=request_id, resource=resource)
        values = []
        for record in self._repository.read_scoped(resource):
            # Missing attribution is quarantined.  No company-wide fallback.
            if not record.entity_id or not record.engagement_id:
                continue
            if (
                record.company_id == scope.company_id
                and record.entity_id == scope.entity_id
                and record.engagement_id == scope.engagement_id
                and (record.analysis_id is None or record.analysis_id == scope.analysis_id)
            ):
                values.append(record.value)
        return tuple(values)

    def read_receipted(self, grant, *, request_id: str, resource: ProtectedResource):
        values = self.read(grant, request_id=request_id, resource=resource)
        results = []
        for value in values:
            receipt_id = _new_id()
            value_hash = _canonical_hash(value)
            receipt = ProtectedReadReceipt(
                grant.scope, request_id, resource, value_hash, grant.capability_id,
                receipt_id, None, grant._issuer, _MINT_SEAL,
            )
            grant._issuer._read_receipts[receipt_id] = (
                grant.capability_id, grant.scope, request_id, resource, value, value_hash, None
            )
            results.append((value, receipt))
        return tuple(results)


class InMemoryOwnershipRepository:
    """Synthetic fixture repository; production adapters remain I/O-specific."""

    def __init__(self, records: Iterable[OwnershipRecord]) -> None:
        self._records = list(records)

    def resolve_analysis(self, analysis_id: str) -> OwnershipRecord | None:
        matches = [record for record in self._records if record.analysis_id == analysis_id]
        if len(matches) != 1:
            return OwnershipRecord(analysis_id, "", None, None, ambiguous=True) if matches else None
        return matches[0]


class InMemoryScopedContextRepository:
    def __init__(self, records: Iterable[ScopedContextRecord]) -> None:
        self._records = tuple(records)

    def read_scoped(self, resource: ProtectedResource) -> Iterable[ScopedContextRecord]:
        return (record for record in self._records if record.resource is resource)
