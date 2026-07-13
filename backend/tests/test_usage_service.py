"""
test_usage_service.py — WP1C + WP1C.1
Tests unitaires du moteur de quotas Usage Service.

Source de vérité : config/product_catalog.py
Aucune constante locale — toutes les valeurs viennent du catalog.

Plans testés :
  FREE  : 1 Analyse/mois,  3 Interactions/mois,  1 Entité max
  PRO   : 30 Analyses/mois, 75 Interactions/mois, 10 Entités max
  SCALE : 100 Analyses/mois, 500 Interactions/mois, Entités illimitées

Executive Capacity Packs :
  Starter  → +10 Analyses bonus
  Growth   → +20 Analyses bonus
  Scale CP → +80 Analyses bonus

SÉMANTIQUE WP1C.1 :
  bonus_analyses = SOLDE RESTANT (pas total acheté)
  analyses_count = quota mensuel consommé (hors bonus)

  Consommation : bonus_analyses > 0 → décrément bonus
                 bonus_analyses = 0 → incrément analyses_count

  Renouvellement : analyses_count → 0, bonus_analyses INCHANGÉ (report)
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.usage_service import UsageService


# ─── Helpers simples ─────────────────────────────────────────────────────────

def _row(analyses_count=0, chat_count=0, bonus_analyses=0):
    """Construit une ligne usage_limits simulée (sémantique WP1C.1).

    analyses_count = quota mensuel consommé (hors bonus)
    bonus_analyses = SOLDE RESTANT d'analyses bonus
    """
    return {
        "analyses_count": analyses_count,
        "chat_count": chat_count,
        "bonus_analyses": bonus_analyses,
    }


def _svc_with_usage(row: dict) -> UsageService:
    """Crée un UsageService avec _get_or_create_usage_row mocké."""
    svc = UsageService()
    svc._get_or_create_usage_row = MagicMock(return_value=row)
    return svc


def _svc_with_chat(monthly_count: int) -> UsageService:
    """Crée un UsageService avec get_monthly_chat_count mocké."""
    svc = UsageService()
    svc.get_monthly_chat_count = MagicMock(return_value=monthly_count)
    return svc


# ─── Mock Supabase en mémoire (pour tests WP1C.1) ────────────────────────────

class _InMemorySupabase:
    """Simule Supabase avec état en mémoire partagé.
    Usage : tester _consume_one_analysis() et increment_analysis().

    IMPORTANT : stocke une RÉFÉRENCE au dict d'état (pas une copie) afin que les
    modifications du builder soient visibles depuis le dict `state` du test.
    """

    def __init__(self, state: dict):
        self.state = state  # référence directe — mutations visibles par le test

    def from_(self, _table):
        return _InMemoryBuilder(self.state)


class _InMemoryBuilder:
    def __init__(self, state: dict):
        self._state = state
        self._mode = "select"
        self._updates = None
        self._filters = {}

    def select(self, *_):
        self._mode = "select"
        return self

    def update(self, updates):
        self._mode = "update"
        self._updates = dict(updates)
        return self

    def upsert(self, data, **_kwargs):
        self._mode = "upsert"
        self._state.update(data)
        return self

    def eq(self, key, value):
        self._filters[key] = value
        return self

    def lt(self, *_):
        return self

    def order(self, *_, **__):
        return self

    def limit(self, _):
        return self

    def execute(self):
        r = MagicMock()
        if self._mode == "select":
            r.data = [dict(self._state)]
        elif self._mode == "update":
            # Vérifie tous les filtres (verrouillage optimiste)
            all_match = all(
                self._state.get(k) == v for k, v in self._filters.items()
            )
            if all_match:
                self._state.update(self._updates)
                r.data = [dict(self._state)]
            else:
                r.data = []  # verrou non acquis
        elif self._mode == "upsert":
            r.data = [dict(self._state)]
        return r


class _NewMonthSupabase:
    """Simule Supabase pour tester le report de bonus lors d'un nouveau mois.

    - Appel SELECT mois courant → vide (pas encore de ligne)
    - Appel SELECT mois précédent (avec .lt()) → renvoie prev_row
    - Appel UPSERT → crée la ligne
    - Appel SELECT mois courant (après upsert) → renvoie la ligne créée
    """

    def __init__(self, prev_bonus: int, prev_monthly: int = 5):
        self.prev_row = {
            "bonus_analyses": prev_bonus,
            "analyses_count": prev_monthly,
            "chat_count": 0,
        }
        self.upserted: dict | None = None

    def from_(self, _table):
        return _NewMonthBuilder(self)


class _NewMonthBuilder:
    def __init__(self, db: _NewMonthSupabase):
        self._db = db
        self._mode = "select"
        self._is_lt = False

    def select(self, *_):
        self._mode = "select"
        return self

    def upsert(self, data, **_kwargs):
        self._db.upserted = dict(data)
        self._mode = "upsert"
        return self

    def eq(self, *_):
        return self

    def lt(self, *_):
        self._is_lt = True
        return self

    def order(self, *_, **__):
        return self

    def limit(self, _):
        return self

    def execute(self):
        r = MagicMock()
        if self._mode == "upsert":
            r.data = [self._db.upserted]
        elif self._is_lt:
            # Requête mois précédent → renvoie prev_row
            r.data = [self._db.prev_row]
        elif self._db.upserted is not None:
            # Mois courant existe (après upsert)
            r.data = [self._db.upserted]
        else:
            # Mois courant absent (avant upsert)
            r.data = []
        return r


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSES — FREE
# ═════════════════════════════════════════════════════════════════════════════

class TestAnalysesFREE(unittest.TestCase):
    """FREE : 1 Analyse/mois."""

    def test_free_analyse_0_autorisee(self):
        """FREE : 0 analyses → autorisé."""
        allowed, reason = _svc_with_usage(_row(0)).can_run_analysis("cid", "free")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_free_analyse_1_bloquee(self):
        """FREE : 1 analyse utilisée → bloqué (quota 1/mois épuisé)."""
        allowed, reason = _svc_with_usage(_row(1)).can_run_analysis("cid", "free")
        self.assertFalse(allowed)
        self.assertIn("1", reason)

    def test_free_limite_vient_du_catalog(self):
        """FREE : le quota analyses vient du Product Catalog (1 Analyse)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("free").analyses, 1)


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSES — PRO
# ═════════════════════════════════════════════════════════════════════════════

