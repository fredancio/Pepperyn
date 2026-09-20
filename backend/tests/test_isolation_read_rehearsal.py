import unittest
from types import SimpleNamespace as NS
from test_isolation_account_provisioning import Factory, bundle, uuid
from sandbox.verify_isolation_accounts import verify


class ReadRehearsalTests(unittest.TestCase):
    def run_case(self, fault=None):
        factory = Factory()
        count = 0
        def make(url, key):
            nonlocal count
            count += 1
            i = count
            factory.created = [None] * i
            client = factory(url, key)
            client.auth.sign_in_with_password = lambda attrs: NS(session=NS(access_token=f"synthetic-token-{i}"))
            return client
        def get(url, headers):
            if "/rest/v1/" in url:
                if "limit=0" in url:
                    if fault == "outage": return 503, {"code": "42501"}
                    if fault == "wrong-denial": return 403, {"code": "UNRELATED"}
                    if fault == "permissive": return 200, []
                    return 403, {"code": "42501"}
                if fault == "foreign-row": return 200, [{"id": "must-not-be-output"}]
                return 200, []
            if not headers: return 401, {}
            i = int(headers["Authorization"][-1])
            if fault == "substitution" and "?" in url: i = 3-i
            if fault == "backend-outage": return 503, {}
            return 200, {"success": True, "data": [{"id": uuid(i+20)}]}
        return verify(bundle(), "anon-test", make, get)

    def test_bounded_pass(self):
        result = self.run_case()
        self.assertEqual(result["status"], "BOUNDED_TWO_USER_READ_ISOLATION_PASS")
        self.assertFalse(result["global_isolation_proven"])
        self.assertFalse(result["analysis_export_isolation_proven"])
        self.assertFalse(result["business_write_performed"])

    def test_falsifications(self):
        for fault in ["outage", "wrong-denial", "permissive", "foreign-row", "substitution", "backend-outage"]:
            with self.subTest(fault=fault):
                result = self.run_case(fault)
                self.assertEqual(result["status"], "REFUSED")
                self.assertNotIn("must-not-be-output", str(result))
                self.assertNotIn("synthetic-token", str(result))
