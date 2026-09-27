"""Local fake database only; cannot establish live successor eligibility."""
import copy
import json
import sys
import pytest
from sandbox import renew_connected_b1 as renewal
from test_governed_analysis_persistence import _Db


@pytest.fixture
def scenario(tmp_path,monkeypatch):
    class Database(_Db):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.client=self
        def close(self): pass
    db=Database(dict(entities=[dict(id=renewal.ENTITY,company_id=renewal.COMPANY,name='Optilux Synthetic Internal Pilot')],
        companies=[dict(id=renewal.COMPANY)],engagements=[dict(id='40000000-0000-0000-0000-000000000001',entity_id=renewal.ENTITY)]))
    data=dict(phase='B1_READ_ONLY_PREFLIGHT_PASS',analysis_id=renewal.ANALYSIS,company_id=renewal.COMPANY,
        entity_id=renewal.ENTITY,engagement_id=db.tables['engagements'][0]['id'],project_url=renewal.PROJECT,
        source_sha256=renewal.SOURCE_HASH,filename=renewal.FILENAME,
        expires_at='2000-01-01T00:00:00+00:00',baseline=renewal.scoped_snapshot(db,renewal.COMPANY))
    old=tmp_path/'b1-connected-rehearsal.json'; old.write_text(json.dumps(data),encoding='utf-8')
    old.with_suffix('.closed').write_text('CLOSED')
    successor=tmp_path/'b1-connected-rehearsal-r2.json'
    monkeypatch.setattr(renewal,'OLD_HASH',renewal.digest(old))
    monkeypatch.setattr(renewal,'CLOSED_HASH',renewal.digest(old.with_suffix('.closed')))
    monkeypatch.setattr(renewal,'ReadOnlyDatabase',lambda key:db)
    for key,value in dict(SUPABASE_URL=renewal.PROJECT,ENVIRONMENT='development',
        PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO='1',PEPPERYN_SYNTHETIC_V1_COMPANY_ID=renewal.COMPANY,
        PEPPERYN_GOVERNED_PIPELINE_TRANSPORT='0',SUPABASE_SERVICE_KEY='LOCAL_TEST_NOT_A_KEY').items():
        monkeypatch.setenv(key,value)
    monkeypatch.setattr(sys,'argv',['renew','--previous',str(old),'--successor',str(successor)])
    return db,data,old,successor


def test_successor_same_uuid_old_bytes_unchanged_read_only_and_not_reusable(scenario,capsys):
    db,data,old,new=scenario
    before=copy.deepcopy(db.tables); oldbytes=old.read_bytes(); closed=old.with_suffix('.closed').read_bytes()
    assert renewal.main()==0
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='B1_SUCCESSOR_PERMIT_CREATED'
    successor=json.loads(new.read_text())
    assert successor['analysis_id']==data['analysis_id']==renewal.ANALYSIS
    assert successor['baseline']==data['baseline']
    assert successor['predecessor_sha256']==renewal.digest(old)
    assert old.read_bytes()==oldbytes and old.with_suffix('.closed').read_bytes()==closed
    assert db.tables==before and all(entry[0]!='rpc' for entry in db.log)
    assert renewal.main()==1


@pytest.mark.parametrize('table',renewal.TABLES)
def test_uuid_anywhere_even_foreign_scope_refuses(scenario,table,capsys):
    db,data,old,new=scenario
    key='id' if table=='analyses' else 'analysis_id'
    db.tables[table]=[{key:renewal.ANALYSIS,'company_id':'foreign'}]
    assert renewal.main()==1
    assert json.loads(capsys.readouterr().out)['diagnostic']=='PROSPECTIVE_UUID_ALREADY_EXISTS'
    assert not new.exists() and new.with_suffix('.closed').exists()


def test_baseline_change_does_not_create_permit(scenario,capsys):
    db,data,old,new=scenario
    db.tables['entities'][0]['name']='changed'
    assert renewal.main()==1
    assert json.loads(capsys.readouterr().out)['diagnostic']=='PREEXISTING_BASELINE_CHANGED'
    assert not new.exists()


def test_closed_predecessor_cannot_hide_attempt_or_activation(scenario):
    _,_,old,new=scenario
    old.with_suffix('.attempt').write_text('unexpected')
    with pytest.raises(renewal.SafeRefusal,match='LOCAL_LINEAGE'):
        renewal.local_precheck(old,new)


def test_successor_cannot_replace_predecessor(scenario):
    _,_,old,_=scenario
    with pytest.raises(renewal.SafeRefusal,match='LOCAL_LINEAGE'):
        renewal.local_precheck(old,old)
