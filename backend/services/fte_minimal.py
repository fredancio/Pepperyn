"""
fte_minimal.py — Financial Time Engine v0 (deterministic kernel only).

Scope, per docs/Architecture/FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md
(narrowed twice through explicit arbitration, 2026-08-08): the smallest
deterministic capability that lets Pepperyn compare newly received
financial information against prior known information for the same
Engagement, without ever inventing a period the data doesn't support and
without ever confusing business time with knowledge time or decision time.

WHAT THIS MODULE DOES:
  - Reads the already-deterministic classification produced by
    temporal_normalizer.build_temporal_context() (never re-parses headers
    itself — see that module's docstring for the "actual_periods" field
    this relies on).
  - Resolves the newest business-time boundary observed in the CURRENT
    dataset (a date, never a fabricated default).
  - Reads the single historical fact persisted for this purpose
    (evidence_ledger_entries.observed_period_end, migration v23).
  - Compares the two, deterministically, into exactly one of five named
    states: NEW, DUPLICATE, GAP, OUT_OF_ORDER, UNKNOWN.
  - Derives YTD coverage and rolling-12 availability, honestly (never
    fabricating missing months), purely from the current dataset's own
    columns — never reconstructed from persisted history.

WHAT THIS MODULE NEVER DOES (contract §16, §21 — negative contract):
  - No closure/close-confidence claim of any kind, qualified or not.
  - No LLM call, anywhere, for any reason.
  - No read of QuantifiedImpact.temporal_role — that field is populated
    (if at all) by non-deterministic LLM output despite its misleading
    docstring; using it here would silently reintroduce an LLM dependency
    into a kernel that must stay at zero. See
    tests/test_fte_minimal.py::TestTemporalRoleIsolation.
  - No cadence/granularity assumption to detect a gap — contiguity is
    checked against the actual observed date boundaries only.
  - No new persistent object (no PeriodObservation/FiscalPeriod/
    BusinessMoment table or aggregate) — this module is a pure projection
    over data that already exists (temporal_normalizer's output) plus one
    additive column (observed_period_end).
  - No mutation of DecisionArc, no mutation of Evidence Ledger rows
    (evidence_ledger_entries is immutable by trigger — this module only
    ever contributes a value at INSERT time, in evidence_ledger_service.py,
    never an UPDATE).
"""
from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Comparison states ──────────────────────────────────────────────────────
# Exactly the five named in the accepted contract / mission Phase 4 — no
# additional state invented for convenience.

PERIOD_RELATIONSHIP_STATES = ("NEW", "DUPLICATE", "GAP", "OUT_OF_ORDER", "UNKNOWN")


@dataclass(frozen=True)
class CurrentPeriodBounds:
    """The newest observed period in the CURRENT dataset — derived fresh
    at every analysis, never persisted as such (contract §10/§11)."""
    start: date
    end: date


# ── Current-dataset resolution (derived, never persisted) ──────────────────

def _resolved_actual_periods(temporal_context: Optional[dict]) -> list[tuple[int, int]]:
    """
    Extract (year, month) pairs from temporal_context["actual_periods"]
    for entries where BOTH year and month are resolvable. Entries with a
    resolvable year but no resolvable month are deliberately excluded —
    a business-time boundary requires both (Article III: absence stays
    absence, never defaulted to a fabricated month).
    """
    if not temporal_context:
        return []
    periods = temporal_context.get("actual_periods") or []
    resolved: list[tuple[int, int]] = []
    for p in periods:
        if not isinstance(p, dict):
            continue
        year, month = p.get("year"), p.get("month")
        if isinstance(year, int) and isinstance(month, int) and 1 <= month <= 12:
            resolved.append((year, month))
    return resolved


def resolve_current_period_bounds(
    temporal_context: Optional[dict],
) -> Optional[CurrentPeriodBounds]:
    """
    Newest observed period in the current dataset, as [first day, last
    day] of the most recent (year, month) among actually-classified
    columns (CURRENT_ACTUAL/HISTORICAL_ACTUAL — never BUDGET/FORECAST/
    PRIOR_YEAR/YTD/UNKNOWN columns, per temporal_normalizer's own role
    classification).

    Returns None if no column resolves both a year and a month — this is
    an honest UNKNOWN, never a fallback to the analysis date or the
    system date.
    """
    resolved = _resolved_actual_periods(temporal_context)
    if not resolved:
        return None
    year, month = max(resolved)
    last_day = calendar.monthrange(year, month)[1]
    return CurrentPeriodBounds(start=date(year, month, 1), end=date(year, month, last_day))


def resolve_newest_observed_period_end(temporal_context: Optional[dict]) -> Optional[date]:
    """
    The single value written to evidence_ledger_entries.observed_period_end
    (migration v23) — the end boundary of resolve_current_period_bounds(),
    or None. This is the ONLY thing this module persists; everything else
    is derived at read time.
    """
    bounds = resolve_current_period_bounds(temporal_context)
    return bounds.end if bounds is not None else None


# ── Historical read (the one persisted fact) ────────────────────────────────

