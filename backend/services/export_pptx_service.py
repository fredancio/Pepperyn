"""
export_pptx_service.py — Board Deck Pepperyn
Master de référence officiel : "Ancienne version du Powerpoint.pptx"

Structure IMMUABLE — 16 slides exactes :
  S1   EXECUTIVE DECISION (couverture)
  S2   EXECUTIVE SUMMARY (3 décisions top)
  S3   DIAGNOSTIC (Pourquoi en sommes-nous arrivés là ?)
  S4   GOUVERNANCE / CEO Dashboard (6 KPIs)
  S5   IMPACT FINANCIER (destructeurs de valeur)
  S6   DÉCISION (le coût de l'inaction)
  S7   DÉCISIONS PRIORITAIRES (table)
  S8   EXÉCUTION (roadmap 30/60/90)
  S9   SIMULATION (action vs inaction)
  S10  PROJECTION (trajectoire financière 12 mois)
  S11  RISQUES (risques majeurs)
  S12  PRIORITÉS (matrice impact/effort)
  S13  SUIVI / Carnet d'exécution (table)
  S14  PILOTAGE / Tableau de bord (table)
  S15  LUNDI MATIN (3 décisions clés)
  S16  ANNEXE (qualité données + méthodologie + engagements)

RÈGLE ABSOLUE : seules les données changent. La structure est figée.
Si une donnée est absente → "Données insuffisantes".
"""
from __future__ import annotations

import io
import math
import re
from datetime import datetime, timedelta
from typing import Any, Optional, List

from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE

from services.executive_decision_model import build_executive_decision_model
from models.executive_case import ExecutiveCaseJSON

# ─── PALETTE ─────────────────────────────────────────────────────────────────
def _rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

NAVY  = _rgb("0A2540")
BLUE  = _rgb("1B73E8")
RED   = _rgb("C0392B")
AMBER = _rgb("B8763A")
GREEN = _rgb("2C7A4B")
GRAY  = _rgb("8A9BB0")
LGRAY = _rgb("D5DCE5")
WHITE = _rgb("FFFFFF")
DARK  = _rgb("1A1A2E")
LBGRAY = _rgb("F5F7FA")

# ─── DIMENSIONS SLIDE 16:9 (33.87 cm × 19.05 cm) ────────────────────────────
SW = Inches(13.33)
SH = Inches(7.5)
ML = Inches(0.5)    # left margin
MR = Inches(0.5)    # right margin
MT = Inches(1.1)    # top (below header band)
MB = Inches(0.45)   # bottom (above footer)
CW = SW - ML - MR   # content width  ~12.33"
CH = SH - MT - MB   # content height ~5.95"


# ─── HELPERS NUMÉRIQUES ───────────────────────────────────────────────────────

def _fmt_eur(v: Optional[float]) -> str:
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    s = f"{abs_v:,.0f}".replace(",", " ")
    return f"{prefix}{s} €"


def _fmt_auto(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "Données insuffisantes"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ("+" if sign and v > 0 else "")
    if abs_v >= 950_000:
        m = abs_v / 1_000_000
        if m >= 10:
            return f"{prefix}{m:.0f} M€"
        return f"{prefix}{m:.1f} M€".replace(".", ",")
    return _fmt_eur(v)


def _safe(v, fallback: str = "Données insuffisantes") -> str:
    if v is None or v == "" or (isinstance(v, (int, float)) and v == 0):
        return fallback
    return str(v)


# ─── RULE 002 — Helpers anti-troncature ──────────────────────────────────────

def _auto_row_h(text: str, col_w_emu: int, font_pt: int, base_pt: float = 28.0) -> int:
    """
    RULE 002 — Calcule la hauteur minimale en EMU pour contenir ce texte dans
    une colonne de largeur col_w_emu, avec une police de font_pt points.
    Aucune information ne doit être visuellement tronquée.
    """
    col_w_in = col_w_emu / 914400  # EMU → inches
    # Calibri : largeur moyenne d'un caractère ≈ font_pt × 0.52 pt
    chars_per_line = max(1, int((col_w_in * 72) / (font_pt * 0.52)))
    n_lines = max(1, math.ceil(len(str(text)) / chars_per_line))
    # Interligne ≈ 1.35 × font_pt ; padding cellule ≈ 8 pt
    height_pt = n_lines * (font_pt * 1.35) + 8
    return int(Pt(max(base_pt, height_pt)))


def _fit_table_rows(tbl, text_col_idx: int, font_pt: int,
                    skip_header: bool = True, min_h_pt: float = 28.0) -> None:
    """
    RULE 002 — Ajuste les hauteurs de lignes d'un tableau python-pptx pour que
    le texte de la colonne principale (text_col_idx) ne soit jamais tronqué.
    """
    col_w_emu = tbl.columns[text_col_idx].width
    for ri in range(len(tbl.rows)):
        if skip_header and ri == 0:
            continue
        cell = tbl.cell(ri, text_col_idx)
        text = cell.text_frame.text
        needed = _auto_row_h(text, col_w_emu, font_pt, min_h_pt)
        current = tbl.rows[ri].height or 0
        if needed > current:
            tbl.rows[ri].height = needed


# ─── UTILITAIRES PYTHON-PPTX ─────────────────────────────────────────────────

def _set_para(para, text: str, size: int, bold: bool = False,
              color: RGBColor = None, align=PP_ALIGN.LEFT,
              italic: bool = False):
    para.text = ""
    run = para.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = "Calibri"
    if color:
        run.font.color.rgb = color
    para.alignment = align


def _text(slide, txt: str, l, t, w, h,
          size: int = 22, bold: bool = False,
          color: RGBColor = None, align=PP_ALIGN.LEFT,
          italic: bool = False):
    if color is None:
        color = DARK
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    _set_para(para, str(txt), size, bold=bold, color=color, align=align, italic=italic)
    return tb


def _rect(slide, l, t, w, h, fill_color: RGBColor = None, line_color: RGBColor = None):
    shape = slide.shapes.add_shape(1, l, t, w, h)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.5)
    else:
        shape.line.fill.background()
    return shape


