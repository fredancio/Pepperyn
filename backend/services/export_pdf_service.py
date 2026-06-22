"""
export_pdf_service.py — Pepperyn V5 Premium Decision Engine
Génère un rapport PDF professionnel à partir d'un AnalysisResult v5.
Utilise reportlab.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import re as _re

from models.executive_decision_model import ExecutiveDecisionModel
from services.executive_decision_model import build_executive_decision_model


# ─── Text sanitisation ───────────────────────────────────────────────────────
def _rl(text: str) -> str:
    if not text:
        return ""
    text = _re.sub(r"~~.*?~~", "", text)
    text = text.strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = _re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    return text


# ─── Palette Pepperyn V5 ─────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#0D47A1")
BLUE_MAIN   = colors.HexColor("#1B73E8")
BLUE_LIGHT  = colors.HexColor("#EFF6FF")
BLUE_DEEP   = colors.HexColor("#0A2540")   # hero blocks
RED         = colors.HexColor("#DC2626")
RED_LIGHT   = colors.HexColor("#FEF2F2")
RED_DARK    = colors.HexColor("#7F1D1D")
AMBER       = colors.HexColor("#D97706")
AMBER_LIGHT = colors.HexColor("#FFFBEB")
ORANGE      = colors.HexColor("#EA580C")
ORANGE_LIGHT= colors.HexColor("#FFF7ED")
GREEN       = colors.HexColor("#15803D")
GREEN_LIGHT = colors.HexColor("#F0FDF4")
GREEN_DARK  = colors.HexColor("#14532D")
SLATE       = colors.HexColor("#1E293B")   # impact financier bg
SLATE_LIGHT = colors.HexColor("#F1F5F9")
GRAY_TEXT   = colors.HexColor("#5F6368")
GRAY_BG     = colors.HexColor("#F8FAFC")
GRAY_BORDER = colors.HexColor("#CBD5E1")
DARK        = colors.HexColor("#1A1A2E")
WHITE       = colors.white

# Chaînes hex jumelles (pour <font color="..."> inline — éviter Color.hexval(), fragile)
RED_HEX        = "#DC2626"
AMBER_HEX      = "#D97706"
GREEN_HEX      = "#15803D"
BLUE_DARK_HEX  = "#0D47A1"
BLUE_MAIN_HEX  = "#1B73E8"
GRAY_HEX       = "#5F6368"

PAGE_W, PAGE_H = A4
MARGIN    = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


# ─── Styles ──────────────────────────────────────────────────────────────────
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=DARK, leading=14, spaceAfter=2,
        ),
        "body_white": ParagraphStyle(
            "body_white", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=WHITE, leading=14,
        ),
        "body_gray": ParagraphStyle(
            "body_gray", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5,
            textColor=GRAY_TEXT, leading=13,
        ),
        "section_title": ParagraphStyle(
            "section_title", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=10,
            textColor=WHITE, leading=14,
        ),
        "subsection": ParagraphStyle(
            "subsection", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9,
            textColor=DARK, leading=13, spaceBefore=4,
        ),
        "subsection_white": ParagraphStyle(
            "subsection_white", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9,
            textColor=WHITE, leading=13,
        ),
        "bullet_blue": ParagraphStyle(
            "bullet_blue", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5,
            textColor=DARK, leading=13,
            leftIndent=10,
        ),
        "decision": ParagraphStyle(
            "decision", parent=base["Normal"],
            fontName="Helvetica-BoldOblique", fontSize=9.5,
            textColor=BLUE_DARK, leading=15,
        ),
        "hero_main": ParagraphStyle(
            "hero_main", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=11,
            textColor=WHITE, leading=17,
        ),
        "hero_decision": ParagraphStyle(
            "hero_decision", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9.5,
            textColor=colors.HexColor("#FCD34D"), leading=15,  # amber-300
        ),
        "score_label": ParagraphStyle(
            "score_label", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.5,
            textColor=GRAY_TEXT, leading=11, alignment=TA_CENTER,
        ),
        "score_interp": ParagraphStyle(
            "score_interp", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=7,
            textColor=GRAY_TEXT, leading=10, alignment=TA_CENTER,
        ),
        "score_value": ParagraphStyle(
            "score_value", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=16,
            leading=20, alignment=TA_CENTER,
        ),
        "impact_item": ParagraphStyle(
            "impact_item", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=WHITE, leading=14,
        ),
        "impact_label": ParagraphStyle(
            "impact_label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.HexColor("#94A3B8"), leading=12,
        ),
        "sim_action": ParagraphStyle(
            "sim_action", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8.5,
            textColor=WHITE, leading=13,
        ),
        "sim_body": ParagraphStyle(
            "sim_body", parent=base["Normal"],
            fontName="Helvetica", fontSize=8,
            textColor=DARK, leading=12,
        ),
        "proj_head": ParagraphStyle(
            "proj_head", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8.5,
            textColor=BLUE_DARK, leading=13,
        ),
        "proj_body": ParagraphStyle(
            "proj_body", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5,
            textColor=DARK, leading=13,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.5,
            textColor=GRAY_TEXT, alignment=TA_CENTER,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"],
            fontName="Helvetica", fontSize=8,
            textColor=GRAY_TEXT, leading=12, spaceAfter=1,
        ),
        "separator": ParagraphStyle(
            "separator", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8,
            textColor=GRAY_TEXT, leading=12, alignment=TA_CENTER,
        ),
        "risque_inaction": ParagraphStyle(
            "risque_inaction", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9.5,
            textColor=RED_DARK, leading=15,
        ),
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _section_header(title: str, bg_color, styles: dict) -> Table:
    cell = Paragraph(title, styles["section_title"])
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def _bullet_rows(items: list[str], icon: str, text_color, bg_color, styles: dict) -> list:
    rows = []
    for item in items:
        clean = item.lstrip("🔴🟢⚠️🔄 ")
        cell = Paragraph(f"{icon}  {_rl(clean)}", styles["body"])
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("BOX",           (0, 0), (-1, -1), 0.5, text_color),
        ]))
        rows.append(t)
        rows.append(Spacer(1, 2))
    return rows


def _score_table(scores: dict[str, int | None], interpretations: dict, styles: dict) -> Table:
    """4 score circles — number + label + colored interpretation badge."""
    score_data = [
        ("Rentabilité", scores.get("rentabilite"), interpretations.get("rentabilite", "")),
        ("Risque",      scores.get("risque"),      interpretations.get("risque", "")),
        ("Structure",   scores.get("structure"),   interpretations.get("structure", "")),
        ("Liquidité",   scores.get("liquidite"),   interpretations.get("liquidite", "")),
    ]
    cells = []
    for label, val, interp in score_data:
        if val is None:
            cells.append(Spacer(1, 1))
            continue
        color_hex = "#15803D" if val >= 8 else "#D97706" if val >= 5 else "#DC2626"
        bg_hex    = "#F0FDF4" if val >= 8 else "#FFFBEB" if val >= 5 else "#FEF2F2"
        score_p = Paragraph(
            f'<font color="{color_hex}"><b>{val}/10</b></font>',
            ParagraphStyle("sv2", fontName="Helvetica-Bold", fontSize=15,
                           leading=19, alignment=TA_CENTER)
        )
        label_p = Paragraph(label, styles["score_label"])
        rows_inner = [[score_p], [label_p]]
        if interp:
            # Interpretation as colored pill
            interp_p = Paragraph(
                f'<font color="{color_hex}"><b>{_rl(interp.upper())}</b></font>',
                ParagraphStyle("si2", fontName="Helvetica-Bold", fontSize=8,
                               leading=11, alignment=TA_CENTER)
            )
            interp_cell = Table([[interp_p]], colWidths=[34 * mm])
            interp_cell.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg_hex)),
                ("BOX",           (0, 0), (-1, -1), 0.8, colors.HexColor(color_hex)),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ]))
            rows_inner.append([interp_cell])
        inner = Table(rows_inner, colWidths=[38 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 1.5, colors.HexColor(color_hex)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ]))
        cells.append(inner)

    valid = [c for c in cells if not isinstance(c, Spacer)]
    if not valid:
        return Spacer(1, 1)

    col_w = CONTENT_W / len(cells)
    t = Table([cells], colWidths=[col_w] * len(cells))
    t.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ─── Header / Footer canvas ──────────────────────────────────────────────────
def _draw_header(canvas, doc, result: dict):
    canvas.saveState()
    canvas.setFillColor(BLUE_DARK)
    canvas.rect(0, PAGE_H - 52 * mm, PAGE_W, 52 * mm, fill=True, stroke=False)
    canvas.setFillColor(BLUE_MAIN)
    canvas.rect(0, PAGE_H - 52 * mm, PAGE_W * 0.6, 52 * mm, fill=True, stroke=False)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(MARGIN, PAGE_H - 22 * mm, "Rapport exécutif")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    doc_type = result.get("type_document", "Document financier")
    conf = result.get("score_confiance", 0)
    date_str = datetime.now().strftime("%d/%m/%Y")
    canvas.drawString(MARGIN, PAGE_H - 30 * mm, f"{doc_type}  ·  Niveau de confiance : {conf}%  ·  {date_str}")

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 22 * mm, "Pepperyn")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 29 * mm, "Copilote financier · Niveau expert")

    canvas.setFillColor(GRAY_TEXT)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 10 * mm,
        f"Généré par Pepperyn — {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  Ce document est confidentiel"
    )
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# ─── V5 Block Builders ────────────────────────────────────────────────────────

def _build_financial_headline(synthese: str | None, styles: dict) -> list:
    """Standalone financial headline — very first block, maximum visibility."""
    if not synthese:
        return []
    rows = [
        [Paragraph(
            '<font color="#94A3B8"><b>💸  PERTE STRUCTURELLE ESTIMÉE</b></font>',
            ParagraphStyle("fh_label", fontName="Helvetica-Bold", fontSize=8.5,
                           textColor=colors.HexColor("#94A3B8"), leading=12)
        )],
        [Paragraph(
            f'<font color="#FCD34D"><b>→  {_rl(synthese)}</b></font>',
            ParagraphStyle("fh_val", fontName="Helvetica-Bold", fontSize=15,
                           textColor=colors.HexColor("#FCD34D"), leading=20)
        )],
        [Paragraph(
            "⚠️  Estimation basée sur les données disponibles uniquement",
            ParagraphStyle("fh_note", fontName="Helvetica-Oblique", fontSize=7.5,
                           textColor=colors.HexColor("#64748B"), leading=11)
        )],
    ]
    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 1), SLATE),
        ("BACKGROUND",    (0, 2), (-1, 2), colors.HexColor("#162032")),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 2, AMBER),
        ("LINEBELOW",     (0, 1), (-1, 1), 0.3, colors.HexColor("#334155")),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))
    return [t, Spacer(1, 8)]


def _build_diagnostic_immediat(diag: str, tension: str | None, styles: dict,
                                show_decision: bool = True) -> list:
    """
    Hero block — dark slate with diagnostic + (optionnellement) décision + tension.
    `show_decision=False` : utilisé dans l'Executive Summary depuis l'Étape C, car la
    décision prioritaire est désormais présentée seule en page 1 (Executive Decision).
    """
    if not diag:
        return []
    story = []
    lines = diag.splitlines()
    main_line = ""
    decision_line = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("👉") or "DÉCISION PRIORITAIRE" in stripped.upper():
            decision_line = stripped.lstrip("👉").replace("DÉCISION PRIORITAIRE :", "").strip()
        elif stripped.startswith("⚡") or "TENSION" in stripped.upper():
            pass  # handled separately via tension param
        elif "DIAGNOSTIC CRITIQUE" in stripped.upper():
            pass  # label row — handled below
        elif stripped:
            main_line = stripped.lstrip("⚠️").strip()

    rows = []
    # Label row — "DIAGNOSTIC CRITIQUE"
    rows.append([Paragraph(
        '<font color="#FCD34D"><b>⚠️  DIAGNOSTIC CRITIQUE</b></font>',
        ParagraphStyle("diag_label", fontName="Helvetica-Bold", fontSize=8,
                       textColor=colors.HexColor("#FCD34D"), leading=11)
    )])
    if main_line:
        rows.append([Paragraph(_rl(main_line), styles["hero_main"])])
    if decision_line and show_decision:
        rows.append([Paragraph(f"👉  DÉCISION PRIORITAIRE : {_rl(decision_line)}", styles["hero_decision"])])

    if not rows:
        rows.append([Paragraph(_rl(diag), styles["hero_main"])])

    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, -1), SLATE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]
    if len(rows) > 1:
        style_cmds.append(("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#374151")))

    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle(style_cmds))

    # Tension line: amber box directly below the hero
    elements = [t]
    if tension:
        tension_cell = Paragraph(
            f"⚡  {_rl(tension)}",
            ParagraphStyle("tension_inline",
                fontName="Helvetica-Bold", fontSize=9,
                textColor=DARK, leading=14)
        )
        t_tension = Table([[tension_cell]], colWidths=[CONTENT_W])
        t_tension.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),  # amber-100
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("BOX",           (0, 0), (-1, -1), 1, AMBER),
        ]))
        elements.append(t_tension)

    story.append(KeepTogether(elements))
    story.append(Spacer(1, 8))
    return story


def _build_resume_executif(resume: str, styles: dict) -> list:
    """3 lines max — concise Apple-style executive summary."""
    if not resume:
        return []
    story = []
    story.append(_section_header("⚡  RÉSUMÉ EXÉCUTIF", BLUE_MAIN, styles))
    story.append(Spacer(1, 3))
    lines = [l.strip() for l in resume.splitlines() if l.strip()]
    for line in lines[:5]:
        story.append(Paragraph(_rl(line), styles["body"]))
    story.append(Spacer(1, 8))
    return story


def _build_impact_financier(synthese: str | None, items: list[str], styles: dict,
                            en_resume: str | None = None) -> list:
    """Impact financier: choc line first, then details, then En résumé."""
    if not synthese and not items:
        return []
    story = []
    story.append(_section_header("💸  IMPACT FINANCIER ESTIMÉ", SLATE, styles))
    story.append(Spacer(1, 2))

    rows = []

    # Row 0 — PERTE ESTIMÉE choc (dark background, bold prominent)
    if synthese:
        synth_p = Paragraph(
            f'<font color="#94A3B8">💸  PERTE STRUCTURELLE ESTIMÉE</font>  '
            f'<font color="#FCD34D"><b>→  {_rl(synthese)}</b></font>',
            ParagraphStyle("synth", fontName="Helvetica-Bold", fontSize=11,
                           textColor=colors.HexColor("#FCD34D"), leading=17)
        )
        rows.append([synth_p])

    # Row 1 — disclaimer
    rows.append([Paragraph(
        "⚠️  Estimations basées sur les données disponibles uniquement.",
        styles["small"]
    )])

    # Rows — details
    for item in items[:4]:
        rows.append([Paragraph(f"→  {_rl(item)}", styles["body"])])

    t = Table(rows, colWidths=[CONTENT_W])
    style_cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, SLATE),
    ]
    if synthese:
        style_cmds.append(("BACKGROUND", (0, 0), (-1, 0), SLATE))
        style_cmds.append(("BACKGROUND", (0, 1), (-1, -1), SLATE_LIGHT))
        style_cmds.append(("LINEBELOW",  (0, 0), (-1, 0), 0.5, GRAY_BORDER))
    else:
        style_cmds.append(("BACKGROUND", (0, 0), (-1, -1), SLATE_LIGHT))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    if en_resume:
        story.append(Spacer(1, 3))
        story.extend(_en_resume_box(en_resume, styles))
    story.append(Spacer(1, 8))
    return story


def _build_avant_apres(actuel: list[str], apres: list[str], gain: str | None, styles: dict,
                       gain_transformations: list[str] | None = None) -> list:
    """Two-column before/after comparison table."""
    if not actuel and not apres:
        return []
    story = []
    story.append(_section_header("📊  AVANT / APRÈS", BLUE_DARK, styles))
    story.append(Spacer(1, 4))

    col_w = CONTENT_W / 2 - 2

    # Header row
    header_row = [
        Paragraph("📉  AUJOURD'HUI", styles["subsection"]),
        Paragraph("📈  APRÈS ACTION", styles["subsection"]),
    ]
    # Content rows
    max_len = max(len(actuel), len(apres), 1)
    content_rows = []
    for i in range(max_len):
        left = Paragraph(f"• {_rl(actuel[i])}" if i < len(actuel) else "", styles["body"])
        right = Paragraph(f"• {_rl(apres[i])}" if i < len(apres) else "", styles["body"])
        content_rows.append([left, right])

    all_rows = [header_row] + content_rows
    col_widths = [col_w, col_w]

    t = Table(all_rows, colWidths=col_widths)
    style_cmds = [
        ("BACKGROUND",    (0, 0), (0, 0), RED_LIGHT),
        ("BACKGROUND",    (1, 0), (1, 0), GREEN_LIGHT),
        ("BACKGROUND",    (0, 1), (0, -1), colors.HexColor("#FFF5F5")),
        ("BACKGROUND",    (1, 1), (1, -1), colors.HexColor("#F0FDF4")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]
    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    # GAIN TOTAL POTENTIEL — proéminent, full width green
    if gain:
        gain_rows = [
            [Paragraph(
                '<font color="#15803D"><b>💥  GAIN TOTAL POTENTIEL</b></font>',
                ParagraphStyle("gain_label", fontName="Helvetica-Bold", fontSize=8,
                               textColor=GREEN, leading=11)
            )],
            [Paragraph(
                f'<font color="#14532D"><b>→  {_rl(gain)}</b></font>',
                ParagraphStyle("gain_val", fontName="Helvetica-Bold", fontSize=12,
                               textColor=GREEN_DARK, leading=17)
            )],
        ]
        # V9 — transformation lines (Rentabilité / Investissement / Modèle)
        for tf in (gain_transformations or []):
            gain_rows.append([Paragraph(
                f'<font color="#15803D">→  {_rl(tf)}</font>',
                ParagraphStyle("gain_tf", fontName="Helvetica", fontSize=8.5,
                               textColor=GREEN, leading=13)
            )])

        tg = Table(gain_rows, colWidths=[CONTENT_W])
        style_cmds_gain = [
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("BOX",           (0, 0), (-1, -1), 1.5, GREEN),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.3, GREEN),
            ("BACKGROUND",    (0, 0), (-1, 1),  GREEN_LIGHT),
        ]
        if gain_transformations:
            style_cmds_gain.append(("BACKGROUND", (0, 2), (-1, -1), colors.HexColor("#F0FFF4")))
            style_cmds_gain.append(("LINEABOVE",  (0, 2), (-1, 2),  0.3, colors.HexColor("#86EFAC")))
        tg.setStyle(TableStyle(style_cmds_gain))
        story.append(tg)

    story.append(Spacer(1, 8))
    return story


def _build_simulateur(sim_lines: list[str], styles: dict) -> list:
    """If/then decision simulator as mini action cards."""
    if not sim_lines:
        return []
    story = []
    story.append(_section_header("🎯  SIMULATEUR DE DÉCISION", BLUE_MAIN, styles))
    story.append(Spacer(1, 4))

    # Parse lines into blocks
    blocks: list[dict] = []
    current: dict = {}
    for line in sim_lines:
        stripped = line.strip()
        if stripped.startswith("→ Action") or stripped.startswith("→ action"):
            if current:
                blocks.append(current)
            current = {"action": stripped.replace("→ Action :", "").replace("→ Action:", "")
                       .replace("→ action :", "").replace("→ action:", "").strip()}
        elif stripped.lower().startswith("impact") and ":" in stripped:
            current["impact"] = stripped.split(":", 1)[-1].strip()
        elif stripped.lower().startswith("résultat") or stripped.lower().startswith("resultat"):
            if ":" in stripped:
                current["resultat"] = stripped.split(":", 1)[-1].strip()
    if current:
        blocks.append(current)

    # Fallback: no structured blocks found, show raw lines
    if not blocks:
        for line in sim_lines[:6]:
            if line.strip():
                story.append(Paragraph(f"→ {_rl(line.strip())}", styles["body"]))
        story.append(Spacer(1, 8))
        return story

    half = CONTENT_W / 2 - 3
    # Render 2 cards per row
    for i in range(0, len(blocks), 2):
        row_blocks = blocks[i:i+2]
        row_cells = []
        for b in row_blocks:
            inner_rows = [
                [Paragraph(f"→ {_rl(b.get('action', ''))}", styles["sim_action"])],
            ]
            if b.get("impact"):
                inner_rows.append([Paragraph(
                    f'<b>Impact :</b>  {_rl(b["impact"])}',
                    styles["sim_body"]
                )])
            if b.get("resultat"):
                inner_rows.append([Paragraph(
                    f'<font color="#15803D"><b>Résultat :</b></font>  {_rl(b["resultat"])}',
                    styles["sim_body"]
                )])
            inner = Table(inner_rows, colWidths=[half])
            inner.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), BLUE_MAIN),
                ("BACKGROUND",    (0, 1), (-1, -1), BLUE_LIGHT),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                ("BOX",           (0, 0), (-1, -1), 0.5, BLUE_MAIN),
            ]))
            row_cells.append(inner)

        if len(row_cells) == 1:
            row_cells.append(Spacer(1, 1))

        col_ws = [half + 3, half + 3]
        row_table = Table([row_cells], colWidths=col_ws)
        row_table.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(row_table)
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 6))
    return story


def _build_projection(p3: list[str], p6: list[str], styles: dict,
                      en_resume: str | None = None) -> list:
    """Two-column 3-month / 6-month projection."""
    if not p3 and not p6:
        return []
    story = []
    story.append(_section_header("📅  PROJECTION TEMPORELLE", BLUE_DARK, styles))
    story.append(Spacer(1, 4))

    col_w = CONTENT_W / 2 - 2
    left_rows = [[Paragraph("📅  3 MOIS — PREMIERS EFFETS", styles["proj_head"])]]
    for l in (p3 or ["Données insuffisantes"]):
        left_rows.append([Paragraph(_rl(l), styles["proj_body"])])
    right_rows = [[Paragraph("📅  6 MOIS — RÉSULTAT ATTENDU", styles["proj_head"])]]
    for l in (p6 or ["Données insuffisantes"]):
        right_rows.append([Paragraph(_rl(l), styles["proj_body"])])

    max_r = max(len(left_rows), len(right_rows))
    while len(left_rows) < max_r:
        left_rows.append([Paragraph("", styles["proj_body"])])
    while len(right_rows) < max_r:
        right_rows.append([Paragraph("", styles["proj_body"])])

    combined = [[l[0], r[0]] for l, r in zip(left_rows, right_rows)]
    t = Table(combined, colWidths=[col_w, col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), BLUE_LIGHT),
        ("BACKGROUND",    (1, 0), (1, 0), BLUE_LIGHT),
        ("BACKGROUND",    (0, 1), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    if en_resume:
        story.append(Spacer(1, 3))
        story.extend(_en_resume_box(en_resume, styles))
    story.append(Spacer(1, 8))
    return story


def _build_risque_inaction(risque: str, styles: dict) -> list:
    """1-sentence red warning: what happens if nothing changes."""
    if not risque:
        return []
    story = []
    cell = Paragraph(
        f"⚠️  <b>SI RIEN NE CHANGE :</b>  {_rl(risque)}",
        styles["risque_inaction"]
    )
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), RED_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("BOX",           (0, 0), (-1, -1), 1.5, RED),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    return story


def _confidence_badge(score: int | None, styles: dict) -> list:
    """Small inline confidence badge — shown at top of Margin / Cash sections."""
    if score is None:
        return []
    color_hex = "#15803D" if score >= 75 else "#D97706" if score >= 50 else "#DC2626"
    bg_hex    = "#F0FDF4" if score >= 75 else "#FFFBEB" if score >= 50 else "#FEF2F2"
    label     = "Fiabilité données" if score >= 75 else "Fiabilité partielle" if score >= 50 else "Données insuffisantes"
    cell = Paragraph(
        f'<font color="{color_hex}"><b>{score}%</b></font>'
        f'<font color="#5F6368">  ·  {label}</font>',
        ParagraphStyle("conf_badge", fontName="Helvetica", fontSize=7.5,
                       leading=11, alignment=TA_RIGHT)
    )
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor(color_hex)),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return [t, Spacer(1, 3)]


def _build_margin_intelligence(items: list[str], confidence: int | None,
                                en_resume: str | None, styles: dict) -> list:
    """Margin Intelligence — analyse des marges, destruction/création, leviers."""
    if not items:
        return []
    story = []
    story.append(_section_header("📊  MARGIN INTELLIGENCE", BLUE_DARK, styles))
    story.append(Spacer(1, 3))
    story.extend(_confidence_badge(confidence, styles))

    for item in items:
        s = item.strip()
        if not s:
            continue
        if s.startswith("🔴"):
            clean = s.lstrip("🔴 ").strip()
            icon, bg, border = "🔴", RED_LIGHT, RED
        elif s.startswith("🟢"):
            clean = s.lstrip("🟢 ").strip()
            icon, bg, border = "🟢", GREEN_LIGHT, GREEN
        elif s.startswith("⚠️"):
            clean = s.lstrip("⚠️ ").strip()
            icon, bg, border = "⚠️", AMBER_LIGHT, AMBER
        else:
            clean = s.lstrip("→ ").strip()
            icon, bg, border = "→", SLATE_LIGHT, GRAY_BORDER

        cell = Paragraph(
            f"<b>{icon}</b>  {_rl(clean)}",
            ParagraphStyle("mi_item", fontName="Helvetica", fontSize=8.5,
                           textColor=DARK, leading=13)
        )
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 0.5, border),
        ]))
        story.append(t)
        story.append(Spacer(1, 2))

    if en_resume:
        story.append(Spacer(1, 2))
        story.extend(_en_resume_box(en_resume, styles))
    story.append(Spacer(1, 8))
    return story


def _build_cash_forecast(items: list[str], bfr: list[str], confidence: int | None,
                          en_resume: str | None, styles: dict) -> list:
    """Cash Forecast & Liquidity Risk — projections trésorerie, BFR, risques."""
    if not items:
        return []
    story = []
    story.append(_section_header("💰  CASH FORECAST & RISQUE LIQUIDITÉ", BLUE_DARK, styles))
    story.append(Spacer(1, 3))
    story.extend(_confidence_badge(confidence, styles))

    # Disclaimer
    disc = Paragraph(
        "⚠️  Projection indicative — estimation basée sur les données disponibles. "
        "Pas une prévision exacte.",
        ParagraphStyle("cf_disc", fontName="Helvetica-Oblique", fontSize=7.5,
                       textColor=GRAY_TEXT, leading=11)
    )
    story.append(disc)
    story.append(Spacer(1, 4))

    for item in items:
        s = item.strip()
        if not s:
            continue
        if s.startswith("⚠️"):
            clean = s.lstrip("⚠️ ").strip()
            bg, border = RED_LIGHT, RED
            label = "⚠️  RISQUE"
            cell = Paragraph(
                f'<b>{label} :</b>  {_rl(clean)}',
                ParagraphStyle("cf_risk", fontName="Helvetica-Bold", fontSize=9,
                               textColor=colors.HexColor("#7F1D1D"), leading=14)
            )
        else:
            clean = s.lstrip("→ ").strip()
            bg, border = BLUE_LIGHT, GRAY_BORDER
            cell = Paragraph(
                f"→  {_rl(clean)}",
                ParagraphStyle("cf_item", fontName="Helvetica", fontSize=8.5,
                               textColor=DARK, leading=13)
            )
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 0.5, border),
        ]))
        story.append(t)
        story.append(Spacer(1, 2))

    # BFR mini table if available
    if bfr:
        story.append(Spacer(1, 3))
        bfr_header = Paragraph(
            '<b>📐  INDICATEURS BFR</b>',
            ParagraphStyle("bfr_h", fontName="Helvetica-Bold", fontSize=8,
                           textColor=BLUE_DARK, leading=12)
        )
        story.append(bfr_header)
        story.append(Spacer(1, 2))
        for b in bfr:
            cell = Paragraph(f"·  {_rl(b.lstrip('→ ').strip())}", styles["body_gray"])
            t = Table([[cell]], colWidths=[CONTENT_W])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), SLATE_LIGHT),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("BOX",           (0, 0), (-1, -1), 0.3, GRAY_BORDER),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))

    if en_resume:
        story.append(Spacer(1, 2))
        story.extend(_en_resume_box(en_resume, styles))
    story.append(Spacer(1, 8))
    return story


def _en_resume_box(text: str, styles: dict) -> list:
    """Blue left-border accent box — 'En résumé' synthesis line."""
    if not text:
        return []
    cell = Paragraph(
        f'<b>👉 En résumé :</b>  {_rl(text)}',
        ParagraphStyle("en_resume_style", fontName="Helvetica-Bold", fontSize=9,
                       textColor=BLUE_DARK, leading=14)
    )
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BLUE_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("LINEBEFORE",    (0, 0), (-1, -1), 3, BLUE_MAIN),
    ]))
    return [t, Spacer(1, 2)]


# ─── V11 Block Builders — Executive Deliverables Manifesto ──────────────────

def _build_macro_section_title(number: int, title: str, styles: dict) -> list:
    """Grand séparateur visuel pour les 8 sections macro du manifeste (1. EXECUTIVE SUMMARY, etc.)."""
    cell = Paragraph(
        f'<font color="#FFFFFF"><b>{number}.</b></font>  '
        f'<font color="#FFFFFF"><b>{_rl(title.upper())}</b></font>',
        ParagraphStyle("macro_title", fontName="Helvetica-Bold", fontSize=13, leading=17)
    )
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BLUE_DEEP),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))
    return [Spacer(1, 10), t, Spacer(1, 8)]


def _build_summary_scoreboard(score_global: int | None, niveau_urgence: str | None,
                               creation_destruction: str | None, styles: dict) -> list:
    """Bandeau compact : indice de santé global + niveau d'urgence + création/destruction de valeur."""
    if score_global is None and not niveau_urgence and not creation_destruction:
        return []

    urgence_colors = {
        "Critique":  ("#DC2626", "#FEF2F2"),
        "Élevé":     ("#EA580C", "#FFF7ED"),
        "Modéré":    ("#D97706", "#FFFBEB"),
        "Maîtrisé":  ("#15803D", "#F0FDF4"),
    }
    color_hex, bg_hex = urgence_colors.get(niveau_urgence or "", ("#5F6368", "#F8FAFC"))

    cells = []
    if score_global is not None:
        score_p = Paragraph(
            f'<font color="{color_hex}"><b>{score_global}/10</b></font>',
            ParagraphStyle("sgv", fontName="Helvetica-Bold", fontSize=22, alignment=TA_CENTER)
        )
        label_p = Paragraph("Indice de santé globale", styles["score_label"])
        inner = Table([[score_p], [label_p]], colWidths=[48 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(color_hex)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ]))
        cells.append(inner)

    if niveau_urgence:
        urg_p = Paragraph(
            f'<font color="{color_hex}"><b>{_rl(niveau_urgence.upper())}</b></font>',
            ParagraphStyle("urgv", fontName="Helvetica-Bold", fontSize=16, alignment=TA_CENTER)
        )
        label_p = Paragraph("Niveau d'urgence", styles["score_label"])
        inner = Table([[urg_p], [label_p]], colWidths=[48 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(color_hex)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ]))
        cells.append(inner)

    rows = []
    if cells:
        col_w = CONTENT_W / len(cells)
        t = Table([cells], colWidths=[col_w] * len(cells))
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        rows.append(t)
        rows.append(Spacer(1, 6))

    if creation_destruction:
        is_destruction = "détruit" in creation_destruction.lower() or "destruction" in creation_destruction.lower()
        c_color = RED if is_destruction else GREEN
        c_bg = RED_LIGHT if is_destruction else GREEN_LIGHT
        icon = "📉" if is_destruction else "📈"
        cell = Paragraph(f'{icon}  <b>{_rl(creation_destruction)}</b>', styles["body"])
        t2 = Table([[cell]], colWidths=[CONTENT_W])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg),
            ("BOX", (0, 0), (-1, -1), 0.8, c_color),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        rows.append(t2)
        rows.append(Spacer(1, 6))

    return rows


