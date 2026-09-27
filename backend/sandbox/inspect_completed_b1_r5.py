"""Independent GET-only postflight of the consumed R5 permit. Never resumes it."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path

from sandbox.preflight_connected_b1 import ReadOnlyDatabase, SafeRefusal
from services.governed_rehearsal_permit import COMPANY, ENTITY, PROJECT, TABLES, SOURCE_HASH, scoped_snapshot
from services.governed_analysis_persistence import load_execution_provenance

ANALYSIS = 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b'
MANIFEST_HASH = '76BB3542C091C5556B381454827F4335BC14200D733469BA0D418615A42BE0E5'
EXECUTION = 'adc1998b-984a-4fb9-ae46-248a69224a52'
ENVELOPE_HASH = 'B74A6956920985CD44E720D5F6B408A6F32F0A4929A9E0D5E9645C2B72812488'


def local_check(root):
    path = root / 'b1-connected-rehearsal-r5.json'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != MANIFEST_HASH:
        raise SafeRefusal('MANIFEST_CHANGED')
    if path.with_suffix('.closed').read_text().strip() != 'CLOSED_NO_AUTOMATIC_RESUME':
        raise SafeRefusal('CLOSURE_UNCONFIRMED')
    if path.with_suffix('.attempt').read_text().strip() != ANALYSIS:
        raise SafeRefusal('ATTEMPT_MISMATCH')
    return json.loads(raw)


def verify_remote(db, data):
    if (data['analysis_id'], data['company_id'], data['entity_id'], data['project_url']) != (ANALYSIS, COMPANY, ENTITY, PROJECT):
        raise SafeRefusal('SCOPE_MISMATCH')
    current = scoped_snapshot(db, COMPANY)
    for table in TABLES:
        if ANALYSIS not in current[table] or ANALYSIS in data['baseline'][table]:
            raise SafeRefusal('EXPECTED_NEW_TRIO_MISSING')
        del current[table][ANALYSIS]
    if current != data['baseline']:
        raise SafeRefusal('BASELINE_OR_ROW_COUNT_CHANGED')
    for table in TABLES:
        key = 'id' if table == 'analyses' else 'analysis_id'
        rows = db.from_(table).select('*').eq(key, ANALYSIS).limit(2).execute().data
        scope_keys = ('company_id', 'entity_id') if table == 'analyses' else ('company_id', 'entity_id', 'engagement_id')
        if len(rows) != 1 or any(rows[0].get(k) != data[k] for k in scope_keys):
            raise SafeRefusal('TRIO_SCOPE_MISMATCH')
    rows = db.from_('engagements').select('id,entity_id').eq('entity_id', ENTITY).limit(2).execute().data
    if len(rows) != 1 or rows[0].get('id') != data['engagement_id']:
        raise SafeRefusal('ENGAGEMENT_CHANGED')
    record = load_execution_provenance(db, **{k: data[k] for k in ('analysis_id', 'company_id', 'entity_id', 'engagement_id')})
    if (record is None or str(record.execution_id) != EXECUTION or record.raw_source_sha256 != SOURCE_HASH
            or record.envelope_sha256 != ENVELOPE_HASH or record.provider_mode != 'LOCAL_MOCK' or record.transport != 'NONE'):
        raise SafeRefusal('OBSERVED_RECEIPT_MISMATCH')


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
        before = {p.name: p.read_bytes() for p in root.glob('b1-connected-rehearsal*') if p.is_file()}
        data = local_check(root)
        if args.local_check:
            print('B1_R5_POSTFLIGHT_LOCAL_CHECK: PASS. No network or write.')
            return 0
        stage = 'EXISTING_SERVICE_KEY'
        if os.getenv('SUPABASE_URL') != PROJECT or not os.getenv('SUPABASE_SERVICE_KEY'):
            raise SafeRefusal('EXISTING_ENVIRONMENT_UNAVAILABLE')
        stage = 'REMOTE_GET_ONLY'
        db = ReadOnlyDatabase(os.environ['SUPABASE_SERVICE_KEY'])
        verify_remote(db, data)
        stage = 'LOCAL_EVIDENCE_UNCHANGED'
        after = {p.name: p.read_bytes() for p in root.glob('b1-connected-rehearsal*') if p.is_file()}
        if before != after:
            raise SafeRefusal('PERMIT_EVIDENCE_CHANGED')
        print(json.dumps(dict(status='BOUNDED_B1_R5_PERSISTED_TRIO_POSTFLIGHT_PASS', analysis_id=ANALYSIS,
            new_durable_rows=3, preexisting_scope_hashes_unchanged=True, receipt_binding_verified=True,
            closed_permits_unchanged=True, business_write_performed=False, transport_activated=False,
            external_provider_used=False, real_data_used=False, b1_global_proven=False)))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='REFUSED', stage=stage,
            diagnostic=str(exc) if isinstance(exc, SafeRefusal) else type(exc).__name__, business_write_performed=False)))
        return 1
    finally:
        if db is not None:
            db.client.close()


if __name__ == '__main__':
    raise SystemExit(main())
