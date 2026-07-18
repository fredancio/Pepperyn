"""
decision_kernel_extractor.py — WP5C, Commit 3
===============================================

Extracteur déterministe AnalysisResult → DecisionKernel dk-1.

Fonction pure : pour un AnalysisResult identique et une version d'extracteur
identique, produit toujours le même DecisionKernel (hors kernel_produced_at).

Garanties
---------
- Aucun appel réseau, aucune lecture de base de données, aucun accès disque.
- Aucune dépendance à analyze.py.
- Aucune génération de Decision Fingerprint (Commit 6 — KERNEL-INV-013).
- Aucune logique de présentation.
- AnalysisResult n'est jamais modifié (lecture seule).

Pipeline interne (12 phases)
-----------------------------
    Phase 1  — Extraction Bloc A + Bloc B (contexte et identité)
    Phase 2  — Extraction des 4 Decisions dimensionnelles
    Phase 3  — Collecte des candidats global_findings
    Phase 4  — Déduplication global_findings (KERNEL-INV-012)
    Phase 5  — Collecte des candidats global_recommendations
    Phase 6  — Déduplication global_recommendations
    Phase 7  — Dérivation score_global + niveau_urgence (decision_rules)
    Phase 8  — Calcul AttributionMetrics
    Phase 9  — Decision Fingerprint (après Phase 10, KERNEL-INV-013)
    Phase 10 — Canonicalisation (ordre stable, JSONB déterministe)
    Phase 11 — Scellement (kernel_produced_at)
    Phase 12 — Validation CA-1 → CA-11

Note sur Phase 11 : kernel_produced_at est posé lors de la construction Pydantic
(étape Phase 1) avec la valeur fournie par `_produced_at` ou datetime.now(UTC).
Cet écart par rapport à la séquence stricte du plan (Phase 11 après Phase 10)
est sans conséquence — le timestamp ne dépend pas du contenu canonicalisé.

Sources de Findings (ordre de priorité §3.4 SPEC-DK-001)
----------------------------------------------------------
    1. problemes_critiques   severity=CRITIQUE
    2. alertes               severity=ÉLEVÉ
    3. impact_financier      severity=None
    4. ce_qui_detruit        severity=None
    5. margin_intelligence   severity=None  source_section=MARGIN_INTELLIGENCE
    6. cash_forecast         severity=None  source_section=CASH_FORECAST
    7. bfr_indicators        severity=None  source_section=BFR_INDICATORS

Sources de Recommendations (ordre de priorité §3.4 SPEC-DK-001)
-----------------------------------------------------------------
    1. plan_action_haute       priority=HAUTE      horizon_défaut=IMMÉDIAT
    2. plan_action_secondaire  priority=SECONDAIRE horizon_défaut=COURT_TERME
    3. leviers_croissance      priority=SECONDAIRE horizon_défaut=MOYEN_TERME
    4. opportunites_v3         priority=SECONDAIRE horizon_défaut=MOYEN_TERME

Référence spec : SPEC-DK-001 Rev 3.1 (DESIGN FROZEN), WP5C_IMPLEMENTATION_PLAN §3
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from models.schemas import AnalysisResult
from services.decision_kernel import (
    KERNEL_VERSION,
    AttributionMetrics,
    Decision,
    DecisionKernel,
    Finding,
    Recommendation,
    SourceRef,
)
from services.decision_fingerprint import compute_decision_fingerprint_from_kernel  # WP5C Phase 9
from services.decision_rules import (
    derive_niveau_urgence,
    derive_polarity,
    derive_score_global,
)

logger = logging.getLogger(__name__)

# ── Version ───────────────────────────────────────────────────────────────────
EXTRACTOR_VERSION: str = "v1"

# ── Sources de Findings (ordre = priorité de déduplication) ──────────────────
# Tuples : (champ AnalysisResult, severity par défaut, source_section)
_FINDING_SOURCES: List[Tuple[str, Optional[str], Optional[str]]] = [
    ("problemes_critiques", "CRITIQUE",  None),
    ("alertes",             "ÉLEVÉ",     None),
    ("impact_financier",    None,        None),
    ("ce_qui_detruit",      None,        None),
    ("margin_intelligence", None,        "MARGIN_INTELLIGENCE"),
    ("cash_forecast",       None,        "CASH_FORECAST"),
    ("bfr_indicators",      None,        "BFR_INDICATORS"),
]

# ── Sources de Recommendations (ordre = priorité de déduplication) ────────────
# Tuples : (champ AnalysisResult, priority, horizon par défaut)
_RECOMMENDATION_SOURCES: List[Tuple[str, str, str]] = [
    ("plan_action_haute",      "HAUTE",      "IMMÉDIAT"),
    ("plan_action_secondaire", "SECONDAIRE", "COURT_TERME"),
    ("leviers_croissance",     "SECONDAIRE", "MOYEN_TERME"),
    ("opportunites_v3",        "SECONDAIRE", "MOYEN_TERME"),
]

# ── Dimensions canoniques (local_id, scope, champ score, clé interpretations) ─
_DIMENSIONS: List[Tuple[str, str, str, str]] = [
    ("d-01", "RENTABILITÉ", "score_rentabilite", "rentabilite"),
    ("d-02", "RISQUE",      "score_risque",      "risque"),
    ("d-03", "STRUCTURE",   "score_structure",   "structure"),
    ("d-04", "LIQUIDITÉ",   "score_liquidite",   "liquidite"),
]

# ── Rangs pour la fusion lors de déduplication ────────────────────────────────
_SEVERITY_RANK: Dict[Optional[str], int] = {
    "CRITIQUE": 4, "ÉLEVÉ": 3, "MODÉRÉ": 2, "FAIBLE": 1, None: 0,
}
_PRIORITY_RANK: Dict[str, int] = {"HAUTE": 2, "SECONDAIRE": 1}

# ── Mapping horizon plan_action_30_60_90 ──────────────────────────────────────
_HORIZON_MAP: Dict[str, str] = {
    "30": "IMMÉDIAT",
    "60": "COURT_TERME",
    "90": "MOYEN_TERME",
}


# ─────────────────────────────────────────────────────────────────────────────
# Exception de validation
# ─────────────────────────────────────────────────────────────────────────────

class KernelValidationError(Exception):
    """Levée quand un DecisionKernel viole un critère CA (CA-1 à CA-11).

    Capturée par extract_decision_kernel() qui retourne alors None.
    Ref : SPEC-DK-001 §IX — Critères d'acceptation.
    """

    def __init__(self, criteria: str, details: str, kernel_id: str) -> None:
        self.criteria = criteria
        self.details = details
        self.kernel_id = kernel_id
        super().__init__(f"[{kernel_id}] {criteria}: {details}")


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation (déduplication uniquement — le texte stocké reste brut)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Normaliser un texte pour la comparaison de déduplication.

    La forme normalisée est utilisée uniquement comme clé de comparaison.
    Le texte original (statement / directive) est toujours conservé intact.

    Algorithme : lowercase → strip → collapse espaces → retire ponctuation → strip.

    Input  : text (str)
    Output : chaîne normalisée (peut être vide)
    Ref    : KERNEL-INV-012, SPEC-DK-001 §3.4
    """
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Extraction des 4 Decisions dimensionnelles
# ─────────────────────────────────────────────────────────────────────────────

