"""Synthetic service/HTTP falsification. Mock DB is not deployed PostgreSQL/RLS proof."""
import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from sandbox import source_dossiers as service
from sandbox import v1_router as routes

COMPANY = "20000000-0000-0000-0000-000000000001"
ENTITY = "30000000-0000-0000-0000-000000000001"
ENGAGEMENT = "40000000-0000-0000-0000-000000000001"
FILE = "pepperyn_v1_heterogeneous_conflict.xlsx"
RAW = (Path(__file__).parent / "golden/fixtures" / FILE).read_bytes()


class UniqueViolation(Exception):
    code = "23505"


class Query:
    def __init__(self, db, table):
        self.db, self.table, self.filters, self.bound, self.record = db, table, {}, 1000, None
    def select(self, _): return self
    def eq(self, key, value): self.filters[key] = value; return self
    def limit(self, value): self.bound = value; return self
    def insert(self, value): self.record = copy.deepcopy(value); return self
    def execute(self):
        if self.db.fail: raise RuntimeError("private database detail")
        rows = self.db.tables.get(self.table, [])
        if self.record is not None:
            assert self.table == service.TABLE
            if any(r["id"] == self.record["id"] for r in rows): raise UniqueViolation()
            self.db.tables.setdefault(self.table, []).append(self.record)
            self.db.writes += 1
            result = [self.record]
        else:
            result = [r for r in rows if all(r.get(k) == v for k, v in self.filters.items())][:self.bound]
            if self.db.ignore_scope and self.table == service.TABLE: result = rows
        return type("Response", (), {"data": copy.deepcopy(result)})()


class Database:
    def __init__(self):
        self.tables = {"entities": [{"id": ENTITY, "company_id": COMPANY}],
                       "engagements": [{"id": ENGAGEMENT, "entity_id": ENTITY}]}
        self.writes = 0; self.fail = False; self.ignore_scope = False
    def from_(self, table): return Query(self, table)


def capture(db, **overrides):
    args = dict(company_id=COMPANY, entity_id=ENTITY, raw=RAW, filename=FILE)
    args.update(overrides)
    return service.capture_dossier(db, **args)


def test_source_attention_retains_provenance_without_decision_or_write():
    db = Database(); db.tables['entities'][0]['name'] = 'Synthetic A'
    saved = capture(db)
    before = copy.deepcopy(db.tables); writes = db.writes
    assert service.list_source_attention(db, company_id=COMPANY) == [
        {'entity_id': ENTITY, 'entity_name': 'Synthetic A', 'dossiers': [saved]}]
    assert db.tables == before and db.writes == writes
    assert service.list_source_attention(db, company_id='20000000-0000-0000-0000-000000000099') == []


def test_source_attention_separates_clients_and_does_not_invent_global_urgency():
    db = Database(); db.tables['entities'][0]['name'] = 'Synthetic A'
    first = capture(db)
    second_entity = '30000000-0000-0000-0000-000000000002'
    db.tables['entities'].append({'id': second_entity, 'company_id': COMPANY, 'name': 'Synthetic B'})
    db.tables['engagements'].append({'id': '40000000-0000-0000-0000-000000000002', 'entity_id': second_entity})
    second = capture(db, entity_id=second_entity)
    groups = service.list_source_attention(db, company_id=COMPANY)
    assert [g['entity_id'] for g in groups] == [ENTITY, second_entity]
    assert groups[0]['dossiers'] == [first] and groups[1]['dossiers'] == [second]
    assert all(set(g) == {'entity_id', 'entity_name', 'dossiers'} for g in groups)
    assert db.writes == 2


@pytest.mark.parametrize('failure', ['corrupt', 'foreign', 'duplicate', 'bound', 'unavailable', 'ownership'])
def test_source_attention_refuses_incomplete_or_foreign_evidence(failure):
    db = Database(); db.tables['entities'][0]['name'] = 'Synthetic A'; capture(db)
    if failure == 'corrupt': db.tables[service.TABLE][0]['payload_sha256'] = '0' * 64
    if failure == 'foreign':
        db.tables[service.TABLE][0]['company_id'] = '20000000-0000-0000-0000-000000000099'
        db.ignore_scope = True
    if failure == 'duplicate': db.tables[service.TABLE] *= 2
    if failure == 'bound': db.tables[service.TABLE] *= 101
    if failure == 'unavailable': db.fail = True
    if failure == 'ownership': db.tables['engagements'] = []
    with pytest.raises(service.SourceDossierRefused, match='UNAVAILABLE'):
        service.list_source_attention(db, company_id=COMPANY)


