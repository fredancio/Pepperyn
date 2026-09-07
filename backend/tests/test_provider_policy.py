from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json

import pytest

from services.provider_policy import (
    PROVIDER_POLICY_VERSION,
    ProviderPolicyRefused,
    _mint_synthetic_test_provider_authorization,
    authorize_configured_provider_request,
    verify_provider_policy_authorization,
)


BODY = {"model": "gpt-5", "store": False, "input": "synthetic"}


def _configure(monkeypatch, tmp_path):
    values = {
        "PEPPERYN_PROVIDER_APPROVED": "1",
        "PEPPERYN_PROVIDER_POLICY_VERSION": PROVIDER_POLICY_VERSION,
        "PEPPERYN_PROVIDER": "openai",
        "PEPPERYN_PROVIDER_PROJECT_ID": "project-non-secret-id",
        "PEPPERYN_PROVIDER_BASE_URL": "https://eu.api.openai.com/v1",
        "PEPPERYN_PROVIDER_ENDPOINT": "/responses",
        "PEPPERYN_PROVIDER_MODEL": "gpt-5",
        "PEPPERYN_PROVIDER_REGION": "europe",
        "PEPPERYN_PROVIDER_RETENTION": "zero_data_retention",
        "PEPPERYN_PROVIDER_DATA_SHARING": "disabled",
        "PEPPERYN_PROVIDER_DPA_STATUS": "effective",
        "PEPPERYN_PROVIDER_EVIDENCE_VERIFIED_AT": "2027-01-01T00:00:00Z",
        "PEPPERYN_PROVIDER_EVIDENCE_EXPIRES_AT": "2027-03-01T00:00:00Z",
    }
    manifest = {
        "policy_version": values["PEPPERYN_PROVIDER_POLICY_VERSION"],
        "provider": values["PEPPERYN_PROVIDER"],
        "project_id": values["PEPPERYN_PROVIDER_PROJECT_ID"],
        "base_url": values["PEPPERYN_PROVIDER_BASE_URL"],
        "endpoint": values["PEPPERYN_PROVIDER_ENDPOINT"],
        "model": values["PEPPERYN_PROVIDER_MODEL"],
        "region": values["PEPPERYN_PROVIDER_REGION"],
        "retention": values["PEPPERYN_PROVIDER_RETENTION"],
        "data_sharing": values["PEPPERYN_PROVIDER_DATA_SHARING"],
        "dpa_status": values["PEPPERYN_PROVIDER_DPA_STATUS"],
        "verified_at": values["PEPPERYN_PROVIDER_EVIDENCE_VERIFIED_AT"],
        "expires_at": values["PEPPERYN_PROVIDER_EVIDENCE_EXPIRES_AT"],
    }
    evidence = tmp_path / "provider-evidence.json"
    raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    evidence.write_bytes(raw)
    values["PEPPERYN_PROVIDER_EVIDENCE_PATH"] = str(evidence)
    values["PEPPERYN_PROVIDER_EVIDENCE_SHA256"] = hashlib.sha256(raw).hexdigest()
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_complete_effective_configuration_authorizes_exact_request(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    authorization = authorize_configured_provider_request(
        task="FINANCIAL_ANALYSIS", request_body=BODY, now=1_800_000_000,
    )
    assert authorization.provider == "openai"
    assert authorization.base_url == "https://eu.api.openai.com/v1"
    assert authorization.retention == "zero_data_retention"
    assert authorization.region == "europe"
    assert authorization.model == "gpt-5"
    assert verify_provider_policy_authorization(
        authorization, task="FINANCIAL_ANALYSIS",
        request_hash=authorization.request_hash, now=1_800_000_000,
    ) is authorization


@pytest.mark.parametrize("missing", [
    "PEPPERYN_PROVIDER_PROJECT_ID", "PEPPERYN_PROVIDER_EVIDENCE_SHA256",
    "PEPPERYN_PROVIDER_RETENTION", "PEPPERYN_PROVIDER_REGION",
])
def test_missing_effective_evidence_fails_closed(monkeypatch, tmp_path, missing):
    _configure(monkeypatch, tmp_path)
    monkeypatch.delenv(missing)
    with pytest.raises(ProviderPolicyRefused, match="CONFIGURATION_INCOMPLETE"):
        authorize_configured_provider_request(task="FINANCIAL_ANALYSIS", request_body=BODY)


@pytest.mark.parametrize(("key", "value"), [
    ("PEPPERYN_PROVIDER_APPROVED", "0"),
    ("PEPPERYN_PROVIDER_REGION", "us"),
    ("PEPPERYN_PROVIDER_RETENTION", "standard"),
    ("PEPPERYN_PROVIDER_BASE_URL", "https://api.openai.com/v1"),
    ("PEPPERYN_PROVIDER_MODEL", "unapproved-model"),
    ("PEPPERYN_PROVIDER_DATA_SHARING", "enabled"),
    ("PEPPERYN_PROVIDER_DPA_STATUS", "pending"),
])
def test_unapproved_policy_dimension_fails_closed(monkeypatch, tmp_path, key, value):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv(key, value)
    with pytest.raises(ProviderPolicyRefused):
        authorize_configured_provider_request(task="FINANCIAL_ANALYSIS", request_body=BODY)


def test_request_store_model_task_and_expiry_are_bound(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    for task, body in (
        ("UNAPPROVED_TASK", BODY),
        ("FINANCIAL_ANALYSIS", {**BODY, "store": True}),
        ("FINANCIAL_ANALYSIS", {**BODY, "model": "other"}),
    ):
        with pytest.raises(ProviderPolicyRefused):
            authorize_configured_provider_request(task=task, request_body=body)
    with pytest.raises(ProviderPolicyRefused, match="EVIDENCE_EXPIRED"):
        authorize_configured_provider_request(
            task="FINANCIAL_ANALYSIS", request_body=BODY, now=1_900_000_000,
        )


def test_evidence_file_hash_and_policy_scope_are_verified(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    evidence = tmp_path / "provider-evidence.json"
    evidence.write_bytes(evidence.read_bytes() + b" ")
    with pytest.raises(ProviderPolicyRefused, match="INVALID_EVIDENCE"):
        authorize_configured_provider_request(task="FINANCIAL_ANALYSIS", request_body=BODY)

    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv("PEPPERYN_PROVIDER_PROJECT_ID", "different-project")
    with pytest.raises(ProviderPolicyRefused, match="EVIDENCE_SCOPE_MISMATCH"):
        authorize_configured_provider_request(task="FINANCIAL_ANALYSIS", request_body=BODY)


def test_authorization_cannot_be_reused_for_another_task_or_body():
    authorization = _mint_synthetic_test_provider_authorization(
        task="FINANCIAL_ANALYSIS", request_body=BODY,
    )
    with pytest.raises(ProviderPolicyRefused, match="MISMATCH"):
        verify_provider_policy_authorization(
            authorization, task="FOUNDER_REVIEW", request_hash=authorization.request_hash,
        )
    with pytest.raises(ProviderPolicyRefused, match="MISMATCH"):
        verify_provider_policy_authorization(
            authorization, task="FINANCIAL_ANALYSIS", request_hash="f" * 64,
        )
    with pytest.raises(ProviderPolicyRefused):
        verify_provider_policy_authorization(
            replace(authorization, _seal=object()), task="FINANCIAL_ANALYSIS",
            request_hash=authorization.request_hash,
        )


@pytest.mark.parametrize(("field", "value"), [
    ("provider", "evil"), ("project_id", "other-project"),
    ("base_url", "https://evil.invalid/v1"), ("endpoint", "/other"),
    ("model", "other"), ("region", "us"), ("retention", "standard"),
    ("evidence_sha256", "f" * 64), ("expires_at", 4_102_444_900.0),
])
def test_every_authorized_policy_dimension_is_issuer_bound(field, value):
    authorization = _mint_synthetic_test_provider_authorization(
        task="FINANCIAL_ANALYSIS", request_body=BODY,
    )
    with pytest.raises(ProviderPolicyRefused):
        verify_provider_policy_authorization(
            replace(authorization, **{field: value}), task="FINANCIAL_ANALYSIS",
            request_hash=authorization.request_hash,
        )


def test_authorization_holder_has_no_mint_capable_issuer():
    authorization = _mint_synthetic_test_provider_authorization(
        task="FINANCIAL_ANALYSIS", request_body=BODY,
    )
    assert isinstance(authorization._issuer_kind, str)
    assert not hasattr(authorization._issuer_kind, "mint")
