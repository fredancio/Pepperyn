"""One authorized read window, not an execution-permit renewal. No write routes."""
import argparse
import asyncio
import json
import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sandbox.inspect_completed_b1_r5 import ANALYSIS, COMPANY, PROJECT, local_check, verify_remote
from sandbox.preflight_connected_b1 import ReadOnlyDatabase
from services.governed_output import read_owned_output

PATH = '/api/governed/analyses/' + ANALYSIS


def build_app(db, resolve_auth, *, deadline, clock=time.monotonic):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.read_succeeded = False
    app.state.closed = False
    lock = asyncio.Lock()
    app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:3000'],
                       allow_methods=['GET'], allow_headers=['Authorization', 'X-Auth-Type'])

    @app.middleware('http')
    async def boundary(request, call_next):
        if (app.state.closed or clock() >= deadline or not request.client
                or request.client.host not in {'127.0.0.1', '::1'}
                or request.url.path != PATH or request.url.query
                or request.method not in {'GET', 'OPTIONS'}):
            return JSONResponse({'detail': 'Read window closed or out of scope'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get(PATH)
    async def read(request: Request, authorization: str | None = Header(default=None),
                   x_auth_type: str | None = Header(default=None)):
        company, _, kind = await resolve_auth(authorization, x_auth_type)
        if kind != 'admin' or company != COMPANY:
            raise HTTPException(404, 'Ressource introuvable')
        async with lock:
            if app.state.closed or clock() >= deadline:
                raise HTTPException(403, 'Read window closed')
            try:
                result = read_owned_output(db, analysis_id=ANALYSIS, company_id=company)
                if result['execution_provenance']['status'] != 'VERIFIED_RECEIPT':
                    raise ValueError('RECEIPT_REQUIRED')
            except Exception:
                app.state.closed = True
                raise HTTPException(503, 'Lecture gouvernee indisponible') from None
            app.state.read_succeeded = True
            app.state.closed = True
            return result

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True)
    args = parser.parse_args()
    root = Path(args.runtime)
    marker = root / 'b1-r5-independent-read.started'
    db = None
    stage = 'CONFIGURATION'
    logging.disable(logging.CRITICAL)
    try:
        if (os.getenv('SUPABASE_URL') != PROJECT or os.getenv('ENVIRONMENT') != 'development'
                or os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT', '0') != '0'
                or not os.getenv('SUPABASE_SERVICE_KEY') or not os.getenv('SUPABASE_ANON_KEY')
                or len(os.getenv('JWT_GUEST_SECRET', '')) < 32):
            raise ValueError('ENVIRONMENT')
        stage = 'CLOSED_R5_AND_GET_ONLY_PREFLIGHT'
        before = {p.name: p.read_bytes() for p in root.glob('b1-connected-rehearsal*') if p.is_file()}
        data = local_check(root)
        db = ReadOnlyDatabase(os.environ['SUPABASE_SERVICE_KEY'])
        verify_remote(db, data)
        # Reuse the actual application authentication unchanged. Main's app is
        # never served; its ingestion/export/legacy routes are not in this app.
        from routers.analyze import _resolve_auth
        import main as application  # Load actual auth dependency; never serve application.app.
        if os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT', '0') != '0':
            raise ValueError('TRANSPORT_CHANGED')
        stage = 'EXCLUSIVE_LOCAL_WINDOW'
        with marker.open('x', encoding='utf-8') as handle:
            handle.write('READ_ONLY_SINGLE_WINDOW\n')
        deadline = time.monotonic() + 1200
        app = build_app(db, _resolve_auth, deadline=deadline)
        import uvicorn
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8000,
                                proxy_headers=False, access_log=False, log_level='critical'))

        async def serve():
            task = asyncio.create_task(server.serve())
            while not task.done():
                if app.state.closed or time.monotonic() >= deadline:
                    app.state.closed = True
                    server.should_exit = True
                await asyncio.sleep(.2)
            await task

        @app.on_event('startup')
        async def ready():
            print('B1_READ_ONLY_WINDOW: READY. 20 minutes maximum; one successful authenticated read. No uploads or exports.', flush=True)
        stage = 'AUTHENTICATED_BROWSER_READ'
        asyncio.run(serve())
        stage = 'GET_ONLY_POSTFLIGHT'
        verify_remote(db, data)
        after = {p.name: p.read_bytes() for p in root.glob('b1-connected-rehearsal*') if p.is_file()}
        if before != after:
            raise ValueError('PERMIT_CHANGED')
        print(json.dumps(dict(status='B1_BOUNDED_READ_SERVER_PASS' if app.state.read_succeeded else 'B1_READ_NOT_PROVEN',
            browser_visual_proven=False, business_write_performed=False, r5_unchanged=True,
            external_provider_used=False, real_data_used=False, b1_global_proven=False)))
        return 0 if app.state.read_succeeded else 1
    except (Exception, KeyboardInterrupt):
        print('B1_READ_REFUSED_STAGE: ' + stage)
        return 1
    finally:
        if db:
            db.client.close()
        if marker.exists():
            closed = marker.with_suffix('.closed')
            if not closed.exists():
                with closed.open('x', encoding='utf-8') as handle:
                    handle.write('CLOSED_NO_AUTOMATIC_RESTART\n')
        print('B1_READ_WINDOW: CLOSED. No execution permit modified.', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
