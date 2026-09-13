"""Falsification tests for durable governed pseudonymous correspondence."""

from dataclasses import replace
from pathlib import Path
import time

from services.pseudonymous_correspondence import (
    CRYPTO_VERSION,
    CorrespondenceRecord,
    CorrespondenceRefused,
    CorrespondenceScope,
    GovernedCorrespondenceRegistry,
)
from services.ownership_authority import (
    InMemoryOwnershipRepository, InMemoryScopedContextRepository,
    OwnershipAuthority, OwnershipRecord, OwnershipRefused, ProtectedContextReader,
    ProtectedResource, ScopedContextRecord,
)


TENANT_A = "11111111-1111-4111-8111-111111111111"
TENANT_B = "22222222-2222-4222-8222-222222222222"
ENTITY_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ENTITY_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ANALYSIS_1 = "10000000-0000-4000-8000-000000000001"
ANALYSIS_2 = "10000000-0000-4000-8000-000000000002"
KEY = bytes(range(32))


class DurableMemoryRepository:
    """Shared fake persistence: survives registry/process object recreation."""
    def __init__(self):
        self.records = {}
        self.bindings = set()
        self.writes = []

    def find_by_fingerprint(self, scope, category, fingerprint):
        return next((record for record in self.records.values()
            if record.scope == scope and record.category == category
            and record.real_fingerprint == fingerprint), None)

    def find_by_pseudonym(self, scope, pseudonym):
        return next((record for record in self.records.values()
            if record.scope == scope and record.pseudonym == pseudonym), None)

    def find_by_id(self, scope, record_id):
        record = self.records.get(record_id)
        return record if record and record.scope == scope else None

    def insert(self, record):
        self.writes.append("insert")
        self.records[record.id] = record
    def bind_analysis(self, record_id, scope, analysis_id):
        self.writes.append("bind")
        assert self.records[record_id].scope == scope
        self.bindings.add((record_id, scope.company_id, scope.entity_id, analysis_id))
    def active_analysis_bindings(self, record_id, scope):
        return tuple(item[3] for item in self.bindings
            if item[:3] == (record_id, scope.company_id, scope.entity_id))
    def purge(self, record_id, scope):
        assert self.records[record_id].scope == scope
        del self.records[record_id]


class AllowPurge:
    def authorize_purge(self, _record, active_analysis_ids): return not active_analysis_ids


def refuses(code, operation):
    try:
        operation()
    except CorrespondenceRefused as exc:
        assert str(exc) == code
        return
    raise AssertionError(f"expected {code}")


def registration_authority(*, scope, analysis_id, category, real_identity,
        ttl_seconds=30.0, details=False):
    request_id = f"register-{analysis_id}-{category}"
    source = {"identity": real_identity}
    authority = OwnershipAuthority(InMemoryOwnershipRepository([
        OwnershipRecord(analysis_id, scope.company_id, scope.entity_id,
            f"engagement-{scope.entity_id}", scope.company_id, scope.entity_id),
    ]), ttl_seconds=ttl_seconds,
        projection_policy={ProtectedResource.ENTITY_CONTEXT: frozenset({("identity",)})})
    principal = authority._accept_authenticated_principal("principal", scope.company_id)
    grant = authority.resolve_and_mint_read_grant(principal=principal,
        analysis_id=analysis_id, request_id=request_id,
        resources=[ProtectedResource.ENTITY_CONTEXT])
    record = ScopedContextRecord(ProtectedResource.ENTITY_CONTEXT,
        scope.company_id, scope.entity_id, grant.scope.engagement_id, analysis_id, source)
    whole = ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(
        grant, request_id=request_id, resource=ProtectedResource.ENTITY_CONTEXT)[0][1]
    identity_receipt = authority.project_read(whole, ("identity",))
    authorization = authority.mint_correspondence_registration_authorization(
        grant=grant, request_id=request_id, category=category,
        real_identity=real_identity, identity_receipt=identity_receipt)
    if details:
        return request_id, authorization, authority, grant, identity_receipt
    return request_id, authorization


