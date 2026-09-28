"""No network/Auth: successor snapshot, collision and catalog gate falsifications."""
import copy
import json
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import pytest

from sandbox.preflight_v40_rehearsal import REGISTRIES,EXISTING,digest,URL
from sandbox.v40_successor_history import HistoryReader,assert_fresh_identities
from sandbox.run_v40_successor import wait_catalog,write_new


def specimen():
    p=dict(id=str(uuid4()),enabled=False,origin='SYNTHETIC',egress='DENY')
    admissions=[dict(execution_id=str(uuid4()),request_id=str(uuid4()),analysis_id=str(uuid4()),
                     policy_id=p['id'],state=s,input_text='synthetic evidence',claim_id=str(uuid4()))
                for s in ('REFUSED','CLOSED','REFUSED')]
    return dict(zip(REGISTRIES,([p],admissions,[])))


class Reader:
    def __init__(self,rows):self.data=copy.deepcopy(rows)
    def rows(self,t,**filters):return copy.deepcopy(self.data.get(t,[]))
    def close(self):pass


@pytest.mark.parametrize('fault',['enabled','missing_policy','missing_admission','state','input','claim','extra_field'])
def test_history_fail_closed(fault):
    h=specimen();raw=Reader(h);view=HistoryReader(raw,h)
    assert view.rows(REGISTRIES[0])==[]
    if fault=='enabled':raw.data[REGISTRIES[0]][0]['enabled']=True
    elif fault=='missing_policy':raw.data[REGISTRIES[0]]=[]
    elif fault=='missing_admission':raw.data[REGISTRIES[1]].pop()
    else:raw.data[REGISTRIES[1]][0][{'state':'state','input':'input_text','claim':'claim_id','extra_field':'unexpected'}[fault]]='changed'
    with pytest.raises(ValueError):view.rows('analyses')


def test_snapshot_not_mutable_alias_and_new_rows_not_hidden():
    h=specimen();raw=Reader(h);view=HistoryReader(raw,h)
    h[REGISTRIES[0]][0]['enabled']=True
    assert view.rows(REGISTRIES[0])==[]
    extra=dict(id=str(uuid4()),enabled=True)
    raw.data[REGISTRIES[0]].append(extra)
    assert view.rows(REGISTRIES[0])==[extra]


def manifest():
    return dict(policy_id=str(uuid4()),cases={label:{k:str(uuid4()) for k in ('execution_id','request_id','analysis_id')}
                for label in ('ROLLBACK','ABANDON','POSITIVE')})


@pytest.mark.parametrize('fault',['old_policy','old_execution','old_request','old_analysis','duplicate','existing_analysis','existing_receipt','none'])
def test_all_identity_domains(fault):
    h=specimen();raw=Reader(h);m=manifest()
    if fault=='old_policy':m['policy_id']=h[REGISTRIES[0]][0]['id']
    elif fault.startswith('old_'):
        k=fault[4:]+'_id';m['cases']['POSITIVE'][k]=h[REGISTRIES[1]][0][k]
    elif fault=='duplicate':m['cases']['POSITIVE']['analysis_id']=m['cases']['ROLLBACK']['request_id']
    elif fault=='existing_analysis':raw.data['analyses']=[{'id':m['cases']['POSITIVE']['analysis_id']}]
    elif fault=='existing_receipt':raw.data['governed_execution_receipts']=[{'analysis_id':m['cases']['POSITIVE']['analysis_id']}]
    if fault=='none':assert_fresh_identities(raw,m,h)
    else:
        with pytest.raises(ValueError):assert_fresh_identities(raw,m,h)


@pytest.mark.parametrize('fault',['none','stale','future','old_version','wrong_snapshot','wrong_sql','wrong_project','not_verified','budget','no_history'])
def test_catalog_bound_to_fresh_history(tmp_path,monkeypatch,fault):
    import sandbox.run_v40_successor as runner
    h=specimen()
    # Build exactly the same SQL ticket while retaining real version/digest checks.
    from sandbox.v40_successor_history import catalog_history_sql,HISTORICAL_ADMISSIONS_SHA
    from hashlib import sha256
    sql=catalog_history_sql(h,HISTORICAL_ADMISSIONS_SHA)
    now=datetime.now(timezone.utc)
    report=dict(version='v40-successor-readiness-1',project=URL,
        definition_status='BOUNDED_DEFINITION_CONFORMANCE_PASS',structure_verified=True,
        observed_at=now.isoformat(),effect_ceiling=19,row_ceiling=7,
        history_status='V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS',historical_snapshot_sha256=digest(h),
        sql_sha256=sha256(sql.encode()).hexdigest().upper())
    changes={'stale':('observed_at',(now-timedelta(seconds=181)).isoformat()),
        'future':('observed_at',(now+timedelta(seconds=90)).isoformat()),'old_version':('version','old'),
        'wrong_snapshot':('historical_snapshot_sha256','0'*64),'wrong_sql':('sql_sha256','0'*64),
        'wrong_project':('project','foreign'),'not_verified':('structure_verified',False),
        'budget':('effect_ceiling',20),'no_history':('history_status','UNKNOWN')}
    if fault!='none':key,value=changes[fault];report[key]=value
    write_new(tmp_path/'catalog-ready.json',report)
    if fault=='none':wait_catalog(tmp_path,h,timeout=1)
    else:
        with pytest.raises(ValueError):wait_catalog(tmp_path,h,timeout=1)
    assert not (tmp_path/'effects.sqlite').exists()


def test_exclusive_artifact_cannot_overwrite(tmp_path):
    p=tmp_path/'manifest.json';write_new(p,{'original':True})
    with pytest.raises(FileExistsError):write_new(p,{'replacement':True})
    assert json.loads(p.read_text())=={'original':True}


def test_default_launcher_never_reads_credentials(monkeypatch,capsys):
    import sandbox.run_v40_successor as runner
    class NoInput:
        def read(self,*a):raise AssertionError('Credential input forbidden')
    monkeypatch.setattr(runner,'check_local',lambda:None)
    monkeypatch.setattr(runner.sys,'argv',['successor'])
    monkeypatch.setattr(runner.sys,'stdin',NoInput())
    assert runner.main()==0
    assert json.loads(capsys.readouterr().out)['secret_read'] is False


def test_previous_authorization_cannot_launch_successor(tmp_path,monkeypatch,capsys):
    import io
    import sandbox.run_v40_successor as runner
    monkeypatch.setattr(runner,'check_local',lambda:None)
    monkeypatch.setattr(runner,'ATTEMPT',tmp_path/'new-attempt')
    monkeypatch.setattr(runner.sys,'argv',['successor','--execute'])
    monkeypatch.setattr(runner.sys,'stdin',io.StringIO(json.dumps(dict(
        anon='DO_NOT_LOG',service='DO_NOT_LOG',bundle={},authorization='V40_19_EFFECTS_7_ROWS_ONE_AUTH_ONLY'))))
    assert runner.main()==1
    output=capsys.readouterr().out
    assert json.loads(output)['stage']=='DISTINCT_AUTHORIZATION'
    assert 'DO_NOT_LOG' not in output and not runner.ATTEMPT.exists()
