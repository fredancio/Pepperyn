"""Local readiness falsification; existing IDs only, no remote client."""
import json

import pytest

from sandbox import run_v41_injected_rehearsal as runner
from sandbox import run_v41_owner_ack_successor as successor
from sandbox import v41_injected_rehearsal as artifacts


def historical_rows():
    return [
        {'id': runner.FAILED_POLICY_ID, 'enabled': False,
         'contract_binding_sha256': runner.FAILED_POLICY_CONTRACT_BINDING_SHA256,
         'specification': {'policy_evidence_sha256': runner.FAILED_POLICY_EVIDENCE_SHA256}},
        {'id': 'f6b1732f-e558-47a0-9106-f0b3e53c3b05', 'enabled': False},
    ]


def test_two_preserved_policies_refuse_before_scope_or_auth(monkeypatch):
    calls = []
    def read(db, table, **filters):
        calls.append((table, filters))
        return historical_rows()
    monkeypatch.setattr(runner, 'rows', read)
    with pytest.raises(ValueError, match='V41_FAILED_POLICY_HISTORY_REFUSED'):
        runner.prepolicy_remote(object(), {})
    assert calls == [('generic_producer_policies_v3', {})]


def test_three_policy_observation_refuses_before_current_binding():
    with pytest.raises(ValueError, match='V41_OWNER_POLICY_SET_REFUSED'):
        runner.validate_observed_owner_policies(historical_rows() + [{}], {}, enabled=True)


def test_frozen_sql_templates_still_require_one_historical_policy():
    # Existing manifest reused only in memory to inspect templates. No allocation.
    manifest = json.loads((successor.ATTEMPT / 'manifest.json').read_text())
    assert 'public.generic_producer_policies_v3) <> 1' in artifacts.policy_insert_sql(manifest)
    assert 'public.generic_producer_policies_v3) = 1' in artifacts.precontrol_sql(runner.REPO, manifest)


def test_previous_structural_baseline_is_not_a_two_policy_baseline():
    baseline = json.loads(successor.BASELINE.read_text())
    assert baseline['structural']['rows']['policy_rows'] == 1
    assert len(historical_rows()) == 2