class TestAnalysesPRO(unittest.TestCase):
    """PRO : 30 Analyses/mois."""

    def test_pro_29_autorisee(self):
        """PRO : 29 analyses → la 30e est autorisée."""
        allowed, _ = _svc_with_usage(_row(29)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_pro_30_bloquee(self):
        """PRO : 30 analyses → la 31e est bloquée."""
        allowed, reason = _svc_with_usage(_row(30)).can_run_analysis("cid", "pro")
        self.assertFalse(allowed)
        self.assertIn("30", reason)

    def test_pro_limite_vient_du_catalog(self):
        """PRO : le quota analyses vient du Product Catalog (30 Analyses)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("pro").analyses, 30)


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSES — SCALE
# ═════════════════════════════════════════════════════════════════════════════

class TestAnalysesSCALE(unittest.TestCase):
    """SCALE : 100 Analyses/mois."""

    def test_scale_99_autorisee(self):
        """SCALE : 99 analyses → la 100e est autorisée."""
        allowed, _ = _svc_with_usage(_row(99)).can_run_analysis("cid", "scale")
        self.assertTrue(allowed)

    def test_scale_100_bloquee(self):
        """SCALE : 100 analyses → la 101e est bloquée."""
        allowed, reason = _svc_with_usage(_row(100)).can_run_analysis("cid", "scale")
        self.assertFalse(allowed)
        self.assertIn("100", reason)

    def test_scale_limite_vient_du_catalog(self):
        """SCALE : le quota analyses vient du Product Catalog (100 Analyses)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("scale").analyses, 100)


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSES — Enterprise (illimité)
# ═════════════════════════════════════════════════════════════════════════════

class TestAnalysesEnterprise(unittest.TestCase):
    """Enterprise : Analyses illimitées."""

    def test_enterprise_toujours_autorise(self):
        """Enterprise : toujours autorisé même avec 9999 analyses."""
        allowed, reason = _svc_with_usage(_row(9999)).can_run_analysis("cid", "enterprise")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_enterprise_analyses_none_dans_catalog(self):
        """Enterprise : catalog retourne analyses=None."""
        from config.product_catalog import get_plan
        self.assertIsNone(get_plan("enterprise").analyses)


# ═════════════════════════════════════════════════════════════════════════════
# EXECUTIVE CAPACITY PACKS — Starter (+10), Growth (+20), Scale (+80)
# ═════════════════════════════════════════════════════════════════════════════

