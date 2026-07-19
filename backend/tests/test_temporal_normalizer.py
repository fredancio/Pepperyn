"""
test_temporal_normalizer.py — Unit tests for temporal column classification.

Covers the 5 required edge cases:
  1. 12 months N-1 + 6 months YTD N  → N is current (not N-1)
  2. Historical more detailed than current period
  3. Two complete years
  4. Budget N+1 + actual N
  5. Ambiguous temporal columns
"""
import pytest
from backend.services.temporal_normalizer import (
    PeriodRole,
    classify_columns,
    build_temporal_context,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def roles(headers: list[str]) -> list[str]:
    """Return just the period_role values as strings for easy assertion."""
    return [c.period_role.value for c in classify_columns(headers)]


def current_year(headers: list[str]) -> int | None:
    """Return detected current year from build_temporal_context."""
    ctx = build_temporal_context(headers)
    return ctx.get("detected_current_year")


# ─── Test 1: 12 months N-1 + 6 months YTD N ─────────────────────────────────

class TestYTDBeatsFrequency:
    """
    The canonical counter-example for frequency-only heuristics.
    N-1 (2018) appears 12 times. N (2019) appears only 6 times as YTD.
    Current year must be 2019 (YTD signal), NOT 2018 (frequency).
    """

    HEADERS_FR = [
        "Compte", "Libellé",
        # 12 months 2018
        "Jan 2018", "Fév 2018", "Mar 2018", "Avr 2018", "Mai 2018", "Jun 2018",
        "Jul 2018", "Aoû 2018", "Sep 2018", "Oct 2018", "Nov 2018", "Déc 2018",
        # 6 months YTD 2019
        "Jan 2019", "Fév 2019", "Mar 2019", "Avr 2019", "Mai 2019", "Juin YTD 2019",
    ]

    def test_current_year_is_2019_not_2018(self):
        yr = current_year(self.HEADERS_FR)
        assert yr == 2019, (
            f"Expected current_year=2019 (YTD signal), got {yr}. "
            "Frequency-only heuristic would return 2018 — this is the key regression."
        )

    def test_2018_months_are_historical(self):
        cols = classify_columns(self.HEADERS_FR)
        for col in cols:
            if col.year == 2018:
                assert col.period_role == PeriodRole.HISTORICAL_ACTUAL, (
                    f"Column '{col.header}' (year=2018) should be HISTORICAL_ACTUAL, "
                    f"got {col.period_role}"
                )

    def test_ytd_column_has_ytd_role(self):
        cols = classify_columns(self.HEADERS_FR)
        ytd_col = next((c for c in cols if c.header == "Juin YTD 2019"), None)
        assert ytd_col is not None
        assert ytd_col.period_role == PeriodRole.YTD

    def test_non_ytd_2019_are_current_actual(self):
        cols = classify_columns(self.HEADERS_FR)
        for col in cols:
            if col.year == 2019 and not col.is_ytd:
                assert col.period_role == PeriodRole.CURRENT_ACTUAL, (
                    f"Column '{col.header}' (2019, non-YTD) should be CURRENT_ACTUAL, "
                    f"got {col.period_role}"
                )


# ─── Test 2: Historical more detailed than current ────────────────────────────

class TestHistoricalMoreDetailed:
    """
    N-1 has monthly granularity (12 cols), N has only annual total.
    Historical detail must not mislead classification.
    """

    HEADERS = [
        "Code",
        # 12 monthly cols for N-1 (2021)
        "Jan 2021", "Fév 2021", "Mar 2021", "Avr 2021", "Mai 2021", "Jun 2021",
        "Jul 2021", "Aoû 2021", "Sep 2021", "Oct 2021", "Nov 2021", "Déc 2021",
        # Annual total for N (2022)
        "Total 2022",
    ]

    def test_current_year_is_2022(self):
        assert current_year(self.HEADERS) == 2022

    def test_2021_is_historical(self):
        cols = classify_columns(self.HEADERS)
        for col in cols:
            if col.year == 2021:
                assert col.period_role == PeriodRole.HISTORICAL_ACTUAL

    def test_2022_is_current(self):
        cols = classify_columns(self.HEADERS)
        col_2022 = next((c for c in cols if c.year == 2022), None)
        assert col_2022 is not None
        assert col_2022.period_role == PeriodRole.CURRENT_ACTUAL


# ─── Test 3: Two complete years ───────────────────────────────────────────────

class TestTwoCompleteYears:
    """
    Two full annual columns, one older than the other.
    The more recent year must be CURRENT_ACTUAL.
    """

    HEADERS = [
        "Poste", "Libellé",
        "Total 2022", "Total 2023",
    ]

    def test_current_year_is_2023(self):
        assert current_year(self.HEADERS) == 2023

    def test_2022_is_historical(self):
        cols = classify_columns(self.HEADERS)
        col = next((c for c in cols if c.year == 2022), None)
        assert col is not None
        assert col.period_role == PeriodRole.HISTORICAL_ACTUAL

    def test_2023_is_current(self):
        cols = classify_columns(self.HEADERS)
        col = next((c for c in cols if c.year == 2023), None)
        assert col is not None
        assert col.period_role == PeriodRole.CURRENT_ACTUAL


# ─── Test 4: Budget N+1 + actual N ───────────────────────────────────────────

class TestBudgetWithActual:
    """
    Budget for N+1 alongside actual for N.
    Budget must not be classified as current/historical actual.
    """

    HEADERS = [
        "Compte",
        "Jan 2023", "Fév 2023", "Mar 2023",  # actual N
        "Budget 2024", "Prévisionnel 2024",   # budget N+1
    ]

    def test_current_year_is_2023(self):
        # Budget columns should not influence current year detection
        assert current_year(self.HEADERS) == 2023

    def test_budget_columns_classified_as_budget(self):
        cols = classify_columns(self.HEADERS)
        budget_cols = [c for c in cols if "Budget" in c.header or "Prévisionnel" in c.header]
        assert len(budget_cols) == 2
        for col in budget_cols:
            assert col.period_role == PeriodRole.BUDGET, (
                f"Column '{col.header}' should be BUDGET, got {col.period_role}"
            )

    def test_2023_actuals_are_current(self):
        cols = classify_columns(self.HEADERS)
        actual_cols = [c for c in cols if c.year == 2023]
        assert len(actual_cols) == 3
        for col in actual_cols:
            assert col.period_role == PeriodRole.CURRENT_ACTUAL


# ─── Test 5: Ambiguous columns ────────────────────────────────────────────────

class TestAmbiguousColumns:
    """
    Mix of columns with no year, partial info, and typical non-temporal labels.
    Non-temporal headers must not be misclassified.
    """

    HEADERS = [
        "Code PCMN",          # no temporal info
        "Libellé",            # no temporal info
        "Total",              # no temporal info
        "Variation %",        # no temporal info
        "Jan 2022",           # temporal
        "N-1",                # prior_year label
        "Cumul YTD",          # YTD without explicit year
        "Forecast",           # forecast without year
    ]

    def test_non_temporal_headers_are_unknown(self):
        cols = classify_columns(self.HEADERS)
        non_temporal = [c for c in cols if c.header in ("Code PCMN", "Libellé", "Total", "Variation %")]
        for col in non_temporal:
            assert col.period_role == PeriodRole.UNKNOWN, (
                f"Header '{col.header}' should be UNKNOWN, got {col.period_role}"
            )

    def test_prior_year_label_classified_correctly(self):
        cols = classify_columns(self.HEADERS)
        col = next((c for c in cols if c.header == "N-1"), None)
        assert col is not None
        assert col.period_role == PeriodRole.PRIOR_YEAR

    def test_ytd_without_year_classified_as_ytd(self):
        cols = classify_columns(self.HEADERS)
        col = next((c for c in cols if c.header == "Cumul YTD"), None)
        assert col is not None
        assert col.period_role == PeriodRole.YTD

    def test_forecast_without_year_classified_as_forecast(self):
        cols = classify_columns(self.HEADERS)
        col = next((c for c in cols if c.header == "Forecast"), None)
        assert col is not None
        assert col.period_role == PeriodRole.FORECAST


# ─── Test 6: build_temporal_context output shape ─────────────────────────────

class TestBuildTemporalContext:
    """Sanity checks for the LLM context dict."""

    def test_output_has_required_keys(self):
        ctx = build_temporal_context(["Jan 2023", "Déc 2022", "Budget 2024"])
        assert "detected_current_year" in ctx
        assert "columns_by_role" in ctx
        assert "classification_note" in ctx

    def test_columns_by_role_groups_correctly(self):
        ctx = build_temporal_context(["Jan 2023", "Budget 2024"])
        by_role = ctx["columns_by_role"]
        assert "CURRENT_ACTUAL" in by_role
        assert "Jan 2023" in by_role["CURRENT_ACTUAL"]
        assert "BUDGET" in by_role
        assert "Budget 2024" in by_role["BUDGET"]

    def test_empty_headers_returns_none_year(self):
        ctx = build_temporal_context([])
        assert ctx["detected_current_year"] is None

    def test_non_temporal_only_headers(self):
        ctx = build_temporal_context(["Code", "Libellé", "Total"])
        assert ctx["detected_current_year"] is None


# ─── Test 7: 2-digit year parsing ────────────────────────────────────────────

class TestTwoDigitYearParsing:
    """
    Some French P&L files use 'Jan-14', 'Sep-19' style headers.
    These must be parsed correctly.
    """

    HEADERS_OPTILUX = [
        "Code", "Libellé",
        # 12 months 2014 (2-digit year)
        "Jan-14", "Fév-14", "Mar-14", "Avr-14", "Mai-14", "Jun-14",
        "Jul-14", "Aoû-14", "Sep-14", "Oct-14", "Nov-14", "Déc-14",
        # columns for 2019
        "Déc-19",
    ]

    def test_2014_year_parsed(self):
        cols = classify_columns(self.HEADERS_OPTILUX)
        col_jan14 = next((c for c in cols if c.header == "Jan-14"), None)
        assert col_jan14 is not None
        assert col_jan14.year == 2014, f"Expected year=2014, got {col_jan14.year}"

    def test_2019_is_current_over_2014(self):
        yr = current_year(self.HEADERS_OPTILUX)
        assert yr == 2019, (
            f"Expected current_year=2019 (most recent), got {yr}. "
            "2014 has 12 occurrences, 2019 has 1 — frequency must not win."
        )

    def test_2014_columns_are_historical(self):
        cols = classify_columns(self.HEADERS_OPTILUX)
        for col in cols:
            if col.year == 2014:
                assert col.period_role == PeriodRole.HISTORICAL_ACTUAL, (
                    f"'{col.header}' should be HISTORICAL_ACTUAL"
                )

    def test_dec_2019_is_current(self):
        cols = classify_columns(self.HEADERS_OPTILUX)
        col = next((c for c in cols if c.header == "Déc-19"), None)
        assert col is not None
        assert col.period_role == PeriodRole.CURRENT_ACTUAL
