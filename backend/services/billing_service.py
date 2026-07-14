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

        # subscription_data.metadata : injecte company_id et plan_or_addon directement
        # dans l'objet Subscription Stripe (pas seulement dans la Session).
        # Objectif : customer.subscription.created / updated / deleted peuvent résoudre
        # la company via sub.metadata.company_id SANS dépendre de l'ordre d'arrivée
        # des webhooks (checkout.session.completed vs customer.subscription.created).
        _subscription_data = (
            {"metadata": {"company_id": company_id, "plan_or_addon": plan_or_addon}}
            if mode == "subscription"
            else None
        )

        create_kwargs: dict = dict(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url=_success,
            cancel_url=_cancel,
            customer_email=customer_email,
            metadata={"company_id": company_id, "plan_or_addon": plan_or_addon},
            allow_promotion_codes=True,
        )
        if _subscription_data is not None:
            create_kwargs["subscription_data"] = _subscription_data

        session = stripe.checkout.Session.create(**create_kwargs)
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

        # ── Validation event.id (requis pour l'idempotence WP1B.3) ──────────────
        event_id = (event.get("id") or "").strip()
        if not event_id:
            logger.critical(
                f"[WEBHOOK INTEGRITY] stripe event.id absent ou vide. "
                f"L'idempotence ne peut pas être garantie sans identifiant d'événement. "
                f"etype={etype}"
            )
            raise ValueError(
                f"Stripe event.id absent ou vide (etype={etype}). "
                f"L'idempotence ne peut pas être garantie — webhook non traitable."
            )

        if etype == "checkout.session.completed":
            session     = event["data"]["object"]
            metadata    = session.get("metadata") or {}
            customer_id = session.get("customer")
            session_id  = session.get("id", "SESSION_ID_INCONNU")

            # ── Validation d'intégrité des metadata ──────────────────────────
            # Un champ manquant ou vide = paiement non imputable = lever
            # immédiatement pour que Stripe retente le webhook.
            company_id    = (metadata.get("company_id")    or "").strip()
            plan_or_addon = (metadata.get("plan_or_addon") or "").strip()

            if not company_id:
                logger.critical(
                    f"[WEBHOOK INTEGRITY] company_id absent ou vide dans les metadata. "
                    f"stripe_session={session_id} — investigation manuelle requise."
                )
                raise ValueError(
                    f"company_id absent ou vide dans les metadata Stripe "
                    f"(stripe_session={session_id}). "
                    f"Webhook non traitable — retraitement manuel requis."
                )

            if not plan_or_addon:
                logger.critical(
                    f"[WEBHOOK INTEGRITY] plan_or_addon absent ou vide dans les metadata. "
                    f"stripe_session={session_id} company_id={company_id} — investigation requise."
                )
                raise ValueError(
                    f"plan_or_addon absent ou vide dans les metadata Stripe "
                    f"(stripe_session={session_id}, company_id={company_id}). "
                    f"Webhook non traitable — retraitement manuel requis."
                )

            if plan_or_addon.startswith("addon_"):
                # ── Executive Capacity Pack ───────────────────────────────────
                # RÈGLE D'INTÉGRITÉ : un pack inconnu NE DOIT JAMAIS être
                # transformé silencieusement en quantité 0.
                # Le client a payé — il faut que ses crédits soient appliqués.
                # On lève ValueError pour que le webhook retourne HTTP non-2xx
                # et que Stripe retente automatiquement.
                try:
                    pack = get_executive_capacity_pack(plan_or_addon)
                except KeyError:
                    logger.critical(
                        f"[WEBHOOK INTEGRITY] Executive Capacity Pack inconnu : "
                        f"'{plan_or_addon}'. stripe_session={session_id} "
                        f"company_id={company_id} customer_id={customer_id}. "
                        f"Le client A ÉTÉ DÉBITÉ mais N'A PAS ÉTÉ CRÉDITÉ. "
                        f"Retraitement manuel OBLIGATOIRE."
                    )
                    raise ValueError(
                        f"Executive Capacity Pack inconnu dans les metadata Stripe : "
                        f"'{plan_or_addon}' (stripe_session={session_id}, "
                        f"company_id={company_id}). "
                        f"Impossible de créditer — retraitement manuel requis."
                    )

                qty = pack.analyses_added   # source unique de vérité : product_catalog
                return {
                    "action":             "add_bonus",
                    "company_id":         company_id,
                    "quantity":           qty,
                    "stripe_customer_id": customer_id,
                    "stripe_event_id":    event_id,
                    "event_type":         etype,
                }
            else:
                # ── Plan payant (PRO ou SCALE) ────────────────────────────────
                # Initialise uniquement : plan, stripe_customer_id, stripe_subscription_id.
                # Le champ subscription_status est géré par customer.subscription.* (ci-dessous).
                subscription_id = session.get("subscription")
                return {
                    "action":                 "init_subscription",
                    "company_id":             company_id,
                    "plan":                   plan_or_addon,
                    "stripe_customer_id":     customer_id,
                    "stripe_subscription_id": subscription_id,
                    "stripe_event_id":        event_id,
                    "event_type":             etype,
                }

        elif etype in ("customer.subscription.created", "customer.subscription.updated"):
            # ── Source de vérité du cycle de vie de l'abonnement ─────────────
            # Ces événements gouvernent subscription_status pour toute la durée
            # de vie de l'abonnement (renouvellements, impayés, changements de plan).
            # customer.subscription.updated est la SEULE autorité pour subscription_status.
            sub             = event["data"]["object"]
            customer_id     = sub.get("customer", "")
            subscription_id = sub.get("id", "")
            sub_status      = sub.get("status", "")   # active | trialing | past_due | …
            sub_metadata    = sub.get("metadata") or {}

            # Résolution optionnelle du plan depuis la Price ID Stripe.
            # Utile pour détecter un changement PRO ↔ SCALE via le Billing Portal.
            price_id = None
            try:
                price_id = sub["items"]["data"][0]["price"]["id"]
            except (KeyError, IndexError, TypeError):
                pass
            new_plan = self._resolve_plan_from_price_id(price_id)

            # ── Résolution du company_id ──────────────────────────────────────
            # Priorité 1 : subscription.metadata.company_id
            #   → garanti si la session Checkout a été créée avec subscription_data.metadata.
            #   → résistant à l'ordre d'arrivée des webhooks (aucune dépendance envers
            #     checkout.session.completed).
            # Priorité 2 : fallback via stripe_customer_id
            #   → couvre les subscriptions créées avant l'ajout de subscription_data.metadata.
            # Si aucune résolution n'aboutit : lever ValueError.
            #   → Stripe retente le webhook (≥ 3 jours) → résolution possible lors du retry.
            company_id = (sub_metadata.get("company_id") or "").strip()
            if not company_id:
                company_id = self._get_company_by_customer(customer_id)

            if not company_id:
                logger.critical(
                    f"[WEBHOOK INTEGRITY] {etype} — company_id introuvable. "
                    f"subscription_id={subscription_id} customer_id={customer_id} "
                    f"sub_metadata={sub_metadata!r} stripe_event_id={event_id}. "
                    f"Stripe va retenter l'événement."
                )
                raise ValueError(
                    f"company_id introuvable pour {etype} "
                    f"(subscription_id={subscription_id}, customer_id={customer_id}). "
                    f"Webhook non traitable — Stripe va retenter."
                )

            return {
                "action":                 "sync_subscription",
                "company_id":             company_id,
                "stripe_customer_id":     customer_id,
                "stripe_subscription_id": subscription_id,
                "subscription_status":    sub_status,
                "plan":                   new_plan,    # None si prix non résolu → plan inchangé en DB
                "stripe_event_id":        event_id,
                "event_type":             etype,
            }

        elif etype == "invoice.paid":
            # ── Paiement reçu — enregistrement sans mise à jour du statut ────
            # subscription_status est géré EXCLUSIVEMENT par customer.subscription.updated.
            # Stripe déclenche customer.subscription.updated (status→active) si le statut
            # changeait (ex. past_due → active). S'il était déjà active, il l'est toujours.
            # → invoice.paid est conservé dans le registre d'idempotence pour audit
            #   et sera utilisable dans le futur (notifications, analytics, etc.).
            invoice     = event["data"]["object"]
            customer_id = invoice.get("customer", "")
            logger.info(
                f"[WEBHOOK] invoice.paid — customer={customer_id} "
                f"stripe_event_id={event_id} — statut délégué à customer.subscription.updated."
            )
            return {
                "action":          "noop",
                "reason":          "invoice.paid — subscription_status délégué à subscription.updated",
                "stripe_event_id": event_id,
                "event_type":      etype,
            }

        elif etype == "customer.subscription.deleted":
            # ── Annulation de l'abonnement → downgrade FREE ───────────────────
            obj          = event["data"]["object"]
            customer_id  = obj.get("customer", "")
            sub_metadata = obj.get("metadata") or {}

            # Résolution metadata-first (même logique que subscription.created/updated).
            # Si company introuvable : noop (pas de raise — un compte inexistant
            # ne peut pas être downgradé, et les retries Stripe seraient infinis).
            company_id = (sub_metadata.get("company_id") or "").strip()
            if not company_id:
                company_id = self._get_company_by_customer(customer_id)

            if not company_id:
                logger.critical(
                    f"[WEBHOOK INTEGRITY] customer.subscription.deleted — company_id introuvable. "
                    f"customer_id={customer_id} sub_metadata={sub_metadata!r} "
                    f"stripe_event_id={event_id}. Downgrade impossible — événement archivé."
                )
                return {
                    "action":          "noop",
                    "reason":          f"company_id_not_found — customer={customer_id}",
                    "stripe_event_id": event_id,
                    "event_type":      etype,
                }

            return {
                "action":          "downgrade_free",
                "company_id":      company_id,
                "stripe_event_id": event_id,
                "event_type":      etype,
            }

        elif etype == "invoice.payment_failed":
            # ── Échec de paiement — enregistrement sans mise à jour du statut ─
            # Quand un paiement échoue, Stripe marque l'abonnement comme past_due
            # (selon la politique de relance configurée) et déclenche
            # customer.subscription.updated (status→past_due).
            # subscription_status est géré EXCLUSIVEMENT par customer.subscription.updated.
            # → invoice.payment_failed est conservé dans le registre pour audit et alertes.
            invoice     = event["data"]["object"]
            customer_id = invoice.get("customer", "")
            logger.warning(
                f"[WEBHOOK] invoice.payment_failed — customer={customer_id} "
                f"stripe_event_id={event_id} — statut délégué à customer.subscription.updated."
            )
            return {
                "action":          "noop",
                "reason":          "invoice.payment_failed — subscription_status délégué à subscription.updated",
                "stripe_event_id": event_id,
                "event_type":      etype,
            }

        return {
            "action":          "unhandled",
            "type":            etype,
            "stripe_event_id": event_id,
            "event_type":      etype,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _resolve_plan_from_price_id(self, price_id: str) -> Optional[str]:
        """
        Résout un Stripe Price ID vers un identifiant de plan Pepperyn (pro | scale).

        Parcourt _ORDERABLE_PLAN_ENV et compare price_id aux variables d'env actives.
        Retourne None si le price_id ne correspond à aucun plan connu
        (cas d'une price non Pepperyn ou d'une variable d'env absente).
        Utilisé par customer.subscription.created/updated pour détecter les changements
        de plan PRO ↔ SCALE opérés via le Stripe Billing Portal.
        """
        if not price_id:
            return None
        for plan_key, env_var in _ORDERABLE_PLAN_ENV.items():
            if price_id == os.environ.get(env_var):
                return plan_key
        return None

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
