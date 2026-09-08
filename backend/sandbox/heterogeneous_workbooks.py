"""Closed registry and local inspection for synthetic V1 workbook rehearsals."""

from __future__ import annotations

import hashlib
from typing import Any

from connectors import FileConnector
from services.anonymization_service import anonymize_parsed_data
from services.data_quality_gate import validate_excel_before_analysis
from services.v1_analysis_contract import build_financial_understanding

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


def inspect_registered_workbook(raw: bytes, filename: str) -> dict[str, Any]:
    """Inspect an exact registered fixture locally; never build or dispatch a provider request."""

    digest = hashlib.sha256(raw).hexdigest().upper()
    registered_name = REGISTERED_WORKBOOKS.get(digest)
    if registered_name is None or filename != registered_name:
        raise SandboxRefused("UNREGISTERED_SYNTHETIC_WORKBOOK")

    gate = validate_excel_before_analysis(raw, filename)
    if not gate.can_analyze or gate.status not in {"ok", "warning"}:
        raise SandboxRefused("SYNTHETIC_WORKBOOK_QUALITY_GATE_REFUSED")
    parsed = FileConnector(raw, filename).fetch()
    anonymized, _ = anonymize_parsed_data(parsed)
    understanding = build_financial_understanding(anonymized)
    return {
        "filename": registered_name,
        "source_sha256": digest,
        "status": understanding.status,
        "current_period": understanding.current_period,
        "facts": [fact.model_dump(mode="json") for fact in understanding.facts],
        "unknowns": list(understanding.unknowns),
        "provider_dispatch": "CLOSED",
    }
