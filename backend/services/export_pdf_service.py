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
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import re as _re


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
    """4 score circles with colour + interpretation."""
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
        color = "#15803D" if val >= 8 else "#D97706" if val >= 5 else "#DC2626"
        score_p = Paragraph(f'<font color="{color}"><b>{val}</b></font>', styles["score_value"])
        label_p = Paragraph(label, styles["score_label"])
        rows_inner = [[score_p], [label_p]]
        if interp:
            rows_inner.append([Paragraph(_rl(interp), styles["score_interp"])])
        inner = Table(rows_inner, colWidths=[38 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX",           (0, 0), (-1, -1), 1.5, colors.HexColor(color)),
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
    canvas.drawString(MARGIN, PAGE_H - 22 * mm, "Rapport d'analyse financière")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    doc_type = result.get("type_document", "Document financier")
    conf = result.get("score_confiance", 0)
    date_str = datetime.now().strftime("%d/%m/%Y")
    canvas.drawString(MARGIN, PAGE_H - 30 * mm, f"{doc_type}  ·  Confiance : {conf}%  ·  {date_str}")

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 22 * mm, "Pepperyn")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 29 * mm, "Analyse IA · Niveau expert")

    canvas.setFillColor(GRAY_TEXT)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 10 * mm,
        f"Généré par Pepperyn — {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  Ce document est confidentiel"
    )
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# ─── V5 Block Builders ────────────────────────────────────────────────────────

def _build_diagnostic_immediat(diag: str, styles: dict) -> list:
    """Hero block — full-width red/dark with bold diagnostic + decision."""
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
        elif stripped:
            main_line = stripped.lstrip("⚠️").strip()

    rows = []
    if main_line:
        rows.append([Paragraph(f"⚠️  {_rl(main_line)}", styles["hero_main"])])
    if decision_line:
        rows.append([Paragraph(f"👉  DÉCISION PRIORITAIRE : {_rl(decision_line)}", styles["hero_decision"])])
    if not rows:
        rows.append([Paragraph(_rl(diag), styles["hero_main"])])

    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SLATE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#374151")),
    ]))
    story.append(KeepTogether([t]))
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


def _build_impact_financier(items: list[str], styles: dict) -> list:
    """Dark slate block with financial impact estimates."""
    if not items:
        return []
    story = []
    story.append(_section_header("💸  IMPACT FINANCIER ESTIMÉ", SLATE, styles))
    story.append(Spacer(1, 2))

    rows = [[Paragraph(
        "⚠️  Estimations basées sur les données disponibles uniquement.",
        styles["small"]
    )]]
    for item in items[:5]:
        rows.append([Paragraph(f"→  {_rl(item)}", styles["body"])])

    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), SLATE_LIGHT),
        ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, SLATE),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, GRAY_BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    return story


def _build_avant_apres(actuel: list[str], apres: list[str], gain: str | None, styles: dict) -> list:
    """Two-column before/after comparison table."""
    if not actuel and not apres:
        return []
    story = []
    story.append(_section_header("📊  AVANT / APRÈS", BLUE_DARK, styles))
    story.append(Spacer(1, 4))

    col_w = CONTENT_W / 2 - 2

    # Header row
    header_row = [
        Paragraph("📉  Situation actuelle", styles["subsection"]),
        Paragraph("📈  Après actions", styles["subsection"]),
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

    # Gain potentiel — full width green row
    if gain:
        gain_cell = Paragraph(
            f'<font color="#15803D"><b>💥  GAIN POTENTIEL : </b></font>{_rl(gain)}',
            styles["body"]
        )
        tg = Table([[gain_cell]], colWidths=[CONTENT_W])
        tg.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GREEN_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 1, GREEN),
        ]))
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


def _build_projection(p3: list[str], p6: list[str], styles: dict) -> list:
    """Two-column 3-month / 6-month projection."""
    if not p3 and not p6:
        return []
    story = []
    story.append(_section_header("📅  PROJECTION TEMPORELLE", BLUE_DARK, styles))
    story.append(Spacer(1, 4))

    col_w = CONTENT_W / 2 - 2
    left_rows = [[Paragraph("3 MOIS", styles["proj_head"])]]
    for l in (p3 or ["Données insuffisantes"]):
        left_rows.append([Paragraph(_rl(l), styles["proj_body"])])
    right_rows = [[Paragraph("6 MOIS", styles["proj_head"])]]
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


