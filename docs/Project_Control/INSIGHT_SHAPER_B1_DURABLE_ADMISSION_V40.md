# B1 — V40 prospective durable admission, bounded local proof

CURRENT DEPLOYMENT UPDATE (2026-09-28): applied once to Integration Test under
separate Founder GO. Structural/vacuity/preservation checks observed conformant,
but supplementary function-body fingerprints mismatch: STOP, cause UNKNOWN.
Full deployment conformance NOT PASS. The preparation history below is preserved;
see INSIGHT_SHAPER_B1_V40_DEPLOYMENT_INSPECTION.md for the superseding remote state.

LATER DIAGNOSTIC RESOLUTION: separate read-only Founder GO established exact
CRLF-only differences for all six bodies, with SQL-normalized hashes matching
source. No semantic difference or remote correction. Initial mismatch evidence
is retained; see the diagnostic section of the same report. No producer admitted.

2026-09-28. IMPLEMENTED / LOCAL_POSTGRESQL_TESTED / NOT_REMOTE_DEPLOYED /
UNCOMMITTED. B1 OPEN. Generic producer UNADMITTED. External Provider CLOSED.
Real-data Admission CLOSED. Self-Selling DEFERRED.

## Purpose and authority

A process-local capability must not be mistaken for durable execution authority.
Restart, concurrent workers, a lost acknowledgment or a late receipt failure must
not permit a second execution or leave a governed result without its provenance.
Reuse the authenticated preparation and V27 atomic envelope transaction; do not
extend V39, relabel historical mock evidence or invent a parallel analysis engine.

`v40_prospective_execution_admission.sql` adds three separate registries:
producer_policies_v2, execution_admissions_v2 and execution_receipts_v2. Existing
V27/V39 sources are unchanged. The distinct contract is
local-synthetic-durable-admission-2; its backend policy is
LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2, not the earlier no-persistence preparation
policy. An unmounted DurableProducerAdmission adapter invokes only the new RPCs.
It neither runs a producer nor installs policies nor opens any HTTP transport.

## Lifecycle and refusal semantics

RESERVED -> CLAIMED -> COMPLETE or REFUSED. RESERVED/CLAIMED may be CLOSED.
No backward transition, deletion, material composition mutation or re-claim.

1. Backend authenticates the actor and derives exact scope and source/input using
   existing governed preparation. No request-supplied policy is accepted.
2. Reserve RPC requires an explicitly enabled, exact synthetic/no-egress policy,
   validates parents and bindings, and uniquely reserves request/execution/analysis
   identity. The database hashes the whole policy/bindings/input/filename object.
3. Claim RPC locks the row, rechecks expiry/policy/parents and commits CLAIMED
   before execution can proceed. Only one concurrent claim succeeds. A lost
   acknowledgment means DO NOT EXECUTE; no retry or replacement UUID.
4. Completion reauthenticates, validates source facts and request nonce, constructs
   provenance in the backend, then validates the durable claim and candidate in
   SQL. Analysis, envelope, new receipt and COMPLETE transition commit together.
5. Ordinary validation/late SQL failure rolls back the entire result trio while
   recording REFUSED. A transaction cancellation/crash can leave CLAIMED, never
   reopen it. Uncertain completion requires inspection, not retry or cleanup.

There is no claim of exactly-once external execution. No provider is used. The
receipt scope is LOCAL_SYNTHETIC_ONLY, not a certification of financial quality
or an assertion that a generic producer is admitted. Candidate remains
UNADMITTED_CANDIDATE; acceptance of test persistence is not product admission.

All three tables have RLS and no client policies; anon/authenticated have no
table/RPC privileges. Service role has SELECT plus four bounded RPCs, no direct
table DML. There is no policy-registration RPC. Policies are empty on deployment;
an enabled policy can only be disabled, not silently rewritten/re-enabled.
The trusted backend owns authentication; SQL verifies membership/parent bindings.
A compromised service role/database owner is not neutralized by these tests.

## Evidence actually obtained

Docker Desktop started by Founder. Agent verified engine and created only
pepperyn-b1-pg16-20260928, label pepperyn.purpose=b1-synthetic-sql-test. Official
postgres:16 image digest:
sha256:1a6ab3f5345eb6dbe04a1349529caabdb0ab09293a09590fad07b2246bfa4b54.
Network none, no published port, no host bind; PostgreSQL data is in container
tmpfs. Local socket trust is confined to this isolated disposable test container,
not a recommended application deployment. Existing n8n container untouched.
No Supabase/JWT/V33/DPAPI credential was used or read. No cloud operation occurred.

