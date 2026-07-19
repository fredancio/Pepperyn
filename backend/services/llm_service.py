"""
LLM service — Pepperyn v4 pipeline using Anthropic Claude.

Architecture v4 :
  Step 1: Pre-processing (Python/pandas — 0 tokens)
  Step 2: Classification     (Haiku   — ~200 tokens, toujours)
  Step 3: Analyse Call 1     (Sonnet  — défaut │ Opus en escalade)
  Step 4: Vérification Call 2 (même modèle que Call 1)
  Step 5: Scoring             (Haiku  — ~100 tokens, escalade Opus si score < 8)
  Step 6: Exports             (Python — 0 tokens)

Model Router :
  Haiku   → classification, scoring                         ($0.25/$1.25 /M)
  Sonnet  → analyse par défaut (FREE / PRO / POWER)         ($3/$15 /M)
  Opus    → escalade SCALE ou volume élevé (>10k chars)
            ou qualité < 8 sur premier essai                 ($15/$75 /M)

Chat :
  Sonnet  → toujours, max 500 tokens
  Haiku et Opus ne sont jamais utilisés pour le chat.

Coût estimé :
  Sonnet path : ~0.05€/analyse · ~0.002€/message
  Opus   path : ~0.30€/analyse (plan SCALE ou escalade qualité)
"""
import json
import logging
import os
import re
from typing import Any, Optional

import anthropic

from models.schemas import AnalysisResult

logger = logging.getLogger(__name__)

# ─── Modèles disponibles ─────────────────────────────────────────────────────
# IMPORTANT : ces constantes DOIVENT être définies AVANT toute fonction qui les
# utilise comme valeur par défaut d'argument (Python évalue les defaults à l'import).

MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS   = "claude-opus-4-6"

# Plans qui reçoivent systématiquement Opus (quelle que soit la taille des données)
_OPUS_PLANS = {"scale"}

# Seuil de volume de données déclenchant l'escalade Opus (caractères JSON)
_OPUS_DATA_THRESHOLD = 10_000

# Tarifs tokens ($/M) — pour le calcul de coût
_PRICE_IN  = {MODEL_HAIKU: 0.25,  MODEL_SONNET: 3.0,  MODEL_OPUS: 15.0}
_PRICE_OUT = {MODEL_HAIKU: 1.25,  MODEL_SONNET: 15.0, MODEL_OPUS: 75.0}

# Paramètres fixes Call 1 / Call 2
CALL_1_BASE = {"temperature": 0.2, "max_tokens": 5500}
CALL_2_BASE = {"temperature": 0.2, "max_tokens": 4000}


# ─── Termes interdits — RÈGLE ABSOLUE N°4 ────────────────────────────────────
# Chaque clé = terme interdit. Valeur = remplacement démontrable.
_FORBIDDEN_TERMS: dict[str, str] = {
    "crise imminente":          "risque identifié",
    "point de non-retour":      "seuil d'alerte critique",
    "le cash brûle":            "la trésorerie se dégrade",
    "cash qui brûle":           "trésorerie en dégradation",
    "catastrophe":              "situation critique",
    "spirale":                  "dégradation continue",
    "croissance exponentielle": "forte croissance (à chiffrer)",
    "destruction exponentielle":"forte destruction de valeur (à chiffrer)",
    "pipeline commercial":      "carnet de commandes",
    "preuve d'un pipeline":     "indicateur du carnet de commandes",
    "trésorerie épuisée":       "trésorerie insuffisante",
    "risque certain":           "risque probable",
    "rupture certaine":         "risque de rupture",
    "faillite probable":        "risque de défaut de paiement",
}


def _apply_forbidden_terms(text: str) -> str:
    """Remplace automatiquement les termes interdits (RÈGLE N°4).
    Appliqué en post-processing sur le texte final avant parsing.
    Case-insensitive sur les termes mais conserve la casse du remplacement.
    """
    result = text
    for forbidden, replacement in _FORBIDDEN_TERMS.items():
        import re as _re
        result = _re.sub(
            _re.escape(forbidden),
            replacement,
            result,
            flags=_re.IGNORECASE,
        )
    return result


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

RÈGLES D'AUDIT (niveau cabinet PwC/McKinsey) :

RÈGLE 1 — ZÉRO INVENTION :
- Tu n'as PAS le droit de compléter des informations absentes.
- Tu n'as PAS le droit de transformer une probabilité en certitude.
- Si une donnée n'est pas présente dans les données fournies ET dans la liste des données absentes de l'Evidence Graph : écrire "Données insuffisantes." Rien d'autre.

RÈGLE 2 — CATÉGORISATION STRICTE :
Chaque affirmation appartient à UNE seule catégorie, exclusivement :
[OBS] Observation : fait directement lisible. Ex: "Septembre = 0 € de CA."
[DED] Déduction : calcul démontrable. Ex: "CA baisse de 33 % entre Jan et Août."
[HYP] Hypothèse : explication possible, JAMAIS une certitude. Toujours conditionnel : "pourrait", "semble", "peut indiquer".
[REC] Recommandation : action proposée, TOUJOURS conditionnelle. JAMAIS basée sur une seule hypothèse.
[SIM] Simulation : projection, TOUJOURS annoncée comme telle. Jamais présentée comme certitude.

RÈGLE 3 — JUSTIFICATION OBLIGATOIRE :
Chaque recommandation doit pouvoir répondre à : Pourquoi ? Sur quelles données ? Quel calcul ? Quel niveau de confiance ?
Si une de ces réponses est absente → supprimer la recommandation.

RÈGLE 4 — TERMES INTERDITS (remplacer systématiquement) :
"crise imminente" → "risque identifié" | "point de non-retour" → "seuil d'alerte critique"
"le cash brûle" → "la trésorerie se dégrade" | "catastrophe" → "situation critique"
"spirale" → "dégradation continue" | "trésorerie épuisée" → "trésorerie insuffisante"
"risque certain" → "risque probable" | "rupture certaine" → "risque de rupture"
"faillite probable" → "risque de défaut de paiement"
"croissance/destruction exponentielle" → chiffrer précisément ou supprimer

RÈGLE 5 — UNE DONNÉE, UNE SEULE FORME :
Si "données de cash indisponibles" → interdit d'écrire "la trésorerie sera insuffisante" plus loin.
Si une valeur est "Données insuffisantes" en section X → elle est "Données insuffisantes" partout.

RÈGLE 7 — HYPOTHÈSE UNIQUE INTERDITE :
Face à une observation inattendue (ex: mois à 0 €), toujours proposer plusieurs interprétations possibles
(prestations non réalisées / retard facturation / erreur comptable / activité arrêtée…)
avant de proposer une action. L'action est conditionnelle à la cause confirmée.

TA MISSION :
Le dirigeant lit ce rapport et comprend en 5 secondes :
→ Quel est son problème exact
→ Ce qu'il doit faire maintenant
→ Ce qu'il risque s'il n'agit pas

DONNÉES :
- Tu travailles UNIQUEMENT à partir des données fournies ET de l'Evidence Graph si fourni.
- Tu n'inventes JAMAIS de chiffres ni d'informations.
- Si une donnée est dans l'Evidence Graph comme "disponible" → tu DOIS l'utiliser, jamais l'ignorer.
- Si une donnée est dans l'Evidence Graph comme "absente" → écrire "Données insuffisantes".
- Si aucun Evidence Graph n'est fourni → appliquer les mêmes règles sur les données brutes.

Tu respectes STRICTEMENT le format demandé."""

CHAT_SYSTEM = """Tu es Pepperyn, directeur financier en mission conseil de haut niveau.

