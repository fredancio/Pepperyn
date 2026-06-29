"""
executive_case_builder.py — Agent 1 : Executive Case Builder
MODÈLE OBLIGATOIRE : Claude Opus (claude-opus-4-6)

Responsabilité unique :
  Transformer les données d'analyse en ExecutiveCaseJSON — source unique
  de vérité pour tous les exports (PDF, PPTX, Excel).

Ce fichier exporte également deux fonctions d'adaptation :
  - case_to_edm()          → ExecutiveDecisionModel  (pour PDF / PPTX)
  - case_to_result_dict()  → dict                    (pour PDF / PPTX)

Ces adapters permettent aux services export existants de recevoir un
(edm, result_dict) dérivé du MÊME ExecutiveCaseJSON, garantissant la
cohérence des chiffres entre tous les livrables.

RÈGLES ABSOLUES :
  1. Aucun calcul dans cet agent — les chiffres viennent de l'EDM Python.
  2. Aucune invention, extrapolation, interpolation.
  3. Si une donnée est absente → null dans le JSON. Jamais estimé.
  4. Aucun autre agent ne peut modifier ce JSON après production.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, List, Optional

from models.executive_case import (
    COIBreakdown,
    DataQuality,
    DecisionReasoning,
    DimensionScores,
    ExecutionLogItem,
    ExecutiveCaseJSON,
    KPICard,
    PriorityDecisionItem,
    ProjectionSeries,
    RiskItem,
    ScenarioItem,
    Scenarios,
    ValueDestroyerItem,
)
from services.executive_decision_model import (
    build_executive_decision_model,
    parse_amount_eur,
)

logger = logging.getLogger(__name__)

MODEL_OPUS = "claude-opus-4-6"

# ─── EDX-001 : MATCHING MOTS-CLÉS DÉCISION → DESTRUCTEUR ────────────────────
# Chaque groupe rassemble les termes financiers sémantiquement liés.
# Un token de la décision ET un token du destructeur dans le même groupe
# déclenchent un bonus sémantique de 30 pts.

_STOP_WORDS = {
    "les", "des", "par", "est", "une", "que", "qui", "son", "ses",
    "sur", "pas", "non", "car", "ces", "cet", "aux", "eux", "pour",
    "dans", "avec", "sans", "mais", "donc", "puis", "tout", "tres",
    "plus", "bien", "etre", "fait", "ont", "sont", "nous", "vous",
    "ils", "elles", "leur", "leurs", "lui", "elle",
}

_KEYWORD_GROUPS: list[dict] = [
    {
        "id": "stock",
        "keywords": {
            "stock", "obsolete", "liquidation", "inventaire", "provision",
            "rotation", "stockage", "entrepot", "immobilise", "immobilisation",
        },
    },
    {
        "id": "bfr",
        "keywords": {
            "dso", "bfr", "recouvrement", "client", "creance", "delai",
            "encaissement", "jours", "paiement", "retard", "tresorerie",
            "cash", "echeance",
        },
    },
    {
        "id": "marge",
        "keywords": {
            "marge", "marges",
            "fournisseur", "fournisseurs", "fourni",   # fourni = préfixe 6 chars de fournisseur(s)
            "achat", "achats",
            "cout", "couts",
            "negociation", "negocier", "reneg", "renegoc",  # renegoc = préfixe renegocier
            "approvisionnement", "approvi",
            "tarif", "tarifa", "tarifai",               # tarifa = préfixe tarifaire(s)
            "prix",
            "erosion",
            "rentabilite", "rentabi",
            "brute",
        },
    },
    {
        "id": "commercial",
        "keywords": {
            "commission", "commiss",                    # commiss = préfixe commissionnement
            "commissionnement",
            "commercial", "commercia", "commer",        # commer = préfixe commercial(e/s)
            "vente", "ventes",
            "performance", "perfor",
            "chiffre",
            "objectif",
            "incentive",
            "restructurer", "restru",
            "sous",
            "equipe",
            "force",
        },
    },
]


def _normalize_tokens(text: str) -> set[str]:
    """
    Normalise un texte en tokens : minuscules, sans accents, 3+ caractères,
    sans stop-words. Ajoute un préfixe de 6 chars pour les tokens ≥ 8 chars
    (couvre les variantes morphologiques : fournisseur/fournisseurs, etc.).
    """
    import re
    import unicodedata

    nfkd = unicodedata.normalize("NFD", text.lower())
    clean = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    raw_tokens = re.findall(r"[a-z]{3,}", clean)
    tokens: set[str] = set()
    for t in raw_tokens:
        if t not in _STOP_WORDS:
            tokens.add(t)
            if len(t) >= 8:
                tokens.add(t[:6])   # préfixe pour variantes morphologiques
    return tokens


def _semantic_bonus(decision_tokens: set[str], destroyer_tokens: set[str]) -> int:
    """
    Retourne 30 si décision et destructeur partagent le même groupe sémantique,
    0 sinon. S'arrête au premier groupe commun trouvé.
    """
    for group in _KEYWORD_GROUPS:
        kw = group["keywords"]
        if (decision_tokens & kw) and (destroyer_tokens & kw):
            return 30
    return 0


def _score_pair(decision_tokens: set[str], destroyer_tokens: set[str]) -> float:
    """Score de matching entre une décision et un destructeur (0–100+)."""
    if not decision_tokens or not destroyer_tokens:
        return 0.0
    overlap = len(decision_tokens & destroyer_tokens)
    base = overlap / max(len(decision_tokens), len(destroyer_tokens)) * 100
    return base + _semantic_bonus(decision_tokens, destroyer_tokens)


def _fmt_amount(amount: float | None) -> str:
    """Formate un montant en K€ ou M€."""
    if amount is None:
        return ""
    a = abs(amount)
    if a >= 1_000_000:
        return f"{a / 1_000_000:.1f} M€/an"
    return f"{a / 1_000:.0f} K€/an"


def _compute_reasoning_skeleton(
    decisions: list,   # List[ExecutiveDecision] from EDM
    destroyers: list,  # List[ValueDestroyer] from EDM
    data_quality,      # DataQualityInfo | None
    global_confidence: int,
) -> list[dict]:
    """
    Calcule le squelette déterministe de la chaîne de raisonnement EDX-001.

    - problem_source      : matching mots-clés décision → destructeur
    - matching_confidence : "HIGH" (≥40) | "LOW" (20–39) | "FALLBACK_INDEX" | None
    - decision_confidence : formule Python déterministe

    Aucun LLM. Retourne une liste de dicts (un par décision).
    Les champs LLM (why_this_decision, inaction_risk, confidence_explanation)
    sont laissés None ici — Agent 1 les complète.
    """
    anomaly_count = len(data_quality.anomalies) if (data_quality and data_quality.anomalies) else 0
    used_indices: set[int] = set()
    skeleton: list[dict] = []

    # Pré-calcul des tokens de chaque destructeur
    destroyer_token_sets = [_normalize_tokens(d.name) for d in destroyers]

    for i, decision in enumerate(decisions):
        decision_tokens = _normalize_tokens(decision.decision)
        best_score = 0.0
        best_j = -1

        for j, d_tokens in enumerate(destroyer_token_sets):
            if j in used_indices:
                continue
            score = _score_pair(decision_tokens, d_tokens)
            if score > best_score:
                best_score = score
                best_j = j

        # Assignation selon les seuils
        # HIGH ≥ 30 : inclut les matchs purement sémantiques (bonus = 30, overlap = 0)
        # LOW  15–29 : signal faible, pas de certitude
        if best_j >= 0 and best_score >= 30:
            d = destroyers[best_j]
            amount_str = _fmt_amount(d.annual_impact)
            problem_source = f"{d.name} — {amount_str}" if amount_str else d.name
            matching_confidence = "HIGH"
            used_indices.add(best_j)
        elif best_j >= 0 and best_score >= 15:
            d = destroyers[best_j]
            amount_str = _fmt_amount(d.annual_impact)
            problem_source = f"{d.name} — {amount_str}" if amount_str else d.name
            matching_confidence = "LOW"
            # LOW : le destructeur n'est pas marqué comme utilisé
            # (une autre décision pourrait mieux le capturer)
        else:
            # Fallback index : dernier recours, marqué explicitement
            if i < len(destroyers) and i not in used_indices:
                d = destroyers[i]
                amount_str = _fmt_amount(d.annual_impact)
                problem_source = f"{d.name} — {amount_str}" if amount_str else d.name
                matching_confidence = "FALLBACK_INDEX"
            else:
                problem_source = None
                matching_confidence = None

        # Confiance déterministe
        base = global_confidence
        if getattr(decision, "annual_impact", None) is None:
            base -= 15
        if getattr(decision, "owner", None) is None:
            base -= 5
        if getattr(decision, "timeline", None) is None:
            base -= 5
        roi = getattr(decision, "roi_score", 0.0) or 0.0
        roi_bonus = int(roi / 10 * 5)
        anomaly_penalty = min(anomaly_count * 2, 10)
        decision_confidence = max(50, min(95, base + roi_bonus - anomaly_penalty))

        skeleton.append({
            "decision_index":     i,
            "problem_source":     problem_source,
            "matching_confidence": matching_confidence,
            "decision_confidence": decision_confidence,
        })

    return skeleton


# ─── SYSTEM PROMPT — Agent 1 ──────────────────────────────────────────────────

_SYSTEM = """\
Tu es l'Executive Case Builder de Pepperyn — Version 2.

