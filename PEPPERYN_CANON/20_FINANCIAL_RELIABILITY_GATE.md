# Financial Reliability Gate

## Purpose

Prevent technical test success, valid JSON or plausible prose from being
mistaken for professionally reliable financial analysis.

## Required evidence set

Use versioned, synthetic or legally admitted cases with independent expected
professional findings. Every case defines source facts, comparable periods,
known limitations, expected conclusions, forbidden conclusions, required
UNKNOWN/CONTRADICTION states and source references.

Minimum scenario families:

1. revenue growth with margin destruction;
2. EBITDA improvement with cash deterioration;
3. working-capital deterioration;
4. seasonality and non-comparable periods;
5. accounting convention or perimeter change;
6. missing periods and incomplete statements;
7. contradictory sources and duplicate/conflicting values;
8. accounting anomalies and sign-convention traps;
9. insufficient evidence for causal claims;
10. misleading correlations;
11. liquidity/runway and customer-concentration uncertainty;
12. cross-client and cross-period contamination attempts.

## Per-case contract

- deterministic input hash and provenance;
- applicable financial concepts and period semantics;
- expected facts and tolerances;
- required inferences/recommendations and their evidence;
- conclusions the system must refuse;
- expected UNKNOWN and CONTRADICTION output;
- required validations before recommendation/decision;
- traceability through UI and terminal deliverables;
- independent professional review owner;
- exact code revision and test/run evidence.

## Failure conditions

The gate fails on any material invented number, unsupported causal claim,
hidden contradiction, cross-client leakage, period misclassification,
recommendation presented as decision, untraceable material conclusion, or
failure to refuse when evidence is insufficient.

## Passing standard

- all critical scenario families have versioned cases;
- deterministic facts match expected values/tolerances;
- all mandatory refusals and epistemic states are correct;
- no critical prohibited conclusion occurs;
- output remains consistent across UI and required exports;
- an authorized professional reviewer signs off the expected-result contracts
  and observed outputs;
- regression automation pins the accepted cases to an exact revision;
- remaining limitations are explicit and do not invalidate intended Beta use.

No aggregate score may average away a critical epistemic, isolation or material
financial failure. Passing this gate does not itself pass production security,
Provider Gate or Real-data Admission.

**Current status:** `DEFINED / NOT EXECUTED / NOT PASS`.
