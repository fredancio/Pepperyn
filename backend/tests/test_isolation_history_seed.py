import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from sandbox import seed_isolation_history as target
from test_isolation_account_provisioning import bundle, uuid


class SeedTests(unittest.TestCase):
    def run_case(self, fault=None):
        scopes = [(uuid(i), uuid(i+10), uuid(i+20), uuid(i+30)) for i in (1, 2)]
        rows, envelopes, calls = {}, {}, []
        inspections = 0
        def inspect(*args, verified_scopes, **kwargs):
            nonlocal inspections
            inspections += 1
            verified_scopes.extend(scopes if fault != "changed-scope" or inspections == 1 else list(reversed(scopes)))
            return {"status": "A26_SCOPES_INSPECTED", "both_scopes_empty": fault != "existing"}
        def save(db, analysis_row, engagement_id, envelope):
            calls.append(analysis_row["id"])
            if fault == "timeout-first" or fault == "timeout-second" and len(calls) == 2:
                raise RuntimeError("sensitive-db-response")
            rows[analysis_row["id"]] = analysis_row
            envelopes[analysis_row["id"]] = envelope
        def load(db, analysis_id, **kwargs):
            if fault == "load-failure": raise RuntimeError("sensitive-db-response")
            return envelopes[analysis_id]
        class Query:
            def __init__(self): self.id = None
            def select(self, fields): return self
            def eq(self, key, value):
                if key == "id": self.id = value
                return self
            def limit(self, n): return self
            def execute(self): return NS(data=[] if fault == "missing-row" else [rows[self.id]])
        db = NS(table=lambda table: Query())
        with patch.object(target, "inspect", inspect), patch.object(target, "save_governed_analysis", save), patch.object(target, "load_governed_envelope", load):
            result = target.seed(bundle(), "service", "anon", lambda *a: db,
                                 authorization="wrong" if fault == "unauthorized" else target.AUTHORIZATION)
        return result, calls, rows

    def test_actual_registered_mock_prepared_and_verified_twice(self):
        result, calls, rows = self.run_case()
        self.assertEqual(result["status"], "A26_SYNTHETIC_PAIRS_SEEDED")
        self.assertEqual(result["verified_pairs"], 2)
        self.assertEqual(len(set(calls)), 2)
        self.assertEqual(len({r["company_id"] for r in rows.values()}), 2)
        self.assertFalse(result["populated_history_isolation_proven"])

    def test_prewrite_refusals(self):
        for fault in ("unauthorized", "existing", "changed-scope"):
            result, calls, _ = self.run_case(fault)
            self.assertEqual(result["status"], "REFUSED")
            self.assertEqual(calls, [])

    def test_partial_failure_no_retry_no_sensitive_output(self):
        for fault, count in (("timeout-first", 1), ("timeout-second", 2), ("load-failure", 1), ("missing-row", 1)):
            result, calls, _ = self.run_case(fault)
            self.assertEqual(result["status"], "REFUSED")
            self.assertEqual(len(calls), count)
            self.assertTrue(result["remote_partial_write_possible"])
            self.assertFalse(result["automatic_retry_permitted"])
            self.assertNotIn("sensitive-db-response", str(result))

    def test_fixture_ids_repeat_for_same_scope_not_across_scopes(self):
        one = (uuid(1), uuid(11), uuid(21), uuid(31))
        self.assertEqual(target.fixture_id(one), target.fixture_id(one))
        self.assertNotEqual(target.fixture_id(one), target.fixture_id((uuid(2), *one[1:])))