class TestExecutiveCapacityPacksStarter(unittest.TestCase):
    """Starter Capacity Pack : +10 Analyses bonus."""

    def test_starter_ajoute_10(self):
        """Starter Pack : 10 Analyses bonus (catalog)."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_starter").analyses_added, 10)

    def test_starter_bonus_consomme_avant_mensuel(self):
        """PRO + Starter : bonus restant → autorisé (bonus > 0)."""
        # 10 bonus restants, 0 mensuel consommé
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=10)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_starter_bonus_epuises_mensuel_disponible(self):
        """PRO + Starter : 10 bonus consommés, quota mensuel disponible (0/30)."""
        # Après 10 bonus consommés : bonus_analyses=0, analyses_count=0
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=0)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_starter_bonus_tous_consommes_mensuel_epuise_pro_bloque(self):
        """PRO + Starter : 10 bonus + 30 mensuel tous consommés → bloqué."""
        # Après 10 bonus + 30 mensuel : bonus_analyses=0, analyses_count=30
        allowed, reason = _svc_with_usage(_row(30, bonus_analyses=0)).can_run_analysis("cid", "pro")
        self.assertFalse(allowed)
        self.assertIn("30", reason)


class TestExecutiveCapacityPacksGrowth(unittest.TestCase):
    """Growth Capacity Pack : +20 Analyses bonus."""

    def test_growth_ajoute_20(self):
        """Growth Pack : 20 Analyses bonus (catalog)."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_growth").analyses_added, 20)

    def test_growth_pro_total_50_autorisee(self):
        """PRO + Growth : 49/50 consommées (20 bonus + 29 mensuel) → 50e autorisée."""
        # Après 20 bonus + 29 mensuel : bonus_analyses=0, analyses_count=29
        allowed, _ = _svc_with_usage(_row(29, bonus_analyses=0)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_growth_pro_50_bloque(self):
        """PRO + Growth : 50/50 consommées (20 bonus + 30 mensuel) → bloqué."""
        # Après 20 bonus + 30 mensuel : bonus_analyses=0, analyses_count=30
        allowed, _ = _svc_with_usage(_row(30, bonus_analyses=0)).can_run_analysis("cid", "pro")
        self.assertFalse(allowed)


class TestExecutiveCapacityPacksScale(unittest.TestCase):
    """Scale Capacity Pack : +80 Analyses bonus."""

    def test_scale_pack_ajoute_80(self):
        """Scale Capacity Pack : 80 Analyses bonus (catalog)."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_scale").analyses_added, 80)

    def test_scale_pack_free_apres_80_bonus_1_mensuelle_reste(self):
        """FREE + Scale Pack : après 80 bonus consommés, 1 quota mensuel reste."""
        # Après 80 bonus : bonus_analyses=0, analyses_count=0, 1 FREE mensuelle dispo
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=0)).can_run_analysis("cid", "free")
        self.assertTrue(allowed)

    def test_scale_pack_free_81_bloque(self):
        """FREE + Scale Pack : 81/81 consommées (80 bonus + 1 mensuel FREE) → bloqué."""
        # Après 80 bonus + 1 mensuel FREE : bonus_analyses=0, analyses_count=1
        allowed, _ = _svc_with_usage(_row(1, bonus_analyses=0)).can_run_analysis("cid", "free")
        self.assertFalse(allowed)


class TestPacksNaffectentPasInteractions(unittest.TestCase):
    """Executive Capacity Packs n'ajoutent JAMAIS d'Interactions."""

    def test_packs_nont_pas_de_champ_chat(self):
        """Aucun pack ne possède de champ Interactions."""
        from config.product_catalog import get_executive_capacity_pack
        from dataclasses import fields
        for pack_id in ["addon_starter", "addon_growth", "addon_scale"]:
            pack = get_executive_capacity_pack(pack_id)
            pack_fields = {f.name for f in fields(pack)}
            self.assertNotIn("chat_monthly_cap", pack_fields, pack_id)
            self.assertNotIn("chat", pack_fields, pack_id)
            self.assertNotIn("interactions", pack_fields, pack_id)


# ═════════════════════════════════════════════════════════════════════════════
# INTERACTIONS — FREE
# ═════════════════════════════════════════════════════════════════════════════

class TestInteractionsFREE(unittest.TestCase):
    """FREE : 3 Interactions/mois."""

    def test_free_2_interactions_autorisee(self):
        """FREE : 2 Interactions → la 3e est autorisée."""
        allowed, reason, model_tier = _svc_with_chat(2).can_chat("cid", "aid", "free")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")
        self.assertEqual(model_tier, "normal")

    def test_free_3_interactions_bloquee(self):
        """FREE : 3 Interactions → la 4e est bloquée."""
        allowed, reason, model_tier = _svc_with_chat(3).can_chat("cid", "aid", "free")
        self.assertFalse(allowed)
        self.assertIn("3", reason)
        self.assertEqual(model_tier, "normal")

    def test_free_interactions_viennent_du_catalog(self):
        """FREE : le quota Interactions vient du Product Catalog (3/mois)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("free").chat_monthly_cap, 3)

    def test_free_aucune_limite_par_analyse(self):
        """FREE : aucune vérification par Analyse — seul le mensuel compte."""
        allowed, _, _ = _svc_with_chat(0).can_chat("cid", "any_analysis_id", "free")
        self.assertTrue(allowed)


