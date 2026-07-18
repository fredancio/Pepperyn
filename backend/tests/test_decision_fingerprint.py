"""
Tests du Decision Fingerprint — WP5A (FIN-001) + WP5C réconciliation (KERNEL-INV-013)

Couvre WP5A (compute_decision_fingerprint) :
  1. Déterminisme : même AnalysisResult → même fingerprint
  2. Normalisation texte : casse / ponctuation / espaces → fingerprint identique
  3. Ordre des problèmes neutre (4+ éléments) → fingerprint identique
  4. Même tranche de score → fingerprint identique
  5. Franchissement de tranche (3→4) → fingerprints différents
  6. Changement d'urgence → fingerprints différents
  7. Analyse vide → None
  8. Format : 32 hex chars, version "v1"
  9. Intégration insert_payload : présence et cohérence des champs

Couvre WP5C (compute_decision_fingerprint_from_kernel) :
  10. kernel=None → (None, None)
  11. Kernel valide → fingerprint 32 hex + version "v1"
  12. Déterminisme depuis Kernel : même Kernel → même fingerprint
  13. Correspondance WP5A/WP5C : mêmes données → même hash
  14. insufficient_data → score None → fingerprint reflète INCONNU pour la tranche
  15. Urgence kernel → fingerprint diffère si libellé diffère
  16. top3 depuis HAUTE recommendations du Kernel
  17. top3 fallback vers CRITIQUE findings si pas de HAUTE recs
  18. Kernel sans champ décisionnel → (None, None)
"""

import pytest
from datetime import datetime, timezone
from types import SimpleNamespace

