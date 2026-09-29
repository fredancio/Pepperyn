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

## V35 bounded live proof — 2026-09-18

A20/A21 checkpoints confirmed: `bca16876fba1c08f6265f3880eb6513c410ae0e5`,
`4eede4adc1de11f5e6ea669be8dcec07cc3144c6`. Founder applied V35 once, inspected
configuration read-only and captured one registered conflict source. Explicit
detail GET after restart (new PID 10700) returned 200 with unchanged claims and
noncanonical semantics; no new POST. Evidence attribution, exact dossier/entity,
references, limits and local JWT recovery/rotation record:
`docs/Product/FinancialReliability/source-dossier-evidence-A20-A21.md`.

This closes only the tested synthetic live persistence debt. Not actual RLS
adversarial execution, cross-client proof, professional review, or production.
The observed retained-detail ambiguity motivates a bounded local UI correction:
clear old detail when refreshing list so an outage cannot appear to revalidate it.
No new analysis, canonical fact, provider use or live write by the agent.
Local correction validation: 112 frontend tests PASS / 15 suites; TypeScript PASS.
Working-tree-only code/docs delta, not yet checkpointed. Pre-existing generated
`frontend/next-env.d.ts` change preserved and excluded from this slice.

## A22 — source clarification portfolio — 2026-09-18

Independent read-only synthetic source section complements decisions without
creating arcs or prioritization claims. Bound 100 verified dossiers; foreign,
corrupt, duplicate, unavailable or unauthorized evidence fails closed. Two-client
mock separation, HTTP closed-mode and component/API falsifications PASS.
398 backend PASS / 2 absent-real-file SKIP; 115 frontend PASS / 16 suites;
TypeScript PASS. LOCAL_TESTED / NOT_CHECKPOINTED, no live query or write by agent.
No FR-EXPECTED-2 edit, provider call, real data or production activation.
Full before/after/rationale/debt: `docs/Product/FinancialReliability/source-attention-evidence-A22.md`.

2026-09-19 recorded live update: agent browser read-only navigation after Founder
backend restart observed A22 source card separate from empty decision register,
correct entity link, exact V35 dossier and references, and no stale selected detail
after list refresh. One-client UI path PASS, not network/DB audit or adversarial
multi-user isolation. No capture/analysis/write control used; no gate change.
See dated live section in the evidence document above. Local code/docs not committed.

## A23 - temporal context through terminal exports - 2026-09-19

Added owned temporal-service composition to authenticated governed XLSX/PDF/PPTX
exports, without new persistence or reinterpretation. Previous/current analysis IDs,
fact IDs, values, units and unknown/contradiction boundaries survive. Historical
outage/integrity failure refuses export. Financial comparability remains unestablished.

21 new local actual-byte/HTTP falsification cases; regression selection including
temporal modules: 461 PASS / 2 absent-real-file SKIP. Frontend 115 PASS / 16 suites;
TypeScript no-emit and frozen FR-EXPECTED-2 integrity PASS. Bounded synthetic PDF pages,
XLSX temporal sheet and PPTX temporal slides rendered and visually inspected.
No live DB/provider/write or new Founder analysis requested. NOT_CHECKPOINTED.
Evidence and explicit limits: `docs/Product/FinancialReliability/temporal-export-evidence-A23.md`.

V35 closeout/A22 and A23 form the next meaningful durability batch. Shared router
and canonical records are checkpointed coherently; unrelated generated
frontend/next-env.d.ts remains preserved and excluded. Wider beta isolation,
professional financial validation, admitted-data Golden workflow and production
gates remain open. External Provider/RD CLOSED; Self-Selling DEFERRED.

## Durability update and A24 - 2026-09-19

Founder confirmed V35/A22/A23 checkpoints 20900c097de48a7e281327853a1417f81f49608f
and 1bd73b2fa6649b6e9de44908064271506b1627f1 synchronized. Local HEAD verified at
the latter. This supersedes earlier NOT_CHECKPOINTED notes, not their proof scope.
Generated frontend/next-env.d.ts remains excluded and preserved.

A24: live metadata-only Integration Test audit established missing RLS/client
privilege containment and exposed entity-creation RPC. V36 migration plus read-only
postflight prepared, not applied. 9 local PostgreSQL-engine scenarios PASS,
56 targeted backend and 115 frontend tests PASS. No business-row reads or writes
in Supabase, provider calls, real data, credentials or Auth changes. Full source,
before/after, evidence and explicit debt: `docs/Security/PEPPERYN_V36_PRIVILEGE_CONTAINMENT_A24.md`.
Actual two-user Supabase adversarial proof remains OPEN. A24 NOT_CHECKPOINTED.

A24 live update: Founder-approved V36 applied once; SQL Editor success and versioned
catalog postflight all table/RPC checks true. One-user source portfolio rendered
existing synthetic evidence after read-only retry (initial unavailability cause
unestablished). No business write/provider/account creation. V36 catalog containment
is LIVE_PROVEN_INTEGRATION, not two-user API/DB/browser or production isolation.
Working-tree evidence awaits a grouped checkpoint; detailed record in A24 above.

A24 technical accounts authorized next; protected Founder-local provisioning
procedure prepared because agent has no Supabase keys. Parser/check-only and eight
mock scenarios PASS; no live users created yet. New user passwords are DPAPI-bound
before first write; existing-attempt file blocks reruns. No gate/allowlist/provider
change. See account preparation section in the A24 security evidence document.

Founder provisioning result supersedes pending account creation: two technical Auth
users/scopes and protected credentials reported PASS; no secrets transmitted.
Bounded real-session READ adversarial runner prepared, not live-executed. Five local
unittest methods / 15 mock scenarios and PowerShell CheckOnly PASS. Requires local
DPAPI restoration plus anon key only; no service key or reprovisioning. Global
two-user isolation, writes and populated financial outputs/exports remain OPEN.

2026-09-20 Founder live result: BOUNDED_TWO_USER_READ_ISOLATION_PASS; existing DPAPI
unchanged; one execution after backend restart. This supersedes NOT LIVE EXECUTED
for the exact two-account read suite, not global isolation, write isolation,
analysis/export isolation or production (all explicitly false in returned result).
No new business write/provider or secret disclosure. A24 now reaches a meaningful
durability checkpoint before further implementation. Full scope remains in A24.

## A24 durability and A25 history boundary - 2026-09-20

Founder confirms commits 1ebe5752714284a1ad30fde90001911aa676b20b3 and
78059c213c2e6eb57092abc3bb5433eb5c915a40 synchronized; local baseline matches.
This supersedes A24 pending-checkpoint statements only. next-env.d.ts is preserved.

A25 corrects false-empty history failures and enforces explicit entity ownership
plus response binding. Six local HTTP tests and seven provisioning/read-runner
test methods PASS; 116 frontend tests PASS. Live history-scope continuation is
prepared with existing accounts and no business writes, NOT EXECUTED. Details and
limits: `docs/Security/PEPPERYN_HISTORY_READ_BOUNDARY_A25.md`. Local changes not yet
checkpointed. No global isolation or admission gate is closed.

### A25 final bounded closeout - 2026-09-20

Founder reports one history rehearsal: BOUNDED_HISTORY_SCOPE_READ_PASS and existing
DPAPI unchanged. This supersedes NOT EXECUTED above only for the runner's bounded
own-empty/foreign-refused/anonymous-refused history checks. Populated history,
global isolation, writes, analysis/export isolation and production remain false.
Final rerun: 13 backend unittest methods and 116 frontend tests PASS. No live
replay or new write by agent. A25 functional/documentary scope complete, local
changes NOT_CHECKPOINTED; pre-existing next-env.d.ts remains excluded.

New Founder Operating Protocol read and acknowledged: V1 scope freeze; classify
work as REQUIRED / FIX-BLOCKER / POST-V1 / REJECTED; convergence over expansion;
no stack replacement without concrete blocker. A25 is FIX-BLOCKER. Per the latest
explicit stop instruction no subsequent workstream has begun. Wider V1 state
reconciliation is pending before further significant development, not claimed
complete here. Await new Founder instruction. External Provider/RD CLOSED and
Self-Selling DEFERRED remain unchanged.

## A25 durable / A26 preflight preparation