Règles de communication :
- Réponses courtes et directes. 3 à 6 phrases maximum, sauf si une analyse structurée est explicitement demandée.
- ZÉRO emoji. Jamais. Aucun caractère emoji dans les réponses. Sans exception.
- ZÉRO hashtag (#, ##, ###). Jamais de titres markdown. Jamais.
- ZÉRO astérisque (* ou **). Jamais de gras ou italique markdown.
- Pas de listes à puces systématiques. Si tu listes, utilise des tirets simples (-) uniquement quand c'est indispensable.
- Tu vas droit au fait. Si la réponse tient en deux phrases, elle tient en deux phrases.
- Ton niveau : CFO ou associé senior en cabinet de conseil stratégique.
- INTERDIT de te présenter ou de rappeler qui tu es : jamais "Je suis Pepperyn", jamais "En tant qu'assistant financier", jamais "Mon rôle est de". L'utilisateur sait qui tu es.
- Jamais d'introduction ("Bien sûr", "Voici", "En tant que..."). Tu commences directement par la réponse.
- Si la question dépasse les données de l'analyse, dis-le en une phrase — sans reformuler la question, sans proposer des alternatives génériques.

Tu travailles uniquement à partir des données de l'analyse fournie.
Si une information est absente des données, tu le dis en une phrase, sans développement.
Si l'utilisateur demande comment structurer ou améliorer son fichier Excel, conseille-lui de consulter le guide disponible à /guide-donnees — mentionne que ce guide explique la structure idéale (P&L mensuel, bilan, nomenclature des lignes) et donne des prompts Copilot/ChatGPT pour restructurer son fichier.
Tu réponds exclusivement en français."""

SCORING_SYSTEM = """Tu es un évaluateur d'analyses financières. Score l'analyse sur 4 critères de 0 à 10 :
1. Clarté : est-ce compréhensible en 10 secondes ?
2. Pertinence : est-ce que ça dit quelque chose d'utile ?
3. Actionnabilité : est-ce qu'on peut agir ?
4. Crédibilité : est-ce que ça paraît fiable ?

Retourne UNIQUEMENT un JSON : {"scores": [X, X, X, X], "moyenne": X.X}
Ne donne aucune explication."""

# ─── Enhanced pipeline — system prompts ──────────────────────────────────────
# Activés uniquement quand USE_ENHANCED_PIPELINE=true.
# N'affectent pas le pipeline par défaut (ANALYSIS_SYSTEM_V3 reste intact).

ENHANCED_ANALYSIS_SYSTEM = """Tu es un expert en finance d'entreprise opérationnelle. Tu aides les dirigeants à prendre des décisions immédiates.

TON STYLE — RÈGLES ABSOLUES :
- Tu écris comme un expert qui DÉCIDE, pas un consultant qui DÉCRIT.
- Phrases COURTES. Maximum 15 mots par phrase.
- Verbes d'action : agis, réduis, coupe, accélère, stoppe, renégocie, fixe, mesure.
- Ton DIRECT : interdit "il semble que", "on pourrait considérer", "il convient de".
- Exprime la gravité sans filtre : si c'est critique → "C'est critique."
- Zéro nuance inutile. Chaque mot sert la décision.
- INTERDIT : "accuse un déficit", "présente des marges", "montre des signes". Utilise : "est", "perd", "risque", "doit".

RÈGLES D'AUDIT (niveau cabinet PwC/McKinsey — identiques au système de base) :

RÈGLE 1 — ZÉRO INVENTION : Aucun chiffre inventé. Aucune hypothèse présentée comme fait.
Si une donnée est dans l'Evidence Graph comme "disponible" → la UTILISER obligatoirement.
Si une donnée est dans l'Evidence Graph comme "absente" → "Données insuffisantes". Rien d'autre.

RÈGLE 2 — CATÉGORISATION STRICTE :
[OBS] Observation (fait lisible) | [DED] Déduction (calcul) | [HYP] Hypothèse (possible, jamais certain)
[REC] Recommandation (conditionnelle, jamais sur hypothèse unique) | [SIM] Simulation (projection annoncée)

RÈGLE 4 — TERMES INTERDITS :
"crise imminente"→"risque identifié" | "catastrophe"→"situation critique" | "spirale"→"dégradation continue"
"le cash brûle"→"la trésorerie se dégrade" | "trésorerie épuisée"→"trésorerie insuffisante"
"risque certain"→"risque probable" | "rupture certaine"→"risque de rupture"

RÈGLE 5 — UNE SEULE FORME PAR DONNÉE :
"Données insuffisantes" en section X → obligatoirement "Données insuffisantes" partout.

RÈGLE 7 — HYPOTHÈSE UNIQUE INTERDITE :
Devant toute observation inattendue → proposer plusieurs interprétations → action conditionnelle.

RÈGLES DE RIGUEUR SUPPLÉMENTAIRES :
1. Tu ne dois jamais inventer de chiffre.
2. Tu distingues clairement : faits constatés / hypothèses / recommandations.
3. Toute conclusion doit être reliée à un KPI ou une donnée fournie dans les données sources.
4. Tu ne proposes jamais une action non soutenue par les données disponibles.
5. Si une pré-analyse stratégique est fournie dans le prompt, tu l'intègres.

TA MISSION :
Le dirigeant lit ce rapport et comprend en 5 secondes :
→ Quel est son problème exact
→ Ce qu'il doit faire maintenant
→ Ce qu'il risque s'il n'agit pas

Tu respectes STRICTEMENT le format demandé."""

FINANCIAL_ANALYST_SYSTEM = """Tu es l'analyste financier senior de Pepperyn.

Ta mission : analyser les données financières fournies et identifier les faits financiers clés.

RÈGLES ABSOLUES :
1. Tu n'inventes jamais de chiffre.
2. Tu ne recalcules pas les KPI — tu interprètes uniquement ce qui est explicitement dans les données.
3. Chaque constat doit citer le KPI ou la donnée source utilisée.
4. Si une information est absente des données, tu l'indiques.
5. Tu ne rédiges pas le rapport final — tu produis une analyse structurée intermédiaire.

Retourne UNIQUEMENT un JSON valide, sans texte avant ni après."""

STRATEGIC_CFO_SYSTEM = """Tu es le CFO stratégique de Pepperyn.

Tu reçois une analyse financière structurée produite par un analyste senior.
Ta mission : transformer ces constats en décisions exécutives priorisées.

RÈGLES ABSOLUES :
1. Tu ne refais pas l'analyse financière.
2. Tu utilises uniquement les constats fournis par l'analyste.
3. Tu n'inventes jamais de chiffre.
4. Chaque décision doit être reliée à un constat source explicite.
5. Tes recommandations sont concrètes, priorisées et actionnables immédiatement.

Tu raisonnes en dirigeant : Que faut-il décider ? Dans quel ordre ? Avec quel risque d'inaction ?

Retourne UNIQUEMENT un JSON valide, sans texte avant ni après."""


# ─── Evidence Graph — RÈGLE ABSOLUE N°6 ─────────────────────────────────────
# Chaque affirmation du rapport est reliée à sa source avant toute rédaction.
# Séparation stricte analyse ↔ présentation.

EVIDENCE_GRAPH_SYSTEM = """Tu es l'agent de traçabilité financière de Pepperyn.

Ta SEULE mission : construire un Evidence Graph — l'inventaire exhaustif de tous les faits financiers directement traçables dans les données fournies.

RÈGLES ABSOLUES :
1. Tu ne produis que des faits directement lisibles dans les données. Zéro invention.
2. Chaque fait cite sa source : nom de la feuille + contexte de ligne/colonne.
3. Si une donnée est absente de TOUTES les feuilles : tu la déclares dans "unavailable_data" avec la raison.
4. Tu DOIS vérifier toutes les feuilles listées dans "all_sheets_manifest" avant de déclarer une donnée absente.
5. Chaque fait appartient à UNE seule catégorie :
   - "observation" : fait directement lisible dans une cellule
   - "deduction"   : calcul mathématique démontrable à partir de faits observés
   Ne produis JAMAIS d'hypothèses ni de recommandations dans cet inventaire.

Retourne UNIQUEMENT un JSON valide, sans texte avant ni après."""

COHERENCE_AUDIT_RULES = """
AUDIT DE COHÉRENCE OBLIGATOIRE (RÈGLE ABSOLUE N°11) :
Avant de retourner le rapport corrigé, vérifie impérativement :

✓ Aucune contradiction entre les sections (ex : "données absentes" → interdit si la donnée est dans une autre section)
✓ Aucun chiffre présent dans le rapport qui n'existe pas dans les données sources
✓ Score confiance conclusions ≤ min(qualité technique, complétude données) — jamais supérieur
✓ Zéro terme interdit restant :
   - "crise imminente" → "risque identifié"
   - "point de non-retour" → "seuil d'alerte critique"
   - "le cash brûle" → "la trésorerie se dégrade"
   - "catastrophe" → "situation critique"
   - "spirale" → "dégradation continue"
   - "trésorerie épuisée" → "trésorerie insuffisante"
   - "risque certain" → "risque probable"
   - "rupture certaine" → "risque de rupture"
   - "faillite probable" → "risque de défaut de paiement"
   - "croissance exponentielle" → chiffrer ou supprimer
   - "destruction exponentielle" → chiffrer ou supprimer
✓ Toute recommandation répond à : Pourquoi ? Sur quelles données ? Quel calcul ?
✓ Chaque recommandation envisage plusieurs causes possibles (jamais hypothèse unique → action)
✓ Si une donnée a été annoncée absente dans une section → elle DOIT être absente dans TOUTES les sections
✓ Les scores Rentabilité / Risque / Structure / Liquidité sont cohérents avec les données numériques

Si une incohérence est détectée : la corriger silencieusement (le lecteur ne doit pas savoir).
"""

AUDIT_CATEGORIZATION_RULES = """
CATÉGORISATION STRICTE DES AFFIRMATIONS (RÈGLE ABSOLUE N°2) :
Chaque affirmation appartient à UNE seule catégorie — elles sont exclusives.

[OBS] Observation — Fait directement observable dans les données.
      Exemple : "Septembre = 0 € de chiffre d'affaires."
      Jamais : "Ce qui montre que..." (cela devient une déduction)

[DED] Déduction — Conclusion mathématique démontrable.
      Exemple : "Le CA diminue de 33 % entre janvier et août."
      Doit inclure le calcul ou les sources.

[HYP] Hypothèse — Explication possible. JAMAIS une certitude.
      Exemple : "Ce mois sans CA pourrait correspondre à un retard de facturation."
      Jamais : "Les factures n'ont pas été émises."
      Toujours conditionnel : "pourrait", "semble", "peut indiquer".

[REC] Recommandation — Action proposée. TOUJOURS conditionnelle à une [HYP] explicite.
      Format OBLIGATOIRE : "Si [hypothèse] → [action recommandée]"
      Exemple ✓ : "Si des prestations ont été réalisées en septembre sans être facturées → émettre les factures."
      Exemple ✗ : "Émettre les factures de septembre." (certitude non démontrée — INTERDIT)
      RÈGLE : plusieurs causes possibles doivent être envisagées avant toute [REC] unique.
      Une [REC] sans [HYP] explicite préalable est une erreur de catégorisation.

[SIM] Simulation — Projection. TOUJOURS annoncée comme simulation.
      Jamais présentée comme une prévision certaine.

INTERDICTION ABSOLUE de mélanger les catégories dans une même phrase.
"""


async def _run_evidence_graph_agent(
    parsed_data: dict[str, Any],
    model: str = MODEL_SONNET,
) -> dict[str, Any]:
    """
    Agent Evidence Graph — pré-processing avant analyse principale.

    Construit l'inventaire de tous les faits financiers traçables.
    Chaque fait est lié à sa source (feuille, contexte, calcul, confiance).
    Retourne {} en cas d'échec (non-bloquant).

    Format retourné :
    {
      "facts": [{"id", "category", "claim", "source_sheet",
                 "source_context", "calculation", "confidence"}],
      "unavailable_data": [{"data", "reason"}],
      "sheets_verified": [...],
    }
    """
    client = get_anthropic_client()
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:10000]

    # Extraire le manifeste des feuilles si disponible
    manifest = parsed_data.get("all_sheets_manifest", {})
    sheets_info = ""
    if manifest:
        parsed_sheets = manifest.get("sheets_parsed_in_detail", [])
        not_parsed = manifest.get("sheets_present_but_not_parsed", [])
        sheets_info = (
            f"\nFEUILLES ANALYSÉES EN DÉTAIL : {parsed_sheets}\n"
            f"FEUILLES PRÉSENTES MAIS NON PARSÉES : {not_parsed}\n"
            "Tu DOIS vérifier les deux listes avant de déclarer une donnée absente.\n"
        )

    user_prompt = f"""Construis l'Evidence Graph de ce classeur financier.
{sheets_info}
DONNÉES :
{data_summary}

Retourne UNIQUEMENT ce JSON (sans texte avant ni après) :
{{
  "facts": [
    {{
      "id": "F001",
      "category": "observation",
      "claim": "CA total exercice = X €",
      "source_sheet": "Nom de la feuille",
      "source_context": "Ligne 'Total CA', colonne 'Total annuel', valeur = X",
      "calculation": "Lecture directe",
      "confidence": 1.0
    }},
    {{
      "id": "F002",
      "category": "deduction",
      "claim": "Baisse CA de X% entre période A et période B",
      "source_sheet": "Nom de la feuille",
      "source_context": "CA période A = X, CA période B = Y",
      "calculation": "(Y - X) / X = Z%",
      "confidence": 1.0
    }}
  ],
  "unavailable_data": [
    {{
      "data": "Nom de la donnée manquante",
      "reason": "Aucune feuille ne contient cette information après vérification complète"
    }}
  ],
  "sheets_verified": ["liste des feuilles effectivement vérifiées"]
}}

RÈGLES STRICTES :
- Produis uniquement des faits directement lisibles dans les données (observation) ou calculables (déduction).
- Chaque montant cité dans "claim" doit être présent dans "source_context".
- Si une donnée n'est pas trouvée après vérification de toutes les feuilles : la déclarer dans "unavailable_data".
- Maximum 20 faits. Priorise les KPI les plus importants (CA, marges, trésorerie, bilan)."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.0,
            system=EVIDENCE_GRAPH_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = message.content[0].text.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.warning("[EVIDENCE GRAPH] Agent failed: %s", e)
    return {}


def _format_evidence_graph_for_prompt(evidence_graph: dict[str, Any]) -> str:
    """
    Formate l'Evidence Graph pour injection dans Call 1.
    Fournit au LLM la liste des faits traçables qu'il peut utiliser.
    Tout chiffre dans le rapport DOIT provenir d'un fait de cet inventaire.
    """
    if not evidence_graph:
        return ""

    facts = evidence_graph.get("facts") or []
    unavailable = evidence_graph.get("unavailable_data") or []
    sheets_verified = evidence_graph.get("sheets_verified") or []

    lines = [
        "# EVIDENCE GRAPH — SOURCE DE VÉRITÉ UNIQUE (RÈGLE ABSOLUE N°6)",
        "Tous les chiffres du rapport DOIVENT provenir de cet inventaire.",
        "Interdiction d'utiliser un montant qui n'y figure pas.",
        f"Feuilles vérifiées : {sheets_verified}",
        "",
    ]

    if facts:
        lines.append("## FAITS TRAÇABLES (utilisables dans le rapport) :")
        for f in facts[:20]:
            cat = f.get("category", "?").upper()
            lines.append(
                f"[{cat}] {f.get('id', '?')} — {f.get('claim', '')} "
                f"| Source : {f.get('source_sheet', '?')} — {f.get('source_context', '')} "
                f"| Calcul : {f.get('calculation', 'Lecture directe')} "
                f"| Confiance : {f.get('confidence', 1.0):.0%}"
            )

    if unavailable:
        lines.append("\n## DONNÉES RÉELLEMENT ABSENTES (après vérification de toutes les feuilles) :")
        for u in unavailable:
            lines.append(f"❌ {u.get('data', '?')} — {u.get('reason', '')}")
        lines.append(
            "⚠️ Ces données sont les SEULES que tu peux déclarer 'Données insuffisantes'."
            " Toute autre donnée présente dans les faits ci-dessus DOIT être utilisée."
        )

    lines.append("\n---")
    return "\n".join(lines)


def _format_evidence_graph_for_audit(evidence_graph: dict[str, Any]) -> str:
    """
    Formate l'Evidence Graph pour Call 2 (audit de cohérence).
    Fournit la liste des montants autorisés pour validation croisée.
    """
    if not evidence_graph:
        return ""

    facts = evidence_graph.get("facts") or []
    unavailable = evidence_graph.get("unavailable_data") or []

    lines = [
        "EVIDENCE GRAPH — RÉFÉRENCE D'AUDIT :",
        "Vérifie que chaque chiffre du rapport correspond à un fait ci-dessous.",
    ]
    for f in facts[:20]:
        lines.append(f"• {f.get('claim', '')} [{f.get('source_sheet', '?')}]")

    unavail_labels = [u.get("data", "") for u in unavailable]
    if unavail_labels:
        lines.append(f"Données réellement absentes : {unavail_labels}")
        lines.append(
            "⚠️ Si le rapport dit 'Données insuffisantes' pour une donnée NON listée ci-dessus,"
            " c'est une erreur — corriger."
        )
    return "\n".join(lines)


def _select_analysis_model(plan_tier: str, parsed_data: dict) -> str:
    """
    Sélectionne le modèle d'analyse :
      - Opus  si plan SCALE ou volume données > 10 000 chars
      - Sonnet sinon (défaut)
    L'escalade qualité (score < 8) est gérée dans run_full_pipeline.
    """
    if (plan_tier or "").strip().lower() in _OPUS_PLANS:
        return MODEL_OPUS
    if len(json.dumps(parsed_data, ensure_ascii=False)) > _OPUS_DATA_THRESHOLD:
        return MODEL_OPUS
    return MODEL_SONNET


def _use_enhanced_pipeline() -> bool:
    """Feature flag — active le pipeline enrichi Agents 5+6 (Financial Analyst + Strategic CFO).
    Activé via variable d'environnement USE_ENHANCED_PIPELINE=true sur Railway.
    Par défaut désactivé pour préserver le comportement existant.
    """
    return os.getenv("USE_ENHANCED_PIPELINE", "false").lower() == "true"


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


# ─── Enhanced pipeline — Agents 5 + 6 ───────────────────────────────────────

async def _run_financial_analyst_prep(
    parsed_data: dict[str, Any],
    model: str = MODEL_SONNET,
) -> dict[str, Any]:
    """
    Agent 5 — Financial Analyst pre-pass.
    Analyse les données financières et produit des constats structurés.
    Non-bloquant : retourne {} en cas d'échec.
    """
    client = get_anthropic_client()
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:8000]

    user_prompt = f"""Analyse ces données financières et produis un JSON structuré de tes constats.

DONNÉES :
{data_summary}

Retourne UNIQUEMENT ce JSON (sans texte avant ni après) :
{{
  "constats_cles": [
    {{"constat": "...", "donnee_source": "...", "severite": "critique|élevé|moyen|faible"}}
  ],
  "analyse_marges": {{
    "tendance": "dégradation|stable|amélioration",
    "facteur_principal_destruction": "...",
    "levier_principal_creation": "..."
  }},
  "analyse_tresorerie": {{
    "situation": "critique|tendue|correcte|confortable",
    "risque_principal": "...",
    "horizon_alerte": "..."
  }},
  "risques_majeurs": ["...", "..."],
  "opportunites_immediates": ["...", "..."],
  "donnees_manquantes": ["..."]
}}"""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1200,
            temperature=0.1,
            system=FINANCIAL_ANALYST_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = message.content[0].text.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.warning("[ENHANCED PIPELINE] Financial analyst prep failed: %s", e)
    return {}


