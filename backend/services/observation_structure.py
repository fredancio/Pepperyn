"""
observation_structure.py — Observation Structure v0: pure classification kernel.

Canonical contract: docs/Architecture/Cognitive/OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md
(merged to main 2026-08-10, commit b53c68b). This module implements the
contract's two orthogonal row-axis dimensions:

  - `structural_role`  — WHAT ROLE this observation plays in the report's
    own structure (LEAF / AGGREGATE / KPI / SECTION_HEADER / UNKNOWN).
  - `derivation_status` — HOW the observation's value was produced, as
    observable from within this file (NO_OBSERVED_FORMULA / DERIVED /
    NOT_APPLICABLE / UNKNOWN).

RENAMED 2026-08-10 (independent adversarial pre-merge review): the value
originally called `SOURCE_VALUE` is renamed `NO_OBSERVED_FORMULA`. Pure
rename, zero behaviour change — every classification decision, every test
assertion's outcome, and the fail-closed independence rule are unchanged.
Rationale: "SOURCE_VALUE" is a loaded term in financial/data-lineage
contexts — it invites a future reader (a consumer author, a future
Economic Nature/Reporting Structure contract, a future prompt to this
same system) to infer "origin of truth" / "elementary source-system fact"
/ "safe to treat as independent," none of which this classifier can
actually prove. What this module observes and can prove is narrower and
purely mechanical: no formula string was found in this cell, in this
file. The old name fought its own caveat paragraph (§3.2's honesty note);
the new name states exactly, and only, what was checked. Three future
consumers (FRU's eventual refactor, Economic Nature, Reporting Structure)
will all read this vocabulary — the cost of a misleading name compounds
with each one, and this is the cheapest point in the system's life to fix
it (before any consumer is wired in at all). `is_arithmetically_independent()`
below remains a separate, explicit policy layered on top of this raw
signal, not a restatement of it — renaming makes that layering more
visible, not less.

Both dimensions apply to a (row, column) observation — a single cell within
one period column — never to "a row" as a row-level constant (contract §2's
corrected scope-unit paragraph).

WHAT THIS MODULE IS NOT:
  - Not a service, not a repository, not an aggregate, no persistence, no
    API endpoint, no hidden global state (mission §8). Every function here
    is pure: same inputs, same outputs, no I/O, no global mutation.
  - Not a hierarchy reconstructor. `derived_from` (which cells a DERIVED
    formula references) is explicitly deferred (contract §10, §14) — not
    computed, not exposed here.
  - Not a semantic classifier. `structural_role = KPI` never means
    "important metric" and is never informed by account naming/EBITDA-style
    semantics (contract §3.1, corrected 2026-08-10) — only by structural
    evidence (formula shape, account-code shape, derivation).
  - Not an Epistemic Dialogue trigger. UNKNOWN and HYPOTHESIS are
    legitimate, final answers in v0 — no ClarificationNeed is ever raised
    from this module (contract §7).

EVIDENCE USED (contract §5), IN ORDER:
  1. Formula presence in the observation's own cell — derivation_status's
     primary and, in v0, only mechanical signal. Sourced from
     formula_evidence.CellFormulaEvidence.
  2. Account-code shape (column A) and caption/value presence at the row
     level — structural_role's primary signal set. The code-shape
     classifier below (`_classify_code_shape`) is explicitly grounded in
     Phidani's own PCMN-derived numbering convention (contract §3.1's own
     "B0/B1/B2/B3 code family... this report template's own invention, not
     a Belgian universal signal" caveat, extended here to the numeric-code
     length heuristic below) — flagged, never claimed universal.

A DISCOVERED CONTRACT TENSION, ARBITRATED FROM FIRST PRINCIPLES (independent
adversarial pre-merge review, 2026-08-10 — not merely papered over with the
implementation's own preference, re-derived independently): contract §2
illustrated dimension-orthogonality with a "hardcoded manual Excel total"
example asserting `structural_role = AGGREGATE` +
`derivation_status = SOURCE_VALUE` (now `NO_OBSERVED_FORMULA`). Contract
§12's own adversarial fixture F ("hardcoded subtotal, no formula") instead
requires `derivation_status = UNKNOWN`, `structural_role` at best
HYPOTHESIS — and §16 makes fixture F part of the binding test contract.
These two passages of the same canonical document were not reconcilable as
literally worded for the same scenario.

Arbitration: what can Pepperyn actually know when it sees an
aggregate-shaped row with no formula? Only that no Excel-formula mechanism
is present in this one file. It cannot distinguish a human-typed total, a
paste-as-values of a formula that used to be there, an ERP-precomputed
figure that duplicates leaves shown elsewhere in this same file, from the
one case where the figure genuinely is an independent source fact that
happens to sit at an aggregate-shaped position. The first three
possibilities all mean "not safe to sum without double-counting"; only the
fourth is safe — and this file's evidence cannot tell them apart. Between
(a) wrongly treating a real rollup as independent — silent, financially
wrong, undetectable downstream — and (b) wrongly treating a genuinely
independent figure as unproven — visible, honest, correctable by a later
capability — (a) is categorically worse. §12/§16's `UNKNOWN` answer is
therefore the epistemically correct one, not a documentary quirk to defer
to for consistency's sake; §2's illustrative sentence was substantively
wrong, not just differently worded. §2 is corrected to match §12/§16 as
part of this review (contract commit, not this module). This module always
implemented §12/§16's behaviour (the fail-closed answer: an aggregate- or
KPI-shaped row with no formula backing is UNKNOWN, never silently treated
as a plain absence of formula) — the correction here is documentary only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from services.formula_evidence import CellFormulaEvidence

# --- Output vocabulary -------------------------------------------------
# Plain string literals, matching the existing informal convention already
# established by fru_sign_convention_detector.py's Candidate.tier field
# ("STRONG_INFERENCE" | "HYPOTHESIS" | "UNKNOWN") — no new enum class, no
# new scoring engine (contract §10, "Confidence vocabulary").

STRUCTURAL_ROLE_VALUES = ("LEAF", "AGGREGATE", "KPI", "SECTION_HEADER", "UNKNOWN")
DERIVATION_STATUS_VALUES = ("NO_OBSERVED_FORMULA", "DERIVED", "NOT_APPLICABLE", "UNKNOWN")
TIER_VALUES = ("STRONG_INFERENCE", "HYPOTHESIS", "UNKNOWN")


@dataclass(frozen=True)
class ObservationClassification:
    """The full v0 output for one (row, column) observation.

    `formula_text` is retained per contract §10's field-inclusion rule — a
    free byproduct of the same cell inspection `derivation_status` already
    requires, zero additional computation.
    """

    structural_role: str  # one of STRUCTURAL_ROLE_VALUES
    structural_role_tier: str  # one of TIER_VALUES
    derivation_status: str  # one of DERIVATION_STATUS_VALUES
    formula_text: Optional[str]

    def is_arithmetically_independent(self) -> bool:
        """Convenience derivation (contract §2, §10) — fail-closed and,
        explicitly, a POLICY layered on top of raw evidence, not a
        restatement of it. `NO_OBSERVED_FORMULA` means only "no formula
        string was found in this cell in this file" — it does not by
        itself prove the value is safe to sum. This method is the place
        where that additional, deliberate judgment call is made: treat
        the absence of an observed formula as the (fail-closed, best
        available) proxy for arithmetic independence, given v0 has no
        stronger signal. A future capability with more evidence (upstream
        ERP lineage, hierarchy reconstruction) could refine this without
        changing what `NO_OBSERVED_FORMULA` itself means.

        Corrected 2026-08-10 (independent adversarial pre-implementation
        review): must be `== NO_OBSERVED_FORMULA` (originally named
        `SOURCE_VALUE` — renamed same day, independent adversarial
        pre-merge review, pure rename, see module docstring), never
        `!= DERIVED`. The latter would silently treat NOT_APPLICABLE and,
        critically, UNKNOWN as "safe to sum" — on a no-formula-cached
        export every observation degrades to UNKNOWN, and `!= DERIVED`
        would then treat the whole file as safe, reintroducing the exact
        rollup double-counting defect this capability exists to prevent
        (protects FRU, §7).
        """
        return self.derivation_status == "NO_OBSERVED_FORMULA"


def _classify_code_shape(code: Union[str, int, float, None]) -> str:
    """Classify an account-code cell's shape into a coarse structural
    bucket, grounded in real Phidani account-code observations (contract
    §11's Golden Case) and explicitly NOT claimed as a universal (even
    Belgian-universal) signal (contract §3.1's own caveat about the
    "B0/B1/B2/B3" family, extended here).

    Returns one of: "NONE", "LEAF_SHAPED", "AGGREGATE_SHAPED",
    "KPI_SHAPED", "UNRECOGNIZED".

    Grounding (real Phidani rows, verified via direct openpyxl inspection):
      - "620250" (int, 6 digits)      -> LEAF_SHAPED  (row 134, a leaf)
      - "70", "62"  (str, <=3 digits) -> AGGREGATE_SHAPED (rows 6, 161 — statutory subtotal classes)
      - "630"       (str, 3 digits)   -> AGGREGATE_SHAPED (row 163 — the passthrough falsifier)
      - "60/64"     (str, compound)   -> AGGREGATE_SHAPED (row 165 — sibling-closure subtotal)
      - 650         (int, 3 digits)   -> AGGREGATE_SHAPED (row 231 — SUM rollup)
      - "B1", "B3"  (str, letter+digit) -> KPI_SHAPED (rows 133, 256 — Phidani's own ad hoc family)
      - 72.44444444444444 (float, corrupted) -> UNRECOGNIZED (row 234 — Case O, malformed code)
    A code of 4-5 digits has no Golden Case evidence either way and is
    deliberately left UNRECOGNIZED rather than guessed.
    """
    if code is None:
        return "NONE"

    if isinstance(code, float):
        # A float account code is itself evidence of representation
        # corruption (profession-model mission finding, real row 234) —
        # never trusted structurally, never guessed at. Case O robustness.
        return "UNRECOGNIZED"

    if isinstance(code, int):
        digits = str(code)
        if len(digits) <= 3:
            return "AGGREGATE_SHAPED"
        if len(digits) >= 6:
            return "LEAF_SHAPED"
        return "UNRECOGNIZED"

    if isinstance(code, str):
        stripped = code.strip()
        if not stripped:
            return "NONE"
        if "/" in stripped:
            parts = [p for p in stripped.split("/") if p]
            if parts and all(p.isdigit() for p in parts):
                return "AGGREGATE_SHAPED"
            return "UNRECOGNIZED"
        if stripped.isdigit():
            if len(stripped) <= 3:
                return "AGGREGATE_SHAPED"
            if len(stripped) >= 6:
                return "LEAF_SHAPED"
            return "UNRECOGNIZED"
        if len(stripped) <= 3 and stripped[0].isalpha() and stripped[1:].isdigit():
            return "KPI_SHAPED"
        return "UNRECOGNIZED"

    return "UNRECOGNIZED"


def _looks_like_free_text_caption(code: Union[str, int, float, None]) -> bool:
    """Distinguish a genuine free-text section caption (real Phidani rows
    3/369: `"Compte de résultats"`, `"PASSIF"` — prose, no digit character
    anywhere) from a malformed/unparseable CODE ATTEMPT (real Phidani row
    234: the corrupted float `72.44444444444444` — still evidence this
    cell was meant to hold a code, not a section title).

    Added 2026-08-10 (independent adversarial pre-merge review) — found by
    direct perturbation, not by an existing test: without this
    distinction, a row with a malformed/unrecognized account code that is
    also blank in some period column (Case O's shape, generalised to a
    column the real file doesn't happen to leave blank) would have been
    misclassified `SECTION_HEADER`, wrongly asserting a structural
    boundary that a future Reporting Structure capability (contract §8)
    would consume as ground truth. `code is None` (true absence) is
    handled separately by `_classify_code_shape` returning `"NONE"` and is
    always eligible; this function only adjudicates the `"UNRECOGNIZED"`
    bucket.
    """
    if code is None:
        return True
    if isinstance(code, (int, float)):
        # A number, however malformed, is evidence of a code attempt, not
        # prose — never eligible for SECTION_HEADER.
        return False
    if isinstance(code, str):
        return not any(ch.isdigit() for ch in code)
    return False


def classify_observation(
    code: Union[str, int, float, None],
    formula: CellFormulaEvidence,
) -> ObservationClassification:
    """Classify one (row, column) observation.

    Inputs are exactly the evidence contract §5 names as available today:
    the row's account code (column A, row-level, shared across the row's
    columns) and this cell's formula evidence (column-specific). No caption
    text, no bold/outline/indentation is consulted (contract §14 — named
    as available but not required for v0's minimum viable classification;
    row 231, bold=False yet a genuine formula-derived subtotal, is the
    real-file proof bold is not a reliable signal — contract §5).

    SECTION_HEADER is the one structural_role value that depends on the
    row having literally nothing in this column (no code AND no literal
    value AND no formula) — contract §3.1's row-level pattern, operationalised
    per-column here per §2's scope-unit correction (a SECTION_HEADER row
    has no value in *any* column, so this holds for whichever column is
    queried).
    """
    code_shape = _classify_code_shape(code)

    # SECTION_HEADER: no recognizable account code in this row (column A
    # is empty, OR — real Phidani rows 3/369 — column A itself holds the
    # section caption text, e.g. "Compte de résultats", "PASSIF", which is
    # UNRECOGNIZED by the code-shape classifier since it is not a code at
    # all), AND nothing at all in this cell (no formula, no literal value).
    # A row with a genuinely recognized code shape (LEAF/AGGREGATE/KPI)
    # that happens to be blank in this one column is NOT_APPLICABLE, not
    # SECTION_HEADER (real Phidani row 256, "B3", blank in some columns —
    # contract §2's structural_role/derivation_status divergence proof;
    # must never collapse into SECTION_HEADER).
    #
    # Corrected 2026-08-10 (independent adversarial pre-merge review): the
    # UNRECOGNIZED bucket alone is not sufficient — it also contains
    # malformed/unparseable CODE ATTEMPTS (real row 234's corrupted float
    # "72.44444444444444"), which are evidence of a data row, not a
    # section title. Only free-text-shaped UNRECOGNIZED codes (no digit
    # character anywhere, e.g. genuine prose captions) are eligible; see
    # _looks_like_free_text_caption.
    section_header_eligible = code_shape == "NONE" or (
        code_shape == "UNRECOGNIZED" and _looks_like_free_text_caption(code)
    )
    if section_header_eligible and not formula.is_formula and not formula.has_literal_value:
        return ObservationClassification(
            structural_role="SECTION_HEADER",
            structural_role_tier="STRONG_INFERENCE",
            derivation_status="NOT_APPLICABLE",
            formula_text=None,
        )

    # derivation_status: mechanical primary rule (contract §3.2).
    if formula.is_formula:
        derivation_status = "DERIVED"
    elif not formula.has_literal_value:
        derivation_status = "NOT_APPLICABLE"
    else:
        # No formula, but a literal value is present. Fail-closed per the
        # arbitrated §2/§12 tension (module docstring): an aggregate- or
        # KPI-shaped code with no formula backing it is suspicious, not
        # safely NO_OBSERVED_FORMULA (contract §12 fixture F / §16 test
        # contract).
        if code_shape in ("AGGREGATE_SHAPED", "KPI_SHAPED"):
            derivation_status = "UNKNOWN"
        else:
            derivation_status = "NO_OBSERVED_FORMULA"

    # structural_role.
    if code_shape == "LEAF_SHAPED":
        if not formula.is_formula and formula.has_literal_value:
            structural_role, tier = "LEAF", "STRONG_INFERENCE"
        else:
            # A leaf-shaped code that is somehow a formula or blank has no
            # Golden Case precedent — honest degrade, never a confident guess.
            structural_role, tier = "UNKNOWN", "UNKNOWN"
    elif code_shape == "AGGREGATE_SHAPED":
        if formula.is_formula:
            # Two independent signals agree (code shape + formula presence)
            # — STRONG, mirroring FRU's own "both signals agree" pattern.
            structural_role, tier = "AGGREGATE", "STRONG_INFERENCE"
        else:
            # Code shape alone, no formula corroboration — the no-formula
            # adversary / Case F shape (contract §6, §11's Golden Case
            # closing row: "HYPOTHESIS-tier AGGREGATE at best").
            structural_role, tier = "AGGREGATE", "HYPOTHESIS"
    elif code_shape == "KPI_SHAPED":
        # Always capped at HYPOTHESIS regardless of formula presence
        # (contract §3.1 — KPI "can never be assigned at STRONG_INFERENCE
        # tier in v0" — the proxy is inherently imperfect without
        # hierarchy-edge information this contract deliberately defers).
        structural_role, tier = "KPI", "HYPOTHESIS"
    else:
        # UNRECOGNIZED code shape (includes malformed codes, e.g. real
        # Phidani row 234's "72.44444444444444" — Case O): honest
        # degradation, never a confident guess, and — proven by
        # construction here — never affects derivation_status, which was
        # already resolved above from formula evidence alone.
        structural_role, tier = "UNKNOWN", "UNKNOWN"

    return ObservationClassification(
        structural_role=structural_role,
        structural_role_tier=tier,
        derivation_status=derivation_status,
        formula_text=formula.formula_text,
    )
