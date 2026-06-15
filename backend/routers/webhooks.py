"""
webhooks.py
Endpoint appelé par Supabase Database Webhooks quand un nouvel utilisateur
s'inscrit (INSERT sur la table profiles).
Envoie les données vers le CRM Aitable.
"""
import os
import logging
from typing import Optional, Any

from fastapi import APIRouter, Request, HTTPException, Header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/new-user")
async def on_new_user(
    request: Request,
    x_webhook_secret: Optional[str] = Header(default=None),
):
    """
    Called by Supabase Database Webhook on INSERT into the 'profiles' table.
    Pushes the new user to the Aitable CRM.

    Supabase sends a JSON body like:
    {
      "type": "INSERT",
      "table": "profiles",
      "record": {
        "id": "...",
        "email": "user@example.com",
        "prenom": "Marie",
        "industry": "SaaS",
        "business_model": "services",
        "created_at": "2024-..."
      }
    }
    """
    # Validate secret (prevent unauthorized calls).
    # Fail-closed : refuse si le secret n'est pas configuré (pas de défaut public).
    from security_config import get_webhook_secret
    try:
        expected_secret = get_webhook_secret()
    except RuntimeError:
        logger.error("[Webhook] WEBHOOK_SECRET non configuré — appel rejeté")
        raise HTTPException(status_code=503, detail="Webhook non configuré")

    import hmac
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, expected_secret):
        raise HTTPException(status_code=401, detail="Secret invalide")

    body: dict[str, Any] = await request.json()
    event_type = body.get("type", "")
    record = body.get("record", {})

    if event_type != "INSERT" or not record:
        return {"ok": True, "skipped": True}

    email    = record.get("email", "")
    prenom   = record.get("prenom", "")
    industry = record.get("industry", "")
    bm       = record.get("business_model", "")
    created  = record.get("created_at", "")

    # Resolve plan from companies table (non-blocking fallback to "free")
    plan = "free"
    try:
        from main import get_supabase_service
        sb = get_supabase_service()
        company_id = record.get("company_id")
        if company_id:
            res = sb.from_("companies").select("plan").eq("id", company_id).single().execute()
            if res.data:
                plan = res.data.get("plan", "free")
    except Exception:
        pass

    # Push to Aitable CRM (non-blocking)
    try:
        from services.crm_service import upsert_user
        upsert_user(
            email=email,
            prenom=prenom,
            industry=industry,
            business_model=bm,
            plan=plan,
            date_inscription=created,
        )
    except Exception as e:
        logger.warning(f"[Webhook] CRM upsert failed for {email}: {e}")

    logger.info(f"[Webhook] new-user processed: {email}")
    return {"ok": True}
