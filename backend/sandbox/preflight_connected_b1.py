"""GET-only Integration preflight. Writes a non-secret local baseline, no DB writes."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from types import SimpleNamespace
from sandbox.bounded_test_transport import INTEGRATION_TEST_ORIGIN, integration_get
from services.governed_rehearsal_permit import PROJECT, COMPANY, ENTITY, FILENAME, SOURCE_HASH, scoped_snapshot
from services.governed_rehearsal_permit import PROTECTED_TABLES, TABLES


class SafeRefusal(ValueError):
    pass


class ReadOnlyDatabase:
    def __init__(self, key):
        if PROJECT != INTEGRATION_TEST_ORIGIN:
            raise ValueError('PROJECT_REFUSED')
        self.headers={'apikey':key,'Authorization':'Bearer '+key}
    def close(self):
        pass
    def from_(self, table):
        if table not in set(TABLES + PROTECTED_TABLES + ('companies','engagements')):
            raise ValueError('READ_SCOPE')
        db=self
        class Query:
            def __init__(self): self.params={}
            def select(self,columns): self.params['select']=columns; return self
            def eq(self,column,value): self.params[column]='eq.'+value; return self
            def limit(self,count): self.params['limit']=str(count); return self
            def execute(self):
                response=integration_get('/rest/v1/'+table,headers=db.headers,params=self.params)
                if response.status_code != 200: raise SafeRefusal('READ_'+table.upper()+'_HTTP_'+str(response.status_code))
                data=response.json()
                if not isinstance(data,list): raise ValueError('READ_SHAPE')
                return SimpleNamespace(data=data)
        return Query()


def preflight(db):
    rows=db.from_('entities').select('id,company_id,name').eq('id',ENTITY).eq('company_id',COMPANY).limit(2).execute().data
    if len(rows)!=1 or rows[0]['name']!='Optilux Synthetic Internal Pilot':
        raise ValueError('ENTITY_BINDING')
    rows=db.from_('companies').select('id').eq('id',COMPANY).limit(2).execute().data
    if len(rows)!=1: raise ValueError('COMPANY_BINDING')
    rows=db.from_('engagements').select('id,entity_id').eq('entity_id',ENTITY).limit(2).execute().data
    if len(rows)!=1 or rows[0]['entity_id']!=ENTITY: raise ValueError('ENGAGEMENT_BINDING')
    engagement=str(UUID(rows[0]['id']))
    # Validate required receipt columns even if its scoped table is empty.
    db.from_('governed_execution_receipts').select('analysis_id,company_id,entity_id,engagement_id,payload,sha256').eq('company_id',COMPANY).limit(1).execute()
    baseline=scoped_snapshot(db,COMPANY)
    identity=str(uuid4())
    if any(identity in values for values in baseline.values()): raise ValueError('ID_COLLISION')
    return dict(phase='B1_READ_ONLY_PREFLIGHT_PASS',project_url=PROJECT,company_id=COMPANY,entity_id=ENTITY,
                engagement_id=engagement,analysis_id=identity,filename=FILENAME,source_sha256=SOURCE_HASH,
                baseline=baseline,expires_at=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat())


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--manifest',required=True)
    path=Path(parser.parse_args().manifest)
    stage='LOCAL_FILES'; db=None
    logging.disable(logging.CRITICAL)
    try:
        if not path.is_absolute() or not path.parent.is_dir() or any(path.with_suffix(s).exists() for s in ('.json','.pending','.attempt','.closed')):
            raise ValueError('EXISTING_STATE')
        fixture=Path(__file__).resolve().parents[1]/'tests/golden/fixtures'/FILENAME
        if hashlib.sha256(fixture.read_bytes()).hexdigest().upper()!=SOURCE_HASH:
            raise ValueError('SOURCE_INTEGRITY')
        stage='SERVICE_KEY_AVAILABILITY'
        key=os.getenv('SUPABASE_SERVICE_KEY','')
        if not key: raise ValueError('KEY_MISSING')
        # Local latch only: do not rerun automatically even after read failure.
        with path.with_suffix('.pending').open('x',encoding='utf-8') as handle:
            handle.write('READ_ONLY_PREFLIGHT_STARTED\n')
        stage='REMOTE_READ_ONLY_SCOPE_AND_SCHEMA'
        db=ReadOnlyDatabase(key)
        data=preflight(db)
        stage='LOCAL_BASELINE'
        with path.open('x',encoding='utf-8') as handle:
            json.dump(data,handle,sort_keys=True); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(dict(status=data['phase'],business_write_performed=False,
            transport_activated=False,new_analysis_created=False,external_provider_used=False,real_data_used=False,
            baseline_counts={table:len(rows) for table,rows in data['baseline'].items()})))
        return 0
    except Exception as exc:
        # Only locally constructed codes; never HTTP response/exception bodies.
        safe_code = str(exc) if isinstance(exc,SafeRefusal) else type(exc).__name__
        print(json.dumps(dict(status='REFUSED',stage=stage,diagnostic=safe_code,
                             business_write_performed=False,transport_activated=False)))
        return 1
    finally:
        if db: db.close()


if __name__=='__main__':
    raise SystemExit(main())