def _header_band(slide, label: str, company: str = ""):
    _rect(slide, 0, 0, SW, Inches(0.75), fill_color=NAVY)
    _text(slide, label.upper(), ML, Inches(0.12), Inches(7), Inches(0.5),
          size=12, bold=True, color=AMBER, align=PP_ALIGN.LEFT)
    _text(slide, "PEPPERYN", SW - Inches(2), Inches(0.12), Inches(1.5), Inches(0.5),
          size=11, bold=True, color=WHITE, align=PP_ALIGN.RIGHT)
    _rect(slide, 0, Inches(0.75), SW, Pt(1), fill_color=BLUE)


def _footer_band(slide, page_num: int, company: str = ""):
    fy = SH - Inches(0.4)
    _rect(slide, 0, fy, SW, Inches(0.4), fill_color=_rgb("F0F3F7"))
    _text(slide, "Document confidentiel — usage interne réservé à la direction",
          ML, fy + Pt(4), Inches(9), Inches(0.3),
          size=9, color=GRAY, align=PP_ALIGN.LEFT)
    _text(slide, str(page_num),
          SW - Inches(1), fy + Pt(4), Inches(0.5), Inches(0.3),
          size=9, bold=True, color=GRAY, align=PP_ALIGN.RIGHT)


def _slide_title(slide, title: str, subtitle: str = ""):
    _text(slide, title, ML, MT - Inches(0.25), CW, Inches(0.55),
          size=36, bold=True, color=NAVY, align=PP_ALIGN.LEFT)
    if subtitle:
        _text(slide, subtitle, ML, MT + Inches(0.35), CW, Inches(0.3),
              size=14, color=GRAY, align=PP_ALIGN.LEFT)


# ─── SLIDE 1 : COUVERTURE ─────────────────────────────────────────────────────