def authorized_register(registry, *, scope, analysis_id, category, real_identity):
    request_id, authorization = registration_authority(scope=scope,
        analysis_id=analysis_id, category=category, real_identity=real_identity)
    return registry.register(scope=scope, analysis_id=analysis_id, category=category,
        real_identity=real_identity, registration_request_id=request_id,
        registration_authorization=authorization)


def test_direct_registration_without_authority_fails_closed():
    registry = GovernedCorrespondenceRegistry(DurableMemoryRepository(), KEY)
    refuses("CORRESPONDENCE_REGISTRATION_AUTHORITY_REQUIRED", lambda: registry.register(
        scope=CorrespondenceScope(TENANT_A, ENTITY_A), analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Synthetic Customer",
        registration_request_id="direct", registration_authorization=None))


def test_registration_authority_is_single_use_and_exactly_bound():
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(DurableMemoryRepository(), KEY)
    request_id, authorization = registration_authority(scope=scope,
        analysis_id=ANALYSIS_1, category="CUSTOMER", real_identity="Synthetic Customer")
    kwargs = dict(scope=scope, analysis_id=ANALYSIS_1, category="CUSTOMER",
        real_identity="Synthetic Customer", registration_request_id=request_id,
        registration_authorization=authorization)
    registry.register(**kwargs)
    refuses("CORRESPONDENCE_REGISTRATION_AUTHORITY_REQUIRED", lambda: registry.register(**kwargs))


def test_registration_source_receipt_cannot_mint_two_authorities():
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    request_id, _, authority, grant, identity_receipt = registration_authority(
        scope=scope, analysis_id=ANALYSIS_1, category="CUSTOMER",
        real_identity="Synthetic Customer", details=True)
    try:
        authority.mint_correspondence_registration_authorization(
            grant=grant, request_id=request_id, category="CUSTOMER",
            real_identity="Synthetic Customer", identity_receipt=identity_receipt)
    except OwnershipRefused as exc:
        assert str(exc) == "REGISTRATION_SOURCE_RECEIPT_REPLAYED"
    else:
        raise AssertionError("registration source receipt replayed")


def test_registration_substitution_and_foreign_scope_fail_closed():
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    cases = (
        dict(real_identity="Other Customer"),
        dict(category="SUPPLIER"),
        dict(analysis_id=ANALYSIS_2),
        dict(scope=CorrespondenceScope(TENANT_A, ENTITY_B)),
        dict(scope=CorrespondenceScope(TENANT_B, ENTITY_A)),
        dict(registration_request_id="other-request"),
    )
    for change in cases:
        registry = GovernedCorrespondenceRegistry(DurableMemoryRepository(), KEY)
        request_id, authorization = registration_authority(scope=scope,
            analysis_id=ANALYSIS_1, category="CUSTOMER", real_identity="Synthetic Customer")
        values = dict(scope=scope, analysis_id=ANALYSIS_1, category="CUSTOMER",
            real_identity="Synthetic Customer", registration_request_id=request_id,
            registration_authorization=authorization)
        values.update(change)
        refuses("CORRESPONDENCE_REGISTRATION_AUTHORITY_REQUIRED",
            lambda values=values: registry.register(**values))


def test_stale_registration_authority_fails_closed():
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    request_id, authorization = registration_authority(scope=scope,
        analysis_id=ANALYSIS_1, category="CUSTOMER",
        real_identity="Synthetic Customer", ttl_seconds=0.001)
    time.sleep(0.05)
    registry = GovernedCorrespondenceRegistry(DurableMemoryRepository(), KEY)
    refuses("CORRESPONDENCE_REGISTRATION_AUTHORITY_REQUIRED", lambda: registry.register(
        scope=scope, analysis_id=ANALYSIS_1, category="CUSTOMER",
        real_identity="Synthetic Customer", registration_request_id=request_id,
        registration_authorization=authorization))