Founder confirmed A25 commits 9281ee7749bc416588a82d6bc4bfc0ab81eaed8b and
3a80529b513ce255d36ae57ab0c52d575ff50f80 synchronized; local HEAD matches latter.
This supersedes A25 NOT_CHECKPOINTED and stop state after new resumption instruction.
A26 state reconciliation and bounded read-only technical-scope preflight prepared:
`docs/Security/PEPPERYN_POPULATED_HISTORY_A26.md`. Four methods / ten scenarios
locally tested; PowerShell CheckOnly PASS. Live preflight pending local protected
credentials. No seed, mutation, gate widening or populated-history proof. Existing
next-env.d.ts preserved; no product implementation changed by A26 preparation.

A26 Founder live preflight: A26_SCOPES_INSPECTED once, both technical scopes have
zero analyses and zero envelopes; DPAPI unchanged, no business writes. This
supersedes preflight LIVE_PENDING, not any isolation proof debt. The existing
registered English fixture was locally executed successfully through its
deterministic mock without DB/provider calls. Next proposed operation is two
synthetic analysis/envelope pairs in the existing technical scopes via V27;
explicit remote-write authorization pending. No seed performed and no gate
expanded. Detailed write/recovery boundary in the A26 evidence document.

A26 Founder GO supersedes pending authorization for exactly two synthetic pairs.
Seed runner/wrapper locally validated (four seed methods and four preflight
methods; CheckOnly PASS). Existing V27 transaction per pair, stable IDs, repeated
scope checks and verified rereads; no retry/upsert/delete. Two-pair atomicity not
claimed. Await Founder-local protected credential execution; no live seed by agent
and no isolation proof promoted. See A26 document for limits and recovery rules.

A26 seed now Founder-reported once: two acknowledged/verified synthetic pairs,
DPAPI unchanged, business_write_performed=true. Isolation flags remain false.
Dedicated session-only populated-history read verifier prepared (positive plus
ten falsifications local PASS); no service key, no new writes/provider. Live
cross-user verification pending protected Founder execution. Scope remains
history GET metadata for the two exact fixtures, never global/output/write proof.

A26 populated read refused live at USER_1_ENGAGEMENT. No history isolation PASS.
V19 documents backend-only engagement access; verifier assumed direct client
visibility without an established contract. Exact live denial vs empty vs other
failure remains unknown. Read-only differential diagnostic prepared/tested; no
V36, persisted pair or permission changes. Details in A26 evidence document.

A26 differential diagnostic Founder result: both user engagement queries 200/empty,
both persisted seed bindings verified, no writes. Corrected test harness uses V19
service-only engagement reference lookup while every history GET uses user sessions.
Local positive/ten falsifications and CheckOnly PASS; corrected live run pending.
No product or privilege changes, no repopulation, no populated-history proof yet.

A26 corrected Founder live run PASS on 2026-09-21: bounded populated histories
only, reference service read separated from user-session history probes. No
business write, unchanged DPAPI; write/output/global/production proof flags false.
Supersedes pending corrected run above. A26 durability batch now warranted before
legacy decision-feedback mutation-boundary investigation; no live mutation probe
executed. Detailed scope and preserved failures in A26 evidence document.

## A26 durable / A27 feedback authority — 2026-09-21

A26 HEAD verified locally at 4094416b69ec0e3af893ab56f65238edc2eb2196;
Founder confirms remote equality and two commits/17 files. Supersedes pending
durability, not wider proof debts. A26 pairs and excluded next-env.d.ts untouched.

A27 FIX-BLOCKER: legacy feedback route now validates owned completed analysis and
persisted recommendation before side effects; governed reports must use V1.
Shared V1 persistence remains unchanged. 44 targeted local tests PASS (feedback
authority, V1 synthetic routes, decision-memory repair, history read boundary).
Deployed read-only catalog inspection independently found direct client write
grants plus company-only RLS on decision_feedback. No exploit/write attempted.
V37 containment prepared, not applied; approval required before remote permission
change. Details: docs/Security/PEPPERYN_FEEDBACK_WRITE_BOUNDARY_A27.md.
Local NOT_CHECKPOINTED; no live write isolation PASS. External Provider/RD CLOSED.

Final A27 run: 46 tests PASS including two static migration checks; these do not
establish PostgreSQL execution. Repository-wide whitespace check still flags the
pre-existing excluded next-env.d.ts; it was not changed. Scoped check excludes it.

V37 Founder GO received and migration applied once in Integration Test: success.
Independent postflight confirms client table/column write grants absent, RLS and
service CRUD retained. Six SQL-role DML refusals across exact A24 identities PASS,
all predicates false and rollback: no business changes. Not JWT-session/API proof.
49 local tests and protected-runner CheckOnly PASS. Actual user-session direct DML
denial runner prepared; local anon credential required. A26 untouched. No global
write isolation claim; no production/provider/real-data activation. See A27 doc.

A27 Founder real-session runner executed once: six direct DML denials PASS;
authority TWO_REAL_AUTHENTICATED_USER_SESSIONS and scope
DECISION_FEEDBACK_DIRECT_TABLE_PRIVILEGES_ONLY. DPAPI unchanged, no business write.
API/write/global/output/production flags remain false. Supersedes live-run pending.
A28 API preparation identifies separate legacy fixtures as necessary for positive
writes: A26 governed reports must remain rejected by this endpoint. Local two-
identity HTTP matrix added; auth/DB doubles only. Bounded seed/feedback/pattern
authorization pending; no new remote writes. See A28 protocol. Not checkpointed.
Final targeted rerun: 50 tests PASS, including the local two-identity HTTP matrix.
Synthetic auth doubles are not a live session claim. No gate widened.

A28 bounded write GO received. Runner implemented with explicit seed/authorized
feedback/adversarial counters, no retry, two-scope before/after comparisons and
unchanged A26 pairs. Five local harness tests PASS; real route/service exercised
with synthetic auth/DB doubles. Read-only running-backend check: reachable but
new authority marker absent. No seed or API POST attempted; backend reload and
protected local credentials required. Canon A28 protocol records this blocker.
Final regression: 55 tests PASS; scoped whitespace check PASS. Live remains pending.

Founder backend restart followed by agent read-only check: A28GuardLoaded=true.
Protected A28 PowerShell runner hash/check-only validated; local keys absent in
agent process, so Founder masked execution required. No A28 write or live API PASS.

A28 first execution refused before seed/POST (all five counters zero). Read-only
Integration diagnosis 2026-09-22 proves user_patterns table absent; both technical
scopes still contain one A26-marked analysis/envelope and zero A28/feedback/arcs.
Runner's broad stage masked a dependency read error. Precise per-table stage and
regression added; no empty fallback. V38 backend-only restoration of V7 table
prepared NOT_APPLIED pending Founder approval. 58 local tests/CheckOnly PASS.
No remote writes, no V37/A26 mutation or live A28 isolation claim. See A28 protocol.

V38 Founder GO executed once on Integration Test, 2026-09-22: migration query
bdbcea94-dcb7-4833-b7d6-a3e2201b94a8 succeeded. Read-only postflight query
065e3faa-f170-492b-952e-846ccb01b82f confirms empty user_patterns, RLS on,
zero policies, expected PK/FK and enabled timestamp trigger, no anon/authenticated
table/column rights and backend SELECT/INSERT/UPDATE only. V37 client table write
denials remain in place. No business DML, A26 change or A28 rerun. This supersedes
V38 NOT_APPLIED, not A28 pending proof. Local documentation not yet checkpointed.
External Provider/Real-data Admission CLOSED; wider isolation claims remain OPEN.

A28 next Founder run seeded 2/2 fixtures then refused at ANONYMOUS_DENIAL, no
authorized POST attempted. Read-only query 1f9d8dab-ba59-4d55-a942-97cca1b79865:
each technical scope has one A26 analysis/envelope, one A28 analysis, zero
feedback/patterns/arcs. Preserved without mutation. Verifier anonymous JSON lacked
Content-Type; local transport reproduction yields 422 before auth versus expected
401 for valid JSON. Minimal verifier header fix and eight local tests PASS.
Historical response status was discarded and remains UNKNOWN pending log evidence.
No live API isolation claim. Old seed wrapper must not be rerun; integrity hash
now refuses corrected source until a safe existing-fixture continuation is ready.
V37/V38 and gates unchanged; see A28 protocol for limitations.

A28 Founder LIVE PASS 2026-09-23 (supersedes pending continuation below):
BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS, existing-only, two fixtures verified,
zero new inserts, two authorized unsure writes and two pattern rows verified,
fifteen adversarial refusals. A26 snapshots unchanged, no arcs, DPAPI unchanged.
Business writes=true; API isolation=true ONLY for A28 legacy unsure scope.
Broader write/analysis-export/global/production flags=false. Preserve all rows;
no rerun. Provider/Real-data CLOSED. Evidence recorded locally, not checkpointed.

