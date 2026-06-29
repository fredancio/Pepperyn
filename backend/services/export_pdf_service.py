"""
export_pdf_service.py — Rapport exécutif Pepperyn
Master de référence officiel : "Ancienne version du PDF.pdf"

Structure — 11 pages (v2 Stabilisation MVP) :
  P1  Couverture
  P2  Le coût réel de l'inaction
  P3  Pourquoi votre rentabilité se dégrade
  P4  Où en êtes-vous aujourd'hui ?
  P5  Vos indicateurs clés
  P6  Que faire maintenant ? (décisions + score ROI)
  P7  Plan d'exécution 30 / 60 / 90 jours
  P8  Ce qui détruit réellement votre rentabilité
  P9  Agir ou ne rien faire ?
  P10 Quand retrouverez-vous l'équilibre ?
  P11 Décision prioritaire (page finale)

RÈGLE ABSOLUE : seules les données changent. La structure est figée.
Si une donnée est absente → afficher "Données insuffisantes".
Aucun graphique waterfall, bridge ou complexe. Tableaux simples uniquement,
sauf graphique à lignes sur P8 et P9 (conditions strictes).
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

# ─── PALETTE (identique au master) ───────────────────────────────────────────
C_NAVY   = colors.HexColor("#0A2540")   # fond boîte dark, titre couverture
C_BLUE   = colors.HexColor("#1B73E8")   # "RAPPORT EXÉCUTIF", bordures section
C_RED    = colors.HexColor("#C0392B")   # chiffres héros, COI, destruction
C_AMBER  = colors.HexColor("#B8763A")   # estimations, priorité moyenne
C_GREEN  = colors.HexColor("#2C7A4B")   # "avec action", confiance
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
CONTENT_TOP    = HEADER_Y - 8 * mm   # début du contenu sous header


# ─── FORMATAGE NUMÉRIQUE ──────────────────────────────────────────────────────

def _fmt_eur(v: Optional[float], sign: bool = False) -> str:
    """Formate un montant en euros (espace comme séparateur de milliers)."""
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = ("-" if v < 0 else ("+" if sign and v > 0 else ""))
    s = f"{abs_v:,.0f}".replace(",", " ")   # espace fine insécable
    return f"{prefix}{s} €"


def _fmt_millions(v: Optional[float]) -> str:
    """Formate en millions : 6 700 000 → '6,7 M€'."""
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    m = abs_v / 1_000_000
    if m >= 10:
        return f"{prefix}{m:.0f} M€"
    return f"{prefix}{m:.1f} M€".replace(".", ",")


def _fmt_auto(v: Optional[float], sign: bool = False) -> str:
    """Si ≥ 1M → millions, sinon euros exact."""
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
    """Extrait un float depuis une chaîne comme '6 700 000 €' ou '-5 465 000'."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    cleaned = re.sub(r"[€\s ]", "", str(s)).replace(",", ".").strip()
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

    ps("cover_label", fontName="Helvetica",    fontSize=9,  textColor=C_GRAY,  alignment=TA_CENTER, leading=14)
    ps("cover_title", fontName="Helvetica-Bold", fontSize=38, textColor=C_NAVY, alignment=TA_CENTER, leading=46, spaceAfter=4)
    ps("cover_sub",   fontName="Helvetica",    fontSize=14, textColor=C_GRAY,  alignment=TA_CENTER, leading=20)
    ps("cover_meta_k",fontName="Helvetica",    fontSize=8,  textColor=C_BLUE,  leading=14)
    ps("cover_meta_v",fontName="Helvetica-Bold",fontSize=10, textColor=C_DARK,  leading=14)
    ps("cover_brand", fontName="Helvetica-Bold",fontSize=10, textColor=C_BLUE,  alignment=TA_CENTER, leading=14)
    ps("cover_conf",  fontName="Helvetica",    fontSize=8,  textColor=C_GRAY,  alignment=TA_CENTER, leading=12)

    ps("section_title",fontName="Helvetica-Bold",fontSize=14, textColor=C_DARK, leading=18, leftIndent=8)
    ps("section_title_red",fontName="Helvetica-Bold",fontSize=14,textColor=C_DARK,leading=18, leftIndent=8)

    ps("hero_xl",  fontName="Helvetica-Bold", fontSize=62, textColor=C_RED,  alignment=TA_LEFT, leading=70)
    ps("hero_l",   fontName="Helvetica-Bold", fontSize=36, textColor=C_DARK, alignment=TA_LEFT, leading=44)
    ps("hero_m",   fontName="Helvetica-Bold", fontSize=24, textColor=C_DARK, alignment=TA_LEFT, leading=30)
    ps("hero_label",fontName="Helvetica",     fontSize=8,  textColor=C_RED,  alignment=TA_LEFT, leading=11, spaceAfter=0)

    ps("kpi_val_red",  fontName="Helvetica-Bold", fontSize=18, textColor=C_RED,   alignment=TA_CENTER, leading=22)
    ps("kpi_val_blue", fontName="Helvetica-Bold", fontSize=18, textColor=C_BLUE,  alignment=TA_CENTER, leading=22)
    ps("kpi_lbl",      fontName="Helvetica",      fontSize=7,  textColor=C_GRAY,  alignment=TA_CENTER, leading=10)

    ps("score_hero",    fontName="Helvetica-Bold", fontSize=52, textColor=C_RED,   alignment=TA_LEFT, leading=60)
    ps("score_hero_lg", fontName="Helvetica-Bold", fontSize=52, textColor=C_GRAY,  alignment=TA_LEFT, leading=60)
    ps("score_label",   fontName="Helvetica",      fontSize=8,  textColor=C_RED,   alignment=TA_LEFT, leading=11)

    ps("dim_score",  fontName="Helvetica-Bold", fontSize=22, textColor=C_DARK, alignment=TA_CENTER, leading=28)
    ps("dim_label",  fontName="Helvetica",      fontSize=9,  textColor=C_GRAY, alignment=TA_CENTER, leading=13)
    ps("dim_badge",  fontName="Helvetica-Bold", fontSize=7,  textColor=C_RED,  alignment=TA_CENTER, leading=10)

    ps("indic_val",  fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK,  alignment=TA_CENTER, leading=18)
    ps("indic_lbl",  fontName="Helvetica",      fontSize=8,  textColor=C_GRAY,  alignment=TA_CENTER, leading=11)
    ps("indic_miss", fontName="Helvetica-Bold", fontSize=11, textColor=C_GRAY,  alignment=TA_CENTER, leading=15)

    ps("diag_label", fontName="Helvetica-Bold", fontSize=8,  textColor=C_AMBER, leading=12, spaceAfter=4)
    ps("body",       fontName="Helvetica",      fontSize=11, textColor=C_DARK,  leading=16, spaceAfter=4)
    ps("body_bold",  fontName="Helvetica-Bold", fontSize=11, textColor=C_DARK,  leading=16, spaceAfter=4)
    ps("body_small", fontName="Helvetica",      fontSize=9,  textColor=C_GRAY,  leading=13, spaceAfter=2)
    ps("quote",      fontName="Helvetica-Oblique", fontSize=10, textColor=C_GRAY, leading=15, leftIndent=10)

    ps("prio_score", fontName="Helvetica-Bold", fontSize=11, textColor=C_DARK, leading=15)
    ps("tbl_hdr",    fontName="Helvetica-Bold", fontSize=9,  textColor=C_DARK, leading=13)
    ps("tbl_cell",   fontName="Helvetica",      fontSize=10, textColor=C_DARK, leading=14)
    ps("tbl_impact", fontName="Helvetica-Bold", fontSize=14, textColor=C_RED,  leading=18, alignment=TA_LEFT)
    ps("tbl_prio_amber",fontName="Helvetica-Bold",fontSize=10,textColor=C_AMBER,leading=14)
    ps("tbl_prio_gray", fontName="Helvetica",   fontSize=10, textColor=C_GRAY, leading=14)

    ps("scen_head_g",fontName="Helvetica-Bold",fontSize=9, textColor=C_GREEN, leading=13)
    ps("scen_head_b",fontName="Helvetica-Bold",fontSize=9, textColor=C_BLUE,  leading=13)
    ps("scen_head_r",fontName="Helvetica-Bold",fontSize=9, textColor=C_RED,   leading=13)
    ps("scen_body",  fontName="Helvetica",     fontSize=9, textColor=C_DARK,  leading=13)

    ps("final_action",fontName="Helvetica-Bold",fontSize=15,textColor=C_AMBER,alignment=TA_CENTER,leading=20)
    ps("final_kpi_v", fontName="Helvetica-Bold",fontSize=18,textColor=C_RED,  alignment=TA_CENTER,leading=22)
    ps("final_kpi_l", fontName="Helvetica",    fontSize=7, textColor=C_GRAY,  alignment=TA_CENTER,leading=10)

    ps("chart_caption",fontName="Helvetica-Oblique",fontSize=9,textColor=C_GRAY,leading=13,spaceAfter=4)

    return S


