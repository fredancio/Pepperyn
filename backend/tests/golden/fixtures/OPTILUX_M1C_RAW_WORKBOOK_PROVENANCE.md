# OPTILUX M1C raw-workbook provenance

- Fixture ID: `OPTILUX_M1C_RAW_V1`
- File: `optilux_m1c_raw_workbook.xlsx`
- SHA-256: `D534C91B9B2AD260526FE029C5DC56F022205EE0BD6C8F9EA0648A5BA1EF8E8D`
- Size: 6,577 bytes
- Created: 2026-08-31 for the M1C synthetic raw-workbook validation only.
- Nature: entirely synthetic literal values; no client or external source data.
- Construction: OpenAI bundled spreadsheet artifact runtime; four sheets, no formulas, macros, external links, hidden sheets or named external data connections.

## Independent financial ground truth

| Metric | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Revenue | 2,000,000 | 2,200,000 | 2,400,000 |
| Gross margin | 1,340,000 | 1,474,000 | 1,608,000 |
| EBITDA | 70,000 | 14,000 | -145,000 |
| Net result | 24,000 | -38,000 | -171,000 |
| Cash | 410,000 | 372,000 | 336,000 |
| DSO days | 48 | 61 | 74 |
| DPO days | 43 | 46 | 51 |
| DIO days | 52 | 57 | 65 |
| BFR days | 57 | 72 | 88 |
| BFR EUR | 312,000 | 434,000 | 579,000 |
| Total assets / liabilities | 2,040,000 | 2,107,000 | 2,206,000 |
| Equity | 1,000,000 | 962,000 | 791,000 |
| Financial debt LT + CT | 640,000 | 795,000 | 927,000 |

The workbook is not an `AnalysisResult` fixture. Its cells are the input to the actual Quality Gate and `FileConnector` parser path.
