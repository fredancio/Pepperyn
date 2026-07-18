"""
test_decision_kernel.py — WP5C, Commit 2
==========================================

Tests unitaires des modèles Pydantic du Decision Kernel.

Ces tests vérifient :
  - La construction valide de chaque modèle
  - Le rejet des champs supplémentaires (extra="forbid")
  - Les vocabulaires fermés (Literal)
  - Les contraintes numériques (ge, le, ge=-1)
  - La cohérence structurelle Decision.status / score / polarity
  - L'invariant des 4 scopes canoniques dans DecisionKernel.decisions (CA-2)
  - La contrainte de paire fingerprint (CA-4)
  - L'absence totale de logique métier dérivée dans les modèles

Périmètre : validation structurelle uniquement. Aucune logique d'extraction,
de persistance, de fingerprint ou de calcul (decision_rules) n'est testée ici.
L'absence de logique dérivée est vérifiée explicitement dans TestDecisionConformite
et TestDecisionKernelConformite.

Référence : SPEC-DK-001 Rev 3.1 (DESIGN FROZEN), WP5C Commit 2.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from pydantic import ValidationError

from services.decision_kernel import (
    KERNEL_VERSION,
    AttributionMetrics,
    Decision,
    DecisionKernel,
    Finding,
    Recommendation,
    SourceRef,
)

# ── Helpers de construction ───────────────────────────────────────────────────
# Chaque helper retourne un dict minimal valide — les tests surchargent
# les clés dont ils ont besoin.

_NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


def _sr(**kw) -> dict:
    return {"source_field": "alertes", "source_index": 0, **kw}


def _finding(**kw) -> dict:
    return {
        "local_id": "f-01",
        "statement": "La trésorerie est négative.",
        "source_field": "problemes_critiques",
        "source_index": 0,
        **kw,
    }


def _rec(**kw) -> dict:
    return {
        "local_id": "r-01",
        "directive": "Réduire les charges fixes.",
        "source_field": "plan_action_haute",
        "source_index": 0,
        "priority": "HAUTE",
        "horizon": "IMMÉDIAT",
        **kw,
    }


def _decision_available(**kw) -> dict:
    return {
        "local_id": "d-01",
        "scope": "RENTABILITÉ",
        "status": "available",
        "score": 5,
        "polarity": "MODÉRÉ",
        **kw,
    }


def _decision_insufficient(**kw) -> dict:
    return {
        "local_id": "d-02",
        "scope": "RISQUE",
        "status": "insufficient_data",
        **kw,
    }


def _four_decisions() -> list:
    """Les 4 Decisions canoniques minimales valides."""
    return [
        _decision_available(local_id="d-01", scope="RENTABILITÉ", score=5, polarity="MODÉRÉ"),
        _decision_insufficient(local_id="d-02", scope="RISQUE"),
        _decision_available(local_id="d-03", scope="STRUCTURE", score=7, polarity="MODÉRÉ"),
        _decision_insufficient(local_id="d-04", scope="LIQUIDITÉ"),
    ]


def _kernel(**kw) -> dict:
    return {
        "kernel_id": "test-uuid-001",
        "kernel_produced_at": _NOW,
        "decisions": _four_decisions(),
        **kw,
    }


# ── 1. Version canonique ──────────────────────────────────────────────────────

class TestKernelVersion:
    def test_constante_dk1(self):
        """KERNEL_VERSION est la chaîne canonique 'dk-1'."""
        assert KERNEL_VERSION == "dk-1"

    def test_constante_est_str(self):
        """KERNEL_VERSION est bien une str, pas un Literal ou un enum."""
        assert isinstance(KERNEL_VERSION, str)


# ── 2. SourceRef ──────────────────────────────────────────────────────────────

class TestSourceRef:
    def test_construction_minimale(self):
        sr = SourceRef(**_sr())
        assert sr.source_field == "alertes"
        assert sr.source_index == 0
        assert sr.source_section is None

    def test_avec_source_section(self):
        sr = SourceRef(**_sr(source_section="CASH_FORECAST"))
        assert sr.source_section == "CASH_FORECAST"

    def test_source_index_moins_un_accepte(self):
        """source_index = -1 est valide (champ scalaire source)."""
        sr = SourceRef(**_sr(source_index=-1))
        assert sr.source_index == -1

    def test_source_index_trop_bas_rejete(self):
        """source_index < -1 est invalide (ge=-1)."""
        with pytest.raises(ValidationError):
            SourceRef(**_sr(source_index=-2))

    def test_champ_extra_rejete(self):
        """extra='forbid' : tout champ non canonique lève une ValidationError."""
        with pytest.raises(ValidationError):
            SourceRef(**_sr(champ_inconnu="oops"))


# ── 3. Finding ────────────────────────────────────────────────────────────────

class TestFinding:
    def test_construction_minimale(self):
        f = Finding(**_finding())
        assert f.local_id == "f-01"
        assert f.statement == "La trésorerie est négative."
        assert f.source_field == "problemes_critiques"
        assert f.source_index == 0

    def test_defaults(self):
        """scope_status défaut "global", severity None, listes vides."""
        f = Finding(**_finding())
        assert f.scope_status == "global"
        assert f.severity is None
        assert f.source_section is None
        assert f.evidence_refs == []
        assert f.source_refs == []

    def test_severity_valeurs_valides(self):
        for sev in ("CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"):
            f = Finding(**_finding(severity=sev))
            assert f.severity == sev

    def test_severity_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(severity="UNKNOWN"))

    def test_scope_status_valeurs_valides(self):
        for ss in ("scoped", "global"):
            f = Finding(**_finding(scope_status=ss))
            assert f.scope_status == ss

    def test_scope_status_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(scope_status="GLOBAL"))

    def test_source_refs_liste_source_ref(self):
        """source_refs accepte une liste de SourceRef (dict coercé par Pydantic)."""
        f = Finding(**_finding(source_refs=[_sr(), _sr(source_index=1)]))
        assert len(f.source_refs) == 2
        assert isinstance(f.source_refs[0], SourceRef)

    def test_champ_extra_rejete(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(champ_inconnu="oops"))


# ── 4. Recommendation ─────────────────────────────────────────────────────────

class TestRecommendation:
    def test_construction_minimale(self):
        r = Recommendation(**_rec())
        assert r.local_id == "r-01"
        assert r.directive == "Réduire les charges fixes."
        assert r.priority == "HAUTE"
        assert r.horizon == "IMMÉDIAT"

    def test_defaults(self):
        """scope_status défaut "global", intent_text/expected_outcome None, source_refs vide."""
        r = Recommendation(**_rec())
        assert r.scope_status == "global"
        assert r.intent_text is None
        assert r.expected_outcome is None
        assert r.source_refs == []

    def test_priority_valeurs_valides(self):
        for p in ("HAUTE", "SECONDAIRE"):
            r = Recommendation(**_rec(priority=p))
            assert r.priority == p

    def test_priority_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Recommendation(**_rec(priority="BASSE"))

    def test_horizon_valeurs_valides(self):
        for h in ("IMMÉDIAT", "COURT_TERME", "MOYEN_TERME"):
            r = Recommendation(**_rec(horizon=h))
            assert r.horizon == h

    def test_horizon_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Recommendation(**_rec(horizon="LONG_TERME"))

    def test_scope_status_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Recommendation(**_rec(scope_status="SCOPED"))

    def test_champ_extra_rejete(self):
        with pytest.raises(ValidationError):
            Recommendation(**_rec(champ_inconnu="oops"))


# ── 5. Decision ───────────────────────────────────────────────────────────────

class TestDecisionAvailable:
    def test_construction_valide(self):
        d = Decision(**_decision_available())
        assert d.status == "available"
        assert d.score == 5
        assert d.polarity == "MODÉRÉ"

    def test_defaults(self):
        """interpretation_text None, findings/recommendations vides."""
        d = Decision(**_decision_available())
        assert d.interpretation_text is None
        assert d.findings == []
        assert d.recommendations == []

    def test_available_sans_score_rejete(self):
        """available exige score ≠ None (DECISION-WP5C-8)."""
        with pytest.raises(ValidationError, match="score ne peut pas être None"):
            Decision(**_decision_available(score=None))

    def test_available_sans_polarity_rejete(self):
        """available exige polarity ≠ None (DECISION-WP5C-8)."""
        with pytest.raises(ValidationError, match="polarity ne peut pas être None"):
            Decision(**_decision_available(polarity=None))

    def test_polarity_valeurs_valides(self):
        for p in ("CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "POSITIF"):
            d = Decision(**_decision_available(polarity=p))
            assert d.polarity == p

    def test_polarity_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Decision(**_decision_available(polarity="ACCEPTABLE"))

    def test_score_borne_inferieure(self):
        d = Decision(**_decision_available(score=0))
        assert d.score == 0

    def test_score_borne_superieure(self):
        d = Decision(**_decision_available(score=10))
        assert d.score == 10

    def test_score_hors_borne_rejete(self):
        with pytest.raises(ValidationError):
            Decision(**_decision_available(score=11))


class TestDecisionInsufficientData:
    def test_construction_valide(self):
        d = Decision(**_decision_insufficient())
        assert d.status == "insufficient_data"
        assert d.score is None
        assert d.polarity is None

    def test_insufficient_avec_score_rejete(self):
        """insufficient_data interdit un score (DECISION-WP5C-8)."""
        with pytest.raises(ValidationError, match="score doit être None"):
            Decision(**_decision_insufficient(score=3))

    def test_insufficient_avec_polarity_rejete(self):
        """insufficient_data interdit une polarity (DECISION-WP5C-8)."""
        with pytest.raises(ValidationError, match="polarity doit être None"):
            Decision(**_decision_insufficient(polarity="CRITIQUE"))

    def test_interpretation_text_autorise(self):
        """interpretation_text est informatif uniquement — pas une source décisionnelle.
        Il peut être présent même pour insufficient_data (KERNEL-INV-010)."""
        d = Decision(**_decision_insufficient(interpretation_text="Données absentes."))
        assert d.interpretation_text == "Données absentes."


class TestDecisionScope:
    def test_tous_scopes_canoniques(self):
        for scope in ("RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ"):
            d = Decision(**_decision_insufficient(scope=scope))
            assert d.scope == scope

    def test_scope_invalide_rejete(self):
        with pytest.raises(ValidationError):
            Decision(**_decision_insufficient(scope="SOLIDITÉ"))

    def test_champ_extra_rejete(self):
        with pytest.raises(ValidationError):
            Decision(**_decision_available(champ_inconnu="oops"))


# ── 6. AttributionMetrics ─────────────────────────────────────────────────────

class TestAttributionMetrics:
    def test_construction_valide(self):
        am = AttributionMetrics(
            mode="conservative_v1",
            dimension_decisions_available=2,
            findings_total=5,
            findings_scoped=0,
            recommendations_total=3,
            recommendations_scoped=0,
        )
        assert am.mode == "conservative_v1"
        assert am.dimension_decisions_available == 2

    def test_mode_invalide_rejete(self):
        with pytest.raises(ValidationError):
            AttributionMetrics(
                mode="aggressive_v1",
                dimension_decisions_available=2,
                findings_total=0,
                findings_scoped=0,
                recommendations_total=0,
                recommendations_scoped=0,
            )

    def test_dimension_decisions_borne_inferieure(self):
        am = AttributionMetrics(
            mode="conservative_v1",
            dimension_decisions_available=0,
            findings_total=0, findings_scoped=0,
            recommendations_total=0, recommendations_scoped=0,
        )
        assert am.dimension_decisions_available == 0

    def test_dimension_decisions_borne_superieure(self):
        am = AttributionMetrics(
            mode="conservative_v1",
            dimension_decisions_available=4,
            findings_total=0, findings_scoped=0,
            recommendations_total=0, recommendations_scoped=0,
        )
        assert am.dimension_decisions_available == 4

    def test_dimension_decisions_hors_borne_rejete(self):
        with pytest.raises(ValidationError):
            AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=5,
                findings_total=0, findings_scoped=0,
                recommendations_total=0, recommendations_scoped=0,
            )

    def test_findings_total_negatif_rejete(self):
        with pytest.raises(ValidationError):
            AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=0,
                findings_total=-1, findings_scoped=0,
                recommendations_total=0, recommendations_scoped=0,
            )

    def test_champ_extra_rejete(self):
        with pytest.raises(ValidationError):
            AttributionMetrics(
                mode="conservative_v1",
                dimension_decisions_available=0,
                findings_total=0, findings_scoped=0,
                recommendations_total=0, recommendations_scoped=0,
                champ_inconnu="oops",
            )


# ── 7. DecisionKernel — Structure des decisions (CA-2) ────────────────────────

class TestDecisionKernelDecisions:
    def test_quatre_decisions_valide(self):
        dk = DecisionKernel(**_kernel())
        assert len(dk.decisions) == 4

    def test_trois_decisions_rejete(self):
        """CA-2 : exactement 4 decisions obligatoires."""
        decisions = _four_decisions()[:3]
        with pytest.raises(ValidationError, match="exactement 4"):
            DecisionKernel(**_kernel(decisions=decisions))

    def test_cinq_decisions_rejete(self):
        """CA-2 : plus de 4 decisions invalide."""
        decisions = _four_decisions() + [
            _decision_insufficient(local_id="d-05", scope="RISQUE"),
        ]
        with pytest.raises(ValidationError, match="exactement 4"):
            DecisionKernel(**_kernel(decisions=decisions))

    def test_scope_manquant_rejete(self):
        """CA-2 : les 4 scopes canoniques doivent tous être présents."""
        decisions = [
            _decision_available(local_id="d-01", scope="RENTABILITÉ", score=5, polarity="MODÉRÉ"),
            _decision_insufficient(local_id="d-02", scope="RISQUE"),
            _decision_available(local_id="d-03", scope="STRUCTURE", score=7, polarity="MODÉRÉ"),
            _decision_insufficient(local_id="d-04", scope="STRUCTURE"),  # doublon, manque LIQUIDITÉ
        ]
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(decisions=decisions))

    def test_scope_duplique_rejete(self):
        """CA-2 : chaque scope doit apparaître exactement une fois.

        Note de comportement : avec exactement 4 decisions, un scope en doublon implique
        toujours un scope manquant. Le validator détecte donc la violation via le check
        "Manquant" (qui précède le check "Doublon" dans le flux). L'erreur est correcte
        dans les deux cas : la liste n'est pas conforme à CA-2.
        """
        decisions = [
            _decision_available(local_id="d-01", scope="RENTABILITÉ", score=5, polarity="MODÉRÉ"),
            _decision_available(local_id="d-02", scope="RENTABILITÉ", score=6, polarity="MODÉRÉ"),
            _decision_insufficient(local_id="d-03", scope="STRUCTURE"),
            _decision_insufficient(local_id="d-04", scope="LIQUIDITÉ"),
        ]
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(decisions=decisions))

    def test_tous_insufficient_accepte(self):
        """CA-2 s'applique à la structure, pas au status. 4×insufficient_data est valide."""
        decisions = [
            _decision_insufficient(local_id="d-01", scope="RENTABILITÉ"),
            _decision_insufficient(local_id="d-02", scope="RISQUE"),
            _decision_insufficient(local_id="d-03", scope="STRUCTURE"),
            _decision_insufficient(local_id="d-04", scope="LIQUIDITÉ"),
        ]
        dk = DecisionKernel(**_kernel(decisions=decisions))
        assert len(dk.decisions) == 4

    def test_tous_available_accepte(self):
        """4×available est aussi valide."""
        decisions = [
            _decision_available(local_id="d-01", scope="RENTABILITÉ", score=5, polarity="MODÉRÉ"),
            _decision_available(local_id="d-02", scope="RISQUE", score=8, polarity="CRITIQUE"),
            _decision_available(local_id="d-03", scope="STRUCTURE", score=7, polarity="MODÉRÉ"),
            _decision_available(local_id="d-04", scope="LIQUIDITÉ", score=9, polarity="POSITIF"),
        ]
        dk = DecisionKernel(**_kernel(decisions=decisions))
        assert all(d.status == "available" for d in dk.decisions)