# ─── CANVAS : HEADER / FOOTER ─────────────────────────────────────────────────

def _draw_header_footer(canvas, doc, doc_type: str, date_str: str) -> None:
    """Dessiné sur chaque page 2-10. Page 1 (couverture) n'a pas de header."""
    canvas.saveState()
    # Header
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(C_BLUE)
    canvas.drawString(MARGIN, HEADER_Y, "RAPPORT EXÉCUTIF")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(C_GRAY)
    canvas.drawRightString(PAGE_W - MARGIN, HEADER_Y, f"{doc_type}  ·  {date_str}")

    canvas.setStrokeColor(C_LGRAY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, HEADER_Y - 3 * mm, PAGE_W - MARGIN, HEADER_Y - 3 * mm)

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(MARGIN, FOOTER_Y, "Document confidentiel")
    canvas.drawRightString(PAGE_W - MARGIN, FOOTER_Y, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


# ─── COMPOSANTS RÉUTILISABLES ─────────────────────────────────────────────────

def _section_header(title: str, styles: dict, bar_color=None) -> Table:
    """Titre de section avec barre verticale colorée à gauche."""
    if bar_color is None:
        bar_color = C_BLUE
    bar = Table([[""]], colWidths=[3 * mm], rowHeights=[22])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bar_color),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    text_style = styles.get("section_title" if bar_color != C_RED else "section_title_red")
    title_p = Paragraph(title, text_style)
    t = Table([[bar, title_p]], colWidths=[5 * mm, CONTENT_W - 5 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _hr(color=None, thickness: float = 0.5) -> HRFlowable:
    if color is None:
        color = C_LGRAY
    return HRFlowable(width=CONTENT_W, color=color, thickness=thickness, spaceAfter=0)


def _sp(h: float) -> Spacer:
    return Spacer(1, h * mm)


# ─── PAGE 1 : COUVERTURE ──────────────────────────────────────────────────────

def _build_cover(company_name: str, date_str: str, styles: dict) -> list:
    s = []
    s.append(_sp(35))
    s.append(Paragraph("VERSION CONFIDENTIELLE", styles["cover_label"]))
    s.append(_sp(6))
    s.append(Paragraph("Rapport exécutif", styles["cover_title"]))
    s.append(_sp(2))
    s.append(Paragraph("Prévisionnel", styles["cover_sub"]))
    s.append(_sp(55))

    # Métadonnées
    meta = [
        ["PRÉPARÉ POUR", company_name or "—"],
        ["PRÉPARÉ PAR", "Pepperyn Financial Control Center"],
        ["DATE", date_str],
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

    # Pied de couverture
    s.append(_hr(C_LGRAY, thickness=0.5))
    s.append(_sp(4))
    s.append(Paragraph("Pepperyn", styles["cover_brand"]))
    s.append(_sp(2))
    s.append(Paragraph("Document confidentiel — usage interne réservé à la direction", styles["cover_conf"]))
    s.append(PageBreak())
    return s


# ─── PAGE 2 : LE COÛT RÉEL DE L'INACTION ─────────────────────────────────────

def _build_page_inaction(edm, risque_text: Optional[str], styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("LE COÛT RÉEL DE L'INACTION", styles))
    s.append(_hr())
    s.append(_sp(6))

    coi = edm.cost_of_inaction
    annual = coi.per_year if coi else None

    # Héros annuel
    hero_text = _fmt_millions(annual) if annual else "Données insuffisantes"
    s.append(Paragraph(hero_text, styles["hero_xl"]))
    s.append(_sp(1))
    s.append(Paragraph("PAR AN, SI RIEN NE CHANGE", styles["hero_label"]))
    s.append(_sp(6))
    s.append(_hr(C_RED, thickness=1.5))
    s.append(_sp(6))

    # 4 sous-métriques
    vals = [
        (_fmt_eur(coi.per_month if coi else None),   "PAR MOIS"),
        (_fmt_eur(coi.per_week if coi else None),    "PAR SEMAINE"),
        (_fmt_eur(coi.per_day if coi else None),     "PAR JOUR"),
        (_fmt_eur(coi.per_hour if coi else None),    "PAR HEURE"),
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
    s.append(_sp(6))
    s.append(_hr())
    s.append(_sp(6))

    # Quote narrative
    if risque_text:
        quote = Table(
            [[Paragraph(f"<b>Si rien ne change :</b>  {_rl(risque_text)}", styles["quote"])]],
            colWidths=[CONTENT_W - 8 * mm],
        )
        quote.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBEFORETABLE", (0, 0), (0, -1), 3, C_BLUE),
        ]))
        s.append(quote)

    s.append(PageBreak())
    return s


# ─── PAGE 3 : POURQUOI VOTRE RENTABILITÉ SE DÉGRADE ─────────────────────────

def _build_page_diagnostic(edm, result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("POURQUOI VOTRE RENTABILITÉ SE DÉGRADE", styles))
    s.append(_hr())
    s.append(_sp(6))

    # Boîte dark navy — perte structurelle estimée
    structural_raw = result.get("impact_financier_synthese")
    structural_v = _parse_float(structural_raw)
    structural_str = (
        f"~{_fmt_eur(structural_v)}/an" if structural_v
        else (_safe(structural_raw, "~Données insuffisantes") + "/an")
    )
    coi = edm.cost_of_inaction
    if coi and coi.per_year and not structural_v:
        structural_str = f"~{_fmt_eur(abs(coi.per_year))}/an"

    box_inner = Table(
        [
            [Paragraph("PERTE STRUCTURELLE ESTIMÉE", ParagraphStyle(
                "pse", fontName="Helvetica-Bold", fontSize=8,
                textColor=colors.HexColor("#AABBCC"), leading=12))],
            [Spacer(1, 3 * mm)],
            [Paragraph(structural_str, ParagraphStyle(
                "pse_val", fontName="Helvetica-Bold", fontSize=30,
                textColor=C_AMBER, leading=36))],
            [Spacer(1, 2 * mm)],
            [Paragraph("Estimation basée sur les données disponibles uniquement", ParagraphStyle(
                "pse_note", fontName="Helvetica-Oblique", fontSize=9,
                textColor=colors.HexColor("#8899AA"), leading=13))],
        ],
        colWidths=[CONTENT_W - 12 * mm],
    )
    box_inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    dark_box = Table([[box_inner]], colWidths=[CONTENT_W])
    dark_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6 * mm),
        ("ROUNDEDCORNERS", [4]),
    ]))
    s.append(dark_box)
    s.append(_sp(6))

    # Diagnostic
    diag = result.get("diagnostic_immediat") or result.get("resume_executif") or result.get("synthese") or ""
    if diag:
        s.append(Paragraph("DIAGNOSTIC", styles["diag_label"]))
        # Premier paragraphe en corps principal
        lines = [l.strip() for l in diag.split("\n") if l.strip()]
        if lines:
            s.append(Paragraph(_rl(lines[0]), styles["body"]))

        # Quote (phrase_tension ou ligne 2 du diagnostic)
        tension = result.get("phrase_tension") or (lines[1] if len(lines) > 1 else None)
        if tension:
            s.append(_sp(2))
            quote = Table(
                [[Paragraph(_rl(tension), styles["quote"])]],
                colWidths=[CONTENT_W - 8 * mm],
            )
            quote.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBEFORETABLE", (0, 0), (0, -1), 3, C_BLUE),
            ]))
            s.append(quote)
            s.append(_sp(3))

        # Lignes suivantes comme bullet points simples
        for line in lines[2:5]:
            s.append(Paragraph(_rl(line), styles["body_small"]))
            s.append(_sp(1))

    s.append(PageBreak())
    return s


