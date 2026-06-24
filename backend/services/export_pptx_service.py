"""
export_pptx_service.py — Executive Board Deck V6
Pepperyn Executive Board Design Specification v0.9 — Founding Partners Edition
Pepperyn — Copilote Financier Exécutif

Document de DÉCISION pour Conseil d'Administration, Comité de Direction,
comité d'investissement, banquier.

RÈGLES ABSOLUES :
  - Minimum 20pt sur tout texte de contenu (exception : metadata décorative 8pt)
  - Titres de slides : 32pt
  - 10 slides exactement
  - Aucun élément décoratif, aucun tableau, aucun remplissage

Structure narrative :
 01. EXECUTIVE DECISION         — Constat
 02. LE COÛT DE L'INACTION     — Urgence
 03. ORIGINE DU PROBLÈME       — Waterfall P&L
 04. LES TROIS DÉCISIONS       — Décisions
 05. POURQUOI CES DÉCISIONS    — Matrice Impact / Effort
 06. EBITDA BRIDGE             — Bridge
 07. AVANT / APRÈS             — Impact comparé
 08. PLAN D'EXÉCUTION          — 30 / 60 / 90 jours
 09. DÉCISION DU CONSEIL       — Vote
 10. RECOMMANDATION            — Copilote Financier
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE — figée par la spec
# ─────────────────────────────────────────────────────────────────────────────
C_WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
C_NAVY        = RGBColor(0x0A, 0x25, 0x40)
C_BLUE        = RGBColor(0x1B, 0x73, 0xE8)
C_DARK        = RGBColor(0x1A, 0x1A, 0x2E)
C_GRAY        = RGBColor(0x5F, 0x63, 0x68)
C_SLATE       = RGBColor(0x94, 0xA3, 0xB8)
C_LINE        = RGBColor(0xE2, 0xE8, 0xF0)
C_LIGHT       = RGBColor(0xF8, 0xFA, 0xFF)
C_GREEN       = RGBColor(0x05, 0x96, 0x69)
C_RED         = RGBColor(0xDC, 0x26, 0x26)
C_AMBER       = RGBColor(0xD9, 0x77, 0x06)
C_LIGHT_GREEN = RGBColor(0xD1, 0xFA, 0xE5)
C_LIGHT_RED   = RGBColor(0xFE, 0xE2, 0xE2)
C_LIGHT_AMBER = RGBColor(0xFE, 0xF3, 0xC7)
C_LIGHT_BLUE  = RGBColor(0xDB, 0xEA, 0xFE)
C_NAVY_LIGHT  = RGBColor(0x1E, 0x3A, 0x5F)

# ─────────────────────────────────────────────────────────────────────────────
# DIMENSIONS SLIDE 16:9
# ─────────────────────────────────────────────────────────────────────────────
SLIDE_W   = Inches(13.333)
SLIDE_H   = Inches(7.5)
MARGIN_L  = Inches(0.80)
MARGIN_R  = Inches(0.80)
CONTENT_W = SLIDE_W - MARGIN_L - MARGIN_R   # ≈ 11.73"
HDR_TOP   = Inches(1.42)                     # sous le titre 32pt
FTR_H     = Inches(0.38)
CONTENT_H = SLIDE_H - HDR_TOP - FTR_H - Inches(0.12)   # ≈ 5.58"

# ─────────────────────────────────────────────────────────────────────────────
# TYPOGRAPHIE — minimum 20pt pour tout texte de contenu
# ─────────────────────────────────────────────────────────────────────────────
T_META    = 8    # exception : metadata purement décorative (footer, section label)
T_TITLE   = 32   # titre de slide
T_HERO_XL = 56   # chiffre héros maximal (coût annuel inaction, couverture)
T_HERO_L  = 44   # chiffre héros grand (coût mensuel)
T_HERO_M  = 34   # chiffre héros moyen (impact décision, KPI before/after)
T_HERO_S  = 26   # chiffre héros secondaire (coût quotidien/horaire)
T_ACCENT  = 24   # sous-titres, en-têtes de blocs, badges
T_BODY    = 22   # corps de texte standard (minimum recommandé)
T_LABEL   = 20   # labels, annotations, textes secondaires (minimum absolu)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def _parse_amount(s: Optional[str]) -> float:
    """Parse '2,4M €' → 2_400_000 ; '350 K€' → 350_000 ; None → 0."""
    if not s:
        return 0.0
    text = str(s).replace('\xa0', '').replace(' ', '').replace(',', '.')
    m = re.search(r'(-?[\d.]+)\s*([MKk]?)\s*[€$£]?', text)
    if not m:
        return 0.0
    try:
        val = float(m.group(1))
        mult = m.group(2).upper()
        if mult == 'M':
            val *= 1_000_000
        elif mult == 'K':
            val *= 1_000
        return val
    except (ValueError, AttributeError):
        return 0.0


def _fmt(v: Optional[float], unit: str = '€', sign: bool = False) -> str:
    """Format compact : 2 400 000 → '2,4 M€'."""
    if v is None:
        return '—'
    abs_v = abs(v)
    pfx = ('+' if v >= 0 else '-') if sign else ('-' if v < 0 else '')
    if abs_v >= 1_000_000:
        s = f"{abs_v / 1_000_000:.1f}".rstrip('0').rstrip('.')
        return f"{pfx}{s} M{unit}"
    if abs_v >= 1_000:
        return f"{pfx}{abs_v / 1_000:.0f} K{unit}"
    return f"{pfx}{abs_v:.0f} {unit}"


def _strip_md(text: Optional[str]) -> str:
    """Supprime les marqueurs Markdown (**bold**, *italic*) du texte brut."""
    if not text:
        return ''
    return re.sub(r'\*+', '', str(text)).strip()


def _trunc(text: Optional[str], n: int) -> str:
    if not text:
        return '—'
    clean = _strip_md(text)
    return clean[:n] + '…' if len(clean) > n else clean


def _effort_score(difficulty: Optional[str]) -> float:
    """1 = facile, 2 = moyen, 3 = difficile."""
    if not difficulty:
        return 2.0
    d = difficulty.lower()
    if any(k in d for k in ('facil', 'low', 'easy', 'simple')):
        return 1.0
    if any(k in d for k in ('diffic', 'hard', 'high', 'élevé', 'complex')):
        return 3.0
    return 2.0


def _difficulty_fr(difficulty: Optional[str]) -> str:
    if not difficulty:
        return '—'
    score = _effort_score(difficulty)
    if score <= 1.0:
        return 'Facile'
    if score >= 3.0:
        return 'Difficile'
    return 'Moyen'


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVES DE DESSIN
# ─────────────────────────────────────────────────────────────────────────────

def _blank(prs: Presentation):
    """Ajoute une slide vierge (layout 6)."""
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(
    slide, left: int, top: int, width: int, height: int,
    fill: RGBColor,
    *,
    border_color: Optional[RGBColor] = None,
    border_pt: float = 0.75,
) -> Any:
    """Rectangle plein."""
    s = slide.shapes.add_shape(
        1, left, top, max(int(width), 1), max(int(height), 1)
    )
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if border_color:
        s.line.color.rgb = border_color
        s.line.width = Pt(border_pt)
    else:
        s.line.fill.background()
    return s


def _txt(
    slide, left: int, top: int, width: int, height: int,
    text: str,
    *,
    size: float,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = None,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    wrap: bool = True,
) -> Any:
    """Boîte de texte Calibri."""
    color = color or C_DARK
    txb = slide.shapes.add_textbox(left, top, max(int(width), 1), max(int(height), 1))
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = str(text) if text is not None else '—'
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = 'Calibri'
    return txb


# ─────────────────────────────────────────────────────────────────────────────
# HEADER & FOOTER COMMUNS
# ─────────────────────────────────────────────────────────────────────────────

def _header(slide, label: str, title: str):
    """Barre navy + label section (T_META) + titre 32pt (T_TITLE)."""
    _rect(slide, 0, 0, SLIDE_W, Inches(0.06), C_NAVY)
    # Metadata décorative (exception réglementaire : T_META = 8pt)
    _txt(slide, MARGIN_L, Inches(0.10), Inches(7), Inches(0.22),
         label.upper(), size=T_META, bold=True, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(2.6), Inches(0.10), Inches(2.4), Inches(0.22),
         'PEPPERYN · CONFIDENTIEL', size=T_META, color=C_SLATE, align=PP_ALIGN.RIGHT)
    # Titre principal — jamais moins de T_TITLE (32pt)
    _txt(slide, MARGIN_L, Inches(0.32), CONTENT_W, Inches(0.90),
         title, size=T_TITLE, bold=True, color=C_NAVY)
    # Séparateur navy sous le titre
    _rect(slide, MARGIN_L, Inches(1.28), CONTENT_W, Emu(28000), C_NAVY)


def _footer(slide, num: int, date_str: str = ''):
    """Footer discret — T_META uniquement."""
    _rect(slide, 0, SLIDE_H - FTR_H, SLIDE_W, FTR_H, C_LIGHT)
    _txt(slide, MARGIN_L, SLIDE_H - FTR_H + Inches(0.06),
         Inches(7), FTR_H - Inches(0.08),
         f'Pepperyn · Document confidentiel · {date_str}',
         size=T_META, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(1.8), SLIDE_H - FTR_H + Inches(0.06),
         Inches(1.6), FTR_H - Inches(0.08),
         f'{num:02d} / 10', size=T_META, bold=True, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# WATERFALL / BRIDGE  (20pt labels, 22pt values)
# ─────────────────────────────────────────────────────────────────────────────

def _waterfall(
    slide,
    items: List[dict],
    left: int, top: int, width: int, height: int,
):
    """
    Waterfall McKinsey. Labels ≥ 20pt, valeurs ≥ 22pt.
    items : [{'label', 'value', 'type': 'start'|'delta'|'end'}]
    """
    if not items:
        return
    n = len(items)

    # Calcul des positions (from_v, to_v) pour chaque barre
    cumul = 0.0
    positions: List[tuple] = []
    for item in items:
        if item['type'] == 'start':
            positions.append((0.0, item['value']))
            cumul = item['value']
        elif item['type'] == 'end':
            positions.append((0.0, item['value']))
        else:
            positions.append((cumul, cumul + item['value']))
            cumul += item['value']

    all_v = [v for p in positions for v in p]
    max_v = max(all_v) * 1.06
    min_v = min(0.0, min(all_v)) * 1.06 if min(all_v) < 0 else 0.0
    v_range = max(max_v - min_v, 1.0)

    label_zone = Inches(0.95)           # 20pt sur 2 lignes max
    val_zone   = Inches(0.40)           # espace pour valeur au-dessus de la barre
    chart_h    = height - label_zone - val_zone
    chart_top  = top + val_zone
    chart_bottom = chart_top + chart_h

    col_w = width / n
    bar_w = int(col_w * 0.56)

    def vy(v: float) -> int:
        frac = (v - min_v) / v_range
        return int(chart_bottom - frac * chart_h)

    # Axe zéro
    zero_y = vy(0)
    _rect(slide, left, zero_y, width, Emu(14000), C_LINE)

    cumul = 0.0
    for i, item in enumerate(items):
        fv, tv = positions[i]
        bar_left = int(left + i * col_w + (col_w - bar_w) / 2)
        y_hi = min(vy(fv), vy(tv))
        y_lo = max(vy(fv), vy(tv))
        bar_h = max(y_lo - y_hi, Emu(22000))

        if item['type'] in ('start', 'end'):
            color = C_NAVY if item['value'] <= 0 else C_BLUE
        else:
            color = C_RED if item['value'] < 0 else C_GREEN

        _rect(slide, bar_left, y_hi, bar_w, bar_h, color)

        # Connecteur vers la barre suivante
        if i < n - 1 and item['type'] != 'end':
            next_bar_left = int(left + (i + 1) * col_w + (col_w - bar_w) / 2)
            conn_y = vy(tv)
            _rect(slide, bar_left + bar_w, conn_y - Emu(6000),
                  next_bar_left - bar_left - bar_w, Emu(12000), C_SLATE)

        # Valeur au-dessus/en-dessous (T_BODY = 22pt)
        # Pour les deltas négatifs : sous la barre seulement si la barre est
        # assez éloignée de la label_zone ; sinon, au-dessus (évite chevauchement).
        val_str = _fmt(item['value'], sign=(item['type'] == 'delta'))
        is_neg_delta = (item['type'] == 'delta' and item['value'] < 0)
        if is_neg_delta and y_lo < chart_bottom - Inches(0.54):
            lbl_y = y_lo + Inches(0.05)
        else:
            lbl_y = y_hi - Inches(0.40)
        _txt(slide, bar_left - Inches(0.15), int(lbl_y),
             bar_w + Inches(0.30), Inches(0.38),
             val_str, size=T_BODY, bold=True,
             color=C_RED if is_neg_delta else C_DARK,
             align=PP_ALIGN.CENTER)

        # Label catégorie en bas (T_LABEL = 20pt)
        _txt(slide,
             bar_left - Inches(0.18),
             int(chart_bottom + Inches(0.08)),
             bar_w + Inches(0.36),
             label_zone - Inches(0.08),
             item['label'],
             size=T_LABEL, color=C_GRAY, align=PP_ALIGN.CENTER, wrap=True)

        if item['type'] == 'delta':
            cumul += item['value']
        elif item['type'] == 'start':
            cumul = item['value']


# ─────────────────────────────────────────────────────────────────────────────
# PLAN 90 JOURS — 3 colonnes (remplace le Gantt)
# ─────────────────────────────────────────────────────────────────────────────

def _plan_columns(slide, phases, left: int, top: int, width: int, height: int):
    """
    3 colonnes STABILISER / OPTIMISER / ACCÉLÉRER.
    Max 2 actions par colonne. Textes ≥ 20pt.
    """
    PHASE_CFG = {
        '30': {'label': 'STABILISER', 'sublabel': 'J0 — J30',  'color': C_BLUE,  'bg': C_LIGHT_BLUE},
        '60': {'label': 'OPTIMISER',  'sublabel': 'J30 — J60', 'color': C_NAVY,  'bg': C_LIGHT},
        '90': {'label': 'ACCÉLÉRER',  'sublabel': 'J60 — J90', 'color': C_GREEN, 'bg': C_LIGHT_GREEN},
    }

    col_gap   = Inches(0.28)
    col_w     = (width - col_gap * 2) / 3
    hdr_h     = Inches(0.72)
    sub_h     = Inches(0.34)
    card_h    = Inches(1.90)
    card_gap  = Inches(0.18)
    card_top  = top + hdr_h + sub_h + Inches(0.22)

    for ci, (horizon, cfg) in enumerate(PHASE_CFG.items()):
        cx = left + ci * (col_w + col_gap)

        # En-tête colonne
        _rect(slide, int(cx), int(top), int(col_w), int(hdr_h), cfg['color'])
        _txt(slide, int(cx + Inches(0.16)), int(top + Inches(0.14)),
             int(col_w - Inches(0.32)), int(hdr_h - Inches(0.14)),
             cfg['label'], size=T_ACCENT, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER)

        # Sous-label période
        _txt(slide, int(cx), int(top + hdr_h + Inches(0.06)),
             int(col_w), int(sub_h),
             cfg['sublabel'], size=T_LABEL, color=C_GRAY, align=PP_ALIGN.CENTER)

        # Récupération actions de la phase correspondante
        phase_actions: list = []
        for phase in phases:
            if str(phase.horizon) == horizon:
                phase_actions = (phase.actions or [])[:2]
                break

        if not phase_actions:
            # Placeholder vide
            _rect(slide, int(cx), int(card_top),
                  int(col_w), int(card_h), cfg['bg'],
                  border_color=cfg['color'], border_pt=1.0)
            _txt(slide, int(cx + Inches(0.16)), int(card_top + Inches(0.70)),
                 int(col_w - Inches(0.32)), Inches(0.50),
                 'Aucune action définie.', size=T_LABEL, color=C_SLATE,
                 align=PP_ALIGN.CENTER)
            continue

        for ai, act in enumerate(phase_actions):
            cy = int(card_top + ai * (card_h + card_gap))

            _rect(slide, int(cx), cy, int(col_w), int(card_h),
                  cfg['bg'], border_color=cfg['color'], border_pt=1.2)
            _rect(slide, int(cx), cy, Inches(0.08), int(card_h), cfg['color'])

            # Action label (T_BODY)
            _txt(slide, int(cx + Inches(0.22)), cy + Inches(0.14),
                 int(col_w - Inches(0.30)), Inches(0.80),
                 _trunc(act.decision, 55), size=T_BODY, bold=True, color=C_DARK,
                 wrap=True)

            # Responsable (T_LABEL)
            if act.owner:
                _txt(slide, int(cx + Inches(0.22)), cy + Inches(1.00),
                     int(col_w - Inches(0.30)), Inches(0.34),
                     f'Resp. : {act.owner}', size=T_LABEL, color=C_GRAY)

            # Impact (T_BODY)
            if act.impact:
                _txt(slide, int(cx + Inches(0.22)), cy + Inches(1.40),
                     int(col_w - Inches(0.30)), Inches(0.36),
                     _fmt(act.impact, sign=True), size=T_BODY, bold=True,
                     color=C_GREEN if (act.impact or 0) > 0 else C_RED)


# ─────────────────────────────────────────────────────────────────────────────
# MATRICE IMPACT / EFFORT  (20pt minimum)
# ─────────────────────────────────────────────────────────────────────────────

def _matrix(slide, decisions, left: int, top: int, width: int, height: int):
    """Matrice Impact / Effort avec quadrants colorés. Labels ≥ 20pt."""
    mid_x = left + width // 2
    mid_y = top  + height // 2
    ax_lbl_h = Inches(0.36)
    chart_h  = height - ax_lbl_h

    quadrants = [
        (left,  top,       'QUICK WINS ★', C_GREEN,  C_LIGHT_GREEN),
        (mid_x, top,       'INVESTIR',     C_BLUE,   C_LIGHT_BLUE),
        (left,  mid_y,     'DÉLÉGUER',     C_GRAY,   C_LIGHT),
        (mid_x, mid_y,     'ÉVITER',       C_AMBER,  C_LIGHT_AMBER),
    ]

    q_w = width // 2
    q_h = chart_h // 2

    for qx, qy, qlabel, qcolor, qbg in quadrants:
        _rect(slide, qx, qy, q_w, q_h, qbg, border_color=qcolor, border_pt=0.5)
        _txt(slide, qx + Inches(0.14), qy + Inches(0.10), q_w - Inches(0.20), Inches(0.36),
             qlabel, size=T_LABEL, bold=True, color=qcolor)

    # Séparateurs centraux
    _rect(slide, mid_x - Emu(8000), top, Emu(16000), chart_h, C_LINE)
    _rect(slide, left, mid_y - Emu(8000), width, Emu(16000), C_LINE)

    # Axe X — label (T_LABEL = 20pt)
    _txt(slide, left, top + chart_h + Inches(0.04), width, ax_lbl_h,
         '◄  EFFORT FAIBLE                                    EFFORT ÉLEVÉ  ►',
         size=T_LABEL, color=C_SLATE, align=PP_ALIGN.CENTER)

    # Points décisions
    ds = Inches(0.46)
    for i, dec in enumerate(decisions):
        impact = abs(dec.annual_impact or 1)
        effort = _effort_score(dec.difficulty)
        norm_x = (effort - 1) / 2      # 0→1
        norm_y = 1.0 - min(impact / max(abs(d.annual_impact or 1) for d in decisions), 1.0)

        dot_cx = int(left + norm_x * width)
        dot_cy = int(top  + norm_y * chart_h)

        _rect(slide, dot_cx - ds // 2, dot_cy - ds // 2, ds, ds, C_NAVY,
              border_color=C_WHITE, border_pt=2.0)
        _txt(slide, dot_cx - ds // 2, dot_cy - ds // 2, ds, ds,
             str(i + 1), size=T_LABEL, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 01 — EXECUTIVE DECISION (couverture)
# ─────────────────────────────────────────────────────────────────────────────

def _s01_cover(prs, edm, company: str, date_str: str):
    slide = _blank(prs)

    # Fond sombre McKinsey
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = C_NAVY

    # Bande accent gauche
    _rect(slide, 0, 0, Inches(0.12), SLIDE_H, C_BLUE)

    # Labels cadre (metadata — T_META)
    _txt(slide, Inches(0.28), Inches(0.18), Inches(6), Inches(0.32),
         'EXECUTIVE DECISION', size=T_META + 2, bold=True, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(3.0), Inches(0.18), Inches(2.8), Inches(0.32),
         'PEPPERYN · CONFIDENTIEL', size=T_META + 1, color=C_SLATE, align=PP_ALIGN.RIGHT)

    # Nom société — T_HERO_XL (56pt)
    _txt(slide, Inches(0.28), Inches(0.56), SLIDE_W - Inches(0.56), Inches(1.40),
         company or '—', size=T_HERO_XL, bold=True, color=C_WHITE)

    # Séparateur bleu
    _rect(slide, Inches(0.28), Inches(2.10), SLIDE_W - Inches(0.40), Emu(45000), C_BLUE)

    # Date + gain potentiel
    decisions = (edm.executive_decisions or [])
    total_gain = sum(d.annual_impact or 0 for d in decisions if (d.annual_impact or 0) > 0)
    gain_str = _fmt(total_gain) if total_gain > 0 else '—'

    _txt(slide, Inches(0.28), Inches(2.28), Inches(5.5), Inches(0.38),
         f'{date_str} · CONFIDENTIEL', size=T_LABEL, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(4.5), Inches(2.28), Inches(4.2), Inches(0.38),
         f'Gain identifié : {gain_str} / an', size=T_LABEL, bold=True,
         color=C_GREEN, align=PP_ALIGN.RIGHT)

    # Décision prioritaire — grand italique blanc (T_HERO_S = 26pt)
    top_decision = _strip_md(decisions[0].decision) if decisions else ''
    if top_decision:
        _txt(slide, Inches(0.28), Inches(2.88), SLIDE_W - Inches(0.56), Inches(3.20),
             f'« {top_decision} »',
             size=T_HERO_S + 4, italic=True, color=C_WHITE, wrap=True)

    # Footer
    _rect(slide, 0, SLIDE_H - Inches(0.55), SLIDE_W, Inches(0.55), C_NAVY_LIGHT)
    _txt(slide, Inches(0.28), SLIDE_H - Inches(0.50), SLIDE_W - Inches(0.56), Inches(0.44),
         'Pepperyn · Copilote Financier Exécutif',
         size=T_LABEL, color=C_SLATE, align=PP_ALIGN.CENTER)
    _txt(slide, SLIDE_W - Inches(2.0), SLIDE_H - Inches(0.50),
         Inches(1.80), Inches(0.44),
         '01 / 10', size=T_META + 2, bold=True, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 02 — LE COÛT DE L'INACTION
# ─────────────────────────────────────────────────────────────────────────────

def _s02_inaction(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '02 — URGENCE', 'Le coût de l\'inaction.')
    _footer(slide, 2, date_str)

    coi = edm.cost_of_inaction
    if not coi:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Données de coût d\'inaction non disponibles.', size=T_LABEL, color=C_GRAY)
        return

    # Hiérarchie des tailles calibrée pour tenir dans CONTENT_H sans chevauchement
    # Les tailles sont ajustées pour que label (20pt) + valeur + gap rentrent par ligne
    ALL_PERIODS = [
        ('PAR AN',      coi.per_year,  44),
        ('PAR MOIS',    coi.per_month, 34),
        ('PAR SEMAINE', coi.per_week,  26),
        ('PAR JOUR',    coi.per_day,   22),
        ('PAR HEURE',   coi.per_hour,  20),
    ]
    periods = [(lbl, v, sz) for lbl, v, sz in ALL_PERIODS if v is not None]
    if not periods:
        return

    # Positionnement dynamique : chaque item occupe exactement label_h + value_h + gap
    LABEL_H  = Inches(0.28)    # 20pt sur 1 ligne
    GAP_H    = Inches(0.10)    # espace entre items
    PHRASE_H = Inches(0.84)    # boîte conclusion en bas
    PHRASE_M = Inches(0.22)    # marge avant la conclusion

    cur_y = HDR_TOP + Inches(0.12)

    for idx, (label, value, font_sz) in enumerate(periods):
        value_h = Inches(font_sz / 72.0 * 1.35)   # hauteur de la valeur en inches

        # Barre accent rouge pour PAR AN
        if idx == 0:
            _rect(slide, MARGIN_L, int(cur_y),
                  Inches(0.08), int(LABEL_H + value_h), C_RED)

        # Label période (T_LABEL = 20pt)
        _txt(slide, MARGIN_L + Inches(0.22), int(cur_y),
             Inches(4.0), LABEL_H,
             label, size=T_LABEL, bold=True, color=C_SLATE)

        # Valeur (taille dégressive)
        _txt(slide, MARGIN_L + Inches(0.22), int(cur_y + LABEL_H),
             CONTENT_W - Inches(0.28), int(value_h),
             _fmt(value), size=float(font_sz), bold=True,
             color=C_RED if idx == 0 else (C_DARK if idx < 2 else C_GRAY))

        cur_y += LABEL_H + value_h + GAP_H

    # Phrase choc (T_ACCENT = 24pt) — en bas, calée sur l'espace restant
    phrase_y = SLIDE_H - FTR_H - PHRASE_H - Inches(0.10)
    _rect(slide, MARGIN_L, int(phrase_y),
          CONTENT_W, int(PHRASE_H), C_LIGHT)
    _txt(slide, MARGIN_L + Inches(0.18), int(phrase_y + Inches(0.18)),
         CONTENT_W - Inches(0.36), int(PHRASE_H - Inches(0.20)),
         'Chaque heure sans décision détruit de la valeur.',
         size=T_ACCENT, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 03 — ORIGINE DU PROBLÈME (Waterfall P&L)
# ─────────────────────────────────────────────────────────────────────────────

def _s03_waterfall(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '03 — ORIGINE', 'D\'où vient le problème ?')
    _footer(slide, 3, date_str)

    ebitda_val  = _parse_amount(edm.ebitda)
    destroyers  = edm.value_destroyers or []

    total_destr = sum(abs(d.annual_impact or 0) for d in destroyers if (d.annual_impact or 0) < 0)
    if total_destr == 0:
        total_destr = sum(abs(d.annual_impact or 0) for d in destroyers)
    revenue = ebitda_val + total_destr if total_destr > 0 else max(abs(ebitda_val) * 4, 1_000_000)

    items: List[dict] = [{'label': "CA", 'value': revenue, 'type': 'start'}]

    if destroyers:
        shown_sum = 0.0
        for d in destroyers[:5]:
            impact_v = -(abs(d.annual_impact or 0))
            items.append({'label': _trunc(d.name, 12), 'value': impact_v, 'type': 'delta'})
            shown_sum += abs(impact_v)
        residual = total_destr - shown_sum
        if residual > 10_000:
            items.append({'label': 'Autres', 'value': -residual, 'type': 'delta'})
    else:
        for lbl, pct in [('Salaires', 0.38), ('Sous-trt.', 0.18),
                          ('Loyers', 0.10), ('Autres', 0.14)]:
            items.append({'label': lbl, 'value': -(revenue * pct), 'type': 'delta'})

    items.append({'label': 'EBITDA', 'value': ebitda_val, 'type': 'end'})

    _waterfall(slide, items,
               left=MARGIN_L,
               top=HDR_TOP + Inches(0.12),
               width=CONTENT_W,
               height=CONTENT_H - Inches(0.12))


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 04 — LES TROIS DÉCISIONS
# ─────────────────────────────────────────────────────────────────────────────

def _s04_decisions(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '04 — DÉCISIONS', 'Les trois décisions.')
    _footer(slide, 4, date_str)

    decisions = (edm.executive_decisions or [])[:3]
    if not decisions:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision identifiée dans l\'analyse.', size=T_LABEL, color=C_GRAY)
        return

    n        = len(decisions)
    card_gap = Inches(0.26)
    card_w   = (CONTENT_W - card_gap * (n - 1)) / n
    card_top = HDR_TOP + Inches(0.10)
    card_h   = CONTENT_H - Inches(0.10)

    ACCENT_COLORS = [C_BLUE, C_NAVY, C_SLATE]

    for i, dec in enumerate(decisions):
        cx  = MARGIN_L + i * (card_w + card_gap)
        acc = ACCENT_COLORS[i % len(ACCENT_COLORS)]

        # Fond carte
        _rect(slide, int(cx), int(card_top), int(card_w), int(card_h),
              C_LIGHT, border_color=C_LINE, border_pt=1.0)
        # Barre couleur en haut
        _rect(slide, int(cx), int(card_top), int(card_w), Inches(0.08), acc)

        # Badge numéro — T_ACCENT (24pt)
        badge_s = Inches(0.50)
        _rect(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.16)),
              int(badge_s), int(badge_s), acc)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.16)),
             int(badge_s), int(badge_s), str(i + 1),
             size=T_ACCENT, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Décision texte — T_BODY (22pt bold), max 2 lignes
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.80)),
             int(card_w - Inches(0.36)), Inches(1.00),
             _trunc(dec.decision, 42), size=T_BODY, bold=True, color=C_DARK, wrap=True)

        # Séparateur
        _rect(slide, int(cx + Inches(0.18)), int(card_top + Inches(1.92)),
              int(card_w - Inches(0.36)), Emu(16000), C_LINE)

        # Impact annuel — hero T_HERO_M (34pt)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(2.06)),
             int(card_w - Inches(0.36)), Inches(0.34),
             'Impact annuel', size=T_LABEL, color=C_SLATE)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(2.40)),
             int(card_w - Inches(0.36)), Inches(0.56),
             _fmt(dec.annual_impact),
             size=T_HERO_M, bold=True,
             color=C_GREEN if (dec.annual_impact or 0) > 0 else C_RED)

        # Séparateur
        _rect(slide, int(cx + Inches(0.18)), int(card_top + Inches(3.04)),
              int(card_w - Inches(0.36)), Emu(14000), C_LINE)

        # Grille 2×2 métriques (T_LABEL labels, T_BODY valeurs)
        half_w = int((card_w - Inches(0.44)) / 2)
        fields = [
            ('ROI Score',    f"{dec.roi_score:.1f} / 10" if dec.roi_score else '—', C_DARK),
            ('Difficulté',   _difficulty_fr(dec.difficulty),                         C_DARK),
            ('Délai',        _trunc(dec.timeline, 18) or '—',                        C_DARK),
            ('Responsable',  _trunc(dec.owner, 18) or '—',                           C_DARK),
        ]
        for j, (lbl, val, vc) in enumerate(fields):
            col = j % 2
            row = j // 2
            mx  = int(cx + Inches(0.18) + col * (half_w + Inches(0.08)))
            my  = int(card_top + Inches(3.18) + row * Inches(0.76))

            _txt(slide, mx, my, half_w, Inches(0.30), lbl,
                 size=T_LABEL, color=C_SLATE)
            _txt(slide, mx, my + Inches(0.30), half_w, Inches(0.36),
                 val, size=T_BODY, bold=True, color=vc)

        # Priorité
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(4.76)),
             int(card_w - Inches(0.36)), Inches(0.30),
             'Priorité', size=T_LABEL, color=C_SLATE)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(5.06)),
             int(card_w - Inches(0.36)), Inches(0.38),
             dec.priority or '—', size=T_BODY, bold=True, color=acc)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 05 — POURQUOI CES DÉCISIONS (Matrice)
# ─────────────────────────────────────────────────────────────────────────────

def _s05_matrix(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '05 — PRIORISATION', 'Pourquoi ces décisions ?')
    _footer(slide, 5, date_str)

    decisions = (edm.executive_decisions or [])[:3]
    if not decisions:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision disponible pour la matrice.', size=T_LABEL, color=C_GRAY)
        return

    matrix_w = int(CONTENT_W * 0.58)
    legend_x = MARGIN_L + matrix_w + Inches(0.50)
    legend_w = CONTENT_W - matrix_w - Inches(0.50)

    _matrix(slide, decisions,
            left=MARGIN_L,
            top=HDR_TOP + Inches(0.10),
            width=matrix_w,
            height=int(CONTENT_H - Inches(0.10)))

    # Légende droite (T_LABEL minimum = 20pt)
    _txt(slide, int(legend_x), int(HDR_TOP + Inches(0.10)),
         int(legend_w), Inches(0.36),
         'DÉCISIONS', size=T_ACCENT, bold=True, color=C_NAVY)

    for i, dec in enumerate(decisions):
        ly = int(HDR_TOP + Inches(0.60) + i * Inches(1.60))

        # Badge numéro
        _rect(slide, int(legend_x), ly, Inches(0.40), Inches(0.40), C_NAVY)
        _txt(slide, int(legend_x), ly, Inches(0.40), Inches(0.40),
             str(i + 1), size=T_LABEL, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER)

        # Texte décision (T_LABEL = 20pt)
        _txt(slide, int(legend_x + Inches(0.50)), ly,
             int(legend_w - Inches(0.50)), Inches(0.56),
             _trunc(dec.decision, 48), size=T_LABEL, bold=True, color=C_DARK,
             wrap=True)

        # Impact + difficulté (T_LABEL = 20pt)
        _txt(slide, int(legend_x + Inches(0.50)), ly + Inches(0.58),
             int(legend_w - Inches(0.50)), Inches(0.30),
             f'{_fmt(dec.annual_impact)}  ·  {_difficulty_fr(dec.difficulty)}',
             size=T_LABEL, color=C_GRAY)

        # Séparateur léger
        if i < len(decisions) - 1:
            _rect(slide, int(legend_x), ly + Inches(1.05),
                  int(legend_w), Emu(10000), C_LINE)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 06 — EBITDA BRIDGE
# ─────────────────────────────────────────────────────────────────────────────

def _s06_bridge(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '06 — IMPACT', 'EBITDA Bridge.')
    _footer(slide, 6, date_str)

    ebitda_now = _parse_amount(edm.ebitda)
    decisions  = (edm.executive_decisions or [])[:3]

    items: List[dict] = [{'label': 'EBITDA\nactuel', 'value': ebitda_now, 'type': 'start'}]
    total_impact = 0.0
    for i, dec in enumerate(decisions):
        impact = dec.annual_impact or 0
        label  = _trunc(dec.decision, 12)
        items.append({'label': label, 'value': impact, 'type': 'delta'})
        total_impact += impact

    items.append({'label': 'EBITDA\nprojeté', 'value': ebitda_now + total_impact, 'type': 'end'})

    _waterfall(slide, items,
               left=MARGIN_L,
               top=HDR_TOP + Inches(0.12),
               width=CONTENT_W,
               height=CONTENT_H - Inches(0.56))

    # Conclusion obligatoire (T_ACCENT = 24pt)
    if ebitda_now != 0 and total_impact != 0:
        reduction_pct = abs(total_impact / ebitda_now * 100)
        msg = (f'Les décisions proposées améliorent l\'EBITDA de {_fmt(total_impact, sign=True)} '
               f'({reduction_pct:.0f} %).')
    else:
        msg = f'Gain total projeté : {_fmt(total_impact, sign=True)}'

    _txt(slide, MARGIN_L, SLIDE_H - FTR_H - Inches(0.54),
         CONTENT_W, Inches(0.44),
         msg, size=T_ACCENT, bold=True,
         color=C_GREEN if total_impact >= 0 else C_RED,
         align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 07 — AVANT / APRÈS
# ─────────────────────────────────────────────────────────────────────────────

def _s07_before_after(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '07 — IMPACT', 'Avant / Après.')
    _footer(slide, 7, date_str)

    ebitda_now  = _parse_amount(edm.ebitda)
    cash_now    = _parse_amount(edm.available_cash)
    decisions   = edm.executive_decisions or []
    total_gain  = sum(d.annual_impact or 0 for d in decisions[:3] if (d.annual_impact or 0) > 0)
    ebitda_after = ebitda_now + total_gain
    cash_after   = cash_now + total_gain * 0.6

    burn_now   = abs(ebitda_now / 12) if ebitda_now < 0 else None
    burn_after = abs(ebitda_after / 12) if ebitda_after < 0 else None
    runway_now   = (f"{cash_now / burn_now:.0f} mois" if burn_now and cash_now > 0 else
                    ('∞' if ebitda_now >= 0 else '—'))
    runway_after = (f"{cash_after / burn_after:.0f} mois" if burn_after and cash_after > 0 else '∞')

    destroyers  = edm.value_destroyers or []
    rev_est     = ebitda_now + sum(abs(d.annual_impact or 0) for d in destroyers)
    margin_now  = f"{ebitda_now / rev_est * 100:.1f} %" if rev_est > 0 else '—'
    margin_aft  = f"{ebitda_after / rev_est * 100:.1f} %" if rev_est > 0 else '—'

    kpis = [
        ('EBITDA',   _fmt(ebitda_now), _fmt(ebitda_after),  ebitda_after > ebitda_now),
        ('Cash',     _fmt(cash_now),   _fmt(cash_after),    cash_after > cash_now),
        ('Marge',    margin_now,        margin_aft,          True),
        ('Runway',   runway_now,        runway_after,         True),
    ]

    col_w   = int((CONTENT_W - Inches(0.50)) / 2)
    col_l   = MARGIN_L
    col_r   = MARGIN_L + col_w + Inches(0.50)
    col_top = HDR_TOP + Inches(0.12)
    kpi_h   = (CONTENT_H - Inches(0.62)) / len(kpis)

    # En-têtes colonnes (T_ACCENT = 24pt)
    for cx, lbl, bg, fc in [
        (col_l, "AUJOURD'HUI",    C_LIGHT_RED,   C_RED),
        (col_r, 'APRÈS DÉCISIONS', C_LIGHT_GREEN, C_GREEN),
    ]:
        _rect(slide, int(cx), int(col_top), int(col_w), Inches(0.54), bg)
        _txt(slide, int(cx + Inches(0.14)), int(col_top + Inches(0.09)),
             int(col_w - Inches(0.28)), Inches(0.38),
             lbl, size=T_ACCENT, bold=True, color=fc, align=PP_ALIGN.CENTER)

    # Séparateur central
    mid_x = int(MARGIN_L + col_w + Inches(0.25))
    _rect(slide, mid_x - Emu(7000), int(col_top), Emu(14000), int(CONTENT_H), C_LINE)

    # Lignes KPI
    for i, (name, val_now, val_aft, improved) in enumerate(kpis):
        ky = int(col_top + Inches(0.64) + i * kpi_h)

        for cx, val, is_after in [(col_l, val_now, False), (col_r, val_aft, True)]:
            _rect(slide, int(cx + Inches(0.06)), ky,
                  int(col_w - Inches(0.12)), int(kpi_h - Inches(0.08)), C_LIGHT)
            # Nom KPI (T_LABEL = 20pt)
            _txt(slide, int(cx + Inches(0.20)), ky + Inches(0.06),
                 int(col_w - Inches(0.40)), Inches(0.32),
                 name, size=T_LABEL, color=C_SLATE)
            # Valeur KPI (T_HERO_M = 34pt)
            v_color = (C_GREEN if improved else C_RED) if is_after else C_DARK
            _txt(slide, int(cx + Inches(0.20)), ky + Inches(0.36),
                 int(col_w - Inches(0.40)), kpi_h - Inches(0.48),
                 val, size=T_HERO_M, bold=True, color=v_color)

        # Flèche centrale (T_BODY = 22pt)
        _txt(slide, mid_x - Inches(0.28), int(ky + kpi_h / 2 - Inches(0.18)),
             Inches(0.56), Inches(0.36),
             '→', size=T_BODY, bold=True,
             color=C_GREEN if improved else C_GRAY,
             align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 08 — PLAN D'EXÉCUTION (3 colonnes 30/60/90j)
# ─────────────────────────────────────────────────────────────────────────────

def _s08_plan(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '08 — PLAN', 'Plan d\'exécution — 90 jours.')
    _footer(slide, 8, date_str)

    phases = edm.roadmap_90_days or []
    if not phases:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Roadmap 90 jours non disponible.', size=T_LABEL, color=C_GRAY)
        return

    _plan_columns(slide, phases,
                  left=MARGIN_L,
                  top=HDR_TOP + Inches(0.10),
                  width=CONTENT_W,
                  height=CONTENT_H - Inches(0.10))


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 09 — DÉCISION DU CONSEIL (Vote)
# ─────────────────────────────────────────────────────────────────────────────

def _s09_vote(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '09 — VOTE', 'Décision du Conseil.')
    _footer(slide, 9, date_str)

    decisions = (edm.executive_decisions or [])[:3]
    n = len(decisions)
    if n == 0:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision à voter.', size=T_LABEL, color=C_GRAY)
        return

    card_gap = Inches(0.26)
    card_w   = (CONTENT_W - card_gap * (n - 1)) / n
    card_top = HDR_TOP + Inches(0.12)
    card_h   = CONTENT_H - Inches(0.12)

    for i, dec in enumerate(decisions):
        cx = MARGIN_L + i * (card_w + card_gap)

        _rect(slide, int(cx), int(card_top), int(card_w), int(card_h),
              C_LIGHT, border_color=C_LINE, border_pt=1.0)
        _rect(slide, int(cx), int(card_top), int(card_w), Inches(0.08), C_NAVY)

        # Badge D1 / D2 / D3 (T_ACCENT = 24pt) — boîte assez grande pour tenir sur 1 ligne
        badge_w = Inches(0.64)
        _rect(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.16)),
              int(badge_w), int(badge_w * 0.70), C_NAVY)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.16)),
             int(badge_w), int(badge_w * 0.70), f'D{i + 1}',
             size=T_ACCENT, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Texte décision (T_BODY = 22pt)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(0.72)),
             int(card_w - Inches(0.36)), Inches(1.10),
             _trunc(dec.decision, 42), size=T_BODY, bold=True, color=C_DARK,
             wrap=True)

        # Impact (T_BODY = 22pt)
        _txt(slide, int(cx + Inches(0.18)), int(card_top + Inches(1.90)),
             int(card_w - Inches(0.36)), Inches(0.36),
             f'Impact : {_fmt(dec.annual_impact)}',
             size=T_BODY, bold=True,
             color=C_GREEN if (dec.annual_impact or 0) > 0 else C_RED)

        # Séparateur
        _rect(slide, int(cx + Inches(0.18)), int(card_top + Inches(2.34)),
              int(card_w - Inches(0.36)), Emu(16000), C_LINE)

        # Options de vote (T_ACCENT = 24pt)
        vote_options = [
            ('□  APPROUVÉE', C_GREEN),
            ('□  REPORTÉE',  C_AMBER),
            ('□  REFUSÉE',   C_RED),
        ]
        opt_h = Inches(0.82)
        for j, (option, color) in enumerate(vote_options):
            vy = int(card_top + Inches(2.52) + j * (opt_h + Inches(0.10)))
            _rect(slide, int(cx + Inches(0.18)), vy,
                  int(card_w - Inches(0.36)), int(opt_h),
                  C_WHITE, border_color=color, border_pt=1.8)
            _txt(slide, int(cx + Inches(0.34)), vy + Inches(0.18),
                 int(card_w - Inches(0.68)), int(opt_h - Inches(0.22)),
                 option, size=T_ACCENT, bold=True, color=color)

    # Note (T_LABEL = 20pt)
    _txt(slide, MARGIN_L, SLIDE_H - FTR_H - Inches(0.42),
         CONTENT_W, Inches(0.34),
         'Cocher une case par décision — vote du Conseil d\'Administration.',
         size=T_LABEL, italic=True, color=C_SLATE, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 10 — RECOMMANDATION DU COPILOTE FINANCIER
# ─────────────────────────────────────────────────────────────────────────────

def _s10_recommendation(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '10 — RECOMMANDATION', 'Recommandation du Copilote Financier.')
    _footer(slide, 10, date_str)

    decisions   = edm.executive_decisions or []
    coi         = edm.cost_of_inaction
    total_gain  = sum(d.annual_impact or 0 for d in decisions if (d.annual_impact or 0) > 0)

    # ── Paragraphe 1 : Ce que je retiens ─────────────────────────────────────
    if decisions:
        top_dec = _trunc(_strip_md(decisions[0].decision), 70)
        roi_str = f"{decisions[0].roi_score:.1f}/10" if decisions[0].roi_score else '—'
        p1 = (f"L'analyse identifie {len(decisions)} décision(s) prioritaire(s) "
              f"pour un impact annuel total de {_fmt(total_gain)}. "
              f"La décision principale — « {top_dec} » — affiche un ROI de {roi_str}.")
    else:
        p1 = "L'analyse n'a pas encore produit de décision prioritaire quantifiée."

    # ── Paragraphe 2 : Ce qui doit être décidé cette semaine ─────────────────
    p0_decs = [d for d in decisions if (d.priority or '').upper().startswith('P0')][:2]
    if p0_decs:
        names = ' et '.join(f'« {_trunc(_strip_md(d.decision), 38)} »' for d in p0_decs)
        weekly = _fmt(total_gain / 52) if total_gain > 0 else '—'
        p2 = (f"Les décisions {names} sont P0 et peuvent être engagées immédiatement. "
              f"Chaque semaine d'attente représente {weekly} de valeur non créée.")
    else:
        weekly = _fmt(total_gain / 52) if total_gain > 0 else '—'
        p2 = (f"Les décisions identifiées nécessitent une validation formelle du Conseil "
              f"avant engagement. Chaque semaine d'attente représente {weekly} de valeur non créée.")

    # ── Paragraphe 3 : Ce qui se produira si rien n'est fait ─────────────────
    per_month = getattr(coi, 'per_month', None) if coi else None
    if per_month and abs(per_month) > 0:
        p3 = (f"En l'absence de décision, la valeur détruite s'élève à "
              f"{_fmt(abs(per_month))} par mois, soit {_fmt(abs(per_month) * 12)} sur 12 mois. "
              f"Ce scénario est entièrement évitable dès cette semaine.")
    else:
        per_year = getattr(coi, 'per_year', None) if coi else None
        ref = abs(per_year) if per_year else abs(total_gain) if total_gain else 0
        p3 = (f"En l'absence de décision, la perte annuelle estimée s'élève à "
              f"{_fmt(ref)}. Chaque mois d'inaction réduit la marge de manœuvre disponible.")

    # ── Layout : 3 blocs empilés ──────────────────────────────────────────────
    BLOCKS = [
        ('1.  Ce que je retiens.',                     p1, C_BLUE),
        ('2.  Ce qui doit être décidé cette semaine.', p2, C_NAVY),
        ('3.  Ce qui se produira si rien n\'est fait.', p3, C_RED),
    ]

    block_h = (CONTENT_H - Inches(0.50)) / 3
    gap_h   = Inches(0.14)

    for k, (hdr_text, body_text, accent_c) in enumerate(BLOCKS):
        by = int(HDR_TOP + Inches(0.10) + k * (block_h + gap_h))

        # Fond du bloc
        _rect(slide, MARGIN_L, by, int(CONTENT_W), int(block_h), C_LIGHT)
        # Bande accent gauche
        _rect(slide, MARGIN_L, by, Inches(0.09), int(block_h), accent_c)

        # En-tête de bloc (T_ACCENT = 24pt)
        _txt(slide, int(MARGIN_L + Inches(0.22)), by + Inches(0.12),
             int(CONTENT_W - Inches(0.28)), Inches(0.40),
             hdr_text, size=T_ACCENT, bold=True, color=C_NAVY)

        # Corps de texte (T_BODY = 22pt)
        body_h = block_h - Inches(0.58)
        _txt(slide, int(MARGIN_L + Inches(0.22)), by + Inches(0.54),
             int(CONTENT_W - Inches(0.28)), int(body_h),
             body_text, size=T_BODY, color=C_DARK, wrap=True)

    # Signature
    _txt(slide, MARGIN_L, SLIDE_H - FTR_H - Inches(0.46),
         CONTENT_W, Inches(0.38),
         'Pepperyn Executive Financial Copilot.',
         size=T_LABEL, italic=True, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def generate_pptx_report(result: Any, company_name: Optional[str] = None) -> bytes:
    """
    Génère l'Executive Board Deck V6 (10 slides) depuis l'EDM.
    `result` peut être :
      - un objet avec attribut `edm` (ExecutiveDecisionModel)
      - un dict (result_dict depuis le cache Supabase/mémoire)
    Retourne les bytes du fichier .pptx.
    """
    edm = getattr(result, 'edm', None)
    if edm is None and isinstance(result, dict):
        edm = result.get('edm')

    if edm is None:
        try:
            from services.executive_decision_model import build_executive_decision_model
            result_dict = result if isinstance(result, dict) else result.__dict__
            edm = build_executive_decision_model(result_dict)
        except Exception as exc:
            raise ValueError(
                f"Impossible de construire l'EDM pour le Board Deck : {exc}"
            ) from exc

    company  = company_name or 'Votre Entreprise'
    date_str = datetime.now().strftime('%d %B %Y')

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _s01_cover(prs, edm, company, date_str)
    _s02_inaction(prs, edm, date_str)
    _s03_waterfall(prs, edm, date_str)
    _s04_decisions(prs, edm, date_str)
    _s05_matrix(prs, edm, date_str)
    _s06_bridge(prs, edm, date_str)
    _s07_before_after(prs, edm, date_str)
    _s08_plan(prs, edm, date_str)
    _s09_vote(prs, edm, date_str)
    _s10_recommendation(prs, edm, date_str)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()
