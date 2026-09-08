from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook
from pypdf import PdfReader
from pptx import Presentation
from pptx.util import Inches

from sandbox.governed_exports import generate_governed_excel, generate_governed_pdf, generate_governed_pptx
from services.v1_analysis_contract import GovernedAnalysisEnvelope


ANALYSIS_ID = "75132a71-1111-4222-8333-123456789abc"


def _envelope(*, action: str = "Valider le tableau des flux.",
              diagnosis: str = "La rentabilite operationnelle est negative.") -> GovernedAnalysisEnvelope:
    fact_id = "FABCDEF123456"
    source_hash = "A" * 64
    return GovernedAnalysisEnvelope.model_validate({
        "source_facts": {
            "status": "UNDERSTOOD", "current_period": "2025",
            "source_representation_sha256": source_hash,
            "facts": [{"fact_id": fact_id, "metric": "EBITDA", "value": -145000,
                       "unit": "EUR", "period": "2025", "source_sheet_ref": "SABCDEF123456",
                       "source_field": "R123456ABCDEF"}], "unknowns": [],
        },
        "governed_analysis": {
            "source_representation_sha256": source_hash, "invocation_nonce": "B" * 32,
            "executive_diagnosis": diagnosis,
            "diagnosis_fact_ids": [fact_id],
            "observations": [{"fact_id": fact_id, "metric": "EBITDA", "observed_value": -145000,
                              "severity": "HIGH"}],
            "dimension_assessments": [{"scope": "PROFITABILITY", "score": 2,
                "rationale": "L'EBITDA degrade la rentabilite.", "fact_ids": [fact_id],
                "confidence": 90, "validation_required": ["Confirmer les retraitements."]}],
            "inferences": [{"statement": "Une tension de tresorerie est possible.",
                            "fact_ids": [fact_id], "confidence": 60,
                            "validation_required": ["Valider le tableau des flux."]}],
            "unknowns": [{"question": "Quel est le flux de tresorerie ?", "materiality": "HIGH"}],
            "contradictions": [],
            "recommendations": [{"priority": "P1", "action": action,
                "rationale": "La traduction en tresorerie n'est pas etablie.", "fact_ids": [fact_id],
                "prerequisite_validation": ["Obtenir le tableau des flux."]}],
        },
    })


def test_excel_is_structured_auditable_and_contains_no_formulas():
    workbook = load_workbook(BytesIO(generate_governed_excel(_envelope(), ANALYSIS_ID)), data_only=False)
    assert workbook.sheetnames == ["Synthese", "Faits sources", "Inferences", "Recommandations", "UNKNOWN"]
    values = [cell.value for sheet in workbook for row in sheet.iter_rows() for cell in row if cell.value is not None]
    text = "\n".join(map(str, values))
    for required in ("Diagnostic (inference)", "Faits sources",
                     "Observation source-matched - severite inferentielle HIGH", "EBITDA = -145000",
                     "Validations requises", "Prerequis", ANALYSIS_ID,
                     "Fournisseur simulé local", "Aucun réseau externe n'a été utilisé",
                     "Les recommandations IA ne constituent pas des decisions confirmees."):
        assert required in text or required in workbook.sheetnames
    assert not [cell for sheet in workbook for row in sheet.iter_rows() for cell in row if cell.data_type == "f"]


def test_provider_text_cannot_become_an_excel_formula():
    workbook = load_workbook(BytesIO(generate_governed_excel(
        _envelope(action='=HYPERLINK("https://invalid.example","click")'), ANALYSIS_ID
    )), data_only=False)
    action = workbook["Recommandations"]["B2"]
    assert action.data_type == "s"
    assert action.value.startswith("'=HYPERLINK")


def test_pdf_contains_governed_sections_and_no_confirmed_decision():
    reader = PdfReader(BytesIO(generate_governed_pdf(_envelope(), ANALYSIS_ID)))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for required in ("Diagnostic - inference", "Faits sources", "Observations gouvernees",
                     "Observation source-matched: EBITDA = -145000", "Severite inferentielle: HIGH",
                     "Inferences et validations",
                     "UNKNOWN et contradictions", "Recommandations proposees", ANALYSIS_ID,
                     "Fournisseur simulé local", "Aucun réseau externe n'a été utilisé",
                     "ne constituent pas des decisions confirmees"):
        assert required in text


def test_pptx_is_governed_complete_and_contains_no_confirmed_decision():
    deck = Presentation(BytesIO(generate_governed_pptx(_envelope(), ANALYSIS_ID)))
    text = "\n".join(
        shape.text for slide in deck.slides for shape in slide.shapes if hasattr(shape, "text_frame")
    )
    for required in ("Analyse financiere", "Situation executive", "INFERENCE",
                     "Constats financiers", "OBSERVATION SOURCE", "EBITDA = -145000",
                     "Severite inferentielle HIGH", "Evaluation et hypotheses",
                     "UNKNOWN HIGH", "Recommandations proposées", "ACTION PROPOSEE", ANALYSIS_ID,
                     "Fournisseur simulé local", "Aucun réseau externe n'a été utilisé",
                     "Obtenir le tableau des flux", "Aucune decision n'est presentee comme confirmee"):
        assert required in text
    assert "Decisions requises" not in text


def test_pptx_preserves_long_governed_content_on_continuation_slides():
    diagnosis = "Diagnostic complet " + "contenu professionnel " * 175
    deck = Presentation(BytesIO(generate_governed_pptx(_envelope(diagnosis=diagnosis), ANALYSIS_ID)))
    body_text = "".join(
        shape.text for slide in deck.slides for shape in slide.shapes
        if hasattr(shape, "text_frame") and shape.left == Inches(0.9)
    )
    diagnosis_chunks = [
        shape.text for slide in deck.slides for shape in slide.shapes
        if hasattr(shape, "text_frame") and shape.left == Inches(0.9)
        and shape.text.startswith(("INFERENCE | ", "INFERENCE (suite) | "))
    ]
    reconstructed = "".join(
        text.removeprefix("INFERENCE | ").removeprefix("INFERENCE (suite) | ")
        for text in diagnosis_chunks
    )
    assert reconstructed.startswith(diagnosis)
    assert all(text.startswith(("INFERENCE | ", "INFERENCE (suite) | ")) for text in diagnosis_chunks)
    all_body_chunks = [
        shape.text for slide in deck.slides for shape in slide.shapes
        if hasattr(shape, "text_frame") and shape.left == Inches(0.9)
    ]
    assert all(" | " in text for text in all_body_chunks)
    assert len(deck.slides) > 6
