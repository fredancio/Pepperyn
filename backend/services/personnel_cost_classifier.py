"""
personnel_cost_classifier.py — PERSONNEL_COST Classifier v0.

Canonical contract: docs/Architecture/Cognitive/PERSONNEL_COST_CLASSIFIER_V0_IMPLEMENTATION_CONTRACT.md
(established 5dfde8c; corrected 669b44b, epistemic semantics; corrected
c547ee5, signal family model final adversarial review).

RESPONSIBILITY (contract §1): exactly one question — for one
already-identified P&L leaf observation, what is the narrowest defensible
hypothesis about whether it represents PERSONNEL_COST? Never a forced
classification; never "not PERSONNEL_COST" treated as evidence for
`OTHER` (contract §5).

THE TWO-FAMILY MODEL (contract §6/§7), implemented exactly, not
approximated:
  - `STRUCTURAL` family = `ACCOUNT_CODE_FAMILY` + `STRUCTURAL_POSITION`
    only. Genuinely non-lexical, mechanically correlated (in a
    well-formed ledger, an account's code-family and its physical
    position are two readings of one underlying editorial fact) —
    grouped as one family, never counted as two independent votes.
  - `LEXICAL` family = `CAPTION_LEXICAL` alone, against the final
    closed, Golden-Case-scoped keyword list (contract §13, corrected:
    `"assurance"`/`"loyer"` removed after being proven dangerous against
    real row 149 — see `_OTHER_KEYWORDS` below).
  - Each family resolves to exactly one of three raw states — no usable
    claim (`None`), `PERSONNEL_COST`-direction, or `OTHER`-direction —
    never a graded/partial value. When a family's own sub-signals are
    both available and genuinely disagree with each other
    (`INTERNALLY_INCONSISTENT`, contract §6), the family resolves to "no
    usable claim" — never escalated to a whole-`Candidate`
    `CONTRADICTION`, because a disagreement within one evidentiary basis
    is a fundamentally weaker, different kind of fact than the two named
    families disagreeing with each other.
  - `Candidate.tier` is computed via `_TIER_TABLE`, a direct, literal
    transcription of the contract's own 9-row `STRUCTURAL`×`LEXICAL`
    table (§7) — no numeric weighting, no majority vote, no per-row
    branch on which real Phidani row is being classified.

PARENT_CAPTION'S ROLE (contract §6, corrected by the Signal Family Model
Final Adversarial Review): a position-consistency check only, never an
independent keyword-matching vote (the original design shared
`CAPTION_LEXICAL`'s own keyword mechanism, a real circularity found and
fixed). **[CORRECTED, independent adversarial pre-merge review, 2026-08-11]**
An earlier version of this module computed a `_parent_caption_confirms_position`
helper for this role, but the review proved by direct behavioral deletion
test (forcing its return value to its opposite across all five real
Golden Cases) that the result had zero causal effect on any `Candidate`
output, evidence list, tier, or professional invariant — the contract's
five worked "Expected:" Golden Case tuples (§9, §10, §11, §12, §12a)
never include a `PARENT_CAPTION` `EvidenceItem`, and no case specifies
anomalous behavior for a missing/inconsistent parent caption. Per the
review's own deletion-test framework ("if NO capability is lost, remove
it — do not retain dead code merely because the contract mentions the
concept historically"), the computation is removed entirely rather than
kept inert. `PARENT_CAPTION` therefore contributes nothing to this v0
kernel's actual behavior — a named, honest simplification, not a silent
omission (see `TestParentCaptionRoleRemoved` in the test suite, which
pins this decision and would fail if `PARENT_CAPTION` ever silently
reappeared as a voting signal).

WHAT THIS MODULE NEVER DOES (contract §2/§13):
  - No LLM call, anywhere, for any reason (contract §26).
  - No synonym/semantic-alias expansion — `concept_vocabulary.match_concept`
    is never called (contract §22); only `get_concept("PERSONNEL_COST")`
    for the canonical identifier string.
  - No Doctrine consultation — `financial_doctrine` is never imported
    (contract §21).
  - No numeric confidence, probability, fuzzy membership, or hidden score
    anywhere (contract §4's explicit prohibition).
  - No row-number branch, no company-name branch, no hardcoded Golden
    Case coordinate or outcome anywhere in this kernel (contract §8/§29).
  - No statement-location / P&L-leaf precondition check — the caller is
    responsible for that (contract §19/§20); behavior on a non-leaf,
    non-P&L input is undefined here, by design.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union

from openpyxl.utils.cell import coordinate_from_string

from .candidate import Candidate, EvidenceItem
from .concept_vocabulary import get_concept
from .formula_reference_extractor import _expand_range

# Canonical PERSONNEL_COST identifier, looked up from Concept Vocabulary
# (contract §22) rather than re-declared as an independent literal.
# `OTHER` is not itself a registered Concept (only EBITDA/PERSONNEL_COST
# are, per concept_vocabulary.py) — it is this classifier's own local,
# non-personnel placeholder value, exactly like Doctrine v0's own
# `classify_cell` fixture precedent (contract §14 Pattern A there).
_PERSONNEL_COST = get_concept("PERSONNEL_COST").id
_OTHER = "OTHER"

# Belgian PCMN charge-account classes (contract §13/§14): class 62
# ("Rémunérations, charges sociales et pensions") is the personnel class;
# the rest of the charge range (60/61 goods-and-services, 63
# amortization, 64 other operating charges, 65 financial charges, 66
# exceptional charges) is, by the formal chart-of-accounts structure
# itself, never personnel — this is a closed, mutually-exclusive class
# taxonomy, not a fragile per-row heuristic. Mirrors (does not import,
# to keep the two v0 slices decoupled) the same charge-class range
# `fru_sign_convention_detector._CHARGE_CODE_PREFIXES` already
# establishes as this file's own PCMN charge scope.
_PERSONNEL_PCMN_PREFIX = "62"
_NON_PERSONNEL_PCMN_PREFIXES = frozenset({"60", "61", "63", "64", "65", "66"})

# Closed, Golden-Case-scoped keyword list (contract §13/§15, corrected by
# the Signal Family Model Final Adversarial Review): "assurance" and
# "loyer" are deliberately absent — neither was ever required by a real
# Golden Case, and "assurance" was proven actively dangerous (real row
# 149, "Assurance accident de travail", would have produced a false
# CONTRADICTION). "Personnel-adjacent name patterns" (named in §13's
# prose) are NOT separately implemented: every real Golden Case that
# needs a personal-name-flavored caption (rows 122/125/128, "Rémunération
# Brute Alain Corchia") already matches via the "rémunération" keyword
# itself, so a dedicated name-pattern matcher is not required by any
# Golden Case and is not built here (the same minimality discipline that
# removed "assurance"/"loyer").
_PERSONNEL_KEYWORDS = ("rémunération", "salaire")
_OTHER_KEYWORDS = ("téléphone",)


@dataclass(frozen=True)
class LeafObservation:
    """Caller-supplied facts about one already-known P&L leaf observation
    (contract §2/§19/§20). The caller is responsible for the P&L/leaf
    precondition — this classifier does not check it and has undefined
    behavior if it is violated.

    `personnel_cost_range`/`other_range` are the already-known aggregate
    ranges (e.g. "C134:C160", "C36:C131") this leaf's position is checked
    against — supplied by the caller, mirroring the existing
    caller-supplied-`root_cell` pattern in `formula_reference_extractor.py`
    and Doctrine v0's own contract §14 Pattern A. This classifier performs
    no automatic "am I in the P&L" or aggregate-discovery logic itself
    (contract §20 — Reporting Structure is not built here).
    """

    account_code_cell: str
    account_code: Optional[Union[str, int, float]]
    position_cell: str
    personnel_cost_range: Optional[str]
    other_range: Optional[str]
    parent_caption_cell: Optional[str]
    parent_caption_text: Optional[str]
    own_caption_cell: str
    own_caption_text: Optional[str]


def _account_code_direction(raw_code: Optional[Union[str, int, float]]) -> Optional[str]:
    """`ACCOUNT_CODE_FAMILY` sub-signal (contract §13/§14). Fails closed —
    returns `None` (absent) for missing, malformed, non-integer-valued,
    or non-Belgian-PCMN-prefixed codes; never fabricates a direction.

    Explicitly tested against the real row-234 corruption pattern
    (`72.44444444444444`, a float with a non-zero fractional part,
    almost certainly a compound code Excel silently coerced into a
    division result, per `FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL.md`):
    truncating such a float via a bare `int()` call would silently
    fabricate a plausible-looking but meaningless prefix — rejected here
    instead by requiring an exact integer value.
    """
    if raw_code is None:
        return None
    if isinstance(raw_code, bool):  # bool is an int subclass; not a code
        return None
    if isinstance(raw_code, float):
        if not raw_code.is_integer():
            return None  # malformed (row-234-shaped) — never fabricated
        icode = int(raw_code)
    elif isinstance(raw_code, int):
        icode = raw_code
    elif isinstance(raw_code, str):
        stripped = raw_code.strip()
        if not re.fullmatch(r"\d+", stripped):
            return None  # non-numeric/malformed string
        icode = int(stripped)
    else:
        return None
    if icode <= 99:
        return None  # bare aggregate code, not a real account-line prefix
    prefix = str(icode)[:2]
    if prefix == _PERSONNEL_PCMN_PREFIX:
        return _PERSONNEL_COST
    if prefix in _NON_PERSONNEL_PCMN_PREFIXES:
        return _OTHER
    return None  # non-Belgian/unrecognized prefix — fails closed


def _parse_range(range_str: Optional[str]) -> Optional[frozenset]:
    """Parses a "C134:C160"-shaped range string into the set of cell
    references it covers, reusing `formula_reference_extractor._expand_range`
    (contract §13's own explicit instruction — "no new range logic
    invented"). Returns `None` for any malformed or non-single-column
    range, never guesses."""
    if not range_str or ":" not in range_str:
        return None
    left, right = range_str.split(":", 1)
    try:
        col1, row1 = coordinate_from_string(left.strip())
        col2, row2 = coordinate_from_string(right.strip())
    except ValueError:
        return None
    return _expand_range(col1, row1, col2, row2)


def _position_direction(
    position_cell: Optional[str],
    personnel_cost_range: Optional[str],
    other_range: Optional[str],
) -> Optional[str]:
    """`STRUCTURAL_POSITION` sub-signal (contract §13). Fails closed for
    missing coordinates, malformed ranges, or a position that (should it
    ever happen with caller-supplied ranges) falls inside both supplied
    ranges at once — never guesses."""
    if not position_cell:
        return None
    personnel_cells = _parse_range(personnel_cost_range)
    other_cells = _parse_range(other_range)
    in_personnel = personnel_cells is not None and position_cell in personnel_cells
    in_other = other_cells is not None and position_cell in other_cells
    if in_personnel and in_other:
        return None  # overlapping/contradictory caller-supplied ranges
    if in_personnel:
        return _PERSONNEL_COST
    if in_other:
        return _OTHER
    return None


def _word_match(normalized_text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword.casefold()) + r"\b"
    return re.search(pattern, normalized_text) is not None


def _caption_direction(caption_text: Optional[str]) -> Optional[str]:
    """`CAPTION_LEXICAL` sub-signal (contract §13/§15). Matches only the
    final, closed keyword list (`_PERSONNEL_KEYWORDS`/`_OTHER_KEYWORDS`)
    — no synonym expansion, no LLM, no invented meaning for an
    unrecognized caption (contract §22, out-of-vocabulary tests). If a
    caption were ever to match both directions' keywords at once (not
    reachable with the current minimal two-term lists, named for
    robustness only, contract §6), this resolves to `None`
    (`INTERNALLY_INCONSISTENT`, collapsed to no usable claim, never a
    fabricated direction)."""
    if not caption_text or not caption_text.strip():
        return None
    normalized = caption_text.strip().casefold()
    personnel_hit = any(_word_match(normalized, kw) for kw in _PERSONNEL_KEYWORDS)
    other_hit = any(_word_match(normalized, kw) for kw in _OTHER_KEYWORDS)
    if personnel_hit and other_hit:
        return None
    if personnel_hit:
        return _PERSONNEL_COST
    if other_hit:
        return _OTHER
    return None  # not recognized by v0's closed list — NOT "no evidence exists" (contract §6, sub-case (c))


def _resolve_family(direction_a: Optional[str], direction_b: Optional[str]) -> Optional[str]:
    """Family-level resolution (contract §6): absent/absent -> no claim;
    exactly one available -> that direction; both available and agree ->
    that direction; both available and genuinely disagree ->
    `INTERNALLY_INCONSISTENT`, collapsed to no usable claim here (`None`)
    — never a silent majority vote, never an invented winner, never
    escalated to Candidate-level CONTRADICTION on its own."""
    if direction_a is None and direction_b is None:
        return None
    if direction_a is None:
        return direction_b
    if direction_b is None:
        return direction_a
    if direction_a == direction_b:
        return direction_a
    return None  # INTERNALLY_INCONSISTENT


# Direct, literal transcription of contract §7's 9-row table — the sole
# source of `value`/`tier`. A categorical (family-presence,
# family-agreement) lookup, no numeric threshold, no majority vote
# anywhere.
_TIER_TABLE: dict[tuple[Optional[str], Optional[str]], tuple[Optional[str], str]] = {
    (None, None): (None, "UNKNOWN"),
    (None, _PERSONNEL_COST): (_PERSONNEL_COST, "HYPOTHESIS"),
    (None, _OTHER): (_OTHER, "HYPOTHESIS"),
    (_PERSONNEL_COST, None): (_PERSONNEL_COST, "HYPOTHESIS"),
    (_PERSONNEL_COST, _PERSONNEL_COST): (_PERSONNEL_COST, "STRONG_INFERENCE"),
    (_PERSONNEL_COST, _OTHER): (None, "CONTRADICTION"),
    (_OTHER, None): (_OTHER, "HYPOTHESIS"),
    (_OTHER, _PERSONNEL_COST): (None, "CONTRADICTION"),
    (_OTHER, _OTHER): (_OTHER, "STRONG_INFERENCE"),
}


def _extract_evidence(
    obs: LeafObservation,
) -> tuple[Optional[str], Optional[str], tuple[EvidenceItem, ...], tuple[EvidenceItem, ...]]:
    """Pure evidence extraction (contract §13/§29). Returns
    `(structural_state, lexical_state, supporting_evidence,
    contradicting_evidence)`. `structural_state`/`lexical_state` are each
    one of `None` (no usable claim), `_PERSONNEL_COST`, or `_OTHER`
    (contract §6/§7) — resolved independently per family, never blended,
    never containing a row-number or caption-text branch."""
    code_direction = _account_code_direction(obs.account_code)
    position_direction = _position_direction(
        obs.position_cell, obs.personnel_cost_range, obs.other_range
    )
    structural_state = _resolve_family(code_direction, position_direction)
    lexical_state = _caption_direction(obs.own_caption_text)

    supporting: list[EvidenceItem] = []
    contradicting: list[EvidenceItem] = []

    def _append(direction: str, item: EvidenceItem) -> None:
        (supporting if direction == _PERSONNEL_COST else contradicting).append(item)

    # STRUCTURAL sub-signal items are only recorded when STRUCTURAL itself
    # resolved to a genuine directional claim — an internally-inconsistent
    # family (both sub-signals present but disagreeing) contributes NO
    # evidence items at all, never a one-sided fragment of a discarded
    # internal conflict (contract §6 — NO_CLAIM means no usable claim).
    if structural_state is not None:
        if code_direction is not None:
            _append(
                structural_state,
                EvidenceItem("ACCOUNT_CODE_FAMILY", obs.account_code_cell, "DETERMINISTIC"),
            )
        if position_direction is not None:
            _append(
                structural_state,
                EvidenceItem("STRUCTURAL_POSITION", obs.position_cell, "DETERMINISTIC"),
            )
    if lexical_state is not None:
        _append(
            lexical_state,
            EvidenceItem("CAPTION_LEXICAL", obs.own_caption_cell, "DETERMINISTIC"),
        )

    return structural_state, lexical_state, tuple(supporting), tuple(contradicting)


def _arbitrate(
    structural_state: Optional[str],
    lexical_state: Optional[str],
    supporting_evidence: tuple[EvidenceItem, ...],
    contradicting_evidence: tuple[EvidenceItem, ...],
) -> Candidate:
    """Pure arbitration (contract §7/§29): a direct table lookup, nothing
    else. No numeric weighting, no majority vote, no case-by-case
    exception."""
    value, tier = _TIER_TABLE[(structural_state, lexical_state)]
    return Candidate(
        value=value,
        tier=tier,
        supporting_evidence=supporting_evidence,
        contradicting_evidence=contradicting_evidence,
    )


def classify_personnel_cost(obs: LeafObservation) -> Candidate:
    """Public entry point (contract §1). Pure, deterministic, no I/O, no
    LLM, no persistence — a `Candidate` recomputed fresh from `obs` every
    call."""
    structural_state, lexical_state, supporting, contradicting = _extract_evidence(obs)
    return _arbitrate(structural_state, lexical_state, supporting, contradicting)
