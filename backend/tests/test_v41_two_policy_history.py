from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from sandbox import v41_two_policy_history as h
from sandbox import run_v41_injected_rehearsal as r
from sandbox import run_v41_owner_ack_successor as old
from sandbox import v41_injected_rehearsal as a


def historical():
    return [dict(h.expected_fields(i), created_at='2026-10-01T16:00:00+00:00') for i in h.POLICY_IDS]


def manifest():
    # Reuse historical IDs in memory only, never allocate an attempt or freeze.
    m = json.loads((r.RUNTIME / 'v41-injected-4/manifest.json').read_text())
    m[h.FIELD] = h.VERSION
    return m


def test_exact_history_only_and_old_refusal(monkeypatch):
    rows = historical()
    assert h.validate(rows) == sorted(rows, key=lambda p: p['id'])
    monkeypatch.setattr(r, 'rows', lambda *args, **kw: deepcopy(rows))
    with pytest.raises(ValueError, match='V41_FAILED_POLICY_HISTORY_REFUSED'):
        r.prepolicy_remote(object(), {})


@pytest.mark.parametrize('index', [0, 1])
@pytest.mark.parametrize('fault', ['missing','extra','duplicate','enabled','id','spec','evidence','binding','text','digest','column','timestamp','timestamp_mutation'])
def test_each_history_fault_refused(index, fault):
    rows = historical()
    before = deepcopy(rows)
    p = rows[index]
    if fault == 'missing': rows.pop(index)
    elif fault == 'extra': rows.append(deepcopy(p))
    elif fault == 'duplicate': p['id'] = rows[1-index]['id']
    elif fault == 'enabled': p['enabled'] = True
    elif fault == 'id': p['id'] = 'substituted'
    elif fault == 'spec': p['specification']['company_id'] = 'substituted'
    elif fault == 'evidence': p['specification']['policy_evidence_sha256'] = '0' * 64
    elif fault == 'binding': p['contract_binding']['task_version'] = 'latest'
    elif fault == 'text': p['contract_binding_text'] += ' '
    elif fault == 'digest': p['contract_binding_sha256'] = '0' * 64
    elif fault == 'column': p['extra'] = True
    elif fault == 'timestamp': p['created_at'] = 'unknown'
    else: p['created_at'] = '2026-10-01T16:00:01+00:00'
    with pytest.raises(ValueError): h.validate(rows, pinned=before)


def test_new_sql_exact_and_old_sql_unchanged():
    m = manifest()
    text = a.precontrol_sql(r.REPO, m)
    assert 'policy_rows = 2 AND admission_rows = 0' in text
    assert "'historical_policies'" in text and "'observed_at'" in text
    for identity in h.POLICY_IDS:
        assert identity in text and identity in a.policy_insert_sql(m)
    assert '>= 2' not in text
    for attempt in ('v41-injected-4','v41-injected-5'):
        folder = r.RUNTIME / attempt
        previous = json.loads((folder / 'manifest.json').read_text())
        assert a.policy_insert_sql(previous).encode() == (folder / 'policy-insert.sql').read_bytes()
        assert a.policy_disable_sql(previous).encode() == (folder / 'policy-disable.sql').read_bytes()
    m[h.FIELD] = 'latest'
    with pytest.raises(ValueError): a.precontrol_sql(r.REPO, m)


def result_fixture():
    m = manifest()
    now = datetime.fromisoformat(m['created_at']) + timedelta(seconds=3)
    result = json.loads(old.BASELINE.read_text())
    result.update(check_version='v41-two-policy-precontrol-1', observed_at=(now-timedelta(seconds=1)).isoformat(),
                  historical_policy_contract=h.VERSION, historical_policies=historical())
    result['structural']['rows']['policy_rows'] = 2
    result['frozen_scope'].update(m['identities'])
    return m, now, result


@pytest.mark.parametrize('fault', ['none','count','catalog','historical','version','scope','future','expired','enabled'])
def test_result_baseline_exact(fault):
    m, now, result = result_fixture()
    if fault == 'count': result['structural']['rows']['policy_rows'] = 3
    elif fault == 'catalog': result['structural']['functions'][0]['conformant'] = False
    elif fault == 'historical': result['historical']['rows'][0]['rows_sha256'] = '0'*64
    elif fault == 'version': result['check_version'] = 'latest'
    elif fault == 'scope': result['frozen_scope']['analysis_id'] = 'substituted'
    elif fault == 'future': result['observed_at'] = (now+timedelta(seconds=1)).isoformat()
    elif fault == 'expired': now += timedelta(days=2)
    elif fault == 'enabled': result['historical_policies'][1]['enabled'] = True
    if fault == 'none': h.validate_result(result, m, now)
    else:
        with pytest.raises(ValueError): h.validate_result(result, m, now)


