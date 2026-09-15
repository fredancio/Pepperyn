"""Unavailable evidence must never yield a successful empty/partial portfolio."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

import main
import routers.arcs as routes
from services.arc_service import ArcService


@pytest.mark.parametrize("failure", [None, "legacy", "governed"])
def test_http_read_availability_boundary(monkeypatch, failure):
    async def auth(*args):
        return "tenant-a", "pro", "admin"

    def legacy(*, company_id, strict_reads):
        assert company_id == "tenant-a" and strict_reads is True
        if failure == "legacy":
            raise RuntimeError("sensitive internal diagnostic")
        return []

    def governed(db, company_id):
        assert company_id == "tenant-a"
        if failure == "governed":
            raise RuntimeError("sensitive internal diagnostic")
        return []

    monkeypatch.setattr(routes, "_resolve_auth", auth)
    monkeypatch.setattr(routes.arc_service, "build_portfolio_briefing", legacy)
    monkeypatch.setattr(routes, "build_governed_portfolio_cards", governed)
    monkeypatch.setattr(main, "get_supabase_service", object)

    async def exercise():
        app = FastAPI()
        app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/portfolio")

    response = asyncio.run(exercise())
    if failure:
        assert response.status_code == 503
        assert "cards" not in response.json()
        assert "sensitive" not in response.text
    else:
        assert response.status_code == 200
        assert response.json() == {"cards": []}


def test_legacy_missing_database_is_unknown_in_strict_mode(monkeypatch):
    service = ArcService()
    monkeypatch.setattr(service, "_get_supabase", lambda: None)
    with pytest.raises(RuntimeError, match="PORTFOLIO_SOURCE_UNAVAILABLE"):
        service.build_portfolio_briefing("tenant-a", strict_reads=True)
    # No global behavior change to other legacy briefing consumers.
    assert service.build_review_briefing("tenant-a") == []


def test_legacy_query_failure_is_not_empty(monkeypatch):
    class BrokenQuery:
        def from_(self, *_): return self
        def select(self, *_): return self
        def eq(self, *_): return self
        def neq(self, *_): return self
        def order(self, *_, **kwargs): return self
        def execute(self): raise RuntimeError("internal database details")

    service = ArcService()
    monkeypatch.setattr(service, "_get_supabase", BrokenQuery)
    with pytest.raises(RuntimeError, match="PORTFOLIO_SOURCE_UNAVAILABLE"):
        service.build_portfolio_briefing("tenant-a", strict_reads=True)
