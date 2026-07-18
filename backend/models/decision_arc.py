"""
Modèles Pydantic — Arc Décisionnel MVP (v16).

Chaîne : Situation → Recommendation → Intention → Decision → Execution → Consequences → Learning
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel

# ── Types ────────────────────────────────────────────────────────────────────

ArcStatus = Literal[
    "intention",
    "decision",           # non atteignable en MVP sans UI dédiée
    "execution",
    "consequences_linked",
    "learning_proposed",
    "closed",
    "abandoned",
]

ExecutionStatus = Literal["not_started", "in_progress", "partial", "complete"]

DecisionConfirmationSource = Literal["explicit", "inferred_from_execution"]

LinkType = Literal[
    "origin",
    "consequence_candidate",
    "consequence_confirmed",
    "consequence_rejected",
    "context",
]


# ── Modèles DB ───────────────────────────────────────────────────────────────

class DecisionArc(BaseModel):
    """Représentation complète d'un Arc Décisionnel."""
    id: UUID
    company_id: UUID
    entity_id: Optional[UUID] = None

    # Origine (IMMUTABLE)
    origin_analysis_id: UUID
    decision_fingerprint: str
    recommendation_id: str
    decision_source: Literal["plan_action_haute", "plan_action"]

    # Recommendation (IMMUTABLE — snapshot Pepperyn)
    recommendation_text: str

    # Decision (IMMUTABLE une fois écrit)
    decision_text: Optional[str] = None
    decision_notes: Optional[str] = None
    decision_confirmed_at: Optional[datetime] = None
    decision_confirmation_source: Optional[DecisionConfirmationSource] = None

    # État
    status: ArcStatus
    execution_status: ExecutionStatus = "not_started"
    execution_notes: Optional[str] = None
    execution_updated_at: Optional[datetime] = None

    # Learning
    learning_text: Optional[str] = None
    learning_confirmed: bool = False
    learning_modified: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    abandoned_at: Optional[datetime] = None
    abandoned_reason: Optional[str] = None


class ArcAnalysisLink(BaseModel):
    """Lien entre un arc et une analyse (origine, conséquence candidate/confirmée/rejetée)."""
    id: UUID
    arc_id: UUID
    analysis_id: UUID
    link_type: LinkType
    # Niveau causal max 3 : "est survenu après" / "est corrélé à" — JAMAIS "a causé"
    link_hypothesis: Optional[str] = None
    confirmed_by_user: Optional[bool] = None  # NULL = pending
    user_rejection_reason: Optional[str] = None
    linked_at: datetime
    reviewed_at: Optional[datetime] = None


# ── Résultats de service ──────────────────────────────────────────────────────

class ArcCreateResult(BaseModel):
    """Résultat de arc_service.create_arc_from_feedback()."""
    created: bool
    arc_id: Optional[str] = None
    arc_status: Optional[str] = None


class ArcConsequenceCandidate(BaseModel):
    """Candidat conséquence retourné dans AnalyzeResponse.arc_consequence_candidates."""
    arc_id: str
    arc_status: str
    recommendation_text: str
    decision_text: Optional[str] = None
    hypothesis: str
    analysis_id: str  # l'analyse N+1 qui a détecté le candidat


# ── Requêtes API ──────────────────────────────────────────────────────────────

class ArcConsequenceRequest(BaseModel):
    """POST /api/arcs/{id}/consequence"""
    analysis_id: str
    confirmed: bool
    rejection_reason: Optional[str] = None


class ArcLearningRequest(BaseModel):
    """POST /api/arcs/{id}/learning"""
    action: Literal["validate", "modify"]
    learning_text: Optional[str] = None
    # Requis si arc.decision_text IS NULL — confirmation rétrospective
    decision_text: Optional[str] = None
