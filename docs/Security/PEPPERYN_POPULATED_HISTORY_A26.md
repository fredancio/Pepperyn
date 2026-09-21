# A26 - Populated history isolation preparation

Classification: V1 FIX / BLOCKER. Base: 3a80529b513ce255d36ae57ab0c52d575ff50f80.
Status: FOUNDER_LIVE_BOUNDED_POPULATED_HISTORY_PASS / NOT_CHECKPOINTED.

## State reconciliation before new development

Working within bounded evidence: synthetic governed chain, persisted source
contradictions, portfolio and temporal outputs; deployed V36 privileges; two-user
A24 reads and A25 empty-own/foreign-refused history. A25 durability is Founder
confirmed at the base above; local HEAD matches. next-env.d.ts stays excluded.

Partial, not global guarantees: financial reliability, multi-client temporal
continuity, provider privacy chain and two-user isolation. Missing isolation
evidence includes populated histories, writes and actual analysis/export outputs.
Professional Financial Reliability and production/admission gates remain open;
FR-EXPECTED-2 must not be replaced with scenario-specific answers. No new failure
of the corrected history route is established. Existing dependencies are retained.

Critical path for this work: exact technical ownership/engagement and existing
record inspection -> bounded synthetic fixture preparation -> populated positive
reads and foreign refusal -> write and analysis/export adversarial evidence.
This is an evidence dependency order, not a declaration that later stages pass.
The V1 routes still require the single designated company; do not weaken that
gate to accommodate test accounts or count gate-only refusals as isolation proof.
Production access/infrastructure, provider account evidence and independent
professional evaluation remain separate blockers. Self-Selling and speculative
architecture improvements remain deferred. No new infrastructure introduced.

## Smallest next executable task

Read-only preflight of the existing two A24 accounts before designing persistent
fixtures. No fake completed financial rows or source-to-canonical promotion is
introduced. No seed command exists in this slice. Any later fixture operation
must explicitly preserve synthetic provenance and avoid duplicates/overwrites.

`backend/sandbox/inspect_populated_history_scope.py` authenticates existing accounts,
verifies their exact own profile, company owner and synthetic company/client names,
requires one bound engagement each and distinct scopes, and reads only bounded
history/envelope metadata filtered by those verified companies. Existing records
are reported as present, never overwritten/deleted or automatically recreated.
Output omits IDs, financial contents, tokens and credentials. Authentication creates
sessions; business access is SELECT-only; no RPC or provider call.

Founder Windows wrapper: `scripts/inspect-integration-history-a26.ps1`. Reuses
existing DPAPI account bundle with unchanged-file check. Requires existing anon
and service keys through process reuse or masked input; no secret regeneration,
persisting new secrets or modification of V33/JWT. No backend restart necessary.

## Validation and limits

Four unittest methods / ten scenarios PASS: correct empty inspection, existing
records preserved, seven malformed/foreign/outage falsifications and wrong project
refused. Test doubles have no write methods. PowerShell CheckOnly PASS, no secret
restoration/network. This is NOT a live preflight or populated-history proof.
Expected live status A26_SCOPES_INSPECTED; all isolation and production proof flags
remain false. A nonempty scope requires inspection of existing state before any
fixture creation; it is not a reason to purge or retry automatically.

## Founder live preflight result

Founder reports one execution: A26_SCOPES_INSPECTED. Each technical account has
analysis_count_bounded=0 and envelope_count_bounded=0; both_scopes_empty=true.
Existing DPAPI unchanged. business_write_performed=false. Populated-history,
write, analysis/export, global isolation and production proof flags all false.
This establishes the inspected empty prerequisite only, not populated isolation.
Evidence is Founder-reported output, not an agent-captured database trace.

## Proposed controlled write boundary - not executed or yet authorized

Minimum fixture population: one genuine registered synthetic mock analysis and
its governed envelope per existing A24 technical account (two analyses and two
envelopes total), through the existing V27 persistence transaction. Reuse only
pepperyn_v1_heterogeneous_english.xlsx and its existing deterministic local mock;
do not fabricate completed placeholder financial reports. Local fixture execution
was checked successfully with DETERMINISTIC_MOCK_NO_NETWORK and no DB writes.

