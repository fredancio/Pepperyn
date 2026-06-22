"""
Tests Étape A — Executive Decision Model (vocabulaire Executive Narrative).

Pas de dépendance à pytest (non installé dans ce projet) : script autonome,
assertions simples, exécutable via :

    python3 backend/tests/test_executive_decision_model.py

Ne touche à aucun fichier existant, ne fait aucun appel réseau/LLM.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.executive_decision_model import (  # noqa: E402
    build_executive_decision_model,
    build_monthly_series,
    compute_cost_of_inaction,
    compute_due_date,
    compute_pct_revenue,
    compute_phase_label,
    compute_priority,
    compute_roi_score,
    parse_amount_eur,
)

PASS = 0
FAIL = 0


def check(label: str, actual, expected):
    global PASS, FAIL
    ok = actual == expected
    PASS += int(ok)
    FAIL += int(not ok)
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label} -> {actual!r} (attendu {expected!r})")


def check_close(label: str, actual, expected, tol=0.01):
    global PASS, FAIL
    ok = actual is not None and abs(actual - expected) <= tol
    PASS += int(ok)
    FAIL += int(not ok)
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label} -> {actual!r} (attendu ~{expected!r})")


print("=== parse_amount_eur ===")
check("vide", parse_amount_eur(""), None)
check("None", parse_amount_eur(None), None)
check("donnees insuffisantes", parse_amount_eur("Données insuffisantes"), None)
check("pourcentage seul", parse_amount_eur("82%"), None)
check_close("entier+espaces", parse_amount_eur("12 600€"), 12_600.0)
check_close("negatif+espaces", parse_amount_eur("-590 000€"), -590_000.0)
check_close("K majuscule", parse_amount_eur("971K€"), 971_000.0)
check_close("K avec espace", parse_amount_eur("336 K€"), 336_000.0)
check_close("M sans espace", parse_amount_eur("+1,8M€"), 1_800_000.0)
check_close("M avec espace", parse_amount_eur("2,4 M€"), 2_400_000.0)
check_close("simple avec signe plus", parse_amount_eur("+415€"), 415.0)
check_close("premier montant si plusieurs", parse_amount_eur("Vous perdez 2,4 M€/an (soit 200K€/mois)"), 2_400_000.0)

print("\n=== compute_cost_of_inaction ===")
coi = compute_cost_of_inaction(1_200_000)
check_close("per_year", coi.per_year, 1_200_000)
check_close("per_month", coi.per_month, 100_000)
check_close("per_week", coi.per_week, 23_076.92, tol=1)
check_close("per_day", coi.per_day, 3_287.67, tol=1)
check_close("per_hour", coi.per_hour, 136.99, tol=1)
check("None en entree", compute_cost_of_inaction(None), None)

print("\n=== compute_priority ===")
check("high (>500k)", compute_priority(600_000), "High")
check("high (=500k)", compute_priority(500_000), "High")
check("medium (100k-500k)", compute_priority(250_000), "Medium")
check("medium (=100k)", compute_priority(100_000), "Medium")
check("low (<100k)", compute_priority(50_000), "Low")
check("negatif traite en valeur absolue", compute_priority(-600_000), "High")
check("not evaluated si None", compute_priority(None), "Not evaluated")

print("\n=== compute_roi_score ===")
check("score roi croit avec impact (faible difficulte)", compute_roi_score(900_000, "faible") > compute_roi_score(200_000, "faible"), True)
check("score roi plus eleve si difficulte faible vs elevee", compute_roi_score(500_000, "faible") > compute_roi_score(500_000, "élevée"), True)
check("score roi 0 si impact None", compute_roi_score(None, "faible"), 0.0)

print("\n=== compute_phase_label ===")
check("30 -> Stabilize", compute_phase_label("30"), "Stabilize")
check("60 -> Optimize", compute_phase_label("60"), "Optimize")
check("90 -> Accelerate", compute_phase_label("90"), "Accelerate")
check("horizon inconnu -> Phase", compute_phase_label("120"), "Phase")

print("\n=== compute_due_date ===")
from datetime import date
check("echeance deterministe", compute_due_date(30, since=date(2026, 1, 1)), "31/01/2026")
check("echeance 90 jours", compute_due_date(90, since=date(2026, 1, 1)), "01/04/2026")

print("\n=== compute_pct_revenue ===")
check_close("pct standard", compute_pct_revenue(120_000, 2_400_000), 5.0)
check("pct sans total_revenue", compute_pct_revenue(120_000, None), None)
check("pct sans impact", compute_pct_revenue(None, 2_400_000), None)

print("\n=== build_monthly_series ===")
series = build_monthly_series(0.0, 1200.0, 12)
check("12 points", len(series), 12)
check_close("premier point", series[0], 0.0)
check_close("dernier point", series[-1], 1200.0)
check("croissance monotone", all(series[i] <= series[i + 1] for i in range(len(series) - 1)), True)

# ─────────────────────────────────────────────────────────────────────────────
# Test d'intégration : dict V11 synthétique -> ExecutiveDecisionModel complet
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== build_executive_decision_model (intégration) ===")

SYNTHETIC_RESULT = {
    "score_global": 3,
    "score_confiance": 90,
    "impact_financier_synthese": "Vous perdez 2,4 M€/an",
    "ceo_dashboard": [
        {"label": "💵 Chiffre d'affaires total", "value": "2 400 000€", "status": None},
        {"label": "💰 Cash disponible", "value": "336 K€", "status": None},
        {"label": "📈 EBITDA", "value": "-145 K€", "status": None},
        {"label": "📊 Marge", "value": "67%", "status": None},
    ],
    "quick_wins": [
        {
            "description": "Geler les recrutements consultants",
            "roi_estime": "+184 000€",
            "temps_mise_en_oeuvre": "1 mois",
            "difficulte": "faible",
        },
        {
            "description": "Renégocier le contrat IT",
            "roi_estime": "+58 000€",
            "temps_mise_en_oeuvre": "2 mois",
            "difficulte": "moyenne",
        },
    ],
    "value_destroyers": [
        {"name": "Masse salariale consultants", "impact_annuel": "278 000€", "tendance": "hausse", "commentaire": "Hausse de 16% sur l'année."},
        {"name": "Sous-traitance IT mal pilotée", "impact_annuel": "58 000€", "tendance": "stable", "commentaire": "Contrat non renégocié."},
    ],
    "leviers_croissance": [
        "🟢 Accélérer le SaaS / ARR sur la base installée",
        "🟢 Renégocier les contrats fournisseurs principaux",
    ],
    "plan_action_30_60_90": [
        {"action": "Geler la masse salariale consultants", "horizon": "30", "responsable": "CFO", "impact_attendu": "+184 000€"},
        {"action": "Renégocier IT", "horizon": "60", "responsable": "DSI", "impact_attendu": "+58 000€"},
        {"action": "Optimiser prix gamme B", "horizon": "90", "responsable": "Dir. Com.", "impact_attendu": "+146 000€"},
    ],
    "scenarios": [
        {"nom": "best_case", "label": "Meilleur cas", "description": "Gain rapide si toutes les actions sont prises."},
        {"nom": "worst_case", "label": "Pire cas", "description": "Dégradation continue si rien ne change."},
    ],
    "data_quality": {"score_data": 82, "status": "ok", "document_format": "xlsx"},
}

edm = build_executive_decision_model(SYNTHETIC_RESULT)

check("ebitda extrait", edm.ebitda, "-145 K€")
check("cash extrait", edm.available_cash, "336 K€")
check("health_score", edm.health_score, 3)
check("executive_confidence", edm.executive_confidence, 90)
check_close("cost_of_inaction per_year", edm.cost_of_inaction.per_year, 2_400_000)
check_close("cost_of_inaction per_month", edm.cost_of_inaction.per_month, 200_000)
check("2 executive decisions", len(edm.executive_decisions), 2)
check("executive decisions triees par impact desc", edm.executive_decisions[0].annual_impact >= edm.executive_decisions[1].annual_impact, True)
check("executive_decision (page 1) = decisions[0]", edm.executive_decision.decision, edm.executive_decisions[0].decision)
check("priorite 184k -> Medium (<500k)", edm.executive_decisions[0].priority, "Medium")
check("2 value destroyers extraits", len(edm.value_destroyers), 2)
check("destroyer trie par impact desc", edm.value_destroyers[0].annual_impact >= edm.value_destroyers[1].annual_impact, True)
check("destroyer name structure (pas de bullet brut)", edm.value_destroyers[0].name, "Masse salariale consultants")
check("destroyer trend traduit en anglais (hausse->up)", edm.value_destroyers[0].trend, "up")
check("destroyer trend stable", edm.value_destroyers[1].trend, "stable")
check("destroyer comment present", edm.value_destroyers[0].comment, "Hausse de 16% sur l'année.")
check_close("destroyer pct_revenue (278000/2400000)", edm.value_destroyers[0].pct_revenue, round(100 * 278_000 / 2_400_000, 1))
check("2 strategic levers extraits", len(edm.strategic_levers), 2)
check("3 phases roadmap 90 jours", len(edm.roadmap_90_days), 3)
check("phase 30 = Stabilize", edm.roadmap_90_days[0].phase_label, "Stabilize")
check("phase 60 = Optimize", edm.roadmap_90_days[1].phase_label, "Optimize")
check("phase 90 = Accelerate", edm.roadmap_90_days[2].phase_label, "Accelerate")
check("execution_log = 3 actions", len(edm.execution_log), 3)
check("execution_log trie par impact desc", edm.execution_log[0].impact >= edm.execution_log[-1].impact, True)
check("status par defaut", edm.execution_log[0].status, "To launch")
check("2 scenarios", len(edm.scenarios), 2)
check("12 points action_series", len(edm.action_series), 12)
check("12 points do_nothing_series", len(edm.do_nothing_series), 12)
check_close("action_series termine au gain global", edm.action_series[-1], 2_400_000)
check_close("do_nothing_series termine au symetrique negatif", edm.do_nothing_series[-1], -2_400_000)
check("copilot_note absent (Etape B)", edm.copilot_note, None)
check("business_context absent (gap documente)", edm.business_context, None)
check("follow_up present", edm.follow_up is not None, True)
check("5 commitments de suivi", len(edm.follow_up.commitments), 5)
check("data_quality parse", edm.data_quality.score_data, 82)

# ─────────────────────────────────────────────────────────────────────────────
# Test bout-en-bout Étape B : texte LLM réaliste -> _parse_v3_text -> EDM
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Étape B — pipeline complet (texte LLM -> parsing -> EDM) ===")

from services.llm_service import _parse_v3_text  # noqa: E402

SYNTHETIC_CLAUDE_TEXT = """[VERIFIED]
# DIAGNOSTIC IMMEDIAT
⚡ TENSION : Marge sous pression.
[Action — 1 phrase courte]

