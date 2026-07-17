"""
test_decision_kernel_extractor.py — WP5C, Commit 3
====================================================

Suite de tests pour backend/services/decision_kernel_extractor.py.

Organisation
------------
    TestNormalizeText                 (3)   — _normalize_text
    TestExtractDecisions              (7)   — _extract_decisions
    TestExtractFindingCandidates      (5)   — _extract_finding_candidates
    TestDeduplicateFindings           (7)   — _deduplicate_findings
    TestBuildHorizonLookup            (3)   — _build_horizon_lookup
    TestExtractRecommendationCandidates(5)  — _extract_recommendation_candidates
    TestDeduplicateRecommendations    (5)   — _deduplicate_recommendations
    TestComputeAttribution            (4)   — _compute_attribution
    TestCanonicalize                  (6)   — _canonicalize
    TestValidateKernel                (8)   — _validate_kernel / KernelValidationError
    TestExtractDecisionKernel         (15)  — extract_decision_kernel (intégration)

Total : 68 tests

Ref : SPEC-DK-001 Rev 3.1, WP5C_IMPLEMENTATION_PLAN §3
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import pytest

from models.schemas import AnalysisResult, DataQualityInfo, PlanActionItem
from services.decision_kernel import (
    AttributionMetrics,
    Decision,
    DecisionKernel,
    Finding,
    Recommendation,
    SourceRef,
)
from services.decision_kernel_extractor import (
    EXTRACTOR_VERSION,
    KernelValidationError,
    _build_horizon_lookup,
    _canonicalize,
    _compute_attribution,
    _deduplicate_findings,
    _deduplicate_recommendations,
    _extract_decisions,
    _extract_finding_candidates,
    _extract_recommendation_candidates,
    _normalize_text,
    _run_extraction_pipeline,
    _validate_kernel,
    extract_decision_kernel,
)

# ── Fixture globale : horodatage fixe pour le déterminisme ──────────────────
_TEST_NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)
_ANALYSE_ID = "test-analyse-001"


def _ar(**kwargs) -> AnalysisResult:
    """Construire un AnalysisResult minimal valide avec scores par défaut.

    Scores par défaut : rentabilite=5, risque=7, structure=6, liquidite=4.
    Tout champ peut être surchargé via **kwargs.
    """
    defaults = dict(
        score_rentabilite=5,
        score_risque=7,
        score_structure=6,
        score_liquidite=4,
    )
    defaults.update(kwargs)
    return AnalysisResult(**defaults)


def _minimal_kernel(
    *,
    decisions: Optional[List[Decision]] = None,
    global_findings: Optional[List[Finding]] = None,
    global_recommendations: Optional[List[Recommendation]] = None,
    attribution: Optional[AttributionMetrics] = None,
    score_global: Optional[int] = 5,
    source_data_hash: Optional[str] = "abc123",
) -> DecisionKernel:
    """Construire un DecisionKernel minimal valide pour les tests de validation."""
    if decisions is None:
        decisions = [
            Decision(
                local_id=f"d-0{i}",
                scope=scope,
                status="available",
                score=5,
                polarity="MODÉRÉ",
            )
            for i, scope in enumerate(
                ("RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ"), start=1
            )
        ]
    if global_findings is None:
        global_findings = []
    if global_recommendations is None:
        global_recommendations = []
    if attribution is None:
        available_count = sum(1 for d in decisions if d.status == "available")
        attribution = AttributionMetrics(
            mode="conservative_v1",
            dimension_decisions_available=available_count,
            findings_total=len(global_findings),
            findings_scoped=0,
            recommendations_total=len(global_recommendations),
            recommendations_scoped=0,
        )
    return DecisionKernel(
        kernel_id=_ANALYSE_ID,
        kernel_version="dk-1",
        kernel_produced_at=_TEST_NOW,
        source_data_hash=source_data_hash,
        decisions=decisions,
        score_global=score_global,
        global_findings=global_findings,
        global_recommendations=global_recommendations,
        attribution=attribution,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TestNormalizeText
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeText:
    """Tests pour _normalize_text().

    Vérifie l'algorithme : lowercase → strip → collapse espaces →
    retire ponctuation → strip.
    Réf. KERNEL-INV-012.
    """

    def test_empty_string_returns_empty(self):
        """Chaîne vide → chaîne vide."""
        assert _normalize_text("") == ""

    def test_normalizes_case_spaces_punctuation(self):
        """Majuscules, espaces multiples et ponctuation supprimés."""
        result = _normalize_text("  Marge NETTE en baisse : -15%  !")
        assert result == "marge nette en baisse 15"

    def test_accented_characters_preserved(self):
        """Les caractères accentués sont conservés (\\w en Python couvre Unicode)."""
        result = _normalize_text("Problème de liquidité élevé")
        assert result == "problème de liquidité élevé"


# ─────────────────────────────────────────────────────────────────────────────
# TestExtractDecisions
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractDecisions:
    """Tests pour _extract_decisions().

    Vérifie l'extraction des 4 Decisions dimensionnelles depuis AnalysisResult.
    Réf. SPEC-DK-001 §3.2, KERNEL-INV-010.
    """

    def test_returns_exactly_four_decisions(self):
        """Toujours exactement 4 Decisions."""
        decisions = _extract_decisions(_ar())
        assert len(decisions) == 4

    def test_canonical_local_ids_and_scopes(self):
        """local_ids d-01..d-04 et scopes dans l'ordre canonique."""
        decisions = _extract_decisions(_ar())
        expected = [
            ("d-01", "RENTABILITÉ"),
            ("d-02", "RISQUE"),
            ("d-03", "STRUCTURE"),
            ("d-04", "LIQUIDITÉ"),
        ]
        actual = [(d.local_id, d.scope) for d in decisions]
        assert actual == expected

    def test_available_when_score_present(self):
        """status=available quand le score est fourni."""
        decisions = _extract_decisions(_ar(score_rentabilite=6))
        rentabilite = next(d for d in decisions if d.scope == "RENTABILITÉ")
        assert rentabilite.status == "available"
        assert rentabilite.score == 6

    def test_insufficient_data_when_score_none(self):
        """status=insufficient_data quand le score est None."""
        decisions = _extract_decisions(_ar(score_rentabilite=None))
        rentabilite = next(d for d in decisions if d.scope == "RENTABILITÉ")
        assert rentabilite.status == "insufficient_data"
        assert rentabilite.score is None
        assert rentabilite.polarity is None

    def test_risque_polarity_uses_inversion(self):
        """RISQUE polarity dérivée par derive_polarity (score effectif = 10 - 7 = 3 → CRITIQUE).

        score_risque=7 → effective=3 → CRITIQUE.
        Réf. KERNEL-INV-010, DECISION-WP5C-8.
        """
        decisions = _extract_decisions(_ar(score_risque=7))
        risque = next(d for d in decisions if d.scope == "RISQUE")
        assert risque.polarity == "CRITIQUE"

    def test_interpretation_text_extracted(self):
        """interpretation_text lu depuis score_interpretations."""
        ar = _ar(score_interpretations={"rentabilite": "Marge sous pression."})
        decisions = _extract_decisions(ar)
        rentabilite = next(d for d in decisions if d.scope == "RENTABILITÉ")
        assert rentabilite.interpretation_text == "Marge sous pression."

    def test_interpretation_text_none_when_empty(self):
        """interpretation_text None si chaîne vide ou blancs uniquement."""
        ar = _ar(score_interpretations={"liquidite": "  "})
        decisions = _extract_decisions(ar)
        liquidite = next(d for d in decisions if d.scope == "LIQUIDITÉ")
        assert liquidite.interpretation_text is None


