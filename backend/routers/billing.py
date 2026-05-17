"""
routers/billing.py — Pepperyn V11
Endpoints de facturation (Stripe Checkout, Portal, Webhook, Quota).

⚠️  Stripe non encore branché — les endpoints /checkout et /portal
     retournent des placeholders jusqu'à demain.

Endpoints :
  GET  /api/billing/usage          → quota du mois (pour la sidebar frontend)
  POST /api/billing/checkout       → créer session Checkout (plan ou add-on)
  POST /api/billing/portal         → ouvrir Billing Portal
  POST /api/billing/webhook        → webhook Stripe (mettre à jour plan/crédits)
  GET  /api/billing/plans          → liste plans + add-ons + prix (pour /upgrade)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Lazy init des services
_billing_service = None
_usage_service   = None


def _get_billing():
    global _billing_service
    if _billing_service is None:
        from services.billing_service import BillingService
        _billing_service = BillingService()
    return _billing_service


def _get_usage():
    global _usage_service
    if _usage_service is None:
        from services.usage_service import UsageService
        _usage_service = UsageService()
    return _usage_service


async def _resolve_auth(authorization: Optional[str]) -> tuple[str, str]:
    """Résout le token → (company_id, plan). Réutilise la logique de analyze.py."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    token = authorization.split(" ", 1)[1]

    import os
    from jose import jwt, JWTError
    JWT_SECRET = os.getenv("JWT_GUEST_SECRET", "pepperyn_guest_secret_key_change_in_prod")
    JWT_ALGORITHM = "HS256"

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") == "guest":
            return payload["company_id"], payload.get("plan", "free")
    except JWTError:
        pass

    from main import get_supabase_service
    supabase = get_supabase_service()
    try:
        user_resp = supabase.auth.get_user(token)
        if user_resp and user_resp.user:
            user_id = user_resp.user.id
            profile = supabase.from_("profiles").select("company_id").eq("id", user_id).limit(1).execute()
            if profile.data:
                company_id = profile.data[0].get("company_id")
                if company_id:
                    plan_resp = supabase.from_("companies").select("plan").eq("id", company_id).limit(1).execute()
                    plan = plan_resp.data[0].get("plan", "free") if plan_resp.data else "free"
                    return company_id, plan
    except Exception as e:
        logger.warning(f"[BILLING AUTH] {e}")

    raise HTTPException(status_code=401, detail="Token invalide")


# ── Plans catalogue (source unique de vérité pour le frontend) ───────────────

PLANS_CATALOGUE = {
    "plans": [
        {
            "id": "free",
            "name": "FREE",
            "subtitle": "Découvrez Pepperyn",
            "price_eur": 0,
            "period": "",
            "analyses_per_month": 1,
            "interactions_per_analysis": 3,
            "highlighted": False,
            "color": "green",
            "features": [
                "1 analyse / mois",
                "Export PDF",
                "Mémoire légère",
                "Données anonymisées",
                "3 interactions contextuelles incluses",
            ],
            "stripe_price_id": None,
            "cta": "Commencer gratuitement",
        },
        {
            "id": "pro",
            "name": "PRO",
            "subtitle": "Pour dirigeants de PME",
            "price_eur": 59,
            "period": "/mois",
            "analyses_per_month": 15,
            "interactions_per_analysis": None,  # illimité
            "highlighted": False,
            "color": "blue",
            "features": [
                "15 analyses / mois",
                "Usage conversationnel inclus",
                "Exports Excel, PDF et PowerPoint",
                "Mémoire persistante",
                "Suivi des tendances financières",
                "Alertes et dérives détectées automatiquement",
                "Analyse multi-périodes",
                "Projections simples",
                "Priorisation intelligente",
            ],
            "stripe_price_id": "price_TODO_pro",
            "cta": "Commencer",
        },
        {
            "id": "power",
            "name": "POWER",
            "subtitle": "Pour CFO, consultants et experts-comptables",
            "price_eur": 129,
            "period": "/mois",
            "analyses_per_month": 75,
            "interactions_per_analysis": None,
            "highlighted": True,
            "badge": "⭐ LE PLUS UTILISÉ",
            "color": "red",
            "features": [
                "75 analyses / mois",
                "Usage avancé inclus",
                "Multi-entités",
                "Mémoire persistante par entité",
                "Simulateur de décisions",
                "Projections avancées",
                "Comparaison périodes",
                "Analyse comparative",
                "Exports premium",
                "Historique enrichi",
                "Détection des tendances récurrentes",
            ],
            "stripe_price_id": "price_TODO_power",
            "cta": "Passer à Power",
        },
        {
            "id": "scale",
            "name": "SCALE",
            "subtitle": "Pour départements financiers et cabinets",
            "price_eur": 349,
            "period": "/mois",
            "analyses_per_month": 250,
            "interactions_per_analysis": None,
            "highlighted": False,
            "color": "purple",
            "features": [
                "250 analyses / mois",
                "Usage intensif inclus",
                "Multi-users",
                "Multi-entités avancé",
                "Permissions utilisateurs",
                "Workspace collaboratif",
                "Historique avancé",
                "Gouvernance des analyses",
                "Support prioritaire",
                "Collaboration équipe finance",
                "Gestion avancée des entités",
            ],
            "stripe_price_id": "price_TODO_scale",
            "cta": "Passer à Scale",
        },
    ],
    "addons": [
        {
            "id": "addon_starter",
            "name": "Starter Pack",
            "analyses": 10,
            "price_eur": 19,
            "description": "+10 analyses supplémentaires",
            "stripe_price_id": "price_TODO_addon_starter",
        },
        {
            "id": "addon_growth",
            "name": "Growth Pack",
            "analyses": 50,
            "price_eur": 69,
            "description": "+50 analyses supplémentaires",
            "stripe_price_id": "price_TODO_addon_growth",
        },
        {
            "id": "addon_scale",
            "name": "Scale Pack",
            "analyses": 200,
            "price_eur": 199,
            "description": "+200 analyses supplémentaires",
            "stripe_price_id": "price_TODO_addon_scale",
        },
    ],
    "microcopy": "Conçu pour absorber les pics d'activité sans interruption.",
}


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/plans")
async def get_plans():
    """Retourne le catalogue des plans et add-ons (public, sans auth)."""
    return {"success": True, "data": PLANS_CATALOGUE}


