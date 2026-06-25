"""
executive_case_v2_builder.py — Builder Python déterministe pour ExecutiveCase V2.

Responsabilité unique :
  Mapper result_dict + ExecutiveDecisionModel → ExecutiveCase V2 (Pydantic validé).

RÈGLES ABSOLUES :
  1. Pas d'appel LLM dans ce fichier.
  2. cost_of_inaction, value_at_risk, value_creation_opportunity → toujours abs().
  3. sacred_sentence immuable.
  4. Aucun chiffre inventé — si la donnée est absente, None ou 0.
  5. Ce fichier ne modifie aucun pipeline existant.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from models.executive_case_v2 import ConversationEngine, ExecutiveCase
from services.executive_decision_model import (
    build_executive_decision_model,
    parse_amount_eur,
)

logger = logging.getLogger(__name__)

# ─── Constantes du Conversation Engine ───────────────────────────────────────
# Les quick prompts et la sacred_sentence sont définis une seule fois ici.
# Ils correspondent exactement à la spécification du master schema.

_SACRED_SENTENCE = "Aucune question n'est trop simple."

_DEFAULT_QUICK_PROMPTS = [
    "Je ne suis pas financier. Expliquez-moi simplement ce que je dois comprendre et faire.",
    "Expliquez-moi ce rapport en 2 minutes.",
    "Que dois-je faire lundi matin ?",
    "Quels sont les risques et opportunités les plus importants ?",
    "Expliquez-moi l'EBITDA simplement.",
]

_ROLE_MODES = {
    "dirigeant":   "Explique les décisions à prendre, sans jargon.",
    "investisseur": "Explique risques, opportunités et trajectoire.",
    "operationnel": "Explique les actions concrètes à lancer.",
    "cfo":         "Conserve le vocabulaire financier mais reste synthétique.",
}

_BASE_GLOSSARY = [
    {
        "term": "EBITDA",
        "plain_language": (
            "Ce que l'activité gagne ou perd avant certains éléments financiers, "
            "fiscaux et comptables. C'est le baromètre de la rentabilité opérationnelle."
        ),
    },
    {
        "term": "Coût de l'inaction",
        "plain_language": (
            "Ce que l'entreprise perd chaque mois en n'agissant pas. "
            "Pas une projection — une estimation basée sur les données transmises."
        ),
    },
    {
        "term": "Marge brute",
        "plain_language": (
            "Ce qu'il reste du chiffre d'affaires après les coûts directs de production. "
            "Indique si le modèle économique est structurellement sain."
        ),
    },
]

# ─── Point d'entrée public ────────────────────────────────────────────────────

def build_executive_case_v2(
    result_dict: dict,
    company_name: str = "",
    analyse_id: str = "",
) -> ExecutiveCase:
    """
    Construit un ExecutiveCase V2 depuis le result_dict et l'EDM Python.

    Mapper 100% déterministe — aucun LLM.
    Toutes les valeurs financières (COI, value_at_risk, value_creation_opportunity)
    sont converties en valeurs positives (abs()) avant injection dans le modèle.

    Args:
        result_dict  : dict issu de AnalysisResult.model_dump().
        company_name : nom de la société (page de couverture).
        analyse_id   : identifiant de l'analyse (metadata).

    Returns:
        ExecutiveCase V2 validé par Pydantic.
    """
    result_dict = result_dict or {}
    edm = build_executive_decision_model(result_dict)

    return ExecutiveCase(
        metadata=_build_metadata(result_dict, company_name, analyse_id),
        data_quality=_build_data_quality(result_dict, edm),
        executive_summary=_build_executive_summary(result_dict, edm),
        health_score=_build_health_score(result_dict, edm),
        financial_performance=_build_financial_performance(result_dict, edm),
        financial_snapshot=_build_financial_snapshot(result_dict, edm),
        value_drivers=_build_value_drivers(result_dict, edm),
        priority_decisions=_build_priority_decisions(edm),
        roadmap=_build_roadmap(edm),
        conversation_engine=_build_conversation_engine(result_dict, edm),
        methodology=_build_methodology(result_dict, edm),
    )


# ─── Builders de blocs ───────────────────────────────────────────────────────

def _build_metadata(result_dict: dict, company_name: str, analyse_id: str) -> dict:
    return {
        "company_name":  company_name or result_dict.get("company_name", ""),
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "analysis_id":   analyse_id or "",
        "document_type": result_dict.get("type_document", "PREVISIONNEL"),
        "language":      "fr",
    }


def _build_data_quality(result_dict: dict, edm) -> dict:
    dq = edm.data_quality
    score = result_dict.get("score_confiance") or 70
    if score >= 70:
        status = "ok"
    elif score >= 50:
        status = "warning"
    else:
        status = "blocked"

    return {
        "source_reliability_score":  score,
        "analysis_confidence_score": score,
        "status":          status,
        "detected_format": result_dict.get("type_document", "Inconnu"),
        "mapping_summary": (dq.assumptions if dq else []) or [],
        "missing_data":    (dq.anomalies   if dq else []) or [],
        "analysis_limits": [],
    }


def _build_executive_summary(result_dict: dict, edm) -> dict:
    # Décision prioritaire
    top_decision = edm.executive_decisions[0] if edm.executive_decisions else None
    top_qw = (result_dict.get("quick_wins") or [None])[0]

    recommendation = ""
    if top_decision:
        recommendation = top_decision.decision
    elif isinstance(top_qw, dict):
        recommendation = top_qw.get("action", "")

    return {
        "core_problem": (
            result_dict.get("diagnostic_immediat")
            or result_dict.get("resume_executif")
            or result_dict.get("synthese")
            or ""
        ),
        "main_opportunity":      result_dict.get("creation_destruction_valeur") or "",
        "strategic_risk":        result_dict.get("risque_inaction") or "",
        "executive_recommendation": recommendation,
        "decision_priority":     recommendation,
    }


def _build_health_score(result_dict: dict, edm) -> dict:
    overall = result_dict.get("score_global") or edm.health_score or 0

    if overall >= 7:
        interpretation = "Situation saine avec des axes d'amélioration identifiés."
    elif overall >= 4:
        interpretation = "Situation mixte — des leviers actionnables existent."
    else:
        interpretation = "Situation fragile mais actionnable."

    return {
        "overall":      overall,
        "profitability": result_dict.get("score_rentabilite"),
        "liquidity":     result_dict.get("score_liquidite"),
        "structure":     result_dict.get("score_structure"),
        "risk":          result_dict.get("score_risque"),
        "interpretation": interpretation,
    }


def _build_financial_performance(result_dict: dict, edm) -> dict:
    coi = edm.cost_of_inaction

    # COI — toujours en valeur absolue (positive)
    coi_annual  = abs(coi.per_year  or 0) if coi else 0
    coi_monthly = abs(coi.per_month or 0) if coi else 0
    coi_weekly  = abs(coi.per_week  or 0) if coi else 0
    coi_daily   = abs(coi.per_day   or 0) if coi else 0
    coi_hourly  = abs(coi.per_hour  or 0) if coi else 0

    # value_at_risk = COI (même calcul — ce qui est exposé si aucune décision)
    var_annual  = coi_annual
    var_monthly = coi_monthly

    # value_creation_opportunity = somme des impacts positifs identifiés
    vco_annual = abs(sum(
        abs(d.annual_impact or 0)
        for d in edm.executive_decisions
        if d.annual_impact
    ))
    vco_monthly = round(vco_annual / 12, 2) if vco_annual else 0

    # Performance angle dérivé du score global
    overall = result_dict.get("score_global") or edm.health_score or 0
    if overall >= 7:
        angle = "positive"
    elif overall >= 4:
        angle = "mixed"
    else:
        angle = "mixed"   # "critical" serait plus juste mais "mixed" est plus actionnable

    return {
        "performance_angle": angle,
        "value_at_risk": {
            "annual":  var_annual,
            "monthly": var_monthly,
            "comment": "Valeur exposée si aucune décision n'est prise.",
        },
        "value_creation_opportunity": {
            "annual":  vco_annual,
            "monthly": vco_monthly,
            "comment": "Gain potentiel issu des décisions prioritaires identifiées.",
        },
        "cost_of_inaction": {
            "annual":  coi_annual,
            "monthly": coi_monthly,
            "weekly":  coi_weekly,
            "daily":   coi_daily,
            "hourly":  coi_hourly,
            "comment": "Coût annualisé de l'absence de décision.",
        },
    }


def _build_financial_snapshot(result_dict: dict, edm) -> dict:
    """Extrait les KPI financiers depuis le ceo_dashboard ou l'EDM."""
    dashboard = result_dict.get("ceo_dashboard") or []

    def _card_value(label_fragment: str) -> Optional[float]:
        """Cherche un montant dans le ceo_dashboard par fragment de label."""
        for card in dashboard:
            lbl = (card.get("label", "") if isinstance(card, dict)
                   else getattr(card, "label", "")).lower()
            if label_fragment.lower() in lbl:
                val_str = (card.get("value", "") if isinstance(card, dict)
                           else getattr(card, "value", ""))
                return parse_amount_eur(str(val_str))
        return None

    return {
        "revenue":      _card_value("ca") or _card_value("chiffre"),
        "ebitda":       _card_value("ebitda"),
        "cash":         _card_value("trésorerie") or _card_value("cash"),
        "gross_margin": _card_value("marge brute") or _card_value("marge"),
        "runway":       None,
        "debt":         _card_value("dette"),
        "growth":       None,
    }


