from pathlib import Path
import pandas as pd
from .schemas import CanonicalDataset, ImportResult
from .mapping import detect_sheet_table, suggest_column_mapping
from .validation import validate_dataset


def _read_excel_sheets(path: str) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path)
    sheets = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        # drop fully empty rows/cols
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            sheets[sheet] = df
    return sheets


def _canonicalize(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    out = pd.DataFrame()
    for canonical_field, original_col in mapping.items():
        out[canonical_field] = df[original_col]
    for col in ["amount", "quantity", "unit_price", "unit_cost", "discount"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in ["date", "period"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def import_finance_excel(path: str, manual_mapping: dict | None = None) -> ImportResult:
    """
    manual_mapping format:
    {
      "sales": {"sheet": "Ventes", "columns": {"date": "Date", "amount": "Montant HT"}},
      "purchases": {"sheet": "Achats", "columns": {...}}
    }
    """
    sheets = _read_excel_sheets(path)
    detected = {}
    tables = {}

    if manual_mapping:
        for table, cfg in manual_mapping.items():
            sheet = cfg["sheet"]
            if sheet in sheets:
                mapping = cfg["columns"]
                tables[table] = _canonicalize(sheets[sheet], mapping)
                mr = suggest_column_mapping(sheets[sheet], table)
                mr.sheet_name = sheet
                mr.column_mapping = mapping
                mr.missing_required_fields = []
                detected[table] = mr
    else:
        for sheet_name, df in sheets.items():
            table, confidence = detect_sheet_table(sheet_name, df)
            if confidence < 0.45:
                continue
            if table in detected and confidence < max(detected[table].confidence.values(), default=0):
                continue
            mr = suggest_column_mapping(df, table)
            mr.sheet_name = sheet_name
            detected[table] = mr
            tables[table] = _canonicalize(df, mr.column_mapping)

    dataset = CanonicalDataset(raw_sheets=sheets)
    dataset.sales = tables.get("sales", pd.DataFrame())
    dataset.purchases = tables.get("purchases", pd.DataFrame())
    dataset.fixed_costs = tables.get("fixed_costs", pd.DataFrame())
    dataset.budget = tables.get("budget", pd.DataFrame())
    dataset.cash = tables.get("cash", pd.DataFrame())
    quality = validate_dataset(tables)
    return ImportResult(dataset=dataset, mapping=detected, quality=quality)
