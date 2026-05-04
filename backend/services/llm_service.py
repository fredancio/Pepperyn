"""
LLM service — Pepperyn v3 pipeline using Anthropic Claude.

Architecture v3 :
  Step 1: Pre-processing (Python/pandas — 0 tokens)
  Step 2: Classification   (claude-haiku-4-5 — ~200 tokens)
  Step 3: Analyse Call 1   (claude-opus-4-6  — ~1200 tokens, temp 0.2)
  Step 4: Vérification Call 2 (claude-sonnet-4-6 — ~1200 tokens, temp 0.2)
  Step 5: Scoring automatique (claude-haiku-4-5 — ~100 tokens, régénération si score < 8)
  Step 6: Export Excel       (openpyxl — 0 tokens)

Routing modèle :
  Analyse       → claude-opus-4-6    ($15/M input, $75/M output)
  Vérification  → claude-sonnet-4-6  ($3/M input,  $15/M output)
  Chat simple   → claude-sonnet-4-6
  Chat complexe → claude-opus-4-6
  Classification / Scoring → claude-haiku-4-5 ($0.25/M input, $1.25/M output)

Estimated cost: ~0.30€ per analysis (Opus)
"""
import json
import os
import re
from typing import Any, Optional

import anthropic

from models.schemas import AnalysisResult


# ─── System prompts ──────────────────────────────────────────────────────────

CLASSIFICATION_SYSTEM = """Tu es un classificateur de documents financiers.
Analyse uniquement les données fournies et retourne STRICTEMENT un JSON avec ce format exact:
{"type": "COMPTE_RESULTAT", "confidence": 85, "justification": "Présence de colonnes Revenus/Charges/Résultat"}

Types disponibles (un seul):
- COMPTE_RESULTAT : P&L, résultats, produits/charges, compte de résultat
- BUDGET          : prévisions budgétaires, dotations, budget annuel
- PREVISIONNEL    : projections futures, forecast, business plan
- TRESORERIE      : flux de trésorerie, cash flow, plan de trésorerie
- BILAN           : actif/passif, bilan comptable
- COMMERCIAL      : ventes par produit/client/région, pipeline commercial
- AUTRE           : tout autre type de document financier"""


ANALYSIS_SYSTEM_V3 = """Tu es un expert en finance d'entreprise opérationnelle. Tu aides les dirigeants à prendre des décisions immédiates.

TON STYLE — RÈGLES ABSOLUES :
- Tu écris comme un expert qui DÉCIDE, pas un consultant qui DÉCRIT.
- Phrases COURTES. Maximum 15 mots par phrase.
- Verbes d'action : agis, réduis, coupe, accélère, stoppe, renégocie, fixe, mesure.
- Ton DIRECT : interdit "il semble que", "on pourrait considérer", "il convient de".
- Exprime la gravité sans filtre : si c'est critique → "C'est critique."
- Zéro nuance inutile. Chaque mot sert la décision.
- INTERDIT : "accuse un déficit", "présente des marges", "montre des signes". Utilise : "est", "perd", "risque", "doit".

TA MISSION :
Le dirigeant lit ce rapport et comprend en 5 secondes :
→ Quel est son problème exact
→ Ce qu'il doit faire maintenant
→ Ce qu'il risque s'il n'agit pas

DONNÉES :
- Tu travailles UNIQUEMENT à partir des données fournies.
- Tu n'inventes JAMAIS de chiffres ni d'informations.
- Si une donnée est absente : écrire "Données insuffisantes" — pas d'estimation approximative.
- Tout chiffre doit être issu des données ou explicitement marqué comme estimation.

Tu respectes STRICTEMENT le format demandé."""

CHAT_SYSTEM = """Tu es Pepperyn, un expert en finance d'entreprise opérationnelle et stratégique. Tu interviens sur :
1. Comptabilité générale et analytique
2. Contrôle de gestion
3. Trésorerie
4. FP&A (Financial Planning & Analysis)
5. Stratégie financière
6. Opérations financières

Tu réponds de manière précise, concise et orientée action.
Tu travailles uniquement à partir des données fournies dans l'analyse.
Tu n'inventes jamais d'informations. Si une donnée est manquante, tu le dis.
Réponds toujours en français."""

