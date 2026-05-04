import pandas as pd
from .schemas import DataQualityReport, FieldIssue
from .canonical import CANONICAL_TABLES

NUMERIC_FIELDS = {"amount", "quantity", "unit_price", "unit_cost", "discount"}
DATE_FIELDS = {"date", "period"}

def _add_issue(issues, severity, table, field, message, rows=0):
    issues.append(FieldIssue(severity=severity, table=table, field=field, message=message, affected_rows=int(rows)))

def validate_dataset(tables: dict) -> DataQualityReport:
    issues = []
    assumptions = []
    penalty = 0

    for table, df in tables.items():
        if table not in CANONICAL_TABLES or df is None or df.empty:
            continue
        spec = CANONICAL_TABLES[table]
        for field in spec["required"]:
            if field not in df.columns:
                _add_issue(issues, "critical", table, field, "Champ obligatoire absent")
                penalty += 18
                continue
            missing = df[field].isna().sum()
            if missing > 0:
                ratio = missing / max(len(df), 1)
                sev = "critical" if ratio > 0.25 else "warning"
                _add_issue(issues, sev, table, field, f"Valeurs manquantes: {missing} / {len(df)}", missing)
                penalty += 15 if sev == "critical" else 6

        for field in set(df.columns) & NUMERIC_FIELDS:
            invalid = pd.to_numeric(df[field], errors="coerce").isna() & df[field].notna()
            if invalid.sum() > 0:
                _add_issue(issues, "warning", table, field, "Valeurs non numériques détectées", invalid.sum())
                penalty += 5

        for field in set(df.columns) & DATE_FIELDS:
            invalid = pd.to_datetime(df[field], errors="coerce").isna() & df[field].notna()
            if invalid.sum() > 0:
                _add_issue(issues, "warning", table, field, "Dates invalides détectées", invalid.sum())
                penalty += 5

        duplicates = df.duplicated().sum()
        if duplicates > 0:
            _add_issue(issues, "warning", table, "rows", "Lignes strictement dupliquées", duplicates)
            penalty += 4

    if "sales" in tables and not tables["sales"].empty and "purchases" not in tables:
        assumptions.append("Aucun fichier/table d'achats détecté: les marges seront incomplètes ou impossibles à calculer.")
        penalty += 12
    if "sales" in tables and "amount" in tables["sales"].columns:
        neg_sales = (pd.to_numeric(tables["sales"]["amount"], errors="coerce") < 0).sum()
        if neg_sales:
            assumptions.append("Des montants de vente négatifs ont été détectés; ils peuvent être des avoirs ou erreurs à qualifier.")

    score = max(0, 100 - penalty)
    if any(i.severity == "critical" for i in issues) and score < 65:
        status = "blocked"
    elif score >= 85:
        status = "good"
    elif score >= 65:
        status = "medium"
    else:
        status = "poor"
    return DataQualityReport(score=score, status=status, issues=issues, assumptions=assumptions)