def _extract_decisions(ar: AnalysisResult) -> List[Decision]:
    """Phase 2 — Extraire les 4 Decisions dimensionnelles depuis AnalysisResult.

    Ordre fixe : d-01 RENTABILITÉ, d-02 RISQUE, d-03 STRUCTURE, d-04 LIQUIDITÉ.
    Polarity dérivée par decision_rules.derive_polarity() — jamais depuis
    interpretation_text (KERNEL-INV-010).

    Input  : ar (AnalysisResult) — post-pipeline, post-EDM
    Output : List[Decision] — toujours exactement 4 éléments, ordre canonique
    Ref    : SPEC-DK-001 §3.2, DECISION-WP5C-8, KERNEL-INV-010
    """
    decisions: List[Decision] = []
    interpretations: dict = ar.score_interpretations or {}

    for local_id, scope, score_field, interp_key in _DIMENSIONS:
        score: Optional[int] = getattr(ar, score_field, None)

        # interpretation_text : None si vide, absent ou non-str (jamais "")
        interp_raw = interpretations.get(interp_key)
        interp: Optional[str] = (
            interp_raw.strip()
            if isinstance(interp_raw, str) and interp_raw.strip()
            else None
        )

        if score is None:
            decisions.append(Decision(
                local_id=local_id,
                scope=scope,
                status="insufficient_data",
                score=None,
                polarity=None,
                interpretation_text=interp,
                findings=[],
                recommendations=[],
            ))
        else:
            polarity = derive_polarity(scope=scope, score=score)
            decisions.append(Decision(
                local_id=local_id,
                scope=scope,
                status="available",
                score=score,
                polarity=polarity,
                interpretation_text=interp,
                findings=[],
                recommendations=[],
            ))

    return decisions


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Collecte des candidats global_findings
# ─────────────────────────────────────────────────────────────────────────────

