# Private Beta financial reliability — reviewed casebook v2

Revision: FR-EXPECTED-2.
Status: FROZEN_EXPECTED_CONTRACTS_WITH_CLARIFICATIONS / EXECUTION_NOT_STARTED.
Authority: independent professional review as transmitted and adopted by Founder.
Reviewer identity/date: NOT_SUPPLIED. Do not invent an independent signature.
Financial Reliability Gate: OPEN / NOT PASS. System-output approval: NOT_GIVEN.
External Provider CLOSED. Real-data Admission CLOSED. Self-Selling DEFERRED.

## Version and authority

The original V1 draft is preserved unchanged at
`../PEPPERYN_PRIVATE_BETA_FINANCIAL_REVIEW_CASEBOOK_V1.md`.
V2 supersedes its expected-result wording, not implementation history. The full
review including transversal requirements is `review-source-v2.txt`.
`professional-reasoning-doctrine-v2.md` formalizes PR-01 through PR-08.
All scenario clarifications below remain normative; twelve bare APPROVED labels
are insufficient. Review-source requirements prevail over an accidental machine
transcription; discrepancy requires a versioned correction, never silent editing.

## Frozen inputs and expectations

`synthetic-inputs-v2.json` contains only synthetic source assertions, explicit
scope/period/convention metadata and missing-evidence declarations. It contains
no expected conclusions. `expected-contracts-v2.json` is an evaluator-only oracle:
numerical expectations, exact review excerpts, doctrine references and readiness.
Never pass oracle IDs/answers/excerpts to a reasoning implementation or provider.
FR12 foreign/unrelated observations are adversarial test setup, NOT admissible
reasoning context. Synthetic carrier IDs are not runtime access capabilities.

Input observations have stable IDs and source references. Source revision is 2;
each source and case has a canonical-JSON SHA256 in `frozen-manifest-v2.json`.
Every frozen text file has a UTF-8/LF canonical SHA256 (CRLF normalized only).
The manifest records baseline implementation hashes and the unmodified V1 hash.
Its own content hash is recorded separately in execution evidence. This is
tamper evidence plus versioning, not a digital signature or legal attestation.
Freeze is local until a scoped Git checkpoint is synchronized.

Source financial amounts are exact EUR with no scale multiplier. Percent and
percentage-point expectations are separately typed, with 0.01 absolute tolerance
for rounded percentage calculations, zero for exact EUR. The original draft's
source facts remain inputs; the reviewed text below refines interpretation.
FR08's 2026 period and synthetic scope IDs are explicit technical carrier metadata,
not professionally approved facts beyond the supplied scenario.

## Execution readiness — static inspection, not observed results

No case is currently FULL_GATE_READY. Bounded extraction/arithmetic can be
tested without claiming professionally validated reasoning or terminal topology.
A test adapter from these neutral JSON sources to current governed representations
must be generic, ownership-bound and independently checked before execution;
do not flatten away period/perimeter/sign metadata or register arbitrary uploads.