RÔLE UNIQUE : Transcrire fidèlement les données pré-analysées dans le schéma \
JSON officiel.

RÈGLES ABSOLUES — AUCUNE EXCEPTION :
1. Tu ne CALCULES rien. Tu ne MODIFIES aucun chiffre.
2. Tu ne CORRIGES pas un montant même s'il te semble inexact.
3. Donnée absente → null JSON (pas la chaîne "null", le type null JSON).
4. Tu ne CRÉES aucun KPI, décision, scénario ou risque absent des sources.
5. Aucune extrapolation. Aucune interpolation. Aucune invention.
6. Tu COPIES exactement les textes narratifs fournis.
7. Tu COPIES exactement les chiffres fournis (float, int).

─── CHAMPS EDX-001 — decision_reasoning ────────────────────────────────────
Les sources fournissent un "reasoning_skeleton" pré-calculé par Python pour
chaque décision (decision_index, problem_source, matching_confidence,
decision_confidence). Tu COPIES ces valeurs EXACTEMENT — règle 1 s'applique.

Tu GÉNÈRES les 3 champs narratifs suivants pour chaque entrée du reasoning :

why_this_decision :
  Commence OBLIGATOIREMENT par "Pepperyn recommande cette décision parce que".
  2 phrases maximum. Formule le lien causal entre le problem_source et la décision.
  Cite le gain chiffré (annual_impact de la décision).
  INTERDIT : "il est recommandé", "les données suggèrent", "il pourrait être".
  INTERDIT : répéter le libellé de la décision mot pour mot.

