"""
PEPPERYN BOARD DECK — PPTX
Design Baseline v1.0 — FROZEN by CTO Review

Ce fichier constitue la source unique de vérité pour toutes les constantes
structurelles du Board Deck PowerPoint.

RÈGLE D'OR : Ce layout ne peut être modifié que par décision explicite du CTO.
Aucun algorithme ne peut ajuster ces valeurs de sa propre initiative.
Toute évolution doit être justifiée par :
  - une nouvelle fonctionnalité métier,
  - ou une demande explicite du CTO.
"""

# ─── PALETTE McKINSEY (identique au PDF) ─────────────────────────────────────
# Sources : export_pptx_service.py — palette gelée en sprint McKinsey Day 2

HEX_NAVY   = "#0A2540"   # header band, card backgrounds sombres
HEX_BLUE   = "#1B73E8"   # accents secondaires, Phase 1
HEX_RED    = "#C0392B"   # pertes, urgence — SIGNAL UNIQUE
HEX_AMBER  = "#B8763A"   # Phase 2, impact box couverture — restreint
HEX_GREEN  = "#2C7A4B"   # gains, Phase 3
HEX_GRAY   = "#8A9BB0"   # labels, footer
HEX_LGRAY  = "#D5DCE5"   # filets de tableau
HEX_WHITE  = "#FFFFFF"   # texte sur fond sombre
HEX_DARK   = "#1A1A2E"   # texte principal sur fond clair
HEX_LBGRAY = "#F5F7FA"   # fond très clair (cards)

# ─── DIMENSIONS SLIDE 16:9 ───────────────────────────────────────────────────
# Format : 33.87 cm × 19.05 cm (Widescreen standard PPTX)
# Unités : inches (python-pptx Inches)

SLIDE_W_IN = 13.33   # largeur slide
SLIDE_H_IN = 7.5     # hauteur slide
ML_IN      = 0.5     # marge gauche
MR_IN      = 0.5     # marge droite
MT_IN      = 1.1     # top (sous le header band)
MB_IN      = 0.45    # bottom (au-dessus du footer)

# Zones dérivées
CONTENT_W_IN = SLIDE_W_IN - ML_IN - MR_IN     # ~12.33"
CONTENT_H_IN = SLIDE_H_IN - MT_IN - MB_IN     # ~5.95"

# ─── NOMBRE DE SLIDES ATTENDU ────────────────────────────────────────────────
# S7b (méthodologie/raisonnement comparatif) est TOUJOURS présente → 17 slides

SLIDES_TOTAL = 17   # avec slide S7b systématique
SLIDES_LEGACY = 16  # ancienne valeur (avant McKinsey Sprint Day 3) — référence historique

# ─── SÉQUENCE DES SLIDES ─────────────────────────────────────────────────────
# Chaque entrée : (position_1indexed, builder_name, header_label, slide_title)
# RÈGLE : l'ordre est immuable. Toute insertion déplace les suivantes → décision CTO.

SLIDE_SEQUENCE = [
    (1,  "_slide_cover",                    "EXECUTIVE DECISION",         "EXECUTIVE DECISION"),
    (2,  "_slide_exec_summary",             "EXECUTIVE SUMMARY",          "Synthèse des décisions prioritaires"),
    (3,  "_slide_diagnostic",               "DIAGNOSTIC",                 "Pourquoi en sommes-nous arrivés là ?"),
    (4,  "_slide_dashboard",                "GOUVERNANCE",                "CEO Dashboard"),
    (5,  "_slide_impact_financier",         "IMPACT FINANCIER",           "Où la valeur attend d'être libérée"),
    (6,  "_slide_cout_inaction",            "DÉCISION",                   "Le coût de l'inaction"),
    (7,  "_slide_decisions_prioritaires",   "DÉCISIONS PRIORITAIRES",     "Plan d'action prioritaire"),
    (8,  "_slide_raisonnement_comparatif",  "MÉTHODOLOGIE / RAISONNEMENT","Comment Pepperyn a raisonné"),
    (9,  "_slide_execution",                "EXÉCUTION",                  "Roadmap 30 / 60 / 90 jours"),
    (10, "_slide_simulation",               "SIMULATION",                 "Impact action vs inaction"),
    (11, "_slide_projection",               "PROJECTION",                 "Trajectoire financière — 12 mois"),
    (12, "_slide_risques",                  "RISQUES",                    "Risques majeurs identifiés"),
    (13, "_slide_priorites",                "PRIORITÉS",                  "Matrice de priorisation — Impact / Effort"),
    (14, "_slide_suivi",                    "SUIVI",                      "Carnet d'exécution"),
    (15, "_slide_pilotage",                 "PILOTAGE",                   "Tableau de bord de pilotage"),
    (16, "_slide_lundi_matin",              "LUNDI MATIN",                "Ce que vous faites lundi matin"),
    (17, "_slide_annexe",                   "ANNEXE",                     "Annexe — Qualité, Méthodologie et Engagements"),
]

# ─── PHASES AGENT — SLIDE 8 (MÉTHODOLOGIE) ───────────────────────────────────
# Labels exacts des 4 phases — source de vérité cross-livrables.
# DOIT être identique à config/pdf_layout.py::PHASE_LABELS.

PHASE_LABELS = [
    "PHASE 1 — CLASSIFICATION ET VALIDATION (AGENT DE CLASSIFICATION)",
    "PHASE 2 — ANALYSE STRATÉGIQUE EN DEUX PASSES (AGENT D'ANALYSE + AGENT DE VÉRIFICATION)",
    "PHASE 3 — CALCUL DES INDICATEURS (MOTEUR DE CALCUL DÉTERMINISTE)",
    "PHASE 4 — STRUCTURATION ET CONVICTION (AGENT 1 — EXECUTIVE CASE BUILDER)",
]

# Labels courts (affichés dans les cards de la slide méthodologie)
PHASE_LABELS_SHORT = [
    "CLASSIFICATION ET VALIDATION",
    "ANALYSE STRATÉGIQUE EN DEUX PASSES",
    "CALCUL DES INDICATEURS",
    "STRUCTURATION ET CONVICTION",
]

# ─── COMPOSANTS STRUCTURELS ───────────────────────────────────────────────────

# Header band
HEADER_H_IN     = 0.75   # hauteur du bandeau header navy
HEADER_FONT_PT  = 12     # taille label section (amber)
BRAND_FONT_PT   = 11     # taille "PEPPERYN" (blanc)

# Footer band
FOOTER_H_IN     = 0.4    # hauteur du bandeau footer
FOOTER_FONT_PT  = 9      # taille texte confidentiel + numéro

# Typographie
FONT_SLIDE_TITLE_PT  = 36   # titre principal de slide
FONT_SUBTITLE_PT     = 14   # sous-titre de slide (GRAY)
FONT_HERO_PT         = 52   # chiffre héros (coût inaction, cover)
FONT_TABLE_HDR_PT    = 11   # en-têtes de tableau (blanc sur NAVY)
FONT_TABLE_BODY_PT   = 12   # cellules de tableau
FONT_CARD_LABEL_PT   = 9    # labels dans les cards
FONT_CARD_TITLE_PT   = 12   # titres dans les cards

# Couleurs de Phase (indices 0–3 → PHASE_LABELS_SHORT)
PHASE_COLORS_HEX = [
    "#1B73E8",   # Phase 1 — bleu
    "#B8763A",   # Phase 2 — amber
    "#2C7A4B",   # Phase 3 — vert
    "#0A2540",   # Phase 4 — navy
]