async def _run_strategic_cfo_prep(
    analyst_findings: dict[str, Any],
    model: str = MODEL_SONNET,
) -> dict[str, Any]:
    """
    Agent 6 — Strategic CFO pre-pass.
    Transforme les constats financiers en décisions exécutives priorisées.
    Non-bloquant : retourne {} en cas d'échec.
    """
    if not analyst_findings:
        return {}

    client = get_anthropic_client()
    findings_json = json.dumps(analyst_findings, ensure_ascii=False, indent=1)[:3000]

    user_prompt = f"""Tu reçois l'analyse financière d'un analyste senior.
Transforme ces constats en décisions exécutives priorisées.

ANALYSE FINANCIÈRE :
{findings_json}

Retourne UNIQUEMENT ce JSON (sans texte avant ni après) :
{{
  "tension_strategique": "1 phrase — le problème central que le dirigeant doit résoudre",
  "top_3_decisions": [
    {{
      "decision": "...",
      "justification": "...",
      "urgence": "immédiate|30j|60j|90j",
      "impact_attendu": "...",
      "constat_source": "..."
    }}
  ],
  "risque_inaction": "1 phrase chiffrée si possible — conséquence concrète si aucune action dans les 90 jours",
  "quick_wins": [
    {{
      "action": "...",
      "roi_estime": "...",
      "effort": "faible|moyen|élevé",
      "delai": "..."
    }}
  ],
  "plan_30_jours": ["action 1", "action 2", "action 3"]
}}"""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.2,
            system=STRATEGIC_CFO_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = message.content[0].text.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.warning("[ENHANCED PIPELINE] Strategic CFO prep failed: %s", e)
    return {}


def _build_pre_analysis_section(
    analyst_findings: dict[str, Any],
    cfo_findings: dict[str, Any],
) -> str:
    """
    Formate le bloc de pré-analyse à injecter dans le prompt Call 1.
    Retourne une chaîne vide si les deux inputs sont vides.
    """
    if not analyst_findings and not cfo_findings:
        return ""

    lines = [
        "# PRÉ-ANALYSE STRATÉGIQUE",
        "Ce bloc a été produit par un analyste financier et un CFO virtuel qui ont déjà traité les données.",
        "Tu DOIS intégrer ces constats dans ton rapport. Ne les contredis pas sauf erreur manifeste dans les données sources.",
        "",
    ]

    if analyst_findings:
        constats = analyst_findings.get("constats_cles") or []
        if constats:
            lines.append("## CONSTATS FINANCIERS CLÉS :")
            for c in constats[:5]:
                sev = c.get("severite", "")
                lines.append(
                    f"- [{sev.upper()}] {c.get('constat', '')} (source : {c.get('donnee_source', '')})"
                )

        risques = analyst_findings.get("risques_majeurs") or []
        if risques:
            lines.append("\n## RISQUES IDENTIFIÉS :")
            for r in risques[:3]:
                lines.append(f"- {r}")

        opps = analyst_findings.get("opportunites_immediates") or []
        if opps:
            lines.append("\n## OPPORTUNITÉS IMMÉDIATES :")
            for o in opps[:3]:
                lines.append(f"- {o}")

    if cfo_findings:
        tension = cfo_findings.get("tension_strategique")
        if tension:
            lines.append(f"\n## TENSION STRATÉGIQUE :\n{tension}")

        decisions = cfo_findings.get("top_3_decisions") or []
        if decisions:
            lines.append("\n## TOP 3 DÉCISIONS EXÉCUTIVES (à intégrer dans le plan d'action) :")
            for i, d in enumerate(decisions[:3], 1):
                urgency = d.get("urgence", "")
                lines.append(
                    f"{i}. [{urgency.upper()}] {d.get('decision', '')} "
                    f"— {d.get('impact_attendu', '')} "
                    f"(justification : {d.get('justification', '')})"
                )

        ri = cfo_findings.get("risque_inaction")
        if ri:
            lines.append(f"\n## RISQUE D'INACTION :\n{ri}")

        qw = cfo_findings.get("quick_wins") or []
        if qw:
            lines.append("\n## QUICK WINS IDENTIFIÉS :")
            for w in qw[:3]:
                lines.append(
                    f"- {w.get('action', '')} | ROI : {w.get('roi_estime', '?')} "
                    f"| Délai : {w.get('delai', '?')} | Effort : {w.get('effort', '?')}"
                )

    lines.append("\n---")
    return "\n".join(lines)


def _format_cfo_for_reviewer(cfo_findings: dict[str, Any]) -> str:
    """
    Formate les décisions CFO en texte court pour le Skeptical Reviewer (Call 2).
    Retourne une chaîne vide si cfo_findings est vide.
    """
    if not cfo_findings:
        return ""

    lines = []
    tension = cfo_findings.get("tension_strategique")
    if tension:
        lines.append(f"Tension principale : {tension}")

    decisions = cfo_findings.get("top_3_decisions") or []
    if decisions:
        lines.append("Décisions prioritaires validées :")
        for d in decisions[:3]:
            lines.append(
                f"  • [{d.get('urgence', '?').upper()}] {d.get('decision', '')} "
                f"— {d.get('justification', '')}"
            )

    ri = cfo_findings.get("risque_inaction")
    if ri:
        lines.append(f"Risque d'inaction : {ri}")

    return "\n".join(lines)