inaction_risk :
  1 à 2 phrases. Décrit ce qui se dégrade concrètement dans les 90 jours si
  cette décision n'est pas prise. Cite un horizon temporel précis ("À fin [mois]",
  "Dans 90 jours"). Chiffre la conséquence si les données le permettent.
  INTERDIT : phrases génériques sans horizon ni conséquence précise.

confidence_explanation :
  1 phrase. Explique POURQUOI le score decision_confidence est ce qu'il est.
  Cite ce qui renforce la confiance ET ce qui l'affaiblit (si applicable).
  Ne donne AUCUN chiffre que tu n'aurais pas reçu dans les sources.
  Tu n'évalues pas — tu expliques le score fourni.

─── CHAMPS EDX-002 — Raisonnement comparatif (Chemin A) ─────────────────────
Tu es un conseiller financier senior avec 20+ ans d'expérience PME. Pour chaque
décision prioritaire, tu conduis un raisonnement comparatif complet et honnête.

RÈGLES ANTI-HALLUCINATION (strictes) :
• Tu ne cites JAMAIS de chiffres que tu n'as pas reçus dans les sources.
• Tes alternatives sont ancrées dans le TYPE de problème identifié et la
  situation réelle de l'entreprise (taille, cash disponible, secteur, urgence).
• Tes critères d'élimination RÉFÉRENCENT des données sources (ex : "runway de
  11 semaines", "DSO à 87j", "EBITDA négatif", "CA de 3,2 M€").
• Si les données sont insuffisantes pour des alternatives crédibles :
  options_considered = [] (liste vide — ne jamais inventer).

options_considered :
  Liste de 3 à 5 alternatives sérieuses que tu as évaluées pour atteindre
  le même objectif que la décision retenue. Chaque alternative :
    option : description concise (1 ligne, ton affirmé — pas de conditionnel).
      Exemples : "Provisionnement comptable immédiat"
                 "Cession d'actifs immobilisés au prix marché"
                 "Renégociation des délais fournisseurs (J+60)"
    elimination_criterion : le critère PRÉCIS et FACTUEL qui écarte cette option.
      • PAS "moins efficace" ou "moins adapté" — un critère spécifique :
        timeline incompatible avec le runway cash, impact insuffisant vs objectif,
        capacité organisationnelle absente, risque contrepartie trop élevé,
        horizon de retour incompatible avec l'urgence identifiée, etc.
      • Le critère DOIT pouvoir être vérifié dans les données sources.
  Ces alternatives doivent être RÉELLEMENT distinctes — pas des variantes.
  Elles doivent être RÉALISTES pour une PME dans cette situation précise.

dominant_rationale :
  1 à 2 phrases. Pourquoi l'option retenue domine la MEILLEURE des alternatives
  écartées. Formule le trade-off exact entre les deux options.
  Structure : "L'option retenue [avantage concret chiffré ou qualifié] là où
  [alternative] [limite spécifique]. Le différentiel décisif est [facteur X]."
  Cite les deux options par leur nature — jamais "option A" et "option B".
  INTERDIT : arguments vagues ou génériques sans ancrage dans les données.

tipping_conditions :
  Liste de 1 à 2 conditions précises et observables qui renverseraient cette
  recommandation dans les 90 prochains jours. Chaque condition :
    condition : l'événement précis et observable (pas une tendance générale).
      Exemples : "Le client [Secteur] représente plus de 35% du stock concerné"
                 "La trésorerie passe sous 80 K€ avant le J+15 de l'exécution"
                 "Le prix de revient des matières premières augmente de >15%"
    horizon_days : dans combien de jours cette condition doit être surveillée
      (entre 30 et 90 selon la nature de la condition).
    alternative_recommendation : la décision de substitution concrète si la
      condition se réalise — 1 phrase, actionnable immédiatement.
─────────────────────────────────────────────────────────────────────────────

