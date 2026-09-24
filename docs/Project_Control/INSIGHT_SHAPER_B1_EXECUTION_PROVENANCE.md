# B1 execution provenance — prepared persistence boundary

2026-09-24; base dd8a99868a3fd68b8038fddc9f5c0399eec00fe0.
IMPLEMENTED / LOCAL_TESTED / INTEGRATION_SCHEMA_DEPLOYED / BOUNDED_MOCK_RECEIPT_PERSISTENCE_RECOVERY_LIVE_PROVEN.
The preparation narrative below is historical; the deployment addendum supersedes
only its migration-not-applied and deployed-catalog-not-verified statements.
The final live rehearsal addendum further supersedes pending receipt proof only
within its stated synthetic scope. B1 overall remains OPEN.

## Why and scope

An immutable financial envelope describes content, not how it was executed.
Generic exports must not inherit fixed synthetic/mock/no-network labels from the
current closed demonstration. Execution provenance must be recorded prospectively,
bound to the actual source, envelope and ownership scope, rather than inferred from
file names or supplied by an end user. This precedes generic export activation.
Here execution means the analysis-processing run, NOT the professional decision
Execution introduced in V31. No decision, follow-up, business execution, outcome,
learning or expected impact is created by this receipt.

BEFORE: V27 atomically saved analysis and envelope, without an execution receipt.
AFTER (prepared, not activated): a trusted closed mock adapter can issue an explicit
receipt after successful execution; an optional persistence protocol sends analysis,
envelope and receipt together through one new RPC. Existing calls still use V27.
No HTTP route or UI is changed, no migration/data write has been performed, and no
running service was restarted. Existing analyses and their evidence are preserved.

## Contract and authority

- `execution_provenance.py`: closed, frozen, revalidated schema; execution UUID,
  executor version, registered-synthetic origin, local-mock mode, no transport,
  raw source hash, representation hash, envelope hash and aware completion time.
- `run_recorded_registered_mock_analysis`: accepts only source bytes/name, executes
  the existing registered mock, then records those attributes itself. Caller cannot
  supply provider/origin/transport labels through this adapter. It is not a generic
  ingestion authority and does not make arbitrary uploads synthetic.
- Persistence additionally binds analysis/company/entity/engagement. Hashes detect
  content mismatch; they are NOT digital signatures or proof against a compromised
  backend/service role. Authentication/ownership is still required before invocation.
- V39 is intentionally limited to that single existing admitted mock producer and
  exact workbook hash/name. This is an admission restriction, not hard-coded FR
  financial reasoning. Supporting other executors requires a reviewed extension;
  the schema must not be loosened merely to obtain generic-looking coverage.
- The new RPC creates a NEW analysis through V27, then inserts the receipt in the
  same statement transaction. Existing analysis IDs or reused execution IDs fail.
  No upsert/backfill/legacy certification path is provided. Missing/uncertain RPC
  acknowledgement is refused with no retry and no fallback to unreceipted saving.
- Reader first checks the scoped envelope, receipt hash/scope, raw source binding
  and model. Missing receipt is `None` (unattested), not local/mock proof. Database
  failure or corruption is an error, never an absence or inferred provenance.

No claim of OS-wide network monitoring is made: NONE describes the reviewed local
executor with no provider transport. Its test blocks socket connection attempts.
Executor version is not an attestation of the complete deployed Git revision;
deployment evidence must separately bind revision/build and running configuration.

## V39 operational boundary

New backend-only table: RLS enabled, no client policies, SELECT only for service
role; direct insert/update/delete denied. Only the new security-definer RPC inserts.
UUID scope foreign keys, unique execution ID and mutation-refusal trigger preserve
append-only provenance. Trigger/FK also refuse deletion of referenced records.
No legal retention duration is invented. A governed purge procedure remains B7
debt and is required before real-data admission; do not disable these constraints
to make deletion work. No existing row or V27 function is modified.

Migration is transactional and refuses an existing/partial installation rather
than overwriting it. The read-only preflight inspects catalog presence/privileges,
not business data; it does not prove project identity or complete deployed schema.

## Evidence and remaining work

96 targeted local tests PASS (receipt protocol plus persistence, shared reads,
workbook inspection, synthetic routes, exports, output isolation, temporal and Beta
admission regressions). Receipt tests cover substitutions, model-copy bypass,
single-RPC payload binding, uncertain acknowledgement without retry, unregistered
input, legacy absence, reload/tamper and database read failure. SQL tests are static.

No local PostgreSQL was available (Docker daemon absent). Therefore SQL execution,
transaction rollback, replay constraints, deployed grants/RLS and restart durability
are NOT proven. Do not describe a mocked RPC as proof of atomic database persistence.
No complete FR case or gate was executed/closed. FR-EXPECTED-2 unchanged.

