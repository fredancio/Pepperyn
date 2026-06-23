"""
export_pptx_service.py — Executive Board Deck V5 (McKinsey / CAC40 Standard)
Pepperyn — Copilote Financier Exécutif

REFONTE TOTALE. Document de DÉCISION pour Conseil d'Administration.
Source unique : Executive Decision Model (EDM). Jamais le PDF.
Chaque slide = une idée. Zéro tableau. Waterfall, Bridge, Gantt, Matrice : formes natives.

Structure narrative imposée :
 01. EXECUTIVE DECISION       — Constat
 02. POURQUOI AGIR MAINTENANT — Urgence
 03. D'OÙ VIENT LE PROBLÈME  — Origine (Waterfall P&L)
 04. LES TROIS DÉCISIONS      — Décisions
 05. POURQUOI CES DÉCISIONS   — Matrice Impact / Effort
 06. EBITDA BRIDGE            — Impact (Bridge)
 07. AVANT / APRÈS            — Impact (comparaison)
 08. LES TROIS SCÉNARIOS      — Impact (scénarios)
 09. PLAN D'EXÉCUTION         — Impact (Gantt 90j)
 10. DÉCISION DU CONSEIL      — Vote
 11. KPIs DE SUIVI            — Suivi
 12. LE COPILOTE FINANCIER    — Pepperyn accompagne dans le temps
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
# PALETTE — McKinsey / Apple / Fonds d'investissement
# ─────────────────────────────────────────────────────────────────────────────
C_WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
C_NAVY        = RGBColor(0x0A, 0x25, 0x40)   # #0A2540 — couverture, accentuation
C_BLUE        = RGBColor(0x1B, 0x73, 0xE8)   # #1B73E8 — Pepperyn
C_DARK        = RGBColor(0x1A, 0x1A, 0x2E)   # #1A1A2E — texte principal
C_GRAY        = RGBColor(0x5F, 0x63, 0x68)   # #5F6368 — texte secondaire
C_SLATE       = RGBColor(0x94, 0xA3, 0xB8)   # #94A3B8 — texte tertiaire / labels
C_LINE        = RGBColor(0xE2, 0xE8, 0xF0)   # #E2E8F0 — séparateurs
C_LIGHT       = RGBColor(0xF8, 0xFA, 0xFF)   # #F8FAFF — fonds de cartes
C_GREEN       = RGBColor(0x05, 0x96, 0x69)   # #059669 — positif
C_RED         = RGBColor(0xDC, 0x26, 0x26)   # #DC2626 — négatif / alerte
C_AMBER       = RGBColor(0xD9, 0x77, 0x06)   # #D97706 — avertissement
C_LIGHT_GREEN = RGBColor(0xD1, 0xFA, 0xE5)   # #D1FAE5
C_LIGHT_RED   = RGBColor(0xFE, 0xE2, 0xE2)   # #FEE2E2
C_LIGHT_AMBER = RGBColor(0xFE, 0xF3, 0xC7)   # #FEF3C7
C_LIGHT_BLUE  = RGBColor(0xDB, 0xEA, 0xFE)   # #DBEAFE
C_NAVY_LIGHT  = RGBColor(0x1E, 0x3A, 0x5F)   # #1E3A5F — navy plus doux

# ─────────────────────────────────────────────────────────────────────────────
# DIMENSIONS SLIDE 16:9
# ─────────────────────────────────────────────────────────────────────────────
SLIDE_W   = Inches(13.333)
SLIDE_H   = Inches(7.5)
MARGIN_L  = Inches(0.8)
MARGIN_R  = Inches(0.8)
CONTENT_W = SLIDE_W - MARGIN_L - MARGIN_R   # ≈ 11.73"
HDR_TOP   = Inches(1.15)   # y où commence le contenu (sous le header)
FTR_H     = Inches(0.30)   # hauteur du footer
CONTENT_H = SLIDE_H - HDR_TOP - FTR_H - Inches(0.15)


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
    """Boîte de texte."""
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
    """Barre navy fine en haut + label de section + titre slide."""
    _rect(slide, 0, 0, SLIDE_W, Inches(0.055), C_NAVY)
    _txt(slide, MARGIN_L, Inches(0.10), Inches(6), Inches(0.22),
         label.upper(), size=6.5, bold=True, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(2.4), Inches(0.10), Inches(2.2), Inches(0.22),
         'PEPPERYN · CONFIDENTIEL', size=6, color=C_SLATE, align=PP_ALIGN.RIGHT)
    _txt(slide, MARGIN_L, Inches(0.34), CONTENT_W, Inches(0.65),
         title, size=21, bold=True, color=C_NAVY)
    _rect(slide, MARGIN_L, Inches(1.05), CONTENT_W, Emu(20000), C_LINE)


def _footer(slide, num: int, date_str: str = ''):
    """Footer discret : date + pagination."""
    _rect(slide, 0, SLIDE_H - Inches(0.30), SLIDE_W, Inches(0.30), C_LIGHT)
    _txt(slide, MARGIN_L, SLIDE_H - Inches(0.28), Inches(7), Inches(0.26),
         f'Pepperyn · Document confidentiel · {date_str}',
         size=6.5, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(1.6), SLIDE_H - Inches(0.28),
         Inches(1.4), Inches(0.26),
         f'{num:02d} / 12', size=6.5, bold=True, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# WATERFALL / BRIDGE  (rendu en formes — zéro tableau)
# ─────────────────────────────────────────────────────────────────────────────

def _waterfall(
    slide,
    items: List[dict],   # {'label', 'value', 'type': 'start'|'delta'|'end'}
    left: int, top: int, width: int, height: int,
):
    """
    Waterfall vertical McKinsey dessiné en rectangles.
    type='start' : barre pleine depuis 0 (Revenue, EBITDA actuel).
    type='delta' : barre flottante (coût ou gain).
    type='end'   : barre pleine depuis 0 (EBITDA final).
    """
    if not items:
        return
    n = len(items)

    # ── calcul des positions (from_v, to_v) pour chaque barre ──
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

    label_zone = Inches(0.55)          # hauteur réservée aux labels en bas
    chart_h = height - label_zone
    chart_bottom = top + chart_h

    col_w = width / n
    bar_w = int(col_w * 0.52)

    def vy(v: float) -> int:
        """Valeur → coordonnée Y (haut de l'écran = petite Y)."""
        frac = (v - min_v) / v_range
        return int(chart_bottom - frac * chart_h)

    # Axe zéro
    zero_y = vy(0)
    _rect(slide, left, zero_y, width, Emu(10000), C_LINE)

    # Barres et connecteurs
    cumul = 0.0
    for i, item in enumerate(items):
        fv, tv = positions[i]
        bar_left = int(left + i * col_w + (col_w - bar_w) / 2)
        y_hi = min(vy(fv), vy(tv))     # y haut (petite valeur y = haut écran)
        y_lo = max(vy(fv), vy(tv))     # y bas
        bar_h = max(y_lo - y_hi, Emu(18000))

        # Couleur
        if item['type'] in ('start', 'end'):
            color = C_NAVY if item['value'] <= 0 else C_BLUE
        else:
            color = C_RED if item['value'] < 0 else C_GREEN

        _rect(slide, bar_left, y_hi, bar_w, bar_h, color)

        # Connecteur horizontal vers la barre suivante
        if i < n - 1 and item['type'] != 'end':
            next_bar_left = int(left + (i + 1) * col_w + (col_w - bar_w) / 2)
            conn_y = vy(tv)
            _rect(slide, bar_left + bar_w, conn_y - Emu(5000),
                  next_bar_left - bar_left - bar_w, Emu(10000), C_SLATE)

        # Valeur au-dessus/en-dessous de la barre
        val_str = _fmt(item['value'], sign=(item['type'] == 'delta'))
        if item['value'] >= 0 or item['type'] == 'start':
            lbl_y = y_hi - Inches(0.26)
        else:
            lbl_y = y_lo + Inches(0.03)
        _txt(slide, bar_left - Inches(0.1), lbl_y, bar_w + Inches(0.2), Inches(0.24),
             val_str, size=7.5, bold=True,
             color=C_RED if (item['type'] == 'delta' and item['value'] < 0) else C_DARK,
             align=PP_ALIGN.CENTER)

        # Label catégorie en bas
        _txt(slide,
             bar_left - Inches(0.12),
             chart_bottom + Inches(0.08),
             bar_w + Inches(0.24),
             label_zone - Inches(0.08),
             item['label'],
             size=6.5, color=C_GRAY, align=PP_ALIGN.CENTER, wrap=True)

        if item['type'] == 'delta':
            cumul += item['value']
        elif item['type'] == 'start':
            cumul = item['value']


# ─────────────────────────────────────────────────────────────────────────────
# GANTT  (rendu en rectangles — zéro liste)
# ─────────────────────────────────────────────────────────────────────────────

def _gantt(slide, phases, left: int, top: int, width: int, height: int):
    """Gantt 0-90 jours dessiné avec des rectangles."""
    PHASE_CFG = {
        '30': {'color': C_BLUE,       'start': 0,  'end': 30,  'label': 'STABILISER'},
        '60': {'color': C_NAVY,       'start': 30, 'end': 60,  'label': 'OPTIMISER'},
        '90': {'color': C_NAVY_LIGHT, 'start': 60, 'end': 90,  'label': 'ACCÉLÉRER'},
    }

    rows: List[dict] = []
    for phase in phases:
        h = str(phase.horizon)
        cfg = PHASE_CFG.get(h, PHASE_CFG['90'])
        for act in (phase.actions or [])[:4]:
            rows.append({
                'label': _trunc(act.decision, 52),
                'owner': _trunc(act.owner or '', 18),
                'start': cfg['start'],
                'end':   cfg['end'],
                'color': cfg['color'],
                'phase': h,
            })

    rows = rows[:12]
    if not rows:
        _txt(slide, left, top, width, height,
             'Aucune action définie dans la roadmap.', size=11, color=C_GRAY)
        return

    label_w  = Inches(4.2)
    chart_l  = left + label_w + Inches(0.1)
    chart_w  = width - label_w - Inches(0.1)
    hdr_h    = Inches(0.32)
    n_rows   = len(rows)
    row_h    = (height - hdr_h) / n_rows

    # Bandes de phase (en-tête)
    for h_key, cfg in PHASE_CFG.items():
        bx = int(chart_l + cfg['start'] / 90 * chart_w)
        bw = int((cfg['end'] - cfg['start']) / 90 * chart_w)
        bg = C_LIGHT_BLUE if h_key == '30' else C_LIGHT
        _rect(slide, bx, top, bw - Emu(8000), hdr_h, bg)
        _txt(slide, bx + Inches(0.06), top, bw - Inches(0.1), hdr_h,
             cfg['label'], size=6.5, bold=True,
             color=C_NAVY if h_key == '30' else C_GRAY,
             align=PP_ALIGN.CENTER)

    # Repères jours
    for day, lbl in [(0, '0'), (30, '30j'), (60, '60j'), (90, '90j')]:
        x = int(chart_l + day / 90 * chart_w)
        _rect(slide, x, top, Emu(8000), height, C_LINE)
        _txt(slide, x - Inches(0.18), top - Inches(0.22), Inches(0.36), Inches(0.20),
             lbl, size=6.5, color=C_SLATE, align=PP_ALIGN.CENTER)

    # Lignes d'action
    for i, row in enumerate(rows):
        ry = int(top + hdr_h + i * row_h)
        bar_h_px = int(row_h * 0.55)
        bar_top  = int(ry + (row_h - bar_h_px) / 2)

        # Fond ligne alternée
        if i % 2 == 0:
            _rect(slide, left, ry, width, int(row_h), C_LIGHT)

        # Label action
        _txt(slide, left + Inches(0.08), ry + Inches(0.03),
             label_w - Inches(0.2), row_h - Inches(0.06),
             row['label'], size=7.5, color=C_DARK, wrap=True)

        # Barre Gantt
        bx = int(chart_l + row['start'] / 90 * chart_w)
        bw = max(int((row['end'] - row['start']) / 90 * chart_w) - Emu(30000), Emu(80000))
        _rect(slide, bx, bar_top, bw, bar_h_px, row['color'])

        # Responsable dans la barre
        if row['owner']:
            _txt(slide, bx + Inches(0.08), bar_top, bw - Inches(0.08), bar_h_px,
                 row['owner'], size=6, color=C_WHITE)


# ─────────────────────────────────────────────────────────────────────────────
# MATRICE IMPACT / EFFORT
# ─────────────────────────────────────────────────────────────────────────────

def _matrix(slide, decisions, left: int, top: int, width: int, height: int):
    """Quadrant Impact / Effort avec points numérotés."""
    ax_lbl_h = Inches(0.30)
    chart_h  = height - ax_lbl_h - Inches(0.10)
    chart_w  = width

    mid_x = int(left + chart_w / 2)
    mid_y = int(top + chart_h / 2)

    # Fonds quadrants
    _rect(slide, left, top, int(chart_w / 2), int(chart_h / 2), C_LIGHT_GREEN)    # TL Quick Wins
    _rect(slide, mid_x, top, int(chart_w / 2), int(chart_h / 2), C_LIGHT_BLUE)    # TR Investir
    _rect(slide, left, mid_y, int(chart_w / 2), int(chart_h / 2), C_LIGHT)         # BL Déléguer
    _rect(slide, mid_x, mid_y, int(chart_w / 2), int(chart_h / 2), C_LIGHT_AMBER)  # BR Éviter

    # Labels quadrants
    _txt(slide, left + Inches(0.12), top + Inches(0.08), Inches(2.8), Inches(0.28),
         'QUICK WINS ★', size=8.5, bold=True, color=C_GREEN)
    _txt(slide, mid_x + Inches(0.12), top + Inches(0.08), Inches(2.8), Inches(0.28),
         'INVESTIR', size=8.5, bold=True, color=C_BLUE)
    _txt(slide, left + Inches(0.12), mid_y + Inches(0.08), Inches(2.8), Inches(0.28),
         'DÉLÉGUER', size=8.5, bold=True, color=C_GRAY)
    _txt(slide, mid_x + Inches(0.12), mid_y + Inches(0.08), Inches(2.8), Inches(0.28),
         'ÉVITER', size=8.5, bold=True, color=C_AMBER)

    # Lignes de séparation
    _rect(slide, mid_x - Emu(5000), top, Emu(10000), int(chart_h), C_WHITE)
    _rect(slide, left, mid_y - Emu(5000), int(chart_w), Emu(10000), C_WHITE)

    # Axe X label
    _txt(slide, left, top + chart_h + Inches(0.05), int(chart_w), ax_lbl_h,
         '◄  EFFORT FAIBLE                                    EFFORT ÉLEVÉ  ►',
         size=7, color=C_SLATE, align=PP_ALIGN.CENTER)

    # Points décisions
    max_impact = max((abs(d.annual_impact or 0) for d in decisions), default=1) or 1

    for i, dec in enumerate(decisions[:5]):
        impact = abs(dec.annual_impact or 0)
        effort = _effort_score(dec.difficulty)  # 1-3

        imp_norm = min(impact / max_impact, 1.0)
        eff_norm = (effort - 1) / 2.0

        dot_cx = int(left + eff_norm * chart_w)
        dot_cy = int(top + (1.0 - imp_norm) * chart_h)

        dot_cx = min(max(dot_cx, left + Inches(0.25)), left + int(chart_w) - Inches(0.25))
        dot_cy = min(max(dot_cy, top + Inches(0.25)), top + int(chart_h) - Inches(0.25))

        ds = Inches(0.38)
        _rect(slide, dot_cx - ds // 2, dot_cy - ds // 2, ds, ds, C_NAVY,
              border_color=C_WHITE, border_pt=2.0)
        _txt(slide, dot_cx - ds // 2, dot_cy - ds // 2, ds, ds,
             str(i + 1), size=10, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 01 — EXECUTIVE DECISION (couverture)
# ─────────────────────────────────────────────────────────────────────────────

def _s01_cover(prs, edm, company: str, date_str: str):
    slide = _blank(prs)

    # ── Fond sombre McKinsey ──────────────────────────────────────
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = C_NAVY   # #0A2540

    # Accent stripe gauche (bleu Pepperyn)
    _rect(slide, 0, 0, Inches(0.10), SLIDE_H, C_BLUE)

    # Labels de cadre (haut de slide)
    _txt(slide, Inches(0.24), Inches(0.18), Inches(6), Inches(0.30),
         'EXECUTIVE DECISION', size=7.5, bold=True, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(2.8), Inches(0.18), Inches(2.6), Inches(0.30),
         'PEPPERYN · CONFIDENTIEL', size=7, color=C_SLATE, align=PP_ALIGN.RIGHT)

    # Nom société — grand, blanc, bold
    _txt(slide, Inches(0.24), Inches(0.60), SLIDE_W - Inches(0.48), Inches(1.30),
         company or '—', size=52, bold=True, color=C_WHITE)

    # Séparateur bleu horizontal
    _rect(slide, Inches(0.24), Inches(2.08), SLIDE_W - Inches(0.34), Emu(45000), C_BLUE)

    # Date + CONFIDENTIEL
    _txt(slide, Inches(0.24), Inches(2.22), SLIDE_W - Inches(0.48), Inches(0.36),
         f'{date_str} · CONFIDENTIEL', size=10, color=C_SLATE)

    # Citation décision principale — italique, blanc
    decisions = (edm.executive_decisions or [])[:3]
    top_quote = _strip_md(decisions[0].decision) if decisions else ''
    if top_quote:
        _txt(slide, Inches(0.24), Inches(2.75), SLIDE_W - Inches(0.48), Inches(3.00),
             f'« {top_quote} »',
             size=30, italic=True, color=C_WHITE, wrap=True)

    # Footer dark
    _rect(slide, 0, SLIDE_H - Inches(0.52), SLIDE_W, Inches(0.52), C_NAVY_LIGHT)
    _txt(slide, Inches(0.24), SLIDE_H - Inches(0.48), SLIDE_W - Inches(0.48), Inches(0.44),
         'Pepperyn · Copilote Financier Exécutif',
         size=10, color=C_SLATE, align=PP_ALIGN.CENTER)
    _txt(slide, SLIDE_W - Inches(1.8), SLIDE_H - Inches(0.48),
         Inches(1.6), Inches(0.44),
         '01 / 12', size=6.5, bold=True, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 02 — POURQUOI AGIR MAINTENANT
# ─────────────────────────────────────────────────────────────────────────────

def _s02_urgency(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '02 — URGENCE', 'Pourquoi le Board doit agir maintenant.')
    _footer(slide, 2, date_str)

    coi = edm.cost_of_inaction or edm.cost_of_inaction_summary
    if not coi:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Données de coût d\'inaction non disponibles.', size=14, color=C_GRAY)
        return

    periods = [
        ('PAR AN',      coi.per_year,  60),
        ('PAR MOIS',    coi.per_month, 40),
        ('PAR SEMAINE', coi.per_week,  30),
        ('PAR JOUR',    coi.per_day,   22),
        ('PAR HEURE',   coi.per_hour,  17),
    ]
    periods = [(lbl, v, sz) for lbl, v, sz in periods if v is not None]
    n = len(periods)
    if n == 0:
        return

    row_h = CONTENT_H / max(n + 1, 5)
    for i, (label, value, font_sz) in enumerate(periods):
        y = HDR_TOP + Inches(0.12) + i * row_h

        # Barre gauche d'accentuation pour le 1er item
        if i == 0:
            _rect(slide, MARGIN_L, y + Inches(0.05), Inches(0.055), row_h - Inches(0.10), C_RED)

        _txt(slide, MARGIN_L + Inches(0.18), y,
             Inches(3.5), Inches(0.26),
             label, size=7, bold=True, color=C_SLATE)
        _txt(slide, MARGIN_L + Inches(0.18), y + Inches(0.22),
             CONTENT_W - Inches(0.20), row_h - Inches(0.22),
             _fmt(value), size=float(font_sz), bold=True,
             color=C_RED if i == 0 else (C_DARK if i < 2 else C_GRAY))

    # Phrase choc
    phrase_y = HDR_TOP + Inches(0.12) + n * row_h + Inches(0.20)
    _rect(slide, MARGIN_L, int(phrase_y - Inches(0.06)),
          CONTENT_W, Inches(0.70), C_LIGHT)
    _txt(slide, MARGIN_L, int(phrase_y),
         CONTENT_W, Inches(0.56),
         'Chaque heure sans décision détruit de la valeur.',
         size=16, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 03 — D'OÙ VIENT LE PROBLÈME (Waterfall P&L)
# ─────────────────────────────────────────────────────────────────────────────

def _s03_waterfall(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '03 — ORIGINE', 'D\'où vient le problème ?')
    _footer(slide, 3, date_str)

    ebitda_val  = _parse_amount(edm.ebitda)
    destroyers  = edm.value_destroyers or []

    # Revenue estimé = EBITDA + total des destructions
    total_destr = sum(abs(d.annual_impact or 0) for d in destroyers if (d.annual_impact or 0) < 0)
    if total_destr == 0:
        # Si aucun destroyer négatif, cherche tous les destroyers
        total_destr = sum(abs(d.annual_impact or 0) for d in destroyers)
    revenue = ebitda_val + total_destr if total_destr > 0 else max(abs(ebitda_val) * 4, 1_000_000)

    items: List[dict] = [{'label': "Chiffre\nd'affaires", 'value': revenue, 'type': 'start'}]

    if destroyers:
        shown_sum = 0.0
        for d in destroyers[:6]:
            impact_v = -(abs(d.annual_impact or 0))
            items.append({'label': _trunc(d.name, 13), 'value': impact_v, 'type': 'delta'})
            shown_sum += abs(impact_v)
        residual = total_destr - shown_sum
        if residual > 10_000:
            items.append({'label': 'Autres\ncoûts', 'value': -residual, 'type': 'delta'})
    else:
        # Fallback générique
        for lbl, pct in [('Masse\nsalariale', 0.38), ('Sous-\ntraitance', 0.18),
                          ('Loyers', 0.10), ('Support', 0.07), ('Autres\ncoûts', 0.07)]:
            items.append({'label': lbl, 'value': -(revenue * pct), 'type': 'delta'})

    items.append({'label': 'EBITDA', 'value': ebitda_val, 'type': 'end'})

    _waterfall(slide, items,
               left=MARGIN_L,
               top=HDR_TOP + Inches(0.10),
               width=CONTENT_W,
               height=CONTENT_H - Inches(0.10))


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 04 — LES TROIS DÉCISIONS
# ─────────────────────────────────────────────────────────────────────────────

def _s04_decisions(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '04 — DÉCISIONS', 'Les trois décisions.')
    _footer(slide, 4, date_str)

    decisions = (edm.executive_decisions or [])[:3]
    n = len(decisions)
    if n == 0:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision identifiée dans l\'analyse.', size=14, color=C_GRAY)
        return

    card_gap = Inches(0.22)
    card_w   = (CONTENT_W - card_gap * (n - 1)) / n
    card_top = HDR_TOP + Inches(0.12)
    card_h   = CONTENT_H - Inches(0.12)

    accents = [C_BLUE, C_NAVY, C_SLATE]

    for i, dec in enumerate(decisions):
        cx = MARGIN_L + i * (card_w + card_gap)
        acc = accents[i % len(accents)]

        # Fond carte + bordure
        _rect(slide, int(cx), int(card_top), int(card_w), int(card_h),
              C_LIGHT, border_color=C_LINE, border_pt=1.0)

        # Bande couleur en haut
        _rect(slide, int(cx), int(card_top), int(card_w), Inches(0.07), acc)

        # Numéro
        _rect(slide, int(cx + Inches(0.22)), int(card_top + Inches(0.16)),
              Inches(0.36), Inches(0.36), acc)
        _txt(slide, int(cx + Inches(0.22)), int(card_top + Inches(0.16)),
             Inches(0.36), Inches(0.36), str(i + 1),
             size=11, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Titre décision
        _txt(slide, int(cx + Inches(0.22)), int(card_top + Inches(0.62)),
             int(card_w - Inches(0.44)), Inches(1.10),
             _trunc(dec.decision, 92), size=12, bold=True, color=C_DARK, wrap=True)

        # Séparateur
        _rect(slide, int(cx + Inches(0.22)), int(card_top + Inches(1.80)),
              int(card_w - Inches(0.44)), Emu(14000), C_LINE)

        # Métriques — grille 2 × 3
        fields = [
            ('Impact annuel', _fmt(dec.annual_impact),
             True, C_GREEN if (dec.annual_impact or 0) > 0 else C_RED),
            ('ROI Score',     f"{dec.roi_score:.1f} / 10" if dec.roi_score else '—',
             False, C_DARK),
            ('Difficulté',    _difficulty_fr(dec.difficulty), False, C_DARK),
            ('Délai',         _trunc(dec.timeline, 20) or '—', False, C_DARK),
            ('Responsable',   _trunc(dec.owner, 24) or '—', False, C_DARK),
            ('Priorité',      dec.priority or '—', False, acc),
        ]

        row_h_m = Inches(0.58)
        for j, (lbl, val, val_bold, val_color) in enumerate(fields):
            col = j % 2
            row = j // 2
            mx  = int(cx + Inches(0.22) + col * (card_w - Inches(0.44)) / 2)
            my  = int(card_top + Inches(1.94) + row * row_h_m)
            mw  = int((card_w - Inches(0.50)) / 2)

            _txt(slide, mx, my, mw, Inches(0.22), lbl, size=6.5, color=C_SLATE)
            _txt(slide, mx, my + Inches(0.22), mw, Inches(0.32),
                 val, size=10, bold=val_bold, color=val_color, wrap=True)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 05 — MATRICE IMPACT / EFFORT
# ─────────────────────────────────────────────────────────────────────────────

def _s05_matrix(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '05 — PRIORISATION', 'Pourquoi ces décisions ?')
    _footer(slide, 5, date_str)

    decisions = (edm.executive_decisions or [])[:5]
    if not decisions:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision disponible pour la matrice.', size=14, color=C_GRAY)
        return

    matrix_w = int(CONTENT_W * 0.60)
    legend_x = MARGIN_L + matrix_w + Inches(0.45)
    legend_w = CONTENT_W - matrix_w - Inches(0.45)

    _matrix(slide, decisions,
            left=MARGIN_L,
            top=HDR_TOP + Inches(0.10),
            width=matrix_w,
            height=int(CONTENT_H - Inches(0.10)))

    # Légende droite
    _txt(slide, int(legend_x), int(HDR_TOP + Inches(0.10)),
         int(legend_w), Inches(0.26),
         'DÉCISIONS ANALYSÉES', size=7, bold=True, color=C_SLATE)

    for i, dec in enumerate(decisions):
        ly = int(HDR_TOP + Inches(0.44) + i * Inches(0.70))
        _rect(slide, int(legend_x), ly + Inches(0.02), Inches(0.28), Inches(0.28), C_NAVY)
        _txt(slide, int(legend_x), ly + Inches(0.02), Inches(0.28), Inches(0.28),
             str(i + 1), size=8, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        _txt(slide, int(legend_x + Inches(0.36)), ly,
             int(legend_w - Inches(0.36)), Inches(0.30),
             _trunc(dec.decision, 44), size=8.5, bold=True, color=C_DARK, wrap=True)
        _txt(slide, int(legend_x + Inches(0.36)), ly + Inches(0.30),
             int(legend_w - Inches(0.36)), Inches(0.24),
             f'Impact : {_fmt(dec.annual_impact)}  ·  {_difficulty_fr(dec.difficulty)}',
             size=7.5, color=C_GRAY)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 06 — EBITDA BRIDGE
# ─────────────────────────────────────────────────────────────────────────────

def _s06_bridge(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '06 — IMPACT', 'EBITDA Bridge — de la situation actuelle à l\'objectif.')
    _footer(slide, 6, date_str)

    ebitda_now = _parse_amount(edm.ebitda)
    decisions  = (edm.executive_decisions or [])[:5]

    categories = ['Masse salariale', 'Sous-traitance', 'Pricing', 'Autres mesures', 'Optimisation']

    items: List[dict] = [{'label': 'EBITDA\nactuel', 'value': ebitda_now, 'type': 'start'}]
    total_impact = 0.0
    for i, dec in enumerate(decisions):
        impact = dec.annual_impact or 0
        cat    = categories[i] if i < len(categories) else f'Levier {i+1}'
        items.append({'label': _trunc(cat, 13), 'value': impact, 'type': 'delta'})
        total_impact += impact

    items.append({'label': 'EBITDA\nprojeté', 'value': ebitda_now + total_impact, 'type': 'end'})

    _waterfall(slide, items,
               left=MARGIN_L,
               top=HDR_TOP + Inches(0.10),
               width=CONTENT_W,
               height=CONTENT_H - Inches(0.12))

    # Annotation gain total
    _txt(slide, MARGIN_L, SLIDE_H - Inches(0.70), CONTENT_W, Inches(0.28),
         f'Gain total projeté : {_fmt(total_impact, sign=True)}',
         size=10, bold=True,
         color=C_GREEN if total_impact >= 0 else C_RED,
         align=PP_ALIGN.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 07 — AVANT / APRÈS
# ─────────────────────────────────────────────────────────────────────────────

def _s07_before_after(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '07 — IMPACT', 'Avant / Après — l\'effet des décisions sur les indicateurs clés.')
    _footer(slide, 7, date_str)

    ebitda_now = _parse_amount(edm.ebitda)
    cash_now   = _parse_amount(edm.available_cash)
    decisions  = edm.executive_decisions or []
    total_gain = sum(d.annual_impact or 0 for d in decisions[:3] if (d.annual_impact or 0) > 0)

    ebitda_after = ebitda_now + total_gain
    cash_after   = cash_now + total_gain * 0.6

    # Runway
    burn_now   = abs(ebitda_now / 12) if ebitda_now < 0 else None
    burn_after = abs(ebitda_after / 12) if ebitda_after < 0 else None
    runway_now   = (f"{cash_now / burn_now:.0f} mois" if burn_now and cash_now > 0 else
                    ('∞' if ebitda_now >= 0 else '—'))
    runway_after = (f"{cash_after / burn_after:.0f} mois" if burn_after and cash_after > 0 else '∞')

    # Marge
    destroyers  = edm.value_destroyers or []
    rev_est     = ebitda_now + sum(abs(d.annual_impact or 0) for d in destroyers)
    margin_now  = f"{ebitda_now / rev_est * 100:.1f} %" if rev_est > 0 else '—'
    margin_aft  = f"{ebitda_after / rev_est * 100:.1f} %" if rev_est > 0 else '—'

    kpis = [
        ('EBITDA',    _fmt(ebitda_now), _fmt(ebitda_after), ebitda_after > ebitda_now),
        ('Cash',      _fmt(cash_now),   _fmt(cash_after),   cash_after > cash_now),
        ('Marge',     margin_now,       margin_aft,          True),
        ('Runway',    runway_now,       runway_after,         True),
        ('Liquidité', _fmt(cash_now),   _fmt(cash_after),   cash_after > cash_now),
    ]

    col_w   = (CONTENT_W - Inches(0.40)) / 2
    col_l   = MARGIN_L
    col_r   = MARGIN_L + col_w + Inches(0.40)
    col_top = HDR_TOP + Inches(0.10)
    kpi_h   = (CONTENT_H - Inches(0.56)) / len(kpis)

    # En-têtes
    for cx, lbl, bg, fc in [
        (col_l, "AUJOURD'HUI",   C_LIGHT_RED,   C_RED),
        (col_r, 'APRÈS DÉCISIONS', C_LIGHT_GREEN, C_GREEN),
    ]:
        _rect(slide, int(cx), int(col_top), int(col_w), Inches(0.44), bg)
        _txt(slide, int(cx + Inches(0.12)), int(col_top + Inches(0.08)),
             int(col_w - Inches(0.24)), Inches(0.32),
             lbl, size=10, bold=True, color=fc, align=PP_ALIGN.CENTER)

    # Séparateur central
    mid_x = int(MARGIN_L + col_w + Inches(0.20))
    _rect(slide, mid_x - Emu(5000), int(col_top), Emu(10000), int(CONTENT_H), C_LINE)

    # Lignes KPI
    for i, (name, val_now, val_aft, improved) in enumerate(kpis):
        ky = int(col_top + Inches(0.54) + i * kpi_h)

        for cx, val, is_after in [(col_l, val_now, False), (col_r, val_aft, True)]:
            _rect(slide, int(cx + Inches(0.06)), ky,
                  int(col_w - Inches(0.12)), int(kpi_h - Inches(0.07)), C_LIGHT)
            _txt(slide, int(cx + Inches(0.18)), ky + Inches(0.04),
                 int(col_w - Inches(0.36)), Inches(0.22),
                 name, size=7, color=C_SLATE)
            v_color = (C_GREEN if improved else C_RED) if is_after else C_DARK
            _txt(slide, int(cx + Inches(0.18)), ky + Inches(0.24),
                 int(col_w - Inches(0.36)), kpi_h - Inches(0.32),
                 val, size=16, bold=True, color=v_color)

        # Flèche centrale
        _txt(slide, mid_x - Inches(0.22), int(ky + kpi_h / 2 - Inches(0.14)),
             Inches(0.44), Inches(0.28),
             '→', size=14, bold=True,
             color=C_GREEN if improved else C_GRAY,
             align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 08 — LES TROIS SCÉNARIOS
# ─────────────────────────────────────────────────────────────────────────────

def _s08_scenarios(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '08 — SCÉNARIOS', 'Les trois scénarios.')
    _footer(slide, 8, date_str)

    ebitda_now = _parse_amount(edm.ebitda)
    cash_now   = _parse_amount(edm.available_cash)
    decisions  = edm.executive_decisions or []
    total_gain = sum(d.annual_impact or 0 for d in decisions[:3] if (d.annual_impact or 0) > 0)

    scenarios = [
        {
            'title':   'NE RIEN FAIRE',
            'bg':      C_LIGHT_RED,
            'accent':  C_RED,
            'ebitda':  ebitda_now,
            'cash':    cash_now,
            'equilib': 'Non atteint' if ebitda_now < 0 else 'Stable',
            'risque':  'ÉLEVÉ',
            'risk_c':  C_RED,
        },
        {
            'title':   'APPLICATION PARTIELLE',
            'bg':      C_LIGHT_AMBER,
            'accent':  C_AMBER,
            'ebitda':  ebitda_now + total_gain * 0.5,
            'cash':    cash_now + total_gain * 0.3,
            'equilib': '6 – 9 mois',
            'risque':  'MODÉRÉ',
            'risk_c':  C_AMBER,
        },
        {
            'title':   'APPLICATION COMPLÈTE',
            'bg':      C_LIGHT_GREEN,
            'accent':  C_GREEN,
            'ebitda':  ebitda_now + total_gain,
            'cash':    cash_now + total_gain * 0.6,
            'equilib': '3 – 6 mois',
            'risque':  'FAIBLE',
            'risk_c':  C_GREEN,
        },
    ]

    card_gap = Inches(0.24)
    card_w   = (CONTENT_W - card_gap * 2) / 3
    card_top = HDR_TOP + Inches(0.12)
    card_h   = CONTENT_H - Inches(0.12)

    for i, sc in enumerate(scenarios):
        cx = MARGIN_L + i * (card_w + card_gap)

        _rect(slide, int(cx), int(card_top), int(card_w), int(card_h),
              sc['bg'], border_color=sc['accent'], border_pt=1.5)
        _rect(slide, int(cx), int(card_top), int(card_w), Inches(0.08), sc['accent'])

        _txt(slide, int(cx + Inches(0.20)), int(card_top + Inches(0.18)),
             int(card_w - Inches(0.40)), Inches(0.44),
             sc['title'], size=10, bold=True, color=sc['accent'])

        _rect(slide, int(cx + Inches(0.20)), int(card_top + Inches(0.72)),
              int(card_w - Inches(0.40)), Emu(14000), sc['accent'])

        fields = [
            ('EBITDA',               _fmt(sc['ebitda'])),
            ('Cash',                 _fmt(sc['cash'])),
            ("Retour à l'équilibre", sc['equilib']),
            ('Risque',               sc['risque']),
        ]
        for j, (lbl, val) in enumerate(fields):
            fy = int(card_top + Inches(0.86) + j * Inches(1.26))
            _txt(slide, int(cx + Inches(0.20)), fy,
                 int(card_w - Inches(0.40)), Inches(0.22),
                 lbl, size=7, color=C_GRAY)
            v_color = sc['risk_c'] if lbl == 'Risque' else (sc['accent'] if j == 0 else C_DARK)
            _txt(slide, int(cx + Inches(0.20)), fy + Inches(0.22),
                 int(card_w - Inches(0.40)), Inches(0.60),
                 val, size=20, bold=True, color=v_color)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 09 — PLAN D'EXÉCUTION (Gantt)
# ─────────────────────────────────────────────────────────────────────────────

def _s09_gantt(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '09 — PLAN', 'Plan d\'exécution — 90 jours.')
    _footer(slide, 9, date_str)

    phases = edm.roadmap_90_days or []
    if not phases:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Roadmap 90 jours non disponible.', size=14, color=C_GRAY)
        return

    _gantt(slide, phases,
           left=MARGIN_L,
           top=HDR_TOP + Inches(0.18),
           width=CONTENT_W,
           height=CONTENT_H - Inches(0.18))


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 10 — DÉCISION DU CONSEIL (Vote)
# ─────────────────────────────────────────────────────────────────────────────

def _s10_vote(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '10 — VOTE', 'Décision du Conseil.')
    _footer(slide, 10, date_str)

    decisions = (edm.executive_decisions or [])[:3]
    n = len(decisions)
    if n == 0:
        _txt(slide, MARGIN_L, HDR_TOP, CONTENT_W, CONTENT_H,
             'Aucune décision à voter.', size=14, color=C_GRAY)
        return

    card_gap = Inches(0.24)
    card_w   = (CONTENT_W - card_gap * (n - 1)) / n
    card_top = HDR_TOP + Inches(0.18)
    card_h   = CONTENT_H - Inches(0.18)

    for i, dec in enumerate(decisions):
        cx = MARGIN_L + i * (card_w + card_gap)

        _rect(slide, int(cx), int(card_top), int(card_w), int(card_h),
              C_LIGHT, border_color=C_LINE, border_pt=1.0)
        _rect(slide, int(cx), int(card_top), int(card_w), Inches(0.07), C_NAVY)

        _txt(slide, int(cx + Inches(0.20)), int(card_top + Inches(0.18)),
             Inches(0.34), Inches(0.34), f'D{i+1}',
             size=9, bold=True, color=C_NAVY)
        _txt(slide, int(cx + Inches(0.20)), int(card_top + Inches(0.58)),
             int(card_w - Inches(0.40)), Inches(1.10),
             _trunc(dec.decision, 90), size=12, bold=True, color=C_DARK, wrap=True)
        _txt(slide, int(cx + Inches(0.20)), int(card_top + Inches(1.76)),
             int(card_w - Inches(0.40)), Inches(0.28),
             f'Impact : {_fmt(dec.annual_impact)}',
             size=10, bold=True, color=C_GREEN if (dec.annual_impact or 0) > 0 else C_RED)

        _rect(slide, int(cx + Inches(0.20)), int(card_top + Inches(2.14)),
              int(card_w - Inches(0.40)), Emu(14000), C_LINE)

        vote_options = [
            ('□  APPROUVÉE', C_GREEN),
            ('□  REPORTÉE',  C_AMBER),
            ('□  REFUSÉE',   C_RED),
        ]
        for j, (option, color) in enumerate(vote_options):
            vy = int(card_top + Inches(2.28) + j * Inches(0.88))
            _rect(slide, int(cx + Inches(0.20)), vy,
                  int(card_w - Inches(0.40)), Inches(0.72),
                  C_WHITE, border_color=color, border_pt=1.5)
            _txt(slide, int(cx + Inches(0.38)), vy + Inches(0.18),
                 int(card_w - Inches(0.60)), Inches(0.36),
                 option, size=12, bold=True, color=color)

    _txt(slide, MARGIN_L, SLIDE_H - Inches(0.72), CONTENT_W, Inches(0.28),
         'Cocher une case par décision — vote du Conseil d\'Administration.',
         size=9, italic=True, color=C_SLATE, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 11 — KPIs DE SUIVI
# ─────────────────────────────────────────────────────────────────────────────

def _s11_kpis(prs, edm, date_str: str):
    slide = _blank(prs)
    _header(slide, '11 — SUIVI', 'KPIs de suivi — quatre indicateurs, pas davantage.')
    _footer(slide, 11, date_str)

    ebitda_now = _parse_amount(edm.ebitda)
    cash_now   = _parse_amount(edm.available_cash)
    decisions  = edm.executive_decisions or []
    total_gain = sum(d.annual_impact or 0 for d in decisions[:3] if (d.annual_impact or 0) > 0)

    burn       = abs(ebitda_now / 12) if ebitda_now < 0 else None
    runway     = f"{cash_now / burn:.0f} mois" if burn and cash_now > 0 else '∞'

    destroyers = edm.value_destroyers or []
    rev_est    = ebitda_now + sum(abs(d.annual_impact or 0) for d in destroyers)
    margin_str = f"{ebitda_now / rev_est * 100:.1f} %" if rev_est > 0 else '—'

    kpis = [
        {'label': 'EBITDA',  'value': _fmt(ebitda_now),
         'target': _fmt(ebitda_now + total_gain), 'color': C_NAVY},
        {'label': 'CASH',    'value': _fmt(cash_now),
         'target': _fmt(cash_now + total_gain * 0.6), 'color': C_BLUE},
        {'label': 'RUNWAY',  'value': runway, 'target': '∞',
         'color': C_GREEN if runway == '∞' else C_AMBER},
        {'label': 'MARGE',   'value': margin_str, 'target': '—', 'color': C_DARK},
    ]

    kpi_gap = Inches(0.20)
    kpi_w   = (CONTENT_W - kpi_gap * 3) / 4
    kpi_h   = CONTENT_H - Inches(0.20)

    for i, kpi in enumerate(kpis):
        kx = MARGIN_L + i * (kpi_w + kpi_gap)
        ky = HDR_TOP + Inches(0.18)

        _rect(slide, int(kx), int(ky), int(kpi_w), int(kpi_h),
              C_LIGHT, border_color=C_LINE, border_pt=1.0)
        _rect(slide, int(kx), int(ky), int(kpi_w), Inches(0.07), kpi['color'])

        _txt(slide, int(kx + Inches(0.18)), int(ky + Inches(0.22)),
             int(kpi_w - Inches(0.36)), Inches(0.26),
             kpi['label'], size=8, bold=True, color=C_SLATE)

        _txt(slide, int(kx + Inches(0.18)), int(ky + Inches(0.54)),
             int(kpi_w - Inches(0.36)), Inches(1.30),
             kpi['value'], size=32, bold=True, color=kpi['color'])

        _rect(slide, int(kx + Inches(0.18)), int(ky + Inches(1.92)),
              int(kpi_w - Inches(0.36)), Emu(12000), C_LINE)

        _txt(slide, int(kx + Inches(0.18)), int(ky + Inches(2.06)),
             int(kpi_w - Inches(0.36)), Inches(0.24),
             'OBJECTIF', size=6.5, color=C_SLATE)
        _txt(slide, int(kx + Inches(0.18)), int(ky + Inches(2.30)),
             int(kpi_w - Inches(0.36)), Inches(0.60),
             kpi['target'], size=18, bold=True, color=C_GREEN)

        _txt(slide, int(kx + Inches(0.18)), int(ky + Inches(2.98)),
             int(kpi_w - Inches(0.36)), Inches(0.24),
             'SUIVI MENSUEL', size=6.5, color=C_SLATE)

        # Barre de statut en bas de carte
        _rect(slide, int(kx), int(ky + kpi_h - Inches(0.26)),
              int(kpi_w), Inches(0.26), kpi['color'])
        _txt(slide, int(kx + Inches(0.10)), int(ky + kpi_h - Inches(0.24)),
             int(kpi_w - Inches(0.20)), Inches(0.22),
             'À SURVEILLER', size=6.5, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 12 — LE COPILOTE FINANCIER EXÉCUTIF
# ─────────────────────────────────────────────────────────────────────────────

def _s12_copilot(prs, date_str: str):
    slide = _blank(prs)
    _header(slide, '12 — SYSTÈME', 'Le Copilote Financier Exécutif.')
    _footer(slide, 12, date_str)

    # Tagline
    _txt(slide, MARGIN_L, HDR_TOP + Inches(0.06), CONTENT_W, Inches(0.32),
         'Pepperyn ne produit pas un rapport. Pepperyn accompagne les décisions dans le temps.',
         size=12, color=C_GRAY, align=PP_ALIGN.CENTER)

    # Deux colonnes de flux
    steps_left = [
        ('01', 'Import Excel',               C_BLUE),
        ('02', 'Executive Decision Model',   C_NAVY),
        ('03', 'Executive Report',           C_NAVY),
        ('04', 'Board Decision Package',     C_NAVY),
        ('05', 'Décisions du Board',         C_GREEN),
    ]
    steps_right = [
        ('06', 'Historique des décisions',   C_SLATE),
        ('07', 'Nouvelle analyse',           C_BLUE),
        ('08', 'Comparaison automatique',    C_BLUE),
        ('09', 'Nouveau Board Deck',         C_NAVY),
        ('10', 'Amélioration continue',      C_GREEN),
    ]

    col_w   = int(CONTENT_W * 0.36)
    col_l   = int(MARGIN_L + Inches(0.20))
    col_r   = int(MARGIN_L + CONTENT_W - col_w - Inches(0.20))
    step_h  = Inches(0.56)
    start_y = HDR_TOP + Inches(0.50)

    for side_steps, cx in [(steps_left, col_l), (steps_right, col_r)]:
        for i, (num, label, color) in enumerate(side_steps):
            sy = start_y + i * step_h

            # Boîte
            _rect(slide, cx, int(sy), col_w, Inches(0.44),
                  C_LIGHT, border_color=color, border_pt=1.2)
            # Pastille numéro
            _rect(slide, cx, int(sy), Inches(0.38), Inches(0.44), color)
            _txt(slide, cx, int(sy), Inches(0.38), Inches(0.44),
                 num, size=8, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
            # Texte
            _txt(slide, cx + Inches(0.46), int(sy + Inches(0.08)),
                 col_w - Inches(0.52), Inches(0.30),
                 label, size=10, bold=True, color=C_DARK)

            # Flèche vers le bas
            if i < len(side_steps) - 1:
                ax = int(cx + col_w / 2 - Inches(0.08))
                ay = int(sy + Inches(0.44))
                _txt(slide, ax, ay, Inches(0.16), Inches(0.12),
                     '↓', size=9, color=C_SLATE, align=PP_ALIGN.CENTER)

    # Pont entre colonnes (bas) et label loop
    loop_base = start_y + len(steps_left) * step_h + Inches(0.06)
    bridge_w  = col_r + col_w - col_l
    _rect(slide, col_l, int(loop_base), bridge_w, Emu(10000), C_LINE)
    _txt(slide, col_l + Inches(0.20), int(loop_base + Inches(0.02)),
         bridge_w - Inches(0.40), Inches(0.22),
         '→   Alimentent automatiquement   →',
         size=7.5, italic=True, color=C_GREEN, align=PP_ALIGN.CENTER)

    # Symbole boucle au centre
    center_x = col_l + col_w + Inches(0.10)
    center_w  = col_r - center_x - Inches(0.10)
    _txt(slide, int(center_x), int(start_y + Inches(0.70)),
         int(center_w), Inches(2.60),
         '⟳', size=60, bold=True, color=C_LINE, align=PP_ALIGN.CENTER)
    _txt(slide, int(center_x), int(start_y + Inches(2.00)),
         int(center_w), Inches(0.55),
         'Boucle\ncontinue', size=8, color=C_SLATE, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def generate_pptx_report(result: Any, company_name: Optional[str] = None) -> bytes:
    """
    Génère l'Executive Board Deck V5 depuis l'EDM.
    `result` peut être :
      - un objet avec attribut `edm` (ExecutiveDecisionModel)
      - un dict (result_dict depuis le cache Supabase/mémoire)
    Si l'EDM est absent, il est construit à la volée depuis le dict.
    Retourne les bytes du fichier .pptx.
    """
    # Extraction EDM
    edm = getattr(result, 'edm', None)
    if edm is None and isinstance(result, dict):
        edm = result.get('edm')

    # Fallback : construire l'EDM depuis le dict d'analyse
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
    _s02_urgency(prs, edm, date_str)
    _s03_waterfall(prs, edm, date_str)
    _s04_decisions(prs, edm, date_str)
    _s05_matrix(prs, edm, date_str)
    _s06_bridge(prs, edm, date_str)
    _s07_before_after(prs, edm, date_str)
    _s08_scenarios(prs, edm, date_str)
    _s09_gantt(prs, edm, date_str)
    _s10_vote(prs, edm, date_str)
    _s11_kpis(prs, edm, date_str)
    _s12_copilot(prs, date_str)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()
