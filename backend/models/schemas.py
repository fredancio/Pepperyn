from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum


class Plan(str, Enum):
    free = "free"
    pro = "pro"
    premium = "premium"
    enterprise = "enterprise"
    # Legacy mappings
    standard = "standard"
    standard_beta = "standard_beta"


class DocumentType(str, Enum):
    compte_resultat = "COMPTE_RESULTAT"
    budget = "BUDGET"
    previsionnel = "PREVISIONNEL"
    tresorerie = "TRESORERIE"
    bilan = "BILAN"
    commercial = "COMMERCIAL"
    autre = "AUTRE"
    inconnu = "INCONNU"


class AnalysisMode(str, Enum):
    quick = "quick"
    complete = "complete"


# ── Auth ────────────────────────────────────────────────────

class PinLoginRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class PinLoginResponse(BaseModel):
    access_token: str
    token_type: str = "guest"
    company_id: str
    plan: str


class UpdatePinRequest(BaseModel):
    new_pin: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


# ── Analysis ─────────────────────────────────────────────────

class LineItem(BaseModel):
    label: str
    value: float
    variation: Optional[float] = None
    pourcentage: Optional[float] = None


class RevenusData(BaseModel):
    total: Optional[float] = None
    breakdown: List[LineItem] = []
    evolution: Optional[str] = None


class CoutsData(BaseModel):
    total: Optional[float] = None
    breakdown: List[LineItem] = []


class MargesData(BaseModel):
    brute: Optional[float] = None
    brute_pct: Optional[float] = None
    operationnelle: Optional[float] = None
    operationnelle_pct: Optional[float] = None
    nette: Optional[float] = None
    nette_pct: Optional[float] = None


class Anomalie(BaseModel):
    description: str
    severity: str = "medium"  # high | medium | low
    impact: Optional[str] = None


class Risque(BaseModel):
    description: str
    probabilite: Optional[str] = None
    impact: Optional[str] = None


class Opportunite(BaseModel):
    description: str
    potentiel: Optional[str] = None


class Recommandation(BaseModel):
    priorite: str = "moyenne"  # haute | moyenne | basse
    action: str
    impact_estime: Optional[str] = None
    delai: Optional[str] = None


class AnalysisResult(BaseModel):
    # Identifiant DB (renseigné après sauvegarde)
    id: Optional[str] = None

    # Champs communs
    type_document: str = "AUTRE"
    score_confiance: int = Field(default=70, ge=0, le=100)

    # Champs v3 (nouveau format)
    resume_executif: Optional[str] = None
    diagnostic_revenus: Optional[str] = None
    diagnostic_couts: Optional[str] = None
    diagnostic_marges: Optional[str] = None
    ce_qui_a_change: List[str] = []
    alertes: List[str] = []
    problemes_critiques: List[str] = []
    opportunites_v3: List[str] = []
    plan_action: List[str] = []
    score_rentabilite: Optional[int] = None
    score_risque: Optional[int] = None
    score_structure: Optional[int] = None
    decision: Optional[str] = None
    memory_insight: Optional[str] = None
    verification_tag: Optional[str] = None

    # Champs legacy (ancien format JSON — backward compat)
    revenus: Optional[RevenusData] = None
    couts: Optional[CoutsData] = None
    marges: Optional[MargesData] = None
    anomalies: List[Anomalie] = []
    risques: List[Risque] = []
    opportunites: List[Opportunite] = []
    recommandations: List[Recommandation] = []
    synthese: Optional[str] = None
    excel_export_url: Optional[str] = None
    excel_export_nom: Optional[str] = None


class AnalyzeResponse(BaseModel):
    success: bool = True
    message: str
    analyse_id: Optional[str] = None
    result: Optional[AnalysisResult] = None
    tokens_used: int = 0
    cout_estime: float = 0.0
    memory_insight: Optional[str] = None


class TextQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class TextQueryResponse(BaseModel):
    success: bool = True
    message: str
    response: str


# ── Feedback ─────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    analyse_id: Optional[str] = None
    learned_something: Optional[bool] = None        # L'analyse m'a appris quelque chose
    would_act: Optional[bool] = None                # Je vais agir suite à cette analyse
    trust_score: Optional[int] = Field(default=None, ge=1, le=5)  # 1-5 confiance
    frustration: Optional[str] = Field(default=None, max_length=1000)  # texte libre
    willingness_to_pay: Optional[int] = Field(default=None, ge=0, le=500)  # €/mois


class FeedbackResponse(BaseModel):
    success: bool = True
    message: str = "Feedback enregistré"