def _extract_finding_candidates(ar: AnalysisResult) -> List[Finding]:
    """Phase 3 — Collecter tous les candidats Finding dans l'ordre de priorité.

    Items vides ou blancs sont filtrés. local_id = "" (placeholder — assigné
    après déduplication en Phase 4).

    Input  : ar (AnalysisResult)
    Output : List[Finding] — candidats ordonnés par priorité de champ source
    Ref    : SPEC-DK-001 §3.3, §10.4, KERNEL-INV-011
    """
    candidates: List[Finding] = []

    for source_field, default_severity, source_section in _FINDING_SOURCES:
        items: List[str] = getattr(ar, source_field, None) or []
        for idx, text in enumerate(items):
            if not text or not text.strip():
                continue
            candidates.append(Finding(
                local_id="",                    # placeholder — Phase 4
                statement=text.strip(),
                source_field=source_field,
                source_index=idx,
                source_section=source_section,
                severity=default_severity,
                scope_status="global",
                evidence_refs=[],
                source_refs=[],
            ))

    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — Déduplication global_findings
# ─────────────────────────────────────────────────────────────────────────────

def _deduplicate_findings(candidates: List[Finding]) -> List[Finding]:
    """Phase 4 — Dédupliquer les candidats Finding par statement normalisé.

    Algorithme (KERNEL-INV-012, SPEC-DK-001 §3.4) :
      - Clé : normalize(statement)
      - Le premier candidat rencontré (plus haute priorité de champ) devient primaire.
      - Les doublons sont absorbés : leur provenance est ajoutée dans source_refs.
      - Severity la plus haute est retenue.
      - local_id assigné séquentiellement après fusion (f-01, f-02, …).

    Input  : candidates — en ordre de priorité des champs source
    Output : List[Finding] — dédupliqués, local_id assignés
    Ref    : KERNEL-INV-012, SPEC-DK-001 §3.4
    """
    groups: Dict[str, Finding] = {}  # normalized_statement → primary Finding

    for candidate in candidates:
        key = _normalize_text(candidate.statement)
        if not key:
            continue

        if key not in groups:
            groups[key] = candidate
        else:
            primary = groups[key]
            # Absorber le doublon : conserver sa provenance dans source_refs
            primary.source_refs.append(SourceRef(
                source_field=candidate.source_field,
                source_index=candidate.source_index,
                source_section=candidate.source_section,
            ))
            # Retenir la severity la plus haute (KERNEL-INV-012)
            if (
                _SEVERITY_RANK.get(candidate.severity, 0)
                > _SEVERITY_RANK.get(primary.severity, 0)
            ):
                primary.severity = candidate.severity

    # Assigner les local_ids séquentiellement dans l'ordre de groupes
    deduped = list(groups.values())
    for i, finding in enumerate(deduped, start=1):
        finding.local_id = f"f-{i:02d}"

    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Collecte des candidats global_recommendations
# ─────────────────────────────────────────────────────────────────────────────

def _build_horizon_lookup(ar: AnalysisResult) -> Dict[str, str]:
    """Construire un lookup normalisé → horizon depuis plan_action_30_60_90.

    Enrichissement optionnel et non-bloquant (SPEC-DK-001 §3.3).
    Items malformés ou sans correspondance dans _HORIZON_MAP sont ignorés.

    Input  : ar (AnalysisResult)
    Output : Dict[str, str] — normalized_directive → Literal horizon
    """
    lookup: Dict[str, str] = {}
    for item in (getattr(ar, "plan_action_30_60_90", None) or []):
        if not item.action or item.horizon not in _HORIZON_MAP:
            continue
        key = _normalize_text(item.action)
        if key:
            lookup[key] = _HORIZON_MAP[item.horizon]
    return lookup


