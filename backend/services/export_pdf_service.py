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

# ─── PALETTE McKINSEY ────────────────────────────────────────────────────────
# Loi 2 : max 3 couleurs actives par page
# Sources : SVG_MOBT31_Srvy_CXO_Exhibit2.svg + Exhibit4.svg
C_NAVY   = colors.HexColor("#0A2540")   # titres, structure (McKinsey #006699 adapté)
C_BLUE   = colors.HexColor("#1B4F8A")   # accents secondaires (roadmap phases)
C_RED    = colors.HexColor("#C0392B")   # pertes, urgence — SIGNAL UNIQUE
C_AMBER  = colors.HexColor("#B8763A")   # priorité moyenne (restreint)
C_GREEN  = colors.HexColor("#1D6A3A")   # gains, confiance haute — SIGNAL UNIQUE
C_GRAY   = colors.HexColor("#6B7280")   # labels, captions (McKinsey #676767)
C_LGRAY  = colors.HexColor("#D8E3E9")   # filets 0.5pt (McKinsey #D8E3E9 exact)
C_WHITE  = colors.white
C_DARK   = colors.HexColor("#1F2937")   # corps de texte (McKinsey #333333 adapté)
C_LBGRAY = colors.HexColor("#F8FAFB")   # fond très clair pour sections

HEX_RED   = "#C0392B"
HEX_AMBER = "#B8763A"
HEX_BLUE  = "#1B4F8A"
HEX_NAVY  = "#0A2540"
HEX_GRAY  = "#6B7280"
HEX_GREEN = "#1D6A3A"

# ─── LAYOUT A4 ────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4               # 595 × 842 pts
MARGIN         = 18 * mm          # 51 pts
CONTENT_W      = PAGE_W - 2 * MARGIN
HEADER_Y       = PAGE_H - 14 * mm
FOOTER_Y       = 9 * mm
CONTENT_TOP    = HEADER_Y - 8 * mm


# ─── TEXTE FALLBACK OFFICIEL ─────────────────────────────────────────────────
# Utilisé partout où une donnée est absente — cohérence garantie par cette constante.
_MANQUE_DATA = (
    "Il nous manque les données nécessaires pour donner une réponse qualitative à cet élément."
)
_MANQUE_DATA_SHORT = "Information non disponible"  # pour les cellules étroites


# ─── FORMATAGE NUMÉRIQUE ──────────────────────────────────────────────────────

