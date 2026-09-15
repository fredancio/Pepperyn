"""Registered upload -> real envelope persistence/validation -> scoped HTTP reads.

Only database I/O and authentication are test doubles. No live RLS claim.
"""
import asyncio
import copy
from pathlib import Path

import httpx
from fastapi import FastAPI

import main
import sandbox.v1_router as routes
from test_v1_synthetic_routes import _Db, _enable, COMPANY_A, COMPANY_B


def test_three_clients_reload_without_cross_client_history_or_new_writes(monkeypatch):
    db = _Db()
    _enable(monkeypatch, db)
    entities = [f"30000000-0000-0000-0000-{i:012d}" for i in (1, 2, 3)]
    db.tables["entities"] = [{"id": eid, "company_id": COMPANY_A,
                              "name": f"Synthetic {i}", "is_primary": i == 0}
                             for i, eid in enumerate(entities)]
    db.tables["engagements"] = [{"id": f"40000000-0000-0000-0000-{i:012d}", "entity_id": eid}
                                for i, eid in enumerate(entities, 1)]

    async def exercise():
        app = FastAPI()
        app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": "Bearer synthetic"}
            name = "pepperyn_v1_heterogeneous_english.xlsx"
            raw = (Path(__file__).parent / "golden" / "fixtures" / name).read_bytes()
            created = []
            for eid in entities:
                response = await client.post("/api/v1/synthetic-workbook-analysis", headers=headers,
                                             files={"file": (name, raw)}, data={"entity_id": eid})
                assert response.status_code == 200
                created.append(response.json())
            assert len({item["analyse_id"] for item in created}) == 3
            # Reconstruct database adapter, leaving no service-local state.
            reconstructed = _Db()
            reconstructed.tables = copy.deepcopy(db.tables)
            monkeypatch.setattr(main, "get_supabase_service", lambda: reconstructed)
            before = copy.deepcopy(reconstructed.tables)
            for eid, item in zip(entities, created):
                aid = item["analyse_id"]
                row = next(r for r in before["analyses"] if r["id"] == aid)
                assert row["entity_id"] == eid
                loaded = await client.get(f"/api/v1/governed-analyses/{aid}", headers=headers)
                assert loaded.status_code == 200
                assert loaded.json()["result"] == item["result"]
                comparison = await client.get(f"/api/v1/governed-analyses/{aid}/temporal-comparison", headers=headers)
                assert comparison.status_code == 200
                assert comparison.json()["status"] == "UNKNOWN"
                assert comparison.json()["previous_analysis_id"] is None
                assert comparison.json()["changes"] == []
            assert reconstructed.tables == before
            # Stored scope substitution without recomputing binding is rejected.
            reconstructed.tables["governed_analysis_envelopes"][0]["binding_sha256"] = "0" * 64
            aid = created[0]["analyse_id"]
            assert (await client.get(f"/api/v1/governed-analyses/{aid}", headers=headers)).status_code == 404
            assert (await client.get(f"/api/v1/governed-analyses/{aid}/temporal-comparison", headers=headers)).status_code == 503
            _enable(monkeypatch, reconstructed, company=COMPANY_B)
            assert (await client.get(f"/api/v1/governed-analyses/{aid}", headers=headers)).status_code == 404

    asyncio.run(exercise())
