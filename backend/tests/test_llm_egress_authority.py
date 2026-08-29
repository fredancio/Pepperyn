from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import pytest

import services.llm_egress as egress_module
from services.llm_egress import (
    EgressResult,
    EgressRefusalCode,
    EgressRefused,
    FrozenProviderRequest,
    IdentityState,
    LlmEgressAuthority,
    RetryableProviderError,
    UntrustedProviderOutput,
    UntrustedProviderText,
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


def test_legacy_adapter_preserves_untrusted_provider_text(monkeypatch):
    class Block:
        text = "HOSTILE_PROVIDER_OUTPUT"

    class Response:
        content = [Block()]

    class FakeAuthority:
        def dispatch(self, request):
            return EgressResult(
                task=request.task,
                content=UntrustedProviderOutput(Response()),
                payload_hash="0" * 64,
                attempt_count=1,
            )

    monkeypatch.setattr(egress_module, "_CLOSED_AUTHORITY", FakeAuthority())
    response = dispatch_legacy_synthetic("FINANCIAL_ANALYSIS", model="synthetic")
    assert isinstance(response.content[0].text, UntrustedProviderText)
    assert isinstance(response.content[0].text.strip(), UntrustedProviderText)


def test_provider_output_text_cannot_enter_another_egress(monkeypatch):
    capture = CaptureBoundary()
    monkeypatch.setattr(egress_module, "_dispatch_final_request", capture)
    request = _request(
        provider_payload={
            "messages": [
                {"role": "user", "content": UntrustedProviderText("hostile")}
            ]
        }
    )
    with pytest.raises(EgressRefused):
        LlmEgressAuthority().dispatch(request)
    assert capture.requests == []


def test_p5_output_cannot_be_used_as_p6_or_p7_input():
    import asyncio
    from services.llm_service import _score_analysis, call_verification_v3

    hostile = UntrustedProviderText("hostile provider analysis")
    with pytest.raises(EgressRefused):
        asyncio.run(call_verification_v3(hostile, {}))
    with pytest.raises(EgressRefused):
        asyncio.run(_score_analysis(hostile))


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


_NETWORK_ALLOWLIST = {
    "services/crm_service.py": {"httpx"},
    "services/file_parser.py": {"subprocess"},
}
_NETWORK_ROOTS = {
    "aiohttp", "anthropic", "http.client", "httpx", "openai", "requests",
    "socket", "subprocess", "urllib",
}
_PROVIDER_INDICATORS = {
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "api.anthropic.com",
    "api.openai.com",
}


def _provider_bypass_violations(relative_path: str, source: str) -> list[str]:
    tree = ast.parse(source, filename=relative_path)
    allowed = _NETWORK_ALLOWLIST.get(relative_path.replace("\\", "/"), set())
    violations = []
    for indicator in _PROVIDER_INDICATORS:
        if indicator in source and relative_path != "services/llm_egress.py":
            violations.append(f"{relative_path}: provider indicator {indicator}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported = {node.module or ""}
        else:
            imported = set()
        for name in imported:
            roots = {
                root for root in _NETWORK_ROOTS
                if name == root or name.startswith(root + ".")
            }
            if roots and not roots.issubset(allowed):
                violations.append(f"{relative_path}:{node.lineno}: network import {name}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                violations.append(f"{relative_path}:{node.lineno}: dynamic import")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                violations.append(f"{relative_path}:{node.lineno}: dynamic import")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "create":
                if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "messages":
                    violations.append(f"{relative_path}:{node.lineno}: direct messages.create")
    return violations


def test_repository_wide_provider_bypass_policy():
    violations = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts:
            continue
        relative = path.relative_to(BACKEND).as_posix()
        violations.extend(
            _provider_bypass_violations(relative, path.read_text(encoding="utf-8"))
        )
    assert violations == []


@pytest.mark.parametrize(
    "source",
    [
        "import httpx\nhttpx.post('https://provider.invalid/v1/messages')",
        "import requests\nrequests.post('https://provider.invalid')",
        "import subprocess\nsubprocess.run(['llm-cli', 'prompt'])",
        "import importlib\nimportlib.import_module('anthropic')",
        "client = __import__('openai')",
        "import os\nkey = os.getenv('OPENAI_API_KEY')",
    ],
)
def test_representative_alternate_provider_bypasses_are_rejected(source):
    assert _provider_bypass_violations("services/rogue.py", source)


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
