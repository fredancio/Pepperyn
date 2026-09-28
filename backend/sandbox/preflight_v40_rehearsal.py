"""V40 service-side READ-ONLY preflight. NO Auth login and NO mutation method.

This is not the rehearsal runner or a policy-registration command. It stops
before the separately budgeted login. No JWT/V33/technical password is needed.
"""
import argparse
import json
import logging
import os
from hashlib import sha256
from pathlib import Path
from uuid import UUID

import httpx

URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
REGISTRIES = ('producer_policies_v2','execution_admissions_v2','execution_receipts_v2')
EXISTING = ('analyses','governed_analysis_envelopes','governed_execution_receipts',
            'decision_feedback','user_patterns','decision_arcs','arc_analysis_links',
            'governed_decision_followups','governed_decision_executions',
            'governed_decision_prerequisite_evidence','synthetic_source_dossiers_v1')
READABLE = frozenset(REGISTRIES + EXISTING + ('companies','entities','engagements','profiles'))
FIXTURE = Path(__file__).parents[1]/'tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx'
RAW_SHA = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'


def require(value):
    if not value:
        raise ValueError('V40_PREFLIGHT_REFUSED')


def digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest().upper()


class ReadOnlyClient:
    def __init__(self, key, *, transport=None):
        require(type(key) is str and bool(key.strip()))
        self.client = httpx.Client(base_url=URL,headers={'apikey':key,'Authorization':'Bearer '+key},
                                  timeout=30,follow_redirects=False,trust_env=False,transport=transport)

    def rows(self, table, **filters):
        require(table in READABLE)
        require(all(k in {'id','company_id','entity_id','name'} and type(v) is str for k,v in filters.items()))
        response = self.client.get('/rest/v1/'+table,params={'select':'*','limit':'1001',
                                        **{k:'eq.'+v for k,v in filters.items()}})
        require(response.status_code==200)
        rows=response.json()
        require(type(rows) is list and len(rows)<1000 and all(type(r) is dict for r in rows))
        return rows

    def close(self):
        self.client.close()


def inspect(db):
    require(sha256(FIXTURE.read_bytes()).hexdigest().upper()==RAW_SHA)
    require(all(db.rows(t)==[] for t in REGISTRIES))
    companies=db.rows('companies',name='Pepperyn A24 Isolation Synthetic 1')
    require(len(companies)==1)
    company=companies[0]
    actor=str(UUID(company['admin_user_id'])); tenant=str(UUID(company['id']))
    profiles=db.rows('profiles',id=actor)
    require(len(profiles)==1 and profiles[0]['id']==actor and profiles[0]['company_id']==tenant)
    entities=db.rows('entities',company_id=tenant)
    require(len(entities)==1 and entities[0]['name']=='Pepperyn A24 Isolation Synthetic 1'
            and entities[0]['is_primary'] is True and entities[0]['company_id']==tenant)
    entity=str(UUID(entities[0]['id']))
    engagements=db.rows('engagements',entity_id=entity)
    require(len(engagements)==1 and engagements[0]['entity_id']==entity)
    engagement=str(UUID(engagements[0]['id']))
    # Hashes only leave this function; no underlying row is printed or persisted.
    snapshots={}
    for t in EXISTING:
        rows=db.rows(t)
        snapshots[t]={'count':len(rows),'sha256':digest(sorted(rows,key=digest))}
    return {'status':'V40_SERVICE_READ_ONLY_PREFLIGHT_PASS','project':URL,
            'scope':{'actor_id':actor,'company_id':tenant,'entity_id':entity,'engagement_id':engagement},
            'source_sha256':RAW_SHA,'baseline':snapshots,'new_registries_empty':True,
            'authenticated_actor_proven':False,'schema_catalog_verified_by_this_script':False,
            'effect_attempts':0,'auth_attempts':0,'business_write_performed':False,
            'rehearsal_ready':False,'external_provider_used':False,'real_data_used':False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args(); db=None
    try:
        if args.check:
            require(args.output is None)
            require(sha256(FIXTURE.read_bytes()).hexdigest().upper()==RAW_SHA)
            print(json.dumps({'status':'V40_PREFLIGHT_LOCAL_CHECK_PASS','network_used':False,
                              'secret_read':False,'business_write_performed':False}))
            return 0
        require(args.output is not None)
        require(not args.output.exists())
        require(os.environ.get('PEPPERYN_V40_PREFLIGHT_AUTHORIZATION')=='READ_ONLY_NO_LOGIN')
        db=ReadOnlyClient(os.environ['PEPPERYN_ISOLATION_SERVICE_KEY'])
        result=inspect(db)
        with args.output.open('x',encoding='utf-8') as stream:
            json.dump(result,stream,sort_keys=True)
        print(json.dumps({k:v for k,v in result.items() if k not in {'scope','baseline'}}))
        return 0
    except Exception:
        print(json.dumps({'status':'V40_SERVICE_PREFLIGHT_REFUSED','effect_attempts':0,
                          'auth_attempts':0,'automatic_retry_permitted':False}))
        return 1
    finally:
        if db is not None: db.close()


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    raise SystemExit(main())