# ─────────────────────────────────────────────────────────────────────────────
# TestExtractFindingCandidates
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractFindingCandidates:
    """Tests pour _extract_finding_candidates().

    Vérifie la collecte des candidats depuis les 7 champs source.
    Réf. SPEC-DK-001 §3.3, §10.4.
    """

    def test_empty_ar_returns_empty_list(self):
        """AnalysisResult vide → aucun candidat."""
        candidates = _extract_finding_candidates(_ar(
            score_rentabilite=5,
            score_risque=7,
            score_structure=6,
            score_liquidite=4,
        ))
        assert candidates == []

    def test_problemes_critiques_severity_critique(self):
        """problemes_critiques → severity=CRITIQUE."""
        ar = _ar(problemes_critiques=["Cash burn critique"])
        candidates = _extract_finding_candidates(ar)
        assert len(candidates) == 1
        assert candidates[0].source_field == "problemes_critiques"
        assert candidates[0].severity == "CRITIQUE"

    def test_alertes_severity_eleve(self):
        """alertes → severity=ÉLEVÉ."""
        ar = _ar(alertes=["Marge dégradée"])
        candidates = _extract_finding_candidates(ar)
        assert candidates[0].severity == "ÉLEVÉ"

    def test_margin_intelligence_has_source_section(self):
        """margin_intelligence → source_section=MARGIN_INTELLIGENCE."""
        ar = _ar(margin_intelligence=["Contribution margin declining"])
        candidates = _extract_finding_candidates(ar)
        assert candidates[0].source_section == "MARGIN_INTELLIGENCE"
        assert candidates[0].severity is None

    def test_blank_items_filtered_out(self):
        """Items vides ou blancs ignorés."""
        ar = _ar(alertes=["", "  ", "Alerte réelle"])
        candidates = _extract_finding_candidates(ar)
        assert len(candidates) == 1
        assert candidates[0].statement == "Alerte réelle"


