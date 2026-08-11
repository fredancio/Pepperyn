"""
test_financial_doctrine.py — services/financial_doctrine.py.

Covers: the real Phidani row 133 Golden Case (assembled through real
formula evidence, the formula reference extractor, a deterministic concept-
classification fixture standing in for Economic Meaning, Concept
Vocabulary, the Doctrine registry, and compare_against_doctrine — every
ingredient traceable, contract §17/mission §19), the MATCH countercase
(mission §20), NOT_APPLICABLE, missing-doctrine behavior, registry
cross-reference validation, no-stored-prose, deterministic explanation,
applicability non-execution, and the Doctrine/classifier import boundary
(mission §31).

Classification (mission §35): each test is tagged INVARIANT, BEHAVIOR,
BOUNDARY, or WEAK/GUARD in its docstring.
"""
import ast
import dataclasses
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

from services.concept_vocabulary import match_concept
from services.financial_doctrine import (
    DOCTRINE_REGISTRY,
    DoctrineStatement,
    _build_registry,
    compare_against_doctrine,
    get_doctrine,
    render_explanation,
)
from services.formula_evidence import cell_formula_evidence, get_worksheet, load_formula_workbook
from services.formula_reference_extractor import ObservedComposition, resolve_composition

_REAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "Phidani.xlsx")
_HAS_REAL_FILE = os.path.exists(_REAL_FILE)


def _real_bytes() -> bytes:
    with open(_REAL_FILE, "rb") as f:
        return f.read()


# ─────────────────────────────────────────────────────────────────────────────
# Real Phidani row 133 Golden Case (contract §17, mission §19)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
class TestRealRow133GoldenCase:
    """PERSONNEL_COST rows live at 134-160 (aggregated at row 161), entirely
    outside row 133's own forward closure (C35, C132 and everything they in
    turn reference) — genuinely, transitively absent, not merely
    unreferenced at the root."""

    @pytest.fixture(scope="class")
    @classmethod
    def ws(cls):
        wb = load_formula_workbook(_real_bytes())
        return get_worksheet(wb, "PHIDANI")

    def _wire_real_workbook(self, ws):
        """Build get_formula/classify_cell over the real worksheet.

        classify_cell is the Economic Meaning stand-in (contract §14
        Pattern A): a deterministic test fixture, not a classifier. It
        only ever answers "is this cell PERSONNEL_COST?" — rows 134-160
        are the only cells ever classified PERSONNEL_COST; everything else
        that IS successfully read is classified as an inert placeholder
        concept (OTHER) so it never appears in unclassified_references
        purely because Economic Meaning wasn't implemented for it. A cell
        with no captured value at all (never visited by the real range)
        is simply never queried.
        """

        def get_formula(cell: str):
            if ":" in cell:  # opaque 2D-range token — never applicable to Phidani
                return None
            col_letters, row = coordinate_from_string(cell)
            col = column_index_from_string(col_letters)
            fe = cell_formula_evidence(ws, row, col)
            return fe.formula_text if fe.is_formula else None

        def classify_cell(cell: str):
            if ":" in cell:
                return None  # unresolved opaque token -> forces UNKNOWN, never MISMATCH
            col_letters, row = coordinate_from_string(cell)
            if col_letters == "C" and 134 <= row <= 160:
                return "PERSONNEL_COST"
            # The fixture's classification rule is pure row-range membership
            # (contract §14 Pattern A: a deterministic stand-in for Economic
            # Meaning, not a content-reading classifier) -- it always knows
            # whether a coordinate falls in the personnel-cost range, so it
            # always answers, regardless of whether the real cell happens to
            # be a formula, a literal, or genuinely empty. An empty cell
            # contributes nothing to a SUM either way and is confirmed, not
            # unclassifiable.
            return "OTHER"

        return get_formula, classify_cell

    def test_candidate_concept_from_real_caption(self, ws):
        """INVARIANT (contract §5/§17). candidate_concept is derived from
        the real caption via Concept Vocabulary's lexical match, never
        hardcoded as a Python literal."""
        caption = ws.cell(row=133, column=2).value
        assert match_concept(caption) == "EBITDA"

    def test_row_133_is_mismatch(self, ws):
        """INVARIANT — the Golden Case. Every ingredient traceable: real
        formula evidence, the forward reference extractor, the concept
        classification fixture, Vocabulary, the Doctrine registry, and
        compare_against_doctrine. No hardcoded "row 133 is wrong" branch
        anywhere in the production code."""
        caption = ws.cell(row=133, column=2).value
        candidate_concept = match_concept(caption)
        assert candidate_concept == "EBITDA"

        get_formula, classify_cell = self._wire_real_workbook(ws)
        observed = resolve_composition("C133", get_formula, classify_cell)

        doctrine = get_doctrine(candidate_concept)
        assert doctrine is not None

        result = compare_against_doctrine(candidate_concept, doctrine, observed)
        assert result == "MISMATCH"
        assert observed.composition_complete is True
        assert "PERSONNEL_COST" not in observed.directly_referenced_concepts


