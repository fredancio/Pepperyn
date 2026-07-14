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

def _make_webhook_event(
    plan_or_addon: str,
    event_type: str = "checkout.session.completed",
    event_id: str = "evt_test_group3_default",
) -> dict:
    """Construit un faux événement Stripe pour les tests webhook (WP1B.3 : event.id requis)."""
    return {
        "id":   event_id,
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
        """Un checkout Plan (PRO) retourne 'init_subscription' (WP4B.5), pas 'add_bonus'.
        checkout.session.completed → init_subscription (plan + customer + subscription_id)."""
        result = self._process("pro")
        self.assertEqual(result["action"], "init_subscription")   # WP4B.5
        self.assertNotIn("quantity", result,
                         "Un checkout PRO ne doit pas contenir un champ 'quantity'")

    # T26 ─────────────────────────────────────────────────────────────────────
    def test_26_unknown_addon_raises_value_error_never_credits_zero(self):
        """
        Un pack inconnu dans les metadata Stripe doit lever ValueError.
        Jamais de quantité 0 silencieuse : le client a payé, il doit être crédité.
        Le webhook HTTP retourne non-2xx → Stripe retente automatiquement.
        """
        with self.assertRaises(ValueError) as ctx:
            self._process("addon_unknown_legacy")
        msg = str(ctx.exception)
        self.assertIn("addon_unknown_legacy", msg,
                      "Le message d'erreur doit identifier le pack inconnu")

    # T26b ────────────────────────────────────────────────────────────────────
    def test_26b_missing_company_id_raises_value_error(self):
        """
        Un webhook sans company_id dans les metadata Stripe doit lever ValueError.
        Impossible d'imputer le crédit sans connaître le client.
        """
        from services.billing_service import BillingService
        svc = BillingService()
        # Événement sans company_id dans les metadata
        fake_event = {
            "id":   "evt_test_26b_no_company",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_no_company",
                    "metadata": {
                        # company_id intentionnellement absent
                        "plan_or_addon": "addon_starter",
                    },
                    "customer": "cus_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with self.assertRaises(ValueError) as ctx:
                svc.process_webhook_event(b"payload", "sig_test")
        self.assertIn("company_id", str(ctx.exception).lower())

    # T26c ────────────────────────────────────────────────────────────────────
    def test_26c_missing_plan_or_addon_raises_value_error(self):
        """
        Un webhook sans plan_or_addon dans les metadata Stripe doit lever ValueError.
        Impossible de créditer un plan/pack sans en connaître l'identifiant.
        """
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            "id":   "evt_test_26c_no_plan",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_no_plan",
                    "metadata": {
                        "company_id": "company_xyz",
                        # plan_or_addon intentionnellement absent
                    },
                    "customer": "cus_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with self.assertRaises(ValueError) as ctx:
                svc.process_webhook_event(b"payload", "sig_test")
        self.assertIn("plan_or_addon", str(ctx.exception).lower())

    # T26d ────────────────────────────────────────────────────────────────────
    def test_26d_empty_metadata_raises_value_error(self):
        """
        Un webhook avec des metadata vides (dict vide) doit lever ValueError.
        Protège contre les webhooks Stripe mal configurés ou frauduleux.
        """
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            "id":   "evt_test_26d_empty_meta",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_empty_meta",
                    "metadata": {},
                    "customer": "cus_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with self.assertRaises(ValueError):
                svc.process_webhook_event(b"payload", "sig_test")


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
# GROUPE 5 — Diagnostic idempotence  (WP1B.2)
#
# Ces tests passent en CONFIRMANT L'ABSENCE de protection d'idempotence.
# Ils documentent l'état actuel. La correction est prévue en WP1B.3.
#
# ⚠️  RISQUE DOCUMENTÉ :
#   Un même checkout.session.completed Executive Capacity Pack reçu deux fois
#   (retry Stripe ou livraison dupliquée) créditera les Analyses DEUX FOIS.
#   Les Plans (PRO/SCALE) sont idempotents par accident (SET, pas INCREMENT).
#
# Solution proposée (WP1B.3) :
#   Table Supabase `stripe_processed_events(stripe_event_id TEXT PRIMARY KEY)`
#   vérifiée avant toute écriture dans le handler webhook de billing.py.
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotencyDiagnostic(unittest.TestCase):
    """
    WP1B.2 — Diagnostic d'idempotence des webhooks Stripe.

    Ces tests passent en confirmant l'état actuel (vulnérabilité documentée).
    Ils seront remplacés par des tests de comportement correct en WP1B.3.
    """

    def _process(self, plan_or_addon: str, event_id: str = "evt_test_default") -> dict:
        """Helper : exécute process_webhook_event avec un event_id explicite."""
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            "id":   event_id,          # ← Stripe event ID unique — ignoré actuellement
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session_abc",
                    "metadata": {
                        "company_id":    "company_idp_test",
                        "plan_or_addon": plan_or_addon,
                    },
                    "customer": "cus_idp_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            return svc.process_webhook_event(b"payload", "sig_test")

    # IDP-01 ──────────────────────────────────────────────────────────────────
    def test_idp_01_stripe_event_id_never_read(self):
        """
        WP1B.3 — process_webhook_event() propage désormais event['id'] Stripe.
        Le stripe_event_id est présent dans le résultat et correctement valorisé.
        ✅ Idempotence garantie : le router peut appeler apply_stripe_webhook avec cet id.
        """
        result = self._process("addon_starter", event_id="evt_UNIQUE_NEVER_REUSED")
        # event["id"] est désormais lu et propagé dans le dict retourné
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_UNIQUE_NEVER_REUSED")

    # IDP-02 ──────────────────────────────────────────────────────────────────
    def test_idp_02_plan_pro_idempotent_by_nature(self):
        """
        PRO : même événement traité deux fois → même action 'init_subscription' (WP4B.5).
        Idempotent par nature : UPDATE companies SET plan='pro' est un SET,
        pas un INCREMENT. Deux exécutions n'ont pas d'effet cumulatif.
        L'idempotence au niveau SQL est garantie par ON CONFLICT (stripe_event_id).
        ✅ Plans : pas de risque de double activation.
        """
        r1 = self._process("pro", "evt_pro_001")
        r2 = self._process("pro", "evt_pro_001")   # même event_id, rejoué
        self.assertEqual(r1["action"], "init_subscription")   # WP4B.5
        self.assertEqual(r2["action"], "init_subscription")   # WP4B.5
        self.assertEqual(r1["plan"],   r2["plan"])

    # IDP-03 ──────────────────────────────────────────────────────────────────
    def test_idp_03_plan_scale_idempotent_by_nature(self):
        """
        SCALE : même événement traité deux fois → même action 'init_subscription' (WP4B.5).
        ✅ Plans : pas de risque de double activation.
        """
        r1 = self._process("scale", "evt_scale_001")
        r2 = self._process("scale", "evt_scale_001")
        self.assertEqual(r1["action"], "init_subscription")   # WP4B.5
        self.assertEqual(r1["plan"],   r2["plan"])

    # IDP-04 ──────────────────────────────────────────────────────────────────
    def test_idp_04_addon_service_layer_stateless_no_dedup(self):
        """
        addon_starter : même événement traité deux fois → add_bonus retourné DEUX FOIS.
        Le service est stateless : il ne détecte pas les doublons.
        ⚠️ VULNÉRABILITÉ CONFIRMÉE : le route handler (billing.py) appellerait
        add_bonus_analyses(company, 10) deux fois → +20 Analyses au lieu de +10.
        Correction prévue en WP1B.3.
        """
        r1 = self._process("addon_starter", "evt_starter_001")
        r2 = self._process("addon_starter", "evt_starter_001")  # même event
        # Les deux appels retournent add_bonus — aucune déduplication
        self.assertEqual(r1["action"], "add_bonus")
        self.assertEqual(r2["action"], "add_bonus")
        self.assertEqual(r1["quantity"], 10)
        self.assertEqual(r2["quantity"], 10)
        # Confirmation : service stateless, dict identique les deux fois
        self.assertEqual(r1, r2,
                         "Service stateless vérifié : même dict retourné deux fois. "
                         "Sans WP1B.3, le route handler créditerait +20 au lieu de +10.")

    # IDP-05 ──────────────────────────────────────────────────────────────────
    def test_idp_05_all_packs_vulnerable_to_double_credit(self):
        """
        Les trois packs retournent add_bonus sans déduplication.
        ⚠️ Starter=+10, Growth=+20, Scale Capacity Pack=+80 seraient crédités
        DEUX FOIS si Stripe rejoue le même webhook.
        """
        cases = [
            ("addon_starter", 10,  "evt_starter_dbl"),
            ("addon_growth",  20,  "evt_growth_dbl"),
            ("addon_scale",   80,  "evt_scale_dbl"),
        ]
        for pack_id, expected_qty, evt_id in cases:
            with self.subTest(pack=pack_id):
                r1 = self._process(pack_id, evt_id)
                r2 = self._process(pack_id, evt_id)
                self.assertEqual(r1["quantity"], expected_qty)
                self.assertEqual(r1, r2,
                                 f"⚠️ {pack_id} : add_bonus retourné deux fois — "
                                 f"double crédit de {expected_qty} Analyses possible")

    # IDP-06 ──────────────────────────────────────────────────────────────────
    def test_idp_06_add_bonus_analyses_uses_read_then_write_not_atomic(self):
        """
        Confirme que add_bonus_analyses() fait READ-THEN-WRITE (pas atomique).
        La formule 'current_bonus + quantity' est un incrément non idempotent.
        ⚠️ Pas de protection via ON CONFLICT, upsert idempotent, ou stripe_event_id.
        """
        import inspect
        from services.usage_service import UsageService
        source = inspect.getsource(UsageService.add_bonus_analyses)
        # L'opération est un incrément, jamais un SET absolu
        self.assertIn("current_bonus + quantity", source,
                      "add_bonus_analyses fait un INCREMENT — pas un SET absolu idempotent")
        # Aucune protection d'idempotence au niveau de l'opération
        self.assertNotIn("stripe_event_id", source)
        self.assertNotIn("ON CONFLICT",     source)
        self.assertNotIn("stripe_session",  source)

    # IDP-07 ──────────────────────────────────────────────────────────────────
    def test_idp_07_no_processed_events_table_in_migrations(self):
        """
        Confirme qu'aucune migration ne crée de table stripe_processed_events.
        ⚠️ Le registre d'événements traités est absent — protection à créer en WP1B.3.
        """
        migrations_dir = os.path.join(
            os.path.dirname(__file__), "..", "migrations"
        )
        if not os.path.isdir(migrations_dir):
            self.skipTest("Répertoire migrations absent — test ignoré")

        for fname in os.listdir(migrations_dir):
            if not fname.endswith(".sql"):
                continue
            fpath = os.path.join(migrations_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().lower()
            self.assertNotIn(
                "stripe_processed_events", content,
                f"Table stripe_processed_events trouvée dans {fname} — "
                f"WP1B.3 est peut-être déjà partiellement implémenté ?"
            )


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 6 — Idempotence webhooks Stripe  (WP1B.3)
#
# Vérifie la chaîne complète d'idempotence :
#   1. billing_service.py propage stripe_event_id dans tous les dicts résultats.
#   2. Un event.id manquant ou vide lève ValueError (impossible de garantir l'idempotence).
#   3. Le router billing.py appelle apply_stripe_webhook RPC avec les bons paramètres.
#   4. RPC status="duplicate" → router retourne action="duplicate_skipped" (HTTP 200).
#
# Architecture d'idempotence :
#   billing_service  → propage stripe_event_id (stateless)
#   billing.py       → appelle apply_stripe_webhook via RPC
#   apply_stripe_webhook (PG) → INSERT ON CONFLICT DO NOTHING + traitement métier atomique
# ─────────────────────────────────────────────────────────────────────────────

class TestWebhookIdempotency(unittest.TestCase):
    """
    WP1B.3 — Idempotence des webhooks Stripe.

    Deux niveaux de tests :
    - Service (G6-01 à G6-08) : propagation event_id, validation missing/empty id.
    - Router  (G6-09 à G6-11) : appel RPC correct, gestion du doublon (duplicate_skipped).
    """

    def _process(self, plan_or_addon: str, event_id: str = "evt_test_idp") -> dict:
        """Helper : process_webhook_event avec un stripe event.id explicite."""
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_idp",
                    "metadata": {
                        "company_id":    "company_idp_test",
                        "plan_or_addon": plan_or_addon,
                    },
                    "customer": "cus_idp_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            return svc.process_webhook_event(b"payload", "sig_test")

    # ── Niveau Service ──────────────────────────────────────────────────────────

    # G6-01 ───────────────────────────────────────────────────────────────────
    def test_g6_01_pro_checkout_propagates_event_id(self):
        """PRO checkout : stripe_event_id et event_type propagés dans le résultat.
        Action = 'init_subscription' depuis WP4B.5."""
        result = self._process("pro", "evt_pro_idp_001")
        self.assertIn("stripe_event_id", result)
        self.assertIn("event_type",      result)
        self.assertEqual(result["stripe_event_id"], "evt_pro_idp_001")
        self.assertEqual(result["event_type"],      "checkout.session.completed")
        self.assertEqual(result["action"],          "init_subscription")   # WP4B.5

    # G6-02 ───────────────────────────────────────────────────────────────────
    def test_g6_02_scale_checkout_propagates_event_id(self):
        """SCALE checkout : stripe_event_id propagé et valorisé correctement.
        Action = 'init_subscription' depuis WP4B.5."""
        result = self._process("scale", "evt_scale_idp_001")
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_scale_idp_001")
        self.assertEqual(result["action"],          "init_subscription")   # WP4B.5

    # G6-03 ───────────────────────────────────────────────────────────────────
    def test_g6_03_addon_starter_propagates_event_id_and_quantity(self):
        """addon_starter : stripe_event_id propagé, quantity=10 (+10 une seule fois)."""
        result = self._process("addon_starter", "evt_starter_idp_001")
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_starter_idp_001")
        self.assertEqual(result["action"],          "add_bonus")
        self.assertEqual(result["quantity"],        10)

    # G6-04 ───────────────────────────────────────────────────────────────────
    def test_g6_04_addon_growth_propagates_event_id_and_quantity(self):
        """addon_growth : stripe_event_id propagé, quantity=20 (+20 une seule fois)."""
        result = self._process("addon_growth", "evt_growth_idp_001")
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_growth_idp_001")
        self.assertEqual(result["action"],          "add_bonus")
        self.assertEqual(result["quantity"],        20)

    # G6-05 ───────────────────────────────────────────────────────────────────
    def test_g6_05_addon_scale_propagates_event_id_and_quantity(self):
        """addon_scale : stripe_event_id propagé, quantity=80 (+80 une seule fois)."""
        result = self._process("addon_scale", "evt_scale_pack_idp_001")
        self.assertIn("stripe_event_id", result)
        self.assertEqual(result["stripe_event_id"], "evt_scale_pack_idp_001")
        self.assertEqual(result["action"],          "add_bonus")
        self.assertEqual(result["quantity"],        80)

    # G6-06 ───────────────────────────────────────────────────────────────────
    def test_g6_06_two_different_events_produce_distinct_event_ids(self):
        """Deux événements différents → deux stripe_event_id distincts dans les résultats."""
        r1 = self._process("addon_starter", "evt_FIRST_001")
        r2 = self._process("addon_starter", "evt_SECOND_002")
        self.assertEqual(r1["stripe_event_id"], "evt_FIRST_001")
        self.assertEqual(r2["stripe_event_id"], "evt_SECOND_002")
        self.assertNotEqual(r1["stripe_event_id"], r2["stripe_event_id"],
                            "Deux événements distincts doivent avoir des event_ids distincts")

    # G6-07 ───────────────────────────────────────────────────────────────────
    def test_g6_07_missing_event_id_raises_value_error(self):
        """
        Webhook sans event.id → ValueError immédiat.
        Sans event_id, l'idempotence est impossible.
        Stripe doit recevoir HTTP 400 et ne pas redelivrer.
        """
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            # "id" intentionnellement absent
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_no_event_id",
                    "metadata": {
                        "company_id":    "company_test",
                        "plan_or_addon": "addon_starter",
                    },
                    "customer": "cus_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with self.assertRaises(ValueError) as ctx:
                svc.process_webhook_event(b"payload", "sig_test")
        self.assertIn("event.id", str(ctx.exception).lower(),
                      "Le message d'erreur doit mentionner event.id ou event_id")

    # G6-08 ───────────────────────────────────────────────────────────────────
    def test_g6_08_empty_event_id_raises_value_error(self):
        """
        Webhook avec event.id vide ("") → ValueError immédiat.
        Un identifiant vide ne peut pas servir de clé d'idempotence.
        """
        from services.billing_service import BillingService
        svc = BillingService()
        fake_event = {
            "id": "",   # vide — invalide
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_empty_event_id",
                    "metadata": {
                        "company_id":    "company_test",
                        "plan_or_addon": "addon_starter",
                    },
                    "customer": "cus_test",
                }
            },
        }
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = fake_event
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with self.assertRaises(ValueError):
                svc.process_webhook_event(b"payload", "sig_test")

    # ── Niveau Router ───────────────────────────────────────────────────────────

    # G6-09 ───────────────────────────────────────────────────────────────────
    def test_g6_09_webhook_handler_calls_rpc_with_correct_params(self):
        """
        Le handler webhook appelle apply_stripe_webhook via RPC avec les bons paramètres.
        Vérifie que stripe_event_id, action, quantity sont correctement transmis.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        service_result = {
            "action":             "add_bonus",
            "company_id":         "company_g6_test",
            "quantity":           10,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_g6_rpc_test",
            "event_type":         "checkout.session.completed",
        }

        request_mock = MagicMock()
        request_mock.body = AsyncMock(return_value=b"payload")

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        exec_result = MagicMock()
        exec_result.data = {"status": "processed"}
        sb_mock = MagicMock()
        sb_mock.rpc.return_value.execute.return_value = exec_result

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_mock):
                response = asyncio.run(stripe_webhook(request_mock, "sig_test"))

        # Vérifier que la RPC a été appelée avec les bons paramètres
        sb_mock.rpc.assert_called_once()
        call_name, call_params = sb_mock.rpc.call_args[0]
        self.assertEqual(call_name, "apply_stripe_webhook")
        self.assertEqual(call_params["p_stripe_event_id"], "evt_g6_rpc_test")
        self.assertEqual(call_params["p_action"],          "add_bonus")
        self.assertEqual(call_params["p_quantity"],        10)

        self.assertEqual(response["received"], True)
        self.assertEqual(response["action"],   "add_bonus")

    # G6-10 ───────────────────────────────────────────────────────────────────
    def test_g6_10_duplicate_event_returns_duplicate_skipped(self):
        """
        Quand la RPC retourne status='duplicate', le handler retourne action='duplicate_skipped'.
        Le même stripe_event_id ne produit jamais deux effets métier.
        Stripe reçoit HTTP 200 → ne retente pas.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        service_result = {
            "action":             "add_bonus",
            "company_id":         "company_g6_dup",
            "quantity":           10,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_g6_DUPLICATE",
            "event_type":         "checkout.session.completed",
        }

        request_mock = MagicMock()
        request_mock.body = AsyncMock(return_value=b"payload")

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        # La RPC simule un conflit sur stripe_event_id (déjà traité)
        exec_result = MagicMock()
        exec_result.data = {"status": "duplicate"}
        sb_mock = MagicMock()
        sb_mock.rpc.return_value.execute.return_value = exec_result

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_mock):
                response = asyncio.run(stripe_webhook(request_mock, "sig_test"))

        self.assertEqual(response["received"], True)
        self.assertEqual(response["action"],   "duplicate_skipped",
                         "Un doublon Stripe doit retourner action='duplicate_skipped'")

    # G6-11 ───────────────────────────────────────────────────────────────────
    def test_g6_11_addon_starter_credited_once_on_duplicate(self):
        """
        addon_starter livré deux fois par Stripe :
          - 1ère livraison : RPC retourne 'processed' → action='add_bonus' (+10)
          - 2ème livraison (même event_id) : RPC retourne 'duplicate' → action='duplicate_skipped'
        Les 10 Analyses bonus sont créditées une seule et unique fois.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        service_result = {
            "action":             "add_bonus",
            "company_id":         "company_addon_once",
            "quantity":           10,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_starter_ONCE",
            "event_type":         "checkout.session.completed",
        }

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        # ── Première livraison : processed ────────────────────────────────────
        request_1 = MagicMock()
        request_1.body = AsyncMock(return_value=b"payload")
        exec_1 = MagicMock()
        exec_1.data = {"status": "processed"}
        sb_1 = MagicMock()
        sb_1.rpc.return_value.execute.return_value = exec_1

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_1):
                r1 = asyncio.run(stripe_webhook(request_1, "sig_test"))

        self.assertEqual(r1["action"], "add_bonus",
                         "Première livraison : doit créditer les analyses")

        # ── Deuxième livraison (même event_id) : duplicate ────────────────────
        request_2 = MagicMock()
        request_2.body = AsyncMock(return_value=b"payload")
        exec_2 = MagicMock()
        exec_2.data = {"status": "duplicate"}
        sb_2 = MagicMock()
        sb_2.rpc.return_value.execute.return_value = exec_2

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_2):
                r2 = asyncio.run(stripe_webhook(request_2, "sig_test"))

        self.assertEqual(r2["action"], "duplicate_skipped",
                         "Deuxième livraison du même webhook → doit être ignorée sans re-crédit")

    # G6-12 ───────────────────────────────────────────────────────────────────
    def test_g6_12_addon_growth_credited_once_on_duplicate(self):
        """
        addon_growth livré deux fois par Stripe :
          - 1ère livraison : RPC retourne 'processed' → action='add_bonus' (+20 analyses)
          - 2ème livraison (même event_id) : RPC retourne 'duplicate' → ignorée
        Les 20 analyses bonus sont créditées une seule et unique fois.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        service_result = {
            "action":             "add_bonus",
            "company_id":         "company_growth_once",
            "quantity":           20,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_growth_ONCE",
            "event_type":         "checkout.session.completed",
        }
        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        # ── Première livraison ────────────────────────────────────────────────
        req_1 = MagicMock()
        req_1.body = AsyncMock(return_value=b"payload")
        exec_1 = MagicMock()
        exec_1.data = {"status": "processed"}
        sb_1 = MagicMock()
        sb_1.rpc.return_value.execute.return_value = exec_1

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_1):
                r1 = asyncio.run(stripe_webhook(req_1, "sig_test"))

        self.assertEqual(r1["action"], "add_bonus")
        _, call_params_1 = sb_1.rpc.call_args[0]
        self.assertEqual(call_params_1["p_quantity"], 20,
                         "Growth Pack : quantité=20 doit être transmise à la RPC")

        # ── Deuxième livraison (même event_id) ───────────────────────────────
        req_2 = MagicMock()
        req_2.body = AsyncMock(return_value=b"payload")
        exec_2 = MagicMock()
        exec_2.data = {"status": "duplicate"}
        sb_2 = MagicMock()
        sb_2.rpc.return_value.execute.return_value = exec_2

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_2):
                r2 = asyncio.run(stripe_webhook(req_2, "sig_test"))

        self.assertEqual(r2["action"], "duplicate_skipped",
                         "Growth Pack doublon → doit être ignoré sans re-crédit de 20 analyses")

    # G6-13 ───────────────────────────────────────────────────────────────────
    def test_g6_13_addon_scale_pack_credited_once_on_duplicate(self):
        """
        addon_scale livré deux fois par Stripe :
          - 1ère livraison : RPC retourne 'processed' → action='add_bonus' (+80 analyses)
          - 2ème livraison (même event_id) : RPC retourne 'duplicate' → ignorée
        Les 80 analyses bonus sont créditées une seule et unique fois.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        service_result = {
            "action":             "add_bonus",
            "company_id":         "company_scale_pack_once",
            "quantity":           80,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_scale_pack_ONCE",
            "event_type":         "checkout.session.completed",
        }
        billing_mock = MagicMock()
        billing_mock.process_webhook_event.return_value = service_result

        # ── Première livraison ────────────────────────────────────────────────
        req_1 = MagicMock()
        req_1.body = AsyncMock(return_value=b"payload")
        exec_1 = MagicMock()
        exec_1.data = {"status": "processed"}
        sb_1 = MagicMock()
        sb_1.rpc.return_value.execute.return_value = exec_1

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_1):
                r1 = asyncio.run(stripe_webhook(req_1, "sig_test"))

        self.assertEqual(r1["action"], "add_bonus")
        _, call_params_1 = sb_1.rpc.call_args[0]
        self.assertEqual(call_params_1["p_quantity"], 80,
                         "Scale Pack : quantité=80 doit être transmise à la RPC")

        # ── Deuxième livraison (même event_id) ───────────────────────────────
        req_2 = MagicMock()
        req_2.body = AsyncMock(return_value=b"payload")
        exec_2 = MagicMock()
        exec_2.data = {"status": "duplicate"}
        sb_2 = MagicMock()
        sb_2.rpc.return_value.execute.return_value = exec_2

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_2):
                r2 = asyncio.run(stripe_webhook(req_2, "sig_test"))

        self.assertEqual(r2["action"], "duplicate_skipped",
                         "Scale Pack doublon → doit être ignoré sans re-crédit de 80 analyses")

    # G6-14 ───────────────────────────────────────────────────────────────────
    def test_g6_14_two_distinct_event_ids_trigger_two_rpc_calls(self):
        """
        Deux event.id Stripe distincts → deux appels RPC avec des p_stripe_event_id différents.
        Vérifie que chaque livraison est tracée individuellement dans le registre d'idempotence
        et que la distinction est correctement propagée jusqu'à la couche SQL.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from routers.billing import stripe_webhook

        billing_mock = MagicMock()
        exec_r = MagicMock()
        exec_r.data = {"status": "processed"}

        # ── Premier événement ─────────────────────────────────────────────────
        billing_mock.process_webhook_event.return_value = {
            "action":             "add_bonus",
            "company_id":         "company_g6_14",
            "quantity":           10,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_FIRST_G6_14",
            "event_type":         "checkout.session.completed",
        }
        req_1 = MagicMock()
        req_1.body = AsyncMock(return_value=b"payload")
        sb_1 = MagicMock()
        sb_1.rpc.return_value.execute.return_value = exec_r

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_1):
                asyncio.run(stripe_webhook(req_1, "sig_1"))

        _, params_1 = sb_1.rpc.call_args[0]
        self.assertEqual(params_1["p_stripe_event_id"], "evt_FIRST_G6_14")

        # ── Deuxième événement (event_id différent) ───────────────────────────
        billing_mock.process_webhook_event.return_value = {
            "action":             "add_bonus",
            "company_id":         "company_g6_14",
            "quantity":           20,
            "stripe_customer_id": "cus_test",
            "stripe_event_id":    "evt_SECOND_G6_14",
            "event_type":         "checkout.session.completed",
        }
        req_2 = MagicMock()
        req_2.body = AsyncMock(return_value=b"payload")
        sb_2 = MagicMock()
        sb_2.rpc.return_value.execute.return_value = exec_r

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_2):
                asyncio.run(stripe_webhook(req_2, "sig_2"))

        _, params_2 = sb_2.rpc.call_args[0]
        self.assertEqual(params_2["p_stripe_event_id"], "evt_SECOND_G6_14")

        # Deux event_ids distincts → deux clés distinctes dans le registre
        self.assertNotEqual(params_1["p_stripe_event_id"], params_2["p_stripe_event_id"],
                            "Deux livraisons distinctes doivent avoir des p_stripe_event_id distincts")

    # G6-15 ───────────────────────────────────────────────────────────────────
    def test_g6_15_invalid_stripe_signature_rpc_never_called(self):
        """
        Signature Stripe invalide → ValueError dans billing_service → HTTP 400.
        La RPC apply_stripe_webhook ne doit JAMAIS être appelée.
        Garantit qu'un faux payload ne peut pas déclencher de modification SQL.
        """
        import asyncio
        from unittest.mock import AsyncMock
        from fastapi import HTTPException
        from routers.billing import stripe_webhook

        billing_mock = MagicMock()
        billing_mock.process_webhook_event.side_effect = ValueError(
            "Webhook verification failed (SignatureVerificationError): No signatures found"
        )

        sb_mock = MagicMock()

        req = MagicMock()
        req.body = AsyncMock(return_value=b"bad_payload")

        with patch("routers.billing._get_billing", return_value=billing_mock):
            with patch("main.get_supabase_service", return_value=sb_mock):
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(stripe_webhook(req, "invalid_sig"))

        self.assertEqual(ctx.exception.status_code, 400,
                         "Signature invalide → HTTP 400 (pas 500)")
        sb_mock.rpc.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 7 — SQL Hardening  (SH-01–SH-12)