def test_runner_single_observation_and_nonregression(tmp_path, monkeypatch):
    m = manifest()
    hist = historical()
    current = dict(h.expected_fields(h.POLICY_IDS[0]), id=m['identities']['policy_id'], enabled=True)
    (tmp_path/'baseline-before.json').write_text(json.dumps({'historical_policies_v3': h.validate(hist)}))
    monkeypatch.setattr(r, 'ATTEMPT', tmp_path)
    r.validate_observed_owner_policies(hist+[current], m, enabled=True)
    hist[1]['created_at'] = '2026-10-01T16:00:01+00:00'
    with pytest.raises(ValueError, match='NONREGRESSION'):
        r.validate_observed_owner_policies(hist+[current], m, enabled=True)


def test_pre_auth_exact_pinned_history_and_effect_free(monkeypatch):
    m = manifest()
    hist = historical()
    calls = []
    def rows(db, table, **filters):
        calls.append((table, filters))
        return deepcopy(hist) if table == 'generic_producer_policies_v3' and not filters else []
    monkeypatch.setattr(r, 'rows', rows)
    monkeypatch.setattr(h, 'accepted_history', lambda *args: historical())
    monkeypatch.setattr(r, 'scope', lambda db, name: m['scope'] if name.endswith('1') else {'foreign': True})
    r.prepolicy_remote(object(), m)
    baseline = r.snapshot(object(), m)
    assert baseline['historical_policies_v3'] == h.validate(hist)
    hist[1]['enabled'] = True
    with pytest.raises(ValueError): r.prepolicy_remote(object(), m)


def test_postpolicy_reuses_single_policy_observation(tmp_path, monkeypatch):
    m = manifest()
    hist = historical()
    current = dict(h.expected_fields(h.POLICY_IDS[0]), id=m['identities']['policy_id'], enabled=True)
    baseline = {table: {'count': 0, 'sha256': r.digest([])} for table in r.BASELINE_TABLES}
    baseline['historical_policies_v3'] = h.validate(hist)
    (tmp_path/'baseline-before.json').write_text(json.dumps(baseline))
    monkeypatch.setattr(r, 'ATTEMPT', tmp_path)
    def rows(db, table, **filters):
        assert table != 'generic_producer_policies_v3', 'Must reuse the single owner observation'
        return []
    monkeypatch.setattr(r, 'rows', rows)
    assert r.postpolicy_remote(object(), m, baseline, hist+[current]) == current
    hist[1]['created_at'] = '2026-10-01T16:00:01+00:00'
    with pytest.raises(ValueError): r.postpolicy_remote(object(), m, baseline, hist+[current])


def test_independent_recovery_refuses_bad_history_before_token_use(tmp_path, monkeypatch):
    m = manifest()
    monkeypatch.setattr(r, 'read_manifest', lambda _: m)
    monkeypatch.setattr(r, 'client', lambda _: object())
    monkeypatch.setattr(r, 'rows', lambda *args, **kwargs: historical())
    with pytest.raises(ValueError, match='CURRENT_SET'):
        r.independent_recovery({'anon':'local','service':'local','token':'not-used'})


@pytest.mark.parametrize('fault', ['none','result','manifest','sql','attestation','absent'])
def test_accepted_history_no_fallback(tmp_path, fault):
    m, now, result = result_fixture()
    m.pop('manifest_sha256')
    m['manifest_sha256'] = r.digest(m)
    a.write_new(tmp_path/'accepted-precontrol-result.json', result)
    (tmp_path/'precontrol.sql').write_bytes(h.sql(r.REPO, m).encode())
    report = dict(schema_version='v41-two-policy-attestation-1', manifest_sha256=m['manifest_sha256'],
                  sql_sha256=a.file_sha256(tmp_path/'precontrol.sql'), result_sha256=a.file_sha256(tmp_path/'accepted-precontrol-result.json'),
                  observed_at=result['observed_at'], historical_snapshot_sha256=r.digest(result['historical']),
                  historical_policies_sha256=r.digest(h.validate(result['historical_policies'])))
    if fault == 'result': (tmp_path/'accepted-precontrol-result.json').write_text('{}')
    elif fault == 'manifest': m['source']['sha256'] = '0'*64
    elif fault == 'sql': (tmp_path/'precontrol.sql').write_text('SELECT 1')
    elif fault == 'attestation': report['result_sha256'] = '0'*64
    if fault != 'absent': a.write_new(tmp_path/'precontrol-ready.json', report)
    if fault == 'none': assert h.accepted_history(tmp_path, m, now) == h.validate(historical())
    else:
        with pytest.raises((ValueError, KeyError, FileNotFoundError)): h.accepted_history(tmp_path, m, now)
