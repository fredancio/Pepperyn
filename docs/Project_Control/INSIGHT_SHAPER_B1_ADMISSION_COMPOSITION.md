# B1 — prospective backend composition: evidence and limits

2026-09-28. Founder invariants accepted as guarantees to demonstrate before
admission, not eighteen independent new subsystems. B1 OPEN. External Provider
CLOSED. Real-data Admission CLOSED. No new producer, route, permit or migration
activated. This slice is local preparation, not generic-producer admission.

## Architecture reconciliation

In this repository `companies.id` / `company_id` is the tenant; the CFO's client
company is `entities.id` / `entity_id`. V19 makes Engagement:Entity permanently
1:1; the tenant is resolved through entities, not a second engagement tenant
column. Thus the Founder chain maps to:

`verified Auth user -> profiles.company_id -> companies -> entities.company_id
 -> engagements.entity_id -> prospective analysis -> exact source -> selected
 producer/version -> contract -> task/version -> immutable input`

The old `_resolve_auth` API returns company/plan/type, not an actor identifier.
This new, unmounted adapter therefore uses the same backend `auth.get_user`
verification and authoritative profile lookup but preserves the actual actor.
Missing/ambiguous profiles fail closed, with no guest or company fallback. This
does not change existing login/read behavior. Test authentication is a fake;
no new live-auth proof is claimed.

Reuse: OwnershipAuthority's sealed in-process capability pattern, lock and
monotonic TTL; existing scope/record types, `_one` read validation, governed
workbook ingestion, envelope validation and candidate consistency. A prospective
resolver is necessary because persisted-analysis read grants cannot honestly
authorize a new analysis. No synthetic old analysis is invented to obtain one.

## Bounded implementation

`governed_producer_admission.py` resolves actor and authoritative parents, accepts
only one trusted server-configured synthetic profile (scope, exact source hash /
filename, producer/version and task/version), and generates prospective analysis,
request and execution UUIDs server-side. It refuses any existing analysis,
envelope or receipt with that analysis ID. It snapshots the actual understood
input into immutable JSON. The opaque capability registry binds the complete
composition, not independently exchangeable evidence pieces.

Consumption verifies the actor again, atomically consumes one recognized attempt,
checks the exact composition and source bytes, and re-resolves parent ownership
and prospective-ID absence. Expiry/closure is checked again after these reads.
The registry refuses duplicate local analysis reservations and stops at 1024
entries rather than evicting tombstones and permitting local ID reuse.

The method deliberately returns only input for local validation. There is no
producer call, network transport, persistence adapter, promotion or receipt
issuer. The profile's trusted configuration is a security boundary, not proof
that arbitrary content with a supplied hash is synthetic. No route accepts a
profile. No installed production profile exists.

## Accept -> refuse -> expected evidence

LOCAL below means fake-auth/in-memory DB tests, not deployed enforcement.

