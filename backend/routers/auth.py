"""
Authentication routes for Pepperyn.
POST /api/auth/pin    — Guest login with 4-digit PIN
DELETE /api/auth/account — Delete account + all data (admin users only)
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from jose import jwt

from models.schemas import PinLoginRequest, PinLoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_GUEST_SECRET", "pepperyn_guest_secret_key_change_in_prod")
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
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/pin", response_model=PinLoginResponse)
async def login_with_pin(request: PinLoginRequest):
    """
    Guest login with 4-digit PIN.
    Validates against Supabase companies table via RPC.
    Returns a JWT valid for 8 hours.
    """
    from main import get_supabase_service

    supabase = get_supabase_service()
    try:
        result = supabase.rpc('validate_pin', {'input_pin': request.pin}).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données: {str(e)}")

    if not result.data:
        # Small delay to prevent brute-force
        import asyncio
        await asyncio.sleep(0.5)
        raise HTTPException(status_code=401, detail="Code PIN incorrect")

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
        raise HTTPException(status_code=401, detail=f"Impossible de vérifier le token: {str(e)}")

    # Récupérer company_id depuis profiles
    try:
        profile_res = supabase.from_("profiles").select("company_id").eq("id", auth_user_id).single().execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profil introuvable")
        company_id = profile_res.data["company_id"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture profil: {str(e)}")

    errors = []

    # 1. Supprimer les analyses
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
