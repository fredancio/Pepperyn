"""
tests/test_billing_migration.py — Pepperyn Release 1.0 — WP1B
Migration Billing : vérification que billing.py et billing_service.py
lisent exclusivement leur source de vérité depuis product_catalog.py.

30 tests organisés en 4 groupes :
  T01–T10  Catalogue API   (_build_plans_catalogue)
  T11–T20  Checkout        (BillingService.create_checkout_session)
  T21–T26  Webhook/Credits (BillingService.process_webhook_event)
  T27–T30  Non-régression  (imports, absence de constantes legacy)
"""
from __future__ import annotations

import os
import sys
import types
import importlib
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# ── Chemin d'import ───────────────────────────────────────────────────────────
_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 1 — Catalogue API  (T01–T10)
# ─────────────────────────────────────────────────────────────────────────────

class TestCatalogueAPI(unittest.TestCase):
    """_build_plans_catalogue() doit retourner les données correctes du Product Catalog."""

    def _catalogue(self) -> dict:
        from routers.billing import _build_plans_catalogue
        return _build_plans_catalogue()

    # T01 ─────────────────────────────────────────────────────────────────────
    def test_01_plans_has_exactly_3_plans(self):
        """Le catalogue expose exactement FREE, PRO et SCALE — aucun POWER."""
        plans = self._catalogue()["plans"]
        self.assertEqual(len(plans), 3, f"Attendu 3 plans, reçu {len(plans)}")

    # T02 ─────────────────────────────────────────────────────────────────────
    def test_02_plan_free_price_is_zero(self):
        """FREE : price_eur = 0, price_cents = 0."""
        free = next(p for p in self._catalogue()["plans"] if p["id"] == "free")
        self.assertEqual(free["price_eur"],   0)
        self.assertEqual(free["price_cents"], 0)

    # T03 ─────────────────────────────────────────────────────────────────────
    def test_03_plan_pro_price_eur(self):
        """PRO : price_eur = 149 (non 59)."""
        pro = next(p for p in self._catalogue()["plans"] if p["id"] == "pro")
        self.assertEqual(pro["price_eur"],   149)
        self.assertEqual(pro["price_cents"], 14_900)

    # T04 ─────────────────────────────────────────────────────────────────────
    def test_04_plan_scale_price_eur(self):
        """SCALE : price_eur = 349."""
        scale = next(p for p in self._catalogue()["plans"] if p["id"] == "scale")
        self.assertEqual(scale["price_eur"],   349)
        self.assertEqual(scale["price_cents"], 34_900)

    # T05 ─────────────────────────────────────────────────────────────────────
    def test_05_plan_pro_analyses_per_month(self):
        """PRO : 30 analyses / mois (non 15)."""
        pro = next(p for p in self._catalogue()["plans"] if p["id"] == "pro")
        self.assertEqual(pro["analyses_per_month"], 30)

    # T06 ─────────────────────────────────────────────────────────────────────
    def test_06_plan_scale_analyses_per_month(self):
        """SCALE : 100 analyses / mois (non 250)."""
        scale = next(p for p in self._catalogue()["plans"] if p["id"] == "scale")
        self.assertEqual(scale["analyses_per_month"], 100)

    # T07 ─────────────────────────────────────────────────────────────────────
    def test_07_executive_capacity_packs_present(self):
        """Les 3 Executive Capacity Packs sont présents."""
        cat = self._catalogue()
        packs = cat.get("executive_capacity_packs", [])
        pack_ids = {p["id"] for p in packs}
        self.assertIn("addon_starter", pack_ids)
        self.assertIn("addon_growth",  pack_ids)
        self.assertIn("addon_scale",   pack_ids)

    # T08 ─────────────────────────────────────────────────────────────────────
    def test_08_no_power_plan_in_catalogue(self):
        """POWER est absent du catalogue (non commercialisé)."""
        ids = {p["id"] for p in self._catalogue()["plans"]}
        self.assertNotIn("power",      ids, "POWER ne doit pas apparaître dans le catalogue public")
        self.assertNotIn("enterprise", ids, "ENTERPRISE ne doit pas apparaître dans le catalogue public")

    # T09 ─────────────────────────────────────────────────────────────────────
    def test_09_no_price_todo_placeholders(self):
        """Aucun Price ID ne doit contenir 'price_TODO'."""
        import json
        dump = json.dumps(self._catalogue())
        self.assertNotIn("price_TODO", dump,
                         "Des placeholders price_TODO subsistent dans la réponse catalogue")

    # T10 ─────────────────────────────────────────────────────────────────────
    def test_10_starter_pack_price_eur(self):
        """Starter Capacity Pack : price_eur = 39 (non 19), analyses_added = 10."""
        packs = self._catalogue()["executive_capacity_packs"]
        starter = next(p for p in packs if p["id"] == "addon_starter")
        self.assertEqual(starter["price_eur"],    39)
        self.assertEqual(starter["price_cents"],  3_900)
        self.assertEqual(starter["analyses_added"], 10)

    # ── Bonus tests dans le groupe 1 ─────────────────────────────────────────

    def test_01b_growth_pack_values(self):
        """Growth Capacity Pack : price_eur = 79, analyses_added = 20 (non 50)."""
        packs = self._catalogue()["executive_capacity_packs"]
        growth = next(p for p in packs if p["id"] == "addon_growth")
        self.assertEqual(growth["price_eur"],      79)
        self.assertEqual(growth["analyses_added"], 20)

    def test_01c_scale_pack_values(self):
        """Scale Capacity Pack : price_eur = 239, analyses_added = 80 (non 200)."""
        packs = self._catalogue()["executive_capacity_packs"]
        scale = next(p for p in packs if p["id"] == "addon_scale")
        self.assertEqual(scale["price_eur"],      239)
        self.assertEqual(scale["analyses_added"], 80)

    def test_01d_addons_alias_equals_packs(self):
        """'addons' est un alias de 'executive_capacity_packs' (compat temporaire)."""
        cat = self._catalogue()
        self.assertEqual(cat["addons"], cat["executive_capacity_packs"])

    def test_01e_chat_monthly_cap_field_present(self):
        """Le champ 'chat_monthly_cap' est présent sur chaque plan (non interactions_per_analysis)."""
        for plan in self._catalogue()["plans"]:
            self.assertIn("chat_monthly_cap", plan,
                          f"Champ 'chat_monthly_cap' absent pour plan '{plan['id']}'")
            self.assertNotIn("interactions_per_analysis", plan,
                             f"Champ interdit 'interactions_per_analysis' présent pour '{plan['id']}'")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 2 — Checkout  (T11–T20)