def _build_ceo_dashboard(cards: list[dict], alertes: list[str], styles: dict,
                          confidence: int | None = None) -> list:
    """Grandes cartes KPI : CA, Cash, EBITDA, Marge, Runway, Dette, Croissance + Niveau de confiance."""
    if not cards and not alertes and confidence is None:
        return []

    rows: list[Any] = []
    rows.append(_section_header("📊  CEO DASHBOARD", BLUE_DARK, styles))
    rows.append(Spacer(1, 6))

    cells = []
    if confidence is not None:
        color_hex = "#15803D" if confidence >= 75 else "#D97706" if confidence >= 50 else "#DC2626"
        bg_hex = "#F0FDF4" if confidence >= 75 else "#FFFBEB" if confidence >= 50 else "#FEF2F2"
        value_p = Paragraph(
            f'<font color="{color_hex}"><b>{confidence}%</b></font>',
            ParagraphStyle("dcv_conf", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, leading=16)
        )
        label_p = Paragraph("Niveau de confiance", styles["score_label"])
        inner = Table([[value_p], [label_p]], colWidths=[34 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(color_hex)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ]))
        cells.append(inner)
    for card in cards:
        label = card.get("label", "") if isinstance(card, dict) else getattr(card, "label", "")
        value = card.get("value", "") if isinstance(card, dict) else getattr(card, "value", "")
        status = card.get("status") if isinstance(card, dict) else getattr(card, "status", None)
        is_missing = status == "missing"
        color_hex = "#9CA3AF" if is_missing else "#0D47A1"
        bg_hex = "#F8FAFC" if is_missing else "#EFF6FF"
        value_p = Paragraph(
            f'<font color="{color_hex}"><b>{_rl(value)}</b></font>',
            ParagraphStyle("dcv", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, leading=16)
        )
        label_p = Paragraph(_rl(label), styles["score_label"])
        inner = Table([[value_p], [label_p]], colWidths=[34 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(color_hex)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ]))
        cells.append(inner)

    if cells:
        # 3 cartes par ligne maximum pour rester lisible
        for i in range(0, len(cells), 3):
            chunk = cells[i:i + 3]
            col_w = CONTENT_W / len(chunk)
            t = Table([chunk], colWidths=[col_w] * len(chunk))
            t.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            rows.append(t)
            rows.append(Spacer(1, 4))

    if alertes:
        rows.append(Spacer(1, 4))
        rows.append(Paragraph("<b>⚠️ Alertes</b>", styles["subsection"]))
        rows.append(Spacer(1, 2))
        rows.extend(_bullet_rows(alertes, "⚠️", AMBER, AMBER_LIGHT, styles))

    rows.append(Spacer(1, 8))
    return rows


