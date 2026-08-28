from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import pytest

import services.llm_egress as egress_module
from services.llm_egress import (
    EgressRefusalCode,
    EgressRefused,
    FrozenProviderRequest,
    IdentityState,
    LlmEgressAuthority,
    RetryableProviderError,
    UntrustedProviderOutput,
    _mint_synthetic_test_request,
    dispatch_legacy_synthetic,
)


BACKEND = Path(__file__).resolve().parents[1]


class CaptureBoundary:
    def __init__(self, result=None, failures=0):
        self.result = result if result is not None else object()
        self.failures = failures
        self.requests: list[FrozenProviderRequest] = []

    def __call__(self, request: FrozenProviderRequest):
        self.requests.append(request)
        if len(self.requests) <= self.failures:
            raise RetryableProviderError("synthetic timeout")
        return self.result


def _request(**changes):
    values = {
        "task": "FINANCIAL_ANALYSIS",
        "provider_payload": {
            "model": "synthetic-model",
            "system": "STATIC_INSTRUCTION",
            "messages": [{"role": "user", "content": "CLIENT_001 revenue 123.45"}],
            "max_tokens": 50,
        },
    }
    values.update(changes)
    return _mint_synthetic_test_request(**values)


def test_final_transport_receives_exact_canonical_payload_bytes(monkeypatch):
    capture = CaptureBoundary(result="synthetic-output")
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    result = LlmEgressAuthority().dispatch(_request())

    assert isinstance(result.content, UntrustedProviderOutput)
    assert result.content.raw_response == "synthetic-output"
    assert len(capture.requests) == 1
    final = capture.requests[0]
    assert json.loads(final.body) == dict(_request().provider_payload)
    assert final.body == (
        b'{"max_tokens":50,"messages":[{"content":"CLIENT_001 revenue 123.45",'
        b'"role":"user"}],"model":"synthetic-model","system":"STATIC_INSTRUCTION"}'
    )
    assert len(final.payload_hash) == 64


def test_retry_reuses_byte_identical_frozen_request(monkeypatch):
    capture = CaptureBoundary(failures=2)
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    result = LlmEgressAuthority().dispatch(_request(max_attempts=3))
    assert result.attempt_count == 3
    assert len(capture.requests) == 3
    assert len({r.body for r in capture.requests}) == 1
    assert len({r.payload_hash for r in capture.requests}) == 1


def test_retry_limit_is_closed_and_deterministic(monkeypatch):
    capture = CaptureBoundary(failures=3)
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    with pytest.raises(RetryableProviderError):
        LlmEgressAuthority().dispatch(_request(max_attempts=2))
    assert len(capture.requests) == 2


def test_reidentified_input_is_refused_before_transport(monkeypatch):
    capture = CaptureBoundary()
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    with pytest.raises(EgressRefused) as exc:
        LlmEgressAuthority().dispatch(
            _request(identity_state=IdentityState.REIDENTIFIED)
        )
    assert exc.value.code is EgressRefusalCode.IDENTITY_FORBIDDEN
    assert capture.requests == []


def test_non_json_payload_is_refused_before_transport(monkeypatch):
    capture = CaptureBoundary()
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    with pytest.raises(EgressRefused) as exc:
        LlmEgressAuthority().dispatch(
            _request(provider_payload={"messages": object()})
        )
    assert exc.value.code is EgressRefusalCode.ROUTE_NOT_ALLOWED
    assert capture.requests == []


def test_default_production_transport_is_closed():
    with pytest.raises(EgressRefused) as exc:
        dispatch_legacy_synthetic(
            "DOCUMENT_CLASSIFICATION",
            model="synthetic-model",
            messages=[{"role": "user", "content": "synthetic"}],
        )
    assert exc.value.code is EgressRefusalCode.REAL_DATA_ADMISSION_CLOSED


def test_logs_contain_metadata_but_not_payload_or_output(caplog, monkeypatch):
    sentinel = "PERSON_SENTINEL_NEVER_LOG"
    capture = CaptureBoundary(result="PROVIDER_OUTPUT_NEVER_LOG")
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    request = _request(
        provider_payload={"messages": [{"role": "user", "content": sentinel}]}
    )
    with caplog.at_level(logging.INFO, logger="services.llm_egress"):
        LlmEgressAuthority().dispatch(request)
    rendered = caplog.text
    assert "task=FINANCIAL_ANALYSIS" in rendered
    assert "payload_hash=" in rendered
    assert sentinel not in rendered
    assert "PROVIDER_OUTPUT_NEVER_LOG" not in rendered


def test_all_production_model_calls_use_the_single_authority():
    violations = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names]
                if any(n.split(".")[0] in {"anthropic", "openai"} for n in names):
                    violations.append(f"{path}: provider SDK import")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "create" and isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "messages":
                        violations.append(f"{path}: direct messages.create")
    assert violations == []


def test_no_model_provider_credentials_outside_authority_package():
    violations = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts or path.name == "llm_egress.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "ANTHROPIC_API_KEY" in source or "api.anthropic.com" in source:
            violations.append(str(path))
    assert violations == []


def test_model_related_modules_cannot_construct_alternate_network_transport():
    model_related = (
        BACKEND / "services" / "llm_service.py",
        BACKEND / "services" / "conversation_engine.py",
        BACKEND / "services" / "executive_case_builder.py",
        BACKEND / "routers" / "analyze.py",
    )
    forbidden_roots = {
        "aiohttp",
        "anthropic",
        "http.client",
        "httpx",
        "openai",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    violations = []
    for path in model_related:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported = {node.module or ""}
            else:
                continue
            if any(
                name == root or name.startswith(root + ".")
                for name in imported
                for root in forbidden_roots
            ):
                violations.append(f"{path}: {sorted(imported)}")
    assert violations == []


def test_test_admission_minter_is_not_used_by_production_code():
    violations = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts or path.name == "llm_egress.py":
            continue
        source = path.read_text(encoding="utf-8")
        if any(
            symbol in source
            for symbol in (
                "_mint_synthetic_test_request",
                "_SYNTHETIC_TEST_ADMISSION",
            )
        ):
            violations.append(str(path))
    assert violations == []


def test_final_dispatch_symbol_has_one_production_call_site():
    occurrences = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "_dispatch_final_request":
                    occurrences.append((path, node.lineno))
    assert len(occurrences) == 1
    assert occurrences[0][0] == BACKEND / "services" / "llm_egress.py"


def test_export_builder_is_deterministic_and_has_no_provider_dispatch():
    source = (BACKEND / "services" / "executive_case_builder.py").read_text(
        encoding="utf-8"
    )
    assert "messages.create" not in source
    assert "dispatch_legacy_synthetic" not in source
    assert "import anthropic" not in source


def test_text_only_endpoint_is_disabled_before_model_dispatch():
    source = (BACKEND / "routers" / "analyze.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "analyze_text"
    )
    assert not any(
        isinstance(node, ast.Name)
        and node.id in {"dispatch_legacy_synthetic", "get_anthropic_client"}
        for node in ast.walk(function)
    )
    assert "status_code=410" in ast.get_source_segment(source, function)