def resolve_previous_observed_period_end(
    supabase: Any,
    company_id: str,
    entity_id: Optional[str],
) -> Optional[date]:
    """
    Reads the most recently persisted observed_period_end for this
    Engagement scope, excluding NULLs, ordered by created_at descending.

    Scoping (contract §6, mission Phase 12): entity_id today, because
    Entity:Engagement is transitionally 1:1 (STRATEGIC_DEFERRED_WORK_
    REGISTER.md §1.2.a). This is NOT encoded as permanent FTE ontology —
    when 1:N Engagements become real, this function's scope key changes
    from entity_id to engagement_id; no new deferred-work entry is needed,
    §1.2.a already names and tracks that trigger.

    Never raises: a read failure here must never break the caller (same
    non-blocking discipline as evidence_ledger_service.save_evidence_capture
    and evidence_query_service — an enrichment read, not a critical path).
    Returns None on any error or absence, exactly as it would for "no
    prior observed period" — the caller (classify_period_relationship)
    treats both identically (NEW), which is correct: a silent read failure
    must never be misreported as a deterministic GAP or OUT_OF_ORDER.
    """
    if not company_id:
        return None
    try:
        query = (
            supabase.from_("evidence_ledger_entries")
            .select("observed_period_end")
            .eq("company_id", company_id)
            .not_.is_("observed_period_end", "null")
            .order("created_at", desc=True)
            .limit(1)
        )
        if entity_id:
            query = query.eq("entity_id", entity_id)
        result = query.execute()
    except Exception as e:
        logger.error(
            "[FTE] resolve_previous_observed_period_end failed — company_id=%s | %s: %s",
            company_id, type(e).__name__, e,
        )
        return None

    rows = result.data or []
    if not rows:
        return None
    raw = rows[0].get("observed_period_end")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        logger.error("[FTE] unparsable observed_period_end value: %r", raw)
        return None


# ── Comparison (pure, deterministic) ────────────────────────────────────────

def classify_period_relationship(
    current: Optional[CurrentPeriodBounds],
    previous_period_end: Optional[date],
) -> str:
    """
    Deterministic relationship between the current dataset's newest
    observed period and the last known one. Returns exactly one of
    PERIOD_RELATIONSHIP_STATES.

    Contiguity ("GAP" vs "NEW") is decided purely from the two actual date
    boundaries observed (previous end, current start) — never from an
    assumed cadence/granularity. This works identically for monthly,
    weekly, quarterly, or any other actual spacing; it does not assume
    monthly reporting merely because Phidani's dates happen to look
    monthly (mission Phase 9 — "do not infer monthly cadence merely
    because dates look monthly").
    """
    if previous_period_end is None:
        # No prior observed period at all — nothing to compare against.
        # The current information is, by definition, new.
        return "NEW"
    if current is None:
        # Current dataset's period could not be determined deterministically.
        return "UNKNOWN"
    if current.end == previous_period_end:
        return "DUPLICATE"
    if current.end < previous_period_end:
        return "OUT_OF_ORDER"
    # current.end > previous_period_end
    gap_days = (current.start - previous_period_end).days
    if gap_days == 1:
        return "NEW"
    if gap_days > 1:
        return "GAP"
    # gap_days <= 0: current starts before or on the previous boundary but
    # ends after it — an overlapping/ambiguous shape, not a clean forward
    # extension. Treated as OUT_OF_ORDER rather than invented as a sixth
    # state.
    return "OUT_OF_ORDER"


# ── YTD coverage (derived, honest about gaps) ───────────────────────────────

def resolve_ytd_coverage(temporal_context: Optional[dict]) -> dict:
    """
    YTD coverage for the current dataset's own detected current year,
    computed purely from the months actually present — never assuming
    a missing month is zero, never claiming complete coverage that the
    data doesn't support (mission Phase 10).

    Returns:
        {"status": "unavailable"} — no resolvable current-year months.
        {"status": "complete", "months_present": [1..N]} — every month
            from 1 through the newest present month is actually present
            (contiguous from January, no gaps).
        {"status": "incomplete", "months_present": [...], "months_missing": [...]}
            — at least one month between 1 and the newest present month
            is absent (e.g. March missing from Jan..Sep).
    """
    resolved = _resolved_actual_periods(temporal_context)
    if not resolved:
        return {"status": "unavailable"}

    newest_year = max(y for y, _m in resolved)
    months_present = sorted({m for y, m in resolved if y == newest_year})
    if not months_present:
        return {"status": "unavailable"}

    newest_month = max(months_present)
    expected = list(range(1, newest_month + 1))
    missing = [m for m in expected if m not in months_present]
    if missing:
        return {
            "status": "incomplete",
            "months_present": months_present,
            "months_missing": missing,
        }
    return {"status": "complete", "months_present": months_present}


# ── Rolling-12 (derived, honest about insufficient history) ────────────────

def resolve_rolling_12(temporal_context: Optional[dict]) -> dict:
    """
    Rolling-12 availability, assessed ONLY from the current dataset's own
    columns (this module does not reconstruct historical months from
    persisted data — only observed_period_end, a single boundary, is
    persisted; see contract §11). A file spanning fewer than 12 contiguous
    actual months honestly reports insufficient history — never
    extrapolated, never LLM-derived, never a fabricated window.
    """
    resolved = sorted(set(_resolved_actual_periods(temporal_context)))
    if len(resolved) < 12:
        return {"status": "insufficient_history", "months_available": len(resolved)}

    # Check the most recent 12 (year, month) pairs are actually contiguous.
    newest = resolved[-12:]
    for i in range(1, len(newest)):
        prev_y, prev_m = newest[i - 1]
        cur_y, cur_m = newest[i]
        expected_y, expected_m = (prev_y, prev_m + 1) if prev_m < 12 else (prev_y + 1, 1)
        if (cur_y, cur_m) != (expected_y, expected_m):
            return {"status": "insufficient_history", "months_available": len(resolved)}

    return {
        "status": "available",
        "window_start": {"year": newest[0][0], "month": newest[0][1]},
        "window_end": {"year": newest[-1][0], "month": newest[-1][1]},
    }
