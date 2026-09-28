# V40 successor 1 — distinct launcher and immutable historical evidence

Status: BOUNDED LIVE SUCCESSOR PASS, 2026-09-28, under the subsequent distinct GO
and fresh conformant preflight. See INSIGHT_SHAPER_B1_V40_SUCCESSOR_LIVE_EVIDENCE.md.
The historical preparation/hold records below remain intact; they are not current
execution instructions. The one-shot attempt is closed and must not be replayed.
B1 OPEN; generic producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. This is not a new producer-admission claim.

## Purpose and separation

The first rehearsal is permanently failed evidence, not a resumable run. Its
runtime directory, journal, refusal and manifest are never changed or reused.
The old policy cab54f0d-8b8c-4e77-bae6-7cc0660de0d7 stays disabled. Its three
admissions remain REFUSED / CLOSED / REFUSED, with no associated result trio.
No historical row is copied into a new admission or requalified.

New entry point: backend/sandbox/run_v40_successor.py.
New wrapper: scripts/rehearse-v40-successor-1.ps1.
New exclusive runtime directory: Pepperyn-runtime/v40-successor-1.
Default invocation checks local integrity only, before any credential access.
Explicit execution requires a distinct Founder GO, not the old authorization.
The old PowerShell/Python entry points are neither invoked nor repinned.
Existing composer, durable adapter, effect budget, process handoff and bounded
orchestration are reused. No product API, V39/V40 schema or generic route changes.

## Authoritative historical preflight, not count-based acceptance

1. Verify pinned original manifest, original refusal and original eleven-table
   service baseline. The original failed journal is not opened or consumed.
2. Read the exact four historical control rows using service read-only access.
   Match all seven policy columns to the original manifest and disabled state;
   match three admissions to original bindings and terminal states. Verify no
   result exists for any historical failed analysis identity.
3. Treat this newly read snapshot as a CANDIDATE, not historical authority.
   Generate a READ ONLY catalog ticket. PostgreSQL must compare its actual full
   rows to that exact snapshot and verify the recorded admissions JSONB SHA-256:
   193a878f3b896212db174c1e3ed1adb52f01ae70786fab907b3eaef30dfb09b6.
   Python does not approximate PostgreSQL serialization or normalize content.
4. Independently verify current V40 definitions, objects, grants/protections and
   relevant storage constraints using the established catalog/parity reports.
   The operator attestation must bind the exact ticket hash, snapshot hash,
   project, version, 19/7 ceilings and observations no older than 180 seconds.
5. Re-read history, scope and the original eleven-table hashes after attestation,
   before the one login. Unexpected additional registry rows are not hidden:
   the established empty-NEW-registry check must still pass.
6. Allocate a frozen backend-owned plan containing the policy UUID and all nine
   case UUIDs BEFORE Auth. Check all ten identities against current durable
   identity domains with read-only service access. Persist only this non-secret
   identity plan and its SHA-256, with zero Auth/effect counts, as local evidence.
   Any collision refuses the attempt without login or a replacement identity.
7. Only then authenticate once. Feed the exact frozen triples through a trusted
   constructor-only one-shot allocation source into the existing composer.
   Auth/ownership/source checks still apply; an allocation is NOT a capability.
   The prepare/API caller has no identity parameter. No UUID generation fallback
   is permitted for the supplied source; exhaustion/mutation refuses.
8. Before publishing the composed manifest or any policy ticket, compare all ten
   composed identities to the original frozen plan and commitment. Existing
   state verification binds durable rows to that same composed manifest; final
   confirmation links it back to the pre-Auth commitment.

HistoryReader exposes only the new-run delta AFTER verifying every historical
row exactly against the frozen snapshot on each read. Each independent worker
receives the same snapshot. Both owner statements recheck full history and the
recorded PostgreSQL hash under registry locks, before and after their mutation.
The old policy cannot be targeted by either new owner statement.

## Final proposed remote scope — requires distinct GO

- Only project ejixkplrgobgwqnhidwt, technical account 1 and existing bindings.
- Only pepperyn_v1_heterogeneous_english.xlsx, verified SHA-256
  FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93.
- Existing deterministic rehearsal mock only. It is not the real generic producer.
- Corrected legacy metadata AUTRE; complete rich result/source/envelope preserved.
- One new policy UUID and nine distinct execution/request/analysis UUIDs, generated
  by the backend primitives. No identity replacement or retry on collision.
  All ten must be absent from the existing identity domains before AUTH_ONCE.
  They are checked again before POLICY_INSERT without replacing them.
  Owner SQL independently rechecks absence in the relevant durable tables.
