"""
fru_sign_convention_detector.py — FRU v0 STUB: expense sign-convention
detector for Epistemic Dialogue's first executable vertical slice.

Scope, per `docs/Architecture/Cognitive/FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`
and the mission that authorized this implementation (2026-08-09): the
smallest deterministic detector that answers exactly one question —

    Does the source strongly suggest that expenses are represented as
    positive absolute values whose economic meaning comes from
    account/post nature rather than raw numeric sign?

THIS IS NOT GENERAL FRU. It is a stub, honestly labeled (mirrors Knowledge
Model v0's own Phidani-loop tests, which used a minimal stub rather than
real FRU). It answers one subject (`EXPENSE_SIGN_CONVENTION`) for one
validated file shape (Belgian PCMN-style account codes). Extending this to
arbitrary financial representation, other subjects, or other chart-of-
accounts conventions is explicitly out of scope — that is the next,
larger, not-yet-authorized mission.

WHAT THIS MODULE NEVER DOES:
  - No LLM call, anywhere, for any reason.
  - No general chart-of-accounts engine — the charge-code prefix set
    below is the minimum needed to interpret Phidani's own codes, not a
    general Belgian PCMN library.
  - No fabricated certainty — degrades honestly to UNKNOWN whenever the
    two signals below disagree or neither is available, exactly as
    `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md` §3/§6 specifies. Never
    guesses.

TWO DETERMINISTIC SIGNALS, VALIDATED AGAINST THE REAL PHIDANI.XLSX
(direct inspection, 2026-08-09 — see the implementation mission's own
final report for exact evidence, not asserted from memory):

  1. ACCOUNT-CODE-RANGE SIGNAL — rows whose account code falls in the
     Belgian PCMN charge range (60-66, `_CHARGE_CODE_PREFIXES` below).
     Real Phidani.xlsx: 289 charge-coded observations across the sheet,
     283 (97.9%) non-negative. The 6 negative observations are legitimate
     documented exceptions (e.g. "Utilisations et reprises (-)",
     "Récupération précompte professionnel" — refunds/reversals, whose
     own label in the source already flags them as an adjustment) —
     NOT evidence of a different sign convention for ordinary charges.
     This is exactly why the signal is a MAJORITY/consistency check
     (`_NONNEG_MAJORITY_THRESHOLD`), never an "any negative disqualifies"
     rule — a single-exception veto would be fragile and would
     misclassify this real file. A genuinely mixed distribution (no
     clear majority either way) still correctly degrades to "signal
     absent" rather than guessing.
  2. ARITHMETIC/SUBTOTAL SIGNAL — Phidani.xlsx has a row whose account
     code is the bare aggregate `"60"` (charges subtotal, e.g.
     `=SUM(C32:C33)`), and a later "Marge brute" row whose formula
     SUBTRACTS that subtotal's cell from revenue (`=C31-C34`, confirmed
     identical pattern across every period column C through... in the
     real file). Subtraction of a *positive* charges subtotal to compute
     a margin is only arithmetically sound under ABSOLUTE_POSITIVE — an
     ADDITION pattern would instead indicate SIGNED_NATURAL. This module
     searches for whichever pattern actually exists, on the real cell
     reference of the "60" row, in the given period column — never
     hardcoded to one cell address.

Combination rule (mirrors `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md` §3
exactly): both signals agree -> STRONG_INFERENCE. Only one signal present
(the other genuinely absent, not contradicting) -> HYPOTHESIS. Both
present but disagree, or neither present -> UNKNOWN, candidate value None.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Belgian PCMN charge-account prefixes (classes 60-66) — the minimum
# needed to interpret Phidani's own codes (mission-scoped, not a general
# chart-of-accounts library; see module docstring).
_CHARGE_CODE_PREFIXES = {"60", "61", "62", "63", "64", "65", "66"}

# Majority threshold for the code-range signal: >=90% non-negative ->
# ABSOLUTE_POSITIVE; <=10% non-negative (i.e. >=90% negative) ->
# SIGNED_NATURAL; anything genuinely mixed in between -> signal absent
# (never guesses). Chosen because it tolerates the real file's own
# documented exceptions (2.1% negative) without being fooled by a
# genuinely different convention.
_NONNEG_MAJORITY_THRESHOLD = 0.9

ABSOLUTE_POSITIVE = "ABSOLUTE_POSITIVE"
SIGNED_NATURAL = "SIGNED_NATURAL"


@dataclass(frozen=True)
class Candidate:
    """FRU's output for the REASON step (contract §3) — internal to the
    detector/orchestration boundary, never itself persisted or passed to
    KnowledgeModel. `value` is None exactly when `tier == "UNKNOWN"`."""
    value: Optional[str]
    tier: str  # "STRONG_INFERENCE" | "HYPOTHESIS" | "UNKNOWN"


def _code_range_signal(charge_values: list[float]) -> Optional[str]:
    """Majority/consistency signal (candidate signal 1, module docstring).
    Returns None (signal absent) if there is no data, or if the
    distribution is genuinely mixed with no clear majority either way —
    never guesses."""
    if not charge_values:
        return None
    nonneg = sum(1 for v in charge_values if v >= 0)
    ratio = nonneg / len(charge_values)
    if ratio >= _NONNEG_MAJORITY_THRESHOLD:
        return ABSOLUTE_POSITIVE
    if ratio <= (1 - _NONNEG_MAJORITY_THRESHOLD):
        return SIGNED_NATURAL
    return None


def detect_expense_sign_convention(
    charge_values: list[float],
    charges_subtracted_in_margin_formula: Optional[bool],
) -> Candidate:
    """
    Pure, deterministic core (unit-testable with synthetic data,
    Phase 15's adversarial matrix) — no file I/O here.

    Args:
        charge_values: observed numeric values for account-coded charge
            rows (candidate signal 1), for a single period column.
        charges_subtracted_in_margin_formula: True if a formula subtracts
            the charges-subtotal cell (signal -> ABSOLUTE_POSITIVE), False
            if a formula adds it instead (signal -> SIGNED_NATURAL), None
            if no such formula relationship was found (signal absent).

    Returns:
        Candidate — never fabricates a value when the two signals
        disagree or neither is available (module docstring).
    """
    codes_signal = _code_range_signal(charge_values)
    if charges_subtracted_in_margin_formula is True:
        arithmetic_signal = ABSOLUTE_POSITIVE
    elif charges_subtracted_in_margin_formula is False:
        arithmetic_signal = SIGNED_NATURAL
    else:
        arithmetic_signal = None

    if codes_signal is not None and arithmetic_signal is not None:
        if codes_signal == arithmetic_signal:
            return Candidate(value=codes_signal, tier="STRONG_INFERENCE")
        return Candidate(value=None, tier="UNKNOWN")  # disagree -> never guess

    if codes_signal is not None:
        return Candidate(value=codes_signal, tier="HYPOTHESIS")
    if arithmetic_signal is not None:
        return Candidate(value=arithmetic_signal, tier="HYPOTHESIS")
    return Candidate(value=None, tier="UNKNOWN")


def detect_expense_sign_convention_from_workbook(
    path: str, period_column: int, sheet_name: Optional[str] = None,
) -> Candidate:
    """
    Real-file adapter (Phase 14) — the only place this module touches
    openpyxl. Extracts the two signals from an actual workbook shaped
    like Phidani.xlsx and delegates to the pure core above. Never used
    by the synthetic adversarial matrix tests (Phase 15), which call
    `detect_expense_sign_convention` directly.

    `period_column` is a 1-indexed column number (e.g. 3 for column C),
    matching openpyxl's own convention.
    """
    import openpyxl  # local import: this module's pure core has zero
    # dependency on openpyxl; only this adapter function does.

    wb_formulas = openpyxl.load_workbook(path, data_only=False)
    wb_values = openpyxl.load_workbook(path, data_only=True)
    ws_f = wb_formulas[sheet_name] if sheet_name else wb_formulas.active
    ws_v = wb_values[sheet_name] if sheet_name else wb_values.active

    charge_values: list[float] = []
    charges_subtotal_row: Optional[int] = None

    for row in ws_f.iter_rows(min_col=1, max_col=1):
        cell = row[0]
        code = cell.value
        if code is None:
            continue
        if isinstance(code, str) and code.strip() == "60":
            charges_subtotal_row = cell.row
            continue
        try:
            icode = int(code)
        except (TypeError, ValueError):
            continue
        if icode <= 99:
            # Excludes bare aggregate codes (e.g. a hypothetical "70"
            # parsed as int) — real account lines in this file are far
            # more than two digits (604000, 611001, ...).
            continue
        prefix = str(icode)[:2]
        if prefix not in _CHARGE_CODE_PREFIXES:
            continue
        v = ws_v.cell(row=cell.row, column=period_column).value
        if isinstance(v, (int, float)):
            charge_values.append(float(v))

    charges_subtracted: Optional[bool] = None
    if charges_subtotal_row is not None:
        col_letter = openpyxl.utils.get_column_letter(period_column)
        target_ref = f"{col_letter}{charges_subtotal_row}"
        minus_pattern = re.compile(rf"-\s*{re.escape(target_ref)}\b")
        plus_pattern = re.compile(rf"\+\s*{re.escape(target_ref)}\b")
        for row in ws_f.iter_rows(min_col=period_column, max_col=period_column):
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    if minus_pattern.search(cell.value):
                        charges_subtracted = True
                        break
                    if plus_pattern.search(cell.value):
                        charges_subtracted = False
                        break
            if charges_subtracted is not None:
                break

    return detect_expense_sign_convention(charge_values, charges_subtracted)