Next: checkpoint the prepared implementation. Then inspect the approved Integration
Test catalog read-only, validate the exact migration plan, and obtain explicit
Founder authorization before applying V39. Only after its deployed checks may a
separately authorized synthetic write rehearsal be proposed. Do not create another
analysis or receipt merely to retrofit the existing Founder analysis.

Generic ingestion, real execution/provider receipts, terminal display/export of
receipts, deployment revision binding and production purge/custody remain open.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## Authorized V39 deployment — 2026-09-24

Founder explicitly authorized preflight, one application and read-only postflight
on Pepperyn Integration Test only. Project name and reference
`ejixkplrgobgwqnhidwt` were verified in the authenticated Supabase dashboard.
Repository HEAD: `1b729888df2de776a9e8cf18440faf9aba2879e2`.
The migration matched committed HEAD; local file SHA-256:
`FED32557CBA5B93AA7DFAF7E850C4924342DFDFA26CAEC83A2AB0C9A7A3B389D`.

Two READ ONLY catalog inspections passed before application: V39 table/functions
absent; V27 envelope and UUID-returning definer RPC present; required UUID columns,
valid unique scope indexes, roles and CREATE/REFERENCES privileges present. No
application rows were read by preflight. The migration was submitted once in SQL
Editor and returned `Success. No rows returned`.

Postflight used BEGIN TRANSACTION READ ONLY / ROLLBACK and observed:

- Eight expected NOT NULL columns with UUID/JSONB/text/timestamptz types.
- Seven validated constraints: analysis primary key, unique execution UUID,
  three scope/envelope foreign keys with DELETE RESTRICT, two payload/hash checks.
- RLS enabled; zero policies; zero PUBLIC table ACL entries.
- anon/authenticated: all seven table privileges false. service_role: SELECT
  true; INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER false.
- RPC: UUID return, SECURITY DEFINER, postgres owner, fixed pg_catalog/public
  search_path; EXECUTE service_role true, anon/authenticated false, PUBLIC ACL zero.
- Trigger function: postgres owner, same fixed search_path, invoker, no EXECUTE
  for anon/authenticated/service_role/PUBLIC. Immutability trigger enabled (`O`),
  BEFORE DELETE OR UPDATE, bound to that function.
- Receipt count exactly zero. No receipt RPC was invoked. No new analysis,
  receipt, history update, synthetic rehearsal or provider call was performed.

This proves SQL deployment and observed catalog protections, NOT application
persistence, transactional rollback under failure, replay rejection in execution,
restart durability, adversarial session enforcement, production or B1 completion.
No historical analysis was retro-certified. The prior 96 tests remain local
evidence; no claim of a new test run accompanies this schema-only deployment.
SQL Editor evidence location: project above, query
`d9ab7ce9-ea5a-4c6e-8a6c-50445658ec9b` (final read-only postflight).

Next boundary: prepare a bounded prospective synthetic persistence/read-back
rehearsal and obtain separate Founder write authorization BEFORE execution.
Current approval does not cover that rehearsal. B1 remains OPEN. Both gates
remain CLOSED. This deployment addendum is local documentation pending a later
durability checkpoint; the migration itself was already checkpointed at HEAD.

## Authorized rehearsal preparation — 2026-09-24, NOT RUN LIVE

Founder subsequently authorized exactly four RPC attempts, technical isolation
account 1's existing scope, the registered English workbook, and at most three
durable rows. No cleanup/retry/replacement IDs, historical changes or gate opening.
If failure follows a commit, preserve the rows as INCOMPLETE evidence; the no-cleanup
instruction takes precedence over treating incomplete evidence as accepted proof.

Prepared `backend/sandbox/rehearse_execution_receipt_v39.py` and
`scripts/rehearse-execution-receipt-v39.ps1` implement:

1. Verify the existing A24 identity through its real user session, profile and
   service-read scope metadata; only account 1 is used. Auth sessions are created,
   but accounts/credentials are not. No business API admission/designation change.
2. Fixed namespace-derived IDs, exclusive local manifest creation, bounded initial
   snapshot of full-row hashes in the three scoped tables. No row contents/secrets
   are written to the manifest or diagnostic output. Existing manifest means STOP.
3. P0001 binding refusal with no rows; deliberate invalid receipt hash-format
   causing the specific 23514 receipt CHECK failure after V27, with absence of all
   three negative objects; one positive save via the actual application service;
   exact replay refused by 23505 analyses_pkey, persisted contents unchanged.
4. Four-call transport budget latched before each attempt, no retries/redirects,
   no generic mutation transport. The local mock rejects socket connections.
   Supabase calls are pinned to the Integration Test project, not a model provider.
5. First process terminates; a second independent Python invocation reloads the
   manifest and production readers, verifies receipt/source/envelope/scope hashes,
   unchanged prior scoped rows and exactly three additions. It makes no business
   writes. A new authentication session is not financial data mutation.

