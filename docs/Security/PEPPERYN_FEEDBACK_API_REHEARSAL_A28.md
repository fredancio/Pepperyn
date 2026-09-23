# A28 — legacy feedback API isolation rehearsal plan

Status: PREPARED / LIVE_NOT_EXECUTED. FIX-BLOCKER. 2026-09-21.

## Why a separate positive fixture is necessary

A26 has two governed analysis/envelope pairs. A27 intentionally rejects all
governed reports at the legacy decision-feedback endpoint, including owned ones.
Do not remove envelopes, relabel those reports or weaken this guard to obtain a
positive response. Their correct owned result is 409, their foreign result 404.

A positive legacy write requires a separate non-governed synthetic legacy report
with a persisted recommendation. No suitable existing legacy fixture has yet been
established in these technical scopes. Inspection must precede insertion, and any
unexpected state must stop the rehearsal rather than overwrite it.

## Requested bounded remote preparation

After explicit Founder authorization, at most two new analyses-table fixtures:
one per existing A24 technical company/entity, stable scope-bound IDs, unmistakable
synthetic A28 marker, no financial claims, one persisted synthetic recommendation,
no governed envelope. These are test fixtures, not application-generated analyses
or financial reliability evidence. Preserve both A26 pairs and existing business
records. No account creation, permission change, reset, deletion or upsert seed.
Preflight must verify exact identities/owners/entities and existing fixture absence.
Partial seed failure stops with acknowledged-count evidence, never an automatic retry.

## API sequence and authority

Require reloaded corrected backend before any negative POST: an old service could
accept a foreign reference. Fixed Integration Test URL and loopback backend only;
External AI closed, no provider keys/use, no real data. Reuse protected A24 credentials.
All tested POSTs use actual user sessions; service authority is limited to fixture
preparation and independent before/after state verification, never the API probe.

1. Snapshot both A26 analysis/envelope pairs, each new fixture and feedback state,
   relevant patterns and arcs, and establish exact persisted recommendation IDs.
2. For each user, attempt the other user's report/recommendation: require 404 and
   unchanged state. Anonymous request requires 401 and unchanged state.
3. Reject forged recommendation ID/text/source on owned legacy fixture (409).
   Reject owned A26 governed report (409), foreign A26 report (404), unchanged state.
4. One legitimate `unsure` feedback per new fixture: require 200, correct persisted
   company/report/recommendation/status, and arc_created false. Caller-supplied
   company cannot override identity-derived ownership.
5. Repeat foreign-scope attempt after positive rows exist: require 404 and byte-
   equivalent existing feedback. Independently reread both scopes and A26 pairs.

Success route calls compute_user_patterns, which may upsert one user_patterns row
per technical company. This is an explicit permitted side effect to be measured,
not silently described as feedback-only. No planned/done status, confirmed decision,
execution, learning or new DecisionArc. If patterns are unavailable, disclose that
separately; do not infer successful persistence from best-effort HTTP success.

## Proof boundary and current result

Only the actual endpoint/status/scope combinations tested may become LIVE_PASS.
Global write isolation, all decisions routes, analysis/export isolation, production
and professional financial reliability remain OPEN. A27 direct-table denial PASS
does not substitute for this API proof. Positive fixtures change the technical
history cardinality: do not rerun A26's exact-one-history verifier unchanged or
rewrite its historical evidence as though its snapshot were still current.

Local HTTP two-identity matrix implemented using synthetic authentication/DB doubles:
foreign 404 without upsert, own 200 with identity-derived company despite forged
company field, anonymous 401, no arc on unsure. This is not real-session proof.
No A28 remote seed or API POST performed. Founder authorization for the two added
fixtures and bounded feedback/pattern writes is the next prerequisite; protected
execution and backend reload will then be arranged without requesting technical choices.

External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## Authorized preparation and current blocker

Founder GO received for exactly two separate synthetic legacy fixtures, one unsure
feedback per fixture and associated user_patterns recomputation, plus denied cross-
user attempts. This supersedes pending authorization above. It does not authorize
A26 changes, arcs, permission weakening, cleanup/deletion or automatic retries.

`backend/sandbox/rehearse_feedback_api.py` now implements this bounded sequence.
It first verifies development health and the loaded legacy route authority marker
in OpenAPI, then repeats V37 direct-denial checks through real user sessions.
Scopes are resolved through the established A26 inspection and independently
authenticated sessions. Initial state must contain exactly one A26 pair per scope,
with no feedback/pattern/arc rows. Unexpected or previously seeded state refuses.
Service-only preparation inserts two stable-ID marked fixtures without upsert.
Every negative API probe compares both scopes with the complete preceding state;
positive feedback verifies exact persisted fields and one pattern row with no
execution rate. All A26 rows/envelopes and arcs are compared unchanged. Fifteen
negative API requests are counted separately from two authorized API requests.