def _fmt_eur(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "—"
    abs_v = abs(v)
    prefix = ("-" if v < 0 else ("+" if sign and v > 0 else ""))
    s = f"{abs_v:,.0f}".replace(",", " ")
    return f"{prefix}{s} €"


def _fmt_millions(v: Optional[float]) -> str:
    if v is None:
        return "—"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    m = abs_v / 1_000_000
    if m >= 10:
        return f"{prefix}{m:.0f} M€"
    return f"{prefix}{m:.1f} M€".replace(".", ",")


def _fmt_auto(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "—"
    if abs(v) >= 950_000:
        raw = _fmt_millions(v)
        if sign and v > 0:
            raw = "+" + raw
        return raw
    return _fmt_eur(v, sign=sign)


def _safe(v, fallback: str = _MANQUE_DATA_SHORT) -> str:
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
    """Échappe le HTML pour ReportLab et convertit le markdown basique.

    Strips any raw HTML tags first (LLM may output <b>...</b> or <i>...</i>
    literals that ReportLab would not render and that look like broken markup).
    """
    if not text:
        return ""
    text = text.strip()
    # Strip raw HTML tags before escaping — prevents <b>foo</b> from rendering as literal text
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"\*+", "", text)  # strip remaining unmatched ** markers (LLM output)
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

    # Loi McKinsey 6 : titre discret, pas dominant
    ps("ceo_q",        fontName="Helvetica-Oblique", fontSize=8.5, textColor=C_GRAY, leading=13, spaceAfter=3)
    ps("section_title",fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK, leading=17, spaceAfter=2)

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
    # Loi McKinsey 4 : en-têtes de tableau discrets (SMALL CAPS gris)
    ps("tbl_hdr",    fontName="Helvetica-Bold", fontSize=7.5, textColor=C_GRAY, leading=11)
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
    """
    Titre de section McKinsey — Loi 6 : discret, pas dominant.
    Question CEO en italique gris → titre bold → règle 0.5pt.
    Zéro barre colorée latérale.
    """
    items = []
    if ceo_question:
        items.append(Paragraph(f'<i>{_rl(ceo_question)}</i>', styles["ceo_q"]))
    items.append(Paragraph(title, styles["section_title"]))
    items.append(_hr(C_DARK, thickness=1.0))
    return items


def _hr(color=None, thickness: float = 0.5) -> HRFlowable:
    if color is None:
        color = C_LGRAY
    return HRFlowable(width=CONTENT_W, color=color, thickness=thickness, spaceAfter=0)


def _sp(h: float) -> Spacer:
    return Spacer(1, h * mm)


def _dark_box(inner_table, styles: dict, bg=None) -> Table:
    """
    Encadré héro — Loi McKinsey 3 : fond très clair, pas navy.
    Le chiffre doit respirer, pas être enfermé dans un rectangle foncé.
    """
    t = Table([[inner_table]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LBGRAY),
        ("LINEBELOW",     (0, 0), (-1, -1), 2.0, C_NAVY),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6 * mm),
        ("TOPPADDING",    (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
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


def _copilot_block(
    insight: str,
    action: str = None,
    styles: dict = None,
    hypothesis: str = None,
) -> list:
    """
    Bloc de raisonnement Pepperyn Copilote — avantage concurrentiel Pepperyn.

    Structure en 3 couches :
      1. Diagnostic factuel  — ancré dans les données transmises
      2. Hypothèse Pepperyn  — anticipation de l'avenir (quitte à pivoter)
      3. Signal de confirmation — l'indicateur qui valide ou invalide l'hypothèse

    Pepperyn n'est pas un ERP (passé) ni un outil BI (présent) : c'est un
    stratège qui émet des hypothèses de haut niveau et les suit dans le temps
    (ARTICLE I + ARTICLE II — Constitution Pepperyn).

    Paramètres :
        insight    : diagnostic factuel (phrase LLM ou calcul Python)
        hypothesis : hypothèse prospective de Pepperyn (quitte à se tromper)
        action     : signal de confirmation / recommandation concrète
        styles     : dict de styles (conservé pour compatibilité)
    """
    _MISSING_INSIGHT = _MANQUE_DATA
    _MISSING_ACTION  = (
        "Partagez vos données financières complètes lors de votre prochaine analyse — "
        "Pepperyn affinera ses recommandations à chaque itération."
    )

    insight_text = insight.strip() if insight else ""
    missing      = len(insight_text) < 10

    rows = []

    # ── Label ─────────────────────────────────────────────────────────────────
    label_ps = ParagraphStyle(
        "cpl", fontName="Helvetica-Bold", fontSize=6.5,
        textColor=C_NAVY, leading=10, spaceAfter=6,
    )
    rows.append([Paragraph("▶  PEPPERYN COPILOTE", label_ps)])

    # ── Diagnostic (couche 1) ─────────────────────────────────────────────────
    insight_ps = ParagraphStyle(
        "cpi", fontName="Helvetica", fontSize=9,
        textColor=C_DARK, leading=14,
    )
    rows.append([Paragraph(_rl(_MISSING_INSIGHT if missing else insight_text), insight_ps)])

    if missing:
        # Fallback données absentes
        fallback_ps = ParagraphStyle(
            "cpf", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#6B7280"), leading=13, spaceBefore=5,
        )
        rows.append([Paragraph(f"→  {_MISSING_ACTION}", fallback_ps)])
    else:
        # ── Hypothèse Pepperyn (couche 2) ─────────────────────────────────────
        if hypothesis:
            hyp_label_ps = ParagraphStyle(
                "cph_lbl", fontName="Helvetica-Bold", fontSize=6.5,
                textColor=C_NAVY, leading=10, spaceBefore=8, spaceAfter=3,
            )
            rows.append([Paragraph("HYPOTHÈSE PEPPERYN", hyp_label_ps)])
            hyp_ps = ParagraphStyle(
                "cph", fontName="Helvetica-Oblique", fontSize=9,
                textColor=colors.HexColor("#2C3E50"), leading=14,
            )
            rows.append([Paragraph(_rl(hypothesis), hyp_ps)])

        # ── Signal / Action (couche 3) ─────────────────────────────────────────
        if action:
            action_ps = ParagraphStyle(
                "cpa", fontName="Helvetica-Bold", fontSize=9,
                textColor=C_BLUE, leading=13, spaceBefore=7,
            )
            rows.append([Paragraph(f"→  {_rl(action)}", action_ps)])

    inner = Table(rows, colWidths=[CONTENT_W - 22 * mm])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    outer = Table([[inner]], colWidths=[CONTENT_W])
    outer.setStyle(TableStyle([
        ("LINEBEFORE",    (0, 0), (0, -1), 3.5, C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#EEF3F8")),
    ]))

    return [_sp(5), outer]


# ─── GRAPHIQUES LIGNE ─────────────────────────────────────────────────────────

def _fmt_chart_axis(val: float) -> str:
    """
    Formate les labels de l'axe Y des graphiques.
    Loi McKinsey 5 : axes lisibles (+2 M€, 0, -2 M€), jamais "2000000".
    """
    if val == 0:
        return "0"
    if abs(val) >= 1_000_000:
        m = val / 1_000_000
        prefix = "+" if m > 0 else ""
        formatted = f"{abs(m):.0f}" if abs(m) == int(abs(m)) else f"{abs(m):.1f}".replace(".", ",")
        return f"{prefix}{formatted} M€" if m > 0 else f"-{formatted} M€"
    if abs(val) >= 1_000:
        k = val / 1_000
        prefix = "+" if k > 0 else ""
        return f"{prefix}{abs(k):.0f} K€" if k > 0 else f"-{abs(k):.0f} K€"
    return f"{val:+.0f} €"


def _line_chart_two(series_a, series_b, width, height, y_min, y_max):
    d = Drawing(width, height)
    lc = HorizontalLineChart()
    lc.x = 44; lc.y = 24
    lc.width = width - 56; lc.height = height - 36
    lc.data = [series_a, series_b]
    lc.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(series_a))]
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.fontSize = 7
    lc.categoryAxis.labels.fontName = "Helvetica"
    lc.valueAxis.valueMin = y_min; lc.valueAxis.valueMax = y_max
    lc.valueAxis.valueStep = (y_max - y_min) / 4
    lc.valueAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontName = "Helvetica"
    lc.valueAxis.labelTextFormat = _fmt_chart_axis   # ← Loi 5 : axes formatés
    lc.lines[0].strokeColor = C_GREEN; lc.lines[0].strokeWidth = 1.5
    lc.lines[1].strokeColor = C_RED;   lc.lines[1].strokeWidth = 1.5
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
    s.append(_sp(12))

    # ── Note de transparence Pepperyn ─────────────────────────────────────────
    disclaimer_ps = ParagraphStyle(
        "cov_disc", fontName="Helvetica", fontSize=7.5,
        textColor=colors.HexColor("#5A6475"), leading=11.5,
        leftIndent=0, spaceAfter=0,
    )
    disc_border = Table(
        [[Paragraph(
            "<b>À propos de ce rapport —</b> "
            "Pepperyn analyse avec exactitude les données financières transmises. "
            "Ses recommandations stratégiques sont des hypothèses scorées et argumentées — non des vérités absolues. "
            "C'est en itérant d'analyse en analyse, et en engageant les décisions proposées, "
            "que le système apprend votre entreprise, affine son regard et améliore ses stratégies, "
            "comme un copilote financier qui grandit avec vous. "
            "Ce rapport s'adresse à toutes les entreprises : celles qui traversent une difficulté, "
            "celles qui stagnent, et celles qui cherchent à accélérer la création de valeur.",
            disclaimer_ps
        )]],
        colWidths=[CONTENT_W],
    )
    disc_border.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ("LINEBEFORE",    (0, 0), (0, -1), 2, C_NAVY),
    ]))
    s.append(disc_border)
    s.append(_sp(18))
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
    s.append(_sp(6))

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
        # Loi McKinsey 1 : BoldOblique (pas Bold-Oblique — nom ReportLab correct)
        right_items.append(Paragraph(f'"{_rl(tension)}"', ParagraphStyle(
            "ten", fontName="Helvetica-BoldOblique", fontSize=10.5,
            textColor=C_DARK, leading=15
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
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("LINEABOVE",     (0, 0), (-1, 0),  1.5, C_LGRAY),  # hairline top seulement
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
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

    # ── Bloc Copilote P1 ──────────────────────────────────────────────────────
    diag_p1   = result.get("diagnostic_immediat") or ""
    tension   = result.get("phrase_tension") or ""
    risque_p1 = result.get("risque_inaction") or ""
    score_g   = result.get("score_global") or 0
    vc_p1     = result.get("creation_destruction_valeur") or ""
    coi_p1    = edm.cost_of_inaction
    weekly_p1 = _fmt_eur(abs(coi_p1.per_week) if coi_p1 and coi_p1.per_week else None)
    n_dec_p1  = len(edm.executive_decisions or [])

    # Diagnostic factuel (couche 1)
    parts_p1 = [x for x in [diag_p1, tension] if x]
    cop1_insight = "  ".join(parts_p1) if parts_p1 else (risque_p1 or "")

    # Hypothèse prospective (couche 2)
    if score_g >= 70:
        cop1_hyp = (
            f"Pepperyn anticipe que votre structure est en position de croissance : "
            f"les {n_dec_p1} décisions identifiées permettent d'accélérer la création de valeur sans déstabiliser l'équilibre existant. "
            f"Cette hypothèse sera confirmée ou révisée dès J+30 selon l'évolution des KPIs de pilotage."
        )
        cop1_action = (
            "Votre avantage concurrentiel est dans l'exécution rapide, pas dans l'analyse supplémentaire. "
            "Signal de validation à J+30 : premier levier activé, premier KPI en progression mesurable."
        )
    else:
        cop1_hyp = (
            f"Pepperyn anticipe qu'à trajectoire constante — sans action dans les 30 prochains jours — "
            f"la destruction de valeur de {weekly_p1} par semaine atteindra un point de non-retour structurel. "
            f"Cette hypothèse est révisable si une première décision majeure est engagée et documentée avant J+15."
        ) if coi_p1 else (
            f"Pepperyn anticipe que l'inaction dans les 30 prochains jours aggrave irréversiblement la trajectoire. "
            f"Cette hypothèse sera confirmée ou révisée selon les premiers signaux opérationnels à J+15."
        )
        cop1_action = (
            "Agir dans les 30 jours est non-négociable. "
            "Signal d'alerte à J+15 : si aucune décision n'est formellement engagée, escalade immédiate au niveau direction."
        )
    s.extend(_copilot_block(cop1_insight, cop1_action, styles, hypothesis=cop1_hyp))

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
    s.append(_sp(7))

    destroyers = edm.value_destroyers[:5]

    # Total valeur identifiée
    total_ann = sum(
        abs(d.annual_impact) for d in destroyers if d.annual_impact
    )

    if total_ann:
        hero_text = _fmt_auto(total_ann)
        # mn1 fix: label précis → "COÛT DE L'INACTION" aligné sur page 4.
        # 161K = total perdu si rien ne change (COI) ; les décisions capturent 139K (86%).
        hero_lbl = "COÛT DE L'INACTION PAR AN"
        inner = Table([
            [Paragraph("COÛT TOTAL DE L'INACTION IDENTIFIÉ", ParagraphStyle(
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
    # McKinsey law 4 : hairlines only, no alternating backgrounds
    cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_DARK),   # règle épaisse sous header
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)
    s.append(_sp(6))

    # ── Bloc Copilote P2 ──────────────────────────────────────────────────────
    structural_p2  = result.get("impact_financier_synthese") or ""
    phrase_tens_p2 = result.get("phrase_tension") or ""
    total_monthly  = total_ann / 12 if total_ann else 0
    n_destr        = len(destroyers)

    # Diagnostic factuel
    if total_ann and n_destr:
        cop2_insight = (
            f"{structural_p2 or phrase_tens_p2}  "
            f"Ces {n_destr} leviers concentrent {_fmt_eur(total_ann)} de valeur sous-employée "
            f"— soit {_fmt_eur(total_monthly)} par mois qui n'entrent pas dans les comptes "
            f"et n'apparaissent dans aucun tableau de bord standard."
        ).strip()
    else:
        cop2_insight = structural_p2 or phrase_tens_p2 or ""

    # Hypothèse prospective
    if destroyers:
        d0          = destroyers[0]
        d0_monthly  = _fmt_eur(abs(d0.monthly_impact)) if d0.monthly_impact else "N/D"
        is_growth   = any(k in (structural_p2 + phrase_tens_p2).lower()
                          for k in ("croissance", "accél", "opportunité", "scale"))
        if is_growth:
            cop2_hyp = (
                f"Pepperyn anticipe que l'optimisation de **{d0.name}** seul libère {d0_monthly}/mois "
                f"de capacité opérationnelle — suffisant pour financer une phase d'accélération sans dilution du capital. "
                f"Cette hypothèse sera confirmée si les premiers indicateurs de ce levier progressent dans les 30 jours."
            )
            cop2_action = (
                f"Activez **{d0.name}** en premier : c'est le levier dont le déblocage finance les suivants. "
                f"Si ce levier résiste, c'est un signal que le problème est structurel et non opérationnel — révisez l'hypothèse."
            )
        else:
            cop2_hyp = (
                f"Pepperyn anticipe que **{d0.name}** est le levier le plus liquide : "
                f"son déblocage génère {d0_monthly}/mois de trésorerie immédiate sans investissement supplémentaire — "
                f"uniquement en corrigeant une pratique existante. "
                f"Si ce n'est pas le cas à J+30, c'est que le levier était surestimé ou que l'exécution a été partielle."
            )
            cop2_action = (
                f"Priorité absolue : **{d0.name}**. "
                f"Commencez par le levier le plus liquide, pas le plus impactant — "
                f"la trésorerie crée le temps pour attaquer les leviers structurels suivants."
            )
        s.extend(_copilot_block(cop2_insight, cop2_action, styles, hypothesis=cop2_hyp))
    else:
        s.extend(_copilot_block(cop2_insight, None, styles))

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
    s.append(_sp(6))

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

    # ── Bloc Copilote P3 ──────────────────────────────────────────────────────
    risque_p3  = result.get("risque_inaction") or ""
    coi_p3     = edm.cost_of_inaction
    monthly_p3 = _fmt_eur(abs(coi_p3.per_month) if coi_p3 and coi_p3.per_month else None)
    weekly_p3  = _fmt_eur(abs(coi_p3.per_week)  if coi_p3 and coi_p3.per_week  else None)
    daily_p3   = _fmt_eur(abs(coi_p3.per_day)   if coi_p3 and coi_p3.per_day   else None)

    cop3_insight = (
        f"Ces chiffres ne sont pas des projections : ils sont calculés mécaniquement "
        f"à partir des données financières transmises. "
        f"La destruction de valeur de {monthly_p3}/mois ({weekly_p3}/semaine, {daily_p3}/jour) est silencieuse — "
        f"elle ne déclenche aucune alerte comptable et n'apparaît dans aucun tableau de bord standard "
        f"tant que l'entreprise n'atteint pas le point de rupture."
    ) if coi_p3 else (risque_p3 or "")

    cop3_hyp = (
        f"Pepperyn anticipe que {risque_p3}  "
        f"La simulation ci-dessous modélise les deux trajectoires sur 12 mois. "
        f"L'écart entre la courbe verte (avec action) et la courbe rouge (sans action) "
        f"représente exactement la valeur que les décisions engagées créent — ou que l'inaction détruit, "
        f"de façon définitive et non-linéaire dans le temps."
    ) if risque_p3 else (
        "Pepperyn anticipe une divergence croissante entre la trajectoire actuelle et une trajectoire optimisée. "
        "Les premières semaines d'inaction ont un coût faible et réversible — les suivantes deviennent structurellement irréversibles."
    )

    cop3_action = (
        f"Chaque semaine sans décision engagée représente {weekly_p3} de valeur définitivement perdue. "
        f"La fenêtre d'action optimale se rétrécit — non pas linéairement, mais exponentiellement."
    ) if coi_p3 else (
        "La fenêtre d'action optimale se rétrécit. La simulation ci-dessous en montre la trajectoire."
    )

    s.extend(_copilot_block(cop3_insight, cop3_action, styles, hypothesis=cop3_hyp))
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
        range_v = max(abs(y_min_v), abs(y_max_v), 10_000)
        ceil_m = int(range_v * 1.3 / 10_000 + 1) * 10_000
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
    s.append(_sp(5))

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
        data.append([Paragraph(_MANQUE_DATA_SHORT, styles["tbl_cell"]), "", "", "", "", ""])
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
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_DARK),   # McKinsey : règle épaisse header
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)

    # ── Bloc Copilote P4 ──────────────────────────────────────────────────────
    reasoning_list = (result_dict or {}).get("decision_reasoning", [])
    cop4_insight = ""
    if reasoning_list:
        first_r = reasoning_list[0] if isinstance(reasoning_list, list) else {}
        if isinstance(first_r, dict):
            cop4_insight = first_r.get("why_this_decision") or ""
        else:
            cop4_insight = getattr(first_r, "why_this_decision", "") or ""
    if not cop4_insight:
        cop4_insight = result_dict.get("creation_destruction_valeur") if result_dict else ""
        cop4_insight = cop4_insight or ""

    n_dec4 = len(decisions)
    cop4_hyp = (
        f"Pepperyn a sélectionné ces {n_dec4} décisions selon 3 critères stricts : "
        f"impact trésorerie à court terme, ratio effort/résultat, et indépendance des leviers. "
        f"Une décision absente de cette liste peut être pertinente sur le fond — "
        f"mais elle ne maximise pas la valeur dans la contrainte de temps et de ressources actuelles. "
        f"Cette sélection sera révisée à J+30 selon les premiers résultats d'exécution."
    )
    cop4_action = (
        f"Exécutez dans cet ordre sauf contrainte opérationnelle majeure. "
        f"Si l'ordre doit changer, documentez la raison et réévaluez l'impact sur les décisions dépendantes. "
        f"La page suivante détaille le raisonnement comparatif de chaque sélection."
    )
    s.extend(_copilot_block(cop4_insight, cop4_action, styles, hypothesis=cop4_hyp))

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
    s.append(_sp(5))

    reasoning_list = (result_dict or {}).get("decision_reasoning", [])
    decisions = edm.executive_decisions[:5]

    if not reasoning_list or not decisions:
        # ── Méthodologie : explication structurée du raisonnement ──────────────
        phase_lbl = ParagraphStyle(
            "ph_lbl", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=C_NAVY, leading=11, spaceBefore=10, spaceAfter=2,
        )
        phase_body = ParagraphStyle(
            "ph_body", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#222222"), leading=13.5, spaceAfter=4,
        )

        phases = [
            (
                "PHASE 1 — CLASSIFICATION ET VALIDATION (AGENT DE CLASSIFICATION)",
                "Un premier agent spécialisé reçoit vos documents financiers, détecte leur nature "
                "(compte de résultat, bilan, trésorerie, ou combinaison) et valide leur structure avant toute analyse. "
                "Il normalise les données, signale les anomalies et calcule le score de fiabilité de la source. "
                "C'est la porte d'entrée obligatoire : aucun agent d'analyse ne peut démarrer "
                "tant que cette étape n'est pas franchie — c'est ce \"score de confiance des données\" "
                "que vous retrouvez en page de transparence.",
            ),
            (
                "PHASE 2 — ANALYSE STRATÉGIQUE EN DEUX PASSES (AGENT D'ANALYSE + AGENT DE VÉRIFICATION)",
                "Un agent d'analyse stratégique effectue une première lecture approfondie des données validées. "
                "Sa mission est double : identifier les mécanismes par lesquels votre entreprise perd de la valeur "
                "(DSO élevé, rotation de stock dégradée, marges comprimées...) mais aussi — et c'est essentiel — "
                "repérer les leviers sous-exploités susceptibles d'en créer "
                "(niches de marge non activées, opportunités de renégociation, capacités disponibles). "
                "Sa production est ensuite soumise à un agent de vérification — un second passage critique "
                "qui corrige les incohérences et évalue la qualité du raisonnement. "
                "Si le score de qualité est insuffisant, les deux passes s'escaladent automatiquement "
                "vers un modèle de raisonnement plus puissant.",
            ),
            (
                "PHASE 3 — CALCUL DES INDICATEURS (MOTEUR DE CALCUL DÉTERMINISTE)",
                "Un moteur de calcul Python — entièrement déterministe, aucune IA — prend les leviers "
                "identifiés en Phase 2 et calcule les indicateurs chiffrés de chaque décision : "
                "impact annuel potentiel, ROI à 90 jours, délai de retour sur investissement, "
                "score de santé financière global et indice d'indépendance opérationnelle. "
                "Aucun modèle de langage n'intervient ici : les mêmes données produiront toujours "
                "les mêmes chiffres, quelle que soit la date de l'analyse. "
                "Ce squelette chiffré est ensuite transmis à l'Agent 1.",
            ),
            (
                "PHASE 4 — STRUCTURATION ET CONVICTION (AGENT 1 — EXECUTIVE CASE BUILDER)",
                "L'Agent 1 — modèle de raisonnement de niveau frontier — reçoit simultanément "
                "l'analyse vérifiée (Phase 2) et le squelette chiffré (Phase 3). "
                "Il sélectionne et ordonne les décisions finales, les structure dans le format officiel du rapport, "
                "puis associe à chacune une hypothèse argumentée et un signal concret à J+30 "
                "permettant de la confirmer ou de l'invalider. "
                "C'est lui qui sépare délibérément ce qui est mesuré (reproductible) "
                "de ce qui est inféré (challengeable) — la distinction fondamentale entre un rapport de chiffres "
                "et un copilote stratégique.",
            ),
        ]

        for lbl, body in phases:
            s.append(_hr(C_LGRAY, thickness=0.4))
            s.append(Paragraph(lbl, phase_lbl))
            s.append(Paragraph(body, phase_body))

        s.append(_hr(C_LGRAY, thickness=0.4))
        s.append(_sp(6))

        # Copilot block spécifique à cette page (logique itérative)
        meth_insight = (
            "Cette page présente la méthodologie que Pepperyn applique pour sélectionner et ordonner ses recommandations. "
            "La comprendre vous permet d'évaluer nos décisions avec le même œil critique que le nôtre — "
            "et de nous challenger si votre connaissance du terrain contredit notre raisonnement."
        )
        meth_hyp = (
            "Pepperyn anticipe que la transparence de la méthode est aussi importante que le résultat : "
            "une recommandation que vous comprenez a plus de chances d'être exécutée qu'une recommandation "
            "que vous subissez. Dans les prochaines versions, ce raisonnement sera disponible décision par décision "
            "— avec les alternatives écartées et les conditions qui feraient pivoter notre recommandation."
        )
        meth_action = (
            "À chaque nouvelle analyse, Pepperyn intègre les résultats des décisions déjà engagées. "
            "Si vous avez exécuté la décision n°1 depuis notre dernière analyse, "
            "son impact réel sera comparé à notre hypothèse initiale — et le raisonnement sera ajusté en conséquence. "
            "La pertinence des recommandations s'améliore à chaque itération : c'est ainsi qu'un copilote apprend."
        )
        s.extend(_copilot_block(meth_insight, meth_action, styles, hypothesis=meth_hyp))

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
    s.append(_sp(7))

    decisions = edm.executive_decisions[:10]
    # Use signed sum so negative-impact decisions reduce the total (e.g. opportunity cost decisions)
    total_ann = sum(d.annual_impact for d in decisions if d.annual_impact)

    # Hero : total impact net si toutes les décisions exécutées
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
        s.append(Paragraph(_MANQUE_DATA, styles["body_small"]))

    # Détail par décision
    if decisions:
        headers = ["Décision", "Potentiel annuel", "ROI/10", "Délai de retour"]
        col_w = [CONTENT_W * 0.45, CONTENT_W * 0.22, CONTENT_W * 0.13, CONTENT_W * 0.20]
        data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

        for dec in decisions:
            ann_str = _fmt_eur(dec.annual_impact, sign=True) if dec.annual_impact else "—"
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
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_DARK),
        ]
        for i in range(1, len(data)):
            cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
        tbl.setStyle(TableStyle(cmds))
        s.append(tbl)
        s.append(_sp(6))

    # ── Bloc Copilote P6 ──────────────────────────────────────────────────────
    vc_stmt = result.get("creation_destruction_valeur") or ""
    value_creation_statement = result.get("value_creation_statement") or ""
    n_d6  = len(decisions) if decisions else 0
    total_monthly_p6 = _fmt_eur(total_ann / 12) if total_ann else None

    cop6_insight_base = value_creation_statement or vc_stmt or ""
    cop6_insight = (
        f"{cop6_insight_base}  "
        f"Ce potentiel est calculé sur la base des données transmises — sans extrapolation ni hypothèse macro."
    ).strip() if cop6_insight_base else ""

    cop6_hyp = (
        f"Pepperyn anticipe que ce potentiel est cumulatif : chaque décision non exécutée soustrait "
        f"sa propre contribution au total. Si seulement 50 % des {n_d6} décisions sont réalisées, "
        f"le résultat ne sera pas la moitié de {_fmt_eur(total_ann) if total_ann else 'N/D'} — "
        f"car certains leviers se conditionnent mutuellement et leur valeur combinée est supérieure à leur somme. "
        f"L'ordre d'exécution et la complétude de l'engagement déterminent le résultat final."
    ) if n_d6 else (
        "Pepperyn anticipe que la valeur mobilisable est conditionnée par la rigueur d'exécution : "
        "chaque décision partiellement engagée produit une fraction de son potentiel, pas son plein effet."
    )

    cop6_action = (
        f"Ce chiffre n'est pas une projection financière — c'est un plafond de valeur mobilisable "
        f"si l'exécution est rigoureuse et séquencée. "
        f"Signal à J+30 : les premiers {total_monthly_p6 if total_monthly_p6 else 'gains'}/mois "
        f"devraient être visibles si la décision prioritaire a été engagée."
    )

    s.extend(_copilot_block(cop6_insight or cop6_hyp, cop6_action, styles, hypothesis=cop6_hyp if cop6_insight else None))

    s.append(PageBreak())
    return s


# ─── P7 : "DANS QUEL ORDRE, QUI FAIT QUOI ?" — CALENDRIER D'ALLOCATION ───────

def _build_page_roadmap(edm, styles: dict, result_dict: dict | None = None) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "CALENDRIER D'ALLOCATION 30 / 60 / 90 JOURS",
        styles,
        ceo_question="Dans quel ordre, et qui fait quoi ?"
    ))
    s.append(_sp(7))

    phases_edm = edm.roadmap_90_days or []

    def _phase_items(horizon: str) -> list[str]:
        for phase in phases_edm:
            if str(getattr(phase, "horizon", "")) == horizon:
                import re as _re_ph
                return [
                    # C3 fix: strip ** markdown LLM avant affichage PDF
                    _re_ph.sub(r'\*+', '', getattr(a, "decision", str(a))).strip()
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
            else [[Paragraph(_MANQUE_DATA_SHORT, miss_style)]]
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

    # ── Bloc Copilote P7 ──────────────────────────────────────────────────────
    urgence = (result_dict or {}).get("niveau_urgence") or ""
    if urgence:
        cop7_insight = (
            f"Niveau d'urgence : {urgence}. "
            f"Le séquençage 30/60/90 jours n'est pas arbitraire : J+30 libère la trésorerie (survie opérationnelle), "
            f"J+60 consolide la structure (stabilité), J+90 accélère la création de valeur (croissance). "
            f"Cet ordre est calculé — démarrer par J+60 avant J+30 détruirait la séquence de financement."
        )
    else:
        cop7_insight = (
            "Le séquençage 30/60/90 jours classe les actions par impact immédiat d'abord, "
            "puis par effet de levier structurel. J+30 libère la trésorerie (survie), "
            "J+60 consolide, J+90 accélère. "
            "Ne pas réorganiser l'ordre sans réévaluer les dépendances de financement."
        )

    cop7_hyp = (
        "Pepperyn anticipe que si la phase J+30 est exécutée correctement, elle libère suffisamment "
        "de ressources opérationnelles pour financer J+60 sans arbitrage budgétaire supplémentaire. "
        "Si ce mécanisme de refinancement interne ne se matérialise pas, "
        "le premier levier était mal dimensionné ou partiellement exécuté — "
        "c'est le signal pour revoir l'hypothèse avant d'engager J+60."
    )

    cop7_action = (
        "Signal de succès à J+30 : première décision exécutée, KPI associé mesuré, résultat documenté. "
        "Si J+30 échoue — ne pas démarrer J+60 sans diagnostic de l'échec. "
        "Un pivot documenté vaut mieux qu'une exécution aveugle de la phase suivante."
    )
    s.extend(_copilot_block(cop7_insight, cop7_action, styles, hypothesis=cop7_hyp))

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
    s.append(_sp(7))

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

    # ── Bloc Copilote P8 ──────────────────────────────────────────────────────
    likely_label = scen_map.get("likely", (None, None))[0] if scen_map.get("likely") else "le cas probable"
    likely_desc  = scen_map.get("likely", (None, None))[1] if scen_map.get("likely") else ""

    cop8_insight = (
        f"Ces 3 scénarios ne sont pas des prévisions — ce sont des cartes de navigation stratégique. "
        f"Le scénario \"{likely_label}\" repose sur l'hypothèse que les décisions prioritaires "
        f"sont engagées dans les 30 prochains jours. "
        f"{likely_desc[:180] + '...' if likely_desc and len(likely_desc) > 180 else (likely_desc or '')}"
    ).strip()

    cop8_hyp = (
        "Pepperyn anticipe que la probabilité de bascule vers le pire cas augmente de façon non-linéaire "
        "après la semaine 6 d'inaction. Les premières semaines d'inaction ont un coût réversible — "
        "les suivantes deviennent structurellement irréversibles car certains leviers se ferment. "
        "Cette hypothèse sera confirmée ou infirmée selon les signaux opérationnels à J+30."
    )

    cop8_action = (
        "Définissez 1 indicateur de surveillance par scénario aujourd'hui — avant de fermer ce rapport. "
        "Si le cas probable se dégrade, passez au plan de contingence sans attendre la confirmation complète : "
        "l'attente de certitude est elle-même une décision d'inaction."
    )
    s.extend(_copilot_block(cop8_insight, cop8_action, styles, hypothesis=cop8_hyp))
    s.append(_sp(6))

    def _scen_block(key, default_label, head_style, border_color):
        lbl, desc = scen_map.get(key, (default_label, _MANQUE_DATA))
        inner = Table([
            [Paragraph(lbl.upper(), head_style)],
            [_sp(3)],
            [Paragraph(_rl(desc) if desc else _MANQUE_DATA, styles["scen_body"])],
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
    s.append(_sp(5))

    risks = result.get("problemes_critiques") or result.get("alertes") or []

    if not risks:
        s.append(Paragraph(_MANQUE_DATA, styles["body_small"]))
        s.append(PageBreak())
        return s

    # ── Bloc Copilote P9 ──────────────────────────────────────────────────────
    first_risk_name = ""
    first_risk_desc = ""
    first_risk_sev  = ""
    first_risk_hor  = ""
    if risks:
        r0 = risks[0]
        if isinstance(r0, dict):
            first_risk_name = r0.get("nom", r0.get("name", ""))
            first_risk_desc = r0.get("description", "")
            first_risk_sev  = r0.get("severite", r0.get("severity", ""))
            first_risk_hor  = r0.get("horizon", "")
        else:
            first_risk_name = getattr(r0, "nom", getattr(r0, "name", ""))
            first_risk_desc = getattr(r0, "description", "")
            first_risk_sev  = getattr(r0, "severity", "")
            first_risk_hor  = getattr(r0, "horizon", "")

    n_risks = len(risks)
    if first_risk_desc:
        cop9_insight = (
            f"Risque prioritaire : {_rl(first_risk_name + ' — ' + first_risk_desc) if first_risk_name else _rl(first_risk_desc)}"
            + (f"  Classé {first_risk_sev}" if first_risk_sev else "")
            + (f", horizon {first_risk_hor}" if first_risk_hor else "")
            + f".  Ces {n_risks} risques sont classés par sévérité et horizon — pas par fréquence d'apparition."
        )
    else:
        cop9_insight = (
            f"Ces {n_risks} risques sont classés par sévérité et horizon. "
            "Chaque risque a un signal observable qui permet une détection précoce."
        )

    cop9_hyp = (
        "Pepperyn anticipe que ces risques ne sont pas indépendants : la réalisation du risque prioritaire "
        "augmente la probabilité des suivants en cascade — leur corrélation est non-linéaire. "
        "Un plan de contingence sur le risque n°1 protège l'ensemble du portefeuille de risques. "
        "Cette hypothèse sera révisée si le contexte opérationnel change significativement à J+30."
    )

    cop9_action = (
        "Assignez un responsable et un seuil de déclenchement à chaque risque classé élevé ou critique. "
        "Un risque sans responsable nommé n'est pas géré — il est subi. "
        "La liste sans plan d'action est une formalité, pas une protection."
    )
    s.extend(_copilot_block(cop9_insight, cop9_action, styles, hypothesis=cop9_hyp))
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
        ("TOPPADDING",    (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_DARK),   # McKinsey hairline
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
    ]
    for i in range(1, len(data)):
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)
    s.append(PageBreak())
    return s


# ── Dictionnaire de définitions — affiché sous chaque carte KPI ──────────────
_KPI_DEFS: dict[str, str] = {
    "chiffre d'affaires": "Total des ventes facturées sur la période. Point de départ de toute analyse de performance.",
    "ebitda": "Résultat avant intérêts, impôts et amortissements. Mesure la rentabilité opérationnelle pure, indépendamment de la structure financière.",
    "résultat net": "Bénéfice ou perte après toutes les charges (exploitation, financières, fiscales). Dernier indicateur de performance globale.",
    "marge brute": "Part du CA restant après les coûts directs (achats, production). Mesure l'efficacité commerciale avant les charges fixes.",
    "trésorerie": "Solde immédiatement disponible (comptes bancaires + caisse). C'est le pouls financier de l'entreprise — un indicateur de survie.",
    "dso clients": "Days Sales Outstanding : délai moyen de règlement des clients, en jours. Un DSO élevé immobilise du capital et accroît le risque de défaillance.",
    "dso": "Days Sales Outstanding : délai moyen de règlement des clients, en jours.",
    "stock obsolète": "Valeur des stocks sans perspective de revente à leur valeur comptable. Capital gelé qui doit être libéré en priorité.",
    "bfr": "Besoin en Fonds de Roulement : décalage entre encaissements clients et décaissements fournisseurs. Un BFR élevé mobilise un financement permanent.",
    "endettement net": "Dettes financières moins la trésorerie disponible. Mesure la dépendance de l'entreprise vis-à-vis de ses créanciers.",
    "confiance": "Score de fiabilité de l'analyse Pepperyn, calculé sur la complétude et la cohérence des données transmises.",
}

def _kpi_definition(label: str) -> str:
    """Retourne la définition associée à un label KPI (matching partiel insensible à la casse)."""
    lbl_low = label.lower()
    for key, defn in _KPI_DEFS.items():
        if key in lbl_low or lbl_low in key:
            return defn
    return ""


# ─── P10 : "COMMENT VAIS-JE MESURER ?" — KPIs DE PILOTAGE ───────────────────

def _build_page_kpis(result: dict, edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "MES KPIs DE PILOTAGE",
        styles,
        ceo_question="Comment vais-je mesurer que ça marche ?"
    ))
    s.append(_sp(6))

    # ── Bloc Copilote P10 ─────────────────────────────────────────────────────
    diag10 = result.get("diagnostic_immediat") or result.get("resume_executif") or ""
    diag10_short = diag10[:220].strip() + "..." if len(diag10) > 220 else diag10

    if diag10_short:
        cop10_insight = (
            f"{diag10_short}  "
            f"Ces KPIs mesurent l'exécution des décisions prioritaires — pas la performance générale. "
            f"Un KPI qui ne bouge pas malgré l'action est un signal : soit l'action n'a pas été exécutée, "
            f"soit l'hypothèse était erronée."
        )
    else:
        cop10_insight = (
            "Ces KPIs mesurent l'exécution des décisions prioritaires — pas la performance générale. "
            "Un KPI sans décision associée est de l'information, pas un outil de pilotage."
        )

    cop10_hyp = (
        "Hypothèse de pilotage Pepperyn : si ces indicateurs sont partagés en CODIR chaque semaine, "
        "la qualité d'exécution des décisions est significativement supérieure à un suivi mensuel. "
        "La fréquence de mesure est un levier d'exécution, pas seulement un outil d'information. "
        "Cette hypothèse sera confirmée si le rythme hebdomadaire est maintenu pendant 4 semaines."
    )

    cop10_action = (
        "Revoyez ces KPIs à J+30. Pour chaque indicateur sans mouvement : "
        "l'action a-t-elle vraiment été exécutée ? L'hypothèse est-elle toujours valide ? "
        "La réponse détermine si vous continuez — ou si vous pivotez."
    )
    s.extend(_copilot_block(cop10_insight, cop10_action, styles, hypothesis=cop10_hyp))
    s.append(_sp(6))

    dashboard = result.get("ceo_dashboard") or []
    score_conf = result.get("score_confiance")

    # Confiance de l'analyse en premier — on l'injecte manuellement,
    # puis on exclut toute entrée "confiance" déjà présente dans le dashboard
    items = []
    if score_conf:
        items.append({
            "label": "Confiance de l'analyse Pepperyn",
            "value": f"{score_conf}%",
            "status": None
        })
    for card in dashboard:
        if isinstance(card, dict):
            lbl = str(card.get("label", "")).lower()
            if score_conf and "confiance" in lbl:
                continue   # déjà injecté ci-dessus
            items.append(card)
        else:
            lbl = getattr(card, "label", "")
            if score_conf and "confiance" in lbl.lower():
                continue
            items.append({
                "label": lbl,
                "value": getattr(card, "value", ""),
                "status": getattr(card, "status", None)
            })

    if not items:
        s.append(Paragraph(_MANQUE_DATA, styles["body_small"]))
        s.append(PageBreak())
        return s

    def _card_color(item):
        val = str(item.get("value", ""))
        label = str(item.get("label", "")).lower()
        if item.get("status") == "missing" or "il nous manque" in val.lower() or "données insuf" in val.lower() or not val or val == "—":
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
        is_miss   = (item.get("status") == "missing" or "il nous manque" in val_str.lower() or "données insuf" in val_str.lower() or not val_str or val_str == "—")
        border_c, val_hex = _card_color(item)

        if is_miss:
            val_p = Paragraph("Il nous manque<br/>les données<br/>nécessaires", styles["indic_miss"])
        else:
            val_p = Paragraph(
                f'<font color="{val_hex}"><b>{_rl(val_str)}</b></font>',
                ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=12,
                               leading=16, alignment=1, textColor=C_DARK)
            )
        lbl_p   = Paragraph(label_str, styles["indic_lbl"])
        defn    = _kpi_definition(label_str)
        defn_ps = ParagraphStyle("kdef", fontName="Helvetica-Oblique", fontSize=6.5,
                                 textColor=C_GRAY, leading=9, alignment=1)
        defn_p  = Paragraph(_rl(defn), defn_ps) if defn else Paragraph("", defn_ps)

        inner = Table([[val_p], [_sp(1)], [lbl_p], [_sp(2)], [defn_p]],
                      colWidths=[col_w - 10 * mm])
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


