"""Distinct fixed successor. All default/prepare/attest/publish operations local."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from sandbox import v41_injected_rehearsal as artifacts
from sandbox import run_v41_injected_rehearsal as runner
from sandbox import v41_two_policy_history as history


ATTEMPT = runner.RUNTIME / 'v41-injected-6'
BASE = '0250a52c0002ef46d3df673fbf810548a17517ff'
PROTOCOL = 'docs/Project_Control/PPR069_ATTEMPT6_PROTOCOL.md'
PROTOCOL_HASH = 'D34FF884F54A48B7B7469CA4C1AE67A2E7BCB910FE8A2A42AC6AF5CD4DA8740C'
BASELINE = runner.REPO / 'backend/tests/fixtures/v41_attempt4_accepted_precontrol.json'
BASELINE_HASH = '7205B6612A16746E768AFCC596D5D0B193DF547CAC08E2748A301F8ABE0C3853'


def precontrol_sql(repo, manifest):
    runner.require(history.enabled(manifest), 'TWO_HISTORY_VERSION_REQUIRED')
    return history.sql(repo, manifest)


def read_manifest(attempt):
    runner.require(artifacts.file_sha256(runner.REPO / PROTOCOL) == PROTOCOL_HASH,
                   'OWNER_ACK_PROTOCOL_CHANGED')
    manifest = artifacts.read_manifest(attempt, protocol_sha256=PROTOCOL_HASH,
                                      checkpoint_head=BASE)
    runner.require(history.enabled(manifest), 'TWO_HISTORY_VERSION_REQUIRED')
    runner.require(manifest['ceilings'] == {'effect_capable_requests': 10, 'durable_rows': 5, 'auth_logins': 1}
        and manifest['policy_contract'] == {'admission_scope':'LOCAL_TEST_ADMISSION',
        'transport_mode':'INJECTED_LOCAL_ONLY','provider_execution_attested':False,
        'producer_global_status':'UNADMITTED','egress_authorization':'CLOSED',
        'real_data_admission':'CLOSED'}, 'ATTEMPT6_CONTRACT_REFUSED')
    forbidden = historical_identities()
    runner.require(not set(manifest['identities'].values()) & forbidden and
        set(manifest['identities']) == {'policy_id','request_id','execution_id','analysis_id'} and
        len(set(manifest['identities'].values())) == 4, 'HISTORICAL_ID_REUSE_REFUSED')
    for name, text in (
        ('precontrol.sql', precontrol_sql(runner.REPO, manifest)),
        ('policy-insert.sql', artifacts.policy_insert_sql(manifest)),
        ('policy-disable.sql', artifacts.policy_disable_sql(manifest)),
    ):
        runner.require((attempt / name).read_bytes() == text.encode('utf-8'),
                       'OWNER_ACK_FROZEN_SQL_CHANGED')
    return manifest


def historical_identities():
    forbidden = set()
    for number in range(1, 6):
        previous = json.loads((runner.RUNTIME / f'v41-injected-{number}' / 'manifest.json').read_text(encoding='utf-8'))
        forbidden.update(previous['identities'].values())
    return forbidden


def freeze(attempt):
    return artifacts.freeze_manifest(runner.REPO, attempt, protocol_relative=PROTOCOL,
        protocol_sha256=PROTOCOL_HASH, checkpoint_head=BASE, precontrol_builder=precontrol_sql,
        historical_policy_contract=history.VERSION, forbidden_identities=historical_identities())


def validate_attestation(manifest, *, attempt=None, now=None):
    attempt = ATTEMPT if attempt is None else attempt
    now = datetime.now(timezone.utc) if now is None else now
    runner.require(read_manifest(attempt) == manifest, 'MANIFEST_CHANGED')
    history.accepted_history(attempt, manifest, now)
    return json.loads((attempt / 'precontrol-ready.json').read_text(encoding='utf-8'))


def attest(source):
    manifest = read_manifest(ATTEMPT)
    result = json.loads(source.read_text(encoding='utf-8-sig'))
    history.validate_result(result, manifest, datetime.now(timezone.utc))
    for name in ('precontrol-ready.json', 'accepted-precontrol-result.json',
                 'baseline-before.json', 'effects.json', 'refused.json', 'result.json'):
        runner.require(not (ATTEMPT / name).exists(), 'ATTESTATION_ALREADY_STARTED')
    artifacts.write_new(ATTEMPT / 'accepted-precontrol-result.json', result)
    artifacts.write_new(ATTEMPT / 'precontrol-ready.json', {
        'schema_version': 'v41-two-policy-attestation-1',
        'manifest_sha256': manifest['manifest_sha256'],
        'sql_sha256': artifacts.file_sha256(ATTEMPT / 'precontrol.sql'),
        'result_sha256': artifacts.file_sha256(ATTEMPT / 'accepted-precontrol-result.json'),
        'observed_at': result['observed_at'],
        'historical_snapshot_sha256': runner.digest(result['historical']),
        'historical_policies_sha256': runner.digest(history.validate(result['historical_policies'])),
    })
    validate_attestation(manifest)


def transfer_record(manifest):
    return {'schema_version':'v41-owner-transfer-ready-1',
        'manifest_sha256':manifest['manifest_sha256'],
        'insert_sha256':artifacts.file_sha256(ATTEMPT / 'policy-insert.sql'),
        'disable_sha256':artifacts.file_sha256(ATTEMPT / 'policy-disable.sql'),
        'publisher_sha256':artifacts.file_sha256(runner.REPO / 'scripts/publish-v41-attempt6-owner-ack.ps1'),
        'qualification':'LOCAL_BYTE_COMPARISON_NOT_REMOTE_STATE'}


def verify_transfers(insert_copy, disable_copy):
    manifest = read_manifest(ATTEMPT)
    runner.require(not any((ATTEMPT / n).exists() for n in
        ('baseline-before.json','effects.json','refused.json','result.json')), 'TRANSFER_TOO_LATE')
    for action, path in (('insert',insert_copy),('disable',disable_copy)):
        canonical = ATTEMPT / f'policy-{action}.sql'
        runner.require(path.resolve() != canonical.resolve() and path.read_bytes() == canonical.read_bytes(),
                       'LOADED_SQL_BYTES_REFUSED')
    artifacts.write_new(ATTEMPT / 'owner-transfer-ready.json', transfer_record(manifest))


def require_transfers(manifest):
    runner.require(json.loads((ATTEMPT / 'owner-transfer-ready.json').read_text(encoding='utf-8'))
                   == transfer_record(manifest), 'TRANSFER_READINESS_REFUSED')


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
    group.add_argument('--verify-transfers', nargs=2, type=Path)
    group.add_argument('--launch-preflight', action='store_true')
    parser.add_argument('--confirm-sql-executed-once', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        freeze(ATTEMPT)
    elif args.attest:
        attest(args.attest)
    elif args.publish:
        publish(args.publish, confirmed=args.confirm_sql_executed_once)
    elif args.verify_transfers:
        verify_transfers(*args.verify_transfers)
    elif args.launch_preflight:
        manifest = read_manifest(ATTEMPT)
        require_transfers(manifest)
        validate_attestation(manifest)
    elif args.local_check:
        read_manifest(ATTEMPT)
    else:
        configure()
        if args.recover:
            return runner.recover_main()
        require_transfers(read_manifest(ATTEMPT))
        return runner.execute(json.load(sys.stdin))
    print('V41_OWNER_ACK_LOCAL_OPERATION_PASS; NO_NETWORK; NO_AUTH')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
