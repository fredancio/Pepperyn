"""
Executive Decision Model — couche de calcul (Étape A, refactor vocabulaire Executive Narrative).

Construit l'ExecutiveDecisionModel à partir du dict brut déjà produit par
`llm_service.py` (le format V11 existant n'est pas modifié). Toute la logique
métier dérivable (coût de l'inaction, priorité, score ROI, échéances, tri,
phases, séries de graphique) vit ici et UNIQUEMENT ici, conformément au
correctif d'architecture : aucun export ne doit recalculer quoi que ce soit.

Règle absolue : tout ce qui peut être calculé en Python l'est. Le LLM n'est
jamais sollicité ici pour produire un ROI, une priorité, un classement ou un
montant dérivé — ces informations sont extraites du texte déjà généré
(montants formatés en euros) puis calculées déterministiquement.

Convention de nommage (voir /NOMENCLATURE_EXECUTIVE.md) : ce module est du
langage interne → anglais. Les exports traduiront vers le français au moment
de l'affichage (non concernés à ce stade).

IMPORTANT (Étape A/B) :
- Aucun appel LLM n'est fait depuis ce module.
- Aucun nouveau champ de prompt n'est requis : `copilot_note` est lu de
  façon optionnelle (`result.get("note_copilote")`) et reste `None` tant que
  le prompt n'a pas été étendu (Étape B traite ce point séparément).
- export_pdf_service.py, export_pptx_service.py et excel_export.py ne sont
  pas modifiés et ne consomment pas encore ce module.
- `business_context` n'est pas alimenté ici (gap documenté — nécessite une
  source de données de profil entreprise, hors scope de cette couche).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from typing import Any, Optional

from models.executive_decision_model import (
    CostOfInaction,
    ExecutionItem,
    ExecutiveDecision,
    ExecutiveDecisionModel,
    FollowUpInfo,
    Phase90Days,
    ValueDestroyer,
)
from models.schemas import DataQualityInfo, ScenarioCase

logger = logging.getLogger(__name__)

# ── E2E Campaign logging — TEMPORAIRE (supprimer après Gate Review Phase 4C) ──
_e2e_log = logging.getLogger("pepperyn.e2e")


def _log_qi_e2e(item_type: str, idx: int, qi) -> None:
    """
    Log structuré pour la Campagne E2E Phase 4B → 4C.
    Permet de mesurer L3 (précision LLM) sur metric_type / period_basis / nature /
    current_vs_historical / annualization_quality / provenance.

    TEMPORAIRE — ne pas laisser en production après la Gate Review.
    Tag de version figée : e2e-campaign-1-start
    """
    try:
        if qi is not None:
            ann_q = qi.annualization_quality()
            _e2e_log.info(
                "[E2E] %s[%d] %s",
                item_type,
                idx,
                json.dumps(
                    {
                        "metric_type": qi.metric_type.value,
                        "period_basis": qi.period_basis.value,
                        "nature": qi.nature.value,
                        "confidence": qi.confidence,
                        "is_current_period": qi.is_current_period,
                        "is_unresolved": qi.is_unresolved(),
                        "ann_quality": ann_q.value if ann_q else None,
                        "provenance": [
                            r.source_type.value if r.source_type else None
                            for r in qi.source_references
                        ],
                        "amount": qi.amount,
                    },
                    ensure_ascii=False,
                ),
            )
        else:
            _e2e_log.info("[E2E] %s[%d] qi=None", item_type, idx)
    except Exception as _e2e_err:
        # Le logging E2E ne doit jamais faire planter le pipeline
        logger.debug("[E2E] logging error for %s[%d]: %s", item_type, idx, _e2e_err)
# ── Fin logging E2E ───────────────────────────────────────────────────────────


def _try_deserialize_qi(qi_dict: Any, amount: Optional[float] = None):
    """
    Désérialise un QuantifiedImpact depuis un dict LLM V3.

    Args:
        qi_dict: Dict brut LLM avec metric_type, period_basis, nature, etc.
                 N'inclut PAS amount (le LLM JSON V3 ne fournit pas le montant).
        amount:  Montant parsé depuis la chaîne legacy (parse_amount_eur).
                 Si fourni et que qi_dict.amount est None, amount est injecté
                 avec source_type=LEGACY_PARSE pour traçabilité explicite.
                 Un fallback legacy ne doit JAMAIS être confondu avec une
                 extraction V3 certifiée.

    Retourne None si absent, None, ou invalide.
    Jamais d'exception levée — retour None si quoi que ce soit échoue.
    """
    if not isinstance(qi_dict, dict):
        return None
    try:
        from models.financial_truth import QuantifiedImpact, SourceType
        effective_dict = dict(qi_dict)

        if effective_dict.get("amount") is None and amount is not None:
            # Injection depuis le parseur legacy — marquer explicitement la provenance
            effective_dict["amount"] = amount
            legacy_ref = {
                "fact_id": None,
                "source_type": SourceType.LEGACY_PARSE.value,
                "source_quote": (
                    "amount injected from parse_amount_eur legacy fallback (Phase 4B) — "
                    "not a certified V3 extraction"
                ),
            }
            refs = list(effective_dict.get("source_references") or [])
            refs.insert(0, legacy_ref)
            effective_dict["source_references"] = refs

        return QuantifiedImpact.from_dict(effective_dict)
    except Exception as e:
        logger.debug(f"[edm] quantified_impact deserialization failed: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de calcul (seuils et mappings — ajustables sans toucher au reste)
# ─────────────────────────────────────────────────────────────────────────────

PRIORITY_THRESHOLD_HIGH = 500_000
PRIORITY_THRESHOLD_MEDIUM = 100_000

DIFFICULTY_WEIGHT = {
    "faible": 3.0,
    "moyenne": 2.0,
    "élevée": 1.0,
    "elevee": 1.0,
}
DIFFICULTY_WEIGHT_DEFAULT = 2.0  # "moyenne" si non renseigné

PHASE_LABELS = {
    "30": "Stabilize",
    "60": "Optimize",
    "90": "Accelerate",
}

STATUS_DEFAULT = "To launch"

FOLLOW_UP_COMMITMENTS = [
    "Comparer les résultats de la prochaine analyse à ceux d'aujourd'hui.",
    "Mesurer l'effet réel des décisions engagées.",
    "Recalculer les projections financières à partir des nouvelles données.",
    "Détecter automatiquement toute nouvelle dérive de rentabilité.",
    "Ajuster les priorités du plan d'action en fonction des résultats observés.",
]

NEXT_ANALYSIS_DELAY_DAYS = 30

# Montant en euros, formaté par le LLM selon le prompt existant : un nombre
# (avec espaces comme séparateur de milliers, virgule comme séparateur
# décimal), suivi optionnellement de K ou M, suivi de €. Exemples valides :
# "1 800 000€", "1,8M€", "2,4 M€", "971K€", "-590 000€", "+12 600€".
# Le signe % est volontairement exclu (on ne veut jamais confondre un
# pourcentage avec un montant).
_AMOUNT_EUR_RE = re.compile(r"([+-]?\d[\d\s]*(?:[.,]\d+)?)\s*([KkMm])?\s*€")


# ─────────────────────────────────────────────────────────────────────────────
# Briques déterministes unitaires
# ─────────────────────────────────────────────────────────────────────────────

def parse_amount_eur(text: Optional[str]) -> Optional[float]:
    """
    Extrait un montant en euros depuis un texte formaté par le LLM.
    Retourne None si aucun montant n'est trouvé (ex. "Données insuffisantes").
    Ne lève jamais d'exception — une chaîne non parsable donne simplement None.
    """
    if not text or not isinstance(text, str):
        return None
    match = _AMOUNT_EUR_RE.search(text)
    if not match:
        return None
    number_str, multiplier = match.group(1), match.group(2)
    number_str = number_str.replace(" ", "").replace(",", ".")
    try:
        value = float(number_str)
    except ValueError:
        return None
    if multiplier and multiplier.lower() == "k":
        value *= 1_000
    elif multiplier and multiplier.lower() == "m":
        value *= 1_000_000
    return value


def compute_cost_of_inaction(annual_impact: Optional[float]) -> Optional[CostOfInaction]:
    """Coût de l'inaction par période — simple division de l'impact annuel."""
    if annual_impact is None:
        return None
    return CostOfInaction(
        per_year=annual_impact,
        per_month=annual_impact / 12,
        per_week=annual_impact / 52,
        per_day=annual_impact / 365,
        per_hour=annual_impact / (365 * 24),
    )


def compute_priority(annual_impact: Optional[float]) -> str:
    """Priorité dérivée de seuils fixes — jamais demandée au LLM."""
    if annual_impact is None:
        return "Not evaluated"
    impact_abs = abs(annual_impact)
    if impact_abs >= PRIORITY_THRESHOLD_HIGH:
        return "High"
    if impact_abs >= PRIORITY_THRESHOLD_MEDIUM:
        return "Medium"
    return "Low"


def compute_roi_score(annual_impact: Optional[float], difficulty: Optional[str]) -> float:
    """
    Score ROI composite (échelle ~0-10) : impact normalisé x poids de
    difficulté. La difficulté reste un jugement qualitatif fourni par le LLM
    (le moteur déterministe ne peut pas l'évaluer) ; tout le reste est calculé.
    """
    weight = DIFFICULTY_WEIGHT.get((difficulty or "").strip().lower(), DIFFICULTY_WEIGHT_DEFAULT)
    impact_norm = min(abs(annual_impact or 0) / 100_000, 10.0)
    return round(impact_norm * weight / 3, 1)


def compute_phase_label(horizon: str) -> str:
    """Libellé de phase dérivé de l'horizon (mapping fixe, jamais demandé au LLM)."""
    return PHASE_LABELS.get(str(horizon).strip(), "Phase")


def compute_due_date(horizon_days: int, since: Optional[date] = None) -> str:
    """Date d'échéance = aujourd'hui + horizon (en jours)."""
    base = since or date.today()
    return (base + timedelta(days=horizon_days)).strftime("%d/%m/%Y")


def compute_pct_revenue(annual_impact: Optional[float], total_revenue: Optional[float]) -> Optional[float]:
    """% du chiffre d'affaires — nécessite un CA total connu (Étape B+). None sinon."""
    if annual_impact is None or not total_revenue:
        return None
    return round(100 * annual_impact / total_revenue, 1)


def build_monthly_series(start: float, end: float, n_points: int = 12) -> list[float]:
    """Interpolation linéaire entre un point de départ et un point d'arrivée connus."""
    if n_points <= 1:
        return [end]
    step = (end - start) / (n_points - 1)
    return [round(start + step * i, 2) for i in range(n_points)]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers d'assemblage (lecture défensive du dict V11 existant)
# ─────────────────────────────────────────────────────────────────────────────

def _find_dashboard_value(raw_cards: list, *keywords: str) -> Optional[str]:
    for c in raw_cards or []:
        if not isinstance(c, dict):
            continue
        label = str(c.get("label") or "").lower()
        if any(kw.lower() in label for kw in keywords):
            return c.get("value")
    return None


def _build_executive_decisions(raw_quick_wins: list) -> list[ExecutiveDecision]:
    decisions: list[ExecutiveDecision] = []
    for _qw_idx, w in enumerate(raw_quick_wins or []):
        if not isinstance(w, dict):
            continue
        description = w.get("description") or ""
        difficulty = w.get("difficulte")
        impact = parse_amount_eur(w.get("roi_estime"))
        # ── Phase 4B : quantified_impact parallèle (legacy inchangé) ────────
        qi = _try_deserialize_qi(w.get("quantified_impact"), amount=impact)
        _log_qi_e2e("quick_win", _qw_idx, qi)
        decisions.append(
            ExecutiveDecision(
                decision=description,
                annual_impact=impact,
                monthly_impact=(impact / 12) if impact is not None else None,
                difficulty=difficulty,
                timeline=w.get("temps_mise_en_oeuvre"),
                owner=None,  # non disponible sur QuickWin aujourd'hui (schemas.py non modifié)
                priority=compute_priority(impact),
                roi_score=compute_roi_score(impact, difficulty),
                status=STATUS_DEFAULT,
                quantified_impact=qi,
            )
        )
    # Tri par impact décroissant — None traité comme le plus bas
    decisions.sort(key=lambda d: (d.annual_impact if d.annual_impact is not None else float("-inf")), reverse=True)
    return decisions


_DESTROYER_BULLET_RE = re.compile(r"^[^\wÀ-ÿ]*")

_TREND_MAP = {"hausse": "up", "baisse": "down", "stable": "stable"}
_EMPTY_VALUES = {"non applicable", "données insuffisantes", "non chiffrable", ""}


def _clean_optional_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    cleaned = text.strip()
    return cleaned if cleaned.lower() not in _EMPTY_VALUES else None


def _build_value_destroyers(
    raw_structured: list,
    raw_bullets: list,
    total_revenue: Optional[float] = None,
) -> list[ValueDestroyer]:
    """
    Préfère le format structuré V12 (`value_destroyers`, list[dict] avec
    name/impact_annuel/tendance/commentaire). Retombe sur l'ancien format
    libre (`ce_qui_detruit`, list[str]) si le format structuré est absent
    (compatibilité ascendante avec des données antérieures à l'Étape B).
    """
    destroyers: list[ValueDestroyer] = []

    if raw_structured:
        for _vd_idx, item in enumerate(raw_structured):
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or "").strip()
            if not name:
                continue
            impact = parse_amount_eur(item.get("impact_annuel"))
            trend = _TREND_MAP.get((item.get("tendance") or "").strip().lower())
            # ── Phase 4B : quantified_impact parallèle (legacy inchangé) ────
            qi = _try_deserialize_qi(item.get("quantified_impact"), amount=impact)
            _log_qi_e2e("destroyer", _vd_idx, qi)
            destroyers.append(
                ValueDestroyer(
                    name=name,
                    annual_impact=impact,
                    monthly_impact=(impact / 12) if impact is not None else None,
                    pct_revenue=compute_pct_revenue(impact, total_revenue),
                    trend=trend,
                    comment=_clean_optional_text(item.get("commentaire")),
                    quantified_impact=qi,
                )
            )
    else:
        for bullet in raw_bullets or []:
            if not isinstance(bullet, str) or not bullet.strip():
                continue
            name = _DESTROYER_BULLET_RE.sub("", bullet).strip()
            impact = parse_amount_eur(bullet)
            destroyers.append(
                ValueDestroyer(
                    name=name or bullet,
                    annual_impact=impact,
                    monthly_impact=(impact / 12) if impact is not None else None,
                    pct_revenue=compute_pct_revenue(impact, total_revenue),
                    trend=None,
                    comment=None,
                    quantified_impact=None,  # format bullet legacy — pas de QI extractable
                )
            )

    destroyers.sort(key=lambda d: (d.annual_impact if d.annual_impact is not None else float("-inf")), reverse=True)
    return destroyers