# ─────────────────────────────────────────────────────────────────────────────
# TestDeduplicateFindings
# ─────────────────────────────────────────────────────────────────────────────

class TestDeduplicateFindings:
    """Tests pour _deduplicate_findings().

    Vérifie la déduplication par statement normalisé et la fusion.
    Réf. KERNEL-INV-012, SPEC-DK-001 §3.4.
    """

    def _make_candidate(
        self,
        statement: str,
        source_field: str = "alertes",
        source_index: int = 0,
        severity: Optional[str] = "ÉLEVÉ",
    ) -> Finding:
        return Finding(
            local_id="",
            statement=statement,
            source_field=source_field,
            source_index=source_index,
            severity=severity,
        )

    def test_empty_candidates_returns_empty(self):
        """Aucun candidat → liste vide."""
        assert _deduplicate_findings([]) == []

    def test_unique_candidates_all_kept(self):
        """Sans doublon, tous les candidats conservés."""
        candidates = [
            self._make_candidate("Marge basse"),
            self._make_candidate("Cash burn élevé"),
        ]
        result = _deduplicate_findings(candidates)
        assert len(result) == 2

    def test_exact_duplicate_merged(self):
        """Doublon exact → un seul Finding, source_refs enrichis."""
        candidates = [
            self._make_candidate("Marge basse", "problemes_critiques", 0),
            self._make_candidate("Marge basse", "alertes", 1),
        ]
        result = _deduplicate_findings(candidates)
        assert len(result) == 1
        assert len(result[0].source_refs) == 1
        assert result[0].source_refs[0].source_field == "alertes"

    def test_near_duplicate_merged_after_normalization(self):
        """Doublon avec ponctuation différente → fusionné."""
        candidates = [
            self._make_candidate("Marge nette : -15%"),
            self._make_candidate("Marge nette  -15"),
        ]
        result = _deduplicate_findings(candidates)
        assert len(result) == 1

    def test_severity_upgrade_on_merge(self):
        """Severity la plus haute retenue sur fusion."""
        low = self._make_candidate("Problème X", severity=None)
        high = self._make_candidate("Problème X", severity="CRITIQUE")
        # Premier = primaire (priorité source), deuxième = absorbé mais CRITIQUE
        result = _deduplicate_findings([low, high])
        assert result[0].severity == "CRITIQUE"

    def test_no_severity_downgrade(self):
        """Severity ne descend jamais lors d'une fusion."""
        high = self._make_candidate("Problème Y", severity="CRITIQUE")
        low = self._make_candidate("Problème Y", severity="FAIBLE")
        result = _deduplicate_findings([high, low])
        assert result[0].severity == "CRITIQUE"

    def test_local_ids_assigned_sequentially(self):
        """local_ids assignés f-01, f-02, f-03."""
        candidates = [
            self._make_candidate(f"Problème {i}")
            for i in range(3)
        ]
        result = _deduplicate_findings(candidates)
        assert [f.local_id for f in result] == ["f-01", "f-02", "f-03"]


# ─────────────────────────────────────────────────────────────────────────────
# TestBuildHorizonLookup
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildHorizonLookup:
    """Tests pour _build_horizon_lookup().

    Vérifie l'enrichissement horizon depuis plan_action_30_60_90.
    """

    def test_empty_plan_action_returns_empty_dict(self):
        """Aucun PlanActionItem → dict vide."""
        assert _build_horizon_lookup(_ar()) == {}

    def test_valid_items_build_lookup(self):
        """PlanActionItems valides → lookup construit."""
        ar = _ar(plan_action_30_60_90=[
            PlanActionItem(action="Réduire les frais généraux", horizon="30"),
            PlanActionItem(action="Renégocier les contrats", horizon="90"),
        ])
        lookup = _build_horizon_lookup(ar)
        key1 = _normalize_text("Réduire les frais généraux")
        key2 = _normalize_text("Renégocier les contrats")
        assert lookup.get(key1) == "IMMÉDIAT"
        assert lookup.get(key2) == "MOYEN_TERME"

    def test_invalid_horizon_ignored(self):
        """PlanActionItem avec horizon invalide ignoré."""
        ar = _ar(plan_action_30_60_90=[
            PlanActionItem(action="Action invalide", horizon="45"),
        ])
        assert _build_horizon_lookup(ar) == {}


