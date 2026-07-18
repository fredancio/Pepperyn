"""
Decision Fingerprint — WP5A (FIN-001) + WP5C réconciliation (KERNEL-INV-013)

Calcule une empreinte décisionnelle (SHA-256, 128 bits, 32 hex chars). L'empreinte
est un signal d'identité décisionnelle, pas un test de stabilité. Elle permet de
détecter si deux analyses ont produit les mêmes conclusions structurelles.

Fonctions publiques
-------------------
compute_decision_fingerprint(analysis_result)
    WP5A — Calcule le fingerprint depuis un objet compatible AnalysisResult (duck typing).
    Conservée inchangée pour rétrocompatibilité. Algorithme de référence.

compute_decision_fingerprint_from_kernel(kernel)
    WP5C (KERNEL-INV-013) — Calcule le fingerprint depuis un DecisionKernel dk-1.
    Délègue à compute_decision_fingerprint() via un proxy : l'algorithme reste identique.
    Appelée par decision_kernel_extractor.py en Phase 9 (après canonicalisation).
    Retourne (fingerprint, version) ou (None, None).

Limites connues de v1
---------------------
- Binning à frontière dure : un score 3 (FAIBLE) et un score 4 (MOYEN) produisent
  des fingerprints différents, même si la tolérance ICD-001 (±1) les accepte comme
  équivalents. La Stability Suite (WP5B+) gère les tolérances sur les champs bruts.
- Normalisation lexicale sans résolution de synonymes : "cash flow" et "trésorerie"
  restent distincts dans v1.
- source_data_hash (calculé par analyze.py) identifie le fichier octet pour octet,
  pas les données financières canoniques (normalized_data_hash, hors périmètre WP5A).

Différences WP5A → WP5C (nouvelles analyses uniquement)
---------------------------------------------------------
1. urgence : WP5A lit ar.niveau_urgence (brut LLM, ex : "critique").
             WP5C lit kernel.niveau_urgence dérivé par derive_niveau_urgence()
             (ex : "Critique"). Les fingerprints diffèrent si la casse diffère.
             C'est une amélioration : le Kernel normalise l'urgence de façon
             déterministe, indépendamment du rendu textuel LLM.

2. top3 : WP5A lit ar.plan_action_haute ou ar.problemes_critiques (listes brutes LLM).
          WP5C lit kernel.global_recommendations[priority=HAUTE] ou
          kernel.global_findings[severity=CRITIQUE] (listes après déduplication Phase 4/6).
          Si la déduplication a fusionné des items, le top3 peut différer.

Usage WP5C (depuis l'extracteur)
---------------------------------
    from services.decision_fingerprint import (
        compute_decision_fingerprint_from_kernel,
        FINGERPRINT_VERSION,
    )
    fp, version = compute_decision_fingerprint_from_kernel(kernel)
    kernel.decision_fingerprint = fp
    kernel.decision_fingerprint_version = version

Règle d'or
----------
Le fingerprint est calculé une fois, dans l'extracteur (Phase 9), et stocké dans
le Kernel. Aucun export, aucune route de lecture, aucun autre service ne doit le
recalculer ou le modifier.

Notes de conception
-------------------
[NC-1] Pourquoi FINGERPRINT_VERSION reste "v1" après WP5C ?
    La version du fingerprint identifie l'algorithme de hash, pas la source des
    données. En WP5C, l'algorithme est strictement identique à WP5A : mêmes champs
    inclus (urgence, 4 scores binned, top3), même fonction de hash (SHA-256[:32]),
    même format de sérialisation JSON (sort_keys=True). Seule la provenance des
    valeurs évolue (Kernel → données dérivées, vs AnalysisResult → données brutes LLM).
    Incrémenter FINGERPRINT_VERSION à "v2" marquerait une rupture de comparabilité :
    deux fingerprints "v2" ne devraient jamais être comparés à des "v1". Or les
    fingerprints WP5C resteront comparables aux fingerprints WP5A pour les analyses
    où les deux sources produisent des valeurs identiques. La version "v1" est donc
    maintenue. Si l'algorithme lui-même change (nouveaux champs, nouveau binning,
    nouveau format), FINGERPRINT_VERSION devra être incrémenté.

[NC-2] Rôle du SimpleNamespace proxy dans compute_decision_fingerprint_from_kernel()
    Le proxy SimpleNamespace est une couche d'adaptation volontaire. Elle permet à
    compute_decision_fingerprint_from_kernel() de déléguer entièrement à l'algorithme
    WP5A (compute_decision_fingerprint()), garantissant l'identité bit-à-bit du hash
    pour des données équivalentes — sans dupliquer la logique de binning, de
    normalisation ou de hash. Cette indirection est intentionnelle : elle matérialise
    le contrat "même algorithme, source différente" de la réconciliation KERNEL-INV-013.
    Lors d'une future version majeure de l'algorithme (FINGERPRINT_VERSION "v2"+),
    cette couche d'adaptation pourra être supprimée : compute_decision_fingerprint_from_kernel()
    pourra alors lire directement le Kernel sans proxy, si le nouvel algorithme est
    conçu nativement pour opérer sur un DecisionKernel.
"""

