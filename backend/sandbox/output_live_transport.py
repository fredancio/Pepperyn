"""Temporary loopback Uvicorn transport; never touches the server on port 8000."""
from contextlib import contextmanager
import threading
import time

import uvicorn
from starlette.responses import JSONResponse

from sandbox.bounded_test_transport import loopback_client, open_loopback_socket


class ReadSurface:
    """Outer containment only; product middleware, lifespan and GET routes remain."""
    def __init__(self, app, ids):
        self.app = app
        self.paths = {'/api/v1/governed-analyses/' + aid + suffix
                      for aid in ids for suffix in ('', '/export.xlsx', '/export.pdf', '/export.pptx')}
        self.paths.add('/health')

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            return await self.app(scope, receive, send)
        if scope['type'] != 'http':
            return
        if scope['method'] not in ('GET', 'OPTIONS') or scope['path'] not in self.paths:
            return await JSONResponse({'detail': 'A30_READ_SURFACE_ONLY'}, status_code=405)(scope, receive, send)
        await self.app(scope, receive, send)


@contextmanager
def live_client(app, ids):
    sock = open_loopback_socket()
    port = sock.getsockname()[1]
    config = uvicorn.Config(ReadSurface(app, ids), log_config=None, access_log=False,
                            lifespan='on', timeout_graceful_shutdown=3)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    try:
        thread.start()
        deadline = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError('A30_UVICORN_START_REFUSED')
            time.sleep(.05)
        with loopback_client(port) as client:
            yield client
    finally:
        server.should_exit = True
        if thread.is_alive(): thread.join(8)
        sock.close()
        if thread.is_alive(): raise RuntimeError('A30_UVICORN_STOP_REFUSED')
