"""
billing_service.py — Pepperyn
Facturation Stripe : Checkout, Portal, Webhook.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY     = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL          = os.getenv("FRONTEND_URL", "https://www.pepperyn.com")

STRIPE_PRICE_IDS: dict[str, str] = {
    "pro":           os.getenv("STRIPE_PRICE_PRO",          ""),
    "scale":         os.getenv("STRIPE_PRICE_SCALE",        ""),
    "addon_starter": os.getenv("STRIPE_PRICE_ADDON_STARTER",""),
    "addon_growth":  os.getenv("STRIPE_PRICE_ADDON_GROWTH", ""),
    "addon_scale":   os.getenv("STRIPE_PRICE_ADDON_SCALE",  ""),
}

ADDON_QUANTITIES: dict[str, int] = {
    "addon_starter": 10,
    "addon_growth":  50,
    "addon_scale":   200,
}


class BillingService:

    def _stripe(self):
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        return stripe

    def is_configured(self) -> bool:
        return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_IDS.get("pro"))

    # ── Checkout ─────────────────────────────────────────────────────────────

    def create_checkout_session(
        self,
        plan_or_addon: str,
        company_id: str,
        customer_email: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict:
        price_id = STRIPE_PRICE_IDS.get(plan_or_addon)
        if not price_id:
            raise ValueError(f"Plan ou add-on inconnu : {plan_or_addon}")

        is_addon  = plan_or_addon.startswith("addon_")
        _success  = (success_url or f"{FRONTEND_URL}/app/billing/success") + f"?plan={plan_or_addon}&session_id={{CHECKOUT_SESSION_ID}}"
        _cancel   = cancel_url or f"{FRONTEND_URL}/upgrade"

        stripe = self._stripe()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment" if is_addon else "subscription",
            success_url=_success,
            cancel_url=_cancel,
            customer_email=customer_email,
            metadata={"company_id": company_id, "plan_or_addon": plan_or_addon},
            allow_promotion_codes=True,
        )
        logger.info(f"[BILLING] Checkout session créée : {session.id} pour {company_id} ({plan_or_addon})")
        return {"checkout_url": session.url, "session_id": session.id}

    # ── Portal ───────────────────────────────────────────────────────────────

    def create_portal_session(
        self,
        company_id: str,
        return_url: Optional[str] = None,
    ) -> dict:
        _return = return_url or f"{FRONTEND_URL}/app/settings"

        # Récupérer le stripe_customer_id depuis Supabase
        customer_id = self._get_stripe_customer_id(company_id)
        if not customer_id:
            raise ValueError("Aucun abonnement Stripe trouvé pour ce compte.")

        stripe = self._stripe()
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=_return,
        )
        return {"portal_url": session.url}

    # ── Webhook ──────────────────────────────────────────────────────────────

    def process_webhook_event(self, payload: bytes, sig_header: str) -> dict:
        stripe = self._stripe()
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise ValueError(f"Webhook verification failed ({type(e).__name__}): {e}")

        etype = event["type"]
        logger.info(f"[WEBHOOK] Événement reçu : {etype}")

        if etype == "checkout.session.completed":
            session      = event["data"]["object"]
            company_id   = session["metadata"].get("company_id", "")
            plan_or_addon = session["metadata"].get("plan_or_addon", "")
            customer_id  = session.get("customer")

            if plan_or_addon.startswith("addon_"):
                qty = ADDON_QUANTITIES.get(plan_or_addon, 0)
                return {
                    "action": "add_bonus",
                    "company_id": company_id,
                    "quantity": qty,
                    "stripe_customer_id": customer_id,
                }
            else:
                return {
                    "action": "update_plan",
                    "company_id": company_id,
                    "plan": plan_or_addon,
                    "stripe_customer_id": customer_id,
                }

        elif etype == "customer.subscription.deleted":
            obj        = event["data"]["object"]
            customer_id = obj.get("customer", "")
            # Retrouver company_id via stripe_customer_id
            company_id = self._get_company_by_customer(customer_id)
            return {"action": "downgrade_free", "company_id": company_id}

        elif etype == "invoice.payment_failed":
            logger.warning(f"[WEBHOOK] Paiement échoué : {event['data']['object'].get('customer')}")
            return {"action": "noop", "reason": "payment_failed — notification à implémenter"}

        return {"action": "unhandled", "type": etype}

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_stripe_customer_id(self, company_id: str) -> Optional[str]:
        try:
            from main import get_supabase_service
            sb = get_supabase_service()
            r = sb.from_("companies").select("stripe_customer_id").eq("id", company_id).single().execute()
            return r.data.get("stripe_customer_id") if r.data else None
        except Exception:
            return None

    def _get_company_by_customer(self, stripe_customer_id: str) -> str:
        try:
            from main import get_supabase_service
            sb = get_supabase_service()
            r = sb.from_("companies").select("id").eq("stripe_customer_id", stripe_customer_id).limit(1).execute()
            return r.data[0]["id"] if r.data else ""
        except Exception:
            return ""
