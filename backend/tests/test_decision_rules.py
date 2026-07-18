"""
Tests des règles Python versionnées — WP5C, Commit 1
=====================================================

Couvre :
  1.  derive_polarity — dimensions directes (RENTABILITÉ, STRUCTURE, LIQUIDITÉ)
  2.  derive_polarity — seuils exacts (frontières CRITIQUE/ÉLEVÉ/MODÉRÉ/POSITIF)
  3.  derive_polarity — inversion RISQUE (invariant fondamental KERNEL-INV-010)
  4.  derive_polarity — table complète RISQUE (score 0 → 10)
  5.  derive_polarity — cohérence STRUCTURE et LIQUIDITÉ (identiques à RENTABILITÉ)
  6.  derive_score_global — 4 dimensions disponibles (avec inversion RISQUE)
  7.  derive_score_global — dimension manquante (None ignoré)
  8.  derive_score_global — toutes dimensions None → None
  9.  derive_score_global — dimension RISQUE seule (inversion vérifiée)
  10. derive_niveau_urgence — tous les paliers et cas None
  11. Constantes exportées — valeurs stables et version "v1"
  12. Déterminisme — même inputs → même output
"""

import pytest

from services.decision_rules import (
    DECISION_RULES_VERSION,
    POLARITY_CRITIQUE,
    POLARITY_ELEVE,
    POLARITY_MODERE,
    POLARITY_POSITIF,
    URGENCE_CRITIQUE,
    URGENCE_ELEVE,
    URGENCE_MAITRISE,
    URGENCE_MODERE,
    _apply_polarity_thresholds,
    derive_niveau_urgence,
    derive_polarity,
    derive_score_global,
)


# ── 1. derive_polarity — dimensions directes ──────────────────────────────────

