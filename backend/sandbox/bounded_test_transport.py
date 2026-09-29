"""Explicit non-provider transports for bounded synthetic verification only.

This module cannot address an arbitrary origin.  It is not imported by product
services and cannot carry a provider request.  Redirects, environment proxies,
automatic retries and response logging are disabled by construction.
"""

from __future__ import annotations

import socket
from urllib.parse import urlsplit

import httpx


INTEGRATION_TEST_ORIGIN = "https://ejixkplrgobgwqnhidwt.supabase.co"
_INTEGRATION_PREFIXES = ("/rest/v1/", "/auth/v1/")
_LOOPBACK_PATHS = frozenset(("/api/entities", "/api/analyses/history"))


def _target(url: str, *, loopback: bool = False) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme == "https"
            and parsed.netloc == "ejixkplrgobgwqnhidwt.supabase.co"
            and parsed.path.startswith(_INTEGRATION_PREFIXES)):
        return url
    if (loopback and parsed.scheme == "http"
            and parsed.hostname == "127.0.0.1" and parsed.port == 8000
            and parsed.path in _LOOPBACK_PATHS):
        return url
    raise ValueError("BOUNDED_TEST_TARGET_REFUSED")


def request(method: str, url: str, *, headers: dict[str, str], json=None, loopback=False):
    if method not in {"GET", "POST", "PATCH", "DELETE"}:
        raise ValueError("BOUNDED_TEST_METHOD_REFUSED")
    target = _target(url, loopback=loopback)
    with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
        return client.request(method, target, headers=headers, json=json)


def integration_get(path: str, *, headers: dict[str, str], params=None):
    if not path.startswith("/rest/v1/"):
        raise ValueError("BOUNDED_TEST_PATH_REFUSED")
    with httpx.Client(base_url=INTEGRATION_TEST_ORIGIN, timeout=30,
                      follow_redirects=False, trust_env=False,
                      headers=headers) as client:
        return client.get(path, params=params)


def integration_request(method: str, path: str, *, headers: dict[str, str],
                        json=None, params=None):
    if method not in {"GET", "POST"} or not path.startswith(_INTEGRATION_PREFIXES):
        raise ValueError("BOUNDED_TEST_PATH_REFUSED")
    with httpx.Client(base_url=INTEGRATION_TEST_ORIGIN, timeout=30,
                      follow_redirects=False, trust_env=False,
                      headers=headers) as client:
        return client.request(method, path, json=json, params=params)


def open_loopback_socket():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    return sock


def loopback_client(port: int):
    if type(port) is not int or not 0 < port < 65536:
        raise ValueError("BOUNDED_TEST_PORT_REFUSED")
    return httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=30,
                        trust_env=False, follow_redirects=False)
