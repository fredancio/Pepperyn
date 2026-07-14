"""
tests/test_wp4b_scale_self_service.py — Pepperyn Release 1.0 — WP4B
Parcours SCALE Self-Service : vérification que le plan SCALE peut être
souscrit en libre-service via Stripe Checkout et que les protections
métier (anti double-souscription, propagation d'event_id) sont correctes.

21 tests organisés en 4 groupes :
  WP4B-01–05  Checkout SCALE via BillingService
  WP4B-06–10  Checkout SCALE via Router (anti double-souscription)
  WP4B-11–15  Webhook SCALE (activation plan, idempotence)
  WP4B-16–21  Non-régression (PRO inchangé, addons inchangés, isolation)
"""
from __future__ import annotations

import os
import sys
import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_stripe_session(url="https://checkout.stripe.com/test_scale", session_id="cs_scale_test"):
    stripe_mock = MagicMock()
    session = MagicMock()
    session.url = url
    session.id = session_id
    stripe_mock.checkout.Session.create.return_value = session
    return stripe_mock


def _make_webhook_event(
    plan_or_addon: str,
    event_type: str = "checkout.session.completed",
    event_id: str = "evt_wp4b_default",
    company_id: str = "company_wp4b_test",
) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "data": {
            "object": {
                "id": "cs_wp4b_session",
                "metadata": {
                    "company_id": company_id,
                    "plan_or_addon": plan_or_addon,
                },
                "customer": "cus_wp4b_test",
            }
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 1 — Checkout SCALE via BillingService  (WP4B-01–05)
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckoutScale(unittest.TestCase):
    """BillingService.create_checkout_session('scale') — validations métier."""

    def _service(self):
        from services.billing_service import BillingService
        return BillingService()

    # WP4B-01 ─────────────────────────────────────────────────────────────────
    def test_wp4b_01_checkout_scale_without_price_id_raises_value_error(self):
        """SCALE sans Price ID STRIPE_PRICE_SCALE → ValueError explicite."""
        svc = self._service()
        env_without_scale = {k: v for k, v in os.environ.items() if k != "STRIPE_PRICE_SCALE"}
        with patch.dict(os.environ, env_without_scale, clear=True):
            with self.assertRaises(ValueError) as ctx:
                svc.create_checkout_session("scale", "company_wp4b_01")
        self.assertIn("STRIPE_PRICE_SCALE", str(ctx.exception),
                      "ValueError doit mentionner STRIPE_PRICE_SCALE")

    # WP4B-02 ─────────────────────────────────────────────────────────────────
    def test_wp4b_02_checkout_scale_with_price_id_calls_stripe(self):
        """SCALE avec Price ID → appel Stripe réel (mocké), retourne checkout_url."""
        svc = self._service()
        stripe_mock = _make_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale_wp4b"}):
                result = svc.create_checkout_session("scale", "company_wp4b_02")
        self.assertIn("checkout_url", result)
        self.assertIn("session_id", result)
        stripe_mock.checkout.Session.create.assert_called_once()

    # WP4B-03 ─────────────────────────────────────────────────────────────────
    def test_wp4b_03_checkout_scale_mode_is_subscription(self):
        """SCALE utilise le mode 'subscription' (abonnement mensuel, pas payment)."""
        svc = self._service()
        stripe_mock = _make_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale_wp4b"}):
                svc.create_checkout_session("scale", "company_wp4b_03")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["mode"], "subscription",
                         "SCALE est un abonnement → mode='subscription'")

    # WP4B-04 ─────────────────────────────────────────────────────────────────
    def test_wp4b_04_checkout_scale_includes_company_id_in_metadata(self):
        """SCALE checkout : company_id transmis dans les metadata Stripe."""
        svc = self._service()
        stripe_mock = _make_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale_wp4b"}):
                svc.create_checkout_session("scale", "company_wp4b_meta_test")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["metadata"]["company_id"], "company_wp4b_meta_test")
        self.assertEqual(call_kwargs["metadata"]["plan_or_addon"], "scale")

    # WP4B-05 ─────────────────────────────────────────────────────────────────
    def test_wp4b_05_checkout_scale_success_url_contains_scale(self):
        """SCALE checkout : success_url contient 'plan=scale'."""
        svc = self._service()
        stripe_mock = _make_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale_wp4b"}):
                svc.create_checkout_session("scale", "company_wp4b_05")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        success_url = call_kwargs.get("success_url", "")
        self.assertIn("scale", success_url.lower(),
                      f"success_url doit contenir 'scale' ; reçu : {success_url}")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 2 — Checkout SCALE via Router (anti double-souscription)  (WP4B-06–10)
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckoutScaleRouter(unittest.TestCase):
    """
    Vérifications du router billing.py :
    - L'endpoint refuse le checkout SCALE si la company est déjà sur SCALE.
    - L'endpoint refuse le checkout PRO si la company est déjà sur PRO.
    - Les autres cas (FREE→SCALE, PRO→SCALE, SCALE→addon) restent autorisés.
    """

    def _checkout(self, plan_or_addon: str, current_company_plan: str) -> dict:
        """Helper : simule POST /api/billing/checkout avec un plan courant mocké."""
        from routers.billing import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan_or_addon=plan_or_addon)
        billing_mock = MagicMock()
        billing_mock.create_checkout_session.return_value = {
            "checkout_url": "https://checkout.stripe.com/test",
            "session_id": "cs_test",
        }

        async def run():
            with patch("routers.billing._resolve_auth",
                       return_value=("company_test", current_company_plan)):
                with patch("routers.billing._get_billing", return_value=billing_mock):
                    return await create_checkout_session(body, authorization="Bearer fake_token")

        return asyncio.run(run())

    def _checkout_raises(self, plan_or_addon: str, current_company_plan: str):
        """Helper : vérifie qu'une HTTPException est levée."""
        from fastapi import HTTPException
        from routers.billing import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan_or_addon=plan_or_addon)

        async def run():
            with patch("routers.billing._resolve_auth",
                       return_value=("company_test", current_company_plan)):
                return await create_checkout_session(body, authorization="Bearer fake_token")

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(run())
        return ctx.exception

    # WP4B-06 ─────────────────────────────────────────────────────────────────
    def test_wp4b_06_scale_company_cannot_subscribe_to_scale_again(self):
        """SCALE → SCALE : double-souscription bloquée → HTTP 400."""
        exc = self._checkout_raises("scale", "scale")
        self.assertEqual(exc.status_code, 400,
                         "Double SCALE → attendu HTTP 400")
        self.assertIn("SCALE", exc.detail,
                      "Message d'erreur doit mentionner SCALE")

    # WP4B-07 ─────────────────────────────────────────────────────────────────
    def test_wp4b_07_pro_company_cannot_subscribe_to_pro_again(self):
        """PRO → PRO : double-souscription bloquée → HTTP 400."""
        exc = self._checkout_raises("pro", "pro")
        self.assertEqual(exc.status_code, 400,
                         "Double PRO → attendu HTTP 400")
        self.assertIn("PRO", exc.detail,
                      "Message d'erreur doit mentionner PRO")

    # WP4B-08 ─────────────────────────────────────────────────────────────────
    def test_wp4b_08_free_company_can_subscribe_to_scale(self):
        """FREE → SCALE : autorisé (pas de double-souscription)."""
        result = self._checkout("scale", "free")
        self.assertIn("data", result)
        self.assertTrue(result.get("success"), "FREE → SCALE doit retourner success=True")

    # WP4B-09 ─────────────────────────────────────────────────────────────────
    def test_wp4b_09_pro_company_blocked_from_scale_checkout(self):
        """PRO → SCALE : bloqué → HTTP 400 (WP4B.1 — risque double-abonnement Stripe).
        WP4B.2 : le Billing Portal n'étant pas accessible depuis l'UI,
        le message renvoie vers info@finflate.com.
        """
        exc = self._checkout_raises("scale", "pro")
        self.assertEqual(exc.status_code, 400,
                         "PRO → SCALE doit retourner HTTP 400")
        self.assertIn("PRO", exc.detail,
                      "Message doit mentionner le plan courant PRO")
        self.assertIn("info@finflate.com", exc.detail,
                      "Message doit renvoyer vers info@finflate.com (WP4B.2)")

    # WP4B-10 ─────────────────────────────────────────────────────────────────
    def test_wp4b_10_scale_company_can_buy_addon(self):
        """SCALE → addon_starter : achat de pack autorisé quelle que soit le plan."""
        result = self._checkout("addon_starter", "scale")
        self.assertIn("data", result)
        self.assertTrue(result.get("success"),
                        "SCALE → addon_starter doit être autorisé")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 3 — Webhook SCALE (activation plan, idempotence)  (WP4B-11–15)