- At most seven NEW durable rows: policy 1, admissions 3, analysis 1, envelope 1,
  v2 receipt 1. The four old rows remain intact: eleven evidence rows in total.
- At most 19 effect-capable requests: one Auth login including its session effects,
  two owner actions, sixteen RPC calls including expected refusals. No refresh or
  second login. Tokens remain in memory/pipes, never files, logs or command lines.
- No historical updates, schema change, V39/V40 reapplication, cleanup, real data
  or provider. No server/browser transport is activated by this launcher.

## Exact effect sequence

1. AUTH_ONCE (after catalog/historical preflight).
2. POLICY_INSERT, new policy only.
3–4. INVALID_SCOPE and INVALID_SOURCE: refuse with no admission/result.
5–8. ROLLBACK_RESERVE / CLAIM / COMPLETE / RECLAIM: intentional late envelope
   failure; terminal REFUSED; no analysis/envelope/receipt; reuse denied.
9–12. ABANDON_RESERVE / CLAIM / RECLAIM / CLOSE: distinct processes; second claim
   denied; explicit CLOSED; no result trio.
13–16. POSITIVE_RESERVE / CLAIM_A / CLAIM_B / COMPLETE: concurrent independent
   processes, exactly one claimant; exactly one atomic result trio.
17–18. POSITIVE_RECLAIM / RECOMPLETE: both denied without changing persisted proof.
19. POLICY_DISABLE: new policy only, after positive verification and recovery.

Recovery is READ ONLY in a new process after both competing processes have exited;
it is not an additional effect slot. Every slot is burnt before dispatch/ticket
publication. Every identity/attempt artifact is exclusive-create, no resume/reset.
Owner coordination timeout, token expiry, unknown acknowledgment, unexpected
refusal/success or changed history closes the attempt without retry or cleanup.
If failure leaves the new policy active, disabling it requires separate Founder
authorization; the launcher does not add an unbudgeted containment operation.

## PASS criteria and limits

Exact final new states REFUSED / CLOSED / COMPLETE; two policies disabled; six
admissions total; one new analysis/envelope/v2 receipt with exact bindings;
rollback leaves no partial trio; race and replay refusals observed; independent
recovery succeeds; original four rows and eleven-table historical baseline
unchanged (only new positive analysis/envelope excluded from delta comparison).
Exactly 19 effect attempts / one Auth, no persisted/logged credentials.

Local PASS is not remote PASS. A future remote PASS proves only this synthetic
durable-admission path with registered mock. B1, true generic producer admission,
HTTP/browser integration, global isolation, provider admission, real-data admission
and production readiness are not inferred. The pre-existing global egress scan
failure stays OPEN. The old historical first PostgreSQL exception stays unrecovered.

## Validation record

Local isolated Docker PostgreSQL 16, network none, no published ports; only new
uniquely named test databases, existing databases retained. Real unchanged
V27/V39/V40 SQL and the reconciled 30-column / ten-constraint analyses fixture.
Auth/HTTP simulated; these tests do not establish live authentication or deployment.

| Validation | Observed result |
| --- | --- |
| Populated-history full sequence, anchor mismatch and identity collision | 3 PASS, 392.09s |
| New entry point through final result and second-launch refusal, with real local SQL and independent workers | 1 PASS, 323.40s |
| Final exact-policy snapshot and anchor refusal rerun (overlapping subset) | 1 PASS, 25.39s |
| Storage parity | 15 PASS, 14.84s |
| Existing backend-only/immutability/expiry/no-reenable guards | 3 PASS, 15.55s |
| Application/composition/budget/transport/process/launcher guards, including 29 successor guards | 167 PASS, 7.84s |
| Egress suite | 34 PASS / 1 unchanged global FAIL, eight pre-existing findings |
| New Windows PowerShell wrapper default mode | PASS; no credentials read, no network, no Auth, no remote writes |

The full entry-point test verifies exact 19-slot journal, seven added rows, all
four historical rows unchanged, independent recovery, both policies disabled,
no token/password/service/anon values in emitted output or attempt artifacts,
and refusal to restart the same attempt before any credential read. Mutated
history, enabled old policy, missing rows, altered state/input/claim/material,
colliding IDs, stale/foreign/unbound catalog attestations and old authorization
are refused. A wrong recorded PostgreSQL anchor fails with zero effect attempts.