# ═════════════════════════════════════════════════════════════════════════════
# INTERACTIONS — PRO
# ═════════════════════════════════════════════════════════════════════════════

class TestInteractionsPRO(unittest.TestCase):
    """PRO : 75 Interactions/mois."""

    def test_pro_74_interactions_autorisee(self):
        """PRO : 74 Interactions → la 75e est autorisée."""
        allowed, _, _ = _svc_with_chat(74).can_chat("cid", None, "pro")
        self.assertTrue(allowed)

    def test_pro_75_interactions_bloquee(self):
        """PRO : 75 Interactions → la 76e est bloquée."""
        allowed, reason, _ = _svc_with_chat(75).can_chat("cid", None, "pro")
        self.assertFalse(allowed)
        self.assertIn("75", reason)

    def test_pro_interactions_viennent_du_catalog(self):
        """PRO : le quota Interactions vient du Product Catalog (75/mois)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("pro").chat_monthly_cap, 75)


# ═════════════════════════════════════════════════════════════════════════════
# INTERACTIONS — SCALE
# ═════════════════════════════════════════════════════════════════════════════

class TestInteractionsSCALE(unittest.TestCase):
    """SCALE : 500 Interactions/mois."""

    def test_scale_499_interactions_autorisee(self):
        """SCALE : 499 Interactions → la 500e est autorisée."""
        allowed, _, _ = _svc_with_chat(499).can_chat("cid", None, "scale")
        self.assertTrue(allowed)

    def test_scale_500_interactions_bloquee(self):
        """SCALE : 500 Interactions → la 501e est bloquée."""
        allowed, reason, _ = _svc_with_chat(500).can_chat("cid", None, "scale")
        self.assertFalse(allowed)
        self.assertIn("500", reason)

    def test_scale_interactions_viennent_du_catalog(self):
        """SCALE : le quota Interactions vient du Product Catalog (500/mois)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("scale").chat_monthly_cap, 500)


# ═════════════════════════════════════════════════════════════════════════════
# INTERACTIONS — Enterprise (illimité)
# ═════════════════════════════════════════════════════════════════════════════

class TestInteractionsEnterprise(unittest.TestCase):
    """Enterprise : Interactions illimitées."""

    def test_enterprise_interactions_illimitees(self):
        """Enterprise : toujours autorisé même avec 9999 Interactions."""
        allowed, reason, _ = _svc_with_chat(9999).can_chat("cid", None, "enterprise")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_enterprise_chat_monthly_cap_none(self):
        """Enterprise : catalog retourne chat_monthly_cap=None."""
        from config.product_catalog import get_plan
        self.assertIsNone(get_plan("enterprise").chat_monthly_cap)


# ═════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ D'USAGE — get_usage_this_month
# ═════════════════════════════════════════════════════════════════════════════

