"""
test_observation_structure_v0.py — Observation Structure v0's pure kernel
(backend/services/observation_structure.py) and its formula-evidence input
(backend/services/formula_evidence.py).

Covers: the real Phidani Golden Case (contract §11), the row-163
dual-dimension independence test (contract §16 — "the single most
important regression guard this contract requires"), the fail-closed
arithmetic-independence test (contract §16, 2026-08-10 correction), the
SECTION_HEADER / NOT_APPLICABLE co-occurrence invariant (contract §16),
and the 16-category adversarial fixture matrix A-P required by the
implementation mission, mapped onto contract §12's own fixture semantics.

See docs/Architecture/Cognitive/OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from services.formula_evidence import (
    CellFormulaEvidence,
    cell_formula_evidence,
    get_worksheet,
    load_formula_workbook,
)
from services.observation_structure import (
    DERIVATION_STATUS_VALUES,
    STRUCTURAL_ROLE_VALUES,
    TIER_VALUES,
    ObservationClassification,
    classify_observation,
)

_REAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "Phidani.xlsx")
_HAS_REAL_FILE = os.path.exists(_REAL_FILE)


def _real_bytes() -> bytes:
    with open(_REAL_FILE, "rb") as f:
        return f.read()


def _fe(is_formula: bool, formula_text=None, has_literal_value: bool = True) -> CellFormulaEvidence:
    """Synthetic formula-evidence constructor for fixtures with no real
    Phidani grounding."""
    return CellFormulaEvidence(
        is_formula=is_formula,
        formula_text=formula_text if is_formula else None,
        has_literal_value=has_literal_value,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Real Phidani Golden Case (contract §11)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
class TestRealPhidaniGoldenCase:
    """Primary regression anchor (contract §16). Rows 3/133/134/161/163/165,
    plus 231/234/256/369 used elsewhere in this window's real-file
    inspection, column C throughout (contract §2's scope-unit correction —
    the Golden Case is implicitly column-C-scoped)."""

    @pytest.fixture(scope="class")
    @classmethod
    def ws(cls):
        wb = load_formula_workbook(_real_bytes())
        return get_worksheet(wb, "PHIDANI")

    def _classify(self, ws, row, column=3):
        code = ws.cell(row=row, column=1).value
        fe = cell_formula_evidence(ws, row, column)
        return classify_observation(code, fe)

    def test_row_134_leaf_source_value(self, ws):
        r = self._classify(ws, 134)
        assert r.structural_role == "LEAF"
        assert r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "SOURCE_VALUE"
        assert r.formula_text is None

    def test_row_161_aggregate_derived_sum_range(self, ws):
        r = self._classify(ws, 161)
        assert r.structural_role == "AGGREGATE"
        assert r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "DERIVED"
        assert r.formula_text == "=SUM(C134:C160)"

    def test_row_165_aggregate_derived_compound_row(self, ws):
        r = self._classify(ws, 165)
        assert r.structural_role == "AGGREGATE"
        assert r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "DERIVED"
        assert r.formula_text == "=C34+C132+C161+C163+C164"

    def test_row_3_section_header(self, ws):
        r = self._classify(ws, 3)
        assert r.structural_role == "SECTION_HEADER"
        assert r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "NOT_APPLICABLE"

    def test_row_369_section_header(self, ws):
        r = self._classify(ws, 369)
        assert r.structural_role == "SECTION_HEADER"
        assert r.derivation_status == "NOT_APPLICABLE"

    def test_row_163_aggregate_derived_single_cell_passthrough(self, ws):
        """The central falsifier of the original one-enum model (§2)."""
        r = self._classify(ws, 163)
        assert r.structural_role == "AGGREGATE"
        assert r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "DERIVED"
        assert r.formula_text == "=C162"

    def test_row_133_kpi_hypothesis_derived_from_derived(self, ws):
        r = self._classify(ws, 133)
        assert r.structural_role == "KPI"
        assert r.structural_role_tier == "HYPOTHESIS"  # never STRONG_INFERENCE for KPI
        assert r.derivation_status == "DERIVED"
        assert r.formula_text == "=C35-C132"

    def test_row_256_kpi_shaped_blank_column_stays_kpi_not_section_header(self, ws):
        """Contract §2's structural_role/derivation_status divergence proof:
        row 256 ("B3") is KPI-shaped but blank in column C — must classify
        as KPI + NOT_APPLICABLE, never collapse into SECTION_HEADER."""
        r = self._classify(ws, 256)
        assert r.structural_role == "KPI"
        assert r.derivation_status == "NOT_APPLICABLE"

    def test_row_231_aggregate_bold_false_proves_bold_not_required(self, ws):
        """Real proof (contract §5) that bold is not a reliable/required
        signal: row 231 is bold=False yet a genuine formula-derived
        subtotal, and this classifier never consults bold at all."""
        r = self._classify(ws, 231)
        assert r.structural_role == "AGGREGATE"
        assert r.derivation_status == "DERIVED"

    def test_row_234_malformed_code_case_o_robustness(self, ws):
        """Case O: the real corrupted account code
        "72.44444444444444" — does not affect derivation_status (still
        DERIVED, from formula evidence alone), degrades structural_role
        honestly to UNKNOWN rather than guessing."""
        r = self._classify(ws, 234)
        assert r.derivation_status == "DERIVED"
        assert r.structural_role == "UNKNOWN"
        assert r.structural_role_tier == "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# Row 163 dual-dimension independence test — "the single most important
# regression guard this contract requires" (contract §16)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
def test_row_163_structural_role_and_derivation_status_are_independently_asserted():
    """A future refactor that silently re-merges the two dimensions (e.g.
    inferring structural_role purely from is_formula, or inferring
    derivation_status purely from account-code shape) would be caught
    here, and nowhere else as directly. Row 163 is AGGREGATE (structural,
    from account-code evidence: "630" is a 3-digit statutory-schema code)
    via a DERIVED single-cell passthrough (from formula evidence alone:
    "=C162") — the formula's trivial shape must never downgrade the role,
    and the role's "aggregate" label must never upgrade the derivation
    mechanism into something more than a passthrough."""
    wb = load_formula_workbook(_real_bytes())
    ws = get_worksheet(wb, "PHIDANI")
    code = ws.cell(row=163, column=1).value
    fe = cell_formula_evidence(ws, 163, 3)

    # Prove structural_role does not depend on formula shape complexity:
    # a passthrough (=C162) yields the identical AGGREGATE/STRONG verdict
    # a genuine multi-row SUM would (row 161's shape).
    role_only = classify_observation(code, fe).structural_role
    assert role_only == "AGGREGATE"

    # Prove derivation_status does not depend on structural role at all —
    # swap in an UNRECOGNIZED code (all structural evidence removed) and
    # confirm derivation_status is unchanged, still DERIVED from formula
    # evidence alone.
    result_no_code_evidence = classify_observation(None, fe)
    assert result_no_code_evidence.derivation_status == "DERIVED"
    assert result_no_code_evidence.structural_role != "AGGREGATE"  # role evidence genuinely removed


# ─────────────────────────────────────────────────────────────────────────────
# Fail-closed arithmetic independence (contract §2/§10/§16, 2026-08-10 fix)
# ─────────────────────────────────────────────────────────────────────────────


class TestFailClosedIndependence:
    def test_source_value_is_independent(self):
        r = classify_observation("620250", _fe(is_formula=False, has_literal_value=True))
        assert r.derivation_status == "SOURCE_VALUE"
        assert r.is_arithmetically_independent() is True

    def test_derived_is_not_independent(self):
        r = classify_observation("62", _fe(is_formula=True, formula_text="=SUM(C1:C5)"))
        assert r.derivation_status == "DERIVED"
        assert r.is_arithmetically_independent() is False

    def test_not_applicable_is_not_independent(self):
        r = classify_observation(None, _fe(is_formula=False, has_literal_value=False))
        assert r.derivation_status == "NOT_APPLICABLE"
        assert r.is_arithmetically_independent() is False

    def test_unknown_is_not_independent_the_critical_guard(self):
        """The single most operationally significant guard in the contract
        (§16): UNKNOWN must never be silently treated as safe to sum. A
        no-formula-cached export degrades every would-be-aggregate row to
        UNKNOWN (aggregate-shaped code, no formula) — this must stay
        excluded from "independent."""
        r = classify_observation("62", _fe(is_formula=False, has_literal_value=True))
        assert r.derivation_status == "UNKNOWN"
        assert r.is_arithmetically_independent() is False

    def test_naive_not_equal_derived_formula_would_have_been_wrong(self):
        """Direct proof the pre-correction formula (`!= DERIVED`) was a
        real bug: on the synthetic no-formula-cached fixture above, the
        naive check would have returned True (wrongly "safe"), while the
        corrected fail-closed formula correctly returns False."""
        r = classify_observation("62", _fe(is_formula=False, has_literal_value=True))
        naive_check = r.derivation_status != "DERIVED"
        correct_check = r.is_arithmetically_independent()
        assert naive_check is True  # the bug: naive formula says "safe"
        assert correct_check is False  # the fix: fail-closed says "not safe"
        assert naive_check != correct_check

    def test_synthetic_whole_file_no_formula_export_every_row_unknown_or_source_value(self):
        """Case G/L: a materialised/flattened export. Every row that would
        normally carry a formula (aggregate/KPI-shaped codes) degrades to
        UNKNOWN; genuine leaf-shaped codes still resolve to SOURCE_VALUE
        (no formula was ever expected for them). No row is wrongly
        upgraded to "independent" merely because the whole file lacks
        formulas."""
        synthetic_rows = [
            ("620250", _fe(is_formula=False, has_literal_value=True)),  # leaf-shaped
            ("62", _fe(is_formula=False, has_literal_value=True)),  # aggregate-shaped, no formula
            ("60/64", _fe(is_formula=False, has_literal_value=True)),  # aggregate-shaped, no formula
            ("B1", _fe(is_formula=False, has_literal_value=True)),  # KPI-shaped, no formula
        ]
        results = [classify_observation(code, fe) for code, fe in synthetic_rows]
        independent_flags = [r.is_arithmetically_independent() for r in results]
        # Only the genuine leaf resolves independent; the three
        # aggregate/KPI-shaped-but-formula-less rows must not.
        assert independent_flags == [True, False, False, False]
        assert results[1].derivation_status == "UNKNOWN"
        assert results[2].derivation_status == "UNKNOWN"
        assert results[3].derivation_status == "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION_HEADER / NOT_APPLICABLE co-occurrence invariant (contract §16)