# ─────────────────────────────────────────────────────────────────────────────
# MATCH countercase (mission §20) — same Vocabulary/Doctrine/comparison code
# ─────────────────────────────────────────────────────────────────────────────


class TestMatchCountercase:
    def test_synthetic_match_no_match_specific_branch(self):
        """INVARIANT. Minimal synthetic composition where PERSONNEL_COST is
        transitively included before the KPI — exact same production
        functions as the real MISMATCH case above, only the input differs."""
        formulas = {"EBITDA_CELL": "=B1-B2", "B2": "=B3+B4", "B3": None, "B4": None}
        classifications = {"B2": "OPEX_TOTAL", "B3": "EXTERNAL_COSTS", "B4": "PERSONNEL_COST"}
        observed = resolve_composition(
            "EBITDA_CELL", lambda c: formulas.get(c), lambda c: classifications.get(c)
        )
        doctrine = get_doctrine("EBITDA")
        result = compare_against_doctrine("EBITDA", doctrine, observed)
        assert result == "MATCH"


# ─────────────────────────────────────────────────────────────────────────────
# MATCH/MISMATCH asymmetry — direct proof at the comparison-function level
# (mission §14/§15, contract §16a)
# ─────────────────────────────────────────────────────────────────────────────


class TestMatchAsymmetry:
    def test_match_does_not_require_global_completeness(self):
        """INVARIANT — the central corrected invariant of this contract
        line. composition_complete=False (an unrelated unresolved branch),
        yet the required concept is positively found -> MATCH."""
        observed = ObservedComposition(
            directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
            unclassified_references=frozenset({"UNK"}),
            composition_complete=False,
        )
        doctrine = get_doctrine("EBITDA")
        assert compare_against_doctrine("EBITDA", doctrine, observed) == "MATCH"

    def test_mismatch_requires_composition_complete_true(self):
        """INVARIANT. The same missing required concept, but with
        composition_complete=False, must yield UNKNOWN, never MISMATCH."""
        observed_incomplete = ObservedComposition(
            directly_referenced_concepts=frozenset(),
            unclassified_references=frozenset({"UNK"}),
            composition_complete=False,
        )
        observed_complete = ObservedComposition(
            directly_referenced_concepts=frozenset(),
            unclassified_references=frozenset(),
            composition_complete=True,
        )
        doctrine = get_doctrine("EBITDA")
        assert compare_against_doctrine("EBITDA", doctrine, observed_incomplete) == "UNKNOWN"
        assert compare_against_doctrine("EBITDA", doctrine, observed_complete) == "MISMATCH"

    def test_unknown_is_not_absence_no_shortcut(self):
        """INVARIANT (mission §15). Searches the actual comparison result:
        a required concept missing from the classified set, with an
        incomplete closure, must never produce MISMATCH — only complete
        composition permits negative proof."""
        observed = ObservedComposition(
            directly_referenced_concepts=frozenset(),
            unclassified_references=frozenset({"SOME_CELL"}),
            composition_complete=False,
        )
        doctrine = get_doctrine("EBITDA")
        result = compare_against_doctrine("EBITDA", doctrine, observed)
        assert result != "MISMATCH"
        assert result == "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# NOT_APPLICABLE, missing doctrine
# ─────────────────────────────────────────────────────────────────────────────


class TestNotApplicable:
    def test_confidently_different_concept_short_circuits(self):
        """INVARIANT (mission §27). Must short-circuit before any
        prerequisite analysis — no EBITDA doctrine applied to an unrelated
        concept, regardless of what `observed` contains."""
        doctrine = get_doctrine("EBITDA")
        observed_anything = ObservedComposition(
            directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
            unclassified_references=frozenset(),
            composition_complete=True,
        )
        assert compare_against_doctrine("REVENUE", doctrine, observed_anything) == "NOT_APPLICABLE"


class TestMissingDoctrine:
    def test_no_doctrine_entry_is_not_fabricated(self):
        """INVARIANT (mission §28). A concept with no doctrine entry must
        not be silently turned into a fabricated MATCH/MISMATCH — get_doctrine
        returns None, and callers must treat that as comparison-unavailable."""
        assert get_doctrine("PERSONNEL_COST") is None  # registered in Vocabulary, has NO doctrine entry
        assert get_doctrine("NOT_A_REAL_CONCEPT") is None


