import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch, AsyncMock, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers import decision_memory as route
from services.decision_memory_service import DecisionMemoryService, extract_recommendations


class Database:
    def __init__(self):
        self.tables = {"analyses": [dict(id="report", company_id="owner", status="completed",
                         analyse_json={"recommandations": [{"action": "Synthetic recommendation"}]})],
                       "governed_analysis_envelopes": [], "decision_feedback": []}
        self.writes = []
        self.fail = None
    def from_(self, table):
        db = self
        class Query:
            def __init__(self): self.rows = list(db.tables[table]); self.write = None
            def select(self, fields): return self
            def eq(self, key, value): self.rows = [r for r in self.rows if r.get(key) == value]; return self
            def limit(self, n): self.rows = self.rows[:n]; return self
            def upsert(self, row, **kwargs): self.write = row; return self
            def execute(self):
                if table == db.fail: raise RuntimeError("private-db-content")
                if self.write is not None: db.writes.append(self.write)
                return NS(data=self.rows)
        return Query()


class WriteAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.service = DecisionMemoryService(self.db)
        self.service.compute_user_patterns = Mock()
        rec = extract_recommendations(self.db.tables["analyses"][0]["analyse_json"], "report")[0]
        self.body = dict(report_id="report", recommendation_id=rec["id"], recommendation_text=rec["text"],
                         recommendation_source=rec["source"], status="unsure")
        self.patches = [patch.object(route, "_decision_memory_service", self.service),
                        patch.object(route, "_resolve_auth", AsyncMock(return_value=("owner", "free", "admin")))]
        for p in self.patches: p.start()
        app = FastAPI(); app.include_router(route.router); self.client = TestClient(app)
    def tearDown(self):
        self.client.close()
        for p in reversed(self.patches): p.stop()
    def post(self): return self.client.post("/api/decision-feedback", json=self.body)
    def refused(self, code):
        response = self.post()
        self.assertEqual(response.status_code, code)
        self.assertEqual(self.db.writes, [])
        self.service.compute_user_patterns.assert_not_called()
        self.assertNotIn("private-db-content", response.text)
    def test_owned_legacy_recommendation_still_writes(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(len(self.db.writes), 1)
        self.assertEqual(self.db.writes[0]["company_id"], "owner")
    def test_foreign_and_missing_report(self):
        self.db.tables["analyses"][0]["company_id"] = "foreign"
        self.refused(404)
        self.db.tables["analyses"] = []
        self.refused(404)
    def test_governed_route_bypass_refused_before_side_effects(self):
        self.db.tables["governed_analysis_envelopes"] = [dict(analysis_id="report", company_id="owner")]
        self.body["status"] = "planned"
        self.refused(409)
    def test_forged_recommendation_and_incomplete_report(self):
        for field in ("recommendation_id", "recommendation_text", "recommendation_source"):
            old = self.body[field]; self.body[field] = "forged"; self.refused(409); self.body[field] = old
        self.db.tables["analyses"][0]["status"] = "pending"; self.refused(409)
    def test_foreign_existing_feedback_never_reassigned(self):
        self.db.tables["decision_feedback"] = [dict(company_id="foreign", report_id="report", recommendation_id=self.body["recommendation_id"])]
        self.refused(409)
    def test_dependency_outages_fail_closed(self):
        for table in self.db.tables:
            self.db.fail = table; self.refused(503)

    def test_two_identity_route_matrix_preserves_write_ownership(self):
        """Local HTTP proof with synthetic auth doubles, not live JWT evidence."""
        from fastapi import HTTPException
        self.db.tables["analyses"].append(dict(
            id="report-b", company_id="owner-b", status="completed",
            analyse_json={"recommandations": [{"action": "Second synthetic recommendation"}]}))
        async def resolve(authorization, x_auth_type):
            owners = {"Bearer synthetic-a": "owner", "Bearer synthetic-b": "owner-b"}
            if authorization not in owners:
                raise HTTPException(401, "Authentification requise")
            return owners[authorization], "free", "admin"
        bodies = []
        for report in self.db.tables["analyses"]:
            rec = extract_recommendations(report["analyse_json"], report["id"])[0]
            bodies.append(dict(report_id=report["id"], recommendation_id=rec["id"],
                               recommendation_text=rec["text"], recommendation_source=rec["source"],
                               status="unsure"))
        with patch.object(route, "_resolve_auth", resolve):
            for i, token in enumerate(("synthetic-a", "synthetic-b")):
                headers = {"Authorization": f"Bearer {token}"}
                foreign = bodies[1-i]
                before = len(self.db.writes)
                denied = self.client.post("/api/decision-feedback", headers=headers, json=foreign)
                self.assertEqual(denied.status_code, 404)
                self.assertEqual(len(self.db.writes), before)
                own = dict(bodies[i], company_id="forged-other-company")
                accepted = self.client.post("/api/decision-feedback", headers=headers, json=own)
                self.assertEqual(accepted.status_code, 200)
                self.assertFalse(accepted.json()["arc_created"])
                self.assertEqual(self.db.writes[-1]["company_id"], ("owner", "owner-b")[i])
                self.assertEqual(self.db.writes[-1]["report_id"], own["report_id"])
            before = len(self.db.writes)
            self.assertEqual(self.client.post("/api/decision-feedback", json=bodies[0]).status_code, 401)
            self.assertEqual(len(self.db.writes), before)