Founder subsequently recovered the original POST log: 422 Unprocessable Entity;
historical status now confirmed, no new request. Verifier defect confirmed, not
an A28 PASS. Existing-only continuation prepared: mandatory explicit mode, zero
fixture inserts, exact original field/scope checks, refusal of existing feedback,
before/after snapshots and numeric HTTP diagnostics. 24 targeted local tests and
protected-wrapper CheckOnly PASS. Live continuation still pending Founder local
execution; A26/V37/V38 unchanged. No cleanup, reseed or remote business write by
agent. Current work remains local/uncheckpointed, admission gates CLOSED.

2026-09-23 durability: Founder confirms A27/A28 checkpoint 999ba51b1f1f3d6a5def46dac5d377b644dd7529,
local=remote, only excluded next-env.d.ts remains; agent HEAD/status match.
Supersedes pending durability for V37/V38/A27/A28, not their bounded proof scopes.

A29 prepared: isolated ASGI GET-only analysis/export verification, one designated
technical company per phase, real-session/persisted A26 execution pending. No
change to product guard or backend 8000. Service adapter refuses mutation/RPC;
eight positive parsed outputs and twenty-four denials required. Local doubles
are not live proof. Running-server/middleware/browser/global/production isolation
remain open. See PEPPERYN_GOVERNED_OUTPUT_ISOLATION_A29.md. No remote A29 run yet.

2026-09-23 Founder A29 PASS: real-session persisted A26 isolated ASGI GET scope,
8 positive outputs / 24 denials, no business writes, DPAPI unchanged. No transport,
global/write/production proof. Supersedes A29 pending, never those open flags.
A30 temporary Uvicorn/main.app/lifespan/Private Beta transport delta prepared;
single-company guard preserved with sequential isolated designation. GET-only
outer containment and service read-only adapter remain explicit test restrictions.
62 local tests and wrapper CheckOnly PASS; actual real-session A30 pending.
No remote mutation, port 8000 change, migration or admission opening.

Founder A30 PASS 2026-09-23: eight positive outputs / twenty-four denials,
REAL_SESSIONS_A26_TEMPORARY_LOOPBACK_UVICORN_READ_SURFACE; transport=true only
there; no business writes, global/write/production=false, DPAPI unchanged.
Provider/Real-data CLOSED. A29/A30 evidence local, not yet checkpointed.
Next actual browser proof blocked on frontend connection refused at port 3000;
backend port 8000 health read succeeds in development. No new financial analysis
or mutation attempted. Existing client designation must remain unchanged.

A31 2026-09-23: frontend restored by Founder. Agent browser observed existing
Optilux history load, reload/reopen of UUID 75132a71-c80c-4469-aba8-5171d947a9d0,
lifecycle restitution and three downloads (new file hashes in A31 protocol).
Bounded single-session navigation/download PASS, not two-user browser isolation
or fresh export render/content acceptance. Temporal CONTRADICTION remains an
explicit refusal; historical intention wording conflicts visually with later
confirmed decision. Reservations preserved, no underlying records modified.
See docs/Security/PEPPERYN_BROWSER_READ_REHEARSAL_A31.md. Both gates CLOSED.

A32 2026-09-23: two A31 reservations treated separately. Exact temporal refusal
branch is same normalized current-period key in another integrity-checked envelope
within company/entity/engagement; rules untouched. UI explains reference ambiguity
versus conflicting amounts and required governed resolution, never latest-wins.
Competing row IDs/history not independently audited; no records modified/deleted.
Decision card now conditions intention wording on actual confirmed state; immutable
analysis decision text explicitly historical. Full frontend 120 tests / TypeScript
PASS; targeted backend 41 PASS. Actual same-session browser reload/reopen confirms
corrected text and preserved lifecycle; NOT two-user browser isolation. See
docs/Product/PEPPERYN_TERMINAL_STATE_REVIEW_A32.md. Local/uncheckpointed; gates CLOSED.

2026-09-24: subsequent Founder reports establish A29–A32 durability and the current
Founder/Governance base c4b414f17f63025032943159bc121c5901f65225. B1 memory-read
correction is local, not yet checkpointed. Four registry outages are explicitly
UNKNOWN in UI and refuse exports; independent analysis remains readable. No live
records, gates or deployment changed. B5 target preparation is documentary and
does not establish configured environments or a working generic Beta path.
See INSIGHT_SHAPER_B1_MEMORY_READ_CONTRACT.md and
INSIGHT_SHAPER_B5_DEPLOYMENT_PREPARATION.md under docs/Project_Control/.
Final checks: 60 targeted backend tests PASS, 17 frontend suites / 121 tests PASS,
TypeScript no-emit PASS. These local results do not promote any live, financial,
privacy, provider, real-data or production gate. next-env.d.ts remains excluded.

Founder d01851f7f86de47a0ccca3a4cb4cbde0f31da443 synchronization establishes
durability of that preceding block only. B1 shared read boundary is subsequently
LOCAL_TESTED with 88 backend tests PASS: own/cross mocked scopes, unavailable
lookups, integrity failure without legacy fallback, invalid IDs and ambiguous
engagement, plus existing lifecycle/export/temporal/isolation regressions. No
new HTTP route, migration, deployment, business write or external call. Not a
full B1/Beta/Financial Reliability PASS. Scope and next debts are recorded in
docs/Project_Control/INSIGHT_SHAPER_B1_SHARED_READ_BOUNDARY.md. Pending checkpoint.

Founder dd8a99868a3fd68b8038fddc9f5c0399eec00fe0 synchronization supersedes that
pending-checkpoint state. Next B1 provenance preparation: 96 local tests PASS;
single mocked RPC binding and fail-closed acknowledgement, no provider/remote data.
V39 SQL checked statically only; no running local PostgreSQL. Migration NOT applied,
no receipt or analysis written remotely, no existing row backfilled. Not live
atomicity/RLS/financial/production proof. Pending durability checkpoint; see
docs/Project_Control/INSIGHT_SHAPER_B1_EXECUTION_PROVENANCE.md.

2026-09-24 V39 deployment proof supersedes MIGRATION_NOT_APPLIED only: code base
1b729888df2de776a9e8cf18440faf9aba2879e2 synchronized per Founder, inspected locally.
Explicitly approved Integration Test project ejixkplrgobgwqnhidwt visually verified;
two read-only catalog prechecks conforming; committed migration applied exactly
once, SQL Editor `Success. No rows returned`. Read-only postflight: expected eight
columns/seven validated constraints; RLS=true, policies=0; clients no table/RPC
privileges, service SELECT-only table and EXECUTE-only persistence entry point;
PUBLIC ACLs absent; fixed function search_path and enabled immutability trigger.
receipt_count=0. No RPC call/business write, no synthetic write rehearsal or
provider call. This proves deployed schema/permissions, NOT live receipt atomicity,
restart, replay, adversarial enforcement, B1, financial reliability or production.
Separate authorization required for prospective synthetic persistence rehearsal.
Details/hash in B1 execution-provenance document. New documentation local pending
durability checkpoint; External Provider/Real-data Admission remain CLOSED.

V39 rehearsal preparation (same date): Founder authorized four calls / at most
three durable synthetic rows, existing technical account 1 only. Harness and
Windows wrapper locally verified: 39 tests PASS plus actual runtime CheckOnly.
Fresh read-only deployed RPC/trigger inspection conforms, receipt_count=0.
NO LIVE REHEARSAL YET: Supabase keys unavailable in agent process; requires one
Founder-local masked-input execution. Exclusive manifest blocks reruns; second
Python process performs business-read-only recovery after first process exits.
See B1 execution-provenance preparation addendum for exact scope, failure handling
and residual debts. Local/uncheckpointed; no B1/gate promotion.

V39 live closeout 2026-09-24 supersedes the preceding NOT RUN LIVE state. Founder
reports BOUNDED_V39_PERSISTENCE_RECOVERY_PASS after first process exited, with
three durable rows, P0001 binding denial, 23514 late rollback leaving no trio,
23505 exact replay denial and unchanged existing scoped rows. Agent inspected
the local manifest read-only: four attempts; scoped counts 2/1/0 -> 3/2/1;
pre-existing hashes identical. Positive UUID 5c441eb9-99fc-55eb-bd33-da29d1fc2ba5.
Second-process proof is Founder-reported terminal evidence; manifest deliberately
retains first-process-complete status and must not be reset/rerun. Exact artifact
hashes and evidence limits are in the B1 execution-provenance live addendum.
No new remote action during closeout. No global B1/HTTP/browser/isolation/production
proof. Gates CLOSED; retained synthetic rows only. Harness and documentary delta
remain local pending durability checkpoint, not part of the current HEAD.

