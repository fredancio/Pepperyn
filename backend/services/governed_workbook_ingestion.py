"""Reusable local parsing/understanding, NOT data admission or provider dispatch.

Uses existing connector/quality/epistemic primitives. The caller must authorize
the source before invoking this service. Correspondence here is the inherited
local parser behavior, not a substitute for V33/V34 or a provider-safe projection.
"""
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from connectors import FileConnector
from services.data_quality_gate import validate_excel_before_analysis
from services.anonymization_service import anonymize_parsed_data
from services.v1_analysis_contract import UnderstandingResult, build_financial_understanding


class WorkbookIngestionRefused(ValueError):
    pass


@dataclass(frozen=True)
class WorkbookUnderstanding:
    source_sha256: str
    understanding: UnderstandingResult
    local_representation: Mapping[str, Any]


def ingest_governed_workbook(raw: bytes, filename: str) -> WorkbookUnderstanding:
    if not isinstance(raw, bytes) or not raw or len(raw) > 1_000_000 or not filename.lower().endswith('.xlsx'):
        raise WorkbookIngestionRefused('WORKBOOK_INPUT_REFUSED')
    try:
        gate = validate_excel_before_analysis(raw, filename)
        if not gate.can_analyze or gate.status not in {'ok', 'warning'}:
            raise WorkbookIngestionRefused('WORKBOOK_QUALITY_REFUSED')
        parsed = FileConnector(raw, filename).fetch()
        representation, _ = anonymize_parsed_data(parsed)
        understanding = build_financial_understanding(representation)
        return WorkbookUnderstanding(sha256(raw).hexdigest().upper(), understanding, representation)
    except WorkbookIngestionRefused:
        raise
    except Exception:
        raise WorkbookIngestionRefused('WORKBOOK_UNDERSTANDING_UNAVAILABLE') from None
