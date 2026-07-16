"""
Tests du Decision Fingerprint — WP5A (FIN-001)

Couvre :
  1. Déterminisme : même AnalysisResult → même fingerprint
  2. Normalisation texte : casse / ponctuation / espaces → fingerprint identique
  3. Ordre des problèmes neutre (4+ éléments) → fingerprint identique
  4. Même tranche de score → fingerprint identique
  5. Franchissement de tranche (3→4) → fingerprints différents
  6. Changement d'urgence → fingerprints différents
  7. Analyse vide → None
  8. Format : 32 hex chars, version "v1"
  9. Intégration insert_payload : présence et cohérence des champs
"""

import pytest
from types import SimpleNamespace

from services.decision_fingerprint import (
    compute_decision_fingerprint,
    FINGERPRINT_VERSION,
    _bin_score,
    _normalize,
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