# ─────────────────────────────────────────────────────────────────────────────
# TestExtractRecommendationCandidates
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractRecommendationCandidates:
    """Tests pour _extract_recommendation_candidates().

    Vérifie la collecte des candidats depuis les 4 champs source.
    """

    def test_empty_ar_returns_empty_list(self):
        """AnalysisResult vide → aucun candidat."""
        candidates = _extract_recommendation_candidates(_ar(), {})
        assert candidates == []

    def test_plan_action_haute_priority_and_horizon(self):
        """plan_action_haute → priority=HAUTE, horizon=IMMÉDIAT par défaut."""
        ar = _ar(plan_action_haute=["Lever des fonds immédiatement"])
        candidates = _extract_recommendation_candidates(ar, {})
        assert len(candidates) == 1
        assert candidates[0].priority == "HAUTE"
        assert candidates[0].horizon == "IMMÉDIAT"

    def test_horizon_enriched_from_lookup(self):
        """Horizon surchargé par plan_action_30_60_90 si correspondance."""
        ar = _ar(plan_action_haute=["Réduire charges"])
        lookup = {_normalize_text("Réduire charges"): "MOYEN_TERME"}
        candidates = _extract_recommendation_candidates(ar, lookup)
        assert candidates[0].horizon == "MOYEN_TERME"

    def test_leviers_croissance_secondaire_moyen_terme(self):
        """leviers_croissance → priority=SECONDAIRE, horizon=MOYEN_TERME."""
        ar = _ar(leviers_croissance=["Développer B2B"])
        candidates = _extract_recommendation_candidates(ar, {})
        assert candidates[0].priority == "SECONDAIRE"
        assert candidates[0].horizon == "MOYEN_TERME"

    def test_blank_items_filtered_out(self):
        """Items blancs ignorés."""
        ar = _ar(plan_action_haute=["", "Action réelle", "  "])
        candidates = _extract_recommendation_candidates(ar, {})
        assert len(candidates) == 1
        assert candidates[0].directive == "Action réelle"


# ─────────────────────────────────────────────────────────────────────────────
# TestDeduplicateRecommendations
# ─────────────────────────────────────────────────────────────────────────────

class TestDeduplicateRecommendations:
    """Tests pour _deduplicate_recommendations().

    Vérifie la déduplication par directive normalisée.
    Réf. KERNEL-INV-012.
    """

    def _make_rec(
        self,
        directive: str,
        source_field: str = "plan_action_haute",
        source_index: int = 0,
        priority: str = "HAUTE",
        horizon: str = "IMMÉDIAT",
    ) -> Recommendation:
        return Recommendation(
            local_id="",
            directive=directive,
            source_field=source_field,
            source_index=source_index,
            priority=priority,
            horizon=horizon,
        )

    def test_no_duplicates_all_kept(self):
        """Sans doublon, toutes les recommandations conservées."""
        recs = [
            self._make_rec("Action A"),
            self._make_rec("Action B"),
        ]
        result = _deduplicate_recommendations(recs)
        assert len(result) == 2

    def test_exact_duplicate_merged(self):
        """Doublon exact → une seule Recommendation, source_refs enrichis."""
        recs = [
            self._make_rec("Réduire les charges", "plan_action_haute", 0, "HAUTE"),
            self._make_rec("Réduire les charges", "leviers_croissance", 1, "SECONDAIRE"),
        ]
        result = _deduplicate_recommendations(recs)
        assert len(result) == 1
        assert len(result[0].source_refs) == 1

    def test_priority_upgrade_on_merge(self):
        """Priority la plus haute retenue sur fusion."""
        low = self._make_rec("Action X", priority="SECONDAIRE")
        high = self._make_rec("Action X", priority="HAUTE")
        result = _deduplicate_recommendations([low, high])
        assert result[0].priority == "HAUTE"

    def test_no_priority_downgrade(self):
        """Priority ne descend jamais lors d'une fusion."""
        high = self._make_rec("Action Y", priority="HAUTE")
        low = self._make_rec("Action Y", priority="SECONDAIRE")
        result = _deduplicate_recommendations([high, low])
        assert result[0].priority == "HAUTE"

    def test_local_ids_assigned_sequentially(self):
        """local_ids assignés r-01, r-02, r-03."""
        recs = [self._make_rec(f"Action {i}") for i in range(3)]
        result = _deduplicate_recommendations(recs)
        assert [r.local_id for r in result] == ["r-01", "r-02", "r-03"]