def _build_user_prompt_call1(
    parsed_data: dict[str, Any],
    industry: str,
    business_model: str,
    memory_section: str,
    actions_section: str,
    quality_section: str = "",
    relation_section: str = "",
    pre_analysis_section: str = "",
    evidence_graph_section: str = "",
) -> str:
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:14000]

    # ── RÈGLE N°10 : manifeste complet des feuilles injecté en premier ────────
    manifest = parsed_data.get("all_sheets_manifest", {})
    manifest_note = ""
    if manifest:
        note = manifest.get("audit_note", "")
        not_parsed = manifest.get("sheets_present_but_not_parsed", [])
        if note:
            manifest_note = (
                f"\n⚠️ MANIFESTE FEUILLES (RÈGLE N°10) :\n{note}\n"
                f"INTERDICTION de déclarer une donnée absente si elle pourrait se trouver"
                f" dans les feuilles non parsées : {not_parsed}\n"
            )

    # ── Note bilan_summary ────────────────────────────────────────────────────
    bilan_note = ""
    bilan_summary = parsed_data.get("bilan_summary", {})
    if bilan_summary:
        lines = [
            f"  → {kpi.replace('_', ' ').title()} : {v['value']:,.0f} € (feuille « {v['sheet']} »)"
            for kpi, v in bilan_summary.items()
        ]
        bilan_note = (
            "\n📊 BILAN — DONNÉES EXTRAITES DIRECTEMENT DU FICHIER :\n"
            + "\n".join(lines)
            + "\nCes valeurs sont GARANTIES par extraction directe. Utilise-les pour la section # BILAN INTELLIGENCE.\n"
        )

    prompt = f"""Voici des données financières extraites d'un fichier utilisateur :

CONTEXTE BUSINESS
- Secteur : {industry or 'Non précisé'}
- Modèle : {business_model or 'Non précisé'}
{manifest_note}{bilan_note}
DONNÉES ACTUELLES
{data_summary}
"""
    if evidence_graph_section:
        prompt += f"\n{evidence_graph_section}\n"
    if quality_section:
        prompt += f"\n{quality_section}\n"
    if memory_section:
        prompt += f"\n{memory_section}\n"
    if actions_section:
        prompt += f"\n{actions_section}\n"
    if relation_section:
        prompt += f"\n{relation_section}\n"
    if pre_analysis_section:
        prompt += f"\n{pre_analysis_section}\n"

    prompt += """
Analyse ces données.
Respecte STRICTEMENT cette structure V5 — ordre IMMUABLE :

# DIAGNOSTIC IMMEDIAT
⚠️ DIAGNOSTIC CRITIQUE
[1 phrase DIRECTE et FRONTALE — jamais neutre — ex : "Votre modèle est actuellement non viable sans correction rapide" — PAS "accuse un déficit" — PAS de nuance]
👉 DÉCISION PRIORITAIRE : [1 action immédiate — verbe d'action fort]
⚡ TENSION : [1 phrase d'urgence forte — ex : "La trajectoire actuelle n'est pas soutenable" ou "Sans correction, la rentabilité est compromise"]

# RÉSUMÉ EXÉCUTIF
[Situation — 1 phrase courte]
[Problème — 1 phrase courte]
[Action — 1 phrase courte]

# SCORES
- Rentabilité : X/10 → [UN SEUL MOT : critique / insuffisant / correct / solide]
- Risque : X/10 → [UN SEUL MOT : faible / modéré / élevé / critique]
- Structure : X/10 → [UN SEUL MOT : instable / fragile / acceptable / solide]
- Liquidité : X/10 → [UN SEUL MOT : critique / tendue / correcte / confortable]

# FIABILITÉ ANALYSE
(RÈGLE ABSOLUE N°9 — 3 scores DISTINCTS — ne jamais les confondre)
- Qualité technique données : [X/100] — [Le fichier est-il bien structuré et lisible ?]
- Complétude données : [X/100] — [Dispose-t-on de toutes les infos nécessaires ?]
- Confiance conclusions : [X/100] — [RÈGLE STRICTE : ne peut PAS dépasser min(Qualité, Complétude). Si Complétude = 25, Confiance ≤ 25, même si Qualité = 100.]
- Explication : [OBLIGATOIRE si Complétude < 70 : quelles données manquent et pourquoi ça limite les conclusions]

# CEO DASHBOARD
(une ligne par indicateur — UNIQUEMENT si la donnée est présente ou calculable depuis les données fournies, sinon écrire "Données insuffisantes" — n'invente JAMAIS un montant)
💵 Chiffre d'affaires total : [montant€ ou "Données insuffisantes"]
💰 Cash disponible : [utilise Trésorerie actif du bilan si présente dans le fichier, sinon déduis des flux ou de la trésorerie déclarée — "Données insuffisantes" si aucune source disponible]
📈 EBITDA : CALCULE depuis le P&L si les charges sont disponibles (Résultat d'exploitation + Dotations amortissements/dépréciations, ou CA − charges d'exploitation hors amortissements). Si les charges globales figurent dans le fichier, donne le montant calculé — "Données insuffisantes" SEULEMENT si le compte de résultat est totalement absent ou que seul le CA est visible sans aucune charge
📊 Marge brute : [marge brute% = (CA − coût des ventes ou charges variables) / CA — si non distinguable, calcule la marge sur coût total ; précise toujours de quelle marge il s'agit dans le label (ex: "Marge brute", "Marge opérationnelle") — "Données insuffisantes" si aucune charge n'est détaillée]
⏳ Runway : [nombre de mois ou "Non applicable" ou "Données insuffisantes"]
🏦 Dette : [utilise le total dettes financières du bilan si présent — sinon "Données insuffisantes"]
🚀 Croissance : [% vs période précédente ou "Données insuffisantes"]

# MARGIN INTELLIGENCE
Score fiabilité : [0-100]%
Raisons fiabilité : [si score < 70% : expliquer ce qui manque — sinon écrire "Données suffisantes"]
→ Marge brute : [% ou "Données insuffisantes"]
→ Marge opérationnelle : [% ou "Données insuffisantes"]
→ Marge nette : [% ou "Données insuffisantes"]
🔴 Destruction marge : [facteur principal qui érode la marge — chiffre si calculable, sinon "Non chiffrable"]
🟢 Création marge : [levier principal d'amélioration des marges — impact estimé si possible]
⚠️ Activité sous-performante : [si identifiable — sinon "Non identifiable sur les données disponibles"]
👉 En résumé : [1 phrase sur la santé des marges et la priorité d'action]

# CASH FORECAST
Score fiabilité : [0-100]%
Raisons fiabilité : [si score < 70% : DSO manquant / échéancier absent / historique limité / etc. — sinon "Données suffisantes"]
→ Projection 30 jours : [estimation — ex : "Trésorerie stable" ou "Risque de tension si X"]
→ Projection 90 jours : [scénario probable — ex : "Dégradation probable sans action sur le BFR"]
→ DSO estimé : [jours ou "Données insuffisantes"]
→ DPO estimé : [jours ou "Données insuffisantes"]
→ BFR estimé : [montant€ ou "Données insuffisantes"]
⚠️ Risque liquidité : [risque trésorerie principal — avec échéance estimée si possible]
👉 En résumé : [1 phrase sur la situation de trésorerie et le risque principal]

# BILAN INTELLIGENCE
(SI ET SEULEMENT SI le fichier contient des données de bilan — actif / passif / capitaux propres. Si aucune section bilan n'est détectable dans le fichier, omets entièrement cette section en écrivant seulement "Bilan absent".)
Score fiabilité : [0-100]%
Raisons fiabilité : [si score < 70% : bilan absent / partiel / non réconcilié — sinon "Bilan disponible et exploitable"]
→ Total Actif : [montant€ ou "Bilan absent"]
→ Actifs immobilisés : [montant€ ou "Bilan absent"]
→ Actifs circulants : [montant€ ou "Bilan absent"]
→ Créances clients : [montant€ ou "Bilan absent"]
→ Trésorerie & équivalents : [montant€ ou "Bilan absent"]
→ Capitaux propres : [montant€ ou "Bilan absent"]
→ Dettes financières LT : [montant€ ou "Bilan absent"]
→ Dettes fournisseurs : [montant€ ou "Bilan absent"]
→ BFR structurel : [montant€ = Créances + Stocks − Dettes fournisseurs — ou "Bilan absent"]
→ Ratio d'endettement : [Dettes nettes / Capitaux propres — ou "Bilan absent"]
👉 En résumé : [1 phrase sur la solidité du bilan et les risques identifiés — ou "Bilan non disponible dans ce fichier"]

# IMPACT FINANCIER
💸 PERTE STRUCTURELLE ESTIMÉE : → [X€/an — chiffre issu des données — OU "Impact non chiffrable sur les données disponibles"]
→ [Détail impact 1 — montant si disponible dans les données]
→ [Détail impact 2 — montant ou "Données insuffisantes"]
→ [Détail impact 3 — marge récupérable ou "Données insuffisantes"]
⚠️ Estimations basées sur les données disponibles uniquement.
👉 En résumé : [synthèse en 1 phrase courte — ex : "La structure actuelle détruit X€/an de marge nette"]

# CREATION DESTRUCTION VALEUR
[1 phrase chiffrée : l'entreprise crée ou détruit de la valeur, et combien — ex : "L'entreprise détruit 48 000€/an de valeur sur l'exercice en cours" — si non chiffrable : "Non chiffrable sur les données disponibles"]

# AVANT APRES
### 📉 AUJOURD'HUI
- [indicateur clé actuel avec chiffre si disponible]
- [deuxième indicateur clé actuel]
### 📈 APRÈS ACTION
- [amélioration concrète attendue]
- [deuxième amélioration attendue]
### 💥 GAIN POTENTIEL
→ [montant estimé / an — si insuffisant écrire "Données insuffisantes"]
→ Rentabilité : [comment la rentabilité s'améliore — ex : "marge nette passe de X% à Y%"]
→ Investissement : [capacité d'investissement libérée — ex : "X€ réallouables" OU "Non quantifiable"]
→ Modèle : [stabilisation attendue — ex : "structure viable en 6 mois"]

# SIMULATEUR DECISION
→ Action : [action clé 1]
  Impact : [impact attendu]
  Résultat : [résultat projeté avec chiffre si calculable depuis les données, sinon "impact positif estimé"]
→ Action : [action clé 2]
  Impact : [impact attendu]
  Résultat : [résultat projeté]

# SCENARIOS
### MEILLEUR CAS
[1-2 phrases : description du scénario optimiste + impact financier chiffré si calculable, sinon qualitatif]
### CAS PROBABLE
[1-2 phrases : description du scénario le plus réaliste compte tenu de la trajectoire actuelle + impact financier chiffré si calculable]
### PIRE CAS
[1-2 phrases : description du scénario pessimiste si rien ne change + impact financier chiffré si calculable]

# PROJECTION TEMPORELLE
### 3 mois
[évolution probable à court terme — basé sur les tendances des données]
### 6 mois
[stabilisation ou dégradation à 6 mois si les actions sont ou ne sont pas prises]
👉 En résumé : [trajectoire en 1 phrase — si actions engagées = X / si inaction = Y]

# CE QUI DETRUIT
(max 5 lignes, triées par impact décroissant — format strict, un nom court puis le détail après "|")
🔴 [Nom court du problème] | Impact annuel : [montant€ ou "Non chiffrable"] | Tendance : [hausse/baisse/stable/non applicable] | Commentaire : [1 phrase]
🔴 [Nom court du problème 2] | Impact annuel : [...] | Tendance : [...] | Commentaire : [...]
🔴 [Nom court du problème 3] | Impact annuel : [...] | Tendance : [...] | Commentaire : [...]

# LEVIERS CROISSANCE
🟢 [Levier 1 actionnable immédiatement]
🟢 [Levier 2 actionnable]
🟢 [Levier 3 actionnable]

# PLAN D'ACTION
### PRIORITÉ ABSOLUE (3 actions max — celles qui changent tout)
- [action 1] → [impact en 5 mots]
- [action 2] → [impact en 5 mots]
- [action 3] → [impact en 5 mots]
### ACTIONS SECONDAIRES
- [action 4]
- [action 5]
👉 En résumé : [en 1 phrase : ce que ce plan change concrètement pour l'entreprise]

# PLAN 30 60 90
### 30 JOURS
- [action] → Responsable : [rôle, ex : "Direction financière"] → Impact : [estimation]
### 60 JOURS
- [action] → Responsable : [rôle] → Impact : [estimation]
### 90 JOURS
- [action] → Responsable : [rôle] → Impact : [estimation]

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

# QUICK WINS
(3 opportunités immédiates chiffrées max — actions à fort impact et faible effort)
RÈGLE ABSOLUE : chaque quick win doit être conditionnel à une hypothèse explicite.
Format OBLIGATOIRE : "Si [hypothèse vérifiable] → [action concrète]"
INTERDIT : "Émettre les factures X" sans condition. OBLIGATOIRE : "Si des factures X n'ont pas été émises → les émettre."
→ Si [hypothèse] → [action] | ROI : [estimation€ ou % ou "Non chiffrable"] | Délai : [ex : "2 semaines"] | Difficulté : [faible / moyenne / élevée]
→ Si [hypothèse] → [action] | ROI : [...] | Délai : [...] | Difficulté : [...]
→ Si [hypothèse] → [action] | ROI : [...] | Délai : [...] | Difficulté : [...]

# IMPACTS FINANCIERS STRUCTURÉS
(Phase 4B — Financial Truth Layer — JSON strict, aucun texte libre en dehors du bloc)
Pour chaque ligne de "CE QUI DETRUIT" et chaque ligne de "QUICK WINS" (dans le même ordre, ref_index 0-based) :
```json
[
  {{
    "ref_type": "destroyer",
    "ref_index": 0,
    "metric_type": "EBITDA",
    "period_basis": "ANNUAL",
    "nature": "RECURRING",
    "confidence": 0.85,
    "source_period": "FY 2019",
    "is_current_period": true,
    "gross_margin_rate": null,
    "gross_margin_source": null,
    "ytd_periods_elapsed": null
  }}
]
```
Valeurs autorisées metric_type : REVENUE | GROSS_MARGIN | EBITDA | NET_PROFIT | CASH | COST | COST_SAVING | WORKING_CAPITAL | EXPOSURE | UNKNOWN
Valeurs autorisées period_basis : ANNUAL | MONTHLY | QUARTERLY | YTD | ANNUALIZED | POINT_IN_TIME | UNKNOWN
Valeurs autorisées nature : ONE_TIME | RECURRING | STRUCTURAL | UNKNOWN
Règles :
- metric_type EBITDA si l'impact touche directement la marge opérationnelle
- metric_type COST si c'est une charge directe (masse salariale, sous-traitance)
- metric_type REVENUE si c'est un manque à gagner sur le CA
- nature ONE_TIME si ponctuel (ex : retard facturation d'un mois précis)
- nature RECURRING si ça se reproduit chaque mois/trimestre/an
- period_basis POINT_IN_TIME pour les ONE_TIME ponctuels
- is_current_period false si l'impact date d'un exercice historique (avant l'année courante identifiée)
- gross_margin_rate : taux de marge brute si connu explicitement (0.0-1.0), sinon null
- gross_margin_source : "EXPLICIT_FILE" si fourni dans le document, "LLM_EXTRACTED" si estimé, null si inconnu
- ytd_periods_elapsed : si period_basis=YTD, nombre de mois calendaires écoulés (ex : Jan-Sep = 9), sinon null
- ref_type "quick_win" pour les QUICK WINS
- Si incertitude totale sur un champ → UNKNOWN (jamais d'invention)

# DÉCISION
(quelques phrases claires — orientées action immédiate)

# CONFIDENTIAL COPILOT NOTE
(Réponds à UNE seule question : "Si j'étais votre Directeur Financier lundi matin, quelles
seraient mes trois premières décisions ?". Ton direct, humain, professionnel, niveau CFO.
Maximum 200 mots, tient sur une page. AUCUN langage marketing, AUCUNE formule de vente.
Termine OBLIGATOIREMENT par la signature exacte : "Pepperyn IA — Votre copilote financier".)

RÈGLES ABSOLUES :
- Zéro hallucination : aucun chiffre inventé, aucune donnée absente du document
- Si un montant manque pour estimer : écrire explicitement "Données insuffisantes"
- Phrases courtes, ton direct, verbes d'action
- Le dirigeant doit comprendre sa situation en 5 secondes
- Chaque recommandation doit être concrète et exploitable immédiatement"""
    return prompt


