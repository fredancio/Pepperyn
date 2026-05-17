from __future__ import annotations
import pandas as pd
from pathlib import Path

REQUIRED_SHEETS = [
    "companies", "periods", "customers", "products", "suppliers", "cost_centers",
    "sales_invoices", "purchase_invoices", "fixed_costs", "budget_lines",
    "cash_movements", "gl_entries"
]

class FinanceDataStore:
    """Charge et normalise les données Excel du POC Pepperyn."""
    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Fichier Excel introuvable: {self.excel_path}")
        self.tables = self._load_workbook()
        self._normalize()

    def _load_workbook(self) -> dict[str, pd.DataFrame]:
        xls = pd.ExcelFile(self.excel_path)
        missing = [s for s in REQUIRED_SHEETS if s not in xls.sheet_names]
        if missing:
            raise ValueError(f"Onglets Excel manquants: {missing}")
        return {sheet: pd.read_excel(self.excel_path, sheet_name=sheet) for sheet in REQUIRED_SHEETS}

    def _normalize(self) -> None:
        for name, df in self.tables.items():
            df.columns = [str(c).strip().lower() for c in df.columns]
            self.tables[name] = df

        for sheet in ["sales_invoices", "purchase_invoices", "fixed_costs", "budget_lines", "cash_movements", "gl_entries"]:
            if "period_id" in self.tables[sheet].columns:
                self.tables[sheet]["period_id"] = self.tables[sheet]["period_id"].astype(str)

        numeric_cols = {
            "sales_invoices": ["quantity", "unit_price", "discount", "net_revenue"],
            "purchase_invoices": ["quantity", "unit_cost", "total_cost"],
            "fixed_costs": ["amount"],
            "budget_lines": ["budget_amount", "budget_quantity", "budget_margin"],
            "cash_movements": ["cash_in", "cash_out"],
            "gl_entries": ["debit", "credit", "amount"],
        }
        for sheet, cols in numeric_cols.items():
            for col in cols:
                if col in self.tables[sheet].columns:
                    self.tables[sheet][col] = pd.to_numeric(self.tables[sheet][col], errors="coerce").fillna(0.0)

    def table(self, name: str) -> pd.DataFrame:
        return self.tables[name].copy()