| Case | Classification | Current boundary |
|---|---|---|
| FR01 | BOUNDED_COMPONENTS_AVAILABLE | Literal REVENUE/GROSS_MARGIN and annual-label deltas; rate semantics and professional findings not established end-to-end. |
| FR02 | BOUNDED_COMPONENTS_AVAILABLE | Literal EBITDA/CASH and differences; stock/flow distinction and investigation-signal reasoning need terminal proof. |
| FR03 | BOUNDED_COMPONENTS_AVAILABLE | Literal WC/components and deltas; source-defined reconciliation and scoped interpretation not fully implemented. |
| FR04 | EXPECTED_GOVERNED_REFUSAL | Q1 is outside current annual SourceFact period grammar. Do not coerce to FY2026; refusal is not full FR04 capability. |
| FR05 | ADDITIONAL_IMPLEMENTATION_REQUIRED | No persisted multi-dimensional comparability/restatement contract on SourceFact. Annual arithmetic NOT_ESTABLISHED is not reconciled NON-COMPARABLE reasoning. |
| FR06 | EXPECTED_GOVERNED_REFUSAL | Annual comparison refuses missing intermediate years. Literal facts remain available; optional two-year arithmetic is not required for acceptance. |
| FR07 | ADDITIONAL_IMPLEMENTATION_REQUIRED | Conflicting metric extraction becomes AMBIGUOUS with facts omitted. Reviewed CONTRADICTION, dependent-claim propagation and independent fact retention not thereby satisfied. |
| FR08 | ADDITIONAL_IMPLEMENTATION_REQUIRED | Gross-margin reconciliation with reported and derived values has no complete governed terminal contract; financial_doctrine v0 only checks its bounded existing convention. |
| FR09 | BOUNDED_COMPONENTS_AVAILABLE | Literal EBITDA/personnel and deltas; potential-factor hypothesis and action-evidence separation not semantically certified by citation validation. |
| FR10 | EXPECTED_GOVERNED_REFUSAL | MARKETING_EXPENSE outside governed V1 metric vocabulary. No ontology widening to pass; future governed reasoning contract retained. |
| FR11 | BOUNDED_COMPONENTS_AVAILABLE | Cash/receivables/short-term debt vocabulary exists. Signal, availability/runway semantics and minimal prioritized requests lack end-to-end proof. |
| FR12 | ADDITIONAL_IMPLEMENTATION_AND_TOPOLOGY_REQUIRED | Scoped component evidence exists, but two-user API/DB/RLS/UI/export adversarial chain is not established. Fixture scope labels are not credentials/authority. |

## Reviewed scenario-specific contracts

### FR01 — REVENUE GROWTH WITH GROSS-MARGIN DETERIORATION

Review source section 6. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Confirmed observations:

Revenue:
1,000,000 → 1,200,000
= +200,000
= +20%

Gross-margin amount:
400,000 → 360,000
= -40,000
= -10%

Gross-margin rate:
40% → 30%
= -10 percentage points.

Authorized professional interpretation:

The growth is less gross-margin-generative than in the previous period / deterioration in gross-margin economics is observed.

Causality remains UNKNOWN.

Do not allow the scenario title “margin destruction” to become causal or normative output language.

Do not attribute the deterioration to pricing, mix, COGS, or another driver without supporting evidence.

Keep the proposed forbidden conclusions.

### FR02 — EBITDA IMPROVEMENT WITH CASH DETERIORATION

Review source section 7. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Observed:

EBITDA:
100,000 → 150,000
= +50,000
= +50%

Closing cash:
200,000 → 80,000
= -120,000
= -60%

Explicitly preserve the conceptual distinction:

EBITDA = period performance flow concept.

Closing cash = point-in-time stock.

The coexistence of EBITDA improvement and cash deterioration is an INVESTIGATION SIGNAL, not an explanation.

“Poor EBITDA-to-cash conversion”, “cash-conversion deterioration”, or equivalent causal/quality statements remain UNKNOWN until supported by a reconciled cash-flow bridge.

Do not compute a conversion ratio from these two stock/flow observations alone.

### FR03 — WORKING CAPITAL DETERIORATION

Review source section 8. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Using the supplied definition:

WC = Receivables + Inventory - Trade Payables

2025:
200 + 100 - 150 = 150k

2026:
300 + 100 - 150 = 250k

Therefore:

WC change = +100k.

The +100k increase reconciles arithmetically entirely to the +100k increase in receivables under the supplied definition.

Authorized interpretation:

More financial resources are tied in receivables at closing, and with unchanged revenue this merits investigation of the collection cycle.

However, the economic cause remains UNKNOWN.

Possible causes such as:

- payment speed;
- billing seasonality;
- payment terms;
- year-end sales concentration;
- cut-off;
- other operational effects

must not be selected without evidence.

Forbidden conclusions should include:

- customer payment terms deteriorated, without ageing/context;
- customers are delinquent;
- 100k of cash was necessarily consumed/lost;
- 100k is immediately recoverable;
- mechanical DSO inference without an accepted denominator/convention.

### FR04 — SEASONALITY / UNEQUAL PERIODS

Review source section 9. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Facts:

FY2025 revenue:
1.2m / 12 months.

Jan-Mar 2026 revenue:
450k / 3 months.