SCORING_SYSTEM = """Tu es un évaluateur d'analyses financières. Score l'analyse sur 4 critères de 0 à 10 :
1. Clarté : est-ce compréhensible en 10 secondes ?
2. Pertinence : est-ce que ça dit quelque chose d'utile ?
3. Actionnabilité : est-ce qu'on peut agir ?
4. Crédibilité : est-ce que ça paraît fiable ?

Retourne UNIQUEMENT un JSON : {"scores": [X, X, X, X], "moyenne": X.X}
Ne donne aucune explication."""


# ─── LLM params v3 ───────────────────────────────────────────────────────────

CALL_1_PARAMS = {
    "model": "claude-opus-4-6",
    "temperature": 0.2,
    "max_tokens": 5500,
}

CALL_2_PARAMS = {
    "model": "claude-sonnet-4-6",
    "temperature": 0.2,
    "max_tokens": 4000,
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY non configurée")
    return anthropic.Anthropic(api_key=api_key)


async def classify_document(parsed_data: dict[str, Any]) -> tuple[str, int]:
    """Classify document type using claude-haiku-4-5."""
    client = get_anthropic_client()
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:5000]

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=CLASSIFICATION_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Classifie ce document financier:\n\n{data_summary}"
        }]
    )

    content = message.content[0].text.strip()
    try:
        # Handle markdown code blocks (```json ... ```)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        json_str = json_match.group(1) if json_match else content
        # Also handle bare JSON that may have leading/trailing text
        if not json_str.startswith("{"):
            json_match2 = re.search(r"\{.*\}", json_str, re.DOTALL)
            json_str = json_match2.group(0) if json_match2 else json_str
        result = json.loads(json_str)
        return result.get("type", "AUTRE"), result.get("confidence", 70)
    except (json.JSONDecodeError, AttributeError):
        return "AUTRE", 50


