"""
export_pptx_service.py
Génère une présentation PowerPoint professionnelle (Pepperyn) à partir d'un AnalysisResult v3.
Utilise python-pptx.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from pptx.enum.dml import MSO_THEME_COLOR
import re as _re


# ─── Text sanitisation ───────────────────────────────────────────────────────
def _clean(text: str) -> str:
    """Strip markdown formatting and audit artefacts for plain-text PPTX runs."""
    if not text:
        return ""
    text = _re.sub(r"~~.*?~~", "", text)        # remove strikethrough
    text = _re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold** → bold
    text = _re.sub(r"\*(.+?)\*", r"\1", text)       # *italic* → italic
    text = _re.sub(r"`(.+?)`", r"\1", text)          # `code` → code
    return text.strip()


# ─── Couleurs ────────────────────────────────────────────────────────────────
C_BLUE_DARK  = RGBColor(0x0D, 0x47, 0xA1)
C_BLUE_MAIN  = RGBColor(0x1B, 0x73, 0xE8)
C_BLUE_LIGHT = RGBColor(0xEF, 0xF6, 0xFF)
C_RED        = RGBColor(0xDC, 0x26, 0x26)
C_RED_LIGHT  = RGBColor(0xFE, 0xF2, 0xF2)
C_AMBER      = RGBColor(0xD9, 0x77, 0x06)
C_AMBER_LIGHT= RGBColor(0xFF, 0xFB, 0xEB)
C_ORANGE     = RGBColor(0xEA, 0x58, 0x0C)
C_ORANGE_LIGHT = RGBColor(0xFF, 0xF7, 0xED)
C_GREEN      = RGBColor(0x15, 0x80, 0x3D)
C_GREEN_LIGHT= RGBColor(0xF0, 0xFD, 0xF4)
C_DARK       = RGBColor(0x1A, 0x1A, 0x2E)
C_GRAY       = RGBColor(0x5F, 0x63, 0x68)
C_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
C_LIGHT_BLUE = RGBColor(0x90, 0xCA, 0xF9)

# Slide dimensions (widescreen 16:9)
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _rgb_to_hex(rgb: RGBColor) -> str:
    return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def _add_rect(slide, left, top, width, height, fill_rgb: RGBColor, line_rgb: RGBColor | None = None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    if line_rgb:
        shape.line.color.rgb = line_rgb
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    return shape


def _add_textbox(slide, left, top, width, height, text: str,
                 font_size: int = 11, bold: bool = False,
                 color: RGBColor = C_DARK, italic: bool = False,
                 align=PP_ALIGN.LEFT, word_wrap: bool = True) -> Any:
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return txBox


def _bullet_block(slide, items: list[str], left, top, width, height,
                  bg_color: RGBColor, border_color: RGBColor,
                  icon: str = "•", max_items: int = 8):
    """Add a coloured bullet list block."""
    shown = items[:max_items]
    extra = len(items) - max_items

    # Background
    rect = _add_rect(slide, left, top, width, height, bg_color, border_color)

    txBox = slide.shapes.add_textbox(
        left + Inches(0.15), top + Inches(0.1),
        width - Inches(0.3), height - Inches(0.2),
    )
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(shown):
        clean = _clean(item.lstrip("🔴🟢⚠️🔄• "))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(2)
        run = p.add_run()
        run.text = f"{icon}  {clean}"
        run.font.size = Pt(9)
        run.font.color.rgb = C_DARK
        run.font.name = "Calibri"

    if extra > 0:
        p = tf.add_paragraph()
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = f"+ {extra} élément(s) supplémentaire(s) — voir rapport PDF"
        run.font.size = Pt(8)
        run.font.italic = True
        run.font.color.rgb = C_GRAY
        run.font.name = "Calibri"


def _score_box(slide, left, top, size, label: str, value: int):
    """Draw a score circle (approximated as square with rounded border)."""
    if value >= 8:
        color = C_GREEN
    elif value >= 5:
        color = C_AMBER
    else:
        color = C_RED

    # Border box
    shape = slide.shapes.add_shape(9, left, top, size, size)  # 9 = rounded rect
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_WHITE
    shape.line.color.rgb = color
    shape.line.width = Pt(2.5)

    # Value
    _add_textbox(slide, left, top + Inches(0.05), size, size - Inches(0.3),
                 str(value), font_size=22, bold=True, color=color, align=PP_ALIGN.CENTER)
    # Label
    _add_textbox(slide, left, top + size - Inches(0.32), size, Inches(0.3),
                 label, font_size=8, color=C_GRAY, align=PP_ALIGN.CENTER)


def _add_slide(prs: Presentation, layout_idx: int = 6):
    """Add a blank slide."""
    layout = prs.slide_layouts[layout_idx]  # 6 = blank
    return prs.slides.add_slide(layout)


def _draw_slide_header(slide, title: str, subtitle: str = "",
                       bg: RGBColor = C_BLUE_MAIN, height: Inches = Inches(1.1)):
    """Top banner for content slides."""
    _add_rect(slide, 0, 0, SLIDE_W, height, bg)
    _add_textbox(slide, Inches(0.4), Inches(0.15), Inches(11), Inches(0.6),
                 title, font_size=16, bold=True, color=C_WHITE)
    if subtitle:
        _add_textbox(slide, Inches(0.4), Inches(0.7), Inches(11), Inches(0.35),
                     subtitle, font_size=9, color=C_LIGHT_BLUE)
    # Footer bar
    _add_rect(slide, 0, SLIDE_H - Inches(0.3), SLIDE_W, Inches(0.3), C_BLUE_DARK)
    now = datetime.now().strftime("%d/%m/%Y")
    _add_textbox(slide, Inches(0.2), SLIDE_H - Inches(0.28), Inches(6), Inches(0.25),
                 f"Pepperyn — Analyse financière · {now}", font_size=7, color=C_LIGHT_BLUE)
    _add_textbox(slide, Inches(10), SLIDE_H - Inches(0.28), Inches(3), Inches(0.25),
                 "confidentiel", font_size=7, color=C_LIGHT_BLUE, align=PP_ALIGN.RIGHT)


# ─── Slides ──────────────────────────────────────────────────────────────────
def _slide_cover(prs: Presentation, result: dict):
    slide = _add_slide(prs)

    # Full blue gradient background
    _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, C_BLUE_DARK)
    _add_rect(slide, 0, 0, Inches(8), SLIDE_H, C_BLUE_MAIN)

    # Title
    _add_textbox(slide, Inches(0.6), Inches(1.8), Inches(9), Inches(1.2),
                 "Rapport d'analyse financière", font_size=32, bold=True, color=C_WHITE)

    # Subtitle
    doc_type = result.get("type_document", "Document financier")
    conf = result.get("score_confiance", 0)
    date_str = datetime.now().strftime("%d/%m/%Y")
    _add_textbox(slide, Inches(0.6), Inches(3.1), Inches(9), Inches(0.5),
                 f"{doc_type}  ·  Confiance : {conf}%  ·  {date_str}",
                 font_size=12, color=C_LIGHT_BLUE)

    # Pepperyn branding
    _add_rect(slide, Inches(10.3), Inches(0.3), Inches(2.6), Inches(0.7), C_WHITE)
    _add_textbox(slide, Inches(10.3), Inches(0.3), Inches(2.6), Inches(0.7),
                 "Pepperyn", font_size=18, bold=True, color=C_BLUE_DARK, align=PP_ALIGN.CENTER)

    _add_textbox(slide, Inches(0.6), Inches(4.0), Inches(8), Inches(0.4),
                 "Analyse IA · Niveau expert · Confidentiel",
                 font_size=9, italic=True, color=C_LIGHT_BLUE)

    # Decorative line
    _add_rect(slide, Inches(0.6), Inches(3.7), Inches(4), Inches(0.04), C_WHITE)


def _slide_resume(prs: Presentation, result: dict):
    slide = _add_slide(prs)
    _draw_slide_header(slide, "📊  RÉSUMÉ EXÉCUTIF")

    resume = result.get("resume_executif") or result.get("synthese", "")
    if resume:
        _add_rect(slide, Inches(0.4), Inches(1.3), Inches(12.5), Inches(5.5), C_BLUE_LIGHT, C_BLUE_MAIN)
        _add_textbox(slide, Inches(0.6), Inches(1.5), Inches(12.1), Inches(5.2),
                     _clean(resume), font_size=12, color=C_DARK)


def _slide_diagnostic(prs: Presentation, result: dict):
    slide = _add_slide(prs)
    _draw_slide_header(slide, "💹  DIAGNOSTIC FINANCIER", bg=C_BLUE_DARK)

    y = Inches(1.25)
    row_h = Inches(1.7)

    for label, key in [
        ("Revenus", "diagnostic_revenus"),
        ("Coûts",   "diagnostic_couts"),
        ("Marges",  "diagnostic_marges"),
    ]:
        text = result.get(key, "")
        if not text:
            continue
        _add_rect(slide, Inches(0.4), y, Inches(12.5), row_h, C_BLUE_LIGHT, C_BLUE_MAIN)
        _add_textbox(slide, Inches(0.55), y + Inches(0.08), Inches(2), Inches(0.35),
                     label, font_size=10, bold=True, color=C_BLUE_DARK)
        _add_textbox(slide, Inches(0.55), y + Inches(0.4), Inches(12), Inches(1.2),
                     _clean(text), font_size=10, color=C_DARK)
        y += row_h + Inches(0.15)


def _slide_changements_alertes(prs: Presentation, result: dict):
    slide = _add_slide(prs)
    _draw_slide_header(slide, "🔄  CE QUI A CHANGÉ  ·  ⚠️  ALERTES", bg=C_AMBER)

    changements = result.get("ce_qui_a_change", [])
    alertes     = result.get("alertes", [])

    # Left: changements
    _add_textbox(slide, Inches(0.4), Inches(1.2), Inches(6), Inches(0.4),
                 "🔄  Ce qui a changé", font_size=11, bold=True, color=C_AMBER)
    if changements:
        _bullet_block(slide, changements,
                      Inches(0.4), Inches(1.65), Inches(5.9), Inches(5.4),
                      C_AMBER_LIGHT, C_AMBER, icon="→", max_items=7)
    else:
        _add_textbox(slide, Inches(0.4), Inches(1.65), Inches(5.9), Inches(0.5),
                     "Aucune variation notable détectée.", font_size=10, color=C_GRAY)

    # Right: alertes
    _add_textbox(slide, Inches(6.8), Inches(1.2), Inches(6), Inches(0.4),
                 f"⚠️  Alertes ({len(alertes)})", font_size=11, bold=True, color=C_ORANGE)
    if alertes:
        _bullet_block(slide, alertes,
                      Inches(6.8), Inches(1.65), Inches(6.1), Inches(5.4),
                      C_ORANGE_LIGHT, C_ORANGE, icon="⚠", max_items=7)
    else:
        _add_textbox(slide, Inches(6.8), Inches(1.65), Inches(6.1), Inches(0.5),
                     "Aucune alerte détectée.", font_size=10, color=C_GRAY)

    # Divider
    _add_rect(slide, Inches(6.6), Inches(1.2), Inches(0.03), Inches(5.9), C_GRAY)


def _slide_problemes(prs: Presentation, result: dict):
    problemes = result.get("problemes_critiques") or []
    if not problemes:
        return

    slide = _add_slide(prs)
    _draw_slide_header(slide, f"🔴  PROBLÈMES CRITIQUES ({len(problemes)})", bg=C_RED)
    _bullet_block(slide, problemes,
                  Inches(0.4), Inches(1.25), Inches(12.5), Inches(5.9),
                  C_RED_LIGHT, C_RED, icon="🔴", max_items=10)


def _slide_opportunites(prs: Presentation, result: dict):
    opportunites = result.get("opportunites_v3") or result.get("opportunites") or []
    if not opportunites:
        return

    opp_list: list[str] = []
    for o in opportunites:
        if isinstance(o, str):
            opp_list.append(o)
        elif isinstance(o, dict):
            opp_list.append(o.get("description", str(o)))

    if not opp_list:
        return

    slide = _add_slide(prs)
    _draw_slide_header(slide, f"🟢  OPPORTUNITÉS ({len(opp_list)})", bg=C_GREEN)
    _bullet_block(slide, opp_list,
                  Inches(0.4), Inches(1.25), Inches(12.5), Inches(5.9),
                  C_GREEN_LIGHT, C_GREEN, icon="🟢", max_items=10)


def _slide_plan_action(prs: Presentation, result: dict):
    actions = result.get("plan_action") or []
    if not actions:
        recs = result.get("recommandations", [])
        actions = [
            f"[{r.get('priorite', '').upper()}] {r.get('action', '')}"
            for r in recs if isinstance(r, dict)
        ]
    if not actions:
        return

    slide = _add_slide(prs)
    _draw_slide_header(slide, f"🎯  PLAN D'ACTION ({len(actions)} actions)", bg=C_BLUE_MAIN)

    y = Inches(1.25)
    row_h = Inches(0.68)
    max_show = min(len(actions), 8)

    for action in actions[:max_show]:
        clean = _clean(action.lstrip("🎯 "))
        is_haute = "priorité haute" in clean.lower() or "[HAUTE]" in clean.upper()
        is_moy   = "priorité moyenne" in clean.lower() or "[MOY" in clean.upper()
        badge = "HAUTE" if is_haute else "MOY." if is_moy else "—"
        badge_color = C_RED if is_haute else C_AMBER if is_moy else C_BLUE_MAIN

        # Badge
        _add_rect(slide, Inches(0.4), y + Inches(0.1), Inches(0.9), Inches(0.42), badge_color)
        _add_textbox(slide, Inches(0.4), y + Inches(0.08), Inches(0.9), Inches(0.42),
                     badge, font_size=8, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Action text
        _add_rect(slide, Inches(1.4), y + Inches(0.05), Inches(11.5), Inches(0.52), C_BLUE_LIGHT, C_BLUE_MAIN)
        _add_textbox(slide, Inches(1.55), y + Inches(0.1), Inches(11.2), Inches(0.42),
                     clean, font_size=9.5, color=C_DARK)
        y += row_h

    if len(actions) > max_show:
        _add_textbox(slide, Inches(0.4), y + Inches(0.05), Inches(12), Inches(0.35),
                     f"+ {len(actions) - max_show} action(s) supplémentaire(s) — voir rapport PDF",
                     font_size=8, italic=True, color=C_GRAY)


def _slide_scores_decision(prs: Presentation, result: dict):
    slide = _add_slide(prs)
    _draw_slide_header(slide, "📈  SCORES & ⚡ DÉCISION", bg=C_BLUE_DARK)

    # Scores
    scores = [
        ("Rentabilité", result.get("score_rentabilite")),
        ("Risque",      result.get("score_risque")),
        ("Structure",   result.get("score_structure")),
    ]
    valid_scores = [(l, v) for l, v in scores if v is not None]

    score_size = Inches(1.6)
    score_y = Inches(1.4)
    total_width = len(valid_scores) * score_size + (len(valid_scores) - 1) * Inches(0.5)
    score_x_start = (SLIDE_W - total_width) / 2

    for i, (label, value) in enumerate(valid_scores):
        x = score_x_start + i * (score_size + Inches(0.5))
        _score_box(slide, x, score_y, score_size, label, value)

    # Decision
    decision = result.get("decision", "")
    if decision:
        _add_rect(slide, Inches(0.4), Inches(3.5), Inches(12.5), Inches(0.35), C_BLUE_MAIN)
        _add_textbox(slide, Inches(0.5), Inches(3.5), Inches(4), Inches(0.35),
                     "⚡  DÉCISION", font_size=11, bold=True, color=C_WHITE)

        _add_rect(slide, Inches(0.4), Inches(3.88), Inches(12.5), Inches(2.8), C_BLUE_LIGHT, C_BLUE_MAIN)
        _add_textbox(slide, Inches(0.6), Inches(4.0), Inches(12.1), Inches(2.6),
                     decision, font_size=12, bold=True, color=C_BLUE_DARK)


# ─── Main ────────────────────────────────────────────────────────────────────
def generate_pptx_report(result: dict) -> bytes:
    """
    Generate a .pptx presentation from an analysis result dict (v3 format).
    Returns PPTX bytes.
    """
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _slide_cover(prs, result)

    resume = result.get("resume_executif") or result.get("synthese", "")
    if resume:
        _slide_resume(prs, result)

    diag_fields = ["diagnostic_revenus", "diagnostic_couts", "diagnostic_marges"]
    if any(result.get(f) for f in diag_fields):
        _slide_diagnostic(prs, result)

    # Changements + Alertes always on same slide
    _slide_changements_alertes(prs, result)

    _slide_problemes(prs, result)
    _slide_opportunites(prs, result)
    _slide_plan_action(prs, result)
    _slide_scores_decision(prs, result)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
