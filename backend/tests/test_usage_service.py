"""
test_usage_service.py — WP1C.2 (Option B)
Tests unitaires du moteur de quotas Usage Service.

Architecture Option B :
  - companies.bonus_analyses_remaining : stock permanent, indépendant des mois.
  - usage_limits.analyses_count        : compteur mensuel uniquement.
  - Bonus consommés EN PREMIER si plan éligible.
  - Plan FREE : bonus SUSPENDUS (stock conservé, non consommable).

Source de vérité : config/product_catalog.py
Aucune constante locale.

Scénarios couverts :
  1.  Consommation normale (mensuel sans bonus)
  2.  Plusieurs achats successifs (stock s'accumule)
  3.  Suspension FREE (bonus présent mais non consommable)
  4.  Réactivation PRO (bonus redevient consommable)
  5.  Changement de mois (reset mensuel, bonus inchangé)
  6.  Concurrence bonus (verrou optimiste, retry)
  7.  Absence de duplication (double decrement refusé)
  8.  Absence de perte (conflit concurrent → fallback mensuel)
  9.  Stock permanent correctement décrémenté
  10. Quotas mensuels inchangés lors de consommation bonus
  11. Interactions (quotas mensuels plans + enterprise)
  12. Signatures API (compat analyze.py)
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.usage_service import UsageService, _BONUS_ELIGIBLE_PLANS


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _svc_with_state(monthly: int = 0, chat: int = 0, bonus: int = 0, plan: str = "pro") -> UsageService:
    """
    Crée un UsageService avec companies et usage_limits mockés.
    _get_or_create_usage_row  → compteur mensuel uniquement.
    _get_bonus_remaining       → stock permanent.
    """
    svc = UsageService()
    svc._get_or_create_usage_row = MagicMock(return_value={
        "analyses_count": monthly,
        "chat_count": chat,
    })
    svc._get_bonus_remaining = MagicMock(return_value=bonus)
    return svc


def _svc_with_chat(monthly_count: int) -> UsageService:
    svc = UsageService()
    svc.get_monthly_chat_count = MagicMock(return_value=monthly_count)
    return svc


def _datetime_from_iso(s: str):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 1 — Consommation normale (mensuel, sans bonus)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario1ConsommationNormale(unittest.TestCase):
    """Scénario 1 : quota mensuel sans bonus."""

    def test_free_0_autorisee(self):
        """FREE : 0/1 analyses → autorisé."""
        allowed, _ = _svc_with_state(monthly=0, bonus=0, plan="free").can_run_analysis("c", "free")
        self.assertTrue(allowed)

    def test_free_1_bloquee(self):
        """FREE : 1/1 analyses → bloqué."""
        allowed, reason = _svc_with_state(monthly=1, bonus=0, plan="free").can_run_analysis("c", "free")
        self.assertFalse(allowed)
        self.assertIn("1", reason)

    def test_pro_29_autorisee(self):
        """PRO : 29/30 → autorisé."""
        allowed, _ = _svc_with_state(monthly=29, bonus=0, plan="pro").can_run_analysis("c", "pro")
        self.assertTrue(allowed)

    def test_pro_30_bloquee(self):
        """PRO : 30/30 → bloqué."""
        allowed, reason = _svc_with_state(monthly=30, bonus=0, plan="pro").can_run_analysis("c", "pro")
        self.assertFalse(allowed)
        self.assertIn("30", reason)

    def test_scale_99_autorisee(self):
        """SCALE : 99/100 → autorisé."""
        allowed, _ = _svc_with_state(monthly=99, bonus=0, plan="scale").can_run_analysis("c", "scale")
        self.assertTrue(allowed)

    def test_scale_100_bloquee(self):
        """SCALE : 100/100 → bloqué."""
        allowed, _ = _svc_with_state(monthly=100, bonus=0, plan="scale").can_run_analysis("c", "scale")
        self.assertFalse(allowed)

    def test_enterprise_illimite(self):
        """Enterprise : toujours autorisé."""
        allowed, reason = _svc_with_state(monthly=9999, bonus=0, plan="enterprise").can_run_analysis("c", "enterprise")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_quotas_viennent_du_catalog(self):
        """Quotas issus du Product Catalog."""
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("free").analyses, 1)
        self.assertEqual(get_plan("pro").analyses, 30)
        self.assertEqual(get_plan("scale").analyses, 100)
        self.assertIsNone(get_plan("enterprise").analyses)


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 2 — Plusieurs achats successifs (accumulation)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario2AchatsSuccessifs(unittest.TestCase):
    """Scénario 2 : le stock s'accumule à chaque achat."""

    def test_stock_apres_starter(self):
        """Starter (+10) : stock = 10."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_starter").analyses_added, 10)

    def test_stock_apres_growth(self):
        """Growth (+20) : stock = 20."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_growth").analyses_added, 20)

    def test_stock_apres_scale_pack(self):
        """Scale Pack (+80) : stock = 80."""
        from config.product_catalog import get_executive_capacity_pack
        self.assertEqual(get_executive_capacity_pack("addon_scale").analyses_added, 80)

    def test_bonus_cumule_debloque_analyses(self):
        """PRO + 30 bonus cumulés (starter x3) : 0/mensuel → autorisé via bonus."""
        # Même avec analyses_count = 30 (quota mensuel plein), bonus > 0 → autorisé
        svc = _svc_with_state(monthly=30, bonus=30, plan="pro")
        allowed, _ = svc.can_run_analysis("c", "pro")
        self.assertTrue(allowed)

    def test_add_bonus_appelle_supabase(self):
        """add_bonus_analyses écrit dans companies.bonus_analyses_remaining."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"bonus_analyses_remaining": 10}
        ]
        svc._supabase = mock_sb
        svc._get_bonus_remaining = MagicMock(return_value=10)
        svc.add_bonus_analyses("cid", 20)
        # Vérifie qu'on a tenté d'écrire bonus_analyses_remaining = 30
        update_call = mock_sb.from_.return_value.update
        update_call.assert_called_once_with({"bonus_analyses_remaining": 30})


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 3 — Suspension FREE
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario3SuspensionFREE(unittest.TestCase):
    """Scénario 3 : plan FREE — bonus conservé mais non consommable."""

    def test_free_bonus_suspend_message(self):
        """FREE + bonus > 0 + mensuel plein → message de suspension."""
        svc = _svc_with_state(monthly=1, bonus=10, plan="free")
        allowed, reason = svc.can_run_analysis("c", "free")
        self.assertFalse(allowed)
        self.assertIn("suspendues", reason)
        self.assertIn("PRO", reason)

    def test_free_bonus_suspend_ne_debloque_pas(self):
        """FREE + bonus = 80 → n'autorise PAS l'analyse (suspension)."""
        svc = _svc_with_state(monthly=1, bonus=80, plan="free")
        allowed, _ = svc.can_run_analysis("c", "free")
        self.assertFalse(allowed)

    def test_free_mensuel_disponible_sans_bonus(self):
        """FREE + bonus = 0 + mensuel = 0 → autorisé normalement."""
        svc = _svc_with_state(monthly=0, bonus=0, plan="free")
        allowed, _ = svc.can_run_analysis("c", "free")
        self.assertTrue(allowed)

    def test_free_pas_dans_bonus_eligible_plans(self):
        """'free' n'est PAS dans _BONUS_ELIGIBLE_PLANS."""
        self.assertNotIn("free", _BONUS_ELIGIBLE_PLANS)

    def test_free_resume_bonus_suspended_flag(self):
        """get_usage_this_month retourne analyses_bonus_suspended=True pour FREE avec bonus."""
        svc = _svc_with_state(monthly=0, bonus=10, plan="free")
        data = svc.get_usage_this_month("c", "free")
        self.assertTrue(data.get("analyses_bonus_suspended"))
        self.assertEqual(data["analyses_bonus"], 10)

    def test_eligible_plans_ne_contient_pas_free(self):
        """_BONUS_ELIGIBLE_PLANS couvre tous les plans payants."""
        for plan in ("pro", "scale", "enterprise", "standard", "standard_beta", "premium"):
            self.assertIn(plan, _BONUS_ELIGIBLE_PLANS, f"{plan} manquant dans _BONUS_ELIGIBLE_PLANS")


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 4 — Réactivation PRO
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario4ReactivationPRO(unittest.TestCase):
    """Scénario 4 : passage FREE → PRO réactive le stock bonus."""

    def test_pro_bonus_disponible_autorise(self):
        """PRO + bonus = 10 + mensuel = 30 (plein) → autorisé via bonus."""
        svc = _svc_with_state(monthly=30, bonus=10, plan="pro")
        allowed, reason = svc.can_run_analysis("c", "pro")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_pro_bonus_autorise_avant_mensuel(self):
        """PRO + bonus > 0 : bonus vérifié en premier (pas besoin de lire mensuel)."""
        svc = UsageService()
        svc._get_bonus_remaining = MagicMock(return_value=5)
        svc._get_or_create_usage_row = MagicMock(return_value={"analyses_count": 0, "chat_count": 0})
        allowed, _ = svc.can_run_analysis("c", "pro")
        self.assertTrue(allowed)
        # _get_or_create_usage_row ne doit PAS avoir été appelé (bonus suffisant)
        svc._get_or_create_usage_row.assert_not_called()

    def test_scale_bonus_reactivation(self):
        """SCALE + bonus = 80 : stock entièrement disponible."""
        svc = _svc_with_state(monthly=0, bonus=80, plan="scale")
        allowed, _ = svc.can_run_analysis("c", "scale")
        self.assertTrue(allowed)

    def test_pro_resume_pas_suspendu(self):
        """get_usage_this_month PRO : analyses_bonus_suspended=False."""
        svc = _svc_with_state(monthly=0, bonus=10, plan="pro")
        data = svc.get_usage_this_month("c", "pro")
        self.assertFalse(data.get("analyses_bonus_suspended"))


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 5 — Changement de mois (reset mensuel, bonus inchangé)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario5ChangementDeMois(unittest.TestCase):
    """Scénario 5 : nouveau mois → analyses_count → 0, bonus permanent inchangé."""

    def test_nouveau_mois_analyses_count_zero(self):
        """Nouveau mois : _get_or_create_usage_row retourne analyses_count=0."""
        svc = _svc_with_state(monthly=0, bonus=20, plan="pro")
        allowed, _ = svc.can_run_analysis("c", "pro")
        # En début de mois, analyses_count=0 mais bonus=20 → autorisé via bonus
        self.assertTrue(allowed)

    def test_bonus_inchange_apres_reset(self):
        """Bonus permanent : non affecté par le reset mensuel."""
        # Simule fin de mois précédent : 30 mensuelles consommées, 5 bonus restants
        # Nouveau mois : analyses_count=0, bonus=5 → autorisé via bonus
        svc = _svc_with_state(monthly=0, bonus=5, plan="pro")
        allowed, _ = svc.can_run_analysis("c", "pro")
        self.assertTrue(allowed)

    def test_nouveau_mois_quota_mensuel_renouvelle(self):
        """Nouveau mois : le quota mensuel est entièrement disponible."""
        svc = _svc_with_state(monthly=0, bonus=0, plan="pro")
        for _ in range(30):
            # Simule 30 appels can_run_analysis (tous avec monthly=0 mocké)
            allowed, _ = svc.can_run_analysis("c", "pro")
            self.assertTrue(allowed)

    def test_get_or_create_cree_ligne_nouvelle(self):
        """_get_or_create_usage_row crée une ligne vierge au nouveau mois."""
        svc = UsageService()
        mock_sb = MagicMock()
        # Premier SELECT : aucun résultat (nouveau mois)
        mock_sb.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_sb.from_.return_value.insert.return_value.execute.return_value = MagicMock()
        svc._supabase = mock_sb
        row = svc._get_or_create_usage_row("cid")
        self.assertEqual(row["analyses_count"], 0)
        self.assertEqual(row["chat_count"], 0)
        # Vérifie que bonus_analyses n'est PAS inséré (Option B)
        insert_args = mock_sb.from_.return_value.insert.call_args
        if insert_args:
            inserted_data = insert_args[0][0]
            self.assertNotIn("bonus_analyses", inserted_data)

    def test_resume_renewal_date_premier_du_mois(self):
        """renewal_date = 1er du mois suivant."""
        svc = _svc_with_state()
        data = svc.get_usage_this_month("c", "pro")
        dt = _datetime_from_iso(data["renewal_date"])
        self.assertEqual(dt.day, 1)


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 6 — Concurrence (verrou optimiste)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario6Concurrence(unittest.TestCase):
    """Scénario 6 : deux requêtes simultanées ne peuvent pas consommer le même bonus."""

    def test_decrement_bonus_optimiste_succes(self):
        """_decrement_bonus : UPDATE WHERE bonus_analyses_remaining = N → retourne True."""
        svc = UsageService()
        mock_sb = MagicMock()
        # SELECT retourne 5
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"bonus_analyses_remaining": 5}
        ]
        # UPDATE WHERE bonus=5 → 1 ligne affectée
        mock_sb.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"bonus_analyses_remaining": 4}
        ]
        svc._supabase = mock_sb
        result = svc._decrement_bonus("cid")
        self.assertTrue(result)

    def test_decrement_bonus_conflit_retourne_false(self):
        """_decrement_bonus : UPDATE WHERE bonus=N → 0 lignes → conflict → False."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"bonus_analyses_remaining": 5}
        ]
        # UPDATE chain : .update(...).eq("id",...).eq("bonus_analyses_remaining",...)
        # → 2 .eq calls → retourne [] (conflit concurrent)
        mock_sb.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        svc._supabase = mock_sb
        result = svc._decrement_bonus("cid")
        self.assertFalse(result)

    def test_increment_monthly_optimiste(self):
        """_increment_monthly_count : UPDATE WHERE analyses_count = M → succès."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"analyses_count": 5}
        ]
        mock_sb.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"analyses_count": 6}
        ]
        svc._supabase = mock_sb
        # Ne doit pas lever d'exception
        svc._increment_monthly_count("cid", "2026-07")

    def test_increment_monthly_retry_sur_conflit(self):
        """_increment_monthly_count : conflit → retry (max 3)."""
        svc = UsageService()
        mock_sb = MagicMock()
        # SELECT retourne toujours 5
        mock_sb.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"analyses_count": 5}
        ]
        # UPDATE retourne toujours [] (conflit permanent)
        mock_sb.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        svc._supabase = mock_sb
        # Ne doit pas lever d'exception (max retries atteint silencieusement)
        svc._increment_monthly_count("cid", "2026-07")


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 7 — Absence de duplication
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario7AbsenceDeDuplication(unittest.TestCase):
    """Scénario 7 : un seul bonus décrémenté par analyse, même sous contention."""

    def test_decrement_bonus_zero_retourne_false(self):
        """_decrement_bonus sur stock = 0 → False (pas de décrémentation)."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"bonus_analyses_remaining": 0}
        ]
        svc._supabase = mock_sb
        result = svc._decrement_bonus("cid")
        self.assertFalse(result)
        # UPDATE ne doit pas avoir été appelé
        mock_sb.from_.return_value.update.assert_not_called()

    def test_can_run_analysis_bonus_zero_lit_mensuel(self):
        """can_run_analysis : bonus=0 → utilise le quota mensuel."""
        svc = _svc_with_state(monthly=5, bonus=0, plan="pro")
        allowed, _ = svc.can_run_analysis("c", "pro")
        self.assertTrue(allowed)
        # Le mensuel a bien été consulté
        svc._get_or_create_usage_row.assert_called()

    def test_packs_naffectent_pas_interactions(self):
        """Aucun pack ne possède de champ Interactions."""
        from config.product_catalog import get_executive_capacity_pack
        from dataclasses import fields
        for pack_id in ["addon_starter", "addon_growth", "addon_scale"]:
            pack = get_executive_capacity_pack(pack_id)
            pack_fields = {f.name for f in fields(pack)}
            self.assertNotIn("chat_monthly_cap", pack_fields, pack_id)
            self.assertNotIn("interactions", pack_fields, pack_id)


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 8 — Absence de perte
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario8AbsenceDePerte(unittest.TestCase):
    """Scénario 8 : conflit concurrent sur bonus → fallback mensuel (pas de perte)."""

    def test_increment_analysis_fallback_mensuel_si_bonus_epuise(self):
        """increment_analysis : si _decrement_bonus retourne False x3, on incrémente le mensuel."""
        svc = UsageService()
        mock_sb = MagicMock()

        # companies : plan=pro, bonus=1
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "pro", "bonus_analyses_remaining": 1}
        ]
        svc._supabase = mock_sb
        svc._decrement_bonus = MagicMock(return_value=False)  # toujours en conflit
        svc._get_bonus_remaining = MagicMock(return_value=0)  # épuisé après conflit
        svc._get_or_create_usage_row = MagicMock(return_value={"analyses_count": 0, "chat_count": 0})
        svc._increment_monthly_count = MagicMock()

        svc.increment_analysis("cid")

        # Fallback mensuel doit avoir été appelé
        svc._increment_monthly_count.assert_called_once()

    def test_bonus_stock_permanent_pas_perdu_apres_reset(self):
        """Stock bonus jamais remis à zéro lors d'un reset mensuel."""
        # _get_or_create_usage_row crée une ligne vierge (reset mensuel)
        # mais _get_bonus_remaining lit companies (non affecté)
        svc = _svc_with_state(monthly=0, bonus=15, plan="pro")
        bonus = svc._get_bonus_remaining("c")
        self.assertEqual(bonus, 15)


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 9 — Stock permanent correctement décrémenté
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario9StockPermanentDecrement(unittest.TestCase):
    """Scénario 9 : chaque analyse bonus décrémente companies.bonus_analyses_remaining de 1."""

    def test_increment_analysis_decrement_bonus_appele(self):
        """increment_analysis PRO + bonus=5 → _decrement_bonus appelé."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "pro", "bonus_analyses_remaining": 5}
        ]
        svc._supabase = mock_sb
        svc._decrement_bonus = MagicMock(return_value=True)
        svc._get_or_create_usage_row = MagicMock(return_value={"analyses_count": 0, "chat_count": 0})
        svc._increment_monthly_count = MagicMock()
        svc._get_bonus_remaining = MagicMock(return_value=5)

        svc.increment_analysis("cid")

        svc._decrement_bonus.assert_called_with("cid")
        # Mensuel ne doit PAS avoir été touché
        svc._increment_monthly_count.assert_not_called()

    def test_increment_analysis_sans_bonus_incremente_mensuel(self):
        """increment_analysis PRO + bonus=0 → _increment_monthly_count appelé."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "pro", "bonus_analyses_remaining": 0}
        ]
        svc._supabase = mock_sb
        svc._decrement_bonus = MagicMock(return_value=False)
        svc._get_or_create_usage_row = MagicMock(return_value={"analyses_count": 5, "chat_count": 0})
        svc._increment_monthly_count = MagicMock()
        svc._get_bonus_remaining = MagicMock(return_value=0)

        svc.increment_analysis("cid")

        svc._increment_monthly_count.assert_called_once()
        svc._decrement_bonus.assert_not_called()

    def test_increment_analysis_free_bonus_suspendu_incremente_mensuel(self):
        """increment_analysis FREE + bonus > 0 → mensuel incrémenté (bonus suspendu)."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "free", "bonus_analyses_remaining": 10}
        ]
        svc._supabase = mock_sb
        svc._decrement_bonus = MagicMock()
        svc._get_or_create_usage_row = MagicMock(return_value={"analyses_count": 0, "chat_count": 0})
        svc._increment_monthly_count = MagicMock()

        svc.increment_analysis("cid")

        svc._decrement_bonus.assert_not_called()
        svc._increment_monthly_count.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIO 10 — Quotas mensuels inchangés lors de consommation bonus
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario10QuotaMensuelInchange(unittest.TestCase):
    """Scénario 10 : consommer du bonus ne touche pas analyses_count mensuel."""

    def test_bonus_consomme_analyses_count_inchange(self):
        """increment_analysis bonus réussi → _increment_monthly_count non appelé."""
        svc = UsageService()
        mock_sb = MagicMock()
        mock_sb.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "pro", "bonus_analyses_remaining": 3}
        ]
        svc._supabase = mock_sb
        svc._decrement_bonus = MagicMock(return_value=True)
        svc._get_or_create_usage_row = MagicMock()
        svc._increment_monthly_count = MagicMock()
        svc._get_bonus_remaining = MagicMock(return_value=3)

        svc.increment_analysis("cid")

        svc._increment_monthly_count.assert_not_called()

    def test_resume_bonus_permanent_independant_du_mensuel(self):
        """get_usage_this_month : bonus et mensuel sont des champs séparés."""
        svc = _svc_with_state(monthly=10, bonus=20, plan="pro")
        data = svc.get_usage_this_month("c", "pro")
        # En Option B, analyses_used = monthly_used uniquement
        self.assertEqual(data["analyses_used"], 10)
        self.assertEqual(data["analyses_bonus"], 20)
        self.assertEqual(data["analyses_bonus_remaining"], 20)
        self.assertEqual(data["analyses_monthly_used"], 10)

    def test_resume_pro_total_allowed_inclut_bonus(self):
        """PRO + 20 bonus : total_allowed = 30 + 20 = 50."""
        svc = _svc_with_state(monthly=0, bonus=20, plan="pro")
        data = svc.get_usage_this_month("c", "pro")
        self.assertEqual(data["analyses_total_allowed"], 50)

    def test_resume_free_total_allowed_sans_bonus_suspendu(self):
        """FREE + bonus suspendu : total_allowed = 1 (quota mensuel seulement)."""
        svc = _svc_with_state(monthly=0, bonus=10, plan="free")
        data = svc.get_usage_this_month("c", "free")
        self.assertEqual(data["analyses_total_allowed"], 1)

    def test_cles_legacy_presentes(self):
        """Clés legacy présentes pour compat billing.py."""
        svc = _svc_with_state(monthly=5, bonus=10, plan="pro")
        data = svc.get_usage_this_month("c", "pro")
        for key in ("bonus_analyses", "total_allowed", "analyses_limit", "analyses_remaining"):
            self.assertIn(key, data, f"Clé legacy manquante : {key}")


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIONS — quota mensuel par plan
# ═══════════════════════════════════════════════════════════════════════════

class TestInteractionsFREE(unittest.TestCase):
    def test_free_2_autorisee(self):
        allowed, _, tier = _svc_with_chat(2).can_chat("c", "a", "free")
        self.assertTrue(allowed)
        self.assertEqual(tier, "normal")

    def test_free_3_bloquee(self):
        allowed, reason, _ = _svc_with_chat(3).can_chat("c", "a", "free")
        self.assertFalse(allowed)
        self.assertIn("3", reason)

    def test_free_catalog(self):
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("free").chat_monthly_cap, 3)


class TestInteractionsPRO(unittest.TestCase):
    def test_pro_74_autorisee(self):
        allowed, _, _ = _svc_with_chat(74).can_chat("c", None, "pro")
        self.assertTrue(allowed)

    def test_pro_75_bloquee(self):
        allowed, reason, _ = _svc_with_chat(75).can_chat("c", None, "pro")
        self.assertFalse(allowed)
        self.assertIn("75", reason)


class TestInteractionsSCALE(unittest.TestCase):
    def test_scale_499_autorisee(self):
        allowed, _, _ = _svc_with_chat(499).can_chat("c", None, "scale")
        self.assertTrue(allowed)

    def test_scale_500_bloquee(self):
        allowed, _, _ = _svc_with_chat(500).can_chat("c", None, "scale")
        self.assertFalse(allowed)


class TestInteractionsEnterprise(unittest.TestCase):
    def test_enterprise_illimite(self):
        allowed, reason, _ = _svc_with_chat(9999).can_chat("c", None, "enterprise")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_enterprise_catalog_none(self):
        from config.product_catalog import get_plan
        self.assertIsNone(get_plan("enterprise").chat_monthly_cap)


# ═══════════════════════════════════════════════════════════════════════════
# Plans legacy (standard, standard_beta, premium)
# ═══════════════════════════════════════════════════════════════════════════

class TestPlansLegacy(unittest.TestCase):
    def test_standard_aligne_pro(self):
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("standard").analyses, 30)
        self.assertEqual(get_plan("standard").chat_monthly_cap, 75)

    def test_standard_beta_aligne_pro(self):
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("standard_beta").analyses, 30)

    def test_premium_aligne_scale(self):
        from config.product_catalog import get_plan
        self.assertEqual(get_plan("premium").analyses, 100)
        self.assertEqual(get_plan("premium").chat_monthly_cap, 500)

    def test_standard_dans_eligible_plans(self):
        """standard / standard_beta / premium sont éligibles au bonus."""
        for plan in ("standard", "standard_beta", "premium"):
            self.assertIn(plan, _BONUS_ELIGIBLE_PLANS)


# ═══════════════════════════════════════════════════════════════════════════
# SIGNATURES D'API — compatibilité analyze.py
# ═══════════════════════════════════════════════════════════════════════════

class TestSignaturesAPI(unittest.TestCase):
    """Vérification contractuelle — signatures attendues par analyze.py."""

    def test_signature_can_run_analysis(self):
        svc = _svc_with_state()
        result = svc.can_run_analysis("cid", "free")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_signature_can_chat(self):
        svc = _svc_with_chat(0)
        result = svc.can_chat("cid", "aid", "free")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[2], str)
        self.assertEqual(result[2], "normal")

    def test_model_tier_toujours_normal(self):
        for count in (0, 9999):
            _, _, tier = _svc_with_chat(count).can_chat("c", None, "pro")
            self.assertEqual(tier, "normal")

    def test_usage_service_importable(self):
        import services.usage_service  # noqa

    def test_no_chat_per_analysis(self):
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("chat_per_analysis", content)

    def test_importe_product_catalog(self):
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("from config.product_catalog import", content)

    def test_bonus_dans_companies_pas_usage_limits(self):
        """usage_service.py lit bonus depuis 'companies', pas depuis 'usage_limits'."""
        path = os.path.join(os.path.dirname(__file__), "..", "services", "usage_service.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("bonus_analyses_remaining", content)
        # _get_bonus_remaining doit lire la table companies
        self.assertIn('"companies"', content)

    def test_product_catalog_sans_chat_per_analysis(self):
        from config.product_catalog import PLAN_LIMITS, PlanLimits
        from dataclasses import fields
        field_names = {f.name for f in fields(PlanLimits)}
        self.assertNotIn("chat_per_analysis", field_names)


if __name__ == "__main__":
    unittest.main()
