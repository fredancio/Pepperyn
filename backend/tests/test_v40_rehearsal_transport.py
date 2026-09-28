import json
import time
from uuid import uuid4

import httpx
import pytest

from sandbox.v40_rehearsal_budget import Budget, BudgetRefused
from sandbox.v40_rehearsal_transport import (
    MemorySession, RehearsalTransport, TransportRefused, RPC_SLOTS,
)
from sandbox.preflight_v40_rehearsal import URL


def setup(tmp_path, responder):
    budget = Budget.create(tmp_path / 'attempt.sqlite')
    calls = []
    def handle(request):
        calls.append(request)
        assert request.url.scheme == 'https'
        assert request.url.host == 'ejixkplrgobgwqnhidwt.supabase.co'
        return responder(request)
    transport = RehearsalTransport(budget=budget, anon_key='TEST_ANON',
        service_key='TEST_SERVICE', transport=httpx.MockTransport(handle))
    return budget, calls, transport


def login_response(actor):
    return httpx.Response(200, json={'user': {'id': actor, 'role':'authenticated',
        'email':'pepperyn-isolation-a24-a@pepperyn-test.invalid'}, 'token_type': 'bearer',
        'access_token': 'TEST_TOKEN', 'refresh_token': 'TEST_REFRESH_NOT_RETAINED',
        'expires_in': 3600, 'expires_at': time.time() + 3600})


def test_single_login_secret_free_journal_and_session_repr(tmp_path, capsys):
    actor = str(uuid4())
    budget, calls, transport = setup(tmp_path, lambda r: login_response(actor))
    session = transport.login_once(password='TEST_PASSWORD', expected_actor=actor)
    with pytest.raises(BudgetRefused):
        transport.login_once(password='TEST_PASSWORD', expected_actor=actor)
    assert len(calls) == 1 and budget.report()['effect_attempts'] == 1
    assert str(calls[0].url) == URL + '/auth/v1/token?grant_type=password'
    assert json.loads(calls[0].content)['email'] == 'pepperyn-isolation-a24-a@pepperyn-test.invalid'
    assert set(vars(session)) == {'access_token', 'actor_id', 'expires_at'}
    assert 'TEST_' not in repr(session) + repr(transport) + json.dumps(budget.report())
    assert b'TEST_' not in (tmp_path / 'attempt.sqlite').read_bytes()
    assert capsys.readouterr().out == ''
    transport.close()


@pytest.mark.parametrize('fault', ['timeout', 'http', 'redirect', 'foreign_actor', 'expired', 'bad_json'])
def test_uncertain_login_never_retried(tmp_path, fault, capsys):
    actor = str(uuid4())
    def responder(request):
        if fault == 'timeout': raise httpx.ReadTimeout('TEST_SECRET_NEVER_PRINT', request=request)
        if fault == 'http': return httpx.Response(401, json={'message': 'TEST_SECRET_NEVER_PRINT'})
        if fault == 'redirect': return httpx.Response(307, headers={'location': 'https://foreign.invalid'})
        if fault == 'bad_json': return httpx.Response(200, text='TEST_SECRET_NEVER_PRINT')
        response = login_response(str(uuid4()) if fault == 'foreign_actor' else actor)
        if fault == 'expired':
            data = response.json(); data['expires_at'] = 0
            return httpx.Response(200, json=data)
        return response
    budget, calls, transport = setup(tmp_path, responder)
    with pytest.raises(TransportRefused, match='AUTH_FAILED_OR_UNCERTAIN_NO_RELOGIN'):
        transport.login_once(password='TEST_PASSWORD', expected_actor=actor)
    with pytest.raises(BudgetRefused):
        transport.login_once(password='TEST_PASSWORD', expected_actor=actor)
    assert len(calls) == 1 and budget.report()['auth_attempts'] == 1
    assert capsys.readouterr().out == ''
    transport.close()


def test_expiry_refuses_before_rpc_no_refresh(tmp_path):
    budget, calls, transport = setup(tmp_path, lambda r: None)
    session = MemorySession('TEST_TOKEN', str(uuid4()), 0)
    with pytest.raises(TransportRefused, match='SESSION_EXPIRED_NO_REFRESH'):
        transport.rpc_once('POSITIVE_CLAIM_A', name='claim_execution_v2', payload={}, session=session)
    assert calls == [] and budget.report()['effect_attempts'] == 0
    transport.close()