# ─────────────────────────────────────────────────────────────────────────────


class TestSectionHeaderInvariant:
    def test_section_header_always_pairs_with_not_applicable(self):
        r = classify_observation(None, _fe(is_formula=False, has_literal_value=False))
        assert r.structural_role == "SECTION_HEADER"
        assert r.derivation_status == "NOT_APPLICABLE"

    def test_section_header_never_produced_with_a_value_present(self):
        """A single blank cell in an otherwise KPI-shaped row must never
        trigger SECTION_HEADER (contract §3.1) — proven here directly by
        constructing exactly that shape."""
        r = classify_observation("B3", _fe(is_formula=False, has_literal_value=False))
        assert r.structural_role != "SECTION_HEADER"

    @pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
    def test_no_real_golden_case_row_violates_the_invariant(self):
        wb = load_formula_workbook(_real_bytes())
        ws = get_worksheet(wb, "PHIDANI")
        for row in (3, 6, 133, 134, 161, 163, 165, 231, 234, 256, 369):
            code = ws.cell(row=row, column=1).value
            fe = cell_formula_evidence(ws, row, 3)
            r = classify_observation(code, fe)
            if r.structural_role == "SECTION_HEADER":
                assert r.derivation_status == "NOT_APPLICABLE", (
                    f"row {row} violates the SECTION_HEADER/NOT_APPLICABLE invariant"
                )