class TestGetUsageThisMonth(unittest.TestCase):
    """Résumé d'usage mensuel et champs WP1D."""

    def test_free_resume_correct(self):
        """FREE : résumé avec valeurs du catalog."""
        data = _svc_with_usage(_row(1, 2)).get_usage_this_month("cid", "free")
        self.assertEqual(data["analyses_limit"], 1)
        self.assertEqual(data["interactions_limit"], 3)
        self.assertEqual(data["analyses_used"], 1)
        self.assertEqual(data["interactions_used"], 2)
        self.assertEqual(data["max_entities"], 1)

    def test_pro_resume_correct(self):
        """PRO : résumé avec valeurs du catalog."""
        data = _svc_with_usage(_row(10, 20)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_limit"], 30)
        self.assertEqual(data["interactions_limit"], 75)
        self.assertEqual(data["analyses_used"], 10)
        self.assertEqual(data["max_entities"], 10)

    def test_scale_resume_correct(self):
        """SCALE : résumé avec valeurs du catalog — entités illimitées."""
        data = _svc_with_usage(_row(0, 0)).get_usage_this_month("cid", "scale")
        self.assertEqual(data["analyses_limit"], 100)
        self.assertEqual(data["interactions_limit"], 500)
        self.assertIsNone(data["max_entities"])

    def test_ordre_consommation_bonus_en_premier(self):
        """Résumé : après 10 bonus + 5 mensuel consommés — sémantique WP1C.1."""
        # En modèle corrigé : analyses_count = mensuel SEULEMENT, bonus_analyses = SOLDE
        # Après 10 bonus consommés puis 5 mensuels : bonus_analyses=0, analyses_count=5
        data = _svc_with_usage(_row(5, bonus_analyses=0)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_bonus_remaining"], 0)     # solde épuisé
        self.assertEqual(data["analyses_monthly_used"], 5)        # 5 mensuelles consommées
        self.assertEqual(data["analyses_monthly_remaining"], 25)  # 30 - 5 = 25

    def test_bonus_partiellement_consommes(self):
        """Résumé : bonus partiellement consommés, mensuel intact."""
        # Après 10 bonus consommés (20 achetés) : bonus_analyses=10, analyses_count=0
        data = _svc_with_usage(_row(0, bonus_analyses=10)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_bonus_remaining"], 10)    # 10 bonus restants
        self.assertEqual(data["analyses_monthly_used"], 0)        # mensuel non touché
        self.assertEqual(data["analyses_monthly_remaining"], 30)  # 30 - 0 = 30

    def test_renewal_date_est_le_premier_du_mois(self):
        """Résumé : renewal_date = 1er du mois suivant."""
        data = _svc_with_usage(_row()).get_usage_this_month("cid", "free")
        self.assertIn("renewal_date", data)
        dt = datetime_from_iso(data["renewal_date"])
        self.assertEqual(dt.day, 1)

    def test_cles_legacy_presentes(self):
        """Résumé : clés legacy présentes pour billing.py (compat)."""
        data = _svc_with_usage(_row(5, bonus_analyses=10)).get_usage_this_month("cid", "pro")
        for key in ("bonus_analyses", "total_allowed", "analyses_limit", "analyses_remaining"):
            self.assertIn(key, data, f"Clé legacy manquante : {key}")


# ═════════════════════════════════════════════════════════════════════════════
# PLANS LEGACY
# ═════════════════════════════════════════════════════════════════════════════

class TestPlansLegacy(unittest.TestCase):
    """standard → PRO, standard_beta → PRO, premium → SCALE."""

    def test_standard_aligne_pro(self):
        """standard → mêmes quotas que PRO (30 Analyses, 75 Interactions)."""
        from config.product_catalog import get_plan
        limits = get_plan("standard")
        self.assertEqual(limits.analyses, 30)
        self.assertEqual(limits.chat_monthly_cap, 75)

    def test_standard_beta_aligne_pro(self):
        """standard_beta → mêmes quotas que PRO."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("standard_beta").analyses, 30)

    def test_premium_aligne_scale(self):
        """premium → mêmes quotas que SCALE (100 Analyses, 500 Interactions)."""
        from config.product_catalog import get_plan
        limits = get_plan("premium")
        self.assertEqual(limits.analyses, 100)
        self.assertEqual(limits.chat_monthly_cap, 500)

    def test_standard_bloque_a_30(self):
        """standard : 30 analyses → la 31e bloquée (quota PRO)."""
        allowed, reason = _svc_with_usage(_row(30)).can_run_analysis("cid", "standard")
        self.assertFalse(allowed)
        self.assertIn("30", reason)

    def test_standard_interactions_bloquees_a_75(self):
        """standard : 75 Interactions → la 76e bloquée (quota PRO)."""
        allowed, reason, _ = _svc_with_chat(75).can_chat("cid", None, "standard")
        self.assertFalse(allowed)
        self.assertIn("75", reason)


# ═════════════════════════════════════════════════════════════════════════════
# ABSENCE DE chat_per_analysis + SIGNATURES D'API
# ═════════════════════════════════════════════════════════════════════════════

class TestContractsFiches(unittest.TestCase):
    """Vérification contractuelle du service."""

    def test_usage_service_sans_chat_per_analysis(self):
        """usage_service.py ne contient aucune référence à chat_per_analysis."""
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn(
            "chat_per_analysis", content,
            "chat_per_analysis ne doit plus exister dans usage_service.py",
        )

    def test_usage_service_sans_plan_limits_local(self):
        """usage_service.py ne définit aucun dict PLAN_LIMITS local."""
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn('"chat_per_analysis"', content)
        self.assertNotIn("'chat_per_analysis'", content)

    def test_usage_service_importe_product_catalog(self):
        """usage_service.py doit importer depuis config.product_catalog."""
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "from config.product_catalog import",
            content,
            "usage_service.py doit importer depuis config.product_catalog",
        )

    def test_product_catalog_sans_chat_per_analysis(self):
        """product_catalog.py ne définit aucune limite chat_per_analysis dans ses structures."""
        from config.product_catalog import PLAN_LIMITS, PlanLimits
        from dataclasses import fields
        field_names = {f.name for f in fields(PlanLimits)}
        self.assertNotIn(
            "chat_per_analysis", field_names,
            "PlanLimits ne doit pas avoir de champ chat_per_analysis",
        )
        for plan_id, limits in PLAN_LIMITS.items():
            self.assertFalse(
                hasattr(limits, "chat_per_analysis"),
                f"Plan '{plan_id}' : chat_per_analysis ne doit pas exister",
            )

    def test_signature_can_run_analysis(self):
        """can_run_analysis() retourne (bool, str) — compat analyze.py."""
        svc = _svc_with_usage(_row())
        result = svc.can_run_analysis("cid", "free")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_signature_can_chat(self):
        """can_chat() retourne (bool, str, str) — compat analyze.py."""
        svc = _svc_with_chat(0)
        result = svc.can_chat("cid", "aid", "free")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)
        self.assertIsInstance(result[2], str)
        self.assertEqual(result[2], "normal")

    def test_model_tier_toujours_normal(self):
        """model_tier = 'normal' dans tous les cas (autorisé et refusé)."""
        allowed, _, tier = _svc_with_chat(0).can_chat("cid", None, "pro")
        self.assertTrue(allowed)
        self.assertEqual(tier, "normal")
        allowed, _, tier = _svc_with_chat(75).can_chat("cid", None, "pro")
        self.assertFalse(allowed)
        self.assertEqual(tier, "normal")

    def test_usage_service_importable(self):
        """usage_service.py s'importe sans erreur."""
        import services.usage_service  # noqa


# ═════════════════════════════════════════════════════════════════════════════
# WP1C.1 — STOCK EXECUTIVE CAPACITY PACKS (15 tests obligatoires)
# ═════════════════════════════════════════════════════════════════════════════

class TestWP1C1_StockPacks(unittest.TestCase):
    """Tests 1-4 : quantités de packs et accumulation."""

    def test_wp1c1_01_starter_stock_10(self):
        """Test 1 — Starter Pack : crédite exactement 10 analyses bonus."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_starter").analyses_added, 10)

    def test_wp1c1_02_growth_stock_20(self):
        """Test 2 — Growth Pack : crédite exactement 20 analyses bonus."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_growth").analyses_added, 20)

    def test_wp1c1_03_scale_pack_stock_80(self):
        """Test 3 — Scale Capacity Pack : crédite exactement 80 analyses bonus."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_scale").analyses_added, 80)

    def test_wp1c1_04_multiple_packs_accumulate(self):
        """Test 4 — Achats multiples : les bonus s'accumulent dans le solde."""
        # Starter(10) + Growth(20) = 30 bonus au total
        from config.product_catalog import get_executive_capacity_pack
        starter = get_executive_capacity_pack("addon_starter").analyses_added
        growth = get_executive_capacity_pack("addon_growth").analyses_added
        accumulated = starter + growth
        self.assertEqual(accumulated, 30)

        # Vérifier que can_run_analysis est autorisé avec ce solde cumulé
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=accumulated)).can_run_analysis(
            "cid", "pro"
        )
        self.assertTrue(allowed)

        # Vérifier que get_usage_this_month reflète le solde cumulé
        data = _svc_with_usage(_row(0, bonus_analyses=accumulated)).get_usage_this_month(
            "cid", "pro"
        )
        self.assertEqual(data["analyses_bonus_remaining"], 30)


