"""No network: falsify the explicitly qualified Founder-approved time bound."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
import sandbox.run_v41_injected_rehearsal as runner
from sandbox.v41_injected_rehearsal import read_manifest


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    original = runner.ATTEMPT
    manifest = read_manifest(original)
    for name in ('manifest.json', 'precontrol.sql'):
        (tmp_path / name).write_bytes((original / name).read_bytes())
    fixture = Path(__file__).parent / 'fixtures/v41_attempt4_accepted_precontrol.json'
    (tmp_path / 'accepted-precontrol-result.json').write_bytes(fixture.read_bytes())
    result = json.loads(fixture.read_text())
    report = {
        'schema_version': 'v41-injected-successor-precontrol-attestation-2',
        'project_url': runner.PROJECT_URL,
        'sql_sha256': runner.file_sha256(tmp_path / 'precontrol.sql'),
        'structural_status': result['structural']['status'],
        'historical_status': result['historical']['status'],
        'frozen_scope_status': result['frozen_scope']['status'],
        'historical_snapshot_sha256': runner.digest(result['historical']),
        'write_performed': False, 'auth_performed': False,
        'freshness_evidence': {
            'kind': 'PROVEN_CONSERVATIVE_LOWER_BOUND',
            'lower_bound_utc': '2026-10-01T07:24:01Z',
            'qualification': 'NOT_EXECUTION_OR_OBSERVATION_TIME',
            'authority': 'FOUNDER_ATTEMPT4_CONSERVATIVE_BOUND_2026_10_01',
            'provenance': 'FROZEN_IDENTITIES_PRESENT_IN_ACCEPTED_PRECONTROL_RESULT',
            'manifest_sha256': manifest['manifest_sha256'],
            'result_file': 'accepted-precontrol-result.json',
            'result_sha256': runner.file_sha256(fixture),
        },
    }
    monkeypatch.setattr(runner, 'ATTEMPT', tmp_path)
    return manifest, report, tmp_path


@pytest.mark.parametrize('stamp,accepted', [
    ('2026-10-01T07:24:01+00:00', False),  # Before actual manifest creation.
    ('2026-10-01T07:24:02+00:00', True),
    ('2026-10-02T07:24:00.999999+00:00', True),
    ('2026-10-02T07:24:01+00:00', False),  # Exactly 24 hours: refused.
    ('2026-10-02T07:24:01.5+00:00', False),  # Still before original deadline.
    ('2026-10-02T07:24:01.869336+00:00', False),
    ('2026-10-03T07:24:00+00:00', False),
    ('2026-10-01T08:00:00', False),  # No timezone.
])
def test_strict_window(prepared, stamp, accepted):
    manifest, report, _ = prepared
    if accepted:
        runner.validate_conservative_freshness(report, manifest, datetime.fromisoformat(stamp))
    else:
        with pytest.raises(ValueError):
            runner.validate_conservative_freshness(report, manifest, datetime.fromisoformat(stamp))


@pytest.mark.parametrize('field', [
    'kind', 'lower_bound_utc', 'qualification', 'authority', 'provenance',
    'manifest_sha256', 'result_file', 'result_sha256',
])
def test_qualification_cannot_be_substituted(prepared, field):
    manifest, report, _ = prepared
    report['freshness_evidence'][field] = 'substituted'
    with pytest.raises(ValueError):
        runner.validate_conservative_freshness(report, manifest, datetime(2026, 10, 1, 8, tzinfo=timezone.utc))


@pytest.mark.parametrize('mutation', ['observed_at', 'deadline', 'historical', 'result', 'missing'])
def test_binding_and_missing_evidence_refuse(prepared, mutation):
    manifest, report, path = prepared
    manifest = deepcopy(manifest)
    if mutation == 'observed_at':
        report['observed_at'] = '2026-10-01T08:00:00Z'
    elif mutation == 'deadline':
        manifest['owner_action_deadline'] = '2026-10-03T07:24:01Z'
    elif mutation == 'historical':
        report['historical_snapshot_sha256'] = '0' * 64
    elif mutation == 'result':
        (path / 'accepted-precontrol-result.json').write_text('{}')
    else:
        report.pop('freshness_evidence')
    with pytest.raises(ValueError):
        runner.validate_conservative_freshness(report, manifest, datetime(2026, 10, 1, 8, tzinfo=timezone.utc))


def test_reader_dispatch_and_no_observed_at(prepared, monkeypatch):
    manifest, report, path = prepared
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 1, 8, tzinfo=timezone.utc)
    monkeypatch.setattr(runner, 'datetime', Clock)
    (path / 'precontrol-ready.json').write_text(json.dumps(report))
    assert runner.precontrol_attestation(manifest) == report
    report['observed_at'] = '2026-10-01T08:00:00Z'
    (path / 'precontrol-ready.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='SHAPE_REFUSED'):
        runner.precontrol_attestation(manifest)


def test_legacy_attestation_retains_its_original_semantics(prepared, monkeypatch):
    manifest, report, path = prepared
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 1, 8, tzinfo=timezone.utc)
    monkeypatch.setattr(runner, 'datetime', Clock)
    report.pop('freshness_evidence')
    report['schema_version'] = 'v41-injected-successor-precontrol-attestation-1'
    report['observed_at'] = '2026-10-01T07:30:00+00:00'
    (path / 'precontrol-ready.json').write_text(json.dumps(report))
    assert runner.precontrol_attestation(manifest) == report
    report['schema_version'] = 'unsupported'
    (path / 'precontrol-ready.json').write_text(json.dumps(report))
    with pytest.raises(ValueError):
        runner.precontrol_attestation(manifest)