def _build_user_prompt_call1(
    parsed_data: dict[str, Any],
    industry: str,
    business_model: str,
    memory_section: str,
    actions_section: str,
    quality_section: str = "",
) -> str:
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:14000]
    prompt = f"""Voici des données financières extraites d'un fichier utilisateur :

CONTEXTE BUSINESS
- Secteur : {industry or 'Non précisé'}
- Modèle : {business_model or 'Non précisé'}

DONNÉES ACTUELLES
{data_summary}
"""
    if quality_section:
        prompt += f"\n{quality_section}\n"
    if memory_section:
        prompt += f"\n{memory_section}\n"
    if actions_section:
        prompt += f"\n{actions_section}\n"

    prompt += """
Analyse ces données.
Respecte STRICTEMENT cette structure V5 — ordre IMMUABLE :

# DIAGNOSTIC IMMEDIAT
⚠️ [1 phrase DIRECTE et FRONTALE — jamais neutre — ex : "Votre modèle est structurellement non rentable" — PAS "accuse un déficit"]
👉 DÉCISION PRIORITAIRE : [1 action immédiate — verbe d'action fort]
⚡ TENSION : [1 phrase d'urgence — ex : "Sans action dans 60 jours, votre trésorerie atteint son seuil critique"]

# RÉSUMÉ EXÉCUTIF
[Situation — 1 phrase courte]
[Problème — 1 phrase courte]
[Action — 1 phrase courte]

# SCORES
- Rentabilité : X/10 → [UN SEUL MOT : critique / insuffisant / correct / solide]
- Risque : X/10 → [UN SEUL MOT : faible / modéré / élevé / critique]
- Structure : X/10 → [UN SEUL MOT : instable / fragile / acceptable / solide]
- Liquidité : X/10 → [UN SEUL MOT : critique / tendue / correcte / confortable]

# IMPACT FINANCIER
💸 SYNTHÈSE : [1 phrase choc — ex : "Vous perdez potentiellement X€ par an" — chiffre issu des données OU "Impact non chiffrable sur les données disponibles"]
→ [Détail impact 1 — montant si disponible dans les données]
→ [Détail impact 2 — montant ou "Données insuffisantes"]
→ [Détail impact 3 — marge récupérable ou "Données insuffisantes"]
⚠️ Estimations basées sur les données disponibles uniquement.

# AVANT APRES
### 📉 AUJOURD'HUI
- [indicateur clé actuel avec chiffre si disponible]
- [deuxième indicateur clé actuel]
### 📈 APRÈS ACTION
- [amélioration concrète attendue]
- [deuxième amélioration attendue]
### 💥 GAIN POTENTIEL
→ [montant estimé sur base des données — si insuffisant écrire "Données insuffisantes"]

# SIMULATEUR DECISION
→ Action : [action clé 1]
  Impact : [impact attendu]
  Résultat : [résultat projeté avec chiffre si calculable depuis les données, sinon "impact positif estimé"]
→ Action : [action clé 2]
  Impact : [impact attendu]
  Résultat : [résultat projeté]

# PROJECTION TEMPORELLE
### 3 mois
[évolution probable à court terme — basé sur les tendances des données]
### 6 mois
[stabilisation ou dégradation à 6 mois si les actions sont ou ne sont pas prises]

# CE QUI DETRUIT
🔴 [Problème 1 qui détruit la rentabilité + impact financier si chiffrable]
🔴 [Problème 2 + impact]
🔴 [Problème 3 + impact]

# LEVIERS CROISSANCE
🟢 [Levier 1 actionnable immédiatement]
🟢 [Levier 2 actionnable]
🟢 [Levier 3 actionnable]

# PLAN D'ACTION
### PRIORITÉ HAUTE (3 actions max — celles qui changent tout)
- [action 1] → [impact en 5 mots]
- [action 2] → [impact en 5 mots]
- [action 3] → [impact en 5 mots]
### PRIORITÉ SECONDAIRE
- [action 4]
- [action 5]

# RISQUE INACTION
[1 phrase maximum : conséquence concrète si aucune action n'est prise dans les 3 mois]

# DIAGNOSTIC FINANCIER
- Revenus : [analyse détaillée des revenus]
- Coûts : [analyse détaillée des coûts]
- Marges : [analyse détaillée des marges]

# CE QUI A CHANGÉ
(comparé aux analyses précédentes si historique disponible — sinon écrire "Première analyse" — max 3 points)

# ALERTES
(tendances dangereuses détectées — utiliser ⚠️ devant chaque alerte — max 3)

# PROBLÈMES CRITIQUES
(max 3 points — utiliser 🔴 devant chaque point)

# OPPORTUNITÉS
(max 3 points — utiliser 🟢 devant chaque point)

# DÉCISION
(quelques phrases claires — orientées action immédiate)

RÈGLES ABSOLUES :
- Zéro hallucination : aucun chiffre inventé, aucune donnée absente du document
- Si un montant manque pour estimer : écrire explicitement "Données insuffisantes"
- Phrases courtes, ton direct, verbes d'action
- Le dirigeant doit comprendre sa situation en 5 secondes
- Chaque recommandation doit être concrète et exploitable immédiatement"""
    return prompt