# ─────────────────────────────────────────────────────────────────────────────
# TestComputeAttribution
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeAttribution:
    """Tests pour _compute_attribution().

    Vérifie le calcul des AttributionMetrics dk-1 (mode=conservative_v1).
    Réf. DECISION-WP5C-10.
    """

    def _make_decisions(self, n_available: int) -> List[Decision]:
        scopes = ("RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ")
        decisions = []
        for i, scope in enumerate(scopes, start=1):
            available = i <= n_available
            decisions.append(Decision(
                local_id=f"d-0{i}",
                scope=scope,
                status="available" if available else "insufficient_data",
                score=5 if available else None,
                polarity="MODÉRÉ" if available else None,
            ))
        return decisions

    def test_mode_is_conservative_v1(self):
        """mode est toujours conservative_v1."""
        attr = _compute_attribution(self._make_decisions(4), [], [])
        assert attr.mode == "conservative_v1"

    def test_all_available_count(self):
        """4 decisions available → dimension_decisions_available=4."""
        attr = _compute_attribution(self._make_decisions(4), [], [])
        assert attr.dimension_decisions_available == 4

    def test_partial_available_count(self):
        """2 decisions available → dimension_decisions_available=2."""
        attr = _compute_attribution(self._make_decisions(2), [], [])
        assert attr.dimension_decisions_available == 2

    def test_findings_and_recs_count(self):
        """findings_total et recommendations_total comptés correctement."""
        findings = [
            Finding(local_id="f-01", statement="A", source_field="alertes", source_index=0)
            for _ in range(3)
        ]
        recs = [
            Recommendation(
                local_id="r-01", directive="B",
                source_field="plan_action_haute", source_index=0,
                priority="HAUTE", horizon="IMMÉDIAT",
            )
            for _ in range(2)
        ]
        attr = _compute_attribution(self._make_decisions(4), findings, recs)
        assert attr.findings_total == 3
        assert attr.recommendations_total == 2
        assert attr.findings_scoped == 0        # dk-1 : jamais de scope attribution
        assert attr.recommendations_scoped == 0


# ─────────────────────────────────────────────────────────────────────────────
# TestCanonicalize
# ─────────────────────────────────────────────────────────────────────────────

class TestCanonicalize:
    """Tests pour _canonicalize().

    Vérifie que l'ordre des objets est stable et prévisible.
    Réf. WP5C_IMPLEMENTATION_PLAN §3.10, Phase 10.
    """

    def _make_finding(self, local_id: str, statement: str = "X") -> Finding:
        return Finding(
            local_id=local_id,
            statement=statement,
            source_field="alertes",
            source_index=0,
        )

    def _make_rec(self, local_id: str, directive: str = "Y") -> Recommendation:
        return Recommendation(
            local_id=local_id,
            directive=directive,
            source_field="plan_action_haute",
            source_index=0,
            priority="HAUTE",
            horizon="IMMÉDIAT",
        )

    def test_decisions_sorted_by_local_id(self):
        """decisions triées d-01 → d-04 même si insérées dans le désordre."""
        kernel = _minimal_kernel(
            decisions=[
                Decision(
                    local_id=lid,
                    scope=scope,
                    status="available",
                    score=5,
                    polarity="MODÉRÉ",
                )
                for lid, scope in [
                    ("d-04", "LIQUIDITÉ"),
                    ("d-02", "RISQUE"),
                    ("d-01", "RENTABILITÉ"),
                    ("d-03", "STRUCTURE"),
                ]
            ]
        )
        _canonicalize(kernel)
        assert [d.local_id for d in kernel.decisions] == ["d-01", "d-02", "d-03", "d-04"]

    def test_global_findings_sorted_by_local_id(self):
        """global_findings triées f-01 → f-03 même si insérées dans le désordre."""
        kernel = _minimal_kernel(global_findings=[
            self._make_finding("f-03"),
            self._make_finding("f-01"),
            self._make_finding("f-02"),
        ])
        _canonicalize(kernel)
        assert [f.local_id for f in kernel.global_findings] == ["f-01", "f-02", "f-03"]

    def test_global_recommendations_sorted_by_local_id(self):
        """global_recommendations triées r-01 → r-02."""
        kernel = _minimal_kernel(global_recommendations=[
            self._make_rec("r-02"),
            self._make_rec("r-01"),
        ])
        _canonicalize(kernel)
        assert [r.local_id for r in kernel.global_recommendations] == ["r-01", "r-02"]

    def test_finding_source_refs_sorted(self):
        """source_refs de chaque Finding triés par (source_field, source_index)."""
        f = self._make_finding("f-01")
        f.source_refs = [
            SourceRef(source_field="problemes_critiques", source_index=2),
            SourceRef(source_field="alertes", source_index=0),
        ]
        kernel = _minimal_kernel(global_findings=[f])
        _canonicalize(kernel)
        refs = kernel.global_findings[0].source_refs
        assert (refs[0].source_field, refs[0].source_index) == ("alertes", 0)
        assert (refs[1].source_field, refs[1].source_index) == ("problemes_critiques", 2)

    def test_finding_evidence_refs_sorted_lexicographically(self):
        """evidence_refs de chaque Finding triés lexicographiquement."""
        f = self._make_finding("f-01")
        f.evidence_refs = ["z_ref", "a_ref", "m_ref"]
        kernel = _minimal_kernel(global_findings=[f])
        _canonicalize(kernel)
        assert kernel.global_findings[0].evidence_refs == ["a_ref", "m_ref", "z_ref"]

    def test_already_sorted_kernel_unchanged(self):
        """Kernel déjà canonicalisé → inchangé (idempotence)."""
        kernel = _minimal_kernel(
            global_findings=[self._make_finding("f-01"), self._make_finding("f-02")],
        )
        _canonicalize(kernel)
        ids_first = [f.local_id for f in kernel.global_findings]
        _canonicalize(kernel)
        ids_second = [f.local_id for f in kernel.global_findings]
        assert ids_first == ids_second


