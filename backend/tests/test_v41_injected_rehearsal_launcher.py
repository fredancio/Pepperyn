import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest

from sandbox.run_v41_injected_rehearsal import EffectBudget, failed_policy_exact
from sandbox.v41_injected_rehearsal import (
    FAILED_POLICY_CONTRACT_BINDING_SHA256,
    FAILED_POLICY_EVIDENCE_SHA256,
    FAILED_POLICY_ID,
    OWNER_ACTION_WINDOW_SECONDS,
    SCOPE,
    freeze_manifest,
    policy_disable_sql,
    policy_insert_sql,
    precontrol_sql,
)


REPO = Path('C:/Users/ADMIN-FRED/Documents/Codex/Pepperyn-development')
IDENTITIES = {
    'policy_id': '11111111-1111-4111-8111-111111111111',
    'request_id': '22222222-2222-4222-8222-222222222222',
    'execution_id': '33333333-3333-4333-8333-333333333333',
    'analysis_id': '44444444-4444-4444-8444-444444444444',
}
MANIFEST = {
    'identities': IDENTITIES,
    'scope': SCOPE,
    'owner_action_deadline': '2099-01-01T00:00:00+00:00',
}


def test_owner_sql_is_exactly_one_insert_then_one_disable():
    insert = policy_insert_sql(MANIFEST)
    disable = policy_disable_sql(MANIFEST)
    assert insert.count('INSERT INTO') == 1
    assert 'UPDATE ' not in insert and 'DELETE ' not in insert and 'CREATE ' not in insert
    assert disable.count('UPDATE ') == 1
    assert 'INSERT ' not in disable and 'DELETE ' not in disable and 'CREATE ' not in disable
    assert IDENTITIES['policy_id'] in insert and IDENTITIES['policy_id'] in disable
    assert "enabled=false" in disable and "AND enabled=true" in disable
    assert "clock_timestamp()" in insert
    assert "V41_OWNER_ACTION_DEADLINE_EXPIRED" in insert
    assert FAILED_POLICY_ID in insert
    assert FAILED_POLICY_EVIDENCE_SHA256 in insert
    assert FAILED_POLICY_CONTRACT_BINDING_SHA256 in insert
    assert "count(*) FROM public.generic_producer_policies_v3) <> 1" in insert


def test_precontrol_is_read_only_and_contains_no_patch_markers():
    sql = precontrol_sql(REPO, MANIFEST)
    assert '\n+  ' not in sql
    assert sql.count('BEGIN TRANSACTION READ ONLY') >= 3
    assert 'V41_INJECTED_SUCCESSOR_FROZEN_SCOPE_PRECONTROL_PASS' in sql
    assert FAILED_POLICY_ID in sql
    assert FAILED_POLICY_EVIDENCE_SHA256 in sql
    for value in IDENTITIES.values():
        UUID(value)
        assert value in sql


def test_effect_budget_refuses_second_auth_and_eleventh_effect(tmp_path):
    journal = tmp_path / 'effects.json'
    budget = EffectBudget(journal)
    budget.run('AUTH_LOGIN', lambda: True, auth=True)
    with pytest.raises(ValueError, match='V41_SECOND_AUTH_REFUSED'):
        budget.run('SECOND_AUTH', lambda: True, auth=True)
    for index in range(2, 11):
        budget.run(f'EFFECT_{index}', lambda: True)
    with pytest.raises(ValueError, match='V41_EFFECT_CEILING_REFUSED'):
        budget.run('EFFECT_11', lambda: True)
    persisted = json.loads(journal.read_text(encoding='utf-8'))
    assert persisted['auth_logins'] == 1
    assert len(persisted['effects']) == 10


def test_expected_refusal_is_recorded_without_acceptance(tmp_path):
    budget = EffectBudget(tmp_path / 'effects.json')
    assert budget.run('REFUSAL', lambda: (_ for _ in ()).throw(RuntimeError()), refusal=True) is None
    assert budget.effects[0]['outcome'] == 'REFUSED_AS_REQUIRED'
    with pytest.raises(ValueError, match='V41_EXPECTED_REFUSAL_ACCEPTED'):
        budget.run('BAD_REFUSAL', lambda: True, refusal=True)


def test_failed_policy_history_is_exact_and_never_enabled():
    row = {
        'id': FAILED_POLICY_ID,
        'enabled': False,
        'contract_binding_sha256': FAILED_POLICY_CONTRACT_BINDING_SHA256,
        'specification': {
            'policy_evidence_sha256': FAILED_POLICY_EVIDENCE_SHA256,
        },
    }
    assert failed_policy_exact(row)
    assert not failed_policy_exact({**row, 'enabled': True})
    assert not failed_policy_exact({
        **row,
        'specification': {'policy_evidence_sha256': '0' * 64},
    })


def test_effect_order_can_record_policy_before_single_auth(tmp_path):
    budget = EffectBudget(tmp_path / 'effects.json')
    budget.owner_observed('POLICY_INSERT')
    budget.run('AUTH_LOGIN', lambda: True, auth=True)
    assert [entry['name'] for entry in budget.effects] == [
        'POLICY_INSERT', 'AUTH_LOGIN',
    ]
    assert budget.auth_logins == 1


def test_successor_manifest_freezes_new_ids_deadline_and_failed_history(tmp_path):
    frozen = freeze_manifest(REPO, tmp_path / 'attempt')
    created = datetime.fromisoformat(frozen['created_at'])
    deadline = datetime.fromisoformat(frozen['owner_action_deadline'])
    assert (deadline - created).total_seconds() == OWNER_ACTION_WINDOW_SECONDS
    assert frozen['predecessor']['policy_id'] == FAILED_POLICY_ID
    assert frozen['predecessor']['required_enabled'] is False
    assert FAILED_POLICY_ID not in frozen['identities'].values()
    assert len(set(frozen['identities'].values())) == 4
    generated = (tmp_path / 'attempt' / 'policy-insert.sql').read_text(encoding='utf-8')
    assert frozen['owner_action_deadline'] in generated
    assert 'V41_OWNER_ACTION_DEADLINE_EXPIRED' in generated