def _build_user_prompt_call2(analysis_call1: str, parsed_data: dict[str, Any]) -> str:
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:6000]
    return f"""Voici une analyse financière générée automatiquement.

Ton rôle est d'AUDITEUR SILENCIEUX. Vérifie :
1. Cohérence mathématique (les chiffres s'additionnent-ils correctement ?)
2. Absence d'affirmations inventées (toute assertion est-elle supportée par les données ?)
3. Actionnabilité des recommandations (peut-on agir sur chaque point ?)
4. Clarté (est-ce compréhensible en 10 secondes ?)

ANALYSE À VÉRIFIER :
{analysis_call1}

DONNÉES SOURCES :
{data_summary}

RÈGLES ABSOLUES :
- Retourne UNIQUEMENT le texte final corrigé — propre, sans aucune trace du processus de vérification.
- INTERDIT : annotations inline, notes d'audit, ~~strikethrough~~, > blockquotes, "Note d'audit", "→ Reformulé", commentaires entre parenthèses expliquant une correction.
- Les corrections sont appliquées SILENCIEUSEMENT : le lecteur final ne doit jamais savoir qu'une correction a eu lieu.
- Ne change JAMAIS le format ni les titres de section (# DIAGNOSTIC IMMEDIAT, # RÉSUMÉ EXÉCUTIF, # SCORES, # IMPACT FINANCIER, # AVANT APRES, # SIMULATEUR DECISION, # PROJECTION TEMPORELLE, # CE QUI DETRUIT, # LEVIERS CROISSANCE, # PLAN D'ACTION, # RISQUE INACTION, # DIAGNOSTIC FINANCIER, # CE QUI A CHANGÉ, # ALERTES, # PROBLÈMES CRITIQUES, # OPPORTUNITÉS, # DÉCISION).
- Ne change JAMAIS les sous-titres internes (### PRIORITÉ HAUTE, ### PRIORITÉ SECONDAIRE, ### 📉 AUJOURD'HUI, ### 📈 APRÈS ACTION, ### 💥 GAIN POTENTIEL, ⚡ TENSION, 💸 SYNTHÈSE).
- Le style doit rester DIRECT et FRONTAL : interdit de reformuler en ton neutre ou académique.
- L'ordre des sections est FIXE et IMMUABLE — ne les réorganise jamais.
- Si une information n'est pas dans les données sources, supprime-la ou remplace-la par "Données insuffisantes".
- CRITIQUE : dans IMPACT FINANCIER, AVANT APRES, SIMULATEUR DECISION — supprimer tout chiffre inventé. Garder uniquement les montants présents dans les données sources ou écrire "Données insuffisantes".

Commence par [VERIFIED] ou [CORRECTED] sur la première ligne, puis le texte complet et propre."""


