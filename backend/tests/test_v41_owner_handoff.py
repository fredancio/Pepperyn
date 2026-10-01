"""Local fakes only; existing IDs, no attempt allocation or network."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest
from httpx import RemoteProtocolError

import sandbox.run_v41_injected_rehearsal as runner
from sandbox.v41_owner_handoff import OwnerPolicyHandoff


@pytest.fixture
def setup(tmp_path, monkeypatch):
    original = runner.ATTEMPT
    manifest = runner.read_manifest(original)
    for name in ('manifest.json', 'policy-insert.sql', 'policy-disable.sql'):
        (tmp_path / name).write_bytes((original / name).read_bytes())
    monkeypatch.setattr(runner, 'ATTEMPT', tmp_path)
    now = [datetime.fromisoformat(manifest['created_at']) + timedelta(seconds=1)]
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now[0]
    monkeypatch.setattr(runner, 'datetime', Clock)
    events = []
    monkeypatch.setattr(runner, 'precontrol_attestation', lambda m: events.append('freshness'))
    expected = {
        'schema_version': 'v41-owner-local-ack-1', 'action': 'insert',
        'manifest_sha256': manifest['manifest_sha256'],
        'policy_id': manifest['identities']['policy_id'],
        'sql_sha256': runner.file_sha256(tmp_path / 'policy-insert.sql'),
    }
    policies = [{
        'id': runner.FAILED_POLICY_ID, 'enabled': False,
        'contract_binding_sha256': runner.FAILED_POLICY_CONTRACT_BINDING_SHA256,
        'specification': {'policy_evidence_sha256': runner.FAILED_POLICY_EVIDENCE_SHA256},
    }, {
        'id': expected['policy_id'], 'enabled': True,
        'contract_binding': runner.CONTRACT_BINDING.model_dump(mode='json'),
        'contract_binding_sha256': runner.GENERIC_ADMISSION_CONTRACT_SHA256,
        'specification': {**runner.specification_without_evidence(manifest),
                          'policy_evidence_sha256': 'A' * 64},
    }]
    def read(*args, **kwargs):
        events.append('read')
        return deepcopy(policies)
    monkeypatch.setattr(runner, 'rows', read)
    return manifest, expected, policies, events, now, tmp_path


def ack_file(setup, data=None, action='insert'):
    _, expected, _, _, _, path = setup
    (path / f'owner-{action}-ack.json').write_text(json.dumps(expected if data is None else data))


def test_human_wait_is_local_and_single_read(setup, monkeypatch):
    manifest, _, _, events, _, _ = setup
    def waiting(_):
        assert 'read' not in events
        ack_file(setup)
    monkeypatch.setattr(runner.time, 'sleep', waiting)
    observed = runner.wait_policy(object(), manifest, enabled=True)
    assert len(observed) == 2 and events.count('read') == 1
    with pytest.raises(FileExistsError):
        runner.wait_policy(object(), manifest, enabled=True)
    assert events.count('read') == 1


@pytest.mark.parametrize('field', ['action', 'manifest_sha256', 'policy_id', 'sql_sha256', 'schema_version'])
def test_substituted_ack_never_reads(setup, field):
    manifest, expected, _, events, _, _ = setup
    ack_file(setup, {**expected, field: 'wrong'})
    with pytest.raises(ValueError, match='ACK_REFUSED'):
        runner.wait_policy(object(), manifest, enabled=True)
    assert 'read' not in events


@pytest.mark.parametrize('case', ['missing', 'invalid_json', 'expired', 'freshness', 'sql_mutation'])
def test_local_refusal_before_read(setup, monkeypatch, case):
    manifest, _, _, events, now, path = setup
    if case == 'missing':
        monkeypatch.setattr(runner.time, 'sleep', lambda _: now.__setitem__(0, datetime.fromisoformat(manifest['owner_action_deadline'])))
    elif case == 'invalid_json':
        (path / 'owner-insert-ack.json').write_text('{')
    else:
        ack_file(setup)
        if case == 'expired':
            now[0] = datetime.fromisoformat(manifest['owner_action_deadline'])
        elif case == 'freshness':
            monkeypatch.setattr(runner, 'precontrol_attestation', lambda m: (_ for _ in ()).throw(ValueError('expired freshness')))
        else:
            (path / 'policy-insert.sql').write_text('changed')
    with pytest.raises(ValueError):
        runner.wait_policy(object(), manifest, enabled=True)
    assert 'read' not in events


@pytest.mark.parametrize('case', ['absent', 'wrong_id', 'scope', 'egress', 'disabled', 'contract', 'history', 'extra'])
def test_bad_remote_observation_refused_once(setup, case):
    manifest, _, policies, events, _, _ = setup
    ack_file(setup)
    if case == 'absent':
        policies.pop()
    elif case == 'wrong_id':
        policies[1]['id'] = runner.FAILED_POLICY_ID
    elif case in ('scope', 'egress'):
        policies[1]['specification']['company_id' if case == 'scope' else 'egress_authorization'] = 'wrong'
    elif case == 'disabled':
        policies[1]['enabled'] = False
    elif case == 'contract':
        policies[1]['contract_binding_sha256'] = '0' * 64
    elif case == 'history':
        policies[0]['enabled'] = True
    else:
        policies.append(deepcopy(policies[1]))
    with pytest.raises(ValueError):
        runner.wait_policy(object(), manifest, enabled=True)
    assert events.count('read') == 1


def test_remote_protocol_error_is_not_absence_and_not_retried(setup, monkeypatch):
    manifest, _, _, events, _, _ = setup
    ack_file(setup)
    error = RemoteProtocolError('synthetic transport failure')
    def failed(*args, **kwargs):
        events.append('read')
        raise error
    monkeypatch.setattr(runner, 'rows', failed)
    with pytest.raises(RemoteProtocolError) as caught:
        runner.wait_policy(object(), manifest, enabled=True)
    assert caught.value is error and events.count('read') == 1


def test_expiry_during_single_read_refuses(setup, monkeypatch):
    manifest, _, policies, events, now, _ = setup
    ack_file(setup)
    def read(*args, **kwargs):
        events.append('read')
        now[0] = datetime.fromisoformat(manifest['owner_action_deadline'])
        return policies
    monkeypatch.setattr(runner, 'rows', read)
    with pytest.raises(ValueError, match='EXPIRED'):
        runner.wait_policy(object(), manifest, enabled=True)
    assert events.count('read') == 1


def test_missing_ack_and_replay_of_in_memory_handoff():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    h = OwnerPolicyHandoff({'ack': True}, deadline=now + timedelta(seconds=1), freshness=lambda: None, clock=lambda: now)
    reads = []
    with pytest.raises(ValueError, match='ACK_REFUSED'):
        h.observe(lambda check: None, lambda: reads.append(1), lambda r: None)
    with pytest.raises(ValueError, match='REPLAY'):
        h.observe(lambda check: {'ack': True}, lambda: reads.append(1), lambda r: None)
    assert reads == []


def test_disable_handoff_is_also_single_read(setup):
    manifest, expected, policies, events, _, path = setup
    policies[1]['enabled'] = False
    ack = {**expected, 'action': 'disable', 'sql_sha256': runner.file_sha256(path / 'policy-disable.sql')}
    ack_file(setup, ack, action='disable')
    runner.wait_policy(object(), manifest, enabled=False)
    assert events.count('read') == 1


@pytest.mark.parametrize('case', ['absent', 'wrong_policy', 'read_error', 'invalid_ack'])
def test_orchestrator_refuses_before_auth_or_effects(setup, monkeypatch, case):
    manifest, expected, policies, events, _, path = setup
    monkeypatch.setattr(runner, 'prepolicy_remote', lambda db, m: (manifest['scope'], {}))
    monkeypatch.setattr(runner, 'snapshot', lambda db: {})
    clients = []
    monkeypatch.setattr(runner, 'client', lambda key: clients.append(key) or object())
    ack_file(setup, {**expected, 'action': 'wrong'} if case == 'invalid_ack' else expected)
    if case == 'absent':
        policies.pop()
    elif case == 'wrong_policy':
        policies[1]['specification']['transport_mode'] = 'EXTERNAL'
    elif case == 'read_error':
        def fail(*args, **kwargs):
            raise RemoteProtocolError('local injected error')
        monkeypatch.setattr(runner, 'rows', fail)
    packet = {'anon': 'local-anon', 'service': 'local-service',
              'authorization': runner.AUTHORIZATION,
              'bundle': {'project_url': runner.PROJECT_URL,
                         'purpose': 'A24_TECHNICAL_ISOLATION_ONLY',
                         'accounts': [{'email': 'pepperyn-isolation-a24-a@pepperyn-test.invalid'}, {}]}}
    assert runner.execute(packet) == 1
    assert clients == ['local-service']  # No authenticated client was reached.
    journal = json.loads((path / 'effects.json').read_text())
    assert journal['auth_logins'] == 0 and journal['effects'] == []
    refused = json.loads((path / 'refused.json').read_text())
    assert refused['observation_limit'] == 'NOT_PROOF_OF_REMOTE_ABSENCE'
    assert not (path / 'result.json').exists()


def test_historical_attempt_refused_before_client_creation(setup, monkeypatch):
    _, _, _, _, _, path = setup
    (path / 'refused.json').write_text('{"historical":true}')
    clients = []
    monkeypatch.setattr(runner, 'client', lambda key: clients.append(key))
    packet = {'anon': 'local', 'service': 'local', 'authorization': runner.AUTHORIZATION,
              'bundle': {'project_url': runner.PROJECT_URL,
                         'purpose': 'A24_TECHNICAL_ISOLATION_ONLY',
                         'accounts': [{'email': 'pepperyn-isolation-a24-a@pepperyn-test.invalid'}, {}]}}
    assert runner.execute(packet) == 1
    assert clients == []
    assert (path / 'refused.json').read_text() == '{"historical":true}'
