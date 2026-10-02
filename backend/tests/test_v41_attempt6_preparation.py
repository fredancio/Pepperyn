"""Attempt 6 local-only preparation and handoff falsification."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from sandbox import run_v41_attempt6 as s
from sandbox import v41_two_policy_history as h
from sandbox import v41_injected_rehearsal as a
from test_v41_two_policy_history import historical


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    original = s.ATTEMPT
    m = s.read_manifest(original)
    for name in ('manifest.json','precontrol.sql','policy-insert.sql','policy-disable.sql'):
        (tmp_path/name).write_bytes((original/name).read_bytes())
    monkeypatch.setattr(s, 'ATTEMPT', tmp_path)
    now = datetime.now(timezone.utc)
    result = json.loads(s.BASELINE.read_text())
    result.update(check_version='v41-two-policy-precontrol-1', observed_at=(now-timedelta(seconds=1)).isoformat(),
                  historical_policy_contract=h.VERSION, historical_policies=historical())
    result['structural']['rows']['policy_rows'] = 2
    result['frozen_scope'].update(m['identities'])
    captured = tmp_path/'captured.json'
    a.write_new(captured, result)
    s.attest(captured)
    return tmp_path, m, now


def test_manifest_identity_contract_frozen(prepared):
    path, m, _ = prepared
    assert s.read_manifest(path) == m
    assert not set(m['identities'].values()) & s.historical_identities()
    assert m[h.FIELD] == h.VERSION
    assert m['checkpoint_head'] == s.BASE
    assert m['ceilings'] == dict(effect_capable_requests=10,durable_rows=5,auth_logins=1)
    assert (datetime.fromisoformat(m['owner_action_deadline'])-datetime.fromisoformat(m['created_at'])).total_seconds() == 86400
    s.validate_attestation(m)
    with pytest.raises(ValueError): s.freeze(path)


@pytest.mark.parametrize('action', ['insert','disable'])
@pytest.mark.parametrize('fault', ['none','expired','terminal','wrong_policy','wrong_sql','missing','no_confirmation','pending'])
def test_acks_one_shot(prepared, action, fault):
    path, m, now = prepared
    expected = dict(schema_version='v41-owner-local-ack-1', action=action,
                    manifest_sha256=m['manifest_sha256'],policy_id=m['identities']['policy_id'],
                    sql_sha256=a.file_sha256(path/f'policy-{action}.sql'))
    deadline = m['owner_action_deadline'] if action == 'insert' else (now+timedelta(seconds=1200)).isoformat()
    marker = dict(ack=deepcopy(expected), deadline_utc=deadline)
    if fault == 'wrong_policy': marker['ack']['policy_id'] = h.POLICY_IDS[1]
    if fault == 'wrong_sql': marker['ack']['sql_sha256'] = '0'*64
    if fault != 'missing': a.write_new(path/f'owner-{action}-handoff-started.json',marker)
    if fault == 'terminal': a.write_new(path/'refused.json',{})
    if fault == 'pending': (path/f'owner-{action}-ack.pending').write_text('preserve')
    if fault == 'expired': now = datetime.fromisoformat(deadline)
    if fault == 'none':
        s.publish(action, now=lambda:now, confirmed=True)
        assert json.loads((path/f'owner-{action}-ack.json').read_text()) == expected
        with pytest.raises(ValueError): s.publish(action, now=lambda:now, confirmed=True)
    else:
        with pytest.raises((ValueError,FileNotFoundError,FileExistsError)):
            s.publish(action, now=lambda:now, confirmed=fault != 'no_confirmation')
        assert not (path/f'owner-{action}-ack.json').exists()


@pytest.mark.parametrize('fault', ['none','insert','disable','canonical_path','late','missing'])
def test_transfer_preparation_is_local_exact_and_before_start(prepared, fault):
    path, m, _ = prepared
    copies = []
    for action in ('insert','disable'):
        copied = path/f'loaded-{action}.txt'
        data = (path/f'policy-{action}.sql').read_bytes()
        if fault == action: data = data.replace(b'\n',b'\r\n')
        copied.write_bytes(data)
        copies.append(copied)
    if fault == 'canonical_path': copies[0] = path/'policy-insert.sql'
    if fault == 'late': a.write_new(path/'effects.json',{})
    if fault == 'missing':
        with pytest.raises(FileNotFoundError): s.require_transfers(m)
        return
    if fault == 'none':
        s.verify_transfers(*copies)
        s.require_transfers(m)
        with pytest.raises(FileExistsError): s.verify_transfers(*copies)
    else:
        with pytest.raises(ValueError): s.verify_transfers(*copies)
        assert not (path/'owner-transfer-ready.json').exists()


@pytest.mark.parametrize('field', ['historical_policy_contract','ceilings','policy_contract','identities'])
def test_rehashed_manifest_cannot_weaken_contract(prepared,field):
    path,m,_=prepared
    m=deepcopy(m)
    if field == h.FIELD: m[field]='latest'
    elif field == 'ceilings': m[field]['auth_logins']=2
    elif field == 'policy_contract': m[field]['egress_authorization']='OPEN'
    else: m[field]['policy_id']=h.POLICY_IDS[1]
    m.pop('manifest_sha256');m['manifest_sha256']=s.runner.digest(m)
    (path/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError):s.read_manifest(path)
