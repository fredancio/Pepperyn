import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest

from sandbox import run_v40_rehearsal as runner
from sandbox.v40_rehearsal_budget import Budget


def catalog(**changes):
    value = dict(version='v40-rehearsal-operator-readiness-1', project=runner.URL,
                 definition_status='BOUNDED_DEFINITION_CONFORMANCE_PASS', structure_verified=True,
                 observed_at=datetime.now(timezone.utc).isoformat(), effect_ceiling=19, row_ceiling=7)
    value.update(changes)
    return value


@pytest.mark.parametrize('changes', [dict(project='https://foreign.invalid'),
    dict(effect_ceiling=20), dict(row_ceiling=8), dict(structure_verified=False),
    dict(definition_status='UNKNOWN'), dict(extra=True),
    dict(observed_at=(datetime.now(timezone.utc)-timedelta(minutes=4)).isoformat()),
    dict(observed_at=(datetime.now(timezone.utc)+timedelta(minutes=4)).isoformat()),
    dict(observed_at='2026-01-01T00:00:00')])
def test_catalog_refuses_without_effect(tmp_path, changes):
    runner.write_new(tmp_path/'catalog-ready.json', catalog(**changes))
    with pytest.raises(Exception): runner.wait_catalog(tmp_path, timeout=0)


def test_current_catalog_and_missing_timeout(tmp_path):
    with pytest.raises(Exception): runner.wait_catalog(tmp_path, timeout=0)
    runner.write_new(tmp_path/'catalog-ready.json', catalog())
    runner.wait_catalog(tmp_path)
    with pytest.raises(FileExistsError): runner.write_new(tmp_path/'catalog-ready.json', catalog())


def test_owner_slot_burned_before_ticket_and_no_retry(tmp_path, monkeypatch):
    budget=Budget.create(tmp_path/'budget.sqlite');budget.take('AUTH_ONCE')
    monkeypatch.setattr(runner, 'owner_sql', lambda *args: 'SELECT controlled_test;')
    class Reader:
        def rows(self, table):
            assert budget.report()['slots']==['AUTH_ONCE','POLICY_INSERT']
            ticket=json.loads((tmp_path/'policy_insert.json').read_text())
            assert ticket['automatic_retry_permitted'] is False
            assert ticket['sql_sha256']==sha256(ticket['sql'].encode()).hexdigest().upper()
            return [dict(id='wrong-policy')]
    owner=runner.OwnerActions(tmp_path,budget,Reader())
    manifest=dict(policy_id='expected', profile={}, contract_sha256='test')
    with pytest.raises(Exception): owner('POLICY_INSERT',manifest)
    original=(tmp_path/'policy_insert.json').read_bytes()
    with pytest.raises(Exception): owner('POLICY_INSERT',manifest)
    assert (tmp_path/'policy_insert.json').read_bytes()==original
    assert budget.report()['effect_attempts']==2


def test_no_credential_input_before_local_check_and_existing_attempt_refused(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(runner,'ATTEMPT',tmp_path)
    monkeypatch.setattr(runner.sys,'argv',['runner'])
    assert runner.main()==1
    result=json.loads(capsys.readouterr().out)
    assert result['stage']=='LOCAL_CHECK'
    assert list(tmp_path.iterdir())==[]
