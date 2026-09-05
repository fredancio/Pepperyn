"""Immutable, tenant/entity-bound persistence for V1 governed analyses."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from services.v1_analysis_contract import GovernedAnalysisEnvelope

SCHEMA_VERSION = "v1-governed-analysis-1"


class GovernedPersistenceRefused(RuntimeError):
    """Content-free fail-closed persistence refusal."""


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise GovernedPersistenceRefused("GOVERNED_SCOPE_INVALID") from exc


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GovernedPersistenceRefused("GOVERNED_ENVELOPE_INVALID") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _binding(*, analysis_id: str, company_id: str, entity_id: str, engagement_id: str, envelope_sha256: str,
             source_sha256: str) -> str:
    return _digest({
        "analysis_id": analysis_id, "company_id": company_id, "entity_id": entity_id,
        "engagement_id": engagement_id,
        "envelope_sha256": envelope_sha256, "source_representation_sha256": source_sha256,
        "schema_version": SCHEMA_VERSION,
    })


def _scope(analysis_id: str, company_id: str, entity_id: str) -> tuple[str, str, str]:
    return _uuid(analysis_id), _uuid(company_id), _uuid(entity_id)


def save_governed_analysis(
    supabase: Any, *, analysis_row: dict[str, Any], engagement_id: str,
    envelope: GovernedAnalysisEnvelope,
) -> None:
    """Create the analysis and immutable envelope in one database transaction."""

    analysis_id, company_id, entity_id = _scope(
        analysis_row.get("id"), analysis_row.get("company_id"), analysis_row.get("entity_id"),
    )
    engagement_id = _uuid(engagement_id)
    envelope = GovernedAnalysisEnvelope.model_validate(envelope)
    envelope_json = envelope.model_dump(mode="json")
    envelope_sha256 = _digest(envelope_json)
    source_sha256 = envelope.source_facts.source_representation_sha256
    try:
        normalized_analysis = dict(analysis_row)
        normalized_analysis.update({"id": analysis_id, "company_id": company_id, "entity_id": entity_id})
        envelope_row = {
            "analysis_id": analysis_id, "company_id": company_id, "entity_id": entity_id,
            "engagement_id": engagement_id,
            "envelope_json": envelope_json, "envelope_sha256": envelope_sha256,
            "binding_sha256": _binding(
                analysis_id=analysis_id, company_id=company_id, entity_id=entity_id,
                engagement_id=engagement_id,
                envelope_sha256=envelope_sha256, source_sha256=source_sha256,
            ),
            "source_representation_sha256": source_sha256,
            "envelope_schema_version": SCHEMA_VERSION,
        }
        supabase.rpc("persist_governed_analysis_v1", {
            "p_analysis": normalized_analysis, "p_envelope": envelope_row,
        }).execute()
    except Exception as exc:
        raise GovernedPersistenceRefused("GOVERNED_PERSISTENCE_FAILED") from exc


def load_governed_envelope(
    supabase: Any, *, analysis_id: str, company_id: str, entity_id: str, engagement_id: str,
) -> GovernedAnalysisEnvelope:
    """Load and cryptographically verify exactly one triple-scoped envelope."""

    analysis_id, company_id, entity_id = _scope(analysis_id, company_id, entity_id)
    engagement_id = _uuid(engagement_id)
    try:
        rows = (
            supabase.from_("governed_analysis_envelopes")
            .select("analysis_id,company_id,entity_id,engagement_id,envelope_json,envelope_sha256,binding_sha256,source_representation_sha256,envelope_schema_version")
            .eq("analysis_id", analysis_id).eq("company_id", company_id).eq("entity_id", entity_id).eq("engagement_id", engagement_id)
            .limit(2).execute()
        ).data or []
    except Exception as exc:
        raise GovernedPersistenceRefused("GOVERNED_PERSISTENCE_FAILED") from exc
    if len(rows) != 1:
        raise GovernedPersistenceRefused("GOVERNED_ANALYSIS_NOT_FOUND")
    row = rows[0]
    if row.get("envelope_schema_version") != SCHEMA_VERSION:
        raise GovernedPersistenceRefused("GOVERNED_VERSION_UNSUPPORTED")
    envelope_json = row.get("envelope_json")
    envelope_sha256 = _digest(envelope_json)
    source_sha256 = row.get("source_representation_sha256")
    expected_binding = _binding(
        analysis_id=analysis_id, company_id=company_id, entity_id=entity_id,
        engagement_id=engagement_id,
        envelope_sha256=envelope_sha256, source_sha256=source_sha256,
    )
    if (
        row.get("envelope_sha256") != envelope_sha256
        or row.get("binding_sha256") != expected_binding
    ):
        raise GovernedPersistenceRefused("GOVERNED_INTEGRITY_MISMATCH")
    try:
        envelope = GovernedAnalysisEnvelope.model_validate(envelope_json)
    except Exception as exc:
        raise GovernedPersistenceRefused("GOVERNED_ENVELOPE_INVALID") from exc
    if envelope.source_facts.source_representation_sha256 != source_sha256:
        raise GovernedPersistenceRefused("GOVERNED_SOURCE_MISMATCH")
    return envelope
