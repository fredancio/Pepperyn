"""
tests/test_wp4b5_webhook_lifecycle.py — Pepperyn WP4B.5
Cycle de vie complet de l'abonnement Stripe : résistance à l'ordre des webhooks,
résolution du company_id, source de vérité du subscription_status.

Architecture testée :
  checkout.session.completed    → init_subscription  (plan + customer_id + subscription_id)
  customer.subscription.created → sync_subscription  (subscription_status + plan optionnel)
  customer.subscription.updated → sync_subscription  (seule autorité du statut)
  customer.subscription.deleted → downgrade_free     (plan=free + status=canceled + sub=NULL)
  invoice.paid                  → noop               (statut délégué à subscription.updated)
  invoice.payment_failed        → noop               (idem)

15 scénarios couverts :
  T01 — checkout avant subscription.created  (ordre normal)
  T02 — subscription.created avant checkout  (ordre inversé — résolution via metadata)
  T03 — subscription.created via fallback customer_id (ancienne subscription sans metadata)
  T04 — subscription.created introuvable → ValueError → Stripe retente
  T05 — subscription.created : status = active
  T06 — subscription.created : status = trialing
  T07 — subscription.updated : status = past_due
  T08 — subscription.updated : changement plan PRO → SCALE via Billing Portal
  T09 — subscription.updated : price inconnue → plan inchangé (new_plan = None)
  T10 — subscription.deleted : metadata-first + downgrade_free
  T11 — subscription.deleted : company introuvable → noop (pas de raise)
  T12 — invoice.paid → noop (aucun update de statut)
  T13 — invoice.payment_failed → noop (aucun update de statut)
  T14 — addon checkout.session.completed → add_bonus (subscription_id + plan non touchés)
  T15 — événement dupliqué : event_id identique → comportement idempotent (noop simulé)
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ── Price IDs de test ─────────────────────────────────────────────────────────
_PRICE_PRO   = "price_test_PRO_xxx"
_PRICE_SCALE = "price_test_SCALE_xxx"
_ENV_PRICES  = {
    "STRIPE_PRICE_PRO":   _PRICE_PRO,
    "STRIPE_PRICE_SCALE": _PRICE_SCALE,
}

# ── Helpers — fabrication d'événements Stripe ─────────────────────────────────

def _event(etype: str, obj: dict, event_id: str = "evt_test_001") -> dict:
    return {"id": event_id, "type": etype, "data": {"object": obj}}


def _checkout_session(
    company_id: str = "comp-abc",
    plan: str = "scale",
    customer: str = "cus_test",
    subscription: str = "sub_test",
) -> dict:
    return {
        "id":           "cs_test",
        "customer":     customer,
        "subscription": subscription,
        "metadata":     {"company_id": company_id, "plan_or_addon": plan},
    }


def _subscription(
    sub_id:      str  = "sub_test",
    customer:    str  = "cus_test",
    status:      str  = "active",
    price_id:    str  = _PRICE_SCALE,
    metadata:    dict = None,
) -> dict:
    return {
        "id":       sub_id,
        "customer": customer,
        "status":   status,
        "metadata": metadata if metadata is not None else {"company_id": "comp-abc", "plan_or_addon": "scale"},
        "items":    {"data": [{"price": {"id": price_id}}]},
    }


def _invoice(customer: str = "cus_test", subscription: str = "sub_test") -> dict:
    return {"customer": customer, "subscription": subscription}


# ── Service factory ───────────────────────────────────────────────────────────

def _make_service(
    company_by_customer: str = "",
    stripe_key: str = "sk_test_fake",
):
    """Crée un BillingService avec stripe mocké + helpers patchés."""
    from services.billing_service import BillingService
    svc = BillingService()

    stripe_mock = MagicMock()
    svc._stripe_mock = stripe_mock

    # _stripe() retourne toujours le mock
    svc._stripe = lambda: stripe_mock

    # STRIPE_WEBHOOK_SECRET doit être non-vide pour que construct_event ne plante pas
    import services.billing_service as _bs
    _bs.STRIPE_WEBHOOK_SECRET = "whsec_test_fake"
    _bs.STRIPE_SECRET_KEY     = stripe_key

    # Patch _get_company_by_customer pour le fallback customer_id
    svc._get_company_by_customer = lambda cid: company_by_customer

    return svc


def _process(svc, event_obj: dict) -> dict:
    """Appelle process_webhook_event avec l'événement directement injecté."""
    svc._stripe_mock.Webhook.construct_event.return_value = event_obj
    return svc.process_webhook_event(b"payload", "sig_test")