These are not directly comparable annual periods.

Do NOT report:

-62.5% annual decline.

Do NOT present:

450k × 4 = 1.8m

as fact or forecast.

A mechanical run-rate may be mathematically calculable, but it is neither an observation nor a forecast.

For V1, it should not be spontaneously presented as a financial conclusion.

If such a run-rate capability is ever exposed, it must be explicitly labelled as mechanical annualization without seasonality and NOT as forecast.

Important additional distinction:

Obtaining Q1 2025 would enable like-for-like Q1 historical comparison.

It would NOT, by itself, establish a reliable FY2026 forecast.

Historical comparability ≠ predictive capability.

### FR05 — PERIMETER / ACCOUNTING-CONVENTION CHANGE

Review source section 10. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Reported revenue:

2025:
1.0m — Entity A / local GAAP.

2026:
1.8m — consolidated A+B after acquisition, with changed revenue-recognition convention.

The arithmetic difference:

+800k / +80%

may be shown only if explicitly qualified as NON-COMPARABLE.

It must not become:

- organic growth;
- like-for-like growth;
- proof of acquisition impact;
- same-scope trend.

Two independent comparability dimensions exist:

PERIMETER_CHANGE

and

ACCOUNTING_CONVENTION_CHANGE.

Resolving one does not automatically resolve the other.

Comparability may only be restored when all relevant dimensions have been reconciled/restated with provenance.

A useful future decomposition may be:

reported variation
→ perimeter effect
→ accounting-convention effect
→ comparable residual

but only when each component is supported by governed evidence.

Do not manufacture the residual.

### FR06 — MISSING PERIOD / INCOMPLETE STATEMENTS

Review source section 11. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Available:

2024 revenue = 900k.

2025 = missing.

2026 revenue = 1.1m.
2026 EBITDA = 80k.

Cash/debt/liabilities/cash-flow data absent.

A difference between 2024 and 2026 may be calculated:

+200k / +22.22%

but must be explicitly described as a difference between two NON-CONSECUTIVE observations.

It must not become 2026-vs-2025 annual growth.

Missing values remain UNKNOWN, never zero.

Positive EBITDA does NOT establish:

- liquidity;
- solvency;
- debt-service capacity;
- overall financial health.

Add explicitly to forbidden conclusions:

inferring solvency, liquidity or debt-service capacity from positive EBITDA alone when required evidence is absent.

### FR07 — CONFLICTING SOURCES

Review source section 12. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Two sources report the same metric/context:

Revenue 2026 = 1.0m.

Revenue 2026 = 900k.

No source precedence or correction exists.

Required epistemic state:

CONTRADICTION.

Do not:

- average to 950k;
- silently select one source;
- apply latest-file-wins;
- discard one source;
- produce a canonical revenue value until resolved.

Pepperyn may calculate and present the discrepancy between competing claims:

100k.

But discrepancy measurement is NOT conflict resolution.

The contradiction should propagate to conclusions that depend on the disputed fact.

It should not necessarily invalidate independent facts elsewhere in the dossier.

Important:

AMBIGUOUS ≠ CONTRADICTION.

AMBIGUOUS means meaning cannot be sufficiently established.

CONTRADICTION means multiple claims are sufficiently understood to establish incompatibility.

### FR08 — ACCOUNTING INCONSISTENCY / SIGN CONVENTION

Review source section 13. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION.

Source states:

Revenue = 1.0m.

COGS = -600k.

Costs use credit-negative presentation.

Gross margin formula = revenue + signed COGS.

Reported gross margin = 1.6m.

Deterministic derivation under the supplied convention:

1.0m + (-600k) = 400k.

Discrepancy with reported gross margin:

1.2m.

Required conceptual separation:

SOURCE FACT:
Reported gross margin = 1.6m.

DETERMINISTIC DERIVATION:
Derived gross margin under supplied convention = 400k.

RECONCILIATION STATUS:
CONTRADICTION.

DISCREPANCY:
1.2m.

The deterministic result must NOT silently overwrite the source-reported value.

Likewise, source truth must not suppress a deterministic inconsistency.

The unresolved state should survive:

