"""
decision_kernel.py — WP5C, Commit 2
=====================================

Modèles Pydantic dk-1 du Decision Kernel de Pepperyn.

Ces modèles représentent et valident la structure du Kernel — ils ne calculent
rien. Toute logique dérivée (polarity, score_global, niveau_urgence, déduplication)
appartient respectivement à decision_rules.py et au futur extracteur (Commit 3).

Hiérarchie des modèles
-----------------------
    SourceRef                  — provenance fusionnée (déduplication)
    Finding                    — fait evidencé, porte sa provenance + scope_status
    Recommendation             — directive d'action, porte sa provenance + scope_status
    Decision                   — verdict dimensionnel (scope + status + score + polarity)
    AttributionMetrics         — compteurs de couverture (Bloc E)
    DecisionKernel             — structure racine dk-1 (5 blocs canoniques)

Contraintes d'intégrité structurelle
-------------------------------------
- Tous les modèles : extra="forbid" — aucun champ non canonique ne peut être injecté.
- Decision : status/score/polarity sont structurellement cohérents (model_validator).
- DecisionKernel.decisions : exactement 4 éléments, les 4 scopes canoniques, sans doublon.
- DecisionKernel : decision_fingerprint et decision_fingerprint_version sont liés (CA-4).

Vocabulaires fermés (Literal)
-------------------------------
- Finding.severity          : CRITIQUE | ÉLEVÉ | MODÉRÉ | FAIBLE  (ou None)
- Finding.scope_status      : scoped | global
- Recommendation.priority   : HAUTE | SECONDAIRE
- Recommendation.horizon    : IMMÉDIAT | COURT_TERME | MOYEN_TERME
- Recommendation.scope_status : scoped | global
- Decision.scope            : RENTABILITÉ | RISQUE | STRUCTURE | LIQUIDITÉ
- Decision.status           : available | insufficient_data
- Decision.polarity         : CRITIQUE | ÉLEVÉ | MODÉRÉ | POSITIF  (ou None)
- AttributionMetrics.mode   : conservative_v1
- DecisionKernel.kernel_version : dk-1
- DecisionKernel.niveau_urgence : Critique | Élevé | Modéré | Maîtrisé  (ou None)

Référence spec
--------------
SPEC-DK-001 Rev 3.1 (DESIGN FROZEN) §III.1
KERNEL-INV-010, KERNEL-INV-011, KERNEL-INV-012
DECISION-WP5C-4, DECISION-WP5C-8, DECISION-WP5C-9, DECISION-WP5C-10, DECISION-WP5C-11

Usage
-----
    from services.decision_kernel import (
        DecisionKernel,
        Decision,
        Finding,
        Recommendation,
        AttributionMetrics,
        SourceRef,
        KERNEL_VERSION,
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ── Version canonique ─────────────────────────────────────────────────────────
# Exportée pour que l'extracteur (Commit 3) et la migration (Commit 4) puissent
# référencer la version sans hard-coder la chaîne "dk-1".
KERNEL_VERSION: str = "dk-1"

# ── Scopes canoniques (ordre fixe, référencé par le validator de DecisionKernel) ─
_CANONICAL_SCOPES: tuple[str, ...] = (
    "RENTABILITÉ",
    "RISQUE",
    "STRUCTURE",
    "LIQUIDITÉ",
)


# ── SourceRef ─────────────────────────────────────────────────────────────────

class SourceRef(BaseModel):
    """Provenance d'un élément issu de la déduplication.

    Chaque doublon absorbé par un Finding ou une Recommendation ajoute une
    SourceRef dans source_refs, garantissant qu'aucune provenance n'est perdue
    (KERNEL-INV-011, KERNEL-INV-012).
    """

    model_config = ConfigDict(extra="forbid")

    source_field: str
    """Champ AnalysisResult d'origine (ex : "alertes", "problemes_critiques")."""

    source_index: int = Field(..., ge=-1)
    """Index 0-based dans la liste source. -1 pour les champs scalaires."""

    source_section: Optional[str] = None
    """Section LLM d'origine si connue (ex : "MARGIN_INTELLIGENCE")."""


