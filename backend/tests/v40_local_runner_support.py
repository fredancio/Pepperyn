"""Test-only Docker transport; no cloud connectivity and no real credentials."""
import json
import subprocess
import time

import httpx

from sandbox.preflight_v40_rehearsal import EXISTING, REGISTRIES
from sandbox.v40_rehearsal_budget import Budget
from sandbox.v40_rehearsal_transport import RehearsalTransport
from sandbox.v40_rehearsal_orchestration import Backend, profile_for


def literal(value):
    return "'"+str(value).replace("'","''")+"'"


def query(config, sql):
    if not config['database'].startswith('b1_v40_') or config['container']!='pepperyn-b1-pg16-20260928':
        raise ValueError('LOCAL_ONLY')
    return subprocess.run(['docker','exec','-i','-u','postgres',config['container'],
        'psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-d',config['database']],
        input=sql.encode(),capture_output=True,timeout=35)


def successful(config, sql):
    result=query(config,sql)
    if result.returncode: raise AssertionError(result.stderr.decode())
    return result.stdout.decode().strip()


class Reader:
    def __init__(self,config):self.config=config
    def close(self):pass
    def rows(self, table, **filters):
        assert table in EXISTING+REGISTRIES+('companies','entities','profiles','engagements')
        if table in EXISTING and table not in ('analyses','governed_analysis_envelopes','governed_execution_receipts'):
            rows=[]  # Reduced local parent schema; explicitly not full deployment proof.
        else:
            rows=json.loads(successful(self.config,f"SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM public.{table} t"))
        if table=='companies':
            for row in rows:row.update(admin_user_id=self.config['scope']['actor_id'],name='Pepperyn A24 Isolation Synthetic 1')
        if table=='entities':
            for row in rows:row.update(name='Pepperyn A24 Isolation Synthetic 1',is_primary=True)
        return [r for r in rows if all(r.get(k)==v for k,v in filters.items())]


def transport(config):
    actor=config['scope']['actor_id']
    def handle(request):
        assert request.url.host=='ejixkplrgobgwqnhidwt.supabase.co'
        if request.url.path=='/auth/v1/token':
            return httpx.Response(200,json={'access_token':'LOCAL_TOKEN','token_type':'bearer',
                'expires_in':3600,'expires_at':time.time()+3600,
                'user':{'id':actor,'role':'authenticated','email':'pepperyn-isolation-a24-a@pepperyn-test.invalid'}})
        if request.url.path=='/auth/v1/user':
            assert request.method=='GET' and request.headers['Authorization']=='Bearer LOCAL_TOKEN'
            return httpx.Response(200,json={'id':actor})
        assert request.url.path.startswith('/rest/v1/rpc/') and request.method=='POST'
        name=request.url.path.rsplit('/',1)[-1]
        assert name in {'reserve_execution_v2','claim_execution_v2','complete_execution_v2','close_execution_v2'}
        params=json.loads(request.content)
        if config.get('fault')=='INVALID_SOURCE_SUCCEEDS' and name=='reserve_execution_v2' and params['p_bindings']['raw_source_sha256']=='0'*64:
            from sandbox.preflight_v40_rehearsal import RAW_SHA
            params['p_bindings']['raw_source_sha256']=RAW_SHA
        args=','.join(k+' => '+(literal(json.dumps(v,ensure_ascii=False))+'::jsonb' if isinstance(v,dict) else literal(v)) for k,v in params.items())
        result=query(config,f'SET ROLE service_role; SELECT public.{name}({args})')
        if result.returncode:
            # Exact expected RAISE paths; unrelated SQL/transport failures are 500.
            msg=result.stderr.decode()
            code='P0001' if any(s in msg for s in ('V40 policy binding refused','V40 policy/source/input refused',
                 'V40 claim refused','V40 completion authority refused')) else 'UNEXPECTED'
            return httpx.Response(400 if code=='P0001' else 500,json={'code':code})
        value=result.stdout.decode().strip()
        if config.get('fault')=='CLAIM_ACK_LOST' and name=='claim_execution_v2':
            row=json.loads(value)
            # Lose only the positive claim acknowledgment; earlier abandon phase unaffected.
            count=int(successful(config,'SELECT count(*) FROM execution_admissions_v2'))
            if count==3 and row['status']=='CLAIMED':return httpx.Response(504,json={'code':'UNCERTAIN'})
        return httpx.Response(200,json=value if name=='close_execution_v2' else json.loads(value))
    return RehearsalTransport(budget=Budget(config['journal']),anon_key='LOCAL_ANON',service_key='LOCAL_SERVICE',transport=httpx.MockTransport(handle))


def factory(config, memory):
    return Backend(Reader(config),transport(config),memory['session'],profile_for(config['scope']),config['policy_id'])
