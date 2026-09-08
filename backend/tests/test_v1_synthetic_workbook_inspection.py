from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
import httpx

import routers.analyze as analyze
import sandbox.v1_router as v1_routes
import main


COMPANY = "20000000-0000-0000-0000-000000000001"
FIXTURES = Path(__file__).parent / "golden" / "fixtures"


def _enable(monkeypatch, company: str = COMPANY) -> None:
    monkeypatch.setenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", COMPANY)

    async def auth(authorization, _x_auth_type):
        if not authorization:
            raise HTTPException(status_code=401, detail="Token requis")
        return company, "pro", "admin"

    monkeypatch.setattr(analyze, "_resolve_auth", auth)


async def _post(client, filename: str, raw: bytes):
    return await client.post(
        "/api/v1/synthetic-workbook-inspection",
        headers={"Authorization": "Bearer test"},
        files={"file": (filename, raw)},
    )


def test_route_accepts_registered_workbook_and_rejects_changed_identity(monkeypatch):
    _enable(monkeypatch)
    filename = "pepperyn_v1_heterogeneous_english.xlsx"
    raw = (FIXTURES / filename).read_bytes()

    async def exercise():
        app = FastAPI(); app.include_router(v1_routes.router)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return (
                await _post(client, filename, raw),
                await _post(client, "renamed.xlsx", raw),
                await _post(client, "unknown.xlsx", b"not-a-workbook"),
            )

    accepted, renamed, unknown = asyncio.run(exercise())
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "UNDERSTOOD"
    assert accepted.json()["current_period"] == "2025"
    assert len(accepted.json()["facts"]) == 10
    assert accepted.json()["provider_dispatch"] == "CLOSED"
    assert renamed.status_code == unknown.status_code == 400


def test_route_preserves_all_three_fail_closed_ambiguities(monkeypatch):
    _enable(monkeypatch)
    filenames = [
        "pepperyn_v1_heterogeneous_ambiguous_period.xlsx",
        "pepperyn_v1_heterogeneous_ambiguous_number.xlsx",
        "pepperyn_v1_heterogeneous_conflict.xlsx",
    ]

    async def exercise():
        app = FastAPI(); app.include_router(v1_routes.router)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return [await _post(client, name, (FIXTURES / name).read_bytes()) for name in filenames]

    responses = asyncio.run(exercise())
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json()["status"] == "AMBIGUOUS" for response in responses)
    assert all(response.json()["facts"] == [] for response in responses)
    assert all(response.json()["unknowns"] for response in responses)
    assert all(response.json()["provider_dispatch"] == "CLOSED" for response in responses)


def test_route_hides_from_non_designated_company(monkeypatch):
    _enable(monkeypatch, company="20000000-0000-0000-0000-000000000002")
    filename = "pepperyn_v1_heterogeneous_english.xlsx"

    async def exercise():
        app = FastAPI(); app.include_router(v1_routes.router)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await _post(client, filename, (FIXTURES / filename).read_bytes())

    assert asyncio.run(exercise()).status_code == 404


def test_mock_analysis_route_validates_persists_and_returns_governed_result(monkeypatch):
    _enable(monkeypatch)
    filename = "pepperyn_v1_heterogeneous_english.xlsx"
    raw = (FIXTURES / filename).read_bytes()
    persisted = {}
    database = object()

    monkeypatch.setattr(main, "get_supabase_service", lambda: database)
    monkeypatch.setattr(
        v1_routes, "_resolve_primary_scope",
        lambda supabase, company_id: ("Synthetic", "entity-id", "engagement-id"),
    )

    def capture(supabase, *, analysis_row, engagement_id, envelope):
        persisted.update(
            supabase=supabase, analysis_row=analysis_row,
            engagement_id=engagement_id, envelope=envelope,
        )

    monkeypatch.setattr(v1_routes, "save_governed_analysis", capture)
    response = asyncio.run(v1_routes.analyze_v1_synthetic_workbook(
        file=UploadFile(file=BytesIO(raw), filename=filename),
        authorization="Bearer synthetic", x_auth_type="admin",
    ))

    assert response.success is True and response.analyse_id
    assert response.tokens_used == 0 and response.cout_estime == 0
    assert response.result.verification_tag == "V1_GOVERNED_SINGLE_CALL"
    assert persisted["supabase"] is database
    assert persisted["engagement_id"] == "engagement-id"
    assert persisted["analysis_row"]["fichier_nom"] == filename
    assert persisted["analysis_row"]["source_data_hash"] == (
        "fe7fe4cc8fc6ce649f1ff61d18fdd3d45e2097031fd05aa8c9e2b7a47fad3b93"
    )
    assert persisted["analysis_row"]["tokens_input"] == 0
    assert persisted["analysis_row"]["cout_estime_euros"] == 0
    persisted["envelope"].validate_lineage()