Founder V39 durability confirmed; locally verified exact checkpoint is
2348e77145b25644bcdcfd22a43afb5e5f339a81 (corrects the reported transcription).
Subsequent B1 governed output composition is local only: 117 tests PASS, including
receipt-to-three-export content, local ASGI owned/foreign/admission failures,
unattested legacy behavior and regressions of shared reads/synthetic outputs/
temporal/execution provenance. No external writes or running-server change.
Router factory is deliberately unmounted; test dependencies are not admission
authority. No real-session/browser/RLS/visual/financial/global B1 promotion.
Scope/remaining debts: docs/Project_Control/INSIGHT_SHAPER_B1_GOVERNED_OUTPUT_COMPOSITION.md.
Local files pending grouped checkpoint; both gates CLOSED, Self-Selling DEFERRED.

2026-09-24: preceding output-composition block synchronized at
17ff325d26530b76a026c2260d045577228ff223. Subsequent connected-pipeline block:
155 targeted backend tests, all 128 frontend tests and TypeScript PASS. Local
proof connects upload, owned scope, raw hash, serialized V39 receipt, recovered
read and all three exported UUID/hash disclosures. Real main composition tested
with substituted authentication/database; no claim of live HTTP/browser/SQL/RLS.
Generic parser variation is not arbitrary-source execution admission. The only
installed producer remains registered synthetic mock; new transport flags remain
off in the running environment. No remote mutation/provider/data admission.
See INSIGHT_SHAPER_B1_CONNECTED_PIPELINE.md for exact next authorized rehearsal
boundary. B1 OPEN; local changes pending durability; next-env.d.ts excluded.

Live B1 authorization received; execution pending safe credential access. Prior
to activation, a one-shot manifest/latch and loopback/exact-analysis restriction
were added and locally falsified: 162 targeted tests PASS. Windows PowerShell
preflight script integrity-only check PASS; no credentials/network in that run.
Read-only actual localhost check finds no new governed routes; browser shows
existing authenticated synthetic client. No upload/remote business mutation.
Founder must run the prepared GET-only preflight; its result is NOT presumed.
This is preparation evidence, not B1 live end-to-end acceptance or gate closure.

B1 GET-only preflight subsequently reported PASS by Founder and corroborated by
the non-secret local manifest: two existing analyses/envelopes, no receipts,
scoped lifecycle hashes; fixed prospective UUID e2dc7bd5-c71a-4c88-821c-b1f2696fb04b.
No attempt/activation marker. Exact permit expires 2026-09-24T15:40:12.249802Z.
Prepared integrity-pinned backend/frontend restart helper; both local checks and
28 focused tests PASS. No secret regeneration, running-server restart or remote
write performed by agent. Pending Founder local restart, then one authorized
application submission. B1 and both admission/provider gates retain prior state.

Later activation refused at missing parent-process environment; predecessor now
closed and preserved, no activation/analysis attempt marker. Founder subsequently
confirmed process reconstruction and existing JWT restoration, then explicitly
authorized a distinct successor with SAME prospective UUID and fresh GET-only
absence/baseline checks. Renewal helper prepared, 16 local tests PASS, local-only
PowerShell check PASS. Actual remote eligibility/successor creation pending
Founder execution in credential-bearing shell. No B1 live PASS, reset, replacement
UUID or provider/real-data gate opening. See B1_CONNECTED_PIPELINE chronology.

2026-09-24 R2 incident postflight: Founder screenshot reports
`B1_R2_NO_WRITE_POSTFLIGHT_PASS` for prospective UUID
`e2dc7bd5-c71a-4c88-821c-b1f2696fb04b`: absent in all three persistence
tables; preexisting scoped hashes and engagement binding unchanged; both closed
permits unchanged. No business write, new permit, transport activation, provider
or real data. This follows R2 backend/frontend activation and a single file
selection refused by the frontend before fetch because no client was explicitly
selected. Agent mistook a listed client for an active selection; no retry.
Both servers subsequently stopped, R2 revoked, no attempt marker observed.
Independent GET-only postflight is now live reported PASS, not analysis execution
or global B1 proof. Six local postflight falsification tests PASS separately.
Next attempt requires explicit successor authorization, same UUID, fresh baseline
checks and verified active client selection. No R3 created or authorized yet.

Subsequently Founder authorized and created R3; backend activated, frontend
refused because the old R2 Next.js process still occupied port 3000. Agent host
inspection identified that process; Founder stopped it normally and stopped R3
backend. No upload/retry, R3 closed, no attempt marker. Founder now reports
B1_R3_NO_WRITE_POSTFLIGHT_PASS: UUID absent in three tables, scoped hashes and
engagement unchanged; no writes or activation by that GET-only postflight.
Agent independently verifies host ports 3000/8000 free after shutdown. This is
bounded incident closure only, not a successful connected analysis or B1 PASS.
No R4 permit or authorization. External Provider and Real-data Admission CLOSED.

2026-09-27 R5 update (supersedes the historical pending states above): after
separate R4/R5 authorizations and verified explicit client selection, one
registered synthetic workbook was submitted through the opt-in governed path.
Browser displayed analysis e2dc7bd5-c71a-4c88-821c-b1f2696fb04b and its verified
local-mock receipt. Three exports were downloaded; full artifact review remains
pending. Founder screenshot dated 2026-09-27 10:59 reports
BOUNDED_B1_R5_PERSISTED_TRIO_POSTFLIGHT_PASS: exactly three new durable rows,
receipt binding verified, preexisting scoped hashes and closed permits unchanged.
GET-only independent postflight, no new write/activation/provider/real data.
JWT/V33 untouched. R5 is closed/expired; no replay or cleanup authorized.
23 local inspector/provenance tests PASS separately. B1-global explicitly false;
fresh browser reopening, full export review, general Beta admission and financial
reliability are not established by this result. Detailed chronology and exact
hashes: docs/Project_Control/INSIGHT_SHAPER_B1_CONNECTED_PIPELINE.md.

2026-09-27 subsequent R5 artifact audit: three original exports parsed and every
PDF page/XLSX sheet/PPTX slide visually inspected; hashes rechecked unchanged.
Bounded provenance/content/render PASS with explicit static-XLSX/native-renderer
and cosmetic PDF pagination limits. Details and SHA-256 evidence are in the B1
control document. No regeneration, upload or remote write. One fresh browser
history reopening displayed unavailable/no replacement: NOT a reread PASS.
Exact HTTP cause unavailable; code independently confirms closed permits deny
reads too. R5 remains closed; separate read-only transport authorization pending.
No B1-global, real-data, provider, professional-reliability or isolation widening.

Distinct read-only window subsequently Founder-authorized, locally prepared and
tested (4 unittest cases with negative subcases; PowerShell CheckOnly PASS).
Exact R5 UUID only, real application auth/ownership retained, GET-only data
adapter, no ingestion/export route, independent local latch, 20-minute maximum,
single successful read then closure. No R5 renewal. Live activation requires
the preserved Founder credential-bearing shell; agent has no process secrets.
Fresh browser proof remains pending, not PASS. See B1 control for implementation.

Subsequent live observation: one authorized history click freshly restored R5
result and exact receipt/source/envelope identifiers; bounded owner-read UI PASS.
No upload/export/intention/replay. Independent read-window closure observed;
R5 manifest hash unchanged. Final server-postflight status awaits terminal
evidence, not assumed. Temporal secondary legacy request remained unavailable;
local snapshot-wiring correction now avoids it and reuses the same validator.
Targeted frontend tests/typecheck PASS; no corrected-temporal live proof claimed.
Full evidence and B1 OPEN rationale are in the B1 connected-pipeline control.

Founder subsequently reports B1_BOUNDED_READ_SERVER_PASS and CLOSED, without
rerun: no business writes, R5 unchanged, no external provider/real data, no B1-global
proof. This is the terminal postflight previously awaited; browser_visual_proven
remains false in that server record, separate from the agent's observed UI PASS.
No second read-window activation. Temporal correction remains local-test-only.

