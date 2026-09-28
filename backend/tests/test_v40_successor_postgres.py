"""New local databases only; populated failed-history preservation end to end."""
import copy
import json
from uuid import uuid4
import pytest

from test_v40_postgres import (sql as base_sql, setup, reserve, claim, bundle, finish,
    literal, ACTOR, COMPANY, ENTITY, ENGAGEMENT, CONTAINER, pytestmark)
from v40_local_runner_support import Reader, transport, successful, query
from v40_successor_local_support import factory
from sandbox.preflight_v40_rehearsal import inspect, digest, REGISTRIES
from sandbox.v40_successor_history import (snapshot, HistoryReader, assert_fresh_identities,
    catalog_history_sql, owner_sql)
from sandbox.v40_rehearsal_budget import Budget, SLOTS
from sandbox.v40_rehearsal_processes import Workers
from sandbox.v40_rehearsal_orchestration import run_protocol


def historical_seed(sql):
    original=setup(sql);cases={}
    for label in ('ROLLBACK','ABANDON','POSITIVE'):
        case=copy.deepcopy(original)
        case['b'].update({k:str(uuid4()) for k in ('analysis_id','execution_id','request_id')})
        r=reserve(sql,case);c=claim(sql,case,r)
        if label=='ABANDON':
            assert sql(f"SET ROLE service_role; SELECT close_execution_v2({literal(case['b']['execution_id'])},{literal(ACTOR)})")=='CLOSED'
        else:
            parts=bundle(case,c)
            if label=='POSITIVE':parts[1]['type_document']='FINANCIAL_WORKBOOK'
            else:parts[2]['binding_sha256']='INVALID'
            assert finish(sql,case,c,parts)['status']=='REFUSED'
        cases[label]=case['b']
    sql(f"UPDATE producer_policies_v2 SET enabled=false WHERE id={literal(original['policy'])}")
    p=json.loads(sql('SELECT to_jsonb(t) FROM producer_policies_v2 t'))
    manifest=dict(policy_id=p['id'],profile=p['specification'],contract_sha256=p['contract_sha256'],cases=cases)
    anchor=sql("SELECT encode(sha256(convert_to(jsonb_agg(to_jsonb(t) ORDER BY execution_id)::text,'UTF8')),'hex') FROM execution_admissions_v2 t")
    return manifest,anchor


@pytest.mark.parametrize('fault',[None,'ANCHOR_MISMATCH','NEW_ID_COLLISION'])
def test_successor_populated_history(tmp_path,fault):
    sql=base_sql.__wrapped__()
    old,anchor=historical_seed(sql)
    config={'database':sql.database,'container':CONTAINER,'journal':str(tmp_path/'effects.sqlite'),
            'policy_id':str(uuid4()),'scope':dict(actor_id=ACTOR,company_id=COMPANY,entity_id=ENTITY,engagement_id=ENGAGEMENT)}
    raw=Reader(config);history=snapshot(raw,old);config['history']=history
    before=inspect(HistoryReader(raw,history))
    assert successful(config,catalog_history_sql(history,anchor))=='V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS'
    journal=Budget.create(config['journal'])
    if fault=='ANCHOR_MISMATCH':
        assert query(config,catalog_history_sql(history,'0'*64)).returncode!=0
        assert journal.report()['effect_attempts']==0
        return
    auth=transport(config);session=auth.login_once(password='LOCAL_PASSWORD',expected_actor=ACTOR)
    memory={'session':session};db=factory(config,memory)
    if fault=='NEW_ID_COLLISION':db.policy_id=old['policy_id']
    manifests=[]
    def publish(m):
        assert_fresh_identities(raw,m,history);manifests.append(m)
    def owner(slot,m):
        journal.take(slot)
        assert successful(config,owner_sql(slot,m,history,anchor))==slot+'_ACK'
    try:
        if fault:
            with pytest.raises(ValueError):
                run_protocol(db,before,publish=publish,owner=owner,workers=Workers(config,memory,factory=factory))
            assert journal.report()['effect_attempts']==1 and manifests==[]
        else:
            result=run_protocol(db,before,publish=publish,owner=owner,workers=Workers(config,memory,factory=factory))
            assert result['new_durable_rows']==7 and result['independent_recovery']
            assert result['admission_states']==dict(ROLLBACK='REFUSED',ABANDON='CLOSED',POSITIVE='COMPLETE')
            assert journal.report()['effect_attempts']==19 and journal.report()['auth_attempts']==1
            assert set(journal.report()['slots'])==set(SLOTS)
            assert successful(config,'SELECT count(*) FROM producer_policies_v2')=='2'
            assert successful(config,'SELECT count(*) FROM execution_admissions_v2')=='6'
            assert successful(config,'SELECT count(*) FROM execution_receipts_v2')=='1'
            assert successful(config,'SELECT count(*) FROM analyses')=='1'
            assert successful(config,'SELECT count(*) FROM governed_analysis_envelopes')=='1'
        for t in REGISTRIES:
            key='id' if t==REGISTRIES[0] else 'execution_id'
            ids={r[key] for r in history[t]}
            assert digest(sorted([r for r in raw.rows(t) if r[key] in ids],key=digest))==digest(sorted(history[t],key=digest))
        assert successful(config,f"SELECT enabled FROM producer_policies_v2 WHERE id={literal(old['policy_id'])}")=='f'
        for p in tmp_path.iterdir():
            assert b'LOCAL_TOKEN' not in p.read_bytes() and b'LOCAL_PASSWORD' not in p.read_bytes()
    finally:
        db.reader.close();db.transport.close();auth.close()