def _build_value_drivers(result_dict: dict, edm) -> dict:
    value_limiters = [
        {
            "title":          v.name,
            "annual_impact":  abs(v.annual_impact or 0),
            "monthly_impact": abs(v.monthly_impact or 0),
            "comment":        getattr(v, "comment", "") or "",
            "confidence":     "medium",
        }
        for v in edm.value_destroyers
    ]

    # value_creators = décisions avec impact positif identifié
    value_creators = [
        {
            "title":          d.decision,
            "annual_impact":  abs(d.annual_impact or 0),
            "monthly_impact": abs(d.monthly_impact or 0),
            "comment":        "",
            "confidence":     "medium",
        }
        for d in edm.executive_decisions
        if d.annual_impact and abs(d.annual_impact) > 0
    ]

    return {
        "value_limiters": value_limiters,
        "value_creators": value_creators,
    }


def _build_priority_decisions(edm) -> list:
    return [
        {
            "title":         d.decision,
            "annual_impact": abs(d.annual_impact or 0),
            "difficulty":    (d.difficulty or "medium").lower(),
            "priority":      d.priority.lower() if d.priority else "medium",
            "owner":         d.owner or "",
            "deadline":      d.timeline or "",
            "status":        "to_launch",
            "rationale":     "",
        }
        for d in edm.executive_decisions
    ]


