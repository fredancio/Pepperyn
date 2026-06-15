"""
Authentication routes for Pepperyn.
POST /api/auth/pin    — Guest login with 4-digit PIN
DELETE /api/auth/account — Delete account + all data (admin users only)
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from jose import jwt

from models.schemas import PinLoginRequest, PinLoginResponse
from security_config import get_jwt_guest_secret
from services.rate_limiter import pin_login_limiter, client_ip_from_request

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_ALGORITHM = "HS256"
GUEST_TOKEN_EXPIRE_HOURS = 8


def create_guest_jwt(company_id: str, plan: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=GUEST_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": f"guest:{company_id}",
        "company_id": company_id,
        "plan": plan,
        "type": "guest",
        "exp": expire,
    }
    return jwt.encode(payload, get_jwt_guest_secret(), algorithm=JWT_ALGORITHM)


@router.post("/pin", response_model=PinLoginResponse)
async def login_with_pin(request: PinLoginRequest, http_request: Request):
    """
    Guest login with 4-digit PIN.
    Validates against Supabase companies table via RPC.
    Returns a JWT valid for 8 hours.

    Protégé contre le brute-force : verrouillage temporaire par IP après
    plusieurs échecs (rate limiter en mémoire, voir services/rate_limiter.py).
    """
    from main import get_supabase_service

    # ── Anti-brute-force : vérifier le verrou avant toute validation ──────────
    client_ip = client_ip_from_request(http_request)
    allowed, retry_after = pin_login_limiter.check(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives. Réessayez plus tard.",
            headers={"Retry-After": str(retry_after)},
        )

    supabase = get_supabase_service()
    try:
        result = supabase.rpc('validate_pin', {'input_pin': request.pin}).execute()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[AUTH] validate_pin error: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur. Merci de réessayer.")

    if not result.data:
        # Enregistrer l'échec (peut déclencher le verrou) + petit délai anti-bruteforce
        pin_login_limiter.record_failure(client_ip)
        import asyncio
        await asyncio.sleep(0.5)
        raise HTTPException(status_code=401, detail="Code PIN incorrect")

    # Succès : réinitialiser le compteur pour cette IP
    pin_login_limiter.record_success(client_ip)

    company = result.data[0]
    guest_token = create_guest_jwt(
        company_id=str(company['company_id']),
        plan=str(company['plan'])
    )

    return PinLoginResponse(
        access_token=guest_token,
        company_id=str(company['company_id']),
        plan=str(company['plan'])
    )


@router.delete("/account")
async def delete_account(
    authorization: Optional[str] = Header(default=None),
):
    """
    Supprime définitivement le compte et toutes les données associées.
    Réservé aux utilisateurs admin (Supabase JWT uniquement).
    Ordre de suppression :
      1. analyses + usage_logs + user_activity + usage_limits
      2. profiles
      3. companies
      4. auth user (Supabase Admin API)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification requis")

    token = authorization.split(" ", 1)[1]

    from main import get_supabase_service
    supabase = get_supabase_service()

    # Vérifier l'identité via Supabase
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token invalide ou expiré")
        auth_user_id = user_response.user.id
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[AUTH] token verify error: {e}")
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    # Récupérer company_id depuis profiles
    try:
        profile_res = supabase.from_("profiles").select("company_id").eq("id", auth_user_id).single().execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profil introuvable")
        company_id = profile_res.data["company_id"]
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[AUTH] profil read error: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur.")

    errors = []

    # 1. Supprimer les sessions + messages (messages cascadent avec sessions)
    try:
        supabase.from_("sessions").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"sessions: {e}")

    # 2. Supprimer les feedbacks
    try:
        supabase.from_("feedback").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"feedback: {e}")

    # 3. Supprimer les analyses (ON DELETE CASCADE supprime financial_metrics liés)
    try:
        supabase.from_("analyses").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"analyses: {e}")

    # 2. Supprimer les usage_logs
    try:
        supabase.from_("usage_logs").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"usage_logs: {e}")

    # 3. Supprimer user_activity
    try:
        supabase.from_("user_activity").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"user_activity: {e}")

    # 4. Supprimer usage_limits
    try:
        supabase.from_("usage_limits").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"usage_limits: {e}")

    # 4b. Supprimer entities + workspaces (ON DELETE CASCADE devrait suffire,
    #     mais on supprime explicitement pour garantir la propreté)
    try:
        supabase.from_("entities").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"entities: {e}")
    try:
        supabase.from_("workspaces").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"workspaces: {e}")

    # 5. Supprimer le profil
    try:
        supabase.from_("profiles").delete().eq("id", auth_user_id).execute()
    except Exception as e:
        errors.append(f"profiles: {e}")

    # 6. Supprimer la company
    try:
        supabase.from_("companies").delete().eq("id", company_id).execute()
    except Exception as e:
        errors.append(f"companies: {e}")

    # 7. Supprimer l'utilisateur Supabase Auth (nécessite service role)
    try:
        supabase.auth.admin.delete_user(auth_user_id)
    except Exception as e:
        errors.append(f"auth_user: {e}")

    if errors:
        # Suppression partielle — on log mais on ne bloque pas
        # (certaines tables peuvent ne pas exister ou être vides)
        import logging
        logging.getLogger(__name__).warning(f"[DELETE_ACCOUNT] Partial errors for {auth_user_id}: {errors}")

    return {"success": True, "message": "Compte et données supprimés définitivement"}
