"""Local application wiring only: fake auth/database, no live/SQL/Beta proof."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from services.governed_pipeline_mount import mount_governed_pipeline, URL
from test_governed_analysis_persistence import _Db, _Rpc, _db, COMPANY_A, COMPANY_B, ENTITY_A, ENTITY_B
from test_governed_output_composition import extract

NAME = 'pepperyn_v1_heterogeneous_english.xlsx'
RAW = Path('tests/golden/fixtures', NAME).read_bytes()


class LocalDatabase(_Db):
    """RPC test double; SQL atomicity is separately proven by V39, not here."""
    def rpc(self, name, params):
        assert name == 'persist_governed_execution_v1'
        self.log.append(('rpc', name))
        db = self
        class Call:
            def execute(self):
                result = _Rpc(db, params).execute()
                receipt = copy.deepcopy(params['p_receipt'])
                scope = {k: receipt['payload'][k] for k in ('analysis_id','company_id','entity_id','engagement_id')}
                db.tables.setdefault('governed_execution_receipts', []).append(receipt | scope)
                return result
        return Call()


@pytest.fixture
def environment(monkeypatch,tmp_path):
    import services.governed_rehearsal_permit as permits
    monkeypatch.setattr(permits,'COMPANY',COMPANY_A)
    monkeypatch.setattr(permits,'ENTITY',ENTITY_A)
    manifest=tmp_path/'rehearsal.json'
    from test_governed_analysis_persistence import ENGAGEMENT_A, ANALYSIS
    manifest.write_text(json.dumps(dict(phase='B1_READ_ONLY_PREFLIGHT_PASS',project_url=URL,
        company_id=COMPANY_A,entity_id=ENTITY_A,engagement_id=ENGAGEMENT_A,analysis_id=ANALYSIS,
        filename=permits.FILENAME,source_sha256=permits.SOURCE_HASH,
        baseline=permits.scoped_snapshot(LocalDatabase(_db().tables),COMPANY_A),
        expires_at=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())),encoding='utf-8')
    monkeypatch.setenv('PEPPERYN_GOVERNED_REHEARSAL_MANIFEST',str(manifest))
    for k, v in dict(PEPPERYN_GOVERNED_PIPELINE_TRANSPORT='1', ENVIRONMENT='development',
                     SUPABASE_URL=URL, PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO='1',
                     PEPPERYN_SYNTHETIC_V1_COMPANY_ID=COMPANY_A).items():
        monkeypatch.setenv(k,v)


async def auth(authorization, auth_type):
    if authorization not in ('Bearer owner', 'Bearer foreign', 'Bearer guest'):
        raise HTTPException(401)
    return (COMPANY_B if authorization == 'Bearer foreign' else COMPANY_A,
            'free', 'guest' if authorization == 'Bearer guest' else 'admin')


def client_for(db):
    app = FastAPI()
    emulate_loopback(app)
    mounted = mount_governed_pipeline(app, database=lambda: db, resolve_auth=auth)
    return TestClient(app), mounted


def emulate_loopback(app):
    @app.middleware('http')
    async def local_request(request,call_next):
        request.scope['client']=('127.0.0.1',12345)
        return await call_next(request)


def upload(client, *, token='owner', entity=ENTITY_A, raw=RAW, name=NAME):
    headers = {'Authorization':'Bearer '+token} if token else {}
    return client.post('/api/governed/analyses', headers=headers,
                       data={'entity_id':entity}, files={'file':(name,raw)})


def test_full_upload_receipt_read_three_exports_and_fresh_application(environment):
    db = LocalDatabase(_db().tables)
    client, mounted = client_for(db)
    assert mounted
    response = upload(client)
    assert response.status_code == 201, response.text
    identity = response.json()['analysis_id']
    assert response.json()['automatic_retry_permitted'] is False
    assert [len(db.tables[t]) for t in ('analyses','governed_analysis_envelopes','governed_execution_receipts')] == [1,1,1]
    before = copy.deepcopy(db.tables)
    # Reconstruct the application against the same stored state, not a real restart.
    client, _ = client_for(LocalDatabase(db.tables))
    url = '/api/governed/analyses/' + identity
    headers = {'Authorization':'Bearer owner'}
    result = client.get(url, headers=headers)
    assert result.status_code == 200, result.text
    receipt = result.json()['execution_provenance']['receipt']
    assert result.json()['analysis_id'] == identity
    stored = db.tables['governed_execution_receipts'][0]['payload']
    assert stored['analysis_id'] == identity
    assert stored['company_id'] == COMPANY_A and stored['entity_id'] == ENTITY_A
    for format in ('xlsx','pdf','pptx'):
        response = client.get(url+'/export.'+format,headers=headers)
        assert response.status_code == 200, response.text
        text = extract(format,response.content)
        for value in (identity,receipt['execution_id'],receipt['raw_source_sha256'],receipt['envelope_sha256']):
            assert value in text
        assert 'UNKNOWN' in text and 'Fournisseur simule local' in text
        assert client.get(url+'/export.'+format,headers={'Authorization':'Bearer foreign'}).status_code == 404
    assert client.get(url,headers={'Authorization':'Bearer foreign'}).status_code == 404
    assert db.tables == before


@pytest.mark.parametrize('kwargs,status', [
    ({'token':None},401), ({'token':'guest'},404), ({'token':'foreign'},404),
    ({'entity':ENTITY_B},404), ({'name':'unregistered.xlsx'},503),
    ({'raw':RAW+b'changed'},503), ({'raw':b'x'*1_000_001},413),
])
def test_upload_denials_do_not_persist(environment,kwargs,status):
    db = LocalDatabase(_db().tables)
    before = copy.deepcopy(db.tables)
    client,_ = client_for(db)
    assert upload(client,**kwargs).status_code == status
    assert db.tables == before and not any(x[0]=='rpc' for x in db.log)


def test_uncertain_persistence_is_not_retried(environment):
    db = LocalDatabase(_db().tables,fail_rpc=True)
    client,_ = client_for(db)
    response = upload(client)
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'PERSISTENCE_UNCERTAIN'
    assert response.json()['detail']['analysis_id']
    assert response.json()['detail']['automatic_retry_permitted'] is False
    assert len([x for x in db.log if x[0]=='rpc']) == 1


@pytest.mark.parametrize('engagements', [[], [{'id':'invalid','entity_id':ENTITY_A}]])
def test_missing_or_invalid_engagement_refuses_before_execution(environment,engagements):
    db=LocalDatabase(_db().tables)
    db.tables['engagements']=engagements
    client,_=client_for(db)
    assert upload(client).status_code in (404,503)
    assert not any(x[0]=='rpc' for x in db.log)


def test_executor_cannot_substitute_source_bytes():
    from services.governed_analysis_create import create_owned_analysis, GovernedCreateRefused
    from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
    db=LocalDatabase(_db().tables)
    with pytest.raises(GovernedCreateRefused,match='EXECUTION_REFUSED'):
        create_owned_analysis(db,company_id=COMPANY_A,entity_id=ENTITY_A,raw=b'different',filename=NAME,
            executor=lambda raw,name:run_recorded_registered_mock_analysis(RAW,NAME))
    assert not any(x[0]=='rpc' for x in db.log)


def test_default_has_no_new_routes(monkeypatch):
    monkeypatch.delenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT',raising=False)
    client,mounted = client_for(None)
    assert not mounted and upload(client).status_code == 404


@pytest.mark.parametrize('key,value', [('ENVIRONMENT','production'),('SUPABASE_URL','https://other.supabase.co'),
    ('PEPPERYN_SYNTHETIC_V1_COMPANY_ID',''),('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO','0')])
def test_invalid_activation_fails_startup(environment,monkeypatch,key,value):
    monkeypatch.setenv(key,value)
    with pytest.raises(HTTPException): client_for(None)


def test_runtime_closure_refuses_before_write(environment,monkeypatch):
    db=LocalDatabase(_db().tables)
    client,_=client_for(db)
    monkeypatch.setenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT','0')
    assert upload(client).status_code == 503
    assert not db.log


def test_main_composition_root_installs_same_path(environment,monkeypatch):
    # Real main import; substitute only auth/database at its composition boundary.
    import importlib
    import services.governed_pipeline_mount as wiring
    db=LocalDatabase(_db().tables)
    def local_install(app, **ignored):
        emulate_loopback(app)
        return mount_governed_pipeline(app,database=lambda:db,resolve_auth=auth)
    with monkeypatch.context() as scoped:
        scoped.setattr(wiring,'mount_governed_pipeline',local_install)
        import main
        importlib.reload(main)
        response=upload(TestClient(main.app))
        assert response.status_code == 201, response.text
    # Restore closed default application to avoid cross-test global state.
    with monkeypatch.context() as scoped:
        scoped.setenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT','0')
        scoped.setenv('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO','0')
        importlib.reload(main)
