# B1 - PPR-067 structural hardening deployment protocol

Status: PREPARED / LOCALLY FALSIFIED / NOT DEPLOYED.
Preparation date: 2026-09-29.
Git baseline: `173495c993b9289aba1817ade2bd75fd851cb798`.

## Purpose and boundary

This is the smallest structural deployment of the already validated PPR-067
hardening on Pepperyn Integration Test (`ejixkplrgobgwqnhidwt`). It replaces
only the bodies of `reserve_generic_execution_v3` and
`complete_generic_execution_v3`, retaining their signatures, owners, ACLs,
`SECURITY DEFINER` status and fixed `search_path`.

It does not create or activate a producer policy, admit a producer, authenticate
an actor, reserve or complete an execution, create an analysis/envelope/receipt,
invoke a transport, or process real data. V39/V40/V41 historical evidence keeps
its recorded meaning. B1 remains OPEN and the Generic Producer remains
UNADMITTED after a structural PASS.

## Versioned artifacts

- write artifact: `backend/migrations/prepared_v41_validation_hardening.sql`;
- write artifact SHA-256:
  `7839106C6DFC6C4C03C30438F35C8C1C16050BF2CC1F204D0744281EBE385F16`;
- preflight: `backend/migrations/ppr067_hardening_preflight_read_only.sql`;
- postflight: `backend/migrations/ppr067_hardening_postflight_read_only.sql`;
- historical comparator:
  `backend/migrations/v41_historical_baseline_read_only.sql`.

Only CRLF-to-LF is an authorized representation normalization for function-body
comparison. Raw fingerprints remain evidence. No whitespace, parser or general
SQL normalization is permitted.

## Local protocol falsification

The protocol was exercised against a dedicated database in the existing
network-disabled PostgreSQL 16 container. The database contained the versioned
synthetic fixture followed by V27, V39, V40 and V41; no cloud credential, remote
project or real data was used.

- original V41 state: preflight PASS and postflight REFUSED;
- one local application of the exact write artifact: transaction PASS;
- hardened state: preflight REFUSED and postflight PASS;
- historical baseline before/after: exact equality, 1,076 characters each;
- registry rows and policies before/after: zero;
- post-hardening function fingerprints: exact values recorded below.

This validates the deployment discriminator and historical comparator locally.
It does not claim the Integration Test preflight or deployment has occurred.

## Fresh read-only precontrols

Run all controls against the visually confirmed Pepperyn Integration Test project
immediately before any write, and retain their complete outputs.

1. Verify the project reference is exactly `ejixkplrgobgwqnhidwt`.
2. Run `ppr067_hardening_preflight_read_only.sql`. Its sole acceptable status is
   `PPR067_HARDENING_READ_ONLY_PREFLIGHT_PASS`.
3. Run `v41_historical_baseline_read_only.sql` and retain the complete JSON as the
   pre-write historical baseline.
4. Recompute the local SHA-256 of the write artifact and require the exact value
   above.

The preflight establishes that all five V41 definitions are exactly the original
reviewed LF/CRLF forms; all metadata and execution privileges are unchanged; the
three registries are owned by `postgres`, RLS-enabled, protected by exactly one
non-internal immutable trigger, have no policies, expose read-only service access,
and contain zero rows. Consequently, an already applied, partially applied,
unknown or non-empty state refuses before the write.

Any missing object, unexpected row, policy, grant, owner, signature, default,
function body, bare carriage return or historical-baseline anomaly is a STOP.
There is no retry, repair, alternate identifier, normalization extension or
automatic adaptation.

## Exactly authorized write

After a distinct Founder GO and only after every precontrol passes, execute the
checkpointed write artifact exactly once and without editing it. Its transaction
performs only:

1. a digest guard over the two original reviewed function bodies;
2. `CREATE OR REPLACE FUNCTION public.reserve_generic_execution_v3(...)`;
3. `CREATE OR REPLACE FUNCTION public.complete_generic_execution_v3(...)`;
4. commit of that transaction.

No table, trigger, constraint, grant, RLS setting, policy or application row is
created, deleted or changed. An error rolls back the whole transaction and ends
the operation. No second execution or corrective write is authorized.

## Read-only postcontrols

After a successful transaction, perform only these reads:

1. Run `ppr067_hardening_postflight_read_only.sql`. Its sole acceptable status is
   `PPR067_HARDENING_STRUCTURAL_POSTFLIGHT_PASS`.
2. Run `v41_historical_baseline_read_only.sql` again. Require byte-for-byte JSON
   equality with the retained pre-write baseline.
3. Confirm the three V41 registries remain empty and no producer policy exists.

The exact post-hardening normalized/raw LF fingerprints are:

| Function | LF SHA-256 | CRLF SHA-256 |
| --- | --- | --- |
| `reserve_generic_execution_v3` | `d8c004ce0b0df839929e55594c921610a65849c691e28fcd6b86fd05ea4a7e2d` | `5e5b154d93146c7cce09778d558b00e3f6e0e336f487b8a480e29baed86e46c3` |
| `complete_generic_execution_v3` | `aafa916300af7b47fe619c0e833515ef838a2fd35db3bb3a5ed45427c019cc32` | `e10c16fc82af6e8b631b602f4defd4409ed057d5d055c7a162ec9e6e1aa0f287` |

The claim, close and guard functions must retain their original V41 fingerprints.
Signatures, result/defaults, owner, language, `SECURITY DEFINER`, `search_path` and
ACL behavior must all remain exact.

## PASS, refusal and rollback

Structural PASS requires every precontrol, the single migration transaction and
every postcontrol above to pass, with exact historical-baseline equality and zero
V41 rows. If the migration transaction fails, PostgreSQL rollback is the only
rollback mechanism used. If a postcontrol refuses after commit, preserve the
deployed state and all outputs, perform no repair or reapplication, and return to
the Founder with `APPLIED / POSTCONTROL DISCREPANCY UNRESOLVED`.

## What this deployment will not prove

It will not prove Generic Producer admission, authenticated ownership, producer
or provider authenticity, a live request/response binding, atomic execution with
application rows, reread/UI/exports, global egress closure, External Provider,
Real-data Admission, Financial Reliability, production security or B1 closure.
The pre-existing Global Egress OPEN/FAIL result is unchanged.

Final governed state after a structural PASS:

`B1 OPEN · Generic Producer UNADMITTED · Global Egress OPEN/FAIL · External Provider CLOSED · Real-data Admission CLOSED`
