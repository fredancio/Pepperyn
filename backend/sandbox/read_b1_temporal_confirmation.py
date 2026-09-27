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


from sandbox.read_completed_b1 import build_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True)
    args = parser.parse_args()
    root = Path(args.runtime)
    marker = root / 'b1-r5-temporal-confirmation.started'
    db = None
    started = False
    stage = 'CONFIGURATION'
    logging.disable(logging.CRITICAL)
    try:
        if (os.getenv('SUPABASE_URL') != PROJECT or os.getenv('ENVIRONMENT') != 'development'
                or os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT', '0') != '0'
                or not os.getenv('SUPABASE_SERVICE_KEY') or not os.getenv('SUPABASE_ANON_KEY')
                or len(os.getenv('JWT_GUEST_SECRET', '')) < 32):
            raise ValueError('ENVIRONMENT')
        stage = 'PREVIOUS_WINDOW_CLOSED'
        prior = root / 'b1-r5-independent-read.started'
        if (prior.read_text().strip() != 'READ_ONLY_SINGLE_WINDOW'
                or prior.with_suffix('.closed').read_text().strip() != 'CLOSED_NO_AUTOMATIC_RESTART'):
            raise ValueError('PREVIOUS_WINDOW_NOT_CLOSED')
        temporal_prior = root / 'b1-r5-temporal-read.started'
        if temporal_prior.with_suffix('.closed').read_text().strip() != 'CLOSED_NO_AUTOMATIC_RESTART':
            raise ValueError('TEMPORAL_PREDECESSOR_OPEN')
        previous_window = (prior.read_bytes(), prior.with_suffix('.closed').read_bytes(), temporal_prior.read_bytes(), temporal_prior.with_suffix('.closed').read_bytes())
        if marker.exists() or marker.with_suffix('.closed').exists():
            raise ValueError('NO_RESTART')
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
        started = True
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
            print('B1_TEMPORAL_CONFIRMATION_ONLY_WINDOW: READY. 20 minutes maximum; one successful authenticated read. No uploads or exports.', flush=True)
        stage = 'AUTHENTICATED_BROWSER_READ'
        asyncio.run(serve())
        stage = 'GET_ONLY_POSTFLIGHT'
        verify_remote(db, data)
        after = {p.name: p.read_bytes() for p in root.glob('b1-connected-rehearsal*') if p.is_file()}
        if before != after or previous_window != (prior.read_bytes(), prior.with_suffix('.closed').read_bytes(), temporal_prior.read_bytes(), temporal_prior.with_suffix('.closed').read_bytes()):
            raise ValueError('PERMIT_CHANGED')
        print(json.dumps(dict(status='B1_TEMPORAL_CONFIRMATION_SERVER_PASS' if app.state.read_succeeded else 'B1_TEMPORAL_CONFIRMATION_NOT_PROVEN',
            browser_visual_proven=False, business_write_performed=False, r5_unchanged=True,
            external_provider_used=False, real_data_used=False, b1_global_proven=False)))
        return 0 if app.state.read_succeeded else 1
    except (Exception, KeyboardInterrupt):
        print('B1_TEMPORAL_CONFIRMATION_REFUSED_STAGE: ' + stage)
        return 1
    finally:
        if db:
            db.client.close()
        if started:
            closed = marker.with_suffix('.closed')
            if not closed.exists():
                with closed.open('x', encoding='utf-8') as handle:
                    handle.write('CLOSED_NO_AUTOMATIC_RESTART\n')
        print('B1_TEMPORAL_CONFIRMATION_WINDOW: CLOSED. No execution permit modified.', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