# ── 8. DecisionKernel — Fingerprint pair (CA-4) ───────────────────────────────

class TestDecisionKernelFingerprintPair:
    def test_fingerprint_tous_deux_none_accepte(self):
        """CA-4 : les deux absents simultanément → valide."""
        dk = DecisionKernel(**_kernel(
            decision_fingerprint=None,
            decision_fingerprint_version=None,
        ))
        assert dk.decision_fingerprint is None
        assert dk.decision_fingerprint_version is None

    def test_fingerprint_tous_deux_set_accepte(self):
        """CA-4 : les deux présents simultanément → valide."""
        dk = DecisionKernel(**_kernel(
            decision_fingerprint="a" * 32,
            decision_fingerprint_version="v1",
        ))
        assert dk.decision_fingerprint == "a" * 32
        assert dk.decision_fingerprint_version == "v1"

    def test_fingerprint_sans_version_rejete(self):
        """CA-4 : fingerprint présent, version absente → invalide."""
        with pytest.raises(ValidationError, match="CA-4"):
            DecisionKernel(**_kernel(
                decision_fingerprint="a" * 32,
                decision_fingerprint_version=None,
            ))

    def test_version_sans_fingerprint_rejete(self):
        """CA-4 : version présente, fingerprint absent → invalide."""
        with pytest.raises(ValidationError, match="CA-4"):
            DecisionKernel(**_kernel(
                decision_fingerprint=None,
                decision_fingerprint_version="v1",
            ))