# ─── P11 : COMPTE DE RÉSULTAT ────────────────────────────────────────────────

def _build_page_pl(fs, styles: dict) -> list:
    """P&L simplifié — une ligne = une vérité chiffrée."""
    from models.executive_case import FinancialStatements
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "COMPTE DE RÉSULTAT",
        styles,
        ceo_question="Quelle est ma rentabilité réelle ?"
    ))
    s.append(_sp(4))
    s.append(Paragraph(
        "Ce compte de résultat présente la formation du résultat, de la vente au bénéfice net. "
        "Chaque palier intermédiaire (Marge brute → EBITDA → EBIT → Résultat net) révèle "
        "où la valeur est créée ou détruite.",
        styles["body_small"]
    ))
    s.append(_sp(5))

    if not fs or not fs.pl_lines:
        s.append(Paragraph("Compte de résultat non disponible pour cette analyse.", styles["body_small"]))
        s.append(PageBreak())
        return s

    if fs.pl_period:
        s.append(Paragraph(fs.pl_period, ParagraphStyle(
            "pl_period", fontName="Helvetica-Oblique", fontSize=8, textColor=C_GRAY, leading=12
        )))
        s.append(_sp(4))

    # Styles locaux
    ps_label_main  = ParagraphStyle("plm",  fontName="Helvetica",      fontSize=9,    textColor=C_DARK,  leading=13)
    ps_label_sub   = ParagraphStyle("pls",  fontName="Helvetica",      fontSize=8.5,  textColor=C_GRAY,  leading=12, leftIndent=12)
    ps_label_sub2  = ParagraphStyle("plst", fontName="Helvetica-Bold", fontSize=9,    textColor=C_DARK,  leading=13)
    ps_label_total = ParagraphStyle("plt",  fontName="Helvetica-Bold", fontSize=9.5,  textColor=C_DARK,  leading=14)
    ps_val_main    = ParagraphStyle("plvm", fontName="Helvetica",      fontSize=9,    textColor=C_DARK,  leading=13, alignment=2)
    ps_val_sub     = ParagraphStyle("plvs", fontName="Helvetica",      fontSize=8.5,  textColor=C_GRAY,  leading=12, alignment=2)
    ps_val_sub2    = ParagraphStyle("plvst",fontName="Helvetica-Bold", fontSize=9,    textColor=C_DARK,  leading=13, alignment=2)
    ps_val_total   = ParagraphStyle("plvt", fontName="Helvetica-Bold", fontSize=9.5,  textColor=C_DARK,  leading=14, alignment=2)

    col_label = CONTENT_W * 0.68
    col_val   = CONTENT_W * 0.32
    data  = []
    cmds  = [
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Séparateur sous l'en-tête invisible (ligne 0 = label fictif non ajouté)
    ]

    for i, line in enumerate(fs.pl_lines):
        val_str = str(line.value_display or "")
        is_neg  = val_str.startswith("-")

        if line.is_total:
            lbl_ps = ps_label_total
            val_ps = ParagraphStyle("plvt2", fontName="Helvetica-Bold", fontSize=9.5,
                                    textColor=C_RED if is_neg else C_GREEN, leading=14, alignment=2)
            cmds.append(("LINEABOVE",  (0, i), (-1, i), 1.5, C_DARK))
            cmds.append(("LINEBELOW",  (0, i), (-1, i), 0.5, C_LGRAY))
        elif line.is_subtotal:
            lbl_ps = ps_label_sub2
            val_ps = ParagraphStyle("plvst2", fontName="Helvetica-Bold", fontSize=9,
                                    textColor=C_RED if is_neg else C_DARK, leading=13, alignment=2)
            cmds.append(("LINEABOVE",  (0, i), (-1, i), 0.5, C_LGRAY))
        elif line.indent > 0:
            lbl_ps = ps_label_sub
            val_ps = ps_val_sub
        else:
            lbl_ps = ps_label_main
            val_ps = ps_val_main

        data.append([
            Paragraph(_rl(line.label), lbl_ps),
            Paragraph(_rl(val_str), val_ps),
        ])

    tbl = Table(data, colWidths=[col_label, col_val])
    tbl.setStyle(TableStyle(cmds))
    s.append(tbl)

    if fs.pl_note:
        s.append(_sp(5))
        s.append(_hr(C_LGRAY, 0.5))
        s.append(_sp(3))
        s.append(Paragraph(f"<i>{_rl(fs.pl_note)}</i>",
                           ParagraphStyle("pln", fontName="Helvetica-Oblique", fontSize=7.5,
                                          textColor=C_GRAY, leading=11)))

    s.append(PageBreak())
    return s


