from pathlib import Path
from io import BytesIO

import openpyxl

from services.data_quality_gate import validate_excel_before_analysis


FIXTURE = Path(__file__).parent / "golden" / "fixtures" / "optilux_m1c_raw_workbook.xlsx"


def test_explicit_financial_statements_override_partial_erp_detection():
    gate = validate_excel_before_analysis(FIXTURE.read_bytes(), FIXTURE.name)

    assert gate.can_analyze is True
    assert gate.status in {"ok", "warning"}
    assert gate.document_format == "structural_pl"
    assert gate.sheets_detected == [
        "Compte de résultat",
        "Bilan",
        "Trésorerie et BFR",
        "Métadonnées synthétiques",
    ]
    assert not any("Champ obligatoire absent" in anomaly for anomaly in gate.anomalies)


def test_complete_erp_mapping_is_not_overridden_by_budget_sheet():
    workbook = openpyxl.Workbook()
    sales = workbook.active
    sales.title = "Ventes"
    sales.append(["Date", "Montant HT", "Client"])
    sales.append(["2025-01-15", 1000, "CLIENT_SYNTHETIQUE"])
    budget = workbook.create_sheet("Budget")
    budget.append(["Période", "Poste", "Montant"])
    budget.append(["2025-01", "CA", 1200])
    buffer = BytesIO()
    workbook.save(buffer)

    gate = validate_excel_before_analysis(buffer.getvalue(), "erp_synthetique.xlsx")

    assert gate.can_analyze is True
    assert gate.document_format == "erp_transactional"
    assert any("sales" in item for item in gate.mapping_summary)