def test_source_attention_http_is_read_only_and_feature_gated(monkeypatch):
    import main
    db = Database(); db.tables['entities'][0]['name'] = 'Synthetic A'; capture(db)
    monkeypatch.setenv('ENVIRONMENT', 'development')
    monkeypatch.setenv('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO', '1')
    monkeypatch.setenv('PEPPERYN_SYNTHETIC_V1_COMPANY_ID', COMPANY)
    async def auth(*_): return COMPANY, 'pro', 'admin'
    monkeypatch.setattr(routes.analyze_routes, '_resolve_auth', auth)
    monkeypatch.setattr(main, 'get_supabase_service', lambda: db)
    async def exercise():
        app = FastAPI(); app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.get('/api/v1/synthetic-source-attention')
            assert response.status_code == 200 and response.json()[0]['dossiers'][0]['status'] == 'CONTRADICTION'
            assert db.writes == 1
            db.fail = True
            response = await client.get('/api/v1/synthetic-source-attention')
            assert response.status_code == 503 and 'private' not in response.text
            monkeypatch.setenv('ENVIRONMENT', 'production')
            assert (await client.get('/api/v1/synthetic-source-attention')).status_code == 404
    asyncio.run(exercise())


def test_reload_and_retry_preserve_conflict_without_analysis_or_duplicate_write():
    db = Database(); saved = capture(db)
    assert capture(db) == saved and db.writes == 1
    reopened = Database(); reopened.tables = json.loads(json.dumps(db.tables))
    loaded = service.load_dossier(reopened, company_id=COMPANY, entity_id=ENTITY, dossier_id=saved["dossier_id"])
    assert loaded == saved
    assert loaded["status"] == "CONTRADICTION" and loaded["facts"] == []
    assert loaded["source_claims"] and loaded["discrepancies"]
    assert loaded["evidence_role"] == "SOURCE_INSPECTION_NOT_ANALYSIS"
    assert set(db.tables) == {"entities", "engagements", service.TABLE}
    assert reopened.writes == 0


@pytest.mark.parametrize("field", ["company_id", "entity_id"])
def test_foreign_capture_is_refused_without_write(field):
    db = Database()
    with pytest.raises(service.SourceDossierRefused, match="NOT_FOUND"):
        capture(db, **{field: "90000000-0000-0000-0000-000000000001"})
    assert db.writes == 0


@pytest.mark.parametrize("field,value", [("entity_id", "foreign"), ("payload_sha256", "A" * 64),
                                        ("schema_version", "future"), ("filename", "real.xlsx")])
def test_scope_and_tampering_are_rejected_even_if_db_returns_foreign_row(field, value):
    db = Database(); capture(db); db.ignore_scope = True
    db.tables[service.TABLE][0][field] = value
    with pytest.raises(service.SourceDossierRefused, match="INTEGRITY_FAILED"):
        service.list_dossiers(db, company_id=COMPANY, entity_id=ENTITY)


def test_missing_capture_is_empty_but_read_failure_never_becomes_empty():
    db = Database()
    assert service.list_dossiers(db, company_id=COMPANY, entity_id=ENTITY) == []
    db.fail = True
    with pytest.raises(service.SourceDossierRefused, match="UNAVAILABLE"):
        service.list_dossiers(db, company_id=COMPANY, entity_id=ENTITY)


def test_unregistered_source_does_not_reach_write():
    db = Database()
    with pytest.raises(Exception, match="UNREGISTERED"):
        capture(db, raw=b"not a registered synthetic workbook")
    assert db.writes == 0


def test_duplicate_engagement_is_not_chosen_arbitrarily():
    db = Database(); db.tables["engagements"] *= 2
    with pytest.raises(service.SourceDossierRefused, match="NOT_FOUND"):
        capture(db)
    assert db.writes == 0


