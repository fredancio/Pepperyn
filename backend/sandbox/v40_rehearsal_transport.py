"""Unreleased V40 rehearsal transport. No SDK session persistence or refresh.

This is a transport component, not authorization to run the rehearsal. Owner SQL
is deliberately absent. A request slot is irrevocably taken before transmission;
an uncertain result cannot be retried. Never print exceptions or response bodies.
"""
from dataclasses import dataclass, field
import time
from uuid import UUID

import httpx

from sandbox.preflight_v40_rehearsal import URL

RPC_SLOTS = {
    'INVALID_SCOPE': 'reserve_execution_v2',
    'INVALID_SOURCE': 'reserve_execution_v2',
    'ROLLBACK_RESERVE': 'reserve_execution_v2',
    'ROLLBACK_CLAIM': 'claim_execution_v2',
    'ROLLBACK_COMPLETE': 'complete_execution_v2',
    'ROLLBACK_RECLAIM': 'claim_execution_v2',
    'ABANDON_RESERVE': 'reserve_execution_v2',
    'ABANDON_CLAIM': 'claim_execution_v2',
    'ABANDON_RECLAIM': 'claim_execution_v2',
    'ABANDON_CLOSE': 'close_execution_v2',
    'POSITIVE_RESERVE': 'reserve_execution_v2',
    'POSITIVE_CLAIM_A': 'claim_execution_v2',
    'POSITIVE_CLAIM_B': 'claim_execution_v2',
    'POSITIVE_COMPLETE': 'complete_execution_v2',
    'POSITIVE_RECLAIM': 'claim_execution_v2',
    'POSITIVE_RECOMPLETE': 'complete_execution_v2',
}


class TransportRefused(ValueError):
    pass


@dataclass(frozen=True, repr=False)
class MemorySession:
    access_token: str = field(repr=False)
    actor_id: str
    expires_at: float

    def __repr__(self):
        return 'MemorySession(REDACTED)'

    def require_valid(self):
        if (type(self.access_token) is not str or not self.access_token
                or type(self.expires_at) not in (int, float)
                or not time.time() + 30 < self.expires_at):
            raise TransportRefused('SESSION_EXPIRED_NO_REFRESH')


class RehearsalTransport:
    def __init__(self, *, budget, anon_key, service_key, transport=None):
        if not all(type(x) is str and x.strip() for x in (anon_key, service_key)):
            raise TransportRefused('KEY_UNAVAILABLE')
        self._budget = budget
        self._anon = anon_key
        self._service = service_key
        self._http = httpx.Client(base_url=URL, timeout=30, trust_env=False,
                                  follow_redirects=False, transport=transport)

    def __repr__(self):
        return 'RehearsalTransport(REDACTED)'

    def login_once(self, *, password, expected_actor):
        # Fixed account/project; no caller-supplied account or URL. No refresh
        # token is extracted or retained from the temporary response object.
        if type(password) is not str or not password:
            raise TransportRefused('PASSWORD_UNAVAILABLE')
        expected_actor = str(UUID(expected_actor))
        self._budget.take('AUTH_ONCE')
        started_at = time.time()
        try:
            response = self._http.post('/auth/v1/token?grant_type=password',
                headers={'apikey': self._anon},
                json={'email': 'pepperyn-isolation-a24-a@pepperyn-test.invalid', 'password': password})
            if response.status_code != 200:
                raise ValueError()
            data = response.json()
            if (data['user']['id'] != expected_actor
                    or data['user'].get('role') != 'authenticated'
                    or data['user'].get('email') != 'pepperyn-isolation-a24-a@pepperyn-test.invalid'
                    or data.get('token_type') != 'bearer'
                    or type(data['expires_in']) is not int or data['expires_in'] <= 30):
                raise ValueError()
            # Conservatively start lifetime before any subsequent operation.
            expiry = min(float(data['expires_at']), started_at + data['expires_in'])
            session = MemorySession(data['access_token'], expected_actor, expiry)
            session.require_valid()
            return session
        except Exception:
            raise TransportRefused('AUTH_FAILED_OR_UNCERTAIN_NO_RELOGIN') from None

    def verify_actor(self, session):
        session.require_valid()
        try:
            response = self._http.get('/auth/v1/user', headers={
                'apikey': self._anon, 'Authorization': 'Bearer ' + session.access_token})
            if response.status_code != 200 or response.json()['id'] != session.actor_id:
                raise ValueError()
            return session.actor_id
        except Exception:
            raise TransportRefused('ACTOR_REFUSED_NO_REFRESH') from None

    def rpc_once(self, slot, *, name, payload, session):
        if RPC_SLOTS.get(slot) != name or type(payload) is not dict:
            raise TransportRefused('RPC_SLOT_MISMATCH')
        self.verify_actor(session)
        self._budget.take(slot)
        try:
            response = self._http.post('/rest/v1/rpc/' + name,
                headers={'apikey': self._service, 'Authorization': 'Bearer ' + self._service},
                json=payload)
            if response.status_code == 200:
                result = response.json()
                # V40 close returns SQL TEXT, unlike the three JSONB RPCs.
                # Normalize only this exact acknowledged terminal value.
                if name == 'close_execution_v2':
                    if result != 'CLOSED':
                        raise ValueError()
                    return {'status': 'CLOSED'}
                if type(result) is not dict:
                    raise ValueError()
                return result
            # Only an explicitly expected SQL refusal may be handled by the
            # orchestrator; do not return server message/detail/hint or payload.
            if response.status_code == 400 and response.json().get('code') in {'P0001', '23505', '23514'}:
                return {'status': 'SQL_REFUSED', 'sqlstate': response.json()['code']}
            raise ValueError()
        except Exception:
            raise TransportRefused('RPC_FAILED_OR_UNCERTAIN_NO_RETRY') from None

    def close(self):
        self._http.close()