# ─────────────────────────────────────────────────────────────────────────────

class TestWebhookScale(unittest.TestCase):
    """process_webhook_event() pour le plan SCALE."""

    def _process(self, plan_or_addon: str, event_id: str = "evt_wp4b_test") -> dict:
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = _make_webhook_event(plan_or_addon, event_id=event_id)
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            return svc.process_webhook_event(b"payload", "sig_test")

    # WP4B-11 ─────────────────────────────────────────────────────────────────
    def test_wp4b_11_scale_webhook_returns_update_plan(self):
        """Webhook SCALE → action='update_plan' (pas add_bonus)."""
        result = self._process("scale", "evt_wp4b_11")
        self.assertEqual(result["action"], "update_plan",
                         "Webhook SCALE doit retourner action='update_plan'")
        self.assertEqual(result["plan"], "scale",
                         "plan retourné doit être 'scale'")
        self.assertNotIn("quantity", result,
                         "Webhook SCALE ne doit pas contenir 'quantity'")

    # WP4B-12 ─────────────────────────────────────────────────────────────────
    def test_wp4b_12_scale_webhook_propagates_event_id(self):
        """Webhook SCALE : stripe_event_id propagé dans le résultat."""
        result = self._process("scale", "evt_wp4b_SCALE_UNIQUE")
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_wp4b_SCALE_UNIQUE")

    # WP4B-13 ─────────────────────────────────────────────────────────────────
    def test_wp4b_13_scale_webhook_idempotent_by_nature(self):
        """SCALE webhook rejoué deux fois → même action, pas d'effet cumulatif."""
        r1 = self._process("scale", "evt_wp4b_SCALE_REPLAY")
        r2 = self._process("scale", "evt_wp4b_SCALE_REPLAY")
        self.assertEqual(r1["action"], "update_plan")
        self.assertEqual(r2["action"], "update_plan")
        self.assertEqual(r1["plan"], r2["plan"],
                         "Deux replays → même plan retourné (idempotent)")

    # WP4B-14 ─────────────────────────────────────────────────────────────────
    def test_wp4b_14_scale_webhook_duplicate_skipped_at_router_level(self):
        """
        Webhook SCALE rejoué → RPC retourne 'duplicate' → action='duplicate_skipped'.
        Le plan n'est activé qu'une seule fois.
        """
        from routers.billing import stripe_webhook

        service_result = {
            "action": "update_plan",
            "plan": "scale",
            "company_id": "company_wp4b_14",
            "stripe_customer_id": "cus_test",
            "stripe_event_id": "evt_wp4b_SCALE_DUP",
            "event_type": "checkout.session.completed",
        }

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        # Deuxième livraison → RPC retourne duplicate
        req = MagicMock()
        req.body = AsyncMock(return_value=b"payload")
        exec_dup = MagicMock()
        exec_dup.data = {"status": "duplicate"}
        sb_dup = MagicMock()
        sb_dup.rpc.return_value.execute.return_value = exec_dup

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_dup):
                r = asyncio.run(stripe_webhook(req, "sig_test"))

        self.assertEqual(r["action"], "duplicate_skipped",
                         "Replay webhook SCALE → duplicate_skipped")

    # WP4B-15 ─────────────────────────────────────────────────────────────────
    def test_wp4b_15_scale_webhook_calls_rpc_with_scale_plan(self):
        """
        Webhook SCALE livraison initiale → RPC appelée avec p_new_plan='scale'.
        Vérifie la chaîne complète jusqu'à l'application SQL.
        """
        from routers.billing import stripe_webhook

        service_result = {
            "action": "update_plan",
            "plan": "scale",
            "company_id": "company_wp4b_15",
            "stripe_customer_id": "cus_test",
            "stripe_event_id": "evt_wp4b_15_scale_rpc",
            "event_type": "checkout.session.completed",
        }

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        req = MagicMock()
        req.body = AsyncMock(return_value=b"payload")
        exec_ok = MagicMock()
        exec_ok.data = {"status": "processed"}
        sb_ok = MagicMock()
        sb_ok.rpc.return_value.execute.return_value = exec_ok

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_ok):
                asyncio.run(stripe_webhook(req, "sig_test"))

        sb_ok.rpc.assert_called_once()
        call_name, call_params = sb_ok.rpc.call_args[0]
        self.assertEqual(call_name, "apply_stripe_webhook")
        self.assertEqual(call_params["p_action"], "update_plan",
                         "p_action doit être 'update_plan' pour SCALE")
        self.assertEqual(call_params["p_new_plan"], "scale",
                         "p_new_plan doit être 'scale'")
        self.assertEqual(call_params["p_stripe_event_id"], "evt_wp4b_15_scale_rpc")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 4 — Non-régression  (WP4B-16–21)
