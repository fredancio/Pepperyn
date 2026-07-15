"""
tests/test_product_catalog.py

PEPPERYN PRODUCT CONTRACT — WP1A
Product Catalog : Tests de conformité

Ce fichier est le gardien permanent de PEPPERYN_DECISIONS_V1.md (WP0.75).
Il doit passer à chaque modification du Product Catalog.
Si un test échoue, aucune migration de consommateur (WP1B/WP2) ne peut commencer.

Tests couverts (20 cas) :
  Plans actifs       : FREE, PRO, SCALE (quotas, prix, plans commerciaux)
  Capacity Packs     : Starter, Growth, Scale (prix, analyses, isolation chat)
  Interactions       : quota mensuel uniquement, aucune limite par Analyse
  Legacy             : standard, standard_beta, premium, power, enterprise
  Robustesse         : identifiants inconnus, import sans Stripe, validation

Référence : PEPPERYN_DECISIONS_V1.md · ADR_001_PRODUCT_CATALOG.md
            Release 1.0 — WP1A — 13 juillet 2026
"""

import os
import sys
import pytest

# ─── Import path ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Garantir qu'aucune variable Stripe ne pollue l'environnement de test
for _env in ("STRIPE_PRICE_PRO", "STRIPE_PRICE_SCALE",
             "STRIPE_PRICE_ADDON_STARTER", "STRIPE_PRICE_ADDON_GROWTH",
             "STRIPE_PRICE_ADDON_SCALE"):
    os.environ.pop(_env, None)

from config.product_catalog import (
    # Constantes
    PLAN_LIMITS,
    PLAN_PRICES,
    EXECUTIVE_CAPACITY_PACKS,
    STRIPE_PRICE_IDS,
    PLAN_DISPLAY_NAMES,
    COMMERCIAL_PLAN_IDS,
    EXECUTIVE_CAPACITY_PACK_IDS,
    LEGACY_PLAN_ALIASES,
    LEGACY_INTERNAL_PLANS,
    # Fonctions
    get_plan,
    get_commercial_plans,
    get_executive_capacity_pack,
    validate_stripe_price_ids,
)


# ═════════════════════════════════════════════════════════════════════════════
# PLANS COMMERCIAUX ACTIFS
# ═════════════════════════════════════════════════════════════════════════════

class TestPlanFree:
    """Test 1 — FREE : 0 centime, 1 Analyse, 3 Interactions, 1 Entité."""

    def test_free_price_is_zero(self):
        assert PLAN_PRICES["free"] == 0

    def test_free_analyses_quota(self):
        assert PLAN_LIMITS["free"].analyses == 1

    def test_free_chat_monthly_cap(self):
        assert PLAN_LIMITS["free"].chat_monthly_cap == 3

    def test_free_max_entities(self):
        assert PLAN_LIMITS["free"].max_entities == 1

    def test_free_get_plan(self):
        limits = get_plan("free")
        assert limits.analyses == 1
        assert limits.chat_monthly_cap == 3
        assert limits.max_entities == 1


class TestPlanPro:
    """Test 2 — PRO : 14 900 centimes, 30 Analyses, 75 Interactions, 10 Entités."""

    def test_pro_price(self):
        assert PLAN_PRICES["pro"] == 14_900

    def test_pro_analyses_quota(self):
        assert PLAN_LIMITS["pro"].analyses == 30

    def test_pro_chat_monthly_cap(self):
        assert PLAN_LIMITS["pro"].chat_monthly_cap == 75

    def test_pro_max_entities(self):
        assert PLAN_LIMITS["pro"].max_entities == 10

    def test_pro_get_plan(self):
        limits = get_plan("pro")
        assert limits.analyses == 30
        assert limits.chat_monthly_cap == 75
        assert limits.max_entities == 10


