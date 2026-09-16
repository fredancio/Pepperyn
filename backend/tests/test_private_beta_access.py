"""Local HTTP admission proof, NOT live Auth/RLS or production evidence."""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import main
from services.private_beta_access import BetaConfigurationRefused, PrivateBetaAccessMiddleware, beta_users

A = "10000000-0000-0000-0000-000000000001"
B = "10000000-0000-0000-0000-000000000002"
C = "10000000-0000-0000-0000-000000000003"


@pytest.fixture(autouse=True)
def closed_config(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PEPPERYN_PRIVATE_BETA", "1")
    monkeypatch.setenv("PEPPERYN_BETA_USER_IDS", f"{A},{B}")


@pytest.mark.parametrize("ids", ["", A, f"{A},{A}", f"{A},{B},{C}", f"{A},invalid"])
def test_configuration_requires_exactly_two_distinct_ids(monkeypatch, ids):
    monkeypatch.setenv("PEPPERYN_BETA_USER_IDS", ids)
    with pytest.raises(BetaConfigurationRefused):
        beta_users()


def test_production_cannot_disable_admission(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("PEPPERYN_PRIVATE_BETA", "0")
    monkeypatch.delenv("PEPPERYN_BETA_USER_IDS")
    with pytest.raises(BetaConfigurationRefused):
        beta_users()
    async def startup():
        with pytest.raises(BetaConfigurationRefused):
            async with main.lifespan(main.app):
                pytest.fail("Invalid production configuration reached startup")
    asyncio.run(startup())


def test_development_without_beta_preserves_existing_route_auth(monkeypatch):
    monkeypatch.setenv("PEPPERYN_PRIVATE_BETA", "0")
    monkeypatch.delenv("PEPPERYN_BETA_USER_IDS")
    assert beta_users() is None


def test_allowed_user_does_not_bypass_endpoint_authorization(monkeypatch):
    from fastapi import HTTPException
    service = MagicMock()
    service.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id=A))
    monkeypatch.setattr(main, "get_supabase_service", lambda: service)
    app = FastAPI()
    app.add_middleware(PrivateBetaAccessMiddleware)
    @app.get("/protected")
    def protected():
        raise HTTPException(status_code=403, detail="ownership refused")
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local") as client:
            response = await client.get("/protected", headers={"Authorization": "Bearer synthetic"})
            assert response.status_code == 403 and response.json()["detail"] == "ownership refused"
    asyncio.run(exercise())


@pytest.mark.parametrize("identity,status", [(A, 200), (B, 200), (C, 403), (None, 401)])
def test_only_verified_allowed_identity_reaches_endpoint(monkeypatch, identity, status):
    service = MagicMock()
    service.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id=identity))
    monkeypatch.setattr(main, "get_supabase_service", lambda: service)
    app = FastAPI()
    app.add_middleware(PrivateBetaAccessMiddleware)
    calls = []

    @app.get("/new-route")
    def endpoint():
        calls.append(True)
        return {"ok": True}

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local") as client:
            response = await client.get("/new-route", headers={"Authorization": "Bearer synthetic-token"})
            assert response.status_code == status
            assert "synthetic-token" not in response.text
    asyncio.run(exercise())
    assert bool(calls) == (status == 200)
    service.auth.get_user.assert_called_once_with("synthetic-token")


def test_actual_app_blocks_guest_and_unlisted_requests_before_endpoint(monkeypatch):
    service = MagicMock()
    service.auth.get_user.side_effect = RuntimeError("sensitive-token-detail")
    monkeypatch.setattr(main, "get_supabase_service", lambda: service)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://local") as client:
            assert (await client.get("/health")).status_code == 200
            assert (await client.get("/api/entities")).status_code == 401
            assert (await client.post("/api/auth/pin", json={"pin": "0000"})).status_code == 403
            assert (await client.post("/api/billing/checkout")).status_code == 403
            response = await client.get("/api/entities", headers={"Authorization": "Bearer synthetic"})
            assert response.status_code == 401 and "sensitive" not in response.text
    asyncio.run(exercise())
    service.from_.assert_not_called()
    service.rpc.assert_not_called()


def test_duplicate_authorization_headers_and_revoked_allowlist_fail_closed(monkeypatch):
    service = MagicMock()
    service.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id=A))
    monkeypatch.setattr(main, "get_supabase_service", lambda: service)
    app = FastAPI()
    app.add_middleware(PrivateBetaAccessMiddleware)
    @app.get("/read")
    def read():
        return {"ok": True}
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local") as client:
            assert (await client.get("/read", headers=[("Authorization", "Bearer a"), ("Authorization", "Bearer b")])).status_code == 401
            service.auth.get_user.assert_not_called()
            assert (await client.get("/read", headers={"Authorization": "Bearer a"})).status_code == 200
            monkeypatch.setenv("PEPPERYN_BETA_USER_IDS", f"{B},{C}")
            assert (await client.get("/read", headers={"Authorization": "Bearer a"})).status_code == 403
    asyncio.run(exercise())


def test_invalid_runtime_config_refuses_and_preflight_does_not_run_endpoint(monkeypatch):
    app = FastAPI()
    app.add_middleware(PrivateBetaAccessMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=["http://local"], allow_methods=["GET"])
    monkeypatch.delenv("PEPPERYN_BETA_USER_IDS")
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local") as client:
            assert (await client.get("/health")).status_code == 503
            response = await client.options("/api/entities", headers={"Origin": "http://local", "Access-Control-Request-Method": "GET"})
            assert response.status_code == 200
    asyncio.run(exercise())
