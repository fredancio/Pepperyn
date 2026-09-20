"""Local HTTP contract falsification; synthetic DB/auth doubles, no live proof."""
import unittest
from types import SimpleNamespace, ModuleType
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from routers import analyze


def row(identity, company, entity, status="completed"):
    return dict(id=identity, company_id=company, entity_id=entity, status=status,
                fichier_nom="synthetic.xlsx", type_document="synthetic",
                created_at="2026-09-20T00:00:00Z", score_confiance=0)


class Database:
    def __init__(self):
        self.tables = {
            "entities": [dict(id="a", company_id="one"), dict(id="b", company_id="two"),
                         dict(id="c", company_id="one")],
            "analyses": [row("aa", "one", "a"), row("bb", "two", "b"),
                         row("cc", "one", "c"), row("pending", "one", "a", "pending")],
        }
        self.calls = []
        self.fault = None
        self.replacement = {}

    def from_(self, table):
        self.calls.append(table)
        db = self

        class Query:
            def __init__(self): self.rows = list(db.tables[table])
            def select(self, fields): return self
            def eq(self, key, value):
                self.rows = [r for r in self.rows if r.get(key) == value]
                return self
            def order(self, *args, **kwargs): return self
            def limit(self, n): self.rows = self.rows[:n]; return self
            def execute(self):
                if db.fault == table: raise RuntimeError("DO_NOT_DISCLOSE_PRIVATE_RESPONSE")
                return SimpleNamespace(data=db.replacement.get(table, self.rows))
        return Query()


class HistoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        main = ModuleType("main")
        main.get_supabase_service = lambda: self.db
        self.main_patch = patch.dict("sys.modules", {"main": main})
        self.main_patch.start()
        self.auth = AsyncMock(return_value=("one", "free", "admin"))
        self.auth_patch = patch.object(analyze, "_resolve_auth", self.auth)
        self.auth_patch.start()
        app = FastAPI()
        app.include_router(analyze.router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.auth_patch.stop()
        self.main_patch.stop()

    def read(self, entity="a"):
        return self.client.get("/api/analyses/history", params={} if entity is None else {"entity_id": entity})

    def test_success_is_scoped_and_projects_only_public_fields(self):
        response = self.read()
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.json()["analyses"]], ["aa"])
        self.assertNotIn("company_id", response.json()["analyses"][0])
        self.assertEqual([r["id"] for r in self.read(None).json()["analyses"]], ["aa", "cc"])
        self.auth.return_value = ("two", "free", "admin")
        self.assertEqual([r["id"] for r in self.read("b").json()["analyses"]], ["bb"])

    def test_foreign_missing_and_empty_scope_are_not_empty_success(self):
        for entity in ("b", "missing", ""):
            with self.subTest(entity=entity):
                self.db.calls.clear()
                self.assertEqual(self.read(entity).status_code, 404)
                self.assertNotIn("analyses", self.db.calls)

    def test_empty_is_success_only_after_owned_entity_and_successful_read(self):
        self.db.tables["analyses"] = []
        self.assertEqual(self.read().json(), {"analyses": []})
        self.assertEqual(self.read().status_code, 200)

    def test_database_failures_are_sanitized_503_not_empty(self):
        for table in ("entities", "analyses"):
            self.db.fault = table
            with self.assertLogs(analyze.logger, level="ERROR") as logs:
                response = self.read()
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Historique indisponible."})
            self.assertNotIn("DO_NOT_DISCLOSE", str(logs.output))

    def test_malformed_or_unbound_rows_fail_closed(self):
        bad = [None, {}, [None], [row("foreign", "two", "a")],
               [row("wrong-entity", "one", "c")], [row("pending", "one", "a", "pending")],
               [row("aa", "one", "a")] * 2, [row("", "one", "a")],
               [row(str(i), "one", "a") for i in range(21)]]
        for rows in bad:
            with self.subTest(rows=rows):
                self.db.replacement = {"analyses": rows}
                self.assertEqual(self.read().status_code, 503)
        for entities in (None, {}, [None], [dict(id="a", company_id="two")],
                         [dict(id="a", company_id="one")] * 2):
            self.db.replacement = {"entities": entities}
            self.assertEqual(self.read().status_code, 503)

    def test_unauthenticated_fails_before_database(self):
        self.auth.side_effect = HTTPException(401, "Token requis")
        self.assertEqual(self.read().status_code, 401)
        self.assertEqual(self.db.calls, [])


if __name__ == "__main__":
    unittest.main()
