"""
tests/test_wp4b1_activation_safety.py — Pepperyn Release 1.0 — WP4B.1
Finalisation et validation réelle du parcours SCALE.

Deux problèmes bloquants corrigés dans WP4B.1 :
  1. La page Success annonçait le plan activé uniquement via ?plan=scale (URL param),
     sans vérification backend. Elle poll désormais /api/billing/usage.
  2. PRO → SCALE créait un second abonnement Stripe. Le checkout est désormais
     bloqué pour toute company ayant déjà un plan payant (PRO ou SCALE).

19 tests organisés en 3 groupes :
  WP4B1-01–07  Anti double-souscription cross-plan (PRO→SCALE, SCALE→PRO bloqués)
  WP4B1-08–11  Endpoint /api/billing/usage retourne le champ 'plan'
  WP4B1-12–19  Assertions statiques sur la page Success (polling, timeout, etc.)
"""
from __future__ import annotations

import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

_FRONTEND_SUCCESS = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "frontend", "app", "app", "billing", "success", "page.tsx"
)


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 1 — Anti double-souscription cross-plan  (WP4B1-01–07)
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossPlanSubscriptionBlock(unittest.TestCase):
    """
    WP4B.1 — La protection anti double-souscription couvre désormais les cas
    cross-plan (PRO → SCALE, SCALE → PRO), pas uniquement same-plan.

    Contexte : create_checkout_session() dans billing_service.py passe
    customer_email mais pas customer=existing_stripe_customer_id.
    Sans blocage, un PRO → SCALE checkout créerait un second abonnement Stripe.
    """

    def _checkout_raises(self, plan_or_addon: str, current_company_plan: str):
        """Vérifie qu'une HTTPException est levée et la retourne."""
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

    def _checkout_ok(self, plan_or_addon: str, current_company_plan: str) -> dict:
        """Vérifie qu'aucune HTTPException n'est levée et retourne le résultat."""
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

    # WP4B1-01 ────────────────────────────────────────────────────────────────
    def test_wp4b1_01_pro_to_scale_blocked(self):
        """PRO → SCALE : bloqué → HTTP 400 (double-abonnement Stripe évité)."""
        exc = self._checkout_raises("scale", "pro")
        self.assertEqual(exc.status_code, 400,
                         "PRO → SCALE doit retourner HTTP 400")

    # WP4B1-02 ────────────────────────────────────────────────────────────────
    def test_wp4b1_02_scale_to_pro_blocked(self):
        """SCALE → PRO : bloqué → HTTP 400 (downgrade via checkout interdit)."""
        exc = self._checkout_raises("pro", "scale")
        self.assertEqual(exc.status_code, 400,
                         "SCALE → PRO doit retourner HTTP 400")

    # WP4B1-03 ────────────────────────────────────────────────────────────────
    def test_wp4b1_03_cross_plan_error_mentions_current_plan(self):
        """PRO → SCALE : message d'erreur mentionne le plan courant (PRO)."""
        exc = self._checkout_raises("scale", "pro")
        self.assertIn("PRO", exc.detail,
                      "Message doit mentionner le plan actuel PRO")

    # WP4B1-04 ────────────────────────────────────────────────────────────────
    def test_wp4b1_04_cross_plan_error_mentions_contact_email(self):
        """PRO → SCALE : message d'erreur renvoie vers info@finflate.com.
        WP4B.2 : le Billing Portal n'est pas accessible depuis l'UI frontend
        et le webhook subscription.updated n'est pas géré.
        L'upgrade PRO→SCALE passe provisoirement par email.
        """
        exc = self._checkout_raises("scale", "pro")
        self.assertIn("info@finflate.com", exc.detail,
                      "Message doit renvoyer vers info@finflate.com")

    # WP4B1-05 ────────────────────────────────────────────────────────────────
    def test_wp4b1_05_free_to_pro_still_allowed(self):
        """FREE → PRO : toujours autorisé (non affecté par WP4B.1)."""
        result = self._checkout_ok("pro", "free")
        self.assertTrue(result.get("success"),
                        "FREE → PRO doit retourner success=True")

    # WP4B1-06 ────────────────────────────────────────────────────────────────
    def test_wp4b1_06_free_to_scale_still_allowed(self):
        """FREE → SCALE : toujours autorisé (non affecté par WP4B.1)."""
        result = self._checkout_ok("scale", "free")
        self.assertTrue(result.get("success"),
                        "FREE → SCALE doit retourner success=True")

    # WP4B1-07 ────────────────────────────────────────────────────────────────
    def test_wp4b1_07_scale_to_addon_still_allowed(self):
        """SCALE → addon_starter : toujours autorisé (les packs ne sont pas des plans)."""
        result = self._checkout_ok("addon_starter", "scale")
        self.assertTrue(result.get("success"),
                        "SCALE → addon_starter doit être autorisé")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 2 — /api/billing/usage retourne le champ 'plan'  (WP4B1-08–11)
# ─────────────────────────────────────────────────────────────────────────────

