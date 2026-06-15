"""
rate_limiter.py — Pepperyn
Limiteur de débit en mémoire (sans dépendance externe), conçu pour freiner le
brute-force du login PIN. Suit les tentatives échouées par clé (ex. adresse IP)
sur une fenêtre glissante, puis verrouille temporairement la clé au-delà d'un
seuil.

Note : l'état est local au process. Avec plusieurs workers uvicorn, la limite
est appliquée par worker (le seuil effectif est donc multiplié par le nombre de
workers). Cela élève fortement la barre sans infrastructure ; pour une limite
stricte et partagée, déplacer l'état vers Redis.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        lockout_seconds: int = 900,
    ) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.lockout = lockout_seconds
        self._attempts: dict[str, deque] = defaultdict(deque)
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Retourne (autorisé, secondes_avant_réessai). Ne consomme rien."""
        now = time.time()
        with self._lock:
            locked_until = self._locked_until.get(key)
            if locked_until is not None:
                if locked_until > now:
                    return False, int(locked_until - now) + 1
                # Verrou expiré
                self._locked_until.pop(key, None)
            return True, 0

    def record_failure(self, key: str) -> None:
        """Enregistre un échec ; verrouille la clé si le seuil est atteint."""
        now = time.time()
        with self._lock:
            dq = self._attempts[key]
            dq.append(now)
            # Purge des tentatives hors fenêtre
            cutoff = now - self.window
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= self.max_attempts:
                self._locked_until[key] = now + self.lockout
                dq.clear()

    def record_success(self, key: str) -> None:
        """Réinitialise le compteur pour la clé (connexion réussie)."""
        with self._lock:
            self._attempts.pop(key, None)
            self._locked_until.pop(key, None)


# Limiteur dédié au login PIN : 5 échecs / 15 min → verrouillage 15 min.
pin_login_limiter = InMemoryRateLimiter(
    max_attempts=5, window_seconds=900, lockout_seconds=900
)


def client_ip_from_request(request) -> str:
    """
    Extrait l'IP cliente d'une requête Starlette/FastAPI en tenant compte d'un
    éventuel proxy (Railway/OVH) via X-Forwarded-For (premier maillon).
    """
    try:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
    except Exception:
        pass
    return "unknown"
