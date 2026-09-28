"""Local spawn/pipe integration of the intended token handoff, not live Auth.

No live runner is released by this test. No secrets in worker arguments, reports,
environment variables or local journal. HTTP is mocked; the process boundary is
real Windows/Python spawn, including a fully terminated first child.
"""
import multiprocessing
import os
import time
from uuid import uuid4

import httpx
import pytest

from sandbox.v40_rehearsal_budget import Budget
from sandbox.v40_rehearsal_transport import RehearsalTransport, MemorySession


def child_read(pipe, journal_path):
    client=None
    try:
        session=pipe.recv()
        requests=[]
        def respond(request):
            requests.append(request)
            # The inherited single token, never a newly logged-in session.
            assert request.method=='GET' and request.url.path=='/auth/v1/user'
            assert request.headers['authorization']=='Bearer '+session.access_token
            return httpx.Response(200,json={'id':session.actor_id})
        client=RehearsalTransport(budget=Budget(journal_path),anon_key='TEST_ANON',
            service_key='TEST_SERVICE',transport=httpx.MockTransport(respond))
        client.verify_actor(session)
        pipe.send({'status':'ACTOR_READ_ONLY','pid':os.getpid(),'reads':len(requests),
                   'auth_attempts':Budget(journal_path).report()['auth_attempts']})
    except Exception:
        pipe.send({'status':'REFUSED_NO_REFRESH','pid':os.getpid()})
    finally:
        if client is not None: client.close()
        pipe.close()


@pytest.mark.parametrize('expired',[False,True])
def test_one_session_memory_pipe_across_successive_independent_processes(tmp_path,expired,capsys):
    path=tmp_path/'attempt.sqlite'
    budget=Budget.create(path)
    budget.take('AUTH_ONCE')  # Models the single preceding login, not live proof.
    session=MemorySession('TEST_TOKEN_ONLY_IN_MEMORY',str(uuid4()),0 if expired else time.time()+300)
    ctx=multiprocessing.get_context('spawn')
    results=[]
    for _ in range(2):
        parent,child=ctx.Pipe()
        process=ctx.Process(target=child_read,args=(child,str(path)))
        process.start();child.close()
        try:
            parent.send(session)
            assert parent.poll(15)
            result=parent.recv()
            process.join(15)
            assert process.exitcode==0 and not process.is_alive()
            results.append(result)
        finally:
            parent.close()
            if process.is_alive():
                process.terminate();process.join(5)
    assert results[0]['pid'] != results[1]['pid'] != os.getpid()
    if expired:
        assert all(r['status']=='REFUSED_NO_REFRESH' for r in results)
    else:
        assert all(r['status']=='ACTOR_READ_ONLY' and r['reads']==1 and r['auth_attempts']==1 for r in results)
    assert budget.report()['effect_attempts']==1
    assert list(tmp_path.iterdir())==[path]
    assert b'TEST_TOKEN' not in path.read_bytes()
    assert 'TEST_TOKEN' not in repr(results)+capsys.readouterr().out
