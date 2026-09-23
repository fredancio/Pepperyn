import copy
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from routers import decision_memory as route
from services.decision_memory_service import DecisionMemoryService
from sandbox import rehearse_feedback_api as runner


class DB:
    def __init__(self, scopes):
        self.rows = {t: [] for t in runner.TABLES}
        self.inserts = 0
        self.fail_insert = 0
        for scope in scopes:
            _, company, entity, engagement = scope
            self.rows['analyses'].append(dict(id=runner.a26_id(scope), company_id=company, entity_id=entity,
                contexte_utilisateur='A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1', status='completed'))
            self.rows['governed_analysis_envelopes'].append(dict(analysis_id=runner.a26_id(scope),
                company_id=company, entity_id=entity, engagement_id=engagement))
    def table(self, table):
        db = self
        class Query:
            def __init__(self): self.filters = []; self.operation = None; self.cap = None
            def select(self, value): return self
            def eq(self, key, value): self.filters.append((key, value)); return self
            def limit(self, value): self.cap = value; return self
            def insert(self, row): self.operation = ('insert', row); return self
            def upsert(self, row, **kwargs): self.operation = ('upsert', row); return self
            def execute(self):
                if self.operation:
                    op, row = self.operation
                    if op == 'insert':
                        db.inserts += 1
                        if db.inserts == db.fail_insert: raise RuntimeError('synthetic write failure')
                    db.rows[table].append(copy.deepcopy(row))
                result = [r for r in db.rows[table] if all(r.get(k) == v for k, v in self.filters)]
                return NS(data=copy.deepcopy(result[:self.cap]))
        return Query()
    from_ = table


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.scopes = [tuple(f'00000000-0000-4000-8000-{n:012d}' for n in range(i, i+4)) for i in (1, 11)]
        self.db = DB(self.scopes)
        self.before = copy.deepcopy(self.db.rows)
        self.bundle = {'accounts': [{'email': 'synthetic-a', 'password': 'unused'},
                                    {'email': 'synthetic-b', 'password': 'unused'}]}
        service = DecisionMemoryService(self.db)
        async def auth(authorization, x_auth_type):
            if authorization not in ('Bearer synthetic-a', 'Bearer synthetic-b'):
                raise HTTPException(401, 'Unauthorized')
            return self.scopes[authorization.endswith('b')][1], 'free', 'admin'
        def inspect(*args, verified_scopes):
            verified_scopes.extend(self.scopes)
            return {'status': 'A26_SCOPES_INSPECTED'}
        self.patches = [patch.object(route, '_resolve_auth', auth), patch.object(route, '_decision_memory_service', service),
                        patch.object(runner, 'inspect', inspect),
                        patch.object(runner, 'direct_denials', return_value={'status': 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS'})]
        for p in self.patches: p.start()
        app = FastAPI(); app.include_router(route.router)
        @app.get('/health')
        def health(): return {'environment': 'development'}
        self.client = TestClient(app)
    def tearDown(self):
        self.client.close()
        for p in reversed(self.patches): p.stop()
    def factory(self, url, key):
        if key == 'service': return self.db
        scopes = self.scopes
        class Auth:
            def sign_in_with_password(self, account): return NS(session=NS(access_token=account['email']))
            def get_user(self, token): return NS(user=NS(id=scopes[token.endswith('b')][0]))
        return NS(auth=Auth())
    def request(self, method, url, headers, payload):
        response = self.client.request(method, url.replace(runner.API, ''), headers=headers, json=payload)
        return response.status_code, response.json()
    def run_rehearsal(self, request=None):
        return runner.run(self.bundle, 'anon', 'service', self.factory, request or self.request,
                          authorization=runner.AUTHORIZATION)
    def test_positive_and_adversarial_real_route_with_doubles(self):
        result = self.run_rehearsal()
        self.assertEqual(result['status'], 'BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS', result)
        self.assertEqual(result['authorized_unsure_writes'], 2)
        self.assertEqual(result['adversarial_refusals'], 15)
        self.assertTrue(result['a26_pairs_unchanged'])
        self.assertEqual(len(self.db.rows['user_patterns']), 2)
        self.assertEqual(self.db.rows['decision_arcs'], [])
    def test_anonymous_transport_media_type_controls_validation(self):
        from urllib.request import Request, HTTPHandler, build_opener
        body = dict(report_id='synthetic', recommendation_id='synthetic',
                    recommendation_text='Synthetic', status='unsure')
        handler = HTTPHandler()
        build_opener(handler)
        old = handler.http_request(Request(runner.API + '/api/decision-feedback',
                    data=json.dumps(body).encode(), headers={}, method='POST'))
        self.assertEqual(old.get_header('Content-type'), 'application/x-www-form-urlencoded')
        with patch.object(route, '_resolve_auth', side_effect=AssertionError('auth not reached')):
            result = self.client.post('/api/decision-feedback', content=old.data,
                                     headers=dict(old.header_items()))
        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.json()['detail'][0]['loc'], ['body'])
        result = self.client.post('/api/decision-feedback', content=old.data,
                                  headers={'Content-Type': 'application/json'})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.db.rows, self.before)
    def test_anonymous_rehearsal_declares_json_without_auth(self):
        def transport(method, url, headers, payload):
            if method == 'POST' and not headers.get('Authorization'):
                self.assertEqual(headers, {'Content-Type': 'application/json'})
            return self.request(method, url, headers, payload)
        self.assertEqual(self.run_rehearsal(transport)['status'],
                         'BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS')
    def test_old_backend_stops_before_seed(self):
        def old(method, url, headers, payload):
            code, data = self.request(method, url, headers, payload)
            if url.endswith('/openapi.json'): data['paths']['/api/decision-feedback']['post'].pop('x-pepperyn-write-authority')
            return code, data
        self.assertEqual(self.run_rehearsal(old)['stage'], 'BACKEND_REVISION')
        self.assertEqual(self.db.rows, self.before)
    def test_partial_seed_never_retries(self):
        self.db.fail_insert = 2
        result = self.run_rehearsal()
        self.assertEqual(result['stage'], 'SEED_2')
        self.assertEqual(result['seed_acknowledged'], 1)
        self.assertFalse(result['automatic_retry_permitted'])
    def test_existing_feedback_stops_before_write(self):
        self.db.rows['decision_feedback'].append({'company_id': self.scopes[0][1]})
        self.assertEqual(self.run_rehearsal()['stage'], 'BASELINE_NO_A28_OR_FEEDBACK')
        self.assertEqual(self.db.inserts, 0)
    def test_missing_patterns_has_precise_safe_stage_and_no_seed(self):
        del self.db.rows['user_patterns']
        result = self.run_rehearsal()
        self.assertEqual(result['stage'], 'SNAPSHOT_USER_1_USER_PATTERNS')
        self.assertEqual(result['seed_attempts'], 0)
        self.assertFalse(result['remote_partial_write_possible'])
    def test_foreign_200_does_not_count_as_pass(self):
        def bypass(method, url, headers, payload):
            if method == 'POST' and headers.get('Authorization') and payload['report_id'] != runner.a26_id(self.scopes[0]):
                return 200, {'success': True}
            return self.request(method, url, headers, payload)
        result = self.run_rehearsal(bypass)
        self.assertEqual(result['stage'], 'USER_1_FOREIGN_BEFORE')
        self.assertEqual(result['authorized_post_attempts'], 0)
    def seed_existing(self):
        def stop(method, url, headers, payload):
            if method == 'POST':
                return 422, {'detail': 'synthetic original refusal'}
            return self.request(method, url, headers, payload)
        result = self.run_rehearsal(stop)
        self.assertEqual(result['seed_acknowledged'], 2)
        self.assertEqual(result['observed_http_status'], 422)
        self.assertEqual(result['expected_http_status'], 401)
        self.db.inserts = 0
    def resume(self):
        return runner.run(self.bundle, 'anon', 'service', self.factory, self.request,
                          authorization=runner.AUTHORIZATION, existing_only=True)
    def test_existing_only_success_and_second_run_refused(self):
        self.seed_existing()
        analyses = copy.deepcopy(self.db.rows['analyses'])
        result = self.resume()
        self.assertEqual(result['status'], 'BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS')
        self.assertEqual(result['authorized_fixture_inserts'], 0)
        self.assertEqual(result['existing_fixtures_verified'], 2)
        self.assertEqual(result['adversarial_refusals'], 15)
        self.assertEqual(self.db.rows['analyses'], analyses)
        self.assertEqual(self.db.inserts, 0)
        after = copy.deepcopy(self.db.rows)
        self.assertEqual(self.resume()['status'], 'REFUSED')
        self.assertEqual(self.db.rows, after)
    def test_existing_only_rejects_missing_changed_or_foreign_fixture(self):
        self.seed_existing()
        original = copy.deepcopy(self.db.rows)
        for field in ('id', 'company_id', 'entity_id', 'analyse_json', 'status'):
            self.db.rows = copy.deepcopy(original)
            self.db.rows['analyses'][-1][field] = 'forged'
            before = copy.deepcopy(self.db.rows)
            result = self.resume()
            self.assertEqual(result['status'], 'REFUSED', field)
            self.assertEqual(result['authorized_post_attempts'], 0)
            self.assertEqual(result['seed_attempts'], 0)
            self.assertEqual(self.db.rows, before)
        self.db.rows = copy.deepcopy(original)
        self.db.rows['analyses'].pop()
        self.assertEqual(self.resume()['status'], 'REFUSED')
        self.assertEqual(self.db.inserts, 0)