# RÉSUMÉ EXÉCUTIF
Synthèse de test.

# SCORES
- Rentabilité : 4/10 → insuffisant
- Risque : 6/10 → élevé
- Structure : 7/10 → solide
- Liquidité : 5/10 → tendue

# CEO DASHBOARD
💵 Chiffre d'affaires total : 2 400 000€
💰 Cash disponible : 336 K€
📈 EBITDA : -145 K€
📊 Marge : 67%
⏳ Runway : Données insuffisantes
🏦 Dette : Données insuffisantes
🚀 Croissance : Données insuffisantes

# MARGIN INTELLIGENCE
Score fiabilité : 80%
Raisons fiabilité : Données suffisantes
→ Marge brute : 67%
→ Marge opérationnelle : Données insuffisantes
→ Marge nette : Données insuffisantes
🔴 Destruction marge : Non chiffrable
🟢 Création marge : Non chiffrable
⚠️ Activité sous-performante : Non identifiable sur les données disponibles
👉 En résumé : Marge fragile.

# CASH FORECAST
→ Données insuffisantes

# IMPACT FINANCIER
💸 PERTE STRUCTURELLE ESTIMÉE : → 2 400 000€/an
→ Détail 1
→ Détail 2
→ Détail 3

# CREATION DESTRUCTION VALEUR
Destruction nette de valeur.

