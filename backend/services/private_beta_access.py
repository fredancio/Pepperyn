"""Backend beta admission, additional to (never replacing) route ownership.

Does not authorize provider/real-data access or configure Supabase signup/RLS.
"""
import os
from uuid import UUID

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse


class BetaConfigurationRefused(RuntimeError):
    pass


def beta_users():
    flag = os.getenv("PEPPERYN_PRIVATE_BETA", "0")
    if flag not in {"0", "1"}:
        raise BetaConfigurationRefused("BETA_CONFIGURATION_INVALID")
    required = os.getenv("ENVIRONMENT", "development").strip().lower() == "production" or flag == "1"
    if not required:
        return None
    try:
        parts = os.getenv("PEPPERYN_BETA_USER_IDS", "").split(",")
        users = frozenset(str(UUID(part.strip())) for part in parts)
    except (ValueError, AttributeError):
        raise BetaConfigurationRefused("BETA_CONFIGURATION_INVALID") from None
    if len(parts) != 2 or len(users) != 2 or str(UUID(int=0)) in users:
        raise BetaConfigurationRefused("BETA_REQUIRES_TWO_DISTINCT_USERS")
    return users


class PrivateBetaAccessMiddleware:
    """Authenticate each request through Supabase Auth; never trust decoded claims.

    All application routes, including subsequently added routes, are protected.
    The only unauthenticated application exemption is GET /health. CORS remains
    outermost so valid browser preflight can finish without reaching endpoints.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            users = beta_users()
        except BetaConfigurationRefused:
            await JSONResponse({"detail": "Accès Private Beta indisponible."}, status_code=503)(scope, receive, send)
            return
        if users is None or (scope["method"] == "GET" and scope["path"] == "/health"):
            await self.app(scope, receive, send)
            return
        if scope["path"].rstrip("/") in {
            "/api/auth/pin", "/api/auth/pin-guest", "/api/auth/send-pin",
            "/api/admin/update-pin", "/api/billing/checkout", "/api/billing/portal",
        }:
            await JSONResponse({"detail": "Fonction indisponible en Private Beta."}, status_code=403)(scope, receive, send)
            return
        from starlette.requests import Request
        headers = Request(scope).headers
        authorization = headers.get("authorization", "")
        if len(headers.getlist("authorization")) != 1 or not authorization.startswith("Bearer ") or not authorization[7:].strip():
            await JSONResponse({"detail": "Authentification requise."}, status_code=401)(scope, receive, send)
            return
        try:
            from main import get_supabase_service
            response = await run_in_threadpool(lambda: get_supabase_service().auth.get_user(authorization[7:]))
            user_id = str(UUID(str(response.user.id)))
        except Exception:
            # Never return/log credentials or auth-service exception messages.
            await JSONResponse({"detail": "Authentification non vérifiable."}, status_code=401)(scope, receive, send)
            return
        if user_id not in users:
            await JSONResponse({"detail": "Accès Private Beta non autorisé."}, status_code=403)(scope, receive, send)
            return
        # Existing endpoint auth, tenant ownership and admin checks still run.
        await self.app(scope, receive, send)