# ═════════════════════════════════════════════════════════════════════════════
# T01–T02 — Ordre des événements (checkout vs subscription.created)
# ═════════════════════════════════════════════════════════════════════════════

class TestEventOrdering(unittest.TestCase):

    # T01 ─────────────────────────────────────────────────────────────────────
    def test_01_checkout_before_subscription_created(self):
        """Ordre normal : checkout.session.completed arrive en premier.
        Résultat attendu : init_subscription avec plan + customer + subscription_id."""
        svc    = _make_service()
        result = _process(svc, _event(
            "checkout.session.completed",
            _checkout_session(company_id="comp-abc", plan="scale",
                              customer="cus_test", subscription="sub_test"),
            event_id="evt_checkout_01",
        ))
        self.assertEqual(result["action"],                 "init_subscription")
        self.assertEqual(result["plan"],                   "scale")
        self.assertEqual(result["company_id"],             "comp-abc")
        self.assertEqual(result["stripe_customer_id"],     "cus_test")
        self.assertEqual(result["stripe_subscription_id"], "sub_test")
        # subscription_status NE doit PAS être dans le résultat init_subscription
        self.assertNotIn("subscription_status", result)

    # T02 ─────────────────────────────────────────────────────────────────────
    def test_02_subscription_created_before_checkout(self):
        """Ordre inversé : customer.subscription.created arrive AVANT checkout.
        La résolution se fait via sub.metadata.company_id — aucune dépendance envers
        checkout.session.completed, aucune perte d'événement."""
        # company_by_customer = "" → le fallback ne trouve rien non plus
        # mais sub.metadata.company_id = "comp-abc" → doit suffire
        svc    = _make_service(company_by_customer="")
        result = _process(svc, _event(
            "customer.subscription.created",
            _subscription(sub_id="sub_test", customer="cus_test", status="active",
                          metadata={"company_id": "comp-abc", "plan_or_addon": "scale"}),
            event_id="evt_sub_created_02",
        ))
        self.assertEqual(result["action"],                 "sync_subscription")
        self.assertEqual(result["company_id"],             "comp-abc")
        self.assertEqual(result["stripe_subscription_id"], "sub_test")
        self.assertEqual(result["subscription_status"],    "active")

    # T03 ─────────────────────────────────────────────────────────────────────
    def test_03_subscription_created_fallback_customer_id(self):
        """Ancienne subscription sans metadata.company_id.
        Fallback : _get_company_by_customer(customer_id) → 'comp-legacy'."""
        svc    = _make_service(company_by_customer="comp-legacy")
        result = _process(svc, _event(
            "customer.subscription.created",
            _subscription(metadata={}),   # metadata vide → fallback nécessaire
            event_id="evt_sub_created_03",
        ))
        self.assertEqual(result["action"],     "sync_subscription")
        self.assertEqual(result["company_id"], "comp-legacy")

    # T04 ─────────────────────────────────────────────────────────────────────
    def test_04_subscription_created_company_not_found_raises(self):
        """Ni metadata ni fallback ne trouvent la company.
        Attendu : ValueError → Stripe retente l'événement."""
        svc = _make_service(company_by_customer="")   # fallback aussi vide
        with self.assertRaises(ValueError) as ctx:
            _process(svc, _event(
                "customer.subscription.created",
                _subscription(metadata={}),   # aucune metadata
                event_id="evt_sub_created_04",
            ))
        self.assertIn("company_id introuvable", str(ctx.exception))

    # T15 ─────────────────────────────────────────────────────────────────────
    def test_15_event_replayed_after_init(self):
        """checkout.session.completed rejoué après init.
        La couche SQL gère l'idempotence (ON CONFLICT DO NOTHING).
        Côté Python : le dict retourné est identique — pas d'exception."""
        svc    = _make_service()
        event  = _event("checkout.session.completed",
                         _checkout_session(), event_id="evt_replay_15")
        # Premier appel
        r1 = _process(svc, event)
        # Deuxième appel (rejoué) — doit retourner le même dict sans erreur
        r2 = _process(svc, event)
        self.assertEqual(r1["action"], r2["action"])
        self.assertEqual(r1["stripe_event_id"], r2["stripe_event_id"])