# ─── PAGE 4 : OÙ EN ÊTES-VOUS AUJOURD'HUI ? ──────────────────────────────────

def _build_page_health(result: dict, edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("OÙ EN ÊTES-VOUS AUJOURD'HUI ?", styles))
    s.append(_hr())
    s.append(_sp(6))

    score_global = result.get("score_global")

    # Héros score
    if score_global is not None:
        score_str = str(score_global)
        score_p = Paragraph(
            f'<font color="{HEX_RED}" size="52"><b>{score_str}</b></font>'
            f'<font color="{HEX_GRAY}" size="52"><b>/10</b></font>',
            ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=52, leading=62)
        )
    else:
        score_p = Paragraph(
            '<font color="#8A9BB0" size="52"><b>N/A</b></font>',
            ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=52, leading=62)
        )
    s.append(score_p)
    s.append(_sp(1))
    s.append(Paragraph("INDICE DE SANTÉ GLOBALE", styles["score_label"]))
    s.append(_sp(4))
    s.append(_hr())
    s.append(_sp(4))

    # Ligne d'urgence
    niveau = result.get("niveau_urgence") or "Urgence critique"
    coi = edm.cost_of_inaction
    cdv = result.get("creation_destruction_valeur") or ""
    annual_str = _fmt_millions(abs(coi.per_year)) if coi and coi.per_year else "—"
    monthly_str = _fmt_eur(abs(coi.per_month)) if coi and coi.per_month else "—"

    urgency_txt = (
        f"<b>{_rl(niveau)}</b>  ·  ↓  "
        f"L'entreprise détruit environ <b>{annual_str}</b> de valeur. "
        f"Chaque mois d'inaction coûte <b>~{monthly_str}</b>."
    )
    if cdv:
        urgency_txt = f"<b>{_rl(niveau)}</b>  ·  ↓  {_rl(cdv)}"
    s.append(Paragraph(urgency_txt, styles["body"]))
    s.append(_sp(6))

    # 4 cartes de dimension
    s.append(Paragraph("DÉTAIL PAR DIMENSION", styles["body_small"]))
    s.append(_sp(3))

    dims = [
        ("Rentabilité", result.get("score_rentabilite"), "CRITIQUE",  C_RED),
        ("Risque",      result.get("score_risque"),      "ÉLEVÉ",     C_AMBER),
        ("Structure",   result.get("score_structure"),   "FRAGILE",   C_GRAY),
        ("Liquidité",   result.get("score_liquidite"),   "TENDUE",    C_AMBER),
    ]

    # Détecter badge approprié selon score
    def _badge(score, default_badge):
        if score is None:
            return default_badge
        if score <= 3:
            return "CRITIQUE"
        if score <= 5:
            return "FRAGILE"
        if score <= 7:
            return "ÉLEVÉ"
        return "STABLE"

    def _badge_color(badge):
        return {
            "CRITIQUE": C_RED, "FRAGILE": C_GRAY,
            "ÉLEVÉ": C_AMBER, "TENDUE": C_AMBER, "STABLE": C_GREEN,
        }.get(badge, C_GRAY)

    cards = []
    for label, score, default_badge, _ in dims:
        badge = _badge(score, default_badge)
        bc = _badge_color(badge)
        score_str = f"{score}/10" if score is not None else "N/A"
        color_hex = HEX_RED if badge == "CRITIQUE" else (
            HEX_AMBER if badge in ("ÉLEVÉ", "TENDUE") else HEX_GRAY
        )
        inner = Table([
            [Paragraph(f'<font color="{color_hex}"><b>{score_str}</b></font>',
                       ParagraphStyle("ds", fontName="Helvetica-Bold", fontSize=20, leading=26, alignment=1))],
            [_sp(1)],
            [Paragraph(label, styles["dim_label"])],
            [_sp(2)],
            [Paragraph(badge, ParagraphStyle("db", fontName="Helvetica-Bold", fontSize=7,
                                              textColor=bc, leading=10, alignment=1))],
        ], colWidths=[CONTENT_W / 4 - 8 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        cards.append(inner)

    cards_t = Table([cards], colWidths=[CONTENT_W / 4] * 4)
    cards_t.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 1, C_RED),
        ("BOX", (1, 0), (1, 0), 1, C_AMBER),
        ("BOX", (2, 0), (2, 0), 1, C_LGRAY),
        ("BOX", (3, 0), (3, 0), 1, C_AMBER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    s.append(cards_t)
    s.append(PageBreak())
    return s


# ─── PAGE 5 : VOS INDICATEURS CLÉS ───────────────────────────────────────────

def _build_page_indicators(result: dict, edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("VOS INDICATEURS CLÉS", styles))
    s.append(_hr())
    s.append(_sp(6))

    # Construire les cartes
    dashboard = result.get("ceo_dashboard") or []
    score_confiance = result.get("score_confiance")

    def _card_val(v, is_missing=False):
        if is_missing or not v or v.lower().startswith("données"):
            return "Données insuffisantes", True
        return v, False

    # Carte principale: niveau de confiance
    conf_val = f"{score_confiance}%" if score_confiance else "Données insuffisantes"
    conf_missing = not score_confiance

    # Cartes depuis dashboard + confiance en premier
    items = []
    items.append({"label": "Niveau de confiance", "value": conf_val,
                  "status": "missing" if conf_missing else None})
    for card in dashboard:
        if isinstance(card, dict):
            items.append(card)
        else:
            items.append({"label": getattr(card, "label", ""), "value": getattr(card, "value", ""),
                          "status": getattr(card, "status", None)})

    def _card_color(item):
        status = item.get("status")
        value = str(item.get("value", ""))
        label = str(item.get("label", "")).lower()
        if status == "missing" or "données insuf" in value.lower():
            return C_LGRAY, HEX_GRAY
        if "confiance" in label or "confidence" in label:
            return C_GREEN, HEX_GREEN
        if "-" in value and any(c.isdigit() for c in value):
            return C_RED, HEX_RED
        return C_BLUE, HEX_BLUE

    def _make_card(item, col_width):
        val_str = str(item.get("value", ""))
        label_str = str(item.get("label", ""))
        is_missing = (item.get("status") == "missing" or
                      "données insuf" in val_str.lower() or not val_str)
        border_c, val_hex = _card_color(item)

        if is_missing:
            val_p = Paragraph("Données<br/>insuffisantes", styles["indic_miss"])
        else:
            val_p = Paragraph(
                f'<font color="{val_hex}"><b>{_rl(val_str)}</b></font>',
                ParagraphStyle("cv", fontName="Helvetica-Bold", fontSize=12, leading=16,
                               alignment=1, textColor=C_DARK)
            )
        lbl_p = Paragraph(label_str, styles["indic_lbl"])

        inner = Table([[val_p], [_sp(1)], [lbl_p]],
                      colWidths=[col_width - 10 * mm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        card = Table([[inner]], colWidths=[col_width - 4 * mm])
        card.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, border_c),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return card

    # Grille 3 colonnes
    col_w = CONTENT_W / 3
    row = []
    for i, item in enumerate(items[:9]):
        row.append(_make_card(item, col_w))
        if len(row) == 3:
            row_t = Table([row], colWidths=[col_w] * 3)
            row_t.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
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
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        s.append(row_t)

    s.append(PageBreak())
    return s


# ─── PAGE 6 : QUE FAIRE MAINTENANT ? ─────────────────────────────────────────

def _build_page_decisions(edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("QUE FAIRE MAINTENANT ?", styles))
    s.append(_hr())
    s.append(_sp(4))

    # Score de priorisation
    score = edm.executive_decisions_score if edm.executive_decisions_score else 0.0
    s.append(Paragraph(
        f"Score de priorisation global  <font color='{HEX_BLUE}'><b>{score:.1f}/10</b></font>",
        styles["prio_score"]
    ))
    s.append(_sp(4))

    # Table des décisions — 6 colonnes avec score ROI
    headers = ["Décision", "Impact annuel", "ROI", "Délai", "Difficulté", "Priorité"]
    col_w = [CONTENT_W * 0.32, CONTENT_W * 0.16, CONTENT_W * 0.10,
             CONTENT_W * 0.12, CONTENT_W * 0.12, CONTENT_W * 0.18]

    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

    def _prio_p(prio):
        if not prio or prio in ("Not evaluated", "Non évaluée"):
            return Paragraph("Non évaluée", styles["tbl_prio_gray"])
        p_low = prio.lower()
        if "high" in p_low or "élevé" in p_low:
            return Paragraph(prio, ParagraphStyle(
                "ph", fontName="Helvetica-Bold", fontSize=10,
                textColor=C_RED, leading=14))
        return Paragraph(prio, styles["tbl_prio_amber"])

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
                Paragraph(impact_str, styles["tbl_impact"]),
                Paragraph(roi_str, styles["tbl_cell"]),
                Paragraph(dec.timeline or "—", styles["tbl_cell"]),
                Paragraph(dec.difficulty or "—", styles["tbl_cell"]),
                _prio_p(dec.priority),
            ])

    tbl = Table(data, colWidths=col_w)
    style_cmds = [
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_LGRAY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
    ]
    for i in range(1, len(data)):
        style_cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(style_cmds))
    s.append(tbl)
    s.append(PageBreak())
    return s


