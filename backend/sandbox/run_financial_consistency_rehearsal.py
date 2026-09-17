"""Bounded offline component evidence, never a Financial Reliability Gate verdict.

Reviewed expected answers are not inputs to either product computation. This
adapter is synthetic-only, not an ingestion registration or authorization proof.
"""
from __future__ import annotations

import json
import hashlib
from datetime import date

from sandbox.verify_financial_review_bundle import BUNDLE, ROOT, json_hash, read_json, text_hash, verify
from sandbox.heterogeneous_workbooks import summarize_understanding
from services.v1_analysis_contract import build_financial_understanding
from services.financial_reconciliation import reconcile_reported_sum


def annual_source_adapter(case: dict) -> tuple[dict, dict]:
    if case.get("synthetic_only") is not True or not case.get("observations"):
        raise ValueError("SYNTHETIC_SOURCE_REQUIRED")
    scope = case["authorized_context"]
    sources = {s["id"] for s in case["sources"]}
    rows = case["observations"]
    if any(o["scope"] != scope or o["source_ref"] not in sources for o in rows):
        raise ValueError("SOURCE_SCOPE_MISMATCH")
    if len({o["id"] for o in rows}) != len(rows):
        raise ValueError("DUPLICATE_OBSERVATION")
    period = rows[0]["period"]
    if any(o["period"] != period or o["unit"] != "EUR" for o in rows):
        raise ValueError("SINGLE_PERIOD_EUR_COMPONENT_ONLY")
    if period.get("kind") != "FLOW" or period.get("months") != 12:
        raise ValueError("ANNUAL_FLOW_COMPONENT_ONLY")
    start, end = date.fromisoformat(period["start"]), date.fromisoformat(period["end"])
    if start != date(start.year, 1, 1) or end != date(start.year, 12, 31):
        raise ValueError("ANNUAL_FLOW_COMPONENT_ONLY")
    year = str(start.year)
    sheets = [{"sheet_name": o["id"], "columns": ["Label", year],
               "full_table": [{"Label": o["metric"].replace("_", " "), year: o["reported_value"]}]}
              for o in rows]
    parsed = {"temporal_context": {"columns_by_role": {"CURRENT_ACTUAL": [year]}}, "sheets": sheets}
    # Each synthetic observation gets a separate sheet, so all source claims remain distinct.
    lineage = {o["id"]: {"source_ref": o["source_ref"], "scope": o["scope"], "period": o["period"]} for o in rows}
    return parsed, lineage


def run() -> dict:
    integrity = verify()
    cases = {c["case_id"]: c for c in read_json(BUNDLE / "synthetic-inputs-v2.json")["cases"]}
    conflict = cases["FR07"]
    parsed, lineage = annual_source_adapter(conflict)
    understanding = build_financial_understanding(parsed)
    inspection = summarize_understanding(understanding)
    references = {"S" + hashlib.sha256(identifier.encode()).hexdigest()[:12].upper():
                  {"observation_id": identifier, **source} for identifier, source in lineage.items()}
    fact_lineage = {fact.fact_id: references[fact.source_sheet_ref] for fact in understanding.facts}
    reconciliation = cases["FR08"]
    if reconciliation["definitions"].get("GROSS_MARGIN_FORMULA") != "REVENUE + SIGNED_COST_OF_SALES":
        raise ValueError("UNSUPPORTED_DECLARED_FORMULA")
    output = reconcile_reported_sum(reconciliation["observations"], scope=reconciliation["authorized_context"],
        reported_metric="GROSS_MARGIN", signed_terms={"REVENUE": 1, "COST_OF_SALES": 1},
        definition_ref="synthetic-inputs-v2.json#/cases/FR08/definitions/GROSS_MARGIN_FORMULA",
        source_sha256=json_hash(reconciliation))
    return {
        "revision": "FR-EXPECTED-2", "evidence": "LOCAL_SYNTHETIC_COMPONENT_OUTPUT_ONLY",
        "manifest_sha256": integrity["manifest_utf8_lf_sha256"],
        "code_utf8_lf_sha256": {path: text_hash(ROOT / path) for path in (
            "backend/services/v1_analysis_contract.py", "backend/services/financial_reconciliation.py",
            "backend/sandbox/heterogeneous_workbooks.py", "backend/sandbox/run_financial_consistency_rehearsal.py")},
        "cases": [
            {"case_id": "FR07", "input_sha256": json_hash(conflict), "fact_lineage": fact_lineage, "output": inspection},
            {"case_id": "FR08", "input_sha256": json_hash(reconciliation), "output": output}],
        "full_case_pass": False, "professional_output_review": "NOT_PERFORMED",
        "financial_reliability_gate": "OPEN_NOT_PASS", "provider_used": False,
        "database_writes": False, "real_data_used": False,
        "not_proven": ["BROWSER_E2E", "PERSISTENCE_OF_CONTRADICTIONS", "EXPORTS_OF_CONTRADICTIONS",
                       "PRODUCTION_AUTHORIZATION", "FULL_FINANCIAL_RELIABILITY"],
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, ensure_ascii=False))