# ═════════════════════════════════════════════════════════════════════════════
# T05–T09 — Statuts et changements de plan
# ═════════════════════════════════════════════════════════════════════════════

class TestSubscriptionStatus(unittest.TestCase):

    # T05 ─────────────────────────────────────────────────────────────────────
    def test_05_subscription_created_status_active(self):
        """customer.subscription.created avec status=active."""
        svc    = _make_service()
        result = _process(svc, _event(
            "customer.subscription.created",
            _subscription(status="active"),
            event_id="evt_status_05",
        ))
        self.assertEqual(result["subscription_status"], "active")

    # T06 ─────────────────────────────────────────────────────────────────────
    def test_06_subscription_created_status_trialing(self):
        """customer.subscription.created avec status=trialing (période d'essai)."""
        svc    = _make_service()
        result = _process(svc, _event(
            "customer.subscription.created",
            _subscription(status="trialing"),
            event_id="evt_status_06",
        ))
        self.assertEqual(result["subscription_status"], "trialing")

    # T07 ─────────────────────────────────────────────────────────────────────
    def test_07_subscription_updated_status_past_due(self):
        """customer.subscription.updated — statut passe à past_due après paiement raté.
        subscription.updated est la SEULE autorité → c'est lui qui met à jour le statut."""
        svc    = _make_service()
        result = _process(svc, _event(
            "customer.subscription.updated",
            _subscription(status="past_due"),
            event_id="evt_status_07",
        ))
        self.assertEqual(result["action"],              "sync_subscription")
        self.assertEqual(result["subscription_status"], "past_due")

    # T08 ─────────────────────────────────────────────────────────────────────
    def test_08_subscription_updated_plan_change_pro_to_scale(self):
        """customer.subscription.updated : changement de plan PRO → SCALE via Billing Portal.
        La price_id SCALE est résolue → plan='scale' dans le résultat."""
        svc    = _make_service()
        with patch.dict(os.environ, _ENV_PRICES):
            result = _process(svc, _event(
                "customer.subscription.updated",
                _subscription(price_id=_PRICE_SCALE, status="active"),
                event_id="evt_plan_change_08",
            ))
        self.assertEqual(result["action"], "sync_subscription")
        self.assertEqual(result["plan"],   "scale")

    # T09 ─────────────────────────────────────────────────────────────────────
    def test_09_subscription_updated_unknown_price_plan_is_none(self):
        """customer.subscription.updated : price inconnue (ex. plan non Pepperyn).
        new_plan doit être None → la DB ne change pas le plan."""
        svc    = _make_service()
        with patch.dict(os.environ, _ENV_PRICES):
            result = _process(svc, _event(
                "customer.subscription.updated",
                _subscription(price_id="price_UNKNOWN_xyz", status="active"),
                event_id="evt_unknown_price_09",
            ))
        self.assertEqual(result["action"], "sync_subscription")
        self.assertIsNone(result["plan"])   # plan inchangé en DB


# ═════════════════════════════════════════════════════════════════════════════
# T10–T11 — Suppression d'abonnement
# ═════════════════════════════════════════════════════════════════════════════

class TestSubscriptionDeleted(unittest.TestCase):

    # T10 ─────────────────────────────────────────────────────────────────────
    def test_10_subscription_deleted_metadata_first(self):
        """customer.subscription.deleted — company résolue via sub.metadata.company_id."""
        svc    = _make_service(company_by_customer="")  # fallback vide
        result = _process(svc, _event(
            "customer.subscription.deleted",
            {   # metadata.company_id présent directement dans la sub
                "id":       "sub_deleted",
                "customer": "cus_test",
                "metadata": {"company_id": "comp-abc"},
                "status":   "canceled",
            },
            event_id="evt_deleted_10",
        ))
        self.assertEqual(result["action"],     "downgrade_free")
        self.assertEqual(result["company_id"], "comp-abc")

    # T11 ─────────────────────────────────────────────────────────────────────
    def test_11_subscription_deleted_company_not_found_noop(self):
        """customer.subscription.deleted — company introuvable → noop (pas de raise).
        Un compte inexistant ne peut pas être downgradé ; les retries Stripe seraient infinis."""
        svc    = _make_service(company_by_customer="")
        result = _process(svc, _event(
            "customer.subscription.deleted",
            {"id": "sub_ghost", "customer": "cus_ghost", "metadata": {}, "status": "canceled"},
            event_id="evt_deleted_11",
        ))
        self.assertEqual(result["action"], "noop")