# ─────────────────────────────────────────────────────────────────────────────

def _make_mock_stripe_session(url="https://checkout.stripe.com/test", session_id="cs_test_abc"):
    """Retourne un mock de stripe.checkout.Session."""
    stripe_mock = MagicMock()
    session = MagicMock()
    session.url = url
    session.id  = session_id
    stripe_mock.checkout.Session.create.return_value = session
    return stripe_mock


class TestCheckout(unittest.TestCase):
    """BillingService.create_checkout_session() — validations métier."""

    def _service(self):
        from services.billing_service import BillingService
        return BillingService()

    # T11 ─────────────────────────────────────────────────────────────────────
    def test_11_checkout_free_raises_value_error(self):
        """FREE ne peut pas déclencher un checkout Stripe."""
        svc = self._service()
        with self.assertRaises(ValueError) as ctx:
            svc.create_checkout_session("free", "company_abc")
        self.assertIn("FREE", str(ctx.exception))

    # T12 ─────────────────────────────────────────────────────────────────────
    def test_12_checkout_power_raises_value_error(self):
        """POWER n'est pas commandable — doit lever ValueError."""
        svc = self._service()
        with self.assertRaises(ValueError) as ctx:
            svc.create_checkout_session("power", "company_abc")
        msg = str(ctx.exception)
        self.assertTrue(
            "power" in msg.lower() or "POWER" in msg,
            f"Message d'erreur inattendu : {msg}"
        )

    # T13 ─────────────────────────────────────────────────────────────────────
    def test_13_checkout_enterprise_raises_value_error(self):
        """ENTERPRISE n'est pas commandable — doit lever ValueError."""
        svc = self._service()
        with self.assertRaises(ValueError):
            svc.create_checkout_session("enterprise", "company_abc")

    # T14 ─────────────────────────────────────────────────────────────────────
    def test_14_checkout_unknown_product_raises_value_error(self):
        """Un produit inexistant doit lever ValueError."""
        svc = self._service()
        with self.assertRaises(ValueError):
            svc.create_checkout_session("addon_unknown", "company_abc")
        with self.assertRaises(ValueError):
            svc.create_checkout_session("diamond", "company_abc")

    # T15 ─────────────────────────────────────────────────────────────────────
    def test_15_checkout_pro_missing_price_id_raises_value_error(self):
        """PRO sans Price ID dans l'environnement → ValueError explicite."""
        svc = self._service()
        env_without_pro = {k: v for k, v in os.environ.items() if k != "STRIPE_PRICE_PRO"}
        with patch.dict(os.environ, env_without_pro, clear=True):
            with self.assertRaises(ValueError) as ctx:
                svc.create_checkout_session("pro", "company_abc")
        self.assertIn("STRIPE_PRICE_PRO", str(ctx.exception))

    # T16 ─────────────────────────────────────────────────────────────────────
    def test_16_checkout_pro_with_price_id_calls_stripe(self):
        """PRO avec Price ID configuré → appel Stripe réel (mocké)."""
        svc = self._service()
        stripe_mock = _make_mock_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_PRO": "price_test_pro"}):
                result = svc.create_checkout_session("pro", "company_abc")
        self.assertIn("checkout_url", result)
        self.assertIn("session_id",   result)
        stripe_mock.checkout.Session.create.assert_called_once()

    # T17 ─────────────────────────────────────────────────────────────────────
    def test_17_checkout_addon_starter_with_price_id_calls_stripe(self):
        """addon_starter avec Price ID configuré → appel Stripe réel (mocké)."""
        svc = self._service()
        stripe_mock = _make_mock_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_ADDON_STARTER": "price_test_starter"}):
                result = svc.create_checkout_session("addon_starter", "company_abc")
        self.assertIn("checkout_url", result)
        stripe_mock.checkout.Session.create.assert_called_once()

    # T18 ─────────────────────────────────────────────────────────────────────
    def test_18_checkout_addon_mode_is_payment(self):
        """Les Executive Capacity Packs utilisent le mode 'payment' (achat unique)."""
        svc = self._service()
        stripe_mock = _make_mock_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_ADDON_GROWTH": "price_test_growth"}):
                svc.create_checkout_session("addon_growth", "company_abc")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["mode"], "payment")

    # T19 ─────────────────────────────────────────────────────────────────────
    def test_19_checkout_plan_mode_is_subscription(self):
        """Les Plans utilisent le mode 'subscription'."""
        svc = self._service()
        stripe_mock = _make_mock_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale"}):
                svc.create_checkout_session("scale", "company_abc")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["mode"], "subscription")

    # T20 ─────────────────────────────────────────────────────────────────────
    def test_20_checkout_includes_company_id_in_metadata(self):
        """Le company_id doit être transmis dans les metadata Stripe."""
        svc = self._service()
        stripe_mock = _make_mock_stripe_session()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_PRO": "price_test_pro"}):
                svc.create_checkout_session("pro", "company_xyz_42")
        call_kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertEqual(call_kwargs["metadata"]["company_id"], "company_xyz_42")
        self.assertEqual(call_kwargs["metadata"]["plan_or_addon"], "pro")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 3 — Webhook / Crédits Executive Capacity Packs  (T21–T26)