# ─── PAGE 7 : PLAN D'EXÉCUTION 30 / 60 / 90 JOURS ───────────────────────────

def _build_page_roadmap(edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("PLAN D'EXÉCUTION 30 / 60 / 90 JOURS", styles))
    s.append(_hr())
    s.append(_sp(6))

    phases_edm = edm.roadmap_90_days or []

    def _phase_items(horizon: str) -> list[str]:
        for phase in phases_edm:
            if str(getattr(phase, "horizon", "")) == horizon:
                return [
                    getattr(a, "decision", str(a))
                    for a in (phase.actions or [])[:6]
                ]
        return []

    cols_def = [
        ("30 JOURS",   "30", C_BLUE),
        ("60 JOURS",   "60", C_AMBER),
        ("90 JOURS",   "90", C_GREEN),
    ]

    col_w = (CONTENT_W - 4 * mm) / 3   # léger espace entre colonnes via padding

    def _col_table(label: str, horizon: str, color) -> Table:
        items = _phase_items(horizon)

        # En-tête de colonne
        hdr_style = ParagraphStyle(
            f"rmap_h_{horizon}", fontName="Helvetica-Bold", fontSize=10,
            textColor=C_WHITE, alignment=TA_CENTER, leading=14,
        )
        hdr = Table(
            [[Paragraph(label, hdr_style)]],
            colWidths=[col_w],
        )
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), color),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))

        # Corps : lignes d'actions
        item_style = ParagraphStyle(
            f"rmap_i_{horizon}", fontName="Helvetica", fontSize=9,
            textColor=C_DARK, leading=13, leftIndent=6,
        )
        miss_style = ParagraphStyle(
            f"rmap_m_{horizon}", fontName="Helvetica-Oblique", fontSize=9,
            textColor=C_GRAY, leading=13, leftIndent=6,
        )

        if not items:
            body_rows = [[Paragraph("Données insuffisantes", miss_style)]]
        else:
            body_rows = [[Paragraph(f"→  {txt}", item_style)] for txt in items]

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

        # Colonne = header + body empilés
        col = Table([[hdr], [body]], colWidths=[col_w])
        col.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        return col

    cols = [_col_table(label, horizon, color) for label, horizon, color in cols_def]

    outer = Table(
        [cols],
        colWidths=[col_w] * 3,
        hAlign="LEFT",
    )
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