Implementation must reauthenticate and revalidate both exact technical ownership
chains, engagement bindings and empty state immediately before the first write.
Use fixed scope-bound fixture IDs; reject any existing or conflicting fixture
instead of overwriting/upserting. Validate both payloads before either write.
Each analysis/envelope pair is atomic under V27; the two pairs are NOT a single
transaction. On timeout or partial failure, stop with safe acknowledged-write
counts; inspect persisted state before any retry. Never automatically purge or
retry. Persisted identity is used to distinguish the two histories, not invented
financial differences between fixtures.

This is explicit Integration Test fixture administration, not permission to open
the single-designated-company UI gate. No gate, user, company, engagement, JWT,
DPAPI, invitation, decision, intention, follow-up, execution, impact or learning
change. No provider transport and no real financial data. Existing pilot analyses
are out of scope. The seed does not itself prove write isolation or analysis/export
access. Subsequent positive/negative history reads must use the actual two users'
sessions, never the service key as a substitute for user authorization.

Founder GO authorizes the two pairs above. Seed implementation is prepared,
locally tested and not live executed. No new Git intervention requested.
External Provider and Real-data Admission CLOSED; Self-Selling DEFERRED.

## Authorized seed preparation

`backend/sandbox/seed_isolation_history.py` and the protected wrapper
`scripts/seed-integration-history-a26.ps1` reauthenticate/inspect both scopes,
prepare both actual registered mock payloads, then repeat both scope/empty checks
before writes. Deterministic scope-bound UUIDs and V27 insert-only primary keys
prevent duplicate fixture IDs. No retry/upsert/delete. Each pair is reread through
the integrity-verifying envelope loader plus exact analysis metadata/JSON checks.
Two-pair atomicity is NOT claimed; concurrent unrelated writes are not excluded
transactionally by preflight. Keep these dedicated technical scopes quiescent.

Success: A26_SYNTHETIC_PAIRS_SEEDED with two acknowledged and verified pairs; all
isolation/production proof flags stay false. Failure: sanitized stage and counters,
remote_partial_write_possible and automatic_retry_permitted=false. Never infer
rollback from client timeout. Founder-local DPAPI/key access needed; agent has not
executed any remote seed.

Validation: four seed unittest methods cover real local registered mock preparation
with doubled DB writes, success, fixed IDs, unauthorized/existing/changed-scope
refusal, first/second write timeout and envelope/row read failure. Four preflight
methods also PASS. PowerShell seed CheckOnly PASS without secrets/network/writes.
Temporary XLSX file-handle ResourceWarnings occurred during repeated local fixture
tests; tests passed, comprehensive resource QA not claimed. No backend/UI gate
changed. Populated two-user history proof remains pending after seed.

## Founder seed result and populated read preparation - 2026-09-21

Founder reports one seed execution: A26_SYNTHETIC_PAIRS_SEEDED, two acknowledged
and two verified pairs, business_write_performed=true, DPAPI unchanged. All
isolation/production flags false. This supersedes pending live seed only, not any
read/write isolation gate. Do not rerun the seed or the empty-history A25 probe.

New dedicated `verify_populated_history.py` and `verify-populated-history-a26.ps1`
use existing password sessions with anon key only, no service-role reads. They
resolve exact own profile/company/entity/engagement and recompute the scope-bound
seed IDs. For both users require exactly the own analysis with expected filename,
type, entity and public schema through entity-filtered, tenant-wide and forged
company-query reads; all four responses must agree. Foreign entity requests must
return the expected 404; anonymous history must return 401. No new application
write, no row content/token output, no provider; logins create Auth sessions.

Result may be BOUNDED_POPULATED_HISTORY_ISOLATION_PASS only after every check,
with proof_scope=A26_TWO_SEEDED_ANALYSES_HISTORY_GET_ONLY. This says nothing about
analysis detail/export access, writes, global isolation, browser or production.
Errors, empty responses, extra rows/fields or unrelated refusals fail closed.
An unavailable direct authenticated engagement read is a blocker, not a reason
to substitute service authority or widen privileges.

