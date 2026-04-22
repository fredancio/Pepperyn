"""
Excel export service — Pepperyn v3.
Génère un rapport Excel 4 onglets avec openpyxl.
Aucun appel LLM.

Onglets :
  1. Synthèse         : résumé exécutif, décision, scores globaux
  2. Diagnostic       : revenus, coûts, marges, problèmes, opportunités
  3. Plan d'Action    : actions priorisées avec Priorité / Action / Responsable / Deadline
  4. Score            : tableau récapitulatif des scores /10
"""
import io
from datetime import datetime
from typing import Any

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models.schemas import AnalysisResult

# ─── Brand colors (without #) ─────────────────────────────────────────────────
BRAND_BLUE = "1B73E8"
BRAND_DARK = "0D47A1"
BRAND_BG   = "EFF6FF"
WHITE      = "FFFFFF"
LIGHT_GRAY = "F8FAFC"
GREEN      = "2E7D32"
ORANGE     = "FF6B35"
RED        = "DC2626"
AMBER      = "F59E0B"


# ─── Style helpers ────────────────────────────────────────────────────────────

def _hfill(color: str = BRAND_BLUE) -> PatternFill:
    return PatternFill("solid", fgColor=color)

def _hfont(bold: bool = True, color: str = WHITE, size: int = 11) -> Font:
    return Font(name="Calibri", bold=bold, color=color, size=size)

def _nfont(bold: bool = False, size: int = 10, color: str = "1A1A2E") -> Font:
    return Font(name="Calibri", bold=bold, size=size, color=color)

def _border() -> Border:
    s = Side(style='thin', color='E2E8F0')
    return Border(left=s, right=s, top=s, bottom=s)

def _section_title(ws, row: int, text: str, color: str = BRAND_BLUE, span: int = 5):
    cell_ref = f"A{row}"
    ws.merge_cells(f"A{row}:{get_column_letter(span)}{row}")
    ws[cell_ref] = f"  {text}"
    ws[cell_ref].font = _hfont(size=12, color=WHITE)
    ws[cell_ref].fill = _hfill(color)
    ws[cell_ref].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 28