@pytest.mark.parametrize('slot,name', [('AUTH_ONCE','claim_execution_v2'),
    ('AUTH_REFRESH','token'), ('POLICY_INSERT','reserve_execution_v2'),
    ('POSITIVE_CLAIM_A','complete_execution_v2'), ('POSITIVE_CLAIM_A','../foreign')])
def test_substituted_request_never_sent(tmp_path, slot, name):
    budget, calls, transport = setup(tmp_path, lambda r: None)
    with pytest.raises(TransportRefused, match='RPC_SLOT_MISMATCH'):
        transport.rpc_once(slot, name=name, payload={}, session=None)
    assert calls == [] and budget.report()['effect_attempts'] == 0
    transport.close()


@pytest.mark.parametrize('fault', ['timeout', 'redirect', '401', '500', 'invalid_success'])
def test_uncertain_rpc_slot_consumed_no_automatic_second_request(tmp_path, fault):
    actor = str(uuid4())
    def responder(request):
        if request.method == 'GET': return httpx.Response(200, json={'id': actor})
        if fault == 'timeout': raise httpx.ReadTimeout('TEST_SECRET', request=request)
        if fault == 'redirect': return httpx.Response(307, headers={'location': '/rest/v1/rpc/claim_execution_v2'})
        if fault == 'invalid_success': return httpx.Response(200, json=[])
        return httpx.Response(int(fault), json={'message': 'TEST_SECRET'})
    budget, calls, transport = setup(tmp_path, responder)
    budget.take('AUTH_ONCE')
    session = MemorySession('TEST_TOKEN', actor, time.time() + 3600)
    with pytest.raises(TransportRefused, match='RPC_FAILED_OR_UNCERTAIN_NO_RETRY'):
        transport.rpc_once('POSITIVE_CLAIM_A', name='claim_execution_v2', payload={}, session=session)
    with pytest.raises(BudgetRefused):
        transport.rpc_once('POSITIVE_CLAIM_A', name='claim_execution_v2', payload={}, session=session)
    assert sum(r.method == 'POST' for r in calls) == 1
    assert budget.report()['effect_attempts'] == 2
    transport.close()


def test_16_rpc_slots_only_expected_refusal_is_safe_not_pass(tmp_path):
    actor = str(uuid4())
    def responder(request):
        if request.method == 'GET': return httpx.Response(200, json={'id': actor})
        return httpx.Response(400, json={'code':'P0001', 'message':'TEST_SECRET', 'detail':'TEST_SECRET'})
    budget, calls, transport = setup(tmp_path, responder)
    budget.take('AUTH_ONCE')
    session = MemorySession('TEST_TOKEN', actor, time.time() + 3600)
    assert len(RPC_SLOTS) == 16
    for slot, name in RPC_SLOTS.items():
        result = transport.rpc_once(slot, name=name, payload={}, session=session)
        assert result == {'status':'SQL_REFUSED', 'sqlstate':'P0001'}
    assert sum(r.method == 'POST' for r in calls) == 16
    assert budget.report()['effect_attempts'] == 17
    transport.close()


@pytest.mark.parametrize('result,accepted', [('CLOSED',True), ('COMPLETE',False),
    ({'status':'CLOSED'},False), (None,False)])
def test_close_requires_exact_sql_text_acknowledgment(tmp_path,result,accepted):
    actor=str(uuid4())
    def responder(request):
        return httpx.Response(200,json={'id':actor} if request.method=='GET' else result)
    budget,calls,transport=setup(tmp_path,responder)
    budget.take('AUTH_ONCE')
    session=MemorySession('TEST_TOKEN',actor,time.time()+3600)
    try:
        if accepted:
            assert transport.rpc_once('ABANDON_CLOSE',name='close_execution_v2',payload={},session=session)=={'status':'CLOSED'}
        else:
            with pytest.raises(TransportRefused):
                transport.rpc_once('ABANDON_CLOSE',name='close_execution_v2',payload={},session=session)
        assert sum(r.method=='POST' for r in calls)==1
        assert budget.report()['effect_attempts']==2
    finally:
        transport.close()