# ─── Main generate function ───────────────────────────────────────────────────
def generate_pdf_report(result: dict) -> bytes:
    """
    Generate a V5 Premium Decision Engine PDF report.
    Returns PDF bytes.
    """
    buf = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=58 * mm,
        bottomMargin=20 * mm,
        title="Rapport Pepperyn V5",
        author="Pepperyn IA",
    )

    story: list[Any] = []

    # ── 0. FIABILITÉ DES DONNÉES ────────────────────────────────────────────
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
            [Paragraph("<b>Confiance analyse IA</b>", styles["body"]),
             Paragraph(f"<b>{score_ia}%</b>", styles["body"]),
             Paragraph("Qualité du raisonnement IA", styles["small"])],
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

    # ── 1. DIAGNOSTIC IMMÉDIAT (hero block) ─────────────────────────────────
    diag_imm = result.get("diagnostic_immediat", "")
    story.extend(_build_diagnostic_immediat(diag_imm, styles))

    # ── 2. RÉSUMÉ EXÉCUTIF ──────────────────────────────────────────────────
    resume = result.get("resume_executif") or result.get("synthese", "")
    story.extend(_build_resume_executif(resume, styles))

    # ── 3. SCORES /10 (4 scores) ────────────────────────────────────────────
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

    # ── 4. IMPACT FINANCIER ─────────────────────────────────────────────────
    impact = result.get("impact_financier") or []
    story.extend(_build_impact_financier(impact, styles))

    # ── 5. AVANT / APRÈS ────────────────────────────────────────────────────
    actuel = result.get("avant_apres_actuel") or []
    apres  = result.get("avant_apres_apres") or []
    gain   = result.get("avant_apres_gain")
    story.extend(_build_avant_apres(actuel, apres, gain, styles))

    # ── 6. SIMULATEUR DE DÉCISION ───────────────────────────────────────────
    sim = result.get("simulateur_decision") or []
    story.extend(_build_simulateur(sim, styles))

    # ── 7. PROJECTION TEMPORELLE ────────────────────────────────────────────
    p3 = result.get("projection_3mois") or []
    p6 = result.get("projection_6mois") or []
    story.extend(_build_projection(p3, p6, styles))

    # ── 8. CE QUI DÉTRUIT VOTRE RENTABILITÉ ─────────────────────────────────
    ce_qui_detruit = result.get("ce_qui_detruit") or []
    if ce_qui_detruit:
        story.append(_section_header("🔴  CE QUI DÉTRUIT VOTRE RENTABILITÉ", RED, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(ce_qui_detruit, "🔴", RED, RED_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 9. LEVIERS DE CROISSANCE ────────────────────────────────────────────
    leviers = result.get("leviers_croissance") or []
    if leviers:
        story.append(_section_header("🟢  LEVIERS DE CROISSANCE", GREEN, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(leviers, "🟢", GREEN, GREEN_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 10. PLAN D'ACTION ───────────────────────────────────────────────────
    actions = result.get("plan_action") or []
    if not actions:
        recs = result.get("recommandations", [])
        actions = [
            f"[{r.get('priorite','').upper()}] {r.get('action', '')}" for r in recs if isinstance(r, dict)
        ]
    if actions:
        story.append(_section_header(f"🎯  PLAN D'ACTION ({len(actions)} actions)", BLUE_MAIN, styles))
        story.append(Spacer(1, 3))
        for action in actions:
            clean = action.lstrip("🎯 ")
            is_haute = "priorité haute" in clean.lower() or "priorité: haute" in clean.lower()
            is_moy   = "priorité moyenne" in clean.lower() or "[MOY" in clean.upper()
            badge_color = "#DC2626" if is_haute else "#D97706" if is_moy else "#1B73E8"
            badge = "HAUTE" if is_haute else "MOY." if is_moy else "—"
            text = f'<font color="{badge_color}"><b>[{badge}]</b></font>  {_rl(clean)}'
            cell = Paragraph(text, styles["body"])
            t = Table([[cell]], colWidths=[CONTENT_W])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), BLUE_LIGHT),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                ("BOX",           (0, 0), (-1, -1), 0.5, BLUE_MAIN),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 8))

    # ── 11. SI RIEN NE CHANGE ───────────────────────────────────────────────
    risque_inaction = result.get("risque_inaction", "")
    story.extend(_build_risque_inaction(risque_inaction, styles))

    # ── 12. DÉCISION ────────────────────────────────────────────────────────
    decision = result.get("decision", "")
    if decision:
        story.append(_section_header("⚡  DÉCISION", BLUE_MAIN, styles))
        story.append(Spacer(1, 3))
        cell = Paragraph(_rl(decision), styles["decision"])
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BLUE_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("BOX",           (0, 0), (-1, -1), 1.5, BLUE_MAIN),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── 13. ÉVOLUTION VS ANALYSE PRÉCÉDENTE ─────────────────────────────────
    memory_insight = result.get("memory_insight", "")
    if memory_insight:
        story.append(_section_header("🔥  ÉVOLUTION VS ANALYSE PRÉCÉDENTE", AMBER, styles))
        story.append(Spacer(1, 3))
        story.append(Paragraph(_rl(memory_insight), styles["body"]))
        story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════════════
    # ANALYSE DÉTAILLÉE (sections techniques complètes)
    # ══════════════════════════════════════════════════════════════════════════
    has_detailed = any([
        result.get("diagnostic_revenus"),
        result.get("diagnostic_couts"),
        result.get("diagnostic_marges"),
        result.get("ce_qui_a_change"),
        result.get("alertes"),
        result.get("problemes_critiques"),
        result.get("opportunites_v3") or result.get("opportunites"),
    ])
    if has_detailed:
        story.extend(_build_separator_detailed(styles))

    # ── 14. DIAGNOSTIC FINANCIER ────────────────────────────────────────────
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

    # ── 15. CE QUI A CHANGÉ ─────────────────────────────────────────────────
    changements = result.get("ce_qui_a_change", [])
    if changements:
        story.append(_section_header("🔄  CE QUI A CHANGÉ", AMBER, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(changements, "🔄", AMBER, AMBER_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 16. ALERTES ─────────────────────────────────────────────────────────
    alertes = result.get("alertes", [])
    if alertes:
        story.append(_section_header(f"⚠️  ALERTES ({len(alertes)})", ORANGE, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(alertes, "⚠️", ORANGE, ORANGE_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 17. PROBLÈMES CRITIQUES ─────────────────────────────────────────────
    problemes = result.get("problemes_critiques", [])
    if problemes:
        story.append(_section_header(f"🔴  PROBLÈMES CRITIQUES ({len(problemes)})", RED, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(problemes, "🔴", RED, RED_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 18. OPPORTUNITÉS ────────────────────────────────────────────────────
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

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_header(c, d, result),
        onLaterPages=lambda c, d: _draw_header(c, d, result),
    )

    return buf.getvalue()