def _build_roadmap_90_days(raw_items: list) -> list[Phase90Days]:
    by_horizon: dict[str, list[ExecutionItem]] = {"30": [], "60": [], "90": []}
    horizon_days = {"30": 30, "60": 60, "90": 90}
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        horizon = str(item.get("horizon") or "").strip()
        if horizon not in by_horizon:
            continue
        impact = parse_amount_eur(item.get("impact_attendu"))
        difficulty = item.get("difficulte")  # absent aujourd'hui (PlanActionItem n'a pas ce champ) → None
        days = horizon_days[horizon]
        due = compute_due_date(days)
        by_horizon[horizon].append(
            ExecutionItem(
                decision=item.get("action") or "",
                owner=item.get("responsable"),
                impact=impact,
                due_date=due,
                difficulty=difficulty,
                roi_score=compute_roi_score(impact, difficulty),
                status=STATUS_DEFAULT,
                review_date=due,
            )
        )
    return [
        Phase90Days(horizon=h, phase_label=compute_phase_label(h), actions=by_horizon[h])
        for h in ("30", "60", "90")
        if by_horizon[h]
    ]


def _build_simulation_series(global_impact: Optional[float], n_points: int = 12) -> tuple[list[float], list[float]]:
    """
    Séries DO NOTHING (rouge) / ACTION (verte) pour le graphique avant/après.
    Simplification assumée (Étape A) : en l'absence de série mensuelle
    structurée fournie par le LLM (les scénarios restent du texte libre
    aujourd'hui), on interpole linéairement entre 0 et le gain annuel global
    déjà extrait, et on prend son symétrique négatif pour le scénario
    "ne rien faire". À affiner en Étape B+ si des montants structurés par
    scénario sont ajoutés au prompt.
    """
    if global_impact is None:
        return [], []
    action_series = build_monthly_series(0.0, global_impact, n_points)
    do_nothing_series = build_monthly_series(0.0, -global_impact, n_points)
    return action_series, do_nothing_series