# ─── PAGE 8 : CE QUI DÉTRUIT RÉELLEMENT VOTRE RENTABILITÉ ────────────────────

def _build_page_destroyers(edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("CE QUI DÉTRUIT RÉELLEMENT VOTRE RENTABILITÉ", styles, bar_color=C_RED))
    s.append(_hr())
    s.append(_sp(4))

    headers = ["Destructeur de valeur", "Impact annuel", "Impact mensuel", "Tendance"]
    col_w = [CONTENT_W * 0.40, CONTENT_W * 0.22, CONTENT_W * 0.22, CONTENT_W * 0.16]

    data = [[Paragraph(h, styles["tbl_hdr"]) for h in headers]]

    destroyers = edm.value_destroyers[:10]
    if not destroyers:
        data.append([Paragraph("Données insuffisantes", styles["tbl_cell"]), "", "", ""])
    else:
        for d in destroyers:
            ann_str = _fmt_auto(d.annual_impact, sign=True) if d.annual_impact else "—"
            mon_str = _fmt_eur(d.monthly_impact) if d.monthly_impact else "—"
            trend = d.trend or "—"
            data.append([
                Paragraph(_rl(d.name), styles["tbl_cell"]),
                Paragraph(ann_str, styles["tbl_impact"]),
                Paragraph(mon_str, styles["tbl_cell"]),
                Paragraph(trend, styles["tbl_cell"]),
            ])

    tbl = Table(data, colWidths=col_w)
    style_cmds = [
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_LGRAY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
    ]
    for i in range(1, len(data)):
        style_cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, C_LGRAY))
    tbl.setStyle(TableStyle(style_cmds))
    s.append(tbl)
    s.append(PageBreak())
    return s