def _extract_recommendation_candidates(
    ar: AnalysisResult,
    horizon_lookup: Dict[str, str],
) -> List[Recommendation]:
    """Phase 5 — Collecter tous les candidats Recommendation dans l'ordre de priorité.

    Items vides filtrés. Horizon enrichi depuis plan_action_30_60_90 si disponible.
    local_id = "" (placeholder — assigné après déduplication en Phase 6).

    Input  : ar (AnalysisResult), horizon_lookup (Dict[str, str])
    Output : List[Recommendation] — candidats ordonnés par priorité de champ source
    Ref    : SPEC-DK-001 §3.3, §10.4, KERNEL-INV-011
    """
    candidates: List[Recommendation] = []

    for source_field, priority, default_horizon in _RECOMMENDATION_SOURCES:
        items: List[str] = getattr(ar, source_field, None) or []
        for idx, text in enumerate(items):
            if not text or not text.strip():
                continue
            # Horizon enrichment depuis plan_action_30_60_90 (optionnel)
            norm = _normalize_text(text)
            horizon = horizon_lookup.get(norm, default_horizon)
            candidates.append(Recommendation(
                local_id="",                    # placeholder — Phase 6
                directive=text.strip(),
                source_field=source_field,
                source_index=idx,
                priority=priority,
                horizon=horizon,
                intent_text=None,
                expected_outcome=None,
                scope_status="global",
                source_refs=[],
            ))

    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Déduplication global_recommendations
# ─────────────────────────────────────────────────────────────────────────────

def _deduplicate_recommendations(candidates: List[Recommendation]) -> List[Recommendation]:
    """Phase 6 — Dédupliquer les candidats Recommendation par directive normalisée.

    Même algorithme que Phase 4 avec directive comme clé et priority_rank pour
    la fusion. local_id assigné séquentiellement après fusion (r-01, r-02, …).

    Input  : candidates — en ordre de priorité des champs source
    Output : List[Recommendation] — dédupliqués, local_id assignés
    Ref    : KERNEL-INV-012, SPEC-DK-001 §3.4
    """
    groups: Dict[str, Recommendation] = {}  # normalized_directive → primary

    for candidate in candidates:
        key = _normalize_text(candidate.directive)
        if not key:
            continue

        if key not in groups:
            groups[key] = candidate
        else:
            primary = groups[key]
            # Absorber le doublon : conserver sa provenance
            primary.source_refs.append(SourceRef(
                source_field=candidate.source_field,
                source_index=candidate.source_index,
                source_section=None,
            ))
            # Retenir la priority la plus haute
            if (
                _PRIORITY_RANK.get(candidate.priority, 0)
                > _PRIORITY_RANK.get(primary.priority, 0)
            ):
                primary.priority = candidate.priority

    # Assigner les local_ids séquentiellement
    deduped = list(groups.values())
    for i, rec in enumerate(deduped, start=1):
        rec.local_id = f"r-{i:02d}"

    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8 — Calcul AttributionMetrics
# ─────────────────────────────────────────────────────────────────────────────

