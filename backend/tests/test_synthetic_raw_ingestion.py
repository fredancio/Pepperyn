from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import zipfile

import pytest

import sandbox.synthetic_raw_ingestion as raw_module
from sandbox.synthetic_product import SandboxRefused


def _sheet(payload, name):
    return next(sheet for sheet in payload["sheets"] if sheet["sheet_name"] == name)


def _row(payload, sheet_name, label):
    sheet = _sheet(payload, sheet_name)
    first_column = sheet["columns"][0]
    return next(row for row in sheet["full_table"] if row[first_column] == label)


def test_registered_raw_workbook_is_exact_synthetic_literal_fixture():
    fixture = raw_module.load_registered_raw_workbook()

    assert fixture.fixture_id == "OPTILUX_M1C_RAW_V1"
    assert fixture.filename == "optilux_m1c_raw_workbook.xlsx"
    assert fixture.sha256 == raw_module.OPTILUX_RAW_WORKBOOK_SHA256
    assert hashlib.sha256(fixture.raw_bytes).hexdigest().upper() == fixture.sha256
    assert tuple(inspect.signature(raw_module.load_registered_raw_workbook).parameters) == ()
    assert tuple(inspect.signature(raw_module.build_registered_raw_financial_input).parameters) == ()
    with pytest.raises(TypeError):
        raw_module.load_registered_raw_workbook("C:/client.xlsx")

    with zipfile.ZipFile(Path(raw_module._RAW_WORKBOOK)) as archive:
        names = archive.namelist()
        assert not any(name.lower().endswith("vbaproject.bin") for name in names)
        assert "xl/externalLinks/externalLink1.xml" not in names
        worksheets = b"".join(
            archive.read(name) for name in names if name.startswith("xl/worksheets/sheet")
        )
        assert b"<f" not in worksheets


def test_raw_bytes_exercise_real_gate_parser_normalizer_and_anonymizer(monkeypatch):
    calls = {"gate": 0, "fetch": 0, "anonymize": 0}
    real_gate = raw_module.validate_excel_before_analysis
    real_fetch = raw_module.FileConnector.fetch
    real_anonymize = raw_module.anonymize_parsed_data

    def gate(*args, **kwargs):
        calls["gate"] += 1
        return real_gate(*args, **kwargs)

    def fetch(self):
        calls["fetch"] += 1
        return real_fetch(self)

    def anonymize(*args, **kwargs):
        calls["anonymize"] += 1
        return real_anonymize(*args, **kwargs)

    monkeypatch.setattr(raw_module, "validate_excel_before_analysis", gate)
    monkeypatch.setattr(raw_module.FileConnector, "fetch", fetch)
    monkeypatch.setattr(raw_module, "anonymize_parsed_data", anonymize)
    monkeypatch.setattr(
        "services.file_parser._convert_with_libreoffice",
        lambda *_: pytest.fail("literal fixture must not invoke LibreOffice fallback"),
    )

    evidence = raw_module.build_registered_raw_financial_input()

    assert calls == {"gate": 1, "fetch": 1, "anonymize": 1}
    assert evidence.quality_gate["status"] == "warning"
    assert evidence.quality_gate["document_format"] == "structural_pl"
    assert evidence.quality_gate["score_data"] == 80
    assert evidence.parsed_payload["source"] == "file"
    assert evidence.parsed_payload["connector_version"] == "1.0"
    assert evidence.parsed_payload["all_sheets_manifest"]["total_sheets_in_workbook"] == 4
    assert evidence.provider_boundary_refusal == "REAL_DATA_ADMISSION_CLOSED"


def test_actual_first_provider_stage_reaches_closed_authority_not_transport(monkeypatch):
    monkeypatch.setattr(
        "services.llm_egress._dispatch_final_request",
        lambda *_: pytest.fail("closed admission must refuse before transport"),
    )

    evidence = raw_module.build_registered_raw_financial_input()

    assert evidence.provider_boundary_refusal == "REAL_DATA_ADMISSION_CLOSED"


def test_parsed_representation_matches_independent_financial_ground_truth():
    evidence = raw_module.build_registered_raw_financial_input()
    parsed = evidence.parsed_payload

    assert _row(parsed, "Compte de résultat", "Chiffre d'affaires")["2025"] == 2400000
    assert _row(parsed, "Compte de résultat", "EBITDA")["2025"] == -145000
    assert _row(parsed, "Compte de résultat", "Résultat net")["2025"] == -171000
    assert _row(parsed, "Bilan", "Total actif")["2025"] == 2206000
    assert _row(parsed, "Bilan", "Total passif")["2025"] == 2206000
    assert _row(parsed, "Bilan", "Capitaux propres")["2025"] == 791000
    assert _row(parsed, "Trésorerie et BFR", "BFR total")["2025"] == 579000
    assert _row(parsed, "Trésorerie et BFR", "DSO jours")["2025"] == 74
    assert parsed["temporal_context"]["detected_current_year"] == 2025
    assert parsed["bfr_summary"]["bfr_eur"]["value"] == 579000
    assert parsed["bfr_summary"]["bfr_eur"]["period"] == "2025"
    assert parsed["bilan_summary"]["capitaux_propres"]["value"] == 791000
    assert parsed["bilan_summary"]["capitaux_propres"]["period"] == "2025"


def test_anonymized_representation_preserves_numbers_without_correspondence_table():
    evidence = raw_module.build_registered_raw_financial_input()
    serialized = json.dumps(evidence.anonymized_payload, ensure_ascii=False, sort_keys=True)

    assert "OPTILUX_SYNTHETIC_ENTITY" not in serialized
    assert "ENTREPRISE_001" in serialized
    assert evidence.anonymization_summary == {"ENTREPRISE": 1}
    assert "real_to_alias" not in serialized
    assert "alias_to_real" not in serialized
    assert _row(evidence.anonymized_payload, "Compte de résultat", "EBITDA")["2025"] == -145000
    assert _row(evidence.anonymized_payload, "Trésorerie et BFR", "BFR total")["2025"] == 579000


def test_modified_workbook_fails_before_gate_or_parser(monkeypatch, tmp_path):
    fixture = raw_module.load_registered_raw_workbook()
    modified = bytearray(fixture.raw_bytes)
    modified[-20] ^= 1
    foreign = tmp_path / fixture.filename
    foreign.write_bytes(modified)
    reached = []
    monkeypatch.setattr(raw_module, "_RAW_WORKBOOK", foreign)
    monkeypatch.setattr(
        raw_module,
        "validate_excel_before_analysis",
        lambda *_: reached.append("gate"),
    )

    with pytest.raises(SandboxRefused, match="REGISTERED_RAW_WORKBOOK_HASH_MISMATCH"):
        raw_module.build_registered_raw_financial_input()
    assert reached == []


def test_actual_cell_mutation_changes_real_parsed_representation(tmp_path):
    import openpyxl

    fixture = raw_module.load_registered_raw_workbook()
    original = raw_module.FileConnector(fixture.raw_bytes, fixture.filename).fetch()
    workbook = openpyxl.load_workbook(raw_module._RAW_WORKBOOK)
    workbook["Compte de résultat"]["D7"] = -146000
    changed_path = tmp_path / fixture.filename
    workbook.save(changed_path)
    changed = raw_module.FileConnector(changed_path.read_bytes(), fixture.filename).fetch()

    assert _row(original, "Compte de résultat", "EBITDA")["2025"] == -145000
    assert _row(changed, "Compte de résultat", "EBITDA")["2025"] == -146000
    assert original != changed