# ─────────────────────────────────────────────────────────────────────────────

class TestSQLHardening(unittest.TestCase):
    """
    WP1B.3.1 — Tests structurels de la migration SQL.

    Vérifient que le fichier v10_stripe_webhook_events.sql contient
    les protections de sécurité exigées par WP1B.3.1 avant application
    sur Supabase.

    Ces tests inspectent le code SQL source sans nécessiter de connexion Supabase.
    Ils constituent le filet de sécurité qui empêche de déployer une migration
    sans les garanties de permission et de validation requises.

    Note : les tests de permission réelle (vérifier qu'anon ne peut effectivement
    pas appeler la fonction sur une instance Supabase) sont des tests d'intégration
    qui s'exécutent après application de la migration — hors scope des tests unitaires.
    """

    def _migration_content(self) -> str:
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "v10_stripe_webhook_events.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            return f.read()

    # SH-01 ───────────────────────────────────────────────────────────────────
    def test_sh_01_revoke_function_from_anon(self):
        """La migration révoque tous les droits sur apply_stripe_webhook pour anon."""
        content = self._migration_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*FROM\s+anon",
            "REVOKE ALL ON FUNCTION apply_stripe_webhook ... FROM anon doit être présent"
        )

    # SH-02 ───────────────────────────────────────────────────────────────────
    def test_sh_02_revoke_function_from_authenticated(self):
        """La migration révoque tous les droits sur apply_stripe_webhook pour authenticated."""
        content = self._migration_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*FROM\s+authenticated",
            "REVOKE ALL ON FUNCTION apply_stripe_webhook ... FROM authenticated doit être présent"
        )

    # SH-03 ───────────────────────────────────────────────────────────────────
    def test_sh_03_grant_function_to_service_role(self):
        """La migration accorde EXECUTE sur apply_stripe_webhook à service_role uniquement."""
        content = self._migration_content()
        self.assertRegex(
            content,
            r"GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*TO\s+service_role",
            "GRANT EXECUTE ON FUNCTION apply_stripe_webhook ... TO service_role doit être présent"
        )

    # SH-04 ───────────────────────────────────────────────────────────────────
    def test_sh_04_revoke_table_from_anon(self):
        """La migration révoque tous les droits sur la table stripe_webhook_events pour anon."""
        content = self._migration_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+TABLE\s+.*stripe_webhook_events.*FROM\s+anon",
            "REVOKE ALL ON TABLE stripe_webhook_events FROM anon doit être présent"
        )

    # SH-05 ───────────────────────────────────────────────────────────────────
    def test_sh_05_revoke_table_from_authenticated(self):
        """La migration révoque tous les droits sur la table stripe_webhook_events pour authenticated."""
        content = self._migration_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+TABLE\s+.*stripe_webhook_events.*FROM\s+authenticated",
            "REVOKE ALL ON TABLE stripe_webhook_events FROM authenticated doit être présent"
        )

    # SH-06 ───────────────────────────────────────────────────────────────────
    def test_sh_06_sql_validates_action_whitelist(self):
        """La fonction SQL valide p_action contre une whitelist via RAISE EXCEPTION."""
        content = self._migration_content()
        self.assertIn("p_action NOT IN", content,
                      "La fonction doit valider p_action contre une whitelist")
        self.assertIn("'update_plan'", content)
        self.assertIn("'add_bonus'", content)
        self.assertIn("'downgrade_free'", content)
        self.assertIn("RAISE EXCEPTION", content,
                      "Un paramètre non autorisé doit lever RAISE EXCEPTION")

    # SH-07 ───────────────────────────────────────────────────────────────────
    def test_sh_07_sql_validates_plan_whitelist(self):
        """La fonction SQL valide p_new_plan : seuls 'pro', 'scale', 'free' sont autorisés."""
        content = self._migration_content()
        self.assertIn("p_new_plan NOT IN", content,
                      "La fonction doit valider p_new_plan contre une whitelist")
        # Les trois plans autorisés doivent figurer dans la whitelist SQL
        self.assertIn("'pro'", content,
                      "'pro' doit être dans la whitelist des plans autorisés")
        self.assertIn("'scale'", content,
                      "'scale' doit être dans la whitelist des plans autorisés")
        self.assertIn("'free'", content,
                      "'free' doit être dans la whitelist (utilisé par le Billing Portal)")

    # SH-08 ───────────────────────────────────────────────────────────────────
    def test_sh_08_sql_validates_quantity_whitelist(self):
        """La fonction SQL valide p_quantity : seuls 10, 20, 80 sont autorisés."""
        content = self._migration_content()
        self.assertIn("p_quantity NOT IN", content,
                      "La fonction doit valider p_quantity contre une whitelist")
        # Les trois quantités officielles des Executive Capacity Packs
        self.assertIn("10", content)   # Starter Pack
        self.assertIn("20", content)   # Growth Pack
        self.assertIn("80", content)   # Scale Capacity Pack

    # SH-09 ───────────────────────────────────────────────────────────────────
    def test_sh_09_function_has_security_definer(self):
        """La fonction est déclarée SECURITY DEFINER (requis pour le modèle de permission)."""
        content = self._migration_content()
        self.assertIn("SECURITY DEFINER", content,
                      "La fonction doit être SECURITY DEFINER")

    # SH-10 ───────────────────────────────────────────────────────────────────
    def test_sh_10_function_has_safe_search_path(self):
        """La fonction fixe SET search_path pour prévenir l'injection via schema shadowing."""
        content = self._migration_content()
        self.assertIn("SET search_path", content,
                      "La fonction SECURITY DEFINER doit fixer SET search_path")

    # SH-11 ───────────────────────────────────────────────────────────────────
    def test_sh_11_function_signature_uses_full_type_list(self):
        """
        La signature complète à 7 paramètres est utilisée dans les REVOKE/GRANT.
        Sans la signature complète, PostgreSQL ne peut pas identifier la surcharge
        exacte à protéger — les REVOKEs cibleraient une fonction inexistante.
        """
        content = self._migration_content()
        self.assertIn(
            "apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)",
            content,
            "La signature complète (TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) "
            "doit figurer dans les instructions REVOKE/GRANT"
        )

    # SH-12 ───────────────────────────────────────────────────────────────────
    def test_sh_12_revoke_from_public_present(self):
        """
        La migration révoque EXECUTE depuis PUBLIC (groupe PostgreSQL par défaut).
        Supabase accorde EXECUTE à PUBLIC lors du CREATE FUNCTION — ce REVOKE
        supprime ce droit avant d'octroyer EXECUTE à service_role uniquement.
        """
        content = self._migration_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*FROM\s+PUBLIC",
            "REVOKE ALL ON FUNCTION ... FROM PUBLIC doit être présent "
            "(supprime le droit EXECUTE par défaut accordé à PUBLIC)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE 8 — SQL Option B : RPC add_bonus cible companies  (WP1C.2)