# ── 9. DecisionKernel — Champs et defaults ────────────────────────────────────

class TestDecisionKernelChamps:
    def test_kernel_version_defaut(self):
        """kernel_version = 'dk-1' par défaut (KERNEL_VERSION constant)."""
        dk = DecisionKernel(**_kernel())
        assert dk.kernel_version == "dk-1"

    def test_kernel_version_invalide_rejete(self):
        """kernel_version n'accepte que 'dk-1' (Literal)."""
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(kernel_version="dk-2"))

    def test_type_document_defaut(self):
        dk = DecisionKernel(**_kernel())
        assert dk.type_document == "AUTRE"

    def test_niveau_urgence_valeurs_valides(self):
        for nu in ("Critique", "Élevé", "Modéré", "Maîtrisé"):
            dk = DecisionKernel(**_kernel(niveau_urgence=nu))
            assert dk.niveau_urgence == nu

    def test_niveau_urgence_invalide_rejete(self):
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(niveau_urgence="CRITIQUE"))

    def test_score_global_borne_inferieure(self):
        dk = DecisionKernel(**_kernel(score_global=0))
        assert dk.score_global == 0

    def test_score_global_borne_superieure(self):
        dk = DecisionKernel(**_kernel(score_global=10))
        assert dk.score_global == 10

    def test_score_global_hors_borne_rejete(self):
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(score_global=11))

    def test_defaults_optionnels_none(self):
        """Champs optionnels absents → None par défaut."""
        dk = DecisionKernel(**_kernel())
        assert dk.score_global is None
        assert dk.niveau_urgence is None
        assert dk.secteur is None
        assert dk.modele_economique is None
        assert dk.source_data_hash is None
        assert dk.score_confiance is None
        assert dk.data_quality_score is None
        assert dk.data_quality_blocking is None
        assert dk.attribution is None

    def test_defaults_listes_vides(self):
        dk = DecisionKernel(**_kernel())
        assert dk.global_findings == []
        assert dk.global_recommendations == []

    def test_champ_extra_rejete(self):
        with pytest.raises(ValidationError):
            DecisionKernel(**_kernel(champ_inconnu="oops"))

    def test_with_attribution(self):
        am = AttributionMetrics(
            mode="conservative_v1",
            dimension_decisions_available=2,
            findings_total=3,
            findings_scoped=0,
            recommendations_total=2,
            recommendations_scoped=0,
        )
        dk = DecisionKernel(**_kernel(attribution=am))
        assert dk.attribution is not None
        assert dk.attribution.mode == "conservative_v1"

    def test_with_global_findings_and_recommendations(self):
        f = Finding(**_finding())
        r = Recommendation(**_rec())
        dk = DecisionKernel(**_kernel(
            global_findings=[f],
            global_recommendations=[r],
        ))
        assert len(dk.global_findings) == 1
        assert len(dk.global_recommendations) == 1


