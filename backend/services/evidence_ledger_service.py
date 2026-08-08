"""
evidence_ledger_service.py — T1C-A/T1C-B : persistance de l'Evidence Ledger (non-bloquant).

Écrit dans evidence_ledger_entries (migration v18) le résultat de
services/evidence_capture.py:capture_evidence(). Suit exactement le même
idiome que la persistance non-bloquante déjà utilisée pour usage_logs
(routers/analyze.py:_save_to_db) : toute erreur est loguée, jamais levée —
l'échec de cette écriture ne doit jamais faire échouer une analyse.

ADR-001 §8 : cette table n'est lue par aucun chemin de production existant.
Cet appel est donc, par construction, sans risque de régression : son échec,
ou son absence, ne change rien au comportement actuel du produit.

ADR-001A : entity_id est le rattachement TRANSITOIRE (voir migration v18) —
nullable, en attendant que l'Engagement (T2) existe physiquement. Aucune
décision de réattribution n'est prise ici ; ce module se contente d'écrire
ce qu'on lui donne.

FTE v0 (migration v23, docs/Architecture/FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md) :
observed_period_end est écrit UNIQUEMENT quand une ligne est de toute façon
insérée (le early-return sur evidence_capture vide n'est pas modifié) —
cette valeur est une métadonnée de l'enregistrement Evidence, pas une
entité indépendante ; sans Evidence, pas de ligne, donc pas de période
persistée non plus. Ce module ne calcule jamais cette valeur lui-même
(voir services/fte_minimal.py, appelé par l'appelant de cette fonction).
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)


def save_evidence_capture(
    analyse_id: str,
    company_id: str,
    entity_id: Optional[str],
    evidence_capture: Optional[dict[str, Any]],
    observed_period_end: Optional[date] = None,
) -> None:
    """
    Persiste une capture Evidence. Non-bloquant par construction : toute
    exception est loguée et avalée, jamais propagée — l'appelant ne doit
    jamais échouer à cause de cet appel (même contrat que l'insert
    usage_logs déjà existant dans routers/analyze.py:_save_to_db).

    N'écrit rien si evidence_capture est vide/None (aucune Evidence Graph
    n'a été produite, ou son parsing a échoué de façon non-bloquante en
    amont — cf. _run_evidence_graph_agent, qui retourne {} sur échec).

    Args:
        analyse_id: id de l'analyse d'origine. UNIQUE côté DB
                    (evidence_ledger_entries.analyse_id) — une seule
                    capture par analyse.
        company_id: requis, NOT NULL côté DB.
        entity_id:  rattachement transitoire (ADR-001A) — peut être None.
        evidence_capture: dict retourné par
                          services.evidence_capture.capture_evidence().
        observed_period_end: FTE v0 (migration v23) — borne de fin de la
                    période la plus récente déterministiquement observée
                    dans le dataset de cette capture, ou None si aucune
                    n'est résoluble. Calculé par l'appelant via
                    services.fte_minimal.resolve_newest_observed_period_end()
                    — jamais recalculé ici, jamais fabriqué si absent.
    """
    if not evidence_capture:
        return
    if not any(evidence_capture.get(k) for k in
               ("facts", "unavailable_data", "sheets_verified", "quantified_impacts")):
        # Capture entièrement vide (aucun fait, aucun impact) — rien à
        # persister. Ce n'est pas une erreur : cf. capture_evidence(),
        # une absence reste une absence, elle n'est pas stockée comme un
        # enregistrement vide sans valeur d'audit.
        return

    try:
        from main import get_supabase_service
        supabase = get_supabase_service()

        insert_payload = {
            "analyse_id": analyse_id,
            "company_id": company_id,
            "facts": evidence_capture.get("facts") or [],
            "unavailable_data": evidence_capture.get("unavailable_data") or [],
            "sheets_verified": evidence_capture.get("sheets_verified") or [],
            "quantified_impacts": evidence_capture.get("quantified_impacts") or [],
            # T1C-B (2026-08-02) : les quantified_impacts portent désormais
            # amount/currency atomiques et des source_references résolues
            # (fact_id déterministe) au lieu du fallback legacy quasi-
            # systématique de T1C-A. Anticipé par la migration v18 ("le schéma
            # JSONB absorbera ce changement sans nouvelle migration") — seule
            # cette version change, marquant sans ambiguïté quelles lignes
            # précèdent/suivent T1C-B.
            "capture_schema_version": "T1C-B-v1",
        }
        if entity_id is not None:
            insert_payload["entity_id"] = entity_id
        if observed_period_end is not None:
            insert_payload["observed_period_end"] = observed_period_end.isoformat()

        logger.debug("[EVIDENCE LEDGER] Insert capture analyse=%s", analyse_id)
        supabase.from_("evidence_ledger_entries").insert(insert_payload).execute()

    except Exception as e:
        logger.error(
            "[EVIDENCE LEDGER ERROR] save_evidence_capture failed — "
            "analyse_id=%s | error=%s: %s", analyse_id, type(e).__name__, e
        )