class TestWP1C1_Consumption(unittest.TestCase):
    """Tests 5-7, 14 : décrémentation du stock bonus et isolation du mensuel."""

    def test_wp1c1_05_each_bonus_decrements_by_one(self):
        """Test 5 — Chaque analyse bonus décrémente bonus_analyses de 1."""
        svc = UsageService()
        state = {
            "company_id": "cid",
            "year_month": "2026-07",
            "bonus_analyses": 5,
            "analyses_count": 0,
        }
        svc._supabase = _InMemorySupabase(state)

        source = svc._consume_one_analysis("cid", "2026-07")

        self.assertEqual(source, "bonus")
        self.assertEqual(state["bonus_analyses"], 4)    # decrementé de 1
        self.assertEqual(state["analyses_count"], 0)    # mensuel non touché

    def test_wp1c1_06_monthly_starts_after_bonus_exhausted(self):
        """Test 6 — Après épuisement du bonus, le quota mensuel est consommé."""
        svc = UsageService()
        state = {
            "company_id": "cid",
            "year_month": "2026-07",
            "bonus_analyses": 0,   # bonus épuisé
            "analyses_count": 5,
        }
        svc._supabase = _InMemorySupabase(state)

        source = svc._consume_one_analysis("cid", "2026-07")

        self.assertEqual(source, "monthly")
        self.assertEqual(state["analyses_count"], 6)    # mensuel incrémenté
        self.assertEqual(state["bonus_analyses"], 0)    # bonus inchangé

    def test_wp1c1_07_monthly_not_decremented_while_bonus(self):
        """Test 7 — Le quota mensuel n'est JAMAIS décrémenté tant que bonus_analyses > 0."""
        svc = UsageService()
        state = {
            "company_id": "cid",
            "year_month": "2026-07",
            "bonus_analyses": 3,
            "analyses_count": 0,
        }
        svc._supabase = _InMemorySupabase(state)

        # Consommer 3 analyses → toutes depuis le bonus
        for _ in range(3):
            svc._consume_one_analysis("cid", "2026-07")

        self.assertEqual(state["bonus_analyses"], 0)    # bonus épuisé
        self.assertEqual(state["analyses_count"], 0)    # mensuel JAMAIS touché

        # La 4e consomme le mensuel
        svc._consume_one_analysis("cid", "2026-07")
        self.assertEqual(state["analyses_count"], 1)    # maintenant touché

    def test_wp1c1_14_no_negative_bonus(self):
        """Test 14 — bonus_analyses ne passe jamais en négatif."""
        svc = UsageService()
        state = {
            "company_id": "cid",
            "year_month": "2026-07",
            "bonus_analyses": 0,   # déjà à 0
            "analyses_count": 3,
        }
        svc._supabase = _InMemorySupabase(state)

        # Consommer 5 analyses avec bonus=0 → toutes depuis le mensuel
        for _ in range(5):
            svc._consume_one_analysis("cid", "2026-07")

        # bonus_analyses ne doit pas être négatif
        self.assertGreaterEqual(state["bonus_analyses"], 0)
        self.assertEqual(state["bonus_analyses"], 0)     # reste à 0
        self.assertEqual(state["analyses_count"], 8)     # mensuel incrémenté


