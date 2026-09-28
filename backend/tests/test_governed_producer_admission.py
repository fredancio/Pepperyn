"""Local fake-auth/read-only DB proof, not live authentication or Beta admission."""
import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.governed_producer_admission import (
    AdmissionRefused, LocalProducerAdmissionPreparation, LocalSyntheticProfile,
)
from services.producer_execution_contract import ExecutionBindingsV2
from test_governed_analysis_persistence import _db, COMPANY_A, COMPANY_B, ENTITY_A, ENTITY_B, ENGAGEMENT_A

ACTOR = "50000000-0000-0000-0000-000000000001"
OTHER = "50000000-0000-0000-0000-000000000002"
NAME = "pepperyn_v1_heterogeneous_english.xlsx"
RAW = (Path(__file__).parent / "golden/fixtures" / NAME).read_bytes()


@pytest.fixture
def system(monkeypatch):
    import socket
    network_attempts = []
    def blocked(*args, **kwargs):
        network_attempts.append(True)
        raise AssertionError("NETWORK_FORBIDDEN")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    db = _db()
    db.tables["companies"] = [{"id": COMPANY_A}, {"id": COMPANY_B}]
    db.tables["profiles"] = [{"id": ACTOR, "company_id": COMPANY_A},
                             {"id": OTHER, "company_id": COMPANY_B}]
    def user(token):
        if token not in {"owner", "foreign"}:
            raise ValueError("INVALID_TOKEN")
        return SimpleNamespace(user=SimpleNamespace(id=ACTOR if token == "owner" else OTHER))
    db.auth = SimpleNamespace(get_user=user)
    profile = LocalSyntheticProfile(
        company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        producer_id="test-only-uninstalled", producer_version="version-1",
        task_id="test-only-analysis", task_version="version-1",
        source_sha256=sha256(RAW).hexdigest().upper(), filename=NAME,
    )
    service = LocalProducerAdmissionPreparation(db, profile=profile)
    yield db, profile, service
    assert network_attempts == []


def prepare(service, **changes):
    return service.prepare(**(dict(authorization="Bearer owner", entity_id=ENTITY_A,
        engagement_id=ENGAGEMENT_A, raw=RAW, filename=NAME) | changes))


def consume(service, prepared, **changes):
    return service.consume_for_local_validation(prepared, **(dict(authorization="Bearer owner", raw=RAW) | changes))


def unchanged(db, before):
    assert db.tables == before  # No analysis, receipt, decision, memory or artifact row.
    assert not any(entry[0] == "rpc" for entry in db.log)


def test_owned_input_bound_and_consumed_once_without_writes(system):
    db, _, service = system
    before = copy.deepcopy(db.tables)
    p = prepare(service)
    assert str(p.bindings.actor_id) == ACTOR
    assert sha256(p.input_json.encode()).hexdigest().upper() == p.bindings.producer_input_sha256
    assert consume(service, p) == p.input_json
    with pytest.raises(AdmissionRefused):
        consume(service, p)
    unchanged(db, before)


@pytest.mark.parametrize("changes", [
    {"authorization": None}, {"authorization": "Bearer guest"}, {"authorization": "Bearer foreign"},
    {"entity_id": ENTITY_B}, {"engagement_id": str(uuid4())},
    {"filename": "different.xlsx"}, {"raw": RAW + b"mutation"}, {"raw": bytearray(RAW)},
])
def test_refused_preparation_has_no_effect(system, changes):
    db, _, service = system
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused, match="COMPOSITION_PREPARATION_REFUSED"):
        prepare(service, **changes)
    assert not service._authority._prospective_executions
    unchanged(db, before)


@pytest.mark.parametrize("table,change", [
    ("profiles", "missing"), ("profiles", "duplicate"), ("companies", "missing"),
    ("entities", "missing"), ("entities", "foreign"), ("engagements", "missing"),
    ("engagements", "foreign"), ("engagements", "duplicate"),
])
def test_authoritative_parent_failure_refuses(system, table, change):
    db, _, service = system
    if change == "missing": db.tables[table] = []
    if change == "duplicate": db.tables[table].append(copy.deepcopy(db.tables[table][0]))
    if change == "foreign":
        db.tables[table][0]["company_id" if table == "entities" else "entity_id"] = COMPANY_B
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused): prepare(service)
    unchanged(db, before)