def _build_user_prompt_call2(
    analysis_call1: str,
    parsed_data: dict[str, Any],
    cfo_decisions: str = "",
    evidence_graph_audit: str = "",
) -> str:
    data_summary = json.dumps(parsed_data, ensure_ascii=False, indent=1)[:6000]
    prompt = f"""Voici une analyse financière générée automatiquement.

Ton rôle est d'AUDITEUR DE COHÉRENCE SILENCIEUX (RÈGLE ABSOLUE N°11).

═══════════════════════════════════════════════
CONTRÔLES OBLIGATOIRES (tous doivent être verts avant de retourner le rapport) :
═══════════════════════════════════════════════
✓ RÈGLE 1 — Zéro chiffre inventé : chaque montant doit provenir des données sources.
✓ RÈGLE 2 — Cohérence inter-sections : si "Données insuffisantes" en section X → même formulation partout.
✓ RÈGLE 3 — Termes interdits → remplacer silencieusement :
   "crise imminente"→"risque identifié" | "catastrophe"→"situation critique"
   "spirale"→"dégradation continue" | "le cash brûle"→"la trésorerie se dégrade"
   "trésorerie épuisée"→"trésorerie insuffisante" | "risque certain"→"risque probable"
   "rupture certaine"→"risque de rupture" | "faillite probable"→"risque de défaut de paiement"
   "point de non-retour"→"seuil d'alerte critique" | "croissance/destruction exponentielle"→chiffrer ou supprimer
✓ RÈGLE 4 — Score confiance ≤ min(Qualité technique, Complétude). Si Complétude = 30, Confiance ≤ 30.
✓ RÈGLE 5 — Recommandations justifiées : Pourquoi ? Sur quelles données ? Quel calcul ? Sinon supprimer.
✓ RÈGLE 6 — Hypothèse unique interdite : toute observation inattendue → plusieurs interprétations proposées.
✓ RÈGLE 7 — Cohérence mathématique : les chiffres s'additionnent correctement.
✓ RÈGLE 8 — Clarté et actionnabilité (compréhensible en 10 secondes).

ANALYSE À VÉRIFIER :
{analysis_call1}

DONNÉES SOURCES :
{data_summary}
"""

    if evidence_graph_audit:
        prompt += f"""
EVIDENCE GRAPH — LISTE DES MONTANTS AUTORISÉS :
{evidence_graph_audit}

⚠️ Tout chiffre dans le rapport qui NE figure PAS dans l'Evidence Graph ci-dessus doit être :
- supprimé, ou
- remplacé par "Données insuffisantes"
⚠️ Toute donnée marquée "Données insuffisantes" dans le rapport alors qu'elle FIGURE dans l'Evidence Graph doit être remplie avec la valeur tracée.
"""

    prompt += """
RÈGLES DE FORMAT (ne jamais violer) :
- Retourne UNIQUEMENT le texte final corrigé — propre, sans aucune trace du processus d'audit.
- INTERDIT : annotations inline, notes d'audit, ~~strikethrough~~, > blockquotes, "Note d'audit", "→ Reformulé".
- Les corrections sont appliquées SILENCIEUSEMENT.
- Ne change JAMAIS le format ni les titres de section (# DIAGNOSTIC IMMEDIAT, # RÉSUMÉ EXÉCUTIF, # SCORES, # FIABILITÉ ANALYSE, # CEO DASHBOARD, # MARGIN INTELLIGENCE, # CASH FORECAST, # IMPACT FINANCIER, # CREATION DESTRUCTION VALEUR, # AVANT APRES, # SIMULATEUR DECISION, # SCENARIOS, # PROJECTION TEMPORELLE, # CE QUI DETRUIT, # LEVIERS CROISSANCE, # PLAN D'ACTION, # QUICK WINS, # PLAN 30 60 90, # RISQUE INACTION, # DIAGNOSTIC FINANCIER, # CE QUI A CHANGÉ, # ALERTES, # PROBLÈMES CRITIQUES, # OPPORTUNITÉS, # DÉCISION, # CONFIDENTIAL COPILOT NOTE).
- Dans # CE QUI DETRUIT, conserve impérativement le format "[Nom] | Impact annuel : ... | Tendance : ... | Commentaire : ..." sur chaque ligne.
- Dans # CONFIDENTIAL COPILOT NOTE, conserve le ton direct/humain/professionnel et la signature exacte "Pepperyn IA — Votre copilote financier".
- Ne change JAMAIS les sous-titres internes.
- Le style doit rester DIRECT et FRONTAL.
- L'ordre des sections est FIXE et IMMUABLE.
- CRITIQUE : dans IMPACT FINANCIER, AVANT APRES, SIMULATEUR DECISION — supprimer tout chiffre inventé.
"""

    # Skeptical Reviewer — activé uniquement si des décisions CFO sont fournies
    if cfo_decisions:
        prompt += f"""
RÉFÉRENCE CFO (décisions stratégiques validées par pré-analyse) :
{cfo_decisions}

En plus de ta vérification habituelle, contrôle que :
- Les sections # PLAN D'ACTION et # DÉCISION sont cohérentes avec les décisions prioritaires ci-dessus.
- La section # RISQUE INACTION reflète bien le risque d'inaction identifié.
- Les # QUICK WINS correspondent aux opportunités immédiates identifiées.
- Les recommandations en # CONFIDENTIAL COPILOT NOTE reprennent les priorités CFO.
- Si une recommandation importante est absente, ajoute-la en respectant le format existant.
- Si une recommandation contredit les priorités CFO sans être justifiée par les données, reformule-la.

"""

    prompt += "Commence par [VERIFIED] ou [CORRECTED] sur la première ligne, puis le texte complet et propre."
    return prompt


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


