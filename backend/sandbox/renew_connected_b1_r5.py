"""Explicitly authorized successor permit. GET-only remotely, no server/upload.

Preserves the closed predecessor and its prospective analysis UUID. A pending
marker forbids automatic renewal retry after an uncertain local/remote outcome.
"""
import argparse
import copy
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sandbox.preflight_connected_b1 import ReadOnlyDatabase, SafeRefusal
from services.governed_rehearsal_permit import (
    COMPANY, ENTITY, PROJECT, FILENAME, SOURCE_HASH, TABLES, scoped_snapshot, RehearsalPermit,
)

OLD_HASH='3861209F118C8F7405009E439C8CA4C2597A1266A4303022AD4E01AD2D03248D'
CLOSED_HASH='4C2399C414D8E82F890BEE06D7E974D76519C29584FE7085CF37520739809189'
ANALYSIS='e2dc7bd5-c71a-4c88-821c-b1f2696fb04b'
AUTHORITY='FOUNDER_B1_R5_SAME_UUID_THREE_ROWS_20260925'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def local_precheck(previous, successor):
    from sandbox.inspect_closed_b1_r3 import local_check
    local_check(previous.parent)  # R1/R2/R3 closed and unchanged; no expiry reopening.
    if previous.name != 'b1-connected-rehearsal-r4.json':
        raise SafeRefusal('PREDECESSOR_PATH_REFUSED')
    if (not previous.is_absolute() or successor != previous.with_name('b1-connected-rehearsal-r5.json')
            or digest(previous)!=OLD_HASH or digest(previous.with_suffix('.closed'))!=CLOSED_HASH
            or any(previous.with_suffix(s).exists() for s in ('.attempt',))
            or any(successor.with_suffix(s).exists() for s in ('.json','.pending','.attempt','.activated','.closed'))):
        raise SafeRefusal('LOCAL_LINEAGE_REFUSED')
    data=json.loads(previous.read_bytes())
    if (data['analysis_id']!=ANALYSIS or data['company_id']!=COMPANY or data['entity_id']!=ENTITY
            or data['project_url']!=PROJECT or data['source_sha256']!=SOURCE_HASH or data['filename']!=FILENAME
            or data['phase']!='B1_READ_ONLY_PREFLIGHT_PASS'):
        raise SafeRefusal('PREDECESSOR_SCOPE_REFUSED')
    fixture=Path(__file__).resolve().parents[1]/'tests/golden/fixtures'/FILENAME
    if digest(fixture)!=SOURCE_HASH: raise SafeRefusal('SOURCE_INTEGRITY_REFUSED')
    return data


def read_successor(db, previous):
    # Global UUID absence, not merely absence under the expected company filter.
    for table in TABLES:
        key='id' if table=='analyses' else 'analysis_id'
        rows=db.from_(table).select(key).eq(key,ANALYSIS).limit(1).execute().data
        if rows!=[]: raise SafeRefusal('PROSPECTIVE_UUID_ALREADY_EXISTS')
    if scoped_snapshot(db,COMPANY)!=previous['baseline']:
        raise SafeRefusal('PREEXISTING_BASELINE_CHANGED')
    rows=db.from_('entities').select('id,company_id,name').eq('id',ENTITY).eq('company_id',COMPANY).limit(2).execute().data
    if len(rows)!=1 or rows[0].get('name')!='Optilux Synthetic Internal Pilot':
        raise SafeRefusal('ENTITY_BINDING_REFUSED')
    rows=db.from_('companies').select('id').eq('id',COMPANY).limit(2).execute().data
    if len(rows)!=1: raise SafeRefusal('COMPANY_BINDING_REFUSED')
    rows=db.from_('engagements').select('id,entity_id').eq('entity_id',ENTITY).limit(2).execute().data
    if len(rows)!=1 or rows[0].get('id')!=previous['engagement_id'] or rows[0].get('entity_id')!=ENTITY:
        raise SafeRefusal('ENGAGEMENT_BINDING_REFUSED')
    now=datetime.now(timezone.utc)
    result=copy.deepcopy(previous)
    result.update(predecessor_sha256=OLD_HASH,predecessor_closed_sha256=CLOSED_HASH,
                  renewal_authority=AUTHORITY,renewed_at=now.isoformat(),
                  expires_at=(now+timedelta(hours=4)).isoformat())
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--previous',required=True)
    parser.add_argument('--successor',required=True); parser.add_argument('--local-check',action='store_true')
    args=parser.parse_args(); previous=Path(args.previous); successor=Path(args.successor)
    stage='LOCAL_LINEAGE'; db=None; pending=False
    logging.disable(logging.CRITICAL)
    try:
        original=local_precheck(previous,successor)
        if args.local_check:
            print('B1_RENEWAL_LOCAL_CHECK: PASS. No credentials, network, permit creation or activation.')
            return 0
        stage='PREPARED_ENVIRONMENT'
        if (os.getenv('SUPABASE_URL')!=PROJECT or os.getenv('ENVIRONMENT')!='development'
                or os.getenv('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO')!='1'
                or os.getenv('PEPPERYN_SYNTHETIC_V1_COMPANY_ID')!=COMPANY
                or os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT')!='0'
                or not os.getenv('SUPABASE_SERVICE_KEY')):
            raise SafeRefusal('PREPARED_ENVIRONMENT_REFUSED')
        with successor.with_suffix('.pending').open('x',encoding='utf-8') as handle:
            handle.write('AUTHORIZED_SUCCESSOR_READ_CHECK_STARTED\n'); handle.flush(); os.fsync(handle.fileno())
        pending=True
        stage='REMOTE_ABSENCE_AND_BASELINE'
        db=ReadOnlyDatabase(os.environ['SUPABASE_SERVICE_KEY'])
        result=read_successor(db,original)
        stage='PREDECESSOR_UNCHANGED'
        from sandbox.inspect_closed_b1_r3 import local_check
        local_check(previous.parent)
        if digest(previous)!=OLD_HASH or digest(previous.with_suffix('.closed'))!=CLOSED_HASH:
            raise SafeRefusal('PREDECESSOR_CHANGED')
        stage='CREATE_DISTINCT_PERMIT'
        with successor.open('x',encoding='utf-8') as handle:
            json.dump(result,handle,sort_keys=True); handle.flush(); os.fsync(handle.fileno())
        RehearsalPermit(successor,COMPANY)
        print(json.dumps(dict(status='B1_R5_PERMIT_CREATED',analysis_id=ANALYSIS,
            prospective_uuid_absent=True,preexisting_hashes_unchanged=True,previous_permit_unchanged=True,
            successor_sha256=digest(successor),expires_at=result['expires_at'],new_permit_created=True,
            business_write_performed=False,transport_activated=False,external_provider_used=False,real_data_used=False)))
        return 0
    except Exception as exc:
        if pending and not successor.with_suffix('.closed').exists():
            with successor.with_suffix('.closed').open('x',encoding='utf-8') as handle:
                handle.write('RENEWAL_REFUSED_NO_RETRY\n')
        print(json.dumps(dict(status='REFUSED',stage=stage,
            diagnostic=str(exc) if isinstance(exc,SafeRefusal) else type(exc).__name__,
            business_write_performed=False,transport_activated=False)))
        return 1
    finally:
        if db: db.client.close()


if __name__=='__main__':
    raise SystemExit(main())
