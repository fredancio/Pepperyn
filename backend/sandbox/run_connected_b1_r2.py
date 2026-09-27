"""Temporary loopback server: existing permit only, no automated upload/retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from services.governed_rehearsal_permit import RehearsalPermit, COMPANY, PROJECT, SOURCE_HASH, FILENAME, scoped_snapshot
from sandbox.preflight_connected_b1 import ReadOnlyDatabase

MANIFEST_HASH='457403C3E5812E6A978C14CC0CC00DCBB5A1CEE520F18C87C0740FBC18F51B46'


def check_local(path):
    from sandbox.renew_connected_b1 import OLD_HASH, CLOSED_HASH
    previous = path.with_name('b1-connected-rehearsal.json')
    if (path.name != 'b1-connected-rehearsal-r2.json'
            or hashlib.sha256(previous.read_bytes()).hexdigest().upper() != OLD_HASH
            or hashlib.sha256(previous.with_suffix('.closed').read_bytes()).hexdigest().upper() != CLOSED_HASH):
        raise ValueError('PREDECESSOR_INTEGRITY')
    if hashlib.sha256(path.read_bytes()).hexdigest().upper()!=MANIFEST_HASH:
        raise ValueError('MANIFEST_INTEGRITY')
    if path.with_suffix('.attempt').exists() or path.with_suffix('.activated').exists():
        raise ValueError('EXISTING_ATTEMPT_NO_RERUN')
    permit=RehearsalPermit(path,COMPANY)
    fixture=Path(__file__).resolve().parents[1]/'tests/golden/fixtures'/FILENAME
    if hashlib.sha256(fixture.read_bytes()).hexdigest().upper()!=SOURCE_HASH:
        raise ValueError('SOURCE_INTEGRITY')
    return permit


def check_remote(permit,db):
    if scoped_snapshot(db,COMPANY)!=permit.data['baseline']:
        raise ValueError('BASELINE_CHANGED')
    rows=db.from_('engagements').select('id,entity_id').eq('entity_id',permit.data['entity_id']).limit(2).execute().data
    if len(rows)!=1 or rows[0]['id']!=permit.data['engagement_id'] or rows[0]['entity_id']!=permit.data['entity_id']:
        raise ValueError('ENGAGEMENT_CHANGED')


def close(path):
    if not path.with_suffix('.closed').exists():
        with path.with_suffix('.closed').open('x',encoding='utf-8') as handle:
            handle.write('CLOSED_NO_AUTOMATIC_RESUME\n'); handle.flush(); os.fsync(handle.fileno())


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--manifest',required=True)
    parser.add_argument('--local-check',action='store_true')
    args=parser.parse_args(); path=Path(args.manifest)
    stage='LOCAL_PERMIT'; started=False
    try:
        permit=check_local(path)
        if args.local_check:
            print('B1_LOCAL_LAUNCH_CHECK: PASS. No network, no activation, no write.')
            return 0
        stage='EXISTING_ENVIRONMENT'
        if (os.getenv('SUPABASE_URL')!=PROJECT or os.getenv('ENVIRONMENT')!='development'
                or os.getenv('PEPPERYN_SYNTHETIC_V1_COMPANY_ID')!=COMPANY
                or os.getenv('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO')!='1'
                or os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT')!='1'
                or os.getenv('PEPPERYN_GOVERNED_REHEARSAL_MANIFEST')!=str(path)
                or not os.getenv('SUPABASE_ANON_KEY') or not os.getenv('SUPABASE_SERVICE_KEY')
                or len(os.getenv('JWT_GUEST_SECRET',''))<32):
            raise ValueError('ENVIRONMENT_REFUSED')
        stage='READ_ONLY_BASELINE_RECHECK'
        db=ReadOnlyDatabase(os.environ['SUPABASE_SERVICE_KEY'])
        try: check_remote(permit,db)
        finally: db.client.close()
        permit.check()
        stage='APPLICATION_IMPORT'
        from main import app
        stage='SINGLE_ACTIVATION'
        with path.with_suffix('.activated').open('x',encoding='utf-8') as handle:
            handle.write('SINGLE_LOOPBACK_SERVER\n'); handle.flush(); os.fsync(handle.fileno())
        started=True
        print('B1_ACTIVATION_PREFLIGHT: PASS. No analysis created. Existing secrets reused.',flush=True)
        stage='LOOPBACK_SERVER'
        import uvicorn
        uvicorn.run(app,host='127.0.0.1',port=8000,proxy_headers=False,log_level='info')
        return 0
    except (Exception,KeyboardInterrupt):
        print(json.dumps(dict(status='B1_LAUNCH_STOPPED',stage=stage,automatic_retry_permitted=False)))
        return 1
    finally:
        if not args.local_check:
            close(path)
            print('B1_TEMPORARY_SURFACE: CLOSED. No replay or cleanup. No live PASS inferred.',flush=True)


if __name__=='__main__':
    raise SystemExit(main())
