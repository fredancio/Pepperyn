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

## A5–A7 checkpoint confirmation

Founder confirms three commits synchronized through
`74d01fb849b4cf961ae4089d4276ecfe55bbc34c` with no remaining entries. These
bounded local proofs are now durable, not LIVE_PROVEN.

## A8/A9 — client availability and scoped history (2026-09-16)

WHY: a CFO must not select a fabricated client after a read failure, repeat a
confirmed creation merely because refresh failed, or see an older response
overwrite the current client's history. Grounding: Golden Workflow, UNKNOWN
invariant, No Silent Regression and ADR-002/T2A atomic Entity+Engagement creation.

A8 BEFORE: list errors became empty success and a selectable placeholder client;
failed post-creation refresh left the creation form open. Default workspace
resolution chose the first row; an empty RPC result could look successful.
AFTER: list errors return safe 503, failed/malformed client responses refuse,
loading/empty/unavailable remain distinct and retry only reads. No placeholder.
Confirmed creation closes the form before refresh; the API unwraps the entity.
Ambiguous default workspaces refuse before RPC. Missing creation confirmation
returns 503 with a verify-list instruction. No automatic write retry or new
idempotency claim for network-ambiguous writes. Plan/auth/atomic SQL unchanged.

A9 BEFORE: late history responses could overwrite another client's selection;
HTTP failure became empty and caught failures were silent. AFTER: history results
are bound to current selection/latest request, invalidated on selection change
or unmount; other-scope stored lists are suppressed. Failures are visible, not
empty-success claims. This is frontend race isolation, not proof of backend
completeness, arbitrary payload authorization, live RLS or user-switch isolation.

Evidence: entity router/engagement mocks; API tests; rendered ChatContainer
with mocked auth/API/child surfaces proves placeholder absence and read-only
retry after successful creation/failed refresh; hook tests cover late-client,
same-client ordering and failure. JSDOM, not browser-E2E. Combined regression:
210 backend tests across 18 modules PASS (3 dependency warnings), 45 frontend
tests across six suites PASS, TypeScript no-emit PASS.

A8/A9 LOCAL_TESTED, not checkpointed/live. No migration, live write, real data
or provider call. Shared central client context and creation/read semantics now
form a durability boundary before wider workflow work: eight implementation/test
files plus four Canon files. External Provider CLOSED; Real-data Admission
CLOSED; Self-Selling DEFERRED. No financial/Beta/RLS gate promoted.

## A8/A9 durability confirmation

Founder confirms both commits synchronized at
`6dc4e9fcb228821b6e750f55df21e06ddeb299f0`, RemainingEntries=0.
The initial checkpoint stopped before commit after staging eight files: mixed
line endings made filtered hash-object differ from the raw indexed api.ts blob.
Raw index bytes and the pinned validated SHA256 matched. No product content was
reset. The corrected checkpoint accepts only the pinned raw or Git-filtered
blob, verifies exact staged scope and safely resumes it. This is not an ACL fix.

## A10/A11/A12 — terminal session context (2026-09-16)

WHY: prior history-list scoping is insufficient if the opened result itself can
arrive late under another client or replace a newer analysis. No Silent Regression
requires unavailable governed results not be silently replaced by another path.

A10 BEFORE: loadSession had no request-generation guard; every governed error
fell back to legacy messages. AFTER: latest operation/selection invalidates old
success and failure results, including new conversation and unmount. Client
switch clears the prior session identifier and analysis-interaction state.
Governed API reads require the requested analysis ID and an object result.
In synthetic V1 mode, any governed failure is explicit with NO legacy fallback,
including 404 (which can also represent integrity/ownership refusal). This does
not certify the entire response schema. Legacy direct reads remain outside
synthetic mode and now show read errors without private diagnostics.

A11: mock workbook, registered inspection and fixed synthetic demo responses
obey the same operation-generation boundary. Navigating away suppresses obsolete
display; requests already sent are not cancelled, rolled back or repeated.
This does not establish global race protection for generic legacy uploads/chat,
deletion races, auth-user switching, live RLS or backend persistence cancellation.

A12: compatibility testing exposed an existing one-message history rendering
bug: message count=1 was treated as an empty welcome screen. The terminal now
distinguishes the actual local welcome ID from a stored message. A stored single
legacy message renders; legacy read failure remains visible. No backend change.

