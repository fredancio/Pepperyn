"""
test_golden_kernels.py — WP5C, Commit 7
=========================================

Golden Tests : preuve formelle de conformité du pipeline Decision Kernel dk-1.

Ces tests ne sont pas une augmentation de couverture ordinaire.
Ils constituent la démonstration officielle que WP5C satisfait ses invariants
architecturaux. Toute régression dans l'un de ces tests indique une modification
non autorisée du comportement déterministe du pipeline.

Référence permanente
--------------------
  fixtures/optilux_v3_analysis_result.json  — entrée canonique Optilux (PME critique)
  expected/optilux_v3_expected_kernel.json  — sortie de référence dk-1

Ces deux fichiers sont des références permanentes du projet.
Toute modification future devra soit :
  (a) reproduire exactement ces sorties, ou
  (b) documenter une décision d'architecture approuvée expliquant l'écart.

Organisation
------------
  TestGoldenDeterminism      (4)  — Même entrée → même sortie, bit pour bit
  TestGoldenCanonicalization (4)  — Ordre input sans effet sur l'output canonique
  TestGoldenDeduplication    (5)  — Doublons → même Kernel que l'entrée propre
  TestGoldenInvariants      (12)  — Chaque KERNEL-INV-* et critère CA documenté
  TestGoldenCompatibility    (3)  — Serialize → Deserialize → Reserialize sans perte
  TestGoldenFingerprint      (6)  — Sensibilité du Fingerprint aux champs décisionnels
  TestGoldenRegression       (4)  — Comparaison contre les fichiers de référence

Total : 38 tests

Référence spec : SPEC-DK-001 Rev 3.1 (DESIGN FROZEN), WP5C_IMPLEMENTATION_PLAN
"""

from __future__ import annotations

import copy
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

from models.schemas import AnalysisResult
from services.decision_fingerprint import (
    FINGERPRINT_VERSION,
    compute_decision_fingerprint_from_kernel,
)
from services.decision_kernel import DecisionKernel
from services.decision_kernel_extractor import (
    _canonicalize,
    extract_decision_kernel,
)
from services.decision_rules import derive_niveau_urgence, derive_score_global

# ── Constantes de test ────────────────────────────────────────────────────────

_GOLDEN_DIR = Path(__file__).parent
_FIXTURE_PATH = _GOLDEN_DIR / "fixtures" / "optilux_v3_analysis_result.json"
_EXPECTED_PATH = _GOLDEN_DIR / "expected" / "optilux_v3_expected_kernel.json"

# Horodatage fixe — correspondant à _produced_at_test dans le fixture JSON
_TEST_NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)

