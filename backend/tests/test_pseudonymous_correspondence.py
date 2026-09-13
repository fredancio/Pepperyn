"""Falsification tests for durable governed pseudonymous correspondence."""

from dataclasses import replace
from pathlib import Path

from services.pseudonymous_correspondence import (
    CRYPTO_VERSION,
    CorrespondenceRecord,
    CorrespondenceRefused,
    CorrespondenceScope,
    GovernedCorrespondenceRegistry,
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


def test_same_identity_is_stable_across_analyses_and_restart_workers():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    first_worker = GovernedCorrespondenceRegistry(repository, KEY)
    first = first_worker.register(scope=scope, analysis_id=ANALYSIS_1,
        category="CUSTOMER", real_identity="Dupont Construction SA")
    # A new object represents a restarted process or another worker.
    second_worker = GovernedCorrespondenceRegistry(repository, KEY)
    second = second_worker.register(scope=scope, analysis_id=ANALYSIS_2,
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
    registered = first_worker.register(scope=scope, analysis_id=ANALYSIS_1,
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
    first_worker.register(scope=scope, analysis_id=ANALYSIS_1,
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
        registry.register(scope=CorrespondenceScope(TENANT_A, ENTITY_A), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
        registry.register(scope=CorrespondenceScope(TENANT_A, ENTITY_B), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
        registry.register(scope=CorrespondenceScope(TENANT_B, ENTITY_A), analysis_id=ANALYSIS_1,
            category="CUSTOMER", real_identity="Shared Counterparty"),
    ]
    assert len({reference.pseudonym for reference in references}) == 3
    assert len({record.real_fingerprint for record in repository.records.values()}) == 3


def test_repository_contains_ciphertext_not_identity_and_tampering_fails_closed():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    reference = registry.register(scope=scope, analysis_id=ANALYSIS_1,
        category="SUPPLIER", real_identity="Highly Sensitive Supplier")
    record = next(iter(repository.records.values()))
    serialized = repr(record)
    assert "Highly Sensitive Supplier" not in serialized
    assert record.crypto_version == CRYPTO_VERSION
    repository.records[record.id] = replace(record, encrypted_value=record.encrypted_value[:-2] + "AA")
    refuses("CORRESPONDENCE_INTEGRITY_FAILED", lambda: registry.rehydrate(
        reference.pseudonym, scope=scope, handles=[reference.handle]))


def test_handle_is_opaque_scope_bound_versioned_and_tamper_evident():
    repository = DurableMemoryRepository()
    scope = CorrespondenceScope(TENANT_A, ENTITY_A)
    registry = GovernedCorrespondenceRegistry(repository, KEY)
    reference = registry.register(scope=scope, analysis_id=ANALYSIS_1,
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
    reference = first.register(scope=scope, analysis_id=ANALYSIS_1,
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
    reference = registry.register(scope=scope, analysis_id=ANALYSIS_1,
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
