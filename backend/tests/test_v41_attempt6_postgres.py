"""Execute exact frozen Attempt 6 SQL only in the isolated synthetic database."""
import json

from sandbox import run_v41_attempt6 as s
from sandbox import v41_two_policy_history as h
from sandbox import v41_injected_rehearsal as a
from test_generic_receipt_v3_postgres import v3sql  # noqa: F401
from test_v40_postgres import sql, literal, js  # noqa: F401


def test_exact_frozen_attempt6_sql(v3sql):
    m = s.read_manifest(s.ATTEMPT)
    v3sql((s.runner.REPO/'backend/migrations/prepared_v41_validation_hardening.sql').read_text())
    scope = a.SCOPE
    v3sql(f"INSERT INTO companies VALUES ({literal(scope['company_id'])});"
          f"INSERT INTO profiles VALUES ({literal(scope['actor_id'])},{literal(scope['company_id'])});"
          f"INSERT INTO entities VALUES ({literal(scope['entity_id'])},{literal(scope['company_id'])});"
          f"INSERT INTO engagements VALUES ({literal(scope['engagement_id'])},{literal(scope['entity_id'])});")
    for identity in h.POLICY_IDS:
        p = h.expected_fields(identity)
        v3sql('INSERT INTO generic_producer_policies_v3(id,specification,contract_binding,contract_binding_text,contract_binding_sha256,enabled) VALUES ('
              f"{literal(identity)},{js(p['specification'])},{js(p['contract_binding'])},{literal(p['contract_binding_text'])},{literal(p['contract_binding_sha256'])},false)")
    pre = (s.ATTEMPT/'precontrol.sql').read_text()
    report = json.loads(v3sql(pre))
    assert report['status'] == 'V41_SUCCESSOR_PRECONTROL_CHECKS_PASS'
    before = h.validate(report['historical_policies'])
    insert = (s.ATTEMPT/'policy-insert.sql').read_text()
    disable = (s.ATTEMPT/'policy-disable.sql').read_text()
    v3sql(insert)
    v3sql(insert, fail=True)
    assert json.loads(v3sql(pre))['status'] == 'REFUSED'
    v3sql(disable)
    v3sql(disable, fail=True)
    assert v3sql('SELECT enabled FROM generic_producer_policies_v3 WHERE id='+literal(m['identities']['policy_id'])) == 'f'
    after = json.loads(v3sql('SELECT jsonb_agg(to_jsonb(p) ORDER BY id) FROM generic_producer_policies_v3 p WHERE id IN ('+','.join(literal(i) for i in h.POLICY_IDS)+')'))
    h.validate(after, pinned=before)
    for table in ('generic_execution_admissions_v3','generic_execution_receipts_v3','analyses','governed_analysis_envelopes'):
        assert v3sql('SELECT count(*) FROM '+table) == '0'
