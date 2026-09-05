"""Closed, deterministic V1 Golden Case built from the hash-pinned M1C workbook.

The provider response is a declared deterministic test double.  Everything
before and after that boundary is real repository logic.  No caller input,
network access, credential, or production admission path exists here.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from sandbox.synthetic_raw_ingestion import build_registered_raw_financial_input
from services.decision_kernel_extractor import extract_decision_kernel
from services.executive_decision_model import build_executive_decision_model
from services.v1_analysis_contract import (
    GovernedAnalysisEnvelope, GovernedFinancialAnalysis,
    build_financial_understanding, build_openai_request,
    parse_openai_response, to_analysis_result,
)

V1_GOLDEN_MODEL = "gpt-5"


@dataclass(frozen=True)
class V1GoldenCaseResult:
    source_workbook_sha256: str
    provider_mode: str
    provider_request: Mapping[str, Any]
    envelope: GovernedAnalysisEnvelope
    executive_decision_model: Mapping[str, Any]
    decision_kernel: Mapping[str, Any] | None


def _deterministic_provider_double(
    understanding_sha256: str,
    nonce: str,
    facts: Mapping[str, Any],
) -> Mapping[str, Any]:
    ebitda = facts["EBITDA"]
    working_capital = facts["WORKING_CAPITAL"]
    analysis = GovernedFinancialAnalysis.model_validate({
        "source_representation_sha256": understanding_sha256,
        "invocation_nonce": nonce,
        "executive_diagnosis": (
            "L'EBITDA négatif constitue la tension observée prioritaire; "
            "l'effet du BFR sur la trésorerie reste à valider."
        ),
        "diagnosis_fact_ids": [ebitda.fact_id, working_capital.fact_id],
        "observations": [
            {"fact_id": ebitda.fact_id, "metric": ebitda.metric,
             "observed_value": ebitda.value, "severity": "HIGH"},
            {"fact_id": working_capital.fact_id, "metric": working_capital.metric,
             "observed_value": working_capital.value, "severity": "MEDIUM"},
        ],
        "dimension_assessments": [{
            "scope": "PROFITABILITY", "score": 2,
            "rationale": "Un EBITDA négatif indique une rentabilité opérationnelle dégradée.",
            "fact_ids": [ebitda.fact_id], "confidence": 90,
            "validation_required": ["Confirmer les retraitements EBITDA."],
        }],
        "inferences": [{
            "statement": "Le BFR peut contribuer à la tension de trésorerie.",
            "fact_ids": [working_capital.fact_id], "confidence": 60,
            "validation_required": ["Rapprocher le BFR du tableau des flux."],
        }],
        "unknowns": [{
            "question": "Quelle part du BFR est échue et recouvrable ?", "materiality": "HIGH",
        }],
        "contradictions": [],
        "recommendations": [{
            "priority": "P1", "action": "Rapprocher le BFR du tableau des flux.",
            "rationale": "Le montant du BFR est observé mais sa causalité de trésorerie ne l'est pas.",
            "fact_ids": [working_capital.fact_id],
            "prerequisite_validation": ["Obtenir le tableau des flux et la balance âgée."],
        }],
    })
    return {"status": "completed", "error": None, "output": [{
        "type": "message", "content": [{"type": "output_text", "text": analysis.model_dump_json()}],
    }]}


def run_v1_golden_case() -> V1GoldenCaseResult:
    """Run the fixed synthetic case; deliberately accepts no runtime input."""

    ingestion = build_registered_raw_financial_input()
    understanding = build_financial_understanding(ingestion.anonymized_payload)
    if understanding.status != "UNDERSTOOD":
        raise RuntimeError("V1_GOLDEN_UNDERSTANDING_NOT_ESTABLISHED")
    request, nonce, requested_understanding = build_openai_request(
        ingestion.anonymized_payload, model=V1_GOLDEN_MODEL,
    )
    if requested_understanding != understanding:
        raise RuntimeError("V1_GOLDEN_REQUEST_UNDERSTANDING_MISMATCH")
    facts = {fact.metric: fact for fact in understanding.facts}
    response = _deterministic_provider_double(
        understanding.source_representation_sha256, nonce, facts,
    )
    analysis = parse_openai_response(response, understanding, nonce)
    envelope = to_analysis_result(analysis, understanding)
    result = envelope.analysis_result
    edm = build_executive_decision_model(result.model_dump(mode="json"))
    kernel = extract_decision_kernel(
        result, "v1-golden-synthetic", source_data_hash=ingestion.source_sha256.lower(),
    )
    return V1GoldenCaseResult(
        source_workbook_sha256=ingestion.source_sha256,
        provider_mode="DETERMINISTIC_TEST_DOUBLE_NO_NETWORK",
        provider_request=request,
        envelope=envelope,
        executive_decision_model=edm.model_dump(mode="json"),
        decision_kernel=kernel.model_dump(mode="json") if kernel is not None else None,
    )


def restart_round_trip(result: V1GoldenCaseResult) -> GovernedAnalysisEnvelope:
    """Model a process restart using only the durable governed envelope."""

    serialized = json.dumps(result.envelope.model_dump(mode="json"), ensure_ascii=False)
    return GovernedAnalysisEnvelope.model_validate_json(serialized)