from services.decision_fingerprint import (
    compute_decision_fingerprint,
    compute_decision_fingerprint_from_kernel,
    FINGERPRINT_VERSION,
    _bin_score,
    _normalize,
)
from services.decision_kernel import (
    Decision,
    DecisionKernel,
    Finding,
    Recommendation,
    AttributionMetrics,
    SourceRef,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ar(**kwargs):
    """Construit un AnalysisResult minimal pour les tests."""
    defaults = {
        "niveau_urgence": "critique",
        "score_rentabilite": 5,
        "score_risque": 7,
        "score_structure": 4,
        "score_liquidite": None,
        "plan_action_haute": [],
        "problemes_critiques": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── Tests unitaires de bas niveau ─────────────────────────────────────────────

class TestBinScore:
    def test_none_retourne_inconnu(self):
        assert _bin_score(None) == "INCONNU"

    def test_zero_est_faible(self):
        assert _bin_score(0) == "FAIBLE"

    def test_trois_est_faible(self):
        assert _bin_score(3) == "FAIBLE"

    def test_quatre_est_moyen(self):
        assert _bin_score(4) == "MOYEN"

    def test_six_est_moyen(self):
        assert _bin_score(6) == "MOYEN"

    def test_sept_est_eleve(self):
        assert _bin_score(7) == "ÉLEVÉ"

    def test_dix_est_eleve(self):
        assert _bin_score(10) == "ÉLEVÉ"


class TestNormalize:
    def test_casse(self):
        assert _normalize("Cash Flow") == "cash flow"

    def test_ponctuation_retiree(self):
        assert _normalize("cash-flow!") == "cash flow"

    def test_espaces_multiples(self):
        assert _normalize("cash  flow") == "cash flow"

    def test_chaine_vide(self):
        assert _normalize("") == ""

    def test_points_virgule(self):
        # "dette; ratio" → ponctuation → espace → collapse espaces → "dette ratio"
        assert _normalize("dette; ratio") == "dette ratio"


# ── Tests de l'empreinte ──────────────────────────────────────────────────────

class TestComputeDecisionFingerprint:

    def test_1_determinisme(self):
        """Même AnalysisResult → même fingerprint, quelle que soit l'invocation."""
        ar = _ar(problemes_critiques=["Trésorerie négative", "Marge insuffisante"])
        fp1 = compute_decision_fingerprint(ar)
        fp2 = compute_decision_fingerprint(ar)
        fp3 = compute_decision_fingerprint(ar)
        assert fp1 is not None
        assert fp1 == fp2 == fp3

    def test_2_normalisation_texte(self):
        """Casse, ponctuation et espaces ne doivent pas changer le fingerprint."""
        ar1 = _ar(problemes_critiques=["Cash Flow Négatif!", "MARGE INSUFFISANTE"])
        ar2 = _ar(problemes_critiques=["cash flow négatif",  "marge insuffisante"])
        assert compute_decision_fingerprint(ar1) == compute_decision_fingerprint(ar2)

    def test_3_ordre_problemes_neutre_4_elements(self):
        """
        Une liste de 4 problèmes dans un ordre différent doit produire le même fingerprint.
        Ce test vérifie que le tri porte sur TOUTE la liste avant la sélection top3,
        et non uniquement sur les 3 premiers éléments (correction #1 du plan révisé).
        """
        problemes = [
            "Endettement excessif",
            "Marge insuffisante",
            "Cash flow négatif",
            "Ratio de liquidité dégradé",
        ]
        ar_ordre_a = _ar(problemes_critiques=problemes)
        ar_ordre_b = _ar(problemes_critiques=list(reversed(problemes)))
        ar_ordre_c = _ar(problemes_critiques=[problemes[2], problemes[0], problemes[3], problemes[1]])
        fp_a = compute_decision_fingerprint(ar_ordre_a)
        fp_b = compute_decision_fingerprint(ar_ordre_b)
        fp_c = compute_decision_fingerprint(ar_ordre_c)
        assert fp_a is not None
        assert fp_a == fp_b == fp_c

    def test_4_meme_tranche_score(self):
        """Scores 4 et 6 sont tous deux MOYEN → fingerprint identique."""
        ar_score4 = _ar(score_rentabilite=4, score_risque=4, score_structure=4, score_liquidite=None)
        ar_score6 = _ar(score_rentabilite=6, score_risque=6, score_structure=6, score_liquidite=None)
        assert compute_decision_fingerprint(ar_score4) == compute_decision_fingerprint(ar_score6)

    def test_5_franchissement_tranche(self):
        """Score 3 (FAIBLE) vs score 4 (MOYEN) → fingerprints différents.

        C'est le comportement documenté : le fingerprint n'est pas le verdict ICD-001.
        Une variation ±1 à la frontière d'une tranche peut changer l'identité décisionnelle.
        La Stability Suite (WP5B+) gère la tolérance sur les champs bruts.
        """
        ar_faible = _ar(score_rentabilite=3)
        ar_moyen  = _ar(score_rentabilite=4)
        fp_faible = compute_decision_fingerprint(ar_faible)
        fp_moyen  = compute_decision_fingerprint(ar_moyen)
        assert fp_faible is not None
        assert fp_moyen  is not None
        assert fp_faible != fp_moyen

    def test_6_urgence_change(self):
        """Un changement d'urgence produit un fingerprint différent."""
        ar_critique = _ar(niveau_urgence="critique")
        ar_modere   = _ar(niveau_urgence="modéré")
        assert compute_decision_fingerprint(ar_critique) != compute_decision_fingerprint(ar_modere)

    def test_7_analyse_vide_retourne_none(self):
        """Une analyse sans champ décisionnel significatif → None.

        Cas : résultat d'une analyse bloquée par le quality gate, ou pipeline
        qui n'a pas pu extraire de champ clé.
        """
        ar_vide = _ar(
            niveau_urgence=None,
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
            plan_action_haute=[],
            problemes_critiques=[],
        )
        assert compute_decision_fingerprint(ar_vide) is None

    def test_8_format_et_version(self):
        """Le fingerprint est une chaîne de 32 caractères hexadécimaux. La version est 'v1'."""
        ar = _ar()
        fp = compute_decision_fingerprint(ar)
        assert fp is not None
        assert len(fp) == 32, f"Attendu 32 chars, obtenu {len(fp)}"
        assert all(c in "0123456789abcdef" for c in fp), "Pas une chaîne hexadécimale"
        assert FINGERPRINT_VERSION == "v1"

    def test_9_integration_insert_payload(self):
        """Simule la logique de _save_to_db : le fingerprint et la version sont
        correctement insérés dans insert_payload lorsque l'analyse est valide.
        """
        ar = _ar(
            niveau_urgence="critique",
            score_rentabilite=3,
            problemes_critiques=["Cash flow négatif", "Marge comprimée"],
        )
        payload: dict = {}

        fp = compute_decision_fingerprint(ar)
        if fp is not None:
            payload["decision_fingerprint"] = fp
            payload["decision_fingerprint_version"] = FINGERPRINT_VERSION

        assert "decision_fingerprint" in payload, "decision_fingerprint absent du payload"
        assert "decision_fingerprint_version" in payload, "decision_fingerprint_version absent du payload"
        assert payload["decision_fingerprint_version"] == "v1"
        assert len(payload["decision_fingerprint"]) == 32

    def test_9b_integration_vide_exclut_les_champs(self):
        """Une analyse vide ne doit injecter aucun champ fingerprint dans le payload."""
        ar_vide = _ar(
            niveau_urgence=None,
            score_rentabilite=None,
            score_risque=None,
            score_structure=None,
            score_liquidite=None,
            plan_action_haute=[],
            problemes_critiques=[],
        )
        payload: dict = {}

        fp = compute_decision_fingerprint(ar_vide)
        if fp is not None:
            payload["decision_fingerprint"] = fp
            payload["decision_fingerprint_version"] = FINGERPRINT_VERSION

        assert "decision_fingerprint" not in payload
        assert "decision_fingerprint_version" not in payload


# ── Helpers pour les tests WP5C ───────────────────────────────────────────────

_TEST_NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)
_ANALYSE_ID = "fp-test-kernel-001"

_SCOPES = ("RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ")
_LOCAL_IDS = ("d-01", "d-02", "d-03", "d-04")


def _decision(scope: str, score=5, polarity="MODÉRÉ"):
    local_id = _LOCAL_IDS[list(_SCOPES).index(scope)]
    return Decision(
        local_id=local_id,
        scope=scope,
        status="available",
        score=score,
        polarity=polarity,
    )


def _decision_id(scope: str):
    local_id = _LOCAL_IDS[list(_SCOPES).index(scope)]
    return Decision(local_id=local_id, scope=scope, status="insufficient_data")


def _finding(local_id: str, statement: str, severity=None, source_field="problemes_critiques", source_index=0):
    return Finding(
        local_id=local_id,
        statement=statement,
        source_field=source_field,
        source_index=source_index,
        severity=severity,
    )


def _recommendation(local_id: str, directive: str, priority="HAUTE", source_field="plan_action_haute", source_index=0):
    return Recommendation(
        local_id=local_id,
        directive=directive,
        priority=priority,
        horizon="IMMÉDIAT",
        source_field=source_field,
        source_index=source_index,
    )


def _kernel(
    decisions=None,
    global_findings=None,
    global_recommendations=None,
    niveau_urgence="Critique",
    score_global=3,
) -> DecisionKernel:
    if decisions is None:
        decisions = [
            _decision("RENTABILITÉ", score=3, polarity="CRITIQUE"),
            _decision("RISQUE", score=7, polarity="CRITIQUE"),
            _decision("STRUCTURE", score=4, polarity="ÉLEVÉ"),
            _decision("LIQUIDITÉ", score=3, polarity="CRITIQUE"),
        ]
    if global_findings is None:
        global_findings = []
    if global_recommendations is None:
        global_recommendations = []
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
        decisions=decisions,
        score_global=score_global,
        niveau_urgence=niveau_urgence,
        global_findings=global_findings,
        global_recommendations=global_recommendations,
        attribution=attribution,
    )