@router.get("/usage")
async def get_usage(
    authorization: Optional[str] = Header(default=None),
):
    """
    Retourne le quota d'analyses du mois en cours pour l'utilisateur connecté.
    Utilisé par la sidebar frontend pour afficher le compteur de crédits.
    """
    company_id, plan = await _resolve_auth(authorization)
    usage = _get_usage().get_usage_this_month(company_id, plan)
    return {"success": True, "data": usage}


class CheckoutRequest(BaseModel):
    plan_or_addon: str  # "pro" | "power" | "scale" | "addon_starter" | "addon_growth" | "addon_scale"
    customer_email: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.post("/checkout")
async def create_checkout_session(
    body: CheckoutRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Crée une session Stripe Checkout pour un plan ou un add-on.
    ⚠️  Retourne un placeholder jusqu'à la configuration de Stripe.
    """
    company_id, plan = await _resolve_auth(authorization)

    try:
        result = _get_billing().create_checkout_session(
            plan_or_addon=body.plan_or_addon,
            company_id=company_id,
            customer_email=body.customer_email,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BILLING] Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la session de paiement")


@router.post("/portal")
async def create_portal_session(
    authorization: Optional[str] = Header(default=None),
):
    """
    Ouvre le Billing Portal Stripe pour gérer l'abonnement.
    ⚠️  Retourne un placeholder jusqu'à la configuration de Stripe.
    """
    company_id, plan = await _resolve_auth(authorization)
    result = _get_billing().create_portal_session(company_id=company_id)
    return {"success": True, "data": result}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(default=None, alias="stripe-signature"),
):
    """
    Webhook Stripe (POST depuis Stripe Dashboard).
    À enregistrer dans Stripe : https://your-railway-url/api/billing/webhook
    Événements à activer :
      - checkout.session.completed
      - customer.subscription.deleted
      - invoice.payment_failed
    """
    payload = await request.body()

    try:
        result = _get_billing().process_webhook_event(payload, stripe_signature or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Appliquer l'action résultante
    if result.get("action") == "update_plan":
        company_id = result.get("company_id")
        new_plan = result.get("plan")
        if company_id and new_plan:
            try:
                from main import get_supabase_service
                sb = get_supabase_service()
                sb.from_("companies").update({"plan": new_plan}).eq("id", company_id).execute()
                logger.info(f"[WEBHOOK] Plan mis à jour : {company_id} → {new_plan}")
            except Exception as e:
                logger.error(f"[WEBHOOK] Erreur update plan: {e}")

    elif result.get("action") == "add_bonus":
        company_id = result.get("company_id")
        quantity = result.get("quantity", 0)
        if company_id and quantity:
            _get_usage().add_bonus_analyses(company_id, quantity)
            logger.info(f"[WEBHOOK] +{quantity} analyses bonus : {company_id}")

    elif result.get("action") == "downgrade_free":
        company_id = result.get("company_id")
        if company_id:
            try:
                from main import get_supabase_service
                sb = get_supabase_service()
                sb.from_("companies").update({"plan": "free"}).eq("id", company_id).execute()
                logger.info(f"[WEBHOOK] Downgrade FREE : {company_id}")
            except Exception as e:
                logger.error(f"[WEBHOOK] Erreur downgrade: {e}")

    return {"received": True, "action": result.get("action", "noop")}