Evidence: ChatContainer.clients tests cover stale success/failure, newer analysis,
new conversation, client-switch during mock analysis, demo/inspection suppression
and no duplicate request; legacy-read tests cover direct-read compatibility and
single-message rendering; API tests reject wrong ID/missing result. Final run:
87 tests across 10 frontend suites PASS, TypeScript no-emit PASS. Includes the
governed intention/decision/follow-up/execution card regressions. Tests use JSDOM
and mocked API/auth/child surfaces, not browser-E2E or real data. Backend unchanged;
no fresh backend regression claim is made for this batch.

Status: LOCAL_TESTED, NOT LIVE_PROVEN, NOT CHECKPOINTED. Five frontend files plus
four Canon files form a coherent session-lifecycle checkpoint before further
central ChatContainer work. External Provider CLOSED; Real-data Admission CLOSED;
Self-Selling DEFERRED. No Private Beta or financial-reliability gate promoted.

## A10–A12 durability confirmation

Founder reports two scoped commits synchronized at
`dc69e0fc7e6756606504df06865296e017bcbe9f`, RemainingEntries=0.
This is checkpoint evidence, not live/browser proof.

## A13/A14 — two-user beta admission and public signup route restriction

WHY: exact two-user authorization and no public signup are explicit Beta entry
requirements (Canon 13/21). The repository previously had only per-route auth,
guest login and a public registration page, not a global two-tester boundary.

A13 implements additive verified-user allowlisting for backend HTTP requests.
Production cannot disable it; explicit beta development mode is available for
validation but has NOT been enabled. Configuration requires exactly two distinct
Auth UUIDs. Startup/runtime configuration failures refuse; auth-service failures,
unknown users and duplicate Authorization headers refuse before endpoint work.
Existing ownership/admin checks still execute for admitted users. PIN surfaces
and checkout/portal refuse in beta. Ordinary development remains unchanged.

A14 adds Next middleware restriction of registration/checkout routes in a
production build or explicit beta mode, without touching login/callback. Direct
Supabase signup and database permissions are outside this route-level proof.

Evidence: test_private_beta_access.py uses mocked Auth, real ASGI middleware and
HTTP requests including actual main.app denial paths and lifespan refusal.
Tests verify both allowed identities, third-user denial, no credential leakage,
configuration refusal, no route-auth bypass, immediate configured-list revocation,
guest/commercial denial, CORS preflight and unchanged ordinary development.
Frontend tests exercise NextResponse and middleware policy with a literal matcher;
not a deployed matcher/browser test. Targeted backend regression: 62 tests across
8 modules PASS (3 dependency warnings). Frontend: 92 tests across 11 suites PASS;
TypeScript no-emit PASS. No real accounts, real data, external LLM or live writes.

Status IMPLEMENTED / LOCAL_TESTED / NOT ACTIVATED / NOT CHECKPOINTED. Backend
global admission is a security-sensitive durability boundary before further auth
or deployment work. Canon 13 records configuration and actual activation evidence
still required. Production build/deployment, effective Supabase signup settings,
live token verification, RLS/storage/RPC privileges, account lifecycle, exact beta
tenancy and professional financial reliability remain unproven. No Beta/security
gate is closed. External Provider CLOSED; Real-data Admission CLOSED; Self-Selling
DEFERRED. No deployed environment or credential configuration was changed.

## A13/A14 durability confirmation

Founder reports scoped checkpoints synchronized at
`06d19c2e1293767f8c75916986c496fe951a776f`, RemainingEntries=0. Repository HEAD
and clean worktree verified at start of this turn. Remote equality is Founder
evidence, not a new ls-remote observation. No activation or gate promotion.

## A15 — usable professional Beta entry and production-build evidence

BEFORE: Beta backend rejects PIN and frontend blocks signup/checkout, but login
still offers guest PIN, public signup, commercial redirect and an Administrator
label. This obstructs the second professional without representing actual roles.
AFTER: server-only shared surface policy supplies a boolean to the login screen.
Beta offers password login and recovery, invitation notice and professional
wording. It offers neither PIN nor signup and redirects only to the existing
chat/portfolio/settings workspace. Ordinary development retains legacy options.
Existing Supabase authentication/backend authorization are unchanged; no role is
granted by the UI. Login is dynamic so server configuration is not frozen at build.

