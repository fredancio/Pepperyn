"""Synthetic parsed facts -> mock response -> real persistence -> scoped HTTP.

No workbook admission, live database/RLS, provider transport or financial
professional certification is exercised by this test.
"""
import asyncio
import copy

import httpx
from fastapi import FastAPI

import main
import sandbox.v1_router as routes
from sandbox.v1_golden_case import _deterministic_provider_double
from services.governed_analysis_persistence import save_governed_analysis
from services.v1_analysis_contract import build_openai_request, parse_openai_response, to_analysis_result
from test_v1_synthetic_routes import _Db, _enable, COMPANY_A


def synthetic_envelope(period, ebitda):
    payload = {
        "temporal_context": {"columns_by_role": {"CURRENT_ACTUAL": [period]}},
        "sheets": [{"sheet_name": "Synthetic P&L", "columns": ["Label", period],
                    "full_table": [{"Label": "EBITDA", period: ebitda},
                                   {"Label": "Working capital", period: 50}]}],
    }
    _, nonce, understanding = build_openai_request(payload, model="mock-local")
    response = _deterministic_provider_double(
        understanding.source_representation_sha256, nonce,
        {f.metric: f for f in understanding.facts},
    )
    return to_analysis_result(parse_openai_response(response, understanding, nonce), understanding)


def test_three_clients_later_periods_keep_exact_sources_and_refuse_gap(monkeypatch):
    db = _Db()
    _enable(monkeypatch, db)
    expected = []
    for client_number, (prior_period, old, new) in enumerate([
        ("2025", -100, -50), ("2025", -200, -270), ("2024", -300, -310),
    ], 1):
        eid = f"30000000-0000-0000-0000-{client_number:012d}"
        engagement = f"40000000-0000-0000-0000-{client_number:012d}"
        if client_number > 1:
            db.tables["entities"].append({"id": eid, "company_id": COMPANY_A})
            db.tables["engagements"].append({"id": engagement, "entity_id": eid})
        saved = []
        # Insert current before prior: ingestion order must not become business time.
        for index, period, value in [(2, "2026", new), (1, prior_period, old)]:
            aid = f"10000000-0000-0000-0000-{client_number * 10 + index:012d}"
            envelope = synthetic_envelope(period, value)
            save_governed_analysis(db, analysis_row={
                "id": aid, "company_id": COMPANY_A, "entity_id": eid,
                "analyse_json": envelope.analysis_result.model_dump(mode="json"),
                "status": "completed", "fichier_nom": "synthetic-parsed-facts",
                "mode": "complete", "type_document": "COMPTE_RESULTAT",
            }, engagement_id=engagement, envelope=envelope)
            saved.append((aid, envelope))
        expected.append((saved, new - old, client_number == 3))

    reconstructed = _Db()
    reconstructed.tables = copy.deepcopy(db.tables)
    monkeypatch.setattr(main, "get_supabase_service", lambda: reconstructed)
    before = copy.deepcopy(reconstructed.tables)

    async def exercise():
        app = FastAPI()
        app.include_router(routes.router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for ((current_id, current), (prior_id, prior)), delta, gap in expected:
                response = await client.get(f"/api/v1/governed-analyses/{current_id}/temporal-comparison",
                                            headers={"Authorization": "Bearer synthetic"})
                assert response.status_code == 200
                result = response.json()
                assert result["current_analysis_id"] == current_id
                assert result["previous_analysis_id"] == prior_id
                assert result["financial_comparability"] == "NOT_ESTABLISHED"
                assert result["causal_interpretation"] is None
                if gap:
                    assert result["status"] == "UNKNOWN" and result["changes"] == []
                else:
                    assert result["status"] == "COMPARABLE"
                    change = next(c for c in result["changes"] if c["metric"] == "EBITDA")
                    assert change["absolute_change"] == delta
                    for key, source in [("previous_fact_id", prior), ("current_fact_id", current)]:
                        assert change[key] == next(f.fact_id for f in source.source_facts.facts if f.metric == "EBITDA")
            assert reconstructed.tables == before
            # A substituted prior payload cannot become an authoritative delta.
            prior_id = expected[0][0][1][0]
            row = next(r for r in reconstructed.tables["governed_analysis_envelopes"] if r["analysis_id"] == prior_id)
            row["envelope_json"] = expected[1][0][1][1].model_dump(mode="json")
            response = await client.get(f"/api/v1/governed-analyses/{expected[0][0][0][0]}/temporal-comparison",
                                        headers={"Authorization": "Bearer synthetic"})
            assert response.status_code == 503

    asyncio.run(exercise())