@pytest.mark.parametrize("field", list(ExecutionBindingsV2.model_fields))
def test_any_binding_change_and_mix_match_refused(system, field):
    db, _, service = system
    first, second = prepare(service), prepare(service)
    data = first.bindings.model_dump(mode="json")
    if field in {"request_id", "actor_id", "execution_id", "analysis_id", "company_id", "entity_id", "engagement_id"}:
        data[field] = str(uuid4())
    elif field.endswith("sha256"): data[field] = "0" * 64
    else: data[field] = "other-valid-version"
    forged = replace(first, bindings=type(first.bindings)(**data))
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused): consume(service, forged)
    with pytest.raises(AdmissionRefused): consume(service, replace(second, authorization=first.authorization))
    unchanged(db, before)


@pytest.mark.parametrize("kind", ["input", "filename", "source", "actor", "closed", "expired", "foreign-worker"])
def test_consumption_failures_never_return_input_or_persist(system, monkeypatch, kind):
    db, profile, service = system
    p = prepare(service)
    before = copy.deepcopy(db.tables)
    kwargs = {}
    if kind == "input": p = replace(p, input_json=p.input_json + " ")
    if kind == "filename": p = replace(p, filename="other.xlsx")
    if kind == "source": kwargs["raw"] = RAW + b"changed"
    if kind == "actor": kwargs["authorization"] = "Bearer foreign"
    if kind == "closed": service.close(p)
    if kind == "expired":
        import services.ownership_authority as ownership
        monkeypatch.setattr(ownership.time, "monotonic", lambda: p.authorization.expires_at)
    if kind == "foreign-worker": service = LocalProducerAdmissionPreparation(db, profile=profile)
    with pytest.raises(AdmissionRefused): consume(service, p, **kwargs)
    unchanged(db, before)


def test_concurrent_replay_one_winner(system):
    db, _, service = system
    p = prepare(service)
    before = copy.deepcopy(db.tables)
    def run():
        try: consume(service, p); return True
        except AdmissionRefused: return False
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: run(), range(2))) == [False, True]
    unchanged(db, before)


@pytest.mark.parametrize("table,key", [("analyses", "id"), ("governed_analysis_envelopes", "analysis_id"), ("governed_execution_receipts", "analysis_id")])
def test_collision_after_prepare_consumes_and_refuses_without_cleanup(system, table, key):
    db, _, service = system
    p = prepare(service)
    db.tables[table] = [{key: str(p.bindings.analysis_id)}]
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused): consume(service, p)
    with pytest.raises(AdmissionRefused): consume(service, p)
    unchanged(db, before)


def test_uuid_collision_cannot_issue_two_capabilities(system, monkeypatch):
    import services.governed_producer_admission as admission
    db, _, service = system
    value = uuid4()
    monkeypatch.setattr(admission, "uuid4", lambda: value)
    p = prepare(service)
    service.close(p)
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused): prepare(service)
    unchanged(db, before)


@pytest.mark.parametrize("change", ["profile", "entity", "engagement", "unavailable", "expires-during-read", "closed-during-read"])
def test_revocation_or_failure_between_prepare_and_consume_stays_closed(system, monkeypatch, change):
    db, _, service = system
    p = prepare(service)
    if change == "profile": db.tables["profiles"][0]["company_id"] = COMPANY_B
    if change == "entity": db.tables["entities"][0]["company_id"] = COMPANY_B
    if change == "engagement": db.tables["engagements"][0]["entity_id"] = ENTITY_B
    repository = service._authority._repository
    original = repository.resolve_prospective
    if change == "unavailable":
        def unavailable(scope): raise ValueError("PRIVATE_DATABASE_DIAGNOSTIC")
        monkeypatch.setattr(repository, "resolve_prospective", unavailable)
    if change in {"expires-during-read", "closed-during-read"}:
        def changed(scope):
            result = original(scope)
            if change == "closed-during-read": service.close(p)
            else:
                import services.ownership_authority as ownership
                monkeypatch.setattr(ownership.time, "monotonic", lambda: p.authorization.expires_at)
            return result
        monkeypatch.setattr(repository, "resolve_prospective", changed)
    before = copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused) as error: consume(service, p)
    assert str(error.value) == "COMPOSITION_CONSUMPTION_REFUSED"
    unchanged(db, before)
