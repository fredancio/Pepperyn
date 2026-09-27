"""Read-only incident postflight. No renewal, RPC, local marker or secret writes."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path

from sandbox.preflight_connected_b1 import ReadOnlyDatabase, SafeRefusal
from services.governed_rehearsal_permit import COMPANY, PROJECT, TABLES, scoped_snapshot

ANALYSIS = 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b'
PINS = {
    'b1-connected-rehearsal-r3.json': '91CCF4AC7E0702EA6F7F8859B29DF3BF7A023972D4A0048858C6F738A659A40E',
    'b1-connected-rehearsal-r3.closed': 'D565E1E2EDC2024F2A9DBC529B03C620F4556F3301C152CF2ECD1A094332430C',
    'b1-connected-rehearsal.json': 'A68F439F3267C1E5B6E3C128B7BD079D0F8EC6832209818CB35095B4D502DF14',
    'b1-connected-rehearsal.closed': 'D565E1E2EDC2024F2A9DBC529B03C620F4556F3301C152CF2ECD1A094332430C',
    'b1-connected-rehearsal-r2.json': '457403C3E5812E6A978C14CC0CC00DCBB5A1CEE520F18C87C0740FBC18F51B46',
    'b1-connected-rehearsal-r2.closed': 'E93E35052430CA88B097CF7B0805F9515D10A65F1872AD8E1C67FEF54AA1FC96',
}


def local_check(root):
    for name, expected in PINS.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest().upper() != expected:
            raise SafeRefusal('LOCAL_EVIDENCE_CHANGED')
    if any((root / ('b1-connected-rehearsal' + suffix + '.attempt')).exists() for suffix in ('', '-r2', '-r3')):
        raise SafeRefusal('UNEXPECTED_ATTEMPT_MARKER')
    return json.loads((root / 'b1-connected-rehearsal-r3.json').read_bytes())


def verify_remote(db, data):
    if data['analysis_id'] != ANALYSIS or data['company_id'] != COMPANY or data['project_url'] != PROJECT:
        raise SafeRefusal('SCOPE_MISMATCH')
    for table in TABLES:
        key = 'id' if table == 'analyses' else 'analysis_id'
        if db.from_(table).select(key).eq(key, ANALYSIS).limit(1).execute().data != []:
            raise SafeRefusal('PROSPECTIVE_UUID_PRESENT_' + table.upper())
    if scoped_snapshot(db, COMPANY) != data['baseline']:
        raise SafeRefusal('PREEXISTING_BASELINE_CHANGED')
    rows = db.from_('engagements').select('id,entity_id').eq('entity_id', data['entity_id']).limit(2).execute().data
    if len(rows) != 1 or rows[0].get('id') != data['engagement_id'] or rows[0].get('entity_id') != data['entity_id']:
        raise SafeRefusal('ENGAGEMENT_CHANGED')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True)
    parser.add_argument('--local-check', action='store_true')
    args = parser.parse_args()
    root = Path(args.runtime)
    db = None
    stage = 'LOCAL_CLOSED_EVIDENCE'
    logging.disable(logging.CRITICAL)
    try:
        data = local_check(root)
        if args.local_check:
            print('B1_R3_POSTFLIGHT_LOCAL_CHECK: PASS. No network or write.')
            return 0
        stage = 'EXISTING_SERVICE_KEY'
        if os.getenv('SUPABASE_URL') != PROJECT or not os.getenv('SUPABASE_SERVICE_KEY'):
            raise SafeRefusal('EXISTING_ENVIRONMENT_UNAVAILABLE')
        stage = 'REMOTE_GET_ONLY'
        db = ReadOnlyDatabase(os.environ['SUPABASE_SERVICE_KEY'])
        verify_remote(db, data)
        stage = 'LOCAL_EVIDENCE_UNCHANGED'
        local_check(root)
        print(json.dumps(dict(status='B1_R3_NO_WRITE_POSTFLIGHT_PASS', analysis_id=ANALYSIS,
            prospective_uuid_absent_in_three_tables=True, preexisting_scope_hashes_unchanged=True,
            engagement_binding_unchanged=True, permits_closed_unchanged=True,
            business_write_performed=False, permit_created=False, transport_activated=False,
            external_provider_used=False, real_data_used=False, b1_global_proven=False)))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='REFUSED', stage=stage,
            diagnostic=str(exc) if isinstance(exc, SafeRefusal) else type(exc).__name__,
            business_write_performed=False, permit_created=False, transport_activated=False)))
        return 1
    finally:
        if db is not None:
            db.client.close()


if __name__ == '__main__':
    raise SystemExit(main())