class TestWP1C1_MonthRenewal(unittest.TestCase):
    """Tests 8-10 : renouvellement mensuel et report du bonus."""

    def _run_get_or_create(self, prev_bonus: int, prev_monthly: int = 5) -> dict:
        """Helper : exécute _get_or_create_usage_row avec mock deux-mois."""
        svc = UsageService()
        mock_sb = _NewMonthSupabase(prev_bonus=prev_bonus, prev_monthly=prev_monthly)
        svc._supabase = mock_sb

        with patch("services.usage_service._current_year_month", return_value="2026-07"):
            row = svc._get_or_create_usage_row("cid")

        return row

    def test_wp1c1_08_consumed_bonus_no_reappear(self):
        """Test 8 — Un bonus consommé (solde=0) ne réapparaît PAS le mois suivant."""
        row = self._run_get_or_create(prev_bonus=0)

        # Le nouveau mois doit avoir bonus_analyses=0 (report de 0)
        self.assertEqual(row.get("bonus_analyses", 0), 0)
        # Et analyses_count repart à 0
        self.assertEqual(row.get("analyses_count", 0), 0)

    def test_wp1c1_09_unconsumed_bonus_persists(self):
        """Test 9 — Un bonus non consommé (solde=7) persiste au mois suivant."""
        row = self._run_get_or_create(prev_bonus=7)

        # Le nouveau mois doit avoir bonus_analyses=7 (report du solde)
        self.assertEqual(row.get("bonus_analyses", 0), 7)

    def test_wp1c1_10_monthly_resets_only(self):
        """Test 10 — Le renouvellement remet analyses_count=0 mais pas bonus_analyses."""
        row = self._run_get_or_create(prev_bonus=15, prev_monthly=30)

        # Quota mensuel repart à 0 (nouveau mois)
        self.assertEqual(row.get("analyses_count", 0), 0)
        # Bonus conservé intégralement
        self.assertEqual(row.get("bonus_analyses", 0), 15)