Read-only SQL Editor precheck additionally inspected both deployed RPC bodies,
analysis PK name and all non-internal triggers on the three tables: V27/V39 bodies
conform to the prepared sequence; analyses_pkey confirmed; only the two expected
immutability UPDATE/DELETE triggers exist, no insertion trigger; receipt_count=0.
This is observed deployment evidence, not a continuously monitored schema lock.
Query 254182a9-94a5-441c-9fae-619ac8226d4d, project ejixkplrgobgwqnhidwt.

Local validation: 39 tests PASS (harness, provenance, governed persistence).
Injected timeout, unexpected success, partial rollback, missing acknowledgement,
replay success, fifth call, baseline mutation and receipt tampering are refused.
The fake database tests do NOT establish PostgreSQL rollback or live persistence.
Windows PowerShell 5-compatible wrapper `-CheckOnly` PASS using the actual Founder
backend runtime: imports/mock source/integrity verified, no credentials/network.
Initial pytest discovery/temp-permission issues were resolved using the existing
test venv and a fresh workspace runtime temp directory; no production dependency
was installed or changed.

Execution is pending Founder-local masked Supabase key availability. The existing
A24 DPAPI bundle is restored read-only; JWT and V33/V34 keys are not accessed.
Manifest: `Pepperyn-runtime/v39-receipt-rehearsal.json`, outside Git. Do not delete
it to obtain a retry. No remote write attempt has occurred in this preparation.
Only a complete second-process success permits BOUNDED_V39_PERSISTENCE_RECOVERY_PASS;
it is not HTTP/Uvicorn/browser, global isolation, professional reliability or B1
global proof. No generic ingestion, provider execution, export receipt display,
deployment-revision attestation, retention/purge or production custody gate closes.

## Live rehearsal closeout — 2026-09-24

Founder reports one execution, first process EXITED_SUCCESSFULLY, followed by
`BOUNDED_V39_PERSISTENCE_RECOVERY_PASS` from the independent second Python process.
No rerun or other command reported. This supersedes the preparation's NOT RUN LIVE
state. Evidence sources are the Founder terminal result plus the local first-process
manifest, inspected read-only; no new remote query or write was made for closeout.

- Project: ejixkplrgobgwqnhidwt, technical account 1 existing scope only.
- New analysis/envelope/receipt shared analysis UUID:
  `5c441eb9-99fc-55eb-bd33-da29d1fc2ba5`.
- Prospective execution UUID: `56a65c32-8ba4-4e6b-a014-e75f81b1c03b`.
- Manifest attempts=4. Binding refusal P0001 left no rows. Receipt CHECK failure
  23514 left no analysis/envelope/receipt, demonstrating the tested late rollback.
  Positive save persisted three rows. Exact replay refused by 23505, unchanged.
- Before/after scoped counts: analyses 2 -> 3, envelopes 1 -> 2, receipts 0 -> 1.
  Existing scoped row hashes unchanged, independently checked locally against the
  manifest. No general database-wide non-mutation/isolation claim is inferred.
- Second-process production reader validates raw source, representation, envelope,
  receipt and exact ownership scope, and compares the persisted row hashes with
  first-process results. Founder reports success, not an agent-run second attempt.
- No provider or real data; no JWT/V33 access. Founder reports existing protected
  bundle unchanged (terminal transcription says DPAJI; wrapper spells DPAPI).

Manifest SHA-256:
`EC04ACE59CBBBE63C1C9B8459868B6F0330730B1753356F4AEE03E89885692D3`.
Harness SHA-256:
`B832B00D120723FAE5040A9A24F02D0DFEB55E6337E1D9D8F6F13F9277CE1D90`.
Wrapper SHA-256:
`4F5B762371995228DD22FE0941CF3B2CDB1E6C10FC551D27C6C31BB1307BF806`.
All three hashes were read locally during closeout. Base HEAD remains
`1b729888df2de776a9e8cf18440faf9aba2879e2`; harness/evidence are local and pending
checkpoint. The manifest intentionally retains FIRST_PROCESS_COMPLETE /
V39_PERSISTED_PENDING_SECOND_PROCESS because verification does not rewrite it.
This is not a failure or a reason to rerun. Second-process evidence is the reported
terminal result and the integrity-pinned wrapper's sequential execution contract.

Retain the three positive synthetic rows and the existing manifest. No cleanup,
retro-certification, historical replacement or migration reapplication is needed.
This is a bounded live proof of V39 application-service persistence, tested
atomicity/refusals and recovery after process termination, NOT HTTP/Uvicorn,
browser, generic real-input execution, global isolation, professional financial
reliability, production, or B1 global PASS. Those flags remain false.

Remaining B1 work includes governed generic ingestion/execution admission outside
the sandbox, application transport and terminal/export consumption of trustworthy
execution provenance, and their end-to-end proof. Provider/real-data, custody and
purge/deployment debts remain separate gates. Both admissions remain CLOSED.
