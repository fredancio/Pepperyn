"""Execute the complete generated read-only precontrol on isolated PostgreSQL."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sandbox.v41_injected_rehearsal import precontrol_sql, SCOPE
from test_v41_injected_successor_postgres import manifest
from test_generic_receipt_v3_postgres import v3sql  # noqa: F401
from test_v40_postgres import sql, literal  # noqa: F401
from test_v41_injected_successor_postgres import (
    FAILED_POLICY_ID, FAILED_POLICY_EVIDENCE_SHA256,
    FAILED_POLICY_CONTRACT_BINDING_SHA256, specification_without_evidence,
    CONTRACT_BINDING, canonical_bytes, js,
)


def test_complete_precontrol_single_result_and_adversarial_states(v3sql):
    repo = Path(__file__).resolve().parents[2]
    v3sql((repo / 'backend/migrations/prepared_v41_validation_hardening.sql').read_text(encoding='utf-8'))
    scope = SCOPE
    v3sql(f"INSERT INTO companies VALUES ({literal(scope['company_id'])});"
          f"INSERT INTO profiles VALUES ({literal(scope['actor_id'])},{literal(scope['company_id'])});"
          f"INSERT INTO entities VALUES ({literal(scope['entity_id'])},{literal(scope['company_id'])});"
          f"INSERT INTO engagements VALUES ({literal(scope['engagement_id'])},{literal(scope['entity_id'])});")
    frozen = manifest(datetime.now(timezone.utc) + timedelta(hours=24))
    query = precontrol_sql(repo, frozen)

    def observe(expected):
        # json.loads also rejects multiple top-level result objects.
        report = json.loads(v3sql(query))
        assert report['status'] == expected
        assert report['write_performed'] is False
        assert report['auth_performed'] is False
        assert report['historical_comparison_required'] is True
        assert len(report['structural']['functions']) == 5
        assert len(report['historical']['rows']) == 6
        return report

    observe('REFUSED')  # Missing historical policy.
    spec = specification_without_evidence(frozen)
    spec['policy_evidence_sha256'] = FAILED_POLICY_EVIDENCE_SHA256
    binding = CONTRACT_BINDING.model_dump(mode='json')

    def insert_policy(identity, evidence):
        copied = dict(spec, policy_evidence_sha256=evidence)
        v3sql('INSERT INTO generic_producer_policies_v3('
              'id,specification,contract_binding,contract_binding_text,contract_binding_sha256,enabled) VALUES ('
              f'{literal(identity)},{js(copied)},{js(binding)},'
              f'{literal(canonical_bytes(binding).decode())},'
              f'{literal(FAILED_POLICY_CONTRACT_BINDING_SHA256)},true)')

    insert_policy(FAILED_POLICY_ID, FAILED_POLICY_EVIDENCE_SHA256)
    observe('REFUSED')  # Active historical policy.
    v3sql('UPDATE generic_producer_policies_v3 SET enabled=false WHERE id=' + literal(FAILED_POLICY_ID))
    before = v3sql('SELECT row_to_json(t) FROM generic_producer_policies_v3 t')
    good = observe('V41_SUCCESSOR_PRECONTROL_CHECKS_PASS')
    assert good['structural']['status'] == 'PPR067_HARDENING_STRUCTURAL_POSTFLIGHT_PASS'
    for expected_hash in (FAILED_POLICY_EVIDENCE_SHA256, FAILED_POLICY_CONTRACT_BINDING_SHA256):
        mismatched = json.loads(v3sql(query.replace(expected_hash, '0' * 64)))
        assert mismatched['status'] == 'REFUSED'
        assert mismatched['frozen_scope']['status'] == 'REFUSED'
    v3sql("ALTER FUNCTION claim_generic_execution_v3(uuid,uuid,text) SET search_path=public")
    observe('REFUSED')
    v3sql("ALTER FUNCTION claim_generic_execution_v3(uuid,uuid,text) SET search_path=pg_catalog,public")
    observe('V41_SUCCESSOR_PRECONTROL_CHECKS_PASS')
    assert before == v3sql('SELECT row_to_json(t) FROM generic_producer_policies_v3 t')
    for table in ('generic_execution_admissions_v3','generic_execution_receipts_v3','analyses','governed_analysis_envelopes'):
        assert v3sql('SELECT count(*) FROM ' + table) == '0'

    v3sql(f"UPDATE profiles SET company_id=(SELECT id FROM companies WHERE id <> {literal(scope['company_id'])} LIMIT 1) WHERE id={literal(scope['actor_id'])}")
    observe('REFUSED')  # Actor binding drift.
    v3sql(f"UPDATE profiles SET company_id={literal(scope['company_id'])} WHERE id={literal(scope['actor_id'])}")
    v3sql('GRANT SELECT ON generic_execution_receipts_v3 TO authenticated')
    observe('REFUSED')  # Permission drift, even with exact historical policy.
    v3sql('REVOKE SELECT ON generic_execution_receipts_v3 FROM authenticated')
    observe('V41_SUCCESSOR_PRECONTROL_CHECKS_PASS')
    insert_policy(frozen['identities']['policy_id'], FAILED_POLICY_EVIDENCE_SHA256)
    observe('REFUSED')  # Additional policy and occupied successor identity.
