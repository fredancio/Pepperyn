"""Falsifications for quarantined provider return and terminal rehydration."""

from dataclasses import replace

import pytest

import services.llm_egress as egress
from services.governed_minimal_projection import (
    TASK, MinimalProjectionRefused, _canonical_bytes,
    compose_financial_change_v1, projection_binding_hash,
)
from services.governed_provider_response import (
    AuthorizedTerminalOutput, ProviderResponseRefused,
    quarantine_and_validate_mock_response, rehydrate_for_authorized_terminal,
)
from services.ownership_authority import (
    InMemoryOwnershipRepository, InMemoryScopedContextRepository,
    OwnershipAuthority, OwnershipRecord, ProtectedContextReader,
    ProtectedResource, ScopedContextRecord,
)
from services.pseudonymous_correspondence import PseudonymousReference
from tests.test_governed_minimal_projection import (
    ANALYSIS, COMPANY, ENGAGEMENT, ENTITY, fixture,
)


def _coverage(value, prefix=()):
    keys = set()
    leaves = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = prefix + (key,)
            keys.add(path)
            child_keys, child_leaves = _coverage(nested, path)
            keys.update(child_keys); leaves.extend(child_leaves)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            child_keys, child_leaves = _coverage(nested, prefix + (index,))
            keys.update(child_keys); leaves.extend(child_leaves)
    else:
        leaves.append(prefix)
    return keys, leaves


def _mock_response(projection):
    return {
        "schema": "FINANCIAL_CHANGE_RESPONSE_V1",
        "subject": projection.payload["subject"],
        "interpretations": [
            {"metric": row["metric"], "direction": row["direction"],
             "assessment": "MATERIAL_CHANGE"}
            for row in projection.payload["metrics"]
        ],
    }


def _run(raw_mutator=None):
    registry, reference, scope, _, _, facts = fixture()
    # Compose with a fresh source authority because the fixture's receipts are consumed once.
    registry2, reference2, scope2, source_authority, source_grant, facts2 = fixture()
    projection = compose_financial_change_v1(
        registry=registry2, correspondence_reference=reference2,
        correspondence_scope=scope2, ownership_authority=source_authority,
        read_grant=source_grant, request_id="request", facts=facts2,
    )
    payload = projection.payload
    allowed, leaves = _coverage(payload)
    repository = InMemoryOwnershipRepository([
        OwnershipRecord(ANALYSIS, COMPANY, ENTITY, ENGAGEMENT, COMPANY, ENTITY)
    ])
    authority = OwnershipAuthority(
        repository, projection_policy={ProtectedResource.ANALYSIS_RESULT: frozenset(leaves)},
        allowed_payload_keys=frozenset(allowed),
    )
    principal = authority._accept_authenticated_principal("principal", COMPANY)
    grant = authority.resolve_and_mint_read_grant(
        principal=principal, analysis_id=ANALYSIS, request_id="request",
        resources=[ProtectedResource.ANALYSIS_RESULT],
    )
    record = ScopedContextRecord(
        ProtectedResource.ANALYSIS_RESULT, COMPANY, ENTITY, ENGAGEMENT, ANALYSIS, payload)
    whole = ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(
        grant, request_id="request", resource=ProtectedResource.ANALYSIS_RESULT)[0][1]
    reads = {path: authority.project_read(whole, path) for path in leaves}
    disclosure = authority.receipt_disclosure(
        grant=grant, request_id="request", protected_reads=reads,
        disclosure_payload=payload,
    )
    outbound = authority.mint_egress_authorization(
        grant=grant, receipt=disclosure, task=TASK)
    raw = _mock_response(projection)
    if raw_mutator:
        raw = raw_mutator(raw, projection)
    original = egress._dispatch_final_request
    egress._dispatch_final_request = lambda frozen: raw
    try:
        result = egress.LlmEgressAuthority().dispatch(
            egress._mint_synthetic_test_request(
                task=TASK, provider_payload=payload, request_id="request",
                egress_authorization=outbound, governed_projection=projection,
            ))
    finally:
        egress._dispatch_final_request = original
    return registry2, reference2, scope2, authority, principal, projection, result


def _validated(raw_mutator=None):
    context = _run(raw_mutator)
    *_, projection, result = context
    validated = quarantine_and_validate_mock_response(result=result, projection=projection)
    return (*context[:-2], projection, validated)


def _terminal(context, *, reference=None, authorization=None):
    registry, original_reference, scope, authority, principal, projection, validated = context
    if authorization is None:
        grant = authority.resolve_and_mint_read_grant(
            principal=principal, analysis_id=ANALYSIS, request_id="request",
            resources=[ProtectedResource.CORRESPONDENCE],
        )
        authorization = authority.mint_rehydration_authorization(
            grant=grant, request_id="request", task=TASK,
            projection_binding_hash=projection_binding_hash(projection),
            correspondence_id=projection.lineage.correspondence_id,
        )
    return rehydrate_for_authorized_terminal(
        validated=validated, registry=registry,
        reference=reference or original_reference, authorization=authorization)