Separately authorized temporal-only window subsequently consumed: one history
read restored result but card stayed unavailable, so temporal browser acceptance
NOT PASS. Closure marker observed; server postflight stdout pending. Browser
script URL matches local .next chat bundle dated September 25, which lacks the
September 27 snapshot wiring. Compiled-asset verification was missed before
consuming the window. Repair/verify frontend delivery before another authorized
read; do not reset/reuse either window. No upload/export/business write by agent.

Subsequent frontend-version verification: corrected bundle served HTTP 200,
then separately authorized browser-only reload establishes client-initialized
chat root data-temporal-contract=governed-response-snapshot-v1 in the active tab.
Marker shared with temporal component; version proof only, not output acceptance.
No analysis selected/read or permit opened; metadata lists unavailable with backend
closed. 22 targeted UI tests/typecheck PASS. Temporal result live proof remains OPEN.

Temporal-confirmation window NOT PASS: after delayed Continue, agent clicked
the single-read button at about 18:46; unavailable/no replacement. Local markers
show start 14:33:44 and closure 14:53:45 September 27. Agent failed to recheck
liveness immediately before action; previous READY was stale. No retry, reset,
R5 modification or corrected-temporal acceptance inferred. New authorization
would be required for any fresh window. B1 and admission gates remain unchanged.

Fresh temporal-confirmation R2 authorized and prepared, NOT activated: distinct
exclusive marker, three closed predecessor windows preserved byte-for-byte,
unchanged shared exact-UUID authenticated owner-only GET reader. Launcher
CheckOnly and five local boundary/lifecycle tests PASS. Fresh targeted frontend
tab shows runtime marker governed-response-snapshot-v1 and unclicked read button.
Immediate liveness check/click after READY is required; no delayed read if expired.
No business write, permit renewal, V39/producer change or live acceptance. Details
in B1_CONNECTED_PIPELINE. B1 and External Provider/Real-data Admission unchanged.

2026-09-27 temporal-confirmation R2 browser PASS, bounded exact R5 UUID only:
after READY, live marker age 87.1s/no closure/backend listener were checked, then
one targeted authenticated UI read was performed immediately. Screenshot and
accessibility tree show governed CONTRADICTION due to non-unique current-period
references, its resolution guidance, exact analysis UUID, no fabricated delta
and no causal/outcome/learning claim. No upload/export/new analysis or second read.
Window independently CLOSED at 17:23:28 UTC and port 8000 no longer listening.
Final server remote-postflight JSON remains Founder-console evidence pending;
closure alone does not prove postflight PASS. No global B1/isolation/reliability
promotion. General producer/generic governed admission remain OPEN; gates CLOSED.

Founder confirms final B1_TEMPORAL_CONFIRMATION_R2_SERVER_PASS and CLOSED,
business_write_performed=false, r5_unchanged=true, external_provider_used=false,
real_data_used=false, b1_global_proven=false. Server browser_visual_proven=false
correctly remains separate from the agent-observed visual PASS. No command rerun.
Bounded temporal closeout complete. Local durability revalidation: 126 backend
tests plus 6 subtests PASS, all 20 frontend suites/136 tests PASS, TypeScript
no-emit PASS. Initial backend invocation used the server venv without pytest and
failed import collection; rerun in the existing development test venv succeeded.
No remote tests, credentials, gates or business state changed during this review.
Accumulated B1 work still pending checkpoint; separate strategic-option deltas
and frontend/next-env.d.ts are excluded and preserved.

2026-09-28 R5 durability now confirmed: 5204b53a (76 files) followed by c1e22508
(3 documents). Founder reports successful push/local=remote; local HEAD and
origin tracking reference independently read as c1e22508fff296385014f7d82718e3e64220aa64.
This supersedes the pending statement above. Nine pre-existing exclusions remain.

Distinct generic-producer preparation: producer-execution-candidate-2 is
UNADMITTED, not a receipt or authority. Every expected scope/request/source/
producer/task/input binding is checked; copied-model and envelope substitutions
are rejected. Existing V39 application adapter rejects it before RPC. 69 local
synthetic tests PASS across candidate, v1 provenance, pipeline and persistence.
Initial run had 17 setup errors from inaccessible default pytest temp storage;
unique writable basetemp resolves this; no failure was reclassified as PASS.
No generic producer/admission integration, replay ledger, versioned persistence,
live proof or gate closure is established. See B1_GENERIC_PRODUCER_CONTRACT for
the exact next integration obligations. This preparation remains local/uncommitted.

2026-09-28 prospective composition: 199 local tests PASS across admission,
candidate, v1 provenance/persistence/pipeline, ownership, projection, response
quarantine and correspondence. Tests assert unchanged database tables, no RPC,
zero socket attempts, one concurrent consumption, expiry/closure/replay refusal,
all-field substitution refusal and authoritative parent rechecks. Fake auth/DB,
not live Supabase/production/distributed atomicity. Two stale ownership assertions
were corrected after HEAD evidence, preserving the no-second-dispatch guarantee.
Wider egress static scan: eight pre-existing import findings across five sandbox
modules, reproduced from HEAD; remains OPEN, allowlist not weakened. No full-suite
PASS claimed. Full matrix and exact limits: B1_ADMISSION_COMPOSITION. Uncommitted;
candidate UNADMITTED, B1 OPEN, External Provider/Real-data Admission CLOSED.

Durable admission follow-on, 2026-09-28: read-only local tooling check found no
PostgreSQL executable; Docker CLI exists but cannot reach its local engine (named
pipe absent), with a separate config-access warning. No daemon/container was
started, no SQL applied, no credentials inspected. Actual multi-session SQL
atomicity/restart proof remains OPEN; it is not replaced by the 199 local tests.
Local Docker startup by Founder is the next prerequisite, before any proposed
isolated PostgreSQL test instance. Detailed falsification requirements recorded
in B1_ADMISSION_COMPOSITION. All admission gates and V39 remain unchanged.

2026-09-28 superseding durable admission evidence: Founder started Docker. Agent
verified it and created a dedicated PostgreSQL 16 container with network none,
no published port/host bind and tmpfs data. No credentials, cloud operations or
existing containers modified. V40 prepared and applied only to newly created
local synthetic test databases, following actual V27/V39 on a reduced base schema.
Final test_v40_postgres run: 29 PASS in 55.34s, including pre/postflight scripts,
independent processes/concurrent claims, refusal effects, late rollback and exact
Python-adapter/SQL composition. 211 targeted Python regression tests PASS with
three warnings. No full-suite PASS: earlier static egress debt remains OPEN.

Distinct durable contract rejects preparation-only authority. Policies are empty
on deployment, client DML/RPC denied, service direct DML denied. No generic
producer called/admitted; synthetic mock output is only a persistence test fixture.
Fresh client-process recovery does NOT establish PostgreSQL/container restart,
disk durability, live Supabase Auth/RLS, HTTP/browser or professional reliability.
V40 NOT deployed remotely; deployment and any later write rehearsal require
separate Founder authorization. B1 OPEN; External Provider/Real-data Admission
CLOSED. Local changes not checkpointed; nine prior exclusions preserved.
Exact guarantees, resources and proof limits: B1_DURABLE_ADMISSION_V40.md.

2026-09-28 authorized structural V40 deployed ONCE to ejixkplrgobgwqnhidwt after
all eight preflight checks passed and UI project identity was verified. Editor
SQL LF hash matched migration D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24.
Success response; three tables empty, expected role permissions, six functions,
three enabled guard triggers and 21 validated constraints observed. Twenty-one
pre-existing public table hashes plus existing function/ACL and table/RLS hashes
unchanged. Supplementary pg_proc.prosrc exact body hashes differ for all six
functions: STOP, cause UNKNOWN, no correction/retry/further remote query. No full
deployment-conformance PASS. New read-only diagnostic authorization recommended.
No business write, producer activation or gate change. Evidence and hashes in
B1_V40_DEPLOYMENT_INSPECTION.md; local docs uncommitted.

V40 read-only diagnostic under distinct Founder GO: two READ ONLY/ROLLBACK
queries of the six pg_proc definitions. All six raw server hashes match expected
LF bodies transformed to CRLF; independently all PostgreSQL CRLF-to-LF hashes and
lengths match expected source. CRLF counts 12/17/6/56/18/52 for scope/claim/close/
complete/guard/reserve; zero bare CR. No multiline string literals in these bodies,
no semantic changes found. Accessibility-rendered body text compressed spaces and
was not used as byte evidence. Signatures/returns/defaults/language/security and
search_path conform. Exact source migration hash unchanged. Representation-only
discrepancy RESOLVED, initial failed comparison preserved, no remote mutation or
reapplication. No deployed behavior test or producer/gate admission inferred.
Future versioned dual-hash verifier proposed, not implemented during diagnosis.