# AVANT APRES
### 📉 AUJOURD'HUI
Situation actuelle.
### 📈 APRÈS ACTION
Situation après action.
### 💥 GAIN POTENTIEL
Gain estimé.

# SIMULATEUR DECISION
→ Rentabilité : test
→ Investissement : test
→ Modèle : test

# SCENARIOS
### MEILLEUR CAS
Gain rapide.
### CAS PROBABLE
Stabilisation.
### PIRE CAS
Dégradation.

# PROJECTION TEMPORELLE
### 3 mois
Stabilisation.
### 6 mois
Retour à l'équilibre.
👉 En résumé : trajectoire positive si action.

# CE QUI DETRUIT
🔴 Masse salariale consultants | Impact annuel : 278 000€ | Tendance : hausse | Commentaire : Hausse de 16% sur l'année.
🔴 Sous-traitance IT mal pilotée | Impact annuel : 58 000€ | Tendance : stable | Commentaire : Contrat non renégocié depuis 2 ans.

# LEVIERS CROISSANCE
🟢 Accélérer le SaaS/ARR
🟢 Renégocier les fournisseurs

# PLAN D'ACTION
- action 1 → impact 1
- action 2 → impact 2

# QUICK WINS
→ Geler les recrutements consultants | ROI : 184 000€ | Délai : 1 mois | Difficulté : faible
→ Renégocier le contrat IT | ROI : 58 000€ | Délai : 2 mois | Difficulté : moyenne

