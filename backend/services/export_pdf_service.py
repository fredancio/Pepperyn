"""
export_pdf_service.py
Génère un rapport PDF professionnel à partir d'un AnalysisResult v3.
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
    """
    Make text safe for reportlab Paragraph (XML parser).
    1. Strip ~~strikethrough~~ and audit artefacts
    2. Escape & < > for XML
    3. Convert **bold** and *italic* to reportlab markup
    """
    if not text:
        return ""
    # Strip markdown strikethrough
    text = _re.sub(r"~~.*?~~", "", text)
    # Strip leading emoji bullet chars
    text = text.strip()
    # Escape XML special chars FIRST (before adding markup tags)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Now convert **bold** → <b>…</b>  and  *italic* → <i>…</i>
    text = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = _re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    return text


# ─── Palette Pepperyn ────────────────────────────────────────────────────────
BLUE_DARK  = colors.HexColor("#0D47A1")
BLUE_MAIN  = colors.HexColor("#1B73E8")
BLUE_LIGHT = colors.HexColor("#EFF6FF")
RED        = colors.HexColor("#DC2626")
RED_LIGHT  = colors.HexColor("#FEF2F2")
AMBER      = colors.HexColor("#D97706")
AMBER_LIGHT= colors.HexColor("#FFFBEB")
ORANGE     = colors.HexColor("#EA580C")
ORANGE_LIGHT = colors.HexColor("#FFF7ED")
GREEN      = colors.HexColor("#15803D")
GREEN_LIGHT= colors.HexColor("#F0FDF4")
GRAY_TEXT  = colors.HexColor("#5F6368")
GRAY_BG    = colors.HexColor("#F8FAFC")
DARK       = colors.HexColor("#1A1A2E")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
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
        "bullet_blue": ParagraphStyle(
            "bullet_blue", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5,
            textColor=DARK, leading=13,
            leftIndent=10, firstLineIndent=0,
        ),
        "decision": ParagraphStyle(
            "decision", parent=base["Normal"],
            fontName="Helvetica-BoldOblique", fontSize=9.5,
            textColor=BLUE_DARK, leading=15,
        ),
        "header_title": ParagraphStyle(
            "header_title", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=20,
            textColor=WHITE, leading=26,
        ),
        "header_sub": ParagraphStyle(
            "header_sub", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#90CAF9"), leading=14,
        ),
        "score_label": ParagraphStyle(
            "score_label", parent=base["Normal"],
            fontName="Helvetica", fontSize=8,
            textColor=GRAY_TEXT, leading=12, alignment=TA_CENTER,
        ),
        "score_value": ParagraphStyle(
            "score_value", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=18,
            leading=22, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.5,
            textColor=GRAY_TEXT, alignment=TA_CENTER,
        ),
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _section_header(title: str, bg_color, styles: dict) -> Table:
    """Colored section header block."""
    cell = Paragraph(title, styles["section_title"])
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def _bullet_rows(items: list[str], icon: str, text_color, bg_color, styles: dict) -> list:
    """List of coloured rows for bullet items."""
    rows = []
    for item in items:
        clean = item.lstrip("🔴🟢⚠️🔄 ")
        cell = Paragraph(f"{icon}  {_rl(clean)}", styles["body"])
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, text_color),
        ]))
        rows.append(t)
        rows.append(Spacer(1, 2))
    return rows


def _score_table(scores: dict[str, int | None], styles: dict) -> Table:
    """3 score circles as a horizontal table."""
    score_data = [
        ("Rentabilité", scores.get("rentabilite")),
        ("Risque",      scores.get("risque")),
        ("Structure",   scores.get("structure")),
    ]
    cells = []
    for label, val in score_data:
        if val is None:
            cells.append("")
            continue
        color = "#15803D" if val >= 8 else "#D97706" if val >= 5 else "#DC2626"
        score_p = Paragraph(
            f'<font color="{color}"><b>{val}</b></font>',
            styles["score_value"],
        )
        label_p = Paragraph(label, styles["score_label"])
        inner = Table([[score_p], [label_p]], colWidths=[40 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(color)),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ]))
        cells.append(inner)

    valid_cells = [c for c in cells if c != ""]
    if not valid_cells:
        return Spacer(1, 1)

    col_w = CONTENT_W / len(valid_cells)
    t = Table([valid_cells], colWidths=[col_w] * len(valid_cells))
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
    # Blue gradient band
    canvas.setFillColor(BLUE_DARK)
    canvas.rect(0, PAGE_H - 52 * mm, PAGE_W, 52 * mm, fill=True, stroke=False)
    canvas.setFillColor(BLUE_MAIN)
    canvas.rect(0, PAGE_H - 52 * mm, PAGE_W * 0.6, 52 * mm, fill=True, stroke=False)

    # Title
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(MARGIN, PAGE_H - 22 * mm, "Rapport d'analyse financière")

    # Subtitle
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    doc_type = result.get("type_document", "Document financier")
    conf = result.get("score_confiance", 0)
    date_str = datetime.now().strftime("%d/%m/%Y")
    canvas.drawString(MARGIN, PAGE_H - 30 * mm, f"{doc_type}  ·  Confiance : {conf}%  ·  {date_str}")

    # Pepperyn badge
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 22 * mm, "Pepperyn")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 29 * mm, "Analyse IA · Niveau expert")

    # Footer
    canvas.setFillColor(GRAY_TEXT)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 10 * mm,
        f"Généré par Pepperyn — {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  Ce document est confidentiel"
    )
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# ─── Main generate function ───────────────────────────────────────────────────
def generate_pdf_report(result: dict) -> bytes:
    """
    Generate a PDF report from an analysis result dict (v3 format).
    Returns PDF bytes.
    """
    buf = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=58 * mm,    # leave room for header band
        bottomMargin=20 * mm,
        title="Rapport Pepperyn",
        author="Pepperyn IA",
    )

    story: list[Any] = []

    # ── 1. Résumé exécutif ──────────────────────────────────────────────────
    resume = result.get("resume_executif") or result.get("synthese", "")
    if resume:
        story.append(_section_header("📊  RÉSUMÉ EXÉCUTIF", BLUE_MAIN, styles))
        story.append(Spacer(1, 3))
        story.append(Paragraph(_rl(resume), styles["body"]))
        story.append(Spacer(1, 8))

    # ── 2. Diagnostic financier ─────────────────────────────────────────────
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

    # ── 3. Ce qui a changé ──────────────────────────────────────────────────
    changements = result.get("ce_qui_a_change", [])
    if changements:
        story.append(_section_header("🔄  CE QUI A CHANGÉ", AMBER, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(changements, "🔄", AMBER, AMBER_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 4. Alertes ──────────────────────────────────────────────────────────
    alertes = result.get("alertes", [])
    if alertes:
        story.append(_section_header(f"⚠️  ALERTES ({len(alertes)})", ORANGE, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(alertes, "⚠️", ORANGE, ORANGE_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 5. Problèmes critiques ──────────────────────────────────────────────
    problemes = result.get("problemes_critiques", [])
    if problemes:
        story.append(_section_header(f"🔴  PROBLÈMES CRITIQUES ({len(problemes)})", RED, styles))
        story.append(Spacer(1, 3))
        story.extend(_bullet_rows(problemes, "🔴", RED, RED_LIGHT, styles))
        story.append(Spacer(1, 8))

    # ── 6. Opportunités ─────────────────────────────────────────────────────
    opportunites = result.get("opportunites_v3") or result.get("opportunites", [])
    if opportunites:
        # opportunites_v3 is list[str], opportunites (old) is list[dict]
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

    # ── 7. Plan d'action ────────────────────────────────────────────────────
    actions = result.get("plan_action") or []
    if not actions:
        # fallback old format
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
                ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, BLUE_MAIN),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 8))

    # ── 8. Scores /10 ───────────────────────────────────────────────────────
    scores = {
        "rentabilite": result.get("score_rentabilite"),
        "risque":      result.get("score_risque"),
        "structure":   result.get("score_structure"),
    }
    if any(v is not None for v in scores.values()):
        story.append(_section_header("📈  SCORES /10", BLUE_DARK, styles))
        story.append(Spacer(1, 6))
        story.append(_score_table(scores, styles))
        story.append(Spacer(1, 8))

    # ── 9. Décision ─────────────────────────────────────────────────────────
    decision = result.get("decision", "")
    if decision:
        story.append(_section_header("⚡  DÉCISION", BLUE_MAIN, styles))
        story.append(Spacer(1, 3))
        cell = Paragraph(_rl(decision), styles["decision"])
        t = Table([[cell]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("BOX", (0, 0), (-1, -1), 1.5, BLUE_MAIN),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── 10. Memory insight ──────────────────────────────────────────────────
    memory_insight = result.get("memory_insight", "")
    if memory_insight:
        story.append(_section_header("🔥  ÉVOLUTION VS ANALYSE PRÉCÉDENTE", AMBER, styles))
        story.append(Spacer(1, 3))
        story.append(Paragraph(_rl(memory_insight), styles["body"]))
        story.append(Spacer(1, 8))

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_header(c, d, result),
        onLaterPages=lambda c, d: _draw_header(c, d, result),
    )

    return buf.getvalue()