def test_http_write_reload_list_and_scope_refusal(monkeypatch):
    import main
    db = Database()
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO", "1")
    monkeypatch.setenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", COMPANY)
    async def auth(*_): return COMPANY, "pro", "admin"
    monkeypatch.setattr(routes.analyze_routes, "_resolve_auth", auth)
    monkeypatch.setattr(main, "get_supabase_service", lambda: db)
    async def exercise():
        app = FastAPI(); app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            saved = await client.post("/api/v1/synthetic-source-dossiers", files={"file": (FILE, RAW)}, data={"entity_id": ENTITY})
            assert saved.status_code == 200
            response = await client.get("/api/v1/synthetic-source-dossiers/" + saved.json()["dossier_id"], params={"entity_id": ENTITY})
            assert response.json() == saved.json()
            listed = await client.get("/api/v1/synthetic-source-dossiers", params={"entity_id": ENTITY})
            assert len(listed.json()) == 1
            foreign = await client.get("/api/v1/synthetic-source-dossiers", params={"entity_id": "90000000-0000-0000-0000-000000000001"})
            assert foreign.status_code == 404
            db.fail = True
            failed = await client.get("/api/v1/synthetic-source-dossiers", params={"entity_id": ENTITY})
            assert failed.status_code == 503 and "private" not in failed.text
            monkeypatch.setenv("ENVIRONMENT", "production")
            closed = await client.get("/api/v1/synthetic-source-dossiers", params={"entity_id": ENTITY})
            assert closed.status_code == 404
    asyncio.run(exercise())
    assert db.writes == 1


def test_migration_is_synthetic_scoped_immutable_and_backend_only():
    sql = (Path(__file__).parents[1] / "migrations/v35_synthetic_source_dossiers.sql").read_text()
    for clause in ("ENABLE ROW LEVEL SECURITY", "REVOKE ALL", "GRANT SELECT, INSERT", "BEFORE UPDATE OR DELETE",
                   "FOREIGN KEY (entity_id, company_id)", "FOREIGN KEY (engagement_id, entity_id)"):
        assert clause in sql
    for sha, filename in service.REGISTERED_WORKBOOKS.items():
        assert sha in sql and filename in sql


def test_same_source_is_not_correlatable_by_dossier_id_across_entities():
    db = Database(); first = capture(db)
    second_entity = "30000000-0000-0000-0000-000000000002"
    db.tables["entities"].append({"id": second_entity, "company_id": COMPANY})
    db.tables["engagements"].append({"id": "40000000-0000-0000-0000-000000000002", "entity_id": second_entity})
    second = capture(db, entity_id=second_entity)
    assert first["dossier_id"] != second["dossier_id"]
    with pytest.raises(service.SourceDossierRefused, match="NOT_FOUND"):
        service.load_dossier(db, company_id=COMPANY, entity_id=second_entity, dossier_id=first["dossier_id"])
    assert len(service.list_dossiers(db, company_id=COMPANY, entity_id=second_entity)) == 1


def test_duplicate_id_with_altered_persisted_content_cannot_acknowledge_retry():
    db = Database(); capture(db)
    db.tables[service.TABLE][0]["understanding"]["facts"][0]["value"] += 1
    with pytest.raises(service.SourceDossierRefused, match="INTEGRITY_FAILED"):
        capture(db)
    assert db.writes == 1


@pytest.mark.parametrize("mode", ["no_auth", "foreign_company", "feature_off"])
def test_http_closed_before_database_access(monkeypatch, mode):
    import main
    from fastapi import HTTPException
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO", "0" if mode == "feature_off" else "1")
    monkeypatch.setenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", COMPANY)
    async def auth(*_):
        if mode == "no_auth": raise HTTPException(401)
        return "90000000-0000-0000-0000-000000000001", "pro", "admin"
    monkeypatch.setattr(routes.analyze_routes, "_resolve_auth", auth)
    monkeypatch.setattr(main, "get_supabase_service", lambda: pytest.fail("Closed access reached DB"))
    async def exercise():
        app = FastAPI(); app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/synthetic-source-dossiers", params={"entity_id": ENTITY})
    assert asyncio.run(exercise()).status_code == (401 if mode == "no_auth" else 404)