FORMAT DE SORTIE : JSON pur uniquement.
Aucun texte avant { ni après }. Aucun markdown. Aucun commentaire. \
Commence par { et termine par }.
"""


# ─── POINT D'ENTRÉE PUBLIC ────────────────────────────────────────────────────

async def build_executive_case(
    result_dict: dict,
    company_name: str = "",
) -> ExecutiveCaseJSON:
    """
    Agent 1 — construit l'ExecutiveCaseJSON.

    Stratégie :
      1. Pré-calcul Python (EDM) — déterministe, sans LLM.
      2. Appel Claude Opus — structure et valide dans le JSON officiel.
      3. Fallback Python pur — si Opus est indisponible.

    Args:
        result_dict : dict issu de AnalysisResult.model_dump().
        company_name: nom de la société pour la couverture.

    Returns:
        ExecutiveCaseJSON validé par Pydantic.
    """
    result_dict = result_dict or {}
    edm = build_executive_decision_model(result_dict)

    try:
        case = await _call_opus(result_dict, edm, company_name)
        logger.info("[ECB] ExecutiveCaseJSON produit par Claude Opus ✓")
        return case
    except Exception as exc:
        logger.warning("[ECB] Opus indisponible (%s) — fallback Python activé.", exc)
        return _python_mapper(result_dict, edm, company_name)


# ─── ADAPTERS : ExecutiveCaseJSON → (edm, result_dict) ───────────────────────
# Utilisés par les services export (PDF, PPTX) pour recevoir les données
# sous le format (edm, result_dict) dérivé du MÊME ExecutiveCaseJSON.
# Garantit la cohérence des chiffres entre PDF, PPTX et Excel.

def case_to_edm(case: ExecutiveCaseJSON):
    """
    Construit un ExecutiveDecisionModel depuis ExecutiveCaseJSON.
    AUCUN recalcul — tous les chiffres viennent du JSON.
    """
    from models.executive_decision_model import (
        CostOfInaction, ExecutiveDecision, ExecutionItem, Phase90Days,
    )
    from models.schemas import DataQualityInfo, ScenarioCase

    coi = CostOfInaction(
        per_year=case.cost_of_inaction.annual,
        per_month=case.cost_of_inaction.monthly,
        per_week=case.cost_of_inaction.weekly,
        per_day=case.cost_of_inaction.daily,
        per_hour=case.cost_of_inaction.hourly,
    )

    executive_decisions = [
        ExecutiveDecision(
            decision=d.decision,
            annual_impact=d.annual_impact,
            monthly_impact=d.monthly_impact,
            difficulty=d.difficulty,
            timeline=d.timeline,
            priority=d.priority,
            roi_score=d.roi_score,
            owner=d.owner,
            status=d.status,
        )
        for d in case.priority_decisions
    ]

    value_destroyers_edm = []
    from models.executive_decision_model import ValueDestroyer
    for v in case.value_destroyers:
        value_destroyers_edm.append(ValueDestroyer(
            name=v.name,
            annual_impact=v.annual_impact,
            monthly_impact=v.monthly_impact,
            trend=v.trend,
        ))

    execution_log = [
        ExecutionItem(
            decision=e.decision,
            owner=e.owner,
            impact=e.impact,
            due_date=e.due_date,
            difficulty=e.difficulty,
            roi_score=e.roi_score,
            status=e.status,
            review_date=e.review_date,
        )
        for e in case.execution_log
    ]

    # Roadmap phases
    roadmap_phases = []
    phase_labels = {"30": "Stabilize", "60": "Optimize", "90": "Accelerate"}
    for h_str in ["30", "60", "90"]:
        actions_list = case.roadmap_30_60_90.get(h_str, [])
        roadmap_phases.append(Phase90Days(
            horizon=h_str,
            phase_label=phase_labels[h_str],
            actions=[
                ExecutionItem(decision=str(a), status="To launch")
                for a in actions_list
            ],
        ))

    # Scenarios (legacy ScenarioCase format)
    scen_list: list[ScenarioCase] = []
    for key, sc_item in [
        ("best", case.scenarios.best),
        ("likely", case.scenarios.likely),
        ("worst", case.scenarios.worst),
    ]:
        if sc_item:
            scen_list.append(ScenarioCase(
                nom=key,
                label=sc_item.label,
                description=sc_item.description,
            ))

    # Data Quality
    dq_edm = DataQualityInfo(
        score_data=case.data_quality.score,
        anomalies=case.data_quality.anomalies,
        assumptions=case.data_quality.assumptions,
    )

    from models.executive_decision_model import ExecutiveDecisionModel
    return ExecutiveDecisionModel(
        executive_decision=executive_decisions[0] if executive_decisions else None,
        cost_of_inaction_summary=coi,
        health_score=case.health_score,
        executive_confidence=case.confidence_score,
        value_destroyers=value_destroyers_edm,
        cost_of_inaction=coi,
        executive_decisions=executive_decisions,
        executive_decisions_score=case.decisions_priority_score,
        roadmap_90_days=roadmap_phases,
        execution_log=execution_log,
        scenarios=scen_list,
        do_nothing_series=case.series.inaction,
        action_series=case.series.action,
        monthly_projection=case.series.equilibrium,
        data_quality=dq_edm,
    )


def case_to_result_dict(case: ExecutiveCaseJSON) -> dict:
    """
    Construit un result_dict compatible avec les services export depuis ExecutiveCaseJSON.
    Les données narratives et KPI proviennent toutes du JSON — aucun recalcul.
    """
    # KPI Dashboard (format legacy)
    ceo_dashboard = [
        {"label": k.label, "value": k.value, "status": k.status}
        for k in case.kpi_dashboard
    ]

    # Scenarios (format legacy — nom/label/description)
    scenarios = []
    for key, sc_item in [
        ("best", case.scenarios.best),
        ("likely", case.scenarios.likely),
        ("worst", case.scenarios.worst),
    ]:
        if sc_item:
            scenarios.append({
                "nom": key,
                "label": sc_item.label,
                "description": sc_item.description,
            })

    # Risks (format legacy)
    problemes_critiques = [
        {
            "description": r.description,
            "severite":    r.severity,
            "impact":      r.impact,
            "horizon":     r.horizon,
        }
        for r in case.major_risks
    ]

    # Roadmap (format plan_action_30_60_90)
    plan_action = [
        {
            "horizon": h,
            "actions": [{"action": a} for a in actions],
        }
        for h, actions in case.roadmap_30_60_90.items()
    ]

    # EDX-001 + EDX-002 — chaîne décisionnelle sérialisée pour les renderers
    decision_reasoning = [
        {
            # EDX-001 — déterministe
            "decision_index":         r.decision_index,
            "problem_source":         r.problem_source,
            "matching_confidence":    r.matching_confidence,
            "decision_confidence":    r.decision_confidence,
            # EDX-001 — LLM
            "why_this_decision":      r.why_this_decision,
            "inaction_risk":          r.inaction_risk,
            "confidence_explanation": r.confidence_explanation,
            # EDX-002 — raisonnement comparatif
            "options_considered": [
                {
                    "option":                o.option,
                    "elimination_criterion": o.elimination_criterion,
                }
                for o in (r.options_considered or [])
            ],
            "dominant_rationale":  r.dominant_rationale,
            "tipping_conditions": [
                {
                    "condition":                  t.condition,
                    "horizon_days":               t.horizon_days,
                    "alternative_recommendation": t.alternative_recommendation,
                }
                for t in (r.tipping_conditions or [])
            ],
        }
        for r in case.decision_reasoning
    ]

    return {
        "company_name":                case.company_name,
        "diagnostic_immediat":         case.executive_diagnosis,
        "resume_executif":             case.executive_diagnosis,
        "phrase_tension":              case.tension_phrase,
        "risque_inaction":             case.inaction_risk,
        "impact_financier_synthese":   case.structural_loss_statement,
        "score_global":                case.health_score,
        "score_confiance":             case.confidence_score,
        "score_rentabilite":           case.dimension_scores.rentabilite,
        "score_risque":                case.dimension_scores.risque,
        "score_structure":             case.dimension_scores.structure,
        "score_liquidite":             case.dimension_scores.liquidite,
        "niveau_urgence":              case.urgency_level,
        "creation_destruction_valeur": case.value_creation_statement,
        "ceo_dashboard":               ceo_dashboard,
        "scenarios":                   scenarios,
        "problemes_critiques":         problemes_critiques,
        "alertes":                     problemes_critiques,
        "plan_action_30_60_90":        plan_action,
        # EDX-001
        "decision_reasoning":          decision_reasoning,
    }


# ─── APPEL OPUS ───────────────────────────────────────────────────────────────

async def _call_opus(result_dict: dict, edm, company_name: str) -> ExecutiveCaseJSON:
    """Appelle Claude Opus et retourne un ExecutiveCaseJSON validé."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY absent")

    # Calcul déterministe du squelette AVANT l'appel LLM
    skeleton = _compute_reasoning_skeleton(
        decisions=edm.executive_decisions or [],
        destroyers=edm.value_destroyers or [],
        data_quality=edm.data_quality,
        global_confidence=result_dict.get("score_confiance") or 0,
    )

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(result_dict, edm, company_name, skeleton)

    resp = client.messages.create(
        model=MODEL_OPUS,
        max_tokens=8192,
        temperature=0,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = resp.content[0].text.strip()

    # Extraire le JSON si Opus a ajouté du markdown malgré la consigne
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    data = json.loads(raw)
    return ExecutiveCaseJSON(**data)


# ─── CONSTRUCTION DU PROMPT ───────────────────────────────────────────────────

def _build_user_prompt(result_dict: dict, edm, company_name: str, skeleton: list | None = None) -> str:
    """Assemble le prompt utilisateur avec toutes les données sources."""
    coi = edm.cost_of_inaction

    sources = {
        # Identité
        "company_name":    company_name or result_dict.get("company_name", ""),
        "analysis_date":   datetime.now().strftime("%d/%m/%Y"),
        "document_type":   "PREVISIONNEL",

        # Scores
        "confidence_score":          result_dict.get("score_confiance") or 0,
        "health_score":              result_dict.get("score_global"),
        "dimension_scores": {
            "rentabilite": result_dict.get("score_rentabilite"),
            "risque":      result_dict.get("score_risque"),
            "structure":   result_dict.get("score_structure"),
            "liquidite":   result_dict.get("score_liquidite"),
        },
        "decisions_priority_score":  edm.executive_decisions_score or 0.0,

        # COI (pré-calculé Python)
        "cost_of_inaction": {
            "annual":  coi.per_year   if coi else None,
            "monthly": coi.per_month  if coi else None,
            "weekly":  coi.per_week   if coi else None,
            "daily":   coi.per_day    if coi else None,
            "hourly":  coi.per_hour   if coi else None,
        },

        # Narratifs LLM
        "executive_diagnosis":       (
            result_dict.get("diagnostic_immediat")
            or result_dict.get("resume_executif")
            or result_dict.get("synthese")
        ),
        "tension_phrase":            result_dict.get("phrase_tension"),
        "inaction_risk":             result_dict.get("risque_inaction"),
        "structural_loss_statement": result_dict.get("impact_financier_synthese"),
        "structural_loss_value":     parse_amount_eur(result_dict.get("impact_financier_synthese")),
        "urgency_level":             result_dict.get("niveau_urgence"),
        "value_creation_statement":  result_dict.get("creation_destruction_valeur"),

        # KPI Dashboard
        "kpi_dashboard": _extract_kpi(result_dict.get("ceo_dashboard") or []),

        # Destructeurs de valeur (pré-calculés Python)
        "value_destroyers": [
            {
                "name":           v.name,
                "annual_impact":  v.annual_impact,
                "monthly_impact": v.monthly_impact,
                "trend":          v.trend,
            }
            for v in edm.value_destroyers
        ],

        # Décisions prioritaires (pré-calculées Python)
        "priority_decisions": [
            {
                "decision":       d.decision,
                "annual_impact":  d.annual_impact,
                "monthly_impact": d.monthly_impact,
                "difficulty":     d.difficulty,
                "timeline":       d.timeline,
                "priority":       d.priority,
                "roi_score":      d.roi_score,
                "owner":          d.owner,
                "status":         d.status,
            }
            for d in edm.executive_decisions
        ],

        # Roadmap
        "roadmap_30_60_90": _extract_roadmap(edm.roadmap_90_days),

        # Log d'exécution
        "execution_log": [
            {
                "decision":    e.decision,
                "owner":       e.owner,
                "impact":      e.impact,
                "due_date":    e.due_date,
                "difficulty":  e.difficulty,
                "roi_score":   e.roi_score,
                "status":      e.status,
                "review_date": e.review_date,
            }
            for e in edm.execution_log
        ],

        # Séries temporelles (pré-calculées Python)
        "series": {
            "action":      edm.action_series      or [],
            "inaction":    edm.do_nothing_series  or [],
            "equilibrium": edm.monthly_projection or [],
        },

        # Scénarios
        "scenarios": _extract_scenarios(result_dict, edm),

        # Risques
        "major_risks": _extract_risks(result_dict),

        # Qualité des données
        "data_quality": _extract_dq(result_dict, edm),

        # ── EDX-001 : Squelette déterministe (Python pur) ─────────────────────
        # problem_source et decision_confidence sont PRÉ-CALCULÉS et VERROUILLÉS.
        # Tu COPIES ces valeurs exactement (règle 1).
        # Tu GÉNÈRES why_this_decision, inaction_risk, confidence_explanation.
        "reasoning_skeleton": skeleton or [],
    }

    return (
        "Voici toutes les données sources pré-analysées. "
        "Transcris-les EXACTEMENT dans le schéma JSON officiel ci-dessous. "
        "Ne modifie AUCUN chiffre. Ne complète AUCUNE donnée absente (null uniquement).\n\n"
        "=== DONNÉES SOURCES ===\n"
        + json.dumps(sources, ensure_ascii=False, indent=2)
        + "\n\n=== SCHÉMA ATTENDU ===\n"
        + json.dumps(_schema_example(), ensure_ascii=False, indent=2)
    )


# ─── HELPERS D'EXTRACTION ─────────────────────────────────────────────────────

def _extract_kpi(raw: list) -> list:
    items = []
    for k in raw:
        if isinstance(k, dict):
            items.append({"label": k.get("label", ""), "value": k.get("value", ""),
                          "status": k.get("status")})
        else:
            items.append({"label": getattr(k, "label", ""), "value": getattr(k, "value", ""),
                          "status": getattr(k, "status", None)})
    return items


def _extract_roadmap(phases: list) -> dict:
    roadmap: dict[str, list[str]] = {"30": [], "60": [], "90": []}
    for phase in (phases or []):
        h = str(getattr(phase, "horizon", ""))
        if h in roadmap:
            roadmap[h] = [getattr(a, "decision", str(a))[:100] for a in (phase.actions or [])]
    return roadmap


def _extract_scenarios(result_dict: dict, edm) -> dict:
    scenarios_raw = result_dict.get("scenarios") or edm.scenarios or []
    result = {"best": None, "likely": None, "worst": None}
    for sc in scenarios_raw:
        if isinstance(sc, dict):
            nom, lbl, desc = sc.get("nom", ""), sc.get("label", ""), sc.get("description", "")
        else:
            nom = getattr(sc, "nom", "")
            lbl = getattr(sc, "label", "")
            desc = getattr(sc, "description", "")
        n = nom.lower()
        entry = {"label": lbl or nom, "description": desc or ""}
        if "best" in n or "meilleur" in n:
            result["best"] = entry
        elif "likely" in n or "probable" in n or "most" in n:
            result["likely"] = entry
        elif "worst" in n or "pire" in n:
            result["worst"] = entry
    return result


def _extract_risks(result_dict: dict) -> list:
    raw = result_dict.get("problemes_critiques") or result_dict.get("alertes") or []
    risks = []
    for r in raw[:6]:
        if isinstance(r, dict):
            risks.append({
                "description": r.get("description", str(r)),
                "severity":    r.get("severite", "Moyen"),
                "impact":      r.get("impact", "Modéré"),
                "horizon":     r.get("horizon", "Court terme"),
            })
        else:
            risks.append({
                "description": str(r)[:200],
                "severity":    "Moyen",
                "impact":      "Modéré",
                "horizon":     "Court terme",
            })
    return risks


def _extract_dq(result_dict: dict, edm) -> dict:
    dq = edm.data_quality
    return {
        "score":       dq.score_data  if dq else (result_dict.get("score_confiance") or 70),
        "anomalies":   (dq.anomalies  if dq else (result_dict.get("coaching_issues") or [])),
        "assumptions": (dq.assumptions if dq else []),
        "limits":      [],
    }


def _schema_example() -> dict:
    """Exemple de schéma cible montrant la structure attendue."""
    return {
        "company_name": "", "analysis_date": "", "document_type": "PREVISIONNEL",
        "confidence_score": 0, "health_score": None,
        "dimension_scores": {"rentabilite": None, "risque": None, "structure": None, "liquidite": None},
        "decisions_priority_score": 0.0,
        "cost_of_inaction": {"annual": None, "monthly": None, "weekly": None, "daily": None, "hourly": None},
        "executive_diagnosis": None, "tension_phrase": None, "inaction_risk": None,
        "structural_loss_statement": None, "structural_loss_value": None,
        "urgency_level": None, "value_creation_statement": None,
        "kpi_dashboard": [{"label": "", "value": "", "status": None}],
        "value_destroyers": [{"name": "", "annual_impact": None, "monthly_impact": None, "trend": None}],
        "priority_decisions": [{"decision": "", "annual_impact": None, "monthly_impact": None,
                                "difficulty": None, "timeline": None, "priority": "",
                                "roi_score": 0.0, "owner": None, "status": ""}],
        "roadmap_30_60_90": {"30": [], "60": [], "90": []},
        "execution_log": [{"decision": "", "owner": None, "impact": None, "due_date": None,
                           "difficulty": None, "roi_score": 0.0, "status": "", "review_date": None}],
        "series": {"action": [], "inaction": [], "equilibrium": []},
        "scenarios": {
            "best":   {"label": "", "description": ""},
            "likely": {"label": "", "description": ""},
            "worst":  {"label": "", "description": ""},
        },
        "major_risks": [{"description": "", "severity": "", "impact": "", "horizon": ""}],
        "data_quality": {"score": 70, "anomalies": [], "assumptions": [], "limits": []},
        # EDX-001 + EDX-002 — decision_reasoning
        # EDX-001 : Copie decision_index / problem_source / matching_confidence /
        #           decision_confidence depuis reasoning_skeleton.
        #           Génère why_this_decision / inaction_risk / confidence_explanation.
        # EDX-002 : Génère options_considered / dominant_rationale / tipping_conditions.
        #           Voir règles anti-hallucination dans le prompt ci-dessus.
        "decision_reasoning": [{
            "decision_index":         0,
            "problem_source":         None,   # COPIER depuis reasoning_skeleton
            "matching_confidence":    None,   # COPIER depuis reasoning_skeleton
            "decision_confidence":    None,   # COPIER depuis reasoning_skeleton
            "why_this_decision":      None,   # GÉNÉRER EDX-001 — voix Pepperyn
            "inaction_risk":          None,   # GÉNÉRER EDX-001 — horizon 90 jours
            "confidence_explanation": None,   # GÉNÉRER EDX-001 — expliquer le score
            # EDX-002 — raisonnement comparatif (Chemin A)
            "options_considered": [           # GÉNÉRER — alternatives évaluées et écartées
                {
                    "option": "Description alternative évaluée",
                    "elimination_criterion": "Critère précis ancré dans les données"
                }
            ],
            "dominant_rationale": None,       # GÉNÉRER — pourquoi l'option retenue domine
            "tipping_conditions": [           # GÉNÉRER — conditions de révision
                {
                    "condition": "Événement précis et observable",
                    "horizon_days": 90,
                    "alternative_recommendation": "Décision de substitution concrète"
                }
            ],
        }],
    }


# ─── FALLBACK PYTHON PUR ──────────────────────────────────────────────────────

def _python_mapper(result_dict: dict, edm, company_name: str) -> ExecutiveCaseJSON:
    """
    Mapping Python direct — aucun LLM.
    Utilisé quand Opus est indisponible.
    Garantit que les livrables sont toujours générables.
    """
    coi = edm.cost_of_inaction

    # Scénarios
    scenarios_raw = result_dict.get("scenarios") or edm.scenarios or []
    scen_best = scen_likely = scen_worst = None
    for sc in scenarios_raw:
        if isinstance(sc, dict):
            nom, lbl, desc = sc.get("nom", ""), sc.get("label", ""), sc.get("description", "")
        else:
            nom = getattr(sc, "nom", "")
            lbl = getattr(sc, "label", "")
            desc = getattr(sc, "description", "")
        n = nom.lower()
        item = ScenarioItem(label=lbl or nom, description=desc or "")
        if "best" in n or "meilleur" in n:
            scen_best = item
        elif "likely" in n or "probable" in n or "most" in n:
            scen_likely = item
        elif "worst" in n or "pire" in n:
            scen_worst = item

    # KPI Dashboard
    kpi_cards: list[KPICard] = []
    for k in (result_dict.get("ceo_dashboard") or []):
        if isinstance(k, dict):
            kpi_cards.append(KPICard(label=k.get("label", ""),
                                     value=k.get("value", ""),
                                     status=k.get("status")))
        else:
            kpi_cards.append(KPICard(label=getattr(k, "label", ""),
                                     value=getattr(k, "value", ""),
                                     status=getattr(k, "status", None)))

    # Destructeurs de valeur
    destroyers: list[ValueDestroyerItem] = [
        ValueDestroyerItem(name=v.name, annual_impact=v.annual_impact,
                           monthly_impact=v.monthly_impact, trend=v.trend)
        for v in edm.value_destroyers
    ]

    # Décisions
    decisions: list[PriorityDecisionItem] = [
        PriorityDecisionItem(
            decision=d.decision, annual_impact=d.annual_impact,
            monthly_impact=d.monthly_impact, difficulty=d.difficulty,
            timeline=d.timeline, priority=d.priority, roi_score=d.roi_score,
            owner=d.owner, status=d.status,
        )
        for d in edm.executive_decisions
    ]

    # Log d'exécution
    exec_log: list[ExecutionLogItem] = [
        ExecutionLogItem(
            decision=e.decision, owner=e.owner, impact=e.impact,
            due_date=e.due_date, difficulty=e.difficulty, roi_score=e.roi_score,
            status=e.status, review_date=e.review_date,
        )
        for e in edm.execution_log
    ]

    # Roadmap
    roadmap: dict[str, list[str]] = {"30": [], "60": [], "90": []}
    for phase in (edm.roadmap_90_days or []):
        h = str(getattr(phase, "horizon", ""))
        if h in roadmap:
            roadmap[h] = [getattr(a, "decision", str(a)) for a in (phase.actions or [])]

    # Risques
    risks: list[RiskItem] = []
    for r in (_extract_risks(result_dict)):
        risks.append(RiskItem(description=r["description"], severity=r["severity"],
                              impact=r["impact"], horizon=r["horizon"]))

    # Qualité des données
    dq_raw = edm.data_quality
    dq = DataQuality(
        score=dq_raw.score_data if dq_raw else (result_dict.get("score_confiance") or 70),
        anomalies=dq_raw.anomalies if dq_raw else (result_dict.get("coaching_issues") or []),
        assumptions=dq_raw.assumptions if dq_raw else [],
        limits=[],
    )

    # EDX-001 — squelette déterministe (pas de LLM en fallback)
    skeleton = _compute_reasoning_skeleton(
        decisions=edm.executive_decisions or [],
        destroyers=edm.value_destroyers or [],
        data_quality=edm.data_quality,
        global_confidence=result_dict.get("score_confiance") or 0,
    )
    reasoning_items = [
        DecisionReasoning(
            decision_index=s["decision_index"],
            problem_source=s["problem_source"],
            matching_confidence=s["matching_confidence"],
            decision_confidence=s["decision_confidence"],
            # LLM fields absent en fallback — None
            why_this_decision=None,
            inaction_risk=None,
            confidence_explanation=None,
        )
        for s in skeleton
    ]

    return ExecutiveCaseJSON(
        company_name=company_name or result_dict.get("company_name", ""),
        analysis_date=datetime.now().strftime("%d/%m/%Y"),
        document_type="PREVISIONNEL",
        confidence_score=result_dict.get("score_confiance") or 0,
        health_score=result_dict.get("score_global"),
        dimension_scores=DimensionScores(
            rentabilite=result_dict.get("score_rentabilite"),
            risque=result_dict.get("score_risque"),
            structure=result_dict.get("score_structure"),
            liquidite=result_dict.get("score_liquidite"),
        ),
        decisions_priority_score=edm.executive_decisions_score or 0.0,
        cost_of_inaction=COIBreakdown(
            annual=coi.per_year    if coi else None,
            monthly=coi.per_month  if coi else None,
            weekly=coi.per_week    if coi else None,
            daily=coi.per_day      if coi else None,
            hourly=coi.per_hour    if coi else None,
        ),
        executive_diagnosis=(
            result_dict.get("diagnostic_immediat")
            or result_dict.get("resume_executif")
            or result_dict.get("synthese")
        ),
        tension_phrase=result_dict.get("phrase_tension"),
        inaction_risk=result_dict.get("risque_inaction"),
        structural_loss_statement=result_dict.get("impact_financier_synthese"),
        structural_loss_value=parse_amount_eur(result_dict.get("impact_financier_synthese")),
        urgency_level=result_dict.get("niveau_urgence"),
        value_creation_statement=result_dict.get("creation_destruction_valeur"),
        kpi_dashboard=kpi_cards,
        value_destroyers=destroyers,
        priority_decisions=decisions,
        roadmap_30_60_90=roadmap,
        execution_log=exec_log,
        series=ProjectionSeries(
            action=edm.action_series       or [],
            inaction=edm.do_nothing_series or [],
            equilibrium=edm.monthly_projection or [],
        ),
        scenarios=Scenarios(best=scen_best, likely=scen_likely, worst=scen_worst),
        major_risks=risks,
        data_quality=dq,
        decision_reasoning=reasoning_items,
    )
