# M1C Synthetic Raw-Workbook Ingestion Evidence

Date: 2026-08-31

## Falsifiable claim

The repository demonstrates this exact local path without parser, payload, or anonymizer mocks:

`registered synthetic XLSX bytes → Data Quality Gate → pepperyn_data_robustness import → FileConnector → file_parser/openpyxl → FinancialDataPayload normalization → temporal/BFR/balance summaries → anonymization`

It does **not** demonstrate `RAW WORKBOOK → FULL PEPPERYN → GPT`.

## Registered source

- Fixture: `OPTILUX_M1C_RAW_V1`
- File: `backend/tests/golden/fixtures/optilux_m1c_raw_workbook.xlsx`
- SHA-256: `D534C91B9B2AD260526FE029C5DC56F022205EE0BD6C8F9EA0648A5BA1EF8E8D`
- Size: 6,577 bytes
- Provenance and independent financial ground truth: `backend/tests/golden/fixtures/OPTILUX_M1C_RAW_WORKBOOK_PROVENANCE.md`
- Contents: four sheets, literal synthetic values only, no formulas, macros or external links.

The sandbox loader accepts no path, bytes, entity, company or fixture argument and refuses any byte change before the Quality Gate or parser runs.

## Components actually exercised

1. `services.data_quality_gate.validate_excel_before_analysis`
2. `pepperyn_data_robustness.import_finance_excel`
3. `connectors.FileConnector.fetch`
4. `services.file_parser.parse_file` and the openpyxl path
5. `services.financial_normalizer.wrap_file_parser_output`
6. temporal classification and prompt-prioritized BFR/balance summary extraction
7. `services.anonymization_service.anonymize_parsed_data`

The Quality Gate writes the registered bytes to an OS temporary file and deletes it in `finally`. The literal workbook does not invoke the LibreOffice subprocess fallback.

## Financial evidence

- Quality Gate: `warning`, `structural_pl`, score data 80, completeness 95, confidence 70; analysis permitted. The warning is caused by the non-numeric synthetic metadata sheet.
- Current actual period: 2025.
- Revenue: 2,400,000.
- EBITDA: -145,000.
- Net result: -171,000.
- Cash: 336,000, explicitly sourced from period 2025.
- BFR: 579,000, explicitly sourced from period 2025.
- Equity: 791,000, explicitly sourced from period 2025.
- Total assets and liabilities: 2,206,000 each.
- Entity sentinel becomes `ENTREPRISE_001`; all asserted numeric values and periods remain unchanged; the correspondence table is not included in the downstream representation.

A test changes the actual workbook EBITDA cell from -145,000 to -146,000 and proves that the real parser output changes. No downstream object is constructed manually.

## P0/P1 findings and corrections

- P1: BFR and balance summaries selected the first historical numeric cell while presenting the summary before full tables. Corrected to require the sole `CURRENT_ACTUAL` value and attach its source period; unresolved or ambiguous periods are omitted rather than mislabeled.
- P1: a partial ERP cash-sheet match overrode explicit P&L/balance sheets and blocked a valid structural workbook. Corrected narrowly: an explicitly named core statement wins only when no complete ERP mapping exists. A regression proves a complete ERP workbook with a Budget sheet remains `erp_transactional`.
- P0: none.

## Bypassed or blocked components

- HTTP auth/quota/stream orchestration and Supabase/CRM/persistence effects are deliberately not invoked.
- The actual first stage, `llm_service.classify_document`, is invoked with the anonymized representation and reaches `dispatch_legacy_synthetic`, which refuses with `REAL_DATA_ADMISSION_CLOSED` before transport. The remainder of `run_full_pipeline` is not invoked; later provider output would be tainted and cannot feed the next provider call under Slice 2.
- Provider-dependent construction of `AnalysisResult`, subsequent EDM/DecisionKernel projections, and the M1A OpenAI review are therefore not demonstrated from this raw workbook.

Creating a static or reconstructed `AnalysisResult` would be a disguised fixture test and is prohibited by M1C's falsification rule.

## Reproduction

From `backend` with the repository environment active:

`python -m sandbox.run_raw_ingestion_evidence`

The command performs no network call, accepts no caller input, persists no production record and prints only synthetic non-secret evidence.

## Milestone implication

The raw-ingestion segment passes after the two P1 corrections. Full M1C remains blocked at a material architecture decision: a receipted, authorized transformation contract is required for provider output to pass safely between the classification/evidence/analysis/verification stages without weakening Slice 1 or Slice 2. Until that decision is made, the honest claim stops at the anonymized financial representation.

Real-data admission remains CLOSED; RD-1 through RD-5 remain unchanged.