# ── Finding ───────────────────────────────────────────────────────────────────

class Finding(BaseModel):
    """Fait evidencé justifiant un Verdict dimensionnel (dk-2+) ou global (dk-1).

    En dk-1, scope_status est toujours "global" — les Findings ne sont pas
    attribués à une Decision dimensionnelle (KERNEL-INV-009, DECISION-WP5C-11).
    La provenance complète (source_field + source_index) est obligatoire (KERNEL-INV-011).
    """

    model_config = ConfigDict(extra="forbid")

    local_id: str
    """Identifiant local au Kernel (ex : "f-01"). Assigné après déduplication."""

    statement: str
    """Texte du fait evidencé. Non normalisé — conserve la casse et la ponctuation
    d'origine. La normalisation est réservée à la comparaison de déduplication."""

    source_field: str
    """Champ AnalysisResult d'origine (ex : "problemes_critiques", "alertes")."""

    source_index: int = Field(..., ge=-1)
    """Index 0-based dans la liste source. -1 si le champ source est scalaire."""

    source_section: Optional[str] = None
    """Section LLM d'origine si connue (ex : "CASH_FORECAST", "BFR_INDICATORS")."""

    severity: Optional[Literal["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"]] = None
    """Sévérité du fait. None si non déterminable depuis le champ source."""

    scope_status: Literal["scoped", "global"] = "global"
    """"global" en dk-1. "scoped" réservé aux attributions dimensionnelles (dk-2+)."""

    evidence_refs: List[str] = Field(default_factory=list)
    """Références aux IDs de l'Evidence Graph. Vide en dk-1 (KERNEL-INV-009)."""

    source_refs: List[SourceRef] = Field(default_factory=list)
    """Provenances fusionnées lors de la déduplication (KERNEL-INV-012).
    Vide si pas de fusion. Contient ≥ 2 entrées en cas de déduplication."""


# ── Recommendation ────────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    """Directive d'action découlant d'un Verdict dimensionnel (dk-2+) ou global (dk-1).

    En dk-1, scope_status est toujours "global" — les Recommendations ne sont pas
    attribuées à une Decision dimensionnelle (KERNEL-INV-009, DECISION-WP5C-11).
    La provenance complète (source_field + source_index) est obligatoire (KERNEL-INV-011).
    """

    model_config = ConfigDict(extra="forbid")

    local_id: str
    """Identifiant local au Kernel (ex : "r-01"). Assigné après déduplication."""

    directive: str
    """Texte de la directive. Conserve la formulation d'origine."""

    source_field: str
    """Champ AnalysisResult d'origine (ex : "plan_action_haute")."""

    source_index: int = Field(..., ge=-1)
    """Index 0-based dans la liste source. -1 si champ scalaire."""

    priority: Literal["HAUTE", "SECONDAIRE"]
    """Priorité de la directive, dérivée du champ source."""

    horizon: Literal["IMMÉDIAT", "COURT_TERME", "MOYEN_TERME"]
    """Temporalité : IMMÉDIAT < 30j, COURT_TERME 30-90j, MOYEN_TERME > 90j."""

    intent_text: Optional[str] = None
    """Transitoire — intention stratégique servie par la directive.
    Sera lié à StrategicIntention (Company) dans une version future (DECISION-WP5C-5)."""

    expected_outcome: Optional[str] = None
    """Résultat qualitatif attendu si la directive est suivie (DECISION-WP5C-6).
    Les projections quantitatives (cible chiffrée, date) appartiennent au Scenario Kernel."""

    scope_status: Literal["scoped", "global"] = "global"
    """"global" en dk-1. "scoped" réservé aux attributions dimensionnelles (dk-2+)."""

    source_refs: List[SourceRef] = Field(default_factory=list)
    """Provenances fusionnées lors de la déduplication (KERNEL-INV-012)."""


