"""A27: real user JWT denial probes, structurally unable to mutate business rows.

POST includes NULL in two NOT NULL columns. PATCH/DELETE require NULL primary key.
Only exact PostgreSQL permission denial qualifies; validation errors are failures.
This does not exercise Pepperyn's API or prove cross-report application ownership.
"""
import json
import logging
import os
import warnings
from uuid import UUID
from urllib.request import Request, urlopen
from urllib.error import HTTPError

URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
EMAILS = [f'pepperyn-isolation-a24-{s}@pepperyn-test.invalid' for s in ('a', 'b')]


def live_request(method, url, headers, payload):
    request = Request(url, data=None if payload is None else json.dumps(payload).encode(),
                      headers=headers, method=method)
    # No automatic retry. Never print exception text or response bodies.
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read() or b'{}')
    except HTTPError as error:
        return error.code, json.loads(error.read() or b'{}')


def verify(bundle, anon_key, factory, request):
    stage = 'INPUT'
    attempts = 0
    try:
        def require(value):
            if not value:
                raise ValueError('REFUSED')
        require(bundle['project_url'] == URL and bundle['purpose'] == 'A24_TECHNICAL_ISOLATION_ONLY'
                and [a['email'] for a in bundle['accounts']] == EMAILS and bool(anon_key))
        scopes = []
        for i, account in enumerate(bundle['accounts'], 1):
            stage = f'USER_{i}_AUTHORITY'
            client = factory(URL, anon_key)
            session = client.auth.sign_in_with_password(account).session
            user = client.auth.get_user(session.access_token).user
            uid = str(UUID(str(user.id)))
            require(user.email == EMAILS[i-1] and user.role == 'authenticated')
            profiles = client.table('profiles').select('id,company_id').eq('id', uid).limit(2).execute().data
            require(len(profiles) == 1 and profiles[0]['id'] == uid)
            company = str(UUID(profiles[0]['company_id']))
            companies = client.table('companies').select('id,admin_user_id,name').eq('id', company).limit(2).execute().data
            require(len(companies) == 1 and companies[0]['id'] == company
                    and companies[0]['admin_user_id'] == uid
                    and companies[0]['name'] == f'Pepperyn A24 Isolation Synthetic {i}')
            scopes.append((uid, company, session.access_token))
        stage = 'DISTINCT_SCOPES'
        require(all(len({s[k] for s in scopes}) == 2 for k in range(2)))
        for i, (_, _, token) in enumerate(scopes, 1):
            headers = {'apikey': anon_key, 'Authorization': f'Bearer {token}',
                       'Content-Type': 'application/json'}
            for method, suffix, payload in (
                ('POST', '', {'company_id': None, 'report_id': None,
                              'recommendation_id': 'A27_NO_ROW_PROBE',
                              'recommendation_text': 'Synthetic no-row probe', 'status': 'unsure'}),
                ('PATCH', '?id=is.null', {'comment': 'A27_NO_ROW_PROBE'}),
                ('DELETE', '?id=is.null', None),
            ):
                stage = f'USER_{i}_{method}_DENIAL'
                attempts += 1
                code, data = request(method, URL + '/rest/v1/decision_feedback' + suffix, headers, payload)
                require(code == 403 and isinstance(data, dict) and data.get('code') == '42501'
                        and data.get('message') == 'permission denied for table decision_feedback')
        return {'status': 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS', 'denied_operations': attempts,
                'authority': 'TWO_REAL_AUTHENTICATED_USER_SESSIONS', 'business_write_performed': False,
                'proof_scope': 'DECISION_FEEDBACK_DIRECT_TABLE_PRIVILEGES_ONLY',
                'api_write_isolation_proven': False, 'write_isolation_proven': False,
                'analysis_export_isolation_proven': False, 'global_isolation_proven': False,
                'production_proof': False, 'external_provider_used': False, 'real_data_used': False}
    except Exception:
        return {'status': 'REFUSED', 'stage': stage, 'attempted_operations': attempts,
                'automatic_retry_permitted': False, 'write_isolation_proven': False}


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings('ignore')
    try:
        from supabase import create_client
        result = verify(json.loads(os.environ['PEPPERYN_ISOLATION_BOOTSTRAP']),
                        os.environ['PEPPERYN_ISOLATION_ANON_KEY'], create_client, live_request)
    except Exception:
        result = {'status': 'REFUSED', 'stage': 'LOCAL_INPUT_OR_IMPORT'}
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS' else 1)
