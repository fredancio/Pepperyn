"""Closed registry and local inspection for synthetic V1 workbook rehearsals."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from connectors import FileConnector
from services.anonymization_service import anonymize_parsed_data
from services.data_quality_gate import validate_excel_before_analysis
from services.v1_analysis_contract import (
    GovernedAnalysisEnvelope,
    GovernedFinancialAnalysis,
    UnderstandingResult,
    build_financial_understanding,
    build_openai_request,
    parse_openai_response,
    to_analysis_result,
)

from sandbox.synthetic_product import SandboxRefused


REGISTERED_WORKBOOKS = {
    "FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93":
        "pepperyn_v1_heterogeneous_english.xlsx",
    "8F35CF676B58BFF823CD423BDA70145A9951A55B9F689FF591282F3EAF9C6E51":
        "pepperyn_v1_heterogeneous_ambiguous_period.xlsx",
    "E89851FF9AAF2FADA84F012CE7BDE846F859C7A62B1531F7C4F7F96A055F9E29":
        "pepperyn_v1_heterogeneous_ambiguous_number.xlsx",
    "176F8F1A9E6A20B61E61C773AD54000D1D91E769B84C99BD2DA7B8ACB038D7E5":
        "pepperyn_v1_heterogeneous_conflict.xlsx",
}

MOCK_ANALYSIS_WORKBOOK = "pepperyn_v1_heterogeneous_english.xlsx"


@dataclass(frozen=True)
class SyntheticMockAnalysis:
    filename: str
    source_sha256: str
    provider_mode: str
    provider_request: Mapping[str, Any]
    envelope: GovernedAnalysisEnvelope


def _registered_understanding(
    raw: bytes, filename: str,
) -> tuple[str, UnderstandingResult, Mapping[str, Any]]:
    digest = hashlib.sha256(raw).hexdigest().upper()
    registered_name = REGISTERED_WORKBOOKS.get(digest)
    if registered_name is None or filename != registered_name:
        raise SandboxRefused("UNREGISTERED_SYNTHETIC_WORKBOOK")

    gate = validate_excel_before_analysis(raw, filename)
    if not gate.can_analyze or gate.status not in {"ok", "warning"}:
        raise SandboxRefused("SYNTHETIC_WORKBOOK_QUALITY_GATE_REFUSED")
    parsed = FileConnector(raw, filename).fetch()
    anonymized, _ = anonymize_parsed_data(parsed)
    return digest, build_financial_understanding(anonymized), anonymized


def inspect_registered_workbook(raw: bytes, filename: str) -> dict[str, Any]:
    """Inspect an exact registered fixture locally; never build or dispatch a provider request."""

    digest, understanding, _ = _registered_understanding(raw, filename)
    return {
        "filename": filename,
        "source_sha256": digest,
        "status": understanding.status,
        "current_period": understanding.current_period,
        "facts": [fact.model_dump(mode="json") for fact in understanding.facts],
        "unknowns": list(understanding.unknowns),
        "provider_dispatch": "CLOSED",
    }


def _mock_response(understanding: UnderstandingResult, nonce: str) -> Mapping[str, Any]:
    facts = {fact.metric: fact for fact in understanding.facts}
    revenue, ebitda = facts["REVENUE"], facts["EBITDA"]
    cash, working_capital = facts["CASH"], facts["WORKING_CAPITAL"]
    analysis = GovernedFinancialAnalysis.model_validate({
        "source_representation_sha256": understanding.source_representation_sha256,
        "invocation_nonce": nonce,
        "executive_diagnosis": (
            "Le chiffre d'affaires, l'EBITDA, la trésorerie et le besoin en fonds de roulement "
            "sont établis; leurs causes et leur trajectoire restent à valider."
        ),
        "diagnosis_fact_ids": [revenue.fact_id, ebitda.fact_id, cash.fact_id, working_capital.fact_id],
        "observations": [
            {"fact_id": revenue.fact_id, "metric": revenue.metric,
             "observed_value": revenue.value, "severity": "INFORMATIONAL"},
            {"fact_id": ebitda.fact_id, "metric": ebitda.metric,
             "observed_value": ebitda.value, "severity": "INFORMATIONAL"},
            {"fact_id": cash.fact_id, "metric": cash.metric,
             "observed_value": cash.value, "severity": "INFORMATIONAL"},
        ],
        "dimension_assessments": [{
            "scope": "PROFITABILITY", "score": 5,
            "rationale": "L'EBITDA observé est positif, sans preuve suffisante de tendance.",
            "fact_ids": [ebitda.fact_id], "confidence": 70,
            "validation_required": ["Confirmer les retraitements et la tendance pluriannuelle."],
        }],
        "inferences": [{
            "statement": "Le niveau de BFR peut mobiliser une part de la trésorerie.",
            "fact_ids": [cash.fact_id, working_capital.fact_id], "confidence": 55,
            "validation_required": ["Rapprocher le BFR du tableau des flux et des échéanciers."],
        }],
        "unknowns": [{
            "question": "Quelle est l'évolution mensuelle de l'EBITDA et de la trésorerie ?",
            "materiality": "HIGH",
        }],
        "contradictions": [],
        "recommendations": [{
            "priority": "P1",
            "action": "Valider la conversion de l'EBITDA en trésorerie sur douze mois.",
            "rationale": "Les montants courants sont établis mais leur dynamique ne l'est pas.",
            "fact_ids": [ebitda.fact_id, cash.fact_id, working_capital.fact_id],
            "prerequisite_validation": ["Obtenir le tableau des flux mensuel et les échéanciers clients."],
        }],
    })
    return {"status": "completed", "error": None, "output": [{
        "type": "message",
        "content": [{"type": "output_text", "text": analysis.model_dump_json()}],
    }]}


def run_registered_mock_analysis(raw: bytes, filename: str) -> SyntheticMockAnalysis:
    """Run one exact synthetic upload through the governed contract with no network transport."""

    digest, understanding, anonymized = _registered_understanding(raw, filename)
    if filename != MOCK_ANALYSIS_WORKBOOK or understanding.status != "UNDERSTOOD":
        raise SandboxRefused("MOCK_ANALYSIS_REQUIRES_REGISTERED_UNDERSTOOD_WORKBOOK")
    request, nonce, requested_understanding = build_openai_request(anonymized, model="mock-v1-local")
    if requested_understanding != understanding or request.get("store") is not False:
        raise SandboxRefused("MOCK_ANALYSIS_REQUEST_INVARIANT_FAILED")
    response = _mock_response(understanding, nonce)
    analysis = parse_openai_response(response, understanding, nonce)
    return SyntheticMockAnalysis(
        filename=filename,
        source_sha256=digest,
        provider_mode="DETERMINISTIC_MOCK_NO_NETWORK",
        provider_request=request,
        envelope=to_analysis_result(analysis, understanding),
    )
