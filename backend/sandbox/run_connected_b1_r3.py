"""Temporary loopback server: existing permit only, no automated upload/retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from services.governed_rehearsal_permit import RehearsalPermit, COMPANY, PROJECT, SOURCE_HASH, FILENAME, scoped_snapshot
from sandbox.preflight_connected_b1 import ReadOnlyDatabase

MANIFEST_HASH='91CCF4AC7E0702EA6F7F8859B29DF3BF7A023972D4A0048858C6F738A659A40E'


def check_local(path):
    from sandbox.inspect_closed_b1_r2 import local_check
    local_check(path.parent)
    if path.name != 'b1-connected-rehearsal-r3.json':
        raise ValueError('SUCCESSOR_PATH_REFUSED')
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
    from sandbox.inspect_closed_b1_r2 import verify_remote
    verify_remote(db, permit.data)



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
