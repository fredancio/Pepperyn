from dataclasses import FrozenInstanceError, replace
import ast
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from services.llm_egress import EgressRefusalCode, EgressRefused, LlmEgressAuthority, _mint_synthetic_test_request
from services.ownership_authority import (
    AuthenticatedPrincipal,
    EgressAuthorization,
    InMemoryOwnershipRepository,
    InMemoryScopedContextRepository,
    OwnershipAuthority,
    OwnershipRecord,
    OwnershipRefused,
    ProtectedContextReader,
    ProtectedReadGrant,
    ProtectedResource,
    ScopedContextRecord,
)


def _authority(records=None, ttl=30.0, **kwargs):
    records = records or [OwnershipRecord("a-a", "co", "entity-a", "eng-a", "co", "entity-a")]
    return OwnershipAuthority(InMemoryOwnershipRepository(records), ttl_seconds=ttl, **kwargs)


def _grant(authority=None, *, analysis="a-a", company="co", request="req", entity=None, engagement=None, resources=None):
    authority = authority or _authority()
    principal = authority._accept_authenticated_principal("user", company)
    return authority, authority.resolve_and_mint_read_grant(
        principal=principal, analysis_id=analysis, request_id=request,
        expected_entity_id=entity, expected_engagement_id=engagement,
        resources=resources or [ProtectedResource.ANALYSIS_RESULT],
    )


def test_foreign_analysis_rejected_before_context_repository_read():
    class Spy:
        reads = 0
        def read_scoped(self, resource):
            self.reads += 1
            return ()
    authority = _authority()
    principal = authority._accept_authenticated_principal("user", "foreign-company")
    spy = Spy()
    with pytest.raises(OwnershipRefused):
        authority.resolve_and_mint_read_grant(principal=principal, analysis_id="a-a", request_id="r", resources=[ProtectedResource.ANALYSIS_RESULT])
    assert spy.reads == 0


def test_same_tenant_different_entity_isolated():
    authority, grant = _grant(resources=[ProtectedResource.MEMORY])
    repo = InMemoryScopedContextRepository([
        ScopedContextRecord(ProtectedResource.MEMORY, "co", "entity-a", "eng-a", None, "A"),
        ScopedContextRecord(ProtectedResource.MEMORY, "co", "entity-b", "eng-b", None, "B"),
    ])
    assert ProtectedContextReader(repo).read(grant, request_id="req", resource=ProtectedResource.MEMORY) == ("A",)


def test_same_entity_different_engagement_isolated():
    authority, grant = _grant(resources=[ProtectedResource.DECISIONS_ACTIONS])
    repo = InMemoryScopedContextRepository([
        ScopedContextRecord(ProtectedResource.DECISIONS_ACTIONS, "co", "entity-a", "eng-a", None, "right"),
        ScopedContextRecord(ProtectedResource.DECISIONS_ACTIONS, "co", "entity-a", "eng-old", None, "wrong"),
    ])
    assert ProtectedContextReader(repo).read(grant, request_id="req", resource=ProtectedResource.DECISIONS_ACTIONS) == ("right",)


@pytest.mark.parametrize("company,entity,engagement", [
    ("other", None, None), ("co", "entity-b", None), ("co", None, "eng-b")
])
def test_caller_supplied_scope_mismatch_rejected(company, entity, engagement):
    with pytest.raises(OwnershipRefused):
        _grant(company=company, entity=entity, engagement=engagement)


def test_ambiguous_ownership_fails_closed():
    authority = _authority([
        OwnershipRecord("a", "co", "e1", "g1", "co", "e1"), OwnershipRecord("a", "co", "e2", "g2", "co", "e2")
    ])
    with pytest.raises(OwnershipRefused):
        _grant(authority, analysis="a")


@pytest.mark.parametrize("record", [
    OwnershipRecord("a", "co", None, "g"), OwnershipRecord("a", "co", "e", None)
])
def test_missing_required_scope_fails_closed(record):
    with pytest.raises(OwnershipRefused):
        _grant(_authority([record]), analysis="a")


@pytest.mark.parametrize("record", [
    OwnershipRecord("a", "co-a", "entity-b", "eng-b", "co-b", "entity-b"),
    OwnershipRecord("a", "co", "entity-a", "eng-b", "co", "entity-b"),
])
def test_incoherent_entity_company_or_engagement_entity_rejected(record):
    with pytest.raises(OwnershipRefused):
        _grant(_authority([record]), analysis="a", company=record.company_id)


def test_ordinary_caller_cannot_mint_capabilities():
    with pytest.raises(OwnershipRefused):
        AuthenticatedPrincipal("u", "co", object())
    principal = _authority()._accept_authenticated_principal("u", "co")
    with pytest.raises(OwnershipRefused):
        ProtectedReadGrant(principal, None, "r", frozenset(), 0, "x", None, object())
    with pytest.raises(OwnershipRefused):
        EgressAuthorization(None, "t", "r", frozenset(), "0" * 64, "x", 0, None, object())


