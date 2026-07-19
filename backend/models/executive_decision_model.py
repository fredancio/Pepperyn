"""
Executive Decision Model (EDM) — Étape A, refactor vocabulaire (Executive Narrative).

Source de vérité unique pour tout contenu décisionnel généré par Pepperyn.
Les exports (Executive Report / Executive Board Deck / Executive Financial
Model, Dashboard, Email, Growth Brain, Copilot) ne font QUE lire ce modèle —
ils ne calculent rien.

Convention de nommage (voir /NOMENCLATURE_EXECUTIVE.md) :
- Langage interne (ce fichier) → anglais, vocabulaire "Executive" officiel.
- Langage visible côté client → français, géré uniquement au niveau des
  exports (non concernés à ce stade).

Structure alignée sur l'Executive Narrative (ordre canonique, immuable) :
1. Executive Decision · 2. Executive Summary · 3. Business Context ·
4. Financial Impact · 5. Executive Decisions · 6. Strategic Levers ·
7. Execution Roadmap · 8. Future Projection · 9. Executive Follow-up ·
10. Confidential Copilot Note · (Annexe technique, hors narration)

IMPORTANT (Étape A/B) :
- Ce fichier ne modifie ni ne remplace `models/schemas.py`. Il réutilise
  `ScenarioCase` et `DataQualityInfo` qui y sont déjà définis (Zero Rewrite
  Policy). `DashboardCard` n'est plus utilisé directement par ce module
  (le bandeau Executive Summary expose désormais des champs typés).
- `BusinessContext` reste un placeholder : aucune source de données n'est
  encore branchée (donnée de profil entreprise, pas une donnée d'analyse).
  Décision de branchement à prendre séparément, hors scope Étape B.
- Aucun champ de ce module n'est encore lu par export_pdf_service.py,
  export_pptx_service.py ou excel_export.py.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from models.financial_truth import QuantifiedImpact
from models.schemas import DataQualityInfo, ScenarioCase

# ── Phase 4B : Financial Truth Layer ─────────────────────────────────────────
# QuantifiedImpact est importé directement depuis models.financial_truth.
# financial_truth.py n'importe que la stdlib → aucun cycle d'import.
# Pydantic v2 gère les Python dataclasses nativement (pas d'arbitrary_types_allowed).
# Les renderers ignorent quantified_impact en Phase 4B (ils lisent annual_impact).
# En Phase 4C, les renderers liront quantified_impact en priorité.

__all__ = [
    "CostOfInaction",
    "ValueDestroyer",
    "ExecutiveDecision",
    "ExecutionItem",
    "Phase90Days",
    "FollowUpInfo",
    "BusinessContext",
    "ExecutiveDecisionModel",
]


class CostOfInaction(BaseModel):
    """Coût de l'inaction, décliné par période. 100% calculé en Python (jamais demandé au LLM)."""
    per_year: Optional[float] = None
    per_month: Optional[float] = None
    per_week: Optional[float] = None
    per_day: Optional[float] = None
    per_hour: Optional[float] = None


class ValueDestroyer(BaseModel):
    """Une ligne de la section 'Financial Impact' (destruction de valeur)."""
    name: str
    annual_impact: Optional[float] = None
    monthly_impact: Optional[float] = None    # 🐍 dérivé de annual_impact
    pct_revenue: Optional[float] = None         # 🐍 dérivé (si CA total connu — Étape B+)
    trend: Optional[str] = None                  # "up" | "down" | "stable" | None
    comment: Optional[str] = None                # texte libre (LLM) — jamais un calcul
    # ── Phase 4B : Financial Truth Layer ────────────────────────────────────
    # Coexiste avec annual_impact. Ignoré par les renderers en Phase 4B.
    # Pydantic v2 valide le type : seul QuantifiedImpact ou None est accepté.
    quantified_impact: Optional[QuantifiedImpact] = None