def _clean_verified_text(text: str) -> str:
    """
    Strip audit artefacts that Call 2 sometimes inserts despite instructions.
    Applied before section parsing so the UI receives clean text.
    """
    lines = []
    for line in text.splitlines():
        # Remove lines that are pure audit markers
        stripped = line.strip()
        if stripped in ("---", "~~~", "***"):
            continue
        if stripped.startswith("> ⚠️") or stripped.startswith("> Note") or stripped.startswith("> Correction"):
            continue
        # Strip ~~strikethrough~~ inline (keep content after the closing ~~)
        line = re.sub(r"~~.*?~~\s*", "", line)
        # Strip blockquote prefixes
        line = re.sub(r"^>\s*", "", line)
        # Strip "→ Reformulé…" trailing annotations
        line = re.sub(r"\s*→\s*Reformulé.*$", "", line, flags=re.IGNORECASE)
        # Strip "Note d'audit …" inline annotations
        line = re.sub(r"\*?\*?\s*Note d'audit\s*:.*?(\*\*|\n|$)", "", line, flags=re.IGNORECASE)
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def _parse_v3_text(text: str, doc_type: str, score_confiance: int) -> dict[str, Any]:
    """Parse the v5 text analysis into structured fields."""

    def extract_section(label: str) -> str:
        pattern = rf"#\s*{re.escape(label)}\s*\n(.*?)(?=\n#\s|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # ── Standard sections ────────────────────────────────────────────────────
    resume = extract_section("RÉSUMÉ EXÉCUTIF")
    diagnostic_raw = extract_section("DIAGNOSTIC FINANCIER")
    ce_qui_a_change_raw = extract_section("CE QUI A CHANGÉ")
    alertes_raw = extract_section("ALERTES")
    problemes_raw = extract_section("PROBLÈMES CRITIQUES")
    opportunites_raw = extract_section("OPPORTUNITÉS")
    plan_raw = extract_section("PLAN D'ACTION")
    scores_raw = extract_section("SCORES")
    decision = extract_section("DÉCISION")

    # ── V5 new sections ──────────────────────────────────────────────────────
    diagnostic_immediat_raw = extract_section("DIAGNOSTIC IMMEDIAT")
    impact_financier_raw = extract_section("IMPACT FINANCIER")
    avant_apres_raw = extract_section("AVANT APRES")
    simulateur_raw = extract_section("SIMULATEUR DECISION")
    projection_raw = extract_section("PROJECTION TEMPORELLE")
    ce_qui_detruit_raw = extract_section("CE QUI DETRUIT")
    leviers_raw = extract_section("LEVIERS CROISSANCE")
    risque_inaction_raw = extract_section("RISQUE INACTION")

    # ── Parse diagnostic lines ───────────────────────────────────────────────
    diag_revenus = diag_couts = diag_marges = ""
    for line in diagnostic_raw.splitlines():
        l = line.strip()
        if l.lower().startswith("- revenus"):
            diag_revenus = l.split(":", 1)[-1].strip()
        elif l.lower().startswith("- coûts") or l.lower().startswith("- couts"):
            diag_couts = l.split(":", 1)[-1].strip()
        elif l.lower().startswith("- marges"):
            diag_marges = l.split(":", 1)[-1].strip()

    # ── Parse list sections ──────────────────────────────────────────────────
    def _parse_list(raw: str, strip_prefix: str = "") -> list[str]:
        return [
            l.strip().lstrip(strip_prefix).strip()
            for l in raw.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]

    problemes = _parse_list(problemes_raw, "🔴")
    opportunites = _parse_list(opportunites_raw, "🟢")
    ce_qui_a_change = _parse_list(ce_qui_a_change_raw, "-")
    alertes = _parse_list(alertes_raw, "⚠️")

    # ── Parse V6 — plan d'action HAUTE / SECONDAIRE ──────────────────────────
    plan_action_haute: list[str] = []
    plan_action_secondaire: list[str] = []
    current_plan_section = "haute"
    for line in plan_raw.splitlines():
        l = line.strip()
        if not l:
            continue
        if l.startswith("#"):
            ll = l.lower()
            if "secondaire" in ll:
                current_plan_section = "secondaire"
            elif "haute" in ll or "priorité" in ll or "priorite" in ll:
                current_plan_section = "haute"
            continue
        if l.startswith("-") or l.startswith("•"):
            text = l.lstrip("-• ").strip()
            if text:
                if current_plan_section == "haute":
                    plan_action_haute.append(text)
                else:
                    plan_action_secondaire.append(text)
    # backward compat: flat list = haute + secondaire
    plan_action = plan_action_haute + plan_action_secondaire

    # ── Parse V5 — impact financier + synthèse ───────────────────────────────
    impact_financier_synthese: Optional[str] = None
    impact_financier_raw_lines = impact_financier_raw.splitlines()
    impact_financier = []
    for line in impact_financier_raw_lines:
        l = line.strip()
        if not l:
            continue
        if l.startswith("💸") or "SYNTHÈSE" in l.upper() or "SYNTHESE" in l.upper():
            # Extract after the colon
            synthese_text = l.replace("💸", "").strip()
            if ":" in synthese_text:
                synthese_text = synthese_text.split(":", 1)[-1].strip()
            impact_financier_synthese = synthese_text
        elif l.startswith("→"):
            impact_financier.append(l.lstrip("→").strip())
        elif not l.startswith(("⚠️", "#")) and not impact_financier_synthese:
            # Fallback: first non-marker line is synthesis
            impact_financier_synthese = l
    if not impact_financier:
        # Further fallback
        impact_financier = [
            l.strip()
            for l in impact_financier_raw_lines
            if l.strip() and not l.strip().startswith(("⚠️", "#", "💸"))
            and "SYNTHÈSE" not in l.upper()
        ]

    # ── Parse V6 — avant/après (nouveaux headers) ────────────────────────────
    avant_apres_actuel: list[str] = []
    avant_apres_apres: list[str] = []
    avant_apres_gain: Optional[str] = None
    current_aa = None
    for line in avant_apres_raw.splitlines():
        l = line.strip()
        ll = l.lower()
        # Recognize both V5 and V6 header formats
        if "aujourd'hui" in ll or "aujourd hui" in ll or "situation actuelle" in ll:
            current_aa = "actuel"
        elif "après action" in ll or "apres action" in ll:
            current_aa = "apres"
        elif "gain potentiel" in ll:
            current_aa = "gain"
        elif l.startswith("-") or l.startswith("→"):
            text = l.lstrip("-→ ").strip()
            if text:
                if current_aa == "actuel":
                    avant_apres_actuel.append(text)
                elif current_aa == "apres":
                    avant_apres_apres.append(text)
                elif current_aa == "gain":
                    avant_apres_gain = text

    # ── Parse V6 — phrase_tension depuis DIAGNOSTIC IMMEDIAT ─────────────────
    phrase_tension: Optional[str] = None
    for line in diagnostic_immediat_raw.splitlines():
        l = line.strip()
        if l.startswith("⚡") or "TENSION" in l.upper():
            phrase_tension = l.replace("⚡", "").replace("TENSION :", "").strip()
            break

    # ── Parse V5 — simulateur décision ──────────────────────────────────────
    simulateur_decision = [
        l.strip()
        for l in simulateur_raw.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]

    # ── Parse V5 — projection temporelle ────────────────────────────────────
    projection_3mois: list[str] = []
    projection_6mois: list[str] = []
    current_proj = None
    for line in projection_raw.splitlines():
        l = line.strip()
        if "3 mois" in l.lower():
            current_proj = "3"
        elif "6 mois" in l.lower():
            current_proj = "6"
        elif l and not l.startswith("#"):
            if current_proj == "3":
                projection_3mois.append(l)
            elif current_proj == "6":
                projection_6mois.append(l)

    # ── Parse V5 — ce qui détruit / leviers ─────────────────────────────────
    ce_qui_detruit = _parse_list(ce_qui_detruit_raw, "🔴")
    leviers_croissance = _parse_list(leviers_raw, "🟢")
    risque_inaction = risque_inaction_raw.strip()

    # ── Parse scores ─────────────────────────────────────────────────────────
    score_rentabilite = score_risque = score_structure = score_liquidite = None
    score_interpretations: dict[str, str] = {}

    def _extract_score(haystack: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*/\s*10", haystack)
        return int(m.group(1)) if m else None

    def _extract_interp(line: str) -> str:
        """Extract text after → on a score line."""
        if "→" in line:
            return line.split("→", 1)[-1].strip()
        return ""

    for line in scores_raw.splitlines():
        ll = line.lower()
        val = _extract_score(line)
        if val is None:
            continue
        interp = _extract_interp(line)
        if "rentabilit" in ll:
            score_rentabilite = val
            if interp:
                score_interpretations["rentabilite"] = interp
        elif "risque" in ll:
            score_risque = val
            if interp:
                score_interpretations["risque"] = interp
        elif "structure" in ll:
            score_structure = val
            if interp:
                score_interpretations["structure"] = interp
        elif "liquidit" in ll:
            score_liquidite = val
            if interp:
                score_interpretations["liquidite"] = interp

    # Second pass: scan the full text if any score is still missing
    if any(s is None for s in [score_rentabilite, score_risque, score_structure]):
        for line in text.splitlines():
            ll = line.lower()
            val = _extract_score(line)
            if val is None:
                continue
            if "rentabilit" in ll and score_rentabilite is None:
                score_rentabilite = val
            elif "risque" in ll and score_risque is None:
                score_risque = val
            elif "structure" in ll and score_structure is None:
                score_structure = val
            elif "liquidit" in ll and score_liquidite is None:
                score_liquidite = val

    # ── Extract verification tag ─────────────────────────────────────────────
    verification_tag = "VERIFIED"
    if text.strip().startswith("[CORRECTED]"):
        verification_tag = "CORRECTED"

    return {
        "type_document": doc_type,
        "score_confiance": score_confiance,
        "resume_executif": resume,
        "diagnostic_revenus": diag_revenus,
        "diagnostic_couts": diag_couts,
        "diagnostic_marges": diag_marges,
        "ce_qui_a_change": ce_qui_a_change,
        "alertes": alertes,
        "problemes_critiques": problemes,
        "opportunites_v3": opportunites,
        "plan_action": plan_action,
        "score_rentabilite": score_rentabilite,
        "score_risque": score_risque,
        "score_structure": score_structure,
        "score_liquidite": score_liquidite,
        "decision": decision,
        "synthese": resume,  # backward compat
        "verification_tag": verification_tag,
        # V5
        "diagnostic_immediat": diagnostic_immediat_raw.strip(),
        "impact_financier": impact_financier,
        "avant_apres_actuel": avant_apres_actuel,
        "avant_apres_apres": avant_apres_apres,
        "avant_apres_gain": avant_apres_gain,
        "simulateur_decision": simulateur_decision,
        "projection_3mois": projection_3mois,
        "projection_6mois": projection_6mois,
        "ce_qui_detruit": ce_qui_detruit,
        "leviers_croissance": leviers_croissance,
        "risque_inaction": risque_inaction,
        "score_interpretations": score_interpretations,
        # V6
        "phrase_tension": phrase_tension,
        "impact_financier_synthese": impact_financier_synthese,
        "plan_action_haute": plan_action_haute,
        "plan_action_secondaire": plan_action_secondaire,
    }


async def _score_analysis(analysis_text: str) -> float:
    """Score the analysis using haiku (~100 tokens). Returns average score 0-10."""
    client = get_anthropic_client()
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system=SCORING_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Évalue cette analyse financière :\n\n{analysis_text[:2000]}"
            }]
        )
        content = message.content[0].text.strip()
        result = json.loads(content)
        return float(result.get("moyenne", 7.0))
    except Exception:
        return 7.0  # Default to passing score on failure