# ── Decision ──────────────────────────────────────────────────────────────────

class Decision(BaseModel):
    """Verdict sur l'une des 4 dimensions Kernel canoniques.

    Les 4 emplacements dimensionnels sont toujours présents dans un Kernel dk-1.
    Si les données sont insuffisantes pour produire un verdict, status="insufficient_data"
    et score/polarity sont None — la dimension n'est pas absente, elle est non prononcée
    (DECISION-WP5C-8, SPEC-DK-001 Rev 3.1 §1.2).

    Cohérence structurelle (model_validator) :
      - status="available"          → score ≠ None, polarity ≠ None
      - status="insufficient_data"  → score = None, polarity = None

    Cette contrainte est structurelle (le modèle la valide) — la valeur de polarity
    par rapport au score reste de la responsabilité de l'extracteur (decision_rules).
    """

    model_config = ConfigDict(extra="forbid")

    local_id: str
    """Identifiant fixe dans le Kernel : "d-01" … "d-04" (par scope canonique)."""

    scope: Literal["RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ"]
    """Dimension évaluée."""

    status: Literal["available", "insufficient_data"]
    """"available" : score produit par le LLM, verdict valide.
    "insufficient_data" : score absent, aucun verdict (DECISION-WP5C-8)."""

    score: Optional[int] = Field(None, ge=0, le=10)
    """Score LLM brut [0-10]. Obligatoirement None si status="insufficient_data"."""

    polarity: Optional[Literal["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "POSITIF"]] = None
    """Polarity canonique, dérivée par decision_rules.derive_polarity() (KERNEL-INV-010).
    Obligatoirement None si status="insufficient_data".
    interpretation_text ne peut ni la modifier ni la contredire."""

    interpretation_text: Optional[str] = None
    """Qualifier textuel produit par le LLM (ex : "critique", "solide").
    Informatif uniquement. N'est jamais une source de vérité décisionnelle (KERNEL-INV-010)."""

    findings: List[Finding] = Field(default_factory=list)
    """Vide en dk-1. Alimenté en dk-2+ si attributions Niveau 2 activées (KERNEL-INV-009)."""

    recommendations: List[Recommendation] = Field(default_factory=list)
    """Vide en dk-1. Alimenté en dk-2+ si attributions Niveau 2 activées."""

    @model_validator(mode="after")
    def validate_status_coherence(self) -> "Decision":
        """Enforce la cohérence structurelle entre status, score et polarity.

        DECISION-WP5C-8 / SPEC-DK-001 Rev 3.1 §1.2 :
          - "insufficient_data" : score et polarity DOIVENT être None.
          - "available"         : score et polarity NE DOIVENT PAS être None.
        La correction sémantique (polarity cohérente avec le score) est la responsabilité
        de l'extracteur via decision_rules.derive_polarity() — pas de ce validator.
        """
        if self.status == "insufficient_data":
            if self.score is not None:
                raise ValueError(
                    f"Decision(scope={self.scope!r}, status='insufficient_data') : "
                    "score doit être None. "
                    "Une Decision sans données ne porte aucun score (DECISION-WP5C-8)."
                )
            if self.polarity is not None:
                raise ValueError(
                    f"Decision(scope={self.scope!r}, status='insufficient_data') : "
                    "polarity doit être None. "
                    "Une Decision sans données ne porte aucune polarity (DECISION-WP5C-8)."
                )
        else:  # status == "available"
            if self.score is None:
                raise ValueError(
                    f"Decision(scope={self.scope!r}, status='available') : "
                    "score ne peut pas être None (DECISION-WP5C-8)."
                )
            if self.polarity is None:
                raise ValueError(
                    f"Decision(scope={self.scope!r}, status='available') : "
                    "polarity ne peut pas être None (DECISION-WP5C-8)."
                )
        return self


# ── AttributionMetrics ────────────────────────────────────────────────────────

class AttributionMetrics(BaseModel):
    """Mesure quantitative de la couverture d'attribution du Kernel.

    Stocke des compteurs bruts (int) — les taux sont dérivables par les consommateurs
    pour éviter duplication et erreurs d'arrondi (DECISION-WP5C-10).

    En dk-1 : findings_scoped = 0 et recommendations_scoped = 0 invariablement
    (KERNEL-INV-009). Le modèle accepte d'autres valeurs pour préparer dk-2.
    """

    model_config = ConfigDict(extra="forbid")

    mode: Literal["conservative_v1"]
    """Stratégie d'attribution. "conservative_v1" : Niveau 1 uniquement (dk-1)."""

    dimension_decisions_available: int = Field(..., ge=0, le=4)
    """Nombre de Decisions avec status="available" [0–4]."""

    findings_total: int = Field(..., ge=0)
    """Nombre total de Findings dans le Kernel (global + dimensionnels)."""

    findings_scoped: int = Field(..., ge=0)
    """Findings avec scope_status="scoped". Invariablement 0 en dk-1."""

    recommendations_total: int = Field(..., ge=0)
    """Nombre total de Recommendations dans le Kernel."""

    recommendations_scoped: int = Field(..., ge=0)
    """Recommendations avec scope_status="scoped". Invariablement 0 en dk-1."""


# ── DecisionKernel ────────────────────────────────────────────────────────────

class DecisionKernel(BaseModel):
    """Source de vérité unique et immuable des décisions Pepperyn pour une analyse.

    Structure en 5 blocs canoniques (SPEC-DK-001 Rev 3.1 §III.1) :
      Bloc A — Identité du Kernel
      Bloc B — Contexte décisionnel
      Bloc C — Verdicts (4 Decisions dimensionnelles + score global dérivé)
      Bloc D — Findings et Recommendations globaux (dk-1)
      Bloc E — Méta-décisionnel

    Invariants structurels enforced par ce modèle :
      CA-2 : decisions contient exactement 4 éléments couvrant les 4 scopes.
      CA-4 : decision_fingerprint et decision_fingerprint_version liés.
    Les invariants CA-8 (cohérence score_global), CA-9 (provenance), CA-10
    (non-duplication), CA-11 (compteurs attribution) sont vérifiés par l'extracteur.
    """

    model_config = ConfigDict(extra="forbid")

    # ── Bloc A — Identité ─────────────────────────────────────────────────────

    kernel_id: str
    """UUID de l'analyse source. Identifiant unique du Kernel."""

    kernel_version: Literal["dk-1"] = KERNEL_VERSION
    """Version du schéma Kernel. "dk-1" pour cette implémentation (WP5C)."""

    kernel_produced_at: datetime
    """Horodatage de scellement UTC. Immutable après production (KERNEL-INV-001)."""

    decision_fingerprint: Optional[str] = None
    """SHA-256[:32] de l'identité décisionnelle (WP5A, KERNEL-INV-013).
    None avant la phase de scellement."""

    decision_fingerprint_version: Optional[str] = None
    """Version de l'algorithme de fingerprint. Doit être défini si fingerprint est
    défini, et absent si fingerprint est absent (CA-4)."""

    source_data_hash: Optional[str] = None
    """SHA-256 du fichier source brut (WP5A). None pour les analyses pré-WP5A."""

    # ── Bloc B — Contexte ─────────────────────────────────────────────────────

    type_document: str = "AUTRE"
    """Nature du document analysé (BILAN, P&L, TRÉSORERIE…)."""

    secteur: Optional[str] = None
    """Secteur d'activité identifié."""

    modele_economique: Optional[str] = None
    """Modèle économique identifié."""

    # ── Bloc C — Verdicts ─────────────────────────────────────────────────────

    decisions: List[Decision]
    """Les 4 emplacements dimensionnels. Toujours 4, status variable (CA-2).
    Ordre canonique : RENTABILITÉ (d-01), RISQUE (d-02), STRUCTURE (d-03),
    LIQUIDITÉ (d-04) — enforced par la Phase 10 (canonicalisation) de l'extracteur."""

    score_global: Optional[int] = Field(None, ge=0, le=10)
    """Synthèse dérivée par decision_rules.derive_score_global() depuis les
    Decisions available uniquement. None si aucune Decision available (KERNEL-INV-008)."""

    niveau_urgence: Optional[Literal["Critique", "Élevé", "Modéré", "Maîtrisé"]] = None
    """Dérivé de score_global par decision_rules.derive_niveau_urgence() (KERNEL-INV-008).
    None si score_global est None."""

    # ── Bloc D — Findings et Recommendations globaux ──────────────────────────

    global_findings: List[Finding] = Field(default_factory=list)
    """Findings non attribués à une dimension (scope_status="global").
    Structure principale de dk-1 (KERNEL-INV-009)."""

    global_recommendations: List[Recommendation] = Field(default_factory=list)
    """Recommendations non attribuées (scope_status="global")."""

    # ── Bloc E — Méta-décisionnel ─────────────────────────────────────────────

    score_confiance: Optional[int] = Field(None, ge=0, le=100)
    """Confiance du moteur dans ses décisions [0-100]."""

    data_quality_score: Optional[int] = Field(None, ge=0, le=100)
    """Score qualité des données sources [0-100]."""

    data_quality_blocking: Optional[bool] = None
    """True si la qualité des données a bloqué ou dégradé les décisions."""

    attribution: Optional[AttributionMetrics] = None
    """Mesure de la couverture d'attribution (DECISION-WP5C-10). None si non calculé."""

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("decisions")
    @classmethod
    def validate_decisions_structure(cls, v: List[Decision]) -> List[Decision]:
        """Enforce CA-2 : exactement 4 Decisions, les 4 scopes canoniques, sans doublon.

        L'ordre des scopes dans la liste est la responsabilité de la Phase 10
        (canonicalisation) de l'extracteur — ce validator vérifie la présence
        et l'unicité, pas l'ordre.
        """
        if len(v) != 4:
            raise ValueError(
                f"decisions doit contenir exactement 4 éléments (CA-2). Reçu : {len(v)}."
            )

        scopes = [d.scope for d in v]

        missing = set(_CANONICAL_SCOPES) - set(scopes)
        unexpected = set(scopes) - set(_CANONICAL_SCOPES)
        if missing or unexpected:
            raise ValueError(
                f"decisions doit couvrir exactement {list(_CANONICAL_SCOPES)}. "
                f"Manquant : {sorted(missing) or '—'}. "
                f"Inattendu : {sorted(unexpected) or '—'}."
            )

        seen: set[str] = set()
        for scope in scopes:
            if scope in seen:
                raise ValueError(
                    f"Chaque scope ne peut apparaître qu'une fois dans decisions. "
                    f"Doublon détecté : {scope!r}."
                )
            seen.add(scope)

        return v

    @model_validator(mode="after")
    def validate_fingerprint_pair(self) -> "DecisionKernel":
        """Enforce CA-4 : fingerprint et fingerprint_version sont set ensemble ou absents ensemble."""
        has_fp = self.decision_fingerprint is not None
        has_fp_v = self.decision_fingerprint_version is not None
        if has_fp != has_fp_v:
            raise ValueError(
                "decision_fingerprint et decision_fingerprint_version doivent être définis "
                "ensemble ou absents ensemble (CA-4). "
                f"fingerprint={'set' if has_fp else 'None'}, "
                f"fingerprint_version={'set' if has_fp_v else 'None'}."
            )
        return self