def _data_row(ws, row: int, label: str, value: str, bold: bool = False, alternate: bool = False):
    ws[f"A{row}"] = label
    ws[f"B{row}"] = value
    ws[f"A{row}"].font = _nfont(bold=bold)
    ws[f"B{row}"].font = _nfont(bold=bold)
    ws[f"A{row}"].border = _border()
    ws[f"B{row}"].border = _border()
    if alternate:
        for col in ["A", "B"]:
            ws[f"{col}{row}"].fill = _hfill(LIGHT_GRAY)


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_excel_report(
    analysis: AnalysisResult,
    original_data: dict[str, Any],
    filename: str = "analyse",
) -> bytes:
    """Generate a 4-tab Excel report. Returns bytes."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    _create_synthese_tab(wb, analysis, filename)
    _create_diagnostic_tab(wb, analysis)
    _create_plan_action_tab(wb, analysis)
    _create_score_tab(wb, analysis)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ─── Onglet 1 : Synthèse ──────────────────────────────────────────────────────

def _create_synthese_tab(wb: openpyxl.Workbook, analysis: AnalysisResult, filename: str):
    ws = wb.create_sheet("Synthèse")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = BRAND_BLUE

    # Title
    ws.merge_cells("A1:F1")
    ws["A1"] = "PEPPERYN — ANALYSE FINANCIÈRE"
    ws["A1"].font = Font(name="Calibri", bold=True, size=16, color=BRAND_DARK)
    ws["A1"].fill = _hfill(BRAND_BG)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 45

    # Metadata
    meta = [
        ("Fichier analysé :", filename),
        ("Date d'analyse :", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Type de document :", analysis.type_document),
        ("Score de confiance :", f"{analysis.score_confiance}%"),
    ]
    for i, (label, value) in enumerate(meta, 3):
        ws[f"A{i}"] = label
        ws[f"B{i}"] = value
        ws[f"A{i}"].font = _nfont(bold=True)
        ws[f"B{i}"].font = _nfont()

    row = 9
    # Résumé Exécutif
    _section_title(ws, row, "RÉSUMÉ EXÉCUTIF", BRAND_DARK)
    row += 1
    resume = analysis.resume_executif or analysis.synthese or "—"
    ws.merge_cells(f"A{row}:F{row + 2}")
    ws[f"A{row}"] = resume
    ws[f"A{row}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws[f"A{row}"].font = _nfont(size=11)
    ws.row_dimensions[row].height = 60
    row += 3

    # Décision
    _section_title(ws, row, "⚡ DÉCISION", BRAND_BLUE)
    row += 1
    decision = analysis.decision or "—"
    ws.merge_cells(f"A{row}:F{row + 1}")
    ws[f"A{row}"] = decision
    ws[f"A{row}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws[f"A{row}"].font = Font(name="Calibri", bold=True, size=11, color=BRAND_DARK)
    ws.row_dimensions[row].height = 50
    row += 2

    # Scores
    row += 1
    _section_title(ws, row, "SCORES /10", BRAND_DARK)
    row += 1
    scores = [
        ("Rentabilité", analysis.score_rentabilite),
        ("Risque", analysis.score_risque),
        ("Structure", analysis.score_structure),
    ]
    for label, val in scores:
        ws[f"A{row}"] = label
        ws[f"B{row}"] = f"{val}/10" if val is not None else "N/A"
        ws[f"A{row}"].font = _nfont(bold=True)
        color = GREEN if (val or 0) >= 8 else (AMBER if (val or 0) >= 5 else RED)
        ws[f"B{row}"].font = Font(name="Calibri", bold=True, color=color, size=12)
        ws[f"A{row}"].border = _border()
        ws[f"B{row}"].border = _border()
        row += 1

    # Column widths
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 40
    for col in ["C", "D", "E", "F"]:
        ws.column_dimensions[col].width = 12


# ─── Onglet 2 : Diagnostic ────────────────────────────────────────────────────

def _create_diagnostic_tab(wb: openpyxl.Workbook, analysis: AnalysisResult):
    ws = wb.create_sheet("Diagnostic")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = BRAND_BLUE
    row = 1

    # Diagnostic Financier (v3 text fields)
    if analysis.diagnostic_revenus or analysis.diagnostic_couts or analysis.diagnostic_marges:
        _section_title(ws, row, "DIAGNOSTIC FINANCIER", BRAND_DARK)
        row += 1
        for label, value in [
            ("Revenus", analysis.diagnostic_revenus),
            ("Coûts", analysis.diagnostic_couts),
            ("Marges", analysis.diagnostic_marges),
        ]:
            if value:
                _data_row(ws, row, label, value, bold=True, alternate=(row % 2 == 0))
                row += 1
        row += 1

    # Legacy: Revenus breakdown
    if analysis.revenus:
        _section_title(ws, row, "REVENUS", GREEN)
        row += 1
        if analysis.revenus.total is not None:
            _data_row(ws, row, "Total revenus", f"{analysis.revenus.total:,.2f} €", bold=True)
            row += 1
        for item in (analysis.revenus.breakdown or []):
            var = f"  ({item.variation:+.1f}%)" if item.variation is not None else ""
            _data_row(ws, row, f"    {item.label}", f"{item.value:,.2f} €{var}", alternate=(row % 2 == 0))
            row += 1
        row += 1

    # Coûts
    if analysis.couts:
        _section_title(ws, row, "COÛTS & CHARGES", ORANGE)
        row += 1
        if analysis.couts.total is not None:
            _data_row(ws, row, "Total charges", f"{analysis.couts.total:,.2f} €", bold=True)
            row += 1
        for item in (analysis.couts.breakdown or []):
            pct = f"  ({item.pourcentage:.1f}% du CA)" if item.pourcentage is not None else ""
            _data_row(ws, row, f"    {item.label}", f"{item.value:,.2f} €{pct}", alternate=(row % 2 == 0))
            row += 1
        row += 1

    # Marges
    if analysis.marges:
        _section_title(ws, row, "MARGES", BRAND_DARK)
        row += 1
        m = analysis.marges
        for label, val, pct_val in [
            ("Marge brute", m.brute, m.brute_pct),
            ("Marge opérationnelle", m.operationnelle, m.operationnelle_pct),
            ("Résultat net", m.nette, m.nette_pct),
        ]:
            if val is not None:
                pct_str = f"  ({pct_val:.1f}%)" if pct_val is not None else ""
                _data_row(ws, row, label, f"{val:,.2f} €{pct_str}", bold=True, alternate=(row % 2 == 0))
                row += 1
        row += 1

    # Problèmes critiques
    problemes = analysis.problemes_critiques or [a.description for a in (analysis.anomalies or [])]
    if problemes:
        _section_title(ws, row, f"PROBLÈMES CRITIQUES ({len(problemes)})", RED)
        row += 1
        for p in problemes:
            _data_row(ws, row, "🔴", p, alternate=(row % 2 == 0))
            row += 1
        row += 1

    # Opportunités
    opps = analysis.opportunites_v3 or [o.description for o in (analysis.opportunites or [])]
    if opps:
        _section_title(ws, row, f"OPPORTUNITÉS ({len(opps)})", GREEN)
        row += 1
        for o in opps:
            _data_row(ws, row, "🟢", o, alternate=(row % 2 == 0))
            row += 1

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 20


# ─── Onglet 3 : Plan d'Action ─────────────────────────────────────────────────

def _create_plan_action_tab(wb: openpyxl.Workbook, analysis: AnalysisResult):
    ws = wb.create_sheet("Plan d'Action")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = BRAND_BLUE

    # Column headers
    headers = ["Priorité", "Action", "Responsable", "Deadline"]
    widths = [18, 60, 22, 18]
    for col, (header, width) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = _hfont(size=11)
        cell.fill = _hfill(BRAND_DARK)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _border()
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 32

    priority_config = {
        "haute": {"bg": "FEE2E2", "label": "🔴 HAUTE", "text": RED},
        "moyenne": {"bg": "FEF3C7", "label": "🟡 MOYENNE", "text": AMBER},
        "basse": {"bg": "DCFCE7", "label": "🟢 BASSE", "text": GREEN},
    }

    # v3 plan_action (text list)
    plan_items = analysis.plan_action or []
    # legacy recommandations
    legacy_recs = analysis.recommandations or []

    row = 2

    if plan_items:
        for action in plan_items:
            # Detect priority from text
            lower = action.lower()
            if "priorité haute" in lower or "priorité: haute" in lower:
                prio_key = "haute"
            elif "priorité moyenne" in lower or "priorité: moyenne" in lower:
                prio_key = "moyenne"
            else:
                prio_key = "basse"
            cfg = priority_config[prio_key]

            ws.cell(row=row, column=1, value=cfg["label"]).fill = PatternFill("solid", fgColor=cfg["bg"])
            ws.cell(row=row, column=1).font = Font(name="Calibri", bold=True, color=cfg["text"], size=10)
            ws.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="top")
            ws.cell(row=row, column=1).border = _border()

            ws.cell(row=row, column=2, value=action).fill = PatternFill("solid", fgColor=cfg["bg"])
            ws.cell(row=row, column=2).font = _nfont(size=10)
            ws.cell(row=row, column=2).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row=row, column=2).border = _border()

            for col in [3, 4]:
                cell = ws.cell(row=row, column=col, value="—")
                cell.fill = PatternFill("solid", fgColor=cfg["bg"])
                cell.font = _nfont(size=10, color="5F6368")
                cell.alignment = Alignment(horizontal="center", vertical="top")
                cell.border = _border()

            ws.row_dimensions[row].height = 40
            row += 1
    elif legacy_recs:
        for rec in legacy_recs:
            priorite = (rec.priorite or "moyenne").lower()
            cfg = priority_config.get(priorite, priority_config["moyenne"])

            values = [cfg["label"], rec.action, "—", rec.delai or "Court terme"]
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.fill = PatternFill("solid", fgColor=cfg["bg"])
                cell.border = _border()
                cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center" if col != 2 else "left")
                if col == 1:
                    cell.font = Font(name="Calibri", bold=True, color=cfg["text"], size=10)
                elif col == 2:
                    cell.font = _nfont(bold=True, size=10)
                else:
                    cell.font = _nfont(size=10)
            ws.row_dimensions[row].height = 45
            row += 1


# ─── Onglet 4 : Score ─────────────────────────────────────────────────────────

def _create_score_tab(wb: openpyxl.Workbook, analysis: AnalysisResult):
    ws = wb.create_sheet("Score")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = BRAND_BLUE

    # Title
    ws.merge_cells("A1:D1")
    ws["A1"] = "SCORES D'ANALYSE — PEPPERYN"
    ws["A1"].font = Font(name="Calibri", bold=True, size=14, color=BRAND_DARK)
    ws["A1"].fill = _hfill(BRAND_BG)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # Scores table header
    headers = ["Indicateur", "Score /10", "Appréciation"]
    widths = [30, 20, 30]
    for col, (header, width) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = _hfont(size=11)
        cell.fill = _hfill(BRAND_DARK)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _border()
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[3].height = 28

    score_data = [
        ("Rentabilité", analysis.score_rentabilite),
        ("Risque", analysis.score_risque),
        ("Structure", analysis.score_structure),
    ]

    def appreciation(val: int | None) -> str:
        if val is None:
            return "—"
        if val >= 8:
            return "✅ Excellent"
        if val >= 6:
            return "🟡 Correct"
        if val >= 4:
            return "🟠 À améliorer"
        return "🔴 Critique"

    for i, (label, val) in enumerate(score_data, 4):
        color = GREEN if (val or 0) >= 8 else (AMBER if (val or 0) >= 5 else RED)
        bg = "DCFCE7" if (val or 0) >= 8 else ("FEF3C7" if (val or 0) >= 5 else "FEE2E2")

        ws.cell(row=i, column=1, value=label).font = _nfont(bold=True, size=11)
        ws.cell(row=i, column=1).border = _border()
        ws.cell(row=i, column=1).fill = PatternFill("solid", fgColor=bg)

        score_cell = ws.cell(row=i, column=2, value=f"{val}/10" if val is not None else "N/A")
        score_cell.font = Font(name="Calibri", bold=True, color=color, size=14)
        score_cell.alignment = Alignment(horizontal="center", vertical="center")
        score_cell.border = _border()
        score_cell.fill = PatternFill("solid", fgColor=bg)

        appr_cell = ws.cell(row=i, column=3, value=appreciation(val))
        appr_cell.font = Font(name="Calibri", bold=True, color=color, size=11)
        appr_cell.alignment = Alignment(horizontal="center", vertical="center")
        appr_cell.border = _border()
        appr_cell.fill = PatternFill("solid", fgColor=bg)

        ws.row_dimensions[i].height = 32

    # Score global moyen
    valid_scores = [v for _, v in score_data if v is not None]
    if valid_scores:
        avg = sum(valid_scores) / len(valid_scores)
        avg_row = len(score_data) + 5
        ws.merge_cells(f"A{avg_row}:C{avg_row}")
        ws[f"A{avg_row}"] = f"Score global moyen : {avg:.1f}/10"
        avg_color = GREEN if avg >= 8 else (AMBER if avg >= 5 else RED)
        ws[f"A{avg_row}"].font = Font(name="Calibri", bold=True, size=13, color=avg_color)
        ws[f"A{avg_row}"].alignment = Alignment(horizontal="center", vertical="center")
        ws[f"A{avg_row}"].fill = _hfill(BRAND_BG)
        ws.row_dimensions[avg_row].height = 36

    # Note de bas de page
    note_row = (len(score_data) + 7) if valid_scores else (len(score_data) + 4)
    ws.merge_cells(f"A{note_row}:C{note_row}")
    ws[f"A{note_row}"] = "Scores calculés par Pepperyn IA — Finflate SRL © 2026"
    ws[f"A{note_row}"].font = Font(name="Calibri", size=9, color="5F6368")
    ws[f"A{note_row}"].alignment = Alignment(horizontal="center")
