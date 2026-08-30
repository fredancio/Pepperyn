"""Optilux-only Founder product rehearsal with no production data adapters."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from models.schemas import AnalysisResult
from services.decision_kernel_extractor import extract_decision_kernel
from services.executive_decision_model import build_executive_decision_model
from services.llm_egress import LlmEgressAuthority


OPTILUX_V3_SHA256 = "6C66DE79F3AEBDACD41CE70AB38070C15A2516912105FB8E226A38CAAFCBFADB"
_FIXTURE = Path(__file__).parents[1] / "tests" / "golden" / "fixtures" / "optilux_v3_analysis_result.json"
_META = {"_comment", "_version", "_produced_at_test", "_analyse_id_test", "_source_data_hash_test"}


class SandboxRefused(RuntimeError):
    pass


class IsolatedSandboxLlmEgressAuthority(LlmEgressAuthority):
    """Development-only authority subclass with no production import path."""

    def dispatch_registered_optilux(self) -> Mapping[str, Any]:
        fixture = load_registered_fixture()
        digest = hashlib.sha256(fixture.raw_bytes).hexdigest().upper()
        if digest != OPTILUX_V3_SHA256 or fixture.fixture_id != "OPTILUX_V3":
            raise SandboxRefused("REGISTERED_FIXTURE_HASH_MISMATCH")
        # Rebuild product projections here; no body, task, model or caller text
        # crosses this sandbox execution boundary.
        body = json.dumps(
            _payload(_deterministic_summary(fixture)), ensure_ascii=False,
            allow_nan=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise SandboxRefused("SANDBOX_CONFIGURATION_REQUIRED")
        try:
            import httpx
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                content=body, timeout=90.0,
            )
            response.raise_for_status()
            value = response.json()
        except Exception as exc:
            raise SandboxRefused("SANDBOX_PROVIDER_FAILED") from exc
        if not isinstance(value, Mapping):
            raise SandboxRefused("SANDBOX_PROVIDER_FAILED")
        return value


@dataclass(frozen=True)
class SandboxFixture:
    fixture_id: str
    sha256: str
    raw_bytes: bytes
    analysis: AnalysisResult


@dataclass(frozen=True)
class SandboxResult:
    fixture_id: str
    deterministic_summary: Mapping[str, Any]
    gpt_review: Mapping[str, Any]
    usage: Mapping[str, int]


def load_registered_fixture() -> SandboxFixture:
    """Closed loader: no path, upload, company, entity, or analysis argument."""

    raw_bytes = _FIXTURE.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest().upper()
    if digest != OPTILUX_V3_SHA256:
        raise SandboxRefused("REGISTERED_FIXTURE_HASH_MISMATCH")
    data = json.loads(raw_bytes.decode("utf-8"))
    for key in _META:
        data.pop(key, None)
    return SandboxFixture("OPTILUX_V3", digest, raw_bytes, AnalysisResult(**data))


_REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["diagnostic", "recommendations", "uncertainties", "founder_questions"],
    "properties": {
        "diagnostic": {"type": "string", "maxLength": 4000},
        "recommendations": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 1000}},
        "uncertainties": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 1000}},
        "founder_questions": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 1000}},
    },
}


def _deterministic_summary(fixture: SandboxFixture) -> dict[str, Any]:
    raw = fixture.analysis.model_dump(mode="json")
    edm = build_executive_decision_model(raw)
    kernel = extract_decision_kernel(
        fixture.analysis, "optilux-sandbox-v3",
        source_data_hash=fixture.sha256.lower(),
    )
    return {
        "company_name": raw.get("company_name") or "Optilux",
        "analysis": raw,
        "executive_decision_model": edm.model_dump(mode="json"),
        "decision_kernel": kernel.model_dump(mode="json") if kernel is not None else None,
    }


def _payload(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model": "gpt-5",
        "store": False,
        "instructions": (
            "You are reviewing the synthetic Optilux financial case inside an isolated development sandbox. "
            "Use only the supplied record. Distinguish observed facts, deterministic calculations, and uncertainty. "
            "Do not claim access to external or real-client data. Respond in French."
        ),
        "input": json.dumps(summary, ensure_ascii=False, sort_keys=True),
        "max_output_tokens": 2500,
        "text": {"format": {"type": "json_schema", "name": "optilux_founder_review", "strict": True, "schema": _REVIEW_SCHEMA}},
    }


def _extract_structured_response(response: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    if response.get("status") != "completed" or response.get("error"):
        raise SandboxRefused("OPENAI_RESPONSE_NOT_COMPLETED")
    texts = []
    for item in response.get("output", []):
        if not isinstance(item, Mapping) or item.get("type") != "message":
            continue
        for block in item.get("content", []):
            if isinstance(block, Mapping) and block.get("type") == "refusal":
                raise SandboxRefused("OPENAI_REFUSAL")
            if isinstance(block, Mapping) and block.get("type") == "output_text":
                texts.append(block.get("text"))
    if len(texts) != 1 or not isinstance(texts[0], str):
        raise SandboxRefused("UNSUPPORTED_OPENAI_RESPONSE")
    try:
        value = json.loads(texts[0])
    except json.JSONDecodeError as exc:
        raise SandboxRefused("MALFORMED_OPENAI_OUTPUT") from exc
    if set(value) != set(_REVIEW_SCHEMA["required"]):
        raise SandboxRefused("OPENAI_OUTPUT_SCHEMA_MISMATCH")
    usage = response.get("usage") or {}
    return value, {
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


def run_rehearsal() -> SandboxResult:
    """No caller content is accepted; the input universe is the registered fixture."""

    fixture = load_registered_fixture()
    summary = _deterministic_summary(fixture)
    response = IsolatedSandboxLlmEgressAuthority().dispatch_registered_optilux()
    review, usage = _extract_structured_response(response)
    return SandboxResult(fixture.fixture_id, summary, review, usage)


def run_conformance(provider: Callable[[bytes], Mapping[str, Any]]) -> SandboxResult:
    fixture = load_registered_fixture()
    summary = _deterministic_summary(fixture)
    body = json.dumps(
        _payload(summary), ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    review, usage = _extract_structured_response(provider(body))
    return SandboxResult(fixture.fixture_id, summary, review, usage)
