"""
connectors/
===========
One connector per data source.  Every connector must implement BaseConnector
and return a FinancialDataPayload.

Available connectors
--------------------
  FileConnector   — file upload (Excel, CSV, PDF)   ← ACTIVE
  ERPConnector    — ERP API (Sage, SAP, Odoo…)      ← STUB (future)
  BankConnector   — Open Banking / PSD2              ← STUB (future)
  OCRConnector    — scanned documents (PDF images)   ← STUB (future)
"""

from connectors.file_connector import FileConnector

__all__ = ["FileConnector"]