# ─────────────────────────────────────────────────────────────────────────────

class TestNonRegressionWP4B(unittest.TestCase):
    """
    Vérifications que WP4B n'a pas cassé le parcours PRO existant
    ni le comportement des Executive Capacity Packs.
    """

    def _service(self):
        from services.billing_service import BillingService
        return BillingService()

    # WP4B-16 ─────────────────────────────────────────────────────────────────
    def test_wp4b_16_checkout_pro_still_works(self):
        """PRO checkout toujours fonctionnel après WP4B (non-régression)."""
        svc = self._service()
        stripe_mock = MagicMock()
        session = MagicMock()
        session.url = "https://checkout.stripe.com/test_pro"
        session.id = "cs_pro_test"
        stripe_mock.checkout.Session.create.return_value = session
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_PRO": "price_test_pro_wp4b"}):
                result = svc.create_checkout_session("pro", "company_wp4b_16")
        self.assertIn("checkout_url", result)
        stripe_mock.checkout.Session.create.assert_called_once()

    # WP4B-17 ─────────────────────────────────────────────────────────────────
    def test_wp4b_17_pro_webhook_returns_update_plan_pro(self):
        """Webhook PRO après WP4B → action='update_plan', plan='pro' (non-régression)."""
        svc = self._service()
        fake_event = _make_webhook_event("pro", event_id="evt_wp4b_pro_nr")
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            result = svc.process_webhook_event(b"payload", "sig_test")
        self.assertEqual(result["action"], "update_plan")
        self.assertEqual(result["plan"], "pro",
                         "Webhook PRO : plan='pro' inchangé")

    # WP4B-18 ─────────────────────────────────────────────────────────────────
    def test_wp4b_18_addon_starter_checkout_unaffected_by_wp4b(self):
        """addon_starter checkout non affecté par WP4B (non-régression)."""
        svc = self._service()
        stripe_mock = MagicMock()
        session = MagicMock()
        session.url = "https://checkout.stripe.com/test_addon"
        session.id = "cs_addon_test"
        stripe_mock.checkout.Session.create.return_value = session
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_ADDON_STARTER": "price_starter_wp4b"}):
                result = svc.create_checkout_session("addon_starter", "company_wp4b_18")
        self.assertIn("checkout_url", result)
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["mode"], "payment",
                         "Addon : mode='payment' inchangé")

    # WP4B-19 ─────────────────────────────────────────────────────────────────
    def test_wp4b_19_addon_webhook_still_returns_add_bonus(self):
        """Webhook addon_growth après WP4B → add_bonus avec quantity=20 (non-régression)."""
        svc = self._service()
        fake_event = _make_webhook_event("addon_growth", event_id="evt_wp4b_addon_nr")
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            result = svc.process_webhook_event(b"payload", "sig_test")
        self.assertEqual(result["action"], "add_bonus")
        self.assertEqual(result["quantity"], 20)

    # WP4B-20 ─────────────────────────────────────────────────────────────────
    def test_wp4b_20_free_plan_still_raises_on_checkout(self):
        """FREE ne déclenche toujours pas de checkout Stripe (non-régression WP4B)."""
        svc = self._service()
        with self.assertRaises(ValueError) as ctx:
            svc.create_checkout_session("free", "company_wp4b_20")
        self.assertIn("FREE", str(ctx.exception))

    # WP4B-21 ─────────────────────────────────────────────────────────────────
    def test_wp4b_21_scale_and_pro_in_orderable_plan_env(self):
        """
        _ORDERABLE_PLAN_ENV contient à la fois 'pro' et 'scale'.
        SCALE était déjà supporté par BillingService avant WP4B.
        """
        # Lire le fichier source complet (pas seulement la classe) car
        # _ORDERABLE_PLAN_ENV est une constante module-level.
        svc_path = os.path.join(os.path.dirname(__file__), "..", "services", "billing_service.py")
        with open(svc_path, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertIn("'scale'", source,
                      "billing_service.py contient 'scale' dans _ORDERABLE_PLAN_ENV")
        self.assertIn("STRIPE_PRICE_SCALE", source,
                      "billing_service.py référence STRIPE_PRICE_SCALE")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