# ─── P12 : BILAN SIMPLIFIÉ ────────────────────────────────────────────────────

def _build_page_bilan(fs, styles: dict) -> list:
    """Bilan à deux colonnes (Actif | Passif) — vue instantanée du patrimoine."""
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "BILAN SIMPLIFIÉ",
        styles,
        ceo_question="Où est engagé mon capital ?"
    ))
    s.append(_sp(4))
    s.append(Paragraph(
        "Le bilan est une photographie du patrimoine de l'entreprise à une date donnée. "
        "L'actif montre comment le capital est employé (immobilisations, stocks, créances, "
        "trésorerie). Le passif montre qui a financé ce capital (actionnaires et créanciers). "
        "Actif = Passif, toujours.",
        styles["body_small"]
    ))
    s.append(_sp(5))

    if not fs or (not fs.assets and not fs.liabilities):
        s.append(Paragraph("Bilan non disponible pour cette analyse.", styles["body_small"]))
        s.append(PageBreak())
        return s

    if fs.bilan_date:
        s.append(Paragraph(fs.bilan_date, ParagraphStyle(
            "bd", fontName="Helvetica-Oblique", fontSize=8, textColor=C_GRAY, leading=12
        )))
        s.append(_sp(4))

    ps_hdr = ParagraphStyle("bh",  fontName="Helvetica-Bold", fontSize=8.5, textColor=C_GRAY,
                            leading=12, alignment=1)
    ps_lbl = ParagraphStyle("bl",  fontName="Helvetica",      fontSize=9,   textColor=C_DARK, leading=13)
    ps_sub = ParagraphStyle("bls", fontName="Helvetica",      fontSize=8.5, textColor=C_GRAY, leading=12, leftIndent=10)
    ps_tot = ParagraphStyle("bt",  fontName="Helvetica-Bold", fontSize=9.5, textColor=C_DARK, leading=14)
    ps_val = ParagraphStyle("bv",  fontName="Helvetica",      fontSize=9,   textColor=C_DARK, leading=13, alignment=2)
    ps_vtot= ParagraphStyle("bvt", fontName="Helvetica-Bold", fontSize=9.5, textColor=C_DARK, leading=14, alignment=2)

    half  = CONTENT_W / 2 - 3 * mm
    col_l = half * 0.65
    col_v = half * 0.35

    def _side_table(lines, title):
        data = [[Paragraph(title, ps_hdr), Paragraph("", ps_hdr)]]
        cmds = [
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("LINEBELOW",     (0, 0), (-1, 0),  1.2, C_DARK),
        ]
        for i, line in enumerate(lines, start=1):
            val_str = str(line.value_display or "")
            if line.is_total:
                lbl_p = Paragraph(_rl(line.label), ps_tot)
                val_p = Paragraph(_rl(val_str), ps_vtot)
                cmds.append(("LINEABOVE", (0, i), (-1, i), 0.8, C_DARK))
            elif line.indent > 0:
                lbl_p = Paragraph(_rl(line.label), ps_sub)
                val_p = Paragraph(_rl(val_str), ParagraphStyle("bvs", fontName="Helvetica",
                                  fontSize=8.5, textColor=C_GRAY, leading=12, alignment=2))
            else:
                lbl_p = Paragraph(_rl(line.label), ps_lbl)
                val_p = Paragraph(_rl(val_str), ps_val)
            data.append([lbl_p, val_p])
            if not line.is_total and i < len(lines):
                cmds.append(("LINEBELOW", (0, i), (-1, i), 0.4, C_LGRAY))
        t = Table(data, colWidths=[col_l, col_v])
        t.setStyle(TableStyle(cmds))
        return t

    actif_t  = _side_table(fs.assets or [],      "ACTIF")
    passif_t = _side_table(fs.liabilities or [], "PASSIF")

    bilan_row = Table([[actif_t, passif_t]], colWidths=[half, half])
    bilan_row.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ("LEFTPADDING",  (1, 0), (1, 0), 6),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",    (0, 0), (0, -1), 0.5, C_LGRAY),
    ]))
    s.append(bilan_row)

    if fs.bfr_display:
        s.append(_sp(6))
        s.append(_hr(C_LGRAY, 0.5))
        s.append(_sp(3))
        bfr_note = (f"<b>BFR (Besoin en Fonds de Roulement) : {_rl(fs.bfr_display)}</b>"
                    " — Décalage entre encaissements clients et paiements fournisseurs. "
                    "Le BFR représente le capital permanent nécessaire pour financer le cycle d'exploitation.")
        if fs.bilan_note:
            bfr_note = f"<i>{_rl(fs.bilan_note)}</i>"
        s.append(Paragraph(bfr_note, ParagraphStyle(
            "bfr_n", fontName="Helvetica-Oblique", fontSize=7.5, textColor=C_GRAY, leading=11
        )))

    s.append(PageBreak())
    return s


