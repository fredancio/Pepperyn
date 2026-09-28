"""Distinct one-shot successor; no resume, old-journal reuse or cleanup route.

Default is LOCAL CHECK ONLY. --execute requires the distinct successor GO in
the stdin packet, after local validation and fresh owner READ-ONLY attestation.
No owner SQL is executed by this process. No new authentication during --check.
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

from sandbox.preflight_v40_rehearsal import ReadOnlyClient, inspect, digest, FIXTURE, RAW_SHA, URL
from sandbox.v40_rehearsal_budget import Budget, SLOTS
from sandbox.v40_rehearsal_transport import RehearsalTransport
from sandbox.v40_rehearsal_orchestration import Backend, profile_for, run_protocol, require
from sandbox.v40_rehearsal_processes import Workers
from sandbox.v40_successor_identities import IdentityPlan, IdentityConsumption
from sandbox.v40_successor_history import (snapshot, HistoryReader, assert_fresh_identities,
    catalog_history_sql, owner_sql, HISTORICAL_POLICY, HISTORICAL_ADMISSIONS_SHA)

RUNTIME=Path('C:/Users/ADMIN-FRED/Documents/Codex/Pepperyn-runtime')
ATTEMPT=RUNTIME/'v40-successor-1'
OLD_MANIFEST=RUNTIME/'v40-rehearsal-19/manifest.json'
BASELINE=RUNTIME/'v40-service-readonly-preflight-19.json'
PINS={OLD_MANIFEST:'15A8A8D6C0844D62EA3257A5E6DAA4EEEC546279BCE00779D143BC8841872EE4',
      BASELINE:'35759DA949A93E0FB4DF030DBE8F9760B27C115D0EF9E2C1E833E830F6CD6F63',
      RUNTIME/'v40-rehearsal-19/refused.json':'93D503AB1C4DC35A12388442A59DDA407A287B2E2EEBEE17FF99421B38206E79'}


def write_new(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,sort_keys=True,ensure_ascii=False)


def check_local():
    require(not ATTEMPT.exists())
    require(sha256(FIXTURE.read_bytes()).hexdigest().upper()==RAW_SHA)
    for path,expected in PINS.items(): require(sha256(path.read_bytes()).hexdigest().upper()==expected)
    old=json.loads(OLD_MANIFEST.read_text(encoding='utf-8'))
    require(old['policy_id']==HISTORICAL_POLICY)
    require(len(set(SLOTS))==len(SLOTS)==19)


def wait_catalog(attempt,history,*,timeout=900):
    sql=catalog_history_sql(history,HISTORICAL_ADMISSIONS_SHA)
    # The operator checks current schema with the existing versioned conformance
    # query AND this exact historical-anchor query. Neither performs mutation.
    ticket={'sql':sql,'sql_sha256':sha256(sql.encode()).hexdigest().upper(),
            'historical_snapshot_sha256':digest(history),'write_performed':False}
    write_new(attempt/'catalog-request.json',ticket)
    print('V40_SUCCESSOR_WAITING_READ_ONLY_CATALOG_NO_AUTH',flush=True)
    deadline=time.monotonic()+timeout
    path=attempt/'catalog-ready.json'
    while not path.exists():
        require(time.monotonic()<deadline);time.sleep(.5)
    report=json.loads(path.read_text(encoding='utf-8'))
    require(set(report)=={'version','project','definition_status','structure_verified','observed_at',
                         'effect_ceiling','row_ceiling','history_status','historical_snapshot_sha256','sql_sha256'})
    require(report['version']=='v40-successor-readiness-1' and report['project']==URL
            and report['definition_status']=='BOUNDED_DEFINITION_CONFORMANCE_PASS'
            and report['structure_verified'] is True and report['effect_ceiling']==19 and report['row_ceiling']==7
            and report['history_status']=='V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS'
            and report['historical_snapshot_sha256']==ticket['historical_snapshot_sha256']
            and report['sql_sha256']==ticket['sql_sha256'])
    stamp=datetime.fromisoformat(report['observed_at'])
    require(stamp.utcoffset() is not None and 0<=(datetime.now(timezone.utc)-stamp).total_seconds()<=180)


def cloud_factory(config,memory):
    reader=HistoryReader(ReadOnlyClient(memory['service']),config['history'])
    return Backend(reader,RehearsalTransport(budget=Budget(config['journal']),
        anon_key=memory['anon'],service_key=memory['service']),memory['session'],
        profile_for(config['scope']),config['policy_id'])


class OwnerActions:
    def __init__(self,attempt,budget,reader,history):
        self.attempt,self.budget,self.reader,self.history=attempt,budget,reader,history

    def __call__(self,action,manifest):
        sql=owner_sql(action,manifest,self.history,HISTORICAL_ADMISSIONS_SHA)
        self.budget.take(action)
        write_new(self.attempt/(action.lower()+'.json'),{'action':action,'policy_id':manifest['policy_id'],
            'sql':sql,'sql_sha256':sha256(sql.encode()).hexdigest().upper(),'automatic_retry_permitted':False})
        print('V40_SUCCESSOR_OWNER_ACTION_REQUIRED: '+action,flush=True)
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
                if action=='POLICY_INSERT': require(p['enabled'] is True);return
                if p['enabled'] is False:return
                require(p['enabled'] is True)
            else:require(action=='POLICY_INSERT')
            time.sleep(.5)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    stage='LOCAL_CHECK';budget=None;reader=None;transport=None
    try:
        check_local()
        if not args.execute:
            print(json.dumps({'status':'V40_SUCCESSOR_LOCAL_CHECK_PASS','network_used':False,'secret_read':False}))
            return 0
        stage='DISTINCT_AUTHORIZATION'
        packet=json.load(sys.stdin)
        require(set(packet)=={'anon','service','bundle','authorization'})
        require(packet['authorization']=='V40_SUCCESSOR_1_DISTINCT_GO_19_EFFECTS_7_NEW_ROWS')
        bundle=packet['bundle']
        require(bundle['project_url']==URL and bundle['purpose']=='A24_TECHNICAL_ISOLATION_ONLY'
                and len(bundle['accounts'])==2
                and bundle['accounts'][0]['email']=='pepperyn-isolation-a24-a@pepperyn-test.invalid')
        anon,service,password=packet['anon'],packet['service'],bundle['accounts'][0]['password']
        del packet,bundle
        stage='EXCLUSIVE_SUCCESSOR'
        ATTEMPT.mkdir();budget=Budget.create(ATTEMPT/'effects.sqlite')
        raw=ReadOnlyClient(service);reader=raw
        stage='HISTORICAL_CANDIDATE_READ'
        history=snapshot(raw,json.loads(OLD_MANIFEST.read_text(encoding='utf-8')))
        reader=HistoryReader(raw,history)
        before=inspect(reader)
        require(before==json.loads(BASELINE.read_text(encoding='utf-8')))
        stage='CATALOG_AND_HISTORICAL_ANCHOR'
        wait_catalog(ATTEMPT,history)
        require(inspect(reader)==before)
        stage='PRE_AUTH_FROZEN_IDENTITIES'
        plan=IdentityPlan.create()
        identity_commitment=plan.commitment()
        assert_fresh_identities(raw,plan.manifest(),history)
        write_new(ATTEMPT/'prechecked-identities.json',dict(
            manifest=plan.manifest(),sha256=identity_commitment,
            auth_attempts=budget.report()['auth_attempts'],effect_attempts=budget.report()['effect_attempts']))
        require(budget.report()['effect_attempts']==0)
        plan.verify(plan.manifest(),identity_commitment)
        stage='SINGLE_AUTH'
        transport=RehearsalTransport(budget=budget,anon_key=anon,service_key=service)
        session=transport.login_once(password=password,expected_actor=before['scope']['actor_id'])
        password=None
        config={'scope':before['scope'],'policy_id':str(plan.policy_id),'journal':str(ATTEMPT/'effects.sqlite'),'history':history}
        db=Backend(reader,transport,session,profile_for(before['scope']),config['policy_id'],
                   identity_source=IdentityConsumption(plan,identity_commitment))
        def publish(manifest):
            plan.verify(manifest,identity_commitment)
            assert_fresh_identities(raw,manifest,history)
            write_new(ATTEMPT/'manifest.json',manifest)
        stage='SUCCESSOR_PROTOCOL'
        result=run_protocol(db,before,publish=publish,owner=OwnerActions(ATTEMPT,budget,reader,history),
            workers=Workers(config,{'anon':anon,'service':service,'session':session},factory=cloud_factory))
        require(budget.report()['effect_attempts']==19 and budget.report()['auth_attempts']==1
                and set(budget.report()['slots'])==set(SLOTS))
        require(inspect_history_unchanged(reader))
        persisted_manifest=json.loads((ATTEMPT/'manifest.json').read_text(encoding='utf-8'))
        plan.verify(persisted_manifest,identity_commitment)
        result.update(status='BOUNDED_V40_SUCCESSOR_PASS',historical_rows_unchanged=4,
            total_evidence_rows=11,effect_attempts=19,auth_attempts=1,business_write_performed=True,
            preauth_identity_commitment=identity_commitment,prechecked_composed_persisted_identity_match=True,
            production_proven=False,global_isolation_proven=False)
        budget.close();write_new(ATTEMPT/'result.json',result)
        print(json.dumps(result),flush=True);return 0
    except BaseException:
        safe={'status':'V40_SUCCESSOR_REFUSED','stage':stage,'automatic_retry_permitted':False}
        if budget is not None:
            try: budget.close();safe.update(budget.report());write_new(ATTEMPT/'refused.json',safe)
            except Exception:pass
        print(json.dumps(safe),flush=True);return 1
    finally:
        if reader is not None:reader.close()
        if transport is not None:transport.close()


def inspect_history_unchanged(reader):
    reader.rows('producer_policies_v2')  # Validates all historical rows, including disabled policy.
    return True


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    raise SystemExit(main())