def _compute_attribution(
    decisions: List[Decision],
    global_findings: List[Finding],
    global_recommendations: List[Recommendation],
) -> AttributionMetrics:
    """Phase 8 — Calculer les AttributionMetrics dk-1.

    En dk-1 : Decision.findings et Decision.recommendations sont toujours vides.
    findings_scoped = 0 et recommendations_scoped = 0 invariablement.

    Input  : decisions, global_findings, global_recommendations
    Output : AttributionMetrics (mode="conservative_v1")
    Ref    : DECISION-WP5C-10, SPEC-DK-001 §3.1 Bloc E
    """
    available_count = sum(1 for d in decisions if d.status == "available")

    # Findings : global + scoped dans les decisions (= 0 en dk-1)
    findings_in_decisions = sum(len(d.findings) for d in decisions)
    findings_total = len(global_findings) + findings_in_decisions
    findings_scoped = sum(
        1 for f in global_findings if f.scope_status == "scoped"
    ) + sum(
        1 for d in decisions for f in d.findings if f.scope_status == "scoped"
    )

    # Recommendations : global + scoped dans les decisions (= 0 en dk-1)
    recs_in_decisions = sum(len(d.recommendations) for d in decisions)
    recs_total = len(global_recommendations) + recs_in_decisions
    recs_scoped = sum(
        1 for r in global_recommendations if r.scope_status == "scoped"
    ) + sum(
        1 for d in decisions for r in d.recommendations if r.scope_status == "scoped"
    )

    return AttributionMetrics(
        mode="conservative_v1",
        dimension_decisions_available=available_count,
        findings_total=findings_total,
        findings_scoped=findings_scoped,
        recommendations_total=recs_total,
        recommendations_scoped=recs_scoped,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10 — Canonicalisation
# ─────────────────────────────────────────────────────────────────────────────

def _canonicalize(kernel: DecisionKernel) -> None:
    """Phase 10 — Canonicaliser l'ordre des objets dans le Kernel (in-place).

    Garantit que deux extractions du même AnalysisResult produisent exactement
    le même JSONB — même ordre des objets, indépendamment de l'ordre d'insertion.

    Étapes :
      1. decisions          → triées par local_id  (d-01, d-02, d-03, d-04)
      2. global_findings    → triés par local_id   (f-01, f-02, …)
      3. global_recommendations → triées par local_id (r-01, r-02, …)
      4. source_refs de chaque Finding → triés par (source_field, source_index)
      5. source_refs de chaque Recommendation → idem
      6. evidence_refs de chaque Finding → triés lexicographiquement (vides en dk-1)

    Input  : kernel (DecisionKernel) — modifié in-place
    Output : None
    Ref    : WP5C_IMPLEMENTATION_PLAN §3.10, Phase 10
    """
    # 1. Decisions
    kernel.decisions.sort(key=lambda d: d.local_id)

    # 2. Global findings
    kernel.global_findings.sort(key=lambda f: f.local_id)

    # 3. Global recommendations
    kernel.global_recommendations.sort(key=lambda r: r.local_id)

    # 4+6. source_refs et evidence_refs de chaque Finding
    for finding in kernel.global_findings:
        finding.source_refs.sort(key=lambda s: (s.source_field, s.source_index))
        finding.evidence_refs.sort()

    # 5. source_refs de chaque Recommendation
    for rec in kernel.global_recommendations:
        rec.source_refs.sort(key=lambda s: (s.source_field, s.source_index))

    # Canonicaliser aussi les findings/recs dans les Decisions (vides en dk-1)
    for decision in kernel.decisions:
        decision.findings.sort(key=lambda f: f.local_id)
        decision.recommendations.sort(key=lambda r: r.local_id)
        for f in decision.findings:
            f.source_refs.sort(key=lambda s: (s.source_field, s.source_index))
            f.evidence_refs.sort()
        for r in decision.recommendations:
            r.source_refs.sort(key=lambda s: (s.source_field, s.source_index))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 12 — Validation CA-1 → CA-11
# ─────────────────────────────────────────────────────────────────────────────

def _validate_kernel(kernel: DecisionKernel) -> None:
    """Phase 12 — Valider les critères d'acceptation CA-1 à CA-11.

    Lève KernelValidationError sur toute violation structurelle.
    CA-3, CA-6, CA-7 (sémantiques) : validés en test uniquement, pas en runtime.
    CA-5 : warning uniquement, pas bloquant.
    CA-4 : enforced structurellement par DecisionKernel.validate_fingerprint_pair
            (Pydantic) — non redondé ici.

    Input  : kernel (DecisionKernel) — entièrement construit, canonicalisé, scellé
    Output : None (lève KernelValidationError sur violation)
    Ref    : SPEC-DK-001 §IX
    """
    kid = kernel.kernel_id

    # CA-1 — Complétude minimale (garantie par construction + Pydantic)
    if not kernel.kernel_id or not kernel.kernel_version or kernel.kernel_produced_at is None:
        raise KernelValidationError(
            "CA-1", "kernel_id, kernel_version et kernel_produced_at sont requis.", kid
        )

    # CA-2 — Slot dimensionnel : exactement 4 decisions + au moins 1 available
    # (len==4 et présence des 4 scopes déjà enforced par Pydantic field_validator)
    available = [d for d in kernel.decisions if d.status == "available"]
    if not available:
        raise KernelValidationError(
            "CA-2",
            "Aucune Decision available. Kernel en état insufficient_data complet — "
            "decision_kernel sera NULL en base (DECISION-WP5C-8).",
            kid,
        )

    # CA-5 — source_data_hash présent (warning uniquement)
    if not kernel.source_data_hash:
        logger.warning(
            "[%s] CA-5 : source_data_hash absent. Attendu pour les analyses post-WP5A.",
            kid,
        )

    # CA-8 — Cohérence globale/dimensionnelle
    scores_map = {d.scope: d.score for d in kernel.decisions}
    expected_global = derive_score_global(scores_map)
    if kernel.score_global != expected_global:
        raise KernelValidationError(
            "CA-8",
            f"score_global={kernel.score_global} != dérivé depuis les scores "
            f"dimensionnels={expected_global}. Incohérence KERNEL-INV-005.",
            kid,
        )

    # CA-9 — Provenance complète sur tous les Findings et Recommendations
    all_findings: List[Finding] = list(kernel.global_findings) + [
        f for d in kernel.decisions for f in d.findings
    ]
    all_recs: List[Recommendation] = list(kernel.global_recommendations) + [
        r for d in kernel.decisions for r in d.recommendations
    ]
    for f in all_findings:
        if not f.source_field or f.source_index < -1:
            raise KernelValidationError(
                "CA-9",
                f"Finding {f.local_id!r} : source_field vide ou source_index < -1.",
                kid,
            )
    for r in all_recs:
        if not r.source_field or r.source_index < -1:
            raise KernelValidationError(
                "CA-9",
                f"Recommendation {r.local_id!r} : source_field vide ou source_index < -1.",
                kid,
            )

    # CA-10 — Absence de duplication (garantie par les Phases 4 et 6)
    finding_keys = [_normalize_text(f.statement) for f in all_findings if f.statement]
    if len(finding_keys) != len(set(finding_keys)):
        raise KernelValidationError(
            "CA-10",
            "Doublons de Finding détectés après déduplication. Erreur dans l'extracteur.",
            kid,
        )
    rec_keys = [_normalize_text(r.directive) for r in all_recs if r.directive]
    if len(rec_keys) != len(set(rec_keys)):
        raise KernelValidationError(
            "CA-10",
            "Doublons de Recommendation détectés après déduplication. Erreur dans l'extracteur.",
            kid,
        )

    # CA-11 — Attribution mesurée et cohérente
    if kernel.attribution:
        actual_findings_total = len(all_findings)
        if kernel.attribution.findings_total != actual_findings_total:
            raise KernelValidationError(
                "CA-11",
                f"attribution.findings_total={kernel.attribution.findings_total} "
                f"!= réel={actual_findings_total}.",
                kid,
            )
        actual_recs_total = len(all_recs)
        if kernel.attribution.recommendations_total != actual_recs_total:
            raise KernelValidationError(
                "CA-11",
                f"attribution.recommendations_total={kernel.attribution.recommendations_total} "
                f"!= réel={actual_recs_total}.",
                kid,
            )
        actual_available = sum(1 for d in kernel.decisions if d.status == "available")
        if kernel.attribution.dimension_decisions_available != actual_available:
            raise KernelValidationError(
                "CA-11",
                f"attribution.dimension_decisions_available="
                f"{kernel.attribution.dimension_decisions_available} "
                f"!= réel={actual_available}.",
                kid,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée public
# ─────────────────────────────────────────────────────────────────────────────

def extract_decision_kernel(
    analysis_result: AnalysisResult,
    analyse_id: str,
    source_data_hash: Optional[str] = None,
    *,
    _produced_at: Optional[datetime] = None,
) -> Optional[DecisionKernel]:
    """Extracteur déterministe AnalysisResult → DecisionKernel dk-1.

    Fonction pure : à AnalysisResult et analyse_id identiques, produit le même
    DecisionKernel (hors kernel_produced_at si _produced_at n'est pas fourni).

    Ne génère pas le Decision Fingerprint — sera ajouté au Commit 6
    conformément à KERNEL-INV-013.
    Ne modifie jamais l'AnalysisResult passé en entrée.

    Args:
        analysis_result  : AnalysisResult post-pipeline, post-EDM. Lecture seule.
        analyse_id       : UUID de l'analyse — devient kernel_id dans le Kernel.
        source_data_hash : SHA-256 du fichier source brut (WP5A). Optionnel.
        _produced_at     : Horodatage de scellement forcé (test uniquement).
                           Si None, datetime.now(timezone.utc) est utilisé.

    Returns:
        DecisionKernel dk-1 valide, ou None si la validation CA échoue
        (notamment CA-2 : aucune Decision available).

    Version : EXTRACTOR_VERSION = "v1"
    Ref     : SPEC-DK-001 Rev 3.1, WP5C_IMPLEMENTATION_PLAN §3
    """
    try:
        return _run_extraction_pipeline(
            analysis_result, analyse_id, source_data_hash, _produced_at
        )
    except KernelValidationError as exc:
        logger.error(
            "[%s] Kernel validation failed — %s : %s. decision_kernel=NULL.",
            analyse_id, exc.criteria, exc.details,
        )
        return None
    except Exception:
        logger.exception(
            "[%s] Erreur inattendue dans l'extracteur dk-1. decision_kernel=NULL.",
            analyse_id,
        )
        return None


def _run_extraction_pipeline(
    ar: AnalysisResult,
    analyse_id: str,
    source_data_hash: Optional[str],
    produced_at: Optional[datetime],
) -> DecisionKernel:
    """Exécuter le pipeline complet (Phases 1–12). Levée sur violation CA.

    Séparé de extract_decision_kernel() pour rendre les exceptions testables
    sans masquage par le handler de prod (return None).
    """
    # ── Phase 2 — 4 Decisions dimensionnelles ─────────────────────────────────
    decisions = _extract_decisions(ar)

    # ── Phase 3 + 4 — global_findings ─────────────────────────────────────────
    finding_candidates = _extract_finding_candidates(ar)
    global_findings = _deduplicate_findings(finding_candidates)

    # ── Phase 5 + 6 — global_recommendations ──────────────────────────────────
    horizon_lookup = _build_horizon_lookup(ar)
    rec_candidates = _extract_recommendation_candidates(ar, horizon_lookup)
    global_recommendations = _deduplicate_recommendations(rec_candidates)

    # ── Phase 7 — score_global + niveau_urgence ────────────────────────────────
    scores_map: Dict[str, Optional[int]] = {d.scope: d.score for d in decisions}
    score_global = derive_score_global(scores_map)
    niveau_urgence = derive_niveau_urgence(score_global)

    # ── Phase 8 — AttributionMetrics ──────────────────────────────────────────
    attribution = _compute_attribution(decisions, global_findings, global_recommendations)

    # ── Phase 1 + 11 — Construction + Scellement ──────────────────────────────
    # Phases 1 et 11 réunies : Pydantic exige tous les champs à la construction.
    # kernel_produced_at = horodatage de scellement (Phase 11 du plan).
    dq = ar.data_quality
    kernel = DecisionKernel(
        # Bloc A — Identité
        kernel_id=analyse_id,
        kernel_version=KERNEL_VERSION,
        kernel_produced_at=produced_at or datetime.now(timezone.utc),
        decision_fingerprint=None,              # Phase 9 : posé après Phase 10 (KERNEL-INV-013)
        decision_fingerprint_version=None,      # Phase 9 : posé après Phase 10
        source_data_hash=source_data_hash,
        # Bloc B — Contexte (secteur/modele_economique absents de AnalysisResult dk-1)
        type_document=ar.type_document or "AUTRE",
        secteur=None,
        modele_economique=None,
        # Bloc C — Verdicts
        decisions=decisions,
        score_global=score_global,
        niveau_urgence=niveau_urgence,
        # Bloc D — Findings et Recommendations globaux
        global_findings=global_findings,
        global_recommendations=global_recommendations,
        # Bloc E — Méta-décisionnel
        score_confiance=ar.score_confiance,
        data_quality_score=dq.score_data if dq is not None else None,
        data_quality_blocking=(dq.status == "blocked") if dq is not None else None,
        attribution=attribution,
    )

    # ── Phase 10 — Canonicalisation ───────────────────────────────────────────
    _canonicalize(kernel)

    # ── Phase 9 — Decision Fingerprint (KERNEL-INV-013) ──────────────────────
    # Calculé APRÈS Phase 10 : global_recommendations et global_findings sont
    # dans un ordre stable et déterministe avant d'entrer dans le hash SHA-256.
    # compute_decision_fingerprint_from_kernel() délègue à l'algorithme WP5A
    # inchangé — seule la source des données est le Kernel (KERNEL-INV-013).
    # Retourne (None, None) si le Kernel n'a pas de champ décisionnel significatif
    # (cas théorique dans ce branch, CA-2 étant intercepté avant cette étape).
    _fp, _fp_version = compute_decision_fingerprint_from_kernel(kernel)
    kernel.decision_fingerprint = _fp
    kernel.decision_fingerprint_version = _fp_version

    # ── Phase 12 — Validation CA-1 → CA-11 ───────────────────────────────────
    _validate_kernel(kernel)

    return kernel
