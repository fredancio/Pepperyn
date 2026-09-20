import unittest
from types import SimpleNamespace as NS
from test_isolation_account_provisioning import Factory, bundle, uuid
from sandbox.verify_isolation_accounts import verify


class ReadRehearsalTests(unittest.TestCase):
    def run_case(self, fault=None, include_history=False):
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
            if "/api/analyses/history" in url:
                own = f"entity_id={uuid(i+20)}" in url
                if fault == "history-outage": return 503, {}
                if fault == "history-false-empty": return 200, {"analyses": []}
                if fault == "history-wrong-denial": return 404, {"detail": "unrelated"}
                if fault == "history-populated": return 200, {"analyses": [{"id": "must-not-be-output"}]}
                return (200, {"analyses": []}) if own else (404, {"detail": "Entité introuvable"})
            if fault == "substitution" and "?" in url: i = 3-i
            if fault == "backend-outage": return 503, {}
            return 200, {"success": True, "data": [{"id": uuid(i+20)}]}
        return verify(bundle(), "anon-test", make, get, include_history=include_history)

    def test_history_scope_pass_is_not_populated_history_proof(self):
        result = self.run_case(include_history=True)
        self.assertEqual(result["status"], "BOUNDED_HISTORY_SCOPE_READ_PASS")
        self.assertFalse(result["populated_history_isolation_proven"])
        self.assertFalse(result["analysis_export_isolation_proven"])

    def test_history_failure_cannot_pass_by_empty_or_unrelated_refusal(self):
        for fault in ("history-outage", "history-false-empty", "history-wrong-denial", "history-populated"):
            with self.subTest(fault=fault):
                result = self.run_case(fault, include_history=True)
                self.assertEqual(result["status"], "REFUSED")
                self.assertNotIn("must-not-be-output", str(result))

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