# ─── P13 : POSITION DE TRÉSORERIE ─────────────────────────────────────────────

def _build_page_tresorerie(fs, styles: dict) -> list:
    """Position de trésorerie — urgence cash et runway."""
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "POSITION DE TRÉSORERIE",
        styles,
        ceo_question="Combien de temps puis-je tenir ?"
    ))
    s.append(_sp(4))
    s.append(Paragraph(
        "La trésorerie est le seul indicateur qui ne ment jamais : une entreprise rentable "
        "peut mourir si elle manque de liquidités. Ce tableau mesure le cash disponible, "
        "la consommation mensuelle (burn rate) et le délai avant rupture.",
        styles["body_small"]
    ))
    s.append(_sp(6))

    if not fs or not fs.cash_current:
        s.append(Paragraph("Position de trésorerie non disponible.", styles["body_small"]))
        s.append(PageBreak())
        return s

    # ── Indicateurs héros ─────────────────────────────────────────────────
    metrics = [
        ("TRÉSORERIE\nDISPONIBLE",     fs.cash_current,          "neutral"),
        ("BURN RATE\nMENSUEL",         fs.cash_burn_monthly,     "negative"),
        ("RUNWAY\nESTIMÉ",             fs.cash_runway_label,     "alert"),
    ]
    col_w3 = CONTENT_W / 3
    hero_cells = []
    for title, val, tone in metrics:
        if not val:
            continue
        is_neg = tone in ("negative", "alert")
        v_color = C_RED if is_neg else C_DARK
        v_hex   = HEX_RED if is_neg else HEX_NAVY
        hero_val = Paragraph(
            f'<font color="{v_hex}"><b>{_rl(val)}</b></font>',
            ParagraphStyle("tv", fontName="Helvetica-Bold", fontSize=14,
                           leading=18, alignment=1, textColor=C_DARK)
        )
        hero_lbl = Paragraph(title, ParagraphStyle(
            "tl", fontName="Helvetica", fontSize=7, textColor=C_GRAY,
            leading=10, alignment=1, spaceAfter=0
        ))
        inner = Table([[hero_lbl], [_sp(3)], [hero_val]], colWidths=[col_w3 - 8 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        card = Table([[inner]], colWidths=[col_w3 - 4 * mm])
        card.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, C_LGRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        hero_cells.append(card)

    while len(hero_cells) < 3:
        hero_cells.append(Table([[""]], colWidths=[col_w3 - 4 * mm]))

    hero_row = Table([hero_cells], colWidths=[col_w3] * 3)
    hero_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(hero_row)
    s.append(_sp(8))

    # ── Tableau des indicateurs détaillés ─────────────────────────────────
    ps_r_lbl = ParagraphStyle("rl", fontName="Helvetica",      fontSize=9,   textColor=C_DARK, leading=13)
    ps_r_val = ParagraphStyle("rv", fontName="Helvetica-Bold", fontSize=9,   textColor=C_DARK, leading=13, alignment=2)
    ps_r_def = ParagraphStyle("rd", fontName="Helvetica-Oblique", fontSize=7.5, textColor=C_GRAY, leading=11)

    detail_rows = [
        ("Ligne de crédit disponible",   fs.credit_line_available,
         "Facilité bancaire pouvant être tirée immédiatement en cas de besoin de liquidités."),
        ("Besoin de financement à 90j",  fs.financing_need_90d,
         "Montant à financer dans les 90 jours si la trajectoire actuelle se maintient sans action corrective."),
    ]

    data = [
        [Paragraph("INDICATEUR", ParagraphStyle("dh", fontName="Helvetica-Bold", fontSize=7.5,
                                                textColor=C_GRAY, leading=11)),
         Paragraph("VALEUR", ParagraphStyle("dvh", fontName="Helvetica-Bold", fontSize=7.5,
                                            textColor=C_GRAY, leading=11, alignment=2))],
    ]
    cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_DARK),
    ]
    for i, (lbl, val, defn) in enumerate(detail_rows, start=1):
        if not val:
            continue
        lbl_cell = Table([
            [Paragraph(_rl(lbl), ps_r_lbl)],
            [Paragraph(f"<i>{_rl(defn)}</i>", ps_r_def)],
        ], colWidths=[CONTENT_W * 0.7])
        lbl_cell.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        is_neg = val.startswith("-") if val else False
        v_col  = C_RED if is_neg else C_DARK
        v_hex  = HEX_RED if is_neg else HEX_NAVY
        val_p  = Paragraph(f'<font color="{v_hex}">{_rl(val)}</font>', ps_r_val)
        data.append([lbl_cell, val_p])
        cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))

    if len(data) > 1:
        tbl = Table(data, colWidths=[CONTENT_W * 0.7, CONTENT_W * 0.3])
        tbl.setStyle(TableStyle(cmds))
        s.append(tbl)

    if fs.cash_note:
        s.append(_sp(6))
        s.append(_hr(C_LGRAY, 0.5))
        s.append(_sp(3))
        s.append(Paragraph(f"<i>{_rl(fs.cash_note)}</i>",
                           ParagraphStyle("cn", fontName="Helvetica-Oblique", fontSize=7.5,
                                          textColor=C_GRAY, leading=11)))

    s.append(PageBreak())
    return s


