import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS
from sandbox import diagnose_history_engagement as target
from test_isolation_account_provisioning import bundle, uuid, user


class DiagnosticTests(unittest.TestCase):
    def run_case(self, status=403, data=None, wrong_binding=False, outage=False):
        scopes = [(uuid(i), uuid(i+10), uuid(i+20), uuid(i+30)) for i in (1, 2)]
        def inspect(*args, verified_scopes, **kwargs):
            verified_scopes.extend(scopes)
            return {"status": "A26_SCOPES_INSPECTED"}
        class Query:
            def __init__(self): self.filters = {}
            def select(self, fields): return self
            def eq(self, k, v): self.filters[k] = v; return self
            def limit(self, n): return self
            def execute(self):
                return NS(data=[dict(self.filters, status="completed", contexte_utilisateur="A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1",
                                     analyse_json={"synthetic": not wrong_binding})])
        def factory(url, key):
            if key == "service": return NS(table=lambda name: Query())
            auth = NS()
            def login(account):
                auth.get_user = lambda token: NS(user=user(bundle()["accounts"].index(account)+1))
                return NS(session=NS(access_token="secret-token"))
            auth.sign_in_with_password = login
            return NS(auth=auth)
        def get(url, headers):
            if outage: raise RuntimeError("secret-data")
            return status, data
        envelope = NS(analysis_result=NS(model_dump=lambda **kwargs: {"synthetic": True}))
        with patch.object(target, "inspect", inspect), patch.object(target, "load_governed_envelope", return_value=envelope):
            return target.diagnose(bundle(), "service", "anon", factory, get)

    def test_permission_vs_empty_vs_unrelated_error(self):
        for status, data, expected in ((403, {"code": "42501", "message": "secret-data"}, "DATABASE_PERMISSION_DENIED"),
                                       (200, [], "EMPTY_UNDER_USER_SESSION"),
                                       (503, {"code": "42501"}, "OTHER_RESPONSE"),
                                       (200, [{"id": "foreign-secret"}], "UNEXPECTED_ROWS")):
            result = self.run_case(status, data)
            self.assertEqual(result["status"], "A26_ENGAGEMENT_DIAGNOSED")
            self.assertEqual(result["findings"][0]["direct_engagement_classification"], expected)
            self.assertTrue(result["findings"][0]["persisted_seed_binding_verified"])
            self.assertFalse(result["populated_history_isolation_proven"])
            self.assertNotIn("secret", str(result))

    def test_wrong_binding_is_not_verified(self):
        result = self.run_case(200, [], wrong_binding=True)
        self.assertFalse(result["findings"][0]["persisted_seed_binding_verified"])

    def test_transport_outage_refuses_safely(self):
        result = self.run_case(outage=True)
        self.assertEqual(result["status"], "REFUSED")
        self.assertNotIn("secret", str(result))
