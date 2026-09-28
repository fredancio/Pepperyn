"""Local independent-process factory. Never opens a real network connection."""
from v40_local_runner_support import Reader, transport
from sandbox.v40_successor_history import HistoryReader
from sandbox.v40_rehearsal_orchestration import Backend, profile_for


def factory(config,memory):
    return Backend(HistoryReader(Reader(config),config['history']),transport(config),
                   memory['session'],profile_for(config['scope']),config['policy_id'])
