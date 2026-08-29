"""Scoped ownership capabilities for protected LLM-context reads.

This module is deliberately not a repository or an inference service.  It
resolves an authoritative ownership graph, mints opaque in-process
capabilities, and validates their narrowly bound use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import secrets
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
    ambiguous: bool = False


@dataclass(frozen=True)
class DisclosureReceipt:
    scope: OwnershipScope
    request_id: str
    resources: frozenset[ProtectedResource]
    disclosure_hash: str
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_DISCLOSURE_RECEIPT")


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


_read_registry: dict[str, tuple[OwnershipScope, str, frozenset[ProtectedResource], float]] = {}
_egress_registry: dict[str, tuple[OwnershipScope, str, str, frozenset[ProtectedResource], str, float, bool]] = {}


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
    registered = _read_registry.get(grant.capability_id)
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
    registered = _egress_registry.get(authorization.capability_id)
    if registered is None:
        raise OwnershipRefused("INVALID_EGRESS_AUTHORIZATION")
    scope, expected_task, expected_request, resources, expected_hash, expiry, consumed = registered
    if consumed:
        raise OwnershipRefused("EGRESS_AUTHORIZATION_REPLAYED")
    if time.monotonic() >= expiry:
        raise OwnershipRefused("EGRESS_AUTHORIZATION_EXPIRED")
    if task != expected_task or request_id != expected_request or disclosure_hash != expected_hash:
        raise OwnershipRefused("EGRESS_AUTHORIZATION_SCOPE_MISMATCH")
    _egress_registry[authorization.capability_id] = (
        scope, expected_task, expected_request, resources, expected_hash, expiry, True
    )
    return scope


class OwnershipAuthority:
    """Resolve authoritative scope and mint capabilities after verification."""

    def __init__(self, repository: OwnershipRepository, *, ttl_seconds: float = 30.0) -> None:
        self._repository = repository
        self._ttl_seconds = ttl_seconds

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
        grant = ProtectedReadGrant(principal, scope, request_id, allowed, expiry, capability_id, _MINT_SEAL)
        _read_registry[capability_id] = (scope, request_id, allowed, expiry)
        return grant

    def receipt_disclosure(
        self,
        *,
        grant: ProtectedReadGrant,
        request_id: str,
        disclosure_resources: Iterable[ProtectedResource],
        disclosure_hash: str,
    ) -> DisclosureReceipt:
        disclosed = frozenset(disclosure_resources)
        if not disclosed or len(disclosure_hash) != 64:
            raise OwnershipRefused("EMPTY_DISCLOSURE")
        for resource in disclosed:
            _validate_read_grant(grant, request_id=request_id, resource=resource)
        return DisclosureReceipt(grant.scope, request_id, disclosed, disclosure_hash, _MINT_SEAL)

    def mint_egress_authorization(
        self,
        *,
        grant: ProtectedReadGrant,
        receipt: DisclosureReceipt,
        task: str,
    ) -> EgressAuthorization:
        if not isinstance(receipt, DisclosureReceipt) or receipt._seal is not _MINT_SEAL:
            raise OwnershipRefused("INVALID_DISCLOSURE_RECEIPT")
        if receipt.scope != grant.scope or receipt.request_id != grant.request_id:
            raise OwnershipRefused("DISCLOSURE_SCOPE_MISMATCH")
        for resource in receipt.resources:
            _validate_read_grant(grant, request_id=receipt.request_id, resource=resource)
        expiry = min(grant.expires_at, time.monotonic() + self._ttl_seconds)
        capability_id = _new_id()
        authorization = EgressAuthorization(
            grant.scope, task, receipt.request_id, receipt.resources, receipt.disclosure_hash,
            capability_id, expiry, _MINT_SEAL
        )
        _egress_registry[capability_id] = (
            grant.scope, task, receipt.request_id, receipt.resources,
            receipt.disclosure_hash, expiry, False
        )
        return authorization


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