# ─── GRAPHIQUE LIGNE ──────────────────────────────────────────────────────────

def _line_chart_two(series_a, series_b, width, height, y_min, y_max):
    """Graphique à deux lignes (avec action / sans action)."""
    d = Drawing(width, height)
    lc = HorizontalLineChart()
    lc.x = 38
    lc.y = 24
    lc.width = width - 50
    lc.height = height - 36
    lc.data = [series_a, series_b]
    lc.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(series_a))]
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.fontSize = 7
    lc.categoryAxis.labels.fontName = "Helvetica"
    lc.valueAxis.valueMin = y_min
    lc.valueAxis.valueMax = y_max
    steps = 4
    lc.valueAxis.valueStep = (y_max - y_min) / steps
    lc.valueAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontName = "Helvetica"
    lc.lines[0].strokeColor = C_GREEN
    lc.lines[0].strokeWidth = 2
    lc.lines[1].strokeColor = C_RED
    lc.lines[1].strokeWidth = 2
    lc.lines[0].symbol = None
    lc.lines[1].symbol = None
    d.add(lc)
    return d


def _line_chart_one(series, width, height, y_min, y_max):
    """Graphique à une ligne (projection)."""
    d = Drawing(width, height)
    lc = HorizontalLineChart()
    lc.x = 38
    lc.y = 24
    lc.width = width - 50
    lc.height = height - 36
    lc.data = [series]
    lc.categoryAxis.categoryNames = [f"M{i + 1}" for i in range(len(series))]
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.fontSize = 7
    lc.categoryAxis.labels.fontName = "Helvetica"
    lc.valueAxis.valueMin = y_min
    lc.valueAxis.valueMax = y_max
    steps = 4
    lc.valueAxis.valueStep = (y_max - y_min) / steps
    lc.valueAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontName = "Helvetica"
    lc.lines[0].strokeColor = C_BLUE
    lc.lines[0].strokeWidth = 2
    lc.lines[0].symbol = None
    d.add(lc)
    return d


# ─── PAGE 8 : AGIR OU NE RIEN FAIRE ? ────────────────────────────────────────

