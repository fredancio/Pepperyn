"""Exact two-history SQL on isolated local PostgreSQL, no successor allocation."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

from sandbox import v41_two_policy_history as h
from sandbox import v41_injected_rehearsal as a
from sandbox import run_v41_injected_rehearsal as r
from test_generic_receipt_v3_postgres import v3sql  # noqa: F401
from test_v40_postgres import sql, literal, js  # noqa: F401


def test_two_history_sql_and_insert_atomicity(v3sql):
    v3sql((r.REPO/'backend/migrations/prepared_v41_validation_hardening.sql').read_text())
    s = a.SCOPE
    v3sql(f"INSERT INTO companies VALUES ({literal(s['company_id'])});"
          f"INSERT INTO profiles VALUES ({literal(s['actor_id'])},{literal(s['company_id'])});"
          f"INSERT INTO entities VALUES ({literal(s['entity_id'])},{literal(s['company_id'])});"
          f"INSERT INTO engagements VALUES ({literal(s['engagement_id'])},{literal(s['entity_id'])});")
    m = json.loads((r.RUNTIME/'v41-injected-4/manifest.json').read_text())
    # An in-memory fixture deadline, not a new attempt/manifest/runtime expiry.
    m['owner_action_deadline'] = (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    m[h.FIELD] = h.VERSION
    query = a.precontrol_sql(r.REPO, m)
    insert = a.policy_insert_sql(m)
    def observe(expected):
        report = json.loads(v3sql(query))
        assert report['status'] == expected
        assert report['write_performed'] is False and report['auth_performed'] is False
        return report
    def add(identity):
        p = h.expected_fields(identity)
        v3sql('INSERT INTO generic_producer_policies_v3(id,specification,contract_binding,contract_binding_text,contract_binding_sha256,enabled) VALUES ('
              f"{literal(identity)},{js(p['specification'])},{js(p['contract_binding'])},{literal(p['contract_binding_text'])},{literal(p['contract_binding_sha256'])},false)")
    observe('REFUSED')
    add(h.POLICY_IDS[0])
    observe('REFUSED')
    v3sql(insert, fail=True)
    add(h.POLICY_IDS[1])
    good = observe('V41_SUCCESSOR_PRECONTROL_CHECKS_PASS')
    h.validate(good['historical_policies'])
    before = good['historical_policies']
    assert good['structural']['rows'] == dict(policy_rows=2, admission_rows=0, receipt_rows=0)
    # Mutate solely inside rolled-back synthetic DB transactions. Temporarily
    # disabling the trigger permits fixture corruption, never remote repair.
    for identity in h.POLICY_IDS:
        for assignment in ("enabled=true", "specification=jsonb_set(specification,'{policy_evidence_sha256}',to_jsonb(repeat('0',64)))",
                           "specification=jsonb_set(specification,'{company_id}',to_jsonb('00000000-0000-0000-0000-000000000000'::text))",
                           "id='00000000-0000-0000-0000-000000000000'::uuid"):
            body = query.split('READ ONLY;',1)[1].rsplit('ROLLBACK;',1)[0]
            statement = ('BEGIN; ALTER TABLE generic_producer_policies_v3 DISABLE TRIGGER generic_policy_v3_guard; '
                         f'UPDATE generic_producer_policies_v3 SET {assignment} WHERE id={literal(identity)}; '
                         'ALTER TABLE generic_producer_policies_v3 ENABLE TRIGGER generic_policy_v3_guard; '
                         + body + ' ROLLBACK;')
            assert json.loads(v3sql(statement))['status'] == 'REFUSED'
    # Valid extra row is not allowed; no fallback to a larger historical set.
    v3sql(insert)
    observe('REFUSED')
    assert v3sql('SELECT count(*) FROM generic_producer_policies_v3') == '3'
    v3sql(insert, fail=True)
    after = json.loads(v3sql('SELECT jsonb_agg(to_jsonb(p) ORDER BY id) FROM generic_producer_policies_v3 p WHERE id IN (' + ','.join(literal(i) for i in h.POLICY_IDS) + ')'))
    h.validate(after, pinned=before)
    for table in ('generic_execution_admissions_v3','generic_execution_receipts_v3','analyses','governed_analysis_envelopes'):
        assert v3sql('SELECT count(*) FROM '+table) == '0'
