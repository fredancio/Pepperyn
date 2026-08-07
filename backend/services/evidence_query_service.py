"""
evidence_query_service.py — Evidence Ledger Consumer #1 : lecture canonique
seule de l'Evidence Ledger (evidence_ledger_entries, v18 / T1C-A / T1C-B).

Ce module est le PREMIER lecteur de production de l'Evidence Ledger
(ADR-001 §8 cesse d'être vrai à partir du moment où ce module est appelé
par un chemin réel — Review Briefing). Il est strictement en lecture,
ne modifie jamais evidence_ledger_entries, et n'appelle jamais de LLM.

RÈGLE FONDAMENTALE (mission Evidence Consumer #1) : ce module ne lit
JAMAIS analyses.analyse_json pour reconstruire une information que
l'Evidence Ledger prétend posséder canoniquement. Si le Ledger ne
supporte pas une information, ce module renvoie une absence honnête —
il ne comble jamais l'écart avec la vérité legacy.

RÈGLE fact_id (T1C-B adversarial review, confirmée par l'arbitrage T2A) :
fact_id n'est ni lu, ni exposé, ni utilisé pour comparer ou dédupliquer
des faits ici. Ce module résout uniquement par analyse_id — déjà UNIQUE
côté DB (migration v18) — qui ne nécessite aucune notion d'identité
métier inter-analyses.

RÈGLE tenant safety : evidence_ledger_entries n'a pas de policy RLS
(v18 — service-role uniquement, même convention que decision_arcs v16).
Toute requête ici filtre donc explicitement par company_id, jamais par
analyse_id seul, même si analyse_id est déjà unique globalement — défense
en profondeur, pas une garantie de commodité.

RÈGLE granularité de l'absence (nommé explicitement, jamais deviné) :
l'absence d'une ligne pour une analyse ne permet PAS de distinguer,
depuis cette seule table :
  - une analyse antérieure à T1C-A (le Ledger n'existait pas encore) ;
  - une capture Evidence Graph légitimement vide (aucun fait produit) ;
  - un échec d'écriture non-bloquant (services/evidence_ledger_service.py).
Ce module ne prétend jamais connaître laquelle de ces trois situations
s'est produite — voir STRATEGIC_DEFERRED_WORK_REGISTER.md pour ce manque
nommé. count_missing_evidence() ci-dessous donne un signal agrégé
actionnable pour l'observabilité, pas une classification par ligne.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Libellés professionnels pour metric_type — jamais l'enum brute
# (MetricType, financial_truth.py) exposée à l'API ou au frontend.
_METRIC_TYPE_LABELS: dict[str, str] = {
    "REVENUE": "Chiffre d'affaires",
    "EBITDA": "EBITDA",
    "COST": "Coût",
    "MARGIN": "Marge",
    "CASH": "Trésorerie",
    "UNKNOWN": "Indicateur financier",
}


def _qualifier_for_source_types(source_references: list[Any]) -> str:
    """
    Traduit SourceType (interne, financial_truth.py) en qualificatif
    professionnel honnête pour l'utilisateur — jamais l'enum brute
    (CANONICAL_FACT, LLM_EXTRACTED, LEGACY_PARSE, ...) exposée telle quelle.

    Épistémologie (Mission 10) : le qualificatif le plus prudent présent
    l'emporte. LEGACY_PARSE (jamais certifié, financial_truth.py) domine
    tout le reste — un seul montant partiellement estimé rend l'ensemble
    du chiffre affiché non-certifié, jamais l'inverse.
    """
    types = {
        r.get("source_type")
        for r in source_references
        if isinstance(r, dict) and r.get("source_type")
    }
    if not types:
        return "non sourcé"
    if "LEGACY_PARSE" in types:
        return "estimation non vérifiée"
    if "CANONICAL_FACT" in types:
        return "preuve vérifiée"
    if "LLM_EXTRACTED" in types:
        return "extraction automatique"
    if "DETERMINISTIC_CALCULATION" in types:
        return "calcul déterministe"
    if "USER_PROVIDED" in types:
        return "saisie utilisateur"
    return "non sourcé"


def _project_evidence_row(row: dict) -> dict:
    """
    Projette une ligne evidence_ledger_entries brute vers EvidenceSupport
    (forme destinée à l'API/UI — jamais les colonnes JSONB brutes).

    N'expose jamais : fact_id, JSONB brut, capture_schema_version,
    analyse_id (déjà connu de l'appelant), entity_id, company_id.
    """
    facts = row.get("facts") or []
    sheets = row.get("sheets_verified") or []
    quantified_impacts = row.get("quantified_impacts") or []

    impacts_display = []
    for qi in quantified_impacts:
        if not isinstance(qi, dict):
            continue
        amount = qi.get("amount")
        # Article X (Constitution) — absence ≠ zéro : un impact dont le
        # montant est absent (None) ne constitue pas une preuve chiffrée
        # exploitable ici. Jamais affiché comme "0", jamais affiché du tout.
        if amount is None:
            continue
        impacts_display.append({
            "amount": amount,
            "currency": qi.get("currency") or "EUR",
            "metric_type_label": _METRIC_TYPE_LABELS.get(
                qi.get("metric_type"), _METRIC_TYPE_LABELS["UNKNOWN"]
            ),
            "confidence": qi.get("confidence"),
            "qualifier": _qualifier_for_source_types(qi.get("source_references") or []),
        })

    return {
        "status": "available",
        "facts_count": len(facts) if isinstance(facts, list) else 0,
        "sheets": sorted({s for s in sheets if isinstance(s, str)}) if isinstance(sheets, list) else [],
        "impacts": impacts_display,
    }


def get_evidence_support_by_analysis(
    supabase: Any,
    analysis_ids: list[str],
    company_id: str,
) -> dict[str, dict]:
    """
    Lit l'Evidence Ledger pour un lot d'analyses, scopé company_id.

    Args:
        supabase: client Supabase (service role).
        analysis_ids: ids d'analyses (analyses.id) pour lesquelles chercher
                      une capture Evidence. Doublons/valeurs vides tolérés.
        company_id: obligatoire — filtre tenant explicite (pas de RLS sur
                    cette table, voir docstring du module).

    Returns:
        dict {analyse_id: EvidenceSupport}. Une analyse absente des clés
        du dict retourné n'a AUCUNE preuve structurée disponible — ni plus,
        ni moins ; ce module ne devine jamais pourquoi (voir docstring).
        En cas d'erreur de lecture : dict vide, jamais une exception levée
        (lecture d'enrichissement, ne doit jamais casser Review Briefing —
        même discipline que le reste du Briefing de revue,
        cf. ArcService.build_review_briefing).
    """
    unique_ids = sorted({a for a in analysis_ids if a})
    if not unique_ids or not company_id:
        return {}

    try:
        result = (
            supabase.from_("evidence_ledger_entries")
            .select("analyse_id, facts, sheets_verified, quantified_impacts")
            .in_("analyse_id", unique_ids)
            .eq("company_id", company_id)
            .execute()
        )
    except Exception as e:
        logger.error(
            "[EVIDENCE QUERY] get_evidence_support_by_analysis failed — %s: %s",
            type(e).__name__, e,
        )
        return {}

    support_by_analysis: dict[str, dict] = {}
    for row in (result.data or []):
        if not isinstance(row, dict):
            continue
        analyse_id = row.get("analyse_id")
        if not analyse_id:
            continue
        try:
            support_by_analysis[analyse_id] = _project_evidence_row(row)
        except Exception as e:
            # Ligne malformée — ne doit jamais faire échouer les autres,
            # ni fabriquer un support factice pour celle-ci (Mission 17).
            logger.error(
                "[EVIDENCE QUERY] malformed evidence row for analyse_id=%s — %s: %s",
                analyse_id, type(e).__name__, e,
            )
            continue

    return support_by_analysis
