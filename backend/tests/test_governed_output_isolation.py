import asyncio
import copy
from uuid import UUID
from types import SimpleNamespace as NS
import pytest
from sandbox import verify_governed_output_isolation as runner
from test_v1_synthetic_routes import _Db, _enable, _empty_request, v1_routes, analyze


def test_read_only_adapter_denies_mutation():
    target = runner.ReadOnly(object())
    for name in ('insert', 'update', 'delete', 'upsert', 'rpc', 'sign_in_with_password'):
        with pytest.raises(RuntimeError): getattr(target, name)


def test_transport_containment_and_cleanup():
    import socket
    from fastapi import FastAPI
    from sandbox.output_live_transport import live_client
    app = FastAPI()
    @app.get('/health')
    def health(): return {'ok': True}
    with live_client(app, ['synthetic-id']) as client:
        port = client.base_url.port
        assert client.get('/health').status_code == 200
        assert client.post('/health').status_code == 405
        assert client.get('/api/other').status_code == 405
    with socket.socket() as released:
        released.bind(('127.0.0.1', port))


@pytest.mark.parametrize('live', [False, True])
def test_two_scopes_actual_routes_and_export_parsers(monkeypatch, live):
    from fastapi import HTTPException
    db = _Db()
    db.tables['entities'] = []
    db.tables['engagements'] = []
    db.table = db.from_
    scopes = []
    for i in (1, 2):
        scope = tuple(f'{n}0000000-0000-0000-0000-{i:012d}' for n in (1, 2, 3, 4))
        scopes.append(scope)
        _, company, entity, engagement = scope
        db.tables['entities'].append(dict(id=entity, company_id=company, is_primary=True, name='Synthetic', relation_type=None))
        db.tables['engagements'].append(dict(id=engagement, entity_id=entity))
        _enable(monkeypatch, db, company=company)
        monkeypatch.setenv('PEPPERYN_SYNTHETIC_V1_COMPANY_ID', company)
        aid = runner.fixture_id(scope)
        monkeypatch.setattr(v1_routes.uuid, 'uuid4', lambda: UUID(aid))
        asyncio.run(v1_routes.run_v1_synthetic_demo(request=_empty_request(), authorization='Bearer local', x_auth_type=None))
        row = db.tables['analyses'][-1]
        row['id'] = aid
        row['contexte_utilisateur'] = 'A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1'
        envelope = db.tables['governed_analysis_envelopes'][-1]
        envelope['analysis_id'] = aid
    before = copy.deepcopy(db.tables)
    def inspect(*args, verified_scopes):
        verified_scopes.extend(scopes)
        return {'status': 'A26_SCOPES_INSPECTED'}
    monkeypatch.setattr(runner, 'inspect', inspect)
    async def auth(authorization, x_auth_type):
        if authorization not in ('Bearer a', 'Bearer b'): raise HTTPException(401)
        return scopes[authorization.endswith('b')][1], 'free', 'admin'
    monkeypatch.setattr(analyze, '_resolve_auth', auth)
    if live:
        import main
        # main was imported by shared test fixtures before demo env was set.
        if not any(r.path == '/api/v1/governed-analyses/{analysis_id}' for r in main.app.routes):
            monkeypatch.setattr(main.app.router, 'routes', list(main.app.routes) + list(v1_routes.router.routes))
    def get_user(token):
        if token not in ('a', 'b'): raise ValueError('Invalid synthetic token')
        return NS(user=NS(id=scopes[token == 'b'][0]))
    db.auth = NS(get_user=get_user)
    def factory(url, key):
        if key == 'service': return db
        return NS(auth=NS(sign_in_with_password=lambda a: NS(session=NS(access_token=a['email'])),
                          get_user=lambda token: NS(user=NS(id=scopes[token == 'b'][0]))))
    result = runner.verify({'accounts': [{'email': 'a'}, {'email': 'b'}]}, 'anon', 'service', factory, live_transport=live)
    assert result['status'] == ('BOUNDED_A30_UVICORN_OUTPUT_ISOLATION_PASS' if live else 'BOUNDED_A29_ASGI_OUTPUT_ISOLATION_PASS'), str(result)
    assert result['positive_outputs'] == 8 and result['denials'] == 24
    assert db.tables == before