| Invariant | Accept condition | Refuse condition | Expected evidence / current status |
|---|---|---|---|
| 1 Actor | Backend Auth user and exactly one profile | Missing/invalid token; missing/ambiguous profile; actor switch | LOCAL positive/negative; actual deployed Auth and profile protection still required |
| 2 Tenant | Profile-resolved tenant equals fixed trusted scope | Foreign tenant or changed membership | LOCAL; no request tenant field |
| 3 Company | Exact entity belongs to resolved tenant | Foreign/missing entity; parent change | LOCAL before parsing and consumption |
| 4 Engagement | Exact engagement belongs to that entity | Foreign/missing/ambiguous engagement | LOCAL; preserves V19, no extra tenant column |
| 5 Analysis | Server UUID absent in all three tables; unique locally | Existing/partial ID; local reservation reuse | LOCAL collision/recheck; cross-process atomic reservation OPEN |
| 6 Source | Exact admitted bytes/hash/filename and derived representation | Swap, append mutation, mutable bytearray, wrong filename | LOCAL; no input returned, no writes |
| 7 Producer | Trusted backend profile's exact id/version | Valid-looking replacement or reserved V1 mock identity | LOCAL binding; actual producer registration/implementation OPEN |
| 8 Contract | Exact hash of profile and fixed local-only policy | Different contract hash | LOCAL commitment substitution test |
| 9 Task/scope | Exact task/version and all scope fields | Task swap, foreign scope, scope widening | LOCAL all binding fields tested |
| 10 Whole composition | Same issued grant and immutable composition | Mix two valid preparations; replace any binding/input/filename | LOCAL; no interchangeable receipt fragments |
| 11 Privacy/egress | Local validation only; no transport method | External use not admitted at all | Zero network attempts in new tests; task-specific external projection/return proof OPEN |
| 12 Validity/replay | Same issuer; open; within TTL; one consumption | Expired/closed/consumed/foreign worker grant; concurrent replay | LOCAL one winner; restart rejects old handles, NOT durable multi-worker replay proof |
| 13 Immutability | Committed immutable input and exact source recheck | Mutation after preparation; ownership revoked during interval | LOCAL; no host-admin/tamper-resistant claim |
| 14 Execution/receipt | Actual execution matches authoritative bindings | Candidate mismatches any expected field/envelope | Candidate consistency LOCAL; actual producer/receipt correspondence OPEN |
| 15 Atomic persistence | Analysis/envelope/admitted receipt in one exact-version transaction | Partial/inconsistent/unadmitted execution | Not implemented for new contract; no writer exists; V39 rejects candidate before RPC. New SQL and live rollback proof OPEN |
| 16 No producer authority | Coordinator alone selects profile and authority | Producer-supplied permission/identity | No producer admitted/called in slice; actual adapter boundary OPEN |
| 17 Provenance | Actor/scope/source/producer/task/contract/input/output linkage | Missing or substituted fields | Candidate schema + local binding LOCAL; durable audit trail and terminal dispatch OPEN |
| 18 History | Existing V39/mock labels and readers unchanged | Reuse mock identity or persist candidate through V39 | LOCAL rejection + existing persistence/pipeline regression; no historical writes |

For every new adversarial test, database tables equal their pre-attempt snapshot
and no RPC occurs. A socket spy asserts **zero attempted connections**, including
exceptions that could otherwise be swallowed. Refusal checks are not just HTTP
codes; there is no HTTP surface in this slice. These tests cannot certify side
effects of an as-yet-uninstalled real producer.

## Limits that block generic admission

The capability registry is process-local. A restart loses its authority; another
worker refuses the handle. That is safe refusal, not durable exactly-once
execution. Pre-execution absence/parent checks do not close the database race
between validation and commit. Before any generic durable execution, require a
separate admitted receipt and atomic persistence protocol which rechecks the
scope and uniquely reserves request/execution/analysis identity transactionally.
Uncertain attempts must remain closed; no automatic replacement identity/retry.
Do not widen V39 or its fixture guard to achieve this.

The current producer-execution-candidate-2 remains UNADMITTED_CANDIDATE. The new
actor_id is required prospectively; no persisted candidate exists to migrate.
No backend profile can serve as External Provider or Real-data Admission. The
actual general producer, source admission beyond governed synthetic fixtures,
task privacy/return policy, database version and UI/export version dispatch all
remain OPEN. Financial correctness remains subject to FR-EXPECTED-2 and its
professional gate; no outcome or learning is inferred.

## Tests and outstanding regression debt

199 tests PASS: new composition/candidate, execution provenance, governed pipeline,
persistence, ownership, minimal projection, provider response and V33 correspondence.
Existing v1 pipeline regressions include the three exports. No live DB/server test.

Two old ownership-test expectations were stale: replay now refuses at the earlier
one-use projection barrier, and the caller inventory omitted committed V34 and
test callers. The first failure was reproduced with ownership_authority loaded
directly from HEAD; committed callers were confirmed with `git grep HEAD`.
Tests now require the actual early refusal AND exactly one mocked dispatch, and
an exact reviewed caller list (including the new verified-auth adapter).

