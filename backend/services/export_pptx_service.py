"""
export_pptx_service.py — Executive Board Deck V4
Pepperyn — Copilote Financier Exécutif

Principe fondamental :
Ce service ne fait QUE raconter visuellement l'histoire déjà contenue dans
l'ExecutiveDecisionModel. Aucune logique métier. Aucun calcul. Aucune
interprétation. Toutes les données proviennent de l'EDM.
Une slide = une idée = une décision.

Structure :
 1. EXECUTIVE DECISION (couverture)
 2. EXECUTIVE SUMMARY
 3. POURQUOI EN SOMMES-NOUS ARRIVÉS LÀ ?
 4. CEO DASHBOARD
 5. OÙ LA VALEUR EST DÉTRUITE
 6. COÛT DE L'INACTION
 7. LES CINQ DÉCISIONS PRIORITAIRES
 8. ROADMAP D'EXÉCUTION
 9. SIMULATION AVANT / APRÈS
10. PROJECTION À 12 MOIS
11. RISQUES MAJEURS
12. MATRICE IMPACT / EFFORT
13. CARNET D'EXÉCUTION
14. TABLEAU DE BORD DE SUIVI
15. LUNDI MATIN
    APPENDIX (non numérotée)
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Optional

from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt


# ─── Palette McKinsey ────────────────────────────────────────────────────────
C_NAVY  = RGBColor(0x0A, 0x25, 0x40)   # fond couverture
C_BLUE  = RGBColor(0x1B, 0x73, 0xE8)   # accent Pepperyn
C_DARK  = RGBColor(0x1A, 0x1A, 0x2E)   # titres
C_GRAY  = RGBColor(0x5F, 0x63, 0x68)   # corps texte
C_SLATE = RGBColor(0x94, 0xA3, 0xB8)   # éléments discrets
C_LIGHT = RGBColor(0xF8, 0xFA, 0xFF)   # fond clair
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_GREEN = RGBColor(0x15, 0x80, 0x3D)   # positif / action
C_RED   = RGBColor(0xDC, 0x26, 0x26)   # négatif / inaction
C_AMBER = RGBColor(0xB4, 0x53, 0x09)   # priorité moyenne
C_LINE  = RGBColor(0xE2, 0xE8, 0xF0)   # séparateurs

SLIDE_W  = Inches(13.33)
SLIDE_H  = Inches(7.5)
MARGIN_L = Inches(0.65)
MARGIN_T = Inches(1.5)
CONTENT_W = SLIDE_W - Inches(1.3)
CONTENT_H = SLIDE_H - Inches(2.1)


# ─── Formatage (affichage uniquement, pas de calcul métier) ──────────────────

def _fmt_eur(v: Optional[float]) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    av = abs(v)
    if av >= 1_000_000:
        return f"{sign}{av / 1_000_000:.1f}M €"
    if av >= 1_000:
        return f"{sign}{av / 1_000:.0f}K €"
    return f"{sign}{av:.0f} €"


def _priority_color(priority: str) -> RGBColor:
    p = (priority or "").lower()
    if "high" in p:
        return C_RED
    if "medium" in p:
        return C_AMBER
    return C_SLATE


def _difficulty_idx(d: Optional[str]) -> float:
    """Convertit la difficulté qualitative (LLM) en indice 0-1 pour les matrices."""
    t = (d or "").strip().lower()
    if "faible" in t or "low" in t:
        return 0.2
    if "élevée" in t or "elevee" in t or "high" in t:
        return 0.8
    return 0.5


def _trend_prob(trend: Optional[str]) -> float:
    """Probabilité approximée depuis la tendance — affichage uniquement."""
    t = (trend or "").lower()
    if "up" in t:
        return 0.78
    if "down" in t:
        return 0.22
    return 0.50


def _trunc(text: str, n: int = 60) -> str:
    t = (text or "").strip()
    return t[:n] + "…" if len(t) > n else t


# ─── Primitives graphiques ───────────────────────────────────────────────────

def _add_slide(prs: Presentation) -> Any:
    return prs.slides.add_slide(prs.slide_layouts[6])  # layout blank


def _rect(slide, left, top, width, height, fill: RGBColor,
          line_rgb: Optional[RGBColor] = None, line_pt: float = 0.5):
    s = slide.shapes.add_shape(1, left, top, width, height)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line_rgb:
        s.line.color.rgb = line_rgb
        s.line.width = Pt(line_pt)
    else:
        s.line.fill.background()
    return s


def _txt(slide, left, top, width, height, text: str, *,
         size: int = 11, bold: bool = False, color: RGBColor = C_DARK,
         align: PP_ALIGN = PP_ALIGN.LEFT, italic: bool = False,
         wrap: bool = True) -> Any:
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = str(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = "Calibri"
    return tb


# ─── Layout commun (hors couverture) ────────────────────────────────────────

def _slide_layout(slide, section: str, title: str, slide_num: int) -> None:
    """Cadre McKinsey : bordure gauche navy, label section, titre, pied de page."""
    # Bordure verticale gauche
    _rect(slide, 0, 0, Inches(0.08), SLIDE_H, C_NAVY)

    # Label section (petit, gris, uppercase)
    _txt(slide, MARGIN_L, Inches(0.30), Inches(10), Inches(0.28),
         section.upper(), size=8, bold=True, color=C_SLATE)

    # Titre principal
    _txt(slide, MARGIN_L, Inches(0.55), Inches(11.5), Inches(0.75),
         title, size=22, bold=True, color=C_DARK)

    # Séparateur sous le titre
    _rect(slide, MARGIN_L, Inches(1.22), Inches(12.4), Inches(0.018), C_LINE)

    # Pied de page
    _rect(slide, 0, SLIDE_H - Inches(0.28), SLIDE_W, Inches(0.28), C_NAVY)
    _txt(slide, Inches(0.2), SLIDE_H - Inches(0.26), Inches(8), Inches(0.22),
         f"Pepperyn · Executive Financial Review · CONFIDENTIEL",
         size=7, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(1.0), SLIDE_H - Inches(0.26), Inches(0.8), Inches(0.22),
         str(slide_num), size=7, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─── SLIDE 1 — EXECUTIVE DECISION (couverture) ───────────────────────────────

def _s01_cover(prs, edm, company_name: str, date_str: str) -> None:
    slide = _add_slide(prs)

    # Fond navy plein
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, C_NAVY)

    # Bandeau bleu accent gauche
    _rect(slide, 0, 0, Inches(0.45), SLIDE_H, C_BLUE)

    # Label discret
    _txt(slide, Inches(0.75), Inches(0.55), Inches(8), Inches(0.35),
         "EXECUTIVE DECISION", size=9, bold=True, color=C_SLATE)

    # Nom de la société
    co = company_name or "—"
    _txt(slide, Inches(0.75), Inches(1.2), Inches(11), Inches(0.9),
         co, size=38, bold=True, color=C_WHITE)

    # Séparateur fin
    _rect(slide, Inches(0.75), Inches(2.25), Inches(5), Inches(0.03), C_BLUE)

    # Date et confidentiel
    _txt(slide, Inches(0.75), Inches(2.4), Inches(6), Inches(0.3),
         f"{date_str}  ·  CONFIDENTIEL", size=10, color=C_SLATE)

    # Phrase principale (décision la plus importante)
    main_phrase = ""
    if edm.executive_decision and edm.executive_decision.decision:
        main_phrase = edm.executive_decision.decision
    if not main_phrase and edm.executive_decisions:
        main_phrase = edm.executive_decisions[0].decision

    if main_phrase:
        _txt(slide, Inches(0.75), Inches(3.3), Inches(11.5), Inches(2.0),
             f'"{_trunc(main_phrase, 120)}"',
             size=20, bold=False, italic=True, color=C_WHITE, wrap=True)

    # Branding Pepperyn
    _txt(slide, Inches(0.75), SLIDE_H - Inches(0.75), Inches(6), Inches(0.4),
         "Pepperyn  ·  Copilote Financier Exécutif",
         size=9, color=C_SLATE)


# ─── SLIDE 2 — EXECUTIVE SUMMARY (3 cartes horizontales) ────────────────────

def _s02_executive_summary(prs, edm, num: int = 2) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "EXECUTIVE SUMMARY", "Les trois décisions les plus importantes.", num)

    decisions = edm.executive_decisions[:3]
    if not decisions:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes pour générer le résumé exécutif.", size=11, color=C_GRAY)
        return

    card_w = CONTENT_W / 3 - Inches(0.2)
    card_h = Inches(4.8)
    card_y = MARGIN_T

    labels = ["Décision 1", "Décision 2", "Décision 3"]

    for i, dec in enumerate(decisions):
        x = MARGIN_L + i * (card_w + Inches(0.3))

        # Fond de la carte
        _rect(slide, x, card_y, card_w, card_h, C_LIGHT, C_LINE)

        # Bandeau supérieur coloré
        accent = C_BLUE if i == 0 else C_SLATE
        _rect(slide, x, card_y, card_w, Inches(0.06), accent)

        # Numéro
        _txt(slide, x + Inches(0.18), card_y + Inches(0.15), card_w, Inches(0.3),
             labels[i], size=8, bold=True, color=C_SLATE)

        # Décision
        _txt(slide, x + Inches(0.18), card_y + Inches(0.5), card_w - Inches(0.3), Inches(1.4),
             _trunc(dec.decision, 80), size=11, bold=True, color=C_DARK, wrap=True)

        # Impact
        impact_txt = _fmt_eur(dec.annual_impact)
        impact_color = C_GREEN if (dec.annual_impact or 0) > 0 else C_RED
        _txt(slide, x + Inches(0.18), card_y + Inches(2.05), card_w - Inches(0.3), Inches(0.45),
             impact_txt, size=19, bold=True, color=impact_color)
        _txt(slide, x + Inches(0.18), card_y + Inches(2.48), card_w - Inches(0.3), Inches(0.25),
             "impact annuel estimé", size=7, color=C_SLATE)

        # Séparateur
        _rect(slide, x + Inches(0.18), card_y + Inches(2.85), card_w - Inches(0.36), Inches(0.01), C_LINE)

        # Priorité / ROI
        pcolor = _priority_color(dec.priority)
        _txt(slide, x + Inches(0.18), card_y + Inches(2.98), card_w - Inches(0.3), Inches(0.28),
             f"Priorité : {dec.priority or '—'}  ·  ROI : {dec.roi_score:.1f}",
             size=8, bold=True, color=pcolor)

        # Échéance
        _txt(slide, x + Inches(0.18), card_y + Inches(3.35), card_w - Inches(0.3), Inches(0.28),
             f"Horizon : {dec.timeline or '—'}", size=8, color=C_GRAY)

        # Statut
        _txt(slide, x + Inches(0.18), card_y + Inches(3.7), card_w - Inches(0.3), Inches(0.28),
             f"Statut : {dec.status}", size=8, italic=True, color=C_SLATE)


# ─── SLIDE 3 — POURQUOI EN SOMMES-NOUS ARRIVÉS LÀ ? ─────────────────────────

def _s03_why(prs, edm, result: dict, num: int = 3) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "DIAGNOSTIC", "Pourquoi en sommes-nous arrivés là ?", num)

    # Les 3 causes principales — dérivées des value destroyers (déjà dans l'EDM)
    causes = []
    for d in edm.value_destroyers[:3]:
        label = _trunc(d.name, 55)
        causes.append((label, d.comment or "", d.annual_impact))

    # Fallback : leviers stratégiques
    if not causes:
        for lever in edm.strategic_levers[:3]:
            causes.append((_trunc(lever, 55), "", None))

    if not causes:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    # Affichage des causes (colonnes)
    col_w = CONTENT_W / max(len(causes), 1) - Inches(0.25)
    for i, (cause, comment, impact) in enumerate(causes):
        x = MARGIN_L + i * (col_w + Inches(0.35))
        y = MARGIN_T

        # Numéro
        _txt(slide, x, y, Inches(0.4), Inches(0.4),
             str(i + 1), size=20, bold=True, color=C_BLUE)

        # Titre cause
        _txt(slide, x + Inches(0.45), y + Inches(0.05), col_w - Inches(0.5), Inches(0.6),
             cause, size=12, bold=True, color=C_DARK, wrap=True)

        # Séparateur
        _rect(slide, x, y + Inches(0.75), col_w, Inches(0.02), C_LINE)

        # Commentaire
        if comment:
            _txt(slide, x, y + Inches(0.9), col_w, Inches(1.2),
                 _trunc(comment, 100), size=10, color=C_GRAY, wrap=True)

        # Impact
        if impact is not None:
            _txt(slide, x, y + Inches(2.2), col_w, Inches(0.35),
                 _fmt_eur(impact), size=14, bold=True,
                 color=C_RED if impact < 0 else C_GREEN)

    # Conclusion (lecture de result — texte libre LLM, aucun calcul)
    summary = (result or {}).get("resume_executif") or (result or {}).get("synthese") or ""
    if summary:
        conclusion = _trunc(summary, 140)
        _rect(slide, MARGIN_L, SLIDE_H - Inches(1.85), CONTENT_W, Inches(0.65), C_NAVY)
        _txt(slide, MARGIN_L + Inches(0.2), SLIDE_H - Inches(1.82), CONTENT_W - Inches(0.4), Inches(0.6),
             conclusion, size=10, italic=True, color=C_WHITE, wrap=True)


# ─── SLIDE 4 — CEO DASHBOARD ─────────────────────────────────────────────────

def _s04_ceo_dashboard(prs, edm, result: dict, num: int = 4) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "GOUVERNANCE", "CEO Dashboard.", num)

    # Priorité à l'EDM ; fallback sur les cartes brutes du LLM (lecture uniquement)
    raw_cards = (result or {}).get("ceo_dashboard") or []
    kpis = []
    for c in raw_cards[:6]:
        if isinstance(c, dict):
            kpis.append((c.get("label", ""), c.get("value", "—")))

    # Assure EBITDA et Cash depuis l'EDM en tête
    edm_kpis = []
    if edm.ebitda:
        edm_kpis.append(("EBITDA", edm.ebitda))
    if edm.available_cash:
        edm_kpis.append(("Cash disponible", edm.available_cash))

    # Fusion : EDM en tête, raw_cards en complément (sans doublon)
    edm_labels = {k.lower() for k, _ in edm_kpis}
    merged = list(edm_kpis) + [
        (k, v) for k, v in kpis if k.lower() not in edm_labels
    ]
    merged = merged[:6]

    if not merged:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes pour le CEO Dashboard.", size=11, color=C_GRAY)
        return

    cols = 3
    rows = (len(merged) + cols - 1) // cols
    cell_w = CONTENT_W / cols - Inches(0.2)
    cell_h = Inches(2.0)

    for idx, (label, value) in enumerate(merged):
        col = idx % cols
        row = idx // cols
        x = MARGIN_L + col * (cell_w + Inches(0.3))
        y = MARGIN_T + row * (cell_h + Inches(0.15))

        _rect(slide, x, y, cell_w, cell_h, C_LIGHT, C_LINE)
        _rect(slide, x, y, cell_w, Inches(0.05), C_NAVY)

        _txt(slide, x + Inches(0.2), y + Inches(0.15), cell_w - Inches(0.3), Inches(0.28),
             (label or "").upper(), size=8, bold=True, color=C_SLATE)

        _txt(slide, x + Inches(0.2), y + Inches(0.5), cell_w - Inches(0.3), Inches(1.1),
             str(value or "—"), size=20, bold=True, color=C_DARK, wrap=True)


# ─── SLIDE 5 — OÙ LA VALEUR EST DÉTRUITE ─────────────────────────────────────

def _s05_waterfall(prs, edm, num: int = 5) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "IMPACT FINANCIER", "Où la valeur est détruite.", num)

    destroyers = [d for d in edm.value_destroyers if d.annual_impact is not None]
    if not destroyers:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    # ── Chart natif python-pptx (BAR_CLUSTERED horizontal) ───────────────────
    chart_data = ChartData()
    chart_data.categories = [_trunc(d.name, 28) for d in destroyers]
    chart_data.add_series("Impact", tuple(d.annual_impact for d in destroyers))

    gf = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED,
        MARGIN_L, MARGIN_T,
        Inches(10.5), Inches(4.8),
        chart_data,
    )
    chart = gf.chart
    chart.has_legend = False

    # Couleur de la série par valeur (rouge pour les coûts négatifs)
    try:
        series = chart.series[0]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = C_RED
        series.format.line.fill.background()
    except Exception:
        pass

    # Valeur pour chaque barre affichée à côté (annotation textuelle)
    bar_h = Inches(4.8) / (len(destroyers) + 1)
    for i, d in enumerate(destroyers):
        label_y = MARGIN_T + Inches(0.35) + i * bar_h
        _txt(slide, MARGIN_L + Inches(10.6), label_y, Inches(2.2), bar_h,
             _fmt_eur(d.annual_impact), size=9, bold=True,
             color=C_RED if (d.annual_impact or 0) < 0 else C_GREEN)

    # Légende axe
    _txt(slide, MARGIN_L, SLIDE_H - Inches(1.6), CONTENT_W, Inches(0.25),
         "Montants en euros — impact annuel estimé · Source : EDM Pepperyn",
         size=7, italic=True, color=C_SLATE)


# ─── SLIDE 6 — COÛT DE L'INACTION ────────────────────────────────────────────

def _s06_cost_of_inaction(prs, edm, num: int = 6) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "DÉCISION", "Le coût de l'inaction.", num)

    coi = edm.cost_of_inaction
    if not coi or coi.per_year is None:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    # Valeur centrale dominante (annuelle)
    _txt(slide, MARGIN_L, MARGIN_T - Inches(0.1), CONTENT_W, Inches(1.0),
         "Chaque année sans décision coûte :", size=13, bold=False, color=C_GRAY)

    _txt(slide, MARGIN_L, MARGIN_T + Inches(0.8), CONTENT_W, Inches(1.5),
         _fmt_eur(coi.per_year), size=52, bold=True, color=C_RED, align=PP_ALIGN.CENTER)

    # 4 KPI secondaires
    kpis = [
        ("Par mois", coi.per_month),
        ("Par semaine", coi.per_week),
        ("Par jour", coi.per_day),
        ("Par heure", coi.per_hour),
    ]
    kw = CONTENT_W / 4 - Inches(0.2)
    ky = MARGIN_T + Inches(2.5)

    for i, (label, val) in enumerate(kpis):
        x = MARGIN_L + i * (kw + Inches(0.25))
        _rect(slide, x, ky, kw, Inches(1.25), C_LIGHT, C_LINE)
        _txt(slide, x + Inches(0.15), ky + Inches(0.12), kw - Inches(0.3), Inches(0.28),
             label.upper(), size=8, bold=True, color=C_SLATE)
        _txt(slide, x + Inches(0.15), ky + Inches(0.42), kw - Inches(0.3), Inches(0.65),
             _fmt_eur(val), size=15, bold=True, color=C_RED)

    # Phrase d'impact
    _txt(slide, MARGIN_L, ky + Inches(1.55), CONTENT_W, Inches(0.35),
         "Ce chiffre augmente chaque heure. La décision ne peut pas attendre.",
         size=11, bold=True, color=C_DARK, italic=True)


# ─── SLIDE 7 — LES CINQ DÉCISIONS PRIORITAIRES ───────────────────────────────

def _s07_decisions_table(prs, edm, num: int = 7) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "DÉCISIONS", "Les cinq décisions prioritaires.", num)

    decisions = edm.executive_decisions[:5]
    if not decisions:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Aucune décision identifiée.", size=11, color=C_GRAY)
        return

    # Colonnes : Décision, Impact, ROI, Priorité, Responsable, Échéance, Statut
    cols = [
        ("Décision",   Inches(3.8)),
        ("Impact",     Inches(1.4)),
        ("ROI",        Inches(0.9)),
        ("Priorité",   Inches(1.1)),
        ("Responsable",Inches(1.5)),
        ("Échéance",   Inches(1.4)),
        ("Statut",     Inches(1.3)),
    ]

    row_h = Inches(0.52)
    header_h = Inches(0.38)
    y = MARGIN_T

    # En-tête
    x = MARGIN_L
    _rect(slide, MARGIN_L, y, CONTENT_W, header_h, C_NAVY)
    for (col_label, col_w) in cols:
        _txt(slide, x + Inches(0.08), y + Inches(0.06), col_w - Inches(0.1), header_h,
             col_label.upper(), size=7.5, bold=True, color=C_WHITE)
        x += col_w

    y += header_h

    for i, dec in enumerate(decisions):
        bg = C_WHITE if i % 2 == 0 else C_LIGHT
        _rect(slide, MARGIN_L, y, CONTENT_W, row_h, bg, C_LINE, 0.3)

        x = MARGIN_L
        pcolor = _priority_color(dec.priority)

        values = [
            (_trunc(dec.decision, 52), C_DARK, 9, True),
            (_fmt_eur(dec.annual_impact), C_GREEN if (dec.annual_impact or 0) > 0 else C_RED, 10, True),
            (f"{dec.roi_score:.1f}", C_BLUE, 10, True),
            (dec.priority or "—", pcolor, 9, True),
            (dec.owner or "—", C_GRAY, 9, False),
            (dec.timeline or "—", C_GRAY, 9, False),
            (dec.status, C_SLATE, 8, False),
        ]

        for j, ((val, col, sz, bld), (_, col_w)) in enumerate(zip(values, cols)):
            _txt(slide, x + Inches(0.08), y + Inches(0.1), col_w - Inches(0.12), row_h - Inches(0.12),
                 val, size=sz, bold=bld, color=col, wrap=True)
            x += col_w

        y += row_h


# ─── SLIDE 8 — ROADMAP D'EXÉCUTION ───────────────────────────────────────────

def _s08_roadmap(prs, edm, num: int = 8) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "EXÉCUTION", "Roadmap d'exécution — 30 / 60 / 90 jours.", num)

    phases = edm.roadmap_90_days
    if not phases:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Aucune action planifiée.", size=11, color=C_GRAY)
        return

    # Ligne de temps horizontale
    timeline_y = MARGIN_T + Inches(0.25)
    _rect(slide, MARGIN_L, timeline_y + Inches(0.18), CONTENT_W, Inches(0.04), C_LINE)

    col_w = CONTENT_W / 3
    colors = [C_BLUE, C_NAVY, RGBColor(0x15, 0x60, 0x2D)]  # bleu, navy, vert foncé
    phase_labels = {"30": "0 → 30 jours · Stabilize",
                    "60": "30 → 60 jours · Optimize",
                    "90": "60 → 90 jours · Accelerate"}

    for i, phase in enumerate(phases[:3]):
        x = MARGIN_L + i * col_w
        color = colors[i % 3]

        # Pastille sur la ligne de temps
        dot_x = x + col_w / 2 - Inches(0.18)
        _rect(slide, dot_x, timeline_y + Inches(0.05), Inches(0.36), Inches(0.36), color)
        _txt(slide, dot_x, timeline_y + Inches(0.07), Inches(0.36), Inches(0.28),
             phase.horizon, size=9, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Label phase
        _txt(slide, x, timeline_y + Inches(0.55), col_w, Inches(0.3),
             phase_labels.get(phase.horizon, phase.phase_label),
             size=8, bold=True, color=color, align=PP_ALIGN.CENTER)

        # Séparateur
        _rect(slide, x + Inches(0.15), timeline_y + Inches(0.92), col_w - Inches(0.3), Inches(0.02), C_LINE)

        # Actions
        action_y = timeline_y + Inches(1.05)
        for j, action in enumerate(phase.actions[:4]):
            _txt(slide, x + Inches(0.18), action_y, col_w - Inches(0.3), Inches(0.42),
                 f"› {_trunc(action.decision, 48)}", size=9, color=C_DARK, wrap=True)
            if action.impact is not None:
                _txt(slide, x + Inches(0.18), action_y + Inches(0.28), col_w - Inches(0.3), Inches(0.22),
                     _fmt_eur(action.impact), size=8, bold=True,
                     color=C_GREEN if action.impact > 0 else C_RED)
            action_y += Inches(0.72)


# ─── SLIDE 9 — SIMULATION AVANT / APRÈS ──────────────────────────────────────

def _s09_before_after(prs, edm, num: int = 9) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "SIMULATION", "Impact de l'action vs inaction.", num)

    action = edm.action_series
    do_nothing = edm.do_nothing_series

    if not action or not do_nothing:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données de simulation insuffisantes.", size=11, color=C_GRAY)
        return

    n = len(action)
    chart_data = ChartData()
    chart_data.categories = [f"M{i + 1}" for i in range(n)]
    chart_data.add_series("Avec décisions (action)", tuple(action))
    chart_data.add_series("Sans décisions (inaction)", tuple(do_nothing))

    gf = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE,
        MARGIN_L, MARGIN_T,
        Inches(11.2), Inches(4.6),
        chart_data,
    )
    chart = gf.chart
    chart.has_legend = True

    try:
        for i, series in enumerate(chart.series):
            c = C_GREEN if i == 0 else C_RED
            series.format.line.color.rgb = c
            series.format.line.width = Pt(2.5)
            series.format.fill.background()
    except Exception:
        pass

    # Gains affichés à droite
    gain_y = MARGIN_T
    if action:
        _txt(slide, MARGIN_L + Inches(11.4), gain_y, Inches(1.6), Inches(0.3),
             "Gain EBITDA", size=8, bold=True, color=C_GREEN)
        _txt(slide, MARGIN_L + Inches(11.4), gain_y + Inches(0.3), Inches(1.6), Inches(0.4),
             _fmt_eur(action[-1] - do_nothing[-1] if do_nothing else action[-1]),
             size=13, bold=True, color=C_GREEN)
    _txt(slide, MARGIN_L, SLIDE_H - Inches(1.6), CONTENT_W, Inches(0.25),
         "Interpolation linéaire depuis l'impact global EDM — 12 points mensuels",
         size=7, italic=True, color=C_SLATE)


# ─── SLIDE 10 — PROJECTION À 12 MOIS ─────────────────────────────────────────

def _s10_projection(prs, edm, num: int = 10) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "PROJECTION", "Trajectoire financière — 12 mois.", num)

    proj = edm.monthly_projection
    if not proj:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    n = len(proj)
    chart_data = ChartData()
    chart_data.categories = [f"M{i + 1}" for i in range(n)]
    chart_data.add_series("Trajectoire cible", tuple(proj))

    gf = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE,
        MARGIN_L, MARGIN_T,
        Inches(11.2), Inches(4.6),
        chart_data,
    )
    chart = gf.chart
    chart.has_legend = False

    try:
        series = chart.series[0]
        series.format.line.color.rgb = C_BLUE
        series.format.line.width = Pt(2.5)
        series.format.fill.background()
    except Exception:
        pass

    # KPI finale
    if proj:
        _txt(slide, MARGIN_L + Inches(11.4), MARGIN_T, Inches(1.6), Inches(0.3),
             "Projection M12", size=8, bold=True, color=C_BLUE)
        _txt(slide, MARGIN_L + Inches(11.4), MARGIN_T + Inches(0.3), Inches(1.6), Inches(0.5),
             _fmt_eur(proj[-1]), size=14, bold=True, color=C_BLUE)

    _txt(slide, MARGIN_L, SLIDE_H - Inches(1.6), CONTENT_W, Inches(0.25),
         "Projection linéaire 12 mois — basée sur l'impact global identifié",
         size=7, italic=True, color=C_SLATE)


# ─── SLIDE 11 — RISQUES MAJEURS (matrice Impact × Probabilité) ───────────────

def _s11_risk_matrix(prs, edm, num: int = 11) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "RISQUES", "Risques majeurs.", num)

    risks = [(d.name, _trend_prob(d.trend), d.annual_impact)
             for d in edm.value_destroyers if d.annual_impact is not None]

    if not risks:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    # Matrice 2×2
    mx, my = MARGIN_L, MARGIN_T
    mw, mh = Inches(8.5), Inches(4.5)

    _rect(slide, mx, my, mw, mh, C_LIGHT, C_LINE)
    _rect(slide, mx + mw / 2, my, Inches(0.015), mh, C_LINE)
    _rect(slide, mx, my + mh / 2, mw, Inches(0.015), C_LINE)

    # Labels quadrants
    labels_q = [
        (mx + Inches(0.1),     my + Inches(0.08), "Faible impact · Forte probabilité",   "SURVEILLER"),
        (mx + mw / 2 + Inches(0.1), my + Inches(0.08), "Fort impact · Forte probabilité", "PRIORITÉ #1"),
        (mx + Inches(0.1),     my + mh / 2 + Inches(0.08), "Faible impact · Faible probabilité", "ACCEPTABLE"),
        (mx + mw / 2 + Inches(0.1), my + mh / 2 + Inches(0.08), "Fort impact · Faible probabilité", "QUICK WIN"),
    ]
    for (qx, qy, qlabel, qtitle) in labels_q:
        _txt(slide, qx, qy, mw / 2 - Inches(0.2), Inches(0.22),
             qtitle, size=8, bold=True, color=C_SLATE)

    # Axes labels
    _txt(slide, mx, my + mh + Inches(0.1), mw / 2, Inches(0.25),
         "← Faible", size=8, color=C_SLATE)
    _txt(slide, mx + mw / 2, my + mh + Inches(0.1), mw / 2, Inches(0.25),
         "Impact financier — Fort →", size=8, color=C_SLATE)
    _txt(slide, mx - Inches(0.5), my, Inches(0.4), mh / 2,
         "Forte probabilité", size=7, italic=True, color=C_SLATE)

    # Normaliser impact pour positionnement
    max_impact = max(abs(v) for _, _, v in risks)

    for name, prob, impact in risks[:8]:
        norm_x = min(abs(impact) / max(max_impact, 1), 1.0)
        # x : fort impact = droite
        dot_x = mx + norm_x * (mw - Inches(0.3)) + Inches(0.15)
        # y : forte probabilité = haut
        dot_y = my + (1 - prob) * (mh - Inches(0.3)) + Inches(0.15)

        _rect(slide, dot_x - Inches(0.12), dot_y - Inches(0.12),
              Inches(0.24), Inches(0.24), C_RED)

        _txt(slide, dot_x + Inches(0.15), dot_y - Inches(0.1),
             Inches(2.0), Inches(0.32),
             _trunc(name, 25), size=7.5, color=C_DARK)

    # Légende impact à droite
    _txt(slide, mx + mw + Inches(0.3), my, Inches(3.8), mh,
         "Les risques sont positionnés selon\nl'ampleur de leur impact financier\n(EDM) et la tendance observée.",
         size=8, italic=True, color=C_SLATE, wrap=True)


# ─── SLIDE 12 — MATRICE IMPACT / EFFORT ──────────────────────────────────────

def _s12_impact_effort(prs, edm, num: int = 12) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "PRIORITÉS", "Matrice impact / effort.", num)

    decisions = [(d.decision, _difficulty_idx(d.difficulty), d.annual_impact)
                 for d in edm.executive_decisions[:5] if d.annual_impact is not None]

    if not decisions:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Données insuffisantes.", size=11, color=C_GRAY)
        return

    mx, my = MARGIN_L, MARGIN_T
    mw, mh = Inches(8.5), Inches(4.5)

    _rect(slide, mx, my, mw, mh, C_LIGHT, C_LINE)
    _rect(slide, mx + mw / 2, my, Inches(0.015), mh, C_LINE)
    _rect(slide, mx, my + mh / 2, mw, Inches(0.015), C_LINE)

    quadrants = [
        (mx + Inches(0.1),         my + Inches(0.08), "Faible effort · Fort impact",  "QUICK WINS"),
        (mx + mw / 2 + Inches(0.1), my + Inches(0.08), "Fort effort · Fort impact",   "INVESTIR"),
        (mx + Inches(0.1),         my + mh / 2 + Inches(0.08), "Faible effort · Faible impact", "DÉLÉGUER"),
        (mx + mw / 2 + Inches(0.1), my + mh / 2 + Inches(0.08), "Fort effort · Faible impact",  "ÉVITER"),
    ]
    for (qx, qy, _, qtitle) in quadrants:
        _txt(slide, qx, qy, mw / 2 - Inches(0.2), Inches(0.22),
             qtitle, size=8, bold=True, color=C_SLATE)

    _txt(slide, mx, my + mh + Inches(0.1), mw / 2, Inches(0.25),
         "← Faible effort", size=8, color=C_SLATE)
    _txt(slide, mx + mw / 2, my + mh + Inches(0.1), mw / 2, Inches(0.25),
         "Effort élevé →", size=8, color=C_SLATE)

    max_impact = max(abs(v) for _, _, v in decisions)

    for i, (name, effort, impact) in enumerate(decisions):
        norm_y = min(abs(impact) / max(max_impact, 1), 1.0)
        # x : effort faible = gauche, effort élevé = droite
        dot_x = mx + effort * (mw - Inches(0.3)) + Inches(0.15)
        # y : fort impact = haut
        dot_y = my + (1 - norm_y) * (mh - Inches(0.3)) + Inches(0.15)

        _rect(slide, dot_x - Inches(0.12), dot_y - Inches(0.12),
              Inches(0.24), Inches(0.24), C_BLUE)
        _txt(slide, dot_x + Inches(0.18), dot_y - Inches(0.12),
             Inches(2.0), Inches(0.32),
             _trunc(name, 25), size=7.5, color=C_DARK)

    _txt(slide, mx + mw + Inches(0.3), my, Inches(3.8), mh,
         "Chaque décision est positionnée selon\nson impact estimé (EDM) et la\ndifficulté d'exécution (LLM).",
         size=8, italic=True, color=C_SLATE, wrap=True)


# ─── SLIDE 13 — CARNET D'EXÉCUTION ───────────────────────────────────────────

def _s13_execution_log(prs, edm, num: int = 13) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "SUIVI", "Carnet d'exécution.", num)

    log = edm.execution_log[:7]
    if not log:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Aucune action planifiée.", size=11, color=C_GRAY)
        return

    cols = [
        ("Action",          Inches(4.2)),
        ("Responsable",     Inches(1.6)),
        ("Échéance",        Inches(1.4)),
        ("Statut",          Inches(1.3)),
        ("Impact attendu",  Inches(1.5)),
        ("Score ROI",       Inches(0.85)),
    ]

    row_h = Inches(0.5)
    header_h = Inches(0.36)
    y = MARGIN_T

    _rect(slide, MARGIN_L, y, CONTENT_W, header_h, C_NAVY)
    x = MARGIN_L
    for col_label, col_w in cols:
        _txt(slide, x + Inches(0.08), y + Inches(0.07), col_w - Inches(0.1), header_h,
             col_label.upper(), size=7.5, bold=True, color=C_WHITE)
        x += col_w

    y += header_h
    for i, item in enumerate(log):
        bg = C_WHITE if i % 2 == 0 else C_LIGHT
        _rect(slide, MARGIN_L, y, CONTENT_W, row_h, bg, C_LINE, 0.3)

        x = MARGIN_L
        vals = [
            (_trunc(item.decision, 55), C_DARK, 8.5, True),
            (item.owner or "—",         C_GRAY, 8.5, False),
            (item.due_date or "—",      C_GRAY, 8.5, False),
            (item.status,               C_SLATE, 8, False),
            (_fmt_eur(item.impact),     C_GREEN if (item.impact or 0) > 0 else C_GRAY, 9, True),
            (f"{item.roi_score:.1f}",   C_BLUE, 9, True),
        ]
        for (val, col, sz, bld), (_, col_w) in zip(vals, cols):
            _txt(slide, x + Inches(0.08), y + Inches(0.1), col_w - Inches(0.1), row_h - Inches(0.12),
                 val, size=sz, bold=bld, color=col, wrap=True)
            x += col_w
        y += row_h


# ─── SLIDE 14 — TABLEAU DE BORD DE SUIVI ─────────────────────────────────────

def _s14_monitoring(prs, edm, num: int = 14) -> None:
    slide = _add_slide(prs)
    _slide_layout(slide, "PILOTAGE", "Tableau de bord de suivi.", num)

    decisions = edm.executive_decisions[:6]
    if not decisions:
        _txt(slide, MARGIN_L, MARGIN_T, CONTENT_W, Inches(0.4),
             "Aucune décision à piloter.", size=11, color=C_GRAY)
        return

    cols = [
        ("Décision",        Inches(4.0)),
        ("Objectif",        Inches(2.2)),
        ("Réalisé",         Inches(1.3)),
        ("Écart",           Inches(1.3)),
        ("Avancement",      Inches(2.0)),
        ("Statut",          Inches(1.0)),
    ]

    row_h = Inches(0.5)
    header_h = Inches(0.36)
    y = MARGIN_T

    _rect(slide, MARGIN_L, y, CONTENT_W, header_h, C_NAVY)
    x = MARGIN_L
    for col_label, col_w in cols:
        _txt(slide, x + Inches(0.08), y + Inches(0.07), col_w - Inches(0.1), header_h,
             col_label.upper(), size=7.5, bold=True, color=C_WHITE)
        x += col_w

    y += header_h
    for i, dec in enumerate(decisions):
        bg = C_WHITE if i % 2 == 0 else C_LIGHT
        _rect(slide, MARGIN_L, y, CONTENT_W, row_h, bg, C_LINE, 0.3)

        x = MARGIN_L
        vals = [
            (_trunc(dec.decision, 52),    C_DARK,  8.5, True),
            (_fmt_eur(dec.annual_impact), C_BLUE,  9,   True),
            ("—",                          C_SLATE, 9,   False),
            ("—",                          C_SLATE, 9,   False),
            ("À initialiser",              C_AMBER, 8,   False),
            (dec.status,                   C_SLATE, 8,   False),
        ]
        for (val, col, sz, bld), (_, col_w) in zip(vals, cols):
            _txt(slide, x + Inches(0.08), y + Inches(0.1), col_w - Inches(0.1), row_h - Inches(0.12),
                 val, size=sz, bold=bld, color=col, wrap=True)
            x += col_w
        y += row_h

    _txt(slide, MARGIN_L, y + Inches(0.15), CONTENT_W, Inches(0.3),
         "Tableau à mettre à jour à chaque réunion de suivi — Source : EDM Pepperyn",
         size=7.5, italic=True, color=C_SLATE)


# ─── SLIDE 15 — LUNDI MATIN ───────────────────────────────────────────────────

def _s15_monday_morning(prs, edm, num: int = 15) -> None:
    slide = _add_slide(prs)

    # Fond navy (slide spéciale)
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, C_NAVY)
    _rect(slide, 0, 0, Inches(0.08), SLIDE_H, C_BLUE)

    _txt(slide, MARGIN_L, Inches(0.35), Inches(8), Inches(0.55),
         "LUNDI MATIN", size=30, bold=True, color=C_WHITE)
    _txt(slide, MARGIN_L, Inches(0.95), Inches(9), Inches(0.35),
         "Les trois décisions à prendre avant 10h.", size=13, italic=True, color=C_SLATE)

    _rect(slide, MARGIN_L, Inches(1.42), Inches(11), Inches(0.03), C_BLUE)

    decisions = edm.executive_decisions[:3]
    if not decisions:
        _txt(slide, MARGIN_L, Inches(1.8), Inches(11), Inches(0.4),
             "Aucune décision prioritaire identifiée.", size=12, color=C_SLATE)
    else:
        card_h = Inches(1.55)
        cols_def = [
            ("Décision",           Inches(4.2)),
            ("Responsable",        Inches(1.8)),
            ("Impact",             Inches(1.8)),
            ("Échéance",           Inches(1.5)),
            ("Prob. succès",       Inches(1.6)),
        ]

        for i, dec in enumerate(decisions):
            cy = Inches(1.6) + i * (card_h + Inches(0.18))
            _rect(slide, MARGIN_L, cy, Inches(11.0), card_h, RGBColor(0x10, 0x2A, 0x48))
            _rect(slide, MARGIN_L, cy, Inches(0.06), card_h, C_BLUE)

            x = MARGIN_L + Inches(0.15)
            vals = [
                (_trunc(dec.decision, 55),  C_WHITE, 10, True),
                (dec.owner or "—",           C_SLATE, 10, False),
                (_fmt_eur(dec.annual_impact),C_GREEN if (dec.annual_impact or 0) > 0 else C_RED, 10, True),
                (dec.timeline or "—",        C_SLATE, 10, False),
                (f"{min(100, max(0, int(dec.roi_score * 10)))}%", C_BLUE, 10, True),
            ]
            for (val, col, sz, bld), (_, col_w) in zip(vals, cols_def):
                _txt(slide, x, cy + Inches(0.55), col_w - Inches(0.1), card_h - Inches(0.6),
                     val, size=sz, bold=bld, color=col, wrap=True)
                x += col_w

            # Label colonne (header au-dessus des cartes, première fois)
            if i == 0:
                hx = MARGIN_L + Inches(0.15)
                for (col_label, col_w) in cols_def:
                    _txt(slide, hx, cy + Inches(0.18), col_w - Inches(0.1), Inches(0.3),
                         col_label.upper(), size=7, bold=True, color=C_SLATE)
                    hx += col_w

    # Branding footer
    _txt(slide, MARGIN_L, SLIDE_H - Inches(0.5), Inches(8), Inches(0.35),
         "Pepperyn  ·  Copilote Financier Exécutif",
         size=9, bold=True, color=C_SLATE)
    _txt(slide, SLIDE_W - Inches(1.2), SLIDE_H - Inches(0.5), Inches(1.0), Inches(0.35),
         str(num), size=8, color=C_SLATE, align=PP_ALIGN.RIGHT)


# ─── APPENDIX ─────────────────────────────────────────────────────────────────

def _appendix(prs, edm) -> None:
    slide = _add_slide(prs)

    _rect(slide, 0, 0, Inches(0.08), SLIDE_H, C_SLATE)
    _txt(slide, MARGIN_L, Inches(0.3), Inches(8), Inches(0.4),
         "ANNEXE", size=11, bold=True, color=C_SLATE)

    _txt(slide, MARGIN_L, Inches(0.75), Inches(11), Inches(0.5),
         "Qualité des données · Hypothèses · Méthodologie",
         size=18, bold=True, color=C_DARK)

    _rect(slide, MARGIN_L, Inches(1.35), Inches(12.4), Inches(0.018), C_LINE)

    dq = edm.data_quality
    y = Inches(1.55)
    col_w = CONTENT_W / 2 - Inches(0.2)

    # Bloc gauche : qualité des données
    _txt(slide, MARGIN_L, y, col_w, Inches(0.3),
         "QUALITÉ DES DONNÉES", size=9, bold=True, color=C_NAVY)
    y2 = y + Inches(0.38)
    if dq:
        items_dq = [
            ("Score qualité", f"{dq.score_data or 0} / 100"),
            ("Statut", dq.status or "—"),
            ("Format détecté", dq.document_format or "—"),
            ("Anomalies", str(len(dq.anomalies or [])) if dq.anomalies is not None else "0"),
        ]
        for label, val in items_dq:
            _txt(slide, MARGIN_L, y2, col_w / 2, Inches(0.3),
                 label, size=9, color=C_GRAY)
            _txt(slide, MARGIN_L + col_w / 2, y2, col_w / 2, Inches(0.3),
                 str(val), size=9, bold=True, color=C_DARK)
            y2 += Inches(0.32)
    else:
        _txt(slide, MARGIN_L, y2, col_w, Inches(0.3),
             "Métadonnées de qualité non disponibles.", size=9, italic=True, color=C_SLATE)

    # Bloc droit : hypothèses et méthodologie
    rx = MARGIN_L + col_w + Inches(0.5)
    _txt(slide, rx, y, col_w, Inches(0.3),
         "HYPOTHÈSES & MÉTHODOLOGIE", size=9, bold=True, color=C_NAVY)

    methodology_lines = [
        "Toutes les données proviennent de l'Executive Decision Model (EDM).",
        "Les impacts financiers sont estimés à partir des données fournies.",
        "Les priorités sont dérivées de seuils fixes (≥500K€ = High, ≥100K€ = Medium).",
        "Les projections sont des interpolations linéaires — non des prévisions certifiées.",
        "Ce Board Deck est confidentiel et destiné exclusivement aux membres du CODIR.",
        "Pepperyn ne certifie pas les données sources — la responsabilité reste à l'utilisateur.",
    ]

    my2 = y + Inches(0.38)
    for line in methodology_lines:
        _txt(slide, rx, my2, col_w, Inches(0.3),
             f"· {line}", size=8, color=C_GRAY, wrap=True)
        my2 += Inches(0.34)

    # Commitments de suivi
    _rect(slide, MARGIN_L, SLIDE_H - Inches(1.55), CONTENT_W, Inches(0.02), C_LINE)
    _txt(slide, MARGIN_L, SLIDE_H - Inches(1.45), CONTENT_W, Inches(0.25),
         "ENGAGEMENTS PEPPERYN", size=8, bold=True, color=C_NAVY)
    follow_y = SLIDE_H - Inches(1.15)
    if edm.follow_up:
        for c in (edm.follow_up.commitments or [])[:3]:
            _txt(slide, MARGIN_L, follow_y, CONTENT_W, Inches(0.25),
                 f"· {c}", size=7.5, italic=True, color=C_GRAY)
            follow_y += Inches(0.26)

    # Pied de page
    _rect(slide, 0, SLIDE_H - Inches(0.28), SLIDE_W, Inches(0.28), C_NAVY)
    _txt(slide, Inches(0.2), SLIDE_H - Inches(0.26), Inches(8), Inches(0.22),
         "Pepperyn · Executive Financial Review · CONFIDENTIEL · ANNEXE NON NUMÉROTÉE",
         size=7, color=C_SLATE)


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def generate_pptx_report(result: dict, company_name: Optional[str] = None) -> bytes:
    """
    Génère le Board Deck exécutif V4 (15 slides + annexe) depuis le dict
    d'analyse brut. Toute la logique métier est déléguée à l'EDM ; ce service
    ne fait que la présentation visuelle.
    """
    from services.executive_decision_model import build_executive_decision_model

    edm = build_executive_decision_model(result or {})

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    date_str = datetime.now().strftime("%d %B %Y")
    co = company_name or (result or {}).get("company_name") or ""

    # 15 slides numérotées
    _s01_cover(prs, edm, co, date_str)
    _s02_executive_summary(prs, edm, num=2)
    _s03_why(prs, edm, result, num=3)
    _s04_ceo_dashboard(prs, edm, result, num=4)
    _s05_waterfall(prs, edm, num=5)
    _s06_cost_of_inaction(prs, edm, num=6)
    _s07_decisions_table(prs, edm, num=7)
    _s08_roadmap(prs, edm, num=8)
    _s09_before_after(prs, edm, num=9)
    _s10_projection(prs, edm, num=10)
    _s11_risk_matrix(prs, edm, num=11)
    _s12_impact_effort(prs, edm, num=12)
    _s13_execution_log(prs, edm, num=13)
    _s14_monitoring(prs, edm, num=14)
    _s15_monday_morning(prs, edm, num=15)

    # Annexe (non numérotée, non destinée à être projetée)
    _appendix(prs, edm)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