The OpenAPI marker is a loaded-route version check, not cryptographic attestation
or independent security proof. The runtime marker was checked read-only on
2026-09-21: backend reachable, A28GuardLoaded=false. No A28 remote write or API
POST has been issued. Restart of the existing Integration Test backend is required
before running the protected rehearsal. Agent process has no Supabase credentials;
existing protected credentials must be supplied locally, never in chat.

Local harness invokes the actual FastAPI route/service with synthetic auth/DB
doubles. Five tests cover the full positive/15-negative flow, old-backend refusal
before seed, partial-seed stop/no retry, unexpected feedback refusal before seed,
and foreign HTTP200 refusal. These are local tests only. No live API PASS.

## Backend reload verified / protected execution ready

Following Founder restart, agent read-only OpenAPI check confirms
A28GuardLoaded=true. Previous loaded-revision blocker is resolved. Agent process
has neither Supabase anon nor service key; no attempt to extract backend secrets.
`scripts/rehearse-feedback-api-a28.ps1` prepared and CheckOnly PASS (no secret
read/network/write). It verifies runner SHA-256, checks the loaded backend again,
restores the existing A24 DPAPI bundle, prompts locally/masked for missing keys,
sets the exact approved A28 authorization, and gates the output on two fixture
inserts, two unsure writes, two pattern rows and fifteen adversarial refusals.
False global/write/output/production flags and unchanged A26 evidence are mandatory.
On failure only safe stage/counters are shown; no automatic rerun or cleanup.
Actual A28 run remains NOT_EXECUTED. Founder protected-local execution is necessary.

## Refusal diagnosed against deployed state — 2026-09-22

Founder ran once: BASELINE_NO_A28_OR_FEEDBACK; all seed/positive/negative counters
zero. This supersedes NOT_EXECUTED, not a successful rehearsal. No automatic retry.
Agent browser diagnostic initially unavailable due to usage approval failure;
resumed after Founder continuation, using read-only SQL transactions only.

Query `31ffa199-1a78-46c1-8381-3e4482bbf785` in visibly identified Integration Test:
analyses/envelopes/feedback/arcs exist; public.user_patterns DOES NOT EXIST.
Query `74c78c52-d612-4216-b1a5-610e5d4d6b96`: each exact A24 technical account has
one analysis marked A26, one envelope, zero A28-marked analyses, zero feedback and
zero arcs. No content rewrite or cleanup performed. Counts confirm no A28 seed;
they are not a new byte-for-byte A26 integrity proof.

Cause: snapshot reads all five tables before baseline assertions; reading absent
user_patterns necessarily fails. Generic stage concealed this dependency error.
The table is defined in historical V7 and used by existing compute_user_patterns;
it is derived state, not canonical financial facts or measured learning. No
existing patterns can be cleaned because the table itself is absent. Whether/how
V7 was historically deployed is UNKNOWN; do not infer it was wholly unapplied.

Runner now reports exact SNAPSHOT_USER_n_TABLE for a failed read; missing patterns
test proves no seed occurs. No missing-table-as-empty fallback, relaxed assertion
or altered product semantics. Wrapper integrity hash updated; old command must not
be reused. V38 prepared NOT_APPLIED: restore V7 column contract and timestamp trigger
on user_patterns only; empty table, backend SELECT/INSERT/UPDATE only, RLS/no client
policy, reject pre-existing table, transaction with effective privilege checks.
No V7 wholesale rerun, no V37 or A26 change. Founder GO V38 required before repair.
After approved deployment: read-only schema/privilege/zero-row postflight, then a
new hash-verified A28 command. 58 local tests PASS; CheckOnly PASS. No live A28 PASS.

## V38 deployed and inspected — 2026-09-22

Founder explicitly authorized only the prepared V38 scope. Executed once in the
visibly identified Pepperyn Integration Test project (ejixkplrgobgwqnhidwt), query
`bdbcea94-dcb7-4833-b7d6-a3e2201b94a8`: Success. No rows returned.
This supersedes the NOT_APPLIED state above. No business DML, A26 alteration,
V37 alteration, A28 cleanup or reseed was performed.

Read-only postflight `065e3faa-f170-492b-952e-846ccb01b82f` confirms:
user_patterns row_count=0; RLS=true; policy_count=0; timestamp trigger enabled
and bound to update_updated_at(); company_id primary key and companies foreign
key present. Effective anon/authenticated table and column privileges all false.
service_role SELECT/INSERT/UPDATE true, DELETE/TRUNCATE/REFERENCES/TRIGGER false.
Existing V37 client table write privileges remain absent. Postflight transaction
ended with ROLLBACK. These are deployed schema/privilege observations, not an
adversarial API isolation PASS or a new byte-for-byte A26 comparison.