Initial preparation wrapper SHA-256 (superseded by the pre-Auth correction below):
95A4FCB12997CEE5C691208562A20184B7F8BFA3599345FFC273DCFD3FDE6035.
That version pinned 20 source/migration/fixture files and defaulted to local checks only.
Remote execution is deliberately NOT performed or advertised as currently
preflighted. The next decision is the distinct successor GO under this protocol.
All evidence from this preparation remains local/uncommitted until a later
durability checkpoint. No Git index operation, cloud request or real Auth login.

## Subsequent conditional GO — stopped before launch

The Founder requires prospective identity absence to be verified before BOTH
authentication and any write. Static inspection of the unchanged pinned launcher
shows login_once at run_v40_successor.py:140, policy UUID allocation at line 142,
and assert_fresh_identities in the later publish callback. The remaining nine
identities are allocated by authenticated preparation in run_protocol. Thus the
local tests established absence before POLICY_INSERT, not before AUTH_ONCE.

Execution was NOT started: no remote request, Auth or write; successor runtime
directory absent. Wrapper SHA remains unchanged. This is a launcher/precondition
ordering gap, not a remote failure or evidence of changed historical rows.
The four remote rows were not freshly read in this stop; no new remote-state PASS.

Proposed local correction: allocate and freeze fresh prospective identities in
trusted orchestration before Auth, check absence read-only, then bind those exact
identities to authenticated composition without caller-controlled substitution.
Falsify collisions and identity swaps with zero Auth/effect attempts. Do not loosen
the ordering requirement, authenticate early, regenerate on collision or alter the
19-effect/seven-row limits. No code correction or remote retry performed here.

## Subsequent Founder-authorized local sequencing correction

The stop above remains historical evidence; it is not deleted or requalified.
Under the next local-only GO, the launcher now creates a frozen IdentityPlan
before login. Ten mutually distinct UUIDs are checked read-only, then the plan
and SHA-256 are recorded with zero Auth/effect attempts. The single login follows.
IdentityConsumption supplies exactly three immutable triples once each to the
trusted backend constructor. It is not exposed by prepare(), HTTP or the producer.
Authentication, tenant and parent ownership still precede composition authority.
Supplying identities conveys no admission or permission by itself.

The composed manifest must equal the prechecked plan before POLICY_INSERT.
Existing PostgreSQL binding/receipt verification checks persistence against that
manifest; final result also carries the original identity commitment. The full
test compares each persisted execution/request/analysis ID directly to the
pre-Auth artifact. No SQL schema or contract changes, no identity regeneration
fallback, no increase to 19 effects / seven rows.

Current corrected PowerShell wrapper SHA-256:
841537DE4A29367D2C5D0A88A529D3FC111D85536DE6B67C7257CB68F094D2CC.
It pins 21 files. The old wrapper and its pins remain untouched.
Local wrapper syntax and default no-secret/no-network check PASS.
177 application/guard tests PASS (8.71s; includes ten new identity tests).
Egress remains 34 PASS / one unchanged eight-finding global FAIL (1.46s).
Full local PostgreSQL entry-point revalidation: 3 PASS (532.30s), with the unchanged
actual SQL and nonempty synthetic historical state:

- Positive: the real corrected main writes its prechecked identity artifact at
  zero effects/Auth before construction of the mock Auth transport. The test
  independently rechecks identity absence at that boundary. Composed and durable
  execution/request/analysis IDs and policy ID exactly equal this artifact.
  Nineteen effects / one mock login / seven new rows; race, rollback, anti-replay,
  independent recovery, four historical rows unchanged, both policies disabled
  and same-attempt restart refusal still PASS. No mock credentials in artifacts.
- Pre-Auth collision with the historical policy: stage PRE_AUTH_FROZEN_IDENTITIES
  refused, zero Auth/effects, no new policy ticket, admission or result.
- Forced substitution of the constructor allocation after Auth: stage
  SUCCESSOR_PROTOCOL refused, one mock Auth as the only effect, no policy ticket
  or composed manifest published and no new business/control row. The historical
  four rows remain exact; no corrective write, cleanup or fallback generation.

Unit tests additionally forbid postcheck UUID generation in the composer, reject
each swapped identity domain, altered commitment, reordered cases and mutated
plan, enforce one-shot exhaustion, and preserve Auth/ownership checks. These are
local/mocked Auth proofs, not live account or PostgreSQL deployment proof.

The previously authorized 19-effect/seven-row protocol can now be executed with
its literal pre-Auth ordering, but only after the next distinct remote GO and
fresh compliant remote controls. This correction performed no remote read, Auth
or write; the real successor attempt directory is still absent. V39/V40 hashes
and original failure artifacts unchanged. Changes remain local/uncommitted;
frontend/next-env.d.ts and all unrelated work preserved. No Git index operation.