Subsequent Founder GO: minimal v40-definition-crlf-1 implemented as a separate
read-only SQL verifier; raw evidence retained, exact LF/CRLF body pins only,
metadata and permissions checked independently. 1 pinned-source test PASS;
36 local PostgreSQL tests PASS including seven acceptance/refusal variants.
Initial CRLF test caught Windows text-stdin translation, fixed in local harness
by byte-exact UTF-8 transport; no verifier weakening. Additional existing-V27
constraint rollback test PASS (1 selected), supporting a future remote protocol
without schema fault injection. No remote operations this slice, V39/V40 migration
unchanged. Proposed next proof: B1_V40_LIVE_REHEARSAL_PROTOCOL.md; remote policy
registration and writes NOT authorized. Generic UNADMITTED; B1 OPEN; gates CLOSED.

Subsequent Founder GO authorized conditional V40 rehearsal within 7 rows and 18
mutation-capable requests. Preparation review identified an omission before any
remote access: existing account path requires POST Auth login, but the fixed
16 RPC + policy insert/disable sequence already totals 18. Auth session effects
were not covered explicitly by the seven application-row bound or read-only
preflight. No credentials read, script executed or remote operation performed.
Stopped without silently removing a test or excluding login from the budget.
Recommended explicit amendment: 19 including one login, technical session effects
separate from unchanged seven proof rows, no refresh/re-login. Details in
B1_V40_LIVE_REHEARSAL_PROTOCOL.md. Runner/local validation not yet completed;
no live V40 admission/atomicity PASS. B1 OPEN, generic UNADMITTED, gates CLOSED.

Founder accepted exact 19-request amendment: one account-1 login plus 16 RPC
attempts and owner policy insert/disable; seven application rows unchanged.
Prepared local SQLite slot journal with transaction locking and fixed Integration
Test transport without retry/redirect/refresh/session persistence. Auth slot is
burned before POST; independent processes cannot consume it twice. Tests include
expired/foreign/ambiguous Auth and RPC responses and no secret in journal/output.
32 preparation/transport component tests PASS. Combined selected admission,
ownership and egress regression: 192 PASS / 1 FAIL; failure is the pre-existing
eight static network-import findings across five older sandbox files, not a
global egress PASS. Two newly introduced fixed-project network modules explicitly
reviewed and SHA-pinned; no blanket network exception. No V39/V40 SQL change.

scripts/inspect-v40-rehearsal-readonly.ps1 CheckOnly PASS using existing local
runtime: source/fixture pins and local Python availability verified, no key
read, login, network or remote write. Eventual command accepts service key only
in masked local entry or reuses Process value; does not open A24/JWT/V33 DPAPI.
Report contains scope UUIDs and record counts/hashes only; not an execution permit
or catalog-conformance proof. The complete live orchestrator and its whole-run
falsification are still pending; components must not be mistaken for a runnable
19-action rehearsal. No remote preflight or authenticated session attempted by
the agent during this amendment work. B1 OPEN; generic UNADMITTED; gates CLOSED.

Follow-on: Founder service-only preflight PASS verified against saved report
SHA256 35759DA949A93E0FB4DF030DBE8F9760B27C115D0EF9E2C1E833E830F6CD6F63.
Captured baseline for eleven tables and exact technical-account-1 parents;
zero Auth/effect attempts, registries empty. Agent then executed three separately
authorized READ ONLY / ROLLBACK SQL inspections via existing Integration Test UI:
six definition checks PASS; expected RLS/privileges and zero rows; 21 constraints
validated and all three expected guard triggers enabled. No technical-account
login or business/schema mutation. The earlier HTTP report remains unchanged;
its catalog/auth/rehearsal readiness flags are not retrospectively relabelled.

Before any live rehearsal, local review corrected SQL TEXT close acknowledgment
decoding (only exact CLOSED accepted) and conservative login lifetime accounting.
Four decoding tests and two real-spawn/pipe handoff-pattern tests added; latter
uses mocked GET Auth and no live session. 38 component tests PASS; combined
selected regression 198 PASS / one known global-egress failure (same eight
older findings). Full orchestration, owner-action coordination and whole-run
validation remain pending. No policy/admission/trio created; no 19-slot attempt
started; original V39/V40 unchanged; no Git operation. B1 OPEN, generic UNADMITTED,
External Provider/Real-data Admission CLOSED.

### V40 complete local orchestration release (subsequent to read-only preparation)

- Actual isolated Docker PostgreSQL full orchestration: 4 PASS / 147.34s.
  Existing backend composer/adapter, actual V27/V39/V40 SQL, independent race and
  recovery processes. Success: 19 slots including one mocked Auth, seven rows,
  final admissions REFUSED/CLOSED/COMPLETE and test policy disabled.
- Falsifications: unexpected source-swap success, lost claim acknowledgment,
  owner INSERT refusal. Fail-closed; no governed trio; partial state preserved,
  no automatic retry/cleanup. Fresh local database per test, no remote writes.
- Launcher/catalog freshness/ticket replay/component/handoff: 50 PASS / 4.53s.
- Contract/admission/definition/egress selected regression: 122 PASS / 1 known
  FAIL / 4.91s. Eight older static-egress findings remain OPEN, not waived.
- Windows wrapper CheckOnly PASS using actual installed Founder Python; no
  secret read/network/Auth. Nineteen source hashes pinned. Wrapper hash and
  exact coordination protocol recorded in B1_V40_LIVE_REHEARSAL_PROTOCOL.md.
- No live rehearsal claim: local Auth/HTTP mocked, auxiliary historical tables
  reduced. Fresh remote checks and one actual session still required. Original
  read-only preflight flags remain false. No remote effect consumed this step.
- Local changes only; no stage/commit/push, no V39/V40 migration change. B1 OPEN,
  generic producer UNADMITTED, External Provider/Real-data Admission CLOSED.

### V40 first remote attempt — refusal evidence, not completion evidence

Fresh six-definition / three-registry / 21-constraint read-only checks conform.
One owner POLICY_INSERT_ACK; journal 16 effect slots including exactly one Auth,
last POSITIVE_COMPLETE. Runtime refused without retry. Independent SQL confirmed
four control rows: policy enabled/SYNTHETIC/DENY, admissions REFUSED/CLOSED/REFUSED;
zero analyses/envelopes for all three attempt IDs and zero v2 receipts. Positive
terminal timestamp 2026-09-28T13:25:35.682675Z. No independent recovery or final
historical-hash PASS. Exact SQL exception unresolved; generic catch suppresses it.
No corrective mutation, policy disable or code patch performed after failure.
Manifest/journal/refusal preserved. Detailed policy/execution IDs and boundaries
in the V40 protocol. B1 OPEN, generic UNADMITTED, both gates CLOSED.

### V40 containment under separate Founder GO

One exact policy disable acknowledged and independently reread: enabled=false,
four evidence rows preserved, zero receipts; admissions and existing analysis /
envelope / V39 receipt aggregate hashes identical before/after. Subsequent work
strictly read-only. Deployed V27 definition and analyses CHECK read directly;
pinned adapter FINANCIAL_WORKBOOK literal fails that CHECK's allowed set. Local
fixture omits CHECK. Logs confirm completion HTTP 200 but do not expose the
handled exception. Historical first exception remains unproven; no 23514 claim
from historical logs. No corrective code, schema or rehearsal changes.
See B1_V40_REFUSAL_DIAGNOSIS.md for exact hashes, limits and minimal proposal.

### V40 local taxonomy correction and bounded database parity

Separate local-only GO: AUTRE storage metadata matches V39 composite-workbook
precedent; rich result FINANCIAL_WORKBOOK and complete envelope remain unchanged.
All 30 observed analyses columns and ten constraints represented in local fixture;
type/nullability/defaults verified. Missing checks/FKs, 32-bit file-size limit and
chat_count NOT NULL now caught before a future remote attempt.
56 actual isolated PostgreSQL tests PASS (227.93s); final 15 parity tests PASS
(17.18s; overlapping subset), 138 application tests PASS (7.66s). Egress 34 PASS
and one unchanged eight-finding scan FAIL. Invalid literal yields local 23514 /
analyses_type_document_check and V40 rollback; corrected full orchestration PASS.
Does not recover the old remote first exception. No remote access/write, no new
live credentials, no migration change, no Git staging. Original launcher remains
unusable under old pin/attempt, not silently repinned. Successor protocol proposed
with seven NEW rows / 19 effects and immutable four-row historical baseline;
implementation/readiness and distinct Founder GO still required before execution.
See B1_V40_LOCAL_STORAGE_PARITY.md. B1 OPEN; generic UNADMITTED; gates CLOSED.