async def call_analysis_v3(
    parsed_data: dict[str, Any],
    industry: str,
    business_model: str,
    memory_section: str = "",
    actions_section: str = "",
    quality_section: str = "",
) -> tuple[str, int, int]:
    """
    Call 1 — Main analysis with claude-sonnet-4-6.
    Returns (analysis_text, input_tokens, output_tokens)
    """
    client = get_anthropic_client()
    user_prompt = _build_user_prompt_call1(
        parsed_data, industry, business_model, memory_section, actions_section, quality_section
    )

    message = client.messages.create(
        system=ANALYSIS_SYSTEM_V3,
        messages=[{"role": "user", "content": user_prompt}],
        **CALL_1_PARAMS,
    )
    text = message.content[0].text.strip()
    return text, message.usage.input_tokens, message.usage.output_tokens


async def call_verification_v3(
    analysis_call1: str,
    parsed_data: dict[str, Any],
) -> str:
    """
    Call 2 — Verification with claude-sonnet-4-6.
    Returns verified/corrected analysis text.
    """
    client = get_anthropic_client()
    user_prompt = _build_user_prompt_call2(analysis_call1, parsed_data)

    message = client.messages.create(
        system=ANALYSIS_SYSTEM_V3,
        messages=[{"role": "user", "content": user_prompt}],
        **CALL_2_PARAMS,
    )
    return message.content[0].text.strip()


