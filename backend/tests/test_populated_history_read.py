import unittest
from sandbox.verify_populated_history import verify
from sandbox.seed_isolation_history import fixture_id
from test_populated_history_preflight import Factory
from test_isolation_account_provisioning import bundle, uuid
from types import SimpleNamespace as NS


class PopulatedReadTests(unittest.TestCase):
    def run_case(self, fault=None):
        f = Factory("engagement" if fault == "engagement" else None)
        def factory(url, key):
            client = f(url, key)
            original_table = client.table
            def table(name):
                if key == "anon" and name == "engagements":
                    raise AssertionError("User engagement access forbidden by fixture")
                if key == "service":
                    self.assertEqual(name, "engagements")
                return original_table(name)
            client.table = table
            i = f.i
            client.auth.sign_in_with_password = lambda attrs: NS(session=NS(access_token=f"secret-{i}"))
            return client
        def get(url, headers):
            if not headers: return (200 if fault == "anonymous" else 401), {}
            self.assertIn(headers["Authorization"], ("Bearer secret-1", "Bearer secret-2"))
            self.assertNotIn("apikey", headers)
            i = int(headers["Authorization"][-1])
            foreign = f"entity_id={uuid(3-i+20)}" in url
            if fault == "outage": return 503, {}
            if foreign and fault != "foreign-empty": return 404, {"detail": "Entité introuvable"}
            if foreign or fault == "empty": return 200, {"analyses": []}
            if fault == "substitution" and "company_id" in url: i = 3-i
            row = {"id": fixture_id((uuid(i), uuid(i+10), uuid(i+20), uuid(i+30))),
                   "entity_id": uuid(i+20), "fichier_nom": "pepperyn_v1_heterogeneous_english.xlsx",
                   "type_document": "AUTRE", "score_confiance": 0, "created_at": "2026-09-20"}
            if fault == "wrong-id": row["id"] = "foreign-must-not-leak"
            if fault == "wrong-entity": row["entity_id"] = uuid(99)
            if fault == "extra-field": row["foreign_data"] = "foreign-must-not-leak"
            return 200, {"analyses": [row, row] if fault == "extra-row" else [row]}
        return verify(bundle(), "anon", factory, get, service_key="service")

    def test_populated_success_is_bounded(self):
        result = self.run_case()
        self.assertEqual(result["status"], "BOUNDED_POPULATED_HISTORY_ISOLATION_PASS")
        self.assertFalse(result["global_isolation_proven"])
        self.assertFalse(result["business_write_performed"])

    def test_falsifications(self):
        for fault in ("engagement", "anonymous", "outage", "foreign-empty", "empty", "substitution", "wrong-id", "wrong-entity", "extra-row", "extra-field"):
            with self.subTest(fault=fault):
                result = self.run_case(fault)
                self.assertEqual(result["status"], "REFUSED")
                self.assertNotIn("secret-", str(result))
                self.assertNotIn("foreign-must-not-leak", str(result))
