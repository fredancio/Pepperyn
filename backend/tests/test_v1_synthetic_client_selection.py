"""HTTP client selection proof; synthetic fixtures, in-memory database only."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

import main
import sandbox.v1_router as routes
from test_v1_synthetic_workbook_inspection import COMPANY, FIXTURES, _enable


class Query:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, *_):
        return self

    def eq(self, key, value):
        self.rows = [row for row in self.rows if row.get(key) == value]
        return self

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    def execute(self):
        return type("Result", (), {"data": self.rows})()


class Database:
    def __init__(self):
        self.tables = {
            "entities": [
                {"id": f"client-{i}", "company_id": COMPANY, "name": f"Synthetic {i}",
                 "is_primary": i == 0, "relation_type": "client"} for i in range(3)
            ] + [{"id": "foreign", "company_id": "other-tenant"}],
            "engagements": [
                {"id": f"engagement-{i}", "entity_id": f"client-{i}"} for i in range(3)
            ],
        }

    def from_(self, table):
        return Query(self.tables[table])


def post(entity):
    async def exercise():
        app = FastAPI()
        app.include_router(routes.router)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            name = "pepperyn_v1_heterogeneous_english.xlsx"
            return await client.post(
                "/api/v1/synthetic-workbook-analysis",
                headers={"Authorization": "Bearer synthetic"},
                files={"file": (name, (FIXTURES / name).read_bytes())},
                data={} if entity is None else {"entity_id": entity},
            )
    return asyncio.run(exercise())


def test_three_selected_clients_reach_persistence_in_exact_scope(monkeypatch):
    _enable(monkeypatch)
    database = Database()
    monkeypatch.setattr(main, "get_supabase_service", lambda: database)
    captured = []

    def save(_database, **record):
        record["envelope"].validate_lineage()
        captured.append(record)

    monkeypatch.setattr(routes, "save_governed_analysis", save)
    responses = [post(f"client-{i}") for i in range(3)]
    assert [r.status_code for r in responses] == [200, 200, 200]
    assert len({r.json()["analyse_id"] for r in responses}) == 3
    assert [(r["analysis_row"]["company_id"], r["analysis_row"]["entity_id"],
             r["engagement_id"]) for r in captured] == [
        (COMPANY, f"client-{i}", f"engagement-{i}") for i in range(3)
    ]
    assert all(r.json()["tokens_used"] == 0 for r in responses)


@pytest.mark.parametrize("failure", ["foreign", "missing", "no_engagement", "duplicate_engagement"])
def test_invalid_explicit_scope_refused_before_analysis_or_write(monkeypatch, failure):
    _enable(monkeypatch)
    database = Database()
    entity = failure if failure in {"foreign", "missing"} else "client-1"
    if failure == "no_engagement":
        database.tables["engagements"] = []
    if failure == "duplicate_engagement":
        database.tables["engagements"].append({"id": "duplicate", "entity_id": entity})
    monkeypatch.setattr(main, "get_supabase_service", lambda: database)

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid scope reached analysis, persistence or primary fallback")

    monkeypatch.setattr(routes, "run_registered_mock_analysis", forbidden)
    monkeypatch.setattr(routes, "save_governed_analysis", forbidden)
    monkeypatch.setattr(routes, "_resolve_primary_scope", forbidden)
    assert post(entity).status_code == 404


def test_omitted_client_preserves_primary_compatibility(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(main, "get_supabase_service", Database)
    captured = []
    monkeypatch.setattr(routes, "save_governed_analysis", lambda db, **r: captured.append(r))
    assert post(None).status_code == 200
    assert captured[0]["analysis_row"]["entity_id"] == "client-0"


def test_other_tenant_refused_before_database_access(monkeypatch):
    _enable(monkeypatch, company="other-tenant")
    monkeypatch.setattr(main, "get_supabase_service", lambda: pytest.fail("Tenant gate bypassed"))
    assert post("client-0").status_code == 404