Evidence: 100 frontend tests in 12 targeted suites PASS, including login policy,
mocked sign-in redirects, development compatibility and prior governed chat tests.
TypeScript no-emit PASS. Next 15.5.24 production build PASS with existing image/hook
warnings, synthetic non-credential key and loopback-only Supabase/API URLs, no .env
files. Built login is dynamic. No real account or backend was contacted by this
build. Explicit ES2017 target retains Next's build-required configuration without
its formatting churn; generated next-env changes restored to prior content/EOL.

HTTP smoke script `frontend/scripts/check-private-beta-http.cjs` is prepared but
NOT EXECUTED. Work denied the local server-launch command before process creation,
including after a network permission grant. No workaround or alternative transport
attempted. Build success does not establish middleware behavior on HTTP, browser
hydration, credential login, recovery delivery, live Auth, RLS or deployment.
Status LOCAL_TESTED / LOCAL_BUILD_PASS / HTTP_PROOF_BLOCKED / NOT_CHECKPOINTED.

## A16 — financial professional-oracle preparation

WHY: Canon 20 requires independent expected professional findings, not more tests
which merely confirm an agent-authored mock output. Existing semantic Golden cases
explicitly test deterministic models, not professional extraction/analysis quality.
No financial engine or current analysis chain is extended for architectural closure.

`docs/Product/PEPPERYN_PRIVATE_BETA_FINANCIAL_REVIEW_CASEBOOK_V1.md` contains twelve
synthetic, numerically specified draft contracts aligned one-for-one with Canon 20:
source conventions, proposed facts, UNKNOWN/CONTRADICTION, prerequisites, forbidden
claims, tolerances and separate review/execution records. All reviewer identities,
dates and approvals remain UNASSIGNED/PENDING. No actual result, workbook admission,
input-hash evidence, UI/export run or independent approval is invented.

Status DOCUMENTED_DRAFT / INDEPENDENT_REVIEW_PENDING / NOT_CHECKPOINTED. This is a
review artifact, NOT twelve executed cases, NOT canonical financial doctrine and
NOT Financial Reliability PASS. Next professional evidence is per-case approval or
correction before freezing executable expected-result oracles. Later execution and
independent output review remain separate. Provider/RD CLOSED; Self-Selling DEFERRED.

## A17 — reviewed financial oracle freeze, not financial execution

Founder supplied the full completed FR01–FR12 independent review with clarifications
and expressly authorized reversible integration/freeze/preparation before execution.
Captured full text at `docs/Product/FinancialReliability/review-source-v2.txt`;
original attachment raw SHA256 AD1B854D9EAF0EA83893371DA8959A426BB673643C292C3E503589BC2F124E1B.
Capture changes line endings/terminal whitespace only. Reviewer identity/date
were not supplied, remain UNKNOWN; no fabricated signature or personal approval.

BEFORE: twelve draft expectations, local implementation evidence, no professional
oracle. AFTER: FR-EXPECTED-2 preserves every scenario-specific review excerpt,
formalizes PR-01..PR-08 separately, versions independent synthetic input assertions
and evaluator-only expectations, and hashes cases/sources/files. Original V1 draft
is untouched (SHA256 831E3CA935CD42C8A8CEFFF2405E9F208E6594D95BDDFFD88101809C3D88EF81).
No product analysis, runtime ontology, prompt, provider or financial algorithm changed.
Prior A15 frontend deltas are preserved, not part of financial implementation.

Frozen casebook UTF-8/LF SHA256:
`A7A78B93B473E86D61C2123DA5C6DBFDC65614F19DF6B4491EF8C39E59A59DAA`.
Frozen manifest UTF-8/LF SHA256:
`63003A44CFAB7922977C3355EDCA0C7E782E379A850EFCFD2A6359A94FA878EF`.
Manifest covers five frozen files, twelve input contracts, twelve expected-result
contracts and twenty-two synthetic sources. Baseline code hashes record inspected
implementation only, not execution proof. CRLF checkout normalization is explicit.
The manifest is integrity/version evidence, not a signature or independent review.

