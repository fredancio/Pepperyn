import unittest
from types import SimpleNamespace as NS
from sandbox.verify_feedback_privileges import verify, URL, EMAILS


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.bundle = dict(project_url=URL, purpose='A24_TECHNICAL_ISOLATION_ONLY',
                           accounts=[dict(email=e, password='synthetic') for e in EMAILS])
        self.calls = []
    def factory(self, url, key):
        test = self
        class Client:
            def __init__(self): self.auth = self
            def sign_in_with_password(self, account):
                self.i = EMAILS.index(account['email']) + 1
                self.uid = f'00000000-0000-4000-8000-{self.i:012d}'
                self.company = f'00000000-0000-4000-9000-{self.i:012d}'
                return NS(session=NS(access_token=f'token-{self.i}'))
            def get_user(self, token): return NS(user=NS(id=self.uid, email=EMAILS[self.i-1], role='authenticated'))
            def table(self, table): self.current = table; return self
            def select(self, fields): return self
            def eq(self, key, value): return self
            def limit(self, n): return self
            def execute(self):
                row = dict(id=self.uid, company_id=self.company) if self.current == 'profiles' else dict(
                    id=self.company, admin_user_id=self.uid, name=f'Pepperyn A24 Isolation Synthetic {self.i}')
                return NS(data=[row])
        return Client()
    def request(self, method, url, headers, payload):
        self.calls.append((method, url, headers, payload))
        if method == 'POST':
            self.assertIsNone(payload['company_id']); self.assertIsNone(payload['report_id'])
        else: self.assertTrue(url.endswith('?id=is.null'))
        return 403, {'code': '42501', 'message': 'permission denied for table decision_feedback'}
    def test_exact_denials_and_no_mutable_payload(self):
        result = verify(self.bundle, 'anon', self.factory, self.request)
        self.assertEqual(result['status'], 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS')
        self.assertEqual(len(self.calls), 6)
        self.assertFalse(result['write_isolation_proven'])
        self.assertEqual({x[2]['Authorization'] for x in self.calls}, {'Bearer token-1', 'Bearer token-2'})
    def test_wrong_error_and_success_never_pass(self):
        for response in [(200, {}), (400, {'code': '23502'}), (401, {}),
                         (403, {'code': '42501', 'message': 'other table'})]:
            result = verify(self.bundle, 'anon', self.factory, lambda *args: response)
            self.assertEqual(result['status'], 'REFUSED')
            self.assertEqual(result['attempted_operations'], 1)
    def test_foreign_project_never_authenticates(self):
        self.bundle['project_url'] = 'https://foreign.invalid'
        result = verify(self.bundle, 'anon', lambda *args: self.fail('No auth permitted'), self.request)
        self.assertEqual(result['stage'], 'INPUT')