async def run_full_pipeline(
    parsed_data: dict[str, Any],
    context: str,
    mode: str = "complete",
    industry: str = "",
    business_model: str = "",
    memory_section: str = "",
    actions_section: str = "",
    quality_section: str = "",
) -> tuple[AnalysisResult, int, float]:
    """
    Run the complete v3 analysis pipeline.
    Returns (AnalysisResult, total_tokens, estimated_cost_euros)
    """
    total_tokens = 0

    # Step 1: Classify document
    doc_type, confidence = await classify_document(parsed_data)
    total_tokens += 300

    # Step 2: Call 1 — Main analysis
    analysis_text, in_tokens, out_tokens = await call_analysis_v3(
        parsed_data,
        industry=industry or context,
        business_model=business_model,
        memory_section=memory_section,
        actions_section=actions_section,
        quality_section=quality_section,
    )
    total_tokens += in_tokens + out_tokens

    # Step 3: Call 2 — Verification (always, both modes)
    verified_text = await call_verification_v3(analysis_text, parsed_data)
    total_tokens += 800  # approx

    # Step 4: Scoring + optional retry
    score = await _score_analysis(verified_text)
    total_tokens += 150

    if score < 8:
        # Retry once
        analysis_text2, in2, out2 = await call_analysis_v3(
            parsed_data,
            industry=industry or context,
            business_model=business_model,
            memory_section=memory_section,
            actions_section=actions_section,
            quality_section=quality_section,
        )
        total_tokens += in2 + out2
        verified_text2 = await call_verification_v3(analysis_text2, parsed_data)
        total_tokens += 800
        score2 = await _score_analysis(verified_text2)
        total_tokens += 150
        if score2 >= score:
            verified_text = verified_text2

    # Step 5: Clean audit artefacts, then parse
    verified_text = _clean_verified_text(verified_text)
    analysis_dict = _parse_v3_text(verified_text, doc_type, confidence)

    # Cost estimate (USD, converted to EUR ≈ ×0.92):
    # claude-opus-4-6:   $15/M input, $75/M output  (Call 1)
    # claude-sonnet-4-6: $3/M input,  $15/M output  (Call 2)
    # claude-haiku-4-5:  $0.25/M input, $1.25/M output (classification + scoring)
    haiku_tokens = 600
    sonnet_call2_tokens = 800
    cost_usd = (
        haiku_tokens * 0.25 / 1_000_000
        + in_tokens * 15 / 1_000_000
        + out_tokens * 75 / 1_000_000
        + sonnet_call2_tokens * 3 / 1_000_000
    )
    cost = cost_usd * 0.92  # USD → EUR

    try:
        result = AnalysisResult(**{
            k: v for k, v in analysis_dict.items()
            if k in AnalysisResult.model_fields
        })
    except Exception:
        result = AnalysisResult(
            type_document=doc_type,
            score_confiance=confidence,
            synthese=analysis_dict.get("resume_executif", "Analyse effectuée avec succès."),
        )

    # Attach v3 extra fields as extra attributes (returned in dict for the route)
    result.__dict__.update({k: v for k, v in analysis_dict.items()})

    return result, total_tokens, round(cost, 4)


