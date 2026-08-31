"""Print non-secret, deterministic M1C raw-ingestion evidence."""

from __future__ import annotations

import json
import sys

from sandbox.synthetic_product import SandboxRefused
from sandbox.synthetic_raw_ingestion import build_registered_raw_financial_input


def _sheet_row(payload: dict, sheet_name: str, label: str) -> dict:
    sheet = next(item for item in payload["sheets"] if item["sheet_name"] == sheet_name)
    label_column = sheet["columns"][0]
    return next(row for row in sheet["full_table"] if row[label_column] == label)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        evidence = build_registered_raw_financial_input()
    except SandboxRefused as exc:
        print(f"Sandbox stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(2)

    parsed = dict(evidence.parsed_payload)
    output = {
        "fixture_id": evidence.fixture_id,
        "source_sha256": evidence.source_sha256,
        "quality_gate": dict(evidence.quality_gate),
        "components_exercised": [
            "validate_excel_before_analysis",
            "pepperyn_data_robustness.import_finance_excel",
            "FileConnector.fetch",
            "services.file_parser.parse_file",
            "financial_normalizer.wrap_file_parser_output",
            "anonymization_service.anonymize_parsed_data",
            "llm_service.classify_document",
            "llm_egress.dispatch_legacy_synthetic (closed admission refusal)",
        ],
        "current_period": parsed["temporal_context"]["detected_current_year"],
        "financial_ground_truth": {
            "revenue_2025": _sheet_row(parsed, "Compte de résultat", "Chiffre d'affaires")["2025"],
            "ebitda_2025": _sheet_row(parsed, "Compte de résultat", "EBITDA")["2025"],
            "net_result_2025": _sheet_row(parsed, "Compte de résultat", "Résultat net")["2025"],
            "cash_2025": parsed["bfr_summary"]["tresorerie_eur"],
            "bfr_2025": parsed["bfr_summary"]["bfr_eur"],
            "equity_2025": parsed["bilan_summary"]["capitaux_propres"],
            "total_assets_2025": parsed["bilan_summary"]["total_actif"],
        },
        "anonymization_summary": dict(evidence.anonymization_summary),
        "financial_representation_sha256": evidence.financial_representation_sha256,
        "provider_boundary_refusal": evidence.provider_boundary_refusal,
        "components_not_exercised": [
            "routers.analyze_file HTTP/auth/quota/persistence side effects",
            "llm_service.run_full_pipeline provider-dependent cognition",
            "AnalysisResult construction from provider output",
            "DecisionKernel and ExecutiveDecisionModel downstream projections",
            "synthetic OpenAI Founder review",
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
