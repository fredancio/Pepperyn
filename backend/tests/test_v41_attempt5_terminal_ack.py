"""Local deadline/terminal reproduction; no new identity or remote operation."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from sandbox import run_v41_owner_ack_successor as successor
from sandbox.v41_owner_handoff import OwnerPolicyHandoff


@pytest.fixture
def disabled_handoff(tmp_path, monkeypatch):
    # Copy frozen identity, never allocate a new attempt or touch runtime evidence.
    manifest = successor.read_manifest(successor.ATTEMPT)
    sql = (successor.ATTEMPT / 'policy-disable.sql').read_bytes()
    (tmp_path / 'policy-disable.sql').write_bytes(sql)
    deadline = datetime(2026, 10, 1, 18, 24, 43, 23441, tzinfo=timezone.utc)
    expected = {
        'schema_version': 'v41-owner-local-ack-1', 'action': 'disable',
        'manifest_sha256': manifest['manifest_sha256'],
        'policy_id': manifest['identities']['policy_id'],
        'sql_sha256': successor.artifacts.file_sha256(tmp_path / 'policy-disable.sql'),
    }
    (tmp_path / 'owner-disable-handoff-started.json').write_text(json.dumps({
        'ack': expected, 'deadline_utc': deadline.isoformat()}))
    monkeypatch.setattr(successor, 'read_manifest', lambda path: manifest)
    return tmp_path, expected, deadline


@pytest.mark.parametrize('terminal', ['refused.json', 'result.json'])
def test_terminal_blocks_disable_before_any_publication(disabled_handoff, terminal):
    path, _, deadline = disabled_handoff
    (path / terminal).write_text('{"preserved":true}')
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    with pytest.raises(ValueError, match='^OWNER_HANDOFF_TERMINATED$'):
        successor.publish('disable', attempt=path,
                          now=lambda: deadline + timedelta(seconds=1), confirmed=True)
    assert {p.name: p.read_bytes() for p in path.iterdir()} == before


def test_exact_deadline_refuses_without_terminal_file(disabled_handoff):
    path, _, deadline = disabled_handoff
    with pytest.raises(ValueError, match='^OWNER_ACK_EXPIRED$'):
        successor.publish('disable', attempt=path, now=lambda: deadline, confirmed=True)
    assert not (path / 'owner-disable-ack.pending').exists()
    assert not (path / 'owner-disable-ack.json').exists()


def test_immediate_ack_then_one_independent_observation(disabled_handoff):
    path, expected, deadline = disabled_handoff
    now = deadline - timedelta(seconds=60)
    successor.publish('disable', attempt=path, now=lambda: now, confirmed=True)
    ack = json.loads((path / 'owner-disable-ack.json').read_text())
    assert ack == expected
    reads = []
    handoff = OwnerPolicyHandoff(expected, deadline=deadline,
                                freshness=lambda: None, clock=lambda: now)
    def read_once():
        reads.append(True)
        return {'enabled': False}
    def validate(row):
        assert row == {'enabled': False}
    assert handoff.observe(lambda check: ack, read_once, validate) == {'enabled': False}
    assert reads == [True]
    with pytest.raises(ValueError, match='REPLAY'):
        handoff.observe(lambda check: ack, read_once, validate)
    with pytest.raises(ValueError, match='BINDING_REFUSED'):
        successor.publish('disable', attempt=path, now=lambda: now, confirmed=True)
    assert reads == [True]


def test_missing_ack_expires_without_observation(disabled_handoff):
    _, expected, deadline = disabled_handoff
    clock = [deadline - timedelta(seconds=1)]
    reads = []
    handoff = OwnerPolicyHandoff(expected, deadline=deadline,
                                freshness=lambda: None, clock=lambda: clock[0])
    def wait(check):
        clock[0] = deadline
        check()
    with pytest.raises(ValueError, match='EXPIRED'):
        handoff.observe(wait, lambda: reads.append(True), lambda row: None)
    assert reads == []


def test_terminal_during_publication_preserves_pending(disabled_handoff):
    path, expected, deadline = disabled_handoff
    def clock():
        (path / 'refused.json').write_text('{"terminal":true}')
        return deadline - timedelta(seconds=1)
    with pytest.raises(ValueError, match='^OWNER_HANDOFF_TERMINATED$'):
        successor.publish('disable', attempt=path, now=clock, confirmed=True)
    assert json.loads((path / 'owner-disable-ack.pending').read_text()) == expected
    assert not (path / 'owner-disable-ack.json').exists()


def test_ack_without_disabled_remote_state_cannot_pass(disabled_handoff):
    path, expected, deadline = disabled_handoff
    now = deadline - timedelta(seconds=60)
    successor.publish('disable', attempt=path, now=lambda: now, confirmed=True)
    handoff = OwnerPolicyHandoff(expected, deadline=deadline,
                                freshness=lambda: None, clock=lambda: now)
    reads = []
    def read():
        reads.append(True)
        return {'enabled': True}
    def validate(row):
        if row['enabled'] is not False:
            raise ValueError('REMOTE_DISABLE_NOT_PROVEN')
    with pytest.raises(ValueError, match='REMOTE_DISABLE_NOT_PROVEN'):
        handoff.observe(lambda check: expected, read, validate)
    assert reads == [True]