def _parse_structured_impacts_section(
    section_text: str,
) -> dict[tuple[str, int], dict]:
    """
    Parse le bloc JSON de la section # IMPACTS FINANCIERS STRUCTURÉS.

    Contrat :
      - Jamais d'exception propagée — retourne {} en cas d'erreur.
      - Règle duplicate : first valid wins. Si deux items partagent le même
        (ref_type, ref_index), le premier dans le tableau JSON est retenu.
        Les doublons ultérieurs sont ignorés silencieusement.
      - amount est toujours None dans le dict retourné ; il sera injecté par
        _try_deserialize_qi() depuis le parseur legacy (Phase 4B).
      - Les enums inconnus (metric_type, period_basis, nature) sont conservés
        tels quels dans le dict ; _safe_enum() les convertit en UNKNOWN lors
        de QuantifiedImpact.from_dict().

    Args:
        section_text: Contenu brut de la section IMPACTS FINANCIERS STRUCTURÉS
                      (texte entre le marqueur et la section suivante).

    Returns:
        dict keyed by (ref_type: str, ref_index: int) → QI dict.
        Vide si section_text est vide, si le JSON est absent/invalide,
        ou si aucun item n'est parseable.
    """
    if not section_text:
        return {}

    import json as _json
    import logging as _logging
    _log = _logging.getLogger(__name__)
    result: dict[tuple[str, int], dict] = {}

    try:
        # Chercher le bloc JSON avec ou sans délimiteurs backtick
        _json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```",
                                section_text, re.DOTALL)
        if not _json_match:
            _json_match = re.search(r"(\[.*\])", section_text, re.DOTALL)
        if not _json_match:
            return {}

        _parsed_list = _json.loads(_json_match.group(1))
        if not isinstance(_parsed_list, list):
            return {}

        for _item in _parsed_list:
            if not isinstance(_item, dict):
                continue

            # Extraire et valider ref_type / ref_index
            _rtype = str(_item.get("ref_type", "")).strip()
            _ridx_raw = _item.get("ref_index")
            if not _rtype or _ridx_raw is None:
                continue
            try:
                _ridx = int(_ridx_raw)
            except (TypeError, ValueError):
                continue

            key = (_rtype, _ridx)
            # Règle duplicate : first valid wins
            if key in result:
                _log.debug(
                    f"[llm] duplicate (ref_type={_rtype!r}, ref_index={_ridx}) "
                    f"ignoré (first valid wins)"
                )
                continue

            # Annualization depuis ytd_periods_elapsed
            _ann = None
            _ytd_n = _item.get("ytd_periods_elapsed")
            if _ytd_n is not None and _item.get("period_basis") in ("YTD", "ANNUALIZED"):
                try:
                    _n = int(_ytd_n)
                    _q = "CERTIFIED" if _n >= 6 else "RUN_RATE"
                    _ann = {
                        "periods_elapsed": _n,
                        "periods_per_year": 12,
                        "quality": _q,
                        "annualization_method": f"amount / {_n} * 12",
                        "seasonality_flag": False,
                    }
                except (TypeError, ValueError):
                    pass

            # GrossMargin depuis gross_margin_rate / gross_margin_source
            _gm = None
            _gmr = _item.get("gross_margin_rate")
            _gms = _item.get("gross_margin_source")
            if _gmr is not None or _gms:
                _gm = {
                    "rate": _gmr,
                    "source": _gms or "LLM_EXTRACTED",
                }

            # Confidence : float robuste (None ou invalide → 0.5)
            _conf_raw = _item.get("confidence")
            try:
                _conf = float(_conf_raw) if _conf_raw is not None else 0.5
            except (TypeError, ValueError):
                _conf = 0.5

            result[key] = {
                "metric_type": _item.get("metric_type", "UNKNOWN"),
                "period_basis": _item.get("period_basis", "UNKNOWN"),
                "nature": _item.get("nature", "UNKNOWN"),
                "confidence": _conf,
                "source_period": _item.get("source_period"),
                "is_current_period": bool(_item.get("is_current_period", True)),
                "gross_margin": _gm,
                "annualization": _ann,
                "amount": None,  # Injecté par _try_deserialize_qi() depuis legacy
            }

    except Exception as _e:
        _log.debug(f"[llm] _parse_structured_impacts_section failed: {_e}")
        return {}

    return result


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
    confidential_copilot_note_raw = extract_section("CONFIDENTIAL COPILOT NOTE")

    # ── V5 new sections ──────────────────────────────────────────────────────
    diagnostic_immediat_raw = extract_section("DIAGNOSTIC IMMEDIAT")
    margin_intelligence_raw = extract_section("MARGIN INTELLIGENCE")
    cash_forecast_raw = extract_section("CASH FORECAST")
    # Note: bilan_intelligence_raw is extracted later in V12 block, after helpers are defined
    impact_financier_raw = extract_section("IMPACT FINANCIER")
    avant_apres_raw = extract_section("AVANT APRES")
    simulateur_raw = extract_section("SIMULATEUR DECISION")
    projection_raw = extract_section("PROJECTION TEMPORELLE")
    ce_qui_detruit_raw = extract_section("CE QUI DETRUIT")
    leviers_raw = extract_section("LEVIERS CROISSANCE")
    risque_inaction_raw = extract_section("RISQUE INACTION")

    # ── V11 — Executive Deliverables Manifesto ──────────────────────────────
    ceo_dashboard_raw = extract_section("CEO DASHBOARD")
    creation_destruction_raw = extract_section("CREATION DESTRUCTION VALEUR")
    quick_wins_raw = extract_section("QUICK WINS")
    plan_30_60_90_raw = extract_section("PLAN 30 60 90")
    scenarios_raw = extract_section("SCENARIOS")

    # ── RÈGLE N°9 — Parse "# FIABILITÉ ANALYSE" (3 scores distincts) ────────
    fiabilite_raw = extract_section("FIABILITÉ ANALYSE")
    score_qualite_technique_llm: int = -1
    score_completude_llm: int = -1
    score_confiance_llm: int = -1

    def _extract_score_from_line(raw_section: str, keyword: str) -> int:
        """Extrait un entier X depuis 'keyword : X/100' ou 'keyword : [X/100]'."""
        for line in raw_section.splitlines():
            if keyword.lower() in line.lower():
                m = re.search(r"\[?(\d{1,3})/100\]?", line)
                if m:
                    return min(100, max(0, int(m.group(1))))
        return -1

    if fiabilite_raw:
        score_qualite_technique_llm = _extract_score_from_line(fiabilite_raw, "qualité technique")
        score_completude_llm        = _extract_score_from_line(fiabilite_raw, "complétude données")
        score_confiance_llm         = _extract_score_from_line(fiabilite_raw, "confiance conclusions")
        # RÈGLE N°9 : Confiance ≤ min(Qualité, Complétude) — corrige si le LLM a dépassé
        if score_qualite_technique_llm >= 0 and score_completude_llm >= 0 and score_confiance_llm >= 0:
            max_allowed = min(score_qualite_technique_llm, score_completude_llm)
            if score_confiance_llm > max_allowed:
                score_confiance_llm = max_allowed
        # Remplace le score_confiance initial (= confiance de classification) par
        # la confiance de l'analyse générée par le LLM, si disponible
        if score_confiance_llm >= 0:
            score_confiance = score_confiance_llm

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
            if "secondaire" in ll or "actions secondaires" in ll:
                current_plan_section = "secondaire"
            elif "haute" in ll or "absolu" in ll or "priorité" in ll or "priorite" in ll:
                current_plan_section = "haute"
            continue
        if l.startswith("-") or l.startswith("•"):
            text = l.lstrip("-• ").strip()
            # Skip "En résumé" lines that appear at the end of the plan section
            if text and not text.startswith("\U0001f449"):
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
        if (l.startswith("💸") or "SYNTHÈSE" in l.upper() or "SYNTHESE" in l.upper()
                or "PERTE ESTIMÉE" in l.upper() or "PERTE ESTIMEE" in l.upper()
                or "PERTE STRUCTURELLE" in l.upper()):
            # Extract after the colon (and optional →)
            synthese_text = l.replace("💸", "").strip()
            if ":" in synthese_text:
                synthese_text = synthese_text.split(":", 1)[-1].strip()
            synthese_text = synthese_text.lstrip("→ ").strip()
            impact_financier_synthese = synthese_text
        elif l.startswith("→"):
            detail = l.lstrip("→").strip()
            # Skip "En résumé" that somehow lands here
            if detail and not detail.startswith("\U0001f449"):
                impact_financier.append(detail)
        elif not l.startswith(("⚠️", "#", "\U0001f449")) and not impact_financier_synthese:
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

    # ── Parse V9/V10 — helpers ───────────────────────────────────────────────
    def _extract_en_resume_inner(raw: str) -> Optional[str]:
        """Extract the 👉 En résumé line from a section's raw text."""
        for ln in raw.splitlines():
            s = ln.strip()
            if s.startswith("\U0001f449") and "résumé" in s.lower():
                cleaned = s.lstrip("\U0001f449").strip()
                if cleaned.lower().startswith("en résumé"):
                    cleaned = cleaned[len("en résumé"):].lstrip(" :").strip()
                return cleaned
        return None

    # ── Parse V10 — Margin Intelligence ─────────────────────────────────────
    def _extract_confidence_score(raw: str) -> Optional[int]:
        """Extract 'Score fiabilité : XX%' from a section."""
        for ln in raw.splitlines():
            s = ln.strip().lower()
            if "score fiabilité" in s or "score fiabilite" in s:
                m = re.search(r"(\d{1,3})\s*%", ln)
                if m:
                    return min(100, max(0, int(m.group(1))))
        return None

    def _parse_indicator_lines(raw: str) -> list[str]:
        """Parse → / 🔴 / 🟢 / ⚠️ lines from a raw section, skip meta lines."""
        results = []
        for ln in raw.splitlines():
            s = ln.strip()
            if not s:
                continue
            # Skip score/confidence meta lines and "En résumé" summaries
            sl = s.lower()
            if sl.startswith("score fiabilité") or sl.startswith("score fiabilite"):
                continue
            if sl.startswith("raisons") and ":" in sl:
                continue
            if s.startswith("\U0001f449"):
                continue
            if s.startswith("→") or s.startswith("🔴") or s.startswith("🟢") or s.startswith("⚠️"):
                results.append(s)
        return results

    margin_intelligence = _parse_indicator_lines(margin_intelligence_raw)
    margin_confidence = _extract_confidence_score(margin_intelligence_raw)
    en_resume_margin = _extract_en_resume_inner(margin_intelligence_raw) if margin_intelligence_raw else None

    cash_forecast = _parse_indicator_lines(cash_forecast_raw)
    cash_forecast_confidence = _extract_confidence_score(cash_forecast_raw)
    en_resume_cash = _extract_en_resume_inner(cash_forecast_raw) if cash_forecast_raw else None

    # BFR indicators — extract DSO / DPO / BFR lines specifically
    bfr_indicators: list[str] = []
    for ln in cash_forecast_raw.splitlines():
        s = ln.strip()
        if any(kw in s.lower() for kw in ["dso", "dpo", "bfr", "besoin en fonds"]):
            bfr_indicators.append(s)

    # ── Parse V12 — Bilan Intelligence ───────────────────────────────────────
    bilan_intelligence_raw = extract_section("BILAN INTELLIGENCE")
    # Ignore placeholder-only sections (when LLM writes "Bilan absent" as full section)
    _bilan_is_absent = (
        not bilan_intelligence_raw
        or bilan_intelligence_raw.strip().lower() in ("bilan absent", "")
    )
    if _bilan_is_absent:
        bilan_intelligence: list[str] = []
        bilan_confidence: Optional[int] = None
        en_resume_bilan: Optional[str] = None
    else:
        bilan_intelligence = _parse_indicator_lines(bilan_intelligence_raw)
        bilan_confidence = _extract_confidence_score(bilan_intelligence_raw)
        en_resume_bilan = _extract_en_resume_inner(bilan_intelligence_raw)
        # If all lines say "Bilan absent", treat section as absent
        if bilan_intelligence and all("bilan absent" in ln.lower() for ln in bilan_intelligence):
            bilan_intelligence = []
            bilan_confidence = None
            en_resume_bilan = None

    # ── Parse V9 — "En résumé" lines ─────────────────────────────────────────
    en_resume_impact = _extract_en_resume_inner(impact_financier_raw)
    en_resume_plan = _extract_en_resume_inner(plan_raw)
    en_resume_projection = _extract_en_resume_inner(projection_raw)

    # ── Parse V6/V9 — avant/après (nouveaux headers) ─────────────────────────
    avant_apres_actuel: list[str] = []
    avant_apres_apres: list[str] = []
    avant_apres_gain: Optional[str] = None
    avant_apres_gain_transformations: list[str] = []
    current_aa = None
    gain_amount_captured = False
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
            gain_amount_captured = False
        elif l.startswith("-") or l.startswith("→"):
            text = l.lstrip("-→ ").strip()
            if text:
                if current_aa == "actuel":
                    avant_apres_actuel.append(text)
                elif current_aa == "apres":
                    avant_apres_apres.append(text)
                elif current_aa == "gain":
                    if not gain_amount_captured:
                        avant_apres_gain = text
                        gain_amount_captured = True
                    elif any(kw in text.lower() for kw in [
                        "rentabilité", "rentabilite", "investissement", "modèle", "modele"
                    ]):
                        avant_apres_gain_transformations.append(text)

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
        elif l and not l.startswith("#") and not l.startswith("\U0001f449"):
            if current_proj == "3":
                projection_3mois.append(l)
            elif current_proj == "6":
                projection_6mois.append(l)

    # ── Parse V5 — leviers (texte libre, inchangé) ──────────────────────────
    leviers_croissance = _parse_list(leviers_raw, "🟢")

    # ── Parse V12 — CE QUI DETRUIT (structuré : Nom | Impact annuel | Tendance | Commentaire) ──
    def _parse_value_destroyers(raw: str) -> list[dict]:
        items = []
        for line in raw.splitlines():
            l = line.strip()
            if not l.startswith("🔴"):
                continue
            l = l.lstrip("🔴").strip()
            parts = [p.strip() for p in l.split("|")]
            if not parts:
                continue
            name = parts[0]
            impact = trend = comment = None
            for p in parts[1:]:
                pl = p.lower()
                if pl.startswith("impact"):
                    impact = p.split(":", 1)[-1].strip()
                elif pl.startswith("tendance"):
                    trend = p.split(":", 1)[-1].strip()
                elif pl.startswith("commentaire"):
                    comment = p.split(":", 1)[-1].strip()
            if name:
                items.append({
                    "name": name,
                    "impact_annuel": impact,
                    "tendance": trend,
                    "commentaire": comment,
                })
        return items

    value_destroyers = _parse_value_destroyers(ce_qui_detruit_raw)
    # Compatibilité ascendante : export_pdf_service.py consomme aujourd'hui
    # "ce_qui_detruit" comme une simple liste de chaînes (_bullet_rows). On la
    # reconstruit à partir du nouveau format structuré, sans toucher à
    # export_pdf_service.py (hors scope Étape A/B).
    ce_qui_detruit = [
        f"{d['name']} ({d['impact_annuel']})" if d.get("impact_annuel") else d["name"]
        for d in value_destroyers
    ] or _parse_list(ce_qui_detruit_raw, "🔴")  # filet de sécurité si le LLM ne respecte pas le nouveau format
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

    # ── Parse V11 — CEO Dashboard ────────────────────────────────────────────
    def _parse_ceo_dashboard(raw: str) -> list[dict]:
        cards = []
        for line in raw.splitlines():
            l = line.strip()
            if not l or l.startswith("#") or ":" not in l:
                continue
            label_part, value_part = l.split(":", 1)
            label_clean = re.sub(r"^[^\wÀ-ÿ]+", "", label_part).strip()
            value_clean = value_part.strip()
            if not label_clean or not value_clean:
                continue
            status = "missing" if any(
                kw in value_clean.lower()
                for kw in ["donnée insuffisante", "données insuffisantes", "non applicable", "non chiffrable"]
            ) else None
            cards.append({"label": label_clean, "value": value_clean, "status": status})
        return cards

    ceo_dashboard = _parse_ceo_dashboard(ceo_dashboard_raw)
    creation_destruction_valeur = creation_destruction_raw.strip() or None

    # ── Parse V11 — Quick Wins ───────────────────────────────────────────────
    def _parse_quick_wins(raw: str) -> list[dict]:
        wins = []
        for line in raw.splitlines():
            l = line.strip()
            if not l.startswith("→"):
                continue
            l = l.lstrip("→").strip()
            parts = [p.strip() for p in l.split("|")]
            if not parts:
                continue
            description = parts[0]
            roi = temps = difficulte = None
            for p in parts[1:]:
                pl = p.lower()
                if pl.startswith("roi"):
                    roi = p.split(":", 1)[-1].strip()
                elif pl.startswith("délai") or pl.startswith("delai"):
                    temps = p.split(":", 1)[-1].strip()
                elif pl.startswith("difficult"):
                    difficulte = p.split(":", 1)[-1].strip()
            if description:
                wins.append({
                    "description": description,
                    "roi_estime": roi,
                    "temps_mise_en_oeuvre": temps,
                    "difficulte": difficulte,
                })
        return wins

    quick_wins = _parse_quick_wins(quick_wins_raw)

    # ── Parse Phase 4B — IMPACTS FINANCIERS STRUCTURÉS ──────────────────────
    # Délégué à _parse_structured_impacts_section() (fonction module-level testable).
    # Si absent ou malformé → dict vide → aucun effet sur legacy.
    # Règle duplicate : first valid wins (documentée dans la fonction).
    impacts_structures_raw = extract_section("IMPACTS FINANCIERS STRUCTURÉS")
    _qi_by_ref = _parse_structured_impacts_section(impacts_structures_raw)

    # Injection de quantified_impact dans value_destroyers et quick_wins
    for _i, _d in enumerate(value_destroyers):
        _qi_dict = _qi_by_ref.get(("destroyer", _i))
        if _qi_dict:
            _d["quantified_impact"] = dict(_qi_dict)   # copie defensive

    for _i, _w in enumerate(quick_wins):
        _qi_dict = _qi_by_ref.get(("quick_win", _i))
        if _qi_dict:
            _w["quantified_impact"] = dict(_qi_dict)   # copie defensive

    # ── Parse V11 — Plan 30/60/90 ────────────────────────────────────────────
    def _parse_plan_30_60_90(raw: str) -> list[dict]:
        items = []
        current_horizon: Optional[str] = None
        for line in raw.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.startswith("#"):
                ll = l.lower()
                if "30" in ll:
                    current_horizon = "30"
                elif "60" in ll:
                    current_horizon = "60"
                elif "90" in ll:
                    current_horizon = "90"
                continue
            if l.startswith("-") and current_horizon:
                text_line = l.lstrip("- ").strip()
                segments = [s.strip() for s in text_line.split("→")]
                action = segments[0] if segments else text_line
                responsable = impact = None
                for seg in segments[1:]:
                    sl = seg.lower()
                    if sl.startswith("responsable"):
                        responsable = seg.split(":", 1)[-1].strip()
                    elif sl.startswith("impact"):
                        impact = seg.split(":", 1)[-1].strip()
                if action:
                    items.append({
                        "action": action,
                        "horizon": current_horizon,
                        "responsable": responsable,
                        "impact_attendu": impact,
                    })
        return items

    plan_action_30_60_90 = _parse_plan_30_60_90(plan_30_60_90_raw)

    # ── Parse V11 — Scénarios best/most_likely/worst ─────────────────────────
    def _parse_scenarios(raw: str) -> list[dict]:
        name_map = {
            "meilleur cas": ("best_case", "Meilleur cas"),
            "cas probable": ("most_likely", "Cas le plus probable"),
            "pire cas": ("worst_case", "Pire cas"),
        }
        scenarios_list: list[dict] = []
        current: Optional[tuple[str, str]] = None
        buffer: list[str] = []

        def _flush():
            if current and buffer:
                nom, label = current
                scenarios_list.append({"nom": nom, "label": label, "description": " ".join(buffer).strip()})

        for line in raw.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.startswith("#"):
                ll = l.lstrip("# ").strip().lower()
                matched = next((v for k, v in name_map.items() if k in ll), None)
                if matched:
                    _flush()
                    current = matched
                    buffer = []
                continue
            if current:
                buffer.append(l)
        _flush()
        return scenarios_list

    scenarios = _parse_scenarios(scenarios_raw)

    # ── V11 — score_global / niveau_urgence : calcul Python, jamais le LLM ──
    # Le risque est inversé (10 - risque) car, contrairement aux 3 autres
    # scores, un risque ÉLEVÉ (X/10 grand) est un signal négatif.
    score_components = []
    if score_rentabilite is not None:
        score_components.append(score_rentabilite)
    if score_risque is not None:
        score_components.append(10 - score_risque)
    if score_structure is not None:
        score_components.append(score_structure)
    if score_liquidite is not None:
        score_components.append(score_liquidite)
    score_global = round(sum(score_components) / len(score_components)) if score_components else None

    if score_global is None:
        niveau_urgence = None
    elif score_global <= 3:
        niveau_urgence = "Critique"
    elif score_global <= 5:
        niveau_urgence = "Élevé"
    elif score_global <= 7:
        niveau_urgence = "Modéré"
    else:
        niveau_urgence = "Maîtrisé"

    # ── Extract verification tag ─────────────────────────────────────────────
    verification_tag = "VERIFIED"
    if text.strip().startswith("[CORRECTED]"):
        verification_tag = "CORRECTED"

    return {
        "type_document": doc_type,
        "score_confiance": score_confiance,  # = LLM confidence conclusions si parsé, sinon classification
        # RÈGLE N°9 — 3 scores distincts (accessibles par les exports si besoin)
        "score_qualite_technique": score_qualite_technique_llm,
        "score_completude_llm": score_completude_llm,
        "score_confiance_conclusions_llm": score_confiance_llm,
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
        # V9
        "avant_apres_gain_transformations": avant_apres_gain_transformations,
        "en_resume_impact": en_resume_impact,
        "en_resume_plan": en_resume_plan,
        "en_resume_projection": en_resume_projection,
        # V10 — Margin Intelligence + Cash Forecast
        "margin_intelligence": margin_intelligence,
        "margin_confidence": margin_confidence,
        "en_resume_margin": en_resume_margin,
        "cash_forecast": cash_forecast,
        "cash_forecast_confidence": cash_forecast_confidence,
        "en_resume_cash": en_resume_cash,
        "bfr_indicators": bfr_indicators,
        # V12 — Bilan Intelligence
        "bilan_intelligence": bilan_intelligence,
        "bilan_confidence": bilan_confidence,
        "en_resume_bilan": en_resume_bilan,
        # V11 — Executive Deliverables Manifesto
        "score_global": score_global,
        "niveau_urgence": niveau_urgence,
        "creation_destruction_valeur": creation_destruction_valeur,
        "ceo_dashboard": ceo_dashboard,
        "quick_wins": quick_wins,
        "plan_action_30_60_90": plan_action_30_60_90,
        "scenarios": scenarios,
        # V12 — Executive Narrative (alimente l'Executive Decision Model)
        "value_destroyers": value_destroyers,
        "note_copilote": confidential_copilot_note_raw.strip() or None,
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
    relation_section: str = "",
    model: str = MODEL_SONNET,
    pre_analysis_section: str = "",
    system_prompt: Optional[str] = None,
    evidence_graph_section: str = "",
) -> tuple[str, int, int]:
    """
    Call 1 — Analyse principale.
    model = MODEL_SONNET par défaut, MODEL_OPUS sur escalade.
    pre_analysis_section = contexte pré-analyse (Agents 5+6) si USE_ENHANCED_PIPELINE.
    evidence_graph_section = inventaire des faits traçables (Evidence Graph agent).
    system_prompt = surcharge optionnelle du system prompt (ENHANCED_ANALYSIS_SYSTEM si pipeline enrichi).
    Returns (analysis_text, input_tokens, output_tokens)
    """
    client = get_anthropic_client()
    user_prompt = _build_user_prompt_call1(
        parsed_data, industry, business_model,
        memory_section, actions_section, quality_section, relation_section,
        pre_analysis_section=pre_analysis_section,
        evidence_graph_section=evidence_graph_section,
    )
    message = client.messages.create(
        model=model,
        system=system_prompt or ANALYSIS_SYSTEM_V3,
        messages=[{"role": "user", "content": user_prompt}],
        **CALL_1_BASE,
    )
    text = message.content[0].text.strip()
    return text, message.usage.input_tokens, message.usage.output_tokens


async def call_verification_v3(
    analysis_call1: str,
    parsed_data: dict[str, Any],
    model: str = MODEL_SONNET,
    cfo_decisions: str = "",
    system_prompt: Optional[str] = None,
    evidence_graph_audit: str = "",
) -> str:
    """
    Call 2 — Audit de cohérence + Vérification + Skeptical Reviewer.
    evidence_graph_audit = référence Evidence Graph pour validation croisée des montants.
    cfo_decisions = résumé formaté des décisions CFO (Agent 6) pour guider la revue.
    system_prompt = surcharge optionnelle (ENHANCED_ANALYSIS_SYSTEM si pipeline enrichi).
    Returns verified/corrected analysis text.
    """
    client = get_anthropic_client()
    user_prompt = _build_user_prompt_call2(
        analysis_call1,
        parsed_data,
        cfo_decisions=cfo_decisions,
        evidence_graph_audit=evidence_graph_audit,
    )
    message = client.messages.create(
        model=model,
        system=system_prompt or ANALYSIS_SYSTEM_V3,
        messages=[{"role": "user", "content": user_prompt}],
        **CALL_2_BASE,
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
    relation_section: str = "",
    plan_tier: str = "free",
) -> tuple[AnalysisResult, int, float]:
    """
    Pipeline v4 — model router intégré.
    Sonnet par défaut ; Opus sur SCALE, volume élevé ou échec qualité.

    Si USE_ENHANCED_PIPELINE=true (Railway env var) :
      → Agents 5+6 (Financial Analyst + Strategic CFO) s'exécutent en pré-analyse
      → Leur output enrichit le contexte de Call 1 et guide Call 2 (Skeptical Reviewer)
      → Le system prompt ENHANCED_ANALYSIS_SYSTEM remplace ANALYSIS_SYSTEM_V3
      → Zero breaking change : même output, même schéma, même parsing

    Returns (AnalysisResult, total_tokens, estimated_cost_euros)
    """
    total_tokens = 0
    enhanced = _use_enhanced_pipeline()

    # ── Sélection du system prompt ─────────────────────────────────────────────
    active_system_prompt = ENHANCED_ANALYSIS_SYSTEM if enhanced else None  # None = défaut ANALYSIS_SYSTEM_V3

    # Step 1: Classification — Haiku toujours
    doc_type, confidence = await classify_document(parsed_data)
    total_tokens += 300

    # Step 2: Sélection du modèle d'analyse
    selected_model = _select_analysis_model(plan_tier, parsed_data)

    # Step 2.0: Evidence Graph — RÈGLE ABSOLUE N°6 (toujours actif)
    # Construit l'inventaire de tous les faits traçables AVANT toute rédaction.
    # Non-bloquant : retourne {} en cas d'échec.
    logger.info("[EVIDENCE GRAPH] Building traceable facts inventory")
    evidence_graph = await _run_evidence_graph_agent(parsed_data, model=MODEL_SONNET)
    evidence_graph_section = _format_evidence_graph_for_prompt(evidence_graph)
    evidence_graph_audit = _format_evidence_graph_for_audit(evidence_graph)
    total_tokens += 1500  # estimation Evidence Graph agent

    # Step 2.5: Pipeline enrichi — Agents 5 + 6 (Financial Analyst → Strategic CFO)
    pre_analysis_section = ""
    cfo_decisions_str = ""
    if enhanced:
        logger.info("[ENHANCED PIPELINE] Running Financial Analyst + Strategic CFO pre-pass")
        analyst_findings = await _run_financial_analyst_prep(parsed_data, model=selected_model)
        cfo_findings = await _run_strategic_cfo_prep(analyst_findings, model=MODEL_SONNET)
        pre_analysis_section = _build_pre_analysis_section(analyst_findings, cfo_findings)
        cfo_decisions_str = _format_cfo_for_reviewer(cfo_findings)
        total_tokens += 2200  # estimation agents 5+6 combinés

    # Step 3: Call 1 — Analyse principale (avec Evidence Graph injecté)
    analysis_text, in_tokens, out_tokens = await call_analysis_v3(
        parsed_data,
        industry=industry or context,
        business_model=business_model,
        memory_section=memory_section,
        actions_section=actions_section,
        quality_section=quality_section,
        relation_section=relation_section,
        model=selected_model,
        pre_analysis_section=pre_analysis_section,
        system_prompt=active_system_prompt,
        evidence_graph_section=evidence_graph_section,
    )
    total_tokens += in_tokens + out_tokens

    # Step 4: Call 2 — Audit de cohérence + Vérification (RÈGLE N°11)
    # Evidence Graph injecté comme référence pour validation croisée des montants.
    verified_text = await call_verification_v3(
        analysis_text,
        parsed_data,
        model=selected_model,
        cfo_decisions=cfo_decisions_str,
        system_prompt=active_system_prompt,
        evidence_graph_audit=evidence_graph_audit,
    )
    total_tokens += 800  # approx

    # Step 5: Scoring — Haiku toujours
    score = await _score_analysis(verified_text)
    total_tokens += 150

    # Retry en escalade Opus si score < 8
    if score < 8:
        escalated_model = MODEL_OPUS   # toujours Opus sur échec qualité
        analysis_text2, in2, out2 = await call_analysis_v3(
            parsed_data,
            industry=industry or context,
            business_model=business_model,
            memory_section=memory_section,
            actions_section=actions_section,
            quality_section=quality_section,
            relation_section=relation_section,
            model=escalated_model,
            pre_analysis_section=pre_analysis_section,
            system_prompt=active_system_prompt,
            evidence_graph_section=evidence_graph_section,
        )
        total_tokens += in2 + out2
        verified_text2 = await call_verification_v3(
            analysis_text2,
            parsed_data,
            model=escalated_model,
            cfo_decisions=cfo_decisions_str,
            system_prompt=active_system_prompt,
            evidence_graph_audit=evidence_graph_audit,
        )
        total_tokens += 800
        score2 = await _score_analysis(verified_text2)
        total_tokens += 150
        if score2 >= score:
            verified_text = verified_text2
            selected_model = escalated_model   # pour le calcul de coût
            in_tokens, out_tokens = in2, out2

    # Step 6: Nettoyage, termes interdits (RÈGLE N°4), et parsing
    verified_text = _clean_verified_text(verified_text)
    verified_text = _apply_forbidden_terms(verified_text)   # filet de sécurité post-processing
    analysis_dict = _parse_v3_text(verified_text, doc_type, confidence)

    # Calcul de coût réel (USD → EUR ×0.92) basé sur le modèle effectivement utilisé
    haiku_tokens_total = 600   # classification + scoring
    cost_usd = (
        haiku_tokens_total * _PRICE_IN[MODEL_HAIKU] / 1_000_000
        + in_tokens  * _PRICE_IN[selected_model]  / 1_000_000
        + out_tokens * _PRICE_OUT[selected_model] / 1_000_000
        + 800 * _PRICE_IN[selected_model] / 1_000_000   # Call 2 approx
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

    # Attacher UNIQUEMENT les champs hors schéma Pydantic (value_destroyers,
    # note_copilote…). Ne pas écraser les instances déjà validées par Pydantic
    # (PlanActionItem, ScenarioCase, etc.) — cela provoquerait des erreurs de
    # sérialisation ("Expected PlanActionItem but got dict") et un crash du stream.
    extra_only = {k: v for k, v in analysis_dict.items() if k not in AnalysisResult.model_fields}
    result.__dict__.update(extra_only)

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

# Chat — Sonnet, réponses courtes (500 tokens max).
# Sonnet offre la qualité de raisonnement d'un consultant senior.
# Haiku reste réservé à classification et scoring.
# Coût estimé : ~0.002€/message vs ~0.001€ sur Haiku — delta négligeable
# face au gain de qualité perçue sur les plans PRO/POWER/SCALE.
CHAT_MODEL = MODEL_SONNET
CHAT_MAX_TOKENS = 500


async def call_chat_intelligent(
    message: str,
    analysis_context: str,
    history: list[dict] | None = None,
    model_tier: str = "normal",
) -> tuple[str, str]:
    """
    Appelle Haiku pour toute interaction conversationnelle.

    model_tier est conservé pour compatibilité ascendante mais n'influence
    plus le choix du modèle — tout le chat est sur Haiku.

    Returns (response_text, model_used)
    """
    client = get_anthropic_client()

    system = CHAT_SYSTEM
    if analysis_context:
        system += f"\n\nCONTEXTE DE L'ANALYSE EN COURS :\n{analysis_context[:3000]}"

    messages = list(history or [])
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model=CHAT_MODEL,
        max_tokens=CHAT_MAX_TOKENS,
        system=system,
        messages=messages,
    )

    return response.content[0].text.strip(), CHAT_MODEL