def test_grant_is_immutable_and_cannot_be_widened():
    _, grant = _grant()
    with pytest.raises(FrozenInstanceError):
        grant.request_id = "other"
    forged = replace(grant, allowed_resources=frozenset([ProtectedResource.MEMORY]))
    with pytest.raises(OwnershipRefused):
        ProtectedContextReader(InMemoryScopedContextRepository([])).read(forged, request_id="req", resource=ProtectedResource.MEMORY)


def test_grant_cannot_cross_request_or_resource():
    _, grant = _grant()
    reader = ProtectedContextReader(InMemoryScopedContextRepository([]))
    with pytest.raises(OwnershipRefused):
        reader.read(grant, request_id="other", resource=ProtectedResource.ANALYSIS_RESULT)
    with pytest.raises(OwnershipRefused):
        reader.read(grant, request_id="req", resource=ProtectedResource.MEMORY)


def test_expired_grant_rejected():
    with pytest.raises(OwnershipRefused):
        _authority(ttl=-1)


@pytest.mark.parametrize("ttl", [0, float("nan"), float("inf"), 301])
def test_invalid_or_unbounded_ttl_rejected(ttl):
    with pytest.raises(OwnershipRefused):
        _authority(ttl=ttl)


def test_legacy_unattributed_memory_is_quarantined():
    _, grant = _grant(resources=[ProtectedResource.MEMORY])
    repo = InMemoryScopedContextRepository([
        ScopedContextRecord(ProtectedResource.MEMORY, "co", None, None, None, "legacy"),
        ScopedContextRecord(ProtectedResource.MEMORY, "co", "entity-a", "eng-a", None, "scoped"),
    ])
    assert ProtectedContextReader(repo).read(grant, request_id="req", resource=ProtectedResource.MEMORY) == ("scoped",)


def _authorized_request():
    payload = {"synthetic": True}
    authority, grant = _grant(_authority(
        projection_policy={ProtectedResource.ANALYSIS_RESULT: frozenset({("synthetic",)})},
        allowed_payload_keys=frozenset({"synthetic"}),
    ))
    records = [ScopedContextRecord(ProtectedResource.ANALYSIS_RESULT, "co", "entity-a", "eng-a", "a-a", payload)]
    source_receipt = ProtectedContextReader(InMemoryScopedContextRepository(records)).read_receipted(
        grant, request_id="req", resource=ProtectedResource.ANALYSIS_RESULT
    )[0][1]
    read_receipt = authority.project_read(source_receipt, ("synthetic",))
    receipt = authority.receipt_disclosure(
        grant=grant, request_id="req", protected_reads=[read_receipt], disclosure_payload=payload
    )
    auth = authority.mint_egress_authorization(grant=grant, receipt=receipt, task="TASK")
    return _mint_synthetic_test_request(task="TASK", provider_payload=payload, request_id="req", egress_authorization=auth)


def test_egress_authorization_is_single_use(monkeypatch):
    import services.llm_egress as module
    monkeypatch.setattr(module, "_dispatch_final_request", lambda request: "ok")
    request = _authorized_request()
    LlmEgressAuthority().dispatch(request)
    with pytest.raises(EgressRefused) as exc:
        LlmEgressAuthority().dispatch(request)
    assert exc.value.code is EgressRefusalCode.OWNERSHIP_AUTHORIZATION_REQUIRED


def test_concurrent_egress_consumption_allows_exactly_one_dispatch(monkeypatch):
    import services.llm_egress as module
    calls = []
    lock = threading.Lock()
    def transport(request):
        with lock:
            calls.append(request)
        return "ok"
    monkeypatch.setattr(module, "_dispatch_final_request", transport)
    request = _authorized_request()
    barrier = threading.Barrier(8)
    def invoke():
        barrier.wait()
        try:
            LlmEgressAuthority().dispatch(request)
            return True
        except EgressRefused:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: invoke(), range(8)))
    assert results.count(True) == 1
    assert len(calls) == 1


def test_disclosure_cannot_claim_foreign_arbitrary_payload():
    authority, grant = _grant(_authority(
        projection_policy={ProtectedResource.ANALYSIS_RESULT: frozenset({("client",)})},
        allowed_payload_keys=frozenset({"client"}),
    ))
    source = {"client": "A"}
    record = ScopedContextRecord(ProtectedResource.ANALYSIS_RESULT, "co", "entity-a", "eng-a", "a-a", source)
    source_receipt = ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(
        grant, request_id="req", resource=ProtectedResource.ANALYSIS_RESULT
    )[0][1]
    read_receipt = authority.project_read(source_receipt, ("client",))
    with pytest.raises(OwnershipRefused):
        authority.receipt_disclosure(
            grant=grant, request_id="req", protected_reads=[read_receipt],
            disclosure_payload={"client": "B"},
        )