# ─────────────────────────────────────────────────────────────────────────────
# TestValidateKernel
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateKernel:
    """Tests pour _validate_kernel() et KernelValidationError.

    Vérifie les critères d'acceptation CA-1 à CA-11.
    Réf. SPEC-DK-001 §IX.
    """

    def test_valid_kernel_no_exception(self):
        """Kernel valide → aucune exception."""
        _validate_kernel(_minimal_kernel())

    def test_ca2_all_insufficient_data_raises(self):
        """CA-2 : aucune Decision available → KernelValidationError."""
        decisions = [
            Decision(
                local_id=f"d-0{i}",
                scope=scope,
                status="insufficient_data",
                score=None,
                polarity=None,
            )
            for i, scope in enumerate(
                ("RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ"), start=1
            )
        ]
        kernel = _minimal_kernel(decisions=decisions, score_global=None)
        with pytest.raises(KernelValidationError) as exc:
            _validate_kernel(kernel)
        assert exc.value.criteria == "CA-2"

    def test_ca5_missing_hash_logs_warning(self, caplog):
        """CA-5 : source_data_hash absent → warning, pas d'exception."""
        kernel = _minimal_kernel(source_data_hash=None)
        with caplog.at_level(logging.WARNING):
            _validate_kernel(kernel)
        assert any("CA-5" in r.message for r in caplog.records)

    def test_ca8_wrong_score_global_raises(self):
        """CA-8 : score_global incohérent avec les scores dimensionnels → KernelValidationError.

        _minimal_kernel utilise 4 decisions avec score=5.
        derive_score_global(4 × score=5) = 5.
        On passe score_global=8 (valide mais erroné) pour déclencher CA-8.
        """
        kernel = _minimal_kernel(score_global=8)
        with pytest.raises(KernelValidationError) as exc:
            _validate_kernel(kernel)
        assert exc.value.criteria == "CA-8"

    def test_ca9_empty_source_field_raises(self):
        """CA-9 : source_field vide dans un Finding → KernelValidationError."""
        f = Finding(
            local_id="f-01",
            statement="Alerte",
            source_field="",   # invalide
            source_index=0,
        )
        kernel = _minimal_kernel(
            global_findings=[f],
            attribution=AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=4,
                findings_total=1,
                findings_scoped=0,
                recommendations_total=0,
                recommendations_scoped=0,
            ),
        )
        with pytest.raises(KernelValidationError) as exc:
            _validate_kernel(kernel)
        assert exc.value.criteria == "CA-9"

    def test_ca10_duplicate_findings_raises(self):
        """CA-10 : doublons après déduplication → KernelValidationError."""
        f1 = Finding(local_id="f-01", statement="Marge basse", source_field="alertes", source_index=0)
        f2 = Finding(local_id="f-02", statement="Marge basse", source_field="alertes", source_index=1)
        kernel = _minimal_kernel(
            global_findings=[f1, f2],
            attribution=AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=4,
                findings_total=2,
                findings_scoped=0,
                recommendations_total=0,
                recommendations_scoped=0,
            ),
        )
        with pytest.raises(KernelValidationError) as exc:
            _validate_kernel(kernel)
        assert exc.value.criteria == "CA-10"

    def test_ca11_wrong_attribution_findings_total_raises(self):
        """CA-11 : attribution.findings_total ne correspond pas au réel → KernelValidationError."""
        f = Finding(local_id="f-01", statement="Alerte", source_field="alertes", source_index=0)
        # Attribution incorrecte : findings_total=5 au lieu de 1
        kernel = _minimal_kernel(
            global_findings=[f],
            attribution=AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=4,
                findings_total=5,         # faux
                findings_scoped=0,
                recommendations_total=0,
                recommendations_scoped=0,
            ),
        )
        with pytest.raises(KernelValidationError) as exc:
            _validate_kernel(kernel)
        assert exc.value.criteria == "CA-11"

    def test_kernel_validation_error_attributes(self):
        """KernelValidationError expose criteria, details et kernel_id."""
        exc = KernelValidationError("CA-2", "Détails.", "test-id")
        assert exc.criteria == "CA-2"
        assert exc.details == "Détails."
        assert exc.kernel_id == "test-id"