def _build_quick_wins(wins: list[dict], styles: dict) -> list:
    """Tableau des opportunités immédiates : description | ROI | délai | difficulté."""
    if not wins:
        return []

    rows: list[Any] = []
    rows.append(_section_header("⚡  OPPORTUNITÉS IMMÉDIATES — QUICK WINS", GREEN, styles))
    rows.append(Spacer(1, 5))

    header = [
        Paragraph("<b>Action</b>", styles["small"]),
        Paragraph("<b>ROI estimé</b>", styles["small"]),
        Paragraph("<b>Délai</b>", styles["small"]),
        Paragraph("<b>Difficulté</b>", styles["small"]),
    ]
    table_rows = [header]
    for w in wins:
        desc = w.get("description", "") if isinstance(w, dict) else getattr(w, "description", "")
        roi = w.get("roi_estime") if isinstance(w, dict) else getattr(w, "roi_estime", None)
        temps = w.get("temps_mise_en_oeuvre") if isinstance(w, dict) else getattr(w, "temps_mise_en_oeuvre", None)
        diff = w.get("difficulte") if isinstance(w, dict) else getattr(w, "difficulte", None)
        table_rows.append([
            Paragraph(_rl(desc), styles["body"]),
            Paragraph(_rl(roi or "—"), styles["body"]),
            Paragraph(_rl(temps or "—"), styles["body"]),
            Paragraph(_rl((diff or "—").capitalize()), styles["body"]),
        ])

    col_w = [CONTENT_W * 0.46, CONTENT_W * 0.2, CONTENT_W * 0.17, CONTENT_W * 0.17]
    t = Table(table_rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), GREEN_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, GREEN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_BG]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    rows.append(t)
    rows.append(Spacer(1, 8))
    return rows


