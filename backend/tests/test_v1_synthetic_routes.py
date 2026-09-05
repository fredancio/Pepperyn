from __future__ import annotations

import asyncio
import copy

from fastapi import FastAPI, HTTPException
import pytest

import main
import routers.analyze as analyze
import sandbox.v1_router as v1_routes
from starlette.requests import Request

COMPANY_A = "20000000-0000-0000-0000-000000000001"
COMPANY_B = "20000000-0000-0000-0000-000000000002"
ENTITY_A = "30000000-0000-0000-0000-000000000001"
ENGAGEMENT_A = "40000000-0000-0000-0000-000000000001"


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, db, table): self.db, self.table = db, table; self.rows = list(db.tables.get(table, ()))
    def select(self, _fields): return self
    def eq(self, field, value): self.rows = [row for row in self.rows if row.get(field) == value]; return self
    def limit(self, count): self.rows = self.rows[:count]; return self
    def execute(self): return _Response(copy.deepcopy(self.rows))


class _Rpc:
    def __init__(self, db, params): self.db, self.params = db, copy.deepcopy(params)
    def execute(self):
        analysis_row = self.params["p_analysis"]
        envelope_row = self.params["p_envelope"]
        assert any(row["id"] == envelope_row["engagement_id"] and row["entity_id"] == analysis_row["entity_id"]
                   for row in self.db.tables["engagements"])
        self.db.tables.setdefault("analyses", []).append(analysis_row)
        self.db.tables.setdefault("governed_analysis_envelopes", []).append(envelope_row)
        return _Response(analysis_row["id"])


class _Db:
    def __init__(self):
        self.tables = {
            "entities": [{"id": ENTITY_A, "company_id": COMPANY_A, "is_primary": True,
                          "name": "Synthetic", "relation_type": None}],
            "engagements": [{"id": ENGAGEMENT_A, "entity_id": ENTITY_A}],
        }
    def from_(self, table): return _Query(self, table)
    def rpc(self, name, params): assert name == "persist_governed_analysis_v1"; return _Rpc(self, params)


def _enable(monkeypatch, db, company=COMPANY_A):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO", "1")
    monkeypatch.setenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", COMPANY_A)
    async def auth(authorization, _x_auth_type):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token requis")
        return company, "pro", "admin"
    monkeypatch.setattr(analyze, "_resolve_auth", auth)
    monkeypatch.setattr(main, "get_supabase_service", lambda: db)


def _empty_request() -> Request:
    async def receive(): return {"type": "http.request", "body": b"", "more_body": False}
    return Request({"type": "http", "method": "POST", "path": "/api/v1/synthetic-demo",
                    "headers": []}, receive)


def test_authenticated_no_body_demo_persists_and_reloads_after_cache_free_reconstruction(monkeypatch):
    db = _Db(); _enable(monkeypatch, db)
    created = asyncio.run(v1_routes.run_v1_synthetic_demo(
        request=_empty_request(), authorization="Bearer test", x_auth_type=None,
    ))
    assert created.result.verification_tag == "V1_GOVERNED_SINGLE_CALL"
    assert len(db.tables["governed_analysis_envelopes"]) == 1

    reconstructed = _Db()
    reconstructed.tables = copy.deepcopy(db.tables)
    monkeypatch.setattr(main, "get_supabase_service", lambda: reconstructed)
    loaded = asyncio.run(v1_routes.get_v1_governed_analysis(
        created.analyse_id, authorization="Bearer test", x_auth_type=None,
    ))
    assert loaded.result == created.result


def test_second_company_cannot_reload_first_company_analysis(monkeypatch):
    db = _Db(); _enable(monkeypatch, db)
    created = asyncio.run(v1_routes.run_v1_synthetic_demo(
        request=_empty_request(), authorization="Bearer a", x_auth_type=None,
    ))
    _enable(monkeypatch, db, company=COMPANY_B)
    with pytest.raises(HTTPException) as error:
        asyncio.run(v1_routes.get_v1_governed_analysis(
            created.analyse_id, authorization="Bearer b", x_auth_type=None,
        ))
    assert error.value.status_code == 404


def test_main_application_does_not_mount_demo_without_startup_flag():
    assert not any(route.path == "/api/v1/synthetic-demo" for route in main.app.routes)


def test_non_designated_company_cannot_create_synthetic_history(monkeypatch):
    db = _Db(); _enable(monkeypatch, db, company=COMPANY_B)
    with pytest.raises(HTTPException) as error:
        asyncio.run(v1_routes.run_v1_synthetic_demo(
            request=_empty_request(), authorization="Bearer b", x_auth_type=None,
        ))
    assert error.value.status_code == 404
    assert not db.tables.get("analyses")


def test_http_contract_accepts_empty_body_rejects_payload_and_serializes(monkeypatch):
    import httpx

    db = _Db(); _enable(monkeypatch, db)
    async def exercise():
        app = FastAPI()
        app.include_router(v1_routes.router)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            missing_auth = await client.post("/api/v1/synthetic-demo")
            with_body = await client.post(
                "/api/v1/synthetic-demo", headers={"Authorization": "Bearer test"}, json={"fixture": "other"},
            )
            created = await client.post(
                "/api/v1/synthetic-demo", headers={"Authorization": "Bearer test"},
            )
            loaded = await client.get(
                f"/api/v1/governed-analyses/{created.json()['analyse_id']}",
                headers={"Authorization": "Bearer test"},
            )
            return missing_auth, with_body, created, loaded
    missing_auth, with_body, created, loaded = asyncio.run(exercise())
    assert missing_auth.status_code == 401
    assert with_body.status_code == 400
    assert created.status_code == loaded.status_code == 200
    assert created.json()["result"]["id"] == created.json()["analyse_id"]
    assert loaded.json()["result"] == created.json()["result"]
