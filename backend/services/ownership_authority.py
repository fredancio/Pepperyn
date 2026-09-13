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
class ProjectionSourceAuthorization:
    scope: OwnershipScope
    request_id: str
    task: str
    policy_id: str
    input_receipt_ids: frozenset[str]
    input_hashes: tuple[tuple[str, str], ...]
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_PROJECTION_SOURCE_AUTHORIZATION")


@dataclass(frozen=True)
class CorrespondenceRegistrationAuthorization:
    scope: OwnershipScope
    request_id: str
    category: str
    identity_hash: str
    source_receipt_id: str
    capability_id: str
    expires_at: float
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_CORRESPONDENCE_REGISTRATION_AUTHORIZATION")


@dataclass(frozen=True)
class ConsumedCorrespondenceRegistration:
    scope: OwnershipScope
    request_id: str
    authority_sha256: str
    source_receipt_sha256: str


@dataclass(frozen=True)
class RehydrationAuthorization:
    scope: OwnershipScope
    request_id: str
    task: str
    projection_binding_hash: str
    correspondence_id: str
    capability_id: str
    expires_at: float
    _issuer: Any
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _MINT_SEAL:
            raise OwnershipRefused("FORGED_REHYDRATION_AUTHORIZATION")


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
    expected = (grant.principal, grant.scope, grant.request_id, grant.allowed_resources, grant.expires_at)
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


def _payload_coverage(value: Any, prefix: tuple[str | int, ...] = ()) -> tuple[set[tuple], dict[tuple, str]]:
    keys: set[tuple] = set()
    leaves: dict[tuple, str] = {}
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise OwnershipRefused("NON_STRING_DISCLOSURE_KEY")
            path = prefix + (key,)
            keys.add(path)
            nested_keys, nested_leaves = _payload_coverage(nested, path)
            keys.update(nested_keys)
            leaves.update(nested_leaves)
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            nested_keys, nested_leaves = _payload_coverage(nested, prefix + (index,))
            keys.update(nested_keys)
            leaves.update(nested_leaves)
    else:
        leaves[prefix] = _canonical_hash(value)
    return keys, leaves