def _build_plan_30_60_90(items: list[dict], styles: dict) -> list:
    """Plan d'action en 3 bandes temporelles : 30 / 60 / 90 jours."""
    if not items:
        return []

    rows: list[Any] = []
    rows.append(_section_header("🗓️  PLAN D'ACTION — 30 / 60 / 90 JOURS", BLUE_MAIN, styles))
    rows.append(Spacer(1, 5))

    horizon_labels = {"30": "30 JOURS", "60": "60 JOURS", "90": "90 JOURS"}
    horizon_colors = {
        "30": (RED, RED_LIGHT, "#DC2626"),
        "60": (AMBER, AMBER_LIGHT, "#D97706"),
        "90": (GREEN, GREEN_LIGHT, "#15803D"),
    }

    for horizon in ["30", "60", "90"]:
        bucket = [
            it for it in items
            if (it.get("horizon") if isinstance(it, dict) else getattr(it, "horizon", None)) == horizon
        ]
        if not bucket:
            continue
        color, bg, color_hex = horizon_colors[horizon]
        rows.append(Paragraph(
            f'<font color="{color_hex}"><b>{horizon_labels[horizon]}</b></font>',
            styles["subsection"]
        ))
        rows.append(Spacer(1, 2))
        for it in bucket:
            action = it.get("action", "") if isinstance(it, dict) else getattr(it, "action", "")
            resp = it.get("responsable") if isinstance(it, dict) else getattr(it, "responsable", None)
            impact = it.get("impact_attendu") if isinstance(it, dict) else getattr(it, "impact_attendu", None)
            detail = _rl(action)
            if resp:
                detail += f'  ·  <font color="#5F6368">Responsable : {_rl(resp)}</font>'
            if impact:
                detail += f'  ·  <font color="#5F6368">Impact : {_rl(impact)}</font>'
            cell = Paragraph(detail, styles["body"])
            t = Table([[cell]], colWidths=[CONTENT_W])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), bg),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 9),
                ("BOX",           (0, 0), (-1, -1), 0.5, color),
            ]))
            rows.append(t)
            rows.append(Spacer(1, 2))
        rows.append(Spacer(1, 4))

    rows.append(Spacer(1, 4))
    return rows


