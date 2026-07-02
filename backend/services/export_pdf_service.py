"""
export_pdf_service.py — Rapport exécutif Pepperyn
Layout CEO Question Framework (v3 — Jour 2 sprint McKinsey)

RÈGLE : chaque page répond à UNE seule question naturelle d'un CEO.
Pages sans question CEO → supprimées.

Structure — 11 pages :
  Cover   Couverture
  P1  "Dois-je m'inquiéter ?"         → VERDICT EXÉCUTIF
  P2  "Pourquoi ?"                     → OÙ VOTRE CAPITAL EST SOUS-EMPLOYÉ
  P3  "Combien cela me coûte ?"        → COÛT DE L'INACTION + SIMULATION
  P4  "Que dois-je faire ?"            → DÉCISIONS PRIORITAIRES
  P5  "Pourquoi cette décision ?"      → COMMENT PEPPERYN A RAISONNÉ
  P6  "Combien vais-je gagner ?"       → VALEUR CRÉÉE SI VOUS AGISSEZ
  P7  "Dans quel ordre, qui fait quoi?" → CALENDRIER D'ALLOCATION 30/60/90
  P8  "Et si je me trompe ?"           → 3 SCÉNARIOS
  P9  "Quels sont les risques ?"       → RISQUES À SURVEILLER
  P10 "Comment vais-je mesurer ?"      → MES KPIs DE PILOTAGE

Decision Density Score cible : ≥ 0,5 décision par élément de données.
Feature Filter : chaque page aide le CEO à mieux allouer les ressources
                 qui créent ou protègent durablement la valeur.
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
pt = 1.0  # 1 point = unité de base ReportLab
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Line, String as RLString, Rect
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from services.executive_decision_model import build_executive_decision_model
from models.executive_case import ExecutiveCaseJSON

# ─── PALETTE ─────────────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor("#0A2540")   # fond boîte dark, titre couverture
C_BLUE   = colors.HexColor("#1B73E8")   # accents principaux, bordures section
C_RED    = colors.HexColor("#C0392B")   # urgence, score critique
C_AMBER  = colors.HexColor("#B8763A")   # estimations, priorité moyenne
C_GREEN  = colors.HexColor("#2C7A4B")   # "avec action", confiance haute
C_GRAY   = colors.HexColor("#8A9BB0")   # textes secondaires, labels
C_LGRAY  = colors.HexColor("#D5DCE5")   # filets, bordures légères
C_WHITE  = colors.white
C_DARK   = colors.HexColor("#1A1A2E")   # corps de texte principal
C_LBGRAY = colors.HexColor("#F5F7FA")   # fond clair pour tableaux alternés

HEX_RED   = "#C0392B"
HEX_AMBER = "#B8763A"
HEX_BLUE  = "#1B73E8"
HEX_NAVY  = "#0A2540"
HEX_GRAY  = "#8A9BB0"
HEX_GREEN = "#2C7A4B"

# ─── LAYOUT A4 ────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4               # 595 × 842 pts
MARGIN         = 18 * mm          # 51 pts
CONTENT_W      = PAGE_W - 2 * MARGIN
HEADER_Y       = PAGE_H - 14 * mm
FOOTER_Y       = 9 * mm
CONTENT_TOP    = HEADER_Y - 8 * mm


# ─── FORMATAGE NUMÉRIQUE ──────────────────────────────────────────────────────

def _fmt_eur(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = ("-" if v < 0 else ("+" if sign and v > 0 else ""))
    s = f"{abs_v:,.0f}".replace(",", " ")
    return f"{prefix}{s} €"


def _fmt_millions(v: Optional[float]) -> str:
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    m = abs_v / 1_000_000
    if m >= 10:
        return f"{prefix}{m:.0f} M€"
    return f"{prefix}{m:.1f} M€".replace(".", ",")


def _fmt_auto(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "Données insuffisantes"
    if abs(v) >= 950_000:
        raw = _fmt_millions(v)
        if sign and v > 0:
            raw = "+" + raw
        return raw
    return _fmt_eur(v, sign=sign)


def _safe(v, fallback: str = "Données insuffisantes") -> str:
    if v is None or v == "" or (isinstance(v, (int, float)) and v == 0):
        return fallback
    return str(v)


def _parse_float(s) -> Optional[float]:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    cleaned = re.sub(r"[€\s ]", "", str(s)).replace(",", ".").strip()
    try:
        if cleaned.upper().endswith("M"):
            return float(cleaned[:-1]) * 1_000_000
        if cleaned.upper().endswith("K"):
            return float(cleaned[:-1]) * 1_000
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _rl(text: str) -> str:
    """Échappe le HTML pour ReportLab et convertit le markdown basique."""
    if not text:
        return ""
    text = text.strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


# ─── STYLES ───────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    S = {}

    def ps(name, parent="Normal", **kw):
        S[name] = ParagraphStyle(name, parent=base[parent], **kw)

    ps("cover_label",  fontName="Helvetica",      fontSize=9,  textColor=C_GRAY,  alignment=TA_CENTER, leading=14)
    ps("cover_title",  fontName="Helvetica-Bold", fontSize=38, textColor=C_NAVY,  alignment=TA_CENTER, leading=46, spaceAfter=4)
    ps("cover_sub",    fontName="Helvetica",      fontSize=14, textColor=C_GRAY,  alignment=TA_CENTER, leading=20)
    ps("cover_meta_k", fontName="Helvetica",      fontSize=8,  textColor=C_BLUE,  leading=14)
    ps("cover_meta_v", fontName="Helvetica-Bold", fontSize=10, textColor=C_DARK,  leading=14)
    ps("cover_brand",  fontName="Helvetica-Bold", fontSize=10, textColor=C_BLUE,  alignment=TA_CENTER, leading=14)
    ps("cover_conf",   fontName="Helvetica",      fontSize=8,  textColor=C_GRAY,  alignment=TA_CENTER, leading=12)

    ps("ceo_q",        fontName="Helvetica-Oblique", fontSize=8, textColor=C_GRAY, leading=12, spaceAfter=2)
    ps("section_title",fontName="Helvetica-Bold", fontSize=14, textColor=C_DARK,  leading=18, leftIndent=8)

    ps("hero_xl",   fontName="Helvetica-Bold", fontSize=62, textColor=C_RED,   alignment=TA_LEFT, leading=70)
    ps("hero_xl_g", fontName="Helvetica-Bold", fontSize=62, textColor=C_GREEN, alignment=TA_LEFT, leading=70)
    ps("hero_xl_b", fontName="Helvetica-Bold", fontSize=62, textColor=C_BLUE,  alignment=TA_LEFT, leading=70)
    ps("hero_l",    fontName="Helvetica-Bold", fontSize=36, textColor=C_DARK,  alignment=TA_LEFT, leading=44)
    ps("hero_m",    fontName="Helvetica-Bold", fontSize=24, textColor=C_DARK,  alignment=TA_LEFT, leading=30)
    ps("hero_label",fontName="Helvetica",      fontSize=8,  textColor=C_RED,   alignment=TA_LEFT, leading=11, spaceAfter=0)
    ps("hero_label_g",fontName="Helvetica",    fontSize=8,  textColor=C_GREEN, alignment=TA_LEFT, leading=11, spaceAfter=0)
    ps("hero_label_b",fontName="Helvetica",    fontSize=8,  textColor=C_BLUE,  alignment=TA_LEFT, leading=11, spaceAfter=0)

    ps("kpi_val_red",  fontName="Helvetica-Bold", fontSize=18, textColor=C_RED,   alignment=TA_CENTER, leading=22)
    ps("kpi_val_blue", fontName="Helvetica-Bold", fontSize=18, textColor=C_BLUE,  alignment=TA_CENTER, leading=22)
    ps("kpi_val_g",    fontName="Helvetica-Bold", fontSize=18, textColor=C_GREEN, alignment=TA_CENTER, leading=22)
    ps("kpi_lbl",      fontName="Helvetica",      fontSize=7,  textColor=C_GRAY,  alignment=TA_CENTER, leading=10)

    ps("dim_score",  fontName="Helvetica-Bold", fontSize=22, textColor=C_DARK, alignment=TA_CENTER, leading=28)
    ps("dim_label",  fontName="Helvetica",      fontSize=9,  textColor=C_GRAY, alignment=TA_CENTER, leading=13)

    ps("indic_val",  fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK, alignment=TA_CENTER, leading=18)
    ps("indic_lbl",  fontName="Helvetica",      fontSize=8,  textColor=C_GRAY, alignment=TA_CENTER, leading=11)
    ps("indic_miss", fontName="Helvetica-Bold", fontSize=11, textColor=C_GRAY, alignment=TA_CENTER, leading=15)

    ps("diag_label", fontName="Helvetica-Bold", fontSize=8,  textColor=C_AMBER, leading=12, spaceAfter=4)
    ps("body",       fontName="Helvetica",      fontSize=11, textColor=C_DARK,  leading=16, spaceAfter=4)
    ps("body_bold",  fontName="Helvetica-Bold", fontSize=11, textColor=C_DARK,  leading=16, spaceAfter=4)
    ps("body_small", fontName="Helvetica",      fontSize=9,  textColor=C_GRAY,  leading=13, spaceAfter=2)
    ps("quote",      fontName="Helvetica-Oblique", fontSize=10, textColor=C_GRAY, leading=15, leftIndent=10)

    ps("prio_score", fontName="Helvetica-Bold", fontSize=11, textColor=C_DARK, leading=15)
    ps("tbl_hdr",    fontName="Helvetica-Bold", fontSize=9,  textColor=C_DARK, leading=13)
    ps("tbl_cell",   fontName="Helvetica",      fontSize=10, textColor=C_DARK, leading=14)
    ps("tbl_impact", fontName="Helvetica-Bold", fontSize=14, textColor=C_BLUE, leading=18, alignment=TA_LEFT)
    ps("tbl_impact_g",fontName="Helvetica-Bold",fontSize=14, textColor=C_GREEN,leading=18, alignment=TA_LEFT)
    ps("tbl_prio_r", fontName="Helvetica-Bold", fontSize=10, textColor=C_RED,   leading=14)
    ps("tbl_prio_a", fontName="Helvetica-Bold", fontSize=10, textColor=C_AMBER, leading=14)
    ps("tbl_prio_g", fontName="Helvetica",      fontSize=10, textColor=C_GRAY,  leading=14)

    ps("scen_head_g",fontName="Helvetica-Bold", fontSize=9, textColor=C_GREEN, leading=13)
    ps("scen_head_b",fontName="Helvetica-Bold", fontSize=9, textColor=C_BLUE,  leading=13)
    ps("scen_head_r",fontName="Helvetica-Bold", fontSize=9, textColor=C_RED,   leading=13)
    ps("scen_body",  fontName="Helvetica",      fontSize=9, textColor=C_DARK,  leading=13)

    ps("risk_sev_r", fontName="Helvetica-Bold", fontSize=8, textColor=C_RED,   leading=12, alignment=TA_CENTER)
    ps("risk_sev_a", fontName="Helvetica-Bold", fontSize=8, textColor=C_AMBER, leading=12, alignment=TA_CENTER)
    ps("risk_sev_g", fontName="Helvetica-Bold", fontSize=8, textColor=C_GRAY,  leading=12, alignment=TA_CENTER)

    ps("chart_caption",fontName="Helvetica-Oblique",fontSize=9,textColor=C_GRAY,leading=13,spaceAfter=4)

    return S


# ─── CANVAS : HEADER / FOOTER ─────────────────────────────────────────────────

def _draw_header_footer(canvas, doc, doc_type: str, date_str: str) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(C_BLUE)
    canvas.drawString(MARGIN, HEADER_Y, "RAPPORT EXÉCUTIF")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(C_GRAY)
    canvas.drawRightString(PAGE_W - MARGIN, HEADER_Y, f"{doc_type}  ·  {date_str}")

    canvas.setStrokeColor(C_LGRAY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, HEADER_Y - 3 * mm, PAGE_W - MARGIN, HEADER_Y - 3 * mm)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(MARGIN, FOOTER_Y, "Document confidentiel")
    canvas.drawRightString(PAGE_W - MARGIN, FOOTER_Y, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# ─── COMPOSANTS RÉUTILISABLES ─────────────────────────────────────────────────

def _section_header(title: str, styles: dict, ceo_question: str = "", bar_color=None) -> list:
    """Titre de section avec question CEO et barre colorée."""
    if bar_color is None:
        bar_color = C_BLUE
    items = []
    if ceo_question:
        items.append(Paragraph(f'<i>{_rl(ceo_question)}</i>', styles["ceo_q"]))
    bar = Table([[""]], colWidths=[3 * mm], rowHeights=[22])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bar_color),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    title_p = Paragraph(title, styles["section_title"])
    t = Table([[bar, title_p]], colWidths=[5 * mm, CONTENT_W - 5 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    items.append(t)
    return items


def _hr(color=None, thickness: float = 0.5) -> HRFlowable:
    if color is None:
        color = C_LGRAY
    return HRFlowable(width=CONTENT_W, color=color, thickness=thickness, spaceAfter=0)


def _sp(h: float) -> Spacer:
    return Spacer(1, h * mm)


def _dark_box(inner_table, styles: dict, bg=None) -> Table:
    """Boîte fond navy pour hero metrics."""
    bg = bg or C_NAVY
    t = Table([[inner_table]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6 * mm),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _quote_box(text: str, styles: dict, bar_color=None) -> Table:
    bar_color = bar_color or C_BLUE
    q = Table(
        [[Paragraph(_rl(text), styles["quote"])]],
        colWidths=[CONTENT_W - 8 * mm],
    )
    q.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBEFORETABLE", (0, 0), (0, -1), 3, bar_color),
    ]))
    return q


# ─── GRAPHIQUES LIGNE ─────────────────────────────────────────────────────────

def _line_chart_two(series_a, series_b, width, height, y_min, y_max):
    d = Drawing(width, height)
    lc = HorizontalLineChart()
    lc.x = 38; lc.y = 24
    lc.width = width - 50; lc.height = height - 36
    lc.data = [series_a, series_b]
    lc.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(series_a))]
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.fontSize = 7
    lc.categoryAxis.labels.fontName = "Helvetica"
    lc.valueAxis.valueMin = y_min; lc.valueAxis.valueMax = y_max
    lc.valueAxis.valueStep = (y_max - y_min) / 4
    lc.valueAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontName = "Helvetica"
    lc.lines[0].strokeColor = C_GREEN; lc.lines[0].strokeWidth = 2
    lc.lines[1].strokeColor = C_RED;   lc.lines[1].strokeWidth = 2
    lc.lines[0].symbol = None; lc.lines[1].symbol = None
    d.add(lc)
    return d


# ─── PAGE COVER ───────────────────────────────────────────────────────────────

def _build_cover(company_name: str, date_str: str, styles: dict) -> list:
    s = []
    s.append(_sp(35))
    s.append(Paragraph("VERSION CONFIDENTIELLE", styles["cover_label"]))
    s.append(_sp(6))
    s.append(Paragraph("Rapport exécutif", styles["cover_title"]))
    s.append(_sp(2))
    s.append(Paragraph("Prévisionnel", styles["cover_sub"]))
    s.append(_sp(55))

    meta = [
        ["PRÉPARÉ POUR", company_name or "—"],
        ["PRÉPARÉ PAR",  "Pepperyn Financial Control Center"],
        ["DATE",         date_str],
    ]
    meta_table = Table(
        [[Paragraph(k, styles["cover_meta_k"]), Paragraph(v, styles["cover_meta_v"])]
         for k, v in meta],
        colWidths=[45 * mm, CONTENT_W - 45 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    s.append(meta_table)
    s.append(_sp(30))
    s.append(_hr(C_LGRAY, thickness=0.5))
    s.append(_sp(4))
    s.append(Paragraph("Pepperyn", styles["cover_brand"]))
    s.append(_sp(2))
    s.append(Paragraph("Document confidentiel — usage interne réservé à la direction", styles["cover_conf"]))
    s.append(PageBreak())
    return s


# ─── P1 : "DOIS-JE M'INQUIÉTER ?" — VERDICT EXÉCUTIF ────────────────────────

def _build_page_verdict(result: dict, edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "VERDICT EXÉCUTIF",
        styles,
        ceo_question="Dois-je m'inquiéter ?"
    ))
    s.append(_hr())
    s.append(_sp(5))

    score = result.get("score_global")
    niveau = result.get("niveau_urgence") or ""
    tension = result.get("phrase_tension") or ""
    diag = result.get("diagnostic_immediat") or result.get("resume_executif") or ""
    conf = result.get("score_confiance")
    coi = edm.cost_of_inaction

    # ── Colonne gauche : score hero + COI semaine ─────────────────────────────
    # Score color
    if score is None:
        score_hex, score_str = HEX_GRAY, "N/A"
    elif score <= 3:
        score_hex, score_str = HEX_RED, str(score)
    elif score <= 5:
        score_hex, score_str = HEX_AMBER, str(score)
    elif score <= 7:
        score_hex, score_str = HEX_BLUE, str(score)
    else:
        score_hex, score_str = HEX_GREEN, str(score)

    score_p = Paragraph(
        f'<font color="{score_hex}" size="52"><b>{score_str}</b></font>'
        f'<font color="{HEX_GRAY}" size="28"><b>/10</b></font>',
        ParagraphStyle("verd_s", fontName="Helvetica-Bold", fontSize=52, leading=62)
    )
    score_lbl = Paragraph("INDICE DE SANTÉ GLOBALE", ParagraphStyle(
        "verd_sl", fontName="Helvetica-Bold", fontSize=7,
        textColor=colors.HexColor(score_hex), leading=10
    ))

    # COI hebdomadaire hero secondaire
    weekly_str = _fmt_eur(abs(coi.per_week)) if coi and coi.per_week else "—"
    coi_p = Paragraph(
        f'<font color="{HEX_RED}"><b>{weekly_str}</b></font>',
        ParagraphStyle("verd_c", fontName="Helvetica-Bold", fontSize=22, leading=28)
    )
    coi_lbl = Paragraph("COÛT DE L'INACTION PAR SEMAINE", ParagraphStyle(
        "verd_cl", fontName="Helvetica", fontSize=7,
        textColor=C_RED, leading=10
    ))

    left_col = Table([
        [score_p],
        [score_lbl],
        [_sp(4)],
        [coi_p],
        [coi_lbl],
    ], colWidths=[CONTENT_W * 0.42])
    left_col.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    # ── Colonne droite : urgence + diagnostic + 4 scores dimension ────────────
    urgency_style = ParagraphStyle(
        "urg", fontName="Helvetica-Bold", fontSize=10,
        textColor=C_DARK if not niveau else (
            C_RED if "critiq" in niveau.lower() else
            C_AMBER if "élevé" in niveau.lower() or "eleve" in niveau.lower() else C_BLUE
        ),
        leading=14
    )

    right_items = []
    if niveau:
        # Badge urgence
        urg_bg = (C_RED if "critiq" in niveau.lower()
                  else C_AMBER if "élevé" in niveau.lower() or "eleve" in niveau.lower()
                  else C_BLUE)
        badge_inner = Table([[Paragraph(
            niveau.upper(),
            ParagraphStyle("ub", fontName="Helvetica-Bold", fontSize=9,
                           textColor=C_WHITE, leading=13)
        )]], colWidths=[CONTENT_W * 0.52])
        badge_inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), urg_bg),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [3]),
        ]))
        right_items.append(badge_inner)
        right_items.append(_sp(4))

    if tension:
        right_items.append(Paragraph(f'<b>"{_rl(tension)}"</b>', ParagraphStyle(
            "ten", fontName="Helvetica-Bold-Oblique", fontSize=11,
            textColor=C_DARK, leading=16
        )))
        right_items.append(_sp(4))

    if diag:
        lines = [l.strip() for l in diag.split("\n") if l.strip()]
        if lines:
            right_items.append(Paragraph(_rl(lines[0]), ParagraphStyle(
                "diag_r", fontName="Helvetica", fontSize=9.5,
                textColor=C_DARK, leading=14
            )))

    # 4 scores dimension
    d_rentab   = result.get("score_rentabilite")
    d_risque   = result.get("score_risque")
    d_struct   = result.get("score_structure")
    d_liquid   = result.get("score_liquidite")

    right_items.append(_sp(5))

    def _dim_cell(label, val):
        if val is None:
            v_str, v_hex = "N/A", HEX_GRAY
        elif val <= 3:
            v_str, v_hex = f"{val}/10", HEX_RED
        elif val <= 5:
            v_str, v_hex = f"{val}/10", HEX_AMBER
        else:
            v_str, v_hex = f"{val}/10", HEX_BLUE
        inner = Table([
            [Paragraph(f'<font color="{v_hex}"><b>{v_str}</b></font>',
                       ParagraphStyle("dc", fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=1))],
            [Paragraph(label, ParagraphStyle("dl", fontName="Helvetica", fontSize=7,
                                              textColor=C_GRAY, leading=10, alignment=1))],
        ], colWidths=[CONTENT_W * 0.13 - 2 * mm])
        inner.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOX", (0, 0), (-1, -1), 0.5, C_LGRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        return inner

    dim_row = Table([[
        _dim_cell("Rentab.", d_rentab),
        _dim_cell("Risque",  d_risque),
        _dim_cell("Structure", d_struct),
        _dim_cell("Liquidité", d_liquid),
    ]], colWidths=[CONTENT_W * 0.13] * 4)
    dim_row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    right_items.append(dim_row)

    # Confiance Pepperyn
    if conf:
        right_items.append(_sp(4))
        right_items.append(Paragraph(
            f'Confiance de l\'analyse : <font color="{HEX_GREEN}"><b>{conf}%</b></font>',
            ParagraphStyle("cfr", fontName="Helvetica", fontSize=8.5,
                           textColor=C_GRAY, leading=13)
        ))

    right_col = Table([[r] for r in right_items], colWidths=[CONTENT_W * 0.55])
    right_col.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    two_cols = Table([[left_col, right_col]], colWidths=[CONTENT_W * 0.43, CONTENT_W * 0.57])
    two_cols.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(two_cols)
    s.append(PageBreak())
    return s


# ─── P2 : "POURQUOI ?" — OÙ VOTRE CAPITAL EST SOUS-EMPLOYÉ ──────────────────

def _build_page_capital(edm, result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "OÙ VOTRE CAPITAL EST SOUS-EMPLOYÉ",
        styles,
        ceo_question="Pourquoi ?"
    ))
    s.append(_hr())
    s.append(_sp(6))

    destroyers = edm.value_destroyers[:5]

    # Total valeur identifiée
    total_ann = sum(
        abs(d.annual_impact) for d in destroyers if d.annual_impact
    )

    if total_ann:
        hero_text = _fmt_auto(total_ann)
        hero_lbl = "DE VALEUR IDENTIFIÉE À LIBÉRER"
        inner = Table([
            [Paragraph("POTENTIEL TOTAL IDENTIFIÉ", ParagraphStyle(
                "pti", fontName="Helvetica-Bold", fontSize=8,
                textColor=colors.HexColor("#AABBCC"), leading=12))],
            [_sp(2)],
            [Paragraph(hero_text, ParagraphStyle(
                "pti_v", fontName="Helvetica-Bold", fontSize=30,
                textColor=C_GREEN, leading=36))],
            [_sp(2)],
            [Paragraph(hero_lbl, ParagraphStyle(
                "pti_l", fontName="Helvetica-Oblique", fontSize=9,
                textColor=colors.HexColor("#8899AA"), leading=13))],
        ], colWidths=[CONTENT_W - 12 * mm])
        inner.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        s.append(_dark_box(inner, styles))
        s.append(_sp(8))

    # Table des leviers
    if not destroyers:
        s.append(Paragraph("Leviers non identifiés — données sources insuffisantes.", styles["body_small"]))
        s.append(PageBreak())
        return s

    headers = ["Levier d'optimisation", "Potentiel annuel", "Potentiel mensuel", "Tendance"]
    col_w = [CONTENT_W * 0.42, CONTENT_W * 0.22, CONTENT_W * 0.20, CONTENT_W * 0.16]
    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

    for i, d in enumerate(destroyers):
        ann_str = _fmt_auto(abs(d.annual_impact), sign=False) if d.annual_impact else "—"
        mon_str = _fmt_eur(abs(d.monthly_impact)) if d.monthly_impact else "—"
        data.append([
            Paragraph(_rl(d.name), styles["tbl_cell"]),
            Paragraph(ann_str, styles["tbl_impact_g"]),
            Paragraph(mon_str, styles["tbl_cell"]),
            Paragraph(d.trend or "→", styles["tbl_cell"]),
        ])

    tbl = Table(data, colWidths=col_w)
    cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.8, C_LGRAY),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_LBGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)
    s.append(_sp(6))

    # Diagnostic narratif (pourquoi ces leviers)
    diag = result.get("diagnostic_immediat") or result.get("resume_executif") or ""
    if diag:
        lines = [l.strip() for l in diag.split("\n") if l.strip()]
        if len(lines) > 1:
            s.append(_hr())
            s.append(_sp(4))
            s.append(Paragraph(_rl(lines[0]), styles["body_small"]))

    s.append(PageBreak())
    return s


# ─── P3 : "COMBIEN CELA ME COÛTE ?" — COI + SIMULATION ──────────────────────

def _build_page_coi(edm, result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "LE COÛT DE L'INACTION",
        styles,
        ceo_question="Combien cela me coûte de ne rien faire ?"
    ))
    s.append(_hr())
    s.append(_sp(5))

    coi = edm.cost_of_inaction
    annual = coi.per_year if coi else None

    # ── Hero annuel ───────────────────────────────────────────────────────────
    hero_text = _fmt_auto(annual) if annual else "—"
    s.append(Paragraph(hero_text, styles["hero_xl"]))
    s.append(_sp(1))
    s.append(Paragraph("PAR AN, SI RIEN NE CHANGE", styles["hero_label"]))
    s.append(_sp(5))
    s.append(_hr(C_RED, thickness=1.5))
    s.append(_sp(5))

    # ── 4 sous-métriques ──────────────────────────────────────────────────────
    vals = [
        (_fmt_eur(coi.per_month  if coi and coi.per_month  else None), "PAR MOIS"),
        (_fmt_eur(coi.per_week   if coi and coi.per_week   else None), "PAR SEMAINE"),
        (_fmt_eur(coi.per_day    if coi and coi.per_day    else None), "PAR JOUR"),
        (_fmt_eur(coi.per_hour   if coi and coi.per_hour   else None), "PAR HEURE"),
    ]
    kpi_data = [[
        Table([[Paragraph(v, styles["kpi_val_red"])], [Paragraph(l, styles["kpi_lbl"])]])
        for v, l in vals
    ]]
    kpi_t = Table(kpi_data, colWidths=[CONTENT_W / 4] * 4)
    kpi_t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    s.append(kpi_t)
    s.append(_sp(5))

    # ── Phrase d'urgence ──────────────────────────────────────────────────────
    risque = result.get("risque_inaction")
    if risque:
        s.append(_quote_box(f"Si rien ne change : {risque}", styles, C_RED))
        s.append(_sp(4))

    s.append(_hr())
    s.append(_sp(4))

    # ── Simulation graphique action vs inaction ────────────────────────────────
    series_a = edm.action_series or []
    series_b = edm.do_nothing_series or []

    has_chart = (
        len(series_a) == 12 and len(series_b) == 12
        and any(v != 0 for v in series_a)
        and any(v != 0 for v in series_b)
    )

    s.append(Paragraph("AGIR OU NE RIEN FAIRE ?", ParagraphStyle(
        "sim_hdr", fontName="Helvetica-Bold", fontSize=8.5,
        textColor=C_GRAY, leading=13, spaceAfter=3
    )))

    if has_chart:
        y_min_v = min(min(series_b), 0)
        y_max_v = max(max(series_a), 0)
        range_v = max(abs(y_min_v), abs(y_max_v), 1_000_000)
        ceil_m = (int(range_v / 1_000_000) + 1) * 1_000_000
        chart = _line_chart_two(series_a, series_b, CONTENT_W, 52 * mm,
                                -ceil_m, ceil_m)
        s.append(chart)
        s.append(_sp(1))
        leg_data = [[
            Paragraph('<font color="#2C7A4B"><b>■</b></font>  Avec action', styles["body_small"]),
            Paragraph('<font color="#C0392B"><b>■</b></font>  Sans action',  styles["body_small"]),
        ]]
        leg_t = Table(leg_data, colWidths=[CONTENT_W / 2, CONTENT_W / 2])
        leg_t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        s.append(leg_t)
    else:
        s.append(Paragraph("Séries de projection non disponibles.", styles["body_small"]))

    s.append(PageBreak())
    return s


# ─── P4 : "QUE DOIS-JE FAIRE ?" — DÉCISIONS PRIORITAIRES ────────────────────

def _build_page_decisions(edm, styles: dict, result_dict: dict | None = None) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "DÉCISIONS PRIORITAIRES",
        styles,
        ceo_question="Que dois-je faire ?"
    ))
    s.append(_hr())
    s.append(_sp(4))

    score = edm.executive_decisions_score if edm.executive_decisions_score else 0.0
    s.append(Paragraph(
        f"Score de priorisation global  <font color='{HEX_BLUE}'><b>{score:.1f}/10</b></font>",
        styles["prio_score"]
    ))
    s.append(_sp(4))

    headers = ["Décision prioritaire", "Potentiel annuel", "ROI", "Délai", "Difficulté", "Priorité"]
    col_w = [CONTENT_W * 0.33, CONTENT_W * 0.16, CONTENT_W * 0.10,
             CONTENT_W * 0.12, CONTENT_W * 0.12, CONTENT_W * 0.17]

    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

    def _prio_p(prio):
        if not prio or prio in ("Not evaluated", "Non évaluée"):
            return Paragraph("Non évaluée", styles["tbl_prio_g"])
        if "high" in prio.lower() or "élevé" in prio.lower():
            return Paragraph(prio, styles["tbl_prio_r"])
        return Paragraph(prio, styles["tbl_prio_a"])

    decisions = edm.executive_decisions[:10]
    if not decisions:
        data.append([Paragraph("Données insuffisantes", styles["tbl_cell"]), "", "", "", "", ""])
    else:
        for dec in decisions:
            impact_str = (_fmt_eur(dec.annual_impact, sign=True)
                          if dec.annual_impact else "—")
            roi_str = f"{dec.roi_score:.1f}/10" if dec.roi_score else "—"
            data.append([
                Paragraph(_rl(dec.decision), styles["tbl_cell"]),
                Paragraph(impact_str, styles["tbl_impact_g"]),
                Paragraph(roi_str, styles["tbl_cell"]),
                Paragraph(dec.timeline or "—", styles["tbl_cell"]),
                Paragraph(dec.difficulty or "—", styles["tbl_cell"]),
                _prio_p(dec.priority),
            ])

    tbl = Table(data, colWidths=col_w)
    cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.8, C_LGRAY),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)
    s.append(PageBreak())
    return s


# ─── P5 : "POURQUOI CETTE DÉCISION ?" — RAISONNEMENT COMPARATIF (EDX-002) ───

def _build_page_reasoning(edm, styles: dict, result_dict: dict | None = None) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "COMMENT PEPPERYN A RAISONNÉ",
        styles,
        ceo_question="Pourquoi cette décision et pas une autre ?"
    ))
    s.append(_hr())
    s.append(_sp(4))

    reasoning_list = (result_dict or {}).get("decision_reasoning", [])
    decisions = edm.executive_decisions[:5]

    if not reasoning_list or not decisions:
        s.append(Paragraph(
            "Le raisonnement comparatif sera disponible à l'activation du module EDX-002.",
            styles["body_small"]
        ))
        s.append(PageBreak())
        return s

    dec_hdr_style = ParagraphStyle(
        "r_dec", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.HexColor(HEX_BLUE), leading=13, spaceBefore=6,
    )
    val_style = ParagraphStyle(
        "r_val", fontName="Helvetica", fontSize=8.5,
        textColor=colors.HexColor("#222222"), leading=12, spaceAfter=2,
    )
    conf_style = ParagraphStyle(
        "r_conf", fontName="Helvetica-Oblique", fontSize=8,
        textColor=C_GRAY, leading=11, spaceAfter=3,
    )
    opt_hdr_style = ParagraphStyle(
        "r_oh", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.HexColor("#555555"), leading=12, spaceBefore=4,
    )
    opt_item_style = ParagraphStyle(
        "r_oi", fontName="Helvetica", fontSize=8,
        textColor=colors.HexColor("#333333"), leading=11, leftIndent=8,
    )
    elim_style = ParagraphStyle(
        "r_el", fontName="Helvetica-Oblique", fontSize=8,
        textColor=C_GRAY, leading=11, leftIndent=16, spaceAfter=2,
    )
    tipping_style = ParagraphStyle(
        "r_tip", fontName="Helvetica", fontSize=8,
        textColor=colors.HexColor("#555555"), leading=11, leftIndent=8, spaceAfter=2,
    )

    reasoning_by_idx = {r["decision_index"]: r for r in reasoning_list}

    for i, dec in enumerate(decisions):
        r = reasoning_by_idx.get(i, {})
        why        = r.get("why_this_decision")
        prob       = r.get("problem_source")
        risk       = r.get("inaction_risk")
        conf       = r.get("decision_confidence")
        conf_expl  = r.get("confidence_explanation")
        match_conf = r.get("matching_confidence", "")
        options    = r.get("options_considered") or []
        dominant   = r.get("dominant_rationale")
        tippings   = r.get("tipping_conditions") or []

        if not why and not prob and not options:
            continue

        s.append(Paragraph(
            f"<b>#{i + 1} — {_rl(dec.decision)}</b>", dec_hdr_style
        ))

        if prob:
            prob_text = _rl(prob)
            if match_conf == "LOW":
                prob_text += " <i>(correspondance approximative)</i>"
            s.append(Paragraph(f"<b>Opportunité ciblée :</b> {prob_text}", val_style))

        if why:
            s.append(Paragraph(f"<b>Pourquoi Pepperyn recommande :</b> {_rl(why)}", val_style))

        if risk:
            s.append(Paragraph(f"<b>Si vous n'agissez pas :</b> {_rl(risk)}", val_style))

        if conf is not None:
            conf_line = f"Confiance : {conf}%"
            if conf_expl:
                conf_line += f" — {_rl(conf_expl)}"
            s.append(Paragraph(conf_line, conf_style))

        # EDX-002 — Options évaluées et écartées
        if options:
            s.append(Paragraph(
                f"Options évaluées : {len(options)} alternatives analysées, écartées :", opt_hdr_style
            ))
            for opt in options:
                opt_name  = _rl(opt.get("option", ""))
                elim_crit = _rl(opt.get("elimination_criterion", ""))
                s.append(Paragraph(f"<b>✗ {opt_name}</b>", opt_item_style))
                if elim_crit:
                    s.append(Paragraph(f"→ Écarté : {elim_crit}", elim_style))

        # EDX-002 — Option dominante
        if dominant:
            dom_inner = Table([
                [Paragraph(
                    f"<b>Option retenue :</b> {_rl(dominant)}",
                    ParagraphStyle("dom", fontName="Helvetica", fontSize=8,
                                   textColor=C_WHITE, leading=12)
                )]
            ], colWidths=[CONTENT_W - 8 * mm])
            dom_inner.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [3]),
            ]))
            s.append(dom_inner)
            s.append(_sp(2))

        # EDX-002 — Conditions de révision
        if tippings:
            s.append(Paragraph("Ce qui me ferait changer d'avis :", opt_hdr_style))
            for t in tippings:
                cond = _rl(t.get("condition", ""))
                alt  = _rl(t.get("alternative_recommendation", ""))
                h    = t.get("horizon_days", 90)
                s.append(Paragraph(
                    f"<b>Si</b> {cond} (horizon : {h}j) → {alt}", tipping_style
                ))

        if i < len(decisions) - 1:
            s.append(_hr())
            s.append(_sp(2))

    s.append(PageBreak())
    return s


# ─── P6 : "COMBIEN VAIS-JE GAGNER ?" — VALEUR CRÉÉE SI VOUS AGISSEZ ─────────

def _build_page_value_creation(edm, result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "VALEUR CRÉÉE SI VOUS AGISSEZ",
        styles,
        ceo_question="Combien vais-je gagner ?"
    ))
    s.append(_hr())
    s.append(_sp(6))

    decisions = edm.executive_decisions[:10]
    total_ann = sum(
        abs(d.annual_impact) for d in decisions if d.annual_impact
    )

    # Hero : total impact si toutes les décisions exécutées
    if total_ann:
        hero_text = _fmt_auto(total_ann)
        inner = Table([
            [Paragraph("IMPACT TOTAL SI EXÉCUTION COMPLÈTE", ParagraphStyle(
                "vc_lbl", fontName="Helvetica-Bold", fontSize=8,
                textColor=colors.HexColor("#AABBCC"), leading=12))],
            [_sp(2)],
            [Paragraph(hero_text, ParagraphStyle(
                "vc_val", fontName="Helvetica-Bold", fontSize=32,
                textColor=C_GREEN, leading=38))],
            [_sp(2)],
            [Paragraph("Potentiel annuel cumulé de toutes les décisions prioritaires", ParagraphStyle(
                "vc_note", fontName="Helvetica-Oblique", fontSize=9,
                textColor=colors.HexColor("#8899AA"), leading=13))],
        ], colWidths=[CONTENT_W - 12 * mm])
        inner.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        s.append(_dark_box(inner, styles))
        s.append(_sp(8))
    else:
        s.append(Paragraph("Données insuffisantes — impacts non calculés.", styles["body_small"]))

    # Détail par décision
    if decisions:
        headers = ["Décision", "Potentiel annuel", "ROI/10", "Délai de retour"]
        col_w = [CONTENT_W * 0.45, CONTENT_W * 0.22, CONTENT_W * 0.13, CONTENT_W * 0.20]
        data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

        for dec in decisions:
            ann_str = _fmt_eur(abs(dec.annual_impact)) if dec.annual_impact else "—"
            roi_str = f"{dec.roi_score:.1f}/10" if dec.roi_score else "—"
            timeline = dec.timeline or "—"
            data.append([
                Paragraph(_rl(dec.decision), styles["tbl_cell"]),
                Paragraph(ann_str, styles["tbl_impact_g"]),
                Paragraph(roi_str, styles["tbl_cell"]),
                Paragraph(timeline, styles["tbl_cell"]),
            ])

        tbl = Table(data, colWidths=col_w)
        cmds = [
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.8, C_LGRAY),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ]
        for i in range(1, len(data)):
            cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
        tbl.setStyle(TableStyle(cmds))
        s.append(tbl)
        s.append(_sp(6))

    # Value creation statement
    vc_stmt = result.get("creation_destruction_valeur")
    if vc_stmt:
        s.append(_hr())
        s.append(_sp(4))
        s.append(_quote_box(vc_stmt, styles, C_GREEN))

    s.append(PageBreak())
    return s


# ─── P7 : "DANS QUEL ORDRE, QUI FAIT QUOI ?" — CALENDRIER D'ALLOCATION ───────

def _build_page_roadmap(edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "CALENDRIER D'ALLOCATION 30 / 60 / 90 JOURS",
        styles,
        ceo_question="Dans quel ordre, et qui fait quoi ?"
    ))
    s.append(_hr())
    s.append(_sp(6))

    phases_edm = edm.roadmap_90_days or []

    def _phase_items(horizon: str) -> list[str]:
        for phase in phases_edm:
            if str(getattr(phase, "horizon", "")) == horizon:
                return [
                    getattr(a, "decision", str(a))
                    for a in (phase.actions or [])[:7]
                ]
        return []

    cols_def = [
        ("30 JOURS",  "30", C_BLUE),
        ("60 JOURS",  "60", C_AMBER),
        ("90 JOURS",  "90", C_GREEN),
    ]
    col_w = (CONTENT_W - 4 * mm) / 3

    def _col_table(label: str, horizon: str, color) -> Table:
        items = _phase_items(horizon)
        hdr = Table([[Paragraph(label, ParagraphStyle(
            f"rh_{horizon}", fontName="Helvetica-Bold", fontSize=10,
            textColor=C_WHITE, alignment=TA_CENTER, leading=14,
        ))]], colWidths=[col_w])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), color),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        item_style = ParagraphStyle(
            f"ri_{horizon}", fontName="Helvetica", fontSize=9,
            textColor=C_DARK, leading=13, leftIndent=6,
        )
        miss_style = ParagraphStyle(
            f"rm_{horizon}", fontName="Helvetica-Oblique", fontSize=9,
            textColor=C_GRAY, leading=13, leftIndent=6,
        )
        body_rows = (
            [[Paragraph(f"→  {txt}", item_style)] for txt in items]
            if items
            else [[Paragraph("Données insuffisantes", miss_style)]]
        )
        body = Table(body_rows, colWidths=[col_w])
        body_cmds = [
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("BACKGROUND",    (0, 0), (-1, -1), C_LBGRAY),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]
        for i in range(len(body_rows) - 1):
            body_cmds.append(("LINEBELOW", (0, i), (-1, i), 0.3, C_LGRAY))
        body.setStyle(TableStyle(body_cmds))
        col = Table([[hdr], [body]], colWidths=[col_w])
        col.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        return col

    cols = [_col_table(label, horizon, color) for label, horizon, color in cols_def]
    outer = Table([cols], colWidths=[col_w] * 3, hAlign="LEFT")
    outer.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2 * mm),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    s.append(outer)
    s.append(PageBreak())
    return s


# ─── P8 : "ET SI JE ME TROMPE ?" — 3 SCÉNARIOS ───────────────────────────────

def _build_page_scenarios(result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "3 SCÉNARIOS — ET SI JE ME TROMPE ?",
        styles,
        ceo_question="Et si je me trompe ?"
    ))
    s.append(_hr())
    s.append(_sp(6))

    scenarios_raw = result.get("scenarios") or []
    scen_map = {}
    for sc in scenarios_raw:
        if isinstance(sc, dict):
            nom, lbl, desc = sc.get("nom", ""), sc.get("label", ""), sc.get("description", "")
        else:
            nom = getattr(sc, "nom", "")
            lbl = getattr(sc, "label", "")
            desc = getattr(sc, "description", "")
        n = nom.lower()
        if "best" in n or "meilleur" in n:
            scen_map["best"] = (lbl or "MEILLEUR CAS", desc)
        elif "likely" in n or "probable" in n:
            scen_map["likely"] = (lbl or "CAS LE PLUS PROBABLE", desc)
        elif "worst" in n or "pire" in n:
            scen_map["worst"] = (lbl or "PIRE CAS", desc)

    s.append(Paragraph(
        "Ces trois scénarios ne sont pas des prévisions. Ce sont des cartes de navigation. "
        "Pour chaque scénario : la condition de déclenchement, l'impact estimé, et la décision à prendre si ce scénario se réalise.",
        styles["body_small"]
    ))
    s.append(_sp(6))

    def _scen_block(key, default_label, head_style, border_color):
        lbl, desc = scen_map.get(key, (default_label, "Données insuffisantes"))
        inner = Table([
            [Paragraph(lbl.upper(), head_style)],
            [_sp(3)],
            [Paragraph(_rl(desc) if desc else "Données insuffisantes", styles["scen_body"])],
        ], colWidths=[CONTENT_W / 3 - 6 * mm])
        inner.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        card = Table([[inner]], colWidths=[CONTENT_W / 3 - 2 * mm])
        card.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, -1), 3, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, -1), C_LBGRAY),
        ]))
        return card

    scen_row = [
        _scen_block("best",   "MEILLEUR CAS",        styles["scen_head_g"], C_GREEN),
        _scen_block("likely", "CAS LE PLUS PROBABLE", styles["scen_head_b"], C_BLUE),
        _scen_block("worst",  "PIRE CAS",             styles["scen_head_r"], C_RED),
    ]
    scen_t = Table([scen_row], colWidths=[CONTENT_W / 3] * 3)
    scen_t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    s.append(scen_t)
    s.append(PageBreak())
    return s


# ─── P9 : "QUELS SONT LES RISQUES ?" — RISQUES À SURVEILLER ─────────────────

def _build_page_risks(result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "RISQUES À SURVEILLER",
        styles,
        ceo_question="Quels sont les risques que je n'ai pas anticipés ?"
    ))
    s.append(_hr())
    s.append(_sp(4))

    risks = result.get("problemes_critiques") or result.get("alertes") or []

    if not risks:
        s.append(Paragraph("Aucun risque critique identifié avec les données disponibles.", styles["body_small"]))
        s.append(PageBreak())
        return s

    s.append(Paragraph(
        "Chaque risque est associé à une décision préventive. "
        "Ce n'est pas une liste de problèmes — c'est un plan de surveillance.",
        styles["body_small"]
    ))
    s.append(_sp(5))

    headers = ["Risque identifié", "Sévérité", "Impact estimé", "Horizon"]
    col_w = [CONTENT_W * 0.44, CONTENT_W * 0.16, CONTENT_W * 0.22, CONTENT_W * 0.18]
    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

    def _sev_style(sev):
        sv = (sev or "").lower()
        if "élevé" in sv or "eleve" in sv or "high" in sv or "critiq" in sv:
            return styles["risk_sev_r"]
        if "moyen" in sv or "medium" in sv or "modéré" in sv:
            return styles["risk_sev_a"]
        return styles["risk_sev_g"]

    for risk in risks[:8]:
        if isinstance(risk, dict):
            desc = risk.get("description", "")
            sev  = risk.get("severite", risk.get("severity", "Moyen"))
            imp  = risk.get("impact", "Modéré")
            hor  = risk.get("horizon", "Court terme")
        else:
            desc = getattr(risk, "description", "")
            sev  = getattr(risk, "severity", "Moyen")
            imp  = getattr(risk, "impact", "Modéré")
            hor  = getattr(risk, "horizon", "Court terme")

        data.append([
            Paragraph(_rl(desc), styles["tbl_cell"]),
            Paragraph(sev, _sev_style(sev)),
            Paragraph(_rl(str(imp)), styles["tbl_cell"]),
            Paragraph(_rl(str(hor)), styles["body_small"]),
        ])

    tbl = Table(data, colWidths=col_w)
    cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.8, C_LGRAY),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_LBGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)
    s.append(PageBreak())
    return s


# ─── P10 : "COMMENT VAIS-JE MESURER ?" — KPIs DE PILOTAGE ───────────────────

def _build_page_kpis(result: dict, edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "MES KPIs DE PILOTAGE",
        styles,
        ceo_question="Comment vais-je mesurer que ça marche ?"
    ))
    s.append(_hr())
    s.append(_sp(6))

    s.append(Paragraph(
        "Ces indicateurs mesurent l'exécution des décisions prioritaires, "
        "pas la performance générale de l'entreprise. "
        "Un KPI sans décision associée est une information — pas un outil de pilotage.",
        styles["body_small"]
    ))
    s.append(_sp(6))

    dashboard = result.get("ceo_dashboard") or []
    score_conf = result.get("score_confiance")

    # Confiance de l'analyse en premier
    items = []
    if score_conf:
        items.append({
            "label": "Confiance de l'analyse Pepperyn",
            "value": f"{score_conf}%",
            "status": None
        })
    for card in dashboard:
        if isinstance(card, dict):
            items.append(card)
        else:
            items.append({
                "label": getattr(card, "label", ""),
                "value": getattr(card, "value", ""),
                "status": getattr(card, "status", None)
            })

    if not items:
        s.append(Paragraph("Données insuffisantes — indicateurs non disponibles.", styles["body_small"]))
        s.append(PageBreak())
        return s

    def _card_color(item):
        val = str(item.get("value", ""))
        label = str(item.get("label", "")).lower()
        if item.get("status") == "missing" or "données insuf" in val.lower():
            return C_LGRAY, HEX_GRAY
        if "confiance" in label:
            return C_GREEN, HEX_GREEN
        if "-" in val and any(c.isdigit() for c in val):
            return C_RED, HEX_RED
        return C_BLUE, HEX_BLUE

    col_w = CONTENT_W / 3
    row = []
    for item in items[:9]:
        val_str   = str(item.get("value", ""))
        label_str = str(item.get("label", ""))
        is_miss   = (item.get("status") == "missing" or "données insuf" in val_str.lower() or not val_str)
        border_c, val_hex = _card_color(item)

        if is_miss:
            val_p = Paragraph("Données<br/>insuffisantes", styles["indic_miss"])
        else:
            val_p = Paragraph(
                f'<font color="{val_hex}"><b>{_rl(val_str)}</b></font>',
                ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=12,
                               leading=16, alignment=1, textColor=C_DARK)
            )
        lbl_p = Paragraph(label_str, styles["indic_lbl"])

        inner = Table([[val_p], [_sp(1)], [lbl_p]], colWidths=[col_w - 10 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        card = Table([[inner]], colWidths=[col_w - 4 * mm])
        card.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 1, border_c),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        row.append(card)

        if len(row) == 3:
            row_t = Table([row], colWidths=[col_w] * 3)
            row_t.setStyle(TableStyle([
                ("LEFTPADDING",   (0, 0), (-1, -1), 2),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            s.append(row_t)
            s.append(_sp(3))
            row = []

    if row:
        while len(row) < 3:
            row.append(Table([[""]], colWidths=[col_w - 4 * mm]))
        row_t = Table([row], colWidths=[col_w] * 3)
        row_t.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        s.append(row_t)

    s.append(PageBreak())
    return s


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

def generate_pdf_report(result, company_name: str | None = None) -> bytes:
    """
    Génère le Rapport exécutif Pepperyn (11 pages — CEO Question Framework v3).

    Args:
        result: ExecutiveCaseJSON (V2 — source unique de vérité)
                OU dict brut de l'analyse LLM (legacy).
        company_name: nom de la société (couverture).
    """
    if isinstance(result, ExecutiveCaseJSON):
        from services.executive_case_builder import case_to_edm, case_to_result_dict
        edm        = case_to_edm(result)
        result_raw = case_to_result_dict(result)
        name       = company_name or result.company_name or "—"
        date_str   = result.analysis_date or datetime.now().strftime("%d/%m/%Y")
    else:
        result_raw = result
        edm        = build_executive_decision_model(result)
        name       = company_name or result.get("company_name") or "—"
        date_str   = datetime.now().strftime("%d/%m/%Y")

    doc_type = "PREVISIONNEL"
    result   = result_raw   # alias pour les builders internes

    styles = _build_styles()

    def _story():
        def _safe_page(page_name, builder_fn):
            try:
                return list(builder_fn())
            except Exception:
                return [
                    PageBreak(),
                    Paragraph(f"Section {page_name} — données insuffisantes",
                               styles.get("body", getSampleStyleSheet()["Normal"])),
                    PageBreak(),
                ]

        story = []

        # Cover — aucun header/footer
        try:
            story.extend(_build_cover(name, date_str, styles))
        except Exception:
            story.append(PageBreak())

        # P1–P10 — CEO Question Framework (RULE 003 : crash isolation)
        story.extend(_safe_page("Verdict",
            lambda: _build_page_verdict(result, edm, styles)))
        story.extend(_safe_page("Capital",
            lambda: _build_page_capital(edm, result, styles)))
        story.extend(_safe_page("COI",
            lambda: _build_page_coi(edm, result, styles)))
        story.extend(_safe_page("Décisions",
            lambda: _build_page_decisions(edm, styles, result)))
        story.extend(_safe_page("Raisonnement",
            lambda: _build_page_reasoning(edm, styles, result)))
        story.extend(_safe_page("Valeur créée",
            lambda: _build_page_value_creation(edm, result, styles)))
        story.extend(_safe_page("Roadmap",
            lambda: _build_page_roadmap(edm, styles)))
        story.extend(_safe_page("Scénarios",
            lambda: _build_page_scenarios(result, styles)))
        story.extend(_safe_page("Risques",
            lambda: _build_page_risks(result, styles)))
        story.extend(_safe_page("KPIs",
            lambda: _build_page_kpis(result, edm, styles)))

        return story

    def _make_doc(buf):
        return SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=22 * mm, bottomMargin=16 * mm,
            title=f"Rapport exécutif — {name}",
            author="Pepperyn Financial Control Center",
        )

    def _on_first(canvas, doc):
        pass  # couverture : aucun header/footer

    def _on_later(canvas, doc):
        _draw_header_footer(canvas, doc, doc_type, date_str)

    buf = io.BytesIO()
    doc = _make_doc(buf)
    try:
        doc.build(_story(), onFirstPage=_on_first, onLaterPages=_on_later)
    except Exception:
        from reportlab.lib.styles import getSampleStyleSheet as _gss
        buf = io.BytesIO()
        fallback = SimpleDocTemplate(buf, pagesize=A4,
                                     leftMargin=MARGIN, rightMargin=MARGIN,
                                     topMargin=22 * mm, bottomMargin=16 * mm)
        _st = _gss()
        fallback.build([
            Paragraph(f"Rapport exécutif — {name}", _st["Heading1"]),
            Spacer(1, 12 * mm),
            Paragraph("Données insuffisantes — le rapport ne peut être généré.", _st["Normal"]),
        ])

    return buf.getvalue()