def _slide_cover(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, SW, SH, fill_color=NAVY)
    _rect(slide, 0, 0, Inches(0.18), SH, fill_color=AMBER)
    _text(slide, "EXECUTIVE DECISION", Inches(0.4), Inches(0.3), Inches(10), Inches(0.4),
          size=13, bold=True, color=AMBER, align=PP_ALIGN.LEFT)
    _text(slide, company or "—", Inches(0.4), Inches(1.1), Inches(12), Inches(0.8),
          size=40, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    _text(slide, date_str, Inches(0.4), Inches(1.95), Inches(6), Inches(0.4),
          size=18, color=GRAY, align=PP_ALIGN.LEFT)
    _rect(slide, Inches(0.4), Inches(2.55), Inches(4), Pt(1.5), fill_color=AMBER)

    dec = edm.executive_decisions[0] if edm.executive_decisions else None
    dec_txt = dec.decision if dec else "Décision prioritaire non disponible"
    impact_str = (_fmt_auto(dec.annual_impact) + " / an" if dec and dec.annual_impact
                  else "Non chiffrable avec les données disponibles")

    _text(slide, "DÉCISION PRIORITAIRE", Inches(0.4), Inches(2.85), Inches(12), Inches(0.4),
          size=12, bold=True, color=BLUE, align=PP_ALIGN.LEFT)
    _text(slide, dec_txt, Inches(0.4), Inches(3.3), Inches(12.4), Inches(1.6),
          size=28, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    _text(slide, impact_str, Inches(0.4), Inches(5.0), Inches(8), Inches(0.7),
          size=34, bold=True, color=AMBER, align=PP_ALIGN.LEFT)
    _text(slide, "RAPPORT CONFIDENTIEL — USAGE INTERNE",
          Inches(0.4), SH - Inches(0.55), Inches(10), Inches(0.35),
          size=10, color=_rgb("4A5A6A"), align=PP_ALIGN.LEFT)
    _text(slide, str(page), SW - Inches(1), SH - Inches(0.55), Inches(0.5), Inches(0.35),
          size=10, color=GRAY, align=PP_ALIGN.RIGHT)


# ─── SLIDE 2 : EXECUTIVE SUMMARY ─────────────────────────────────────────────

def _slide_exec_summary(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "EXECUTIVE SUMMARY", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Synthèse des décisions prioritaires")

    decisions = edm.executive_decisions[:3]
    if not decisions:
        _text(slide, "Données insuffisantes", ML, MT + Inches(0.5), CW, Inches(1), size=22, color=GRAY)
        return

    row_h = (CH - Inches(0.6)) / 3
    row_top = MT + Inches(0.55)

    for i, dec in enumerate(decisions):
        y = row_top + i * row_h
        _rect(slide, ML, y, CW, row_h - Pt(4), fill_color=_rgb("F0F4FA"), line_color=LGRAY)
        _text(slide, f"#{i + 1}", ML + Inches(0.1), y + Inches(0.08), Inches(0.4), row_h,
              size=14, bold=True, color=BLUE)
        _text(slide, dec.decision, ML + Inches(0.55), y + Inches(0.08),
              Inches(5.8), row_h - Inches(0.15), size=14, color=DARK)
        impact_str = _fmt_auto(dec.annual_impact, sign=True) if dec.annual_impact else "—"
        _text(slide, impact_str, ML + Inches(6.5), y + Inches(0.08), Inches(1.9), Inches(0.45),
              size=16, bold=True, color=RED, align=PP_ALIGN.RIGHT)
        _text(slide, "IMPACT / AN", ML + Inches(6.5), y + Inches(0.52), Inches(1.9), Inches(0.3),
              size=9, color=GRAY, align=PP_ALIGN.RIGHT)
        roi = f"{dec.roi_score:.1f}/10" if dec.roi_score else "—"
        _text(slide, roi, ML + Inches(8.55), y + Inches(0.08), Inches(1.2), Inches(0.45),
              size=16, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        _text(slide, "SCORE ROI", ML + Inches(8.55), y + Inches(0.52), Inches(1.2), Inches(0.3),
              size=9, color=GRAY, align=PP_ALIGN.CENTER)
        horizon = dec.timeline or "—"
        _text(slide, horizon, ML + Inches(9.9), y + Inches(0.08), Inches(1.2), Inches(0.45),
              size=14, color=AMBER, align=PP_ALIGN.CENTER)
        _text(slide, "HORIZON", ML + Inches(9.9), y + Inches(0.52), Inches(1.2), Inches(0.3),
              size=9, color=GRAY, align=PP_ALIGN.CENTER)
        status = dec.status or "À lancer"
        _text(slide, status, ML + Inches(11.2), y + Inches(0.08), Inches(1.1), Inches(0.45),
              size=12, color=GREEN, align=PP_ALIGN.CENTER)
        _text(slide, "STATUT", ML + Inches(11.2), y + Inches(0.52), Inches(1.1), Inches(0.3),
              size=9, color=GRAY, align=PP_ALIGN.CENTER)


# ─── SLIDE 3 : DIAGNOSTIC ─────────────────────────────────────────────────────

def _slide_diagnostic(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "DIAGNOSTIC", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Pourquoi en sommes-nous arrivés là ?")

    diag = (result.get("diagnostic_immediat") or result.get("resume_executif")
            or result.get("synthese") or "Données insuffisantes")
    _text(slide, diag.strip(), ML, MT + Inches(0.55), CW, Inches(1.6), size=22, color=DARK)

    destroyers = edm.value_destroyers[:3]
    if destroyers:
        _text(slide, "TOP 3 DESTRUCTEURS DE VALEUR", ML, MT + Inches(2.35),
              CW, Inches(0.4), size=12, bold=True, color=AMBER)
        card_w = CW / 3 - Inches(0.1)
        for i, d in enumerate(destroyers):
            lx = ML + i * (card_w + Inches(0.15))
            ly = MT + Inches(2.8)
            _rect(slide, lx, ly, card_w, Inches(1.8), fill_color=_rgb("FBF0EE"), line_color=_rgb("E8B0A8"))
            ann_str = _fmt_auto(d.annual_impact) if d.annual_impact else "Non chiffrable"
            _text(slide, ann_str, lx + Inches(0.1), ly + Inches(0.08),
                  card_w - Inches(0.2), Inches(0.65), size=22, bold=True, color=RED)
            _text(slide, d.name, lx + Inches(0.1), ly + Inches(0.75),
                  card_w - Inches(0.2), Inches(1.0), size=13, color=DARK)


# ─── SLIDE 4 : GOUVERNANCE / CEO DASHBOARD ────────────────────────────────────

def _slide_dashboard(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "GOUVERNANCE", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "CEO Dashboard", "Indicateurs stratégiques clés")

    dashboard = result.get("ceo_dashboard") or []
    items = []
    for card in dashboard[:6]:
        if isinstance(card, dict):
            items.append(card)
        else:
            items.append({"label": getattr(card, "label", ""),
                          "value": getattr(card, "value", ""),
                          "status": getattr(card, "status", None)})
    while len(items) < 6:
        items.append({"label": "—", "value": "Données insuffisantes", "status": "missing"})

    card_w = CW / 3 - Inches(0.12)
    card_h = Inches(1.95)
    card_top_1 = MT + Inches(0.65)
    card_top_2 = card_top_1 + card_h + Inches(0.18)

    for idx, item in enumerate(items[:6]):
        row = idx // 3
        col = idx % 3
        lx = ML + col * (card_w + Inches(0.18))
        ly = card_top_1 if row == 0 else card_top_2
        is_missing = (item.get("status") == "missing" or
                      "données insuf" in str(item.get("value", "")).lower())
        border_c = LGRAY if is_missing else BLUE
        val_c = GRAY if is_missing else RED
        val = str(item.get("value", "—"))
        lbl = str(item.get("label", ""))
        _rect(slide, lx, ly, card_w, card_h, fill_color=_rgb("F5F8FF"), line_color=border_c)
        _text(slide, val, lx + Inches(0.12), ly + Inches(0.25),
              card_w - Inches(0.24), Inches(0.85),
              size=24, bold=True, color=val_c, align=PP_ALIGN.CENTER)
        _text(slide, lbl.upper(), lx + Inches(0.1), ly + Inches(1.2),
              card_w - Inches(0.2), Inches(0.5),
              size=11, bold=True, color=GRAY, align=PP_ALIGN.CENTER)


# ─── SLIDE 5 : IMPACT FINANCIER ───────────────────────────────────────────────

def _slide_impact_financier(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "IMPACT FINANCIER", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Où la valeur est détruite", "Analyse des destructeurs de valeur")

    destroyers = edm.value_destroyers[:8]
    rows = []
    for d in destroyers:
        rows.append([
            d.name,
            _fmt_auto(d.annual_impact) if d.annual_impact else "Non chiffrable",
            _fmt_eur(d.monthly_impact) if d.monthly_impact else "—",
            d.trend or "—",
        ])
    if not rows:
        rows = [["Données insuffisantes", "—", "—", "—"]]

    tbl_top = MT + Inches(0.55)
    tbl_h = CH - Inches(0.6)
    tbl = slide.shapes.add_table(len(rows) + 1, 4, ML, tbl_top, CW, tbl_h).table

    col_pct = [0.48, 0.22, 0.18, 0.12]
    for i, pct in enumerate(col_pct):
        tbl.columns[i].width = int(CW * pct)

    for ci, hdr in enumerate(["Destructeur de valeur", "Impact annuel", "Impact mensuel", "Tendance"]):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        _set_para(cell.text_frame.paragraphs[0], hdr, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        cell.margin_top = Pt(4)
        cell.margin_bottom = Pt(4)

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb("F5F8FF")
            else:
                cell.fill.background()
            fc = RED if ci == 1 else DARK
            _set_para(cell.text_frame.paragraphs[0], val, 12,
                      bold=(ci == 1), color=fc,
                      align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
    _fit_table_rows(tbl, text_col_idx=0, font_pt=12)  # RULE 002


# ─── SLIDE 6 : DÉCISION — COÛT DE L'INACTION ─────────────────────────────────

def _slide_cout_inaction(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "DÉCISION", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Le coût de l'inaction", "Si rien ne change maintenant")

    coi = edm.cost_of_inaction
    hero_str = (_fmt_eur(abs(coi.per_month)) if coi and coi.per_month
                else "Données insuffisantes")
    _text(slide, hero_str, ML, MT + Inches(0.5), Inches(8), Inches(1.15),
          size=52, bold=True, color=RED, align=PP_ALIGN.LEFT)
    _text(slide, "COÛT DE L'INACTION — PAR MOIS", ML, MT + Inches(1.7),
          Inches(8), Inches(0.35), size=13, bold=True, color=RED)
    _rect(slide, ML, MT + Inches(2.15), Inches(8), Pt(2), fill_color=RED)

    sub_vals = [
        (_fmt_eur(abs(coi.per_week)) if coi and coi.per_week else "—", "PAR SEMAINE"),
        (_fmt_eur(abs(coi.per_day))  if coi and coi.per_day  else "—", "PAR JOUR"),
        (_fmt_eur(abs(coi.per_hour)) if coi and coi.per_hour else "—", "PAR HEURE"),
    ]
    sub_w = Inches(3.5)
    for i, (val, lbl) in enumerate(sub_vals):
        lx = ML + i * (sub_w + Inches(0.5))
        _text(slide, val, lx, MT + Inches(2.4), sub_w, Inches(0.65), size=24, bold=True, color=DARK)
        _text(slide, lbl, lx, MT + Inches(3.0), sub_w, Inches(0.35), size=11, color=GRAY)

    risque = result.get("risque_inaction") or ""
    if risque:
        _rect(slide, ML, MT + Inches(3.6), CW, Inches(1.2), fill_color=_rgb("F5F8FF"), line_color=LGRAY)
        _text(slide, risque, ML + Inches(0.15), MT + Inches(3.7),
              CW - Inches(0.3), Inches(1.5), size=14, color=DARK, italic=True)


# ─── SLIDE 7 : DÉCISIONS PRIORITAIRES ────────────────────────────────────────

def _slide_decisions_prioritaires(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "DÉCISIONS PRIORITAIRES", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Plan d'action prioritaire")

    decisions = edm.executive_decisions[:8]
    rows = []
    for d in decisions:
        rows.append([
            d.decision,
            _fmt_auto(d.annual_impact, sign=True) if d.annual_impact else "Non chiffrable",
            f"{d.roi_score:.1f}/10",
            d.priority or "—",
            d.owner or "Direction",
            d.timeline or "—",
            d.status or "À lancer",
        ])
    if not rows:
        rows = [["Données insuffisantes"] + ["—"] * 6]

    col_pct = [0.26, 0.14, 0.07, 0.10, 0.13, 0.14, 0.16]
    tbl_top = MT + Inches(0.55)
    tbl_h = CH - Inches(0.6)
    tbl = slide.shapes.add_table(len(rows) + 1, 7, ML, tbl_top, CW, tbl_h).table
    for i, pct in enumerate(col_pct):
        tbl.columns[i].width = int(CW * pct)

    for ci, hdr in enumerate(["Décision", "Impact annuel", "ROI", "Priorité", "Responsable", "Horizon", "Statut"]):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        _set_para(cell.text_frame.paragraphs[0], hdr, 10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb("F5F8FF")
            else:
                cell.fill.background()
            fc = RED if ci == 1 else (AMBER if ci == 3 else DARK)
            _set_para(cell.text_frame.paragraphs[0], val, 10, color=fc,
                      align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
    _fit_table_rows(tbl, text_col_idx=0, font_pt=10, min_h_pt=32.0)  # RULE 002


# ─── SLIDE 8 : EXÉCUTION (ROADMAP 30/60/90) ──────────────────────────────────

def _slide_execution(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "EXÉCUTION", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Roadmap d'exécution — 30 / 60 / 90 jours")

    phases_edm = edm.roadmap_90_days or []
    plan_items = result.get("plan_action_30_60_90") or []

    def _phase_items(horizon: str) -> List[str]:
        for phase in phases_edm:
            if str(phase.horizon) == horizon:
                return [a.decision for a in phase.actions[:5]]
        if plan_items:
            items = []
            for p in plan_items:
                h = str(getattr(p, "horizon", None) or (p.get("horizon", "") if isinstance(p, dict) else ""))
                if h == horizon:
                    act = (getattr(p, "action", None) or p.get("action", "")) if isinstance(p, dict) else getattr(p, "action", "")
                    if act:
                        items.append(str(act))
            return items[:5]
        return []

    cols = [("30 JOURS", "30", BLUE), ("60 JOURS", "60", AMBER), ("90 JOURS", "90", GREEN)]
    col_w = CW / 3 - Inches(0.1)
    cy = MT + Inches(0.55)

    for i, (label, horizon, c) in enumerate(cols):
        lx = ML + i * (col_w + Inches(0.15))
        _rect(slide, lx, cy, col_w, Inches(0.45), fill_color=c)
        _text(slide, label, lx, cy + Pt(4), col_w, Inches(0.4),
              size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        items = _phase_items(horizon) or ["Données insuffisantes"]
        item_y = cy + Inches(0.55)
        for txt in items:
            item_h = Inches(0.65)
            _rect(slide, lx, item_y, col_w, item_h - Pt(2), fill_color=_rgb("F5F8FF"), line_color=LGRAY)
            _rect(slide, lx + Inches(0.12), item_y + Inches(0.22), Inches(0.08), Inches(0.08), fill_color=c)
            _text(slide, txt, lx + Inches(0.28), item_y + Pt(4),
                  col_w - Inches(0.38), item_h - Pt(8), size=12, color=DARK)
            item_y += item_h + Pt(3)
            if item_y > SH - Inches(0.65):
                break


# ─── SLIDE 9 : SIMULATION (Action vs Inaction) ────────────────────────────────

def _slide_simulation(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "SIMULATION", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Impact action vs inaction", "Trajectoire sur 12 mois")

    series_a = edm.action_series or []
    series_b = edm.do_nothing_series or []
    has_data = (len(series_a) == 12 and len(series_b) == 12
                and any(v != 0 for v in series_a))

    tbl_top = MT + Inches(0.55)

    if has_data:
        simplified_headers = ["", "Mois 3", "Mois 6", "Mois 9", "Mois 12"]
        rows = [
            ["Avec action (scenario central)",
             _fmt_auto(series_a[2]), _fmt_auto(series_a[5]),
             _fmt_auto(series_a[8]), _fmt_auto(series_a[11])],
            ["Sans action",
             _fmt_auto(series_b[2]), _fmt_auto(series_b[5]),
             _fmt_auto(series_b[8]), _fmt_auto(series_b[11])],
        ]
        tbl_h = Inches(1.8)
        tbl = slide.shapes.add_table(3, 5, ML, tbl_top, CW, tbl_h).table
        col_pct = [0.38, 0.155, 0.155, 0.155, 0.155]
        for i, pct in enumerate(col_pct):
            tbl.columns[i].width = int(CW * pct)
        for ci, hdr in enumerate(simplified_headers):
            cell = tbl.cell(0, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY
            _set_para(cell.text_frame.paragraphs[0], hdr, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        for ri, row in enumerate(rows):
            fc = GREEN if ri == 0 else RED
            for ci, val in enumerate(row):
                cell = tbl.cell(ri + 1, ci)
                cell.fill.background()
                _set_para(cell.text_frame.paragraphs[0], val, 13,
                          bold=(ci > 0), color=fc if ci > 0 else DARK,
                          align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
        scen_y = MT + Inches(2.55)
    else:
        _text(slide, "Données insuffisantes", ML, tbl_top, CW, Inches(1), size=22, color=GRAY)
        scen_y = MT + Inches(1.8)

    # Scénarios dans les 3 colonnes
    scenarios = result.get("scenarios") or edm.scenarios or []
    scen_map = {}
    for sc in scenarios:
        if isinstance(sc, dict):
            nom, lbl, desc = sc.get("nom", ""), sc.get("label", ""), sc.get("description", "")
        else:
            nom = getattr(sc, "nom", "")
            lbl = getattr(sc, "label", "")
            desc = getattr(sc, "description", "")
        n = nom.lower()
        if "best" in n or "meilleur" in n:
            scen_map["best"] = (lbl, desc)
        elif "likely" in n or "probable" in n or "most" in n:
            scen_map["likely"] = (lbl, desc)
        elif "worst" in n or "pire" in n:
            scen_map["worst"] = (lbl, desc)

    scen_data = [
        ("Meilleur cas",         scen_map.get("best",   ("", ""))[1], GREEN),
        ("Cas le plus probable", scen_map.get("likely", ("", ""))[1], BLUE),
        ("Pire cas",             scen_map.get("worst",  ("", ""))[1], RED),
    ]
    sw_col = CW / 3 - Inches(0.1)
    col_h = SH - scen_y - Inches(0.5)
    for i, (lbl, desc, c) in enumerate(scen_data):
        lx = ML + i * (sw_col + Inches(0.15))
        _rect(slide, lx, scen_y, sw_col, col_h, fill_color=_rgb("F5F8FF"), line_color=c)
        _text(slide, lbl.upper(), lx + Inches(0.1), scen_y + Inches(0.08),
              sw_col - Inches(0.2), Inches(0.35), size=11, bold=True, color=c)
        _text(slide, desc if desc else "Données insuffisantes",
              lx + Inches(0.1), scen_y + Inches(0.48), sw_col - Inches(0.2),
              col_h - Inches(0.6), size=11, color=DARK)


# ─── SLIDE 10 : PROJECTION ────────────────────────────────────────────────────

def _slide_projection(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "PROJECTION", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Trajectoire financière — 12 mois",
                 "Si les décisions prioritaires sont engagées maintenant")

    series = edm.monthly_projection or []
    has_data = len(series) == 12 and any(v != 0 for v in series)
    tbl_top = MT + Inches(0.55)
    tbl_h = Inches(2.2)

    if has_data:
        tbl = slide.shapes.add_table(2, 12, ML, tbl_top, CW, tbl_h).table
        for i in range(12):
            tbl.columns[i].width = int(CW / 12)
        for ci in range(12):
            cell = tbl.cell(0, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY
            _set_para(cell.text_frame.paragraphs[0], f"M{ci+1}", 10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        for ci, v in enumerate(series):
            cell = tbl.cell(1, ci)
            fc = GREEN if v >= 0 else RED
            cell.fill.background()
            _set_para(cell.text_frame.paragraphs[0], _fmt_auto(v), 11, bold=True, color=fc, align=PP_ALIGN.CENTER)
        break_even = next((i + 1 for i, v in enumerate(series) if v >= 0), None)
        msg = (f"Retour à l'équilibre estimé au mois {break_even}, sous réserve d'engagement des décisions."
               if break_even
               else "Le retour à l'équilibre n'est pas atteint sur 12 mois dans le scénario central.")
        _text(slide, msg, ML, tbl_top + tbl_h + Inches(0.2), CW, Inches(0.5),
              size=14, color=GRAY, italic=True)
    else:
        _text(slide, "Données insuffisantes", ML, tbl_top, CW, Inches(1), size=22, color=GRAY)

    coi = edm.cost_of_inaction
    if coi and coi.per_year:
        sub_y = MT + Inches(3.5)
        _rect(slide, ML, sub_y, CW, Inches(1.5), fill_color=_rgb("FBF0EE"), line_color=RED)
        _text(slide, "Coût total si aucune action sur 12 mois",
              ML + Inches(0.2), sub_y + Inches(0.15), CW - Inches(0.4), Inches(0.4),
              size=13, color=RED, bold=True)
        _text(slide, _fmt_auto(abs(coi.per_year)),
              ML + Inches(0.2), sub_y + Inches(0.6), CW - Inches(0.4), Inches(0.6),
              size=30, bold=True, color=RED)


# ─── SLIDE 11 : RISQUES ───────────────────────────────────────────────────────

def _slide_risques(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "RISQUES", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Risques majeurs identifiés")

    risques_raw = result.get("problemes_critiques") or result.get("alertes") or []
    destroyers = edm.value_destroyers
    rows = []
    for r in risques_raw[:6]:
        if isinstance(r, dict):
            desc = (r.get("description") or str(r))
            sev  = r.get("severite", "Moyen")
            imp  = r.get("impact", "Modéré")
            hor  = r.get("horizon", "Court terme")
        else:
            desc = str(r)
            sev  = "Moyen"
            imp  = "Modéré"
            hor  = "Court terme"
        rows.append([desc, sev, imp, hor])
    if not rows and destroyers:
        for d in destroyers[:5]:
            sev = "Élevé" if d.annual_impact and abs(d.annual_impact) > 500_000 else "Moyen"
            rows.append([d.name, sev, "Fort", "Immédiat"])
    if not rows:
        rows = [["Données insuffisantes", "—", "—", "—"]]

    tbl_top = MT + Inches(0.55)
    tbl_h = CH - Inches(0.6)
    tbl = slide.shapes.add_table(len(rows) + 1, 4, ML, tbl_top, CW, tbl_h).table
    col_pct = [0.50, 0.15, 0.20, 0.15]
    for i, pct in enumerate(col_pct):
        tbl.columns[i].width = int(CW * pct)
    for ci, hdr in enumerate(["Risque identifié", "Sévérité", "Impact potentiel", "Horizon"]):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        _set_para(cell.text_frame.paragraphs[0], hdr, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb("F5F8FF")
            else:
                cell.fill.background()
            fc = RED if val == "Élevé" else (AMBER if val == "Moyen" else DARK)
            if ci != 1:
                fc = DARK
            _set_para(cell.text_frame.paragraphs[0], val, 12, color=fc,
                      align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
    _fit_table_rows(tbl, text_col_idx=0, font_pt=12)  # RULE 002


# ─── SLIDE 12 : PRIORITÉS (matrice impact/effort) ────────────────────────────

def _slide_priorites(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "PRIORITÉS", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Matrice de priorisation — Impact / Effort")

    q_w = CW / 2 - Inches(0.1)
    q_h = (CH - Inches(0.6)) / 2 - Inches(0.05)
    q_l = ML
    q_t = MT + Inches(0.55)

    quads = [
        ("IMPACT ÉLEVÉ — EFFORT FAIBLE", "Démarrer immédiatement", GREEN, _rgb("EFF8F1")),
        ("IMPACT ÉLEVÉ — EFFORT FORT",   "Planifier avec soin",    AMBER,  _rgb("FDF6EC")),
        ("IMPACT FAIBLE — EFFORT FAIBLE","Opportunités rapides",   BLUE,   _rgb("EFF5FF")),
        ("IMPACT FAIBLE — EFFORT FORT",  "Déprioritiser",          GRAY,   _rgb("F5F5F5")),
    ]

    decisions = edm.executive_decisions
    q_items: list = [[], [], [], []]
    for dec in decisions:
        high_impact = dec.annual_impact and abs(dec.annual_impact) > 200_000
        dif = (dec.difficulty or "").lower()
        high_effort = "élevé" in dif or "high" in dif or "fort" in dif or "difficile" in dif
        if high_impact and not high_effort:
            q_items[0].append(dec.decision)
        elif high_impact and high_effort:
            q_items[1].append(dec.decision)
        elif not high_impact and not high_effort:
            q_items[2].append(dec.decision)
        else:
            q_items[3].append(dec.decision)

    positions = [
        (q_l,                      q_t),
        (q_l + q_w + Inches(0.2),  q_t),
        (q_l,                      q_t + q_h + Inches(0.1)),
        (q_l + q_w + Inches(0.2),  q_t + q_h + Inches(0.1)),
    ]

    for idx, ((label, subtitle, c, bg), pos) in enumerate(zip(quads, positions)):
        lx, ly = pos
        _rect(slide, lx, ly, q_w, q_h, fill_color=bg, line_color=c)
        _text(slide, label, lx + Inches(0.1), ly + Inches(0.08),
              q_w - Inches(0.2), Inches(0.4), size=10, bold=True, color=c)
        _text(slide, subtitle, lx + Inches(0.1), ly + Inches(0.48),
              q_w - Inches(0.2), Inches(0.3), size=10, color=GRAY, italic=True)
        items = q_items[idx] or ["Données insuffisantes"]
        ty = ly + Inches(0.85)
        for it in items[:3]:
            item_h = max(Inches(0.35), _auto_row_h(it, int(q_w - Inches(0.25)), 9) / 914400 * Inches(1))
            _text(slide, f"• {it}", lx + Inches(0.15), ty, q_w - Inches(0.25), item_h,
                  size=9, color=DARK)
            ty += item_h + Pt(4)
            if ty + item_h > ly + q_h:
                break


# ─── SLIDE 13 : SUIVI / CARNET D'EXÉCUTION ───────────────────────────────────

def _slide_suivi(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "SUIVI", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Carnet d'exécution")

    exec_items = edm.execution_log or []
    decisions = edm.executive_decisions
    rows = []
    if exec_items:
        for item in exec_items[:8]:
            rows.append([
                item.decision, item.owner or "Direction",
                item.due_date or "—", item.status or "À lancer",
                _fmt_auto(item.impact) if item.impact else "—",
                f"{item.roi_score:.1f}/10",
            ])
    elif decisions:
        for dec in decisions[:8]:
            rows.append([
                dec.decision, dec.owner or "Direction",
                dec.timeline or "—", dec.status or "À lancer",
                _fmt_auto(dec.annual_impact) if dec.annual_impact else "—",
                f"{dec.roi_score:.1f}/10",
            ])
    if not rows:
        rows = [["Données insuffisantes", "—", "—", "—", "—", "—"]]

    tbl_top = MT + Inches(0.55)
    tbl_h = CH - Inches(0.6)
    tbl = slide.shapes.add_table(len(rows) + 1, 6, ML, tbl_top, CW, tbl_h).table
    col_pct = [0.35, 0.14, 0.12, 0.13, 0.14, 0.12]
    for i, pct in enumerate(col_pct):
        tbl.columns[i].width = int(CW * pct)
    for ci, hdr in enumerate(["Action", "Responsable", "Horizon", "Statut", "Impact", "ROI"]):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        _set_para(cell.text_frame.paragraphs[0], hdr, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb("F5F8FF")
            else:
                cell.fill.background()
            fc = RED if ci == 4 else DARK
            _set_para(cell.text_frame.paragraphs[0], val, 11, color=fc,
                      align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
    _fit_table_rows(tbl, text_col_idx=0, font_pt=11)  # RULE 002


# ─── SLIDE 14 : PILOTAGE / TABLEAU DE BORD ───────────────────────────────────

def _slide_pilotage(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "PILOTAGE", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Tableau de bord de pilotage")

    decisions = edm.executive_decisions[:7]
    rows = []
    for dec in decisions:
        rows.append([
            dec.decision,
            _fmt_auto(dec.annual_impact) if dec.annual_impact else "Non défini",
            "À mesurer", "—", "0 %", dec.status or "À lancer",
        ])
    if not rows:
        rows = [["Données insuffisantes", "—", "—", "—", "—", "—"]]

    tbl_top = MT + Inches(0.55)
    tbl_h = CH - Inches(0.6)
    tbl = slide.shapes.add_table(len(rows) + 1, 6, ML, tbl_top, CW, tbl_h).table
    col_pct = [0.34, 0.16, 0.14, 0.12, 0.12, 0.12]
    for i, pct in enumerate(col_pct):
        tbl.columns[i].width = int(CW * pct)
    for ci, hdr in enumerate(["Décision", "Objectif", "Réalisé", "Écart", "Avancement", "Statut"]):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        _set_para(cell.text_frame.paragraphs[0], hdr, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            if ri % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb("F5F8FF")
            else:
                cell.fill.background()
            _set_para(cell.text_frame.paragraphs[0], val, 11, color=DARK,
                      align=PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER)
    _fit_table_rows(tbl, text_col_idx=0, font_pt=11)  # RULE 002


# ─── SLIDE 15 : LUNDI MATIN ───────────────────────────────────────────────────

def _slide_lundi_matin(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "LUNDI MATIN", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Ce que vous faites lundi matin",
                 "3 décisions à enclencher dès cette semaine")

    top_3 = edm.executive_decisions[:3]
    card_h = (CH - Inches(0.7)) / 3 - Inches(0.1)
    card_top = MT + Inches(0.55)

    for i in range(3):
        dec = top_3[i] if i < len(top_3) else None
        cy = card_top + i * (card_h + Inches(0.12))
        c = [RED, AMBER, BLUE][i]
        _rect(slide, ML, cy, CW, card_h, fill_color=_rgb("F5F8FF"), line_color=c)
        _text(slide, str(i + 1), ML + Inches(0.15), cy + Inches(0.08), Inches(0.45), card_h,
              size=34, bold=True, color=c, align=PP_ALIGN.CENTER)
        dec_txt = dec.decision if dec else "Données insuffisantes"
        _text(slide, dec_txt, ML + Inches(0.75), cy + Inches(0.08),
              Inches(7.5), card_h - Inches(0.1), size=16, bold=True, color=DARK)
        if dec:
            items = [
                (dec.owner or "Direction", "Responsable"),
                (_fmt_auto(dec.annual_impact) if dec.annual_impact else "—", "Impact / an"),
                (dec.timeline or "—", "Horizon"),
                (f"{min(100, int(dec.roi_score * 10))}%" if dec.roi_score else "—", "Prob. succès"),
            ]
            for j, (val, lbl) in enumerate(items):
                lx = Inches(8.5) + j * Inches(1.0)
                _text(slide, val, lx, cy + Inches(0.08), Inches(0.95), Inches(0.55),
                      size=9, bold=True, color=c, align=PP_ALIGN.CENTER)
                _text(slide, lbl, lx, cy + Inches(0.58), Inches(0.95), Inches(0.3),
                      size=8, color=GRAY, align=PP_ALIGN.CENTER)


# ─── SLIDE 16 : ANNEXE ────────────────────────────────────────────────────────

def _slide_annexe(prs, edm, result: dict, company: str, date_str: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header_band(slide, "ANNEXE", company)
    _footer_band(slide, page, company)
    _slide_title(slide, "Annexe — Qualité, Méthodologie et Engagements")

    dq = edm.data_quality
    score_data = dq.score_data if dq else (result.get("score_confiance") or 70)
    anomalies = (dq.anomalies if dq and dq.anomalies else result.get("coaching_issues") or [])
    assumptions = (dq.assumptions if dq and dq.assumptions else [])

    col_w = CW / 3 - Inches(0.12)
    col_top = MT + Inches(0.55)
    col_h = CH - Inches(0.6)

    # Colonne 1 : Qualité des données
    lx1 = ML
    _rect(slide, lx1, col_top, col_w, col_h, fill_color=_rgb("F5F8FF"), line_color=BLUE)
    _text(slide, "QUALITÉ DES DONNÉES", lx1 + Inches(0.1), col_top + Inches(0.1),
          col_w - Inches(0.2), Inches(0.4), size=11, bold=True, color=BLUE)
    _text(slide, f"Score de confiance : {score_data}%",
          lx1 + Inches(0.1), col_top + Inches(0.6), col_w - Inches(0.2), Inches(0.4),
          size=16, bold=True, color=NAVY)
    ay = col_top + Inches(1.1)
    if anomalies:
        for a in anomalies[:4]:
            _text(slide, f"• {str(a)}", lx1 + Inches(0.1), ay,
                  col_w - Inches(0.2), Inches(0.45), size=10, color=DARK)
            ay += Inches(0.43)
    else:
        _text(slide, "Aucune anomalie majeure détectée.", lx1 + Inches(0.1), ay,
              col_w - Inches(0.2), Inches(0.4), size=11, color=GREEN)

    # Colonne 2 : Hypothèses et Méthodologie
    lx2 = ML + col_w + Inches(0.18)
    _rect(slide, lx2, col_top, col_w, col_h, fill_color=_rgb("F5F8FF"), line_color=AMBER)
    _text(slide, "HYPOTHÈSES ET MÉTHODOLOGIE", lx2 + Inches(0.1), col_top + Inches(0.1),
          col_w - Inches(0.2), Inches(0.4), size=11, bold=True, color=AMBER)
    hyp = assumptions[:4] or [
        "Calculs basés sur les données soumises uniquement.",
        "Les projections supposent une mise en œuvre dans les 30 jours.",
        "Aucune extrapolation sectorielle n'a été effectuée.",
        "Le coût de l'inaction est calculé par interpolation linéaire.",
    ]
    hy = col_top + Inches(0.6)
    for h in hyp:
        _text(slide, f"• {str(h)}", lx2 + Inches(0.1), hy,
              col_w - Inches(0.2), Inches(0.45), size=10, color=DARK)
        hy += Inches(0.45)

    # Colonne 3 : Engagements Pepperyn
    lx3 = ML + 2 * (col_w + Inches(0.18))
    _rect(slide, lx3, col_top, col_w, col_h, fill_color=_rgb("F5F8FF"), line_color=NAVY)
    _text(slide, "ENGAGEMENTS PEPPERYN", lx3 + Inches(0.1), col_top + Inches(0.1),
          col_w - Inches(0.2), Inches(0.4), size=11, bold=True, color=NAVY)
    engagements = [
        "Accompagnement sur 90 jours pour l'implémentation.",
        "Révision bimensuelle des indicateurs de pilotage.",
        "Adaptation du plan en cas de changement de contexte.",
        "Disponibilité directe : equipe@pepperyn.fr",
    ]
    ey = col_top + Inches(0.6)
    for e in engagements:
        _text(slide, f"• {e}", lx3 + Inches(0.1), ey,
              col_w - Inches(0.2), Inches(0.42), size=11, color=DARK)
        ey += Inches(0.45)

    _text(slide,
          "Ce document est confidentiel et destiné exclusivement à la direction de l'entreprise cliente. "
          "Pepperyn ne garantit pas l'exactitude des projections qui dépendent des données fournies.",
          ML, SH - Inches(0.85), CW, Inches(0.35), size=9, color=GRAY, italic=True)


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

def generate_pptx_report(result: Any, company_name: Optional[str] = None) -> bytes:
    """
    Génère le Board Deck Pepperyn (16 slides).

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
        company    = company_name or result.company_name or "—"
        date_str   = result.analysis_date or datetime.now().strftime("%d %B %Y")
        result     = result_raw   # alias pour les builders internes (inchangés)
    else:
        # ── Legacy : comportement existant ───────────────────────────────────
        edm      = build_executive_decision_model(result)
        date_str = datetime.now().strftime("%d %B %Y")
        company  = company_name or result.get("company_name") or "—"

    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH

    slides_builders = [
        _slide_cover,                   # S1
        _slide_exec_summary,            # S2
        _slide_diagnostic,              # S3
        _slide_dashboard,               # S4
        _slide_impact_financier,        # S5
        _slide_cout_inaction,           # S6
        _slide_decisions_prioritaires,  # S7
        _slide_execution,               # S8
        _slide_simulation,              # S9
        _slide_projection,              # S10
        _slide_risques,                 # S11
        _slide_priorites,               # S12
        _slide_suivi,                   # S13
        _slide_pilotage,                # S14
        _slide_lundi_matin,             # S15
        _slide_annexe,                  # S16
    ]

    for page_num, builder in enumerate(slides_builders, start=1):
        try:
            builder(prs, edm, result, company, date_str, page_num)
        except Exception as exc:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            _header_band(slide, f"SLIDE {page_num}", company)
            _footer_band(slide, page_num, company)
            _text(slide, f"Slide {page_num} — Données insuffisantes",
                  ML, MT + Inches(1), CW, Inches(1), size=18, color=GRAY)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