# ═════════════════════════════════════════════════════════════════════════════
# T12–T13 — Événements invoice : noop, aucune mise à jour du statut
# ═════════════════════════════════════════════════════════════════════════════

class TestInvoiceEventsAreNoop(unittest.TestCase):
    """invoice.paid et invoice.payment_failed ne doivent jamais modifier
    subscription_status. customer.subscription.updated est la seule autorité."""

    # T12 ─────────────────────────────────────────────────────────────────────
    def test_12_invoice_paid_is_noop(self):
        """invoice.paid → action='noop', aucun subscription_status dans le résultat."""
        svc    = _make_service()
        result = _process(svc, _event("invoice.paid", _invoice(), event_id="evt_inv_paid_12"))
        self.assertEqual(result["action"], "noop")
        self.assertNotIn("subscription_status", result)

    # T13 ─────────────────────────────────────────────────────────────────────
    def test_13_invoice_payment_failed_is_noop(self):
        """invoice.payment_failed → action='noop', aucun subscription_status.
        Stripe déclenchera customer.subscription.updated avec status=past_due."""
        svc    = _make_service()
        result = _process(svc, _event(
            "invoice.payment_failed", _invoice(), event_id="evt_inv_failed_13"
        ))
        self.assertEqual(result["action"], "noop")
        self.assertNotIn("subscription_status", result)


# ═════════════════════════════════════════════════════════════════════════════
# T14 — Addon : pas d'impact sur subscription_id ni plan
# ═════════════════════════════════════════════════════════════════════════════

class TestAddonWebhook(unittest.TestCase):

    # T14 ─────────────────────────────────────────────────────────────────────
    def test_14_addon_checkout_returns_add_bonus_not_subscription(self):
        """checkout.session.completed pour un Executive Capacity Pack (addon_growth).
        Attendu : action='add_bonus', quantity=20, aucun stripe_subscription_id,
        aucun changement de plan."""
        svc = _make_service()
        obj = {
            "id":           "cs_addon_test",
            "customer":     "cus_test",
            "subscription": None,    # pas de subscription pour un pack one-time
            "metadata":     {"company_id": "comp-abc", "plan_or_addon": "addon_growth"},
        }
        result = _process(svc, _event(
            "checkout.session.completed", obj, event_id="evt_addon_14"
        ))
        self.assertEqual(result["action"],   "add_bonus")
        self.assertEqual(result["quantity"], 20)
        self.assertNotIn("stripe_subscription_id", result)
        self.assertNotIn("plan",                   result)


# ═════════════════════════════════════════════════════════════════════════════
# Intégrité — subscription_data.metadata dans create_checkout_session
# ═════════════════════════════════════════════════════════════════════════════

class TestCheckoutSessionMetadata(unittest.TestCase):

    def _make_stripe_mock(self):
        session_mock = MagicMock()
        session_mock.id  = "cs_fake_id"
        session_mock.url = "https://checkout.stripe.com/fake"
        stripe_mock = MagicMock()
        stripe_mock.checkout.Session.create.return_value = session_mock
        return stripe_mock

    def test_subscription_data_metadata_injected_for_plan(self):
        """create_checkout_session (mode subscription) doit transmettre
        subscription_data.metadata avec company_id et plan_or_addon.
        Garantit que customer.subscription.created peut résoudre la company
        sans dépendre de l'ordre des webhooks."""
        from services.billing_service import BillingService
        svc = BillingService()
        stripe_mock = self._make_stripe_mock()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_SCALE": "price_test_scale"}):
                svc.create_checkout_session("scale", "comp-xyz")
        kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertIn("subscription_data", kwargs)
        sub_meta = kwargs["subscription_data"]["metadata"]
        self.assertEqual(sub_meta["company_id"],    "comp-xyz")
        self.assertEqual(sub_meta["plan_or_addon"], "scale")

    def test_subscription_data_absent_for_addon(self):
        """create_checkout_session pour un addon (mode payment) NE doit PAS
        passer subscription_data (non pertinent pour un paiement unique)."""
        from services.billing_service import BillingService
        svc = BillingService()
        stripe_mock = self._make_stripe_mock()
        with patch.object(svc, "_stripe", return_value=stripe_mock):
            with patch.dict(os.environ, {"STRIPE_PRICE_ADDON_GROWTH": "price_test_growth"}):
                svc.create_checkout_session("addon_growth", "comp-xyz")
        kwargs = stripe_mock.checkout.Session.create.call_args[1]
        self.assertNotIn("subscription_data", kwargs)