def _to_scenario_cases(raw_scenarios: list) -> list[ScenarioCase]:
    cases: list[ScenarioCase] = []
    for s in raw_scenarios or []:
        if isinstance(s, ScenarioCase):
            cases.append(s)
        elif isinstance(s, dict) and s.get("nom") and s.get("label"):
            cases.append(ScenarioCase(**s))
    return cases


def _to_data_quality(raw_dq: Any) -> Optional[DataQualityInfo]:
    if raw_dq is None:
        return None
    if isinstance(raw_dq, DataQualityInfo):
        return raw_dq
    if isinstance(raw_dq, dict):
        try:
            return DataQualityInfo(**raw_dq)
        except Exception:
            return None
    return None


def _build_follow_up() -> FollowUpInfo:
    return FollowUpInfo(
        next_analysis_recommended=compute_due_date(NEXT_ANALYSIS_DELAY_DAYS),
        commitments=list(FOLLOW_UP_COMMITMENTS),
    )


def _build_strategic_levers(raw_levers: list) -> list[str]:
    """Strategic Levers — texte libre (LLM), repris tel quel depuis 'leviers_croissance'."""
    return [lever.strip() for lever in (raw_levers or []) if isinstance(lever, str) and lever.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────────────────────────────────────

def build_executive_decision_model(result: dict) -> ExecutiveDecisionModel:
    """
    Construit l'ExecutiveDecisionModel à partir du dict V11 déjà produit par
    `llm_service.py`. Ne fait aucun appel LLM, ne modifie pas `result`.
    """
    result = result or {}

    raw_dashboard = result.get("ceo_dashboard") or []
    ebitda = _find_dashboard_value(raw_dashboard, "ebitda")
    available_cash = _find_dashboard_value(raw_dashboard, "cash")
    total_revenue = parse_amount_eur(_find_dashboard_value(raw_dashboard, "chiffre d'affaires", "ca total"))

    executive_decisions = _build_executive_decisions(result.get("quick_wins") or [])
    executive_decisions_score = (
        round(sum(d.roi_score for d in executive_decisions) / len(executive_decisions), 1)
        if executive_decisions
        else 0.0
    )
    executive_decision = executive_decisions[0] if executive_decisions else None

    value_destroyers = _build_value_destroyers(
        result.get("value_destroyers") or [],
        result.get("ce_qui_detruit") or [],
        total_revenue,
    )

    # COI = somme des impacts absolus des leviers identifiés (valeur sous-optimisée)
    # C'est le coût d'opportunité réel, pas le montant de la trésorerie.
    # Fallback sur impact_financier_synthese si aucun levier n'est disponible.
    destroyers_total = sum(abs(v.annual_impact or 0) for v in value_destroyers)
    global_impact_fallback = parse_amount_eur(result.get("impact_financier_synthese"))
    coi_base = destroyers_total if destroyers_total > 0 else global_impact_fallback
    cost_of_inaction = compute_cost_of_inaction(coi_base)

    roadmap_90_days = _build_roadmap_90_days(result.get("plan_action_30_60_90") or [])
    execution_log = sorted(
        (action for phase in roadmap_90_days for action in phase.actions),
        key=lambda a: (a.impact if a.impact is not None else float("-inf")),
        reverse=True,
    )

    # Séries temporelles basées sur l'impact NET des décisions (pas le COI)
    # → action = gain si toutes les décisions sont exécutées
    # → inaction = perte d'opportunité symétrique
    decisions_net = sum((d.annual_impact or 0) for d in executive_decisions)
    series_base = decisions_net if decisions_net != 0 else coi_base
    action_series, do_nothing_series = _build_simulation_series(series_base)
    monthly_projection = build_monthly_series(0.0, series_base, 12) if series_base is not None else []

    return ExecutiveDecisionModel(
        executive_decision=executive_decision,
        cost_of_inaction_summary=cost_of_inaction,
        ebitda=ebitda,
        available_cash=available_cash,
        health_score=result.get("score_global"),
        executive_confidence=result.get("score_confiance"),
        business_context=None,  # gap documenté — aucune source branchée à ce stade
        value_destroyers=value_destroyers,
        cost_of_inaction=cost_of_inaction,
        executive_decisions=executive_decisions,
        executive_decisions_score=executive_decisions_score,
        strategic_levers=_build_strategic_levers(result.get("leviers_croissance") or []),
        roadmap_90_days=roadmap_90_days,
        execution_log=list(execution_log),
        scenarios=_to_scenario_cases(result.get("scenarios") or []),
        do_nothing_series=do_nothing_series,
        action_series=action_series,
        monthly_projection=monthly_projection,
        follow_up=_build_follow_up(),
        copilot_note=result.get("note_copilote"),  # optionnel — alimenté à l'Étape B
        data_quality=_to_data_quality(result.get("data_quality")),
    )
