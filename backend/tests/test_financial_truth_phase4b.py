"""
test_financial_truth_phase4b.py — Tests Phase 4B : Financial Truth Layer

Couvre :
  - Cas A–J du Design V3 FINAL
  - Méthodes QuantifiedImpact (recurring_annual_equivalent, run_rate_annual, one_time_amount, is_unresolved)
  - EconomicEventResolver (hash déterministe, registre, catégories)
  - Invariant UNKNOWN ≠ 0
  - Migration parallèle (quantified_impact coexiste avec annual_impact)
  - AnnualizationQuality (CERTIFIED vs RUN_RATE vs REFUSED)
  - Anti-double-comptage (economic_event_id)
  - Serialisation / désérialisation round-trip

RÈGLE ABSOLUE : ces tests ne vérifient PAS les livrables de production.
  Les renderers (PDF/PPTX/Excel) lisent annual_impact en Phase 4B.
  quantified_impact est vérifié uniquement sur les objets Python.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from models.financial_truth import (
    AnnualizationMetadata,
    AnnualizationQuality,
    EconomicEvent,
    EconomicEventStatus,
    GrossMarginResolution,
    GrossMarginSource,
    ImpactNature,
    MetricType,
    PeriodBasis,
    QuantifiedImpact,
    SourceReference,
    SourceType,
    SimulationMetricResult,
    build_event_hash,
    normalize_period,
    _safe_enum,
)
from services.economic_event_resolver import (
    EconomicEventResolver,
    resolve_simulation_metric,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures réutilisables
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def qi_revenue_one_time():
    """Cas A : Revenu ponctuel non annualisable — retard facturation Sep 2019."""
    return QuantifiedImpact(
        amount=454_000.0,
        metric_type=MetricType.REVENUE,
        period_basis=PeriodBasis.POINT_IN_TIME,
        nature=ImpactNature.ONE_TIME,
        confidence=0.85,
        source_period="Sep 2019",
        is_current_period=True,
        source_references=[
            SourceReference(sheet="P&L", row_label="Code 70 - CA", period="Sep 2019", observed_value=454_000.0)
        ],
    )


@pytest.fixture
def qi_cost_monthly_recurring():
    """Cas B : Économie mensuelle récurrente certifiée."""
    return QuantifiedImpact(
        amount=4_000.0,
        metric_type=MetricType.COST_SAVING,
        period_basis=PeriodBasis.MONTHLY,
        nature=ImpactNature.RECURRING,
        confidence=0.90,
        source_period="FY 2019",
        is_current_period=True,
    )


@pytest.fixture
def qi_revenue_historical():
    """Cas C : Revenue historique exclu des totaux courants."""
    return QuantifiedImpact(
        amount=49_000.0,
        metric_type=MetricType.REVENUE,
        period_basis=PeriodBasis.ANNUAL,
        nature=ImpactNature.RECURRING,
        source_period="FY 2014",
        temporal_role="HISTORICAL_ACTUAL",
        is_current_period=False,  # EXCLU des totaux courants
    )


@pytest.fixture
def qi_exposure_unknown():
    """Cas D : Exposition avec nature inconnue."""
    return QuantifiedImpact(
        amount=200_000.0,
        metric_type=MetricType.EXPOSURE,
        period_basis=PeriodBasis.UNKNOWN,
        nature=ImpactNature.UNKNOWN,
    )


@pytest.fixture
def qi_ytd_certified():
    """Cas G : YTD 6 mois calendaires complets → CERTIFIED."""
    return QuantifiedImpact(
        amount=227_000.0,
        metric_type=MetricType.EBITDA,
        period_basis=PeriodBasis.YTD,
        nature=ImpactNature.RECURRING,
        source_period="Jan-Jun 2019",
        is_current_period=True,
        annualization=AnnualizationMetadata(
            periods_elapsed=6,
            periods_per_year=12,
            quality=AnnualizationQuality.CERTIFIED,
            annualization_method="amount / 6 * 12",
            seasonality_flag=False,
        ),
    )


@pytest.fixture
def qi_ytd_run_rate():
    """Cas I : YTD 4 mois → RUN_RATE (< seuil 6 mois)."""
    return QuantifiedImpact(
        amount=150_000.0,
        metric_type=MetricType.EBITDA,
        period_basis=PeriodBasis.YTD,
        nature=ImpactNature.RECURRING,
        source_period="Jan-Apr 2019",
        is_current_period=True,
        annualization=AnnualizationMetadata(
            periods_elapsed=4,
            periods_per_year=12,
            quality=AnnualizationQuality.RUN_RATE,
            annualization_method="amount / 4 * 12",
            non_annualization_reason="Seuil minimum 6 mois non atteint (4 mois écoulés)",
        ),
    )


@pytest.fixture
def qi_revenue_no_margin():
    """Cas H : Revenue sans taux de marge → simulation EBITDA refusée."""
    return QuantifiedImpact(
        amount=454_000.0,
        metric_type=MetricType.REVENUE,
        period_basis=PeriodBasis.ANNUAL,
        nature=ImpactNature.RECURRING,
        gross_margin=GrossMarginResolution(rate=None, source=GrossMarginSource.UNKNOWN),
        is_current_period=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CAS A — Revenu ponctuel non annualisable
# ─────────────────────────────────────────────────────────────────────────────

class TestCasA_RevenueOneTime:

    def test_one_time_amount_returns_value(self, qi_revenue_one_time):
        assert qi_revenue_one_time.one_time_amount() == pytest.approx(454_000.0)

    def test_recurring_annual_equivalent_is_none(self, qi_revenue_one_time):
        assert qi_revenue_one_time.recurring_annual_equivalent() is None

    def test_run_rate_annual_is_none(self, qi_revenue_one_time):
        assert qi_revenue_one_time.run_rate_annual() is None

    def test_is_not_unresolved(self, qi_revenue_one_time):
        # POINT_IN_TIME + ONE_TIME = résolu (seulement absent des totaux recurring)
        assert qi_revenue_one_time.is_unresolved() is False

    def test_economic_event_id_assignable(self, qi_revenue_one_time):
        qi_revenue_one_time.economic_event_id = "test_event_id"
        assert qi_revenue_one_time.economic_event_id == "test_event_id"


# ─────────────────────────────────────────────────────────────────────────────
# CAS B — Économie mensuelle récurrente certifiée
# ─────────────────────────────────────────────────────────────────────────────

class TestCasB_MonthlyCostSaving:

    def test_recurring_annual_equivalent(self, qi_cost_monthly_recurring):
        assert qi_cost_monthly_recurring.recurring_annual_equivalent() == pytest.approx(48_000.0)

    def test_one_time_amount_is_none(self, qi_cost_monthly_recurring):
        assert qi_cost_monthly_recurring.one_time_amount() is None

    def test_is_not_unresolved(self, qi_cost_monthly_recurring):
        assert qi_cost_monthly_recurring.is_unresolved() is False

    def test_run_rate_annual_equals_certified(self, qi_cost_monthly_recurring):
        # Pour MONTHLY, run_rate = recurring_annual_equivalent
        assert qi_cost_monthly_recurring.run_rate_annual() == pytest.approx(48_000.0)


# ─────────────────────────────────────────────────────────────────────────────
# CAS C — Impact historique exclu des totaux courants
# ─────────────────────────────────────────────────────────────────────────────

class TestCasC_HistoricalImpact:

    def test_is_unresolved_when_not_current(self, qi_revenue_historical):
        assert qi_revenue_historical.is_unresolved() is True

    def test_recurring_annual_equivalent_still_calculable(self, qi_revenue_historical):
        # La méthode calcule, mais is_unresolved() = True empêche la contribution aux totaux
        assert qi_revenue_historical.recurring_annual_equivalent() == pytest.approx(49_000.0)

    def test_temporal_role_is_historical(self, qi_revenue_historical):
        assert qi_revenue_historical.temporal_role == "HISTORICAL_ACTUAL"

    def test_not_current_period(self, qi_revenue_historical):
        assert qi_revenue_historical.is_current_period is False


# ─────────────────────────────────────────────────────────────────────────────
# CAS D — Exposition avec nature inconnue
# ─────────────────────────────────────────────────────────────────────────────

class TestCasD_ExposureUnknown:

    def test_is_unresolved_exposure(self, qi_exposure_unknown):
        assert qi_exposure_unknown.is_unresolved() is True

    def test_recurring_annual_equivalent_is_none(self, qi_exposure_unknown):
        assert qi_exposure_unknown.recurring_annual_equivalent() is None

    def test_one_time_amount_is_none(self, qi_exposure_unknown):
        assert qi_exposure_unknown.one_time_amount() is None

    def test_run_rate_is_none(self, qi_exposure_unknown):
        assert qi_exposure_unknown.run_rate_annual() is None

    def test_amount_is_not_zero(self, qi_exposure_unknown):
        """UNKNOWN ≠ 0 : amount peut être fourni, mais les méthodes retournent None."""
        assert qi_exposure_unknown.amount == pytest.approx(200_000.0)  # pas None
        # Les méthodes de calcul retournent None car metric_type=EXPOSURE
        assert qi_exposure_unknown.recurring_annual_equivalent() is None


# ─────────────────────────────────────────────────────────────────────────────
# CAS E — Métriques hétérogènes non agrégables
# ─────────────────────────────────────────────────────────────────────────────

class TestCasE_HeterogeneousMetrics:

    def test_revenue_without_margin_not_integrated_to_ebitda(self, qi_revenue_no_margin):
        """Revenue sans taux de marge → non intégré à la simulation EBITDA."""
        result = resolve_simulation_metric([qi_revenue_no_margin], ebitda_base=None)
        # Si une seule métrique REVENUE → metric=REVENUE (pas d'EBITDA)
        assert result.metric == MetricType.REVENUE

    def test_heterogeneous_impacts_no_simulation(self):
        """Deux métriques différentes sans base EBITDA → metric=None."""
        qi1 = QuantifiedImpact(
            amount=100_000.0,
            metric_type=MetricType.REVENUE,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        qi2 = QuantifiedImpact(
            amount=50_000.0,
            metric_type=MetricType.CASH,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        result = resolve_simulation_metric([qi1, qi2], ebitda_base=None)
        assert result.metric is None
        assert len(result.unconvertible) == 2

    def test_ebitda_compatible_with_cost_saving(self):
        """COST_SAVING est compatible EBITDA → intégré si base EBITDA disponible."""
        qi1 = QuantifiedImpact(
            amount=48_000.0,
            metric_type=MetricType.COST_SAVING,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        result = resolve_simulation_metric([qi1], ebitda_base=-200_000.0)
        assert result.metric == MetricType.EBITDA
        assert len(result.unconvertible) == 0


# ─────────────────────────────────────────────────────────────────────────────
# CAS F — Anti-double-comptage via economic_event_id
# ─────────────────────────────────────────────────────────────────────────────

class TestCasF_AntiDoubleComptage:

    def test_same_event_same_hash(self):
        """Même inputs → même event_id (déterministe)."""
        h1 = build_event_hash("optilux", MetricType.REVENUE, ["fact_001"], "Sep 2019", None, "BILLING_DELAY")
        h2 = build_event_hash("optilux", MetricType.REVENUE, ["fact_001"], "Sep 2019", None, "BILLING_DELAY")
        assert h1 == h2

    def test_different_company_different_hash(self):
        h1 = build_event_hash("optilux", MetricType.REVENUE, ["fact_001"], "Sep 2019", None, "BILLING_DELAY")
        h2 = build_event_hash("other_co", MetricType.REVENUE, ["fact_001"], "Sep 2019", None, "BILLING_DELAY")
        assert h1 != h2

    def test_different_period_different_hash(self):
        h1 = build_event_hash("optilux", MetricType.REVENUE, ["fact_001"], "Sep 2019", None, "BILLING_DELAY")
        h2 = build_event_hash("optilux", MetricType.REVENUE, ["fact_001"], "Oct 2019", None, "BILLING_DELAY")
        assert h1 != h2

    def test_hash_length_16_hex(self):
        h = build_event_hash("optilux", MetricType.EBITDA, [], "FY 2019", None, "COST_OVERRUN")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_sorted_fact_ids_give_same_hash(self):
        """L'ordre des fact_ids ne change pas le hash."""
        h1 = build_event_hash("co", MetricType.COST, ["b", "a"], "2019", None, "OTHER")
        h2 = build_event_hash("co", MetricType.COST, ["a", "b"], "2019", None, "OTHER")
        assert h1 == h2


