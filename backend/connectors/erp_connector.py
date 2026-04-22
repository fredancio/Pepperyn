"""
erp_connector.py — ERPConnector  [STUB — not yet active]
=========================================================
Future connector for ERP systems (Sage, SAP Business One, Odoo, QuickBooks…).

When to activate
----------------
When Pepperyn supports direct ERP integration (v2 roadmap), implement the
methods below.  The analyze endpoint will then accept an ERP source without
any changes to the LLM pipeline or export services.

How ERP data differs from file uploads
---------------------------------------
- Data arrives as structured JSON/XML via REST or SOAP API
- No formulas — the ERP database stores computed values directly
- Account codes follow a chart of accounts (PCG in France, GAAP in US, IFRS…)
- Periods are explicit objects, not column headers
- Some ERPs provide drill-down (e.g. get the invoices behind a COGS line)

Implementation checklist (when the time comes)
-----------------------------------------------
1.  Choose the API method:
      a. OAuth2 / API key — most modern ERPs (Sage Business Cloud, QuickBooks Online)
      b. Direct DB export — Sage 100, older on-premise systems
      c. Middleware (e.g. Zapier, Make, Pennylane API) — easiest to start

2.  Map ERP account codes to Pepperyn categories:
      revenue_keywords  →  PCG 70x, GAAP 4xx, etc.
      cost_keywords     →  PCG 60x-65x
      payroll           →  PCG 641
      …

3.  Build ledger_entries list:
      [
        { "code": "706000", "label": "Prestations de services",
          "2024-01": 38500, "2024-02": 42000, … },
        …
      ]

4.  Call wrap_erp_output() (implement in financial_normalizer.py) to produce
    a FinancialDataPayload with source="erp".

5.  Add ERPConnector to connectors/__init__.py.

6.  In analyze.py, detect the source type and instantiate the right connector:
      if request.source == "erp":
          connector = ERPConnector(config=request.erp_config)
      else:
          connector = FileConnector(file_bytes, filename)
      payload = connector.fetch()
"""

from connectors.base import BaseConnector
from services.financial_normalizer import FinancialDataPayload


class ERPConnector(BaseConnector):
    """
    [STUB] Connector for ERP systems.

    Not yet implemented.  Raises NotImplementedError on fetch().
    """

    connector_name = "erp"

    def __init__(self, erp_type: str, credentials: dict, company_id: str) -> None:
        """
        Args:
            erp_type    : "sage" | "sap" | "odoo" | "quickbooks" | "pennylane"
            credentials : API key, OAuth tokens, DB credentials, etc.
            company_id  : Pepperyn company UUID (for data isolation)
        """
        self._erp_type   = erp_type
        self._credentials = credentials
        self._company_id  = company_id

    def fetch(self) -> FinancialDataPayload:
        raise NotImplementedError(
            f"ERPConnector ({self._erp_type}) is not yet implemented. "
            "See the implementation checklist in this file."
        )

    # ── Future helper methods (implement when activating) ─────────────────────

    def _get_trial_balance(self, year: int, month_from: int, month_to: int) -> list:
        """Fetch trial balance (balance des comptes) for the given period."""
        raise NotImplementedError

    def _get_income_statement(self, year: int) -> list:
        """Fetch P&L / Compte de résultat."""
        raise NotImplementedError

    def _get_balance_sheet(self, year: int) -> list:
        """Fetch balance sheet / Bilan."""
        raise NotImplementedError

    def _map_account_to_category(self, account_code: str) -> str:
        """
        Map an ERP account code to a Pepperyn financial category.
        Returns one of: "revenue" | "cost" | "payroll" | "margin" | "other"
        """
        raise NotImplementedError