class TestUsageEndpointReturnsPlan(unittest.TestCase):
    """
    WP4B.1 — La page Success poll /api/billing/usage pour confirmer l'activation.
    L'endpoint doit inclure data.plan dans sa réponse.
    """

    def _call_usage(self, current_plan: str) -> dict:
        """Helper : simule GET /api/billing/usage pour une company avec un plan donné."""
        from routers.billing import get_usage

        usage_data = {
            "plan": current_plan,
            "analyses_used": 0,
            "analyses_limit": 30,
            "analyses_remaining": 30,
        }
        usage_mock = MagicMock()
        usage_mock.get_usage_this_month.return_value = usage_data

        async def run():
            with patch("routers.billing._resolve_auth",
                       return_value=("company_test", current_plan)):
                with patch("routers.billing._get_usage", return_value=usage_mock):
                    return await get_usage(authorization="Bearer fake_token")

        return asyncio.run(run())

    # WP4B1-08 ────────────────────────────────────────────────────────────────
    def test_wp4b1_08_usage_endpoint_returns_plan_field(self):
        """GET /api/billing/usage retourne bien le champ 'plan' dans data."""
        resp = self._call_usage("pro")
        self.assertIn("data", resp, "Réponse doit contenir 'data'")
        self.assertIn("plan", resp["data"],
                      "data doit contenir le champ 'plan'")

    # WP4B1-09 ────────────────────────────────────────────────────────────────
    def test_wp4b1_09_usage_endpoint_plan_matches_pro(self):
        """GET /api/billing/usage : data.plan='pro' pour une company PRO."""
        resp = self._call_usage("pro")
        self.assertEqual(resp["data"]["plan"], "pro",
                         "data.plan doit être 'pro' pour une company PRO")

    # WP4B1-10 ────────────────────────────────────────────────────────────────
    def test_wp4b1_10_usage_endpoint_plan_matches_scale(self):
        """GET /api/billing/usage : data.plan='scale' pour une company SCALE."""
        resp = self._call_usage("scale")
        self.assertEqual(resp["data"]["plan"], "scale",
                         "data.plan doit être 'scale' pour une company SCALE")

    # WP4B1-11 ────────────────────────────────────────────────────────────────
    def test_wp4b1_11_usage_endpoint_plan_matches_free(self):
        """GET /api/billing/usage : data.plan='free' pour une company FREE."""
        resp = self._call_usage("free")
        self.assertEqual(resp["data"]["plan"], "free",
                         "data.plan doit être 'free' pour une company FREE")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 3 — Success page : assertions statiques  (WP4B1-12–19)
# ─────────────────────────────────────────────────────────────────────────────

class TestSuccessPageStaticAssertions(unittest.TestCase):
    """
    WP4B.1 — Vérifications statiques du fichier billing/success/page.tsx.
    La page a été réécrite pour poller le backend au lieu d'afficher le succès
    immédiatement à partir du paramètre URL.
    """

    @classmethod
    def setUpClass(cls):
        success_path = os.path.normpath(_FRONTEND_SUCCESS)
        if not os.path.exists(success_path):
            raise FileNotFoundError(
                f"success/page.tsx introuvable : {success_path}"
            )
        with open(success_path, "r", encoding="utf-8") as f:
            cls.src = f.read()

    # WP4B1-12 ────────────────────────────────────────────────────────────────
    def test_wp4b1_12_success_page_has_waiting_state(self):
        """La page Success possède un état 'waiting' (activation en attente)."""
        self.assertIn("'waiting'", self.src,
                      "La page doit déclarer l'état 'waiting'")

    # WP4B1-13 ────────────────────────────────────────────────────────────────
    def test_wp4b1_13_success_page_has_timeout_state(self):
        """La page Success possède un état 'timeout'."""
        self.assertIn("'timeout'", self.src,
                      "La page doit déclarer l'état 'timeout'")

    # WP4B1-14 ────────────────────────────────────────────────────────────────
    def test_wp4b1_14_success_page_has_confirmed_state(self):
        """La page Success possède un état 'confirmed'."""
        self.assertIn("'confirmed'", self.src,
                      "La page doit déclarer l'état 'confirmed'")

    # WP4B1-15 ────────────────────────────────────────────────────────────────
    def test_wp4b1_15_success_page_polls_billing_usage(self):
        """La page Success appelle /api/billing/usage pour confirmer l'activation."""
        self.assertIn("/api/billing/usage", self.src,
                      "La page doit poller /api/billing/usage")

    # WP4B1-16 ────────────────────────────────────────────────────────────────
    def test_wp4b1_16_success_page_uses_supabase_auth(self):
        """La page Success utilise supabase.auth.getSession() pour obtenir le token."""
        self.assertIn("supabase.auth.getSession", self.src,
                      "La page doit appeler supabase.auth.getSession")

    # WP4B1-17 ────────────────────────────────────────────────────────────────
    def test_wp4b1_17_success_page_has_max_poll_attempts(self):
        """La page Success définit MAX_POLL_ATTEMPTS (limite du polling)."""
        self.assertIn("MAX_POLL_ATTEMPTS", self.src,
                      "La page doit définir MAX_POLL_ATTEMPTS")

    # WP4B1-18 ────────────────────────────────────────────────────────────────
    def test_wp4b1_18_success_page_timeout_shows_finflate_email(self):
        """La page timeout affiche info@finflate.com pour le support."""
        self.assertIn("info@finflate.com", self.src,
                      "La page timeout doit afficher info@finflate.com")

    # WP4B1-19 ────────────────────────────────────────────────────────────────
    def test_wp4b1_19_success_page_skips_polling_for_addons(self):
        """La page Success ne polle pas pour les addons (isAddon check présent)."""
        self.assertIn("isAddon", self.src,
                      "La page doit contenir la variable isAddon")
        # Le polling est conditionné par if (isAddon) return
        self.assertIn("if (isAddon) return", self.src,
                      "Le polling doit être court-circuité pour les addons")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