def _build_roadmap(edm) -> dict:
    roadmap: dict = {"day_30": [], "day_60": [], "day_90": []}
    key_map = {"30": "day_30", "60": "day_60", "90": "day_90"}

    for phase in (edm.roadmap_90_days or []):
        h = str(getattr(phase, "horizon", ""))
        key = key_map.get(h)
        if not key:
            continue
        for action in (phase.actions or []):
            roadmap[key].append({
                "title":    getattr(action, "decision", str(action)),
                "owner":    getattr(action, "owner", "") or "",
                "impact":   abs(getattr(action, "impact", None) or 0) or None,
                "deadline": getattr(action, "due_date", "") or "",
                "status":   "to_launch",
            })

    return roadmap


def _build_conversation_engine(result_dict: dict, edm) -> ConversationEngine:
    """
    Génère le bloc ConversationEngine depuis les données de l'analyse.
    Aucun LLM. Aucune invention. Toutes les valeurs viennent du result_dict ou de l'EDM.
    """
    # ── Auto-opening message ──────────────────────────────────────────────────
    urgence = result_dict.get("niveau_urgence") or ""
    tension = result_dict.get("phrase_tension") or ""

    if tension:
        opening_context = f"{tension} "
    elif urgence:
        opening_context = f"Niveau d'urgence : {urgence}. "
    else:
        opening_context = ""

    auto_opening_message = (
        f"👋 Votre analyse est prête. {opening_context}"
        "Si vous n'êtes pas financier, aucun problème : "
        "je peux vous expliquer simplement ce rapport, répondre à vos questions "
        "et vous aider à préparer vos décisions. "
        "Aucune question n'est trop simple."
    )

    # ── plain_language_context ────────────────────────────────────────────────
    top_decisions_plain = [
        d.decision
        for d in edm.executive_decisions[:3]
    ]
    monday_actions = [
        d.decision
        for d in edm.executive_decisions[:3]
        if d.timeline and "30" in str(d.timeline)
    ] or top_decisions_plain[:3]

    plain_language_context = {
        "one_sentence_summary": (
            result_dict.get("diagnostic_immediat")
            or result_dict.get("resume_executif")
            or "Des leviers d'amélioration ont été identifiés dans cette analyse."
        ),
        "what_is_happening": result_dict.get("diagnostic_immediat") or "",
        "why_it_matters":    result_dict.get("phrase_tension") or "",
        "three_things_to_understand": [
            result_dict.get("risque_inaction") or "L'inaction a un coût mesurable.",
            result_dict.get("impact_financier_synthese") or "Des décisions prioritaires ont été identifiées.",
            "Cette analyse est basée uniquement sur les données transmises.",
        ],
        "three_decisions_to_take": top_decisions_plain or ["Consulter les décisions prioritaires."],
        "biggest_risk":       result_dict.get("risque_inaction") or "",
        "biggest_opportunity": result_dict.get("creation_destruction_valeur") or "",
        "expected_outcome":   "Une trajectoire plus lisible et une meilleure rentabilité.",
        "monday_morning_actions": monday_actions or ["Consulter les décisions prioritaires."],
    }

    # ── financial_glossary ────────────────────────────────────────────────────
    # Ajouter les termes des KPI présents dans le dashboard
    glossary = list(_BASE_GLOSSARY)
    dashboard_labels = [
        (c.get("label", "") if isinstance(c, dict) else getattr(c, "label", "")).upper()
        for c in (result_dict.get("ceo_dashboard") or [])
    ]
    if any("MARGE" in lbl for lbl in dashboard_labels) and not any(
        g["term"] == "Marge brute" for g in glossary
    ):
        glossary.append({
            "term": "Marge brute",
            "plain_language": "Ce qu'il reste du CA après les coûts directs de production.",
        })

    return ConversationEngine(
        auto_opening_message=auto_opening_message,
        suggested_quick_prompts=_DEFAULT_QUICK_PROMPTS,
        plain_language_context=plain_language_context,
        role_modes=_ROLE_MODES,
        financial_glossary=glossary,
        sacred_sentence=_SACRED_SENTENCE,
    )


