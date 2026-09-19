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

## Professional oracle preparation (A16, historical draft stage)

The draft casebook at
`docs/Product/PEPPERYN_PRIVATE_BETA_FINANCIAL_REVIEW_CASEBOOK_V1.md` instantiates
the twelve families with synthetic numbers, proposed expected/forbidden findings
and source conventions. It is not independent approval, executable fixture proof,
or a gate PASS. Each contract requires authorized professional review before it
becomes an acceptance oracle. Review of expectations and review of actual outputs
must be recorded separately. Current gate status above remains unchanged.

## Reviewed oracle freeze (A17)

Founder has transmitted the independent professional review with clarifications
for every FR01–FR12. Full preserved source, v2 casebook, transversal doctrine,
separate synthetic inputs/evaluator-only expectations and frozen hashes are in
`docs/Product/FinancialReliability/`. Normative revision: `FR-EXPECTED-2`.
The V1 draft is preserved unchanged. V2 is the active expected-result contract.
This review adopts professional reasoning integrity, not just factual integrity;
see PR-01..PR-08 and Canon 11. No runtime behavior is inferred from this adoption.

Reviewer name/date/signature are not supplied. Founder transmission is the source
of authority for preparing this oracle; final independent review-owner/signoff
evidence remains an explicit audit item. Do not ask for re-approval of the twelve
contracts merely because metadata is missing, and do not invent that metadata.

Readiness: FR01/02/03/09/11 have bounded current component paths; FR04/06/10 have
expected scope refusals; FR05/07/08 require additional governed implementation;
FR12 needs the actual synthetic two-user API/DB/RLS/UI/export topology. None is
fully gate-ready. Generic input adapters and terminal execution evidence remain
missing. Refusal evidence is bounded; it does not waive required professional
usefulness or silently redefine the full gate. Do not widen FR10 vocabulary to pass.

Preparation ran artifact integrity/schema falsifications ONLY (eight tests), zero
financial analyses. Source/period/scope references and frozen hashes are validated,
not Pepperyn's financial conclusions. Gate remains OPEN / NOT EXECUTED / NOT PASS.
The execution protocol is in `casebook-v2.md`; report precedes any gate execution.

2026-09-17 A18/A19 supersedes the NOT EXECUTED preparation snapshot only for
FR07/FR08 bounded local components. Their numerical outputs match the frozen
contracts; no complete case, professional output review or Financial Reliability
Gate PASS is claimed. Terminal persistence/export and governed definition authority
remain missing. Full gate stays OPEN_NOT_PASS. Exact evidence and limitations:
`docs/Product/FinancialReliability/consistency-component-evidence-A18-A19.md`.

A20/A21 implements synthetic unresolved-source snapshot capture/reload and UI with
local mock/HTTP/component tests. V35 has not executed; live durability/RLS, persisted
reported/derived reconciliation and full temporal/memory/export propagation remain
unproven. This narrows an implementation gap without closing FR07/FR08 or this gate.
See `docs/Product/FinancialReliability/source-dossier-evidence-A20-A21.md`.

2026-09-18: V35 installation and one synthetic conflict dossier's capture/browser
reload/backend-restart detail read are Founder-reported LIVE_PROVEN. This supersedes
the preceding not-executed V35 snapshot only. It demonstrates preservation of
contradictory claims, not their resolution or professional approval. Full gate stays
OPEN_NOT_PASS; adversarial isolation, reconciliation and terminal propagation remain due.

A22 narrows the portfolio visibility gap for persisted synthetic unresolved sources;
local service/HTTP/UI proof only. It does not resolve contradictory claims or their
financial consequences. No full case/gate promotion. Source:
`docs/Product/FinancialReliability/source-attention-evidence-A22.md`.

A22 bounded live browser navigation now observed (recorded 2026-09-19), for the
existing synthetic conflict dossier only. Visibility/provenance is not professional
validation or source resolution; Financial Reliability Gate remains OPEN_NOT_PASS.

A23 carries bounded owned temporal arithmetic and provenance to three governed
exports. Local HTTP/output/render checks narrow terminal-loss risk, not professional
financial comparability or full-case reliability. V35 contradictory-source linkage
to conclusions/exports remains a separate contextual-relevance debt. FR-EXPECTED-2
unchanged; Financial Reliability Gate remains OPEN_NOT_PASS. Evidence:
`docs/Product/FinancialReliability/temporal-export-evidence-A23.md`.