class OwnershipAuthority:
    """Resolve authoritative scope and mint capabilities after verification."""

    def __init__(
        self,
        repository: OwnershipRepository,
        *,
        ttl_seconds: float = 30.0,
        projection_policy: Mapping[ProtectedResource, frozenset[tuple[str | int, ...]]] | None = None,
        allowed_payload_keys: frozenset[tuple[str | int, ...]] = frozenset(),
        allowed_static_values: frozenset[Any] = frozenset(),
    ) -> None:
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0 or ttl_seconds > 300:
            raise OwnershipRefused("INVALID_CAPABILITY_TTL")
        self._repository = repository
        self._ttl_seconds = ttl_seconds
        self._read_registry: dict[str, tuple[AuthenticatedPrincipal, OwnershipScope, str, frozenset[ProtectedResource], float]] = {}
        self._egress_registry: dict[str, tuple[OwnershipScope, str, str, frozenset[ProtectedResource], str, float, bool]] = {}
        self._lock = threading.Lock()
        self._read_receipts: dict[str, tuple[str, OwnershipScope, str, ProtectedResource, Any, str, tuple | None]] = {}
        self._used_projected_receipts: set[str] = set()
        self._used_projection_source_receipts: set[str] = set()
        self._used_registration_source_receipts: set[str] = set()
        self._correspondence_registration_registry: dict[str, tuple[
            OwnershipScope, str, str, str, str, float, bool,
        ]] = {}
        self._rehydration_registry: dict[str, tuple[
            OwnershipScope, str, str, str, str, float, bool,
        ]] = {}
        self._disclosure_receipts: dict[str, tuple[str, frozenset[str], str, bool, OwnershipScope, str, frozenset[ProtectedResource]]] = {}
        self._projection_policy = dict(projection_policy or {})
        self._allowed_payload_keys = allowed_payload_keys
        self._allowed_static_hashes = frozenset(_canonical_hash(value) for value in allowed_static_values)

    def _prune(self) -> None:
        now = time.monotonic()
        self._read_registry = {key: value for key, value in self._read_registry.items() if value[4] > now}
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
        self._read_registry[capability_id] = (principal, scope, request_id, allowed, expiry)
        return grant

    def receipt_disclosure(
        self,
        *,
        grant: ProtectedReadGrant,
        request_id: str,
        protected_reads: Mapping[tuple[str | int, ...], ProtectedReadReceipt],
        disclosure_payload: Mapping[str, Any],
    ) -> DisclosureReceipt:
        reads_by_destination = dict(protected_reads)
        reads = tuple(reads_by_destination.values())
        disclosed = frozenset(read.resource for read in reads)
        if not reads:
            raise OwnershipRefused("EMPTY_DISCLOSURE")
        payload_keys, payload_leaves = _payload_coverage(disclosure_payload)
        if not payload_keys.issubset(self._allowed_payload_keys):
            raise OwnershipRefused("UNAPPROVED_DISCLOSURE_KEY")
        projected_hashes: set[str] = set()
        receipt_ids: set[str] = set()
        with self._lock:
            for destination, read in reads_by_destination.items():
                _validate_read_grant(grant, request_id=request_id, resource=read.resource)
                registered = self._read_receipts.get(read.receipt_id)
                expected = (
                    read.grant_id, read.scope, read.request_id, read.resource,
                    registered[4] if registered else None, read.value_hash, read.projection_path,
                )
                if (
                    read._seal is not _MINT_SEAL or read._issuer is not self
                    or read.scope != grant.scope or read.request_id != request_id
                    or read.grant_id != grant.capability_id or read.projection_path is None
                    or registered != expected or read.receipt_id in self._used_projected_receipts
                    or payload_leaves.get(destination) != read.value_hash
                ):
                    raise OwnershipRefused("INVALID_READ_RECEIPT")
                projected_hashes.add(read.value_hash)
                receipt_ids.add(read.receipt_id)
            uncovered = set(payload_leaves) - set(reads_by_destination)
            if any(payload_leaves[path] not in self._allowed_static_hashes for path in uncovered):
                raise OwnershipRefused("UNCOVERED_DISCLOSURE_VALUE")
            if set(reads_by_destination) - set(payload_leaves):
                raise OwnershipRefused("UNUSED_READ_RECEIPT")
            receipt_id = _new_id()
            receipt = DisclosureReceipt(
                grant.scope, request_id, disclosed, _canonical_hash(disclosure_payload),
                grant.capability_id, frozenset(receipt_ids), receipt_id, self, _MINT_SEAL
            )
            self._disclosure_receipts[receipt_id] = (
                grant.capability_id, frozenset(receipt_ids), receipt.disclosure_hash, False,
                grant.scope, request_id, disclosed,
            )
            self._used_projected_receipts.update(receipt_ids)
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
        with self._lock:
            registered_receipt = self._disclosure_receipts.get(receipt.receipt_id)
            expected_disclosure = (
                receipt.grant_id, receipt.input_receipt_ids, receipt.disclosure_hash,
                False, receipt.scope, receipt.request_id, receipt.resources,
            )
            if (
                receipt._issuer is not self or receipt.scope != grant.scope
                or receipt.request_id != grant.request_id or receipt.grant_id != grant.capability_id
                or registered_receipt != expected_disclosure
            ):
                raise OwnershipRefused("DISCLOSURE_SCOPE_MISMATCH")
            # Burn before leaving the critical section; later failure stays closed.
            self._disclosure_receipts[receipt.receipt_id] = (
                registered_receipt[0], registered_receipt[1], registered_receipt[2], True,
                registered_receipt[4], registered_receipt[5], registered_receipt[6],
            )
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
        return authorization

    def authorize_projection_sources(
        self, *, grant: ProtectedReadGrant, request_id: str, task: str,
        policy_id: str, inputs: Mapping[str, tuple[Any, ProtectedReadReceipt]],
    ) -> ProjectionSourceAuthorization:
        """Bind exact authoritative values to one deterministic projection."""

        if not task or not policy_id or not inputs or len(inputs) > 32:
            raise OwnershipRefused("PROJECTION_SOURCES_INVALID")
        hashes: list[tuple[str, str]] = []
        receipt_ids: set[str] = set()
        with self._lock:
            for label, pair in sorted(inputs.items()):
                if not isinstance(label, str) or not label or not isinstance(pair, tuple) or len(pair) != 2:
                    raise OwnershipRefused("PROJECTION_SOURCES_INVALID")
                value, receipt = pair
                if not isinstance(receipt, ProtectedReadReceipt):
                    raise OwnershipRefused("INVALID_READ_RECEIPT")
                _validate_read_grant(grant, request_id=request_id, resource=receipt.resource)
                registered = self._read_receipts.get(receipt.receipt_id)
                expected = (
                    receipt.grant_id, receipt.scope, receipt.request_id, receipt.resource,
                    registered[4] if registered else None, receipt.value_hash,
                    receipt.projection_path,
                )
                if (
                    receipt._seal is not _MINT_SEAL or receipt._issuer is not self
                    or receipt.scope != grant.scope or receipt.request_id != request_id
                    or receipt.grant_id != grant.capability_id or receipt.projection_path is None
                    or registered != expected
                    or receipt.receipt_id in self._used_projection_source_receipts
                    or receipt.value_hash != _canonical_hash(value)
                    or receipt.resource is not ProtectedResource.ANALYSIS_RESULT
                ):
                    raise OwnershipRefused("INVALID_PROJECTION_SOURCE_RECEIPT")
                hashes.append((label, receipt.value_hash))
                receipt_ids.add(receipt.receipt_id)
            if len(receipt_ids) != len(inputs):
                raise OwnershipRefused("DUPLICATE_PROJECTION_SOURCE_RECEIPT")
            self._used_projection_source_receipts.update(receipt_ids)
        return ProjectionSourceAuthorization(
            grant.scope, request_id, task, policy_id, frozenset(receipt_ids),
            tuple(hashes), self, _MINT_SEAL,
        )

    def mint_correspondence_registration_authorization(
        self, *, grant: ProtectedReadGrant, request_id: str, category: str,
        real_identity: str, identity_receipt: ProtectedReadReceipt,
    ) -> CorrespondenceRegistrationAuthorization:
        """Authorize one initial V33 registration from one governed identity read."""

        normalized_category = category.strip().upper()
        if not request_id or not normalized_category or not isinstance(real_identity, str):
            raise OwnershipRefused("REGISTRATION_INPUT_INVALID")
        if not isinstance(identity_receipt, ProtectedReadReceipt):
            raise OwnershipRefused("INVALID_READ_RECEIPT")
        _validate_read_grant(grant, request_id=request_id, resource=identity_receipt.resource)
        registered = self._read_receipts.get(identity_receipt.receipt_id)
        expected = (
            identity_receipt.grant_id, identity_receipt.scope,
            identity_receipt.request_id, identity_receipt.resource,
            registered[4] if registered else None, identity_receipt.value_hash,
            identity_receipt.projection_path,
        )
        if (
            identity_receipt._seal is not _MINT_SEAL
            or identity_receipt._issuer is not self
            or identity_receipt.scope != grant.scope
            or identity_receipt.request_id != request_id
            or identity_receipt.grant_id != grant.capability_id
            or identity_receipt.projection_path is None
            or identity_receipt.resource is not ProtectedResource.ENTITY_CONTEXT
            or registered != expected
            or identity_receipt.value_hash != _canonical_hash(real_identity)
        ):
            raise OwnershipRefused("INVALID_REGISTRATION_SOURCE_RECEIPT")
        capability_id = _new_id()
        expiry = min(grant.expires_at, time.monotonic() + self._ttl_seconds)
        with self._lock:
            if identity_receipt.receipt_id in self._used_registration_source_receipts:
                raise OwnershipRefused("REGISTRATION_SOURCE_RECEIPT_REPLAYED")
            self._used_registration_source_receipts.add(identity_receipt.receipt_id)
            authorization = CorrespondenceRegistrationAuthorization(
                grant.scope, request_id, normalized_category,
                identity_receipt.value_hash, identity_receipt.receipt_id,
                capability_id, expiry, self, _MINT_SEAL,
            )
            self._correspondence_registration_registry[capability_id] = (
                grant.scope, request_id, normalized_category,
                identity_receipt.value_hash, identity_receipt.receipt_id,
                expiry, False,
            )
        return authorization

    def mint_rehydration_authorization(
        self, *, grant: ProtectedReadGrant, request_id: str, task: str,
        projection_binding_hash: str, correspondence_id: str,
    ) -> RehydrationAuthorization:
        """Authorize one terminal-only local resolution for one provider return."""

        _validate_read_grant(
            grant, request_id=request_id, resource=ProtectedResource.CORRESPONDENCE)
        if (
            not task or not correspondence_id
            or not isinstance(projection_binding_hash, str)
            or len(projection_binding_hash) != 64
        ):
            raise OwnershipRefused("REHYDRATION_INPUT_INVALID")
        try:
            int(projection_binding_hash, 16)
        except ValueError as exc:
            raise OwnershipRefused("REHYDRATION_INPUT_INVALID") from exc
        capability_id = _new_id()
        expiry = min(grant.expires_at, time.monotonic() + self._ttl_seconds)
        authorization = RehydrationAuthorization(
            grant.scope, request_id, task, projection_binding_hash.lower(),
            correspondence_id, capability_id, expiry, self, _MINT_SEAL,
        )
        with self._lock:
            self._rehydration_registry[capability_id] = (
                grant.scope, request_id, task, projection_binding_hash.lower(),
                correspondence_id, expiry, False,
            )
        return authorization

    def _consume_rehydration(
        self, authorization: RehydrationAuthorization, *, scope: OwnershipScope,
        request_id: str, task: str, projection_binding_hash: str,
        correspondence_id: str,
    ) -> OwnershipScope:
        with self._lock:
            registered = self._rehydration_registry.get(authorization.capability_id)
            expected = (
                authorization.scope, authorization.request_id, authorization.task,
                authorization.projection_binding_hash,
                authorization.correspondence_id, authorization.expires_at, False,
            )
            if registered != expected or authorization._seal is not _MINT_SEAL:
                raise OwnershipRefused("INVALID_REHYDRATION_AUTHORIZATION")
            if time.monotonic() >= authorization.expires_at:
                raise OwnershipRefused("REHYDRATION_AUTHORIZATION_EXPIRED")
            if (
                scope != authorization.scope or request_id != authorization.request_id
                or task != authorization.task
                or projection_binding_hash.lower() != authorization.projection_binding_hash
                or correspondence_id != authorization.correspondence_id
            ):
                raise OwnershipRefused("REHYDRATION_AUTHORIZATION_SCOPE_MISMATCH")
            self._rehydration_registry[authorization.capability_id] = (*registered[:-1], True)
        return scope

    def _consume_correspondence_registration(
        self, authorization: CorrespondenceRegistrationAuthorization,
        *, scope: OwnershipScope, analysis_id: str, request_id: str,
        category: str, real_identity: str,
    ) -> ConsumedCorrespondenceRegistration:
        with self._lock:
            registered = self._correspondence_registration_registry.get(
                authorization.capability_id)
            expected = (
                authorization.scope, authorization.request_id,
                authorization.category, authorization.identity_hash,
                authorization.source_receipt_id, authorization.expires_at, False,
            )
            if registered != expected or authorization._seal is not _MINT_SEAL:
                raise OwnershipRefused("INVALID_REGISTRATION_AUTHORIZATION")
            if time.monotonic() >= authorization.expires_at:
                raise OwnershipRefused("REGISTRATION_AUTHORIZATION_EXPIRED")
            if (
                scope != authorization.scope or analysis_id != scope.analysis_id
                or request_id != authorization.request_id
                or category != authorization.category
                or _canonical_hash(real_identity) != authorization.identity_hash
            ):
                raise OwnershipRefused("REGISTRATION_AUTHORIZATION_SCOPE_MISMATCH")
            # Burn before persistence. A failed insert cannot make the authority reusable.
            self._correspondence_registration_registry[authorization.capability_id] = (
                *registered[:-1], True,
            )
        return ConsumedCorrespondenceRegistration(
            scope, request_id,
            hashlib.sha256(authorization.capability_id.encode()).hexdigest(),
            hashlib.sha256(authorization.source_receipt_id.encode()).hexdigest(),
        )

    def project_read(self, receipt: ProtectedReadReceipt, path: tuple[str | int, ...]) -> ProtectedReadReceipt:
        with self._lock:
            registered = self._read_receipts.get(receipt.receipt_id)
            expected = (
                receipt.grant_id, receipt.scope, receipt.request_id, receipt.resource,
                registered[4] if registered else None, receipt.value_hash, receipt.projection_path,
            )
            if (
                receipt._issuer is not self or registered != expected or receipt.projection_path is not None
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
            expected_authorization = (
                authorization.scope, authorization.task, authorization.request_id,
                authorization.disclosure_resources, authorization.disclosure_hash,
                authorization.expires_at, False,
            )
            if registered != expected_authorization:
                raise OwnershipRefused("INVALID_EGRESS_AUTHORIZATION")
            if time.monotonic() >= expiry:
                raise OwnershipRefused("EGRESS_AUTHORIZATION_EXPIRED")
            if task != expected_task or request_id != expected_request or disclosure_hash != expected_hash:
                raise OwnershipRefused("EGRESS_AUTHORIZATION_SCOPE_MISMATCH")
            self._egress_registry[authorization.capability_id] = (
                scope, expected_task, expected_request, resources, expected_hash, expiry, True
            )
            return scope


def consume_correspondence_registration_authorization(
    authorization: CorrespondenceRegistrationAuthorization | None, *,
    company_id: str, entity_id: str, analysis_id: str, request_id: str,
    category: str, real_identity: str,
) -> ConsumedCorrespondenceRegistration:
    if (
        not isinstance(authorization, CorrespondenceRegistrationAuthorization)
        or authorization._seal is not _MINT_SEAL
        or not isinstance(authorization._issuer, OwnershipAuthority)
    ):
        raise OwnershipRefused("INVALID_REGISTRATION_AUTHORIZATION")
    expected_scope = authorization.scope
    if expected_scope.company_id != company_id or expected_scope.entity_id != entity_id:
        raise OwnershipRefused("REGISTRATION_AUTHORIZATION_SCOPE_MISMATCH")
    return authorization._issuer._consume_correspondence_registration(
        authorization, scope=expected_scope, analysis_id=analysis_id,
        request_id=request_id, category=category, real_identity=real_identity,
    )


def consume_rehydration_authorization(
    authorization: RehydrationAuthorization | None, *, scope: OwnershipScope,
    request_id: str, task: str, projection_binding_hash: str,
    correspondence_id: str,
) -> OwnershipScope:
    if (
        not isinstance(authorization, RehydrationAuthorization)
        or authorization._seal is not _MINT_SEAL
        or not isinstance(authorization._issuer, OwnershipAuthority)
    ):
        raise OwnershipRefused("INVALID_REHYDRATION_AUTHORIZATION")
    return authorization._issuer._consume_rehydration(
        authorization, scope=scope, request_id=request_id, task=task,
        projection_binding_hash=projection_binding_hash,
        correspondence_id=correspondence_id,
    )


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
