"""Static scope/guard checks, not a PostgreSQL execution or deployed proof."""
from pathlib import Path
import re
import unittest


class FeedbackMigrationTests(unittest.TestCase):
    def test_transaction_and_effective_right_guards(self):
        sql = (Path(__file__).parents[1] / 'migrations/v37_confine_decision_feedback_writes.sql').read_text(encoding='utf-8')
        for clause in ('BEGIN;', 'COMMIT;', 'lock_timeout', 'statement_timeout',
                       'has_any_column_privilege', 'V37_SERVICE_BASELINE_REFUSED',
                       'V37_EFFECTIVE_TABLE_WRITE_REMAINS', 'V37_SERVICE_PRIVILEGE_LOST'):
            self.assertIn(clause, sql)
        self.assertEqual(set(re.findall(r'public\.([a-z_]+)', sql)), {'decision_feedback'})

    def test_no_row_mutation_or_policy_replacement(self):
        sql = (Path(__file__).parents[1] / 'migrations/v37_confine_decision_feedback_writes.sql').read_text(encoding='utf-8')
        self.assertNotRegex(sql, r'(?i)\b(INSERT\s+INTO|DELETE\s+FROM|UPDATE\s+public|DROP\s+POLICY|CREATE\s+POLICY|ALTER\s+TABLE)\b')
        self.assertNotRegex(sql, r'(?i)REVOKE\s+(ALL|SELECT)')
        self.assertIn('FROM PUBLIC, anon, authenticated', sql)