class TestPlanScale:
    """Test 3 — SCALE : 34 900 centimes, 100 Analyses, 500 Interactions, Entités illimitées."""

    def test_scale_price(self):
        assert PLAN_PRICES["scale"] == 34_900

    def test_scale_analyses_quota(self):
        assert PLAN_LIMITS["scale"].analyses == 100

    def test_scale_chat_monthly_cap(self):
        assert PLAN_LIMITS["scale"].chat_monthly_cap == 500

    def test_scale_max_entities_is_none_meaning_unlimited(self):
        """None représente 'illimité' pour max_entities sur SCALE."""
        assert PLAN_LIMITS["scale"].max_entities is None

    def test_scale_get_plan(self):
        limits = get_plan("scale")
        assert limits.analyses == 100
        assert limits.chat_monthly_cap == 500
        assert limits.max_entities is None


class TestCommercialPlansInterface:
    """Test 4 — Seuls FREE, PRO et SCALE sont retournés comme Plans commerciaux."""

    def test_commercial_plan_ids_exact(self):
        assert set(COMMERCIAL_PLAN_IDS) == {"free", "pro", "scale"}

    def test_get_commercial_plans_returns_three(self):
        plans = get_commercial_plans()
        assert len(plans) == 3

    def test_get_commercial_plans_ids(self):
        plan_ids = {p["id"] for p in get_commercial_plans()}
        assert plan_ids == {"free", "pro", "scale"}

    def test_get_commercial_plans_no_legacy(self):
        plan_ids = {p["id"] for p in get_commercial_plans()}
        legacy = {"standard", "standard_beta", "premium", "power", "enterprise"}
        assert plan_ids.isdisjoint(legacy)

    def test_get_commercial_plans_structure(self):
        required_keys = {
            "id", "name", "label", "price_cents",
            "analyses_per_month", "chat_per_month",
            "max_entities", "stripe_price_id",
        }
        for plan in get_commercial_plans():
            assert required_keys.issubset(plan.keys()), (
                f"Clés manquantes dans le plan '{plan.get('id')}': "
                f"{required_keys - plan.keys()}"
            )

    def test_commercial_plans_values(self):
        plans = {p["id"]: p for p in get_commercial_plans()}
        assert plans["free"]["price_cents"]        == 0
        assert plans["free"]["analyses_per_month"] == 1
        assert plans["free"]["chat_per_month"]     == 3
        assert plans["pro"]["price_cents"]         == 14_900
        assert plans["pro"]["analyses_per_month"]  == 30
        assert plans["pro"]["chat_per_month"]      == 75
        assert plans["scale"]["price_cents"]       == 34_900
        assert plans["scale"]["analyses_per_month"] == 100
        assert plans["scale"]["chat_per_month"]    == 500


# ═════════════════════════════════════════════════════════════════════════════
# EXECUTIVE CAPACITY PACKS
# ═════════════════════════════════════════════════════════════════════════════

