# Astra execution evidence

## A1 — selected synthetic client ownership (2026-09-15)

Authority: Founder accepted the takeover audit and authorized autonomous HOW.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## Standing checkpoint operation — Founder directive

Normal Git writes are blocked by this Work sandbox, not by a stale lock.
Do not remove sandbox ACLs or retry Git privilege workarounds. Group compatible
tested slices until a meaningful recovery/traceability boundary; then prepare
one fail-closed Founder script with exact per-commit scope and remote checks.
Uncommitted evidence below is local-only until checkpoint confirmation.

WHY: selecting one client must not silently save its analysis against the
primary client. Client-specific continuity starts at ingestion ownership.

BEFORE: the UI selected an entity for ordinary analysis/history, but the
synthetic mock request omitted it and always used the primary entity.

AFTER: the request carries the selected entity. The backend resolves its
tenant ownership and exact engagement before reading/analysing the workbook.
Foreign/missing entities and missing/ambiguous engagements refuse without a
primary fallback. Omitted selection retains the existing primary-client path.
The designated-tenant gate, registered-fixture admission, mock-only analysis
and non-production mounting remain unchanged. No migration is needed.

Evidence: `backend/tests/test_v1_synthetic_client_selection.py` exercises the
HTTP route with the registered workbook and an in-memory database. Three
selected clients reach the persistence boundary with distinct analysis IDs
and exact entity/engagement binding. Four invalid-scope cases refuse before
analysis/write; foreign tenant refuses before database access. Frontend API
tests verify the multipart client field. The React callback tracks selection.

Executed: 23 backend tests (selection, inspection, Portfolio, temporal) PASS;
7 frontend API tests PASS; TypeScript no-emit check PASS. No live account or
database is used. Extended regression: 70 PASS, 1 FAIL at V31 prerequisite
registration (expected 200, received 404); investigation tracked below.

The same failure was reproduced with the HEAD router loaded directly from
Git into the test process without changing working-tree files. The older
`synthetic-demo` asks for a cash-flow statement and aged balance, whereas V32
accepts exactly monthly cash flows and customer schedules. The test uses the
wrong source scenario. Keep the production prerequisite guard unchanged and
repair the test separately using the registered English workbook.

LIMITS: HTTP-to-persistence-call proof, not live persistence, two-user auth/RLS,
browser interaction, multi-period end-to-end flow or financial reliability.
No new live analysis or founder rehearsal was created. Next proof includes
multi-client continuity and unavailable versus empty Portfolio evidence.

## A1 regression repair and checkpoint state

The V31 route test now imports the registered English workbook through the
HTTP upload route instead of the older demo. No prerequisite guard or runtime
V31/V32 behavior was changed. The combined nine-module backend run is now
94 PASS (3 dependency warnings); frontend API 7 PASS; TypeScript PASS.
The combined run includes persistence, governed contracts, Golden Case,
heterogeneous inputs, synthetic routes, selection, Portfolio and temporal tests.

Git diff whitespace check PASS. Checkpoint is PENDING: Git cannot create
`.git/index.lock` even after explicit write permission was requested and granted
for the repository and its `.git` directory. No index mutation, commit or push
succeeded. HEAD remains the handover checkpoint. This is a local tested delta,
not a remotely recoverable implementation claim.

### A1 checkpoint closure (Founder confirmation)

Supersedes the pending Git state above: Founder checkpointed and synchronized
`606e7afa36db14672e3b6e69013f9c49b7a05fbf`, reporting equal local/remote HEAD
and zero remaining entries. Local HEAD and clean working tree were independently
checked at the start of A2. No new remote-server attestation is inferred.

## A2 — unavailable Portfolio evidence is not an empty queue

WHY: a CFO must not infer that nothing needs attention when the underlying
decision or execution state could not be read. UNKNOWN is not absence.

BEFORE: governed registry read failures returned an empty list; legacy briefing
read failures could do the same. The endpoint merged these lists and returned
200, allowing the UI to show its normal empty-state message.