Local verification: actual verifier with synthetic Auth/HTTP doubles, positive
scenario plus ten falsifications; preflight regression also passes. PowerShell
CheckOnly passes without credentials or transport. Live verification still
requires Founder-local DPAPI access; no backend restart or seed repetition needed.

## Live populated-read refusal - 2026-09-21

Founder ran once: USER_1_ENGAGEMENT refusal, no business write or retry. No
populated-history PASS. Repository diagnosis: V19 explicitly describes engagements
as backend/service-key data with no direct client consumer/policy contract. The
verifier incorrectly assumed direct authenticated visibility. Its generic stage
does not establish whether live response was permission denied, RLS-empty, malformed
or transport failure. Prior seed service-key verification supports binding only
at seed time, not current state or user visibility. V36 did not grant this access.

No permission/schema/seed change is justified from that stage alone. Prepared
read-only differential diagnostic `diagnose_history_engagement.py` and wrapper:
revalidate exact technical scopes, classify direct user REST status without raw
error bodies, and separately check existing deterministic seed analysis/envelope
binding via service reads. Privileged diagnostic reads are explicitly NOT user
isolation proof. No insert/update/delete/RPC, no new fixture, no regeneration.
Three local methods / six diagnostic cases PASS; live diagnosis pending protected
credentials. Do not rerun the seed or weaken V36 to accommodate this test defect.

## Diagnosed verifier defect and V19-aligned correction - 2026-09-21

Founder diagnostic ran once: both direct user engagement reads return HTTP 200
with EMPTY_UNDER_USER_SESSION; both persisted_seed_binding_verified=true. No
business write, DPAPI unchanged, all proof flags false. This supports correct
existing pairs and an invalid verifier access assumption, not a bad seed binding.
It does not by itself identify the exact deployed RLS policy responsible for empty
visibility, or prove that this table's wider policy configuration is correct.

Correction is confined to the test harness. Following V19, a separate service
client retrieves only id/entity_id engagement reference metadata for the exact
entity whose user ownership has already been verified. The deterministic expected
fixture ID is derived from this reference; all history GETs still use only the
individual user token (or no token for the negative anonymous case). The service
client never reads history for this proof and its reference read is not evidence
of user authorization. No product route, V36 grant, RLS policy, seed or binding is
changed. Earlier anon-only/no-service-key verifier wording is superseded here.

Updated tests explicitly disallow user engagement reads, restrict the service
client to engagements, and assert only the two user Bearer tokens reach history
transport. Positive case and ten falsifications PASS; PowerShell CheckOnly PASS.
Expected output retains BOUNDED_POPULATED_HISTORY_ISOLATION_PASS with explicit
engagement_reference_authority=SERVICE_READ_ONLY and
history_probe_authority=USER_SESSIONS_ONLY. Live corrected run remains pending;
no populated-history PASS claimed yet. Wrapper reuses/prompts masked anon/service
keys and preserves DPAPI, JWT and V33. No backend restart or seed repeat required.

## Bounded live closeout - 2026-09-21

Founder ran the corrected verifier once: BOUNDED_POPULATED_HISTORY_ISOLATION_PASS,
populated_history_isolation_proven=true, engagement_reference_authority=SERVICE_READ_ONLY,
history_probe_authority=USER_SESSIONS_ONLY. DPAPI unchanged; no business writes.
This is Founder-reported live proof for the two seeded histories and exact GET
probes, not an independently captured full trace. Write, analysis/export, global
isolation and production flags remain false. No pairs were changed or reseeded.

A26 functional bounded scope is closed. Durability checkpoint warranted before
expanding to mutations: seeded live fixtures and their verification/recovery tools
must be recoverable. Next risk selected from repository: legacy
`POST /api/decision-feedback` and `DecisionMemoryService.upsert_feedback` pass a
caller report ID toward service-authority persistence. Investigate ownership and
governed-path bypass before attempting adversarial writes. No live exploit or
write-isolation conclusion inferred from code inspection. Do not mutate A26 pairs.
