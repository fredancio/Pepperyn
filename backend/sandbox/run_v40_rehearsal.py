"""One-shot V40 launcher. No CLI resume, alternate project or cleanup path.

Credentials enter only through stdin, and access token through worker pipes.
Owner INSERT/disable use SQL Editor; this process cannot perform direct DML.
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sandbox.preflight_v40_rehearsal import ReadOnlyClient, inspect, FIXTURE, RAW_SHA, URL
from sandbox.v40_rehearsal_budget import Budget, SLOTS
from sandbox.v40_rehearsal_transport import RehearsalTransport
from sandbox.v40_rehearsal_orchestration import Backend, profile_for, run_protocol, require
from sandbox.v40_rehearsal_processes import Workers
from sandbox.v40_rehearsal_owner import owner_sql

RUNTIME=Path('C:/Users/ADMIN-FRED/Documents/Codex/Pepperyn-runtime')
ATTEMPT=RUNTIME/'v40-rehearsal-19'
BASELINE=RUNTIME/'v40-service-readonly-preflight-19.json'
BASELINE_HASH='35759DA949A93E0FB4DF030DBE8F9760B27C115D0EF9E2C1E833E830F6CD6F63'
MIGRATION_HASH='D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24'


def write_new(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,sort_keys=True,ensure_ascii=False)


def check_local():
    require(sha256(FIXTURE.read_bytes()).hexdigest().upper()==RAW_SHA)
    migration=Path(__file__).parents[1]/'migrations/v40_prospective_execution_admission.sql'
    require(sha256(migration.read_bytes()).hexdigest().upper()==MIGRATION_HASH)
    require(len(SLOTS)==len(set(SLOTS))==19 and SLOTS[0]=='AUTH_ONCE' and SLOTS[-1]=='POLICY_DISABLE')
    require(not ATTEMPT.exists())
    require(sha256(BASELINE.read_bytes()).hexdigest().upper()==BASELINE_HASH)


def wait_catalog(attempt, *, timeout=900):
    """Trusted local operator attests actual UI read-only checks; not authority
    for a product API. The runtime separately rechecks scope/rows before Auth.
    An earlier read-only snapshot is never an execution permit.
    """
    deadline=time.monotonic()+timeout
    path=attempt/'catalog-ready.json'
    while not path.exists():
        require(time.monotonic()<deadline)
        time.sleep(0.5)
    report=json.loads(path.read_text(encoding='utf-8'))
    require(set(report)=={'version','project','definition_status','structure_verified','observed_at','effect_ceiling','row_ceiling'})
    require(report['version']=='v40-rehearsal-operator-readiness-1' and report['project']==URL
            and report['definition_status']=='BOUNDED_DEFINITION_CONFORMANCE_PASS'
            and report['structure_verified'] is True and report['effect_ceiling']==19 and report['row_ceiling']==7)
    stamp=datetime.fromisoformat(report['observed_at'])
    require(stamp.utcoffset() is not None and 0<=(datetime.now(timezone.utc)-stamp).total_seconds()<=180)


class OwnerActions:
    def __init__(self, attempt, budget, reader):
        self.attempt,self.budget,self.reader=attempt,budget,reader

    def __call__(self, action, manifest):
        sql=owner_sql(action,manifest)
        self.budget.take(action)  # Burn before making the owner ticket visible.
        write_new(self.attempt/(action.lower()+'.json'),{
            'action':action,'policy_id':manifest['policy_id'],'sql':sql,
            'sql_sha256':sha256(sql.encode()).hexdigest().upper(),'automatic_retry_permitted':False})
        print('V40_OWNER_ACTION_REQUIRED: '+action,flush=True)
        deadline=time.monotonic()+90
        while True:
            require(time.monotonic()<deadline)
            rows=self.reader.rows('producer_policies_v2')
            require(len(rows)<=1)
            if rows:
                p=rows[0]
                require(p['id']==manifest['policy_id'] and p['specification']==manifest['profile']
                        and p['contract_sha256']==manifest['contract_sha256']
                        and p['origin']=='SYNTHETIC' and p['egress']=='DENY')
                if action=='POLICY_INSERT':require(p['enabled'] is True);return
                if p['enabled'] is False:return
                require(p['enabled'] is True)
            else:require(action=='POLICY_INSERT')
            time.sleep(0.5)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    stage='LOCAL_CHECK';budget=None;reader=None;transport=None
    try:
        check_local()
        if args.check:
            print(json.dumps({'status':'V40_RUNNER_LOCAL_CHECK_PASS','network_used':False,'secret_read':False}))
            return 0
        stage='EXCLUSIVE_ATTEMPT'
        ATTEMPT.mkdir()  # Existing/partial attempt is never resumed or reset.
        budget=Budget.create(ATTEMPT/'effects.sqlite')
        stage='CREDENTIAL_INPUT'
        packet=json.load(sys.stdin)
        require(set(packet)=={'anon','service','bundle','authorization'})
        require(packet['authorization']=='V40_19_EFFECTS_7_ROWS_ONE_AUTH_ONLY')
        bundle=packet['bundle']
        require(bundle['project_url']==URL and bundle['purpose']=='A24_TECHNICAL_ISOLATION_ONLY'
                and len(bundle['accounts'])==2
                and bundle['accounts'][0]['email']=='pepperyn-isolation-a24-a@pepperyn-test.invalid')
        anon,service=packet['anon'],packet['service']
        password=bundle['accounts'][0]['password']
        del packet,bundle
        reader=ReadOnlyClient(service)
        stage='FRESH_SERVICE_PREFLIGHT'
        before=inspect(reader)
        require(before==json.loads(BASELINE.read_text(encoding='utf-8')))
        write_new(ATTEMPT/'ready.json',{'status':'V40_WAITING_READ_ONLY_CATALOG_NO_AUTH',
            'auth_attempts':0,'effect_attempts':0,'business_write_performed':False})
        print('V40_WAITING_READ_ONLY_CATALOG_NO_AUTH. Keep this terminal open. No login yet.',flush=True)
        stage='CATALOG_GATE'
        wait_catalog(ATTEMPT)
        require(inspect(reader)==before)
        stage='SINGLE_AUTH'
        transport=RehearsalTransport(budget=budget,anon_key=anon,service_key=service)
        session=transport.login_once(password=password,expected_actor=before['scope']['actor_id'])
        password=None
        config={'scope':before['scope'],'policy_id':str(uuid4()),'journal':str(ATTEMPT/'effects.sqlite')}
        memory={'anon':anon,'service':service,'session':session}
        db=Backend(reader,transport,session,profile_for(before['scope']),config['policy_id'])
        stage='BOUNDED_PROTOCOL'
        result=run_protocol(db,before,publish=lambda m:write_new(ATTEMPT/'manifest.json',m),
            owner=OwnerActions(ATTEMPT,budget,reader),workers=Workers(config,memory))
        require(budget.report()['effect_attempts']==19 and budget.report()['auth_attempts']==1
                and set(budget.report()['slots'])==set(SLOTS))
        result.update(effect_attempts=19,auth_attempts=1,business_write_performed=True,
                      production_proven=False,global_isolation_proven=False)
        budget.close()
        write_new(ATTEMPT/'result.json',result)
        print(json.dumps(result),flush=True)
        return 0
    except BaseException:
        safe={'status':'V40_REHEARSAL_REFUSED','stage':stage,'automatic_retry_permitted':False}
        if budget is not None:
            try:
                budget.close();safe.update(budget.report())
                write_new(ATTEMPT/'refused.json',safe)
            except Exception:pass
        print(json.dumps(safe),flush=True)
        return 1
    finally:
        if reader is not None:reader.close()
        if transport is not None:transport.close()


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    raise SystemExit(main())
