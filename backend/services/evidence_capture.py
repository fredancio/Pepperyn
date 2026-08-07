"""
evidence_capture.py — T1C-A : Evidence capture (pur, sans I/O).

Périmètre strict de T1C-A (décidé par Fred, 2026-08-02) :
  - Capture UNIQUEMENT ce que le pipeline produit déjà aujourd'hui.
  - Aucune modification du prompt. Aucun nouveau champ demandé au LLM.
  - Le comportement utilisateur reste identique — ce module n'est lu par
    aucun chemin de production existant (ADR-001 §8 : strictement additif).

Réutilisation délibérée (Constitution, Article XII — simplicité, une seule
représentation faisant autorité) : la logique de désérialisation d'un
QuantifiedImpact et de parsing du montant legacy existe déjà, correcte,
dans executive_decision_model.py (_try_deserialize_qi, parse_amount_eur).
Ce module ne la réécrit pas — il la réutilise à l'identique.

One New Truth Rule (Fred, 2026-08-02) : l'Evidence Ledger devient la
source de vérité pour les faits financiers quantifiés. Aucun ancien objet
n'est enrichi pour porter cette même vérité. En particulier :
  - schemas.py / AnalysisResult / QuickWin ne sont PAS modifiés ici.
  - Ils restent des projections narratives, inchangées par ce module.

Ownership (ADR-001A) : la capture elle-même ne prend aucune décision de
rattachement (Engagement vs Entity, transitoire) — cette décision relève
de la couche de persistance (evidence_ledger_service.py, T1C-A étape
suivante), pas de la capture, qui reste pure et sans connaissance du
domaine d'ownership.

Ce module est délibérément pur : aucune I/O, aucun appel réseau, aucune
dépendance à Supabase, aucun import de routers/. Il prend en entrée des
dicts déjà produits en mémoire par le pipeline et retourne un dict pur
(pas d'instances dataclass) — condition nécessaire pour que
deanonymize_recursive() (routers/analyze.py) puisse traverser la
structure automatiquement une fois attachée à
result.__dict__["_evidence_capture"].

Point d'intégration prévu (étape suivante de T1C-A, non faite par ce
fichier) : services/llm_service.py, run_full_pipeline(), immédiatement
après `analysis_dict = _parse_v3_text(...)` et avant le `return` de la
fonction — seul endroit du pipeline où evidence_graph et analysis_dict
non filtré par Pydantic coexistent encore dans le même scope.
"""
from __future__ import annotations

from typing import Any, Optional

from models.financial_truth import QuantifiedImpact
from services.executive_decision_model import _try_deserialize_qi, parse_amount_eur


def capture_evidence(
    evidence_graph: Optional[dict[str, Any]],
    analysis_dict: dict[str, Any],
) -> dict[str, Any]:
    """
    Construit la capture Evidence à partir de ce que le pipeline produit déjà.

    N'invente rien : reprend telles quelles les données déjà calculées par
    le LLM aujourd'hui, et déjà correctement désérialisées ailleurs
    (executive_decision_model.py). Lecture seule : ne modifie ni
    evidence_graph ni analysis_dict.

    Chaque impact structuré est conservé même si sa désérialisation échoue
    (impact=None) — une capture incomplète reste une information d'audit
    utile (cf. T1B : "UNKNOWN ≠ 0", une absence ne doit jamais être
    silencieusement supprimée, seulement représentée comme absente).

    Args:
        evidence_graph: dict retourné par _run_evidence_graph_agent
                        (peut être {} ou None en cas d'échec — non-bloquant
                        par construction dans le pipeline existant).
        analysis_dict: dict retourné par _parse_v3_text (AVANT toute
                       coercition Pydantic — c'est la condition nécessaire
                       pour que quantified_impact soit encore présent,
                       cf. T1B section 2).

    Returns:
        {
          "facts": [...],               # Evidence Graph — tel quel
          "unavailable_data": [...],    # Evidence Graph — tel quel
          "sheets_verified": [...],     # Evidence Graph — tel quel
          "quantified_impacts": [
              {
                "origin": "destroyer" | "quick_win",
                "index": int,            # position dans la liste d'origine
                "impact": dict | None,   # QuantifiedImpact.to_dict(), ou None
              },
              ...
          ],
        }
    """
    evidence_graph = evidence_graph or {}
    analysis_dict = analysis_dict or {}

    facts = list(evidence_graph.get("facts") or [])
    unavailable_data = list(evidence_graph.get("unavailable_data") or [])
    sheets_verified = list(evidence_graph.get("sheets_verified") or [])

    quantified_impacts: list[dict[str, Any]] = []

    for idx, item in enumerate(analysis_dict.get("value_destroyers") or []):
        if not isinstance(item, dict):
            continue
        qi = _capture_one_impact(item, amount_field="impact_annuel")
        quantified_impacts.append({
            "origin": "destroyer",
            "index": idx,
            "impact": qi.to_dict() if qi is not None else None,
        })

    for idx, item in enumerate(analysis_dict.get("quick_wins") or []):
        if not isinstance(item, dict):
            continue
        qi = _capture_one_impact(item, amount_field="roi_estime")
        quantified_impacts.append({
            "origin": "quick_win",
            "index": idx,
            "impact": qi.to_dict() if qi is not None else None,
        })

    return {
        "facts": facts,
        "unavailable_data": unavailable_data,
        "sheets_verified": sheets_verified,
        "quantified_impacts": quantified_impacts,
    }


def _capture_one_impact(item: dict[str, Any], amount_field: str) -> Optional[QuantifiedImpact]:
    """
    Reproduit exactement la logique déjà en production dans
    executive_decision_model.py (_build_executive_decisions pour les
    quick wins, _build_value_destroyers pour les destroyers) : le montant
    legacy est parsé depuis le champ texte correspondant
    (roi_estime / impact_annuel) puis injecté dans le QuantifiedImpact
    structuré s'il en manque un — jamais l'inverse, jamais de fallback
    vers 0. Aucune règle nouvelle : réutilisation stricte de code existant.
    """
    amount = parse_amount_eur(item.get(amount_field))
    return _try_deserialize_qi(item.get("quantified_impact"), amount=amount)
