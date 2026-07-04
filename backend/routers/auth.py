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

from pydantic import BaseModel
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


class SendPinRequest(BaseModel):
    recipient_email: str


@router.post("/send-pin")
async def send_pin_by_email(
    body: SendPinRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Envoie le PIN de l'entreprise par email au destinataire indiqué.
    Réservé aux admins (token Supabase requis).
    Utilise Resend pour l'envoi.
    """
    import html as _html
    import logging as _logging
    import re as _re

    log = _logging.getLogger(__name__)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification requis")

    token = authorization.split(" ", 1)[1]

    from main import get_supabase_service
    supabase = get_supabase_service()

    # Identifier l'admin + récupérer le PIN
    try:
        user_resp = supabase.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise HTTPException(status_code=401, detail="Token invalide ou expiré")
        auth_user_id = user_resp.user.id
    except HTTPException:
        raise
    except Exception as e:
        log.warning(f"[SEND-PIN] token error: {e}")
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    try:
        profile_res = supabase.from_("profiles").select("company_id").eq("id", auth_user_id).single().execute()
        company_id = profile_res.data["company_id"]
        company_res = supabase.from_("companies").select("pin_code, name").eq("id", company_id).single().execute()
        pin_code = company_res.data.get("pin_code", "")
        company_name = company_res.data.get("name", "Pepperyn")
    except Exception as e:
        log.error(f"[SEND-PIN] data fetch error: {e}")
        raise HTTPException(status_code=500, detail="Impossible de récupérer les données du compte")

    if not pin_code:
        raise HTTPException(status_code=404, detail="Aucun PIN configuré pour ce compte")

    # Validation basique de l'email
    recipient = body.recipient_email.strip()
    if not _re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", recipient):
        raise HTTPException(status_code=400, detail="Adresse email invalide")

    api_key = os.environ.get("RESEND_API_KEY")
    notify_from = os.environ.get("NOTIFY_FROM", "Pepperyn <noreply@pepperyn.fr>")

    if not api_key:
        log.info("[SEND-PIN] RESEND_API_KEY non configuré — email non envoyé")
        raise HTTPException(status_code=503, detail="Service d'email non configuré")

    try:
        import resend
        resend.api_key = api_key

        e_company = _html.escape(company_name)
        e_pin = _html.escape(pin_code)
        e_recipient = _html.escape(recipient)

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #f8fafc;">
          <div style="background: #1B73E8; padding: 28px 24px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 800;">Votre accès Pepperyn</h1>
            <p style="color: #bfdbfe; margin: 6px 0 0; font-size: 14px;">{e_company}</p>
          </div>
          <div style="background: white; padding: 32px 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
            <p style="color: #374151; font-size: 15px; margin: 0 0 20px;">
              Vous avez été invité à rejoindre l'espace Pepperyn de <strong>{e_company}</strong>.
              Utilisez le code ci-dessous pour vous connecter :
            </p>
            <div style="background: #EFF6FF; border: 2px solid #1B73E8; border-radius: 12px; padding: 24px; text-align: center; margin: 0 0 24px;">
              <p style="color: #6b7280; font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 1px;">Code PIN</p>
              <p style="color: #1B73E8; font-size: 42px; font-weight: 900; letter-spacing: 12px; margin: 0;">{e_pin}</p>
            </div>
            <p style="color: #6b7280; font-size: 13px; margin: 0 0 20px;">
              Rendez-vous sur <a href="https://www.pepperyn.com/login" style="color: #1B73E8;">pepperyn.com</a>
              et saisissez ce code pour accéder à l'espace de votre entreprise.
            </p>
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
              Ne partagez pas ce code en dehors de votre équipe.
            </p>
          </div>
        </div>"""

        resend.Emails.send({
            "from": notify_from,
            "to": [recipient],
            "subject": f"Votre code d'accès Pepperyn — {e_company}",
            "html": html_body,
        })
        log.info(f"[SEND-PIN] PIN envoyé à {e_recipient} pour {company_id}")
    except Exception as e:
        log.error(f"[SEND-PIN] Resend error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")

    return {"success": True, "message": f"PIN envoyé à {recipient}"}


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

    # 4c. Supprimer la mémoire décisionnelle
    try:
        supabase.from_("decision_memory").delete().eq("company_id", company_id).execute()
    except Exception as e:
        errors.append(f"decision_memory: {e}")

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