- persistence;
- temporal history;
- UI;
- memory;
- exports.

Conceptually preserve:

reported value
+ derived value
+ provenance
+ discrepancy
+ CONTRADICTION
+ unresolved status

until governed resolution.

No EBITDA derivation is permitted from the available data.

### FR09 — INSUFFICIENT EVIDENCE FOR CAUSAL CLAIMS

Review source section 14. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION AND TRANSVERSAL DOCTRINE CONSEQUENCE.

Observed:

EBITDA:
100k → 50k
= -50k.

Personnel cost:
300k → 350k
= +50k.

The numerical coincidence does NOT establish that personnel cost caused the EBITDA deterioration.

However, Pepperyn should not become intellectually silent.

Authorized reasoning:

The +50k personnel-cost movement may be surfaced as a POTENTIAL FACTOR TO INVESTIGATE because there is a professionally relevant economic mechanism.

Its actual causal contribution remains UNKNOWN until a sufficiently complete EBITDA bridge and relevant context are available.

Therefore:

similarity of numerical movements ≠ proof of causality.

Co-movement + plausible economic mechanism ≠ demonstrated causality.

Even established causality would NOT automatically justify an action such as staff reduction.

Diagnosis ≠ management decision.

A decision would require additional context such as:

- productivity;
- capacity requirements;
- growth plans;
- contractual constraints;
- restructuring costs;
- operational consequences;
- other relevant evidence.

This case is the primary source for the transversal reasoning chain:

OBSERVATION
→ SIGNAL
→ HYPOTHESIS
→ INVESTIGATION
→ CAUSALITY
→ ECONOMIC IMPACT
→ OPTIONS
→ DECISION.

### FR10 — MISLEADING CORRELATION

Review source section 15. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION AND TRANSVERSAL DOCTRINE CONSEQUENCE.

Observed:

Revenue:
2024 800k
2025 900k
2026 1.0m

Marketing expense:
40k
50k
60k

A positive co-movement exists.

This may become a SIGNAL worth investigating.

It must NOT become:

Marketing increase → revenue increase.

The hypothesis that marketing contributed to growth may be surfaced as UNVERIFIED.

Causality remains UNKNOWN without attribution/counterfactual/lag/other-driver evidence.

Critically:

100k revenue change / 10k marketing-spend change = 10

may be mathematically calculable.

It is NOT automatically:

- ROI;
- ROAS;
- return;
- causal attribution;
- incremental revenue multiple.

A professional semantic label may only be applied when the governed conditions defining that concept are satisfied.

Additional invariant:

ESTABLISHED CAUSALITY
≠
PROVEN ECONOMIC PROFITABILITY
≠
JUSTIFIED RECOMMENDATION.

Even if marketing causality were later demonstrated, increasing the budget would still require relevant economic evidence such as margin, acquisition economics, retention, saturation, timing and other context.

Current implementation constraint:

Marketing expense is outside the current governed metric vocabulary.

Do NOT widen the ontology merely to make FR10 pass.

The current system should honestly refuse unsupported metric interpretation where required.

The professional contract recorded here defines the intended reasoning once the concept is governed.

### FR11 — LIQUIDITY / RUNWAY / CUSTOMER CONCENTRATION

Review source section 16. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION AND TRANSVERSAL DOCTRINE CONSEQUENCE.

At 31 Dec 2026:

Cash = 60k.

Receivables = 240k.

Current debt = 100k.

Missing:

- burn rate;
- repayment schedule;
- cash restrictions;
- receivables ageing;
- customer split.

The fact that cash (60k) is below current debt (100k) may constitute a LIQUIDITY INVESTIGATION SIGNAL.

It does NOT establish:

- a 40k liquidity deficit;
- inability to pay;
- insolvency.

Current debt does not necessarily mean all 100k is immediately payable.

Likewise:

60k cash + 240k receivables ≠ 300k immediately available liquidity.

Invariant:

ASSET
≠
LIQUIDITY
≠
IMMEDIATELY AVAILABLE LIQUIDITY.

Receivables must not silently become cash.

Runway remains UNKNOWN without an accepted burn-rate definition and supporting evidence.