class TestDerivePolarity:
    """Couvre les 4 paliers de polarity sur les dimensions à sémantique directe
    (score élevé = bonne santé) et l'inversion de la dimension RISQUE."""

    # ── Paliers nominaux (RENTABILITÉ comme proxy direct) ─────────────────────

    def test_direct_score_faible_critique(self):
        """score=2, RENTABILITÉ → CRITIQUE (score ≤ 3)."""
        assert derive_polarity("RENTABILITÉ", 2) == POLARITY_CRITIQUE

    def test_direct_score_moyen_eleve(self):
        """score=5, RENTABILITÉ → ÉLEVÉ (3 < score ≤ 5)."""
        assert derive_polarity("RENTABILITÉ", 5) == POLARITY_ELEVE

    def test_direct_score_modere(self):
        """score=7, RENTABILITÉ → MODÉRÉ (5 < score ≤ 7)."""
        assert derive_polarity("RENTABILITÉ", 7) == POLARITY_MODERE

    def test_direct_score_positif(self):
        """score=9, RENTABILITÉ → POSITIF (score > 7)."""
        assert derive_polarity("RENTABILITÉ", 9) == POLARITY_POSITIF

    # ── Frontières exactes (seuils ≤ 3, ≤ 5, ≤ 7) ────────────────────────────

    def test_direct_boundary_critique_max(self):
        """score=3 est la valeur maximale de CRITIQUE."""
        assert derive_polarity("RENTABILITÉ", 3) == POLARITY_CRITIQUE

    def test_direct_boundary_eleve_min(self):
        """score=4 est la valeur minimale de ÉLEVÉ (juste au-dessus de 3)."""
        assert derive_polarity("RENTABILITÉ", 4) == POLARITY_ELEVE

    def test_direct_boundary_eleve_max(self):
        """score=5 est la valeur maximale de ÉLEVÉ."""
        assert derive_polarity("RENTABILITÉ", 5) == POLARITY_ELEVE

    def test_direct_boundary_modere_min(self):
        """score=6 est la valeur minimale de MODÉRÉ (juste au-dessus de 5)."""
        assert derive_polarity("RENTABILITÉ", 6) == POLARITY_MODERE

    def test_direct_boundary_modere_max(self):
        """score=7 est la valeur maximale de MODÉRÉ."""
        assert derive_polarity("RENTABILITÉ", 7) == POLARITY_MODERE

    def test_direct_boundary_positif_min(self):
        """score=8 est la valeur minimale de POSITIF (juste au-dessus de 7)."""
        assert derive_polarity("RENTABILITÉ", 8) == POLARITY_POSITIF

    def test_direct_score_zero_critique(self):
        """score=0 → CRITIQUE (plancher de l'échelle)."""
        assert derive_polarity("RENTABILITÉ", 0) == POLARITY_CRITIQUE

    def test_direct_score_10_positif(self):
        """score=10 → POSITIF (plafond de l'échelle)."""
        assert derive_polarity("RENTABILITÉ", 10) == POLARITY_POSITIF

    # ── Inversion RISQUE — invariant KERNEL-INV-010 ───────────────────────────

    def test_risque_score_7_critique(self):
        """score_risque=7 → effective=10-7=3 → CRITIQUE.

        Cas fondateur de l'inversion : un risque élevé (7/10) est une mauvaise
        nouvelle pour l'entreprise → polarity CRITIQUE.
        Invariant : KERNEL-INV-010, DECISION-WP5C-9.
        """
        assert derive_polarity("RISQUE", 7) == POLARITY_CRITIQUE

    def test_risque_score_2_positif(self):
        """score_risque=2 → effective=10-2=8 → POSITIF.

        Un risque très faible est un bon signal → polarity POSITIF.
        """
        assert derive_polarity("RISQUE", 2) == POLARITY_POSITIF

    def test_risque_score_5_eleve(self):
        """score_risque=5 → effective=10-5=5 → ÉLEVÉ.

        Note plan WP5C : le plan mentionnait "MODÉRÉ" dans le nom du test mais
        calculait correctement "(10-5=5 → ÉLEVÉ)". La valeur correcte est ÉLEVÉ.
        Écart documenté dans le rapport de Commit 1 — logique non modifiée.
        """
        assert derive_polarity("RISQUE", 5) == POLARITY_ELEVE

    def test_risque_score_3_modere(self):
        """score_risque=3 → effective=10-3=7 → MODÉRÉ."""
        assert derive_polarity("RISQUE", 3) == POLARITY_MODERE

    def test_risque_score_4_modere(self):
        """score_risque=4 → effective=10-4=6 → MODÉRÉ (5 < 6 ≤ 7)."""
        assert derive_polarity("RISQUE", 4) == POLARITY_MODERE

    def test_risque_score_6_eleve(self):
        """score_risque=6 → effective=10-6=4 → ÉLEVÉ (3 < 4 ≤ 5)."""
        assert derive_polarity("RISQUE", 6) == POLARITY_ELEVE

    def test_risque_score_8_critique(self):
        """score_risque=8 → effective=10-8=2 → CRITIQUE (≤ 3)."""
        assert derive_polarity("RISQUE", 8) == POLARITY_CRITIQUE

    def test_risque_score_0_positif(self):
        """score_risque=0 → effective=10-0=10 → POSITIF (risque nul)."""
        assert derive_polarity("RISQUE", 0) == POLARITY_POSITIF

    def test_risque_score_10_critique(self):
        """score_risque=10 → effective=10-10=0 → CRITIQUE (risque maximal)."""
        assert derive_polarity("RISQUE", 10) == POLARITY_CRITIQUE

    # ── STRUCTURE et LIQUIDITÉ — sémantique identique à RENTABILITÉ ───────────

    def test_structure_direct_seuils(self):
        """STRUCTURE utilise la sémantique directe (pas d'inversion)."""
        assert derive_polarity("STRUCTURE", 6) == POLARITY_MODERE
        assert derive_polarity("STRUCTURE", 3) == POLARITY_CRITIQUE
        assert derive_polarity("STRUCTURE", 8) == POLARITY_POSITIF

    def test_liquidite_direct_seuils(self):
        """LIQUIDITÉ utilise la sémantique directe (pas d'inversion)."""
        assert derive_polarity("LIQUIDITÉ", 0) == POLARITY_CRITIQUE
        assert derive_polarity("LIQUIDITÉ", 4) == POLARITY_ELEVE
        assert derive_polarity("LIQUIDITÉ", 10) == POLARITY_POSITIF


# ── 2. derive_score_global ────────────────────────────────────────────────────