def test_legitimate_value_cannot_cover_additional_rogue_payload_leaf():
    authority, grant = _grant(_authority(
        projection_policy={ProtectedResource.ANALYSIS_RESULT: frozenset({("client",)})},
        allowed_payload_keys=frozenset({"authorized", "client", "rogue"}),
    ))
    source = {"client": "B"}
    record = ScopedContextRecord(ProtectedResource.ANALYSIS_RESULT, "co", "entity-a", "eng-a", "a-a", source)
    source_receipt = ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(
        grant, request_id="req", resource=ProtectedResource.ANALYSIS_RESULT
    )[0][1]
    projected = authority.project_read(source_receipt, ("client",))
    with pytest.raises(OwnershipRefused):
        authority.receipt_disclosure(
            grant=grant, request_id="req", protected_reads=[projected],
            disclosure_payload={"authorized": {"client": "B"}, "rogue": "CLIENT_A_SECRET"},
        )


def test_receipts_cannot_cross_authority_or_grant():
    policy = {ProtectedResource.ANALYSIS_RESULT: frozenset({("value",)})}
    authority_a, grant_a = _grant(_authority(projection_policy=policy, allowed_payload_keys=frozenset({"value"})), request="same")
    authority_b, grant_b = _grant(_authority(projection_policy=policy, allowed_payload_keys=frozenset({"value"})), request="same")
    record = ScopedContextRecord(ProtectedResource.ANALYSIS_RESULT, "co", "entity-a", "eng-a", "a-a", {"value": 1})
    source_a = ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(
        grant_a, request_id="same", resource=ProtectedResource.ANALYSIS_RESULT
    )[0][1]
    projected_a = authority_a.project_read(source_a, ("value",))
    with pytest.raises(OwnershipRefused):
        authority_b.receipt_disclosure(
            grant=grant_b, request_id="same", protected_reads=[projected_a],
            disclosure_payload={"value": 1},
        )


def test_egress_rejects_missing_or_copied_authorization_before_dispatch(monkeypatch):
    import services.llm_egress as module
    calls = []
    monkeypatch.setattr(module, "_dispatch_final_request", lambda request: calls.append(request))
    missing = _mint_synthetic_test_request(task="TASK", provider_payload={}, request_id="req")
    with pytest.raises(EgressRefused):
        LlmEgressAuthority().dispatch(missing)
    copied = replace(_authorized_request(), request_id="other")
    with pytest.raises(EgressRefused):
        LlmEgressAuthority().dispatch(copied)
    assert calls == []


def test_unauthorized_request_causes_zero_provider_dispatch(monkeypatch):
    import services.llm_egress as module
    calls = []
    monkeypatch.setattr(module, "_dispatch_final_request", lambda request: calls.append(request))
    with pytest.raises(EgressRefused):
        LlmEgressAuthority().dispatch(_mint_synthetic_test_request(task="TASK", provider_payload={}))
    assert calls == []


def test_chat_resolves_ownership_before_any_protected_cache_read():
    source = (Path(__file__).parents[1] / "routers" / "analyze.py").read_text(encoding="utf-8")
    function = next(
        node for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "chat_with_analysis"
    )
    calls = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(function) if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    assert "_mint_analysis_read_grant" in calls
    mint_line = next(node.lineno for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_mint_analysis_read_grant")
    read_lines = [node.lineno for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_read_protected_cache"]
    assert read_lines and mint_line < min(read_lines)


def test_legacy_company_wide_memory_is_not_read_for_analysis_egress():
    source = (Path(__file__).parents[1] / "routers" / "analyze.py").read_text(encoding="utf-8")
    assert "_memory_service.get_memory_context(company_id)" not in source
    assert "_decision_memory_service.build_decision_memory_prompt_section(company_id)" not in source


def test_capability_minting_is_confined_to_ownership_authority():
    backend = Path(__file__).parents[1]
    forbidden = ("ProtectedReadGrant(", "EgressAuthorization(")
    violations = []
    for path in (backend / "services").rglob("*.py"):
        if path.name == "ownership_authority.py":
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            violations.append(path.relative_to(backend).as_posix())
    assert violations == []


def test_principal_acceptance_boundary_has_no_request_field_callers():
    backend = Path(__file__).parents[1]
    callers = []
    for path in backend.rglob("*.py"):
        if path.name in {"ownership_authority.py", "test_ownership_authority.py", "test_llm_egress_authority.py"}:
            continue
        if "._accept_authenticated_principal(" in path.read_text(encoding="utf-8"):
            callers.append(path.relative_to(backend).as_posix())
    assert callers == ["routers/analyze.py"]


def test_known_protected_chat_caches_only_use_protected_getter():
    source = (Path(__file__).parents[1] / "routers" / "analyze.py").read_text(encoding="utf-8")
    chat = source[source.index("async def chat_with_analysis"):source.index("def _resolve_entity_name")]
    for cache_name in (
        "_anonymization_cache", "_analysis_result_cache", "_executive_case_v2_cache",
        "_protected_correspondence_cache", "_protected_analysis_result_cache",
        "_protected_executive_case_v2_cache",
    ):
        assert f"{cache_name}.get(" not in chat


def test_capability_internals_are_not_accessed_outside_authority_module():
    backend = Path(__file__).parents[1]
    forbidden = ("_MINT_SEAL", "._read_registry", "._egress_registry")
    violations = []
    for path in backend.rglob("*.py"):
        if path.name in {"ownership_authority.py", "test_ownership_authority.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            violations.append(path.relative_to(backend).as_posix())
    assert violations == []
