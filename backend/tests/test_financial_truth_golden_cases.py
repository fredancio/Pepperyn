"""
test_financial_truth_golden_cases.py — Golden Semantic Cases Phase 4B

NATURE DE CES TESTS (important) :
  Ces cas sont des "golden semantic cases" — des constructions directes en Python
  qui vérifient que le MODÈLE DÉTERMINISTE (QuantifiedImpact + méthodes) fonctionne
  correctement sur 10 scénarios financiers représentatifs.

  Ce ne sont PAS des tests d'extraction LLM end-to-end.
  Les llm_dict sont des dicts Python hardcodés qui SIMULENT ce qu'un parseur
  correct produirait — ils ne viennent pas d'un vrai appel LLM.

  Ce qui est mesuré ici :
    ✅ Précision du modèle déterministe (from_dict → méthodes) — 10/10 attendu
    ❌ NON MESURÉ : précision du parser JSON sur output LLM réel
    ❌ NON MESURÉ : précision extraction LLM end-to-end (metric_type, etc.)

  PRÉCONDITION PHASE 4C (à mesurer séparément) :
    Avant de passer en Phase 4C, valider sur ≥ 10 vraies analyses end-to-end :
      prompt Call 3 réel → réponse LLM réelle → parsing → QuantifiedImpact final
    Seuil requis : ≥ 85 % de précision par dimension (metric_type, period_basis, nature).

Pipeline testé ici :
  llm_dict Python hardcodé → QuantifiedImpact.from_dict() → méthodes → assertions
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.financial_truth import (
    AnnualizationQuality,
    ImpactNature,
    MetricType,
    PeriodBasis,
    GrossMarginSource,
    QuantifiedImpact,
    build_event_hash,
)
from services.economic_event_resolver import EconomicEventResolver


# ─────────────────────────────────────────────────────────────────────────────
# 10 golden semantic cases
# Format : llm_dict simulé (ce qu'un parseur correct produirait) +
#          legacy_amount simulé (ce que parse_amount_eur() retournerait)
# Ces valeurs sont hardcodées — elles NE viennent PAS d'un vrai LLM.
# ─────────────────────────────────────────────────────────────────────────────

GOLDEN_CASES = [
    # Cas 1 : Retard facturation Sep 2019 — ponctuel revenue
    {
        "id": "GC_01",
        "description": "Retard facturation Septembre 2019 (Optilux V3)",
        "llm_dict": {
            "metric_type": "REVENUE",
            "period_basis": "POINT_IN_TIME",
            "nature": "ONE_TIME",
            "confidence": 0.85,
            "source_period": "Sep 2019",
            "is_current_period": True,
        },
        "legacy_amount": 454_000.0,
        "expected": {
            "metric_type": MetricType.REVENUE,
            "period_basis": PeriodBasis.POINT_IN_TIME,
            "nature": ImpactNature.ONE_TIME,
            "is_current_period": True,
            "is_unresolved": False,
            "recurring_annual_eq": None,
            "one_time_amount": 454_000.0,
        },
    },
    # Cas 2 : Masse salariale sous-traitance — coût annuel récurrent
    {
        "id": "GC_02",
        "description": "Charges sous-traitance IT — coût récurrent annuel",
        "llm_dict": {
            "metric_type": "COST",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.90,
            "source_period": "FY 2019",
            "is_current_period": True,
        },
        "legacy_amount": -120_000.0,
        "expected": {
            "metric_type": MetricType.COST,
            "period_basis": PeriodBasis.ANNUAL,
            "nature": ImpactNature.RECURRING,
            "is_current_period": True,
            "is_unresolved": False,
            "recurring_annual_eq": -120_000.0,
            "one_time_amount": None,
        },
    },
    # Cas 3 : Colonnes 2014 — données historiques, non courantes
    {
        "id": "GC_03",
        "description": "CA 2014 colonnes Optilux V3 — historique exclu",
        "llm_dict": {
            "metric_type": "REVENUE",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.70,
            "source_period": "FY 2014",
            "is_current_period": False,
        },
        "legacy_amount": 890_000.0,
        "expected": {
            "metric_type": MetricType.REVENUE,
            "period_basis": PeriodBasis.ANNUAL,
            "nature": ImpactNature.RECURRING,
            "is_current_period": False,
            "is_unresolved": True,  # Non courant → exclu
            "recurring_annual_eq": 890_000.0,  # Calculable mais non inclus
            "one_time_amount": None,
        },
    },
    # Cas 4 : Économie sur négociation fournisseur — ponctuelle (one-time gain)
    {
        "id": "GC_04",
        "description": "Gain renégociation contrat fournisseur — ponctuel",
        "llm_dict": {
            "metric_type": "COST_SAVING",
            "period_basis": "POINT_IN_TIME",
            "nature": "ONE_TIME",
            "confidence": 0.75,
            "source_period": "Q3 2019",
            "is_current_period": True,
        },
        "legacy_amount": 35_000.0,
        "expected": {
            "metric_type": MetricType.COST_SAVING,
            "period_basis": PeriodBasis.POINT_IN_TIME,
            "nature": ImpactNature.ONE_TIME,
            "is_current_period": True,
            "is_unresolved": False,
            "recurring_annual_eq": None,
            "one_time_amount": 35_000.0,
        },
    },
    # Cas 5 : Perte marge brute structurelle — récurrente mensuelle
    {
        "id": "GC_05",
        "description": "Érosion marge brute — coût direct récurrent mensuel",
        "llm_dict": {
            "metric_type": "GROSS_MARGIN",
            "period_basis": "MONTHLY",
            "nature": "STRUCTURAL",
            "confidence": 0.80,
            "source_period": "Jan-Sep 2019",
            "is_current_period": True,
        },
        "legacy_amount": -8_500.0,
        "expected": {
            "metric_type": MetricType.GROSS_MARGIN,
            "period_basis": PeriodBasis.MONTHLY,
            "nature": ImpactNature.STRUCTURAL,
            "is_current_period": True,
            "is_unresolved": False,
            "recurring_annual_eq": -8_500.0 * 12,
            "one_time_amount": None,
        },
    },
    # Cas 6 : Tension BFR — exposition trésorerie (EXPOSURE, non annualisable)
    {
        "id": "GC_06",
        "description": "Tension BFR — exposition trésorerie non annualisable",
        "llm_dict": {
            "metric_type": "EXPOSURE",
            "period_basis": "POINT_IN_TIME",
            "nature": "UNKNOWN",
            "confidence": 0.60,
            "source_period": "Sep 2019",
            "is_current_period": True,
        },
        "legacy_amount": 75_000.0,
        "expected": {
            "metric_type": MetricType.EXPOSURE,
            "period_basis": PeriodBasis.POINT_IN_TIME,
            "nature": ImpactNature.UNKNOWN,
            "is_current_period": True,
            "is_unresolved": True,  # EXPOSURE toujours non résolu
            "recurring_annual_eq": None,
            "one_time_amount": None,
        },
    },
    # Cas 7 : Revenue YTD 9 mois — CERTIFIED (≥6 mois)
    {
        "id": "GC_07",
        "description": "CA YTD Jan-Sep 2019 — annualisation certifiée",
        "llm_dict": {
            "metric_type": "REVENUE",
            "period_basis": "YTD",
            "nature": "RECURRING",
            "confidence": 0.88,
            "source_period": "Jan-Sep 2019",
            "is_current_period": True,
            "ytd_periods_elapsed": 9,
        },
        "legacy_amount": 810_000.0,
        "expected": {
            "metric_type": MetricType.REVENUE,
            "period_basis": PeriodBasis.YTD,
            "nature": ImpactNature.RECURRING,
            "is_current_period": True,
            "is_unresolved": False,
            "annualization_quality": AnnualizationQuality.CERTIFIED,
            "recurring_annual_eq": pytest.approx(810_000.0 / 9 * 12),
            "one_time_amount": None,
        },
    },
    # Cas 8 : EBITDA négatif — données insuffisantes (UNKNOWN ≠ 0)
    {
        "id": "GC_08",
        "description": "EBITDA source 'Données insuffisantes' — amount=None",
        "llm_dict": {
            "metric_type": "EBITDA",
            "period_basis": "ANNUAL",
            "nature": "UNKNOWN",
            "confidence": 0.0,
            "source_period": "FY 2019",
            "is_current_period": True,
        },
        "legacy_amount": None,  # Données insuffisantes → None (jamais 0)
        "expected": {
            "metric_type": MetricType.EBITDA,
            "period_basis": PeriodBasis.ANNUAL,
            "nature": ImpactNature.UNKNOWN,
            "is_current_period": True,
            "is_unresolved": True,  # amount=None → unresolved
            "recurring_annual_eq": None,
            "one_time_amount": None,
        },
    },
    # Cas 9 : Revenue avec taux de marge connu — convertible EBITDA
    {
        "id": "GC_09",
        "description": "CA avec taux marge explicite — convertible en EBITDA",
        "llm_dict": {
            "metric_type": "REVENUE",
            "period_basis": "ANNUAL",
            "nature": "RECURRING",
            "confidence": 0.82,
            "source_period": "FY 2019",
            "is_current_period": True,
            "gross_margin": {"rate": 0.42, "source": "EXPLICIT_FILE"},
        },
        "legacy_amount": 1_200_000.0,
        "expected": {
            "metric_type": MetricType.REVENUE,
            "period_basis": PeriodBasis.ANNUAL,
            "nature": ImpactNature.RECURRING,
            "is_current_period": True,
            "is_unresolved": False,
            "gross_margin_rate": pytest.approx(0.42),
            "gross_margin_source": GrossMarginSource.EXPLICIT_FILE,
            "recurring_annual_eq": 1_200_000.0,
        },
    },
    # Cas 10 : Impact net_profit — type métrique correctement identifié
    {
        "id": "GC_10",
        "description": "Résultat net positif — structurel annuel",
        "llm_dict": {
            "metric_type": "NET_PROFIT",
            "period_basis": "ANNUAL",
            "nature": "STRUCTURAL",
            "confidence": 0.78,
            "source_period": "FY 2019",
            "is_current_period": True,
        },
        "legacy_amount": 85_000.0,
        "expected": {
            "metric_type": MetricType.NET_PROFIT,
            "period_basis": PeriodBasis.ANNUAL,
            "nature": ImpactNature.STRUCTURAL,
            "is_current_period": True,
            "is_unresolved": False,
            "recurring_annual_eq": 85_000.0,
            "one_time_amount": None,
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Exécution des cas et collecte de la matrice de précision
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenCases:
    """
    10 golden semantic cases.
    Chaque test vérifie UNE dimension du modèle déterministe.
    NE mesure PAS la précision d'extraction LLM end-to-end.
    """

    def _build_qi(self, case: dict) -> QuantifiedImpact:
        d = dict(case["llm_dict"])
        d["amount"] = case["legacy_amount"]
        # Gestion YTD/annualization depuis ytd_periods_elapsed
        ytd_n = d.pop("ytd_periods_elapsed", None)
        if ytd_n is not None and d.get("period_basis") in ("YTD", "ANNUALIZED"):
            quality = "CERTIFIED" if ytd_n >= 6 else "RUN_RATE"
            d["annualization"] = {
                "periods_elapsed": ytd_n,
                "periods_per_year": 12,
                "quality": quality,
                "annualization_method": f"amount / {ytd_n} * 12",
            }
        return QuantifiedImpact.from_dict(d)

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_metric_type_classification(self, case):
        """Dimension 1 : metric_type."""
        qi = self._build_qi(case)
        assert qi.metric_type == case["expected"]["metric_type"], (
            f"[{case['id']}] {case['description']} — metric_type mismatch: "
            f"got {qi.metric_type}, expected {case['expected']['metric_type']}"
        )

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_period_basis_classification(self, case):
        """Dimension 2 : period_basis."""
        qi = self._build_qi(case)
        assert qi.period_basis == case["expected"]["period_basis"], (
            f"[{case['id']}] {case['description']} — period_basis mismatch: "
            f"got {qi.period_basis}, expected {case['expected']['period_basis']}"
        )

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_impact_nature_classification(self, case):
        """Dimension 3 : nature."""
        qi = self._build_qi(case)
        assert qi.nature == case["expected"]["nature"], (
            f"[{case['id']}] {case['description']} — nature mismatch: "
            f"got {qi.nature}, expected {case['expected']['nature']}"
        )

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_current_vs_historical(self, case):
        """Dimension 4 : is_current_period."""
        qi = self._build_qi(case)
        assert qi.is_current_period == case["expected"]["is_current_period"], (
            f"[{case['id']}] {case['description']} — is_current_period mismatch: "
            f"got {qi.is_current_period}, expected {case['expected']['is_current_period']}"
        )

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_is_unresolved(self, case):
        """Dimension 5 : is_unresolved."""
        qi = self._build_qi(case)
        assert qi.is_unresolved() == case["expected"]["is_unresolved"], (
            f"[{case['id']}] {case['description']} — is_unresolved mismatch: "
            f"got {qi.is_unresolved()}, expected {case['expected']['is_unresolved']}"
        )

    @pytest.mark.parametrize("case", [c for c in GOLDEN_CASES if "annualization_quality" in c["expected"]],
                             ids=[c["id"] for c in GOLDEN_CASES if "annualization_quality" in c["expected"]])
    def test_annualization_quality(self, case):
        """Dimension 6 : annualization_quality (cas avec YTD uniquement)."""
        qi = self._build_qi(case)
        assert qi.annualization_quality() == case["expected"]["annualization_quality"], (
            f"[{case['id']}] {case['description']} — annualization_quality mismatch"
        )

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_recurring_annual_equivalent(self, case):
        """Dimension 7 : recurring_annual_equivalent()."""
        qi = self._build_qi(case)
        expected = case["expected"]["recurring_annual_eq"]
        result = qi.recurring_annual_equivalent()
        if expected is None:
            assert result is None, (
                f"[{case['id']}] Expected None, got {result}"
            )
        else:
            assert result == pytest.approx(expected), (
                f"[{case['id']}] recurring_annual_equivalent mismatch: "
                f"got {result}, expected {expected}"
            )

    @pytest.mark.parametrize("case", [c for c in GOLDEN_CASES if "gross_margin_rate" in c["expected"]],
                             ids=[c["id"] for c in GOLDEN_CASES if "gross_margin_rate" in c["expected"]])
    def test_gross_margin_resolution(self, case):
        """Dimension 8 : gross_margin (taux + source)."""
        qi = self._build_qi(case)
        assert qi.gross_margin is not None
        assert qi.gross_margin.rate == case["expected"]["gross_margin_rate"]
        assert qi.gross_margin.source == case["expected"]["gross_margin_source"]


# ─────────────────────────────────────────────────────────────────────────────
# Matrice de précision agrégée — rapport humain-lisible
# ─────────────────────────────────────────────────────────────────────────────

class TestPrecisionMatrix:
    """
    Matrice de précision du modèle déterministe sur 10 golden semantic cases.
    Seuil minimum : ≥ 85 % par dimension.

    ATTENTION : cette matrice mesure la précision du MODÈLE DÉTERMINISTE,
    pas la précision d'extraction LLM. Voir docstring du module pour la
    distinction et la précondition Phase 4C.
    """

    DIMENSIONS = [
        "metric_type",
        "period_basis",
        "nature",
        "is_current_period",
        "is_unresolved",
    ]

    def _build_qi(self, case: dict) -> QuantifiedImpact:
        d = dict(case["llm_dict"])
        d["amount"] = case["legacy_amount"]
        ytd_n = d.pop("ytd_periods_elapsed", None)
        if ytd_n is not None and d.get("period_basis") in ("YTD", "ANNUALIZED"):
            quality = "CERTIFIED" if ytd_n >= 6 else "RUN_RATE"
            d["annualization"] = {
                "periods_elapsed": ytd_n,
                "periods_per_year": 12,
                "quality": quality,
                "annualization_method": f"amount / {ytd_n} * 12",
            }
        return QuantifiedImpact.from_dict(d)

    def test_precision_matrix_meets_threshold(self):
        """
        Vérifie que toutes les dimensions clés atteignent ≥ 85 % de précision
        sur les 10 cas représentatifs.
        """
        results = {dim: {"correct": 0, "total": 0} for dim in self.DIMENSIONS}

        for case in GOLDEN_CASES:
            qi = self._build_qi(case)
            exp = case["expected"]

            # metric_type
            results["metric_type"]["total"] += 1
            if qi.metric_type == exp["metric_type"]:
                results["metric_type"]["correct"] += 1

            # period_basis
            results["period_basis"]["total"] += 1
            if qi.period_basis == exp["period_basis"]:
                results["period_basis"]["correct"] += 1

            # nature
            results["nature"]["total"] += 1
            if qi.nature == exp["nature"]:
                results["nature"]["correct"] += 1

            # is_current_period
            results["is_current_period"]["total"] += 1
            if qi.is_current_period == exp["is_current_period"]:
                results["is_current_period"]["correct"] += 1

            # is_unresolved
            results["is_unresolved"]["total"] += 1
            if qi.is_unresolved() == exp["is_unresolved"]:
                results["is_unresolved"]["correct"] += 1

        # Rapport et vérification des seuils
        print("\n\n" + "=" * 60)
        print("MATRICE DE PRÉCISION PHASE 4B — 10 CAS RÉELS")
        print("=" * 60)
        all_pass = True
        for dim, counts in results.items():
            pct = 100 * counts["correct"] / counts["total"] if counts["total"] else 0
            status = "✅" if pct >= 85 else "❌"
            print(f"{status} {dim:<25} {counts['correct']}/{counts['total']} = {pct:.0f}%")
            if pct < 85:
                all_pass = False
        print("=" * 60)

        assert all_pass, (
            "Une ou plusieurs dimensions sont sous le seuil de 85 %. "
            "Voir rapport ci-dessus."
        )

    def test_economic_event_id_stability(self):
        """Dimension provenance : hash stable sur deux appels identiques."""
        h1 = build_event_hash("optilux", MetricType.REVENUE, ["GC_01"], "Sep 2019", None, "BILLING_DELAY")
        h2 = build_event_hash("optilux", MetricType.REVENUE, ["GC_01"], "Sep 2019", None, "BILLING_DELAY")
        assert h1 == h2, "event_id doit être déterministe"

    def test_all_10_cases_produce_valid_qi_objects(self):
        """Tous les 10 cas produisent un objet QuantifiedImpact valide (pas de crash)."""
        for case in GOLDEN_CASES:
            d = dict(case["llm_dict"])
            d["amount"] = case["legacy_amount"]
            d.pop("ytd_periods_elapsed", None)
            qi = QuantifiedImpact.from_dict(d)
            assert isinstance(qi, QuantifiedImpact), f"[{case['id']}] Expected QuantifiedImpact"
            # UNKNOWN ≠ 0 : amount doit être exactement ce qui a été passé
            assert qi.amount == case["legacy_amount"], (
                f"[{case['id']}] amount mismatch: got {qi.amount}, expected {case['legacy_amount']}"
            )
