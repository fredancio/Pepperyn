"""Terminal presentation of a server-loaded temporal comparison, not new analysis.

Ownership and previous-source integrity are enforced by the temporal loader.
These checks prevent a misbound or broadened snapshot reaching a renderer;
they are not a replacement for the loader or a caller-facing authority.
"""
from math import isfinite

from services.v1_analysis_contract import GovernedAnalysisEnvelope


def temporal_export_rows(envelope: GovernedAnalysisEnvelope, analysis_id: str,
                         comparison: dict | None) -> list[tuple[str, object]]:
    if comparison is None:
        # Compatibility for internal single-envelope renderers. HTTP exports
        # always load the owned history and never use this omission fallback.
        return []
    c = comparison
    statuses = {
        "COMPARABLE": "Ecarts arithmetiques disponibles",
        "PARTIALLY_COMPARABLE": "Ecarts arithmetiques partiels",
        "UNKNOWN": "UNKNOWN",
        "CONTRADICTION": "CONTRADICTION",
    }
    if (not isinstance(c, dict) or c.get("status") not in statuses
            or c.get("current_analysis_id") != analysis_id
            or c.get("current_period") != envelope.source_facts.current_period
            or c.get("comparison_scope") != "ANNUAL_LABEL_ARITHMETIC_ONLY"
            or c.get("financial_comparability") != "NOT_ESTABLISHED"
            or c.get("causal_interpretation") is not None):
        raise ValueError("TEMPORAL_EXPORT_BINDING_REFUSED")
    for key in ("changes", "unknowns", "contradictions"):
        if not isinstance(c.get(key), list):
            raise ValueError("TEMPORAL_EXPORT_SHAPE_REFUSED")
    if (any(not isinstance(x, str) or not x.strip()
            for key in ("unknowns", "contradictions") for x in c[key])
            or (c["status"] in {"UNKNOWN", "CONTRADICTION"} and c["changes"])
            or (c["status"] == "UNKNOWN" and not c["unknowns"])
            or (c["status"] == "CONTRADICTION" and not c["contradictions"])
            or (c["status"] == "COMPARABLE" and c["unknowns"])
            or (c["status"] == "PARTIALLY_COMPARABLE" and not c["unknowns"])
            or (c["status"] in {"COMPARABLE", "PARTIALLY_COMPARABLE"}
                and (not c["changes"] or c["contradictions"]))):
        raise ValueError("TEMPORAL_EXPORT_STATE_REFUSED")
    if c["changes"] and (not c.get("previous_analysis_id")
                         or c["previous_analysis_id"] == analysis_id
                         or not c.get("previous_period")):
        raise ValueError("TEMPORAL_EXPORT_PREVIOUS_REFUSED")
    facts = {fact.fact_id: fact for fact in envelope.source_facts.facts}
    seen = set()
    for change in c["changes"]:
        if not isinstance(change, dict):
            raise ValueError("TEMPORAL_EXPORT_CHANGE_REFUSED")
        fact = facts.get(change.get("current_fact_id"))
        if (fact is None or change.get("metric") in seen
                or change.get("metric") != fact.metric or change.get("unit") != fact.unit
                or change.get("current_value") != fact.value
                or not isinstance(change.get("previous_fact_id"), str)
                or not change["previous_fact_id"].strip()
                or any(type(change.get(k)) not in (int, float) or not isfinite(change[k])
                       for k in ("previous_value", "current_value", "absolute_change"))):
            raise ValueError("TEMPORAL_EXPORT_FACT_REFUSED")
        seen.add(change["metric"])
    rows: list[tuple[str, object]] = [
        ("Statut temporel", statuses[c["status"]]),
        ("Limite", "Comparabilite financiere non etablie. Calcul entre libelles annuels uniquement."),
        ("Interpretation", "Aucune causalite, aucun impact economique, resultat ou apprentissage deduit."),
        ("Analyse courante", analysis_id),
        ("Periode courante", c["current_period"] or "UNKNOWN"),
        ("Analyse anterieure", c.get("previous_analysis_id") or "Non selectionnee"),
        ("Periode anterieure", c.get("previous_period") or "UNKNOWN"),
    ]
    for change in c["changes"]:
        metric = change["metric"]
        rows.extend([
            (f"{metric} - unite", change["unit"]),
            (f"{metric} - valeur anterieure", change["previous_value"]),
            (f"{metric} - valeur courante", change["current_value"]),
            (f"{metric} - ecart arithmetique", change["absolute_change"]),
            (f"{metric} - fait anterieur", change["previous_fact_id"]),
            (f"{metric} - fait courant", change["current_fact_id"]),
        ])
    rows.extend(("UNKNOWN temporel", item) for item in c["unknowns"])
    rows.extend(("CONTRADICTION temporelle", item) for item in c["contradictions"])
    return rows