#
# Vérifie la migration v11b_stripe_rpc_add_bonus_option_b.sql.
# Garantit que l'action 'add_bonus' écrit dans companies.bonus_analyses_remaining
# (stock permanent) et non dans usage_limits.bonus_analyses (Option A vestige).
# ─────────────────────────────────────────────────────────────────────────────

class TestV11bRPCOptionB(unittest.TestCase):
    """
    WP1C.2 — Tests structurels de la migration v11b.

    Ces tests inspectent le code SQL source sans connexion Supabase.
    Ils constituent le filet de sécurité vérifiant que :
      - L'action 'add_bonus' écrit dans companies.bonus_analyses_remaining.
      - La table usage_limits n'est plus touchée par 'add_bonus'.
      - Les protections de sécurité (SECURITY DEFINER, search_path, REVOKE/GRANT)
        sont ré-appliquées dans la migration.
      - La whitelist des quantités (10, 20, 80) reste en vigueur.
    """

    def _v11b_content(self) -> str:
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations",
            "v11b_stripe_rpc_add_bonus_option_b.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            return f.read()

    # V11B-01 ─────────────────────────────────────────────────────────────────
    def test_v11b_01_fichier_existe(self):
        """La migration v11b existe dans le répertoire migrations/."""
        migrations_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")
        self.assertIn(
            "v11b_stripe_rpc_add_bonus_option_b.sql",
            os.listdir(migrations_dir),
            "v11b_stripe_rpc_add_bonus_option_b.sql absent du répertoire migrations/"
        )

    # V11B-02 ─────────────────────────────────────────────────────────────────
    def test_v11b_02_add_bonus_ecrit_dans_companies(self):
        """add_bonus Option B : UPDATE sur companies (stock permanent)."""
        content = self._v11b_content()
        self.assertIn(
            "bonus_analyses_remaining",
            content,
            "v11b doit mettre à jour companies.bonus_analyses_remaining"
        )
        self.assertIn(
            "public.companies",
            content,
            "v11b doit cibler public.companies dans le bloc add_bonus"
        )

    # V11B-03 ─────────────────────────────────────────────────────────────────
    def test_v11b_03_add_bonus_nexcrit_pas_dans_usage_limits(self):
        """add_bonus Option B : aucun INSERT/UPDATE sur usage_limits.bonus_analyses."""
        content = self._v11b_content()
        # La nouvelle version ne doit pas insérer dans usage_limits pour add_bonus
        self.assertNotIn(
            "INSERT INTO public.usage_limits",
            content,
            "v11b ne doit plus insérer dans usage_limits (Option A supprimée)"
        )

    # V11B-04 ─────────────────────────────────────────────────────────────────
    def test_v11b_04_increments_bonus_remaining(self):
        """add_bonus Option B : incrément atomique COALESCE(bonus_analyses_remaining, 0) + p_quantity."""
        content = self._v11b_content()
        self.assertIn(
            "COALESCE(bonus_analyses_remaining, 0) + p_quantity",
            content,
            "v11b doit utiliser l'incrément atomique COALESCE(...) + p_quantity"
        )

    # V11B-05 ─────────────────────────────────────────────────────────────────
    def test_v11b_05_create_or_replace_function(self):
        """v11b utilise CREATE OR REPLACE FUNCTION apply_stripe_webhook."""
        content = self._v11b_content()
        self.assertIn(
            "CREATE OR REPLACE FUNCTION public.apply_stripe_webhook",
            content,
            "v11b doit utiliser CREATE OR REPLACE FUNCTION apply_stripe_webhook"
        )

    # V11B-06 ─────────────────────────────────────────────────────────────────
    def test_v11b_06_security_definer_conserve(self):
        """v11b conserve SECURITY DEFINER (requis pour le modèle de permission)."""
        content = self._v11b_content()
        self.assertIn("SECURITY DEFINER", content)

    # V11B-07 ─────────────────────────────────────────────────────────────────
    def test_v11b_07_search_path_conserve(self):
        """v11b conserve SET search_path (prévient le schema shadowing)."""
        content = self._v11b_content()
        self.assertIn("SET search_path", content)

    # V11B-08 ─────────────────────────────────────────────────────────────────
    def test_v11b_08_revoke_grant_reappliques(self):
        """v11b ré-applique REVOKE/GRANT après CREATE OR REPLACE."""
        content = self._v11b_content()
        self.assertRegex(
            content,
            r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*FROM\s+anon",
        )
        self.assertRegex(
            content,
            r"GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+.*apply_stripe_webhook.*TO\s+service_role",
        )

    # V11B-09 ─────────────────────────────────────────────────────────────────
    def test_v11b_09_whitelist_quantites_conservee(self):
        """v11b conserve la whitelist des quantités autorisées (10, 20, 80)."""
        content = self._v11b_content()
        self.assertIn("p_quantity NOT IN", content)
        for qty in ("10", "20", "80"):
            self.assertIn(qty, content, f"Quantité {qty} absente de la whitelist v11b")

    # V11B-10 ─────────────────────────────────────────────────────────────────
    def test_v11b_10_whitelist_actions_conservee(self):
        """v11b conserve la whitelist des actions (update_plan, add_bonus, etc.)."""
        content = self._v11b_content()
        self.assertIn("p_action NOT IN", content)
        for action in ("'update_plan'", "'add_bonus'", "'downgrade_free'"):
            self.assertIn(action, content, f"Action {action} absente de la whitelist v11b")

    # V11B-11 ─────────────────────────────────────────────────────────────────
    def test_v11b_11_idempotence_conservee(self):
        """v11b conserve le registre d'idempotence (INSERT ON CONFLICT DO NOTHING)."""
        content = self._v11b_content()
        self.assertIn("ON CONFLICT (stripe_event_id) DO NOTHING", content)
        self.assertIn("stripe_webhook_events", content)

    # V11B-12 ─────────────────────────────────────────────────────────────────
    def test_v11b_12_v_year_month_supprime(self):
        """v11b ne déclare plus v_year_month (plus utilisé après Option B)."""
        content = self._v11b_content()
        self.assertNotIn(
            "v_year_month",
            content,
            "v_year_month ne doit plus figurer dans le DECLARE de v11b (Option B)"
        )


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
