"""
temporal_normalizer.py — Dynamic temporal column classification.

Classifies Excel column headers into period roles without hardcoding specific
years. Uses a hierarchical signal approach (NOT frequency-only).

Priority hierarchy for determining "current year":
  1. Explicit CURRENT / ACTUAL / N labels in headers
  2. Most recent year among YTD-associated columns
  3. Max year across non-budget / non-forecast columns
  4. Frequency as secondary tiebreaker only (when years are tied)

This correctly handles the case of 12 months N-1 + 6 months YTD N:
  - N-1 appears 12× (most frequent) → WRONG to call it current
  - N appears 6× as YTD → RIGHT: YTD = current year candidate

PeriodRole enum values:
  CURRENT_ACTUAL    — column belongs to the current fiscal year (actual/realized)
  HISTORICAL_ACTUAL — column belongs to a prior year (actual/realized)
  PRIOR_YEAR        — explicitly labeled N-1 / année précédente
  BUDGET            — budget / prévisionnel column
  FORECAST          — forecast / projection column
  YTD               — year-to-date cumulative column (current or near-current)
  UNKNOWN           — cannot be classified
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── PeriodRole ──────────────────────────────────────────────────────────────

class PeriodRole(str, Enum):
    CURRENT_ACTUAL    = "CURRENT_ACTUAL"
    HISTORICAL_ACTUAL = "HISTORICAL_ACTUAL"
    PRIOR_YEAR        = "PRIOR_YEAR"
    BUDGET            = "BUDGET"
    FORECAST          = "FORECAST"
    YTD               = "YTD"
    UNKNOWN           = "UNKNOWN"


# ─── TemporalColumn ──────────────────────────────────────────────────────────

@dataclass
class TemporalColumn:
    header: str
    period_role: PeriodRole = PeriodRole.UNKNOWN
    year: Optional[int] = None
    month: Optional[int] = None        # 1–12, or None
    is_ytd: bool = False
    is_budget: bool = False
    is_forecast: bool = False
    is_prior_year: bool = False        # explicitly labeled N-1
    is_current_explicit: bool = False  # explicitly labeled N / current
    signals: list[str] = field(default_factory=list)  # debug: matched signals


# ─── Internal constants ───────────────────────────────────────────────────────

# French and English month abbreviations → month number
_MONTH_MAP: dict[str, int] = {
    # French full
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "décembre": 12,
    # French abbrev (3-char)
    "jan": 1, "fév": 2, "mar": 3, "avr": 4,
    "jui": 6, "jul": 7, "aoû": 8, "sep": 9, "oct": 10, "nov": 11, "déc": 12,
    # English full
    "january": 1, "february": 2, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
    # English abbrev
    "feb": 2, "apr": 4, "aug": 8, "dec": 12,
    # Numeric short (some files use "01", "02"…)
}

# Patterns that mark a column as budget
_BUDGET_PATTERNS = re.compile(
    r"\b(budget|budg|prévi|previsio|prévision|prévisionnel|previsionnel)\b",
    re.IGNORECASE,
)

# Patterns that mark a column as forecast / projection
_FORECAST_PATTERNS = re.compile(
    r"\b(forecast|fcst|proj|projection|estimat|estimate|n\s*\+\s*1)\b",
    re.IGNORECASE,
)

# Patterns that mark a column as YTD
_YTD_PATTERNS = re.compile(
    r"\b(ytd|y\.t\.d|cumul|cumulé|cumulatif|année\s+en\s+cours|nine.month|"
    r"six.month|nine\s+m|six\s+m|(\d+)\s*m\s+ytd|(\d+)\s*m\s+cum)\b",
    re.IGNORECASE,
)

# Month-count YTD like "9M", "6M", "3M" standing alone
_MONTH_COUNT_YTD = re.compile(r"(?<!\d)(\d{1,2})[mM](?!\d)")

# Patterns that mark a column as prior year (N-1)
_PRIOR_YEAR_PATTERNS = re.compile(
    r"\b(n\s*-\s*1|année\s+précédente|annee\s+precedente|prior\s+year|previous\s+year|"
    r"last\s+year|exercice\s+précédent)\b",
    re.IGNORECASE,
)

# Patterns that mark a column as explicitly current / actual
_CURRENT_EXPLICIT_PATTERNS = re.compile(
    r"\b(current|en\s+cours|réel|reel|réalisé|realise|actual|n\b(?!\s*[-+]\s*\d))\b",
    re.IGNORECASE,
)

# 4-digit year
_YEAR_RE = re.compile(r"\b(19\d{2}|20[0-3]\d)\b")

# 2-digit year (ambiguous — only used when embedded next to a month token)
_YEAR2_RE = re.compile(r"\b(\d{2})\b")


# ─── Parsing ─────────────────────────────────────────────────────────────────

def _parse_column(header: str) -> TemporalColumn:
    """
    Parse a single column header and extract temporal signals.
    """
    col = TemporalColumn(header=header)
    h = header.strip()
    signals: list[str] = []

    # ── Boolean signals ────────────────────────────────────────────────────
    if _BUDGET_PATTERNS.search(h):
        col.is_budget = True
        signals.append("budget")

    if _FORECAST_PATTERNS.search(h):
        col.is_forecast = True
        signals.append("forecast")

    if _YTD_PATTERNS.search(h) or _MONTH_COUNT_YTD.search(h):
        col.is_ytd = True
        signals.append("ytd")

    if _PRIOR_YEAR_PATTERNS.search(h):
        col.is_prior_year = True
        signals.append("prior_year")

    if _CURRENT_EXPLICIT_PATTERNS.search(h):
        col.is_current_explicit = True
        signals.append("current_explicit")

    # ── Year extraction ────────────────────────────────────────────────────
    year_matches = _YEAR_RE.findall(h)
    if year_matches:
        # If multiple years in header, take the latest (e.g. "Jan 2019 - Dec 2019")
        col.year = max(int(y) for y in year_matches)
        signals.append(f"year={col.year}")
    else:
        # Try to extract 2-digit year if a month token is present
        month_found = _extract_month(h)
        if month_found is not None:
            y2_matches = _YEAR2_RE.findall(h)
            for y2 in y2_matches:
                y2_int = int(y2)
                # Heuristic: 00–39 → 2000–2039, 40–99 → 1940–1999
                if 0 <= y2_int <= 39:
                    col.year = 2000 + y2_int
                else:
                    col.year = 1900 + y2_int
                signals.append(f"year2={col.year}")
                break

    # ── Month extraction ───────────────────────────────────────────────────
    col.month = _extract_month(h)
    if col.month:
        signals.append(f"month={col.month}")

    col.signals = signals
    return col


def _extract_month(header: str) -> Optional[int]:
    """Return the month number (1-12) found in the header, or None."""
    h_lower = header.lower()
    # Try named months (longest match first to avoid 'mar' matching 'mars')
    for name, num in sorted(_MONTH_MAP.items(), key=lambda x: -len(x[0])):
        if name in h_lower:
            return num
    # Try numeric month pattern like "M01", "M02", "/01/"
    m = re.search(r"(?:m|/)0?([1-9]|1[0-2])(?:/|\b)", h_lower)
    if m:
        return int(m.group(1))
    return None


# ─── Current-year determination ───────────────────────────────────────────────

def _determine_current_year(cols: list[TemporalColumn]) -> Optional[int]:
    """
    Determine the current (most recent actual) year using the signal hierarchy:
      1. Explicit CURRENT / N / ACTUAL label
      2. Most recent year in YTD-flagged columns
      3. Max year among non-budget, non-forecast columns
      4. Frequency as secondary tiebreaker (only if tied in recency)
    """
    years_with_years = [c for c in cols if c.year is not None]
    if not years_with_years:
        return None

    # ── Signal 1: explicit current/actual marker ──────────────────────────
    explicit_current_years = [
        c.year for c in years_with_years
        if c.is_current_explicit and not c.is_budget and not c.is_forecast
    ]
    if explicit_current_years:
        return max(explicit_current_years)

    # ── Signal 2: most recent year among YTD columns ──────────────────────
    # YTD columns belong to the "in-progress" (current) year — even if they
    # appear less frequently than a full prior year.
    ytd_years = [
        c.year for c in years_with_years
        if c.is_ytd and not c.is_budget and not c.is_forecast
    ]
    if ytd_years:
        return max(ytd_years)

    # ── Signal 3: max year among actual (non-budget, non-forecast) columns ─
    actual_years = [
        c.year for c in years_with_years
        if not c.is_budget and not c.is_forecast
    ]
    if actual_years:
        # Use max year (most recent actual = current)
        max_actual = max(actual_years)
        return max_actual

    # ── Signal 4: max year overall (fallback) ────────────────────────────
    return max(c.year for c in years_with_years)


# ─── Public API ──────────────────────────────────────────────────────────────

def classify_columns(headers: list[str]) -> list[TemporalColumn]:
    """
    Classify a list of column headers into temporal period roles.

    Args:
        headers: Raw column header strings from the Excel sheet.

    Returns:
        List of TemporalColumn objects, one per header, in the same order.

    The algorithm uses a hierarchical approach — NOT frequency-only:
      - YTD signal → identifies current year even if it appears only once
      - Most recent year among actuals → current, even if less frequent
      - Frequency used only as final tiebreaker
    """
    parsed = [_parse_column(h) for h in headers]
    current_year = _determine_current_year(parsed)

    for col in parsed:
        col.period_role = _classify_single(col, current_year)

    return parsed


def _classify_single(col: TemporalColumn, current_year: Optional[int]) -> PeriodRole:
    """Assign PeriodRole to a single parsed column."""
    # ── Explicit prior-year label ──────────────────────────────────────────
    if col.is_prior_year:
        return PeriodRole.PRIOR_YEAR

    # ── Budget ────────────────────────────────────────────────────────────
    if col.is_budget:
        return PeriodRole.BUDGET

    # ── Forecast ─────────────────────────────────────────────────────────
    if col.is_forecast:
        return PeriodRole.FORECAST

    # ── YTD ──────────────────────────────────────────────────────────────
    if col.is_ytd:
        return PeriodRole.YTD

    # ── No year detected → UNKNOWN ────────────────────────────────────────
    if col.year is None:
        return PeriodRole.UNKNOWN

    # ── Year-based classification ─────────────────────────────────────────
    if current_year is None:
        return PeriodRole.UNKNOWN

    if col.year == current_year:
        return PeriodRole.CURRENT_ACTUAL

    if col.year < current_year:
        return PeriodRole.HISTORICAL_ACTUAL

    # col.year > current_year → future period without explicit budget/forecast signal
    return PeriodRole.FORECAST


# ─── Summary helper ──────────────────────────────────────────────────────────

def build_temporal_context(headers: list[str]) -> dict:
    """
    Build a dict suitable for injection into the LLM context.
    Tells the LLM which columns are current vs historical vs budget.
    """
    cols = classify_columns(headers)
    current_year = _determine_current_year(cols)

    by_role: dict[str, list[str]] = {}
    for col in cols:
        role = col.period_role.value
        by_role.setdefault(role, []).append(col.header)

    result: dict = {
        "detected_current_year": current_year,
        "columns_by_role": by_role,
        "classification_note": (
            "Classification dynamique (sans hardcoding d'années). "
            "CURRENT_ACTUAL = exercice en cours (données réalisées). "
            "HISTORICAL_ACTUAL = exercice(s) antérieur(s) réalisé(s). "
            "YTD = cumul année en cours. "
            "BUDGET = budget/prévisionnel. "
            "PRIOR_YEAR = N-1 explicite. "
            "FORECAST = projection future."
        ),
    }
    return result
