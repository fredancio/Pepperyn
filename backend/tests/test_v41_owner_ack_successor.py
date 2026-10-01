"""Local successor preparation, publication and attestation; no credentials."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from sandbox import run_v41_owner_ack_successor as successor
from sandbox import v41_injected_rehearsal as artifacts


@pytest.fixture
def prepared(tmp_path):
    attempt = tmp_path / 'isolated-successor'
    manifest = successor.freeze(attempt)
    now = datetime.fromisoformat(manifest['created_at']) + timedelta(seconds=2)
    result = json.loads(successor.BASELINE.read_text(encoding='utf-8'))
    result['check_version'] = 'v41-owner-ack-precontrol-1'
    result['observed_at'] = (now - timedelta(seconds=1)).isoformat()
    result['frozen_scope'].update(manifest['identities'])
    artifacts.write_new(attempt / 'accepted-precontrol-result.json', result)
    artifacts.write_new(attempt / 'precontrol-ready.json', {
        'schema_version': 'v41-owner-ack-attestation-1',
        'manifest_sha256': manifest['manifest_sha256'],
        'sql_sha256': artifacts.file_sha256(attempt / 'precontrol.sql'),
        'result_sha256': artifacts.file_sha256(attempt / 'accepted-precontrol-result.json'),
        'observed_at': result['observed_at'],
        'historical_snapshot_sha256': successor.runner.digest(result['historical']),
    })
    expected = {'schema_version': 'v41-owner-local-ack-1', 'action': 'insert',
        'manifest_sha256': manifest['manifest_sha256'],
        'policy_id': manifest['identities']['policy_id'],
        'sql_sha256': artifacts.file_sha256(attempt / 'policy-insert.sql')}
    artifacts.write_new(attempt / 'owner-insert-handoff-started.json', {
        'ack': expected, 'deadline_utc': manifest['owner_action_deadline']})
    return attempt, manifest, now, result, expected


def test_frozen_roundtrip_protocol_and_timestamp(prepared):
    attempt, manifest, now, _, _ = prepared
    assert successor.read_manifest(attempt) == manifest
    assert manifest['checkpoint_head'] == successor.BASE
    assert manifest['protocol_sha256'] == successor.PROTOCOL_HASH
    sql = (attempt / 'precontrol.sql').read_text()
    assert "'observed_at',statement_timestamp()" in sql
    assert 'REPEATABLE READ READ ONLY' in sql and sql.endswith('ROLLBACK;\n')
    successor.validate_attestation(manifest, attempt=attempt, now=now)
    with pytest.raises(ValueError):
        successor.freeze(attempt)


def test_atomic_publication_and_consumption(prepared, monkeypatch):
    attempt, _, now, _, expected = prepared
    rename = successor.os.rename
    observed = []
    def inspect(source, dest):
        assert not dest.exists()
        assert json.loads(source.read_text()) == expected
        observed.append(True)
        rename(source, dest)
    monkeypatch.setattr(successor.os, 'rename', inspect)
    successor.publish('insert', attempt=attempt, now=lambda: now, confirmed=True)
    assert observed == [True]
    assert json.loads((attempt / 'owner-insert-ack.json').read_text()) == expected
    assert not (attempt / 'owner-insert-ack.pending').exists()
    with pytest.raises(ValueError):
        successor.publish('insert', attempt=attempt, now=lambda: now, confirmed=True)


@pytest.mark.parametrize('mutation', ['no_confirmation','missing_marker','wrong_action','wrong_policy',
    'wrong_sql','wrong_manifest','expired','terminal','pending','unknown_field','sql_file','manifest_file'])
def test_publisher_refusals(prepared, mutation):
    attempt, manifest, now, _, _ = prepared
    path = attempt / 'owner-insert-handoff-started.json'
    marker = json.loads(path.read_text())
    if mutation == 'missing_marker':
        path.rename(attempt / 'preserved-marker.json')
    elif mutation.startswith('wrong_'):
        key = {'wrong_action':'action','wrong_policy':'policy_id','wrong_sql':'sql_sha256',
               'wrong_manifest':'manifest_sha256'}[mutation]
        marker['ack'][key] = 'substituted'
        path.write_text(json.dumps(marker))
    elif mutation == 'unknown_field':
        marker['extra'] = True
        path.write_text(json.dumps(marker))
    elif mutation == 'expired':
        now = datetime.fromisoformat(manifest['owner_action_deadline'])
    elif mutation == 'terminal':
        (attempt / 'refused.json').write_text('{}')
    elif mutation == 'pending':
        (attempt / 'owner-insert-ack.pending').write_text('preserve')
    elif mutation == 'sql_file':
        (attempt / 'policy-insert.sql').write_text('substituted')
    elif mutation == 'manifest_file':
        changed = dict(manifest, owner_action_deadline='2099-01-01T00:00:00+00:00')
        (attempt / 'manifest.json').write_text(json.dumps(changed))
    with pytest.raises((ValueError, FileNotFoundError, FileExistsError)):
        successor.publish('insert', attempt=attempt, now=lambda: now,
                          confirmed=mutation != 'no_confirmation')
    assert not (attempt / 'owner-insert-ack.json').exists()


def test_failed_rename_preserves_pending_no_fallback(prepared, monkeypatch):
    attempt, _, now, _, _ = prepared
    def fail(*args):
        raise OSError('injected local failure')
    monkeypatch.setattr(successor.os, 'rename', fail)
    with pytest.raises(OSError):
        successor.publish('insert', attempt=attempt, now=lambda: now, confirmed=True)
    assert (attempt / 'owner-insert-ack.pending').is_file()
    assert not (attempt / 'owner-insert-ack.json').exists()


def test_disable_ack_separate_from_expired_insertion(prepared):
    attempt, manifest, now, _, expected = prepared
    now = datetime.fromisoformat(manifest['owner_action_deadline']) + timedelta(seconds=1)
    ack = {**expected, 'action':'disable',
           'sql_sha256': artifacts.file_sha256(attempt / 'policy-disable.sql')}
    artifacts.write_new(attempt / 'owner-disable-handoff-started.json', {
        'ack':ack, 'deadline_utc':(now + timedelta(seconds=1200)).isoformat()})
    successor.publish('disable', attempt=attempt, now=lambda: now, confirmed=True)
    assert json.loads((attempt / 'owner-disable-ack.json').read_text()) == ack


@pytest.mark.parametrize('mutation', ['future','old','missing_time','history','identity','structure','no_auth','version'])
def test_precontrol_refuses_incomplete_or_substituted(prepared, mutation):
    _, manifest, now, result, _ = prepared
    result = deepcopy(result)
    if mutation == 'future': result['observed_at'] = (now + timedelta(seconds=1)).isoformat()
    elif mutation == 'old': result['observed_at'] = (now - timedelta(days=1)).isoformat()
    elif mutation == 'missing_time': result.pop('observed_at')
    elif mutation == 'history': result['historical']['rows'][0]['row_count'] += 1
    elif mutation == 'identity': result['frozen_scope']['analysis_id'] = result['frozen_scope']['policy_id']
    elif mutation == 'structure': result['structural']['rows']['policy_rows'] += 1
    elif mutation == 'no_auth': result['auth_performed'] = True
    else: result['check_version'] = 'unknown'
    with pytest.raises((ValueError, KeyError)):
        successor.validate_result(result, manifest, now)


def test_publisher_to_runner_one_observation_no_auth(prepared, monkeypatch):
    attempt, manifest, now, _, _ = prepared
    # Preserve the fixture's marker under another name; runner creates its own.
    (attempt / 'owner-insert-handoff-started.json').rename(attempt / 'fixture-marker.json')
    runner = successor.runner
    monkeypatch.setattr(runner, 'ATTEMPT', attempt)
    monkeypatch.setattr(runner, 'read_manifest', successor.read_manifest)
    monkeypatch.setattr(runner, 'precontrol_attestation',
        lambda m: successor.validate_attestation(m, attempt=attempt, now=now))
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now
    monkeypatch.setattr(runner, 'datetime', Clock)
    observed = []
    policies = [{
        'id': artifacts.FAILED_POLICY_ID, 'enabled': False,
        'contract_binding_sha256': artifacts.FAILED_POLICY_CONTRACT_BINDING_SHA256,
        'specification': {'policy_evidence_sha256': artifacts.FAILED_POLICY_EVIDENCE_SHA256},
    }, {
        'id': manifest['identities']['policy_id'], 'enabled': True,
        'contract_binding_sha256': runner.GENERIC_ADMISSION_CONTRACT_SHA256,
        'contract_binding': runner.CONTRACT_BINDING.model_dump(mode='json'),
        'specification': {**artifacts.specification_without_evidence(manifest),
                          'policy_evidence_sha256': 'A'*64},
    }]
    def local_wait(_):
        assert observed == []
        successor.publish('insert', attempt=attempt, now=lambda: now, confirmed=True)
    monkeypatch.setattr(runner.time, 'sleep', local_wait)
    monkeypatch.setattr(runner, 'rows', lambda *args, **kwargs: observed.append(True) or policies)
    assert runner.wait_policy(object(), manifest, enabled=True) == policies
    assert observed == [True]
