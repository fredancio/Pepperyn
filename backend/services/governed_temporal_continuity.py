"""Deterministic, read-only temporal comparison of governed V1 envelopes.

This module describes change, never cause. It only compares immutable source
facts from two integrity-checked envelopes belonging to the same scope.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
import re
from typing import Any

from services.governed_analysis_persistence import GovernedPersistenceRefused, load_governed_envelope
from services.v1_analysis_contract import GovernedAnalysisEnvelope, SourceFact


class GovernedTemporalContinuityRefused(RuntimeError):
    """Content-free fail-closed temporal comparison refusal."""


def _period_key(period: str | None) -> int | None:
    if not isinstance(period, str):
        return None
    match = re.fullmatch(r"(?:(\d{4})|FY(\d{2}|\d{4})(?: ACTUAL)?)", period)
    if not match:
        return None
    digits = match.group(1) or match.group(2)
    year = int(digits)
    # Retain the existing bounded FYxx -> 20xx convention, never infer dates.
    return 2000 + year if len(digits) == 2 else (year or None)


def _comparison_boundary() -> dict[str, str]:
    # A shared year-label family is NOT evidence of financial comparability.
    return {
        "comparison_scope": "ANNUAL_LABEL_ARITHMETIC_ONLY",
        "financial_comparability": "NOT_ESTABLISHED",
    }


def _facts_by_metric(facts: tuple[SourceFact, ...]) -> tuple[dict[str, SourceFact], list[str]]:
    grouped: dict[str, list[SourceFact]] = {}
    for fact in facts:
        grouped.setdefault(fact.metric, []).append(fact)
    contradictions = [
        f"Plusieurs faits gouvernés existent pour {metric} dans une même période."
        for metric, values in sorted(grouped.items()) if len(values) != 1
    ]
    unique = {metric: values[0] for metric, values in grouped.items() if len(values) == 1}
    return unique, contradictions


def compare_governed_envelopes(
    previous: GovernedAnalysisEnvelope,
    current: GovernedAnalysisEnvelope,
    *,
    previous_analysis_id: str,
    current_analysis_id: str,
) -> dict[str, Any]:
    """Compare literal facts without producing inference, cause or forecast."""
    previous_period = previous.source_facts.current_period
    current_period = current.source_facts.current_period
    previous_key, current_key = _period_key(previous_period), _period_key(current_period)
    result: dict[str, Any] = {
        **_comparison_boundary(),
        "previous_analysis_id": previous_analysis_id,
        "current_analysis_id": current_analysis_id,
        "previous_period": previous_period,
        "current_period": current_period,
        "changes": [],
        "unknowns": [],
        "contradictions": [],
        "causal_interpretation": None,
    }
    if previous.source_facts.status != "UNDERSTOOD" or current.source_facts.status != "UNDERSTOOD":
        result.update(status="UNKNOWN", unknowns=["La compréhension des deux sources n'est pas établie."])
        return result
    if previous_key is None or current_key is None:
        result.update(status="UNKNOWN", unknowns=["Les deux périodes gouvernées ne sont pas comparables."])
        return result
    if previous_key >= current_key:
        result.update(status="CONTRADICTION", contradictions=[
            "La période antérieure doit précéder strictement la période courante."
        ])
        return result
    if previous_period.startswith("FY") != current_period.startswith("FY"):
        result.update(status="UNKNOWN", unknowns=[
            "Le rapprochement des libellés calendaires et fiscaux n'est pas établi."
        ])
        return result
    if current_key - previous_key != 1:
        result.update(status="UNKNOWN", unknowns=[
            "Des années intermédiaires manquent ; aucun écart annuel consécutif n'est établi."
        ])
        return result

    previous_facts, previous_conflicts = _facts_by_metric(previous.source_facts.facts)
    current_facts, current_conflicts = _facts_by_metric(current.source_facts.facts)
    conflicts = previous_conflicts + current_conflicts
    if conflicts:
        result.update(status="CONTRADICTION", contradictions=conflicts)
        return result

    for metric in sorted(set(previous_facts) & set(current_facts)):
        before, after = previous_facts[metric], current_facts[metric]
        if before.unit != after.unit:
            result["unknowns"].append(f"Unité non comparable pour {metric}.")
            continue
        before_value, after_value = Decimal(str(before.value)), Decimal(str(after.value))
        if not before_value.is_finite() or not after_value.is_finite():
            result["unknowns"].append(f"Valeur non finie pour {metric} ; comparaison refusée.")
            continue
        # Default Decimal precision (28) can silently round large source integers.
        # Allocate enough precision for the literal operands and a carry digit.
        with localcontext() as context:
            context.prec = max(
                before_value.adjusted(), after_value.adjusted(), 0,
            ) - min(before_value.as_tuple().exponent, after_value.as_tuple().exponent, 0) + 3
            delta = after_value - before_value
        result["changes"].append({
            "metric": metric,
            "unit": after.unit,
            "previous_value": before.value,
            "current_value": after.value,
            "absolute_change": int(delta) if delta == delta.to_integral() else float(delta),
            "previous_fact_id": before.fact_id,
            "current_fact_id": after.fact_id,
        })
    for metric in sorted(set(previous_facts) - set(current_facts)):
        result["unknowns"].append(f"{metric} est absent de la période courante.")
    for metric in sorted(set(current_facts) - set(previous_facts)):
        result["unknowns"].append(f"{metric} est absent de la période antérieure.")
    if result["changes"] and result["unknowns"]:
        result["status"] = "PARTIALLY_COMPARABLE"
    else:
        result["status"] = "COMPARABLE" if result["changes"] else "UNKNOWN"
    if not result["changes"] and not result["unknowns"]:
        result["unknowns"].append("Aucune métrique commune comparable.")
    return result


def load_governed_temporal_comparison(
    supabase: Any, *, analysis_id: str, company_id: str,
) -> dict[str, Any]:
    """Load target and its unique nearest earlier period, strictly scoped."""
    try:
        target_rows = (
            supabase.from_("governed_analysis_envelopes")
            .select("analysis_id,company_id,entity_id,engagement_id,envelope_json")
            .eq("analysis_id", analysis_id).eq("company_id", company_id).limit(2).execute()
        ).data or []
        if len(target_rows) != 1:
            raise GovernedTemporalContinuityRefused("TEMPORAL_TARGET_NOT_FOUND")
        target = target_rows[0]
        rows = (
            supabase.from_("governed_analysis_envelopes")
            .select("analysis_id,company_id,entity_id,engagement_id,envelope_json")
            .eq("company_id", company_id).eq("entity_id", target["entity_id"])
            .eq("engagement_id", target["engagement_id"]).execute()
        ).data or []
    except GovernedTemporalContinuityRefused:
        raise
    except Exception as exc:
        raise GovernedTemporalContinuityRefused("TEMPORAL_PERSISTENCE_UNAVAILABLE") from exc

    try:
        current = load_governed_envelope(
            supabase, analysis_id=analysis_id, company_id=company_id,
            entity_id=target["entity_id"], engagement_id=target["engagement_id"],
        )
        verified_rows = []
        for row in rows:
            if row.get("analysis_id") == analysis_id:
                continue
            verified_rows.append((row, load_governed_envelope(
                supabase, analysis_id=row["analysis_id"], company_id=company_id,
                entity_id=target["entity_id"], engagement_id=target["engagement_id"],
            )))
    except (GovernedPersistenceRefused, KeyError) as exc:
        raise GovernedTemporalContinuityRefused("TEMPORAL_INTEGRITY_REFUSED") from exc

    target_period = current.source_facts.current_period
    target_key = _period_key(target_period)
    if target_key is None:
        return _unknown(analysis_id, target_period, "La période gouvernée courante n'est pas comparable.")
    if any(_period_key(envelope.source_facts.current_period) == target_key for _, envelope in verified_rows):
        return {
            **_comparison_boundary(), "status": "CONTRADICTION",
            "previous_analysis_id": None, "current_analysis_id": analysis_id,
            "previous_period": None, "current_period": target_period,
            "changes": [], "unknowns": [],
            "contradictions": ["Plusieurs analyses gouvernées existent pour la période courante."],
            "causal_interpretation": None,
        }
    if any(_period_key(envelope.source_facts.current_period) is None for _, envelope in verified_rows):
        return _unknown(analysis_id, target_period,
                        "Une période historique ne peut pas être ordonnée ; l'antériorité la plus proche n'est pas établie.")
    candidates = []
    for row, envelope in verified_rows:
        period = envelope.source_facts.current_period
        key = _period_key(period)
        if key is not None and key < target_key:
            candidates.append((key, row, envelope))
    if not candidates:
        return _unknown(analysis_id, target_period, "Aucune période antérieure gouvernée n'est disponible.")
    nearest_key = max(key for key, _, _ in candidates)
    nearest = [(row, envelope) for key, row, envelope in candidates if key == nearest_key]
    if len(nearest) != 1:
        return {
            **_comparison_boundary(),
            "status": "CONTRADICTION", "previous_analysis_id": None,
            "current_analysis_id": analysis_id, "previous_period": str(nearest_key),
            "current_period": target_period, "changes": [], "unknowns": [],
            "contradictions": ["Plusieurs analyses gouvernées existent pour la période antérieure la plus proche."],
            "causal_interpretation": None,
        }
    previous_row, previous = nearest[0]
    return compare_governed_envelopes(
        previous, current, previous_analysis_id=previous_row["analysis_id"],
        current_analysis_id=analysis_id,
    )


def _unknown(analysis_id: str, period: str | None, message: str) -> dict[str, Any]:
    return {
        **_comparison_boundary(),
        "status": "UNKNOWN", "previous_analysis_id": None,
        "current_analysis_id": analysis_id, "previous_period": None,
        "current_period": period, "changes": [], "unknowns": [message],
        "contradictions": [], "causal_interpretation": None,
    }