# ─────────────────────────────────────────────────────────────────────────────
# TestExtractDecisionKernel (intégration)
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractDecisionKernel:
    """Tests d'intégration pour extract_decision_kernel().

    Vérifie le comportement de la fonction publique (pipeline complet).
    Réf. SPEC-DK-001 Rev 3.1, WP5C_IMPLEMENTATION_PLAN §3.
    """

    def test_happy_path_returns_kernel(self):
        """Cas nominal : retourne un DecisionKernel valide."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID,
            source_data_hash="sha256-abc",
            _produced_at=_TEST_NOW,
        )
        assert result is not None
        assert isinstance(result, DecisionKernel)

    def test_ca2_failure_returns_none(self):
        """CA-2 : aucune Decision available → retourne None (NULL kernel)."""
        ar = _ar(
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
        )
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is None

    def test_type_document_propagated(self):
        """type_document de AnalysisResult propagé dans le Kernel."""
        ar = _ar(type_document="BILAN")
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.type_document == "BILAN"

    def test_type_document_defaults_to_autre_when_empty(self):
        """type_document vide → 'AUTRE' dans le Kernel.

        AnalysisResult.type_document est str (non Optional), donc on teste
        la chaîne vide "" — traitée comme falsy par l'extracteur.
        """
        ar = _ar(type_document="")
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.type_document == "AUTRE"

    def test_score_confiance_propagated(self):
        """score_confiance de AnalysisResult propagé."""
        ar = _ar(score_confiance=85)
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.score_confiance == 85

    def test_data_quality_propagated(self):
        """data_quality → score_data et status propagés."""
        dq = DataQualityInfo(score_data=72, status="ok")
        ar = _ar(data_quality=dq)
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.data_quality_score == 72
        assert result.data_quality_blocking is False

    def test_data_quality_blocking_true_when_blocked(self):
        """data_quality.status='blocked' → data_quality_blocking=True."""
        dq = DataQualityInfo(score_data=20, status="blocked")
        ar = _ar(data_quality=dq)
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.data_quality_blocking is True

    def test_data_quality_none_produces_none_fields(self):
        """data_quality=None → data_quality_score et data_quality_blocking sont None."""
        ar = _ar(data_quality=None)
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.data_quality_score is None
        assert result.data_quality_blocking is None

    def test_produced_at_respected(self):
        """_produced_at surchargé → kernel_produced_at correspondant."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert result is not None
        assert result.kernel_produced_at == _TEST_NOW

    def test_determinism_same_input_same_output(self):
        """Même entrée → même sortie (déterminisme, hors kernel_produced_at)."""
        ar = _ar(
            alertes=["Marge basse", "Cash burn"],
            plan_action_haute=["Lever des fonds"],
        )
        r1 = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        r2 = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert r1 is not None and r2 is not None
        # Comparer les JSONs (excluent kernel_produced_at qui est forcé identique ici)
        assert r1.model_dump() == r2.model_dump()

    def test_decision_fingerprint_set_after_extraction(self):
        """decision_fingerprint et decision_fingerprint_version sont posés par Phase 9."""
        result = extract_decision_kernel(_ar(), _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert result.decision_fingerprint is not None
        assert result.decision_fingerprint_version is not None

    def test_source_data_hash_propagated(self):
        """source_data_hash fourni → propagé dans le Kernel."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID,
            source_data_hash="sha256-xyz",
            _produced_at=_TEST_NOW,
        )
        assert result is not None
        assert result.source_data_hash == "sha256-xyz"

    def test_score_global_and_niveau_urgence_derived(self):
        """score_global et niveau_urgence correctement dérivés depuis les scores."""
        result = extract_decision_kernel(
            _ar(
                score_rentabilite=5,
                score_risque=7,
                score_structure=6,
                score_liquidite=4,
            ),
            _ANALYSE_ID,
            _produced_at=_TEST_NOW,
        )
        assert result is not None
        # Vérifications cohérence
        assert result.score_global is not None
        assert result.niveau_urgence is not None

    def test_global_findings_populated_from_ar(self):
        """global_findings extraits depuis AnalysisResult."""
        ar = _ar(alertes=["Marge en baisse", "Dette court terme"])
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert len(result.global_findings) == 2
        assert result.global_findings[0].local_id == "f-01"

    def test_global_recommendations_populated_from_ar(self):
        """global_recommendations extraites depuis AnalysisResult."""
        ar = _ar(plan_action_haute=["Réduire coûts"], leviers_croissance=["Développer export"])
        result = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is not None
        assert len(result.global_recommendations) == 2


# ─────────────────────────────────────────────────────────────────────────────
# TestExtractorVersion
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractorVersion:
    """Vérifie que la constante EXTRACTOR_VERSION est bien exportée."""

    def test_extractor_version_is_v1(self):
        """EXTRACTOR_VERSION == 'v1'."""
        assert EXTRACTOR_VERSION == "v1"


# ─────────────────────────────────────────────────────────────────────────────
# TestRunExtractionPipelineRaisesOnValidationError
# ─────────────────────────────────────────────────────────────────────────────

class TestRunExtractionPipelineRaisesOnValidationError:
    """_run_extraction_pipeline() lève KernelValidationError (testable sans masquage).

    extract_decision_kernel() capture ces exceptions et retourne None.
    Ces tests permettent de vérifier que les exceptions sont bien levées.
    """

    def test_ca2_raises_from_pipeline(self):
        """CA-2 → KernelValidationError levée par _run_extraction_pipeline."""
        ar = _ar(
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
        )
        with pytest.raises(KernelValidationError) as exc:
            _run_extraction_pipeline(ar, _ANALYSE_ID, "sha256-abc", _TEST_NOW)
        assert exc.value.criteria == "CA-2"
        assert exc.value.kernel_id == _ANALYSE_ID


# ─────────────────────────────────────────────────────────────────────────────
# TestPhase9Fingerprint — WP5C Commit 6 (KERNEL-INV-013)
# ─────────────────────────────────────────────────────────────────────────────

class TestPhase9Fingerprint:
    """Vérifie la Phase 9 — Decision Fingerprint intégré dans le pipeline extracteur.

    KERNEL-INV-013 : compute_decision_fingerprint_from_kernel() est appelée
    APRÈS Phase 10 (canonicalisation), AVANT Phase 12 (validation).
    Le fingerprint est posé sur kernel.decision_fingerprint et
    kernel.decision_fingerprint_version.

    Tests d'intégration via extract_decision_kernel() (pipeline complet).
    """

    def test_fingerprint_present_apres_extraction(self):
        """Pipeline complet → decision_fingerprint est non-None dans le Kernel."""
        result = extract_decision_kernel(
            _ar(score_rentabilite=5, score_risque=7, score_structure=6, score_liquidite=4),
            _ANALYSE_ID,
            source_data_hash="sha256-xyz",
            _produced_at=_TEST_NOW,
        )
        assert result is not None
        assert result.decision_fingerprint is not None

    def test_fingerprint_version_est_v1(self):
        """decision_fingerprint_version == "v1" (FINGERPRINT_VERSION)."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert result is not None
        assert result.decision_fingerprint_version == "v1"

    def test_fingerprint_est_32_hex_chars(self):
        """Format : chaîne de 32 caractères hexadécimaux."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert result is not None
        fp = result.decision_fingerprint
        assert fp is not None
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fingerprint_deterministe(self):
        """Même AnalysisResult → même fingerprint sur deux invocations."""
        ar = _ar(
            score_rentabilite=3,
            score_risque=8,
            alertes=["Marge critique"],
            plan_action_haute=["Réduire les coûts fixes"],
        )
        r1 = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        r2 = extract_decision_kernel(ar, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert r1 is not None and r2 is not None
        assert r1.decision_fingerprint == r2.decision_fingerprint

    def test_fingerprint_nul_si_ca2(self):
        """CA-2 : extract_decision_kernel() retourne None → pas de Kernel, pas de fingerprint."""
        ar_ca2 = _ar(
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
        )
        result = extract_decision_kernel(ar_ca2, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert result is None   # pas de Kernel, donc pas de fingerprint

    def test_fingerprint_differe_selon_scores(self):
        """Scores différents → fingerprints différents (quand la tranche change)."""
        ar_faible = _ar(score_rentabilite=2)   # FAIBLE
        ar_eleve  = _ar(score_rentabilite=8)   # ÉLEVÉ
        r1 = extract_decision_kernel(ar_faible, _ANALYSE_ID, _produced_at=_TEST_NOW)
        r2 = extract_decision_kernel(ar_eleve,  _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert r1 is not None and r2 is not None
        assert r1.decision_fingerprint != r2.decision_fingerprint

    def test_fingerprint_ca4_pair_set_together(self):
        """CA-4 : fingerprint et fingerprint_version sont posés ensemble."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert result is not None
        has_fp = result.decision_fingerprint is not None
        has_version = result.decision_fingerprint_version is not None
        assert has_fp == has_version, "CA-4 : fingerprint et version doivent être liés"

    def test_fingerprint_inclus_dans_kernel_jsonb(self):
        """model_dump() inclut decision_fingerprint — sérialisable dans JSONB."""
        result = extract_decision_kernel(
            _ar(), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert result is not None
        dumped = result.model_dump(mode="json")
        assert "decision_fingerprint" in dumped
        assert dumped["decision_fingerprint"] is not None
        assert "decision_fingerprint_version" in dumped
        assert dumped["decision_fingerprint_version"] == "v1"