def _build_scenarios(scenarios: list[dict], styles: dict) -> list:
    """Simulation Avant/Après — 3 scénarios nommés : meilleur cas / cas probable / pire cas."""
    if not scenarios:
        return []

    rows: list[Any] = []
    rows.append(_section_header("🎲  SIMULATION — MEILLEUR CAS / CAS PROBABLE / PIRE CAS", BLUE_DARK, styles))
    rows.append(Spacer(1, 5))

    style_map = {
        "best_case":   ("🟢", GREEN, GREEN_LIGHT),
        "most_likely": ("🔵", BLUE_MAIN, BLUE_LIGHT),
        "worst_case":  ("🔴", RED, RED_LIGHT),
    }

    cells = []
    for sc in scenarios:
        nom = sc.get("nom", "") if isinstance(sc, dict) else getattr(sc, "nom", "")
        label = sc.get("label", "") if isinstance(sc, dict) else getattr(sc, "label", "")
        desc = sc.get("description", "") if isinstance(sc, dict) else getattr(sc, "description", "")
        icon, color, bg = style_map.get(nom, ("⚪", GRAY_TEXT, GRAY_BG))

        title_p = Paragraph(f'{icon}  <b>{_rl(label.upper())}</b>', ParagraphStyle(
            "scn_title", fontName="Helvetica-Bold", fontSize=9.5, textColor=color, leading=13))
        desc_p = Paragraph(_rl(desc), ParagraphStyle(
            "scn_desc", fontName="Helvetica", fontSize=8.5, textColor=DARK, leading=12))
        inner = Table([[title_p], [Spacer(1, 3)], [desc_p]], colWidths=[CONTENT_W / 3 - 4])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("BOX",           (0, 0), (-1, -1), 0.8, color),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        cells.append(inner)

    if cells:
        col_w = CONTENT_W / len(cells)
        t = Table([cells], colWidths=[col_w] * len(cells))
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        rows.append(t)

    rows.append(Spacer(1, 8))
    return rows


def _build_separator_detailed(styles: dict) -> list:
    """Visual separator before the detailed analysis section."""
    story = []
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width=CONTENT_W, thickness=1, color=GRAY_BORDER))
    story.append(Spacer(1, 4))
    cell = Paragraph("▼  ANALYSE DÉTAILLÉE — DONNÉES COMPLÈTES", styles["separator"])
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX",           (0, 0), (-1, -1), 0.3, GRAY_BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))
    return story


# ─── V12 Block Builders — Executive Narrative (Étape C) ──────────────────────
# Ces builders lisent UNIQUEMENT l'ExecutiveDecisionModel (aucun calcul ici,
# toute la logique métier vit dans services/executive_decision_model.py).
# Vocabulaire interne (EDM) en anglais -> affichage client en français.

_PRIORITY_FR = {"High": "Élevée", "Medium": "Moyenne", "Low": "Faible", "Not evaluated": "Non évaluée"}
_STATUS_FR = {"To launch": "À lancer"}
_TREND_FR = {"up": "↑ En hausse", "down": "↓ En baisse", "stable": "→ Stable", None: "—"}


def _fmt_eur(value: float | None, show_sign: bool = False) -> str:
    """Formate un montant en euros, style français (espace milliers, virgule décimale)."""
    if value is None:
        return "—"
    sign = ""
    if show_sign and value > 0:
        sign = "+"
    elif value < 0:
        sign = "-"
    v = abs(value)
    if v >= 1_000_000:
        return f"{sign}{v / 1_000_000:.1f}".replace(".", ",") + " M€"
    return f"{sign}{v:,.0f}".replace(",", " ") + " €"


def _stat_card(label: str, value: str, border_color, hex_str: str, styles: dict, width=None) -> Table:
    """Petite carte KPI carrée — réutilisée par les sections Executive Decision / Coût de l'inaction."""
    value_p = Paragraph(
        f'<font color="{hex_str}"><b>{_rl(value)}</b></font>',
        ParagraphStyle("stat_v", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, leading=16),
    )
    label_p = Paragraph(_rl(label), styles["score_label"])
    inner = Table([[value_p], [label_p]], colWidths=[width or (CONTENT_W / 3 - 6)])
    inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return inner