import hashlib
import json
import re
from types import SimpleNamespace
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from services.decision_kernel import DecisionKernel

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


# ─────────────────────────────────────────────────────────────────────────────
# WP5C — Réconciliation KERNEL-INV-013
# ─────────────────────────────────────────────────────────────────────────────

def compute_decision_fingerprint_from_kernel(
    kernel: Optional["DecisionKernel"],
) -> Tuple[Optional[str], Optional[str]]:
    """Calcule le Decision Fingerprint v1 depuis un DecisionKernel dk-1.

    Réconciliation WP5C (KERNEL-INV-013) : le fingerprint dépend exclusivement
    du Kernel, jamais directement de l'AnalysisResult.

    Délègue à compute_decision_fingerprint() dont l'algorithme reste inchangé
    (WP5A, commit a35d16ce). Seule la source des données change : les champs
    sont extraits du Kernel et injectés via un proxy SimpleNamespace.

    Doit être appelée APRÈS la Phase 10 (canonicalisation) de l'extracteur,
    de sorte que global_recommendations et global_findings soient dans un ordre
    stable avant le hash.

    Args:
        kernel : DecisionKernel dk-1, ou None (CA-2 ou erreur d'extraction).

    Returns:
        (fingerprint, version) :
            - fingerprint : chaîne 32 hex chars (SHA-256[:32]) ou None.
            - version     : FINGERPRINT_VERSION ("v1") ou None.
            Les deux sont None ensemble (CA-4 du Kernel l'impose).

    Sources des données (vs WP5A)
    ------------------------------
        urgence       ← kernel.niveau_urgence    (vs ar.niveau_urgence)
        score_rent.   ← decisions[RENTABILITÉ].score (None si insufficient_data)
        score_risque  ← decisions[RISQUE].score
        score_struct. ← decisions[STRUCTURE].score
        score_liquid. ← decisions[LIQUIDITÉ].score
        top3 source   ← global_recommendations[priority=HAUTE].directive
                        (fallback : global_findings[severity=CRITIQUE].statement)

    Ref : KERNEL-INV-013, WP5C_IMPLEMENTATION_PLAN §3.9
    """
    if kernel is None:
        return None, None

    # ── Scores par scope (None si insufficient_data) ─────────────────────────
    scores_by_scope: dict = {d.scope: d.score for d in kernel.decisions}

    # ── Équivalent plan_action_haute : Recommendations HAUTE ──────────────────
    # global_recommendations est canonicalisé (Phase 10) → ordre stable.
    # Correspond à ar.plan_action_haute post-EDM, après déduplication.
    plan_action_haute = [
        r.directive
        for r in kernel.global_recommendations
        if r.priority == "HAUTE"
    ]

    # ── Équivalent problemes_critiques : Findings CRITIQUE (fallback) ─────────
    # Utilisé si plan_action_haute est vide — même logique que WP5A.
    # global_findings est canonicalisé (Phase 10) → ordre stable.
    problemes_critiques = [
        f.statement
        for f in kernel.global_findings
        if f.severity == "CRITIQUE"
    ]

    # ── Proxy compatible avec compute_decision_fingerprint() ──────────────────
    # Duck typing : compute_decision_fingerprint() n'impose aucun type strict.
    # Le proxy porte exactement les attributs lus par _has_significant_fields()
    # et compute_decision_fingerprint().
    proxy = SimpleNamespace(
        niveau_urgence=kernel.niveau_urgence,
        score_rentabilite=scores_by_scope.get("RENTABILITÉ"),
        score_risque=scores_by_scope.get("RISQUE"),
        score_structure=scores_by_scope.get("STRUCTURE"),
        score_liquidite=scores_by_scope.get("LIQUIDITÉ"),
        plan_action_haute=plan_action_haute,
        problemes_critiques=problemes_critiques,
    )

    fp = compute_decision_fingerprint(proxy)
    if fp is None:
        return None, None
    return fp, FINGERPRINT_VERSION
