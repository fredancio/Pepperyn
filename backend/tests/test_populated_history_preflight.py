import unittest
from copy import deepcopy
from types import SimpleNamespace as NS
from sandbox.inspect_populated_history_scope import inspect
from test_isolation_account_provisioning import bundle, uuid, user


class Factory:
    def __init__(self, fault=None):
        self.i = 0
        self.fault = fault
        self.reads = []

    def __call__(self, url, key):
        parent = self
        if key == "anon": self.i += 1
        client = NS()
        client.auth = NS(sign_in_with_password=lambda attrs: NS(session=NS(access_token="secret")),
                         get_user=lambda token: NS(user=user(parent.i)))

        class Query:
            def __init__(self, table): self.table = table; self.filters = {}
            def select(self, fields): return self
            def eq(self, k, v): self.filters[k] = v; return self
            def limit(self, n): assert n == 2; return self
            def execute(self):
                i = parent.i
                company, entity = uuid(i+10), uuid(i+20)
                parent.reads.append((self.table, self.filters))
                if parent.fault == "outage": raise RuntimeError("secret")
                data = {
                    "profiles": [{"id": uuid(i), "company_id": company}],
                    "companies": [{"id": company, "admin_user_id": uuid(i), "name": f"Pepperyn A24 Isolation Synthetic {i}"}],
                    "entities": [{"id": entity, "company_id": company, "name": f"Pepperyn A24 Isolation Synthetic {i}", "is_primary": True}],
                    "engagements": [{"id": uuid(i+30), "entity_id": entity}],
                    "analyses": [], "governed_analysis_envelopes": [],
                }[self.table]
                if parent.fault == "owner" and self.table == "companies": data[0]["admin_user_id"] = uuid(99)
                if parent.fault == "foreign-entity" and self.table == "entities": data[0]["company_id"] = uuid(99)
                if parent.fault == "engagement" and self.table == "engagements": data[0]["entity_id"] = uuid(99)
                if parent.fault == "duplicate-engagement" and self.table == "engagements": data *= 2
                if parent.fault == "malformed" and self.table == "analyses": data = None
                if parent.fault == "foreign-row" and self.table == "analyses": data = [{"company_id": uuid(99)}]
                if parent.fault == "populated" and self.table == "analyses": data = [{"company_id": company, "id": uuid(100)}]
                return NS(data=data)
        client.table = Query
        return client


class PreflightTests(unittest.TestCase):
    def test_empty_scope_inspection_does_not_claim_isolation(self):
        f = Factory()
        result = inspect(bundle(), "service", "anon", f)
        self.assertEqual(result["status"], "A26_SCOPES_INSPECTED")
        self.assertTrue(result["both_scopes_empty"])
        self.assertFalse(result["populated_history_isolation_proven"])
        self.assertFalse(result["business_write_performed"])
        for table, filters in f.reads:
            if table in ("analyses", "governed_analysis_envelopes"):
                self.assertIn("company_id", filters)

    def test_existing_records_are_reported_not_overwritten(self):
        result = inspect(bundle(), "service", "anon", Factory("populated"))
        self.assertEqual(result["status"], "A26_SCOPES_INSPECTED")
        self.assertFalse(result["both_scopes_empty"])

    def test_falsifications_are_content_free(self):
        for fault in ("outage", "owner", "foreign-entity", "engagement", "duplicate-engagement", "malformed", "foreign-row"):
            with self.subTest(fault=fault):
                result = inspect(bundle(), "service", "anon", Factory(fault))
                self.assertEqual(result["status"], "REFUSED")
                self.assertNotIn("secret", str(result))

    def test_wrong_project_refused_before_access(self):
        data = deepcopy(bundle()); data["project_url"] = "https://wrong.invalid"
        f = Factory()
        self.assertEqual(inspect(data, "service", "anon", f)["status"], "REFUSED")
        self.assertEqual(f.reads, [])
