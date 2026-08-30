from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

import sandbox.synthetic_product as sandbox_module
from sandbox.synthetic_product import (
    IsolatedSandboxLlmEgressAuthority,
    OPTILUX_V3_SHA256,
    SandboxRefused,
    load_registered_fixture,
    run_conformance,
)


BACKEND = Path(__file__).parents[1]


def _response(value=None):
    value = value or {
        "diagnostic": "Cas synthétique Optilux.",
        "recommendations": ["Prioriser la trésorerie."],
        "uncertainties": ["Validation dirigeant requise."],
        "founder_questions": ["Cette sortie réduit-elle le travail cognitif ?"],
    }
    return {
        "status": "completed",
        "error": None,
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}],
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    }


def test_registry_contains_only_exact_optilux_fixture():
    fixture = load_registered_fixture()
    assert fixture.fixture_id == "OPTILUX_V3"
    assert fixture.sha256 == OPTILUX_V3_SHA256


def test_loader_accepts_no_path_upload_or_identifiers():
    assert tuple(inspect.signature(load_registered_fixture).parameters) == ()
    with pytest.raises(TypeError):
        load_registered_fixture("C:/real-client.xlsx")
    assert tuple(inspect.signature(IsolatedSandboxLlmEgressAuthority.dispatch_registered_optilux).parameters) == ("self",)


def test_modified_or_foreign_fixture_is_rejected(monkeypatch, tmp_path):
    foreign = tmp_path / "foreign.json"
    foreign.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sandbox_module, "_FIXTURE", foreign)
    with pytest.raises(SandboxRefused, match="HASH_MISMATCH"):
        load_registered_fixture()


def test_conformance_reuses_real_financial_models_and_never_calls_network():
    seen = []
    result = run_conformance(lambda body: seen.append(json.loads(body)) or _response())
    assert result.fixture_id == "OPTILUX_V3"
    assert result.deterministic_summary["analysis"]
    assert result.deterministic_summary["executive_decision_model"]
    assert result.deterministic_summary["decision_kernel"]
    assert result.gpt_review["diagnostic"] == "Cas synthétique Optilux."
    assert seen[0]["store"] is False


def test_sandbox_response_refusal_and_wrong_shape_fail_closed():
    with pytest.raises(SandboxRefused):
        run_conformance(lambda _: {"status": "incomplete"})
    with pytest.raises(SandboxRefused):
        run_conformance(lambda _: _response({"diagnostic": "missing fields"}))


def test_sandbox_has_no_production_data_or_memory_imports():
    source = (BACKEND / "sandbox" / "synthetic_product.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    forbidden = {"supabase", "services.memory_service", "services.decision_memory_service"}
    assert not any(name in forbidden or name.startswith("routers") for name in imports)
    assert "company_id" not in inspect.signature(sandbox_module.run_rehearsal).parameters
    assert "analysis_id" not in inspect.signature(sandbox_module.run_rehearsal).parameters


def test_production_modules_do_not_import_sandbox():
    violations = []
    for root in (BACKEND / "services", BACKEND / "routers"):
        for path in root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if "from sandbox" in source or "import sandbox" in source:
                violations.append(path.relative_to(BACKEND).as_posix())
    assert violations == []


def test_live_sandbox_transport_remains_behind_llm_egress_authority():
    backend = BACKEND
    network_tokens = ("httpx.post(", "OpenAI(", "requests.post(")
    violations = []
    for path in backend.rglob("*.py"):
        if path.name == "synthetic_product.py" or "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if any(token in source for token in network_tokens):
            violations.append(path.relative_to(backend).as_posix())
    assert violations == []