# PLAN 30 60 90
### 30 JOURS
- Geler la masse salariale consultants → Responsable : CFO → Impact : 184 000€
### 60 JOURS
- Renégocier IT → Responsable : DSI → Impact : 58 000€
### 90 JOURS
- Optimiser prix gamme B → Responsable : Dir. Com. → Impact : 146 000€

# RISQUE INACTION
Dégradation continue si rien ne change.

# DIAGNOSTIC FINANCIER
- Revenus : stable
- Coûts : en hausse
- Marges : sous pression

# CE QUI A CHANGÉ
- Première analyse

# ALERTES
⚠️ Masse salariale en hausse

# PROBLÈMES CRITIQUES
🔴 Marge sous pression

# OPPORTUNITÉS
🟢 Renégociation fournisseurs

# DÉCISION
Geler les recrutements consultants dès cette semaine.

# CONFIDENTIAL COPILOT NOTE
Si j'étais votre Directeur Financier lundi matin, je gèlerais immédiatement les recrutements
consultants, je renégocierais le contrat IT, et je lancerais l'optimisation des prix sur la
gamme B. Ces trois décisions représentent l'essentiel du potentiel de redressement à court terme.

Pepperyn IA — Votre copilote financier
"""

parsed = _parse_v3_text(SYNTHETIC_CLAUDE_TEXT, "COMPTE_RESULTAT", 90)
check("parsing : 2 value_destroyers structures", len(parsed["value_destroyers"]), 2)
check("parsing : value_destroyers[0].name", parsed["value_destroyers"][0]["name"], "Masse salariale consultants")
check("parsing : ce_qui_detruit retro-compat (list[str])", all(isinstance(s, str) for s in parsed["ce_qui_detruit"]), True)
check("parsing : note_copilote extraite", "Pepperyn IA" in (parsed["note_copilote"] or ""), True)
check("parsing : CA total dans ceo_dashboard", any("affaires" in c["label"].lower() for c in parsed["ceo_dashboard"]), True)

parsed["score_global"] = 3  # normalement injecté par call_analysis_v3 avant export ; simulé ici
edm_e2e = build_executive_decision_model(parsed)
check("E2E : pct_revenue calcule depuis le texte LLM reel", edm_e2e.value_destroyers[0].pct_revenue, round(100 * 278_000 / 2_400_000, 1))
check("E2E : trend traduit", edm_e2e.value_destroyers[0].trend, "up")
check("E2E : copilot_note alimentee depuis le LLM", edm_e2e.copilot_note is not None and "Pepperyn IA" in edm_e2e.copilot_note, True)
check("E2E : strategic_levers depuis leviers_croissance", len(edm_e2e.strategic_levers), 2)
check("E2E : executive_decision = decision la plus impactante", edm_e2e.executive_decision.decision, "Geler les recrutements consultants")

print("\n=== Robustesse : dict vide / incomplet ===")
edm_empty = build_executive_decision_model({})
check("aucun crash sur dict vide", edm_empty is not None, True)
check("ebitda None sur dict vide", edm_empty.ebitda, None)
check("listes vides sur dict vide", edm_empty.executive_decisions, [])
check("cost_of_inaction None sur dict vide", edm_empty.cost_of_inaction, None)
check("strategic_levers vide sur dict vide", edm_empty.strategic_levers, [])
check("follow_up toujours present", edm_empty.follow_up is not None, True)

edm_none = build_executive_decision_model(None)
check("aucun crash sur None", edm_none is not None, True)

print(f"\n{'=' * 60}\nRésultat : {PASS} OK / {FAIL} FAIL\n{'=' * 60}")
sys.exit(1 if FAIL else 0)
