import copy
import json
import multiprocessing
from uuid import uuid4

import httpx
import pytest

from sandbox.v40_rehearsal_budget import Budget, BudgetRefused, SLOTS
from sandbox.preflight_v40_rehearsal import ReadOnlyClient, inspect, REGISTRIES, EXISTING, URL


def take_slot(path, slot, queue):
    try:
        queue.put(('TAKEN',Budget(path).take(slot)))
    except BudgetRefused:
        queue.put(('REFUSED',None))


def test_one_login_even_with_two_independent_processes(tmp_path):
    path=tmp_path/'attempt.sqlite'
    journal=Budget.create(path)
    ctx=multiprocessing.get_context('spawn'); queue=ctx.Queue()
    children=[ctx.Process(target=take_slot,args=(str(path),'AUTH_ONCE',queue)) for _ in range(2)]
    for child in children: child.start()
    for child in children:
        child.join(15)
        assert child.exitcode==0
    assert sorted(queue.get(timeout=2)[0] for _ in children)==['REFUSED','TAKEN']
    assert journal.report()['auth_attempts']==1


def test_global_19_slots_and_no_replay_reset_refresh(tmp_path):
    path=tmp_path/'attempt.sqlite'; journal=Budget.create(path)
    with pytest.raises(BudgetRefused): journal.take('POLICY_INSERT')
    assert journal.report()['effect_attempts']==0
    for i,slot in enumerate(SLOTS,1): assert journal.take(slot)==i
    assert journal.report()['effect_attempts']==19
    for slot in SLOTS+('AUTH_REFRESH','SECOND_LOGIN','OTHER_RPC'):
        with pytest.raises(BudgetRefused): Budget(path).take(slot)
    with pytest.raises(FileExistsError): Budget.create(path)
    assert journal.report()['auth_attempts']==1


def test_closed_missing_and_corrupt_journals_refuse(tmp_path):
    with pytest.raises(BudgetRefused): Budget(tmp_path/'absent').take('AUTH_ONCE')
    path=tmp_path/'bad';path.write_bytes(b'partial')
    with pytest.raises(BudgetRefused): Budget(path).take('AUTH_ONCE')
    journal=Budget.create(tmp_path/'valid');journal.close()
    with pytest.raises(BudgetRefused): journal.take('AUTH_ONCE')


def data():
    actor,company,entity,engagement=[str(uuid4()) for _ in range(4)]
    tables={t:[] for t in REGISTRIES+EXISTING}
    tables.update(companies=[dict(id=company,admin_user_id=actor,name='Pepperyn A24 Isolation Synthetic 1')],
                  profiles=[dict(id=actor,company_id=company)],
                  entities=[dict(id=entity,company_id=company,name='Pepperyn A24 Isolation Synthetic 1',is_primary=True)],
                  engagements=[dict(id=engagement,entity_id=entity)])
    return tables


@pytest.mark.parametrize('fault',[None,'nonempty','foreign_profile','foreign_entity','foreign_engagement','duplicate','http','redirect','truncated'])
def test_read_only_preflight_with_no_login_or_effect(fault,capsys):
    tables=data(); requests=[]
    if fault=='nonempty': tables[REGISTRIES[0]]=[{'id':str(uuid4())}]
    if fault=='foreign_profile': tables['profiles'][0]['company_id']=str(uuid4())
    if fault=='foreign_entity': tables['entities'][0]['company_id']=str(uuid4())
    if fault=='foreign_engagement': tables['engagements'][0]['entity_id']=str(uuid4())
    if fault=='duplicate': tables['companies']*=2
    if fault=='truncated': tables['analyses']=[{'id':str(i)} for i in range(1000)]
    before=copy.deepcopy(tables)
    def responder(request):
        requests.append(request)
        assert request.method=='GET' and str(request.url).startswith(URL+'/rest/v1/')
        if fault=='http': return httpx.Response(500,json={'secret':'DO_NOT_ECHO'})
        if fault=='redirect': return httpx.Response(302,headers={'Location':'https://unrelated.invalid'})
        return httpx.Response(200,json=tables[request.url.path.split('/')[-1]])
    db=ReadOnlyClient('LOCAL_TEST_SECRET',transport=httpx.MockTransport(responder))
    try:
        if fault:
            with pytest.raises(ValueError,match='V40_PREFLIGHT_REFUSED'): inspect(db)
        else:
            result=inspect(db)
            assert result['effect_attempts']==result['auth_attempts']==0
            assert not result['rehearsal_ready'] and not result['authenticated_actor_proven']
            assert 'LOCAL_TEST_SECRET' not in json.dumps(result)
        assert tables==before
        assert requests and all('/auth/' not in str(r.url) for r in requests)
        assert not capsys.readouterr().out
    finally: db.close()


def test_unknown_path_refused_before_request():
    calls=[]
    db=ReadOnlyClient('LOCAL_TEST_SECRET',transport=httpx.MockTransport(lambda r:calls.append(r)))
    try:
        for table in ('https://other.invalid','../rpc/reserve_execution_v2','auth/v1/token'):
            with pytest.raises(ValueError): db.rows(table)
        assert calls==[]
    finally: db.close()