Read-only checker `backend/sandbox/verify_financial_review_bundle.py` and eight
unittest integrity tests PASS: frozen content, CRLF stability, tampered numeric
input refusal, foreign source/numeric basis refusal, substituted review refusal,
missing/duplicate fixture refusal and no invented gate/attribution. These execute
NO financial analysis. No provider, account, DB write, live system or real data.

Static readiness only: FR01/02/03/09/11 have bounded literal/arithmetic component
paths; FR04/06/10 expected capability refusals; FR05/07/08 need missing governed
implementation; FR12 also needs live synthetic two-user topology. No FULL_GATE_READY
case. Generic adapters and actual terminal/output professional review remain due.
FR07 current AMBIGUOUS refusal is not reviewed CONTRADICTION PASS; annual-label
COMPARABLE is not economic comparability; citation validation is not semantic proof.

No WHY conflict found with Constitution Articles II/III/VII or Profession Model
chapters 2/7/8. Canon 00/02/08/11/20 records adopted professional requirements;
Canon 10/16 records implementation/attribution debt. Do not force a new ontology or
revoke explicit human conditional decision authority to complete the reasoning chain.

Status LOCAL_FROZEN / STRUCTURAL_CHECKS_PASS / NOT_CHECKPOINTED / EXECUTION_NOT_STARTED.
Stop before gate execution and report protocol/readiness. A scoped durability
checkpoint is appropriate before using this immutable oracle in later implementation.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## A18/A19 — source consistency and bounded financial measurement — 2026-09-17

Previous A15/A17 durability confirmed by Founder; actual inspected HEAD and local
origin tracking ref `a2b0c782125bcbdca188bb688a3e4a9f634c8c03`, initially clean.
The shortened hash in the Founder message is not used in checkpoint preconditions.
A18/A19 are LOCAL_TESTED / NOT_CHECKPOINTED, not live/production or full gate proof.

A18 replaces conflict-as-ambiguity loss with retained source claims and exact
references, distinct CONTRADICTION, discrepancy measurement and investigation in
synthetic inspection/chat. No contradictory canonical facts or provider admission.
A19 implements pure explicit-definition signed-sum reconciliation with separate
reported/derived/discrepancy values and bounded UNKNOWN requests. Caller ownership
and definition authority are not established by this internal arithmetic function.

175 targeted/regression backend tests PASS; 104 frontend tests PASS; TypeScript
no-emit PASS. FR07/FR08 frozen-input component runner executed without provider,
DB write, real data or new analysis. Numeric outputs match separate frozen oracle
checks; professional/full-case approval remains absent. Source and full scope:
`docs/Product/FinancialReliability/consistency-component-evidence-A18-A19.md`.

Next: ownership-bound durable unresolved findings and terminal integration, not
more speculative reasoning or redundant arithmetic tests. Provider/RD CLOSED;
Self-Selling DEFERRED. Preserve original frozen review artifacts unchanged.

## A20/A21 — scoped source dossiers and terminal reloading

A18/A19 durable commits confirmed by Founder: `f8e01977be010e151925ac6df1c65db67c392511`
and `b3f59e2fb0c5e6b50872b1d32a9beb4fef978ae5`; local HEAD/clean tree verified.
A20/A21 remain LOCAL_TESTED / NOT_CHECKPOINTED / V35_NOT_DEPLOYED.

Distinct synthetic source snapshots preserve contradictions independently of V27
analyses, historical V18 capture and V24 confirmed knowledge. Entity/engagement
ownership, insert-only/idempotent capture, source hashes and schema are checked;
no provider, new governed analysis, canonical-value selection or decision write.
Explicit UI capture and scoped reload are behind an additional OFF-by-default flag.

389 backend PASS / 2 absent-real-file SKIP; 111 frontend PASS; TypeScript PASS.
Mock store reconstruction and HTTP/component proofs only; no actual PostgreSQL/RLS,
live restart, browser E2E or professional gate proof. V35 SQL was not executed.
No reachable local Docker daemon; no external account or credentials changed.

Full scope, inherited design reconciliation, limitations and conditional integration
protocol: `docs/Product/FinancialReliability/source-dossier-evidence-A20-A21.md`.
Persisted arithmetic reconciliation/definition authority, temporal/exports/memory
propagation remain open. FR-EXPECTED-2 unchanged. Provider/RD CLOSED; Self-Selling DEFERRED.
