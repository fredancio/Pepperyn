"""Durable, scoped pseudonymous correspondence for the V1 privacy boundary.

Real identities never leave this component. Stable pseudonyms are derived
inside one company/entity continuity boundary and are therefore deliberately
non-correlatable across Pepperyn clients. No provider transport lives here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from typing import Any, Iterable, Protocol
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


CRYPTO_VERSION = "v1-aes256gcm-hmacsha256"
_CATEGORY = re.compile(r"^[A-Z][A-Z0-9_]{1,31}$")
_PSEUDONYM = re.compile(r"^[A-Z][A-Z0-9_]{1,31}-[A-F0-9]{16}$")


class CorrespondenceRefused(RuntimeError):
    """Content-free fail-closed refusal."""


@dataclass(frozen=True)
class CorrespondenceScope:
    company_id: str
    entity_id: str

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "company_id", str(UUID(self.company_id)))
            object.__setattr__(self, "entity_id", str(UUID(self.entity_id)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_SCOPE_INVALID") from exc


@dataclass(frozen=True)
class CorrespondenceRecord:
    id: str
    scope: CorrespondenceScope
    category: str
    pseudonym: str
    real_fingerprint: str
    encrypted_value: str
    nonce: str
    ciphertext_sha256: str
    crypto_version: str
    mapping_version: int


@dataclass(frozen=True)
class PseudonymousReference:
    pseudonym: str
    handle: str


class CorrespondenceRepository(Protocol):
    def find_by_fingerprint(self, scope: CorrespondenceScope, category: str, fingerprint: str) -> CorrespondenceRecord | None: ...
    def find_by_pseudonym(self, scope: CorrespondenceScope, pseudonym: str) -> CorrespondenceRecord | None: ...
    def find_by_id(self, scope: CorrespondenceScope, record_id: str) -> CorrespondenceRecord | None: ...
    def insert(self, record: CorrespondenceRecord) -> None: ...
    def bind_analysis(self, record_id: str, scope: CorrespondenceScope, analysis_id: str) -> None: ...
    def active_analysis_bindings(self, record_id: str, scope: CorrespondenceScope) -> tuple[str, ...]: ...
    def purge(self, record_id: str, scope: CorrespondenceScope) -> None: ...


class PurgePolicy(Protocol):
    """Injected policy: no legal or product retention duration is assumed."""
    def authorize_purge(self, record: CorrespondenceRecord, active_analysis_ids: tuple[str, ...]) -> bool: ...


class GovernedCorrespondenceRegistry:
    """Encrypt mappings, issue opaque handles and perform local rehydration."""

    def __init__(self, repository: CorrespondenceRepository, master_key: bytes) -> None:
        if not isinstance(master_key, bytes) or len(master_key) != 32:
            raise CorrespondenceRefused("CORRESPONDENCE_KEY_INVALID")
        self._repository = repository
        self._encryption_key = hmac.new(master_key, b"pepperyn:correspondence:encryption:v1", hashlib.sha256).digest()
        self._pseudonym_key = hmac.new(master_key, b"pepperyn:correspondence:pseudonym:v1", hashlib.sha256).digest()
        self._handle_key = hmac.new(master_key, b"pepperyn:correspondence:handle:v1", hashlib.sha256).digest()

    @classmethod
    def from_environment(cls, repository: CorrespondenceRepository) -> "GovernedCorrespondenceRegistry":
        encoded = os.getenv("PEPPERYN_CORRESPONDENCE_KEY", "")
        try:
            key = _unb64(encoded)
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_KEY_INVALID") from exc
        return cls(repository, key)

    def register(
        self, *, scope: CorrespondenceScope, analysis_id: str,
        category: str, real_identity: str, handle_ttl_seconds: int = 300,
    ) -> PseudonymousReference:
        category = category.strip().upper()
        real_identity = real_identity.strip()
        analysis_id = _uuid(analysis_id)
        if not _CATEGORY.fullmatch(category) or len(real_identity) < 2 or len(real_identity) > 1000:
            raise CorrespondenceRefused("CORRESPONDENCE_VALUE_INVALID")
        fingerprint = self._fingerprint(scope, category, real_identity)
        pseudonym = f"{category}-{fingerprint[:16]}"
        record = self._repository.find_by_fingerprint(scope, category, fingerprint)
        collision = self._repository.find_by_pseudonym(scope, pseudonym)
        if collision is not None and (record is None or collision.id != record.id):
            raise CorrespondenceRefused("CORRESPONDENCE_COLLISION")
        if record is None:
            record_id = str(uuid4())
            nonce = secrets.token_bytes(12)
            aad = self._aad(record_id, scope, category, pseudonym, 1)
            encrypted = AESGCM(self._encryption_key).encrypt(nonce, real_identity.encode("utf-8"), aad)
            record = CorrespondenceRecord(
                id=record_id, scope=scope, category=category, pseudonym=pseudonym,
                real_fingerprint=fingerprint,
                encrypted_value=_b64(encrypted), nonce=_b64(nonce),
                ciphertext_sha256=hashlib.sha256(encrypted).hexdigest().upper(),
                crypto_version=CRYPTO_VERSION, mapping_version=1,
            )
            try:
                self._repository.insert(record)
            except Exception as exc:
                raise CorrespondenceRefused("CORRESPONDENCE_PERSISTENCE_FAILED") from exc
        else:
            self._decrypt_and_verify(record, expected_identity=real_identity)
        try:
            self._repository.bind_analysis(record.id, scope, analysis_id)
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_BINDING_FAILED") from exc
        return PseudonymousReference(record.pseudonym, self._issue_handle(record, handle_ttl_seconds))

    def reference_existing(
        self, *, scope: CorrespondenceScope, category: str,
        real_identity: str, handle_ttl_seconds: int = 300,
    ) -> PseudonymousReference:
        """Resolve an existing mapping without inserting or binding anything."""
        category = category.strip().upper()
        real_identity = real_identity.strip()
        if not _CATEGORY.fullmatch(category) or len(real_identity) < 2 or len(real_identity) > 1000:
            raise CorrespondenceRefused("CORRESPONDENCE_VALUE_INVALID")
        fingerprint = self._fingerprint(scope, category, real_identity)
        try:
            record = self._repository.find_by_fingerprint(scope, category, fingerprint)
        except CorrespondenceRefused:
            raise
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_PERSISTENCE_FAILED") from exc
        if record is None:
            raise CorrespondenceRefused("CORRESPONDENCE_UNAVAILABLE")
        self._decrypt_and_verify(record, expected_identity=real_identity)
        return PseudonymousReference(record.pseudonym, self._issue_handle(record, handle_ttl_seconds))

    def rehydrate(
        self, value: Any, *, scope: CorrespondenceScope, handles: Iterable[str],
    ) -> Any:
        replacements: dict[str, str] = {}
        for handle in handles:
            record = self._resolve_handle(handle, scope)
            replacements[record.pseudonym] = self._decrypt_and_verify(record)
        return _replace_recursive(value, replacements)

    def purge(
        self, *, scope: CorrespondenceScope, handle: str,
        policy: PurgePolicy | None,
    ) -> None:
        if policy is None:
            raise CorrespondenceRefused("PURGE_POLICY_REQUIRED")
        record = self._resolve_handle(handle, scope)
        try:
            bindings = self._repository.active_analysis_bindings(record.id, scope)
            if bindings or not policy.authorize_purge(record, bindings):
                raise CorrespondenceRefused("CORRESPONDENCE_RETENTION_REQUIRED")
            self._repository.purge(record.id, scope)
        except CorrespondenceRefused:
            raise
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_PURGE_FAILED") from exc

    def _fingerprint(self, scope: CorrespondenceScope, category: str, real_identity: str) -> str:
        material = json.dumps(
            [scope.company_id, scope.entity_id, category, real_identity],
            ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(self._pseudonym_key, material, hashlib.sha256).hexdigest().upper()

    def _issue_handle(self, record: CorrespondenceRecord, ttl_seconds: int) -> str:
        if not isinstance(ttl_seconds, int) or ttl_seconds < 1 or ttl_seconds > 300:
            raise CorrespondenceRefused("CORRESPONDENCE_HANDLE_TTL_INVALID")
        payload = {
            "id": record.id, "company_id": record.scope.company_id,
            "entity_id": record.scope.entity_id, "version": record.mapping_version,
            "exp": int(datetime.now(timezone.utc).timestamp()) + ttl_seconds,
        }
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._handle_key).encrypt(
            nonce, json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            b"pepperyn:correspondence:opaque-handle:v1",
        )
        return f"{_b64(nonce)}.{_b64(ciphertext)}"

    def _resolve_handle(self, handle: str, scope: CorrespondenceScope) -> CorrespondenceRecord:
        try:
            nonce, ciphertext = handle.split(".", 1)
            clear = AESGCM(self._handle_key).decrypt(
                _unb64(nonce), _unb64(ciphertext),
                b"pepperyn:correspondence:opaque-handle:v1",
            )
            payload = json.loads(clear)
            if int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
                raise CorrespondenceRefused("CORRESPONDENCE_HANDLE_EXPIRED")
            if payload["company_id"] != scope.company_id or payload["entity_id"] != scope.entity_id:
                raise CorrespondenceRefused("CORRESPONDENCE_SCOPE_MISMATCH")
            record = self._repository.find_by_id(scope, _uuid(payload["id"]))
            if record is None or record.mapping_version != int(payload["version"]):
                raise CorrespondenceRefused("CORRESPONDENCE_UNAVAILABLE")
            return record
        except CorrespondenceRefused:
            raise
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_HANDLE_INVALID") from exc

    def _decrypt_and_verify(self, record: CorrespondenceRecord, expected_identity: str | None = None) -> str:
        if record.crypto_version != CRYPTO_VERSION or not _PSEUDONYM.fullmatch(record.pseudonym):
            raise CorrespondenceRefused("CORRESPONDENCE_VERSION_UNSUPPORTED")
        try:
            encrypted = _unb64(record.encrypted_value)
            if not hmac.compare_digest(
                record.ciphertext_sha256, hashlib.sha256(encrypted).hexdigest().upper(),
            ):
                raise CorrespondenceRefused("CORRESPONDENCE_INTEGRITY_FAILED")
            aad = self._aad(record.id, record.scope, record.category, record.pseudonym, record.mapping_version)
            clear = AESGCM(self._encryption_key).decrypt(_unb64(record.nonce), encrypted, aad).decode("utf-8")
        except CorrespondenceRefused:
            raise
        except Exception as exc:
            raise CorrespondenceRefused("CORRESPONDENCE_INTEGRITY_FAILED") from exc
        if not hmac.compare_digest(record.real_fingerprint, self._fingerprint(record.scope, record.category, clear)):
            raise CorrespondenceRefused("CORRESPONDENCE_INTEGRITY_FAILED")
        # compare_digest rejects non-ASCII ``str`` values. Identities are
        # legitimate Unicode text, so compare their canonical UTF-8 bytes.
        if expected_identity is not None and not hmac.compare_digest(
            clear.encode("utf-8"), expected_identity.encode("utf-8"),
        ):
            raise CorrespondenceRefused("CORRESPONDENCE_INTEGRITY_FAILED")
        return clear

    @staticmethod
    def _aad(record_id: str, scope: CorrespondenceScope, category: str, pseudonym: str, version: int) -> bytes:
        return json.dumps(
            [record_id, scope.company_id, scope.entity_id, category, pseudonym, version, CRYPTO_VERSION],
            separators=(",", ":"),
        ).encode("utf-8")


class SupabaseCorrespondenceRepository:
    """Service-role adapter; database RLS remains defense in depth."""

    def __init__(self, supabase: Any) -> None:
        self._supabase = supabase

    def _one(self, query: Any) -> CorrespondenceRecord | None:
        rows = query.limit(2).execute().data or []
        if len(rows) > 1:
            raise CorrespondenceRefused("CORRESPONDENCE_AMBIGUOUS")
        return _row_to_record(rows[0]) if rows else None

    def find_by_fingerprint(self, scope, category, fingerprint):
        return self._one(self._base(scope).eq("category", category).eq("real_fingerprint", fingerprint))

    def find_by_pseudonym(self, scope, pseudonym):
        return self._one(self._base(scope).eq("pseudonym", pseudonym))

    def find_by_id(self, scope, record_id):
        return self._one(self._base(scope).eq("id", record_id))

    def insert(self, record):
        self._supabase.from_("pseudonymous_correspondence").insert({
            "id": record.id, "company_id": record.scope.company_id, "entity_id": record.scope.entity_id,
            "category": record.category, "pseudonym": record.pseudonym,
            "real_fingerprint": record.real_fingerprint, "encrypted_value": record.encrypted_value,
            "nonce": record.nonce, "ciphertext_sha256": record.ciphertext_sha256,
            "crypto_version": record.crypto_version,
            "mapping_version": record.mapping_version,
        }).execute()

    def bind_analysis(self, record_id, scope, analysis_id):
        self._supabase.from_("pseudonymous_correspondence_bindings").upsert({
            "correspondence_id": record_id, "analysis_id": analysis_id,
            "company_id": scope.company_id, "entity_id": scope.entity_id,
        }, on_conflict="correspondence_id,analysis_id", ignore_duplicates=True).execute()

    def active_analysis_bindings(self, record_id, scope):
        rows = (self._supabase.from_("pseudonymous_correspondence_bindings").select("analysis_id")
            .eq("correspondence_id", record_id).eq("company_id", scope.company_id)
            .eq("entity_id", scope.entity_id).execute()).data or []
        return tuple(row["analysis_id"] for row in rows)

    def purge(self, record_id, scope):
        self._supabase.rpc("purge_pseudonymous_correspondence_v1", {
            "p_correspondence_id": record_id, "p_company_id": scope.company_id,
            "p_entity_id": scope.entity_id,
        }).execute()

    def _base(self, scope):
        return (self._supabase.from_("pseudonymous_correspondence")
            .select("id,company_id,entity_id,category,pseudonym,real_fingerprint,encrypted_value,nonce,ciphertext_sha256,crypto_version,mapping_version")
            .eq("company_id", scope.company_id).eq("entity_id", scope.entity_id))


def _row_to_record(row: dict[str, Any]) -> CorrespondenceRecord:
    return CorrespondenceRecord(
        id=_uuid(row["id"]), scope=CorrespondenceScope(row["company_id"], row["entity_id"]),
        category=row["category"], pseudonym=row["pseudonym"], real_fingerprint=row["real_fingerprint"],
        encrypted_value=row["encrypted_value"], nonce=row["nonce"],
        ciphertext_sha256=row["ciphertext_sha256"],
        crypto_version=row["crypto_version"], mapping_version=int(row["mapping_version"]),
    )


def _replace_recursive(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        result = value
        for pseudonym in sorted(replacements, key=len, reverse=True):
            result = result.replace(pseudonym, replacements[pseudonym])
        return result
    if isinstance(value, list):
        return [_replace_recursive(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_recursive(item, replacements) for item in value)
    if isinstance(value, dict):
        return {key: _replace_recursive(item, replacements) for key, item in value.items()}
    return value


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise CorrespondenceRefused("CORRESPONDENCE_SCOPE_INVALID") from exc


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
