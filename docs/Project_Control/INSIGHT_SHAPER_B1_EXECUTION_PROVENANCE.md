# B1 execution provenance — prepared persistence boundary

2026-09-24; base dd8a99868a3fd68b8038fddc9f5c0399eec00fe0.
IMPLEMENTED / LOCAL_TESTED / MIGRATION_NOT_APPLIED / NOT_LIVE_PROVEN.

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