def _fallback_parse(content: str, doc_type: str) -> dict[str, Any]:
    """Fallback when JSON parsing fails."""
    return {
        "type_document": doc_type,
        "score_confiance": 50,
        "synthese": content[:500] if content else "Analyse effectuée.",
        "recommandations": [
            {
                "priorite": "moyenne",
                "action": "Relancez l'analyse avec un fichier mieux structuré pour obtenir des résultats détaillés.",
                "impact_estime": "Amélioration de la qualité d'analyse",
                "delai": "Immédiat"
            }
        ]
    }


# ─── Chat intelligence ───────────────────────────────────────────────────────

_COMPLEX_CHAT_KEYWORDS = [
    "projette", "prévision", "forecast", "budget", "stratégie", "plan financier",
    "dcf", "valorisation", "rachat", "fusion", "acquisition", "levée de fonds",
    "restructur", "trésorerie à", "flux de trésorerie", "modèle financier",
    "analyse sectorielle", "benchmark", "risque de crédit", "covenant",
    "multiple", "ebitda", "ebita", "wacc", "coût du capital",
]

_SIMPLE_CHAT_THRESHOLD = 120  # words


def detect_chat_complexity(message: str) -> str:
    """
    Detect whether a chat message requires Opus (complex) or Sonnet (simple).
    Returns 'opus' or 'sonnet'.
    Complex = long message OR contains strategic/analytical keywords.
    """
    word_count = len(message.split())
    lower = message.lower()

    if word_count >= _SIMPLE_CHAT_THRESHOLD:
        return "opus"

    for kw in _COMPLEX_CHAT_KEYWORDS:
        if kw in lower:
            return "opus"

    return "sonnet"


async def call_chat_intelligent(
    message: str,
    analysis_context: str,
    history: list[dict] | None = None,
    model_tier: str = "normal",
) -> tuple[str, str]:
    """
    Route chat message to Sonnet or Opus based on complexity + model_tier.
    model_tier: 'normal' → auto-detect | 'downgraded' → force Sonnet

    Returns (response_text, model_used)
    """
    client = get_anthropic_client()

    if model_tier == "downgraded":
        model = "claude-sonnet-4-6"
    else:
        complexity = detect_chat_complexity(message)
        model = "claude-opus-4-6" if complexity == "opus" else "claude-sonnet-4-6"

    system = CHAT_SYSTEM
    if analysis_context:
        system += f"\n\nCONTEXTE DE L'ANALYSE EN COURS :\n{analysis_context[:3000]}"

    messages = list(history or [])
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model=model,
        max_tokens=800,
        system=system,
        messages=messages,
    )

    return response.content[0].text.strip(), model
