"""Hash-pinned raw-workbook ingestion evidence for the synthetic M1C gate."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from connectors import FileConnector
from services.anonymization_service import anonymize_parsed_data
from services.data_quality_gate import validate_excel_before_analysis
from services.llm_egress import EgressRefusalCode, EgressRefused

from sandbox.synthetic_product import SandboxRefused


OPTILUX_RAW_WORKBOOK_FIXTURE_ID = "OPTILUX_M1C_RAW_V1"
OPTILUX_RAW_WORKBOOK_FILENAME = "optilux_m1c_raw_workbook.xlsx"
OPTILUX_RAW_WORKBOOK_SHA256 = "D534C91B9B2AD260526FE029C5DC56F022205EE0BD6C8F9EA0648A5BA1EF8E8D"
_RAW_WORKBOOK = (
    Path(__file__).parents[1] / "tests" / "golden" / "fixtures" / OPTILUX_RAW_WORKBOOK_FILENAME
)


@dataclass(frozen=True)
class RawWorkbookFixture:
    fixture_id: str
    filename: str
    sha256: str
    raw_bytes: bytes


@dataclass(frozen=True)
class RawIngestionEvidence:
    fixture_id: str
    source_sha256: str
    quality_gate: Mapping[str, Any]
    parsed_payload: Mapping[str, Any]
    anonymized_payload: Mapping[str, Any]
    anonymization_summary: Mapping[str, int]
    financial_representation_sha256: str
    provider_boundary_refusal: str


def load_registered_raw_workbook() -> RawWorkbookFixture:
    """Load only the byte-exact registered synthetic workbook."""

    raw_bytes = _RAW_WORKBOOK.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest().upper()
    if digest != OPTILUX_RAW_WORKBOOK_SHA256:
        raise SandboxRefused("REGISTERED_RAW_WORKBOOK_HASH_MISMATCH")
    return RawWorkbookFixture(
        fixture_id=OPTILUX_RAW_WORKBOOK_FIXTURE_ID,
        filename=OPTILUX_RAW_WORKBOOK_FILENAME,
        sha256=digest,
        raw_bytes=raw_bytes,
    )


def build_registered_raw_financial_input() -> RawIngestionEvidence:
    """Exercise real local ingestion and stop at the closed provider boundary."""

    fixture = load_registered_raw_workbook()
    gate = validate_excel_before_analysis(fixture.raw_bytes, fixture.filename)
    if (
        not gate.can_analyze
        or gate.status not in {"ok", "warning"}
        or gate.document_format != "structural_pl"
        or gate.blocking_reason is not None
    ):
        raise SandboxRefused("RAW_WORKBOOK_QUALITY_GATE_REFUSED")

    parsed_payload = FileConnector(fixture.raw_bytes, fixture.filename).fetch()
    anonymized_payload, correspondence = anonymize_parsed_data(parsed_payload)
    serialized = json.dumps(
        anonymized_payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    # Execute the actual first cognitive stage. Slice 1 must refuse before the
    # transport boundary because this registered workbook has no real-data
    # admission or ownership authorization.
    from services.llm_service import classify_document
    try:
        asyncio.run(classify_document(anonymized_payload))
    except EgressRefused as exc:
        if exc.code is not EgressRefusalCode.REAL_DATA_ADMISSION_CLOSED:
            raise SandboxRefused("UNEXPECTED_PROVIDER_PIPELINE_REFUSAL") from exc
        provider_boundary_refusal = exc.code.value
    else:  # pragma: no cover - a security invariant guards this branch
        raise SandboxRefused("PROVIDER_PIPELINE_BOUNDARY_UNEXPECTEDLY_OPEN")

    return RawIngestionEvidence(
        fixture_id=fixture.fixture_id,
        source_sha256=fixture.sha256,
        quality_gate=gate.to_report_section(),
        parsed_payload=parsed_payload,
        anonymized_payload=anonymized_payload,
        anonymization_summary=correspondence.to_summary(),
        financial_representation_sha256=hashlib.sha256(serialized).hexdigest().upper(),
        provider_boundary_refusal=provider_boundary_refusal,
    )
