from typing import Dict, Tuple
import pandas as pd
from rapidfuzz import fuzz
from .canonical import CANONICAL_TABLES
from .schemas import MappingResult

TABLE_HINTS = {
    "sales": ["sales", "vente", "ventes", "revenue", "ca", "invoice", "facture client", "customers"],
    "purchases": ["purchase", "purchases", "achat", "achats", "supplier", "fournisseur", "cogs"],
    "fixed_costs": ["fixed", "fixe", "overhead", "opex", "charges", "frais", "costs"],
    "budget": ["budget", "forecast", "prévision", "prevision"],
    "cash": ["cash", "bank", "banque", "trésorerie", "tresorerie", "payment", "paiement"],
}

def _norm(s: str) -> str:
    return str(s).strip().lower().replace("_", " ").replace("-", " ")

def _best_column_for_field(columns, aliases) -> Tuple[str | None, float]:
    best_col, best_score = None, 0.0
    for col in columns:
        col_norm = _norm(col)
        for alias in aliases:
            score = fuzz.token_set_ratio(col_norm, _norm(alias)) / 100
            if score > best_score:
                best_col, best_score = col, score
    if best_score < 0.62:
        return None, best_score
    return best_col, best_score

def suggest_column_mapping(df: pd.DataFrame, table_name: str) -> MappingResult:
    spec = CANONICAL_TABLES[table_name]
    used = set()
    mapping, confidence = {}, {}
    for field, aliases in spec["aliases"].items():
        candidates = [c for c in df.columns if c not in used]
        col, score = _best_column_for_field(candidates, aliases)
        if col:
            mapping[field] = col
            confidence[field] = round(score, 3)
            used.add(col)
    missing = [f for f in spec["required"] if f not in mapping]
    return MappingResult(table_name=table_name, sheet_name="", column_mapping=mapping, confidence=confidence, missing_required_fields=missing)

def detect_sheet_table(sheet_name: str, df: pd.DataFrame) -> Tuple[str, float]:
    name = _norm(sheet_name)
    best_table, best_score = "sales", 0.0
    for table, hints in TABLE_HINTS.items():
        sheet_score = max(fuzz.token_set_ratio(name, h) for h in hints) / 100 if hints else 0
        mapping = suggest_column_mapping(df, table)
        required_total = len(CANONICAL_TABLES[table]["required"])
        required_found = required_total - len(mapping.missing_required_fields)
        mapping_score = required_found / max(required_total, 1)
        score = 0.45 * sheet_score + 0.55 * mapping_score
        if score > best_score:
            best_table, best_score = table, score
    return best_table, round(best_score, 3)
