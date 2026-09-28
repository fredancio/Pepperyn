"""Complete 19-effect / seven-row LOCAL orchestration, real independent workers.

Actual V27/V39/V40 SQL in the previously isolated Docker test environment;
Auth and HTTP boundary mocked. No remote credentials or endpoint connections.
"""
import json
from uuid import uuid4
import pytest

from test_v40_postgres import sql as base_sql, ACTOR, COMPANY, ENTITY, ENGAGEMENT, CONTAINER, pytestmark
from v40_local_runner_support import factory, Reader, transport, successful, literal
from sandbox.preflight_v40_rehearsal import inspect
from sandbox.v40_rehearsal_budget import Budget, SLOTS
from sandbox.v40_rehearsal_orchestration import run_protocol
from sandbox.v40_rehearsal_processes import Workers
from sandbox.v40_rehearsal_owner import owner_sql


@pytest.fixture
def sql():
    # New isolated database for EACH whole-run falsification, never reset/replay.
    return base_sql.__wrapped__()


@pytest.mark.parametrize('fault',[None,'INVALID_SOURCE_SUCCEEDS','CLAIM_ACK_LOST','OWNER_INSERT_REFUSED'])
def test_full_local_sequence(sql,tmp_path,fault):
    path=tmp_path/'attempt.sqlite'
    journal=Budget.create(path)
    config={'database':sql.database,'container':CONTAINER,'journal':str(path),
        'policy_id':str(uuid4()),'fault':fault,'scope':{'actor_id':ACTOR,'company_id':COMPANY,'entity_id':ENTITY,'engagement_id':ENGAGEMENT}}
    reader=Reader(config);before=inspect(reader)
    auth=transport(config)
    session=auth.login_once(password='LOCAL_PASSWORD',expected_actor=ACTOR)
    memory={'session':session}
    db=factory(config,memory)
    def publish(manifest):
        with (tmp_path/'manifest.json').open('x') as f:json.dump(manifest,f)
    def owner(slot,manifest):
        journal.take(slot)
        if fault=='OWNER_INSERT_REFUSED':raise ValueError('OWNER_REFUSED')
        assert successful(config,owner_sql(slot,manifest))==slot+'_ACK'
    try:
        if fault:
            with pytest.raises(ValueError):
                run_protocol(db,before,publish=publish,owner=owner,workers=Workers(config,memory,factory=factory))
            assert journal.report()['auth_attempts']==1
            assert 'POLICY_DISABLE' not in journal.report()['slots']
            assert 'POSITIVE_COMPLETE' not in journal.report()['slots']
            assert successful(config,'SELECT count(*) FROM analyses')=='0'
            assert successful(config,'SELECT count(*) FROM governed_analysis_envelopes')=='0'
            assert successful(config,'SELECT count(*) FROM execution_receipts_v2')=='0'
            expected={'INVALID_SOURCE_SUCCEEDS':(4,1),'CLAIM_ACK_LOST':(15,3),'OWNER_INSERT_REFUSED':(2,0)}[fault]
            assert journal.report()['effect_attempts']==expected[0]
            assert successful(config,'SELECT count(*) FROM execution_admissions_v2')==str(expected[1])
            return
        result=run_protocol(db,before,publish=publish,owner=owner,workers=Workers(config,memory,factory=factory))
        assert result['status']=='BOUNDED_V40_REHEARSAL_PASS'
        assert result['new_durable_rows']==7
        assert result['admission_states']=={'ROLLBACK':'REFUSED','ABANDON':'CLOSED','POSITIVE':'COMPLETE'}
        assert set(journal.report()['slots'])==set(SLOTS)
        assert journal.report()['effect_attempts']==19 and journal.report()['auth_attempts']==1
        assert successful(config,'SELECT count(*) FROM producer_policies_v2')=='1'
        assert successful(config,'SELECT count(*) FROM execution_admissions_v2')=='3'
        assert successful(config,'SELECT count(*) FROM execution_receipts_v2')=='1'
        for path in tmp_path.iterdir():
            assert b'LOCAL_TOKEN' not in path.read_bytes() and b'LOCAL_PASSWORD' not in path.read_bytes()
    finally:
        db.reader.close();db.transport.close();auth.close()
