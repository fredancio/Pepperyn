"""Distinct fixed successor. All default/prepare/attest/publish operations local."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from sandbox import v41_injected_rehearsal as artifacts
from sandbox import run_v41_injected_rehearsal as runner


ATTEMPT = runner.RUNTIME / 'v41-injected-5'
BASE = 'ff14a3237152388c6b32989f29f5fd80f39874e9'
PROTOCOL = 'docs/Project_Control/PPR069_OWNER_ACK_SUCCESSOR_PROTOCOL.md'
PROTOCOL_HASH = 'CD8167C8BE8AB4D4C283B580350F34AB8923D59DD3A150C2E8F94BA70B3332F1'
BASELINE = runner.REPO / 'backend/tests/fixtures/v41_attempt4_accepted_precontrol.json'
BASELINE_HASH = '7205B6612A16746E768AFCC596D5D0B193DF547CAC08E2748A301F8ABE0C3853'


def precontrol_sql(repo, manifest):
    old = " 'check_version','v41-successor-single-result-precontrol-2',"
    sql = artifacts.precontrol_sql(repo, manifest)
    runner.require(sql.count(old) == 1, 'PRECONTROL_TEMPLATE_DRIFT')
    return sql.replace(old, " 'check_version','v41-owner-ack-precontrol-1',\n 'observed_at',statement_timestamp(),")


def read_manifest(attempt):
    runner.require(artifacts.file_sha256(runner.REPO / PROTOCOL) == PROTOCOL_HASH,
                   'OWNER_ACK_PROTOCOL_CHANGED')
    manifest = artifacts.read_manifest(attempt, protocol_sha256=PROTOCOL_HASH,
                                      checkpoint_head=BASE)
    for name, text in (
        ('precontrol.sql', precontrol_sql(runner.REPO, manifest)),
        ('policy-insert.sql', artifacts.policy_insert_sql(manifest)),
        ('policy-disable.sql', artifacts.policy_disable_sql(manifest)),
    ):
        runner.require((attempt / name).read_bytes() == text.encode('utf-8'),
                       'OWNER_ACK_FROZEN_SQL_CHANGED')
    return manifest


def freeze(attempt):
    return artifacts.freeze_manifest(runner.REPO, attempt, protocol_relative=PROTOCOL,
        protocol_sha256=PROTOCOL_HASH, checkpoint_head=BASE, precontrol_builder=precontrol_sql)


def validate_result(result, manifest, now):
    runner.require(artifacts.file_sha256(BASELINE) == BASELINE_HASH, 'BASELINE_CHANGED')
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    stamp = datetime.fromisoformat(result['observed_at'])
    created = datetime.fromisoformat(manifest['created_at'])
    deadline = datetime.fromisoformat(manifest['owner_action_deadline'])
    runner.require(stamp.utcoffset() is not None and now.utcoffset() is not None and
                   created <= stamp <= now < deadline and (now-stamp).total_seconds() < 86400,
                   'OWNER_ACK_PRECONTROL_EXPIRED')
    runner.require(result['check_version'] == 'v41-owner-ack-precontrol-1' and
        result['status'] == 'V41_SUCCESSOR_PRECONTROL_CHECKS_PASS' and
        result['write_performed'] is False and result['auth_performed'] is False and
        result['historical_comparison_required'] is True and
        result['historical'] == baseline['historical'] and
        result['structural'] == baseline['structural'] and
        result['frozen_scope'] == {
            'status': 'V41_INJECTED_SUCCESSOR_FROZEN_SCOPE_PRECONTROL_PASS',
            **manifest['identities'], 'write_performed': False, 'auth_performed': False},
        'OWNER_ACK_PRECONTROL_RESULT_REFUSED')


def validate_attestation(manifest, *, attempt=None, now=None):
    attempt = ATTEMPT if attempt is None else attempt
    now = datetime.now(timezone.utc) if now is None else now
    runner.require(read_manifest(attempt) == manifest, 'MANIFEST_CHANGED')
    raw = attempt / 'accepted-precontrol-result.json'
    result = json.loads(raw.read_text(encoding='utf-8'))
    validate_result(result, manifest, now)
    report = json.loads((attempt / 'precontrol-ready.json').read_text(encoding='utf-8'))
    runner.require(report == {
        'schema_version': 'v41-owner-ack-attestation-1',
        'manifest_sha256': manifest['manifest_sha256'],
        'sql_sha256': artifacts.file_sha256(attempt / 'precontrol.sql'),
        'result_sha256': artifacts.file_sha256(raw),
        'observed_at': result['observed_at'],
        'historical_snapshot_sha256': runner.digest(result['historical']),
    }, 'OWNER_ACK_ATTESTATION_REFUSED')
    return report


def attest(source):
    manifest = read_manifest(ATTEMPT)
    result = json.loads(source.read_text(encoding='utf-8-sig'))
    validate_result(result, manifest, datetime.now(timezone.utc))
    for name in ('precontrol-ready.json', 'accepted-precontrol-result.json',
                 'baseline-before.json', 'effects.json', 'refused.json', 'result.json'):
        runner.require(not (ATTEMPT / name).exists(), 'ATTESTATION_ALREADY_STARTED')
    artifacts.write_new(ATTEMPT / 'accepted-precontrol-result.json', result)
    artifacts.write_new(ATTEMPT / 'precontrol-ready.json', {
        'schema_version': 'v41-owner-ack-attestation-1',
        'manifest_sha256': manifest['manifest_sha256'],
        'sql_sha256': artifacts.file_sha256(ATTEMPT / 'precontrol.sql'),
        'result_sha256': artifacts.file_sha256(ATTEMPT / 'accepted-precontrol-result.json'),
        'observed_at': result['observed_at'],
        'historical_snapshot_sha256': runner.digest(result['historical']),
    })
    validate_attestation(manifest)


def publish(action, *, attempt=None, now=None, confirmed=False):
    attempt = ATTEMPT if attempt is None else attempt
    clock = now or (lambda: datetime.now(timezone.utc))
    runner.require(os.name == 'nt' and confirmed and action in ('insert', 'disable'),
                   'OWNER_ACTION_CONFIRMATION_REQUIRED')
    manifest = read_manifest(attempt)
    expected = {'schema_version': 'v41-owner-local-ack-1', 'action': action,
        'manifest_sha256': manifest['manifest_sha256'],
        'policy_id': manifest['identities']['policy_id'],
        'sql_sha256': artifacts.file_sha256(attempt / f'policy-{action}.sql')}
    marker_path = attempt / f'owner-{action}-handoff-started.json'
    marker = json.loads(marker_path.read_text(encoding='utf-8'))
    pending = attempt / f'owner-{action}-ack.pending'
    final = attempt / f'owner-{action}-ack.json'

    def check():
        runner.require(not any((attempt / n).exists() for n in ('refused.json', 'result.json')),
                       'OWNER_HANDOFF_TERMINATED')
        runner.require(not final.exists() and read_manifest(attempt) == manifest and
                       json.loads(marker_path.read_text(encoding='utf-8')) == marker and
                       set(marker) == {'ack', 'deadline_utc'} and marker['ack'] == expected,
                       'OWNER_HANDOFF_BINDING_REFUSED')
        deadline = datetime.fromisoformat(marker['deadline_utc'])
        current = clock()
        runner.require(deadline.utcoffset() is not None and current.utcoffset() is not None and
                       current < deadline, 'OWNER_ACK_EXPIRED')
        if action == 'insert':
            runner.require(deadline == datetime.fromisoformat(manifest['owner_action_deadline']),
                           'OWNER_DEADLINE_CHANGED')
            validate_attestation(manifest, attempt=attempt, now=current)

    check()
    data = artifacts.canonical_bytes(expected) + b'\n'
    with pending.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    check()
    runner.require(pending.read_bytes() == data, 'OWNER_ACK_STAGING_CHANGED')
    # Windows rename is same-directory, atomic and refuses an existing target.
    os.rename(pending, final)
    runner.require(final.read_bytes() == data, 'OWNER_ACK_PUBLICATION_CHANGED')


def configure():
    runner.ATTEMPT = ATTEMPT
    runner.ENTRYPOINT = Path(__file__).resolve()
    runner.read_manifest = read_manifest
    runner.precontrol_attestation = validate_attestation


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--attest', type=Path)
    group.add_argument('--publish', choices=('insert', 'disable'))
    group.add_argument('--execute', action='store_true')
    group.add_argument('--recover', action='store_true')
    group.add_argument('--local-check', action='store_true')
    parser.add_argument('--confirm-sql-executed-once', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        freeze(ATTEMPT)
    elif args.attest:
        attest(args.attest)
    elif args.publish:
        publish(args.publish, confirmed=args.confirm_sql_executed_once)
    elif args.local_check:
        read_manifest(ATTEMPT)
    else:
        configure()
        if args.recover:
            return runner.recover_main()
        return runner.execute(json.load(sys.stdin))
    print('V41_OWNER_ACK_LOCAL_OPERATION_PASS; NO_NETWORK; NO_AUTH')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