class ExecutiveDecision(BaseModel):
    """Une ligne de la section 'Executive Decisions' (tableau trié par impact)."""
    decision: str
    annual_impact: Optional[float] = None
    monthly_impact: Optional[float] = None     # 🐍 dérivé
    difficulty: Optional[str] = None            # jugement qualitatif (LLM) — pas un calcul
    timeline: Optional[str] = None
    owner: Optional[str] = None
    priority: str = "Not evaluated"              # 🐍 dérivé des seuils d'impact
    roi_score: float = 0.0                         # 🐍 dérivé (impact x difficulté)
    status: str = "To launch"                       # 🐍 valeur par défaut
    # ── Phase 4B : Financial Truth Layer ────────────────────────────────────
    # Coexiste avec annual_impact. Ignoré par les renderers en Phase 4B.
    # Pydantic v2 valide le type : seul QuantifiedImpact ou None est accepté.
    quantified_impact: Optional[QuantifiedImpact] = None


class ExecutionItem(BaseModel):
    """Une ligne du carnet d'exécution (Execution Roadmap)."""
    decision: str
    owner: Optional[str] = None
    impact: Optional[float] = None
    due_date: Optional[str] = None               # 🐍 dérivé (aujourd'hui + horizon)
    difficulty: Optional[str] = None             # jugement qualitatif (LLM)
    roi_score: float = 0.0                          # 🐍 dérivé
    status: str = "To launch"                        # 🐍 valeur par défaut
    review_date: Optional[str] = None               # 🐍 dérivé


class Phase90Days(BaseModel):
    """Une phase du plan 90 jours (Stabilize / Optimize / Accelerate)."""
    horizon: str                                  # "30" | "60" | "90"
    phase_label: str                              # 🐍 dérivé du horizon (mapping fixe)
    actions: List[ExecutionItem] = Field(default_factory=list)


class FollowUpInfo(BaseModel):
    """Section 'Executive Follow-up' — non commerciale."""
    next_analysis_recommended: Optional[str] = None  # 🐍 dérivé (date)
    commitments: List[str] = Field(default_factory=list)  # texte statique, pas de LLM


class BusinessContext(BaseModel):
    """
    Section 'Business Context' — PLACEHOLDER (gap identifié à la revue
    Executive Narrative). Nécessite une source de données de profil
    entreprise (secteur, modèle économique, taille), absente de l'EDM
    aujourd'hui. Reste à None tant que cette source n'est pas branchée.
    """
    sector: Optional[str] = None
    business_model: Optional[str] = None
    company_size: Optional[str] = None


class ExecutiveDecisionModel(BaseModel):
    """
    Source de vérité unique pour un rapport Pepperyn.
    Construit une seule fois par `build_executive_decision_model()`,
    puis lu (jamais recalculé) par chaque export.
    """

    # 1. Executive Decision — LA décision la plus importante, seule, en page de tête
    executive_decision: Optional[ExecutiveDecision] = None
    cost_of_inaction_summary: Optional[CostOfInaction] = None

    # 2. Executive Summary
    ebitda: Optional[str] = None
    available_cash: Optional[str] = None
    health_score: Optional[int] = None              # = ancien score_global
    executive_confidence: Optional[int] = None        # = ancien score_confiance

    # 3. Business Context (placeholder — voir BusinessContext)
    business_context: Optional[BusinessContext] = None

    # 4. Financial Impact
    value_destroyers: List[ValueDestroyer] = Field(default_factory=list)
    cost_of_inaction: Optional[CostOfInaction] = None

    # 5. Executive Decisions
    executive_decisions: List[ExecutiveDecision] = Field(default_factory=list)
    executive_decisions_score: float = 0.0             # 🐍 moyenne des roi_score individuels

    # 6. Strategic Levers (gap corrigé — manquait à l'Étape A)
    strategic_levers: List[str] = Field(default_factory=list)

    # 7. Execution Roadmap
    roadmap_90_days: List[Phase90Days] = Field(default_factory=list)
    execution_log: List[ExecutionItem] = Field(default_factory=list)

    # 8. Future Projection
    scenarios: List[ScenarioCase] = Field(default_factory=list)
    do_nothing_series: List[float] = Field(default_factory=list)   # 🐍 interpolée
    action_series: List[float] = Field(default_factory=list)        # 🐍 interpolée
    monthly_projection: List[float] = Field(default_factory=list)     # 🐍 interpolée

    # 9. Executive Follow-up
    follow_up: Optional[FollowUpInfo] = None

    # 10. Confidential Copilot Note
    copilot_note: Optional[str] = None               # texte LLM — champ optionnel, alimenté à l'Étape B

    # Annexe & méthodologie (technique, hors narration principale)
    data_quality: Optional[DataQualityInfo] = None