@pytest.mark.parametrize('identity_fault',[None,'PREAUTH_COLLISION','POSTAUTH_SUBSTITUTION'])
def test_complete_new_entrypoint_local_only(tmp_path,monkeypatch,capsys,identity_fault):
    """Real successor main, journal, tickets, mock Auth, actual SQL and workers."""
    import io
    from datetime import datetime,timezone
    from hashlib import sha256
    import sandbox.run_v40_successor as runner
    sql=base_sql.__wrapped__();old,anchor=historical_seed(sql)
    attempt=tmp_path/'successor'
    config={'database':sql.database,'container':CONTAINER,'journal':str(attempt/'effects.sqlite'),
            'scope':dict(actor_id=ACTOR,company_id=COMPANY,entity_id=ENTITY,engagement_id=ENGAGEMENT)}
    raw=Reader(config);h=snapshot(raw,old)
    oldpath=tmp_path/'old-manifest.json';oldpath.write_text(json.dumps(old))
    baseline=tmp_path/'baseline.json';baseline.write_text(json.dumps(inspect(HistoryReader(raw,h))))
    monkeypatch.setattr(runner,'ATTEMPT',attempt)
    monkeypatch.setattr(runner,'OLD_MANIFEST',oldpath)
    monkeypatch.setattr(runner,'BASELINE',baseline)
    monkeypatch.setattr(runner,'PINS',{p:sha256(p.read_bytes()).hexdigest().upper() for p in (oldpath,baseline)})
    monkeypatch.setattr(runner,'HISTORICAL_POLICY',old['policy_id'])
    monkeypatch.setattr(runner,'HISTORICAL_ADMISSIONS_SHA',anchor)
    if identity_fault=='PREAUTH_COLLISION':
        from uuid import UUID
        plan=runner.IdentityPlan.create()
        collided=runner.IdentityPlan(UUID(old['policy_id']),plan.triples)
        monkeypatch.setattr(runner.IdentityPlan,'create',classmethod(lambda cls:collided))
    if identity_fault=='POSTAUTH_SUBSTITUTION':
        original_backend=runner.Backend
        def substituted_backend(*args,**kwargs):
            foreign=runner.IdentityPlan.create()
            kwargs['identity_source']=runner.IdentityConsumption(foreign,foreign.commitment())
            return original_backend(*args,**kwargs)
        monkeypatch.setattr(runner,'Backend',substituted_backend)
    monkeypatch.setattr(runner,'ReadOnlyClient',lambda key:Reader(config))
    def checked_transport(**kw):
        checked=json.loads((attempt/'prechecked-identities.json').read_text())
        assert checked['auth_attempts']==checked['effect_attempts']==0
        assert Budget(config['journal']).report()['effect_attempts']==0
        assert_fresh_identities(raw,checked['manifest'],h)
        return transport(config)
    monkeypatch.setattr(runner,'RehearsalTransport',checked_transport)
    monkeypatch.setattr(runner,'Workers',lambda cfg,mem,**kw:Workers(dict(cfg,**{k:config[k] for k in ('container','database')}),mem,factory=factory))
    write=runner.write_new
    def local_operator(path,value):
        write(path,value)
        if path.name=='catalog-request.json':
            assert successful(config,value['sql'])=='V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS'
            from sandbox.preflight_v40_rehearsal import URL
            write(attempt/'catalog-ready.json',dict(version='v40-successor-readiness-1',project=URL,
                definition_status='BOUNDED_DEFINITION_CONFORMANCE_PASS',structure_verified=True,
                observed_at=datetime.now(timezone.utc).isoformat(),effect_ceiling=19,row_ceiling=7,
                history_status='V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS',
                historical_snapshot_sha256=value['historical_snapshot_sha256'],sql_sha256=value['sql_sha256']))
        elif path.name in ('policy_insert.json','policy_disable.json'):
            assert value['action'] in Budget(config['journal']).report()['slots']
            assert sha256(value['sql'].encode()).hexdigest().upper()==value['sql_sha256']
            assert successful(config,value['sql'])==value['action']+'_ACK'
    monkeypatch.setattr(runner,'write_new',local_operator)
    from sandbox.preflight_v40_rehearsal import URL
    packet=dict(anon='LOCAL_ANON',service='LOCAL_SERVICE',authorization='V40_SUCCESSOR_1_DISTINCT_GO_19_EFFECTS_7_NEW_ROWS',
        bundle=dict(project_url=URL,purpose='A24_TECHNICAL_ISOLATION_ONLY',accounts=[
            dict(email='pepperyn-isolation-a24-a@pepperyn-test.invalid',password='LOCAL_PASSWORD'),{}]))
    monkeypatch.setattr(runner.sys,'argv',['successor','--execute'])
    monkeypatch.setattr(runner.sys,'stdin',io.StringIO(json.dumps(packet)))
    if identity_fault:
        assert runner.main()==1
        refused=json.loads((attempt/'refused.json').read_text())
        expected=0 if identity_fault=='PREAUTH_COLLISION' else 1
        assert refused['auth_attempts']==refused['effect_attempts']==expected
        assert refused['stage']==('PRE_AUTH_FROZEN_IDENTITIES' if expected==0 else 'SUCCESSOR_PROTOCOL')
        assert not (attempt/'policy_insert.json').exists() and not (attempt/'manifest.json').exists()
        assert snapshot(raw,old)==h
        assert successful(config,'SELECT count(*) FROM analyses')=='0'
        assert successful(config,'SELECT count(*) FROM governed_analysis_envelopes')=='0'
        assert successful(config,'SELECT count(*) FROM execution_receipts_v2')=='0'
        assert not (attempt/'result.json').exists()
        return
    assert runner.main()==0
    result=json.loads((attempt/'result.json').read_text())
    assert result['status']=='BOUNDED_V40_SUCCESSOR_PASS'
    assert result['historical_rows_unchanged']==4 and result['total_evidence_rows']==11
    assert result['new_durable_rows']==7 and result['effect_attempts']==19 and result['auth_attempts']==1
    assert result['generic_producer_admitted'] is False
    assert result['b1_global_proven'] is False
    checked=json.loads((attempt/'prechecked-identities.json').read_text())
    composed=json.loads((attempt/'manifest.json').read_text())
    assert result['prechecked_composed_persisted_identity_match'] is True
    assert result['preauth_identity_commitment']==checked['sha256']
    assert composed['policy_id']==checked['manifest']['policy_id']
    persisted={a['execution_id']:a for a in raw.rows('execution_admissions_v2')}
    for label,ids in checked['manifest']['cases'].items():
        assert {k:composed['cases'][label][k] for k in ids}==ids
        assert {k:persisted[ids['execution_id']][k] for k in ids}==ids
    assert checked['manifest']['policy_id'] in {p['id'] for p in raw.rows('producer_policies_v2')}
    output=capsys.readouterr().out
    for secret in ('LOCAL_TOKEN','LOCAL_PASSWORD','LOCAL_SERVICE','LOCAL_ANON'):
        assert secret not in output
        assert all(secret.encode() not in p.read_bytes() for p in attempt.iterdir())
    # The same entry point MUST refuse a second invocation before reading stdin.
    assert runner.main()==1
    assert json.loads(capsys.readouterr().out)['stage']=='LOCAL_CHECK'