### V40 successor 1 — populated-history launcher validation only

Separate local-preparation GO, no remote authorization exercised. New entry point
run_v40_successor.py and wrapper rehearse-v40-successor-1.ps1; old launcher,
attempt directory and evidence identities preserved. Original manifest/refusal/
eleven-table baseline pinned. Exact old policy disabled; full admissions anchored
to recorded PostgreSQL JSONB hash, not merely accepted as a fresh baseline.
Fresh catalog attestation and ten absent distinct IDs required before mutation.

Actual isolated PostgreSQL: three successor cases PASS (392.09s), full new main
including independent worker recovery and second-invocation refusal PASS (323.40s),
final overlapping anchor test PASS (25.39s). Seven NEW rows / four old rows intact;
nineteen effects / one MOCK Auth; new policy disabled; no old identity reused.
Storage parity 15 PASS (14.84s), existing immutability/expiry guards 3 PASS (15.55s),
application and launcher guards 167 PASS (7.84s). Egress 34 PASS / unchanged one
global FAIL with eight older findings. Windows wrapper default local check PASS
without secrets or network. No cloud call or real Auth; V39/V40 hashes unchanged.

Local readiness only; distinct remote GO and fresh catalog/history preflight still
required. No generic admission or B1 closure; gates remain CLOSED. No Git index,
commit or push; local/uncommitted evidence. Full protocol and wrapper SHA-256 in
docs/Project_Control/INSIGHT_SHAPER_B1_V40_SUCCESSOR_PROTOCOL.md.

### V40 successor pre-Auth ordering — correction after static stop

The conditional remote GO required all prospective identity absence checks before
Auth; static inspection showed the prior launcher checked only before business
writes. It was stopped without launch, Auth or remote requests. That local PASS
was not broadened to satisfy the stricter ordering.

The subsequent local-only GO is implemented by frozen IdentityPlan and a trusted
constructor-only IdentityConsumption. Existing composer still authenticates and
resolves ownership; allocation itself is not authority. Ten exact prechecked IDs
are committed before Auth and checked again against composition before policy
creation, then against the persisted bindings via existing result verification.

177 application/guard tests PASS (8.71s). Three actual local PostgreSQL main-entry
tests PASS (532.30s): full 19-effect/seven-row positive with exact prechecked =
composed = persisted IDs, collision refusal with zero Auth/effects, and forced
post-Auth substitution refusal with only one mock Auth and no new durable row.
Prior four-row history preserved; positive retains race, atomicity/rollback,
anti-replay, independent recovery and final new-policy disable. Windows wrapper
default integrity/syntax PASS. Egress 34 PASS / one unchanged global FAIL.
No remote reads, Auth or writes; real successor directory absent; V39/V40 and
original failure artifacts unchanged. Literal protocol locally validated, next
remote GO/fresh checks required. B1 OPEN; generic UNADMITTED; gates CLOSED.
Local/uncommitted evidence only. Current wrapper hash in successor protocol.

### V40 successor 1 — live bounded PASS, 2026-09-28

The subsequent distinct remote GO was exercised once. Fresh READ ONLY controls
confirmed six V40 functions (raw plus versioned CRLF-to-LF hashes), actual table
protections and relevant storage parity, exact old four-row snapshot and its
historical PostgreSQL anchor. Ten identities were checked absent at zero Auth/
effects, then reused exactly by authenticated composition and durable results.

Observed BOUNDED_V40_SUCCESSOR_PASS at 17:34 UTC: nineteen effect attempts,
one Auth, seven new rows; REFUSED / CLOSED / COMPLETE. Real independent worker
race had one winner; late failure rolled back the result trio; replay refused;
new-process recovery succeeded after workers exited. New policy disabled once;
old policy remains disabled; all four historical rows unchanged. Separate final
READ ONLY SQL at 17:35:26Z corroborates exact bindings, both disabled policies,
zero partial negative-case result rows and unchanged historical analyses,
envelope and V39 hashes. Journal independently read in mode=ro: closed=1 and
nineteen unique slots. No retry, cleanup, schema mutation, provider or real data.

New positive analysis: 162a5aa6-8ff1-4031-b726-b866006f0939. Detailed identities,
artifact hashes, Auth effects, receipt limits and source of every claim are in
docs/Project_Control/INSIGHT_SHAPER_B1_V40_SUCCESSOR_LIVE_EVIDENCE.md.
Original failed proof is not requalified. Generic remains UNADMITTED; B1 OPEN;
global egress scan debt OPEN; both admission gates CLOSED. No HTTP/browser v2,
database restart, global isolation, professional or production proof inferred.
No Git index/commit/push: documentation and implementation still local/uncommitted.

### B1 version-aware owned V39/V40 reread and terminal provenance — local PASS

Under Sol medium and DEC-033, the owned-output path now discovers V39 and V40
receipts only after analysis/company/entity ownership is established. V39 keeps
its existing strict receipt validation. V40 additionally binds the exact COMPLETE
admission, receipt, policy, actor/company/entity/engagement, analysis, source,
input, producer/task versions, contract, composition and immutable envelope.
The receipt-bound engagement is used directly; no current/default engagement is
substituted. A disabled V40 policy remains historical evidence only and grants no
new execution authority.

The server emits a common terminal projection with an explicit V39 or V40
version. The UI and XLSX/PDF/PPTX renderers consume that server-owned projection;
V40 is labeled local synthetic / EGRESS DENY / generic producer UNADMITTED, never
as V39 mock or as admitted generic execution. Legacy absence remains UNATTESTED.

Falsifications cover dual versions, unknown receipt version, foreign/substituted
scope, missing admission/policy, contract/source/input/candidate/envelope changes,
non-COMPLETE state, registry outage and multi-engagement substitution. Every
present-but-invalid receipt refuses `UNAVAILABLE`; it never falls back to legacy
or V39. Own V39 and V40 reads and all three exports preserve exact hashes and do
not mutate repository state. Local validation: 127 backend PASS, 37 PostgreSQL
tests skipped without their isolated database; 19 frontend PASS; TypeScript and
Python syntax checks PASS. The earlier pnpm dependency relocation was reverted
inside ignored node_modules before Jest; no tracked dependency or lockfile change.

No remote read/write, Auth, producer invocation, provider call or real data.
This is LOCAL_TESTED only: V40 live GET/browser/export and the actual generic
producer connection remain unproved. B1 OPEN; generic producer UNADMITTED;
global egress debt OPEN; External Provider and Real-data Admission CLOSED.

### B1 backend-owned producer adapter — local bounded PASS

Under Sol medium, the existing V40 claim/completion services and governed V1
financial-analysis models were composed without adding an authority primitive.
The backend-selected adapter verifies producer/version, task/version and exact
admission-contract digest before claim. Its callable input contains only the
bounded task, correlation nonce and immutable governed source facts. Tests assert
that actor, company, entity, engagement, analysis and execution identifiers are
absent from the serialized producer view.

After one invocation, Pepperyn JSON-isolates the returned object, applies the
closed `GovernedFinancialAnalysis` schema, nonce/source/fact-lineage checks, and
constructs the envelope itself. Only the pre-existing `DurableProducerAdmission`
can perform completion. Falsifications prove no invocation on profile/contract
mismatch, no invocation on claimed-input substitution, no completion on injected
scope, changed nonce/source/fact, malformed output or producer exception, one
sanitized refusal and no retry. The completion candidate/envelope digest and V40
bindings are backend-constructed. A socket denial probe observed zero product
network attempts.

Consolidated local selection: 185 PASS in 9.45s. Thirty-seven PostgreSQL cases
were skipped because no isolated PostgreSQL runtime was supplied to this run;
their status is explicitly NOT EXECUTED. No remote Auth/read/write, policy,
admission, producer registration, provider call or real data. V39 regressions and
version-aware V40 output tests remain PASS. This establishes local composition
only: real generic producer UNADMITTED, B1 OPEN, global egress debt OPEN and both
admission gates CLOSED.