# ═════════════════════════════════════════════════════════════════════════════
# Tests structurels SQL — v12_stripe_lifecycle_sync.sql
# Validation statique : aucun accès DB requis.
# ═════════════════════════════════════════════════════════════════════════════

import pathlib as _pathlib

def _sql_v12() -> str:
    """Charge le contenu de v12_stripe_lifecycle_sync.sql."""
    path = _pathlib.Path(__file__).parent.parent / "migrations" / "v12_stripe_lifecycle_sync.sql"
    return path.read_text(encoding="utf-8")


class TestSQLMigrationV12Structure(unittest.TestCase):
    """Valide statiquement le contenu de v12_stripe_lifecycle_sync.sql.
    Aucune connexion DB requise — lecture du fichier uniquement."""

    @classmethod
    def setUpClass(cls):
        cls.sql = _sql_v12()

    # ── Signatures ────────────────────────────────────────────────────────────

    def test_sql_01_signature_9params_present(self):
        """La signature 9-params (avec p_stripe_subscription et p_subscription_status) est présente."""
        self.assertIn("p_stripe_subscription", self.sql)
        self.assertIn("p_subscription_status", self.sql)
        # Forme complète : 9 TEXT params dans la signature CREATE OR REPLACE
        self.assertIn("CREATE OR REPLACE FUNCTION public.apply_stripe_webhook", self.sql)

    def test_sql_02_drop_7params_present(self):
        """DROP FUNCTION IF EXISTS pour la signature 7-params est présent."""
        # La signature 7-params : (TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)
        self.assertIn(
            "DROP FUNCTION IF EXISTS public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)",
            self.sql,
        )

    def test_sql_03_drop_after_grant(self):
        """Le DROP de la 7-params apparaît APRÈS le GRANT sur la 9-params.
        Garantit que la 9-params est opérationnelle avant la suppression de l'ancienne."""
        grant_pos = self.sql.find(
            "GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)"
        )
        drop_pos = self.sql.find(
            "DROP FUNCTION IF EXISTS public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)"
        )
        self.assertGreater(grant_pos, 0, "GRANT 9-params introuvable")
        self.assertGreater(drop_pos, 0, "DROP 7-params introuvable")
        self.assertGreater(drop_pos, grant_pos, "DROP doit apparaître APRÈS GRANT")

    # ── Sécurité de la fonction ───────────────────────────────────────────────

    def test_sql_04_security_definer(self):
        """La fonction utilise SECURITY DEFINER."""
        self.assertIn("SECURITY DEFINER", self.sql)

    def test_sql_05_search_path_public(self):
        """SET search_path = public est déclaré."""
        self.assertIn("SET search_path = public", self.sql)

    # ── Permissions ───────────────────────────────────────────────────────────

    def test_sql_06_revoke_public_9params(self):
        """REVOKE ALL FROM PUBLIC sur la 9-params."""
        self.assertIn(
            "REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)\n    FROM PUBLIC",
            self.sql,
        )

    def test_sql_07_revoke_anon_9params(self):
        """REVOKE ALL FROM anon sur la 9-params."""
        self.assertIn(
            "REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)\n    FROM anon",
            self.sql,
        )

    def test_sql_08_revoke_authenticated_9params(self):
        """REVOKE ALL FROM authenticated sur la 9-params."""
        self.assertIn(
            "REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)\n    FROM authenticated",
            self.sql,
        )

    def test_sql_09_grant_service_role_9params(self):
        """GRANT EXECUTE TO service_role sur la 9-params."""
        self.assertIn(
            "GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)\n    TO service_role",
            self.sql,
        )

    def test_sql_10_revoke_7params_service_role(self):
        """REVOKE EXECUTE FROM service_role sur la 7-params."""
        self.assertIn(
            "REVOKE EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)\n    FROM service_role",
            self.sql,
        )

    # ── Whitelist des actions ─────────────────────────────────────────────────

    def test_sql_11_action_whitelist_all_actions(self):
        """Les 7 actions de la whitelist sont toutes déclarées."""
        for action in (
            "init_subscription", "sync_subscription", "update_plan",
            "add_bonus", "downgrade_free", "noop", "unhandled",
        ):
            self.assertIn(action, self.sql, f"Action absente de la whitelist : {action!r}")

    # ── Whitelist des statuts ─────────────────────────────────────────────────

    def test_sql_12_status_whitelist_all_statuses(self):
        """Les 8 statuts Stripe natifs sont tous déclarés dans la whitelist."""
        for status in (
            "active", "trialing", "past_due", "canceled",
            "unpaid", "paused", "incomplete", "incomplete_expired",
        ):
            self.assertIn(status, self.sql, f"Statut absent de la whitelist : {status!r}")

    # ── Branches métier ───────────────────────────────────────────────────────

    def test_sql_13_init_subscription_branch_no_subscription_status(self):
        """init_subscription ne doit PAS mettre à jour subscription_status.
        Elle initialise uniquement plan + stripe_customer_id + stripe_subscription_id.

        Méthode : on isole le bloc UPDATE jusqu'au WHERE (borne propre, sans commentaires
        du bloc suivant) et on vérifie l'absence d'assignation SQL subscription_status = …
        """
        import re
        # Extraire le bloc UPDATE de init_subscription :
        # de "IF p_action = 'init_subscription'" jusqu'au "WHERE id = …;" inclus
        pattern = re.compile(
            r"IF p_action = 'init_subscription'.*?WHERE id = p_company_id::UUID;",
            re.DOTALL,
        )
        m = pattern.search(self.sql)
        self.assertIsNotNone(m, "Bloc init_subscription introuvable dans le SQL")
        init_update_block = m.group(0)
        # Vérifier qu'aucune assignation SQL de subscription_status n'est présente
        # (pattern : "subscription_status" suivi de "=" hors commentaire)
        # Les commentaires du prochain bloc ne sont PAS inclus dans cette extraction.
        self.assertNotIn("subscription_status", init_update_block,
            "init_subscription ne doit pas écrire subscription_status — "
            f"bloc extrait : {init_update_block!r}")

    def test_sql_14_sync_subscription_sets_subscription_status(self):
        """sync_subscription doit mettre à jour subscription_status."""
        start = self.sql.find("p_action = 'sync_subscription'")
        self.assertGreater(start, 0)
        end = self.sql.find("ELSIF p_action =", start + 1)
        sync_block = self.sql[start:end]
        self.assertIn("subscription_status", sync_block,
            "sync_subscription doit écrire subscription_status")

    def test_sql_15_add_bonus_branch_unchanged(self):
        """add_bonus incrémente bonus_analyses_remaining (Option B — WP1C.2)."""
        self.assertIn("bonus_analyses_remaining", self.sql)
        self.assertIn("COALESCE(bonus_analyses_remaining, 0) + p_quantity", self.sql)

    def test_sql_16_downgrade_free_clears_subscription_id(self):
        """downgrade_free positionne plan='free', status='canceled' et subscription_id=NULL."""
        start = self.sql.find("p_action = 'downgrade_free'")
        self.assertGreater(start, 0)
        end = self.sql.find("-- ELSE", start)
        downgrade_block = self.sql[start:end]
        self.assertIn("plan                   = 'free'",    downgrade_block)
        self.assertIn("subscription_status    = 'canceled'", downgrade_block)
        self.assertIn("stripe_subscription_id = NULL",       downgrade_block)

    # ── Idempotence ───────────────────────────────────────────────────────────

    def test_sql_17_idempotence_on_conflict_stripe_event_id(self):
        """L'idempotence repose sur ON CONFLICT (stripe_event_id) DO NOTHING."""
        self.assertIn("ON CONFLICT (stripe_event_id) DO NOTHING", self.sql)
        self.assertIn("IF NOT FOUND THEN", self.sql)
        # Le retour 'duplicate' doit être explicitement défini
        self.assertIn("'duplicate'", self.sql)


if __name__ == "__main__":
    unittest.main(verbosity=2)