def _build_executive_decision_page(edm: ExecutiveDecisionModel, decision_context: str | None, styles: dict) -> list:
    """
    Section 1 — Executive Decision.
    LA décision la plus importante, seule, présentée de façon très visuelle.
    Le dirigeant doit la comprendre en moins de 10 secondes.
    """
    ed = edm.executive_decision
    if not ed:
        return []

    story: list[Any] = [Spacer(1, 26)]

    rows = [
        [Paragraph(
            '<font color="#94A3B8"><b>DÉCISION PRIORITAIRE</b></font>',
            ParagraphStyle("ed_label", fontName="Helvetica-Bold", fontSize=10, leading=14),
        )],
        [Paragraph(
            f'<font color="#FFFFFF"><b>{_rl(ed.decision)}</b></font>',
            ParagraphStyle("ed_title", fontName="Helvetica-Bold", fontSize=19, leading=25),
        )],
    ]
    if ed.annual_impact is not None:
        rows.append([Paragraph(
            f'<font color="#FCD34D"><b>Impact estimé : {_fmt_eur(ed.annual_impact, show_sign=True)} / an</b></font>',
            ParagraphStyle("ed_impact", fontName="Helvetica-Bold", fontSize=15, leading=20),
        )])
    if decision_context:
        rows.append([Paragraph(
            _rl(decision_context),
            ParagraphStyle("ed_context", fontName="Helvetica", fontSize=10,
                           textColor=colors.HexColor("#CBD5E1"), leading=15),
        )])

    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_DEEP),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # Stats de soutien : priorité + coût de l'inaction (mois / jour)
    cells = []
    priority_fr = _PRIORITY_FR.get(ed.priority, ed.priority)
    p_color, p_hex = {"Élevée": (RED, RED_HEX), "Moyenne": (AMBER, AMBER_HEX), "Faible": (GREEN, GREEN_HEX)}.get(
        priority_fr, (GRAY_BORDER, GRAY_HEX)
    )
    cells.append(_stat_card("Priorité", priority_fr, p_color, p_hex, styles))
    coi = edm.cost_of_inaction_summary
    if coi and coi.per_month is not None:
        cells.append(_stat_card("Coût de l'inaction / mois", _fmt_eur(coi.per_month), RED, RED_HEX, styles))
    if coi and coi.per_day is not None:
        cells.append(_stat_card("Coût de l'inaction / jour", _fmt_eur(coi.per_day), RED, RED_HEX, styles))
    if cells:
        col_w = CONTENT_W / len(cells)
        t2 = Table([cells], colWidths=[col_w] * len(cells))
        t2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(t2)
        story.append(Spacer(1, 16))

    cta = Paragraph(
        "👉  <b>Agissez cette semaine.</b>",
        ParagraphStyle("ed_cta", fontName="Helvetica-Bold", fontSize=12,
                       textColor=BLUE_DARK, leading=17, alignment=TA_CENTER),
    )
    t3 = Table([[cta]], colWidths=[CONTENT_W])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 1, BLUE_MAIN),
    ]))
    story.append(t3)
    story.append(PageBreak())
    return story


def _build_value_destroyers_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 4 — Ce qui détruit la rentabilité (tableau structuré, Top 5)."""
    destroyers = edm.value_destroyers[:5]
    if not destroyers:
        return []
    rows: list[Any] = [_section_header("CE QUI DÉTRUIT VOTRE RENTABILITÉ", RED, styles), Spacer(1, 5)]

    header = [Paragraph(f"<b>{h}</b>", styles["small"]) for h in
              ["Destructeur de valeur", "Impact annuel", "Impact mensuel", "Tendance"]]
    table_rows = [header]
    for d in destroyers:
        table_rows.append([
            Paragraph(_rl(d.name), styles["body"]),
            Paragraph(_fmt_eur(d.annual_impact), styles["body"]),
            Paragraph(_fmt_eur(d.monthly_impact), styles["body"]),
            Paragraph(_TREND_FR.get(d.trend, "—"), styles["body"]),
        ])
    col_w = [CONTENT_W * 0.4, CONTENT_W * 0.22, CONTENT_W * 0.22, CONTENT_W * 0.16]
    t = Table(table_rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RED_LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, RED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    rows.append(t)

    comments = [d.comment for d in destroyers if d.comment]
    if comments:
        rows.append(Spacer(1, 4))
        for c in comments[:3]:
            rows.append(Paragraph(f"·  {_rl(c)}", styles["body_gray"]))

    rows.append(Spacer(1, 8))
    rows.append(PageBreak())
    return rows


def _build_cost_of_inaction_page(edm: ExecutiveDecisionModel, risque_text: str | None, styles: dict) -> list:
    """Section 5 — Coût de l'inaction (page dédiée, 100% calculé en Python)."""
    coi = edm.cost_of_inaction
    if not coi:
        return []
    story: list[Any] = [_section_header("COMBIEN VOUS COÛTE L'INACTION", SLATE, styles), Spacer(1, 10)]

    periods = [
        ("Par an", coi.per_year), ("Par mois", coi.per_month), ("Par semaine", coi.per_week),
        ("Par jour", coi.per_day), ("Par heure", coi.per_hour),
    ]
    cells = [_stat_card(label, _fmt_eur(val), RED, RED_HEX, styles) for label, val in periods if val is not None]
    for i in range(0, len(cells), 3):
        chunk = cells[i:i + 3]
        col_w = CONTENT_W / len(chunk)
        t = Table([chunk], colWidths=[col_w] * len(chunk))
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    if risque_text:
        story.append(Spacer(1, 4))
        cell = Paragraph(f"⚠️  <b>Si rien ne change :</b>  {_rl(risque_text)}", styles["risque_inaction"])
        t2 = Table([[cell]], colWidths=[CONTENT_W])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), RED_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("BOX", (0, 0), (-1, -1), 1.5, RED), ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        story.append(t2)

    story.append(Spacer(1, 8))
    story.append(PageBreak())
    return story


def _build_executive_decisions_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 6 — Executive Decisions / Priorités d'action (tableau trié par impact)."""
    decisions = edm.executive_decisions
    if not decisions:
        return []
    rows: list[Any] = [_section_header("PRIORITÉS D'ACTION", GREEN, styles), Spacer(1, 4)]
    rows.append(Paragraph(f"<b>Score de priorisation global :</b> {edm.executive_decisions_score}/10", styles["body"]))
    rows.append(Spacer(1, 5))

    header = [Paragraph(f"<b>{h}</b>", styles["small"]) for h in
              ["Décision", "Impact annuel", "Délai", "Difficulté", "Priorité"]]
    table_rows = [header]
    for d in decisions:
        table_rows.append([
            Paragraph(_rl(d.decision), styles["body"]),
            Paragraph(_fmt_eur(d.annual_impact, show_sign=True), styles["body"]),
            Paragraph(_rl(d.timeline or "—"), styles["body"]),
            Paragraph(_rl((d.difficulty or "—").capitalize()), styles["body"]),
            Paragraph(_PRIORITY_FR.get(d.priority, d.priority), styles["body"]),
        ])
    col_w = [CONTENT_W * 0.36, CONTENT_W * 0.18, CONTENT_W * 0.14, CONTENT_W * 0.16, CONTENT_W * 0.16]
    t = Table(table_rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.5, GREEN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("BOX", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    rows.append(t)
    rows.append(Spacer(1, 8))
    rows.append(PageBreak())
    return rows


def _build_simulation_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 7 — Simulation Avant/Après : courbe Action (verte) vs Inaction (rouge)."""
    if not edm.action_series or not edm.do_nothing_series:
        return []
    story: list[Any] = [_section_header("SIMULATION — AGIR OU NE RIEN FAIRE", BLUE_DARK, styles), Spacer(1, 8)]

    d = Drawing(CONTENT_W, 46 * mm)
    chart = HorizontalLineChart()
    chart.x = 10
    chart.y = 8 * mm
    chart.width = CONTENT_W - 20
    chart.height = 36 * mm
    chart.data = [edm.action_series, edm.do_nothing_series]
    chart.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(edm.action_series))]
    chart.categoryAxis.labels.fontSize = 6
    chart.categoryAxis.labels.fillColor = GRAY_TEXT
    chart.valueAxis.labels.fontSize = 6
    chart.valueAxis.labels.fillColor = GRAY_TEXT
    chart.valueAxis.labelTextFormat = lambda v: _fmt_eur(v)
    all_vals = edm.action_series + edm.do_nothing_series
    vmax = max(abs(v) for v in all_vals) * 1.15 if all_vals else 1
    chart.valueAxis.valueMin = -vmax
    chart.valueAxis.valueMax = vmax
    chart.lines[0].strokeColor = GREEN
    chart.lines[0].strokeWidth = 2
    chart.lines[1].strokeColor = RED
    chart.lines[1].strokeWidth = 2
    chart.joinedLines = 1
    d.add(chart)
    story.append(d)

    legend_row = [
        Paragraph('<font color="#15803D">━━</font>  Avec action', ParagraphStyle(
            "leg1", fontName="Helvetica", fontSize=8, alignment=TA_CENTER, leading=11)),
        Paragraph('<font color="#DC2626">━━</font>  Sans action', ParagraphStyle(
            "leg2", fontName="Helvetica", fontSize=8, alignment=TA_CENTER, leading=11)),
    ]
    t_legend = Table([legend_row], colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    story.append(t_legend)
    story.append(Spacer(1, 6))

    style_map = {
        "best_case": ("🟢", GREEN, GREEN_LIGHT),
        "most_likely": ("🔵", BLUE_MAIN, BLUE_LIGHT),
        "worst_case": ("🔴", RED, RED_LIGHT),
    }
    cells = []
    for sc in edm.scenarios:
        icon, color, bg = style_map.get(sc.nom, ("⚪", GRAY_TEXT, GRAY_BG))
        title_p = Paragraph(f'{icon}  <b>{_rl(sc.label.upper())}</b>', ParagraphStyle(
            "scn_t", fontName="Helvetica-Bold", fontSize=9, textColor=color, leading=12))
        desc_p = Paragraph(_rl(sc.description), ParagraphStyle(
            "scn_d", fontName="Helvetica", fontSize=8, textColor=DARK, leading=11))
        inner = Table([[title_p], [desc_p]], colWidths=[CONTENT_W / 3 - 4])
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.8, color),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        cells.append(inner)
    if cells:
        col_w = CONTENT_W / len(cells)
        t2 = Table([cells], colWidths=[col_w] * len(cells))
        t2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t2)

    story.append(Spacer(1, 8))
    story.append(PageBreak())
    return story


def _build_projection_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 8 — Projection et trajectoire (courbe simple, 12 mois)."""
    if not edm.monthly_projection:
        return []
    story: list[Any] = [_section_header("PROJECTION ET TRAJECTOIRE", BLUE_DARK, styles), Spacer(1, 8)]

    d = Drawing(CONTENT_W, 46 * mm)
    chart = HorizontalLineChart()
    chart.x = 10
    chart.y = 8 * mm
    chart.width = CONTENT_W - 20
    chart.height = 36 * mm
    chart.data = [edm.monthly_projection]
    chart.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(edm.monthly_projection))]
    chart.categoryAxis.labels.fontSize = 6
    chart.valueAxis.labels.fontSize = 6
    chart.valueAxis.labelTextFormat = lambda v: _fmt_eur(v)
    vmax = max(edm.monthly_projection) * 1.15 if edm.monthly_projection else 1
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = vmax if vmax > 0 else 1
    chart.lines[0].strokeColor = BLUE_MAIN
    chart.lines[0].strokeWidth = 2.2
    chart.joinedLines = 1
    d.add(chart)
    story.append(d)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Trajectoire estimée sur 12 mois si les décisions prioritaires sont engagées dès maintenant.",
        styles["body_gray"],
    ))
    story.append(Spacer(1, 8))
    story.append(PageBreak())
    return story


