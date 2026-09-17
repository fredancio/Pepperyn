"""Artifact checks ONLY: no financial evaluation, product import or network."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from sandbox.verify_financial_review_bundle import BUNDLE, read_json, validate_schema, verify


class FinancialReviewBundleIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.inputs = read_json(BUNDLE / "synthetic-inputs-v2.json")
        self.oracle = read_json(BUNDLE / "expected-contracts-v2.json")
        self.review = (BUNDLE / "review-source-v2.txt").read_text(encoding="utf-8")

    def test_frozen_bundle_is_integral_but_not_executed_or_gate_pass(self):
        result = verify()
        self.assertEqual(result["artifact_integrity"], "PASS")
        self.assertEqual(result["financial_analyses_executed"], 0)
        self.assertEqual(result["financial_reliability_gate"], "OPEN_NOT_PASS")

    def test_input_mutation_breaks_frozen_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for source in BUNDLE.iterdir():
                if source.is_file():
                    (target / source.name).write_bytes(source.read_bytes())
            self.inputs["cases"][0]["observations"][0]["reported_value"] += 1
            (target / "synthetic-inputs-v2.json").write_text(json.dumps(self.inputs), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "FROZEN_CONTENT_MISMATCH"):
                verify(target)

    def test_crlf_checkout_does_not_change_canonical_text_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for source in BUNDLE.iterdir():
                if source.is_file():
                    text = source.read_text(encoding="utf-8").replace("\n", "\r\n")
                    (target / source.name).write_bytes(text.encode("utf-8"))
            self.assertEqual(verify(target), verify())

    def test_cross_case_source_reference_refused(self):
        self.inputs["cases"][0]["observations"][0]["source_ref"] = "FR02.S1"
        with self.assertRaisesRegex(ValueError, "UNKNOWN_SOURCE_REF"):
            validate_schema(self.inputs, self.oracle, self.review)

    def test_foreign_numeric_basis_refused(self):
        self.oracle["cases"][11]["numerical_expectations"][0]["observation_refs"] = ["FR12.O4"]
        with self.assertRaisesRegex(ValueError, "FOREIGN_NUMERIC_BASIS"):
            validate_schema(self.inputs, self.oracle, self.review)

    def test_cross_case_review_substitution_refused(self):
        self.oracle["cases"][0]["normative_review_excerpt"] = self.oracle["cases"][1]["normative_review_excerpt"]
        with self.assertRaisesRegex(ValueError, "REVIEW_EXCERPT_MISMATCH"):
            validate_schema(self.inputs, self.oracle, self.review)

    def test_gate_promotion_or_fabricated_attribution_refused(self):
        for field, value in [("execution_status", "PASS"), ("financial_reliability_gate", "PASS"),
                             ("reviewer_identity", "fabricated"), ("review_date", "2026-09-16")]:
            oracle = copy.deepcopy(self.oracle)
            oracle[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_schema(self.inputs, oracle, self.review)

    def test_duplicate_case_and_missing_foreign_fixture_refused(self):
        self.inputs["cases"][1]["case_id"] = "FR01"
        with self.assertRaisesRegex(ValueError, "INPUT_CASE_SET"):
            validate_schema(self.inputs, self.oracle, self.review)
        self.inputs = read_json(BUNDLE / "synthetic-inputs-v2.json")
        self.inputs["cases"][11]["adversarial_only_observations"] = []
        with self.assertRaisesRegex(ValueError, "ADVERSARIAL_INPUT_MISSING"):
            validate_schema(self.inputs, self.oracle, self.review)
