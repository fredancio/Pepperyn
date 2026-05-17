from typing import Literal, Optional
from pydantic import BaseModel, Field

Period = str
Comparison = Literal["previous_period", "last_year", "budget"]
Dimension = Literal["product", "customer", "segment", "region", "supplier", "category", "department"]
MarginType = Literal["commercial", "gross", "contribution", "ebitda"]
CostType = Literal["fixed", "variable", "all"]

class MetricResult(BaseModel):
    metric: str
    period: Optional[str] = None
    value: float | int | str | None = None
    unit: str = "EUR"
    details: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

class TableResult(BaseModel):
    title: str
    rows: list[dict]
    warnings: list[str] = Field(default_factory=list)

class CodirAnswer(BaseModel):
    question: str
    period: Optional[str] = None
    answer: str
    key_numbers: dict = Field(default_factory=dict)
    causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