An additional wider `test_llm_egress_authority` run still exposes a pre-existing
static-policy debt: eight network-import findings in five committed bounded
sandbox modules (output_live_transport, preflight_connected_b1,
rehearse_execution_receipt_v39, verify_feedback_privileges,
verify_isolation_accounts). The same findings were
reproduced scanning only HEAD blobs. The blanket allowlist was NOT relaxed.
This suite is not recorded as PASS. Review those bounded network surfaces before
claiming a repository-wide no-bypass proof or wiring a new transport. None is
called by this composition module; this is not evidence of an external LLM call.

Next implementation dependency: reconcile actual producer execution with a
separate admitted receipt and atomic durable admission, while keeping the
application mount off. Database deployment or a remote rehearsal still requires
specific Founder authorization. Current source/test preparation is uncommitted;
R5 checkpoint c1e22508 remains intact and the nine prior exclusions are untouched.

## Historical prerequisite: local PostgreSQL initially unavailable

2026-09-28 read-only runtime inspection: no psql/postgres/initdb command was found
and no installation was found at the checked standard PostgreSQL location.
docker.exe is installed, but the local docker_engine named pipe is absent and
the CLI cannot reach a running engine. CLI also reports denied access to its
user configuration; no configuration or credential content was read or changed.
No container, database, migration, source profile or receipt was created.

Next bounded proof must use a disposable local PostgreSQL instance, synthetic
identities only and no Integration Test credentials. It must exercise two actual
database sessions/processes, not treat a Python lock or fake RPC as SQL proof.
Before requesting any Supabase deployment, prepare and test the separate durable
contract against that instance. Reuse the governed envelope transaction where
appropriate, never extend persist_governed_execution_v1 or its V39 source guard.

Required protocol to falsify:

- durable immutable whole-composition reservation, unique request/execution/
  prospective analysis, exact trusted producer policy and authoritative parents;
- one atomic claim committed BEFORE execution, so a producer failure or restart
  cannot make admission executable a second time;
- result/envelope/new receipt written together, with an exact admission match
  rechecked inside the transaction; no incomplete governed result on late failure;
- terminal refusal on expiry, closure, cross-scope substitution, concurrent replay
  or receipt mismatch; uncertain acknowledgements require inspection, never an
  automatic retry, new identifier or erasure of consumed evidence;
- process restart and concurrent-connection tests, including a killed/failed
  claimant, with durable rows and forbidden effects inspected independently;
- backend-only privileges and an empty/closed producer admission configuration
  until separately authorized. Schema presence does not admit a producer.

At that inspection these were requirements for a forthcoming SQL implementation, NOT evidence that
it exists or works. No new migration has been authored or applied in this step.
Founder local intervention needed: start Docker Desktop deliberately, without
manually starting existing Pepperyn services/containers, so the agent can first
inspect the engine and select an isolated test instance. Do not start a cloud
environment, provide secrets or reopen R5. If Docker startup would affect an
existing sensitive workload, stop and inspect rather than changing it.

## Superseding local SQL evidence — 2026-09-28

Founder started Docker; the isolated local proof is now complete. The earlier
absence-of-SQL and unavailable-runtime statements describe the prior state only.
V40 and an unmounted backend adapter are implemented and locally tested, NOT
deployed to Supabase and NOT evidence of actual generic producer admission.
See INSIGHT_SHAPER_B1_DURABLE_ADMISSION_V40.md for the exact proof and limits.

The matrix above remains the preparation-layer assessment. Its durable gaps
5/10/12/13/15/17 now have bounded actual PostgreSQL coverage: unique reservation,
immutable composition, committed one-use claim, concurrent claim refusal,
atomic result trio with terminal refusal after late failure, and independent
client-process recovery. Scope is a reduced synthetic PostgreSQL schema, not
deployed Supabase/Auth, HTTP, server restart or global isolation. No actual
generic producer has been called or admitted; 7/14/16 still require its controlled
connection and evidence. Terminal output dispatch remains OPEN.

Preparation-only policy cannot be promoted into persistence authority: the
durable adapter requires the distinct LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2 policy.
V40 is empty/closed on deployment, with no producer-registration RPC. No profile
is installed remotely. 211 targeted Python tests plus 29 actual local PostgreSQL
tests PASS. The global static egress debt remains OPEN; no allowlist relaxation.
Local source/test evidence is uncommitted after R5 checkpoint c1e22508.
