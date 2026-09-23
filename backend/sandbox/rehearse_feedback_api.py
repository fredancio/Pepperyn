"""A28 authorized synthetic rehearsal. No retries, deletion or provider transport.

Service authority: scope/snapshot reads and exactly two absent legacy fixture inserts.
All feedback probes: actual user bearer sessions only. Stops on any unexpected state.
"""
import json
import logging
import os
import warnings
from uuid import uuid5, NAMESPACE_URL
from sandbox.inspect_populated_history_scope import inspect
from sandbox.seed_isolation_history import fixture_id as a26_id
from sandbox.verify_feedback_privileges import live_request, verify as direct_denials, URL
from services.decision_memory_service import extract_recommendations

API = 'http://127.0.0.1:8000'
AUTHORIZATION = 'A28_TWO_LEGACY_FIXTURES_UNSURE_AND_PATTERNS_ONLY'
TABLES = ('analyses', 'governed_analysis_envelopes', 'decision_feedback', 'user_patterns', 'decision_arcs')


def run(bundle, anon, service, factory, request, *, authorization, existing_only=False):
    stage = 'AUTHORIZATION'
    seed_attempts = seed_ack = positive_attempts = positive_ack = negative_attempts = 0
    observed_http_status = expected_http_status = None
    try:
        def check(value):
            if not value:
                raise ValueError('REFUSED')
        check(authorization == AUTHORIZATION)
        stage = 'BACKEND_REVISION'
        code, health = request('GET', API + '/health', {}, None)
        check(code == 200 and health.get('environment') == 'development')
        code, schema = request('GET', API + '/openapi.json', {}, None)
        check(code == 200 and schema['paths']['/api/decision-feedback']['post'].get(
            'x-pepperyn-write-authority') == 'owned-persisted-recommendation-v1')
        stage = 'V37_USER_SESSION_DENIALS'
        check(direct_denials(bundle, anon, factory, request)['status'] == 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS')
        stage = 'EXACT_TECHNICAL_SCOPES'
        scopes = []
        check(inspect(bundle, service, anon, factory, verified_scopes=scopes)['status'] == 'A26_SCOPES_INSPECTED')
        check(len(scopes) == 2)
        db = factory(URL, service)
        def snapshot():
            nonlocal stage
            previous_stage = stage
            result = []
            for account_index, (_, company, _, _) in enumerate(scopes, 1):
                state = {}
                for table in TABLES:
                    stage = f'SNAPSHOT_USER_{account_index}_{table.upper()}'
                    rows = db.table(table).select('*').eq('company_id', company).limit(5).execute().data
                    check(isinstance(rows, list) and len(rows) < 5
                          and all(r.get('company_id') == company for r in rows))
                    state[table] = sorted(rows, key=lambda r: json.dumps(r, sort_keys=True))
                result.append(state)
            stage = previous_stage
            return result
        stage = 'BASELINE_EXISTING_A28_NO_FEEDBACK' if existing_only else 'BASELINE_NO_A28_OR_FEEDBACK'
        before = snapshot()
        prepared = []
        headers = []
        for i, scope in enumerate(scopes):
            uid, company, entity, engagement = scope
            state = before[i]
            check(len(state['analyses']) == (2 if existing_only else 1)
                  and len(state['governed_analysis_envelopes']) == 1)
            a26 = [r for r in state['analyses'] if r['id'] == a26_id(scope)]
            check(len(a26) == 1 and a26[0]['entity_id'] == entity
                  and a26[0].get('contexte_utilisateur') == 'A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1')
            envelope = state['governed_analysis_envelopes'][0]
            check(envelope['analysis_id'] == a26_id(scope) and envelope['entity_id'] == entity
                  and envelope['engagement_id'] == engagement)
            check(state['decision_feedback'] == [] and state['user_patterns'] == [] and state['decision_arcs'] == [])
            aid = str(uuid5(NAMESPACE_URL, 'pepperyn:integration:a28:v1:' + ':'.join(scope)))
            row = dict(id=aid, company_id=company, entity_id=entity,
                       fichier_nom=f'A28_SYNTHETIC_LEGACY_{i+1}.xlsx', fichier_type='xlsx',
                       type_document='AUTRE', contexte_utilisateur='A28_TECHNICAL_LEGACY_FIXTURE_V1',
                       mode='complete', status='completed', score_confiance=0,
                       analyse_json={'recommandations': [{'action': f'Vérifier le scénario synthétique A28 {i+1}.'}]},
                       tokens_input=0, cout_estime_euros=0, duree_traitement_ms=0, chat_count=0)
            prepared.append(row)
            if existing_only:
                stored = [r for r in state['analyses'] if r['id'] == row['id']]
                check(len(stored) == 1 and all(stored[0].get(k) == v for k, v in row.items()))
            client = factory(URL, anon)
            account = bundle['accounts'][i]
            session = client.auth.sign_in_with_password({'email': account['email'], 'password': account['password']}).session
            check(str(client.auth.get_user(session.access_token).user.id) == uid)
            headers.append({'Authorization': 'Bearer ' + session.access_token, 'Content-Type': 'application/json'})
        stage = 'PREWRITE_RECHECK'
        check(snapshot() == before)
        for i, row in enumerate([] if existing_only else prepared):
            stage = f'SEED_{i+1}'
            seed_attempts += 1
            db.table('analyses').insert(row).execute()
            seed_ack += 1
        stage = 'SEED_REREAD'
        baseline = snapshot()
        for i, row in enumerate(prepared):
            check(len(baseline[i]['analyses']) == 2)
            stored = [r for r in baseline[i]['analyses'] if r['id'] == row['id']]
            check(len(stored) == 1 and all(stored[0].get(k) == v for k, v in row.items()))
            check([r for r in baseline[i]['analyses'] if r['id'] != row['id']] ==
                  [r for r in before[i]['analyses'] if r['id'] != row['id']])
            check(all(baseline[i][t] == before[i][t] for t in TABLES if t != 'analyses'))
        check(not existing_only or baseline == before)
        bodies = []
        for row in prepared:
            rec = extract_recommendations(row['analyse_json'], row['id'])[0]
            bodies.append(dict(report_id=row['id'], recommendation_id=rec['id'], recommendation_text=rec['text'],
                               recommendation_source=rec['source'], status='unsure', comment='A28 synthetic authorized feedback'))
        def refuse(body, auth, expected, expected_state):
            nonlocal negative_attempts, observed_http_status, expected_http_status
            negative_attempts += 1
            expected_http_status = expected
            observed_http_status = None
            code, _ = request('POST', API + '/api/decision-feedback', auth, body)
            observed_http_status = code
            check(code == expected and snapshot() == expected_state)
        stage = 'ANONYMOUS_DENIAL'
        refuse(bodies[0], {'Content-Type': 'application/json'}, 401, baseline)
        for i in range(2):
            stage = f'USER_{i+1}_FOREIGN_BEFORE'
            refuse(bodies[1-i], headers[i], 404, baseline)
            stage = f'USER_{i+1}_GOVERNED_BYPASS'
            refuse(dict(bodies[i], report_id=a26_id(scopes[i])), headers[i], 409, baseline)
            refuse(dict(bodies[i], report_id=a26_id(scopes[1-i])), headers[i], 404, baseline)
            for field in ('recommendation_id', 'recommendation_text', 'recommendation_source'):
                stage = f'USER_{i+1}_FORGED_{field.upper()}'
                refuse(dict(bodies[i], **{field: 'A28_FORGED'}), headers[i], 409, baseline)
        for i in range(2):
            stage = f'USER_{i+1}_AUTHORIZED_UNSURE'
            positive_attempts += 1
            expected_http_status = 200
            observed_http_status = None
            code, result = request('POST', API + '/api/decision-feedback', headers[i],
                                   dict(bodies[i], company_id=scopes[1-i][1]))
            observed_http_status = code
            check(code == 200 and result.get('success') is True and result.get('arc_created') is False)
            positive_ack += 1
            after = snapshot()
            check(after[1-i] == baseline[1-i])
            check(all(after[i][t] == baseline[i][t] for t in ('analyses', 'governed_analysis_envelopes', 'decision_arcs')))
            feedback = after[i]['decision_feedback']
            check(len(feedback) == 1 and all(feedback[0].get(k) == v for k, v in bodies[i].items())
                  and feedback[0]['company_id'] == scopes[i][1] and feedback[0].get('decision_kind') is None)
            patterns = after[i]['user_patterns']
            check(len(patterns) == 1 and patterns[0].get('total_feedback_count') == 1
                  and patterns[0].get('execution_rate') is None)
            baseline = after
        for i in range(2):
            stage = f'USER_{i+1}_FOREIGN_AFTER'
            refuse(bodies[1-i], headers[i], 404, baseline)
        return dict(status='BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS',
                    existing_fixtures_verified=2 if existing_only else 0,
                    continuation_existing_only=existing_only,
                    authorized_fixture_inserts=seed_ack, authorized_unsure_writes=positive_ack,
                    authorized_pattern_rows_verified=2, adversarial_refusals=negative_attempts,
                    a26_pairs_unchanged=True, arcs_created=False, business_write_performed=True,
                    api_write_isolation_proven=True, proof_scope='A28_TWO_LEGACY_UNSURE_API_WRITES_ONLY',
                    write_isolation_proven=False, analysis_export_isolation_proven=False,
                    global_isolation_proven=False, production_proof=False, external_provider_used=False, real_data_used=False)
    except Exception:
        return dict(status='REFUSED', stage=stage, seed_attempts=seed_attempts, seed_acknowledged=seed_ack,
                    observed_http_status=observed_http_status, expected_http_status=expected_http_status,
                    authorized_post_attempts=positive_attempts, authorized_post_acknowledged=positive_ack,
                    negative_post_attempts=negative_attempts,
                    remote_partial_write_possible=bool(seed_attempts or positive_attempts or negative_attempts),
                    automatic_retry_permitted=False, api_write_isolation_proven=False)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings('ignore')
    try:
        from supabase import create_client
        if os.environ.get('PEPPERYN_A28_MODE') != 'EXISTING_ONLY':
            raise ValueError('EXISTING_ONLY_REQUIRED')
        result = run(json.loads(os.environ['PEPPERYN_ISOLATION_BOOTSTRAP']),
                     os.environ['PEPPERYN_ISOLATION_ANON_KEY'], os.environ['PEPPERYN_ISOLATION_SERVICE_KEY'],
                     create_client, live_request, authorization=os.environ.get('PEPPERYN_A28_AUTHORIZATION'),
                     existing_only=True)
    except Exception:
        result = dict(status='REFUSED', stage='LOCAL_INPUT_OR_IMPORT', automatic_retry_permitted=False)
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS' else 1)