AFTER: failed governed registry reads raise a named unavailable condition.
The Portfolio requests strict legacy briefing reads (including database absence,
arc query failure and entity-name query failure). Any source exception prevents
the merge and returns a safe 503, with no partial cards or raw diagnostic.
Other legacy briefing consumers retain their existing behavior; no global
availability guarantee is claimed. Successful empty reads remain 200/cards=[];
executed decisions remain excluded from active work. No new domain state,
DecisionArc, migration, provider transport or real-data use was introduced.

Proof: parameterized failures in all five governed registry reads; HTTP 503
for either source and HTTP 200 for a successful empty response; strict legacy
database/query failures; existing Portfolio/briefing regressions. The combined
13-module backend run passes 169 tests (3 dependency warnings). Existing
PortfolioHome tests pass 13 cases, including error versus empty rendering.
All tests use local mocks/fixtures, not the live integration database.

Status: IMPLEMENTED / TESTED, NOT LIVE_PROVEN. Missing or inconsistent rows
without a read exception, optional evidence-enrichment availability, two-user
RLS and the complete multi-period browser workflow are not proven by A2.
Code: governed_portfolio_service.py, arc_service.py, routers/arcs.py.
Tests: test_portfolio_availability.py, test_governed_portfolio_projection.py,
test_portfolio_briefing.py, test_review_briefing.py and PortfolioHome.test.tsx.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## A3 — multi-client reload through actual envelope integrity checks

WHY: an ingestion ownership assertion must survive persistence and later reads.
`test_v1_multiclient_reload.py` uploads the existing registered English workbook
for three owned entities through HTTP, runs real governed serialization/binding
and reload validation, and reconstructs the in-memory database adapter before
reads. All analyses reload in exact client scope. Read operations create no
new rows. With no earlier period, each comparison remains UNKNOWN rather than
borrowing another client's evidence. Corrupt binding refuses; a different
tenant cannot retrieve the analysis. Authentication and database I/O are mocks.
No new source fixture or admission route was created. NOT live RLS/restart proof.

## A4 — terminal temporal comparison in the governed analysis UI

WHY: the CFO needs to see changes and limitations without technical API calls.
The existing read-only comparison endpoint now has a typed frontend consumer
and an analysis panel, mounted only for a governed result with an analysis ID.
It displays period labels, literal before/after/delta values, units, analysis
IDs and fact references. Partial/UNKNOWN/CONTRADICTION and request failure remain
distinct. No cause, decision outcome or learning is generated. Invalid response
shape, wrong analysis ID or non-null causal content is refused. Late responses
from a previous analysis cannot overwrite the current panel.

This does not expand the backend's annual-label comparability policy, certify
financial comparability generally, or provide live/browser multi-period proof.
Positive/partial UI output is fixture-driven; A3's upload workflow establishes
the no-prior UNKNOWN case. Real-data and provider admission remain CLOSED.

Batch validation: 170 backend tests across 14 modules PASS (3 dependency
warnings); 31 frontend tests across four suites PASS; TypeScript no-emit PASS.
No live database writes or external LLM calls. A2/A3/A4 are LOCAL_TESTED,
checkpoint pending. Their combined boundary is a meaningful recovery point
before adding new financial/period semantics. Durable baseline remains A1
`606e7afa36db14672e3b6e69013f9c49b7a05fbf` until batch confirmation.

## A2–A4 durability confirmation

Founder confirms four scoped commits synchronized through
`dc7a14fda86f23e3ea653ccb73dc9b16533f17b1`, no remaining entries.
Local HEAD and origin tracking ref were inspected and match. Remote synchronization
is Founder-reported, not a fresh network query. These local test proofs are now
Git-checkpointed, not thereby promoted to LIVE_PROVEN.

## A5/A6 — temporal refusal and terminal scope (2026-09-16)

WHY: a CFO must not mistake annual-label arithmetic for established financial
comparability. Grounding: FTE_MINIMAL_IMPLEMENTATION_CONTRACT sections 2–4,
15–16; Financial Reliability Gate families 4–6; UNKNOWN is not implicit certainty.