# ─── PAGE TRANSPARENCE & FIABILITÉ ───────────────────────────────────────────

def _build_page_transparence(result: dict, edm, styles: dict) -> list:
    """Page dédiée à la fiabilité des données et à la nature du raisonnement Pepperyn."""
    s = []
    s.append(_sp(6))
    s.extend(_section_header(
        "TRANSPARENCE & FIABILITÉ DE L'ANALYSE",
        styles,
        ceo_question="Puis-je faire confiance à ce rapport ?"
    ))
    s.append(_sp(7))

    score_data  = result.get("score_confiance") or result.get("confidence_score") or 0
    health      = result.get("score_global") or 0
    dq          = result.get("data_quality") or {}
    anomalies   = dq.get("anomalies") or [] if isinstance(dq, dict) else []
    assumptions = dq.get("assumptions") or [] if isinstance(dq, dict) else []
    limits      = dq.get("limits") or [] if isinstance(dq, dict) else []

    # ── Section 1 : scores de confiance ───────────────────────────────────────
    row_lbl_ps  = ParagraphStyle("tp_lbl", fontName="Helvetica-Bold", fontSize=8.5,
                                  textColor=C_DARK, leading=12)
    row_val_ps  = ParagraphStyle("tp_val", fontName="Helvetica-Bold", fontSize=14,
                                  textColor=C_NAVY, leading=18, alignment=TA_CENTER)
    row_desc_ps = ParagraphStyle("tp_desc", fontName="Helvetica", fontSize=8,
                                  textColor=C_GRAY, leading=11)

    def _score_bar(score: int, color) -> Table:
        pct = max(0, min(score, 100))
        bar_w = CONTENT_W * 0.38
        filled = bar_w * pct / 100
        inner = Table([[""]], colWidths=[filled])
        inner.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), color),
                                    ("TOPPADDING",(0,0),(-1,-1),3),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),3)]))
        outer = Table([[inner]], colWidths=[bar_w])
        outer.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,C_LGRAY),
                                    ("TOPPADDING",(0,0),(-1,-1),0),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),0),
                                    ("LEFTPADDING",(0,0),(-1,-1),0),
                                    ("RIGHTPADDING",(0,0),(-1,-1),0)]))
        return outer

    score_color_data = C_GREEN if score_data >= 70 else (C_AMBER if score_data >= 40 else C_RED)
    score_color_stra = C_GREEN if health    >= 70 else (C_AMBER if health    >= 40 else C_RED)

    scores_data = [
        [
            Paragraph("FIABILITÉ DES DONNÉES SOURCE", row_lbl_ps),
            Paragraph("CONFIANCE DU RAISONNEMENT STRATÉGIQUE", row_lbl_ps),
        ],
        [
            Paragraph(f"{score_data}%", row_val_ps),
            Paragraph(f"{health}/10", row_val_ps),
        ],
        [
            _score_bar(score_data, score_color_data),
            _score_bar(min(health * 10, 100), score_color_stra),
        ],
        [
            Paragraph(
                "Mesure la complétude et la cohérence interne des données financières transmises. "
                "Un score ≥ 80 % signifie que les chiffres sont suffisants pour un diagnostic structurel fiable.",
                row_desc_ps
            ),
            Paragraph(
                "Reflet de la santé financière globale calculée par Pepperyn. "
                "Il conditionne le niveau de prudence appliqué aux hypothèses stratégiques : "
                "plus il est bas, plus les décisions urgentes sont prioritaires.",
                row_desc_ps
            ),
        ],
    ]
    scores_table = Table(scores_data, colWidths=[CONTENT_W / 2] * 2)
    scores_table.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",     (0, 0), (0, -1), 0.5, C_LGRAY),
    ]))
    s.append(scores_table)
    s.append(_sp(8))

    # ── Section 2 : anomalies, hypothèses, limites ────────────────────────────
    detail_lbl_ps = ParagraphStyle("tp_dlbl", fontName="Helvetica-Bold", fontSize=8,
                                    textColor=C_NAVY, leading=12, spaceBefore=6)
    detail_ps     = ParagraphStyle("tp_d", fontName="Helvetica", fontSize=8,
                                    textColor=C_DARK, leading=12, leftIndent=8)
    detail_miss   = ParagraphStyle("tp_dm", fontName="Helvetica-Oblique", fontSize=8,
                                    textColor=C_GRAY, leading=12, leftIndent=8)

    def _detail_col(title: str, items: list, miss_label: str) -> list:
        col = [Paragraph(title, detail_lbl_ps)]
        if items:
            for item in items[:6]:
                col.append(Paragraph(f"• {_rl(str(item))}", detail_ps))
        else:
            col.append(Paragraph(miss_label, detail_miss))
        return col

    def _col_table(items_list: list) -> Table:
        t = Table([[p] for p in items_list], colWidths=[CONTENT_W / 3 - 4 * mm])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        return t

    col_anom  = _detail_col("ANOMALIES DÉTECTÉES",  anomalies,  "Aucune anomalie détectée dans les données transmises.")
    col_assum = _detail_col("HYPOTHÈSES APPLIQUÉES", assumptions, "Analyse directe — aucune hypothèse de substitution nécessaire.")
    col_lim   = _detail_col("LIMITES DU PÉRIMÈTRE", limits,      "Périmètre complet — aucune limite identifiée.")

    detail_row = Table(
        [[_col_table(col_anom), _col_table(col_assum), _col_table(col_lim)]],
        colWidths=[CONTENT_W / 3] * 3,
    )
    detail_row.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",     (0, 0), (1, -1), 0.5, C_LGRAY),
    ]))
    s.append(detail_row)
    s.append(_sp(8))

    # ── Section 3 : comment Pepperyn crée de la valeur pour TOUTES les entreprises ─
    s.extend(_copilot_block(
        insight=(
            "Pepperyn n'est pas uniquement un outil de diagnostic pour les entreprises en difficulté. "
            "Il s'adresse avec la même rigueur aux entreprises en croissance, aux structures stables "
            "qui stagnent et à celles qui cherchent à accélérer la création de valeur. "
            "Pour chaque profil, il identifie les leviers sous-exploités — "
            "non pas les problèmes à résoudre, mais les opportunités à saisir."
        ),
        action=(
            "À chaque nouvelle analyse, Pepperyn intègre les résultats des décisions précédemment engagées. "
            "C'est en itérant que le système apprend votre entreprise, affine son regard "
            "et améliore la pertinence de ses recommandations — comme tout copilote qui grandit avec vous."
        ),
        styles=styles,
        hypothesis=(
            "Pepperyn anticipe qu'une entreprise qui analyse sa performance à intervalle régulier "
            "— et qui engage au moins 50 % des décisions recommandées — voit la pertinence des recommandations "
            "s'améliorer de façon mesurable à partir de la 3e analyse. "
            "Cette hypothèse sera documentée et révisée au fil des itérations."
        ),
    ))

    s.append(PageBreak())
    return s


