"""Read-only arithmetic reconciliation under an explicitly supplied definition.

Internal computation, NOT an authorization boundary, classifier or canonical writer.
Callers must obtain scope and definition from governed evidence before use. No
default accounting convention; no causal, economic or decision inference.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
from typing import Any, Mapping, Sequence


def reconcile_reported_sum(
    observations: Sequence[Mapping[str, Any]], *, scope: Mapping[str, str],
    reported_metric: str, signed_terms: Mapping[str, int],
    definition_ref: str | None, source_sha256: str,
) -> dict[str, Any]:
    """Compare a reported subtotal with its declared signed composition.

    Exact Decimal arithmetic; output decimals are strings. Input values are never
    mutated/replaced. Every used claim is referenced; ambiguity is never averaged.
    Identical scope is required but is not proof of caller ownership/authorization.
    """
    if set(scope) != {"tenant", "entity", "engagement"} or not all(scope.values()):
        raise ValueError("RECONCILIATION_SCOPE_REQUIRED")
    if len(source_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in source_sha256):
        raise ValueError("RECONCILIATION_SOURCE_DIGEST_REQUIRED")
    if len(observations) > 250 or len(signed_terms) > 20:
        raise ValueError("RECONCILIATION_BOUND_EXCEEDED")
    result: dict[str, Any] = {
        "status": "UNKNOWN", "scope": dict(scope), "source_sha256": source_sha256,
        "definition_ref": definition_ref, "reported_metric": reported_metric,
        "reported_claims": [], "derived_value": None, "discrepancy": None,
        "dependency_refs": [], "canonical_value": None,
        "automatic_resolution": False, "causality": "NOT_ESTABLISHED",
        "economic_impact": "NOT_ESTABLISHED", "decision": None,
    }

    def unknown(reason: str, request: str, status: str = "UNKNOWN") -> dict[str, Any]:
        return {**result, "status": status, "reason": reason,
                "information_request": {"priority": "BEFORE_DEPENDENT_CONCLUSION", "request": request}}

    if not definition_ref or not signed_terms:
        return unknown("DEFINITION_NOT_ESTABLISHED", "Obtenir la formule et la convention de signes applicables au sous-total.")
    if reported_metric in signed_terms or any(type(v) is not int or v not in (-1, 1) for v in signed_terms.values()):
        raise ValueError("RECONCILIATION_INVALID_COMPOSITION")
    required = {reported_metric, *signed_terms}
    # Reject foreign observations before constructing any output context.
    if any(dict(o.get("scope", {})) != dict(scope) for o in observations):
        raise ValueError("RECONCILIATION_FOREIGN_SCOPE")
    selected = [o for o in observations if o.get("metric") in required]
    ids = [o.get("id") for o in selected]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("RECONCILIATION_INVALID_CLAIM_REFERENCES")
    if any(not o.get("source_ref") for o in selected):
        raise ValueError("RECONCILIATION_SOURCE_REFERENCE_REQUIRED")
    if required != {o["metric"] for o in selected}:
        missing = sorted(required - {o["metric"] for o in selected})
        return unknown("MISSING_COMPONENTS", "Obtenir uniquement les postes manquants : " + ", ".join(missing))
    period, unit = selected[0].get("period"), selected[0].get("unit")
    if not period or not unit or any(o.get("period") != period or o.get("unit") != unit for o in selected):
        return unknown("SCOPE_OR_UNIT_NOT_COMPARABLE", "Confirmer une période, une durée et une unité communes avant rapprochement.")
    values: dict[str, set[Decimal]] = {metric: set() for metric in required}
    claims = []
    for observation in selected:
        raw = observation.get("reported_value")
        if type(raw) not in (int, float):
            return unknown("NUMERIC_MEANING_AMBIGUOUS", "Clarifier la représentation numérique des postes concernés.", "AMBIGUOUS")
        try:
            value = Decimal(str(raw))
        except InvalidOperation:
            raise ValueError("RECONCILIATION_INVALID_NUMBER") from None
        if not value.is_finite():
            raise ValueError("RECONCILIATION_NONFINITE_NUMBER")
        values[observation["metric"]].add(value)
        claims.append({"id": observation["id"], "source_ref": observation["source_ref"],
                       "metric": observation["metric"], "value": str(value)})
    result.update(period=dict(period), unit=unit, dependency_refs=claims,
                  reported_claims=[c for c in claims if c["metric"] == reported_metric])
    if any(len(group) > 1 for group in values.values()):
        return unknown("CONFLICTING_DEPENDENCY", "Rapprocher les affirmations incompatibles avant de conclure sur le sous-total.", "CONTRADICTION")
    numbers = [next(iter(group)) for group in values.values()]
    # Enough precision for aligned decimal places plus carries; no implicit 28-digit rounding.
    precision = max(n.adjusted() for n in numbers) - min(n.as_tuple().exponent for n in numbers) + len(numbers) + 2
    with localcontext() as arithmetic:
        arithmetic.prec = max(28, precision)
        derived = sum((next(iter(values[metric])) * coefficient for metric, coefficient in signed_terms.items()), Decimal(0))
        reported = next(iter(values[reported_metric]))
        difference = abs(reported - derived)
    result.update(
        status="CONTRADICTION" if difference else "ARITHMETIC_MATCH_ONLY",
        derived_value=str(derived), discrepancy=str(difference),
        formula_terms=dict(signed_terms),
        information_request={"priority": "BEFORE_DEPENDENT_CONCLUSION",
            "request": "Confirmer la correction ou la base de signes ; aucune valeur n'est automatiquement remplacée."}
        if difference else None,
    )
    return result
