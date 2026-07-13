"""
routers/billing.py — Pepperyn Release 1.0
Endpoints de facturation (Stripe Checkout, Portal, Webhook, Quota).

Données commerciales (plans, quantités, prix) :
  → lues exclusivement depuis config/product_catalog.py
  → aucun catalogue commercial local dans ce fichier

Endpoints :
  GET  /api/billing/plans          → catalogue plans + Executive Capacity Packs
  GET  /api/billing/usage          → quota du mois (pour la sidebar frontend)
  POST /api/billing/checkout       → créer session Checkout (plan ou pack)
  POST /api/billing/portal         → ouvrir Billing Portal Stripe
  POST /api/billing/webhook        → webhook Stripe (mettre à jour plan/crédits)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from config.product_catalog import (
    get_commercial_plans,
    EXECUTIVE_CAPACITY_PACKS,
    EXECUTIVE_CAPACITY_PACK_IDS,
)

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

    from jose import jwt, JWTError
    from security_config import get_jwt_guest_secret
    JWT_ALGORITHM = "HS256"

    try:
        payload = jwt.decode(token, get_jwt_guest_secret(), algorithms=[JWT_ALGORITHM])
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


# ── Catalogue commercial dynamique ───────────────────────────────────────────
#
# PLANS_CATALOGUE est supprimé.
# Le catalogue est construit à la demande depuis product_catalog.py.
#
# Évolutions du contrat de réponse par rapport à l'ancien PLANS_CATALOGUE :
#   - Champs supprimés : subtitle, highlighted, badge, color, features, cta
#     (données marketing — appartiennent au frontend, pas à l'API)
#   - 'interactions_per_analysis' → 'chat_monthly_cap' (quota mensuel global,
#     sémantique correcte — il n'existe pas de limite par analyse)
#   - 'price_cents' ajouté (valeur canonique en centimes)
#   - 'label', 'max_entities' ajoutés
#   - POWER supprimé (non commercialisé publiquement)
#   - prix corrects : PRO=149€/30 analyses, SCALE=349€/100 analyses
#   - packs corrects : Starter=10/39€, Growth=20/79€, Scale=80/239€
#   - 'addons' conservé comme alias de 'executive_capacity_packs' (compat WP5)
#   - Mise à jour frontale prévue en WP5


def _build_plans_catalogue() -> dict:
    """
    Construit le catalogue Plans + Executive Capacity Packs depuis product_catalog.py.
    Appelé à chaque requête GET /api/billing/plans afin de refléter l'état courant
    des variables d'environnement (Price IDs Stripe).
    """
    # ── Plans FREE / PRO / SCALE ──────────────────────────────────────────────
    plans_out = []
    for p in get_commercial_plans():
        plans_out.append({
            "id":                 p["id"],
            "name":               p["name"],
            "label":              p["label"],
            "price_cents":        p["price_cents"],
            "price_eur":          p["price_cents"] // 100,
            "period":             "" if p["id"] == "free" else "/mois",
            "analyses_per_month": p["analyses_per_month"],
            "chat_monthly_cap":   p["chat_per_month"],
            "max_entities":       p["max_entities"],
            "stripe_price_id":    p["stripe_price_id"],
        })

    # ── Executive Capacity Packs ──────────────────────────────────────────────
    packs_out = []
    for pack_id in EXECUTIVE_CAPACITY_PACK_IDS:
        pack = EXECUTIVE_CAPACITY_PACKS[pack_id]
        packs_out.append({
            "id":             pack.pack_id,
            "name":           pack.display_name,
            "analyses_added": pack.analyses_added,
            "analyses":       pack.analyses_added,   # alias compat — supprimé en WP5
            "price_cents":    pack.price_cents,
            "price_eur":      pack.price_cents // 100,
            "stripe_price_id": pack.stripe_price_id,
        })

    return {
        "plans":                    plans_out,
        "executive_capacity_packs": packs_out,
        "addons":                   packs_out,   # alias compat — supprimé en WP5
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/plans")
async def get_plans():
    """
    Retourne le catalogue des Plans et Executive Capacity Packs (public, sans auth).
    Données issues exclusivement de config/product_catalog.py.
    """
    return {"success": True, "data": _build_plans_catalogue()}


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
    plan_or_addon: str  # "pro" | "scale" | "addon_starter" | "addon_growth" | "addon_scale"
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
    logger.info(f"[WEBHOOK] Reçu — sig présente: {bool(stripe_signature)}, payload: {len(payload)} bytes")

    try:
        result = _get_billing().process_webhook_event(payload, stripe_signature or "")
    except ValueError as e:
        logger.warning(f"[WEBHOOK] Erreur validation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[WEBHOOK] Erreur inattendue: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors du traitement du webhook.")

    # Appliquer l'action résultante
    if result.get("action") == "update_plan":
        company_id = result.get("company_id")
        new_plan   = result.get("plan")
        customer_id = result.get("stripe_customer_id")
        if company_id and new_plan:
            try:
                from main import get_supabase_service
                sb = get_supabase_service()
                update_data = {"plan": new_plan}
                if customer_id:
                    update_data["stripe_customer_id"] = customer_id
                sb.from_("companies").update(update_data).eq("id", company_id).execute()
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