# ── 10. Conformité — absence de logique dérivée ───────────────────────────────

class TestDecisionConformite:
    """Vérifie que Decision ne contient aucune logique métier dérivée.

    Le modèle représente et valide — il ne calcule pas.
    La polarity appartient à decision_rules.derive_polarity() (KERNEL-INV-010).
    """

    def test_polarity_non_derivee_du_score(self):
        """Le modèle accepte n'importe quelle polarity valide pour un score donné,
        même si elle est sémantiquement incohérente avec le score.
        La vérification sémantique appartient à l'extracteur."""
        # score=9 + polarity="CRITIQUE" : incohérent mais structurellement valide
        d = Decision(**_decision_available(score=9, polarity="CRITIQUE"))
        assert d.polarity == "CRITIQUE"
        assert d.score == 9

    def test_aucun_attribut_calcule(self):
        """Decision ne doit pas posséder d'attribut calculé non déclaré dans la spec."""
        d = Decision(**_decision_available())
        spec_fields = {
            "local_id", "scope", "status", "score",
            "polarity", "interpretation_text", "findings", "recommendations",
        }
        model_fields = set(d.model_fields.keys())
        assert model_fields == spec_fields, (
            f"Écart entre spec et modèle.\n"
            f"  Extra dans le modèle  : {model_fields - spec_fields}\n"
            f"  Manquant dans le modèle : {spec_fields - model_fields}"
        )


class TestDecisionKernelConformite:
    """Vérifie que DecisionKernel ne contient aucune logique métier dérivée."""

    def test_aucun_attribut_calcule(self):
        """DecisionKernel ne doit pas posséder d'attribut calculé non déclaré dans la spec."""
        spec_fields = {
            # Bloc A
            "kernel_id", "kernel_version", "kernel_produced_at",
            "decision_fingerprint", "decision_fingerprint_version", "source_data_hash",
            # Bloc B
            "type_document", "secteur", "modele_economique",
            # Bloc C
            "decisions", "score_global", "niveau_urgence",
            # Bloc D
            "global_findings", "global_recommendations",
            # Bloc E
            "score_confiance", "data_quality_score", "data_quality_blocking", "attribution",
        }
        model_fields = set(DecisionKernel.model_fields.keys())
        assert model_fields == spec_fields, (
            f"Écart entre spec et modèle.\n"
            f"  Extra dans le modèle  : {model_fields - spec_fields}\n"
            f"  Manquant dans le modèle : {spec_fields - model_fields}"
        )
