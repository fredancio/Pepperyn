"""
formula_reference_extractor.py — pure forward formula-reference extraction
and forward dependency closure resolution.

Canonical contract: docs/Architecture/Cognitive/CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md
§13/§13a/§13b (corrected 2026-08-11, twice: composition-completeness /
false-mismatch fix, then the Final Semantic Arbitration removing the
arbitrary `max_depth` constant).

`extract_cell_references` — single-hop, forward-only primitive. Regex-based,
the same technique already used by fru_sign_convention_detector.py's own
margin-subtraction search. Expands single-column vertical ranges (e.g.
"C36:C131", the only range shape Phidani actually uses) into every member
cell; any other range shape is kept as one opaque, unresolvable token
rather than silently under-expanded (fail closed — an under-expanded range
could hide a required concept and produce a false MISMATCH, exactly the
defect this contract line has already found and corrected once).

`resolve_composition` — forward dependency traversal with cycle detection
(NOT "DAG traversal": terminology corrected 2026-08-11 — cycles are
guarded against, not assumed impossible). No `max_depth` parameter:
termination is guaranteed by the `on_stack` cycle guard plus `done`
memoization operating over any real workbook's finite cell universe
(contract §13a) — proven, not assumed. Not a graph engine: single
direction (forward only), no fixed-point iteration, no backward inference.

Doctrine-agnostic by design: this module has no knowledge of
DoctrineStatement, required_prior_deductions, or comparison semantics — it
only resolves which concepts are reachable from a root cell's forward
formula references, and whether that resolution is complete.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

ConceptId = str

_COL_ROW = r"\$?([A-Za-z]{1,3})\$?([0-9]+)"
_RANGE_RE = re.compile(_COL_ROW + r":" + _COL_ROW)
_CELL_RE = re.compile(_COL_ROW)


def _expand_range(col1: str, row1: int, col2: str, row2: int) -> Optional[frozenset]:
    """Expand a single-column vertical range into individual cell
    references. Returns None for any other shape (different columns) —
    callers must then treat the range as one opaque, unresolvable token,
    never silently approximate it."""
    if col1.upper() != col2.upper():
        return None
    lo, hi = sorted((row1, row2))
    return frozenset(f"{col1.upper()}{r}" for r in range(lo, hi + 1))


def extract_cell_references(formula: Optional[str]) -> frozenset:
    """Single-hop, forward-only extraction of cell references from a
    formula string (contract §13). Pure regex, no evaluation, no recursion
    — see `resolve_composition` for the closure built on top of this
    primitive.

    Row 133: extract_cell_references("=C35-C132") == frozenset({"C35", "C132"}).
    Row 132: extract_cell_references("=SUM(C36:C131)") expands to the full
    96-cell range {"C36", "C37", ..., "C131"} — required for the Golden
    Case's own composition-completeness claim to be honest (a doctrine
    requirement could legitimately be hidden anywhere inside a summed
    range, not only at its two endpoints).

    Absolute-reference markers ("$C$35") are normalized to their bare
    column-row form. Cross-sheet references are out of scope for the
    Golden Case and are not specially handled.
    """
    if not formula:
        return frozenset()

    refs: set = set()
    consumed_spans: list = []

    for m in _RANGE_RE.finditer(formula):
        col1, row1, col2, row2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        expanded = _expand_range(col1, row1, col2, row2)
        if expanded is not None:
            refs.update(expanded)
        else:
            refs.add(m.group(0).replace("$", ""))
        consumed_spans.append(m.span())

    def _inside_consumed(pos: int) -> bool:
        return any(start <= pos < end for start, end in consumed_spans)

    for m in _CELL_RE.finditer(formula):
        if _inside_consumed(m.start()):
            continue
        refs.add(m.group(0).replace("$", ""))

    return frozenset(refs)


@dataclass(frozen=True)
class ObservedComposition:
    """Contract §15/§16 (corrected 2026-08-11). Doctrine-agnostic: produced
    by `resolve_composition` below, consumed only by
    services.financial_doctrine.compare_against_doctrine.
    """

    directly_referenced_concepts: frozenset
    unclassified_references: frozenset
    composition_complete: bool


def resolve_composition(
    root_cell: str,
    get_formula: Callable[[str], Optional[str]],
    classify_cell: Callable[[str], Optional[ConceptId]],
) -> ObservedComposition:
    """Forward dependency traversal with cycle detection (contract §13,
    terminology corrected 2026-08-11).

    No `max_depth` parameter (contract §13a — removed, not re-justified
    with a different constant). Termination is guaranteed by the
    `on_stack` cycle guard plus `done` memoization operating over any real
    workbook's finite cell universe, independent of depth.

    `get_formula(cell)` returns the cell's own formula text, or None if the
    cell is a raw input (terminal — nothing further to expand).
    `classify_cell(cell)` returns the cell's concept classification, or
    None if unclassifiable — supplied by an Economic Meaning stand-in
    (contract §14 Pattern A: a deterministic test fixture in this slice,
    never a classifier implemented here).

    Every reachable formula-derived cell is expanded regardless of its own
    classification (contract §16 — "an aggregate label never excuses
    skipping expansion"). A detected cycle sets `composition_complete =
    False` and returns without raising and without looping.
    """
    resolved: set = set()
    unclassified: set = set()
    complete = True
    on_stack: set = set()
    done: set = set()

    def expand(cell: str) -> None:
        nonlocal complete
        if cell in done:
            return  # diamond dependency, already fully resolved — not a cycle
        if cell in on_stack:
            complete = False  # true cycle — fail closed, never guess, never loop
            return
        on_stack.add(cell)
        concept = classify_cell(cell)
        if concept is not None:
            resolved.add(concept)
        else:
            unclassified.add(cell)
            complete = False
        formula = get_formula(cell)
        if formula is not None:
            for ref in extract_cell_references(formula):
                expand(ref)
        on_stack.discard(cell)
        done.add(cell)

    root_formula = get_formula(root_cell)
    if root_formula is not None:
        for ref in extract_cell_references(root_formula):
            expand(ref)

    return ObservedComposition(
        directly_referenced_concepts=frozenset(resolved),
        unclassified_references=frozenset(unclassified),
        composition_complete=complete,
    )
