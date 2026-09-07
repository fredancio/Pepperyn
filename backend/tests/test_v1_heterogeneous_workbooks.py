from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

import pytest

from connectors import FileConnector
from services.anonymization_service import anonymize_parsed_data
from services.data_quality_gate import validate_excel_before_analysis
from services.v1_analysis_contract import build_financial_understanding, build_openai_request


FIXTURES = Path(__file__).parent / "golden" / "fixtures"
CASES = {
    "pepperyn_v1_heterogeneous_english.xlsx": (
        "FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93",
        "UNDERSTOOD",
    ),
    "pepperyn_v1_heterogeneous_ambiguous_period.xlsx": (
        "8F35CF676B58BFF823CD423BDA70145A9951A55B9F689FF591282F3EAF9C6E51",
        "AMBIGUOUS",
    ),
    "pepperyn_v1_heterogeneous_ambiguous_number.xlsx": (
        "E89851FF9AAF2FADA84F012CE7BDE846F859C7A62B1531F7C4F7F96A055F9E29",
        "AMBIGUOUS",
    ),
    "pepperyn_v1_heterogeneous_conflict.xlsx": (
        "176F8F1A9E6A20B61E61C773AD54000D1D91E769B84C99BD2DA7B8ACB038D7E5",
        "AMBIGUOUS",
    ),
}


def _actual_pipeline(filename: str):
    path = FIXTURES / filename
    raw = path.read_bytes()
    gate = validate_excel_before_analysis(raw, filename)
    parsed = FileConnector(raw, filename).fetch()
    anonymized, _ = anonymize_parsed_data(parsed)
    return raw, gate, parsed, anonymized, build_financial_understanding(anonymized)


@pytest.mark.parametrize("filename", CASES)
def test_registered_heterogeneous_workbooks_are_literal_and_hash_pinned(filename):
    expected_hash, _ = CASES[filename]
    path = FIXTURES / filename
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_hash

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert not any(name.lower().endswith("vbaproject.bin") for name in names)
        assert not any(name.startswith("xl/externalLinks/") for name in names)
        worksheets = b"".join(
            archive.read(name) for name in names if name.startswith("xl/worksheets/sheet")
        )
        assert b"<f" not in worksheets


@pytest.mark.parametrize("filename", CASES)
def test_each_xlsx_exercises_gate_parser_anonymizer_and_governed_understanding(filename):
    _, expected_status = CASES[filename]
    _, gate, parsed, anonymized, understanding = _actual_pipeline(filename)

    assert gate.can_analyze and gate.status in {"ok", "warning"}
    assert gate.document_format == "structural_pl"
    assert parsed["source"] == "file"
    assert parsed["connector_version"] == "1.0"
    assert anonymized is not parsed
    assert understanding.status == expected_status


def test_english_reordered_workbook_is_understood_from_real_parser_output():
    _, _, parsed, anonymized, understanding = _actual_pipeline(
        "pepperyn_v1_heterogeneous_english.xlsx"
    )
    assert parsed["temporal_context"]["columns_by_role"] == {
        "UNKNOWN": ["Account caption"],
        "HISTORICAL_ACTUAL": ["2024"],
        "CURRENT_ACTUAL": ["2025"],
    }
    assert understanding.current_period == "2025"
    facts = {fact.metric: fact.value for fact in understanding.facts}
    assert facts == {
        "REVENUE": 2_100_000,
        "COST_OF_SALES": -1_290_000,
        "GROSS_MARGIN": 810_000,
        "PERSONNEL_COST": -455_000,
        "EBITDA": 62_000,
        "NET_RESULT": 21_000,
        "CASH": 198_000,
        "WORKING_CAPITAL": 402_000,
        "DSO_DAYS": 58,
        "PAYABLES": 235_000,
    }
    request, _, request_understanding = build_openai_request(
        anonymized, model="gpt-test"
    )
    assert request["store"] is False
    assert request_understanding == understanding


@pytest.mark.parametrize(
    "filename,expected_unknown",
    [
        (
            "pepperyn_v1_heterogeneous_ambiguous_period.xlsx",
            "Exactly one CURRENT_ACTUAL column could not be established.",
        ),
        (
            "pepperyn_v1_heterogeneous_ambiguous_number.xlsx",
            "Ambiguous numeric representation for governed metric REVENUE.",
        ),
        (
            "pepperyn_v1_heterogeneous_conflict.xlsx",
            "Conflicting values exist for a governed metric in the current period.",
        ),
    ],
)
def test_unsafe_workbooks_preserve_specific_unknown_and_forbid_provider_request(
    filename, expected_unknown
):
    _, _, _, anonymized, understanding = _actual_pipeline(filename)
    assert expected_unknown in understanding.unknowns
    assert understanding.facts == ()
    with pytest.raises(ValueError, match="provider dispatch forbidden"):
        build_openai_request(anonymized, model="gpt-test")
