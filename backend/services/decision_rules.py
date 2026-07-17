"""
decision_rules.py — WP5C, Commit 1
===================================

Règles Python versionnées pour la dérivation des jugements canoniques du Decision Kernel.
Ce module est le moteur déterministe de Pepperyn : pour un ensemble d'inputs donnés,
il produit toujours le même output, indépendamment de tout appel LLM ou de tout état
externe.

Version actuelle : DECISION_RULES_VERSION = "v1"

Règles implémentées (v1)
------------------------
derive_polarity(scope, score) → CRITIQUE | ÉLEVÉ | MODÉRÉ | POSITIF
    Cas particulier RISQUE : le score est inversé (10 - score_risque) avant application
    des seuils. Un score_risque=7 exprime un risque élevé (mauvais signal) → CRITIQUE.
    Décision fondatrice : DECISION-WP5C-9 · Invariant : KERNEL-INV-010.

derive_score_global(scores) → int | None
    Moyenne arrondie des scores disponibles, avec inversion du score RISQUE.
    Identique à la règle existante dans _parse_v3_text (llm_service.py).
    Décision fondatrice : DECISION-WP5C-1 · Invariant : KERNEL-INV-008.

derive_niveau_urgence(score_global) → str | None
    Seuils : ≤3 → Critique, ≤5 → Élevé, ≤7 → Modéré, >7 → Maîtrisé.
    Décision fondatrice : DECISION-WP5C-1 · Invariant : KERNEL-INV-008.

Extension prévue
----------------
Ce module accueillera les futures règles déterministes (severity, health_status, …)
au fil des versions dk-2+, selon la Règle E-6 (Structure First) de SPEC-DK-001 Rev 3.1.
Chaque nouvelle règle porte sa propre docstring indiquant version, entrée, sortie et
invariant appliqué.

Usage
-----
    from services.decision_rules import (
        derive_polarity,
        derive_score_global,
        derive_niveau_urgence,
        DECISION_RULES_VERSION,
    )
"""

from __future__ import annotations

from typing import Dict, Optional

# ── Version ───────────────────────────────────────────────────────────────────
# Incrémenter si un seuil, une constante de label ou une règle de dérivation
# change. Les Kernels produits sous deux versions de règles différentes ne sont
# pas directement comparables sur leurs champs dérivés (polarity, score_global).
DECISION_RULES_VERSION = "v1"

# ── Dimension RISQUE ──────────────────────────────────────────────────────────
# Seule dimension dont l'interprétation est inversée : un score_risque élevé
# signifie un risque intense (mauvais signal). Toutes les autres dimensions
# suivent la sémantique directe : score élevé = bonne santé.
# Source : KERNEL-INV-010, DECISION-WP5C-9.
_SCOPE_RISQUE: str = "RISQUE"

# ── Seuils de polarity (v1) ───────────────────────────────────────────────────
# Appliqués au score *effectif* (direct ou inversé selon la dimension).
# Frontières :  ≤ 3 → CRITIQUE
#               ≤ 5 → ÉLEVÉ
#               ≤ 7 → MODÉRÉ
#               > 7 → POSITIF
_POLARITY_CRITIQUE_MAX: int = 3
_POLARITY_ELEVE_MAX: int    = 5
_POLARITY_MODERE_MAX: int   = 7

# Valeurs canoniques — utiliser ces constantes dans les consommateurs pour
# éviter les chaînes magiques et faciliter la détection de régressions.
POLARITY_CRITIQUE: str = "CRITIQUE"
POLARITY_ELEVE: str    = "ÉLEVÉ"
POLARITY_MODERE: str   = "MODÉRÉ"
POLARITY_POSITIF: str  = "POSITIF"

# ── Seuils de niveau d'urgence (v1) ──────────────────────────────────────────
# Les frontières numériques sont identiques aux seuils de polarity, mais les
# labels sont différents (majuscule initiale, style titre — pas tout-majuscule).
# Seuils :  ≤ 3 → Critique
#           ≤ 5 → Élevé
#           ≤ 7 → Modéré
#           > 7 → Maîtrisé
_URGENCE_CRITIQUE_MAX: int = 3
_URGENCE_ELEVE_MAX: int    = 5
_URGENCE_MODERE_MAX: int   = 7

URGENCE_CRITIQUE: str = "Critique"
URGENCE_ELEVE: str    = "Élevé"
URGENCE_MODERE: str   = "Modéré"
URGENCE_MAITRISE: str = "Maîtrisé"


# ── Règle interne de seuils ───────────────────────────────────────────────────

def _apply_polarity_thresholds(effective_score: int) -> str:
    """Applique les seuils de polarity à un score effectif déjà normalisé.

    Entrée  : effective_score (int) — score [0-10], après inversion éventuelle pour RISQUE.
    Sortie  : "CRITIQUE" | "ÉLEVÉ" | "MODÉRÉ" | "POSITIF"
    Version : v1 (DECISION_RULES_VERSION)
    Invariant : KERNEL-INV-010 — fonction interne ; l'entrée publique est derive_polarity.
    """
    if effective_score <= _POLARITY_CRITIQUE_MAX:
        return POLARITY_CRITIQUE
    if effective_score <= _POLARITY_ELEVE_MAX:
        return POLARITY_ELEVE
    if effective_score <= _POLARITY_MODERE_MAX:
        return POLARITY_MODERE
    return POLARITY_POSITIF


