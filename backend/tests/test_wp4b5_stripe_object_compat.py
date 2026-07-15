"""
tests/test_wp4b5_stripe_object_compat.py — Pepperyn Release 1.0 — WP4B.5
Compatibilité StripeObject : vérifier que process_webhook_event() normalise
correctement un StripeObject retourné par stripe.Webhook.construct_event().

Contexte
--------
stripe >= 5.x retourne un StripeObject typé depuis construct_event().
StripeObject ne supporte pas .get() (AttributeError observé en production ligne 193).
Le correctif : event.to_dict() immédiatement après construct_event().

Les tests ci-dessous simulent le comportement réel de production en passant
de vrais StripeObjects (stripe.Event.construct_from()) au lieu de dicts Python.
Ils échoueraient SANS le correctif, et doivent passer AVEC le correctif.

7 scénarios couverts :
  COMPAT-01  checkout.session.completed — plan PRO
  COMPAT-02  checkout.session.completed — addon_starter
  COMPAT-03  customer.subscription.created — metadata-first
  COMPAT-04  customer.subscription.updated — statut past_due
  COMPAT-05  customer.subscription.deleted — downgrade_free
  COMPAT-06  invoice.paid — noop
  COMPAT-07  invoice.payment_failed — noop
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import stripe as _stripe_lib


# ─────────────────────────────────────────────────────────────────────────────
# Helper : construire un vrai StripeObject à partir d'un dict brut
# ─────────────────────────────────────────────────────────────────────────────

def _make_stripe_event_object(raw: dict) -> _stripe_lib.Event:
    """
    Retourne un stripe.Event typé (StripeObject), comme le ferait
    stripe.Webhook.construct_event() en production.
    Les tests qui passent ce StripeObject valident que to_dict()
    est appliqué avant tout accès .get().
    """
    return _stripe_lib.Event.construct_from(raw, key="sk_test_xxx")


def _confirm_no_get(event_obj) -> None:
    """
    Vérifie que l'objet passé est bien un StripeObject sans .get().
    Sert à documenter explicitement le problème que le correctif résout.
    """
    assert not isinstance(event_obj, dict), (
        "Attendu un StripeObject, pas un dict Python"
    )
    assert not hasattr(event_obj, "get"), (
        f"Le StripeObject {type(event_obj)} ne doit pas exposer .get() "
        f"— sinon le test ne valide pas le correctif"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Classe de base avec le helper d'appel unifié
# ─────────────────────────────────────────────────────────────────────────────

class _StripeObjectCompatBase(unittest.TestCase):
    """
    Base commune : process_webhook_event() appelé avec un vrai StripeObject
    retourné par construct_event() (pas un dict).
    """

    def _process_with_stripe_object(self, raw_event: dict) -> dict:
        """
        Crée un StripeObject depuis raw_event, le passe à construct_event(),
        et appelle process_webhook_event(). Le correctif doit empêcher l'AttributeError.
        """
        from services.billing_service import BillingService
        svc = BillingService()

        stripe_event_obj = _make_stripe_event_object(raw_event)
        _confirm_no_get(stripe_event_obj)   # Preuve que c'est bien un StripeObject

        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = stripe_event_obj

        with patch.object(svc, "_stripe", return_value=stripe_mock):
            return svc.process_webhook_event(b"payload", "sig_test")


# ─────────────────────────────────────────────────────────────────────────────
# COMPAT-01 — checkout.session.completed — plan PRO
# ─────────────────────────────────────────────────────────────────────────────

class TestStripeObjectCheckoutPlan(_StripeObjectCompatBase):

    # COMPAT-01
    def test_compat_01_checkout_plan_pro_from_stripe_object(self):
        """
        StripeObject checkout.session.completed (plan=pro) → init_subscription.
        Sans correctif : AttributeError: 'Event' object has no attribute 'get' (ligne 193).
        """
        raw = {
            "id": "evt_compat_01_pro",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_compat_01",
                    "metadata": {
                        "company_id":    "co_compat_01",
                        "plan_or_addon": "pro",
                    },
                    "customer":     "cus_compat_01",
                    "subscription": "sub_compat_01",
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],                 "init_subscription",
                         "COMPAT-01 : action doit être init_subscription")
        self.assertEqual(result["plan"],                   "pro")
        self.assertEqual(result["company_id"],             "co_compat_01")
        self.assertEqual(result["stripe_customer_id"],     "cus_compat_01")
        self.assertEqual(result["stripe_subscription_id"], "sub_compat_01")
        self.assertEqual(result["stripe_event_id"],        "evt_compat_01_pro")
        self.assertEqual(result["event_type"],             "checkout.session.completed")

    # COMPAT-02
    def test_compat_02_checkout_addon_from_stripe_object(self):
        """
        StripeObject checkout.session.completed (addon_starter) → add_bonus.
        Valide que les objets imbriqués metadata sont bien convertis.
        """
        raw = {
            "id": "evt_compat_02_addon",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_compat_02",
                    "metadata": {
                        "company_id":    "co_compat_02",
                        "plan_or_addon": "addon_starter",
                    },
                    "customer": "cus_compat_02",
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],             "add_bonus",
                         "COMPAT-02 : addon doit retourner add_bonus")
        self.assertEqual(result["quantity"],           10,
                         "COMPAT-02 : addon_starter = 10 analyses")
        self.assertEqual(result["company_id"],         "co_compat_02")
        self.assertEqual(result["stripe_customer_id"], "cus_compat_02")
        self.assertEqual(result["stripe_event_id"],    "evt_compat_02_addon")


# ─────────────────────────────────────────────────────────────────────────────
# COMPAT-03/04 — customer.subscription.created / updated
# ─────────────────────────────────────────────────────────────────────────────

class TestStripeObjectSubscription(_StripeObjectCompatBase):

    # COMPAT-03
    def test_compat_03_subscription_created_from_stripe_object(self):
        """
        StripeObject customer.subscription.created → sync_subscription.
        company_id résolu depuis subscription.metadata (metadata-first).
        Valide que sub_metadata.get() fonctionne après normalisation.
        """
        raw = {
            "id": "evt_compat_03_created",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id":       "sub_compat_03",
                    "customer": "cus_compat_03",
                    "status":   "active",
                    "metadata": {"company_id": "co_compat_03"},
                    "items": {
                        "data": [
                            {"price": {"id": "price_test_pro"}}
                        ]
                    },
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],                 "sync_subscription",
                         "COMPAT-03 : subscription.created → sync_subscription")
        self.assertEqual(result["company_id"],             "co_compat_03")
        self.assertEqual(result["stripe_customer_id"],     "cus_compat_03")
        self.assertEqual(result["stripe_subscription_id"], "sub_compat_03")
        self.assertEqual(result["subscription_status"],    "active")
        self.assertEqual(result["stripe_event_id"],        "evt_compat_03_created")

    # COMPAT-04
    def test_compat_04_subscription_updated_past_due_from_stripe_object(self):
        """
        StripeObject customer.subscription.updated (status=past_due) → sync_subscription.
        Valide que subscription_status est correctement lu depuis le StripeObject.
        """
        raw = {
            "id": "evt_compat_04_updated",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id":       "sub_compat_04",
                    "customer": "cus_compat_04",
                    "status":   "past_due",
                    "metadata": {"company_id": "co_compat_04"},
                    "items": {"data": []},
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],              "sync_subscription")
        self.assertEqual(result["subscription_status"], "past_due",
                         "COMPAT-04 : past_due doit être transmis")
        self.assertEqual(result["company_id"],          "co_compat_04")


# ─────────────────────────────────────────────────────────────────────────────
# COMPAT-05 — customer.subscription.deleted
# ─────────────────────────────────────────────────────────────────────────────

class TestStripeObjectSubscriptionDeleted(_StripeObjectCompatBase):

    # COMPAT-05
    def test_compat_05_subscription_deleted_from_stripe_object(self):
        """
        StripeObject customer.subscription.deleted → downgrade_free.
        company_id résolu depuis metadata (metadata-first).
        Valide obj.get('metadata') sur un StripeObject imbriqué.
        """
        raw = {
            "id": "evt_compat_05_deleted",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id":       "sub_compat_05",
                    "customer": "cus_compat_05",
                    "status":   "canceled",
                    "metadata": {"company_id": "co_compat_05"},
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],          "downgrade_free",
                         "COMPAT-05 : subscription.deleted → downgrade_free")
        self.assertEqual(result["company_id"],      "co_compat_05")
        self.assertEqual(result["stripe_event_id"], "evt_compat_05_deleted")


# ─────────────────────────────────────────────────────────────────────────────
# COMPAT-06/07 — invoice.paid / invoice.payment_failed
# ─────────────────────────────────────────────────────────────────────────────

class TestStripeObjectInvoice(_StripeObjectCompatBase):

    # COMPAT-06
    def test_compat_06_invoice_paid_from_stripe_object(self):
        """
        StripeObject invoice.paid → noop.
        Valide que invoice.get('customer') fonctionne après normalisation.
        """
        raw = {
            "id": "evt_compat_06_inv_paid",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "customer": "cus_compat_06",
                    "status":   "paid",
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],          "noop",
                         "COMPAT-06 : invoice.paid → noop")
        self.assertEqual(result["stripe_event_id"], "evt_compat_06_inv_paid")

    # COMPAT-07
    def test_compat_07_invoice_payment_failed_from_stripe_object(self):
        """
        StripeObject invoice.payment_failed → noop.
        Valide que invoice.get('customer') fonctionne après normalisation.
        """
        raw = {
            "id": "evt_compat_07_inv_fail",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_compat_07",
                    "status":   "open",
                }
            },
        }
        result = self._process_with_stripe_object(raw)

        self.assertEqual(result["action"],          "noop",
                         "COMPAT-07 : invoice.payment_failed → noop")
        self.assertEqual(result["stripe_event_id"], "evt_compat_07_inv_fail")


# ─────────────────────────────────────────────────────────────────────────────
# COMPAT-08 — Validation directe : to_dict() est bien appelé
# ─────────────────────────────────────────────────────────────────────────────

class TestStripeObjectNormalization(unittest.TestCase):

    def test_compat_08_stripe_object_get_raises_without_normalization(self):
        """
        Test unitaire direct du bug : StripeObject.get('id') lève AttributeError.
        Prouve que la normalisation to_dict() est obligatoire.
        Ce test valide la prémisse du correctif, indépendamment du service.
        """
        raw = {
            "id": "evt_compat_08_unit",
            "type": "invoice.paid",
            "data": {"object": {"customer": "cus_test"}},
        }
        stripe_event_obj = _stripe_lib.Event.construct_from(raw, key="sk_test_xxx")

        # 1. StripeObject ne supporte pas .get() — c'est le bug de production
        self.assertFalse(hasattr(stripe_event_obj, "get"),
                         "StripeObject ne doit pas exposer .get()")
        with self.assertRaises(AttributeError,
                               msg="event.get('id') doit lever AttributeError sans normalisation"):
            stripe_event_obj.get("id")   # type: ignore[attr-defined]

        # 2. to_dict() convertit le StripeObject en dict natif
        native = stripe_event_obj.to_dict()
        self.assertIsInstance(native, dict,
                              "to_dict() doit retourner un dict Python natif")

        # 3. Après normalisation, .get() fonctionne sur tous les niveaux
        self.assertEqual(native.get("id"), "evt_compat_08_unit")
        self.assertEqual(native.get("type"), "invoice.paid")
        data_obj = native.get("data", {}).get("object", {})
        self.assertIsInstance(data_obj, dict,
                              "data.object doit être un dict après to_dict()")
        self.assertEqual(data_obj.get("customer"), "cus_test")

    def test_compat_09_no_attribute_error_on_stripe_object(self):
        """
        Régression directe du bug de production :
        sans correctif, event.get('id') lève AttributeError: 'Event' object has no attribute 'get'.
        Avec correctif, le même StripeObject est normalisé et traité sans erreur.
        """
        from services.billing_service import BillingService
        svc = BillingService()

        raw = {
            "id": "evt_compat_09_regression",
            "type": "invoice.paid",
            "data": {
                "object": {"customer": "cus_test", "status": "paid"}
            },
        }
        stripe_event_obj = _stripe_lib.Event.construct_from(raw, key="sk_test_xxx")

        # Confirmer que le StripeObject lui-même n'a pas .get() (le bug)
        self.assertFalse(hasattr(stripe_event_obj, "get"),
                         "StripeObject ne doit pas exposer .get() — c'est le bug d'origine")

        # Appeler process_webhook_event avec ce StripeObject : ne doit pas lever
        stripe_mock = MagicMock()
        stripe_mock.Webhook.construct_event.return_value = stripe_event_obj

        try:
            with patch.object(svc, "_stripe", return_value=stripe_mock):
                result = svc.process_webhook_event(b"payload", "sig_test")
            self.assertEqual(result["action"], "noop")
        except AttributeError as e:
            self.fail(
                f"AttributeError inattendu — le correctif to_dict() n'a pas été appliqué : {e}"
            )


if __name__ == "__main__":
    unittest.main()
