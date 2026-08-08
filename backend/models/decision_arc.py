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
    # Rattachement Engagement (v21) — résolu à la création quand possible
    # via origin_analysis_id → analyses.entity_id → engagements.entity_id,
    # jamais fabriqué. Voir services/arc_service.py::_resolve_current_engagement_id.
    engagement_id: Optional[UUID] = None

    # Origine (IMMUTABLE tant que non-NULL — voir garde ci-dessous)
    # Nullable depuis v22 (Decision Memory Integrity Repair, 2026-08-08) :
    # provenance historique, PAS une identité ni une propriété. La
    # suppression ordinaire de l'Analysis d'origine (nettoyage d'historique,
    # DELETE /api/analyses/history) met ce champ à NULL sans jamais détruire
    # le DecisionArc — la mémoire décisionnelle professionnelle survit à la
    # disparition de son point de départ. Seule une érasure complète de la
    # company (GDPR) détruit le DecisionArc, via company_id ON DELETE
    # CASCADE (v16, inchangé). Voir CURRENT_DOMAIN_MODEL.md, section
    # DecisionArc, invariant de continuité mémorielle.
    origin_analysis_id: Optional[UUID] = None
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


class ArcAbandonRequest(BaseModel):
    """
    POST /api/arcs/{id}/abandon — "Ne plus suivre" côté UI (Review Briefing).

    RÈGLE SÉMANTIQUE (correction 2026-08-05) : cette transition signifie
    uniquement "ce point ne doit plus apparaître dans le briefing actif".
    Elle n'affirme jamais que le sujet a été réglé, résolu ou exécuté —
    `abandoned` == suivi arrêté, pas résultat constaté.
    """
    reason: Optional[str] = None


# ── Review Briefing (Capability 3 — Monthly Review Engine) ───────────────────

BriefingPriority = Literal["urgent", "to_check", "done", "closed"]

# Motifs proposés à l'utilisateur pour abandoned_reason — vocabulaire interne
# reste "abandoned" dans tous les cas, ce sont des libellés de contexte humain,
# jamais un nouveau statut métier affiché comme un résultat constaté par Pepperyn.
ABANDON_REASON_CHOICES: dict[str, str] = {
    "handled_elsewhere": "Traité en dehors de Pepperyn",
    "no_longer_relevant": "Devenu non pertinent",
    "decision_abandoned": "Décision abandonnée",
    "other": "Autre",
}


class BriefingItem(BaseModel):
    """
    Un élément du Review Briefing — synthèse opérationnelle, pas un fait brut.
    Généré par ArcService.build_review_briefing() à partir d'un DecisionArc.
    why_it_matters et questions_to_ask sont toujours templatés (jamais un
    appel LLM) — voir REVIEW_BRIEFING_IMPLEMENTATION_PLAN.md section 6.
    """
    arc_id: str
    source_type: Literal["decision_arc"] = "decision_arc"
    # Client propriétaire de l'arc — nécessaire pour regrouper par client
    # dans Portfolio Intelligence (build_portfolio_briefing). Absent pour un
    # arc sans client rattaché ; ce champ ne change rien pour les usages
    # existants du Briefing de revue (déjà scopé par entity_id en amont).
    entity_id: Optional[str] = None
    priority: BriefingPriority
    title: str
    temporal_context: str
    why_it_matters: Optional[str] = None
    questions_to_ask: list[str] = []
    # Affiché uniquement pour priority="closed" — jamais de question sur une
    # carte close (rien d'ouvert à discuter, voir section 1B du plan).
    learning_text: Optional[str] = None
    # Ancienneté brute en jours, utilisée pour le tie-break de tri du
    # Portfolio (Incrément 2, Mission 4) — voir _arc_to_briefing_item()
    # pour la date exacte utilisée selon le statut. Additif : ne change
    # rien pour les consommateurs existants du Briefing de revue, qui
    # continuent d'utiliser temporal_context (texte formaté), pas ce champ.
    age_days: int = 0


# ── Portfolio Intelligence (Incrément 1 + 2) ──────────────────────────────────

class PortfolioCard(BaseModel):
    """
    Une carte de Portfolio Intelligence — un client, son point le plus
    prioritaire parmi ses BriefingItem actifs. Généré par
    ArcService.build_portfolio_briefing() : pur regroupement du Briefing de
    revue existant par entity_id, aucun nouveau calcul, aucune nouvelle
    source de donnée.

    Incrément 1 : entity_name + top_item.title + action.
    Incrément 2 (voir docs/Product/portfolio-card-review/) : ajoute
    other_active_count et why_it_matters_display. temporal_context reste
    lu directement depuis top_item — déjà présent, jamais dupliqué ici.
    """
    entity_id: str
    entity_name: str
    top_item: BriefingItem
    # Nombre d'autres points actifs (priority != "closed") du même client,
    # en plus de top_item — 0 si aucun. "Actif" exclut délibérément
    # "closed" : un point clos ne demande plus de préparation, le compter
    # gonflerait la charge perçue sans raison (voir Mission 2, Incrément 2).
    other_active_count: int = 0
    # Sous-ensemble de top_item.why_it_matters : présent uniquement quand
    # le texte apporte une information distincte de l'icône de priorité,
    # du statut, du contexte temporel et du titre — voir
    # ArcService._is_why_it_matters_distinct() (Mission 3, Incrément 2).
    # None ne signifie jamais "aucune raison" : uniquement "déjà dite
    # ailleurs sur la carte". Le Review Briefing par client continue
    # d'afficher top_item.why_it_matters sans filtre, inchangé.
    why_it_matters_display: Optional[str] = None
