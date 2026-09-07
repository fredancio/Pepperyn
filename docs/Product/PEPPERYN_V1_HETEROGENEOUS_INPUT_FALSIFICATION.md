# PEPPERYN — V1 Heterogeneous Financial Input Falsification

**Date:** 2026-09-07  
**Admission:** synthetic only; real-data admission CLOSED

## Acceptance contract

The test must use byte-real, hash-pinned XLSX workbooks and the actual local
Pepperyn ingestion components. A safely rejected workbook passes only when the
governed representation identifies the specific uncertainty and forbids
provider request construction. Merely throwing a parser exception is not a
product-quality pass.

## Exact pipeline exercised

`XLSX bytes → Data Quality Gate → FileConnector → file parser and temporal
normalization → anonymization → governed financial understanding → bounded
provider-request builder (understood case only)`

No provider, API key, HTTP route, database or real-client datum is used.

## Case results

1. **English management workbook — UNDERSTOOD.** Two differently named and
   ordered sheets produce ten literal 2025 facts, including revenue EUR
   2,100,000, EBITDA EUR 62,000, cash EUR 198,000 and working capital EUR
   402,000. The provider request remains stateless with `store=false`.
2. **Ambiguous period — AMBIGUOUS.** `Current` and `Latest` are not silently
   interpreted as a year. No fact is promoted and provider request construction
   is forbidden.
3. **Locale-ambiguous numbers — AMBIGUOUS.** Values such as
   `1 234 567,89` and `72.500,00` remain unresolved rather than being assigned
   an unsafe magnitude. No fact is promoted and provider request construction
   is forbidden.
4. **Conflicting revenue — AMBIGUOUS.** Revenue of EUR 1,000,000 and net sales
   of EUR 990,000 for the same current period remain an explicit conflict. No
   fact is promoted and provider request construction is forbidden.

## Bypasses and limits

- The governed model response is not produced; this suite stops before network
  dispatch.
- Authentication, persistence, reload and exports are not repeated; those are
  covered by the Fresh-Founder Golden Workflow.
- The test matrix is falsification-oriented, not generalized FRU support.
- `FY25 Actual` remains conservatively unclassified by the raw temporal parser;
  this is safe behavior and a future P2 compatibility opportunity, not a silent
  interpretation defect.

## Verdict

The current V1 ingestion path is no longer evidenced solely by one idealized
Optilux layout. It correctly interprets a distinct English workbook and safely
preserves UNKNOWN/AMBIGUOUS for three materially different hazards.

## Validation

- Focused heterogeneous-ingestion, adjacent M1C/contract and Slice 1/2/provider
  policy suite: `148 passed`.
- All four workbook packages contain no formula, VBA project or external link.
- Every worksheet was rendered and visually inspected; labels and numeric
  values are visible without clipping.
- A raw repository-wide pytest invocation is not a valid regression command:
  the historical standalone EDM script calls `sys.exit(1)` during collection.
  The available development virtual environment also lacks optional `pypdf`
  used by unrelated export tests. These environment limitations do not affect
  the focused ingestion/security suite and are not represented as product
  regressions.
