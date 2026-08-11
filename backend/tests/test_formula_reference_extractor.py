"""
test_formula_reference_extractor.py — services/formula_reference_extractor.py.

Covers: extract_cell_references (single reference, subtraction, SUM/range,
multi-reference, invalid formula, self-reference) and resolve_composition
(forward dependency closure, cycle detection including self-cycle, no
arbitrary depth constant — mission §10/§11/§26, contract §13/§13a).

Classification (mission §35): each test is tagged INVARIANT, BEHAVIOR,
BOUNDARY, or WEAK/GUARD in its docstring.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.formula_reference_extractor import (
    ObservedComposition,
    extract_cell_references,
    resolve_composition,
)


# ─────────────────────────────────────────────────────────────────────────────
# extract_cell_references
# ─────────────────────────────────────────────────────────────────────────────


class TestExtractCellReferences:
    def test_single_reference(self):
        """BEHAVIOR. One bare cell reference."""
        assert extract_cell_references("=C35") == frozenset({"C35"})

    def test_subtraction_row_133(self):
        """BEHAVIOR. Real Phidani row 133 formula, exactly as documented in
        the canonical contract §17."""
        assert extract_cell_references("=C35-C132") == frozenset({"C35", "C132"})

    def test_sum_range_row_132(self):
        """INVARIANT. Real Phidani row 132 formula: a single-column
        vertical SUM range must expand to every member cell, not just its
        two endpoints — an under-expanded range could hide a required
        concept and silently reproduce the false-MISMATCH defect already
        found and corrected once in this contract line."""
        refs = extract_cell_references("=SUM(C36:C131)")
        assert refs == frozenset(f"C{r}" for r in range(36, 132))
        assert len(refs) == 96

    def test_multi_reference_formula_row_165(self):
        """BEHAVIOR. Real Phidani row 165 formula: five bare references,
        no range."""
        assert extract_cell_references("=C34+C132+C161+C163+C164") == frozenset(
            {"C34", "C132", "C161", "C163", "C164"}
        )

    def test_invalid_formula_no_crash(self):
        """WEAK/GUARD. Malformed/non-formula text never raises — returns
        whatever cell-shaped tokens it can find, or empty."""
        assert extract_cell_references("=this is not a valid formula###") == frozenset()

    def test_empty_and_none_formula(self):
        """BOUNDARY. Empty string and None both yield an empty set (a
        RAW_INPUT cell has no formula at all)."""
        assert extract_cell_references("") == frozenset()
        assert extract_cell_references(None) == frozenset()

    def test_self_reference(self):
        """BOUNDARY. A formula referencing its own cell is extracted like
        any other reference — resolve_composition, not the extractor, is
        responsible for detecting that this constitutes a cycle."""
        assert extract_cell_references("=A1+1") == frozenset({"A1"})

    def test_absolute_reference_markers_normalized(self):
        """BEHAVIOR. "$C$35" normalizes to "C35" — the same cell as a bare
        reference, dollar signs carry no doctrine-relevant meaning here."""
        assert extract_cell_references("=$C$35-C132") == frozenset({"C35", "C132"})

    def test_non_single_column_range_kept_opaque(self):
        """BOUNDARY. A 2D range (different columns) is not silently
        under-expanded — it is kept as one opaque, unresolvable token so a
        downstream consumer treats it as unclassifiable rather than
        pretending it was fully examined."""
        refs = extract_cell_references("=SUM(A1:C10)")
        assert refs == frozenset({"A1:C10"})


# ─────────────────────────────────────────────────────────────────────────────
# Known limitations — pinning tests, NOT correctness assertions that the
# fabricated tokens below are desirable. Added 2026-08-11 (independent
# adversarial pre-merge review, "Formula reference extraction" §3):
# extract_cell_references has no awareness of Excel quoted-string-literal
# boundaries or the SheetName! cross-sheet prefix, and can therefore
# fabricate a reference-like token from either. Both cases were verified
# empirically to have ZERO exposure in the real Phidani.xlsx Golden Case
# (all 6042 formula cells scanned: single sheet, SUM()+arithmetic only,
# no quotes, no cross-sheet syntax). These tests exist so a future change
# to the extractor's parsing strategy is a deliberate, reviewed decision,
# never a silent behavior drift. See formula_reference_extractor.py's
# module docstring for the full named-limitation statement.
# ─────────────────────────────────────────────────────────────────────────────


class TestKnownLimitations:
    def test_quoted_string_can_produce_spurious_token(self):
        """BOUNDARY / KNOWN LIMITATION — pinning test, not a correctness
        assertion. Documents the CURRENT, ACCEPTED behavior: text inside a
        quoted string literal that happens to be cell-shaped is extracted
        as if it were a real reference."""
        refs = extract_cell_references('=IF(A1="TAXE5",1,0)')
        assert refs == frozenset({"A1", "AXE5"})  # "AXE5" is spurious,
        # fabricated from inside the quoted string literal "TAXE5" — NOT
        # a real reference in this formula. Pinned as known behavior.

    def test_cross_sheet_reference_can_produce_spurious_token(self):
        """BOUNDARY / KNOWN LIMITATION — pinning test, not a correctness
        assertion. Documents the CURRENT, ACCEPTED behavior: a fragment of
        a `SheetName!` prefix can be mis-extracted as if it were a
        same-sheet cell reference. Real Phidani.xlsx has exactly one
        sheet ("PHIDANI") — cross-sheet formulas are structurally
        impossible in the actual Golden Case data."""
        refs = extract_cell_references("=Sheet2!C35")
        assert refs == frozenset({"C35", "eet2"})  # "eet2" is spurious,
        # fabricated from inside the sheet name "Sheet2" — NOT a real
        # reference in this formula. Pinned as known behavior.


# ─────────────────────────────────────────────────────────────────────────────
# resolve_composition
# ─────────────────────────────────────────────────────────────────────────────


def _wire(formulas: dict, classifications: dict):
    """Build get_formula/classify_cell callbacks over plain dicts — no
    workbook, no I/O. `formulas` maps cell -> formula text or None (RAW_INPUT).
    `classifications` maps cell -> concept id; a cell absent from this dict
    is unclassifiable (classify_cell returns None)."""

    def get_formula(cell):
        return formulas.get(cell)

    def classify_cell(cell):
        return classifications.get(cell)

    return get_formula, classify_cell


class TestResolveComposition:
    """NOTE: extract_cell_references only recognizes Excel-shaped tokens
    (letters immediately followed by digits — contract §13). All symbolic
    cells referenced *through a formula string* in these fixtures must
    therefore be cell-shaped ("B1", "B2", ...); only the root_cell key
    itself (looked up directly, never regex-extracted) may be an arbitrary
    label such as "ROOT"."""

    def test_direct_match_case_a(self):
        """BEHAVIOR (mission §21/CASE A). Direct reference, positively
        classified — MATCH-shaped composition."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": None},
            classifications={"B1": "PERSONNEL_COST"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert result == ObservedComposition(
            directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
            unclassified_references=frozenset(),
            composition_complete=True,
        )

    def test_nested_match_case_b(self):
        """INVARIANT (mission §21, contract CASE B — the regression test
        for the original false-MISMATCH defect). PERSONNEL_COST is not a
        direct root reference but is transitively included via OPEX_TOTAL —
        must still resolve into directly_referenced_concepts."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2+B3", "B2": None, "B3": None},
            classifications={"B1": "OPEX_TOTAL", "B2": "EXTERNAL_COSTS", "B3": "PERSONNEL_COST"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert result.directly_referenced_concepts == frozenset(
            {"OPEX_TOTAL", "EXTERNAL_COSTS", "PERSONNEL_COST"}
        )
        assert result.composition_complete is True

    def test_deep_nested_match_case_e(self):
        """INVARIANT (mission §22). Three-hop chain — PERSONNEL_COST found
        at depth 3, with no depth-specific code path involved."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2", "B2": "=B3", "B3": None},
            classifications={"B1": "OPERATING_COSTS", "B2": "STAFF_AND_SERVICES", "B3": "PERSONNEL_COST"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert "PERSONNEL_COST" in result.directly_referenced_concepts
        assert result.composition_complete is True

    def test_incomplete_nested_case_c(self):
        """INVARIANT (mission §23, contract CASE C). An unresolvable
        component forces composition_complete=False."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2+B3", "B2": None, "B3": None},
            classifications={"B1": "OPEX_TOTAL", "B2": "EXTERNAL_COSTS"},  # B3 unclassifiable
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert "PERSONNEL_COST" not in result.directly_referenced_concepts
        assert result.composition_complete is False
        assert "B3" in result.unclassified_references

    def test_partial_positive_case_a_again(self):
        """INVARIANT (mission §24, contract CASE A — the asymmetry proof).
        PERSONNEL_COST positively found alongside a separate, unrelated
        unresolved branch — composition_complete is False, but the
        positively-found concept is unaffected."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2+B3", "B2": None, "B3": None},
            classifications={"B1": "OPEX_TOTAL", "B2": "PERSONNEL_COST"},  # B3 unclassifiable
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert "PERSONNEL_COST" in result.directly_referenced_concepts
        assert result.composition_complete is False  # computed, but (proven in
        # test_financial_doctrine.py) never consulted once PERSONNEL_COST is found

    def test_complete_absence_case_d(self):
        """INVARIANT (mission §25, contract CASE D — the canonical proof of
        negative evidence). Fully resolved closure, required concept
        genuinely absent throughout."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2", "B2": None},
            classifications={"B1": "OPEX_TOTAL", "B2": "EXTERNAL_COSTS"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert "PERSONNEL_COST" not in result.directly_referenced_concepts
        assert result.composition_complete is True

    def test_three_node_cycle(self):
        """INVARIANT (mission §26). A -> B -> C -> A terminates,
        composition_complete=False, no exception, no infinite recursion."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B2", "B2": "=B3", "B3": "=B1"},
            classifications={"B1": "X", "B2": "Y", "B3": "Z"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert result.composition_complete is False

    def test_self_cycle(self):
        """INVARIANT (mission §26). A cell referencing itself terminates
        the same way a multi-node cycle does."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1", "B1": "=B1+1"},
            classifications={"B1": "X"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert result.composition_complete is False

    def test_diamond_dependency_not_a_cycle(self):
        """BOUNDARY. The same cell referenced from two different branches
        of the same closure is resolved once (memoized), and does NOT set
        composition_complete=False."""
        get_formula, classify_cell = _wire(
            formulas={"ROOT": "=B1+B2", "B1": "=B3", "B2": "=B3", "B3": None},
            classifications={"B1": "X", "B2": "Y", "B3": "Z"},
        )
        result = resolve_composition("ROOT", get_formula, classify_cell)
        assert result.composition_complete is True
        assert result.directly_referenced_concepts == frozenset({"X", "Y", "Z"})

    def test_no_max_depth_parameter(self):
        """BOUNDARY (mission §14, contract §13a corrected 2026-08-11).
        resolve_composition's signature carries no depth-related
        parameter — keeps the domain contract honest that no such
        constant exists."""
        import inspect

        params = inspect.signature(resolve_composition).parameters
        assert not any("depth" in name.lower() for name in params)

    def test_deep_but_valid_chain_terminates_without_depth_constant(self):
        """INVARIANT (mission §14/§18, contract §13a). A synthetic acyclic
        chain of 20 hops (deliberately deep) resolves correctly with no
        depth constant involved — termination is guaranteed by the cycle
        guard alone, over a finite, acyclic reference graph."""
        n = 20
        formulas = {f"N{i}": f"=N{i + 1}" for i in range(n)}
        formulas[f"N{n}"] = None
        classifications = {f"N{i}": f"CONCEPT_{i}" for i in range(n + 1)}
        result = resolve_composition("ROOT", lambda c: formulas.get("N0") if c == "N0" else formulas.get(c), classify_cell=classifications.get)
        # ROOT itself has no formula registered; walk starts by treating N0 as the
        # first hop via a dedicated get_formula wired directly to ROOT below instead.
        get_formula = lambda c: {"ROOT": "=N0", **formulas}.get(c)
        result = resolve_composition("ROOT", get_formula, classifications.get)
        assert result.composition_complete is True
        assert f"CONCEPT_{n}" in result.directly_referenced_concepts

    def test_terminal_raw_input_no_formula(self):
        """BOUNDARY. A root cell with no formula at all resolves to an
        empty, complete composition — nothing to expand."""
        result = resolve_composition("ROOT", lambda c: None, lambda c: None)
        assert result == ObservedComposition(
            directly_referenced_concepts=frozenset(),
            unclassified_references=frozenset(),
            composition_complete=True,
        )
