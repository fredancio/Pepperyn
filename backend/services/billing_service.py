"""
billing_service.py — Pepperyn V11
Infrastructure de facturation préparée pour Stripe.

⚠️  STRIPE NON ENCORE BRANCHÉ — les méthodes retournent des placeholders.
     Pour activer : ajouter STRIPE_SECRET_KEY dans les env vars Railway
     et décommenter les lignes `import stripe` + remplacer les placeholders.

Architecture Stripe prévue :
  - Checkout Session  → abonnement mensuel (plans) ou paiement unique (add-ons)
  - Customer Portal   → gestion abonnement self-serve
  - Webhook           → mise à jour plan/crédits dans Supabase après paiement
  - Feature gating    → lecture plan depuis Supabase (déjà en place via UsageService)
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Stripe Price IDs (à renseigner dans Railway env vars) ────────────────────
STRIPE_PRICE_IDS: dict[str, str] = {
    # Plans mensuels
    "pro":   os.getenv("STRIPE_PRICE_PRO",   "price_TODO_pro"),
    "power": os.getenv("STRIPE_PRICE_POWER", "price_TODO_power"),
    "scale": os.getenv("STRIPE_PRICE_SCALE", "price_TODO_scale"),
    # Add-on packs (paiement unique)
    "addon_starter": os.getenv("STRIPE_PRICE_ADDON_STARTER", "price_TODO_addon_starter"),
    "addon_growth":  os.getenv("STRIPE_PRICE_ADDON_GROWTH",  "price_TODO_addon_growth"),
    "addon_scale":   os.getenv("STRIPE_PRICE_ADDON_SCALE",   "price_TODO_addon_scale"),
}

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SECRET_KEY     = os.getenv("STRIPE_SECRET_KEY", "")

# Mapping Stripe Price ID → plan name (pour webhooks)
PRICE_TO_PLAN: dict[str, str] = {v: k for k, v in STRIPE_PRICE_IDS.items() if k in ("pro", "power", "scale")}

# Mapping Stripe Price ID → add-on quantity (pour webhooks)
PRICE_TO_ADDON_QUANTITY: dict[str, int] = {
    STRIPE_PRICE_IDS["addon_starter"]: 10,
    STRIPE_PRICE_IDS["addon_growth"]:  50,
    STRIPE_PRICE_IDS["addon_scale"]:   200,
}

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.pepperyn.com")


class BillingService:
    """
    Prépare les sessions Stripe Checkout et Portal.
    ⚠️  Mode placeholder — remplacer par stripe.checkout.Session.create(...)
        quand STRIPE_SECRET_KEY sera configuré.
    """

    def is_stripe_configured(self) -> bool:
        return bool(STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith("sk_test_TODO"))

    # ── Checkout Session ─────────────────────────────────────────────────────

    def create_checkout_session(
        self,
        plan_or_addon: str,
        company_id: str,
        customer_email: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict:
        """
        Crée une session Stripe Checkout.
        Si Stripe non configuré, retourne un placeholder avec instructions.

        Args:
            plan_or_addon: "pro" | "power" | "scale" | "addon_starter" | "addon_growth" | "addon_scale"
            company_id:    UUID Supabase de la company
            customer_email: email pré-rempli dans le Checkout
        """
        price_id = STRIPE_PRICE_IDS.get(plan_or_addon)
        if not price_id:
            raise ValueError(f"Plan ou add-on inconnu : {plan_or_addon}")

        is_addon = plan_or_addon.startswith("addon_")
        _success = success_url or f"{FRONTEND_URL}/app/billing/success?plan={plan_or_addon}"
        _cancel  = cancel_url  or f"{FRONTEND_URL}/upgrade"

        if not self.is_stripe_configured():
            logger.warning("[BILLING] Stripe non configuré — retour placeholder")
            return {
                "placeholder": True,
                "message": "Stripe non encore configuré. Ajoutez STRIPE_SECRET_KEY dans les env vars Railway.",
                "plan": plan_or_addon,
                "price_id": price_id,
                "checkout_url": None,
            }

        # ── TODO demain : décommenter et adapter ────────────────────────────
        # import stripe
        # stripe.api_key = STRIPE_SECRET_KEY
        #
        # session = stripe.checkout.Session.create(
        #     payment_method_types=["card"],
        #     line_items=[{"price": price_id, "quantity": 1}],
        #     mode="payment" if is_addon else "subscription",
        #     success_url=_success + "&session_id={CHECKOUT_SESSION_ID}",
        #     cancel_url=_cancel,
        #     customer_email=customer_email,
        #     metadata={"company_id": company_id, "plan_or_addon": plan_or_addon},
        # )
        # return {"checkout_url": session.url, "session_id": session.id}
        # ────────────────────────────────────────────────────────────────────

        return {"checkout_url": None, "placeholder": True}

    # ── Customer Portal ──────────────────────────────────────────────────────

    def create_portal_session(
        self,
        company_id: str,
        return_url: Optional[str] = None,
    ) -> dict:
        """
        Ouvre le Billing Portal Stripe (gestion abonnement self-serve).
        L'utilisateur peut y annuler, changer de plan, mettre à jour sa CB.
        """
        _return = return_url or f"{FRONTEND_URL}/app/settings"

        if not self.is_stripe_configured():
            return {
                "placeholder": True,
                "message": "Stripe non encore configuré.",
                "portal_url": None,
            }

        # ── TODO demain ──────────────────────────────────────────────────────
        # import stripe
        # stripe.api_key = STRIPE_SECRET_KEY
        # # Récupérer stripe_customer_id depuis Supabase
        # customer_id = self._get_stripe_customer_id(company_id)
        # session = stripe.billing_portal.Session.create(
        #     customer=customer_id,
        #     return_url=_return,
        # )
        # return {"portal_url": session.url}
        # ────────────────────────────────────────────────────────────────────

        return {"portal_url": None, "placeholder": True}

    # ── Webhook processing ───────────────────────────────────────────────────

    def process_webhook_event(self, payload: bytes, sig_header: str) -> dict:
        """
        Traite un webhook Stripe (checkout.session.completed, etc.)
        Retourne {"action": str, "company_id": str, "plan": str, "quantity": int}

        Structure webhook prévue :
          checkout.session.completed → mise à jour plan OU ajout crédits bonus
          customer.subscription.deleted → downgrade vers FREE
          invoice.payment_failed → notif email (TODO)
        """
        if not self.is_stripe_configured() or not STRIPE_WEBHOOK_SECRET:
            return {"action": "noop", "reason": "Stripe non configuré"}

        # ── TODO demain ──────────────────────────────────────────────────────
        # import stripe
        # stripe.api_key = STRIPE_SECRET_KEY
        # try:
        #     event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        # except stripe.error.SignatureVerificationError:
        #     raise ValueError("Signature webhook invalide")
        #
        # if event["type"] == "checkout.session.completed":
        #     session = event["data"]["object"]
        #     company_id = session["metadata"]["company_id"]
        #     plan_or_addon = session["metadata"]["plan_or_addon"]
        #
        #     if plan_or_addon.startswith("addon_"):
        #         qty = PRICE_TO_ADDON_QUANTITY.get(session["amount_total"], 0)
        #         return {"action": "add_bonus", "company_id": company_id, "quantity": qty}
        #     else:
        #         return {"action": "update_plan", "company_id": company_id, "plan": plan_or_addon}
        #
        # elif event["type"] == "customer.subscription.deleted":
        #     session = event["data"]["object"]
        #     company_id = session["metadata"].get("company_id", "")
        #     return {"action": "downgrade_free", "company_id": company_id}
        #
        # return {"action": "unhandled", "type": event["type"]}
        # ────────────────────────────────────────────────────────────────────

        return {"action": "noop", "reason": "Webhook handler non encore activé"}

    def _get_stripe_customer_id(self, company_id: str) -> Optional[str]:
        """Récupère le stripe_customer_id depuis la table companies."""
        try:
            from main import get_supabase_service
            sb = get_supabase_service()
            result = sb.from_("companies").select("stripe_customer_id").eq("id", company_id).single().execute()
            return result.data.get("stripe_customer_id") if result.data else None
        except Exception:
            return None
