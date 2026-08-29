"""Single synthetic-only authority for every external model dispatch.

Slice 1 deliberately ships with a closed production transport.  A caller can
prepare the same semantic request it used before this gate, but no network call
is possible until later slices supply verified provenance and authorization.
Tests replace the private final boundary with a capture double and therefore
exercise the final serialized bytes without opening real-client admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import logging
from types import MappingProxyType
from typing import Any, Mapping

from services.ownership_authority import (
    EgressAuthorization,
    OwnershipRefused,
    consume_egress_authorization,
)


logger = logging.getLogger(__name__)


class EgressRefusalCode(str, Enum):
    REAL_DATA_ADMISSION_CLOSED = "REAL_DATA_ADMISSION_CLOSED"
    IDENTITY_FORBIDDEN = "IDENTITY_FORBIDDEN"
    ROUTE_NOT_ALLOWED = "ROUTE_NOT_ALLOWED"
    TRANSPORT_CLOSED = "TRANSPORT_CLOSED"
    OWNERSHIP_AUTHORIZATION_REQUIRED = "OWNERSHIP_AUTHORIZATION_REQUIRED"


class EgressRefused(RuntimeError):
    """Safe, content-free refusal raised before provider dispatch."""

    def __init__(self, code: EgressRefusalCode) -> None:
        self.code = code
        super().__init__(code.value)


class RetryableProviderError(RuntimeError):
    """Transport-only signal that permits a byte-identical retry."""


class IdentityState(str, Enum):
    NO_IDENTITY = "NO_IDENTITY"
    PSEUDONYMOUS = "PSEUDONYMOUS"
    REIDENTIFIED = "REIDENTIFIED"


@dataclass(frozen=True)
class SyntheticEgressRequest:
    """Temporary Slice-1 adapter envelope; never authorizes real data."""

    task: str
    provider_payload: Mapping[str, Any]
    identity_state: IdentityState = IdentityState.PSEUDONYMOUS
    max_attempts: int = 1
    _admission: object | None = None
    request_id: str = ""
    egress_authorization: EgressAuthorization | None = None


@dataclass(frozen=True)
class FrozenProviderRequest:
    """Exact immutable body presented to the sole transport boundary."""

    task: str
    body: bytes
    payload_hash: str


@dataclass(frozen=True)
class UntrustedProviderOutput:
    """Provider material that has no identity/safety authority."""

    raw_response: Any


class _UntrustedProviderDerived:
    """Opaque provider-derived value with no implicit native conversion."""

    __slots__ = ("__value",)

    def __init__(self, value: Any) -> None:
        self.__value = value

    def __repr__(self) -> str:
        return "<UNTRUSTED_PROVIDER_DERIVED>"

    def __str__(self) -> str:
        raise TypeError("provider-derived value requires an authorized transformation")

    def __format__(self, format_spec: str) -> str:
        raise TypeError("provider-derived value requires an authorized transformation")

    def __getitem__(self, key: Any) -> Any:
        raise TypeError("provider-derived value is opaque")

    def __bool__(self) -> bool:
        raise TypeError("provider-derived value is opaque")


class UntrustedProviderText(_UntrustedProviderDerived):
    """Opaque text originating at a provider; never valid egress input."""

    def strip(self, chars: str | None = None) -> "UntrustedProviderText":
        return self

    lstrip = strip
    rstrip = strip


def taint_provider_derived(value: Any) -> Any:
    """Wrap a parsed provider value without exposing native operations."""

    return _UntrustedProviderDerived(value)


class _UntrustedContentBlockProxy:
    def __init__(self, block: Any) -> None:
        self.__block = block

    def __getattr__(self, name: str) -> Any:
        value = getattr(self.__block, name)
        if name == "text" and isinstance(value, str):
            return UntrustedProviderText(value)
        return value


class _UntrustedLegacyResponseProxy:
    def __init__(self, response: Any) -> None:
        self.__response = response

    def __getattr__(self, name: str) -> Any:
        value = getattr(self.__response, name)
        if name == "content":
            return tuple(_UntrustedContentBlockProxy(block) for block in value)
        return value


@dataclass(frozen=True)
class EgressResult:
    task: str
    content: UntrustedProviderOutput
    payload_hash: str
    attempt_count: int


_SYNTHETIC_TEST_ADMISSION = object()


def _dispatch_final_request(request: FrozenProviderRequest) -> Any:
    """Sole future network boundary; closed in the production Slice-1 build."""

    raise EgressRefused(EgressRefusalCode.TRANSPORT_CLOSED)


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    _reject_provider_output(value)
    try:
        return json.dumps(
            dict(value),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EgressRefused(EgressRefusalCode.ROUTE_NOT_ALLOWED) from exc


def _reject_provider_output(value: Any) -> None:
    if isinstance(value, (UntrustedProviderOutput, _UntrustedProviderDerived)):
        raise EgressRefused(EgressRefusalCode.IDENTITY_FORBIDDEN)
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_provider_output(key)
            _reject_provider_output(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_provider_output(nested)


def reject_untrusted_provider_input(value: Any) -> None:
    """Fail before prompt construction can erase provider-output taint."""

    _reject_provider_output(value)


class LlmEgressAuthority:
    """Narrow boundary validator/renderer; contains no cognitive logic."""

    def dispatch(self, request: SyntheticEgressRequest) -> EgressResult:
        if request.identity_state is IdentityState.REIDENTIFIED:
            raise EgressRefused(EgressRefusalCode.IDENTITY_FORBIDDEN)
        if request._admission is not _SYNTHETIC_TEST_ADMISSION:
            raise EgressRefused(EgressRefusalCode.REAL_DATA_ADMISSION_CLOSED)
        if not request.task or not isinstance(request.provider_payload, Mapping):
            raise EgressRefused(EgressRefusalCode.ROUTE_NOT_ALLOWED)
        body = _canonical_json_bytes(request.provider_payload)
        payload_hash = hashlib.sha256(body).hexdigest()
        try:
            consume_egress_authorization(
                request.egress_authorization,
                task=request.task,
                request_id=request.request_id,
                disclosure_hash=payload_hash,
            )
        except OwnershipRefused as exc:
            raise EgressRefused(EgressRefusalCode.OWNERSHIP_AUTHORIZATION_REQUIRED) from exc
        frozen = FrozenProviderRequest(
            task=request.task,
            body=body,
            payload_hash=payload_hash,
        )
        logger.info(
            "LLM egress request task=%s payload_hash=%s",
            request.task,
            frozen.payload_hash,
        )
        if request.max_attempts < 1 or request.max_attempts > 3:
            raise EgressRefused(EgressRefusalCode.ROUTE_NOT_ALLOWED)
        for attempt in range(1, request.max_attempts + 1):
            try:
                raw_response = _dispatch_final_request(frozen)
                return EgressResult(
                    task=request.task,
                    content=UntrustedProviderOutput(raw_response),
                    payload_hash=frozen.payload_hash,
                    attempt_count=attempt,
                )
            except RetryableProviderError:
                logger.warning(
                    "LLM egress retry task=%s payload_hash=%s attempt=%d",
                    request.task,
                    frozen.payload_hash,
                    attempt,
                )
                if attempt == request.max_attempts:
                    raise
        raise AssertionError("unreachable")


_CLOSED_AUTHORITY = LlmEgressAuthority()


def _mint_synthetic_test_request(
    *,
    task: str,
    provider_payload: Mapping[str, Any],
    identity_state: IdentityState = IdentityState.PSEUDONYMOUS,
    max_attempts: int = 1,
    request_id: str = "",
    egress_authorization: EgressAuthorization | None = None,
) -> SyntheticEgressRequest:
    """Test-harness-only mint; production use is forbidden by static policy."""

    return SyntheticEgressRequest(
        task=task,
        provider_payload=provider_payload,
        identity_state=identity_state,
        max_attempts=max_attempts,
        _admission=_SYNTHETIC_TEST_ADMISSION,
        request_id=request_id,
        egress_authorization=egress_authorization,
    )


def dispatch_legacy_synthetic(task: str, **provider_payload: Any) -> Any:
    """Route a legacy semantic payload through the closed Slice-1 authority.

    This compatibility adapter exists only to remove provider bypasses while
    later slices replace legacy prompt-shaped inputs with receipted segments.
    It cannot install a transport or select a real-data mode.
    """

    request = SyntheticEgressRequest(
        task=task,
        provider_payload=MappingProxyType(dict(provider_payload)),
    )
    result = _CLOSED_AUTHORITY.dispatch(request)
    return _UntrustedLegacyResponseProxy(result.content.raw_response)