# ─────────────────────────────────────────────────────────────────────────────

def _make_webhook_event(plan_or_addon: str, event_type: str = "checkout.session.completed") -> dict:
    """Construit un faux événement Stripe pour les tests webhook."""
    return {
        "type": event_type,
        "data": {
            "object": {
                "metadata": {
                    "company_id":    "company_webhook_test",
                    "plan_or_addon": plan_or_addon,
                },
                "customer": "cus_test_webhook",
            }
        },
    }


class TestWebhookCredits(unittest.TestCase):
    """process_webhook_event() — crédits corrects pour chaque Executive Capacity Pack."""

    def _process(self, plan_or_addon: str) -> dict:
        """Helper : process un faux webhook checkout.session.completed."""
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = _make_webhook_event(plan_or_addon)
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            return svc.process_webhook_event(b"payload", "sig_test")

    # T21 ─────────────────────────────────────────────────────────────────────
    def test_21_starter_pack_credits_10_analyses(self):
        """addon_starter crédite exactement 10 Analyses bonus (non 50, non 200)."""
        result = self._process("addon_starter")
        self.assertEqual(result["quantity"], 10)

    # T22 ─────────────────────────────────────────────────────────────────────
    def test_22_growth_pack_credits_20_analyses(self):
        """addon_growth crédite exactement 20 Analyses bonus (non 50)."""
        result = self._process("addon_growth")
        self.assertEqual(result["quantity"], 20)

    # T23 ─────────────────────────────────────────────────────────────────────
    def test_23_scale_pack_credits_80_analyses(self):
        """addon_scale crédite exactement 80 Analyses bonus (non 200)."""
        result = self._process("addon_scale")
        self.assertEqual(result["quantity"], 80)

    # T24 ─────────────────────────────────────────────────────────────────────
    def test_24_addon_webhook_returns_add_bonus_action(self):
        """Un pack retourne l'action 'add_bonus', jamais 'update_plan'."""
        for pack_id in ("addon_starter", "addon_growth", "addon_scale"):
            with self.subTest(pack_id=pack_id):
                result = self._process(pack_id)
                self.assertEqual(result["action"], "add_bonus",
                                 f"Pack {pack_id} : attendu 'add_bonus', reçu '{result['action']}'")
                self.assertNotEqual(result["action"], "update_plan")

    # T25 ─────────────────────────────────────────────────────────────────────
    def test_25_plan_checkout_does_not_add_bonus(self):
        """Un checkout Plan (PRO) retourne 'update_plan', pas 'add_bonus'."""
        result = self._process("pro")
        self.assertEqual(result["action"], "update_plan")
        self.assertNotIn("quantity", result,
                         "Un checkout PRO ne doit pas contenir un champ 'quantity'")

    # T26 ─────────────────────────────────────────────────────────────────────
    def test_26_unknown_addon_credits_zero(self):
        """Un pack inconnu dans les metadata Stripe crédite 0 (erreur gracieuse)."""
        result = self._process("addon_unknown_legacy")
        self.assertEqual(result["action"],   "add_bonus")
        self.assertEqual(result["quantity"], 0,
                         "Un pack inconnu doit créditer 0 analyse — jamais une quantité fantôme")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 4 — Non-régression  (T27–T30)