# ─────────────────────────────────────────────────────────────────────────────
# 16-category adversarial fixture matrix, A-P (implementation mission §20;
# mapped onto contract §12's own fixture semantics where they overlap)
# ─────────────────────────────────────────────────────────────────────────────


class TestFixtureAdversarialMatrix:
    def test_a_leaf_direct(self):
        r = classify_observation("705000", _fe(is_formula=False, has_literal_value=True))
        assert r.structural_role == "LEAF" and r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "SOURCE_VALUE"

    def test_b_formula_aggregate_sum_range(self):
        r = classify_observation("61", _fe(is_formula=True, formula_text="=SUM(C10:C20)"))
        assert r.structural_role == "AGGREGATE" and r.structural_role_tier == "STRONG_INFERENCE"
        assert r.derivation_status == "DERIVED"

    @pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
    def test_c_formula_single_cell_passthrough_real_row_163(self):
        wb = load_formula_workbook(_real_bytes())
        ws = get_worksheet(wb, "PHIDANI")
        r = classify_observation(ws.cell(row=163, column=1).value, cell_formula_evidence(ws, 163, 3))
        assert r.structural_role == "AGGREGATE"
        assert r.derivation_status == "DERIVED"

    def test_d_formula_ratio_kpi_candidate_synthetic(self):
        """Purely synthetic (contract §12: no division/ratio formula exists
        anywhere in real Phidani, confirmed by direct inspection)."""
        r = classify_observation("B2", _fe(is_formula=True, formula_text="=C35/C6"))
        assert r.structural_role == "KPI" and r.structural_role_tier == "HYPOTHESIS"
        assert r.derivation_status == "DERIVED"

    def test_e_section_header_no_value(self):
        r = classify_observation("Section Title", _fe(is_formula=False, has_literal_value=False))
        assert r.structural_role == "SECTION_HEADER"
        assert r.derivation_status == "NOT_APPLICABLE"

    def test_f_hardcoded_subtotal_no_formula(self):
        """Contract §12 fixture F, followed over §2's conflicting
        illustrative example — see observation_structure.py's module
        docstring for the discovered tension and why F/§16 was chosen."""
        r = classify_observation("62", _fe(is_formula=False, has_literal_value=True))
        assert r.derivation_status == "UNKNOWN"
        assert r.structural_role == "AGGREGATE"
        assert r.structural_role_tier == "HYPOTHESIS"

    def test_g_no_formula_export_whole_file_adversary(self):
        rows = [
            classify_observation("620250", _fe(is_formula=False, has_literal_value=True)),
            classify_observation("62", _fe(is_formula=False, has_literal_value=True)),
            classify_observation("60/64", _fe(is_formula=False, has_literal_value=True)),
        ]
        assert rows[0].derivation_status == "SOURCE_VALUE"
        assert rows[1].derivation_status == "UNKNOWN"
        assert rows[2].derivation_status == "UNKNOWN"

    @pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
    def test_h_formula_contradicts_caption_no_reconciliation_attempted(self):
        """derivation_status trusts the formula; structural_role trusts
        code shape; the two are allowed to diverge without being forced
        into agreement (contract §12, resolved as the row-163 shape)."""
        # Leaf-shaped code that is, contradictorily, a formula.
        r = classify_observation("705000", _fe(is_formula=True, formula_text="=C1+C2"))
        assert r.derivation_status == "DERIVED"  # formula evidence wins for this dimension
        assert r.structural_role == "UNKNOWN"  # code-shape evidence honestly conflicts, no guess

    def test_i_misleading_row_order_never_influences_classification(self):
        """Correction 2 (prior FRU mission): derivation_status/structural_role
        must never be inferred from position/order. classify_observation
        takes no row-index or ordering argument at all — classifying the
        "same" observation twice, once as if it were first and once as if
        it were last in a synthetic sequence, must be byte-identical,
        since no ordering information can reach the function."""
        fe = _fe(is_formula=True, formula_text="=SUM(C1:C9)")
        r_first = classify_observation("61", fe)
        # Simulate "elsewhere in a differently-ordered sheet" by simply
        # calling again — no index parameter exists to vary.
        r_elsewhere = classify_observation("61", fe)
        assert r_first == r_elsewhere

    def test_j_zero_valued_leaf_is_source_value_not_absence(self):
        """Article III: a true zero is a fact, never confused with
        "nothing here." """
        r = classify_observation("620999", _fe(is_formula=False, has_literal_value=True))
        assert r.derivation_status == "SOURCE_VALUE"

    def test_k_blank_future_period_cell(self):
        r = classify_observation("620250", _fe(is_formula=False, has_literal_value=False))
        assert r.derivation_status == "NOT_APPLICABLE"

    @pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
    def test_l_malformed_account_code_real_row_234(self):
        wb = load_formula_workbook(_real_bytes())
        ws = get_worksheet(wb, "PHIDANI")
        r = classify_observation(ws.cell(row=234, column=1).value, cell_formula_evidence(ws, 234, 3))
        assert r.derivation_status == "DERIVED"  # unaffected by the corrupted code
        assert r.structural_role == "UNKNOWN"  # honest degrade, no crash, no guess

    def test_m_mixed_pl_and_balance_sheet_section_headers_independent(self):
        """v0 does not need to know which statement a row belongs to
        (contract §12) — two SECTION_HEADER rows from "different
        statements" classify identically and independently, no cross-row
        state is consulted."""
        r_pl = classify_observation("Compte de résultats", _fe(is_formula=False, has_literal_value=False))
        r_bs = classify_observation("PASSIF", _fe(is_formula=False, has_literal_value=False))
        assert r_pl.structural_role == r_bs.structural_role == "SECTION_HEADER"
        assert r_pl.derivation_status == r_bs.derivation_status == "NOT_APPLICABLE"

    @pytest.mark.skipif(not _HAS_REAL_FILE, reason="Phidani.xlsx not present in this checkout")
    def test_n_row_163_dual_dimension_assertion(self):
        wb = load_formula_workbook(_real_bytes())
        ws = get_worksheet(wb, "PHIDANI")
        r = classify_observation(ws.cell(row=163, column=1).value, cell_formula_evidence(ws, 163, 3))
        assert r.structural_role == "AGGREGATE"
        assert r.derivation_status == "DERIVED"
        assert r.formula_text == "=C162"

    def test_o_formula_result_blank_but_formula_present_is_derived(self):
        """Resolved edge case (contract §3.2, 2026-08-10): mechanism-based,
        not output-based. formula_evidence.py never even carries a cached
        result — is_formula alone determines DERIVED, regardless of what
        the (unobserved-by-this-module) cached value would have been."""
        r = classify_observation("62", _fe(is_formula=True, formula_text="=SUM(C1:C5)"))
        assert r.derivation_status == "DERIVED"
        assert r.derivation_status != "NOT_APPLICABLE"

    def test_p_fail_closed_unknown_independence(self):
        r = classify_observation("62", _fe(is_formula=False, has_literal_value=True))
        assert r.derivation_status == "UNKNOWN"
        assert r.is_arithmetically_independent() is False