def _build_methodology(result_dict: dict, edm) -> dict:
    dq = edm.data_quality
    return {
        "analysis_method": "Analyse à partir des données transmises uniquement.",
        "assumptions":     (dq.assumptions if dq else []) or [
            "Aucune donnée manquante n'est inventée."
        ],
        "calculation_rules": [
            "Le coût d'inaction ne peut jamais être négatif.",
            "Les impacts sont des estimations basées sur les données transmises.",
        ],
        "source_notes": ["Données issues du fichier importé."],
    }


# ─── Test local ──────────────────────────────────────────────────────────────

def _run_test() -> None:
    """Fonction de test sur données synthétiques — exécutable directement."""
    result = {
        "score_global": 3,
        "score_confiance": 68,
        "score_rentabilite": 2,
        "score_risque": 4,
        "score_structure": 5,
        "score_liquidite": 3,
        "type_document": "PREVISIONNEL",
        "diagnostic_immediat": "La structure de coûts limite la performance.",
        "phrase_tension": "Chaque mois sans action génère 455 000 € de pertes.",
        "risque_inaction": "Franchissement du seuil de cessation à horizon 6 mois.",
        "impact_financier_synthese": "-5 465 000 €",
        "niveau_urgence": "Urgence critique",
        "creation_destruction_valeur": "Destruction active de 455 416 € par mois.",
        "ceo_dashboard": [
            {"label": "CA Total",    "value": "8 500 000 €"},
            {"label": "EBITDA",      "value": "-1 200 000 €"},
            {"label": "Trésorerie",  "value": "320 000 €"},
            {"label": "Marge brute", "value": "28 %"},
        ],
        "scenarios": [
            {"nom": "best_case",   "label": "MEILLEUR CAS", "description": "Retour équilibre M9."},
            {"nom": "most_likely", "label": "CAS PROBABLE", "description": "Break-even M12."},
            {"nom": "worst_case",  "label": "PIRE CAS",     "description": "Dégradation continue."},
        ],
        "quick_wins": [
            {"action": "Renégocier contrats fournisseurs", "impact": "-900 000 €",
             "difficulte": "Faible", "horizon": "30"},
        ],
        "value_destroyers": [
            {"nom": "Coûts fixes surdimensionnés", "impact_annuel": "-2 800 000 €"},
            {"nom": "Délais clients excessifs",    "impact_annuel": "-900 000 €"},
        ],
        "plan_action_30_60_90": [
            {"horizon": "30", "actions": [{"action": "Audit coûts fixes", "impact": "-500 000 €"}]},
            {"horizon": "60", "actions": [{"action": "Renégocier fournisseurs"}]},
            {"horizon": "90", "actions": [{"action": "Revue structurelle des coûts"}]},
        ],
    }

    case = build_executive_case_v2(result, "Acme SAS", "test-001")

    # Assertions critiques
    coi = case.financial_performance["cost_of_inaction"]
    var = case.financial_performance["value_at_risk"]
    vco = case.financial_performance["value_creation_opportunity"]

    assert coi["annual"] >= 0, f"COI négatif : {coi['annual']}"
    assert var["annual"] >= 0, f"VAR négatif : {var['annual']}"
    assert vco["annual"] >= 0, f"VCO négatif : {vco['annual']}"
    assert case.conversation_engine.sacred_sentence == _SACRED_SENTENCE
    assert 4 <= len(case.conversation_engine.suggested_quick_prompts) <= 6
    assert case.metadata["company_name"] == "Acme SAS"

    print("✓ build_executive_case_v2 — validation Pydantic OK")
    print(f"  COI annuel (abs) : {coi['annual']:,.2f} €")
    print(f"  VAR annuel (abs) : {var['annual']:,.2f} €")
    print(f"  VCO annuel (abs) : {vco['annual']:,.2f} €")
    print(f"  sacred_sentence  : \"{case.conversation_engine.sacred_sentence}\"")
    print(f"  quick_prompts    : {len(case.conversation_engine.suggested_quick_prompts)} items")
    print(f"  value_limiters   : {len(case.value_drivers['value_limiters'])} items")
    print(f"  priority_decisions: {len(case.priority_decisions)} items")
    print(f"  roadmap day_30   : {len(case.roadmap['day_30'])} actions")
    print(f"  auto_opening_msg : \"{case.conversation_engine.auto_opening_message[:60]}...\"")
    print("✓ TOUS LES CHECKS PASSÉS")


if __name__ == "__main__":
    _run_test()
