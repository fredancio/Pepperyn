"""Static repair scope checks, not deployed PostgreSQL proof."""
import re
import unittest
from pathlib import Path


class PatternsRepairTests(unittest.TestCase):
    def test_restore_v7_columns_without_other_table_mutation(self):
        folder = Path(__file__).parents[1] / 'migrations'
        old = (folder / 'v7_decision_memory.sql').read_text(encoding='utf-8')
        new = (folder / 'v38_restore_backend_user_patterns.sql').read_text(encoding='utf-8')
        def columns(sql):
            body = sql.split('public.user_patterns (', 1)[1].split('\n);', 1)[0]
            return re.findall(r'^\s*(\w+)\s+(?:UUID|NUMERIC|JSONB|TEXT|INTEGER|TIMESTAMP)\b', body, re.M)
        self.assertEqual(columns(old), columns(new))
        self.assertNotRegex(new, r'(?i)\b(INSERT INTO|DELETE FROM|UPDATE public\.|DROP TABLE)')
        self.assertIn('V38_ALREADY_PRESENT_STOP_AND_INSPECT', new)
        self.assertNotIn('IF NOT EXISTS', new)
    def test_backend_only_transactional_privileges(self):
        sql = (Path(__file__).parents[1] / 'migrations/v38_restore_backend_user_patterns.sql').read_text(encoding='utf-8')
        for text in ('BEGIN;', 'COMMIT;', 'ENABLE ROW LEVEL SECURITY', 'has_any_column_privilege',
                     'GRANT SELECT, INSERT, UPDATE ON public.user_patterns TO service_role'):
            self.assertIn(text, sql)
        self.assertNotIn('CREATE POLICY', sql)
