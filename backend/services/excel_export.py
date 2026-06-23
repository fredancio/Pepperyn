"""
excel_export.py — Executive Financial Model V2
Pepperyn — Copilote Financier Exécutif

Ce fichier n'est PAS un rapport Excel.
C'est un laboratoire de décision.

Le dirigeant doit ouvrir ce classeur et avoir immédiatement envie de tester
des hypothèses, de simuler des scénarios, d'explorer des décisions.

Toutes les données proviennent de l'ExecutiveDecisionModel (EDM).
Aucune logique métier propre au classeur.

Structure (8 feuilles) :
  1. Executive Dashboard     — KPI en temps réel
  2. Hypothèses              — Toutes les hypothèses modifiables (cellules bleues)
  3. Decision Lab            — Simulateur de décisions (cœur du modèle)
  4. Sensibilité             — Qu'est-ce qui influence le plus notre résultat ?
  5. Scénarios               — Prudent / Central / Ambitieux / Personnalisé
  6. Roadmap                 — Pilotage visuel des décisions
  7. Historique              — Comparaison inter-périodes (template)
  8. EDM (masquée)           — Source technique unique, ne pas modifier

Convention couleurs (standard modèles financiers) :
  Bleu  = saisie utilisateur modifiable
  Noir  = formule calculée automatiquement
  Vert  = lien inter-feuille
  Orange = alerte
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from models.schemas import AnalysisResult

# ─── Palette & conventions ────────────────────────────────────────────────────
P_NAVY  = "0A2540"
P_BLUE  = "1B73E8"
P_DARK  = "1A1A2E"
P_GRAY  = "5F6368"
P_SLATE = "94A3B8"
P_LINE  = "E2E8F0"
P_WHITE = "FFFFFF"
P_LIGHT = "F8FAFF"
P_GREEN = "158038"
P_RED   = "DC2626"
P_AMBER = "B45309"

# Convention de couleur standard (modèles financiers)
FONT_INPUT   = "0000FF"   # Bleu  = cellule saisie utilisateur
FONT_FORMULA = "000000"   # Noir  = formule automatique
FONT_LINK    = "008000"   # Vert  = lien inter-feuille

# Noms des feuilles (utilisés dans les formules Excel)
SN_DASH  = "Executive Dashboard"
SN_HYPO  = "Hypothèses"
SN_LAB   = "Decision Lab"
SN_SENSI = "Sensibilité"
SN_SCEN  = "Scénarios"
SN_ROAD  = "Roadmap"
SN_HIST  = "Historique"
SN_EDM   = "EDM"

# Lignes clés dans la feuille EDM (référencées par formules dans les autres feuilles)
EDM_R_HEALTH    = 3
EDM_R_CONFID    = 4
EDM_R_EBITDA    = 5
EDM_R_CASH      = 6
EDM_R_COI_YEAR  = 7
EDM_R_COI_MONTH = 8
EDM_R_COI_WEEK  = 9
EDM_R_COI_DAY   = 10
EDM_R_COI_HOUR  = 11
EDM_R_IMPACT    = 12
EDM_R_DEC_START = 29    # Première décision : ligne 29, col B = annual_impact
MAX_DEC = 10

# Lignes clés dans Decision Lab (référencées par Dashboard et Scénarios)
LAB_R_DEC_START = 6
LAB_R_DEC_END   = LAB_R_DEC_START + MAX_DEC - 1   # = 15
LAB_R_TOTAL     = LAB_R_DEC_END + 1               # = 16
LAB_R_EBITDA    = LAB_R_TOTAL + 4                 # = 20
LAB_R_IMPACT    = LAB_R_TOTAL + 5                 # = 21
LAB_R_PROJ      = LAB_R_TOTAL + 6                 # = 22
LAB_R_VAR_PCT   = LAB_R_TOTAL + 7                 # = 23
LAB_COL_IMPACT  = 5                               # Colonne E = impact projeté

# Lignes clés dans Hypothèses (référencées par Decision Lab, Sensibilité, Scénarios)
HYPO_R_EBITDA  = 5
HYPO_R_CASH    = 6
HYPO_R_COI     = 7
HYPO_R_CA      = 11
HYPO_R_CROISS  = 12
HYPO_R_PRIX    = 13
HYPO_R_VOLUME  = 14
HYPO_R_MARGE_B = 15
HYPO_R_MASA    = 18
HYPO_R_CHARGES = 19
HYPO_R_SOUSTRX = 20
HYPO_R_INFLAT  = 21
HYPO_R_MARGE_N = 22


# ─── Utilitaires de formatage (affichage, pas de calcul métier) ───────────────

def _parse_eur(s: Optional[str]) -> float:
    """'1 800 000 €' → 1_800_000.0  /  '1.2M €' → 1_200_000.0"""
    if not s:
        return 0.0
    c = re.sub(r"[€\s]", "", str(s)).replace(",", ".").strip()
    try:
        if c.upper().endswith("M"):
            return float(c[:-1]) * 1_000_000
        if c.upper().endswith("K"):
            return float(c[:-1]) * 1_000
        return float(c)
    except (ValueError, TypeError):
        return 0.0


# ─── Primitives de style ──────────────────────────────────────────────────────

def _fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)

def _font(size: int = 10, bold: bool = False, color: str = P_DARK,
          italic: bool = False) -> Font:
    return Font(name="Calibri", size=size, bold=bold, color=color, italic=italic)

def _align(h: str = "left", v: str = "center", wrap: bool = False) -> Alignment:
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def _border_thin() -> Border:
    s = Side(style="thin", color=P_LINE)
    return Border(left=s, right=s, top=s, bottom=s)

def _border_accent() -> Border:
    return Border(left=Side(style="medium", color=P_BLUE),
                  right=Side(style="thin", color=P_LINE),
                  top=Side(style="thin", color=P_LINE),
                  bottom=Side(style="thin", color=P_LINE))

def _header_bar(ws, row: int, text: str, col_start: int = 1,
                col_end: int = 18, size: int = 13, bg: str = P_NAVY) -> None:
    ws.merge_cells(start_row=row, start_column=col_start,
                   end_row=row, end_column=col_end)
    c = ws.cell(row=row, column=col_start, value=f"  {text}")
    c.font = _font(size=size, bold=True, color=P_WHITE)
    c.fill = _fill(bg)
    c.alignment = _align("left")
    ws.row_dimensions[row].height = 34

def _section_bar(ws, row: int, text: str, col_start: int = 1,
                 col_end: int = 18, bg: str = P_BLUE) -> None:
    ws.merge_cells(start_row=row, start_column=col_start,
                   end_row=row, end_column=col_end)
    c = ws.cell(row=row, column=col_start, value=f"  {text}")
    c.font = _font(size=9, bold=True, color=P_WHITE)
    c.fill = _fill(bg)
    c.alignment = _align("left")
    ws.row_dimensions[row].height = 22

def _col_headers(ws, row: int, headers: list, start_col: int = 1,
                 bg: str = P_NAVY) -> None:
    for i, h in enumerate(headers):
        c = ws.cell(row=row, column=start_col + i, value=h)
        c.font = _font(size=9, bold=True, color=P_WHITE)
        c.fill = _fill(bg)
        c.alignment = _align("center")
        c.border = _border_thin()
    ws.row_dimensions[row].height = 22

def _instruction(ws, row: int, text: str, col: int = 1, col_end: int = 18) -> None:
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col_end)
    c = ws.cell(row=row, column=col, value=f"  ℹ  {text}")
    c.font = _font(size=9, italic=True, color=P_SLATE)
    c.fill = _fill("FFFBEB")
    c.alignment = _align("left")
    ws.row_dimensions[row].height = 20

def _kpi_block(ws, row: int, col: int, label: str, value, *,
               width: int = 3, height: int = 3, fill_c: str = P_LIGHT,
               val_size: int = 16, val_color: str = P_DARK,
               num_format: str = None) -> None:
    end_col = col + width - 1
    for r in range(row, row + height):
        for ci in range(col, end_col + 1):
            ws.cell(row=r, column=ci).fill = _fill(fill_c)
    for ci in range(col, end_col + 1):
        ws.cell(row=row, column=ci).border = Border(
            top=Side(style="medium", color=P_BLUE))
    ws.merge_cells(start_row=row, start_column=col,
                   end_row=row, end_column=end_col)
    lc = ws.cell(row=row, column=col, value=label.upper())
    lc.font = _font(size=8, color=P_SLATE, bold=True)
    lc.alignment = _align("left")
    ws.merge_cells(start_row=row + 1, start_column=col,
                   end_row=row + height - 1, end_column=end_col)
    vc = ws.cell(row=row + 1, column=col, value=value)
    vc.font = _font(size=val_size, bold=True, color=val_color)
    vc.alignment = _align("left", "center")
    if num_format:
        vc.number_format = num_format

def _widths(ws, mapping: dict) -> None:
    for k, w in mapping.items():
        col = get_column_letter(k) if isinstance(k, int) else k
        ws.column_dimensions[col].width = w

def _freeze(ws, cell: str = "A4") -> None:
    ws.freeze_panes = cell


# ─── FEUILLE EDM (masquée — source unique) ────────────────────────────────────

def _build_edm(wb: Workbook, edm, raw: dict) -> None:
    ws = wb.create_sheet(SN_EDM)
    ws.tab_color = P_SLATE

    _header_bar(ws, 1, "EXECUTIVE DECISION MODEL — Source technique (ne jamais modifier)", col_end=8)
    ws.cell(row=2, column=1,
            value="Ce feuillet alimente l'ensemble du classeur. Toutes ses valeurs proviennent de l'EDM Pepperyn."
            ).font = _font(italic=True, color=P_SLATE)

    coi = edm.cost_of_inaction
    global_rows = [
        (EDM_R_HEALTH,    "Score Santé",                edm.health_score or 0),
        (EDM_R_CONFID,    "Niveau de confiance",        edm.executive_confidence or 0),
        (EDM_R_EBITDA,    "EBITDA (numérique €)",       _parse_eur(edm.ebitda)),
        (EDM_R_CASH,      "Cash disponible (€)",        _parse_eur(edm.available_cash)),
        (EDM_R_COI_YEAR,  "Coût de l'inaction / an",    (coi.per_year or 0) if coi else 0),
        (EDM_R_COI_MONTH, "Coût de l'inaction / mois",  (coi.per_month or 0) if coi else 0),
        (EDM_R_COI_WEEK,  "Coût de l'inaction / sem.",  (coi.per_week or 0) if coi else 0),
        (EDM_R_COI_DAY,   "Coût de l'inaction / jour",  (coi.per_day or 0) if coi else 0),
        (EDM_R_COI_HOUR,  "Coût de l'inaction / heure", (coi.per_hour or 0) if coi else 0),
        (EDM_R_IMPACT,    "Impact total identifié",
         -sum(abs(d.annual_impact or 0) for d in edm.value_destroyers)),
    ]
    for r, label, val in global_rows:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_GRAY)
        ws.cell(row=r, column=2, value=val)

    # Value destroyers
    dh = 15
    _col_headers(ws, dh, ["Levier de destruction", "Impact annuel (€)", "Impact mensuel (€)", "Tendance", "Commentaire"])
    for i, d in enumerate(edm.value_destroyers[:MAX_DEC]):
        r = dh + 1 + i
        ws.cell(row=r, column=1, value=d.name)
        ws.cell(row=r, column=2, value=d.annual_impact or 0)
        ws.cell(row=r, column=3, value=d.monthly_impact or 0)
        ws.cell(row=r, column=4, value=d.trend or "stable")
        ws.cell(row=r, column=5, value=(d.comment or "")[:100])

    # Executive decisions — col B = annual_impact (référencé par Decision Lab)
    dech = EDM_R_DEC_START - 1  # = 28 = header
    _col_headers(ws, dech, ["Décision", "Impact annuel (€)", "Difficulté",
                             "Horizon", "Responsable", "Priorité", "ROI score"])
    for i, dec in enumerate(edm.executive_decisions[:MAX_DEC]):
        r = EDM_R_DEC_START + i
        ws.cell(row=r, column=1, value=dec.decision)
        ws.cell(row=r, column=2, value=dec.annual_impact or 0)
        ws.cell(row=r, column=3, value=dec.difficulty or "—")
        ws.cell(row=r, column=4, value=dec.timeline or "—")
        ws.cell(row=r, column=5, value=dec.owner or "—")
        ws.cell(row=r, column=6, value=dec.priority)
        ws.cell(row=r, column=7, value=dec.roi_score)

    # CEO dashboard cards (brutes — lecture uniquement)
    raw_cards = (raw or {}).get("ceo_dashboard") or []
    r = 42
    ws.cell(row=r - 1, column=1, value="CEO Dashboard brut").font = _font(bold=True, color=P_NAVY)
    for i, card in enumerate(raw_cards[:8]):
        if isinstance(card, dict):
            ws.cell(row=r + i, column=1, value=card.get("label", ""))
            ws.cell(row=r + i, column=2, value=card.get("value", "—"))

    # Séries temporelles (12 mois)
    r = 53
    ws.cell(row=r - 1, column=1, value="Séries temporelles").font = _font(bold=True, color=P_NAVY)
    _col_headers(ws, r, ["Série"] + [f"M{j+1}" for j in range(12)])
    ws.cell(row=r + 1, column=1, value="Action (avec décisions)")
    ws.cell(row=r + 2, column=1, value="Inaction (sans décision)")
    ws.cell(row=r + 3, column=1, value="Trajectoire cible")
    for j, v in enumerate(edm.action_series[:12]):
        ws.cell(row=r + 1, column=2 + j, value=v)
    for j, v in enumerate(edm.do_nothing_series[:12]):
        ws.cell(row=r + 2, column=2 + j, value=v)
    for j, v in enumerate(edm.monthly_projection[:12]):
        ws.cell(row=r + 3, column=2 + j, value=v)

    _widths(ws, {"A": 35, "B": 18, "C": 16, "D": 14, "E": 28, "F": 14, "G": 10})


# ─── FEUILLE 1 : EXECUTIVE DASHBOARD ─────────────────────────────────────────

def _build_dashboard(wb: Workbook, edm, raw: dict) -> None:
    ws = wb.create_sheet(SN_DASH)
    ws.tab_color = P_NAVY

    date_str = datetime.now().strftime("%d %B %Y")
    _header_bar(ws, 1, f"EXECUTIVE DASHBOARD  ·  {date_str}  ·  CONFIDENTIEL", col_end=20)
    _instruction(ws, 2,
                 "Tableau de bord en temps réel — toutes les valeurs se mettent à jour automatiquement "
                 "lorsque vous modifiez vos hypothèses ou simulez des décisions dans Decision Lab.",
                 col_end=20)
    ws.row_dimensions[3].height = 8

    # Ligne 1 de KPI — 4 blocs (colonnes 2, 6, 10, 14 ; largeur 3 chacun)
    kpi_cols = [2, 6, 10, 14]
    kpi_w = 3

    kpi_r1 = [
        ("EBITDA actuel",       f"=EDM!B{EDM_R_EBITDA}",  P_DARK,  "#,##0 €;(#,##0 €);-"),
        ("Cash disponible",     f"=EDM!B{EDM_R_CASH}",    P_DARK,  "#,##0 €;(#,##0 €);-"),
        ("Score santé",         f"=EDM!B{EDM_R_HEALTH}",  P_DARK,  "0\"/10\""),
        ("Niveau de confiance", f"=EDM!B{EDM_R_CONFID}",  P_DARK,  "0\"/10\""),
    ]
    r1_start = 4
    for (label, val, vc, nf), col in zip(kpi_r1, kpi_cols):
        _kpi_block(ws, r1_start, col, label, val, width=kpi_w, height=4,
                   val_size=18, val_color=vc, num_format=nf)

    kpi_r2 = [
        ("Coût inaction / an",  f"=EDM!B{EDM_R_COI_YEAR}",            P_RED,   "#,##0 €;(#,##0 €);-"),
        ("Impact identifié",    f"=EDM!B{EDM_R_IMPACT}",               P_AMBER, "#,##0 €;(#,##0 €);-"),
        ("EBITDA projeté",      f"='{SN_LAB}'!B{LAB_R_PROJ}",          P_GREEN, "#,##0 €;(#,##0 €);-"),
        ("Variation projetée",  f"='{SN_LAB}'!B{LAB_R_VAR_PCT}",       P_BLUE,  "0.0%"),
    ]
    r2_start = r1_start + 5
    for (label, val, vc, nf), col in zip(kpi_r2, kpi_cols):
        _kpi_block(ws, r2_start, col, label, val, width=kpi_w, height=4,
                   val_size=18, val_color=vc, num_format=nf)

    # Coût de l'inaction détaillé
    r_coi_hdr = r2_start + 5
    ws.row_dimensions[r_coi_hdr].height = 8
    _section_bar(ws, r_coi_hdr + 1, "COÛT DE L'INACTION — Chaque heure compte", col_end=20)
    coi_items = [
        ("Par heure",   f"=EDM!B{EDM_R_COI_HOUR}", 2),
        ("Par jour",    f"=EDM!B{EDM_R_COI_DAY}",  6),
        ("Par semaine", f"=EDM!B{EDM_R_COI_WEEK}", 10),
        ("Par mois",    f"=EDM!B{EDM_R_COI_MONTH}",14),
    ]
    cr = r_coi_hdr + 2
    for label, val, col in coi_items:
        _kpi_block(ws, cr, col, label, val, width=kpi_w, height=3,
                   fill_c="FFF8F8", val_size=14, val_color=P_RED,
                   num_format="#,##0 €;(#,##0 €);-")

    # Navigation rapide
    nav_r = cr + 4
    ws.row_dimensions[nav_r].height = 8
    _section_bar(ws, nav_r + 1, "NAVIGATION RAPIDE", col_end=20)
    nav_items = [
        (2,  "→  Hypothèses",    "Modifier les paramètres"),
        (6,  "→  Decision Lab",  "Simuler des décisions"),
        (10, "→  Sensibilité",   "Identifier les leviers"),
        (14, "→  Scénarios",     "Comparer les visions"),
    ]
    for col, name, desc in nav_items:
        c = ws.cell(row=nav_r + 2, column=col, value=name)
        c.font = _font(size=9, color=P_BLUE, bold=True)
        c.fill = _fill(P_LIGHT)
        ws.merge_cells(start_row=nav_r + 2, start_column=col,
                       end_row=nav_r + 2, end_column=col + kpi_w - 1)
        c2 = ws.cell(row=nav_r + 3, column=col, value=desc)
        c2.font = _font(size=8, color=P_GRAY)
        c2.fill = _fill(P_LIGHT)
        ws.merge_cells(start_row=nav_r + 3, start_column=col,
                       end_row=nav_r + 3, end_column=col + kpi_w - 1)

    _widths(ws, {i: 6 for i in range(1, 21)})
    _widths(ws, {"A": 1, "E": 1, "I": 1, "M": 1, "Q": 1})
    _freeze(ws, "A4")


# ─── FEUILLE 2 : HYPOTHÈSES ───────────────────────────────────────────────────

def _build_hypotheses(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_HYPO)
    ws.tab_color = P_BLUE

    _header_bar(ws, 1, "HYPOTHÈSES — Paramètres de votre modèle financier", col_end=12)
    _instruction(ws, 2,
                 "Cellules BLEUES = vous pouvez les modifier. "
                 "Toutes les autres feuilles se recalculent immédiatement.",
                 col_end=12)
    ws.row_dimensions[3].height = 8
    _col_headers(ws, 4, ["Paramètre", "Valeur", "Unité", "Note / Source"], bg=P_NAVY)

    # Section A — Données de référence EDM (liens verts, ne pas modifier)
    _section_bar(ws, HYPO_R_EBITDA - 1, "A — DONNÉES DE RÉFÉRENCE (issues de l'EDM — liens automatiques)", col_end=4)
    ref_rows = [
        (HYPO_R_EBITDA, "EBITDA de référence",     f"=EDM!B{EDM_R_EBITDA}",   "€",    "Lien EDM Pepperyn"),
        (HYPO_R_CASH,   "Cash disponible",          f"=EDM!B{EDM_R_CASH}",     "€",    "Lien EDM Pepperyn"),
        (HYPO_R_COI,    "Coût de l'inaction / an", f"=EDM!B{EDM_R_COI_YEAR}", "€/an", "Lien EDM Pepperyn"),
    ]
    for r, label, val, unit, note in ref_rows:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_GRAY)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(color=FONT_LINK, bold=True)
        c.number_format = "#,##0 €;(#,##0 €);-"
        c.border = _border_thin()
        ws.cell(row=r, column=3, value=unit).font = _font(color=P_SLATE)
        ws.cell(row=r, column=4, value=note).font = _font(italic=True, color=P_SLATE)
    ws.row_dimensions[HYPO_R_COI + 1].height = 8

    # Section B — Hypothèses de revenus (cellules bleues)
    ebitda_num = _parse_eur(edm.ebitda)
    _section_bar(ws, HYPO_R_CA - 1, "B — HYPOTHÈSES DE REVENUS  ↓ cellules bleues modifiables", col_end=4)
    rev_rows = [
        (HYPO_R_CA,     "Chiffre d'affaires estimé", max(ebitda_num * 2.5, 0), "#,##0 €;(#,##0 €);-", "Votre estimation CA annuel"),
        (HYPO_R_CROISS, "Taux de croissance annuel",  0.05,                     "0.0%",                "Objectif de croissance"),
        (HYPO_R_PRIX,   "Prix moyen de vente (€)",    0.0,                      "#,##0 €;(#,##0 €);-", "Prix unitaire moyen"),
        (HYPO_R_VOLUME, "Volume mensuel (unités)",     0.0,                      "#,##0",               "Nombre d'unités / mois"),
        (HYPO_R_MARGE_B,"Marge brute (%)",             0.40,                     "0.0%",                "Marge avant charges de structure"),
    ]
    for r, label, val, nf, note in rev_rows:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_DARK)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(color=FONT_INPUT, bold=True)
        c.fill = _fill("EFF6FF")
        c.number_format = nf
        c.border = _border_thin()
        ws.cell(row=r, column=4, value=note).font = _font(italic=True, color=P_SLATE)
    ws.row_dimensions[HYPO_R_MARGE_B + 1].height = 8

    # Section C — Hypothèses de coûts
    masa_init  = abs(next((d.annual_impact for d in edm.value_destroyers
                           if "salarial" in (d.name or "").lower()), None) or 0)
    charg_init = abs(next((d.annual_impact for d in edm.value_destroyers
                           if "charge" in (d.name or "").lower()), None) or 0)
    sous_init  = abs(next((d.annual_impact for d in edm.value_destroyers
                           if "sous" in (d.name or "").lower()), None) or 0)
    _section_bar(ws, HYPO_R_MASA - 1, "C — HYPOTHÈSES DE COÛTS  ↓ cellules bleues modifiables", col_end=4)
    cost_rows = [
        (HYPO_R_MASA,    "Masse salariale annuelle", masa_init,  "#,##0 €;(#,##0 €);-", "Initialisation EDM"),
        (HYPO_R_CHARGES, "Charges fixes annuelles",  charg_init, "#,##0 €;(#,##0 €);-", "Initialisation EDM"),
        (HYPO_R_SOUSTRX, "Coût de sous-traitance",   sous_init,  "#,##0 €;(#,##0 €);-", "Initialisation EDM"),
        (HYPO_R_INFLAT,  "Taux d'inflation (%)",     0.025,      "0.0%",                "Hypothèse macro"),
        (HYPO_R_MARGE_N, "Marge nette cible (%)",    0.10,       "0.0%",                "Objectif de profitabilité"),
    ]
    for r, label, val, nf, note in cost_rows:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_DARK)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(color=FONT_INPUT, bold=True)
        c.fill = _fill("EFF6FF")
        c.number_format = nf
        c.border = _border_thin()
        ws.cell(row=r, column=4, value=note).font = _font(italic=True, color=P_SLATE)
    ws.row_dimensions[HYPO_R_MARGE_N + 1].height = 8

    # Section D — Paramètres de simulation
    sim_base = HYPO_R_MARGE_N + 2
    _section_bar(ws, sim_base, "D — PARAMÈTRES DE SIMULATION", col_end=4)
    sim_rows = [
        (sim_base + 1, "Horizon de projection (mois)",         12,    "#,##0",  "Période couverte par la simulation"),
        (sim_base + 2, "Probabilité de réussite des décisions", 0.80, "0.0%",   "Taux de succès moyen estimé"),
        (sim_base + 3, "Taux d'actualisation / WACC",          0.08,  "0.0%",   "Coût d'opportunité du capital"),
    ]
    for r, label, val, nf, note in sim_rows:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_DARK)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(color=FONT_INPUT, bold=True)
        c.fill = _fill("EFF6FF")
        c.number_format = nf
        c.border = _border_thin()
        ws.cell(row=r, column=4, value=note).font = _font(italic=True, color=P_SLATE)

    _widths(ws, {"A": 35, "B": 20, "C": 12, "D": 32})
    _freeze(ws, "A5")


# ─── FEUILLE 3 : DECISION LAB ────────────────────────────────────────────────

def _build_decision_lab(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_LAB)
    ws.tab_color = P_GREEN

    _header_bar(ws, 1, "DECISION LAB — Simulateur stratégique", col_end=10)
    _instruction(ws, 2,
                 "Modifiez la colonne EXÉCUTION % (cellules bleues) pour simuler vos scénarios. "
                 "Tous les indicateurs se recalculent instantanément. "
                 "0% = décision non prise. 100% = décision totalement exécutée.",
                 col_end=10)
    ws.row_dimensions[3].height = 8
    _section_bar(ws, 4, "SIMULATION — Ajustez le % d'exécution pour chaque décision", col_end=10)

    headers = ["#", "Décision", "Impact de base (€)", "Exécution %",
               "Impact projeté (€)", "Responsable", "Horizon", "Priorité"]
    _col_headers(ws, 5, headers, bg=P_NAVY)

    decisions = edm.executive_decisions[:MAX_DEC]
    lc = get_column_letter(LAB_COL_IMPACT)  # "E"

    for i in range(MAX_DEC):
        r = LAB_R_DEC_START + i
        alt = P_LIGHT if i % 2 == 0 else P_WHITE
        dec = decisions[i] if i < len(decisions) else None

        # Col A: numéro
        c = ws.cell(row=r, column=1, value=i + 1)
        c.font = _font(color=P_SLATE, bold=True)
        c.fill = _fill(alt)
        c.border = _border_thin()
        c.alignment = _align("center")

        # Col B: décision
        dec_text = dec.decision if dec else "[Décision disponible]"
        c = ws.cell(row=r, column=2, value=dec_text)
        c.font = _font(color=P_DARK if dec else P_SLATE,
                       italic=not dec, bold=bool(dec))
        c.fill = _fill(alt)
        c.border = _border_thin()
        c.alignment = _align("left", wrap=True)
        ws.row_dimensions[r].height = 28

        # Col C: impact de base (lien EDM — vert)
        edm_ref = f"EDM!B{EDM_R_DEC_START + i}"
        c = ws.cell(row=r, column=3, value=f"={edm_ref}")
        c.font = _font(color=FONT_LINK, bold=True)
        c.fill = _fill(alt)
        c.border = _border_thin()
        c.number_format = "#,##0 €;(#,##0 €);-"
        c.alignment = _align("right")

        # Col D: exécution % (SAISIE UTILISATEUR — bleu)
        exec_val = 1.0 if dec else 0.0
        c = ws.cell(row=r, column=4, value=exec_val)
        c.font = _font(color=FONT_INPUT, bold=True)
        c.fill = _fill("DBEAFE")
        c.border = _border_accent()
        c.number_format = "0%"
        c.alignment = _align("center")

        # Col E: impact projeté (formule noire = base × exécution)
        c = ws.cell(row=r, column=LAB_COL_IMPACT, value=f"=C{r}*D{r}")
        c.font = _font(color=FONT_FORMULA, bold=True)
        c.fill = _fill(alt)
        c.border = _border_thin()
        c.number_format = "#,##0 €;(#,##0 €);-"
        c.alignment = _align("right")

        # Col F: responsable (pré-rempli modifiable)
        c = ws.cell(row=r, column=6, value=dec.owner if dec else "—")
        c.font = _font(color=FONT_INPUT)
        c.fill = _fill(alt)
        c.border = _border_thin()

        # Col G: horizon
        c = ws.cell(row=r, column=7, value=dec.timeline if dec else "—")
        c.font = _font(color=FONT_INPUT)
        c.fill = _fill(alt)
        c.border = _border_thin()

        # Col H: priorité
        if dec:
            p_lower = (dec.priority or "").lower()
            p_color = P_RED if "high" in p_lower else (P_AMBER if "medium" in p_lower else P_GRAY)
            c = ws.cell(row=r, column=8, value=dec.priority)
            c.font = _font(color=p_color, bold=True)
        else:
            ws.cell(row=r, column=8, value="—").font = _font(color=P_SLATE)
        ws.cell(row=r, column=8).fill = _fill(alt)
        ws.cell(row=r, column=8).border = _border_thin()

    # Ligne totaux
    r_tot = LAB_R_TOTAL
    ws.merge_cells(start_row=r_tot, start_column=1, end_row=r_tot, end_column=2)
    c = ws.cell(row=r_tot, column=1, value="TOTAL IMPACT SIMULÉ")
    c.font = _font(size=10, bold=True, color=P_WHITE)
    c.fill = _fill(P_NAVY)
    c.alignment = _align("right")

    c3 = ws.cell(row=r_tot, column=3, value=f"=SUM(C{LAB_R_DEC_START}:C{LAB_R_DEC_END})")
    c3.font = _font(bold=True, color=P_WHITE)
    c3.fill = _fill(P_NAVY)
    c3.number_format = "#,##0 €;(#,##0 €);-"
    c3.alignment = _align("right")

    c5 = ws.cell(row=r_tot, column=LAB_COL_IMPACT,
                 value=f"=SUM({lc}{LAB_R_DEC_START}:{lc}{LAB_R_DEC_END})")
    c5.font = _font(bold=True, color=P_WHITE)
    c5.fill = _fill(P_NAVY)
    c5.number_format = "#,##0 €;(#,##0 €);-"
    c5.alignment = _align("right")

    # Tableau de bord projeté
    ws.row_dimensions[r_tot + 1].height = 10
    _section_bar(ws, r_tot + 2, "TABLEAU DE BORD PROJETÉ — Recalcul automatique", col_end=10)

    proj_def = [
        (LAB_R_EBITDA,   "EBITDA de base (€)",
         f"='{SN_HYPO}'!B{HYPO_R_EBITDA}", "#,##0 €;(#,##0 €);-", FONT_LINK),
        (LAB_R_IMPACT,   "Impact simulé total (€)",
         f"={lc}{r_tot}", "#,##0 €;(#,##0 €);-", FONT_FORMULA),
        (LAB_R_PROJ,     "EBITDA projeté (€)",
         f"=B{LAB_R_EBITDA}+B{LAB_R_IMPACT}", "#,##0 €;(#,##0 €);-", FONT_FORMULA),
        (LAB_R_VAR_PCT,  "Variation vs actuel (%)",
         f"=IFERROR(B{LAB_R_IMPACT}/ABS(B{LAB_R_EBITDA}),0)", "0.0%", FONT_FORMULA),
        (LAB_R_VAR_PCT+1,"Coût de l'inaction (rappel)",
         f"=EDM!B{EDM_R_COI_YEAR}", "#,##0 €;(#,##0 €);-", FONT_LINK),
        (LAB_R_VAR_PCT+2,"Gain net vs inaction",
         f"=B{LAB_R_PROJ}+ABS(EDM!B{EDM_R_COI_YEAR})",
         "#,##0 €;(#,##0 €);-", FONT_FORMULA),
    ]
    for r, label, val, nf, fc in proj_def:
        ws.cell(row=r, column=1, value=label).font = _font(color=P_GRAY, bold=True)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(bold=True, color=fc, size=12)
        c.number_format = nf
        c.border = _border_thin()
        c.alignment = _align("right")

    _widths(ws, {"A": 4, "B": 42, "C": 20, "D": 14, "E": 20,
                 "F": 18, "G": 14, "H": 14})
    _freeze(ws, "B6")


# ─── FEUILLE 4 : SENSIBILITÉ ──────────────────────────────────────────────────

def _build_sensitivity(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_SENSI)
    ws.tab_color = P_AMBER

    _header_bar(ws, 1, "ANALYSE DE SENSIBILITÉ — Qu'est-ce qui influence le plus notre résultat ?", col_end=12)
    _instruction(ws, 2,
                 "Ce tableau montre l'impact € d'une variation de ±X% de chaque variable sur votre résultat. "
                 "Les valeurs se recalculent automatiquement lorsque vous modifiez la feuille Hypothèses.",
                 col_end=12)
    ws.row_dimensions[3].height = 8

    pcts = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]
    pct_labels = [f"{int(p*100):+d}%" for p in pcts]
    _col_headers(ws, 4, ["Variable"] + pct_labels + ["Levier clé ?"], bg=P_NAVY)

    # Variables et leur référence dans Hypothèses
    sens_vars = [
        ("Chiffre d'affaires",        f"'{SN_HYPO}'!B{HYPO_R_CA}",      True),
        ("Masse salariale",           f"'{SN_HYPO}'!B{HYPO_R_MASA}",    False),
        ("Charges fixes",             f"'{SN_HYPO}'!B{HYPO_R_CHARGES}", False),
        ("Sous-traitance",            f"'{SN_HYPO}'!B{HYPO_R_SOUSTRX}", False),
        ("Prix moyen de vente",       f"'{SN_HYPO}'!B{HYPO_R_PRIX}",    True),
        ("Volume (unités/mois × 12)", f"'{SN_HYPO}'!B{HYPO_R_VOLUME}",  True),
        ("Marge brute (%×CA)",        f"'{SN_HYPO}'!B{HYPO_R_CA}",      True),
        ("Taux d'inflation",          f"'{SN_HYPO}'!B{HYPO_R_MASA}",    False),
    ]

    for i, (label, ref, is_lever) in enumerate(sens_vars):
        r = 5 + i
        alt = P_LIGHT if i % 2 == 0 else P_WHITE

        c = ws.cell(row=r, column=1, value=label)
        c.font = _font(color=P_DARK, bold=True)
        c.fill = _fill(alt)
        c.border = _border_thin()

        for j, pct in enumerate(pcts):
            formula = f"=IFERROR({ref}*{pct},0)"
            c = ws.cell(row=r, column=2 + j, value=formula)
            c.font = _font(color=P_GREEN if pct > 0 else P_RED, bold=True)
            c.fill = _fill(alt)
            c.border = _border_thin()
            c.number_format = "#,##0 €;(#,##0 €);-"
            c.alignment = _align("right")

        lev = ws.cell(row=r, column=2 + len(pcts), value="★ Levier clé" if is_lever else "—")
        lev.font = _font(color=P_AMBER if is_lever else P_SLATE, bold=is_lever)
        lev.fill = _fill(alt)
        lev.border = _border_thin()

    r_note = 5 + len(sens_vars) + 2
    _section_bar(ws, r_note, "COMMENT LIRE CE TABLEAU", col_end=12, bg=P_NAVY)
    guide = [
        ("Valeurs vertes (+)", "= la variable aide le résultat si elle augmente (ex: CA, prix, volume)"),
        ("Valeurs rouges (−)", "= la variable pèse sur le résultat si elle augmente (ex: coûts)"),
        ("★ Levier clé",      "= variable avec le plus fort potentiel d'impact sur la performance"),
        ("Pour agir",         "→ allez dans la feuille Hypothèses (onglet bleu) et modifiez les cellules bleues"),
    ]
    for k, (label, val) in enumerate(guide):
        r = r_note + 1 + k
        ws.cell(row=r, column=1, value=label).font = _font(bold=True, color=P_DARK)
        c = ws.cell(row=r, column=2, value=val)
        c.font = _font(color=P_GRAY)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)

    _widths(ws, {"A": 32, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14, "H": 14})
    _freeze(ws, "B5")


# ─── FEUILLE 5 : SCÉNARIOS ───────────────────────────────────────────────────

def _build_scenarios(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_SCEN)
    ws.tab_color = P_BLUE

    _header_bar(ws, 1, "COMPARAISON DE SCÉNARIOS — Prudent · Central · Ambitieux · Personnalisé", col_end=14)
    _instruction(ws, 2,
                 "Le scénario Personnalisé reprend vos simulations du Decision Lab en temps réel. "
                 "Les trois autres appliquent des multiplicateurs au même impact de base.",
                 col_end=14)
    ws.row_dimensions[3].height = 8

    _col_headers(ws, 4, ["Indicateur", "Prudent (75%)", "Central (100%)",
                          "Ambitieux (130%)", "Personnalisé (Decision Lab)"], bg=P_NAVY)

    lc = get_column_letter(LAB_COL_IMPACT)
    lab_total_ref   = f"='{SN_LAB}'!{lc}{LAB_R_TOTAL}"
    lab_ebitda_ref  = f"='{SN_LAB}'!B{LAB_R_EBITDA}"

    metrics = [
        ("EBITDA de base (€)",
         f"={lab_ebitda_ref}", f"={lab_ebitda_ref}", f"={lab_ebitda_ref}", f"={lab_ebitda_ref}",
         "#,##0 €;(#,##0 €);-"),
        ("Impact décisions (€)",
         f"={lab_total_ref}*0.75", f"={lab_total_ref}", f"={lab_total_ref}*1.30", f"={lab_total_ref}",
         "#,##0 €;(#,##0 €);-"),
        ("EBITDA projeté (€)",
         "=B6+B7", "=C6+C7", "=D6+D7", "=E6+E7",
         "#,##0 €;(#,##0 €);-"),
        ("Variation vs actuel (%)",
         "=IFERROR(B7/ABS(B6),0)", "=IFERROR(C7/ABS(C6),0)",
         "=IFERROR(D7/ABS(D6),0)", "=IFERROR(E7/ABS(E6),0)",
         "0.0%"),
        ("Coût inaction évité (€)",
         f"=ABS(EDM!B{EDM_R_COI_YEAR})*0.75",
         f"=ABS(EDM!B{EDM_R_COI_YEAR})",
         f"=ABS(EDM!B{EDM_R_COI_YEAR})*1.30",
         f"=ABS(EDM!B{EDM_R_COI_YEAR})",
         "#,##0 €;(#,##0 €);-"),
        ("Score santé (rappel)",
         f"=EDM!B{EDM_R_HEALTH}", f"=EDM!B{EDM_R_HEALTH}",
         f"=EDM!B{EDM_R_HEALTH}", f"=EDM!B{EDM_R_HEALTH}",
         "0\"/10\""),
    ]

    scen_colors = [P_AMBER, P_NAVY, P_GREEN, P_BLUE]
    row_base = 5
    for i, (label, v1, v2, v3, v4, nf) in enumerate(metrics):
        r = row_base + i
        alt = P_LIGHT if i % 2 == 0 else P_WHITE

        ws.cell(row=r, column=1, value=label).font = _font(bold=True, color=P_DARK)
        ws.cell(row=r, column=1).fill = _fill(alt)
        ws.cell(row=r, column=1).border = _border_thin()

        is_hero = (r == row_base + 2)   # ligne EBITDA projeté = mise en valeur
        for j, val in enumerate([v1, v2, v3, v4]):
            c = ws.cell(row=r, column=2 + j, value=val)
            c.font = _font(bold=True, color=P_WHITE if is_hero else P_DARK,
                           size=14 if is_hero else 10)
            c.fill = _fill(scen_colors[j] if is_hero else alt)
            c.number_format = nf
            c.border = _border_thin()
            c.alignment = _align("right")

    # Scénarios qualitatifs LLM (si disponibles)
    if edm.scenarios:
        r_sc = row_base + len(metrics) + 2
        _section_bar(ws, r_sc, "SCÉNARIOS IDENTIFIÉS PAR LE COPILOTE", col_end=14)
        _col_headers(ws, r_sc + 1, ["Scénario", "Label", "Description"], bg=P_NAVY)
        for k, sc in enumerate(edm.scenarios[:5]):
            r = r_sc + 2 + k
            ws.cell(row=r, column=1, value=getattr(sc, "nom", f"S{k+1}")).font = _font(bold=True)
            ws.cell(row=r, column=2, value=getattr(sc, "label", "—")).font = _font(color=P_BLUE)
            desc = getattr(sc, "description", "—")
            c = ws.cell(row=r, column=3, value=(desc or "")[:140])
            c.font = _font(color=P_GRAY)
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=14)

    _widths(ws, {"A": 30, "B": 22, "C": 22, "D": 22, "E": 28})
    _freeze(ws, "B5")


# ─── FEUILLE 6 : ROADMAP ─────────────────────────────────────────────────────

def _build_roadmap(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_ROAD)
    ws.tab_color = P_NAVY

    _header_bar(ws, 1, "ROADMAP D'EXÉCUTION — Pilotage des décisions", col_end=16)
    _instruction(ws, 2,
                 "Modifiez le Statut (colonne D, cellule bleue) pour suivre l'avancement. "
                 "Valeurs : To launch · In progress · Completed · Blocked",
                 col_end=16)
    ws.row_dimensions[3].height = 8

    _col_headers(ws, 4, ["#", "Décision / Action", "Responsable", "Statut",
                          "Impact (€)", "Priorité", "Horizon", "Phase 90j", "ROI score"])

    statuses_color = {
        "To launch": P_SLATE, "In progress": P_BLUE,
        "Completed": P_GREEN, "Blocked": P_RED,
    }

    for i in range(MAX_DEC):
        r = 5 + i
        alt = P_LIGHT if i % 2 == 0 else P_WHITE
        dec = edm.executive_decisions[i] if i < len(edm.executive_decisions) else None

        for col in range(1, 10):
            ws.cell(row=r, column=col).fill = _fill(alt)
            ws.cell(row=r, column=col).border = _border_thin()

        ws.cell(row=r, column=1, value=i + 1).alignment = _align("center")
        ws.cell(row=r, column=1).font = _font(color=P_SLATE, bold=True)

        if dec:
            c = ws.cell(row=r, column=2, value=dec.decision)
            c.font = _font(color=P_DARK, bold=True)
            c.alignment = _align("left", wrap=True)
            ws.row_dimensions[r].height = 30

            c = ws.cell(row=r, column=3, value=dec.owner or "À définir")
            c.font = _font(color=FONT_INPUT)

            c = ws.cell(row=r, column=4, value=dec.status)
            c.font = _font(color=statuses_color.get(dec.status, P_SLATE),
                           bold=True)
            c.fill = _fill("DBEAFE")
            c.border = _border_accent()

            c = ws.cell(row=r, column=5, value=f"=EDM!B{EDM_R_DEC_START + i}")
            c.font = _font(color=FONT_LINK, bold=True)
            c.number_format = "#,##0 €;(#,##0 €);-"

            p_lower = (dec.priority or "").lower()
            p_color = P_RED if "high" in p_lower else (P_AMBER if "medium" in p_lower else P_GRAY)
            ws.cell(row=r, column=6, value=dec.priority).font = _font(color=p_color, bold=True)
            ws.cell(row=r, column=7, value=dec.timeline or "—").font = _font(color=P_GRAY)
            phase_label = "0–30j" if i < 3 else ("30–60j" if i < 6 else "60–90j")
            ws.cell(row=r, column=8, value=phase_label).font = _font(color=P_SLATE)

            c = ws.cell(row=r, column=9, value=f"=EDM!G{EDM_R_DEC_START + i}")
            c.font = _font(color=FONT_LINK)
            c.number_format = "0.0"
            c.alignment = _align("center")
        else:
            ws.cell(row=r, column=2, value="[Décision à définir]").font = _font(color=P_SLATE, italic=True)

    # Phases roadmap depuis EDM
    if edm.roadmap_90_days:
        r_ph = 5 + MAX_DEC + 2
        _section_bar(ws, r_ph, "DÉTAIL PHASES 30 / 60 / 90 JOURS (source EDM)", col_end=16)
        r_ph += 1
        for phase in edm.roadmap_90_days[:3]:
            _section_bar(ws, r_ph,
                         f"Phase {phase.horizon} jours — {phase.phase_label}",
                         col_end=16, bg=P_SLATE)
            r_ph += 1
            for action in (phase.actions or [])[:6]:
                ws.cell(row=r_ph, column=1, value="›").font = _font(color=P_BLUE, bold=True)
                c = ws.cell(row=r_ph, column=2, value=action.decision)
                c.font = _font(color=P_DARK)
                ws.merge_cells(start_row=r_ph, start_column=2, end_row=r_ph, end_column=5)
                ws.cell(row=r_ph, column=6, value=action.owner or "—").font = _font(color=P_GRAY)
                ws.cell(row=r_ph, column=7, value=action.due_date or "—").font = _font(color=P_GRAY)
                if action.impact is not None:
                    c = ws.cell(row=r_ph, column=8, value=action.impact)
                    c.font = _font(color=P_GREEN if action.impact > 0 else P_RED, bold=True)
                    c.number_format = "#,##0 €;(#,##0 €);-"
                r_ph += 1

    _widths(ws, {"A": 4, "B": 40, "C": 18, "D": 14, "E": 18, "F": 12,
                 "G": 12, "H": 10, "I": 10})
    _freeze(ws, "B5")


# ─── FEUILLE 7 : HISTORIQUE ───────────────────────────────────────────────────

def _build_historique(wb: Workbook, edm) -> None:
    ws = wb.create_sheet(SN_HIST)
    ws.tab_color = P_SLATE

    date_now = datetime.now().strftime("%b %Y")
    _header_bar(ws, 1, "HISTORIQUE — Comparaison inter-périodes", col_end=12)
    _instruction(ws, 2,
                 "Colonne actuelle = données EDM en temps réel. "
                 "Renseignez les colonnes bleues manuellement à chaque nouvelle analyse.",
                 col_end=12)
    ws.row_dimensions[3].height = 8

    _col_headers(ws, 4, ["Indicateur", date_now, "Mois N-1",
                          "Trim. N-1", "An N-1", "Évolution (vs An N-1)"], bg=P_NAVY)

    metrics = [
        ("EBITDA (€)",               f"=EDM!B{EDM_R_EBITDA}",    "#,##0 €;(#,##0 €);-"),
        ("Cash disponible (€)",      f"=EDM!B{EDM_R_CASH}",      "#,##0 €;(#,##0 €);-"),
        ("Coût de l'inaction / an",  f"=EDM!B{EDM_R_COI_YEAR}",  "#,##0 €;(#,##0 €);-"),
        ("Impact total identifié",   f"=EDM!B{EDM_R_IMPACT}",    "#,##0 €;(#,##0 €);-"),
        ("Score santé",              f"=EDM!B{EDM_R_HEALTH}",    "0\"/10\""),
        ("Niveau de confiance",      f"=EDM!B{EDM_R_CONFID}",    "0\"/10\""),
        ("EBITDA projeté (Decision Lab)", f"='{SN_LAB}'!B{LAB_R_PROJ}", "#,##0 €;(#,##0 €);-"),
        ("Variation projetée (%)",   f"='{SN_LAB}'!B{LAB_R_VAR_PCT}", "0.0%"),
    ]

    for i, (label, cur_val, nf) in enumerate(metrics):
        r = 5 + i
        alt = P_LIGHT if i % 2 == 0 else P_WHITE

        c = ws.cell(row=r, column=1, value=label)
        c.font = _font(bold=True, color=P_DARK)
        c.fill = _fill(alt)
        c.border = _border_thin()

        # Colonne actuelle (lien automatique)
        c = ws.cell(row=r, column=2, value=cur_val)
        c.font = _font(bold=True, color=FONT_LINK)
        c.fill = _fill(alt)
        c.number_format = nf
        c.border = _border_thin()
        c.alignment = _align("right")

        # Colonnes historiques (saisie manuelle — bleu)
        for j in range(1, 4):
            c = ws.cell(row=r, column=2 + j)
            c.font = _font(color=FONT_INPUT)
            c.fill = _fill("EFF6FF" if j % 2 == 0 else alt)
            c.number_format = nf
            c.border = _border_thin()
            c.alignment = _align("right")

        # Évolution vs An N-1
        c = ws.cell(row=r, column=6, value=f"=IFERROR((B{r}-E{r})/ABS(E{r}),\"—\")")
        c.font = _font(color=FONT_FORMULA, bold=True)
        c.fill = _fill(alt)
        c.number_format = "0.0%"
        c.border = _border_thin()
        c.alignment = _align("right")

    # Instructions d'utilisation
    r_guide = 5 + len(metrics) + 2
    _section_bar(ws, r_guide, "MODE D'EMPLOI", col_end=12, bg=P_SLATE)
    guide = [
        "Après chaque nouvelle analyse Pepperyn, copiez-collez les valeurs actuelles dans 'Mois N-1'.",
        "Renseignez 'Trim. N-1' et 'An N-1' manuellement depuis vos données de gestion.",
        "La colonne Évolution se calcule automatiquement dès que An N-1 est renseignée.",
        "Ce tableau vous permet de suivre la progression de votre santé financière dans le temps.",
    ]
    for k, note in enumerate(guide):
        r = r_guide + 1 + k
        c = ws.cell(row=r, column=1, value=f"  {k+1}.  {note}")
        c.font = _font(italic=True, color=P_GRAY)
        c.fill = _fill(P_LIGHT)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=12)
        ws.row_dimensions[r].height = 22

    _widths(ws, {"A": 32, "B": 20, "C": 18, "D": 18, "E": 18, "F": 20})
    _freeze(ws, "B5")


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

def generate_excel_report(
    analysis: AnalysisResult,
    original_data: dict[str, Any],
    filename: str = "analyse",
) -> bytes:
    """
    Génère l'Executive Financial Model V2 (8 feuilles).
    Signature maintenue pour compatibilité avec analyze.py.
    Toutes les données proviennent de l'EDM — aucune logique métier propre.

    Ordre des feuilles :
      1. Executive Dashboard  2. Hypothèses  3. Decision Lab
      4. Sensibilité          5. Scénarios   6. Roadmap
      7. Historique           8. EDM (masquée)
    """
    from services.executive_decision_model import build_executive_decision_model

    edm = build_executive_decision_model(original_data or {})

    wb = Workbook()
    wb.remove(wb.active)

    # EDM en premier (toutes les autres feuilles le référencent)
    _build_edm(wb, edm, original_data)

    # 7 feuilles visibles
    _build_dashboard(wb, edm, original_data)
    _build_hypotheses(wb, edm)
    _build_decision_lab(wb, edm)
    _build_sensitivity(wb, edm)
    _build_scenarios(wb, edm)
    _build_roadmap(wb, edm)
    _build_historique(wb, edm)

    # Masquer la feuille EDM
    wb[SN_EDM].sheet_state = "hidden"

    # Dashboard actif à l'ouverture
    wb.active = wb[SN_DASH]

    # Recalcul automatique à l'ouverture
    wb.calculation.calcMode = "auto"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