# ─────────────────────────────────────────────────────────────────────────────
# CAS G — YTD 6 mois calendaires CERTIFIED
# ─────────────────────────────────────────────────────────────────────────────

class TestCasG_YTDCertified:

    def test_recurring_annual_certified(self, qi_ytd_certified):
        expected = 227_000.0 / 6 * 12
        assert qi_ytd_certified.recurring_annual_equivalent() == pytest.approx(expected)

    def test_quality_is_certified(self, qi_ytd_certified):
        assert qi_ytd_certified.annualization_quality() == AnnualizationQuality.CERTIFIED

    def test_not_unresolved(self, qi_ytd_certified):
        assert qi_ytd_certified.is_unresolved() is False

    def test_run_rate_equals_certified_for_ytd_certified(self, qi_ytd_certified):
        assert qi_ytd_certified.run_rate_annual() == qi_ytd_certified.recurring_annual_equivalent()


# ─────────────────────────────────────────────────────────────────────────────
# CAS H — Revenue sans marge → simulation EBITDA refusée
# ─────────────────────────────────────────────────────────────────────────────

class TestCasH_RevenueNoMargin:

    def test_revenue_without_margin_becomes_simulation_metric_when_only_option(self, qi_revenue_no_margin):
        """
        REVENUE sans taux de marge + ebitda_base présente mais aucun impact EBITDA-compatible
        → étape 1 ne peut pas construire de simulation EBITDA (integrable=∅)
        → étape 2 : REVENUE est la seule métrique → metric=REVENUE
        L'impact est le simulation metric, pas unconvertible.
        unconvertible n'est peuplé qu'en context EBITDA (Phase 4C).
        """
        result = resolve_simulation_metric([qi_revenue_no_margin], ebitda_base=-200_000.0)
        # Aucun impact EBITDA-compatible → step 1 ne retourne rien
        # Step 2 : unique métrique = REVENUE
        assert result.metric == MetricType.REVENUE
        assert len(result.unconvertible) == 0

    def test_revenue_unconvertible_when_ebitda_impact_also_present(self, qi_revenue_no_margin):
        """
        REVENUE sans marge + EBITDA compatible → EBITDA devient metric,
        REVENUE sans marge entre dans unconvertible.
        """
        qi_ebitda = QuantifiedImpact(
            amount=48_000.0,
            metric_type=MetricType.COST_SAVING,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        result = resolve_simulation_metric([qi_revenue_no_margin, qi_ebitda], ebitda_base=-200_000.0)
        assert result.metric == MetricType.EBITDA
        assert qi_revenue_no_margin in result.unconvertible
        assert qi_ebitda not in result.unconvertible

    def test_gross_margin_source_is_unknown(self, qi_revenue_no_margin):
        assert qi_revenue_no_margin.gross_margin.source == GrossMarginSource.UNKNOWN
        assert qi_revenue_no_margin.gross_margin.rate is None


# ─────────────────────────────────────────────────────────────────────────────
# CAS I — YTD 4 mois → RUN_RATE (non certifié)
# ─────────────────────────────────────────────────────────────────────────────

class TestCasI_YTDRunRate:

    def test_run_rate_annual_calculated(self, qi_ytd_run_rate):
        expected = 150_000.0 / 4 * 12
        assert qi_ytd_run_rate.run_rate_annual() == pytest.approx(expected)

    def test_recurring_annual_equivalent_returns_calculated_value_for_ytd_run_rate(self, qi_ytd_run_rate):
        """
        Pour PeriodBasis.YTD + quality=RUN_RATE, recurring_annual_equivalent() retourne
        la valeur calculée (design V3 section A.6 : quality != REFUSED → return).
        La distinction CERTIFIED/RUN_RATE est gérée au niveau CostOfInactionV2 (Phase 4C),
        pas au niveau de la méthode recurring_annual_equivalent().
        """
        expected = 150_000.0 / 4 * 12
        assert qi_ytd_run_rate.recurring_annual_equivalent() == pytest.approx(expected)

    def test_quality_is_run_rate(self, qi_ytd_run_rate):
        assert qi_ytd_run_rate.annualization_quality() == AnnualizationQuality.RUN_RATE

    def test_not_unresolved(self, qi_ytd_run_rate):
        # RUN_RATE n'est pas unresolved (il est calculable, juste non certifié)
        assert qi_ytd_run_rate.is_unresolved() is False


# ─────────────────────────────────────────────────────────────────────────────
# CAS J — Arc fermé, impact réalisé partiel (modèle EconomicEvent)
# ─────────────────────────────────────────────────────────────────────────────

class TestCasJ_ClosedArcPartialResolution:

    def test_economic_event_creation(self, qi_revenue_one_time):
        event = EconomicEvent(
            event_id="ev_abc123",
            event_category="BILLING_DELAY",
            company_id="optilux",
            metric_type=MetricType.REVENUE,
            period="2019-09",
            entity=None,
            identified_exposure=qi_revenue_one_time,
        )
        assert event.status == EconomicEventStatus.IDENTIFIED
        assert event.realized_corrective_impact is None

    def test_residual_exposure_after_partial_resolution(self, qi_revenue_one_time):
        realized = QuantifiedImpact(
            amount=420_000.0,
            metric_type=MetricType.REVENUE,
            period_basis=PeriodBasis.POINT_IN_TIME,
            nature=ImpactNature.ONE_TIME,
        )
        identified_amount = qi_revenue_one_time.amount
        realized_amount = realized.amount
        residual = identified_amount - realized_amount
        assert residual == pytest.approx(34_000.0)

    def test_metrics_incompatible_no_residual(self):
        """Métriques incompatibles → pas de residual_exposure."""
        identified = QuantifiedImpact(
            amount=454_000.0,
            metric_type=MetricType.REVENUE,
            period_basis=PeriodBasis.POINT_IN_TIME,
            nature=ImpactNature.ONE_TIME,
        )
        realized = QuantifiedImpact(
            amount=200_000.0,
            metric_type=MetricType.EBITDA,  # ≠ REVENUE
            period_basis=PeriodBasis.POINT_IN_TIME,
            nature=ImpactNature.ONE_TIME,
        )
        # Métriques différentes → residual non calculable
        compatible = identified.metric_type == realized.metric_type
        assert compatible is False  # → residual_exposure = None dans la logique métier


# ─────────────────────────────────────────────────────────────────────────────
# Tests EconomicEventResolver
# ─────────────────────────────────────────────────────────────────────────────

class TestEconomicEventResolver:

    def test_resolve_creates_event(self, qi_revenue_one_time):
        resolver = EconomicEventResolver(company_id="optilux")
        event = resolver.resolve(
            impact=qi_revenue_one_time,
            event_category="BILLING_DELAY",
            source_fact_ids=["fact_001"],
            period="Sep 2019",
        )
        assert event.event_id is not None
        assert len(event.event_id) == 16
        assert event.event_category == "BILLING_DELAY"
        assert event.company_id == "optilux"

    def test_resolve_same_inputs_returns_same_event(self, qi_revenue_one_time):
        resolver = EconomicEventResolver(company_id="optilux")
        ev1 = resolver.resolve(
            impact=qi_revenue_one_time,
            event_category="BILLING_DELAY",
            source_fact_ids=["fact_001"],
            period="Sep 2019",
        )
        ev2 = resolver.resolve(
            impact=qi_revenue_one_time,
            event_category="BILLING_DELAY",
            source_fact_ids=["fact_001"],
            period="Sep 2019",
        )
        assert ev1.event_id == ev2.event_id
        assert ev1 is ev2  # même objet en mémoire (registre)

    def test_invalid_category_replaced_by_other(self, qi_revenue_one_time):
        resolver = EconomicEventResolver(company_id="optilux")
        event = resolver.resolve(
            impact=qi_revenue_one_time,
            event_category="INVALID_CATEGORY",
        )
        assert event.event_category == "OTHER"

    def test_economic_event_id_injected_into_impact(self, qi_revenue_one_time):
        qi_revenue_one_time.economic_event_id = None
        resolver = EconomicEventResolver(company_id="optilux")
        event = resolver.resolve(impact=qi_revenue_one_time, event_category="BILLING_DELAY")
        assert qi_revenue_one_time.economic_event_id == event.event_id

    def test_clear_resets_registry(self, qi_revenue_one_time):
        resolver = EconomicEventResolver(company_id="optilux")
        resolver.resolve(impact=qi_revenue_one_time, event_category="BILLING_DELAY")
        assert len(resolver.all_events()) == 1
        resolver.clear()
        assert len(resolver.all_events()) == 0

    def test_summary_structure(self, qi_revenue_one_time, qi_cost_monthly_recurring):
        resolver = EconomicEventResolver(company_id="optilux")
        resolver.resolve(impact=qi_revenue_one_time, event_category="BILLING_DELAY", period="Sep 2019")
        # Nouveau resolver pour le deuxième (évite la collision de hash avec period identique)
        qi_cost_monthly_recurring.economic_event_id = None
        resolver.resolve(impact=qi_cost_monthly_recurring, event_category="COST_OVERRUN", period="FY 2019")
        summary = resolver.summary()
        assert summary["total_events"] == 2
        assert "BILLING_DELAY" in summary["by_category"]
        assert "COST_OVERRUN" in summary["by_category"]


# ─────────────────────────────────────────────────────────────────────────────
# Tests UNKNOWN ≠ 0 — invariant fondamental
# ─────────────────────────────────────────────────────────────────────────────

class TestUnknownNotZero:

    def test_none_amount_is_unresolved(self):
        qi = QuantifiedImpact(
            amount=None,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        assert qi.is_unresolved() is True
        assert qi.recurring_annual_equivalent() is None
        assert qi.run_rate_annual() is None
        assert qi.one_time_amount() is None

    def test_none_amount_not_equal_zero(self):
        qi = QuantifiedImpact(amount=None, metric_type=MetricType.EBITDA,
                              period_basis=PeriodBasis.ANNUAL, nature=ImpactNature.RECURRING)
        assert qi.amount is None
        assert qi.amount != 0.0

    def test_zero_amount_is_valid_financial_zero(self):
        """0.0 = vrai zéro observé (ex : "0 €") — différent de l'absence de donnée."""
        qi = QuantifiedImpact(
            amount=0.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        assert qi.amount == 0.0
        assert qi.amount is not None
        assert qi.recurring_annual_equivalent() == pytest.approx(0.0)

    def test_unknown_metric_type_is_unresolved(self):
        qi = QuantifiedImpact(
            amount=100_000.0,
            metric_type=MetricType.UNKNOWN,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        assert qi.is_unresolved() is True

    def test_unknown_period_basis_is_unresolved(self):
        qi = QuantifiedImpact(
            amount=100_000.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.UNKNOWN,
            nature=ImpactNature.RECURRING,
        )
        assert qi.is_unresolved() is True


# ─────────────────────────────────────────────────────────────────────────────
# Tests sérialisation / désérialisation round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestSerializationRoundTrip:

    def test_to_dict_from_dict_round_trip(self, qi_ytd_certified):
        d = qi_ytd_certified.to_dict()
        restored = QuantifiedImpact.from_dict(d)
        assert restored.amount == pytest.approx(qi_ytd_certified.amount)
        assert restored.metric_type == qi_ytd_certified.metric_type
        assert restored.period_basis == qi_ytd_certified.period_basis
        assert restored.nature == qi_ytd_certified.nature
        assert restored.annualization is not None
        assert restored.annualization.quality == AnnualizationQuality.CERTIFIED
        assert restored.annualization.periods_elapsed == 6

    def test_from_dict_invalid_enum_falls_to_unknown(self):
        d = {
            "amount": 50_000.0,
            "metric_type": "INVALID_TYPE",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
        }
        qi = QuantifiedImpact.from_dict(d)
        assert qi.metric_type == MetricType.UNKNOWN

    def test_from_dict_none_amount_preserved(self):
        d = {"amount": None, "metric_type": "EBITDA", "period_basis": "ANNUAL", "nature": "RECURRING"}
        qi = QuantifiedImpact.from_dict(d)
        assert qi.amount is None

    def test_from_dict_with_gross_margin(self):
        d = {
            "amount": 100_000.0,
            "metric_type": "REVENUE",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "gross_margin": {"rate": 0.42, "source": "EXPLICIT_FILE"},
        }
        qi = QuantifiedImpact.from_dict(d)
        assert qi.gross_margin is not None
        assert qi.gross_margin.rate == pytest.approx(0.42)
        assert qi.gross_margin.source == GrossMarginSource.EXPLICIT_FILE

    def test_from_dict_malformed_gross_margin_returns_none(self):
        d = {
            "amount": 100_000.0,
            "metric_type": "EBITDA",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "gross_margin": {"rate": 0.42, "source": "NOT_A_VALID_SOURCE"},
        }
        qi = QuantifiedImpact.from_dict(d)
        assert qi.gross_margin is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests migration parallèle (quantified_impact coexiste avec annual_impact)
# ─────────────────────────────────────────────────────────────────────────────

class TestParallelMigration:

    def test_value_destroyer_has_quantified_impact_field(self):
        from models.executive_decision_model import ValueDestroyer
        vd = ValueDestroyer(name="Test Destroyer", annual_impact=48_000.0)
        assert hasattr(vd, "quantified_impact")
        assert vd.quantified_impact is None  # Pas encore peuplé

    def test_executive_decision_has_quantified_impact_field(self):
        from models.executive_decision_model import ExecutiveDecision
        ed = ExecutiveDecision(decision="Test decision", annual_impact=100_000.0)
        assert hasattr(ed, "quantified_impact")
        assert ed.quantified_impact is None

    def test_value_destroyer_annual_impact_unchanged_when_qi_present(self):
        """annual_impact reste inchangé quand quantified_impact est peuplé."""
        from models.executive_decision_model import ValueDestroyer
        qi = QuantifiedImpact(
            amount=48_000.0,
            metric_type=MetricType.COST_SAVING,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        vd = ValueDestroyer(
            name="Optimisation charges",
            annual_impact=48_000.0,   # legacy — inchangé
            quantified_impact=qi,     # Phase 4B — parallèle
        )
        assert vd.annual_impact == pytest.approx(48_000.0)
        assert vd.quantified_impact is not None
        assert vd.quantified_impact.metric_type == MetricType.COST_SAVING

    def test_renderer_reads_annual_impact_not_qi(self):
        """Simulation renderer Phase 4B : annual_impact disponible même si QI None."""
        from models.executive_decision_model import ValueDestroyer
        vd = ValueDestroyer(name="Impact test", annual_impact=120_000.0, quantified_impact=None)
        # Le renderer lit annual_impact (comportement legacy inchangé)
        assert vd.annual_impact == pytest.approx(120_000.0)
        assert vd.quantified_impact is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests normalize_period et safe_enum
# ─────────────────────────────────────────────────────────────────────────────

class TestUtilityFunctions:

    def test_normalize_period_month_year(self):
        assert normalize_period("Sep 2019") == "2019-09"
        assert normalize_period("jan 2014") == "2014-01"
        assert normalize_period("Déc 2019") == "2019-12"

    def test_normalize_period_fy(self):
        assert normalize_period("FY 2019") == "FY-2019"

    def test_normalize_period_already_normalized(self):
        assert normalize_period("2019-09") == "2019-09"

    def test_safe_enum_valid_value(self):
        result = _safe_enum(MetricType, "EBITDA", MetricType.UNKNOWN)
        assert result == MetricType.EBITDA

    def test_safe_enum_invalid_value_returns_default(self):
        result = _safe_enum(MetricType, "NOT_A_METRIC", MetricType.UNKNOWN)
        assert result == MetricType.UNKNOWN

    def test_safe_enum_none_returns_default(self):
        result = _safe_enum(PeriodBasis, None, PeriodBasis.UNKNOWN)
        assert result == PeriodBasis.UNKNOWN

    def test_source_reference_anchored_with_fact_id(self):
        ref = SourceReference(fact_id="fact_001")
        assert ref.is_anchored() is True

    def test_source_reference_anchored_with_minimal_fields(self):
        ref = SourceReference(sheet="P&L", row_label="CA", period="Sep 2019")
        assert ref.is_anchored() is True

    def test_source_reference_not_anchored_when_incomplete(self):
        ref = SourceReference(sheet="P&L")  # manque row_label et period
        assert ref.is_anchored() is False


# ─────────────────────────────────────────────────────────────────────────────
# Tests AnnualizationQuality règles calendaires
# ─────────────────────────────────────────────────────────────────────────────

class TestAnnualizationQuality:

    def test_refused_quality_makes_recurring_none(self):
        qi = QuantifiedImpact(
            amount=50_000.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.ANNUALIZED,
            nature=ImpactNature.RECURRING,
            annualization=AnnualizationMetadata(
                periods_elapsed=3,
                periods_per_year=12,
                quality=AnnualizationQuality.REFUSED,
                annualization_method="",
                non_annualization_reason="Saisonnalité détectée",
            ),
        )
        assert qi.recurring_annual_equivalent() is None
        assert qi.is_unresolved() is True

    def test_certified_quarterly(self):
        qi = QuantifiedImpact(
            amount=100_000.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.YTD,
            nature=ImpactNature.RECURRING,
            annualization=AnnualizationMetadata(
                periods_elapsed=2,
                periods_per_year=4,
                quality=AnnualizationQuality.CERTIFIED,
                annualization_method="amount / 2 * 4",
            ),
        )
        assert qi.recurring_annual_equivalent() == pytest.approx(100_000.0 / 2 * 4)

    def test_no_annualization_on_annual_period_basis(self):
        """ANNUAL ne nécessite pas AnnualizationMetadata."""
        qi = QuantifiedImpact(
            amount=200_000.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        assert qi.recurring_annual_equivalent() == pytest.approx(200_000.0)
        assert qi.annualization is None
        assert qi.annualization_quality() is None


# ─────────────────────────────────────────────────────────────────────────────
# GAP 1 — Contrat de typage fort (Optional[QuantifiedImpact])
# ─────────────────────────────────────────────────────────────────────────────

class TestTypingContract:
    """
    Vérifie que Pydantic v2 enforce le type Optional[QuantifiedImpact]
    sur ValueDestroyer et ExecutiveDecision.
    """

    def test_none_accepted_by_value_destroyer(self):
        from models.executive_decision_model import ValueDestroyer
        vd = ValueDestroyer(name="test", quantified_impact=None)
        assert vd.quantified_impact is None

    def test_valid_qi_accepted_by_value_destroyer(self):
        from models.executive_decision_model import ValueDestroyer
        qi = QuantifiedImpact(
            amount=80_000.0,
            metric_type=MetricType.COST,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        vd = ValueDestroyer(name="test", quantified_impact=qi)
        assert vd.quantified_impact is qi
        assert vd.quantified_impact.amount == 80_000.0

    def test_valid_qi_accepted_by_executive_decision(self):
        from models.executive_decision_model import ExecutiveDecision
        qi = QuantifiedImpact(
            amount=150_000.0,
            metric_type=MetricType.EBITDA,
            period_basis=PeriodBasis.ANNUAL,
            nature=ImpactNature.RECURRING,
        )
        ed = ExecutiveDecision(decision="Renégocier contrats fournisseurs", quantified_impact=qi)
        assert ed.quantified_impact is qi

    def test_invalid_string_rejected_by_value_destroyer(self):
        """Pydantic v2 doit rejeter un type invalide avec ValidationError."""
        from models.executive_decision_model import ValueDestroyer
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ValueDestroyer(name="bad", quantified_impact="une_string_invalide")

    def test_invalid_dict_rejected_by_value_destroyer(self):
        """Un dict brut (non-construit via from_dict) doit être rejeté."""
        from models.executive_decision_model import ValueDestroyer
        from pydantic import ValidationError
        # Pydantic v2 peut accepter des dicts si le type est un BaseModel,
        # mais pour un @dataclass il attend soit None soit une instance.
        # Si Pydantic v2 tente de construire depuis un dict partiel → doit échouer
        # (champ obligatoire 'amount' manque dans ce dict).
        with pytest.raises((ValidationError, TypeError)):
            ValueDestroyer(name="bad", quantified_impact={"metric_type": "EBITDA"})

    def test_quantified_impact_not_any_type_hint(self):
        """Vérifie que le type hint de quantified_impact n'est pas Any."""
        import inspect
        from models.executive_decision_model import ValueDestroyer
        hints = {}
        for cls in type(ValueDestroyer).__mro__:
            if hasattr(cls, '__annotations__'):
                hints.update(cls.__annotations__)
        # Le type doit référencer QuantifiedImpact, pas Any
        field_type = str(ValueDestroyer.model_fields["quantified_impact"].annotation)
        assert "Any" not in field_type, (
            f"quantified_impact ne doit pas être typé Any. Type actuel : {field_type}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP 2 — Robustesse du parser _parse_structured_impacts_section()
# ─────────────────────────────────────────────────────────────────────────────

class TestParserRobustness:
    """
    10 cas de robustesse pour _parse_structured_impacts_section().

    Règle fondamentale :
      - Aucune exception ne doit remonter au pipeline principal.
      - Un item invalide → quantified_impact = None sur cet item (legacy inchangé).
      - Règle duplicate : first valid wins.
      - amount = 0.0 reste un vrai zéro (jamais converti en None).
    """

    def _parse(self, section_text: str) -> dict:
        from services.llm_service import _parse_structured_impacts_section
        return _parse_structured_impacts_section(section_text)

    def _valid_section(self, items: list) -> str:
        """Construit une section bien formée autour d'une liste d'items."""
        import json
        return f"```json\n{json.dumps(items)}\n```"

    # ── Cas 1 : section absente ─────────────────────────────────────────────
    def test_empty_section_text_returns_empty_dict(self):
        """Section absente → dict vide, pas d'exception."""
        result = self._parse("")
        assert result == {}

    def test_none_like_empty_string_returns_empty_dict(self):
        """Section avec contenu vide → dict vide."""
        result = self._parse("   \n  ")
        assert result == {}

    # ── Cas 2 : JSON invalide ───────────────────────────────────────────────
    def test_invalid_json_returns_empty_dict(self):
        """JSON invalide (syntaxe cassée) → dict vide, aucune exception."""
        broken = "```json\n[{metric_type: EBITDA,}]\n```"
        result = self._parse(broken)
        assert result == {}

    # ── Cas 3 : JSON tronqué ────────────────────────────────────────────────
    def test_truncated_json_returns_empty_dict(self):
        """JSON tronqué (liste non fermée) → dict vide."""
        truncated = '```json\n[{"ref_type": "destroyer", "ref_index": 0, "metric_type": "EBITDA"'
        result = self._parse(truncated)
        assert result == {}

    # ── Cas 4 : enum inconnu ────────────────────────────────────────────────
    def test_unknown_enum_value_preserved_in_dict(self):
        """
        Un enum inconnu (ex: metric_type = 'MARGE') est conservé tel quel dans le dict.
        _safe_enum() le convertira en UNKNOWN lors de QuantifiedImpact.from_dict().
        Le parser ne doit pas lever d'exception sur des enums non reconnus.
        """
        items = [{"ref_type": "destroyer", "ref_index": 0,
                  "metric_type": "MARGE_INCONNUE",
                  "period_basis": "ANNUAL", "nature": "RECURRING",
                  "confidence": 0.7, "is_current_period": True}]
        result = self._parse(self._valid_section(items))
        assert ("destroyer", 0) in result
        qi_dict = result[("destroyer", 0)]
        assert qi_dict["metric_type"] == "MARGE_INCONNUE"
        # Vérification que from_dict le convertit bien en UNKNOWN
        qi = QuantifiedImpact.from_dict({**qi_dict, "amount": 50_000.0})
        assert qi.metric_type == MetricType.UNKNOWN

    # ── Cas 5 : ref_index hors limites ──────────────────────────────────────
    def test_ref_index_out_of_bounds_parsed_but_not_injected(self):
        """
        ref_index hors limites (99 pour 2 destroyers) : le parser accepte l'index
        mais l'injection dans les destroyers ne trouve pas de correspondance → item
        legacy inchangé (quantified_impact absent de son dict).
        """
        items = [{"ref_type": "destroyer", "ref_index": 99,
                  "metric_type": "EBITDA", "period_basis": "ANNUAL",
                  "nature": "RECURRING", "confidence": 0.8, "is_current_period": True}]
        result = self._parse(self._valid_section(items))
        # Le parser stocke l'entrée (index 99 est syntaxiquement valide)
        assert ("destroyer", 99) in result
        # Simulation injection : seuls les indexes 0 et 1 existent pour 2 destroyers
        destroyers = [{"name": "d0"}, {"name": "d1"}]
        for i, d in enumerate(destroyers):
            qi_dict = result.get(("destroyer", i))
            if qi_dict:
                d["quantified_impact"] = qi_dict
        # Aucun des 2 destroyers ne reçoit de QI (seul index 99 est dans result)
        assert "quantified_impact" not in destroyers[0]
        assert "quantified_impact" not in destroyers[1]

    # ── Cas 6 : duplicate ref_type/ref_index (first valid wins) ─────────────
    def test_duplicate_ref_first_valid_wins(self):
        """
        Deux items avec le même (ref_type, ref_index) :
        le premier dans le tableau JSON est retenu, le second ignoré.
        Règle : first valid wins.
        """
        items = [
            {"ref_type": "destroyer", "ref_index": 0,
             "metric_type": "EBITDA", "period_basis": "ANNUAL",
             "nature": "RECURRING", "confidence": 0.9, "is_current_period": True},
            {"ref_type": "destroyer", "ref_index": 0,
             "metric_type": "REVENUE", "period_basis": "MONTHLY",  # doublon
             "nature": "ONE_TIME", "confidence": 0.3, "is_current_period": False},
        ]
        result = self._parse(self._valid_section(items))
        assert ("destroyer", 0) in result
        kept = result[("destroyer", 0)]
        assert kept["metric_type"] == "EBITDA", "First valid wins : EBITDA doit être conservé"
        assert kept["confidence"] == pytest.approx(0.9)

    # ── Cas 7 : quantified_impact partiel ───────────────────────────────────
    def test_partial_qi_uses_defaults(self):
        """
        Item partiel (confidence absent, is_current_period absent) :
        le parser utilise les valeurs par défaut (0.5, True).
        """
        items = [{"ref_type": "quick_win", "ref_index": 0,
                  "metric_type": "COST_SAVING", "period_basis": "ANNUAL",
                  "nature": "RECURRING"}]
        result = self._parse(self._valid_section(items))
        assert ("quick_win", 0) in result
        qi_dict = result[("quick_win", 0)]
        assert qi_dict["confidence"] == pytest.approx(0.5)
        assert qi_dict["is_current_period"] is True

    # ── Cas 8 : amount = 0.0 (vrai zéro) ────────────────────────────────────
    def test_amount_zero_not_converted_to_none_after_injection(self):
        """
        amount = 0.0 dans le legacy_amount doit rester 0.0 après injection.
        INVARIANT : 0.0 est un vrai zéro observé, jamais None.
        """
        from services.executive_decision_model import _try_deserialize_qi
        qi_dict = {
            "metric_type": "COST_SAVING",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.7,
            "is_current_period": True,
            "amount": None,
        }
        qi = _try_deserialize_qi(qi_dict, amount=0.0)
        assert qi is not None, "QI doit être construit même avec amount=0.0"
        assert qi.amount == 0.0, "0.0 est un vrai zéro — ne doit pas devenir None"
        assert qi.source_references[0].source_type == SourceType.LEGACY_PARSE

    # ── Cas 9 : amount = null (None legacy) ─────────────────────────────────
    def test_amount_null_legacy_results_in_none_amount(self):
        """
        Si legacy_amount est None (données insuffisantes), amount reste None.
        is_unresolved() doit retourner True.
        """
        from services.executive_decision_model import _try_deserialize_qi
        qi_dict = {
            "metric_type": "EBITDA",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.0,
            "is_current_period": True,
            "amount": None,
        }
        qi = _try_deserialize_qi(qi_dict, amount=None)
        assert qi is not None
        assert qi.amount is None
        assert qi.is_unresolved() is True
        # Pas de SourceReference LEGACY_PARSE si amount n'a pas été injecté
        legacy_refs = [r for r in qi.source_references
                       if r.source_type == SourceType.LEGACY_PARSE]
        assert len(legacy_refs) == 0

    # ── Cas 10 : texte libre avant/après le bloc JSON ────────────────────────
    def test_text_before_and_after_json_block(self):
        """
        Texte libre autour du bloc JSON (LLM qui ajoute des explications)
        ne doit pas bloquer le parsing.
        """
        section_with_noise = """
Voici l'analyse structurée des impacts financiers :

Note préliminaire : ces données sont extraites du fichier P&L FY2019.

```json
[
  {"ref_type": "destroyer", "ref_index": 0,
   "metric_type": "REVENUE", "period_basis": "POINT_IN_TIME",
   "nature": "ONE_TIME", "confidence": 0.85, "is_current_period": true}
]
```

Ces impacts seront utilisés pour calculer le coût de l'inaction.
Voir section DÉCISION pour les recommandations.
"""
        result = self._parse(section_with_noise)
        assert ("destroyer", 0) in result
        qi_dict = result[("destroyer", 0)]
        assert qi_dict["metric_type"] == "REVENUE"
        assert qi_dict["confidence"] == pytest.approx(0.85)


# ─────────────────────────────────────────────────────────────────────────────
# GAP 3 — Provenance legacy : SourceType + is_anchored()
# ─────────────────────────────────────────────────────────────────────────────

class TestSourceTypeProvenance:
    """
    Vérifie que la traçabilité de provenance fonctionne correctement.
    Un LEGACY_PARSE ne doit jamais être confondu avec une extraction certifiée.
    """

    def test_legacy_parse_source_type_exists(self):
        """SourceType.LEGACY_PARSE doit exister dans l'enum."""
        assert SourceType.LEGACY_PARSE.value == "LEGACY_PARSE"

    def test_all_source_types_exist(self):
        """Tous les types de provenance doivent être définis."""
        expected = {"CANONICAL_FACT", "LEGACY_PARSE", "LLM_EXTRACTED",
                    "USER_PROVIDED", "DETERMINISTIC_CALCULATION"}
        actual = {st.value for st in SourceType}
        assert expected == actual

    def test_legacy_parse_ref_is_not_anchored(self):
        """
        Une SourceReference LEGACY_PARSE ne doit JAMAIS être considérée
        comme ancrée, même si fact_id est renseigné.
        """
        ref = SourceReference(
            fact_id="quelque_chose",  # ignoré si source_type=LEGACY_PARSE
            source_type=SourceType.LEGACY_PARSE,
            source_quote="amount from parse_amount_eur",
        )
        assert ref.is_anchored() is False

    def test_canonical_fact_ref_with_fact_id_is_anchored(self):
        """Une CANONICAL_FACT avec fact_id est ancrée."""
        ref = SourceReference(
            fact_id="canonical_001",
            source_type=SourceType.CANONICAL_FACT,
        )
        assert ref.is_anchored() is True

    def test_llm_extracted_ref_without_fact_id_not_anchored(self):
        """LLM_EXTRACTED sans fact_id ni (sheet+row_label+period) → non ancré."""
        ref = SourceReference(
            source_type=SourceType.LLM_EXTRACTED,
            source_quote="extrait du LLM",
        )
        assert ref.is_anchored() is False

    def test_legacy_amount_injection_marks_provenance(self):
        """
        Après injection legacy, la SourceReference LEGACY_PARSE est présente
        et is_anchored() retourne False.
        """
        from services.executive_decision_model import _try_deserialize_qi
        qi_dict = {
            "metric_type": "REVENUE",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.8,
            "is_current_period": True,
            "amount": None,
        }
        qi = _try_deserialize_qi(qi_dict, amount=300_000.0)
        assert qi.amount == 300_000.0
        legacy_refs = [r for r in qi.source_references
                       if r.source_type == SourceType.LEGACY_PARSE]
        assert len(legacy_refs) == 1
        assert legacy_refs[0].is_anchored() is False
        assert "Phase 4B" in legacy_refs[0].source_quote

    def test_source_type_round_trip_serialization(self):
        """source_type survive à un round-trip to_dict() → from_dict()."""
        from services.executive_decision_model import _try_deserialize_qi
        qi_dict = {
            "metric_type": "EBITDA",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.9,
            "is_current_period": True,
            "amount": None,
        }
        qi = _try_deserialize_qi(qi_dict, amount=500_000.0)
        serialized = qi.to_dict()
        qi_back = QuantifiedImpact.from_dict(serialized)
        assert len(qi_back.source_references) == 1
        assert qi_back.source_references[0].source_type == SourceType.LEGACY_PARSE