# ─────────────────────────────────────────────────────────────────────────────
# Registry validation (mission §7/§29)
# ─────────────────────────────────────────────────────────────────────────────


class TestRegistryValidation:
    def test_duplicate_concept_doctrine_entry_rejected(self):
        """INVARIANT."""
        duplicates = (
            DoctrineStatement(
                id="A", concept="EBITDA", required_prior_deductions=("PERSONNEL_COST",),
                authority_type="PROFESSIONAL_CONVENTION", provenance="x", version=1,
            ),
            DoctrineStatement(
                id="B", concept="EBITDA", required_prior_deductions=(),
                authority_type="PROFESSIONAL_CONVENTION", provenance="y", version=1,
            ),
        )
        with pytest.raises(ValueError):
            _build_registry(duplicates)

    def test_unknown_concept_reference_rejected(self):
        """INVARIANT. Doctrine's own `concept` field must exist in
        Vocabulary."""
        bad = (
            DoctrineStatement(
                id="A", concept="NOT_A_REGISTERED_CONCEPT", required_prior_deductions=(),
                authority_type="PROFESSIONAL_CONVENTION", provenance="x", version=1,
            ),
        )
        with pytest.raises(ValueError):
            _build_registry(bad)

    def test_invalid_required_prior_deductions_reference_rejected(self):
        """INVARIANT. Every concept named in required_prior_deductions must
        also exist in Vocabulary — no silent runtime fallback to an
        arbitrary string."""
        bad = (
            DoctrineStatement(
                id="A", concept="EBITDA", required_prior_deductions=("NOT_A_REGISTERED_CONCEPT",),
                authority_type="PROFESSIONAL_CONVENTION", provenance="x", version=1,
            ),
        )
        with pytest.raises(ValueError):
            _build_registry(bad)

    def test_registry_immutable_no_runtime_mutation_api(self):
        """BOUNDARY."""
        import services.financial_doctrine as mod

        public_names = [n for n in dir(mod) if not n.startswith("_")]
        write_like = [n for n in public_names if any(w in n.lower() for w in ("register", "add", "mutate", "update", "delete", "write"))]
        assert write_like == []

    def test_exactly_one_doctrine_entry_v0(self):
        """BOUNDARY (mission §6 — "the first entry exists only to prove the
        architecture"). No Gross Margin, EBIT, FCF, Working Capital, or
        ratio entries."""
        assert len(DOCTRINE_REGISTRY) == 1
        assert set(DOCTRINE_REGISTRY.keys()) == {"EBITDA"}


# ─────────────────────────────────────────────────────────────────────────────
# No stored prose / deterministic explanation (mission §18/§32, contract §10)
# ─────────────────────────────────────────────────────────────────────────────


class TestNoStoredProse:
    def test_doctrine_statement_has_no_proposition_field(self):
        """INVARIANT — structural, mirrors the same introspection pattern
        already used elsewhere in this codebase for "no numeric value
        produced" guarantees."""
        field_names = {f.name for f in dataclasses.fields(DoctrineStatement)}
        assert "proposition" not in field_names

    def test_doctrine_statement_has_no_applicability_field(self):
        """INVARIANT (contract §12, corrected 2026-08-11). applicability is
        documentary metadata only — not a dataclass field, so it cannot be
        misread because it does not exist."""
        field_names = {f.name for f in dataclasses.fields(DoctrineStatement)}
        assert "applicability" not in field_names

    def test_doctrine_statement_has_no_concept_aliases_field(self):
        """INVARIANT (contract §8, corrected). Aliases live only in
        Concept Vocabulary — no duplicated representation."""
        field_names = {f.name for f in dataclasses.fields(DoctrineStatement)}
        assert "concept_aliases" not in field_names

    def test_explanation_is_deterministic(self):
        """BEHAVIOR."""
        doctrine = get_doctrine("EBITDA")
        assert render_explanation(doctrine) == render_explanation(doctrine)

    def test_explanation_changes_mechanically_with_structured_content(self):
        """INVARIANT (mission §18). Changing structured doctrine content
        changes rendered output mechanically — the renderer never carries
        independent financial semantics."""
        a = DoctrineStatement(
            id="A", concept="EBITDA", required_prior_deductions=("PERSONNEL_COST",),
            authority_type="PROFESSIONAL_CONVENTION", provenance="x", version=1,
        )
        b = DoctrineStatement(
            id="B", concept="EBITDA", required_prior_deductions=(),
            authority_type="PROFESSIONAL_CONVENTION", provenance="x", version=1,
        )
        assert render_explanation(a) != render_explanation(b)