class TestStarterCapacityPack:
    """Test 5 — Starter : 3 900 centimes, +10 Analyses."""

    def test_starter_price(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_starter"].price_cents == 3_900

    def test_starter_analyses_added(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_starter"].analyses_added == 10

    def test_starter_display_name(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_starter"].display_name == "Starter Capacity Pack"

    def test_starter_get_pack(self):
        pack = get_executive_capacity_pack("addon_starter")
        assert pack.price_cents == 3_900
        assert pack.analyses_added == 10


class TestGrowthCapacityPack:
    """Test 6 — Growth : 7 900 centimes, +20 Analyses."""

    def test_growth_price(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_growth"].price_cents == 7_900

    def test_growth_analyses_added(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_growth"].analyses_added == 20

    def test_growth_display_name(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_growth"].display_name == "Growth Capacity Pack"

    def test_growth_get_pack(self):
        pack = get_executive_capacity_pack("addon_growth")
        assert pack.price_cents == 7_900
        assert pack.analyses_added == 20


class TestScaleCapacityPack:
    """Test 7 — Scale Capacity Pack : 23 900 centimes, +80 Analyses."""

    def test_scale_pack_price(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_scale"].price_cents == 23_900

    def test_scale_pack_analyses_added(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_scale"].analyses_added == 80

    def test_scale_pack_display_name(self):
        assert EXECUTIVE_CAPACITY_PACKS["addon_scale"].display_name == "Scale Capacity Pack"

    def test_scale_pack_get_pack(self):
        pack = get_executive_capacity_pack("addon_scale")
        assert pack.price_cents == 23_900
        assert pack.analyses_added == 80


class TestCapacityPacksNoChatProperty:
    """Test 8 — Aucun Executive Capacity Pack ne contient de propriété liée aux Interactions."""

    @pytest.mark.parametrize("pack_id", ["addon_starter", "addon_growth", "addon_scale"])
    def test_pack_has_no_chat_attribute(self, pack_id):
        pack = get_executive_capacity_pack(pack_id)
        # Les packs n'ajoutent jamais d'Interactions — aucun champ chat ne doit exister
        assert not hasattr(pack, "chat_added"),          f"{pack_id} : 'chat_added' interdit"
        assert not hasattr(pack, "chat_monthly_cap"),    f"{pack_id} : 'chat_monthly_cap' interdit"
        assert not hasattr(pack, "interactions_added"),  f"{pack_id} : 'interactions_added' interdit"
        assert not hasattr(pack, "chat_per_analysis"),   f"{pack_id} : 'chat_per_analysis' interdit"

    @pytest.mark.parametrize("pack_id", ["addon_starter", "addon_growth", "addon_scale"])
    def test_pack_dataclass_fields_whitelist(self, pack_id):
        """Vérifie que les champs de l'objet correspondent exactement aux champs attendus."""
        import dataclasses
        pack = get_executive_capacity_pack(pack_id)
        field_names = {f.name for f in dataclasses.fields(pack)}
        expected = {"pack_id", "display_name", "analyses_added", "price_cents", "stripe_price_id_env"}
        assert field_names == expected, (
            f"{pack_id} : champs inattendus {field_names - expected} ou manquants {expected - field_names}"
        )


class TestCapacityPacksNotPlans:
    """Test 9 — Aucun Executive Capacity Pack n'est considéré comme un Plan."""

    def test_pack_ids_disjoint_from_plan_ids(self):
        assert set(EXECUTIVE_CAPACITY_PACK_IDS).isdisjoint(set(COMMERCIAL_PLAN_IDS))

    def test_packs_not_in_plan_limits(self):
        for pack_id in EXECUTIVE_CAPACITY_PACK_IDS:
            assert pack_id not in PLAN_LIMITS, (
                f"'{pack_id}' ne doit pas figurer dans PLAN_LIMITS"
            )

    def test_packs_not_in_plan_prices(self):
        for pack_id in EXECUTIVE_CAPACITY_PACK_IDS:
            assert pack_id not in PLAN_PRICES, (
                f"'{pack_id}' ne doit pas figurer dans PLAN_PRICES"
            )


# ═════════════════════════════════════════════════════════════════════════════
# INTERACTIONS — RÈGLE CONTRACTUELLE
# ═════════════════════════════════════════════════════════════════════════════

class TestInteractionsRule:
    """Tests 10, 11, 12 — Interactions : mensuel uniquement, aucune limite par Analyse."""

    def test_10_no_chat_per_analysis_key_in_plan_limits(self):
        """Test 10 — chat_per_analysis est absent de tous les PlanLimits."""
        import dataclasses
        for plan_id, limits in PLAN_LIMITS.items():
            field_names = {f.name for f in dataclasses.fields(limits)}
            assert "chat_per_analysis" not in field_names, (
                f"Plan '{plan_id}' : 'chat_per_analysis' est interdit dans PlanLimits"
            )

    def test_10_plan_limits_fields_whitelist(self):
        """Les PlanLimits ne contiennent que les champs officiels."""
        import dataclasses
        for plan_id, limits in PLAN_LIMITS.items():
            field_names = {f.name for f in dataclasses.fields(limits)}
            allowed = {"analyses", "chat_monthly_cap", "max_entities"}
            forbidden_found = field_names - allowed
            assert not forbidden_found, (
                f"Plan '{plan_id}' : champs interdits dans PlanLimits : {forbidden_found}"
            )

    def test_11_interactions_defined_monthly_only(self):
        """Test 11 — Les Interactions sont définies uniquement par chat_monthly_cap."""
        for plan_id, limits in PLAN_LIMITS.items():
            # Le seul champ autorisé pour les Interactions est chat_monthly_cap
            assert hasattr(limits, "chat_monthly_cap"), (
                f"Plan '{plan_id}' : chat_monthly_cap manquant"
            )

    def test_11_get_commercial_plans_chat_key(self):
        """get_commercial_plans() utilise 'chat_per_month' (mensuel), pas 'chat_per_analysis'."""
        for plan in get_commercial_plans():
            assert "chat_per_month" in plan
            assert "chat_per_analysis" not in plan
            assert "interactions_per_analysis" not in plan

    def test_12_scale_chat_cap_is_not_unlimited(self):
        """Test 12 — SCALE n'est pas illimité en Interactions (500/mois)."""
        assert PLAN_LIMITS["scale"].chat_monthly_cap == 500
        assert PLAN_LIMITS["scale"].chat_monthly_cap is not None

    def test_12_no_plan_has_unlimited_chat_except_enterprise(self):
        """Seul Enterprise peut avoir chat_monthly_cap=None (illimité)."""
        for plan_id, limits in PLAN_LIMITS.items():
            if plan_id == "enterprise":
                continue  # Enterprise seul autorisé à être illimité
            assert limits.chat_monthly_cap is not None, (
                f"Plan '{plan_id}' : chat_monthly_cap ne peut pas être None "
                f"(illimité interdit sauf Enterprise)"
            )


# ═════════════════════════════════════════════════════════════════════════════
# PLANS LEGACY
# ═════════════════════════════════════════════════════════════════════════════

class TestLegacyPlans:
    """Tests 13, 14, 15, 16 — Plans legacy et plans internes hérités."""

    def test_13_standard_aligned_on_pro(self):
        """Test 13 — standard est aligné sur PRO."""
        assert PLAN_LIMITS["standard"].analyses        == PLAN_LIMITS["pro"].analyses
        assert PLAN_LIMITS["standard"].chat_monthly_cap == PLAN_LIMITS["pro"].chat_monthly_cap
        assert PLAN_LIMITS["standard"].max_entities    == PLAN_LIMITS["pro"].max_entities

    def test_13_standard_beta_aligned_on_pro(self):
        """Test 13 — standard_beta est aligné sur PRO."""
        assert PLAN_LIMITS["standard_beta"].analyses        == PLAN_LIMITS["pro"].analyses
        assert PLAN_LIMITS["standard_beta"].chat_monthly_cap == PLAN_LIMITS["pro"].chat_monthly_cap
        assert PLAN_LIMITS["standard_beta"].max_entities    == PLAN_LIMITS["pro"].max_entities

    def test_14_premium_aligned_on_scale(self):
        """Test 14 — premium est aligné sur SCALE."""
        assert PLAN_LIMITS["premium"].analyses        == PLAN_LIMITS["scale"].analyses
        assert PLAN_LIMITS["premium"].chat_monthly_cap == PLAN_LIMITS["scale"].chat_monthly_cap
        assert PLAN_LIMITS["premium"].max_entities    == PLAN_LIMITS["scale"].max_entities

    def test_13_legacy_aliases_map(self):
        """LEGACY_PLAN_ALIASES documente l'alignement standard/premium → pro/scale."""
        assert LEGACY_PLAN_ALIASES["standard"]      == "pro"
        assert LEGACY_PLAN_ALIASES["standard_beta"] == "pro"
        assert LEGACY_PLAN_ALIASES["premium"]       == "scale"

    def test_15_no_legacy_in_commercial_interface(self):
        """Test 15 — Aucun Plan legacy n'est retourné par get_commercial_plans()."""
        plan_ids = {p["id"] for p in get_commercial_plans()}
        legacy = {"standard", "standard_beta", "premium"}
        assert plan_ids.isdisjoint(legacy)

    def test_15_no_legacy_in_commercial_plan_ids(self):
        legacy = {"standard", "standard_beta", "premium"}
        assert set(COMMERCIAL_PLAN_IDS).isdisjoint(legacy)

    def test_16_power_is_in_legacy_internal_plans(self):
        """Test 16 — power est répertorié comme plan interne non commercial."""
        assert "power" in LEGACY_INTERNAL_PLANS

    def test_16_enterprise_is_in_legacy_internal_plans(self):
        """Test 16 — enterprise est répertorié comme plan interne non commercial."""
        assert "enterprise" in LEGACY_INTERNAL_PLANS

    def test_16_power_not_in_commercial_plan_ids(self):
        assert "power" not in COMMERCIAL_PLAN_IDS

    def test_16_enterprise_not_in_commercial_plan_ids(self):
        assert "enterprise" not in COMMERCIAL_PLAN_IDS

    def test_16_power_no_stripe_price_id(self):
        """Test 16 — power n'a pas de Stripe Price ID."""
        assert "power" not in STRIPE_PRICE_IDS

    def test_16_enterprise_no_stripe_price_id(self):
        """Test 16 — enterprise n'a pas de Stripe Price ID."""
        assert "enterprise" not in STRIPE_PRICE_IDS

    def test_16_power_not_in_plan_prices(self):
        """Test 16 — power n'a pas de prix commercial défini."""
        assert "power" not in PLAN_PRICES

    def test_16_enterprise_not_in_plan_prices(self):
        """Test 16 — enterprise n'a pas de prix commercial défini."""
        assert "enterprise" not in PLAN_PRICES

    def test_16_power_not_commercial_in_display(self):
        """Test 16 — Si power est dans PLAN_DISPLAY_NAMES, il doit être non commercial."""
        if "power" in PLAN_DISPLAY_NAMES:
            assert not PLAN_DISPLAY_NAMES["power"].is_commercial

    def test_16_power_not_returned_by_get_commercial_plans(self):
        plan_ids = {p["id"] for p in get_commercial_plans()}
        assert "power" not in plan_ids
        assert "enterprise" not in plan_ids


# ═════════════════════════════════════════════════════════════════════════════
# ROBUSTESSE
# ═════════════════════════════════════════════════════════════════════════════

class TestRobustness:
    """Tests 17, 18, 19, 20 — Comportement face aux erreurs et environnements variés."""

    def test_17_get_plan_unknown_raises_key_error(self):
        """Test 17 — Un identifiant de Plan inconnu lève KeyError."""
        with pytest.raises(KeyError):
            get_plan("unknown_plan")

    def test_17_get_plan_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_plan("")

    def test_17_get_plan_power_is_in_catalog_for_compat(self):
        """power est accessible via get_plan() pour compat code hérité."""
        limits = get_plan("power")
        assert limits is not None

    def test_18_get_pack_unknown_raises_key_error(self):
        """Test 18 — Un identifiant de pack inconnu lève KeyError."""
        with pytest.raises(KeyError):
            get_executive_capacity_pack("unknown_pack")

    def test_18_get_pack_plan_id_raises_key_error(self):
        """Un identifiant de Plan ne doit pas être accepté comme pack."""
        with pytest.raises(KeyError):
            get_executive_capacity_pack("pro")

    def test_18_get_pack_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_executive_capacity_pack("")

    def test_19_module_importable_without_stripe_vars(self):
        """Test 19 — Le catalogue est importable sans variables Stripe configurées."""
        # Les variables Stripe ont été supprimées en tête de fichier.
        # L'import a déjà réussi (ce test tourne). On vérifie juste que
        # les valeurs sont None (pas une exception).
        assert STRIPE_PRICE_IDS["pro"]   is None
        assert STRIPE_PRICE_IDS["scale"] is None

    def test_19_stripe_price_ids_structure_without_vars(self):
        """Sans variables d'env, tous les Price IDs payants sont None."""
        for key in ("pro", "scale", "addon_starter", "addon_growth", "addon_scale"):
            assert STRIPE_PRICE_IDS[key] is None, (
                f"STRIPE_PRICE_IDS['{key}'] devrait être None sans variable d'env"
            )

    def test_19_free_stripe_price_id_always_none(self):
        """FREE n'a jamais de Stripe Price ID, même avec des variables configurées."""
        assert STRIPE_PRICE_IDS["free"] is None

    def test_20_validate_stripe_price_ids_returns_all_false_without_vars(self):
        """Test 20 — validate_stripe_price_ids() détecte les Price IDs manquants."""
        result = validate_stripe_price_ids()
        # Sans variables Stripe, tout doit être False
        for product_id, is_configured in result.items():
            assert not is_configured, (
                f"'{product_id}' devrait être non configuré sans variable Stripe"
            )

    def test_20_validate_stripe_price_ids_covers_all_payable(self):
        """Test 20 — validate_stripe_price_ids() couvre tous les produits payants."""
        result = validate_stripe_price_ids()
        expected_products = {"pro", "scale", "addon_starter", "addon_growth", "addon_scale"}
        assert set(result.keys()) == expected_products

    def test_20_validate_stripe_price_ids_with_env(self, monkeypatch):
        """Test 20 — validate_stripe_price_ids() retourne True quand les vars sont présentes."""
        monkeypatch.setenv("STRIPE_PRICE_PRO",           "price_test_pro")
        monkeypatch.setenv("STRIPE_PRICE_SCALE",         "price_test_scale")
        monkeypatch.setenv("STRIPE_PRICE_ADDON_STARTER", "price_test_starter")
        monkeypatch.setenv("STRIPE_PRICE_ADDON_GROWTH",  "price_test_growth")
        monkeypatch.setenv("STRIPE_PRICE_ADDON_SCALE",   "price_test_addon_scale")
        result = validate_stripe_price_ids()
        assert all(result.values()), f"Certains Price IDs non détectés : {result}"

    def test_20_pack_stripe_price_id_property_with_env(self, monkeypatch):
        """Test 20 — La property stripe_price_id sur ExecutiveCapacityPack fonctionne."""
        monkeypatch.setenv("STRIPE_PRICE_ADDON_GROWTH", "price_test_growth_123")
        pack = get_executive_capacity_pack("addon_growth")
        assert pack.stripe_price_id == "price_test_growth_123"

    def test_20_pack_stripe_price_id_property_without_env(self):
        """Test 20 — stripe_price_id retourne None si la variable est absente."""
        pack = get_executive_capacity_pack("addon_starter")
        assert pack.stripe_price_id is None


# ═════════════════════════════════════════════════════════════════════════════
# CONTRÔLES ADDITIONNELS D'INTÉGRITÉ GLOBALE
# ═════════════════════════════════════════════════════════════════════════════

class TestGlobalIntegrity:
    """Contrôles transversaux garantissant la cohérence interne du catalogue."""

    def test_all_commercial_plans_have_price(self):
        for plan_id in COMMERCIAL_PLAN_IDS:
            assert plan_id in PLAN_PRICES, f"Prix manquant pour '{plan_id}'"

    def test_all_commercial_plans_have_limits(self):
        for plan_id in COMMERCIAL_PLAN_IDS:
            assert plan_id in PLAN_LIMITS, f"Limites manquantes pour '{plan_id}'"

    def test_all_commercial_plans_have_display_name(self):
        for plan_id in COMMERCIAL_PLAN_IDS:
            assert plan_id in PLAN_DISPLAY_NAMES, f"Nom d'affichage manquant pour '{plan_id}'"

    def test_all_commercial_plans_are_marked_commercial(self):
        for plan_id in COMMERCIAL_PLAN_IDS:
            assert PLAN_DISPLAY_NAMES[plan_id].is_commercial

    def test_all_pack_ids_in_executive_capacity_packs(self):
        for pack_id in EXECUTIVE_CAPACITY_PACK_IDS:
            assert pack_id in EXECUTIVE_CAPACITY_PACKS

    def test_executive_capacity_packs_no_duplicates(self):
        assert len(EXECUTIVE_CAPACITY_PACK_IDS) == len(set(EXECUTIVE_CAPACITY_PACK_IDS))

    def test_commercial_plan_ids_no_duplicates(self):
        assert len(COMMERCIAL_PLAN_IDS) == len(set(COMMERCIAL_PLAN_IDS))

    def test_plan_limits_are_frozen(self):
        """Les PlanLimits sont immutables (frozen dataclass)."""
        limits = get_plan("pro")
        with pytest.raises((AttributeError, TypeError)):
            limits.analyses = 999  # type: ignore[misc]

    def test_executive_capacity_packs_are_frozen(self):
        """Les ExecutiveCapacityPack sont immutables (frozen dataclass)."""
        pack = get_executive_capacity_pack("addon_starter")
        with pytest.raises((AttributeError, TypeError)):
            pack.analyses_added = 999  # type: ignore[misc]

    def test_free_plan_no_stripe_price_id(self):
        """FREE n'a pas de Stripe Price ID dans STRIPE_PRICE_IDS."""
        assert STRIPE_PRICE_IDS.get("free") is None

    def test_scale_analyses_less_than_old_incorrect_value(self):
        """Régression : SCALE doit avoir 100 Analyses, pas 250 (ancienne valeur incorrecte)."""
        assert PLAN_LIMITS["scale"].analyses == 100
        assert PLAN_LIMITS["scale"].analyses != 250

    def test_pro_analyses_not_old_incorrect_value(self):
        """Régression : PRO doit avoir 30 Analyses, pas 15 (ancienne valeur incorrecte)."""
        assert PLAN_LIMITS["pro"].analyses == 30
        assert PLAN_LIMITS["pro"].analyses != 15

    def test_pro_chat_not_old_incorrect_value(self):
        """Régression : PRO doit avoir 75 Interactions/mois, pas 300 (ancienne valeur)."""
        assert PLAN_LIMITS["pro"].chat_monthly_cap == 75
        assert PLAN_LIMITS["pro"].chat_monthly_cap != 300

    def test_scale_chat_not_none_old_incorrect_value(self):
        """Régression : SCALE doit avoir 500 Interactions/mois, pas None (illimité)."""
        assert PLAN_LIMITS["scale"].chat_monthly_cap == 500
        assert PLAN_LIMITS["scale"].chat_monthly_cap is not None

    def test_addon_growth_analyses_not_old_incorrect_value(self):
        """Régression : addon_growth doit ajouter 20 Analyses, pas 50."""
        assert EXECUTIVE_CAPACITY_PACKS["addon_growth"].analyses_added == 20
        assert EXECUTIVE_CAPACITY_PACKS["addon_growth"].analyses_added != 50

    def test_addon_scale_analyses_not_old_incorrect_value(self):
        """Régression : addon_scale doit ajouter 80 Analyses, pas 200."""
        assert EXECUTIVE_CAPACITY_PACKS["addon_scale"].analyses_added == 80
        assert EXECUTIVE_CAPACITY_PACKS["addon_scale"].analyses_added != 200

    def test_pro_price_not_old_incorrect_value(self):
        """Régression : PRO doit coûter 149€ (14900 centimes), pas 59€ (5900)."""
        assert PLAN_PRICES["pro"] == 14_900
        assert PLAN_PRICES["pro"] != 5_900