def _build_page_simulation(edm, result: dict, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("AGIR OU NE RIEN FAIRE ?", styles))
    s.append(_hr())
    s.append(_sp(4))

    series_a = edm.action_series or []
    series_b = edm.do_nothing_series or []

    has_chart = (
        len(series_a) == 12 and len(series_b) == 12
        and any(v != 0 for v in series_a)
        and any(v != 0 for v in series_b)
    )

    if has_chart:
        y_min_v = min(min(series_b), 0)
        y_max_v = max(max(series_a), 0)
        # Arrondir aux millions
        range_v = max(abs(y_min_v), abs(y_max_v), 1_000_000)
        ceil_m = (int(range_v / 1_000_000) + 1) * 1_000_000
        y_min = -ceil_m
        y_max = ceil_m

        chart = _line_chart_two(series_a, series_b, CONTENT_W, 58 * mm, y_min, y_max)
        s.append(chart)
        s.append(_sp(2))

        # Légende
        legend_data = [[
            Paragraph('<font color="#2C7A4B"><b>■</b></font>  Avec action', styles["body_small"]),
            Paragraph('<font color="#C0392B"><b>■</b></font>  Sans action',  styles["body_small"]),
        ]]
        leg_t = Table(legend_data, colWidths=[CONTENT_W / 2, CONTENT_W / 2])
        leg_t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        s.append(leg_t)
    else:
        s.append(Paragraph("Données insuffisantes", styles["indic_miss"]))

    s.append(_sp(5))
    s.append(_hr())
    s.append(_sp(4))

    # 3 scénarios
    scenarios = result.get("scenarios") or edm.scenarios or []
    scen_map = {}
    for sc in scenarios:
        if isinstance(sc, dict):
            nom, lbl, desc = sc.get("nom", ""), sc.get("label", ""), sc.get("description", "")
        else:
            nom, lbl, desc = getattr(sc, "nom", ""), getattr(sc, "label", ""), getattr(sc, "description", "")
        n = nom.lower()
        if "best" in n or "meilleur" in n:
            scen_map["best"] = (lbl or "MEILLEUR CAS", desc)
        elif "likely" in n or "probable" in n or "most" in n:
            scen_map["likely"] = (lbl or "CAS LE PLUS PROBABLE", desc)
        elif "worst" in n or "pire" in n:
            scen_map["worst"] = (lbl or "PIRE CAS", desc)

    def _scen_block(key, default_label, head_style, border_color):
        lbl, desc = scen_map.get(key, (default_label, "Données insuffisantes"))
        inner = Table([
            [Paragraph(lbl.upper(), head_style)],
            [_sp(2)],
            [Paragraph(_rl(desc) if desc else "Données insuffisantes",
                       styles["scen_body"])],
        ], colWidths=[CONTENT_W / 3 - 6 * mm])
        inner.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        card = Table([[inner]], colWidths=[CONTENT_W / 3 - 2 * mm])
        card.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, -1), 2, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
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


# ─── PAGE 9 : QUAND RETROUVEREZ-VOUS L'ÉQUILIBRE ? ───────────────────────────

def _build_page_projection(edm, styles: dict) -> list:
    s = []
    s.append(_sp(6))
    s.append(_section_header("QUAND RETROUVEREZ-VOUS L'ÉQUILIBRE ?", styles))
    s.append(_hr())
    s.append(_sp(4))

    series = edm.monthly_projection or []
    has_chart = len(series) == 12 and any(v != 0 for v in series)

    if has_chart:
        y_max_v = max(max(series), 1)
        ceil_m = (int(y_max_v / 1_000_000) + 1) * 1_000_000
        chart = _line_chart_one(series, CONTENT_W, 56 * mm, 0, ceil_m)
        s.append(chart)
        s.append(_sp(3))
        s.append(Paragraph(
            "Trajectoire estimée sur 12 mois si les décisions prioritaires sont engagées dès maintenant.",
            styles["chart_caption"]
        ))
    else:
        s.append(Paragraph("Données insuffisantes", styles["indic_miss"]))

    s.append(PageBreak())
    return s


# ─── PAGE 10 : DÉCISION PRIORITAIRE (page finale) ─────────────────────────────

def _build_page_final(edm, styles: dict) -> list:
    s = []
    s.append(_sp(10))

    # Boîte navy principale
    top_dec = (edm.executive_decisions[0] if edm.executive_decisions else None)
    dec_text = top_dec.decision if top_dec else "Décision prioritaire non disponible"
    impact_val = top_dec.annual_impact if top_dec else None
    impact_str = _fmt_eur(impact_val, sign=True) + " / an" if impact_val else "— / an"

    box_rows = [
        [Paragraph("DÉCISION PRIORITAIRE", ParagraphStyle(
            "dp_lbl", fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.HexColor("#8899BB"), leading=13))],
        [_sp(3)],
        [Paragraph(_rl(dec_text), ParagraphStyle(
            "dp_dec", fontName="Helvetica-Bold", fontSize=16,
            textColor=C_WHITE, leading=22))],
        [_sp(3)],
        [Paragraph(impact_str, ParagraphStyle(
            "dp_imp", fontName="Helvetica-Bold", fontSize=32,
            textColor=C_AMBER, leading=38))],
    ]
    box_inner = Table(box_rows, colWidths=[CONTENT_W - 12 * mm])
    box_inner.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    dark_box = Table([[box_inner]], colWidths=[CONTENT_W])
    dark_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 7 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7 * mm),
    ]))
    s.append(dark_box)
    s.append(_sp(5))
    s.append(_hr(C_LGRAY))
    s.append(_sp(6))

    # 3 métriques sous la boîte
    coi = edm.cost_of_inaction
    prio = top_dec.priority if top_dec else "—"
    monthly_str = _fmt_eur(abs(coi.per_month)) if coi and coi.per_month else "Données insuffisantes"
    daily_str   = _fmt_eur(abs(coi.per_day))   if coi and coi.per_day   else "Données insuffisantes"

    prio_color = HEX_RED if prio and "high" in prio.lower() else HEX_AMBER

    metrics = [
        (prio or "—",       "PRIORITÉ",                    prio_color),
        (monthly_str,       "COÛT DE L'INACTION / MOIS",   HEX_RED),
        (daily_str,         "COÛT DE L'INACTION / JOUR",   HEX_RED),
    ]
    col_w = CONTENT_W / 3
    kpi_cells = []
    for val, lbl, hex_c in metrics:
        cell = Table([
            [Paragraph(f'<font color="{hex_c}"><b>{_rl(val)}</b></font>',
                       ParagraphStyle("fv", fontName="Helvetica-Bold", fontSize=18,
                                      leading=22, alignment=1))],
            [_sp(1)],
            [Paragraph(lbl, ParagraphStyle("fl", fontName="Helvetica", fontSize=7,
                                           textColor=C_GRAY, leading=10, alignment=1))],
        ], colWidths=[col_w - 4 * mm])
        cell.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        kpi_cells.append(cell)

    kpi_t = Table([kpi_cells], colWidths=[col_w] * 3)
    kpi_t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("LINEAFTER", (0, 0), (0, 0), 0.5, C_LGRAY),
        ("LINEAFTER", (1, 0), (1, 0), 0.5, C_LGRAY),
    ]))
    s.append(kpi_t)
    s.append(_sp(6))
    s.append(_hr(C_LGRAY))
    s.append(_sp(8))

    # Call to action
    horizon = top_dec.timeline if top_dec and top_dec.timeline else "cette semaine"
    s.append(Paragraph(f"Agissez {horizon.lower() if 'semaine' in (horizon or '').lower() else 'maintenant'}.",
                       styles["final_action"]))
    return s


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

