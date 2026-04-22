"""
base.py — Abstract base class for all Pepperyn data connectors.

Every connector must inherit from BaseConnector and implement fetch().
The return type is always FinancialDataPayload — the single format understood
by the LLM pipeline.

Usage pattern
-------------
    connector = SomeConnector(config)
    payload = connector.fetch()           # sync
    # or
    payload = await connector.afetch()    # async (optional override)

    result = await run_full_pipeline(payload, context, ...)
"""

from abc import ABC, abstractmethod
from typing import Any

from services.financial_normalizer import FinancialDataPayload


class BaseConnector(ABC):
    """
    Abstract base for all Pepperyn data connectors.

    Subclasses must implement fetch().
    They may optionally override afetch() for async sources (APIs, webhooks).
    """

    # Human-readable name shown in logs and the CRM
    connector_name: str = "base"

    @abstractmethod
    def fetch(self) -> FinancialDataPayload:
        """
        Pull data from the source and return a normalized FinancialDataPayload.
        Must be synchronous.  For async sources, run the event loop internally
        or override afetch() instead.
        """
        ...

    async def afetch(self) -> FinancialDataPayload:
        """
        Async variant of fetch().  Default implementation just calls fetch()
        in a thread pool.  Override for truly async sources (aiohttp, etc.).
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch)

    def validate(self, payload: FinancialDataPayload) -> None:
        """
        Basic sanity check on a payload before it reaches the LLM pipeline.
        Raises ValueError if the payload is clearly incomplete.
        Subclasses may override to add source-specific validation.
        """
        if not payload.get("source"):
            raise ValueError("FinancialDataPayload is missing 'source' field")
        if not payload.get("source_name"):
            raise ValueError("FinancialDataPayload is missing 'source_name' field")
        # A valid payload must have either sheets (tabular) or text_content (PDF/OCR)
        has_tabular = bool(payload.get("sheets") or payload.get("ledger_entries"))
        has_text    = bool(payload.get("text_content") or payload.get("tables"))
        if not has_tabular and not has_text:
            raise ValueError(
                "FinancialDataPayload contains no usable data "
                "(no sheets, ledger_entries, text_content, or tables)"
            )
