"""
executive_case.py — Contrat de données officiel Pepperyn V2
Source unique de vérité pour tous les exports (PDF, PPTX, Excel).

Produit par  : Executive Case Builder (Agent 1 — Claude Opus)
Consommé par :
  - Executive Report Builder       (Agent 2 — PDF)
  - Executive Board Deck Builder   (Agent 3 — PPTX)
  - Executive Financial Model Builder (Agent 4 — Excel)

RÈGLE ABSOLUE :
  1. Ce JSON est produit UNE seule fois par Agent 1.
  2. Aucun agent de présentation ne modifie, recalcule, ou extrapole un champ.
  3. Si une donnée est absente → champ = None. Jamais estimé, jamais imputé
     par les agents de présentation.
  4. PDF = PPTX = Excel : même valeur, même chiffre, sans exception.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─── SUB-MODELS ───────────────────────────────────────────────────────────────

class COIBreakdown(BaseModel):
    """Coût de l'inaction — calculé UNE seule fois par Agent 1 (Python deterministe)."""
    annual:  Optional[float] = None   # par an
    monthly: Optional[float] = None   # par mois
    weekly:  Optional[float] = None   # par semaine
    daily:   Optional[float] = None   # par jour
    hourly:  Optional[float] = None   # par heure


class DimensionScores(BaseModel):
    """Scores par dimension (0-10). Source : LLM."""
    rentabilite: Optional[int] = None
    risque:      Optional[int] = None
    structure:   Optional[int] = None
    liquidite:   Optional[int] = None


class KPICard(BaseModel):
    """Un indicateur clé du CEO Dashboard."""
    label:  str
    value:  str
    status: Optional[str] = None    # "missing" si donnée absente


class ValueDestroyerItem(BaseModel):
    """Un destructeur de valeur identifié par Agent 1."""
    name:           str
    annual_impact:  Optional[float] = None
    monthly_impact: Optional[float] = None
    trend:          Optional[str]   = None   # "↑" | "↓" | "→" | None


class PriorityDecisionItem(BaseModel):
    """Une décision prioritaire. Impact pré-calculé par Python."""
    decision:       str
    annual_impact:  Optional[float] = None
    monthly_impact: Optional[float] = None
    difficulty:     Optional[str]   = None   # "Faible" | "Moyen" | "Élevé"
    timeline:       Optional[str]   = None   # "30 jours" | "60 jours" | "90 jours"
    priority:       str             = "Non évaluée"
    roi_score:      float           = 0.0
    owner:          Optional[str]   = None
    status:         str             = "À lancer"


class ExecutionLogItem(BaseModel):
    """Un item du carnet d'exécution."""
    decision:    str
    owner:       Optional[str]   = None
    impact:      Optional[float] = None
    due_date:    Optional[str]   = None
    difficulty:  Optional[str]   = None
    roi_score:   float           = 0.0
    status:      str             = "À lancer"
    review_date: Optional[str]   = None


class ScenarioItem(BaseModel):
    """Un scénario (meilleur / probable / pire)."""
    label:       str
    description: str


class Scenarios(BaseModel):
    """Les trois scénarios officiels."""
    best:   Optional[ScenarioItem] = None
    likely: Optional[ScenarioItem] = None
    worst:  Optional[ScenarioItem] = None


class ProjectionSeries(BaseModel):
    """Séries temporelles 12 mois — calculées UNE seule fois par interpolation Python."""
    action:      List[float] = Field(default_factory=list)   # avec action
    inaction:    List[float] = Field(default_factory=list)   # sans action
    equilibrium: List[float] = Field(default_factory=list)   # trajectoire cible


class RiskItem(BaseModel):
    """Un risque majeur identifié."""
    description: str
    severity:    str = "Moyen"
    impact:      str = "Modéré"
    horizon:     str = "Court terme"


class DataQuality(BaseModel):
    """Qualité et limites des données sources."""
    score:       int        = 70
    anomalies:   List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limits:      List[str] = Field(default_factory=list)


# ─── CONTRAT PRINCIPAL ────────────────────────────────────────────────────────

class ExecutiveCaseJSON(BaseModel):
    """
    Source unique de vérité pour un rapport Pepperyn V2.

    Produit par l'Executive Case Builder (Claude Opus — Agent 1).
    Lu TEL QUEL par PDF, PPTX, Excel — aucune modification autorisée.

    Garantie de cohérence : PDF, PPTX et Excel affichent exactement
    les mêmes chiffres car ils lisent tous depuis ce même objet.
    """

    # ── Identité ──────────────────────────────────────────────────────────────
    company_name:  str = ""
    analysis_date: str = ""
    document_type: str = "PREVISIONNEL"

    # ── Scores ────────────────────────────────────────────────────────────────
    confidence_score:         int             = 0
    health_score:             Optional[int]   = None
    dimension_scores:         DimensionScores = Field(default_factory=DimensionScores)
    decisions_priority_score: float           = 0.0

    # ── Coût de l'inaction (pré-calculé Python, copié tel quel) ───────────────
    cost_of_inaction: COIBreakdown = Field(default_factory=COIBreakdown)

    # ── Narratifs (produits par LLM, copiés exactement) ───────────────────────
    executive_diagnosis:       Optional[str]   = None
    tension_phrase:            Optional[str]   = None
    inaction_risk:             Optional[str]   = None
    structural_loss_statement: Optional[str]   = None   # texte libre source LLM
    structural_loss_value:     Optional[float] = None   # montant parsé en €
    urgency_level:             Optional[str]   = None
    value_creation_statement:  Optional[str]   = None

    # ── KPI Dashboard ─────────────────────────────────────────────────────────
    kpi_dashboard: List[KPICard] = Field(default_factory=list)

    # ── Analyse décisionnelle ─────────────────────────────────────────────────
    value_destroyers:   List[ValueDestroyerItem]   = Field(default_factory=list)
    priority_decisions: List[PriorityDecisionItem] = Field(default_factory=list)

    # ── Roadmap ───────────────────────────────────────────────────────────────
    roadmap_30_60_90: Dict[str, List[str]] = Field(
        default_factory=lambda: {"30": [], "60": [], "90": []}
    )
    execution_log: List[ExecutionLogItem] = Field(default_factory=list)

    # ── Projections financières ───────────────────────────────────────────────
    series:    ProjectionSeries = Field(default_factory=ProjectionSeries)
    scenarios: Scenarios        = Field(default_factory=Scenarios)

    # ── Risques ───────────────────────────────────────────────────────────────
    major_risks: List[RiskItem] = Field(default_factory=list)

    # ── Qualité des données ───────────────────────────────────────────────────
    data_quality: DataQuality = Field(default_factory=DataQuality)