A5 BEFORE: mixed fiscal/plain labels and missing years allowed deltas; unknown
history was skipped; duplicate current-period analyses were not refused.
Subtraction used default Decimal precision and lacked nonfinite operand guards.
AFTER: these chronological ambiguities refuse numeric comparison; duplicated
current periods return CONTRADICTION, unordered history returns UNKNOWN.
Invalid year-zero/unbound short labels refuse. Existing FYxx -> 20xx convention
remains bounded, not a fiscal calendar. Non-UNDERSTOOD sources cannot authorize
comparison. Nonfinite metrics are refused and subtraction precision is derived
from operands to avoid rounding large integers. No dates or closure invented.
Every response states ANNUAL_LABEL_ARITHMETIC_ONLY and financial comparability
NOT_ESTABLISHED. No new canonical source, decision, outcome or learning.

A6: frontend requires those exact scope markers and coherent status/changes/
uncertainty combinations. Numeric magnitudes beyond the browser safe-integer
range refuse display rather than silently round. This is not a complete exact-
decimal transport contract. The panel explicitly discloses that duration,
coverage, perimeter and accounting conventions are not established. Existing
fact/analysis references and causal disclaimer remain. An old backend lacking
the markers becomes visibly unavailable, not silently accepted.

Evidence: backend/tests/test_temporal_comparison_safety.py and existing temporal
tests; frontend temporal API/panel suites. Comparator fixtures use constructed
synthetic envelopes and database doubles, not independent professional evidence.
HTTP/persistence and portfolio regressions are run separately. No live database
writes, migrations, provider transport or real data. A5/A6 are LOCAL_TESTED,
NOT LIVE_PROVEN and NOT GIT_CHECKPOINTED. The twelve-family Financial Reliability
Gate, full interval comparability, real two-user RLS and actual multi-period
upload/browser proof remain OPEN. External Provider CLOSED; Real-data Admission
CLOSED; Self-Selling DEFERRED. No Founder action needed for these local slices.

Final validation on 2026-09-16: 187 backend tests across 15 modules PASS
(3 dependency warnings), 36 frontend tests across four suites PASS, TypeScript
no-emit PASS. Working-tree diff whitespace check PASS. Ten scoped files remain
local (six implementation/test files and four Canon files); HEAD unchanged at
`dc7a14fda86f23e3ea653ccb73dc9b16533f17b1`. No commit/push performed. Batched
checkpoint model retained; no per-slice Founder Git intervention requested.

## A7 — multi-client later-period persistence proof (2026-09-16)

WHY: the CFO needs the prior facts of the exact client, not whichever record was
uploaded last. BEFORE A3 proved three-client reload and no-prior UNKNOWN only.
AFTER test_v1_multiperiod_persistence.py builds parsed synthetic sources, passes
them through real financial understanding, a declared local mock response,
response validation, envelope construction, real save/hash/binding logic and
HTTP comparison after in-memory database reconstruction. Current periods are
inserted before prior periods deliberately. Three clients retain their own prior
analysis/fact references: EBITDA deltas +50 and -70, while a missing intermediate
year refuses a delta. Reads leave storage unchanged. Substituting another
client's prior payload without its binding causes HTTP 503, not an accepted delta.

No new ingestion route, registered workbook, database migration or live write.
This proves the bounded composition from parsed source to persisted comparison,
NOT real workbook multi-period admission, browser integration, process restart,
live RLS or professional financial correctness. Authentication/database remain
test doubles. General comparability stays NOT_ESTABLISHED.

Additional falsification: test_v1_analysis_contract.py pins existing NaN/+Inf/
-Inf refusal before understanding or request creation. Inspection found strict
JSON canonicalization already provides this guarantee; no redundant runtime
change was retained. No provider transport occurred.

Final combined run: 191 backend tests across 16 modules PASS (3 dependency
warnings). A5/A6/A7 remain LOCAL_TESTED, NOT LIVE_PROVEN and checkpoint pending.
This cumulative batch now spans comparison semantics, terminal interpretation
and multi-client persistence proof; checkpoint before further expansion to
preserve a clear regression/recovery baseline. Planned commits: six A5/A6
implementation/test files; two A7/falsification test files; four Canon files.
No gate is promoted. External Provider CLOSED; Real-data Admission CLOSED;
Self-Selling DEFERRED.