# ─── PAGE DE CLÔTURE (BACK COVER) ─────────────────────────────────────────────

def _build_back_cover(styles: dict) -> list:
    """Page de clôture — sobre, Pepperyn branding."""
    s = []
    s.append(_sp(85))
    s.append(_hr(C_LGRAY, thickness=0.5))
    s.append(_sp(10))

    brand_ps = ParagraphStyle(
        "bc_brand", fontName="Helvetica-Bold", fontSize=22,
        textColor=C_NAVY, leading=28, alignment=TA_CENTER,
    )
    sub_ps = ParagraphStyle(
        "bc_sub", fontName="Helvetica", fontSize=11,
        textColor=C_GRAY, leading=16, alignment=TA_CENTER,
    )
    conf_ps = ParagraphStyle(
        "bc_conf", fontName="Helvetica", fontSize=7.5,
        textColor=colors.HexColor("#8899AA"), leading=11, alignment=TA_CENTER,
    )

    s.append(Paragraph("Pepperyn", brand_ps))
    s.append(_sp(3))
    s.append(Paragraph("Financial Control Center", sub_ps))
    s.append(_sp(14))
    s.append(Paragraph(
        "Ce rapport a été préparé à partir des données transmises par votre entreprise. "
        "Il est destiné exclusivement à un usage interne de direction.",
        conf_ps
    ))
    return s


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