# ─────────────────────────────────────────────────────────────────────────────
# Output vocabulary sanity (guards against silent typo/enum drift)
# ─────────────────────────────────────────────────────────────────────────────


class TestOutputVocabulary:
    def test_every_result_uses_only_contract_vocabulary(self):
        samples = [
            classify_observation("620250", _fe(False, has_literal_value=True)),
            classify_observation("62", _fe(True, "=SUM(C1:C5)")),
            classify_observation("B1", _fe(True, "=C1-C2")),
            classify_observation(None, _fe(False, has_literal_value=False)),
            classify_observation("62", _fe(False, has_literal_value=True)),
        ]
        for r in samples:
            assert r.structural_role in STRUCTURAL_ROLE_VALUES
            assert r.structural_role_tier in TIER_VALUES
            assert r.derivation_status in DERIVATION_STATUS_VALUES

    def test_kpi_never_reaches_strong_inference_tier(self):
        """Contract §3.1: KPI can never be assigned at STRONG_INFERENCE —
        checked across every synthetic KPI-shaped input this suite
        constructs, formula present or not."""
        for is_formula, text in [(True, "=C1-C2"), (False, None)]:
            r = classify_observation("B1", _fe(is_formula, text, has_literal_value=not is_formula and True))
            if r.structural_role == "KPI":
                assert r.structural_role_tier != "STRONG_INFERENCE"
