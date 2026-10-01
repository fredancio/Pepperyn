"""Reproduce the checkpointed adapter defect using local fake Auth/DB only."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from sandbox import run_v41_injected_rehearsal as runner
from sandbox import run_v41_owner_ack_successor as successor
from services.governed_producer_admission import AdmissionRefused
from test_governed_producer_admission import system as local_system


@pytest.fixture
def composition(local_system):
    db, profile, _ = local_system
    # Reuse existing frozen identity values in memory; no new allocation/artifact.
    manifest = json.loads((successor.ATTEMPT / 'manifest.json').read_text())
    manifest['scope'].update(company_id=str(profile.company_id),
                             entity_id=str(profile.entity_id),
                             engagement_id=str(profile.engagement_id))
    return db, manifest


class HistoricalRecordingDb:
    """Exact relevant surface before the fix: from_/rpc, no auth forwarding."""
    def __init__(self, db):
        self.db = db
        self.rpc_params = {}

    def from_(self, table):
        return self.db.from_(table)

    def rpc(self, name, params):
        self.rpc_params[name] = deepcopy(params)
        return self.db.rpc(name, params)


def test_historical_missing_auth_is_wrapped_before_any_read(composition):
    db, manifest = composition
    wrapped = HistoricalRecordingDb(db)
    before = deepcopy(db.tables)
    assert callable(db.auth.get_user)
    with pytest.raises(AttributeError, match='auth'):
        _ = wrapped.auth
    with pytest.raises(AdmissionRefused, match='^COMPOSITION_PREPARATION_REFUSED$'):
        runner.prepare_execution(wrapped, 'owner', manifest)
    assert db.tables == before and db.log == [] and wrapped.rpc_params == {}


def test_wrapper_preserves_exact_authenticated_composition(composition):
    db, manifest = composition
    expected, raw = runner.prepare_execution(db, 'owner', manifest)
    before = deepcopy(db.tables)
    calls = []
    original = db.auth.get_user
    db.auth = SimpleNamespace(get_user=lambda token: calls.append(token) or original(token))
    wrapped = runner.RecordingDb(db)
    assert wrapped.auth is db.auth
    actual, actual_raw = runner.prepare_execution(wrapped, 'owner', manifest)
    assert calls == ['owner']  # Existing-token verification, no login/refresh.
    assert actual.bindings == expected.bindings
    assert actual.source_facts == expected.source_facts
    assert actual.frozen_request == expected.frozen_request
    assert actual_raw == raw and actual.policy_id == expected.policy_id
    assert db.tables == before and wrapped.rpc_params == {}
    assert not any(entry[0] == 'rpc' for entry in db.log)


@pytest.mark.parametrize('fault', ['invalid_token', 'foreign_actor', 'entity', 'engagement', 'occupied'])
def test_forwarding_never_bypasses_authority(composition, fault):
    db, manifest = composition
    token = 'guest' if fault == 'invalid_token' else 'foreign' if fault == 'foreign_actor' else 'owner'
    if fault == 'entity':
        db.tables['entities'] = []
    elif fault == 'engagement':
        db.tables['engagements'] = []
    elif fault == 'occupied':
        db.tables.setdefault('analyses', []).append({'id': manifest['identities']['analysis_id']})
    before = deepcopy(db.tables)
    wrapped = runner.RecordingDb(db)
    with pytest.raises(AdmissionRefused, match='^COMPOSITION_PREPARATION_REFUSED$'):
        runner.prepare_execution(wrapped, token, manifest)
    assert db.tables == before and wrapped.rpc_params == {}


def test_rpc_capture_remains_exact_and_isolated():
    calls = []
    db = SimpleNamespace(rpc=lambda name, params: calls.append((name, deepcopy(params))) or 'result')
    wrapped = runner.RecordingDb(db)
    params = {'nested': {'value': 1}}
    assert wrapped.rpc('local-test-only', params) == 'result'
    params['nested']['value'] = 2
    assert wrapped.rpc_params == {'local-test-only': {'nested': {'value': 1}}}
    assert calls == [('local-test-only', {'nested': {'value': 1}})]