def generate_pdf_report(result, company_name: str | None = None) -> bytes:
    """
    Génère le Rapport exécutif Pepperyn (14 pages — CEO Question Framework v4 + états financiers).

    Args:
        result: ExecutiveCaseJSON (V2 — source unique de vérité)
                OU dict brut de l'analyse LLM (legacy).
        company_name: nom de la société (couverture).
    """
    if isinstance(result, ExecutiveCaseJSON):
        from services.executive_case_builder import case_to_edm, case_to_result_dict
        case_obj   = result                            # objet original — pour les états financiers
        edm        = case_to_edm(result)
        result_raw = case_to_result_dict(result)
        name       = company_name or result.company_name or "—"
        date_str   = result.analysis_date or datetime.now().strftime("%d/%m/%Y")
    else:
        case_obj   = None
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
                    Paragraph(
                        f"Section {page_name} — {_MANQUE_DATA}",
                        styles.get("body", getSampleStyleSheet()["Normal"]),
                    ),
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
            lambda: _build_page_roadmap(edm, styles, result)))
        story.extend(_safe_page("Scénarios",
            lambda: _build_page_scenarios(result, styles)))
        story.extend(_safe_page("Risques",
            lambda: _build_page_risks(result, styles)))
        story.extend(_safe_page("KPIs",
            lambda: _build_page_kpis(result, edm, styles)))
        story.extend(_safe_page("Transparence",
            lambda: _build_page_transparence(result, edm, styles)))

        # P11–P13 — États financiers (optionnels — présents si financial_statements fourni)
        fs = getattr(case_obj, "financial_statements", None) if case_obj else None
        if fs:
            story.extend(_safe_page("P&L",
                lambda: _build_page_pl(fs, styles)))
            story.extend(_safe_page("Bilan",
                lambda: _build_page_bilan(fs, styles)))
            story.extend(_safe_page("Trésorerie",
                lambda: _build_page_tresorerie(fs, styles)))

        # Back cover — toujours en dernière position
        story.extend(_build_back_cover(styles))

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
            Paragraph(_MANQUE_DATA, _st["Normal"]),
        ])

    return buf.getvalue()
