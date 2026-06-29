"""
PEPPERYN EXECUTIVE FINANCIAL MODEL
Design Baseline v1.0 — FROZEN by CTO Review

Ce fichier constitue la source unique de vérité pour toutes les constantes
de mise en page du Financial Model Excel.

RÈGLE D'OR : Ce layout ne peut être modifié que par décision explicite du CTO.
Aucun algorithme ne peut ajuster ces valeurs de sa propre initiative.
Toute évolution doit être justifiée par :
  - une nouvelle fonctionnalité métier,
  - ou une demande explicite du CTO.
"""

# ─── HAUTEURS DE LIGNE STANDARD ──────────────────────────────────────────────
# Valeurs en points Excel. Constantes issues de l'inspection visuelle CTO (v7).

ROW_H_HEADER           = 34   # _header_bar  (bandeau titre navy)
ROW_H_SECTION          = 22   # _section_bar (bandeau sous-section)
ROW_H_COL_HDR          = 22   # _col_headers (ligne d'en-têtes de colonne)
ROW_H_NAV              = 18   # _nav_bar     (bandeau fil d'Ariane)
ROW_H_INSTRUCTION      = 20   # _instruction (note ℹ, texte court)
ROW_H_INSTRUCTION_WIDE = 40   # _instruction (Dashboard — texte 2 lignes)
ROW_H_KPI_PROJECTED    = 26   # Tableau de bord projeté (Decision Lab)
ROW_H_GUIDE_NOTE       = 22   # Lignes guide/mode d'emploi

# ─── COL_END PAR FEUILLE ─────────────────────────────────────────────────────
# Nombre de colonnes couvertes par les barres (header, instruction, nav, section).
# Doit être strictement égal au nombre de colonnes de données de la feuille.

COL_END_EDM          = 8
COL_END_DASHBOARD    = 17
COL_END_HYPOTHESES   = 4
COL_END_DECISION_LAB = 8
COL_END_SENSIBILITE  = 8
COL_END_SCENARIOS    = 5
COL_END_ROADMAP      = 9
COL_END_HISTORIQUE   = 6

# ─── LARGEURS DE COLONNE PAR FEUILLE ─────────────────────────────────────────
# Clés = lettres de colonne (str). Valeurs = largeur en unités Excel.
# Total indicatif entre parenthèses pour contrôle.

COLS_EDM = {
    "A": 35, "B": 18, "C": 16, "D": 14, "E": 28, "F": 14, "G": 10,
}
# Total : 135u

# Dashboard : toutes les colonnes à 7u, puis les espaceurs surchargés.
COLS_DASHBOARD_BASE = {str(i): 7 for i in range(1, 18)}  # A→Q = 7u chacune
COLS_DASHBOARD = {
    "A": 1.5, "B": 7, "C": 7, "D": 7,
    "E": 1.5, "F": 7, "G": 7, "H": 7,
    "I": 1.5, "J": 7, "K": 7, "L": 7,
    "M": 1.5, "N": 7, "O": 7, "P": 7,
    "Q": 1.5,
}
# Total : 4×1.5 + 13×7 = 6 + 91 = 97u

COLS_HYPOTHESES = {
    "A": 36, "B": 22, "C": 12, "D": 34,
}
# Total : 104u

COLS_DECISION_LAB = {
    "A": 4, "B": 90, "C": 20, "D": 10, "E": 14, "F": 18, "G": 12, "H": 12,
}
# Total : 180u

COLS_SENSIBILITE = {
    "A": 34, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14, "H": 18,
}
# Total : 136u

COLS_SCENARIOS = {
    "A": 32, "B": 24, "C": 24, "D": 24, "E": 30,
}
# Total : 134u

COLS_ROADMAP = {
    # B (Décision/Action) = colonne primaire — jamais réduite.
    # C (Responsable) élargi à 24u pour tenir "DAF + Directeur Logistique" sur 1 ligne.
    # G, H, I allégés en compensation — total inchangé à 167u.
    "A":  4, "B": 76, "C": 24,
    "D": 13, "E": 13, "F": 11,
    "G": 10, "H":  8, "I":  8,
}
# Total : 167u

COLS_HISTORIQUE = {
    "A": 34, "B": 22, "C": 20, "D": 20, "E": 20, "F": 22,
}
# Total : 138u