Customer concentration also remains UNKNOWN without customer-level distribution.

240k receivables could theoretically be concentrated in one customer or spread across many; the aggregate alone does not establish distribution risk.

Most importantly:

UNKNOWN should, when useful, generate a prioritized request for the minimum missing evidence needed to improve the decision.

For liquidity this may include, according to context:

- debt maturity schedule;
- cash forecast;
- cash restrictions;
- receivables ageing.

For concentration:

- receivables/customer distribution.

Do not automatically request every possible financial dataset.

### FR12 — CROSS-CLIENT / CROSS-PERIOD / CROSS-TENANT CONTAMINATION

Review source section 17. Exact professionally reviewed wording:

VERDICT:
APPROVED WITH CLARIFICATION AND ARCHITECTURAL INVARIANT.

Synthetic observations:

T1 / Entity A / 2025 = 100k revenue.

T1 / Entity A / 2026 = 120k revenue.

T1 / Entity B / 2026 = 9m revenue.

T2 / Entity A / 2026 = 8m revenue.

Legitimate temporal comparison for T1/A:

100k → 120k
= +20k
= +20%.

T1/B must not contaminate T1/A reasoning despite being accessible within the same tenant.

T2/A must be inaccessible to T1 and must be excluded BEFORE reasoning-context construction.

Do not load cross-tenant evidence and instruct the LLM to ignore it.

Security boundary must precede intelligence boundary.

Authorization and contextual relevance are distinct.

Isolation must apply to:

- facts;
- sources;
- derivations;
- hypotheses;
- contradictions;
- temporal history;
- decisions;
- actions;
- memory;
- citations;
- UI;
- exports.

Duplicate current-period evidence must not silently replace another conflicting observation.

Temporal logic must not become a hidden contradiction-resolution mechanism.

A refused read must remain FORBIDDEN.

It must not become EMPTY.

Final FR12 validation requires a real synthetic two-user adversarial proof through the intended topology:

two users
→ API
→ DB
→ RLS
→ UI
→ export

A dictionary-filter/mock proof is useful but insufficient for terminal Gate evidence.

No real customer data is authorized for this proof.

## Proposed execution protocol — not executed

1. Verify the frozen manifest, fixture schema, source/observation references and
   unchanged oracle. Resolve transcription discrepancies before any result run.
2. Checkpoint inputs/oracle/doctrine separately from product changes, then pin
   the candidate implementation revision and configuration; no test-specific
   production code or prompts. Keep expected results out of runtime context.
3. Implement only generic missing invariants or source adapters needed for the
   chosen bounded capability. Do not fabricate supported concepts. Preserve
   explicit unsupported/refusal and unimplemented statuses in the coverage ledger.
4. Run authorized synthetic-only component checks first, then actual governed
   ingestion/persistence/temporal/UI/export checks where implemented. Mocks prove
   contracts only, not financial reasoning, actual provider or live RLS behavior.
   No external provider call is authorized while its gate is CLOSED.
5. Capture input/output hashes, exact revision, fact/citation/period/context lineage,
   numerical differences and per-case semantic findings. Use professional rubric
   review, not keyword matching or a model-generated PASS. Critical false claims
   fail regardless of aggregate score; omissions and blanket refusal also evaluated.
6. FR12 requires two synthetic users in the intended isolated test topology through
   API/DB/RLS/UI/export; foreign evidence never enters reasoning context. Account/
   credential/migration access and production actions follow existing authority.
7. Professional reviewer signs observed results separately from reviewed expectations.
   Record owner/date and artifact evidence. No reviewed expectation implies a result.
8. Gate closure requires ALL Canon 20 evidence, including terminal consistency and
   professional signoff. Supported-refusal slices do not silently waive full-gate
   requirements or open Provider/Real-data/production gates.

## Stop for this preparation

Only artifact-integrity/schema validation is permitted in this preparation step.
No financial analysis, provider response, database write or Financial Reliability
Gate execution has been performed. Report freeze hashes, readiness and open items
before subsequent execution. No new WHY decision is identified for preparing this
bundle; missing reviewer attribution remains explicit audit debt, not guessed.