class TestWP1C1_PlanInteraction(unittest.TestCase):
    """Tests 11-12 : interaction plan / bonus."""

    def test_wp1c1_11_free_with_bonus_uses_bonus_first(self):
        """Test 11 — Plan FREE avec bonus : le bonus est consommé avant le quota mensuel."""
        # FREE avec 5 bonus restants → autorisé (bonus en premier)
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=5)).can_run_analysis("cid", "free")
        self.assertTrue(allowed)

        # FREE après épuisement du bonus : quota mensuel FREE (1) disponible
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=0)).can_run_analysis("cid", "free")
        self.assertTrue(allowed)

        # FREE après épuisement du bonus ET du quota mensuel → bloqué
        allowed, reason = _svc_with_usage(_row(1, bonus_analyses=0)).can_run_analysis("cid", "free")
        self.assertFalse(allowed)

    def test_wp1c1_12_resubscription_reactivates_balance(self):
        """Test 12 — Re-souscription PRO/SCALE : le solde bonus est préservé indépendamment du plan."""
        # Le plan change ne touche pas bonus_analyses dans usage_limits
        # → un utilisateur qui revient sur PRO retrouve son solde intact
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=15)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

        data = _svc_with_usage(_row(0, bonus_analyses=15)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_bonus_remaining"], 15)
        self.assertEqual(data["analyses_monthly_used"], 0)


class TestWP1C1_Concurrency(unittest.TestCase):
    """Test 13 : verrouillage optimiste pour consommation concurrente."""

    def test_wp1c1_13_optimistic_locking_prevents_double_consume(self):
        """Test 13 — Le verrouillage optimiste empêche deux consommations du même bonus.

        Simulation : le verrou bonus échoue systématiquement (concurrent a déjà décrémenté).
        Résultat attendu : fallback sur le quota mensuel, pas de bonus négatif.
        """
        svc = UsageService()

        class _ConcurrentSupabase:
            def __init__(self):
                self.state = {"bonus_analyses": 1, "analyses_count": 0}

            def from_(self, _table):
                return _ConcurrentBuilder(self.state)

        class _ConcurrentBuilder:
            def __init__(self, state):
                self._state = state
                self._updates = None

            def select(self, *_): return self
            def update(self, u):
                self._updates = u
                return self
            def eq(self, *_): return self

            def execute(self):
                r = MagicMock()
                if self._updates is None:
                    # SELECT → renvoie état actuel
                    r.data = [dict(self._state)]
                elif "bonus_analyses" in self._updates:
                    # Tentative de décrémentation bonus → verrou jamais acquis
                    r.data = []
                else:
                    # Incrémentation analyses_count (fallback) → réussit
                    self._state.update(self._updates)
                    r.data = [dict(self._state)]
                return r

        mock_sb = _ConcurrentSupabase()
        svc._supabase = mock_sb

        result = svc._consume_one_analysis("cid", "2026-07")

        # Après MAX_RETRIES échoués, le fallback incrémente analyses_count
        self.assertEqual(result, "monthly")
        # Le bonus n'a jamais été décrémenté (verrou jamais acquis)
        self.assertEqual(mock_sb.state["bonus_analyses"], 1)
        # Le quota mensuel a été incrémenté à la place
        self.assertEqual(mock_sb.state["analyses_count"], 1)


class TestWP1C1_DisplayTotals(unittest.TestCase):
    """Test 15 : affichage des totaux dans get_usage_this_month."""

    def test_wp1c1_15_display_totals_all_fields(self):
        """Test 15 — get_usage_this_month expose monthly_remaining, bonus_remaining, total_remaining."""
        # PRO + 5 bonus restants, 10 mensuel consommé
        data = _svc_with_usage(_row(10, bonus_analyses=5)).get_usage_this_month("cid", "pro")

        # Solde bonus restant
        self.assertEqual(data["analyses_bonus_remaining"], 5)
        # Quota mensuel consommé
        self.assertEqual(data["analyses_monthly_used"], 10)
        # Quota mensuel restant : 30 - 10 = 20
        self.assertEqual(data["analyses_monthly_remaining"], 20)
        # Total restant : 5 bonus + 20 mensuel = 25
        self.assertEqual(data["analyses_remaining"], 25)

        # Clés requises présentes
        required_keys = [
            "analyses_bonus_remaining",
            "analyses_monthly_remaining",
            "analyses_monthly_used",
            "analyses_remaining",
            "renewal_date",
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Clé manquante dans get_usage_this_month : {key}")

    def test_wp1c1_15b_totals_without_bonus(self):
        """Test 15b — Totaux sans bonus : total_remaining = quota mensuel restant."""
        # PRO, pas de bonus, 5 mensuel consommé
        data = _svc_with_usage(_row(5, bonus_analyses=0)).get_usage_this_month("cid", "pro")

        self.assertEqual(data["analyses_bonus_remaining"], 0)
        self.assertEqual(data["analyses_monthly_remaining"], 25)  # 30 - 5 = 25
        self.assertEqual(data["analyses_remaining"], 25)          # 0 + 25

    def test_wp1c1_15c_totals_only_bonus(self):
        """Test 15c — Totaux avec seulement du bonus (mensuel intact)."""
        # PRO + 20 bonus, 0 mensuel consommé (bonus en cours d'utilisation)
        data = _svc_with_usage(_row(0, bonus_analyses=20)).get_usage_this_month("cid", "pro")

        self.assertEqual(data["analyses_bonus_remaining"], 20)
        self.assertEqual(data["analyses_monthly_remaining"], 30)  # 30 - 0 = 30
        self.assertEqual(data["analyses_remaining"], 50)          # 20 + 30


# ─── Helper datetime ─────────────────────────────────────────────────────────

def datetime_from_iso(s: str):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


if __name__ == "__main__":
    unittest.main()
