"""
file_connector.py — FileConnector
===================================
Wraps file_parser.parse_file() and returns a FinancialDataPayload.

This is the ACTIVE connector used today for user file uploads (Excel, CSV, PDF).
It is a thin adapter: all the heavy lifting (formula caching, LibreOffice fallback,
P&L detection, anomaly analysis) stays in services/file_parser.py.

Usage
-----
    connector = FileConnector(file_bytes=b"...", filename="P&L_2024.xlsx")
    payload = connector.fetch()
    result  = await run_full_pipeline(payload, context)
"""

from connectors.base import BaseConnector
from services.file_parser import parse_file
from services.financial_normalizer import FinancialDataPayload, wrap_file_parser_output


class FileConnector(BaseConnector):
    """
    Connector for user-uploaded files (Excel, CSV, PDF).

    Accepts raw file bytes + filename, delegates to file_parser,
    and wraps the result in a FinancialDataPayload envelope.
    """

    connector_name = "file"

    def __init__(self, file_bytes: bytes, filename: str) -> None:
        self._file_bytes = file_bytes
        self._filename = filename

    def fetch(self) -> FinancialDataPayload:
        """
        Parse the uploaded file and return a normalized FinancialDataPayload.

        Raises:
            ValueError  — unsupported format or corrupt file
            RuntimeError — unexpected parse error
        """
        raw = parse_file(self._file_bytes, self._filename)
        payload = wrap_file_parser_output(raw, self._filename)
        self.validate(payload)
        return payload