# ── Polarity ──────────────────────────────────────────────────────────────────

def derive_polarity(scope: str, score: int) -> str:
    """Dérive la polarity canonique d'une Decision depuis son scope et son score brut.

    Entrée  : scope (str)  — dimension Kernel : "RENTABILITÉ" | "RISQUE" |
                              "STRUCTURE" | "LIQUIDITÉ".
              score (int)  — score LLM brut [0-10].
    Sortie  : "CRITIQUE" | "ÉLEVÉ" | "MODÉRÉ" | "POSITIF"
    Version : v1 (DECISION_RULES_VERSION)
    Invariant : KERNEL-INV-010 — Decision.polarity est dérivée EXCLUSIVEMENT par
                cette fonction. Aucun texte LLM (y compris interpretation_text) ne
                peut modifier ni contredire la valeur retournée.
    Décision : DECISION-WP5C-9.

    Cas particulier RISQUE
    ----------------------
    Un score_risque élevé exprime un risque intense — c'est un mauvais signal pour
    la santé de l'entreprise. La règle applique l'inversion (10 - score_risque) avant
    les seuils afin que la polarity résultante reflète la santé de l'entreprise sur
    cette dimension, et non l'intensité du risque.

    Table de correspondance RISQUE (v1) :
        score_risque  effective  polarity
             0-2          8-10   POSITIF   (risque très faible)
               3             7   MODÉRÉ    (risque modéré)
             4-6           4-6   ÉLEVÉ     (risque notable)  ← 10-score ∈ [4,6]
            7-10           0-3   CRITIQUE  (risque sévère)
    """
    if scope == _SCOPE_RISQUE:
        effective_score = 10 - score
    else:
        effective_score = score
    return _apply_polarity_thresholds(effective_score)


# ── Score global ──────────────────────────────────────────────────────────────

def derive_score_global(scores: Dict[str, Optional[int]]) -> Optional[int]:
    """Dérive le score global depuis les scores dimensionnels disponibles.

    Entrée  : scores (Dict[str, Optional[int]]) — mapping scope → score brut | None.
              Clés attendues : "RENTABILITÉ", "RISQUE", "STRUCTURE", "LIQUIDITÉ".
              Les dimensions absentes (valeur None) sont ignorées dans le calcul.
    Sortie  : score global arrondi [0-10], ou None si aucune dimension disponible.
    Version : v1 (DECISION_RULES_VERSION)
    Invariant : KERNEL-INV-008 — score_global est calculé par cette règle Python,
                jamais extrait du texte LLM. La valeur retournée a primauté absolue
                sur toute valeur présente dans AnalysisResult.score_global.
    Décision : DECISION-WP5C-1.

    Inversion RISQUE
    ----------------
    Le score RISQUE contribue au score global via (10 - score_risque), alignant
    sa sémantique avec les dimensions directes : un risque élevé dégrade le score
    global. Règle identique à celle de _parse_v3_text dans llm_service.py (ligne ~590).

    Arrondissement
    --------------
    Utilise round() de Python (arrondi au plus proche, "round half to even" sur
    les .5 exacts). Ce comportement est documenté et stable pour v1.
    """
    components: list[int] = []

    rentabilite: Optional[int] = scores.get("RENTABILITÉ")
    risque: Optional[int]      = scores.get("RISQUE")
    structure: Optional[int]   = scores.get("STRUCTURE")
    liquidite: Optional[int]   = scores.get("LIQUIDITÉ")

    if rentabilite is not None:
        components.append(rentabilite)
    if risque is not None:
        components.append(10 - risque)          # inversion RISQUE
    if structure is not None:
        components.append(structure)
    if liquidite is not None:
        components.append(liquidite)

    if not components:
        return None

    return round(sum(components) / len(components))


# ── Niveau d'urgence ──────────────────────────────────────────────────────────

def derive_niveau_urgence(score_global: Optional[int]) -> Optional[str]:
    """Dérive le niveau d'urgence depuis le score global.

    Entrée  : score_global (Optional[int]) — entier [0-10] ou None.
    Sortie  : "Critique" | "Élevé" | "Modéré" | "Maîtrisé", ou None si
              score_global est None (aucune Decision available dans le Kernel).
    Version : v1 (DECISION_RULES_VERSION)
    Invariant : KERNEL-INV-008 — niveau_urgence est dérivé de score_global, lui-même
                dérivé des scores dimensionnels. Aucune synthèse narrative LLM ne peut
                modifier ce résultat.
    Décision : DECISION-WP5C-1.

    Seuils (v1) :
        score ≤ 3  →  Critique
        score ≤ 5  →  Élevé
        score ≤ 7  →  Modéré
        score > 7  →  Maîtrisé
    """
    if score_global is None:
        return None
    if score_global <= _URGENCE_CRITIQUE_MAX:
        return URGENCE_CRITIQUE
    if score_global <= _URGENCE_ELEVE_MAX:
        return URGENCE_ELEVE
    if score_global <= _URGENCE_MODERE_MAX:
        return URGENCE_MODERE
    return URGENCE_MAITRISE