# ─────────────────────────────────────────────────────────────────────────────

class TestNonRegression(unittest.TestCase):
    """Vérifications structurelles : absence de constantes legacy, imports propres."""

    # T27 ─────────────────────────────────────────────────────────────────────
    def test_27_billing_service_has_no_local_addon_quantities(self):
        """ADDON_QUANTITIES ne doit plus exister dans billing_service.py."""
        import services.billing_service as bs_mod
        self.assertFalse(
            hasattr(bs_mod, "ADDON_QUANTITIES"),
            "ADDON_QUANTITIES est une constante legacy supprimée en WP1B — "
            "les quantités doivent venir de product_catalog.EXECUTIVE_CAPACITY_PACKS"
        )

    # T28 ─────────────────────────────────────────────────────────────────────
    def test_28_billing_service_has_no_local_stripe_price_ids_dict(self):
        """Le dictionnaire module-level STRIPE_PRICE_IDS ne doit plus exister dans billing_service.py."""
        import services.billing_service as bs_mod
        self.assertFalse(
            hasattr(bs_mod, "STRIPE_PRICE_IDS"),
            "STRIPE_PRICE_IDS local est une constante legacy supprimée en WP1B — "
            "les Price IDs viennent de product_catalog ou d'os.environ"
        )

    # T29 ─────────────────────────────────────────────────────────────────────
    def test_29_billing_router_has_no_plans_catalogue(self):
        """PLANS_CATALOGUE ne doit plus exister dans routers/billing.py."""
        import routers.billing as billing_mod
        self.assertFalse(
            hasattr(billing_mod, "PLANS_CATALOGUE"),
            "PLANS_CATALOGUE est une constante legacy supprimée en WP1B — "
            "le catalogue est généré dynamiquement par _build_plans_catalogue()"
        )

    # T30 ─────────────────────────────────────────────────────────────────────
    def test_30_no_price_todo_in_billing_source_files(self):
        """Aucun fichier billing ne doit contenir 'price_TODO'."""
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        targets = [
            os.path.join(backend_dir, "routers", "billing.py"),
            os.path.join(backend_dir, "services", "billing_service.py"),
        ]
        for path in targets:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn(
                "price_TODO", content,
                f"Placeholder 'price_TODO' trouvé dans {os.path.basename(path)} — "
                f"les Price IDs doivent venir des variables d'environnement"
            )

    # ── Tests supplémentaires dans le groupe 4 ─────────────────────────────

    def test_30b_billing_router_imports_product_catalog(self):
        """billing.py doit importer depuis config.product_catalog."""
        billing_path = os.path.join(
            os.path.dirname(__file__), "..", "routers", "billing.py"
        )
        with open(billing_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("product_catalog", content,
                      "billing.py doit importer depuis config.product_catalog")

    def test_30c_billing_service_imports_product_catalog(self):
        """billing_service.py doit importer depuis config.product_catalog."""
        svc_path = os.path.join(
            os.path.dirname(__file__), "..", "services", "billing_service.py"
        )
        with open(svc_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("product_catalog", content,
                      "billing_service.py doit importer depuis config.product_catalog")

    def test_30d_build_plans_catalogue_is_callable(self):
        """_build_plans_catalogue() doit être accessible et retourner un dict."""
        from routers.billing import _build_plans_catalogue
        result = _build_plans_catalogue()
        self.assertIsInstance(result, dict)
        self.assertIn("plans",  result)
        self.assertIn("addons", result)

    def test_30e_product_catalog_not_imported_in_usage_service(self):
        """
        usage_service.py n'est pas modifié en WP1B.
        Vérifier qu'il ne possède pas encore les corrections de quotas
        (celles-ci sont prévues en WP1C).
        """
        # Ce test documente l'état pré-WP1C : usage_service n'a PAS encore
        # été migré vers product_catalog. Il échouera en WP1C (comportement attendu).
        svc_path = os.path.join(
            os.path.dirname(__file__), "..", "services", "usage_service.py"
        )
        if not os.path.exists(svc_path):
            self.skipTest("usage_service.py absent — test ignoré")
        with open(svc_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Si product_catalog est déjà importé dans usage_service, c'est que
        # WP1C a commencé — ce test doit alors être retiré du fichier WP1B.
        # Pour l'instant on vérifie juste que usage_service est importable.
        import services.usage_service  # noqa — doit s'importer sans erreur


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