class TestDeriveScoreGlobal:
    """Couvre le calcul du score global avec inversion RISQUE et gestion des None."""

    def test_4_dimensions_disponibles(self):
        """4 scores disponibles — inversion RISQUE incluse.

        {RENTABILITÉ:3, RISQUE:7, STRUCTURE:6, LIQUIDITÉ:4}
        → components = [3, 10-7, 6, 4] = [3, 3, 6, 4]
        → sum=16, count=4, moyenne=4.0 → 4
        """
        scores = {
            "RENTABILITÉ": 3,
            "RISQUE": 7,
            "STRUCTURE": 6,
            "LIQUIDITÉ": 4,
        }
        assert derive_score_global(scores) == 4

    def test_dimension_manquante_ignoree(self):
        """Une dimension None est ignorée dans le calcul.

        {RENTABILITÉ:3, RISQUE:None, STRUCTURE:6, LIQUIDITÉ:4}
        → components = [3, 6, 4] (RISQUE ignoré)
        → sum=13, count=3, round(13/3) = round(4.33) = 4
        """
        scores = {
            "RENTABILITÉ": 3,
            "RISQUE": None,
            "STRUCTURE": 6,
            "LIQUIDITÉ": 4,
        }
        assert derive_score_global(scores) == 4

    def test_toutes_dimensions_none(self):
        """Aucune dimension disponible → None (Kernel en état insufficient_data complet)."""
        scores = {
            "RENTABILITÉ": None,
            "RISQUE": None,
            "STRUCTURE": None,
            "LIQUIDITÉ": None,
        }
        assert derive_score_global(scores) is None

    def test_dict_vide(self):
        """Dict vide → None."""
        assert derive_score_global({}) is None

    def test_risque_seul_inversion(self):
        """Seul RISQUE disponible — l'inversion est appliquée.

        {RISQUE:7} → components = [10-7] = [3] → score_global=3
        """
        scores = {"RISQUE": 7}
        assert derive_score_global(scores) == 3

    def test_risque_seul_inversion_faible(self):
        """RISQUE=2 → 10-2=8 → score_global=8 (risque faible = bon score global)."""
        scores = {"RISQUE": 2}
        assert derive_score_global(scores) == 8

    def test_rentabilite_seule(self):
        """Seule RENTABILITÉ disponible — pas d'inversion."""
        scores = {"RENTABILITÉ": 6}
        assert derive_score_global(scores) == 6

    def test_deux_dimensions(self):
        """{RENTABILITÉ:4, LIQUIDITÉ:6} → (4+6)/2 = 5."""
        scores = {"RENTABILITÉ": 4, "LIQUIDITÉ": 6}
        assert derive_score_global(scores) == 5

    def test_score_global_coherence_avec_llm_service(self):
        """Vérifie la cohérence avec la règle existante de _parse_v3_text.

        La règle dans llm_service.py applique la même formule :
            score_components.append(10 - score_risque)
        Pour {R:5, Ri:3, S:7, L:6} :
        → [5, 10-3, 7, 6] = [5, 7, 7, 6] → sum=25, /4=6.25 → round=6
        """
        scores = {
            "RENTABILITÉ": 5,
            "RISQUE": 3,
            "STRUCTURE": 7,
            "LIQUIDITÉ": 6,
        }
        assert derive_score_global(scores) == 6

    def test_clefs_absentes_ignorees(self):
        """Les clefs absentes du dict sont traitées comme None (scores.get → None)."""
        scores = {"RENTABILITÉ": 8}   # RISQUE, STRUCTURE, LIQUIDITÉ absents
        assert derive_score_global(scores) == 8


# ── 3. derive_niveau_urgence ──────────────────────────────────────────────────

