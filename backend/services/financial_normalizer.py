"""
financial_normalizer.py
=======================
Defines FinancialDataPayload — the single normalized format that all data sources
(file upload, ERP, bank feed, OCR) must produce before reaching Claude.

Why this exists
---------------
Claude's analysis pipeline (llm_service.run_full_pipeline) should never know
*where* the data came from.  Whether a user uploads an Excel file, Pepperyn
pulls from Sage via API, or a bank sends a PSD2 feed — the LLM always receives
the same structure.

Adding a new source = create a new connector in connectors/ that returns a
FinancialDataPayload.  Zero changes required anywhere else.

FinancialDataPayload structure
------------------------------
All fields that were previously produced by file_parser.py are preserved so
that the existing LLM prompt builder, Excel export, and API response code
continue to work without modification.  Three new top-level keys are added:

  source           — origin of the data ("file", "erp", "bank", "ocr")
  source_name      — human-readable label (filename, ERP name, bank name…)
  connector_version — semver string; increment when the payload schema changes
  metadata         — connector-specific extras (never sent to Claude)

Backward compatibility
----------------------
FinancialDataPayload is a plain TypedDict (dict subclass).  All existing code
that reads parsed_data["sheets"], parsed_data["filename"], etc. continues to
work unchanged — TypedDict is purely a type hint, not a runtime wrapper.
"""

from typing import Any, Optional
try:
    from typing import TypedDict, NotRequired
except ImportError:
    # Python 3.10 fallback
    from typing_extensions import TypedDict, NotRequired


# ── Payload definition ────────────────────────────────────────────────────────

class FinancialDataPayload(TypedDict):
    """
    Universal financial data payload consumed by the LLM pipeline.

    Source-agnostic fields (always present):
    """
    # ── Origin metadata (new) ─────────────────────────────────────────────────
    source: str                      # "file" | "erp" | "bank" | "ocr"
    source_name: str                 # filename, ERP name, bank name, etc.
    connector_version: str           # "1.0" — bump when schema changes

    # ── File-origin fields (set by FileConnector / file_parser) ──────────────
    filename: NotRequired[str]
    format: NotRequired[str]         # "excel" | "csv" | "pdf"
    sheets_count: NotRequired[int]
    sheets: NotRequired[list]        # list of sheet summary dicts
    total_rows: NotRequired[int]

    # ── PDF-specific fields ───────────────────────────────────────────────────
    pages: NotRequired[int]
    text_content: NotRequired[str]
    tables: NotRequired[list]

    # ── ERP / bank fields (set by future connectors) ─────────────────────────
    periods: NotRequired[list]       # e.g. ["2024-01", "2024-02", …]
    ledger_entries: NotRequired[list]  # normalized accounting lines
    account_plan: NotRequired[str]   # "PCG" | "IFRS" | "GAAP" | …

    # ── Connector-specific extras (NOT forwarded to Claude) ──────────────────
    metadata: NotRequired[dict]


# ── Helper ────────────────────────────────────────────────────────────────────

def wrap_file_parser_output(
    parsed: dict[str, Any],
    filename: str,
) -> FinancialDataPayload:
    """
    Wrap the dict produced by file_parser.parse_file() into a
    FinancialDataPayload.  All existing keys are preserved; the three new
    origin keys are injected.

    This is the only place that bridges the old world (file_parser) and the
    new world (FinancialDataPayload).  Future connectors build the payload
    directly without going through file_parser.
    """
    payload: FinancialDataPayload = {
        # New envelope fields
        "source": "file",
        "source_name": filename,
        "connector_version": "1.0",
        # Pass-through everything file_parser produced
        **parsed,
        # Connector-specific extras (none for file uploads)
        "metadata": {
            "original_filename": filename,
        },
    }
    return payload
