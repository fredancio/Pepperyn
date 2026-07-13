"""
test_usage_service.py — WP1C
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
  Règle    : bonus consommés EN PREMIER, N'affectent JAMAIS les Interactions

Règle contractuelle :
  Il n'existe aucune limite d'Interactions par Analyse.
  Aucune référence à chat_per_analysis dans ce fichier ni dans usage_service.py.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.usage_service import UsageService


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _row(analyses_count=0, chat_count=0, bonus_analyses=0):
    """Construit une ligne usage_limits simulée."""
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
        """PRO + Starter : bonus consommés en premier — 0/40 → autorisé."""
        # 10 bonus, 0 utilisées → autorisé (quota total = 30 + 10 = 40)
        allowed, _ = _svc_with_usage(_row(0, bonus_analyses=10)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_starter_bonus_epuises_mensuel_disponible(self):
        """PRO + Starter : bonus épuisés (10/10) mais quota mensuel disponible."""
        # 10 utilisées = bonus épuisés, reste 20 mensuelles → autorisé
        allowed, _ = _svc_with_usage(_row(10, bonus_analyses=10)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_starter_total_40_pro_bloque(self):
        """PRO + Starter : 40/40 utilisées → bloqué (bonus mentionné)."""
        allowed, reason = _svc_with_usage(_row(40, bonus_analyses=10)).can_run_analysis("cid", "pro")
        self.assertFalse(allowed)
        self.assertIn("10", reason)  # bonus mentionné dans le message d'erreur


class TestExecutiveCapacityPacksGrowth(unittest.TestCase):
    """Growth Capacity Pack : +20 Analyses bonus."""

    def test_growth_ajoute_20(self):
        """Growth Pack : 20 Analyses bonus (catalog)."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_growth").analyses_added, 20)

    def test_growth_pro_total_50_autorise(self):
        """PRO + Growth : 49/50 utilisées → autorisé."""
        allowed, _ = _svc_with_usage(_row(49, bonus_analyses=20)).can_run_analysis("cid", "pro")
        self.assertTrue(allowed)

    def test_growth_pro_50_bloque(self):
        """PRO + Growth : 50/50 utilisées → bloqué."""
        allowed, _ = _svc_with_usage(_row(50, bonus_analyses=20)).can_run_analysis("cid", "pro")
        self.assertFalse(allowed)


class TestExecutiveCapacityPacksScale(unittest.TestCase):
    """Scale Capacity Pack : +80 Analyses bonus."""

    def test_scale_pack_ajoute_80(self):
        """Scale Capacity Pack : 80 Analyses bonus (catalog)."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_scale").analyses_added, 80)

    def test_scale_pack_free_total_81_autorise(self):
        """FREE + Scale Pack : 80/81 utilisées → autorisé."""
        allowed, _ = _svc_with_usage(_row(80, bonus_analyses=80)).can_run_analysis("cid", "free")
        self.assertTrue(allowed)

    def test_scale_pack_free_81_bloque(self):
        """FREE + Scale Pack : 81/81 utilisées → bloqué."""
        allowed, _ = _svc_with_usage(_row(81, bonus_analyses=80)).can_run_analysis("cid", "free")
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
        self.assertIn("3", reason)  # quota de 3 apparaît dans le message
        self.assertEqual(model_tier, "normal")

    def test_free_interactions_viennent_du_catalog(self):
        """FREE : le quota Interactions vient du Product Catalog (3/mois)."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("free").chat_monthly_cap, 3)

    def test_free_aucune_limite_par_analyse(self):
        """FREE : aucune vérification par Analyse — seul le mensuel compte."""
        # Même avec un analysis_id, pas de limite par Analyse
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
        """Résumé : bonus consommés en premier, mensuel ensuite."""
        # PRO + 10 bonus, 15 analyses utilisées
        # → 10 bonus consommés, 5 mensuelles consommées, 25 mensuelles restantes
        data = _svc_with_usage(_row(15, bonus_analyses=10)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_bonus_used"], 10)
        self.assertEqual(data["analyses_bonus_remaining"], 0)
        self.assertEqual(data["analyses_monthly_used"], 5)
        self.assertEqual(data["analyses_monthly_remaining"], 25)

    def test_bonus_partiellement_consommes(self):
        """Résumé : bonus partiellement consommés."""
        # PRO + 20 bonus, 10 analyses utilisées
        # → 10 bonus consommés, 10 restants, 0 mensuel consommé
        data = _svc_with_usage(_row(10, bonus_analyses=20)).get_usage_this_month("cid", "pro")
        self.assertEqual(data["analyses_bonus_used"], 10)
        self.assertEqual(data["analyses_bonus_remaining"], 10)
        self.assertEqual(data["analyses_monthly_used"], 0)
        self.assertEqual(data["analyses_monthly_remaining"], 30)

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
        # Le fichier ne doit pas contenir de dict littéral {"analyses": ... "chat_per_analysis": ...}
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
        # PlanLimits ne doit pas avoir de champ chat_per_analysis
        field_names = {f.name for f in fields(PlanLimits)}
        self.assertNotIn(
            "chat_per_analysis", field_names,
            "PlanLimits ne doit pas avoir de champ chat_per_analysis",
        )
        # Aucun objet PlanLimits ne doit avoir un attribut chat_per_analysis
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
        self.assertEqual(result[2], "normal")  # model_tier toujours "normal"

    def test_model_tier_toujours_normal(self):
        """model_tier = 'normal' dans tous les cas (autorisé et refusé)."""
        # Autorisé
        allowed, _, tier = _svc_with_chat(0).can_chat("cid", None, "pro")
        self.assertTrue(allowed)
        self.assertEqual(tier, "normal")
        # Refusé
        allowed, _, tier = _svc_with_chat(75).can_chat("cid", None, "pro")
        self.assertFalse(allowed)
        self.assertEqual(tier, "normal")

    def test_usage_service_importable(self):
        """usage_service.py s'importe sans erreur."""
        import services.usage_service  # noqa


# ─── Helper datetime ─────────────────────────────────────────────────────────

def datetime_from_iso(s: str):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


if __name__ == "__main__":
    unittest.main()
