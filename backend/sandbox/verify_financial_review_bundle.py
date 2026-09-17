"""Read-only artifact verification. Never imports/runs Pepperyn financial analysis.

This validates the frozen review package, not financial correctness or gate PASS.
Only standard-library file/JSON/hash/schema operations; no network/database writes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "docs/Product/FinancialReliability"
FILES = (
    "review-source-v2.txt", "professional-reasoning-doctrine-v2.md",
    "casebook-v2.md", "synthetic-inputs-v2.json", "expected-contracts-v2.json",
)
IDS = [f"FR{i:02d}" for i in range(1, 13)]


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def json_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest().upper()


def text_hash(path: Path) -> str:
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    require("\r" not in text, "UNSUPPORTED_LINE_ENDING")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def describe(bundle: Path = BUNDLE) -> dict:
    """Integrity description for tooling; NOT approval or auto-freeze."""
    inputs = read_json(bundle / "synthetic-inputs-v2.json")
    oracle = read_json(bundle / "expected-contracts-v2.json")
    sources = {}
    for case in inputs["cases"]:
        observations = case["observations"] + case["adversarial_only_observations"]
        for source in case["sources"]:
            sources[source["id"]] = json_hash({
                "source": source,
                "observations": [o for o in observations if o["source_ref"] == source["id"]],
                "case_definitions": case.get("definitions", {}),
                "case_comparability": case["comparability"],
            })
    return {
        "files_utf8_lf_sha256": {name: text_hash(bundle / name) for name in FILES},
        "case_input_sha256": {c["case_id"]: json_hash(c) for c in inputs["cases"]},
        "case_contract_sha256": {c["case_id"]: json_hash(c) for c in oracle["cases"]},
        "source_sha256": sources,
    }


def validate_schema(inputs: dict, oracle: dict, review_text: str) -> None:
    require(inputs["schema_version"] == oracle["schema_version"] == 1, "SCHEMA_VERSION")
    require(inputs["synthetic_only"] is True and inputs["not_upload_registered"] is True, "SYNTHETIC_BOUNDARY")
    require(inputs["casebook_revision"] == oracle["revision"] == "FR-EXPECTED-2", "REVISION")
    require([c["case_id"] for c in inputs["cases"]] == IDS, "INPUT_CASE_SET")
    require([c["case_id"] for c in oracle["cases"]] == IDS, "ORACLE_CASE_SET")
    require(oracle["execution_status"] == "NOT_EXECUTED", "EXECUTION_CLAIM")
    require(oracle["financial_reliability_gate"] == "OPEN_NOT_PASS", "GATE_CLAIM")
    require(oracle["oracle_is_not_runtime_input"] is True, "ORACLE_SEPARATION")
    require(oracle["reviewer_identity"] is None and oracle["review_date"] is None, "INVENTED_ATTRIBUTION")
    all_observation_ids = set()
    for case, contract in zip(inputs["cases"], oracle["cases"]):
        cid = case["case_id"]
        require(case["synthetic_only"] is True and case["revision"] == 2, "CASE_SCOPE")
        require(contract["gate_execution"] == "NOT_EXECUTED" and
                contract["system_output_approval"] == "NOT_GIVEN", "RESULT_CLAIM")
        require(contract["readiness"]["basis"] == "STATIC_REPOSITORY_INSPECTION_NOT_EXECUTION", "READINESS_CLAIM")
        excerpt = contract["normative_review_excerpt"]
        section = int(cid[2:]) + 5
        require(contract["review_section"] == section, "REVIEW_SECTION_MISMATCH")
        marker = f"{section}. {cid} —"
        require(marker in review_text, "REVIEW_SECTION_MISSING")
        section_text = review_text.split(marker, 1)[1].split("\n============================================================", 2)[1].strip()
        require(excerpt == section_text, "REVIEW_EXCERPT_MISMATCH")
        require(contract["review_verdict"] in excerpt, "REVIEW_VERDICT_MISMATCH")
        source_ids = [s["id"] for s in case["sources"]]
        require(len(source_ids) == len(set(source_ids)), "DUPLICATE_SOURCE")
        require(all(s.startswith(cid + ".S") for s in source_ids), "FOREIGN_SOURCE_REF")
        local_ids = set()
        for observation in case["observations"] + case["adversarial_only_observations"]:
            oid = observation["id"]
            require(oid.startswith(cid + ".O") and oid not in all_observation_ids, "OBSERVATION_ID")
            all_observation_ids.add(oid)
            local_ids.add(oid)
            require(observation["source_ref"] in source_ids, "UNKNOWN_SOURCE_REF")
            require(type(observation["reported_value"]) is int and observation["unit"] == "EUR", "INPUT_VALUE")
            require(set(observation["scope"]) == {"tenant", "entity", "engagement"}, "SCOPE_FIELDS")
            require(all(observation["scope"].values()), "EMPTY_SCOPE")
            period = observation["period"]
            if period["kind"] == "STOCK":
                date.fromisoformat(period["as_of"])
            else:
                require(period["kind"] == "FLOW", "PERIOD_KIND")
                require(date.fromisoformat(period["start"]) <= date.fromisoformat(period["end"]), "PERIOD_ORDER")
                require(period["months"] in (3, 12), "PERIOD_DURATION")
        ordinary_ids = {o["id"] for o in case["observations"]}
        for item in contract["numerical_expectations"]:
            require(set(item["observation_refs"]) <= ordinary_ids, "FOREIGN_NUMERIC_BASIS")
            require(bool(item["observation_refs"]), "UNSOURCED_EXPECTATION")
            require(item["unit"] in {"EUR", "PERCENT", "PERCENTAGE_POINTS"}, "EXPECTED_UNIT")
            require(item["absolute_tolerance"] == (0 if item["unit"] == "EUR" else 0.01), "TOLERANCE")
        if cid != "FR12":
            require(not case["adversarial_only_observations"], "UNEXPECTED_ADVERSARIAL_INPUT")
        else:
            require(len(case["adversarial_only_observations"]) == 2, "ADVERSARIAL_INPUT_MISSING")
            require(all(o["scope"] == case["authorized_context"] for o in case["observations"]), "AUTHORIZED_SCOPE")
            require(all(o["scope"] != case["authorized_context"] and o["adversarial_only"] is True
                        for o in case["adversarial_only_observations"]), "ADVERSARIAL_SCOPE")


def verify(bundle: Path = BUNDLE) -> dict:
    manifest = read_json(bundle / "frozen-manifest-v2.json")
    require(manifest["revision"] == "FR-EXPECTED-2", "MANIFEST_REVISION")
    require(manifest["integrity"] == describe(bundle), "FROZEN_CONTENT_MISMATCH")
    validate_schema(read_json(bundle / "synthetic-inputs-v2.json"),
                    read_json(bundle / "expected-contracts-v2.json"),
                    (bundle / "review-source-v2.txt").read_text(encoding="utf-8"))
    return {"artifact_integrity": "PASS", "case_count": 12,
            "manifest_utf8_lf_sha256": text_hash(bundle / "frozen-manifest-v2.json"),
            "financial_analyses_executed": 0, "financial_reliability_gate": "OPEN_NOT_PASS",
            "provider_used": False, "database_writes": False}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
