"""
PEPPERYN EXECUTIVE REPORT — PDF
Design Baseline v1.0 — FROZEN by CTO Review

Ce fichier constitue la source unique de vérité pour toutes les constantes
structurelles du Rapport Exécutif PDF.

RÈGLE D'OR : Ce layout ne peut être modifié que par décision explicite du CTO.
Aucun algorithme ne peut ajuster ces valeurs de sa propre initiative.
Toute évolution doit être justifiée par :
  - une nouvelle fonctionnalité métier,
  - ou une demande explicite du CTO.
"""

# ─── PALETTE McKINSEY (valeurs hexadécimales brutes) ─────────────────────────
# Sources : export_pdf_service.py — palette gelée en sprint McKinsey Day 2

HEX_NAVY   = "#0A2540"   # titres, structure
HEX_BLUE   = "#1B4F8A"   # accents secondaires (roadmap phases)
HEX_RED    = "#C0392B"   # pertes, urgence — SIGNAL UNIQUE
HEX_AMBER  = "#B8763A"   # priorité moyenne (restreint)
HEX_GREEN  = "#1D6A3A"   # gains, confiance haute — SIGNAL UNIQUE
HEX_GRAY   = "#6B7280"   # labels, captions
HEX_LGRAY  = "#D8E3E9"   # filets 0.5 pt
HEX_LBGRAY = "#F8FAFB"   # fond très clair pour sections

# ─── GÉOMÉTRIE A4 ─────────────────────────────────────────────────────────────
# 1 pt ReportLab = 1/72 inch. A4 = 595.28 × 841.89 pts.

PAGE_W_PT      = 595   # largeur A4 arrondie (pts)
PAGE_H_PT      = 842   # hauteur A4 arrondie (pts)
MARGIN_MM      = 18    # marge latérale (mm)
TOP_MARGIN_MM  = 22    # marge supérieure (mm)
BOT_MARGIN_MM  = 16    # marge inférieure (mm)

# ─── NOMBRE DE PAGES ATTENDU ──────────────────────────────────────────────────
# Avec financial_statements complets (bilan, P&L, trésorerie) :
#   Cover(1) + P1–P10(10) + Transparence(1) + P&L+Bilan+Tréso(3) + Back(1) = 16

PAGES_FULL = 16   # avec états financiers
PAGES_SLIM = 13   # sans états financiers (P&L/Bilan/Tréso absents)

# ─── SÉQUENCE DES PAGES — CEO QUESTION FRAMEWORK ────────────────────────────
# Chaque entrée est un tuple (position_1indexed, builder_name, question_CEO, titre_section).
# RÈGLE : l'ordre est immuable. Toute insertion déplace les suivantes → décision CTO.

PAGE_SEQUENCE = [
    (1,  "cover",           None,                                   "RAPPORT EXÉCUTIF"),
    (2,  "verdict",         "Dois-je m'inquiéter ?",                "VERDICT EXÉCUTIF"),
    (3,  "capital",         "Pourquoi ?",                           "OÙ VOTRE CAPITAL EST SOUS-EMPLOYÉ"),
    (4,  "coi",             "Combien cela me coûte ?",              "COÛT DE L'INACTION"),
    (5,  "decisions",       "Que dois-je faire ?",                  "DÉCISIONS PRIORITAIRES"),
    (6,  "reasoning",       "Pourquoi cette décision ?",            "COMMENT PEPPERYN A RAISONNÉ"),
    (7,  "value_creation",  "Combien vais-je gagner ?",             "VALEUR CRÉÉE SI VOUS AGISSEZ"),
    (8,  "roadmap",         "Dans quel ordre, qui fait quoi ?",     "CALENDRIER D'ALLOCATION 30 / 60 / 90 JOURS"),
    (9,  "scenarios",       "Et si je me trompe ?",                 "3 SCÉNARIOS"),
    (10, "risks",           "Quels sont les risques ?",             "RISQUES À SURVEILLER"),
    (11, "kpis",            "Comment vais-je mesurer ?",            "MES KPIs DE PILOTAGE"),
    (12, "transparence",    None,                                   "TRANSPARENCE & FIABILITÉ DE L'ANALYSE"),
    # Pages 13-15 : états financiers (optionnel — présents si financial_statements fourni)
    (13, "pl",              None,                                   "COMPTE DE RÉSULTAT"),
    (14, "bilan",           None,                                   "BILAN"),
    (15, "tresorerie",      None,                                   "FLUX DE TRÉSORERIE"),
    (16, "back_cover",      None,                                   "Pepperyn"),
]

# ─── PHASES AGENT — PAGE 6 (RAISONNEMENT) ────────────────────────────────────
# Labels exacts des 4 phases de la méthodologie Pepperyn.
# Gelés ici pour que le test de cohérence cross-livrables puisse les vérifier.

PHASE_LABELS = [
    "PHASE 1 — CLASSIFICATION ET VALIDATION (AGENT DE CLASSIFICATION)",
    "PHASE 2 — ANALYSE STRATÉGIQUE EN DEUX PASSES (AGENT D'ANALYSE + AGENT DE VÉRIFICATION)",
    "PHASE 3 — CALCUL DES INDICATEURS (MOTEUR DE CALCUL DÉTERMINISTE)",
    "PHASE 4 — STRUCTURATION ET CONVICTION (AGENT 1 — EXECUTIVE CASE BUILDER)",
]

# ─── TYPOGRAPHIE CLÉS ────────────────────────────────────────────────────────
# Tailles en points. Fonte : Helvetica (système, pas d'import tiers requis).

FONT_HEADER_SIZE     = 7.5   # bandeau supérieur header
FONT_PAGE_TITLE_SIZE = 14    # titre de section (grande question CEO)
FONT_BODY_SIZE       = 9     # corps de texte standard
FONT_CAPTION_SIZE    = 8     # légendes, notes
FONT_HERO_SIZE       = 36    # chiffres-héros (type "1,1 M€")
