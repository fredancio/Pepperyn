"""
Decision Fingerprint — WP5A (FIN-001)

Calcule une empreinte décisionnelle (SHA-256, 128 bits, 32 hex chars) à partir des
champs clés d'un AnalysisResult. L'empreinte est un signal d'identité décisionnelle,
pas un test de stabilité. Elle permet de détecter si deux analyses ont produit les
mêmes conclusions structurelles.

Limites connues de v1
---------------------
- Binning à frontière dure : un score 3 (FAIBLE) et un score 4 (MOYEN) produisent
  des fingerprints différents, même si la tolérance ICD-001 (±1) les accepte comme
  équivalents. La Stability Suite (WP5B+) gère les tolérances sur les champs bruts.
- Normalisation lexicale sans résolution de synonymes : "cash flow" et "trésorerie"
  restent distincts dans v1.
- source_data_hash (calculé par analyze.py) identifie le fichier octet pour octet,
  pas les données financières canoniques (normalized_data_hash, hors périmètre WP5A).

Usage
-----
    from services.decision_fingerprint import compute_decision_fingerprint, FINGERPRINT_VERSION

    fp = compute_decision_fingerprint(analysis_result)
    if fp is not None:
        payload["decision_fingerprint"] = fp
        payload["decision_fingerprint_version"] = FINGERPRINT_VERSION

Règle d'or
----------
compute_decision_fingerprint() est le SEUL point de calcul autorisé.
Aucun export, aucune route de lecture, aucun autre service ne doit recalculer
ou modifier ce fingerprint. Il est calculé une fois à la création et jamais modifié.
"""

import hashlib
import json
import re
from typing import Optional

# ── Constante de version ──────────────────────────────────────────────────────
# Incrémenter si l'algorithme change (champs inclus, binning, normalisation…).
# Les fingerprints de versions différentes ne doivent jamais être comparés directement.
# L'index composite (version, fingerprint) impose cet invariant au niveau requête.
FINGERPRINT_VERSION = "v1"

# ── Seuils de binning ─────────────────────────────────────────────────────────
# Scores 0-10 groupés en 3 tranches pour absorber les variations mineures.
# Attention : une variation à la frontière (ex. 3→4) peut changer la tranche
# même si elle est dans la tolérance ICD-001 (±1). C'est documenté et attendu.
_BIN_FAIBLE_MAX = 3   # [0..3]  → FAIBLE
_BIN_MOYEN_MAX = 6    # [4..6]  → MOYEN
                      # [7..10] → ÉLEVÉ


def _bin_score(v: Optional[int]) -> str:
    """Convertit un score 0-10 en tranche qualitative pour le fingerprint.

    Args:
        v: Score entier 0-10, ou None si absent.

    Returns:
        "FAIBLE" (0-3), "MOYEN" (4-6), "ÉLEVÉ" (7-10), ou "INCONNU" si None.
    """
    if v is None:
        return "INCONNU"
    if v <= _BIN_FAIBLE_MAX:
        return "FAIBLE"
    if v <= _BIN_MOYEN_MAX:
        return "MOYEN"
    return "ÉLEVÉ"


def _normalize(s: str) -> str:
    """Normalise un texte pour le fingerprint : lowercase + ponctuation → espace.

    L'objectif est que des variations superficielles (casse, ponctuation, espaces
    multiples) ne produisent pas de fingerprints différents.
    Limite v1 : les synonymes ne sont pas résolus.

    Args:
        s: Texte brut issu de l'AnalysisResult.

    Returns:
        Texte normalisé, ou chaîne vide si l'entrée est vide.
    """
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)   # ponctuation → espace
    s = re.sub(r"\s+", " ", s).strip()  # espaces multiples → espace simple
    return s


def _has_significant_fields(ar) -> bool:
    """Détermine si l'AnalysisResult contient au moins un champ décisionnel significatif.

    Une analyse sans champ décisionnel (ex. bloquée par le quality gate, ou
    résultat vide) ne doit pas recevoir de fingerprint officiel.

    Args:
        ar: AnalysisResult (ou tout objet avec les attributs attendus).

    Returns:
        True si au moins un champ décisionnel est présent, False sinon.
    """
    if ar.niveau_urgence:
        return True
    scores = [ar.score_rentabilite, ar.score_risque, ar.score_structure, ar.score_liquidite]
    if any(s is not None for s in scores):
        return True
    if getattr(ar, "plan_action_haute", None):
        return True
    if getattr(ar, "problemes_critiques", None):
        return True
    return False


def compute_decision_fingerprint(analysis_result) -> Optional[str]:
    """Calcule le Decision Fingerprint v1 d'un AnalysisResult.

    Algorithme v1
    -------------
    inputs = {
        "v":       FINGERPRINT_VERSION,
        "urgence": niveau_urgence or "INCONNU",
        "scores": {
            "rentabilite": _bin_score(score_rentabilite),
            "risque":      _bin_score(score_risque),
            "structure":   _bin_score(score_structure),
            "liquidite":   _bin_score(score_liquidite),
        },
        "top3": top3_sorted,  # ALL problèmes normalisés + triés, puis [:3]
    }
    fingerprint = SHA-256(json.dumps(inputs, sort_keys=True))[:32]

    Neutralité à l'ordre : TOUTE la liste source est normalisée et triée
    alphabétiquement avant que les 3 premiers éléments soient sélectionnés.
    Une liste [A, B, C, D] et [D, C, B, A] produisent le même fingerprint.

    Source des problèmes : plan_action_haute en priorité, sinon problemes_critiques.

    Args:
        analysis_result: Instance d'AnalysisResult (ou objet compatible).

    Returns:
        Chaîne de 32 caractères hexadécimaux (128 bits), ou None si l'analyse
        ne contient pas de champ décisionnel significatif.
    """
    if not _has_significant_fields(analysis_result):
        return None

    # Source des problèmes : plan_action_haute en priorité, sinon problemes_critiques
    source = (
        getattr(analysis_result, "plan_action_haute", None)
        or getattr(analysis_result, "problemes_critiques", None)
        or []
    )

    # Normaliser TOUTE la liste, filtrer les vides, trier globalement, prendre top3.
    # L'ordre de la liste source ne doit jamais influencer le fingerprint.
    normalized_all = sorted(filter(None, (_normalize(p) for p in source)))
    top3 = normalized_all[:3]

    inputs = {
        "v": FINGERPRINT_VERSION,
        "urgence": analysis_result.niveau_urgence or "INCONNU",
        "scores": {
            "rentabilite": _bin_score(analysis_result.score_rentabilite),
            "risque": _bin_score(analysis_result.score_risque),
            "structure": _bin_score(analysis_result.score_structure),
            "liquidite": _bin_score(analysis_result.score_liquidite),
        },
        "top3": top3,
    }

    payload = json.dumps(inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
