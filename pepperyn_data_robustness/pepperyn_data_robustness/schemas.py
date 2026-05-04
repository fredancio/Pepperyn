from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd

@dataclass
class FieldIssue:
    severity: str  # info | warning | critical
    table: str
    field: str
    message: str
    affected_rows: int = 0

@dataclass
class DataQualityReport:
    score: int
    status: str  # good | medium | poor | blocked
    issues: List[FieldIssue] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    def summary_text(self) -> str:
        lines = [f"Score qualité: {self.score}/100", f"Statut: {self.status}"]
        if self.assumptions:
            lines.append("Hypothèses: " + "; ".join(self.assumptions))
        critical = [i for i in self.issues if i.severity == "critical"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        lines.append(f"Anomalies critiques: {len(critical)}")
        lines.append(f"Avertissements: {len(warnings)}")
        for issue in self.issues[:12]:
            lines.append(f"- [{issue.severity}] {issue.table}.{issue.field}: {issue.message} ({issue.affected_rows} lignes)")
        return "\n".join(lines)

@dataclass
class MappingResult:
    table_name: str
    sheet_name: str
    column_mapping: Dict[str, str]  # canonical_field -> original_column
    confidence: Dict[str, float]
    missing_required_fields: List[str] = field(default_factory=list)

@dataclass
class CanonicalDataset:
    sales: pd.DataFrame = field(default_factory=pd.DataFrame)
    purchases: pd.DataFrame = field(default_factory=pd.DataFrame)
    fixed_costs: pd.DataFrame = field(default_factory=pd.DataFrame)
    budget: pd.DataFrame = field(default_factory=pd.DataFrame)
    cash: pd.DataFrame = field(default_factory=pd.DataFrame)
    raw_sheets: Dict[str, pd.DataFrame] = field(default_factory=dict)

@dataclass
class ImportResult:
    dataset: CanonicalDataset
    mapping: Dict[str, MappingResult]
    quality: DataQualityReport
