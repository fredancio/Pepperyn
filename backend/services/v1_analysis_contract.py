"""V1 governed single-call financial analysis contract.

The model may reason over deterministic, source-referenced facts.  It cannot
create canonical enterprise facts: every claim must retain explicit evidence
references and an epistemic category.  This module performs no network I/O and
does not alter real-data admission.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import secrets
import unicodedata
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.schemas import AnalysisResult


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceFact(_ClosedModel):
    fact_id: str = Field(pattern=r"^F[A-F0-9]{12}$")
    metric: Literal[
        "REVENUE", "COST_OF_SALES", "GROSS_MARGIN", "PERSONNEL_COST", "OTHER_FIXED_COSTS",
        "EBITDA", "NET_RESULT", "NET_MARGIN", "FIXED_ASSETS", "INVENTORY", "RECEIVABLES",
        "CASH", "WORKING_CAPITAL", "DSO_DAYS", "DPO_DAYS", "DIO_DAYS", "BFR_DAYS",
        "EQUITY", "LONG_TERM_DEBT", "SHORT_TERM_DEBT", "PAYABLES", "OTHER_CURRENT_LIABILITIES",
        "TOTAL_ASSETS", "TOTAL_LIABILITIES",
    ]
    value: int | float
    unit: Literal["EUR", "DAYS", "RATIO"]
    period: str = Field(pattern=r"^(?:\d{4}|FY\d{2,4}(?: ACTUAL)?)$")
    source_sheet_ref: str = Field(pattern=r"^S[A-F0-9]{12}$")
    source_field: str = Field(pattern=r"^R[A-F0-9]{12}$")


class UnderstandingResult(_ClosedModel):
    status: Literal["UNDERSTOOD", "AMBIGUOUS", "INSUFFICIENT"]
    current_period: str | None = None
    facts: tuple[SourceFact, ...] = Field(default=(), max_length=250)
    unknowns: tuple[str, ...] = Field(default=(), max_length=20)
    source_representation_sha256: str = Field(pattern=r"^[A-F0-9]{64}$")

    @model_validator(mode="after")
    def require_safe_state(self) -> "UnderstandingResult":
        if self.status == "UNDERSTOOD" and (not self.current_period or not self.facts):
            raise ValueError("UNDERSTOOD requires a current period and source facts")
        if self.status != "UNDERSTOOD" and not self.unknowns:
            raise ValueError("ambiguous/insufficient understanding requires explicit unknowns")
        ids = [fact.fact_id for fact in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("fact ids must be unique")
        if self.current_period and any(fact.period != self.current_period for fact in self.facts):
            raise ValueError("all facts must match the governed current period")
        return self


class GroundedObservation(_ClosedModel):
    fact_id: str
    metric: str
    observed_value: int | float
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]


class GovernedInference(_ClosedModel):
    statement: str = Field(min_length=1, max_length=1500)
    fact_ids: tuple[str, ...] = Field(max_length=12)
    confidence: int = Field(ge=0, le=100)
    validation_required: tuple[str, ...] = Field(min_length=1, max_length=8)


class GovernedDimensionAssessment(_ClosedModel):
    scope: Literal["PROFITABILITY", "RISK", "STRUCTURE", "LIQUIDITY"]
    score: int = Field(ge=0, le=10)
    rationale: str = Field(min_length=1, max_length=1200)
    fact_ids: tuple[str, ...] = Field(min_length=1, max_length=12)
    confidence: int = Field(ge=0, le=100)
    validation_required: tuple[str, ...] = Field(min_length=1, max_length=8)


class GovernedUnknown(_ClosedModel):
    question: str = Field(min_length=1, max_length=800)
    materiality: Literal["HIGH", "MEDIUM", "LOW"]


class GovernedContradiction(_ClosedModel):
    statement: str = Field(min_length=1, max_length=1200)
    fact_ids: tuple[str, ...] = Field(min_length=2, max_length=12)


class GovernedRecommendation(_ClosedModel):
    priority: Literal["P1", "P2", "P3"]
    action: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=1200)
    fact_ids: tuple[str, ...] = Field(max_length=12)
    prerequisite_validation: tuple[str, ...] = Field(max_length=8)


class GovernedFinancialAnalysis(_ClosedModel):
    source_representation_sha256: str = Field(pattern=r"^[A-F0-9]{64}$")
    invocation_nonce: str = Field(pattern=r"^[A-F0-9]{32}$")
    executive_diagnosis: str = Field(min_length=1, max_length=4000)
    diagnosis_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=20)
    observations: tuple[GroundedObservation, ...] = Field(min_length=1, max_length=20)
    dimension_assessments: tuple[GovernedDimensionAssessment, ...] = Field(max_length=4)
    inferences: tuple[GovernedInference, ...] = Field(max_length=15)
    unknowns: tuple[GovernedUnknown, ...] = Field(max_length=15)
    contradictions: tuple[GovernedContradiction, ...] = Field(max_length=10)
    recommendations: tuple[GovernedRecommendation, ...] = Field(min_length=1, max_length=8)

    def validate_against(self, understanding: UnderstandingResult) -> None:
        if understanding.status != "UNDERSTOOD":
            raise ValueError("analysis is forbidden when financial understanding is not established")
        known = {fact.fact_id for fact in understanding.facts}
        references: list[str] = list(self.diagnosis_fact_ids)
        references.extend(item.fact_id for item in self.observations)
        for item in (*self.dimension_assessments, *self.inferences, *self.contradictions, *self.recommendations):
            references.extend(item.fact_ids)
        unknown = sorted(set(references) - known)
        if unknown:
            raise ValueError(f"analysis references unknown facts: {unknown}")
        by_id = {fact.fact_id: fact for fact in understanding.facts}
        for observation in self.observations:
            fact = by_id[observation.fact_id]
            if observation.metric != fact.metric or observation.observed_value != fact.value:
                raise ValueError("observation does not match its cited source fact")
        for contradiction in self.contradictions:
            if len(set(contradiction.fact_ids)) != len(contradiction.fact_ids):
                raise ValueError("contradiction requires distinct facts")
        scopes = [item.scope for item in self.dimension_assessments]
        if len(scopes) != len(set(scopes)):
            raise ValueError("dimension assessments must have unique scopes")
        for recommendation in self.recommendations:
            if not recommendation.fact_ids and not recommendation.prerequisite_validation:
                raise ValueError("recommendation requires evidence or prerequisite validation")


V1_ANALYSIS_SCHEMA_NAME = "pepperyn_v1_governed_financial_analysis"


def build_openai_request(
    minimized_anonymized_representation: Mapping[str, Any],
    *,
    model: str,
    max_output_tokens: int = 16_384,
) -> tuple[dict[str, Any], str, UnderstandingResult]:
    """Build from the minimized/anonymized representation; perform no dispatch."""

    understanding = build_financial_understanding(minimized_anonymized_representation)
    if understanding.status != "UNDERSTOOD":
        raise ValueError("provider dispatch forbidden without governed understanding")
    if not model or max_output_tokens < 4_096 or max_output_tokens > 32_768:
        raise ValueError("invalid bounded provider configuration")
    nonce = secrets.token_hex(16).upper()
    request = {
        "model": model,
        "store": False,
        "instructions": (
            "Analyze only the supplied source facts. Keep observations, inferences, unknowns, "
            "contradictions and recommendations epistemically separate. Cite fact_ids for every "
            "diagnosis, observation, dimension assessment, inference, contradiction and evidence-grounded recommendation. "
            "Dimension scores are governed inferences, never deterministic source facts. "
            "Never treat an inference or recommendation as canonical enterprise truth. If evidence "
            "is insufficient or ambiguous, record an unknown or contradiction. Respond in French."
        ),
        "input": json.dumps({
            "invocation_nonce": nonce,
            "source_facts": understanding.model_dump(mode="json"),
        }, ensure_ascii=False, separators=(",", ":")),
        "reasoning": {"effort": "medium"},
        "max_output_tokens": max_output_tokens,
        "text": {
            "format": {
                "type": "json_schema",
                "name": V1_ANALYSIS_SCHEMA_NAME,
                "strict": True,
                "schema": GovernedFinancialAnalysis.model_json_schema(),
            }
        },
    }
    return request, nonce, understanding


def parse_openai_response(
    response: Mapping[str, Any],
    understanding: UnderstandingResult,
    invocation_nonce: str,
) -> GovernedFinancialAnalysis:
    """Fail closed on transport state, refusal, shape, schema or lineage."""

    status = response.get("status")
    if status == "incomplete":
        details = response.get("incomplete_details")
        reason = details.get("reason") if isinstance(details, Mapping) else "unknown"
        raise ValueError(f"OPENAI_RESPONSE_INCOMPLETE_{str(reason).upper()}")
    if status != "completed" or response.get("error"):
        raise ValueError("OPENAI_RESPONSE_NOT_COMPLETED")
    texts: list[str] = []
    for item in response.get("output", ()):
        if not isinstance(item, Mapping) or item.get("type") != "message":
            continue
        for block in item.get("content", ()):
            if isinstance(block, Mapping) and block.get("type") == "refusal":
                raise ValueError("OPENAI_RESPONSE_REFUSED")
            if isinstance(block, Mapping) and block.get("type") == "output_text" and isinstance(block.get("text"), str):
                texts.append(block["text"])
    if len(texts) != 1:
        raise ValueError("OPENAI_RESPONSE_UNSUPPORTED_SHAPE")
    analysis = GovernedFinancialAnalysis.model_validate_json(texts[0])
    if analysis.source_representation_sha256 != understanding.source_representation_sha256:
        raise ValueError("OPENAI_RESPONSE_SOURCE_MISMATCH")
    if analysis.invocation_nonce != invocation_nonce:
        raise ValueError("OPENAI_RESPONSE_INVOCATION_MISMATCH")
    analysis.validate_against(understanding)
    return analysis


def _canonical_hash(value: Mapping[str, Any]) -> str:
    body = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest().upper()


def _number(value: Any) -> tuple[int | float | None, bool]:
    if isinstance(value, bool):
        return None, False
    if isinstance(value, (int, float)):
        return value, False
    if isinstance(value, str):
        compact = value.strip()
        if not re.fullmatch(r"[-+]?\d+", compact):
            return None, bool(re.search(r"\d[\s,.]\d", compact))
        try:
            parsed = Decimal(compact)
        except InvalidOperation:
            return None, True
        return (int(parsed) if parsed == parsed.to_integral() else float(parsed)), False
    return None, False


def _normalized_label(value: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c)).split())


_METRICS = {
    "chiffre d'affaires": ("REVENUE", "EUR"), "net sales": ("REVENUE", "EUR"), "revenue": ("REVENUE", "EUR"),
    "cout des ventes": ("COST_OF_SALES", "EUR"), "co�t des ventes": ("COST_OF_SALES", "EUR"), "cost of sales": ("COST_OF_SALES", "EUR"),
    "marge brute": ("GROSS_MARGIN", "EUR"), "gross margin": ("GROSS_MARGIN", "EUR"),
    "charges de personnel": ("PERSONNEL_COST", "EUR"), "personnel cost": ("PERSONNEL_COST", "EUR"),
    "autres couts fixes": ("OTHER_FIXED_COSTS", "EUR"), "autres co�ts fixes": ("OTHER_FIXED_COSTS", "EUR"),
    "ebitda": ("EBITDA", "EUR"), "resultat net": ("NET_RESULT", "EUR"), "net result": ("NET_RESULT", "EUR"),
    "r�sultat net": ("NET_RESULT", "EUR"), "marge nette": ("NET_MARGIN", "RATIO"), "net margin": ("NET_MARGIN", "RATIO"),
    "actifs immobilises": ("FIXED_ASSETS", "EUR"), "actifs immobilis�s": ("FIXED_ASSETS", "EUR"), "fixed assets": ("FIXED_ASSETS", "EUR"),
    "stocks": ("INVENTORY", "EUR"), "inventory": ("INVENTORY", "EUR"),
    "creances clients": ("RECEIVABLES", "EUR"), "cr�ances clients": ("RECEIVABLES", "EUR"), "receivables": ("RECEIVABLES", "EUR"),
    "tresorerie actif": ("CASH", "EUR"), "tr�sorerie actif": ("CASH", "EUR"),
    "tresorerie": ("CASH", "EUR"), "cash": ("CASH", "EUR"), "bfr total": ("WORKING_CAPITAL", "EUR"),
    "working capital": ("WORKING_CAPITAL", "EUR"), "dso jours": ("DSO_DAYS", "DAYS"), "dso days": ("DSO_DAYS", "DAYS"),
    "dpo jours": ("DPO_DAYS", "DAYS"), "dpo days": ("DPO_DAYS", "DAYS"), "dio jours": ("DIO_DAYS", "DAYS"),
    "dio days": ("DIO_DAYS", "DAYS"), "bfr jours": ("BFR_DAYS", "DAYS"), "working capital days": ("BFR_DAYS", "DAYS"),
    "capitaux propres": ("EQUITY", "EUR"), "equity": ("EQUITY", "EUR"), "total actif": ("TOTAL_ASSETS", "EUR"),
    "dettes financieres lt": ("LONG_TERM_DEBT", "EUR"), "dettes financi�res lt": ("LONG_TERM_DEBT", "EUR"), "long term debt": ("LONG_TERM_DEBT", "EUR"),
    "dettes financieres ct": ("SHORT_TERM_DEBT", "EUR"), "dettes financi�res ct": ("SHORT_TERM_DEBT", "EUR"), "short term debt": ("SHORT_TERM_DEBT", "EUR"),
    "dettes fournisseurs": ("PAYABLES", "EUR"), "payables": ("PAYABLES", "EUR"),
    "autres dettes court terme": ("OTHER_CURRENT_LIABILITIES", "EUR"), "other current liabilities": ("OTHER_CURRENT_LIABILITIES", "EUR"),
    "total assets": ("TOTAL_ASSETS", "EUR"), "total passif": ("TOTAL_LIABILITIES", "EUR"), "total liabilities": ("TOTAL_LIABILITIES", "EUR"),
}


def build_financial_understanding(parsed_data: Mapping[str, Any]) -> UnderstandingResult:
    """Extract current-period literal facts or return a safe ambiguity state."""

    serializable = json.loads(json.dumps(parsed_data, ensure_ascii=False, allow_nan=False))
    digest = _canonical_hash(serializable)
    parsed_data = serializable
    temporal = parsed_data.get("temporal_context")
    if not isinstance(temporal, Mapping):
        return UnderstandingResult(
            status="AMBIGUOUS", unknowns=("No governed temporal context was detected.",),
            source_representation_sha256=digest,
        )
    roles = temporal.get("columns_by_role")
    current_columns = roles.get("CURRENT_ACTUAL") if isinstance(roles, Mapping) else None
    if not isinstance(current_columns, list) or len(current_columns) != 1 or not isinstance(current_columns[0], str):
        return UnderstandingResult(
            status="AMBIGUOUS",
            unknowns=("Exactly one CURRENT_ACTUAL column could not be established.",),
            source_representation_sha256=digest,
        )
    current_column = current_columns[0].upper()
    if not re.fullmatch(r"(?:\d{4}|FY\d{2,4}(?: ACTUAL)?)", current_column):
        return UnderstandingResult(
            status="AMBIGUOUS",
            unknowns=("The current-period label is outside the governed V1 temporal grammar.",),
            source_representation_sha256=digest,
        )
    sheets = parsed_data.get("sheets")
    if not isinstance(sheets, list):
        return UnderstandingResult(
            status="INSUFFICIENT", current_period=current_column,
            unknowns=("No detailed financial sheet is available.",),
            source_representation_sha256=digest,
        )

    facts: list[SourceFact] = []
    ambiguities: list[str] = []
    unsupported_numeric_rows = 0
    for sheet in sheets:
        if not isinstance(sheet, Mapping):
            continue
        sheet_name = sheet.get("sheet_name")
        columns = sheet.get("columns")
        rows = sheet.get("full_table")
        if not isinstance(sheet_name, str) or not isinstance(columns, list) or not columns or not isinstance(rows, list):
            continue
        label_column = columns[0]
        if not isinstance(label_column, str):
            continue
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                continue
            label = row.get(label_column)
            if not isinstance(label, str) or not label.strip():
                continue
            semantic = _METRICS.get(_normalized_label(label))
            if semantic is None:
                raw_value = row.get(current_columns[0])
                if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                    unsupported_numeric_rows += 1
                elif isinstance(raw_value, str) and re.search(r"\d", raw_value):
                    unsupported_numeric_rows += 1
                continue
            value, ambiguous = _number(row.get(current_columns[0]))
            if ambiguous:
                ambiguities.append(f"Ambiguous numeric representation for governed metric {semantic[0]}.")
                continue
            if value is None:
                continue
            metric, unit = semantic
            sheet_ref = "S" + hashlib.sha256(sheet_name.encode("utf-8")).hexdigest()[:12].upper()
            source_field = "R" + hashlib.sha256(f"{sheet_ref}|{row_index}|{current_column}".encode()).hexdigest()[:12].upper()
            fact_id = "F" + hashlib.sha256(f"{metric}|{current_column}|{sheet_ref}|{source_field}|{value}".encode()).hexdigest()[:12].upper()
            facts.append(SourceFact(
                fact_id=fact_id, metric=metric, value=value, unit=unit, period=current_column,
                source_sheet_ref=sheet_ref, source_field=source_field,
            ))
    if len(facts) > 250:
        ambiguities.append("The recognized fact envelope exceeds the V1 bound of 250 facts.")
    if unsupported_numeric_rows:
        ambiguities.append("Numeric rows outside the governed V1 metric vocabulary require review.")
    by_metric: dict[str, set[int | float]] = {}
    for fact in facts:
        by_metric.setdefault(fact.metric, set()).add(fact.value)
    if any(len(values) > 1 for values in by_metric.values()):
        ambiguities.append("Conflicting values exist for a governed metric in the current period.")
    if ambiguities:
        return UnderstandingResult(status="AMBIGUOUS", current_period=current_column, unknowns=tuple(ambiguities), source_representation_sha256=digest)
    if not facts:
        return UnderstandingResult(
            status="INSUFFICIENT", current_period=current_column,
            unknowns=("No numeric current-period facts were found in detailed sheets.",),
            source_representation_sha256=digest,
        )
    return UnderstandingResult(
        status="UNDERSTOOD", current_period=current_column, facts=tuple(facts),
        source_representation_sha256=digest,
    )


def to_analysis_result(
    analysis: GovernedFinancialAnalysis,
    understanding: UnderstandingResult,
    *,
    document_type: str = "FINANCIAL_WORKBOOK",
) -> "GovernedAnalysisEnvelope":
    """Validate lineage and adapt the governed result to the existing UI model."""

    analysis.validate_against(understanding)
    # Provider-selected scores, severities and priorities are retained only in
    # the governed envelope and never promoted to legacy canonical fields.
    return GovernedAnalysisEnvelope(governed_analysis=analysis, source_facts=understanding)


class GovernedAnalysisEnvelope(_ClosedModel):
    governed_analysis: GovernedFinancialAnalysis
    source_facts: UnderstandingResult

    @model_validator(mode="after")
    def validate_lineage(self) -> "GovernedAnalysisEnvelope":
        if self.governed_analysis.source_representation_sha256 != self.source_facts.source_representation_sha256:
            raise ValueError("governed envelope source lineage mismatch")
        self.governed_analysis.validate_against(self.source_facts)
        return self

    @property
    def analysis_result(self) -> AnalysisResult:
        """Return a fresh non-authoritative compatibility projection."""
        analysis = self.governed_analysis
        understanding = self.source_facts
        facts_by_metric = {fact.metric: fact for fact in understanding.facts}

        def _eur_card(metric: str, label: str) -> dict[str, str] | None:
            fact = facts_by_metric.get(metric)
            if fact is None or fact.unit != "EUR":
                return None
            value = f"{fact.value:,.0f}".replace(",", " ")
            return {"label": label, "value": f"{value} €"}

        dashboard = [card for card in (
            _eur_card("REVENUE", "Chiffre d'affaires"),
            _eur_card("EBITDA", "EBITDA"),
            _eur_card("CASH", "Cash disponible"),
        ) if card is not None]
        result = AnalysisResult(
            type_document="FINANCIAL_WORKBOOK",
            # Legacy confidence is not authoritative: provider confidence stays
            # only in governed_analysis with its evidence and validation needs.
            score_confiance=0,
            resume_executif=f"INFERENCE — {analysis.executive_diagnosis}",
            synthese=f"INFERENCE — {analysis.executive_diagnosis}",
            problemes_critiques=[],
            alertes=[f"OBSERVED: {item.metric} = {item.observed_value}" for item in analysis.observations]
            + [f"INFERRED SEVERITY ({item.severity}): {item.metric}" for item in analysis.observations]
            + [f"UNKNOWN: {item.question}" for item in analysis.unknowns]
            + [f"UNDERSTANDING UNKNOWN: {item}" for item in understanding.unknowns]
            + [f"CONTRADICTION: {item.statement}" for item in analysis.contradictions],
            plan_action=[f"{item.priority} — {item.action}"
                + (f" | Prérequis: {'; '.join(item.prerequisite_validation)}" if item.prerequisite_validation else "")
                for item in analysis.recommendations],
            ceo_dashboard=dashboard,
            decision="Décision professionnelle requise; les recommandations IA ne sont pas des décisions confirmées.",
            verification_tag="V1_GOVERNED_SINGLE_CALL",
        )
        return result