def generate_pdf_report(result, company_name: str | None = None) -> bytes:
    """
    Génère le Rapport exécutif Pepperyn (10 pages).

    Args:
        result: ExecutiveCaseJSON (V2 — source unique de vérité)
                OU dict brut de l'analyse LLM (legacy — rétrocompatibilité).
        company_name: nom de la société (couverture).

    Pipeline V2 :
        - Si ExecutiveCaseJSON → adapté via case_to_edm() + case_to_result_dict()
          Garantie : PDF, PPTX et Excel affichent exactement les mêmes chiffres.
        - Si dict → comportement legacy inchangé.
    """
    if isinstance(result, ExecutiveCaseJSON):
        # ── V2 : source unique de vérité ─────────────────────────────────────
        from services.executive_case_builder import case_to_edm, case_to_result_dict
        edm        = case_to_edm(result)
        result_raw = case_to_result_dict(result)
        name       = company_name or result.company_name or "—"
        date_str   = result.analysis_date or datetime.now().strftime("%d/%m/%Y")
    else:
        # ── Legacy : comportement existant ───────────────────────────────────
        result_raw = result
        edm        = build_executive_decision_model(result)
        name       = company_name or result.get("company_name") or "—"
        date_str   = datetime.now().strftime("%d/%m/%Y")

    doc_type = "PREVISIONNEL"
    result   = result_raw   # alias pour les builders internes (inchangés)

    styles = _build_styles()

    def _story():
        # RULE 003 — Renderer Responsibility
        # Every page builder is isolated. A crash on one page never kills the document.
        # The renderer owns its presentation problems — they never reach the caller.

        def _safe_page(page_name, builder_fn):
            try:
                return list(builder_fn())
            except Exception:
                # Graceful fallback: empty page with error label — never propagate
                return [
                    PageBreak(),
                    Paragraph(f"Section {page_name} — données insuffisantes",
                               styles.get("body", getSampleStyleSheet()["Normal"])),
                    PageBreak(),
                ]

        story = []

        # P1 — Couverture (pas de header/footer sur cette page)
        try:
            story.extend(_build_cover(name, date_str, styles))
        except Exception:
            story.append(Paragraph("Couverture — données insuffisantes",
                                   styles.get("body", getSampleStyleSheet()["Normal"])))
            story.append(PageBreak())

        # P2-P11 — pages de contenu isolées (RULE 003)
        story.extend(_safe_page("Coût de l'inaction",
            lambda: _build_page_inaction(edm, result.get("risque_inaction"), styles)))
        story.extend(_safe_page("Diagnostic",
            lambda: _build_page_diagnostic(edm, result, styles)))
        story.extend(_safe_page("Santé",
            lambda: _build_page_health(result, edm, styles)))
        story.extend(_safe_page("Indicateurs",
            lambda: _build_page_indicators(result, edm, styles)))
        story.extend(_safe_page("Décisions",
            lambda: _build_page_decisions(edm, styles)))
        story.extend(_safe_page("Roadmap",
            lambda: _build_page_roadmap(edm, styles)))
        story.extend(_safe_page("Destroyers",
            lambda: _build_page_destroyers(edm, styles)))
        story.extend(_safe_page("Simulation",
            lambda: _build_page_simulation(edm, result, styles)))
        story.extend(_safe_page("Projection",
            lambda: _build_page_projection(edm, styles)))
        story.extend(_safe_page("Conclusion",
            lambda: _build_page_final(edm, styles)))

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

    # La couverture est toujours la première page → onFirstPage = rien
    # Pages 2+ → header/footer dessiné sur canvas
    def _on_first(canvas, doc):
        pass   # couverture : aucun header/footer canvas

    def _on_later(canvas, doc):
        _draw_header_footer(canvas, doc, doc_type, date_str)

    buf = io.BytesIO()
    doc = _make_doc(buf)
    try:
        doc.build(_story(), onFirstPage=_on_first, onLaterPages=_on_later)
    except Exception:
        # RULE 003 — Renderer Responsibility
        # If the ReportLab layout engine fails (e.g. LayoutError on extreme content),
        # produce a minimal valid PDF. The renderer NEVER propagates to the caller.
        from reportlab.lib.styles import getSampleStyleSheet as _gss
        buf = io.BytesIO()
        fallback = SimpleDocTemplate(buf, pagesize=A4,
                                     leftMargin=MARGIN, rightMargin=MARGIN,
                                     topMargin=22 * mm, bottomMargin=16 * mm)
        _st = _gss()
        fallback.build([
            Paragraph(f"Rapport exécutif — {name}", _st["Heading1"]),
            Spacer(1, 12 * mm),
            Paragraph("Données insuffisantes — le rapport ne peut être généré avec les données actuelles.", _st["Normal"]),
        ])

    return buf.getvalue()