class TestDeriveNiveauUrgence:
    """Couvre les 4 paliers du niveau d'urgence et le cas None."""

    def test_none_retourne_none(self):
        """score_global=None → None (aucune Decision available)."""
        assert derive_niveau_urgence(None) is None

    def test_critique_boundary_max(self):
        """score_global=3 → Critique (frontière maximale du palier)."""
        assert derive_niveau_urgence(3) == URGENCE_CRITIQUE

    def test_critique_zero(self):
        """score_global=0 → Critique."""
        assert derive_niveau_urgence(0) == URGENCE_CRITIQUE

    def test_eleve_boundary_min(self):
        """score_global=4 → Élevé (premier score au-dessus de 3)."""
        assert derive_niveau_urgence(4) == URGENCE_ELEVE

    def test_eleve_boundary_max(self):
        """score_global=5 → Élevé (frontière maximale du palier)."""
        assert derive_niveau_urgence(5) == URGENCE_ELEVE

    def test_modere_boundary_min(self):
        """score_global=6 → Modéré (premier score au-dessus de 5)."""
        assert derive_niveau_urgence(6) == URGENCE_MODERE

    def test_modere_boundary_max(self):
        """score_global=7 → Modéré (frontière maximale du palier)."""
        assert derive_niveau_urgence(7) == URGENCE_MODERE

    def test_maitrise_boundary_min(self):
        """score_global=8 → Maîtrisé (premier score au-dessus de 7)."""
        assert derive_niveau_urgence(8) == URGENCE_MAITRISE

    def test_maitrise_max(self):
        """score_global=10 → Maîtrisé (plafond de l'échelle)."""
        assert derive_niveau_urgence(10) == URGENCE_MAITRISE


# ── 4. Constantes exportées ───────────────────────────────────────────────────

class TestConstantes:
    """Vérifie la stabilité des constantes exportées — toute modification ici
    est un signal qu'un champ Kernel persisté est potentiellement rompu."""

    def test_version(self):
        """DECISION_RULES_VERSION doit être 'v1' pour WP5C."""
        assert DECISION_RULES_VERSION == "v1"

    def test_polarity_values(self):
        """Les 4 valeurs canoniques de polarity sont stables."""
        assert POLARITY_CRITIQUE == "CRITIQUE"
        assert POLARITY_ELEVE    == "ÉLEVÉ"
        assert POLARITY_MODERE   == "MODÉRÉ"
        assert POLARITY_POSITIF  == "POSITIF"

    def test_urgence_values(self):
        """Les 4 valeurs canoniques de niveau d'urgence sont stables."""
        assert URGENCE_CRITIQUE == "Critique"
        assert URGENCE_ELEVE    == "Élevé"
        assert URGENCE_MODERE   == "Modéré"
        assert URGENCE_MAITRISE == "Maîtrisé"

    def test_polarity_not_same_as_urgence(self):
        """Polarity et urgence ont des casses différentes — pas d'aliasing involontaire."""
        assert POLARITY_CRITIQUE != URGENCE_CRITIQUE  # "CRITIQUE" ≠ "Critique"


# ── 5. Déterminisme ───────────────────────────────────────────────────────────

class TestDeterminisme:
    """Pour tout input, les fonctions retournent toujours le même output.
    Propriété fondamentale du moteur déterministe (KERNEL-INV-012 / général)."""

    def test_derive_polarity_deterministe(self):
        """Trois appels successifs produisent le même résultat."""
        r1 = derive_polarity("RISQUE", 7)
        r2 = derive_polarity("RISQUE", 7)
        r3 = derive_polarity("RISQUE", 7)
        assert r1 == r2 == r3 == POLARITY_CRITIQUE

    def test_derive_score_global_deterministe(self):
        """Même dict → même score global à chaque appel."""
        scores = {"RENTABILITÉ": 3, "RISQUE": 7, "STRUCTURE": 6, "LIQUIDITÉ": 4}
        assert derive_score_global(scores) == derive_score_global(scores) == 4

    def test_derive_niveau_urgence_deterministe(self):
        """Même score_global → même urgence."""
        assert derive_niveau_urgence(5) == derive_niveau_urgence(5) == URGENCE_ELEVE

    def test_pipeline_complet_deterministe(self):
        """Enchaînement derive_score_global → derive_niveau_urgence est déterministe."""
        scores = {"RENTABILITÉ": 3, "RISQUE": 7, "STRUCTURE": 6, "LIQUIDITÉ": 4}
        sg1 = derive_score_global(scores)
        sg2 = derive_score_global(scores)
        assert sg1 == sg2
        assert derive_niveau_urgence(sg1) == derive_niveau_urgence(sg2) == URGENCE_ELEVE