def test_mock_response_is_quarantined_noncanonical_and_exactly_bound():
    context = _validated(); validated = context[-1]; projection = context[-2]
    assert validated.epistemic_state == "PROVIDER_INFERENCE_NOT_CANONICAL"
    assert validated.projection_binding_hash == projection_binding_hash(projection)
    assert validated.projection_payload_hash == projection.payload_hash
    assert validated.scope.analysis_id == ANALYSIS


def test_authorized_local_rehydration_is_terminal_only():
    context = _validated(); terminal = _terminal(context)
    rendered = terminal.render_terminal()
    assert isinstance(terminal, AuthorizedTerminalOutput)
    assert rendered["subject"] == "V33 SYNTHETIC COUNTERPARTY"
    with pytest.raises(egress.EgressRefused) as refused:
        egress.reject_untrusted_provider_input(terminal)
    assert refused.value.code is egress.EgressRefusalCode.IDENTITY_FORBIDDEN
    with pytest.raises(egress.EgressRefused):
        egress.reject_untrusted_provider_input({"nested": terminal})
    with pytest.raises(egress.EgressRefused):
        egress.reject_untrusted_provider_input(rendered)
    with pytest.raises(MinimalProjectionRefused) as refused_projection:
        _canonical_bytes({"nested": terminal})
    assert str(refused_projection.value) == "REIDENTIFIED_TERMINAL_ONLY"
    with pytest.raises(MinimalProjectionRefused):
        _canonical_bytes(rendered)


@pytest.mark.parametrize("mutator", [
    lambda raw, p: {**raw, "subject": "COUNTERPARTY-AAAAAAAAAAAAAAAA"},
    lambda raw, p: {**raw, "interpretations": [{**raw["interpretations"][0], "metric": "CASH"}]},
    lambda raw, p: {**raw, "interpretations": [{**raw["interpretations"][0], "direction": "UP" if raw["interpretations"][0]["direction"] != "UP" else "DOWN"}]},
    lambda raw, p: {**raw, "free_text": "identity context"},
    lambda raw, p: {**raw, "interpretations": raw["interpretations"][:-1]},
])
def test_substitution_unknown_reference_and_free_form_response_fail_closed(mutator):
    with pytest.raises(ProviderResponseRefused):
        _validated(mutator)


def test_response_receipt_and_validated_inference_are_single_use():
    context = _run(); *_, projection, result = context
    quarantine_and_validate_mock_response(result=result, projection=projection)
    with pytest.raises(ProviderResponseRefused):
        quarantine_and_validate_mock_response(result=result, projection=projection)
    context = _validated(); _terminal(context)
    with pytest.raises(ProviderResponseRefused):
        _terminal(context)


def test_forged_egress_result_is_refused():
    context = _run(); *_, projection, result = context
    forged = replace(result, attempt_count=2)
    with pytest.raises(ProviderResponseRefused):
        quarantine_and_validate_mock_response(result=forged, projection=projection)


def test_provider_response_mutation_after_dispatch_is_refused():
    context = _run(); *_, projection, result = context
    result.content.raw_response["subject"] = "COUNTERPARTY-AAAAAAAAAAAAAAAA"
    with pytest.raises(ProviderResponseRefused):
        quarantine_and_validate_mock_response(result=result, projection=projection)


def test_unknown_pseudonym_handle_and_foreign_authority_fail_closed():
    context = _validated()
    unknown = PseudonymousReference("COUNTERPARTY-AAAAAAAAAAAAAAAA", context[1].handle)
    with pytest.raises(ProviderResponseRefused):
        _terminal(context, reference=unknown)

    context = _validated()
    registry, reference, scope, authority, principal, projection, validated = context
    foreign_repo = InMemoryOwnershipRepository([
        OwnershipRecord(ANALYSIS, "22222222-2222-4222-8222-222222222222",
                        ENTITY, ENGAGEMENT, "22222222-2222-4222-8222-222222222222", ENTITY)
    ])
    foreign = OwnershipAuthority(foreign_repo)
    foreign_principal = foreign._accept_authenticated_principal(
        "foreign", "22222222-2222-4222-8222-222222222222")
    foreign_grant = foreign.resolve_and_mint_read_grant(
        principal=foreign_principal, analysis_id=ANALYSIS, request_id="request",
        resources=[ProtectedResource.CORRESPONDENCE])
    foreign_auth = foreign.mint_rehydration_authorization(
        grant=foreign_grant, request_id="request", task=TASK,
        projection_binding_hash=projection_binding_hash(projection),
        correspondence_id=projection.lineage.correspondence_id)
    with pytest.raises(ProviderResponseRefused):
        _terminal(context, authorization=foreign_auth)