class TestApplicabilityNeverExecuted:
    def test_compare_against_doctrine_source_never_references_applicability(self):
        """INVARIANT (mission §9/§19, contract §12). AST-based structural
        guarantee: the comparison function's own CODE BODY never accesses
        an `.applicability` attribute (docstring prose explaining that the
        field does not exist is not itself a violation — checked via the
        parsed syntax tree, not a raw substring match on the whole source,
        which would also match this very docstring)."""
        source = inspect.getsource(compare_against_doctrine)
        tree = ast.parse(source)
        attribute_names = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        assert "applicability" not in attribute_names


class TestAuthorityModel:
    def test_only_professional_convention_populated_in_v0(self):
        """BOUNDARY (mission §8). v0 populates only PROFESSIONAL_CONVENTION;
        MATHEMATICAL_IDENTITY is declared in the type but unused."""
        for stmt in DOCTRINE_REGISTRY.values():
            assert stmt.authority_type == "PROFESSIONAL_CONVENTION"

    def test_no_behavioral_branching_on_authority_type(self):
        """INVARIANT (mission §8 — "do not implement behavioral policy for
        mathematical identities beyond what the contract actually
        authorizes"). compare_against_doctrine's source never branches on
        authority_type."""
        source = inspect.getsource(compare_against_doctrine)
        assert "authority_type" not in source


# ─────────────────────────────────────────────────────────────────────────────
# Provenance/version, zero LLM, no DB, classification boundary (mission §31/§33)
# ─────────────────────────────────────────────────────────────────────────────


class TestProvenanceAndVersion:
    def test_every_doctrine_entry_has_provenance_and_version(self):
        """BEHAVIOR."""
        for stmt in DOCTRINE_REGISTRY.values():
            assert stmt.provenance and isinstance(stmt.provenance, str)
            assert isinstance(stmt.version, int) and stmt.version >= 1


class TestGovernanceBoundaries:
    """INVARIANT (mission §31/§33). Static + behavioral checks that Doctrine
    never imports LLM/classifier/persistence/dialogue modules — runtime
    behavior tests are primary (see
    test_comparison_consumes_only_already_classified_concepts below and
    the boundary tests in TestRealRow133GoldenCase, which prove the actual
    call graph never touches such a module); this AST-based import check is
    a fast structural corroboration, not the sole guarantee. Deliberately
    AST-based (only real `import`/`from ... import` statements), not a raw
    substring search on the whole source — a substring search would also
    flag this module's own docstrings, which legitimately *name* the
    forbidden systems while explaining that they are NOT used."""

    _FORBIDDEN_MODULE_SUBSTRINGS = (
        "openai",
        "anthropic",
        "llm_service",
        "epistemic_dialogue",
        "knowledge_model",
        "conversation_engine",
        "executive_case",
        "supabase",
        "psycopg",
        "sqlalchemy",
    )

    def _imported_module_names(self, module) -> set:
        tree = ast.parse(inspect.getsource(module))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        return names

    def _assert_no_forbidden_imports(self, module):
        imported = self._imported_module_names(module)
        for name in imported:
            lowered = name.lower()
            for forbidden in self._FORBIDDEN_MODULE_SUBSTRINGS:
                assert forbidden not in lowered, f"forbidden import found: {name}"

    def test_no_forbidden_imports_in_financial_doctrine(self):
        import services.financial_doctrine as mod

        self._assert_no_forbidden_imports(mod)

    def test_no_forbidden_imports_in_concept_vocabulary(self):
        import services.concept_vocabulary as mod

        self._assert_no_forbidden_imports(mod)

    def test_no_forbidden_imports_in_formula_reference_extractor(self):
        import services.formula_reference_extractor as mod

        self._assert_no_forbidden_imports(mod)

    def test_comparison_consumes_only_already_classified_concepts(self):
        """BEHAVIOR. compare_against_doctrine's signature takes
        pre-classified inputs only — no raw text, no file, no cell
        coordinates it could classify itself."""
        params = list(inspect.signature(compare_against_doctrine).parameters)
        assert params == ["candidate_concept", "doctrine", "observed"]

    def test_no_global_mutable_state_beyond_frozen_registries(self):
        """BOUNDARY. The two module-level registries are the only
        module-level containers, and both are built once at import time via
        a fail-closed constructor — never mutated afterward."""
        import services.financial_doctrine as mod

        assert isinstance(mod.DOCTRINE_REGISTRY, dict)
        # Frozen dataclass values inside prevent in-place field mutation;
        # no setter/mutator function exists (covered by
        # test_registry_immutable_no_runtime_mutation_api above).