Each test run creates a new uniquely named database; existing databases are not
dropped. Reduced representative parent tables plus actual V27 and V39 migrations
precede V40. Synthetic policy and scope fixtures are installed only in that local
database. A registered mock supplies test output: this is NOT execution of the
future generic producer. Each SQL call uses a separate psql process/transaction.

Final actual PostgreSQL suite: **29 PASS in 55.34s**. Includes:

- preflight PASS before installation, empty registries and exact postflight
  privileges/triggers afterward, preflight refusal on already-installed schema;
- positive atomic trio and exact binding, reread from independent client process;
- two competing processes with one successful claim, abandoned claim unreusable;
- field substitution, duplicate identities, cross-scope/membership changes;
- receipt/envelope/request mismatch and expired completion: no result trio;
- injected late receipt failure: no analysis/envelope/receipt survives, REFUSED;
- policy disable, closure, replay, material mutation and client/direct-DML denial;
- real Python adapter through SQL-backed test client, including separate
  coordinator instances and no fallback to the old V39 RPC.

Targeted Python regression: **211 PASS**, three warnings. Includes preparation,
candidate, adapter, ownership, governed pipeline/persistence, minimal projection,
provider-return quarantine and correspondence suites. Adapter tests refuse
uncertain or substituted acknowledgments without retry/fallback, and refuse
promotion of a preparation-only contract into persistence authority.
These are selected suites, NOT a full-repository PASS. The previously documented
eight static network-import findings in five old sandbox files remain OPEN.

## What this does not prove

- No remote V40 deployment, Supabase Auth/PostgREST or deployed RLS proof.
- No full historical migration replay; local parent schema is deliberately reduced.
- Fresh independent client processes are proven, not PostgreSQL/container/host
  restart or disk durability. Tmpfs contents disappear when the container stops.
- No actual generic producer, HTTP/UI mount, v2 terminal/export dispatch, provider
  privacy admission, real-data ingestion, professional reliability or Beta readiness.
- No global isolation, external side-effect exactly-once guarantee, key-custody,
  backup/restore or production proof. No historical record was requalified.

## Next boundary and required authorization

V40 preflight and postflight SQL files are prepared and tested locally. The next
remote schema step requires explicit Founder authorization for Integration Test
project ejixkplrgobgwqnhidwt ONLY: read-only preflight, one transactional V40
installation if conformant, then read-only object/privilege/empty-registry checks.
Project identity must be verified independently; preflight deliberately reports
project_identity_verified=false. Any unexpected/partial existing object refuses
installation; no automatic overwrite, reset, destructive recovery or retry.

Scope of that future authorization: three new empty tables, three triggers and
six functions with their exact privileges; no source policy registered, no
admission, analysis, envelope or receipt created, no existing history changed.
It does NOT authorize a subsequent synthetic write rehearsal or actual producer
activation. Those need their own bounded protocol/authority. No Supabase operation
has yet been performed. Generic producer connection and remaining egress/terminal
debts must be addressed separately; schema deployment alone cannot close B1.

## Durability

Current Git anchor remains c1e22508fff296385014f7d82718e3e64220aa64. This work is
local/uncommitted; the nine strategic/DEC-032/next-env exclusions are preserved.
The test harness is the reproducible proof source; transient test databases are
not a durable Git checkpoint or a production backup.

## Subsequent remote evidence — 2026-09-28

The local-only and pending-deployment statements above describe the preparation
stage, not the current bounded state. V40 was deployed separately; the first
rehearsal failed and its four control rows remain immutable historical evidence.
After the separately authorized local serialization/parity/sequencing corrections,
the distinct successor passed live with nineteen effects including one Auth,
seven new rows, race/rollback/anti-replay and independent application-process
recovery. Both policies are now disabled. No V39/V40 reapplication or alteration.
See INSIGHT_SHAPER_B1_V40_SUCCESSOR_LIVE_EVIDENCE.md for the exact identities,
hashes, independent postcheck and limits. The actual generic producer remains
UNADMITTED, B1 OPEN, both admission gates CLOSED. Evidence is local/uncommitted.