# ── Tests WP5C — compute_decision_fingerprint_from_kernel ─────────────────────

class TestComputeDecisionFingerprintFromKernel:
    """Tests de réconciliation KERNEL-INV-013.

    Vérifie que compute_decision_fingerprint_from_kernel() :
    - Renvoie (None, None) si le Kernel est None.
    - Produit un fingerprint 32 hex + version "v1" pour un Kernel valide.
    - Est déterministe.
    - Produit le même hash que WP5A pour des données concordantes.
    - Gère correctly insufficient_data (score=None → binning INCONNU).
    - Extrait le top3 depuis global_recommendations[HAUTE] ou global_findings[CRITIQUE].
    """

    def test_10_none_kernel_retourne_none_none(self):
        """kernel=None (CA-2) → (None, None)."""
        fp, version = compute_decision_fingerprint_from_kernel(None)
        assert fp is None
        assert version is None

    def test_11_kernel_valide_retourne_fingerprint_et_version(self):
        """Kernel valide → fingerprint non-None, version "v1"."""
        k = _kernel()
        fp, version = compute_decision_fingerprint_from_kernel(k)
        assert fp is not None
        assert version == "v1"
        assert version == FINGERPRINT_VERSION

    def test_11b_fingerprint_est_32_hex_chars(self):
        """Format : 32 caractères hexadécimaux."""
        k = _kernel()
        fp, _ = compute_decision_fingerprint_from_kernel(k)
        assert fp is not None
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)

    def test_12_determinisme_depuis_kernel(self):
        """Même Kernel → même fingerprint sur 3 invocations successives."""
        k = _kernel()
        results = [compute_decision_fingerprint_from_kernel(k)[0] for _ in range(3)]
        assert results[0] is not None
        assert results[0] == results[1] == results[2]

    def test_13_correspondance_wp5a_wp5c_donnees_concordantes(self):
        """Même données → même hash que WP5A quand urgence et scores concordent.

        Ce test vérifie l'invariant clé de la réconciliation : pour des données
        identiques (même urgence, mêmes scores, même top3), les deux fonctions
        produisent le même fingerprint. L'urgence doit être dans le format du
        Kernel (ex. "Critique"), pas le format LLM brut ("critique").
        """
        # Score bruts : rentabilite=3 (FAIBLE), risque=7 (→ risque_effectif=3, FAIBLE),
        # structure=4 (MOYEN), liquidite=3 (FAIBLE)
        # top3 source : plan_action_haute = ["Réduire les coûts"]
        k = _kernel(
            decisions=[
                _decision("RENTABILITÉ", score=3, polarity="CRITIQUE"),
                _decision("RISQUE", score=7, polarity="CRITIQUE"),
                _decision("STRUCTURE", score=4, polarity="ÉLEVÉ"),
                _decision("LIQUIDITÉ", score=3, polarity="CRITIQUE"),
            ],
            global_recommendations=[
                _recommendation("r-01", "Réduire les coûts", priority="HAUTE"),
            ],
            niveau_urgence="Critique",
            score_global=3,
        )
        # Proxy WP5A équivalent — urgence en format Kernel (titre), même top3
        ar_proxy = SimpleNamespace(
            niveau_urgence="Critique",       # ← format Kernel, pas "critique" LLM
            score_rentabilite=3,
            score_risque=7,
            score_structure=4,
            score_liquidite=3,
            plan_action_haute=["Réduire les coûts"],
            problemes_critiques=[],
        )
        fp_kernel, _ = compute_decision_fingerprint_from_kernel(k)
        fp_ar = compute_decision_fingerprint(ar_proxy)
        assert fp_kernel is not None
        assert fp_ar is not None
        assert fp_kernel == fp_ar, (
            "Le fingerprint WP5C doit être identique au fingerprint WP5A "
            "quand les données sont concordantes (même urgence, mêmes scores, même top3)."
        )

    def test_14_insufficient_data_contribue_score_none(self):
        """Une Decision insufficient_data contribue score=None → binning INCONNU."""
        # LIQUIDITÉ en insufficient_data
        k_with_id = _kernel(
            decisions=[
                _decision("RENTABILITÉ", score=5, polarity="MODÉRÉ"),
                _decision("RISQUE", score=5, polarity="MODÉRÉ"),
                _decision("STRUCTURE", score=5, polarity="MODÉRÉ"),
                _decision_id("LIQUIDITÉ"),               # insufficient_data
            ],
            niveau_urgence="Modéré",
            score_global=5,
        )
        # Proxy WP5A avec liquidite=None pour vérifier la même logique
        ar_proxy = SimpleNamespace(
            niveau_urgence="Modéré",
            score_rentabilite=5,
            score_risque=5,
            score_structure=5,
            score_liquidite=None,              # ← même que insufficient_data
            plan_action_haute=[],
            problemes_critiques=[],
        )
        fp_kernel, _ = compute_decision_fingerprint_from_kernel(k_with_id)
        fp_ar = compute_decision_fingerprint(ar_proxy)
        assert fp_kernel is not None
        assert fp_ar is not None
        assert fp_kernel == fp_ar

    def test_15_urgence_differente_produit_fingerprint_different(self):
        """Kernel avec urgence différente → fingerprints différents."""
        k_critique = _kernel(niveau_urgence="Critique", score_global=3)
        k_modere = _kernel(niveau_urgence="Modéré", score_global=5)
        fp_crit, _ = compute_decision_fingerprint_from_kernel(k_critique)
        fp_mod, _ = compute_decision_fingerprint_from_kernel(k_modere)
        assert fp_crit is not None
        assert fp_mod is not None
        assert fp_crit != fp_mod

    def test_16_top3_depuis_recommendations_haute(self):
        """Le top3 est extrait depuis global_recommendations[priority=HAUTE].

        Un Kernel sans findings CRITIQUE mais avec HAUTE recommendations doit
        produire un fingerprint non-None et utiliser les directives comme top3.
        """
        k = _kernel(
            global_recommendations=[
                _recommendation("r-01", "Réduire les charges fixes", priority="HAUTE"),
                _recommendation("r-02", "Optimiser le BFR", priority="HAUTE"),
                _recommendation("r-03", "Renégocier la dette", priority="SECONDAIRE"),
            ],
            global_findings=[],
        )
        fp, version = compute_decision_fingerprint_from_kernel(k)
        assert fp is not None
        # Vérifier la cohérence : même fingerprint qu'un proxy avec plan_action_haute
        ar_proxy = SimpleNamespace(
            niveau_urgence=k.niveau_urgence,
            score_rentabilite=3,
            score_risque=7,
            score_structure=4,
            score_liquidite=3,
            plan_action_haute=["Réduire les charges fixes", "Optimiser le BFR"],
            problemes_critiques=[],
        )
        fp_ar = compute_decision_fingerprint(ar_proxy)
        assert fp == fp_ar

    def test_17_top3_fallback_findings_critique(self):
        """Sans HAUTE recommendations, le top3 vient des CRITIQUE findings.

        Logique identique à WP5A : plan_action_haute or problemes_critiques.
        """
        k = _kernel(
            global_findings=[
                _finding("f-01", "Trésorerie négative", severity="CRITIQUE"),
                _finding("f-02", "Marge nette effondrée", severity="CRITIQUE"),
                _finding("f-03", "Endettement critique", severity="ÉLEVÉ"),  # ÉLEVÉ, pas CRITIQUE
            ],
            global_recommendations=[
                # Uniquement SECONDAIRE — pas de HAUTE
                _recommendation("r-01", "Renégocier", priority="SECONDAIRE",
                                source_field="plan_action_secondaire"),
            ],
        )
        fp_kernel, _ = compute_decision_fingerprint_from_kernel(k)
        # Proxy WP5A équivalent : plan_action_haute vide → fallback problemes_critiques
        ar_proxy = SimpleNamespace(
            niveau_urgence=k.niveau_urgence,
            score_rentabilite=3,
            score_risque=7,
            score_structure=4,
            score_liquidite=3,
            plan_action_haute=[],                # vide → fallback
            problemes_critiques=["Trésorerie négative", "Marge nette effondrée"],
        )
        fp_ar = compute_decision_fingerprint(ar_proxy)
        assert fp_kernel is not None
        assert fp_ar is not None
        assert fp_kernel == fp_ar

    def test_18_kernel_sans_champ_significatif_retourne_none(self):
        """Kernel sans urgence, sans scores, sans findings/recs → (None, None).

        Théorique en production (CA-2 renvoie None avant d'arriver ici),
        mais la fonction doit rester robuste si un tel objet est passé.
        """
        k_vide = _kernel(
            decisions=[
                _decision_id("RENTABILITÉ"),
                _decision_id("RISQUE"),
                _decision_id("STRUCTURE"),
                _decision_id("LIQUIDITÉ"),
            ],
            niveau_urgence=None,
            score_global=None,
            global_findings=[],
            global_recommendations=[],
        )
        fp, version = compute_decision_fingerprint_from_kernel(k_vide)
        assert fp is None
        assert version is None
