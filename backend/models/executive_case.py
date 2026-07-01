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


class EliminatedOption(BaseModel):
    """
    Une option alternative évaluée et écartée dans le raisonnement comparatif.

    EDX-002 — Chemin A : le LLM génère librement les alternatives,
    ancrées dans les données sources de l'entreprise.

    Règle anti-hallucination : elimination_criterion DOIT référencer
    une donnée factuelle fournie dans les sources (cash runway, DSO, EBITDA,
    horizon temporel, etc.). Aucun chiffre inventé.
    """
    option:                str  # Description concise de l'alternative (1 ligne, ton affirmé)
    elimination_criterion: str  # Critère précis et factuel qui écarte cette option


class TippingCondition(BaseModel):
    """
    Une condition observable qui renverserait la recommandation dans l'horizon cible.

    EDX-002 — Pepperyn ne dit pas "je pourrais me tromper".
    Il dit : "Voici exactement ce qui me ferait changer d'avis, et vers quoi."
    """
    condition:                  str      # L'événement précis et observable
    horizon_days:               int = 90 # Délai de surveillance en jours
    alternative_recommendation: str      # La décision de substitution si condition réalisée


class DecisionReasoning(BaseModel):
    """
    Chaîne de raisonnement associée à une décision prioritaire.

    EDX-001 (champs existants) — matching déterministe + raisonnement simple.
    EDX-002 (champs nouveaux) — raisonnement comparatif McKinsey :
      "J'ai étudié N options. J'en ai éliminé N-1. Voici pourquoi.
       Parmi les survivantes, j'en recommande une. Voici pourquoi elle domine.
       Voici ce qui pourrait me faire changer d'avis dans 90 jours."

    Responsabilité par champ :
      decision_index          → clé de liaison avec priority_decisions[i]
      problem_source          → Python pur (matching mots-clés vs value_destroyers)
      matching_confidence     → Python pur ("HIGH" | "LOW" | "FALLBACK_INDEX" | None)
      decision_confidence     → Python pur (formule déterministe)
      why_this_decision       → LLM EDX-001 — voix Pepperyn, lien causal
      inaction_risk           → LLM EDX-001 — conséquence à 90 jours
      confidence_explanation  → LLM EDX-001 — explication du score
      options_considered      → LLM EDX-002 — alternatives évaluées et écartées
      dominant_rationale      → LLM EDX-002 — pourquoi l'option retenue domine
      tipping_conditions      → LLM EDX-002 — conditions de révision à 90 jours
    """
    # ── EDX-001 — déterministe (Python pur) ──────────────────────────────────
    decision_index:         int
    problem_source:         Optional[str] = None
    matching_confidence:    Optional[str] = None   # "HIGH" | "LOW" | "FALLBACK_INDEX"
    decision_confidence:    Optional[int] = None

    # ── EDX-001 — LLM ────────────────────────────────────────────────────────
    why_this_decision:      Optional[str] = None
    inaction_risk:          Optional[str] = None
    confidence_explanation: Optional[str] = None

    # ── EDX-002 — LLM (raisonnement comparatif — Chemin A) ───────────────────
    # Le LLM génère librement les alternatives, ancrées dans les données sources.
    # Liste vide si données insuffisantes pour alternatives crédibles.
    options_considered:  List["EliminatedOption"]  = Field(default_factory=list)
    dominant_rationale:  Optional[str]             = None
    tipping_conditions:  List["TippingCondition"]  = Field(default_factory=list)


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


# ─── ÉTATS FINANCIERS SIMPLIFIÉS ─────────────────────────────────────────────

class PLLine(BaseModel):
    """Une ligne du compte de résultat."""
    label:         str
    value_display: str            # ex: "8 200 K€", "28 %", "-240 K€"
    indent:        int  = 0       # 0 = ligne principale, 1 = sous-ligne indentée
    is_subtotal:   bool = False   # sous-total (filet fin dessus)
    is_total:      bool = False   # total (filet épais dessus + en gras)
    is_separator:  bool = False   # ligne vide pour aérer


class BalanceLine(BaseModel):
    """Une ligne du bilan simplifié."""
    label:         str
    value_display: str
    indent:        int  = 0
    is_total:      bool = False


class FinancialStatements(BaseModel):
    """
    États financiers simplifiés fournis avec le cas.
    Optionnel — absent si l'entreprise n'a pas fourni ses comptes complets.
    """
    # ── Compte de résultat (P&L) ──────────────────────────────────────────
    pl_period:  str             = ""   # ex: "Exercice 2025–2026 (12 mois estimés)"
    pl_lines:   List[PLLine]    = Field(default_factory=list)
    pl_note:    Optional[str]   = None # note de bas de page

    # ── Bilan simplifié ────────────────────────────────────────────────────
    bilan_date:   str                = ""
    assets:       List[BalanceLine]  = Field(default_factory=list)
    liabilities:  List[BalanceLine]  = Field(default_factory=list)
    bfr_display:  Optional[str]      = None  # ex: "2 340 K€"
    bilan_note:   Optional[str]      = None

    # ── Position de trésorerie ─────────────────────────────────────────────
    cash_current:           Optional[str] = None  # ex: "180 K€"
    cash_burn_monthly:      Optional[str] = None  # ex: "-141 K€ / mois"
    cash_runway_label:      Optional[str] = None  # ex: "1,3 mois (~5 semaines)"
    credit_line_available:  Optional[str] = None
    financing_need_90d:     Optional[str] = None  # ex: "-245 K€"
    cash_note:              Optional[str] = None


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

    # ── Chaîne décisionnelle EDX-001 ──────────────────────────────────────────
    # Raisonnements associés aux décisions prioritaires.
    # Séparé de priority_decisions pour permettre l'évolution indépendante.
    # decision_reasoning[i].decision_index → priority_decisions[j]
    decision_reasoning: List[DecisionReasoning] = Field(default_factory=list)

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

    # ── États financiers simplifiés (optionnel) ───────────────────────────────
    financial_statements: Optional[FinancialStatements] = None

    # ── Qualité des données ───────────────────────────────────────────────────
    data_quality: DataQuality = Field(default_factory=DataQuality)
