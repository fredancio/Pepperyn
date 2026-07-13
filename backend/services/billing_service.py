"""
billing_service.py — Pepperyn Release 1.0
Facturation Stripe : Checkout, Portal, Webhook.

Données commerciales (plans, quantités packs, Price IDs) :
  → lues exclusivement depuis config/product_catalog.py
  → aucune constante commerciale locale dans ce fichier
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config infrastructure ─────────────────────────────────────────────────────

STRIPE_SECRET_KEY     = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL          = os.getenv("FRONTEND_URL", "https://www.pepperyn.com")

# ── Catalogue commercial — source unique de vérité ────────────────────────────
# STRIPE_PRICE_IDS et ADDON_QUANTITIES sont supprimés.
# Les données commerciales sont lues depuis config/product_catalog.py.

from config.product_catalog import (
    get_executive_capacity_pack,
    validate_stripe_price_ids,
)

# Plans commandables via Stripe Checkout.
# FREE est exclu : l'inscription FREE est directe, sans checkout.
# POWER et ENTERPRISE sont exclus : non commercialisés publiquement.
_ORDERABLE_PLAN_ENV: dict[str, str] = {
    "pro":   "STRIPE_PRICE_PRO",
    "scale": "STRIPE_PRICE_SCALE",
}


class BillingService:

    def _stripe(self):
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        return stripe

    def is_configured(self) -> bool:
        """Retourne True si la clé Stripe et le Price ID PRO sont configurés."""
        price_ids_ok = validate_stripe_price_ids()
        return bool(STRIPE_SECRET_KEY and price_ids_ok.get("pro"))

    # ── Checkout ─────────────────────────────────────────────────────────────

    def create_checkout_session(
        self,
        plan_or_addon: str,
        company_id: str,
        customer_email: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict:
        """
        Crée une session Stripe Checkout pour un Plan payant ou un Executive Capacity Pack.

        Règles métier :
        - FREE ne peut jamais déclencher un checkout (inscription directe).
        - POWER et ENTERPRISE ne sont pas commandables publiquement.
        - Seuls 'pro', 'scale' et les trois packs officiels sont acceptés.
        - Un Price ID absent de l'environnement provoque une erreur explicite.
        """
        # ── 1. Bloquer FREE ───────────────────────────────────────────────────
        if plan_or_addon == "free":
            raise ValueError(
                "FREE ne nécessite pas de checkout Stripe. "
                "L'inscription FREE est directe."
            )

        is_pack = plan_or_addon.startswith("addon_")

        if is_pack:
            # ── 2a. Executive Capacity Pack ───────────────────────────────────
            try:
                pack = get_executive_capacity_pack(plan_or_addon)
            except KeyError:
                raise ValueError(
                    f"Executive Capacity Pack inconnu : '{plan_or_addon}'. "
                    f"Packs valides : addon_starter, addon_growth, addon_scale."
                )

            price_id = pack.stripe_price_id   # property — lit depuis l'env à l'appel
            if price_id is None:
                raise ValueError(
                    f"Stripe Price ID manquant pour '{plan_or_addon}'. "
                    f"Configurer la variable d'environnement '{pack.stripe_price_id_env}'."
                )
            mode = "payment"

        else:
            # ── 2b. Plan payant (PRO ou SCALE uniquement) ─────────────────────
            if plan_or_addon not in _ORDERABLE_PLAN_ENV:
                raise ValueError(
                    f"Plan non commandable via Stripe : '{plan_or_addon}'. "
                    f"Plans commandables : {sorted(_ORDERABLE_PLAN_ENV.keys())}. "
                    f"POWER et ENTERPRISE ne sont pas commercialisés publiquement."
                )

            env_var  = _ORDERABLE_PLAN_ENV[plan_or_addon]
            price_id = os.environ.get(env_var)
            if not price_id:
                raise ValueError(
                    f"Stripe Price ID manquant pour Plan '{plan_or_addon}'. "
                    f"Configurer la variable d'environnement '{env_var}'."
                )
            mode = "subscription"

        _success = (
            (success_url or f"{FRONTEND_URL}/app/billing/success")
            + f"?plan={plan_or_addon}&session_id={{CHECKOUT_SESSION_ID}}"
        )
        _cancel = cancel_url or f"{FRONTEND_URL}/upgrade"

        stripe = self._stripe()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url=_success,
            cancel_url=_cancel,
            customer_email=customer_email,
            metadata={"company_id": company_id, "plan_or_addon": plan_or_addon},
            allow_promotion_codes=True,
        )
        logger.info(
            f"[BILLING] Checkout créé : {session.id} "
            f"— company={company_id} — produit={plan_or_addon} — mode={mode}"
        )
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
            session       = event["data"]["object"]
            metadata      = session["metadata"]
            company_id    = metadata["company_id"] if "company_id" in metadata else ""
            plan_or_addon = metadata["plan_or_addon"] if "plan_or_addon" in metadata else ""
            customer_id   = session["customer"] if "customer" in session else None

            if plan_or_addon.startswith("addon_"):
                # Quantité lue depuis product_catalog (source unique de vérité).
                # Ne jamais utiliser de constante locale ADDON_QUANTITIES.
                try:
                    qty = get_executive_capacity_pack(plan_or_addon).analyses_added
                except KeyError:
                    logger.error(
                        f"[WEBHOOK] Executive Capacity Pack inconnu dans metadata : "
                        f"'{plan_or_addon}'. Quantité 0 appliquée — vérifier les données Stripe."
                    )
                    qty = 0
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
            obj         = event["data"]["object"]
            customer_id = obj["customer"] if "customer" in obj else ""
            company_id  = self._get_company_by_customer(customer_id)
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