A28 has not been rerun. Its previously authorized bounded rehearsal may now be
attempted once with the updated integrity-checked wrapper; all baseline and
cross-scope guards remain mandatory. API/write/global/production proof remains
OPEN. External Provider and Real-data Admission remain CLOSED.

## Anonymous probe refusal after seed — 2026-09-22

Founder execution stopped at ANONYMOUS_DENIAL: seed attempts/acknowledgements 2/2,
authorized POST attempts/acknowledgements 0/0, negative POST attempts 1.
Read-only Integration query 1f9d8dab-ba59-4d55-a942-97cca1b79865 confirms for each
exact technical owner: one A26-marked analysis, one A28-marked analysis, one
envelope, zero feedback, zero patterns, zero arcs. No remote mutation or retry.
Counts are not a fresh byte-for-byte fixture integrity proof.

Verifier defect reproduced locally: anonymous request used headers={} while
serializing JSON. urllib supplies application/x-www-form-urlencoded for that
body; FastAPI rejects it with 422 at body validation before route authentication.
The expected 401 applies to a correctly declared JSON request. TestClient(json=)
had hidden this wire-format discrepancy. Corrected only the anonymous probe's
Content-Type; authorization remains absent and expected denial remains exactly
401. Eight local harness tests PASS, including old-transport 422 before auth,
corrected-transport 401, no simulated business changes, and explicit JSON header.
No application authorization, V37 or V38 change.

Historical HTTP status/body is UNKNOWN: original runner discarded the response
body and did not retain the status in its refusal output. Reproduced 422 is not
a recovered live log. Founder backend log line is required to establish that
specific historical status without issuing another POST. No live A28/API PASS.

DO NOT rerun the seed script: fixtures now exist. The wrapper's old source hash
intentionally no longer matches the corrected runner, preventing accidental
execution. A separately validated existing-fixture-only continuation is still
required; no reseed, cleanup, credential rotation or fixture modification allowed
during diagnosis. Both admission gates remain CLOSED.

## Historical status confirmed / existing-only continuation prepared

Founder recovered the original backend log: POST /api/decision-feedback returned
422 Unprocessable Entity. No new request was issued. This closes the historical
status UNKNOWN above and corroborates the verifier transport defect; it does not
constitute an authentication-denial or API isolation PASS.

Continuation now requires explicit -ExistingOnly in the protected wrapper and
EXISTING_ONLY at the Python CLI. It cannot enter the seed loop. Both exact stable
fixture IDs and all originally supplied fields must match their tenant/entity
scope; one A26 analysis/envelope per scope and zero feedback/patterns/arcs remain
mandatory. Missing/changed/foreign fixtures refuse without replacement. Snapshots
are rechecked before probes and compared after every operation. No resume after
partial feedback writes is supported. Successful output requires zero inserts,
two verified existing fixtures, two authorized unsure writes/pattern rows and
fifteen adversarial denials. Wider proof flags remain false.

24 targeted local tests PASS, including continuation without insertion, altered
and missing fixture refusals, and rejection of a second run after feedback exists.
PowerShell -ExistingOnly -CheckOnly PASS, with no secrets/network/writes. Safe
failure output now includes numeric expected/observed HTTP statuses, never bodies.
No live continuation performed by agent; protected local credentials require
Founder execution once. No new backend version or migration is required for this
verifier-only correction. A28 remains OPEN and all gates unchanged.

## Founder live existing-only PASS — 2026-09-23

Executed once; BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS. Two existing fixtures
verified; continuation_existing_only=true; zero fixture inserts; two authorized
unsure writes; two derived pattern rows verified; fifteen adversarial refusals.
A26 pairs unchanged by runner snapshots; no arcs created; existing DPAPI unchanged.
These two feedback writes and their pattern recalculations were explicitly
authorized synthetic effects, distinct from the fifteen refused adversarial probes.
Business writes occurred. No rerun after PASS; preserve fixtures and feedbacks.

api_write_isolation_proven=true ONLY for A28_TWO_LEGACY_UNSURE_API_WRITES_ONLY.
write_isolation_proven=false; analysis_export_isolation_proven=false;
global_isolation_proven=false; production_proof=false. No other feedback status,
governed lifecycle write, output route or production topology is covered.
External Provider and Real-data Admission CLOSED. Local package awaits checkpoint.

Next priority: positive own-analysis/exports plus foreign denial with the two
technical sessions. Current governed routes have a single designated-company
guard before ownership lookup; two undifferentiated 404s cannot prove isolation.
Preserve that guard. Determine a bounded rehearsal configuration rather than
weakening admission or claiming an all-denied probe proves output isolation.
