"""Independent rehearsal workers. Credentials travel through memory pipes only."""
import contextlib
import logging
import multiprocessing
import os
import time

from sandbox.preflight_v40_rehearsal import ReadOnlyClient
from sandbox.v40_rehearsal_budget import Budget
from sandbox.v40_rehearsal_transport import RehearsalTransport
from sandbox.v40_rehearsal_orchestration import Backend, profile_for, claim, complete, verify_state, require


def cloud_backend(config, memory):
    return Backend(ReadOnlyClient(memory['service']),
        RehearsalTransport(budget=Budget(config['journal']),anon_key=memory['anon'],service_key=memory['service']),
        memory['session'],profile_for(config['scope']),config['policy_id'])


def _entry(pipe, factory, config, mode, job, barrier):
    db=None
    logging.disable(logging.CRITICAL)
    try:
        # No credentials in Process.args, environment variables, files or argv.
        memory=pipe.recv()
        db=factory(config,memory)
        if mode=='RECOVER':
            db.transport.verify_actor(db.session)
            result=verify_state(db.reader,**job)
        else:
            if barrier is not None: barrier.wait(timeout=30)
            result=claim(db,job,mode)
            if mode.startswith('POSITIVE_CLAIM_'):
                pipe.send(dict(result,pid=os.getpid()))
                if result['status']!='CLAIMED': return
                require(pipe.poll(45) and pipe.recv()=='EXECUTE_ACKNOWLEDGED_WINNER_ONCE')
                result=complete(db,result['claimed'],'POSITIVE_COMPLETE')
        pipe.send(dict(result,pid=os.getpid()))
    except BaseException:
        try: pipe.send({'status':'WORKER_REFUSED_NO_RETRY','pid':os.getpid()})
        except Exception: pass
    finally:
        if db is not None:
            db.reader.close();db.transport.close()
        pipe.close()


def _quiet_entry(*args):
    # Never print a worker traceback containing a request or memory credentials.
    with open(os.devnull,'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        _entry(*args)


class Workers:
    def __init__(self, config, memory, factory=cloud_backend):
        self.config,self.memory,self.factory=config,memory,factory

    def __repr__(self):
        return 'V40Workers(REDACTED)'

    def __call__(self, mode, job):
        require(mode in {'ABANDON_CLAIM','ABANDON_RECLAIM','POSITIVE_RACE','RECOVER'})
        ctx=multiprocessing.get_context('spawn')
        modes=['POSITIVE_CLAIM_A','POSITIVE_CLAIM_B'] if mode=='POSITIVE_RACE' else [mode]
        barrier=ctx.Barrier(2) if len(modes)==2 else None
        children=[]
        deadline=time.monotonic()+120
        def receive(pipe):
            remaining=deadline-time.monotonic()
            require(remaining>0 and pipe.poll(remaining))
            result=pipe.recv()
            require(type(result) is dict and result.get('status')!='WORKER_REFUSED_NO_RETRY')
            return result
        try:
            for child_mode in modes:
                parent,child=ctx.Pipe()
                proc=ctx.Process(target=_quiet_entry,args=(child,self.factory,self.config,child_mode,job,barrier))
                proc.start();child.close();children.append((proc,parent))
                parent.send(self.memory)
            first=[receive(pipe) for _,pipe in children]
            if mode=='POSITIVE_RACE':
                require(sorted(r['status'] for r in first)==['CLAIMED','EXPECTED_CLAIM_REFUSAL'])
                winner=next(i for i,r in enumerate(first) if r['status']=='CLAIMED')
                children[winner][1].send('EXECUTE_ACKNOWLEDGED_WINNER_ONCE')
                result=receive(children[winner][1])
                require(result['status']=='COMPLETE')
                result.update(claim_refusals=1,pids=[r['pid'] for r in first])
            else:
                result=first[0]
            # Returning means every execution/claim process has actually exited.
            for proc,_ in children:
                proc.join(max(0,deadline-time.monotonic()))
                require(proc.exitcode==0 and not proc.is_alive())
            return result
        finally:
            for proc,pipe in children:
                pipe.close()
                if proc.is_alive():
                    # Owned worker only. Remote completion is UNKNOWN, never retry.
                    proc.terminate();proc.join(5)