# Identifiant et hash stables pour tous les tests golden
_ANALYSE_ID = "optilux-golden-v3-001"
_SOURCE_HASH = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_ar() -> AnalysisResult:
    """Charger le fixture Optilux v3 comme AnalysisResult valide."""
    with open(_FIXTURE_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # Retirer les champs méta de test
    for key in ["_comment", "_version", "_produced_at_test",
                "_analyse_id_test", "_source_data_hash_test"]:
        raw.pop(key, None)
    return AnalysisResult(**raw)


def _load_expected_kernel() -> dict:
    """Charger le kernel de référence sérialisé (dict JSON)."""
    with open(_EXPECTED_PATH, encoding="utf-8") as f:
        return json.load(f)


def _extract_golden(ar: Optional[AnalysisResult] = None) -> Optional[DecisionKernel]:
    """Extraire le Kernel depuis le fixture (ou un AR alternatif) avec timestamp fixe."""
    if ar is None:
        ar = _load_ar()
    return extract_decision_kernel(
        ar, _ANALYSE_ID,
        source_data_hash=_SOURCE_HASH,
        _produced_at=_TEST_NOW,
    )


def _ar(**kwargs) -> AnalysisResult:
    """Construire un AnalysisResult minimal synthétique (scores par défaut)."""
    defaults = dict(
        score_rentabilite=5,
        score_risque=5,
        score_structure=5,
        score_liquidite=5,
    )
    defaults.update(kwargs)
    return AnalysisResult(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenDeterminism
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenDeterminism:
    """Même entrée + même _produced_at → même Kernel → même Fingerprint → même JSON.

    Propriété fondamentale : le pipeline est une fonction pure déterministe.
    KERNEL-INV-001 (scellement), KERNEL-INV-008 (règles Python), KERNEL-INV-012 (dédup).
    """

    def test_g01_same_ar_same_kernel_json(self):
        """Même AnalysisResult + même _produced_at → même model_dump(mode='json')."""
        r1 = _extract_golden()
        r2 = _extract_golden()
        assert r1 is not None and r2 is not None
        assert r1.model_dump(mode="json") == r2.model_dump(mode="json"), (
            "Le pipeline n'est pas déterministe : deux invocations identiques "
            "produisent des Kernels différents."
        )

    def test_g02_same_kernel_same_fingerprint(self):
        """Même Kernel → même Fingerprint sur 3 invocations successives."""
        kernel = _extract_golden()
        assert kernel is not None
        # Le fingerprint est déjà calculé (Phase 9) — il doit être stable
        fp1 = kernel.decision_fingerprint
        fp2, _ = compute_decision_fingerprint_from_kernel(kernel)
        fp3, _ = compute_decision_fingerprint_from_kernel(kernel)
        assert fp1 is not None
        assert fp1 == fp2 == fp3, (
            f"Fingerprint instable : fp1={fp1}, fp2={fp2}, fp3={fp3}"
        )

    def test_g03_same_kernel_same_json_serialization(self):
        """Sérialisation JSON identique sur 3 appels model_dump()."""
        kernel = _extract_golden()
        assert kernel is not None
        d1 = json.dumps(kernel.model_dump(mode="json"), sort_keys=True)
        d2 = json.dumps(kernel.model_dump(mode="json"), sort_keys=True)
        d3 = json.dumps(kernel.model_dump(mode="json"), sort_keys=True)
        assert d1 == d2 == d3

    def test_g04_full_pipeline_bit_for_bit_reproducible(self):
        """Pipeline complet : 5 extractions identiques → 5 JSONs identiques."""
        ar = _load_ar()
        results = [
            json.dumps(
                extract_decision_kernel(
                    ar, _ANALYSE_ID,
                    source_data_hash=_SOURCE_HASH,
                    _produced_at=_TEST_NOW,
                ).model_dump(mode="json"),
                sort_keys=True
            )
            for _ in range(5)
        ]
        assert len(set(results)) == 1, (
            "Instabilité détectée : les 5 extractions produisent des résultats différents."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenCanonicalization
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenCanonicalization:
    """L'ordre des éléments dans le Kernel est stable et prévisible.

    Invariant : quel que soit l'état interne intermédiaire, le Kernel livré
    respecte le tri canonique (local_id lexicographique) sur ses listes.
    Phase 10 — _canonicalize().
    """

    def test_g05_decisions_in_canonical_scope_order(self):
        """Décisions dans l'ordre canonique : d-01 RENTABILITÉ, d-02 RISQUE, etc."""
        kernel = _extract_golden()
        assert kernel is not None
        expected = [
            ("d-01", "RENTABILITÉ"),
            ("d-02", "RISQUE"),
            ("d-03", "STRUCTURE"),
            ("d-04", "LIQUIDITÉ"),
        ]
        actual = [(d.local_id, d.scope) for d in kernel.decisions]
        assert actual == expected, f"Ordre canonique des Decisions violé : {actual}"

    def test_g06_findings_in_sequential_local_id_order(self):
        """global_findings triés f-01, f-02, …, f-N dans l'ordre croissant."""
        kernel = _extract_golden()
        assert kernel is not None
        ids = [f.local_id for f in kernel.global_findings]
        assert ids == sorted(ids), f"Findings non triés : {ids}"
        assert ids[0] == "f-01", f"Premier Finding inattendu : {ids[0]}"

    def test_g07_recommendations_in_sequential_local_id_order(self):
        """global_recommendations triées r-01, r-02, …, r-N dans l'ordre croissant."""
        kernel = _extract_golden()
        assert kernel is not None
        ids = [r.local_id for r in kernel.global_recommendations]
        assert ids == sorted(ids), f"Recommendations non triées : {ids}"
        assert ids[0] == "r-01", f"Première Recommendation inattendue : {ids[0]}"

    def test_g08_canonicalize_is_idempotent_on_shuffled_kernel(self):
        """Canonicalisation idempotente : shuffler les listes puis canonicaliser
        produit le même Kernel que le Kernel original.

        Ce test valide le cas de la désérialisation depuis JSONB : un Kernel
        reconstruit depuis la base (listes potentiellement non ordonnées) retrouve
        son état canonique après _canonicalize().
        """
        kernel_ref = _extract_golden()
        assert kernel_ref is not None
        ref_dump = kernel_ref.model_dump(mode="json")

        # Reconstruire un Kernel depuis le JSON référence (simule désérialisation JSONB)
        kernel_deserialized = DecisionKernel.model_validate(
            copy.deepcopy(ref_dump)
        )
        # Mélanger les listes pour simuler un ordre non déterministe depuis JSONB
        random.seed(42)
        random.shuffle(kernel_deserialized.decisions)
        random.shuffle(kernel_deserialized.global_findings)
        random.shuffle(kernel_deserialized.global_recommendations)

        # Appliquer la canonicalisation
        _canonicalize(kernel_deserialized)

        shuffled_dump = kernel_deserialized.model_dump(mode="json")
        assert ref_dump == shuffled_dump, (
            "La canonicalisation ne restaure pas l'ordre canonique après désérialisation."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenDeduplication
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenDeduplication:
    """Les doublons de Findings et Recommendations produisent le même Kernel
    que l'entrée déjà dédupliquée.

    Invariant KERNEL-INV-012 : déduplication déterministe par normalisation,
    upgrade de severity/priority, fusion des source_refs.
    """

    def test_g09_fixture_near_duplicate_finding_merged(self):
        """Le fixture contient 'Marge nette négative…' dans problemes_critiques ET alertes.

        Après déduplication Phase 4, un seul Finding f-01 (CRITIQUE) doit subsister,
        avec source_refs contenant la provenance alertes/0.
        """
        kernel = _extract_golden()
        assert kernel is not None

        statements = [f.statement for f in kernel.global_findings]
        # Vérifier qu'un seul Finding contient "Marge nette négative"
        marge_findings = [s for s in statements if "Marge nette négative" in s]
        assert len(marge_findings) == 1, (
            f"Attendu 1 Finding 'Marge nette négative', obtenu {len(marge_findings)} : "
            f"{marge_findings}"
        )

    def test_g10_merged_finding_uses_higher_severity(self):
        """Le Finding fusionné (problemes_critiques=CRITIQUE, alertes=ÉLEVÉ)
        conserve CRITIQUE — jamais de downgrade (KERNEL-INV-012).
        """
        kernel = _extract_golden()
        assert kernel is not None
        merged = next(
            f for f in kernel.global_findings
            if "Marge nette négative" in f.statement
        )
        assert merged.severity == "CRITIQUE", (
            f"Severity degradée après fusion : attendu CRITIQUE, obtenu {merged.severity}"
        )

    def test_g11_merged_finding_preserves_source_refs(self):
        """Le Finding fusionné a des source_refs contenant la provenance du doublon.

        source_field=problemes_critiques (primaire) + source_refs=[alertes/0 (doublon)].
        """
        kernel = _extract_golden()
        assert kernel is not None
        merged = next(
            f for f in kernel.global_findings
            if "Marge nette négative" in f.statement
        )
        assert merged.source_field == "problemes_critiques", (
            f"source_field primaire inattendu : {merged.source_field}"
        )
        assert len(merged.source_refs) >= 1, (
            "source_refs vide : la provenance du doublon alertes/0 n'a pas été préservée."
        )
        source_fields_in_refs = [sr.source_field for sr in merged.source_refs]
        assert "alertes" in source_fields_in_refs, (
            f"La provenance 'alertes' absente des source_refs : {source_fields_in_refs}"
        )

    def test_g12_duplicate_input_same_as_clean_input(self):
        """Entrée avec doublon → même Kernel qu'une entrée sans doublon (KERNEL-INV-012).

        Ce test est la formalisation la plus forte de l'invariant de déduplication :
        la déduplication est transparente pour le consommateur du Kernel.
        """
        # Entrée avec doublon exact
        ar_with_dup = _ar(
            problemes_critiques=["Marge basse sur 3 ans", "Trésorerie critique"],
            alertes=["Marge basse sur 3 ans"],  # doublon de problemes_critiques[0]
        )
        # Entrée propre (équivalente, sans doublon)
        ar_clean = _ar(
            problemes_critiques=["Marge basse sur 3 ans", "Trésorerie critique"],
            alertes=[],
        )
        k_dup = extract_decision_kernel(ar_with_dup, _ANALYSE_ID, _produced_at=_TEST_NOW)
        k_clean = extract_decision_kernel(ar_clean, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert k_dup is not None and k_clean is not None

        # Comparer les statements des Findings (structure principale)
        stmts_dup = sorted(f.statement for f in k_dup.global_findings)
        stmts_clean = sorted(f.statement for f in k_clean.global_findings)
        assert stmts_dup == stmts_clean, (
            f"Déduplication instable : dup={stmts_dup}, clean={stmts_clean}"
        )

    def test_g13_near_duplicate_merged_case_and_punctuation(self):
        """Un doublon avec variation de casse + ponctuation est fusionné (KERNEL-INV-012).

        _normalize_text : lowercase + retrait ponctuation + collapse espaces.
        """
        ar_with_near_dup = _ar(
            alertes=["Marge NETTE dégradée!", "Marge nette dégradée"],
        )
        k = extract_decision_kernel(ar_with_near_dup, _ANALYSE_ID, _produced_at=_TEST_NOW)
        assert k is not None
        # Doit produire 1 seul Finding
        assert len(k.global_findings) == 1, (
            f"Attendu 1 Finding après déduplication near-dup, obtenu {len(k.global_findings)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenInvariants
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenInvariants:
    """Couverture formelle des invariants KERNEL-INV-* et critères CA.

    Chaque invariant documenté dans SPEC-DK-001 Rev 3.1 a au moins un test dédié.
    Ces tests constituent la matrice de conformité officielle de WP5C.
    """

    # ── KERNEL-INV-001 : Scellement immutable ─────────────────────────────────

    def test_g14_inv001_kernel_produced_at_matches_input(self):
        """KERNEL-INV-001 : kernel_produced_at == _produced_at injecté.

        Le scellement est posé une seule fois à la construction (Phase 11).
        Le timestamp ne varie pas après le scellement.
        """
        kernel = _extract_golden()
        assert kernel is not None
        assert kernel.kernel_produced_at == _TEST_NOW, (
            f"kernel_produced_at={kernel.kernel_produced_at} != _TEST_NOW={_TEST_NOW}"
        )

    # ── KERNEL-INV-008 : Dérivation Python exclusive ──────────────────────────

    def test_g15_inv008_score_global_overrides_llm(self):
        """KERNEL-INV-008 : score_global est dérivé par derive_score_global(),
        jamais extrait du champ ar.score_global (LLM).

        Le fixture LLM donne score_global=2, mais derive_score_global() calcule
        round((3 + 3 + 4 + 3) / 4) = round(3.25) = 3 en Python (arrondi pair).
        Le Kernel doit valoir 3, pas 2.
        """
        kernel = _extract_golden()
        assert kernel is not None
        # Valeur LLM dans le fixture : 2
        # Valeur dérivée par Python : 3
        assert kernel.score_global == 3, (
            f"score_global={kernel.score_global} : le Kernel a copié la valeur LLM (2) "
            "au lieu d'appliquer derive_score_global()."
        )
        # Vérification arithmétique indépendante
        scores_map = {d.scope: d.score for d in kernel.decisions}
        expected = derive_score_global(scores_map)
        assert kernel.score_global == expected

    def test_g16_inv008_niveau_urgence_derived_by_python_rule(self):
        """KERNEL-INV-008 : niveau_urgence dérivé par derive_niveau_urgence(),
        pas copié de ar.niveau_urgence (LLM).

        Le fixture LLM donne niveau_urgence="critique" (minuscule).
        derive_niveau_urgence(3) retourne "Critique" (majuscule initiale).
        """
        kernel = _extract_golden()
        assert kernel is not None
        # La valeur LLM (fixture) est "critique" (minuscule)
        # La valeur dérivée doit être "Critique" (format canonique)
        assert kernel.niveau_urgence == "Critique", (
            f"niveau_urgence={kernel.niveau_urgence!r} : valeur LLM copiée "
            "au lieu d'appliquer derive_niveau_urgence()."
        )
        # Vérification indépendante via la règle Python
        expected_urgence = derive_niveau_urgence(kernel.score_global)
        assert kernel.niveau_urgence == expected_urgence

    # ── KERNEL-INV-009 : dk-1 tout global ────────────────────────────────────

    def test_g17_inv009_all_findings_global_scope(self):
        """KERNEL-INV-009 : en dk-1, tous les Findings ont scope_status='global'."""
        kernel = _extract_golden()
        assert kernel is not None
        for f in kernel.global_findings:
            assert f.scope_status == "global", (
                f"Finding {f.local_id} a scope_status={f.scope_status!r} (attendu 'global')"
            )

    def test_g18_inv009_all_recommendations_global_scope(self):
        """KERNEL-INV-009 : en dk-1, toutes les Recommendations ont scope_status='global'."""
        kernel = _extract_golden()
        assert kernel is not None
        for r in kernel.global_recommendations:
            assert r.scope_status == "global", (
                f"Recommendation {r.local_id} a scope_status={r.scope_status!r} (attendu 'global')"
            )

    def test_g19_inv009_attribution_scoped_counts_zero(self):
        """KERNEL-INV-009 : findings_scoped=0 et recommendations_scoped=0 en dk-1."""
        kernel = _extract_golden()
        assert kernel is not None
        assert kernel.attribution is not None
        assert kernel.attribution.findings_scoped == 0, (
            f"findings_scoped={kernel.attribution.findings_scoped} (attendu 0 en dk-1)"
        )
        assert kernel.attribution.recommendations_scoped == 0, (
            f"recommendations_scoped={kernel.attribution.recommendations_scoped} (attendu 0 en dk-1)"
        )

    # ── KERNEL-INV-010 : Polarity par règle Python ────────────────────────────

    def test_g20_inv010_polarity_derived_by_python_not_llm(self):
        """KERNEL-INV-010 : Decision.polarity dérivée par derive_polarity(), jamais
        depuis interpretation_text ou toute autre source LLM.

        Test sur le fixture : RENTABILITÉ score=3 → CRITIQUE (≤3 seuil polarity).
        """
        kernel = _extract_golden()
        assert kernel is not None
        rent = next(d for d in kernel.decisions if d.scope == "RENTABILITÉ")
        assert rent.score == 3
        assert rent.polarity == "CRITIQUE", (
            f"RENTABILITÉ score=3 : polarity={rent.polarity} (attendu CRITIQUE)"
        )

    def test_g21_inv010_risque_polarity_inverted(self):
        """KERNEL-INV-010 : dimension RISQUE utilise 10 - score_risque.

        Fixture : score_risque=7 → effective=10-7=3 → CRITIQUE (≤3).
        Un score_risque élevé = risque sévère = mauvaise santé = CRITIQUE.
        """
        kernel = _extract_golden()
        assert kernel is not None
        risque = next(d for d in kernel.decisions if d.scope == "RISQUE")
        assert risque.score == 7
        assert risque.polarity == "CRITIQUE", (
            f"RISQUE score=7 (effective=3) : polarity={risque.polarity} (attendu CRITIQUE)"
        )
        # Vérification avec une valeur inverse : score_risque=2 → effective=8 → POSITIF
        k_low_risk = extract_decision_kernel(
            _ar(score_risque=2), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert k_low_risk is not None
        risque_low = next(d for d in k_low_risk.decisions if d.scope == "RISQUE")
        assert risque_low.polarity == "POSITIF", (
            f"RISQUE score=2 (effective=8) : polarity={risque_low.polarity} (attendu POSITIF)"
        )

    # ── KERNEL-INV-011 : Provenance complète ──────────────────────────────────

    def test_g22_inv011_all_findings_have_valid_provenance(self):
        """KERNEL-INV-011 : chaque Finding a source_field non vide et source_index ≥ 0."""
        kernel = _extract_golden()
        assert kernel is not None
        for f in kernel.global_findings:
            assert f.source_field, (
                f"Finding {f.local_id!r} : source_field vide — provenance manquante."
            )
            assert f.source_index >= 0, (
                f"Finding {f.local_id!r} : source_index={f.source_index} < 0."
            )

    def test_g23_inv011_all_recommendations_have_valid_provenance(self):
        """KERNEL-INV-011 : chaque Recommendation a source_field non vide et source_index ≥ 0."""
        kernel = _extract_golden()
        assert kernel is not None
        for r in kernel.global_recommendations:
            assert r.source_field, (
                f"Recommendation {r.local_id!r} : source_field vide."
            )
            assert r.source_index >= 0, (
                f"Recommendation {r.local_id!r} : source_index={r.source_index} < 0."
            )

    # ── KERNEL-INV-012 : Déduplication déterministe ───────────────────────────

    def test_g24_inv012_deduplication_deterministic_on_golden(self):
        """KERNEL-INV-012 : le nombre de Findings après déduplication est stable
        quelle que soit l'invocation.

        Le fixture a 5 Findings uniques + 1 near-duplicate fusionné = 6 Findings au total.
        Ce test vérifie la stabilité de ce compte.
        """
        k1 = _extract_golden()
        k2 = _extract_golden()
        assert k1 is not None and k2 is not None
        assert len(k1.global_findings) == len(k2.global_findings), (
            "Nombre de Findings instable entre deux extractions identiques."
        )
        assert len(k1.global_findings) == 6, (
            f"Attendu 6 Findings (5 uniques + 1 near-dup fusionné), "
            f"obtenu {len(k1.global_findings)}"
        )

    # ── KERNEL-INV-013 : Fingerprint depuis Kernel ────────────────────────────

    def test_g25_inv013_fingerprint_embedded_in_kernel(self):
        """KERNEL-INV-013 : le Fingerprint est embarqué dans le Kernel (Phase 9),
        jamais calculé depuis AnalysisResult directement.

        Test : le fingerprint du Kernel == celui de compute_decision_fingerprint_from_kernel.
        """
        kernel = _extract_golden()
        assert kernel is not None
        assert kernel.decision_fingerprint is not None, (
            "Fingerprint absent du Kernel — Phase 9 non exécutée."
        )
        # Recalcul depuis le Kernel → doit être identique
        fp_recalc, _ = compute_decision_fingerprint_from_kernel(kernel)
        assert kernel.decision_fingerprint == fp_recalc, (
            f"Fingerprint embarqué ({kernel.decision_fingerprint}) != "
            f"recalculé depuis Kernel ({fp_recalc})."
        )

    # ── CA-2 : Kernel NULL si toutes Decisions insufficient_data ─────────────

    def test_g39_ca2_all_insufficient_data_returns_none_kernel(self):
        """CA-2 : si toutes les Decisions sont insufficient_data,
        extract_decision_kernel() retourne None.
        Aucun Kernel et aucun Fingerprint ne sont produits.

        Ce test est le Golden dédié à CA-2 : le pipeline entier refuse de
        sceller un Kernel sans aucune dimension disponible. La règle est
        appliquée par _validate_kernel() lors de la Phase 12.

        Note : ce cas ne nécessite pas de fichier de référence JSON —
        la valeur de référence est None par définition.
        """
        ar_all_none = _ar(
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
        )
        kernel = extract_decision_kernel(
            ar_all_none, _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert kernel is None, (
            "CA-2 : toutes les Decisions sont insufficient_data mais "
            "extract_decision_kernel() a retourné un Kernel non-None. "
            "La Phase 12 (_validate_kernel) n'a pas appliqué CA-2."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenCompatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenCompatibility:
    """Un Kernel valide peut être sérialisé, désérialisé, resérialisé sans perte.

    Cette propriété est requise pour la persistance JSONB et la reconstruction
    depuis la base de données.
    """

    def test_g26_serialize_deserialize_reserialize_identity(self):
        """model_dump() → model_validate() → model_dump() == original."""
        kernel = _extract_golden()
        assert kernel is not None

        dump1 = kernel.model_dump(mode="json")
        kernel2 = DecisionKernel.model_validate(dump1)
        dump2 = kernel2.model_dump(mode="json")

        assert dump1 == dump2, (
            "Perte de données lors du cycle serialize→deserialize→serialize."
        )

    def test_g27_json_round_trip_no_loss(self):
        """JSON string → parse → JSON string == original (round-trip sans perte)."""
        kernel = _extract_golden()
        assert kernel is not None

        json_str1 = json.dumps(kernel.model_dump(mode="json"), sort_keys=True)
        kernel2 = DecisionKernel.model_validate(json.loads(json_str1))
        json_str2 = json.dumps(kernel2.model_dump(mode="json"), sort_keys=True)

        assert json_str1 == json_str2

    def test_g28_model_dump_json_mode_safe_for_jsonb(self):
        """model_dump(mode='json') ne contient que des types JSON natifs.

        JSONB Supabase exige des types Python de base : dict, list, str, int, float,
        bool, None. Pas de datetime, UUID, Decimal, etc.
        """
        kernel = _extract_golden()
        assert kernel is not None
        dumped = kernel.model_dump(mode="json")

        def _check_json_safe(obj, path="root"):
            assert isinstance(obj, (dict, list, str, int, float, bool, type(None))), (
                f"Type non JSON-safe {type(obj).__name__} à {path}"
            )
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _check_json_safe(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _check_json_safe(v, f"{path}[{i}]")

        _check_json_safe(dumped)


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenFingerprint
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenFingerprint:
    """Sensibilité du Decision Fingerprint aux champs décisionnels.

    Les tests vérifient que :
    - Les champs décisionnels (scores, urgence, top3) MODIFIENT le fingerprint.
    - Les champs non-décisionnels (type_document, produced_at, score_confiance)
      NE MODIFIENT PAS le fingerprint.
    """

    def test_g29_same_kernel_same_fingerprint(self):
        """Deux Kernels identiques → Fingerprints identiques."""
        k1 = _extract_golden()
        k2 = _extract_golden()
        assert k1 is not None and k2 is not None
        assert k1.decision_fingerprint == k2.decision_fingerprint

    def test_g30_available_decision_score_change_changes_fingerprint(self):
        """Modifier le score d'une Decision 'available' change le Fingerprint
        si et seulement si le changement franchit une frontière de tranche (binning).

        Test : score_rentabilite 3 (FAIBLE) → 7 (ÉLEVÉ) → FP change.
        """
        k_faible = extract_decision_kernel(
            _ar(score_rentabilite=3), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        k_eleve = extract_decision_kernel(
            _ar(score_rentabilite=7), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert k_faible is not None and k_eleve is not None
        assert k_faible.decision_fingerprint != k_eleve.decision_fingerprint, (
            "Le Fingerprint n'a pas changé malgré un changement de tranche de score."
        )

    def test_g31_urgence_change_changes_fingerprint(self):
        """Modifier niveau_urgence (via score_global) change le Fingerprint.

        score_global ≤3 → Critique, ≤5 → Élevé → FP différents.
        """
        # score=2 → score_global=2 → Critique
        k_crit = extract_decision_kernel(
            _ar(score_rentabilite=2, score_risque=8, score_structure=2, score_liquidite=2),
            _ANALYSE_ID, _produced_at=_TEST_NOW,
        )
        # score=5 → score_global=5 → Élevé
        k_elev = extract_decision_kernel(
            _ar(score_rentabilite=5, score_risque=5, score_structure=5, score_liquidite=5),
            _ANALYSE_ID, _produced_at=_TEST_NOW,
        )
        assert k_crit is not None and k_elev is not None
        assert k_crit.niveau_urgence != k_elev.niveau_urgence
        assert k_crit.decision_fingerprint != k_elev.decision_fingerprint

    def test_g32_type_document_change_no_fingerprint_change(self):
        """Modifier type_document (champ non décisionnel) ne change pas le Fingerprint.

        type_document n'entre pas dans le hash SHA-256 de compute_decision_fingerprint().
        """
        k_pl = extract_decision_kernel(
            _ar(type_document="P&L"), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        k_bilan = extract_decision_kernel(
            _ar(type_document="BILAN"), _ANALYSE_ID, _produced_at=_TEST_NOW
        )
        assert k_pl is not None and k_bilan is not None
        assert k_pl.decision_fingerprint == k_bilan.decision_fingerprint, (
            "type_document a modifié le Fingerprint — ce champ ne devrait pas y contribuer."
        )

    def test_g33_produced_at_change_no_fingerprint_change(self):
        """Modifier kernel_produced_at ne change pas le Fingerprint.

        Le timestamp de scellement est un champ méta, pas un champ décisionnel.
        """
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 7, 17, tzinfo=timezone.utc)
        k1 = extract_decision_kernel(_ar(), _ANALYSE_ID, _produced_at=t1)
        k2 = extract_decision_kernel(_ar(), _ANALYSE_ID, _produced_at=t2)
        assert k1 is not None and k2 is not None
        assert k1.kernel_produced_at != k2.kernel_produced_at
        assert k1.decision_fingerprint == k2.decision_fingerprint, (
            "kernel_produced_at a modifié le Fingerprint — ce champ ne doit pas y contribuer."
        )

    def test_g34_haute_recommendation_change_changes_fingerprint(self):
        """Modifier une directive de Recommendation HAUTE change le Fingerprint.

        Les directives HAUTE entrent dans le top3 du hash.
        """
        k1 = extract_decision_kernel(
            _ar(plan_action_haute=["Réduire les coûts fixes"]),
            _ANALYSE_ID, _produced_at=_TEST_NOW,
        )
        k2 = extract_decision_kernel(
            _ar(plan_action_haute=["Augmenter le chiffre d'affaires"]),
            _ANALYSE_ID, _produced_at=_TEST_NOW,
        )
        assert k1 is not None and k2 is not None
        assert k1.decision_fingerprint != k2.decision_fingerprint, (
            "Changer une directive HAUTE n'a pas modifié le Fingerprint."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestGoldenRegression
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenRegression:
    """Comparaison du pipeline contre les fichiers de référence permanents.

    Ces tests DOIVENT passer à chaque exécution future.
    Un échec indique soit :
    (a) une régression non intentionnelle → corriger le code, ou
    (b) une évolution architecturale documentée → mettre à jour les fichiers de référence.

    Le fichier expected/optilux_v3_expected_kernel.json est la source de vérité.
    """

    def test_g35_optilux_v3_decisions_match_expected(self):
        """Les 4 Decisions du Golden Kernel correspondent exactement aux attendus.

        Couverture : scope, status, score, polarity pour les 4 dimensions.
        """
        kernel = _extract_golden()
        expected = _load_expected_kernel()
        assert kernel is not None

        actual_decisions = [
            {
                "local_id": d.local_id,
                "scope": d.scope,
                "status": d.status,
                "score": d.score,
                "polarity": d.polarity,
            }
            for d in kernel.decisions
        ]
        expected_decisions = [
            {
                "local_id": d["local_id"],
                "scope": d["scope"],
                "status": d["status"],
                "score": d["score"],
                "polarity": d["polarity"],
            }
            for d in expected["decisions"]
        ]
        assert actual_decisions == expected_decisions, (
            "Les Decisions du Kernel ne correspondent pas à la référence.\n"
            f"Attendu : {expected_decisions}\n"
            f"Obtenu  : {actual_decisions}"
        )

    def test_g36_optilux_v3_findings_structure_matches_expected(self):
        """Les Findings du Golden Kernel correspondent à la référence.

        Couverture : nombre, statements, severities, source_fields.
        La déduplication du near-duplicate est incluse (f-01 CRITIQUE fusionné).
        """
        kernel = _extract_golden()
        expected = _load_expected_kernel()
        assert kernel is not None

        actual = [
            {
                "local_id": f.local_id,
                "statement": f.statement,
                "severity": f.severity,
                "source_field": f.source_field,
                "has_source_refs": len(f.source_refs) > 0,
            }
            for f in kernel.global_findings
        ]
        expected_f = [
            {
                "local_id": f["local_id"],
                "statement": f["statement"],
                "severity": f["severity"],
                "source_field": f["source_field"],
                "has_source_refs": len(f["source_refs"]) > 0,
            }
            for f in expected["global_findings"]
        ]
        assert actual == expected_f, (
            f"Structure des Findings différente de la référence.\n"
            f"Attendu {len(expected_f)} Findings, obtenu {len(actual)}."
        )

    def test_g37_optilux_v3_fingerprint_stable(self):
        """Le Fingerprint du Golden Kernel doit correspondre à la valeur de référence.

        Toute modification du Fingerprint de référence doit être une décision
        consciente documentée dans le commit qui l'introduit.
        """
        kernel = _extract_golden()
        expected = _load_expected_kernel()
        assert kernel is not None

        expected_fp = expected["decision_fingerprint"]
        assert kernel.decision_fingerprint == expected_fp, (
            f"RÉGRESSION FINGERPRINT :\n"
            f"  Attendu  : {expected_fp}\n"
            f"  Obtenu   : {kernel.decision_fingerprint}\n"
            "Une modification du pipeline ou de l'algorithme de fingerprint a changé "
            "la valeur de référence. Si ce changement est intentionnel, régénérer "
            "expected/optilux_v3_expected_kernel.json et documenter la décision."
        )

    def test_g38_optilux_v3_full_kernel_matches_expected(self):
        """Comparaison complète du Kernel contre la référence JSON.

        Tous les champs sont comparés sauf kernel_produced_at (timestamp volatile
        exclu pour permettre les comparaisons cross-session).
        kernel_id est inclus car fixé à _ANALYSE_ID dans les deux cas.
        """
        kernel = _extract_golden()
        expected = _load_expected_kernel()
        assert kernel is not None

        actual_dump = kernel.model_dump(mode="json")

        # Exclure kernel_produced_at de la comparaison (timestamp volatil)
        # Tous les autres champs sont déterministes et DOIVENT correspondre.
        _VOLATILE_FIELDS = {"kernel_produced_at"}

        def _strip(d: dict) -> dict:
            return {k: v for k, v in d.items() if k not in _VOLATILE_FIELDS}

        assert _strip(actual_dump) == _strip(expected), (
            "RÉGRESSION STRUCTURELLE : le Kernel produit diffère de la référence.\n"
            "Vérifier les champs qui ont changé et documenter la cause."
        )