def test_same_identity_is_stable_across_analyses_and_restart_workers():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    first_worker = GovernedCorrespondenceRegistry(repository, KEY)
    first = authorized_register(first_worker, scope=scope, analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Dupont Construction SA")
    # A new object represents a restarted process or another worker.
    second_worker = GovernedCorrespondenceRegistry(repository, KEY)
    second = authorized_register(second_worker, scope=scope, analysis_id=ANALYSIS_2,
        category="CUSTOMER", real_identity="Dupont Construction SA")
    assert first.pseudonym == second.pseudonym
    assert second_worker.rehydrate(
        {"client": second.pseudonym}, scope=scope, handles=[second.handle],
    ) == {"client": "Dupont Construction SA"}
    assert len(repository.records) == 1
    assert len(repository.bindings) == 2


def test_second_process_verification_is_strictly_read_only():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    first_worker = GovernedCorrespondenceRegistry(repository, KEY)
    registered = authorized_register(first_worker, scope=scope, analysis_id=ANALYSIS_1,
        category="COUNTERPARTY", real_identity="Synthetic Counterparty")
    writes_after_registration = list(repository.writes)
    second_worker = GovernedCorrespondenceRegistry(repository, KEY)
    existing = second_worker.reference_existing(scope=scope,
        category="COUNTERPARTY", real_identity="Synthetic Counterparty")
    assert existing.pseudonym == registered.pseudonym
    assert second_worker.rehydrate(existing.pseudonym, scope=scope,
        handles=[existing.handle]) == "Synthetic Counterparty"
    assert repository.writes == writes_after_registration


def test_second_process_verifies_unicode_identity_without_writing():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    first_worker = GovernedCorrespondenceRegistry(repository, KEY)
    authorized_register(first_worker, scope=scope, analysis_id=ANALYSIS_1,
        category="COUNTERPARTY",
        real_identity="V33 SYNTHETIC COUNTERPARTY — NO REAL IDENTITY")
    writes_after_registration = list(repository.writes)

    second_worker = GovernedCorrespondenceRegistry(repository, KEY)
    existing = second_worker.reference_existing(scope=scope, category="COUNTERPARTY",
        real_identity="V33 SYNTHETIC COUNTERPARTY — NO REAL IDENTITY")

    assert second_worker.rehydrate(existing.pseudonym, scope=scope,
        handles=[existing.handle]) == "V33 SYNTHETIC COUNTERPARTY — NO REAL IDENTITY"
    assert repository.writes == writes_after_registration


def test_same_identity_is_non_correlatable_across_client_boundaries():
    repository = DurableMemoryRepository()
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    references = [
        authorized_register(registry, scope=CorrespondenceScope(TENANT_A, ENTITY_A), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
        authorized_register(registry, scope=CorrespondenceScope(TENANT_A, ENTITY_B), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
        authorized_register(registry, scope=CorrespondenceScope(TENANT_B, ENTITY_A), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
    ]
    assert len({reference.pseudonym for reference in references}) == 3
    assert len({record.real_fingerprint for record in repository.records.values()}) == 3


def test_repository_contains_ciphertext_not_identity_and_tampering_fails_closed():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    reference = authorized_register(registry, scope=scope, analysis_id=ANALYSIS_1,
        category="SUPPLIER", real_identity="Highly Sensitive Supplier")
    record = next(iter(repository.records.values()))
    serialized = repr(record)
    assert "Highly Sensitive Supplier" not in serialized
    assert record.crypto_version == CRYPTO_VERSION
    assert record.registration_version == "ownership-v1"
    assert len(record.registration_request_sha256) == 64
    assert len(record.registration_authority_sha256) == 64
    assert len(record.registration_source_receipt_sha256) == 64
    repository.records[record.id] = replace(record, encrypted_value=record.encrypted_value[:-2] + "AA")
    refuses("CORRESPONDENCE_INTEGRITY_FAILED", lambda: registry.rehydrate(
        reference.pseudonym, scope=scope, handles=[reference.handle]))


def test_handle_is_opaque_scope_bound_versioned_and_tamper_evident():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    reference = authorized_register(registry, scope=scope, analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Dupont Construction SA")
    assert "Dupont" not in reference.handle
    refuses("CORRESPONDENCE_SCOPE_MISMATCH", lambda: registry.rehydrate(
        reference.pseudonym, scope=CorrespondenceScope(TENANT_A, ENTITY_B), handles=[reference.handle]))
    refuses("CORRESPONDENCE_HANDLE_INVALID", lambda: registry.rehydrate(
        reference.pseudonym, scope=scope, handles=[reference.handle + "x"]))
    record = next(iter(repository.records.values()))
    repository.records[record.id] = replace(record, mapping_version=2)
    refuses("CORRESPONDENCE_UNAVAILABLE", lambda: registry.rehydrate(
        reference.pseudonym, scope=scope, handles=[reference.handle]))


def test_wrong_key_cannot_link_or_decrypt_existing_mapping():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    first = GovernedCorrespondenceRegistry(repository, KEY)
    reference = authorized_register(first, scope=scope, analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Dupont Construction SA")
    other_key_worker = GovernedCorrespondenceRegistry(repository, b"z" * 32)
    try:
        other_key_worker.rehydrate(reference.pseudonym, scope=scope, handles=[reference.handle])
    except CorrespondenceRefused:
        pass
    else:
        raise AssertionError("wrong key unexpectedly resolved correspondence")


def test_purge_requires_injected_policy_and_zero_active_analysis_bindings():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    reference = authorized_register(registry, scope=scope, analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Transient Customer")
    refuses("PURGE_POLICY_REQUIRED", lambda: registry.purge(
        scope=scope, handle=reference.handle, policy=None))
    refuses("CORRESPONDENCE_RETENTION_REQUIRED", lambda: registry.purge(
        scope=scope, handle=reference.handle, policy=AllowPurge()))
    repository.bindings.clear()  # simulates authoritative analysis/reference deletion
    registry.purge(scope=scope, handle=reference.handle, policy=AllowPurge())
    assert repository.records == {}


def test_migration_is_backend_only_immutable_and_reference_guarded():
    sql = (Path(__file__).parents[1] / "migrations" /
        "v33_governed_pseudonymous_correspondence.sql").read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FROM PUBLIC, anon, authenticated, service_role" in sql
    assert "BEFORE UPDATE" in sql
    assert "correspondence retention required" in sql
    assert "ON DELETE CASCADE" in sql  # bindings disappear with their analysis
    assert "GRANT SELECT, INSERT" in sql
    assert "GRANT UPDATE" not in sql and "GRANT DELETE" not in sql


def test_v34_requires_authoritative_origin_for_every_new_mapping():
    sql = (Path(__file__).parents[1] / "migrations" /
        "v34_authorized_correspondence_registration.sql").read_text(encoding="utf-8")
    assert "require_authorized_correspondence_registration_v1" in sql
    assert "BEFORE INSERT" in sql
    assert "registration_authority_sha256 IS NULL" in sql
    assert "registration_source_receipt_sha256 IS NULL" in sql
    assert "UPDATE public.pseudonymous_correspondence" not in sql


def test_correspondence_component_has_no_provider_or_egress_dependency():
    source = (Path(__file__).parents[1] / "services" /
        "pseudonymous_correspondence.py").read_text(encoding="utf-8")
    assert "services.llm_egress" not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "requests." not in source and "httpx" not in source


def test_reference_existing_preserves_fail_closed_repository_reason():
    class RefusingRepository(DurableMemoryRepository):
        def find_by_fingerprint(self, scope, category, fingerprint):
            raise CorrespondenceRefused("CORRESPONDENCE_RECORD_AMBIGUOUS")

    registry = GovernedCorrespondenceRegistry(RefusingRepository(), KEY)
    refuses("CORRESPONDENCE_RECORD_AMBIGUOUS", lambda: registry.reference_existing(
        scope=CorrespondenceScope(TENANT_A, ENTITY_A), category="CUSTOMER",
        real_identity="Synthetic Counterparty"))