def _build_execution_log_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 9 — Carnet d'exécution (remplace l'ancienne 'Analyse détaillée')."""
    items = edm.execution_log
    if not items:
        return []
    rows: list[Any] = [_section_header("CARNET D'EXÉCUTION", BLUE_MAIN, styles), Spacer(1, 5)]

    header = [Paragraph(f"<b>{h}</b>", styles["small"]) for h in
              ["Décision", "Responsable", "Impact", "Échéance", "Statut"]]
    table_rows = [header]
    for it in items:
        table_rows.append([
            Paragraph(_rl(it.decision), styles["body"]),
            Paragraph(_rl(it.owner or "—"), styles["body"]),
            Paragraph(_fmt_eur(it.impact, show_sign=True), styles["body"]),
            Paragraph(_rl(it.due_date or "—"), styles["body"]),
            Paragraph(_STATUS_FR.get(it.status, it.status), styles["body"]),
        ])
    col_w = [CONTENT_W * 0.36, CONTENT_W * 0.16, CONTENT_W * 0.18, CONTENT_W * 0.16, CONTENT_W * 0.14]
    t = Table(table_rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.5, BLUE_MAIN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("BOX", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    rows.append(t)
    rows.append(Spacer(1, 8))
    rows.append(PageBreak())
    return rows


def _build_copilot_note_section(edm: ExecutiveDecisionModel, styles: dict) -> list:
    """Section 10 — Note confidentielle du copilote financier."""
    note = edm.copilot_note
    if not note:
        return []
    story: list[Any] = [_section_header("NOTE CONFIDENTIELLE DU COPILOTE FINANCIER", BLUE_DEEP, styles), Spacer(1, 10)]

    # Découpage en paragraphes réels (ligne vide = nouveau paragraphe) ; les
    # retours à la ligne simples ne sont que des sauts de mise en forme dans
    # le texte source et doivent être recollés en une seule phrase continue.
    paragraphs = [
        " ".join(p.split())
        for p in _re.split(r"\n\s*\n", note)
        if p.strip()
    ]
    note_rows = [[Paragraph(_rl(p), ParagraphStyle(
        "note_p", fontName="Helvetica", fontSize=10, textColor=DARK, leading=16))] for p in paragraphs]
    t = Table(note_rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    return story


def _build_follow_up_section(edm: ExecutiveDecisionModel, memory_insight: str | None, styles: dict) -> list:
    """Section 11 — Comment Pepperyn continuera à vous accompagner (non commerciale)."""
    fu = edm.follow_up
    if not fu:
        return []
    story: list[Any] = [
        _section_header("COMMENT PEPPERYN CONTINUERA À VOUS ACCOMPAGNER", BLUE_DARK, styles),
        Spacer(1, 6),
    ]
    if memory_insight:
        story.append(Paragraph(f"<b>Depuis votre dernière analyse :</b> {_rl(memory_insight)}", styles["body"]))
        story.append(Spacer(1, 6))
    for commitment in fu.commitments:
        cell = Paragraph(f"✓  {_rl(commitment)}", styles["body"])
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("BOX", (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ]))
        story.append(t)
        story.append(Spacer(1, 2))
    if fu.next_analysis_recommended:
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>Prochaine analyse recommandée :</b> {_rl(fu.next_analysis_recommended)}", styles["body"]
        ))
    story.append(Spacer(1, 8))
    return story


# ─── Main generate function ───────────────────────────────────────────────────
def generate_pdf_report(result: dict) -> bytes:
    """
    Generate the Pepperyn Executive Report (PDF) — Executive Narrative, 12 sections.
    Lit exclusivement l'Executive Decision Model pour tout contenu calculé
    (impact, priorité, ROI, coût de l'inaction, séries, statut) ; le texte
    libre (LLM) est lu directement sur `result` pour les sections qui n'ont
    pas (encore) d'équivalent dans l'EDM (Résumé exécutif, contexte).
    Returns PDF bytes.
    """
    buf = io.BytesIO()
    styles = _build_styles()
    edm = build_executive_decision_model(result)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=58 * mm,
        bottomMargin=20 * mm,
        title="Rapport exécutif Pepperyn",
        author="Pepperyn",
    )

    story: list[Any] = []

    # ── BLOC : FIABILITÉ DES DONNÉES (réassemblé en ANNEXE — section 12) ───────
    _idx_data_quality = len(story)
    dq = result.get("data_quality") or {}
    if dq:
        dq_score   = dq.get("score_data", 70) if isinstance(dq, dict) else getattr(dq, "score_data", 70)
        dq_status  = (dq.get("status", "ok") if isinstance(dq, dict) else getattr(dq, "status", "ok")).lower()
        dq_format  = dq.get("document_format", "") if isinstance(dq, dict) else getattr(dq, "document_format", "")
        dq_mapping = dq.get("mapping_summary", []) if isinstance(dq, dict) else getattr(dq, "mapping_summary", [])
        dq_anomaly = dq.get("anomalies", []) if isinstance(dq, dict) else getattr(dq, "anomalies", [])
        dq_assumpt = dq.get("assumptions", []) if isinstance(dq, dict) else getattr(dq, "assumptions", [])

        status_color = {"ok": GREEN, "warning": AMBER, "blocked": RED}.get(dq_status, GRAY_TEXT)
        status_bg    = {"ok": GREEN_LIGHT, "warning": AMBER_LIGHT, "blocked": RED_LIGHT}.get(dq_status, GRAY_BG)
        status_label = {"ok": "✅ OK", "warning": "⚠️ AVERTISSEMENT", "blocked": "🚫 BLOQUÉ"}.get(dq_status, dq_status.upper())

        story.append(_section_header("🔍  FIABILITÉ DES DONNÉES", status_color, styles))
        story.append(Spacer(1, 4))

        score_ia = result.get("score_confiance", 0)
        rows_dq = [
            [Paragraph("<b>Score fiabilité données source</b>", styles["body"]),
             Paragraph(f"<b>{dq_score}/100</b>", styles["body"]),
             Paragraph(f"<b>{status_label}</b>", styles["body"])],
            [Paragraph("<b>Niveau de confiance</b>", styles["body"]),
             Paragraph(f"<b>{score_ia}%</b>", styles["body"]),
             Paragraph("Qualité de l'analyse", styles["small"])],
        ]
        col_w = [CONTENT_W * 0.45, CONTENT_W * 0.2, CONTENT_W * 0.35]
        t_scores = Table(rows_dq, colWidths=col_w)
        t_scores.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), status_bg),
            ("BACKGROUND", (0, 1), (-1, 1), BLUE_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("BOX",           (0, 0), (-1, -1), 0.5, status_color),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.3, GRAY_TEXT),
        ]))
        story.append(t_scores)
        story.append(Spacer(1, 4))

        fmt_label = {
            "structural_pl": "Document structurel (P&L / Bilan / Budget)",
            "erp_transactional": "Données transactionnelles (ERP / exports comptables)",
        }.get(dq_format, dq_format or "Indéterminé")
        story.append(Paragraph(f"<b>Format détecté :</b> {_rl(fmt_label)}", styles["small"]))
        story.append(Spacer(1, 2))

        if dq_mapping:
            story.append(Paragraph("<b>Mapping détecté :</b>", styles["small"]))
            for m in dq_mapping[:4]:
                story.append(Paragraph(f"  • {_rl(m)}", styles["small"]))
            story.append(Spacer(1, 2))

        if dq_anomaly:
            story.append(Paragraph(f"<b>Anomalies ({len(dq_anomaly)}) :</b>", styles["small"]))
            for a in dq_anomaly[:5]:
                story.append(Paragraph(f"  ⚠️ {_rl(a)}", styles["small"]))
            story.append(Spacer(1, 2))

        if dq_assumpt:
            story.append(Paragraph("<b>Limites de l'analyse :</b>", styles["small"]))
            for a in dq_assumpt[:3]:
                story.append(Paragraph(f"  ℹ️ {_rl(a)}", styles["small"]))
            story.append(Spacer(1, 2))

        if dq_status == "warning":
            warn_cell = Paragraph(
                "⚠️  <b>Analyse basée sur des données partiellement fiables.</b> "
                "Certaines conclusions peuvent être biaisées. Validez les données sources avant toute décision.",
                styles["body"]
            )
            t_warn = Table([[warn_cell]], colWidths=[CONTENT_W])
            t_warn.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), AMBER_LIGHT),
                ("BOX",        (0, 0), (-1, -1), 1.0, AMBER),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ]))
            story.append(t_warn)
            story.append(Spacer(1, 2))

        story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=GRAY_TEXT))
        story.append(Spacer(1, 10))
    block_data_quality = story[_idx_data_quality:]
    del story[_idx_data_quality:]

    # ── BLOC : COMPLÉMENTS D'ANALYSE (réassemblé en ANNEXE — section 12) ───────
    # Contenu technique conservé (aucune perte d'information) mais retiré de la
    # narration principale pour respecter le principe « une page = une idée » et
    # la réduction de la surcharge visuelle demandées à l'Étape C.
    _idx_complements = len(story)

    impact_synthese = result.get("impact_financier_synthese")
    impact = result.get("impact_financier") or []
    story.extend(_build_impact_financier(impact_synthese, impact, styles,
                                         en_resume=result.get("en_resume_impact")))

    story.extend(_build_margin_intelligence(
        items=result.get("margin_intelligence") or [],
        confidence=result.get("margin_confidence"),
        en_resume=result.get("en_resume_margin"),
        styles=styles,
    ))

    story.extend(_build_cash_forecast(
        items=result.get("cash_forecast") or [],
        bfr=result.get("bfr_indicators") or [],
        confidence=result.get("cash_forecast_confidence"),
        en_resume=result.get("en_resume_cash"),
        styles=styles,
    ))

    diag_rev  = result.get("diagnostic_revenus", "")
    diag_cout = result.get("diagnostic_couts", "")
    diag_marge= result.get("diagnostic_marges", "")
    if any([diag_rev, diag_cout, diag_marge]):
        story.append(_section_header("💹  DIAGNOSTIC FINANCIER", BLUE_DARK, styles))
        story.append(Spacer(1, 3))
        if diag_rev:
            story.append(Paragraph(f"<b>Revenus :</b> {_rl(diag_rev)}", styles["body"]))
            story.append(Spacer(1, 2))
        if diag_cout:
            story.append(Paragraph(f"<b>Coûts :</b> {_rl(diag_cout)}", styles["body"]))
            story.append(Spacer(1, 2))
        if diag_marge:
            story.append(Paragraph(f"<b>Marges :</b> {_rl(diag_marge)}", styles["body"]))
        story.append(Spacer(1, 8))

    changements = result.get("ce_qui_a_change", [])
    if changements:
        story.append(_section_header("🔄  CE QUI A CHANGÉ", AMBER, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(changements, "🔄", AMBER, AMBER_LIGHT, styles))
        story.append(Spacer(1, 8))

    problemes = result.get("problemes_critiques", [])
    if problemes:
        story.append(_section_header(f"🔴  PROBLÈMES CRITIQUES ({len(problemes)})", RED, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(problemes, "🔴", RED, RED_LIGHT, styles))
        story.append(Spacer(1, 8))

    opportunites = result.get("opportunites_v3") or result.get("opportunites", [])
    if opportunites:
        opp_list: list[str] = []
        for o in opportunites:
            if isinstance(o, str):
                opp_list.append(o)
            elif isinstance(o, dict):
                opp_list.append(o.get("description", str(o)))
        if opp_list:
            story.append(_section_header(f"🟢  OPPORTUNITÉS ({len(opp_list)})", GREEN, styles))
            story.append(Spacer(1, 3))
            story.extend(_bullet_rows(opp_list, "🟢", GREEN, GREEN_LIGHT, styles))
            story.append(Spacer(1, 8))

    block_complements = story[_idx_complements:]
    del story[_idx_complements:]

    # ═══════════════════════════════════════════════════════════════════════
    # EXECUTIVE NARRATIVE — assemblage dans l'ordre canonique (12 sections)
    # Une page = une idée principale. Chaque section démarre sur une page
    # neuve (PageBreak) ; tout le contenu calculé vient de l'EDM, jamais
    # recalculé ici.
    # ═══════════════════════════════════════════════════════════════════════

    # 1. EXECUTIVE DECISION — page de tête, décision unique, ultra-visuelle
    story.extend(_build_executive_decision_page(edm, result.get("decision"), styles))

    # 2. EXECUTIVE SUMMARY
    story.extend(_build_macro_section_title(2, "Résumé exécutif", styles))
    story.extend(_build_financial_headline(result.get("impact_financier_synthese"), styles))
    diag_imm = result.get("diagnostic_immediat", "")
    tension = result.get("phrase_tension", "")
    story.extend(_build_diagnostic_immediat(diag_imm, tension, styles, show_decision=False))
    resume = result.get("resume_executif") or result.get("synthese", "")
    story.extend(_build_resume_executif(resume, styles))
    scores = {
        "rentabilite": result.get("score_rentabilite"),
        "risque":      result.get("score_risque"),
        "structure":   result.get("score_structure"),
        "liquidite":   result.get("score_liquidite"),
    }
    interpretations = result.get("score_interpretations") or {}
    if isinstance(interpretations, dict) and any(v is not None for v in scores.values()):
        story.append(_section_header("📈  SCORES /10", BLUE_DARK, styles))
        story.append(Spacer(1, 6))
        story.append(_score_table(scores, interpretations, styles))
        story.append(Spacer(1, 8))
    story.extend(_build_summary_scoreboard(
        result.get("score_global"), result.get("niveau_urgence"),
        result.get("creation_destruction_valeur"), styles,
    ))
    story.append(PageBreak())

    # 3. CEO DASHBOARD
    story.extend(_build_macro_section_title(3, "CEO Dashboard", styles))
    story.extend(_build_ceo_dashboard(
        result.get("ceo_dashboard") or [], result.get("alertes") or [], styles,
        confidence=edm.executive_confidence,
    ))
    story.append(PageBreak())

    # 4. CE QUI DÉTRUIT LA RENTABILITÉ
    story.extend(_build_value_destroyers_section(edm, styles))

    # 5. COÛT DE L'INACTION
    story.extend(_build_cost_of_inaction_page(edm, result.get("risque_inaction"), styles))

    # 6. EXECUTIVE DECISIONS / PRIORITÉS D'ACTION
    story.extend(_build_executive_decisions_section(edm, styles))

    # 7. SIMULATION AVANT / APRÈS
    story.extend(_build_simulation_section(edm, styles))

    # 8. PROJECTION ET TRAJECTOIRE
    story.extend(_build_projection_section(edm, styles))

    # 9. CARNET D'EXÉCUTION
    story.extend(_build_execution_log_section(edm, styles))

    # 10. NOTE CONFIDENTIELLE DU COPILOTE FINANCIER
    story.extend(_build_copilot_note_section(edm, styles))

    # 11. COMMENT PEPPERYN CONTINUERA À VOUS ACCOMPAGNER
    story.extend(_build_follow_up_section(edm, result.get("memory_insight"), styles))
    story.append(PageBreak())

    # 12. ANNEXES & MÉTHODOLOGIE
    story.extend(_build_macro_section_title(12, "Annexes et méthodologie", styles))
    story.extend(block_data_quality)
    if block_complements:
        story.extend(_build_separator_detailed(styles))
        story.extend(block_complements)

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_header(c, d, result),
        onLaterPages=lambda c, d: _draw_header(c, d, result),
    )

    return buf.getvalue()