### Genuine generic-producer candidate local proof — PPR-064

Sol medium fixed the candidate profile to OpenAI Responses `gpt-5` for the one
governed financial-analysis task, while leaving its state UNADMITTED and egress
CLOSED. A claimed-input request builder preserves the backend nonce and exposes
only governed source facts plus static task/schema material. The only transport
is an injected single-use local callable. The strict existing response validator
and PPR-063 adapter retain quarantine and backend-only completion authority.

The future `governed-generic-producer-receipt-3` contract is defined separately;
it cannot be minted by this slice. V40 SQL remains unchanged and its local test
receipt remains LOCAL_SYNTHETIC_ONLY / egress DENY / generic unadmitted. Actual
local PostgreSQL proves exact prechecked/composed/persisted identities, atomic
completion and no V39 fallback for the candidate mechanics.

Evidence: 52 focused PASS; 235 related non-PG PASS; 38 PostgreSQL PASS in the
isolated container, including every one of the 37 previously NOT EXECUTED tests.
Targeted new-module scan: zero egress findings. Repository-wide egress scan:
unchanged FAIL with eight pre-existing findings; four adjacent controls PASS.
No remote access, provider call, real data or gate change. Full record:
docs/Project_Control/INSIGHT_SHAPER_B1_GENERIC_PRODUCER_CANDIDATE_LOCAL_PROOF.md.

### PPR-065 — durable receipt future-proofing, local only

Founder DEC-034 requires the receipt to retain one indivisible binding for the
exact fact schema, positive projection policy, task and output contract. Local
code and the V41 migration candidate enforce canonical binding text/JSON/digest,
the same admission-contract identity throughout reserve/claim/complete, strict
supported-version reread and no `latest` fallback.

Evidence: 15 V41 PostgreSQL PASS; 68 targeted V40/V41 PostgreSQL PASS; 134 related
application PASS. Four-version substitutions, valid-looking recombination,
unknown version, post-precheck mutation, persisted mismatch, concurrency, replay
and partial completion were falsified. V39/V40 remain unchanged. Global egress:
34 PASS / one unchanged repository-wide FAIL with eight prior findings.

This is LOCAL PASS only. V41 has not been applied remotely and no policy or
producer has been admitted. Runtime reread/UI/exports and live execution remain
OPEN. B1 OPEN; generic producer UNADMITTED; External Provider and Real-data
Admission CLOSED. Evidence document:
docs/Project_Control/INSIGHT_SHAPER_B1_DURABLE_RECEIPT_FUTURE_PROOFING_LOCAL_PROOF.md.

### PPR-066 — V41 empty structural deployment, live bounded PASS

V41 was applied exactly once to Pepperyn Integration Test after fresh preflight
and historical baseline PASS. Structural postflight confirms three empty
RLS-enabled registries, one immutable guard trigger per table, no direct client
read, service-role SELECT only, and service-only execution functions.

The initial definition check returned `REFUSED` and remains preserved evidence.
All normalized hashes already matched; diagnosis proved its CRLF columns had
mistakenly duplicated LF hashes. The five observed raw hashes exactly equal the
independently recomputed CRLF bodies. Only the read-only verifier expectations
were corrected. Three static controls and four isolated PostgreSQL cases PASS:
LF and CRLF accept; semantic and whitespace mutations refuse. The corrected live
check reports `V41_DEFINITION_CONFORMANCE_PASS` for all five functions.

Pre/post row counts and hashes for analyses, V39 envelopes/receipts and V40
policies/admissions/receipts are identical; the relevant 59-item catalog hash is
also identical. Final V41 counts are 0/0/0. No policy, admission, analysis,
receipt, producer call, provider use or real data occurred.

This is structural deployment evidence only. B1 remains OPEN, genuine producer
UNADMITTED, global egress OPEN/FAIL, External Provider CLOSED and Real-data
Admission CLOSED. Full record:
docs/Project_Control/INSIGHT_SHAPER_B1_V41_STRUCTURAL_DEPLOYMENT_EVIDENCE.md.

### PPR-067 - post-V41 validation hardening, bounded LOCAL PASS

Founder authorized local reproduction/correction only. The actual network-none
PostgreSQL fixture reproduces policy/scope recombination, missing/null/numeric
receipt digests and request-digest substitution. The original V41 migration is
unchanged; prepared_v41_validation_hardening.sql is a separate undeployed
transactional correction of two function bodies with original-body hash guards.
Authority, signatures, owners, ACLs and other functions remain unchanged.

Final complete campaign: 168 PostgreSQL PASS (84 before / 84 after); 111 related
application PASS; 26 V39 regression PASS. No skip or unexecuted PostgreSQL case
in this protocol. Before-phase acceptances record defects, not valid admissions.
Refusals assert no result trio; storage/receipt tests also snapshot other public
test tables. Late envelope insertion failure rolls back the inserted analysis.
Concurrency, replay, expiry, independent reread and disabled policy are covered.
Initial generated-SQL syntax failure and subsequent catalog parser-offset
comparison failure are retained and explained, not requalified as successful runs.

The local campaign itself used no remote operation or product-provider invocation
and created no generic producer admission. The hardening was subsequently applied
once under a separate Founder GO to Pepperyn Integration Test. Fresh preflight,
exact guarded application and independent postflight PASS; all three V41
registries remain empty, zero policies exist, and the exact historical baseline
before/after is identical. Global egress is not requalified by this deployment.
B1 OPEN; both gates CLOSED. Full local scope and live structural evidence:
docs/Project_Control/INSIGHT_SHAPER_B1_POST_V41_VALIDATION_LOCAL_PROOF.md.
docs/Project_Control/INSIGHT_SHAPER_B1_PPR067_STRUCTURAL_DEPLOYMENT_EVIDENCE.md.

### PPR-068 — post-review local B1 chain and egress confinement

Under the consolidated Astra decision and Sol-medium routing, the three local
tranches reached bounded PASS without remote access. Exact frozen request,
single-use V41 reserve/claim/complete, backend-only result construction,
persisted-row reread and common UI/XLSX/PDF/PPTX provenance are locally composed.
Injected evidence remains non-attested. The actual OpenAI producer is neither
invoked nor admitted.

PostgreSQL: 187 PASS, zero skipped/not executed. The intermediate 69 hardened
failures are retained: their cause was a Python-versus-PostgreSQL `jsonb` policy
digest fixture. PostgreSQL now creates the policy digest used by the receipt;
the complete rerun passed. Application selections: 223 PASS and a final 58 PASS.
Frontend: 7 PASS and TypeScript PASS.

The historical eight-findings/five-files global egress debt was closed by
confinement, not a blanket whitelist. Those callers now use a content-pinned
fixed Integration Test/loopback capability inaccessible from product services.
Global egress suite: 36 PASS; adjacent bounded network regressions: 61 PASS plus
seven subtests. No network or credential was used in these tests.

PPR-067 is now structurally deployed with empty registries and unchanged history;
this does not execute or admit the locally composed chain. The PPR-068 local proof
is checkpointed. B1 stays OPEN, Generic Producer UNADMITTED, External Provider
CLOSED and Real-data Admission CLOSED. A bounded synthetic/injected V41 durable
rehearsal requires a distinct Founder GO.

### PPR-069 — DEC-035 bounded-policy contract and rehearsal readiness

After Astra resolved the admission-semantics ambiguity, Sol implemented only the
local guard needed before rehearsal. The immutable PPR-065 profile and digest
remain byte-for-byte unchanged. New policy validation binds DEC-035 and the exact
synthetic scope while requiring local injection, false provider attestation,
closed egress, closed real-data admission and `UNADMITTED` global producer state.

Adversarial tests refuse missing/unknown decision, global-admission claim,
profile-state mutation, scope substitution, external transport, false attestation,
egress widening and disabled policy before reserve. Independent persisted-row
reread retains proof after disablement and projects the non-global status through
UI and XLSX/PDF/PPTX. Results: backend 90 PASS; frontend 7 PASS; TypeScript PASS;
isolated PostgreSQL 187 PASS and zero NOT EXECUTED. The container was local,
networkless, unbound and stopped after validation. No remote operation, Auth,
policy, admission, provider or real data was used.

The exact proposed live protocol is
`docs/Project_Control/INSIGHT_SHAPER_B1_V41_INJECTED_DURABLE_REHEARSAL_PROTOCOL.md`.
It remains NOT EXECUTED and requires a distinct Founder GO.
