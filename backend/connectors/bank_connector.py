"""
bank_connector.py — BankConnector  [STUB — not yet active]
==========================================================
Future connector for bank feeds via Open Banking (PSD2 / DSP2 in Europe)
or direct CSV exports from banking portals.

Use cases
---------
- Cash flow analysis from real bank transactions
- Reconciliation with ERP / accounting data
- Automatic categorization of transactions (payroll, suppliers, VAT, etc.)
- Detect unusual payment patterns or cash burn acceleration

Two integration paths
---------------------
A. PSD2 / Open Banking API (e.g. Bridge by Bankin', Plaid, Tink, Swan)
   — Requires user consent (OAuth2 redirect)
   — Returns structured JSON: IBAN, transactions, balances
   — Most accurate, real-time

B. CSV export from bank portal (Société Générale, BNP, CIC, …)
   — User downloads + uploads the CSV manually
   — Simpler to implement, no OAuth needed
   — Handle with FileConnector + a bank-format normalization step

Implementation checklist (when the time comes)
-----------------------------------------------
1.  Choose provider: Bridge API is the most common for French fintechs.
2.  Add OAuth2 redirect flow in the frontend (user grants bank access).
3.  Fetch transactions for the requested period via provider API.
4.  Normalize:
      [
        { "date": "2024-01-15", "label": "VIREMENT SAGE FRANCE",
          "amount": -4820.00, "category": "software", "iban_dest": "FR76…" },
        …
      ]
5.  Build FinancialDataPayload with source="bank", ledger_entries=transactions.
6.  Add BankConnector to connectors/__init__.py.
"""

from connectors.base import BaseConnector
from services.financial_normalizer import FinancialDataPayload


class BankConnector(BaseConnector):
    """
    [STUB] Connector for bank transaction feeds.

    Not yet implemented.  Raises NotImplementedError on fetch().
    """

    connector_name = "bank"

    def __init__(self, provider: str, access_token: str, iban: str) -> None:
        """
        Args:
            provider     : "bridge" | "plaid" | "tink" | "csv_upload"
            access_token : provider OAuth2 access token
            iban         : bank account to fetch (FR76…)
        """
        self._provider     = provider
        self._access_token = access_token
        self._iban         = iban

    def fetch(self) -> FinancialDataPayload:
        raise NotImplementedError(
            f"BankConnector ({self._provider}) is not yet implemented. "
            "See the implementation checklist in this file."
        )
