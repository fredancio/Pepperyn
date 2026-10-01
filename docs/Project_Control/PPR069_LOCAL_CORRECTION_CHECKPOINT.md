# PPR-069 local correction checkpoint scope

Date: 2026-10-01. Base: 62834f948a093eff7f7859928abad9a1b61af219.
Scope: RecordingDb.auth forwarding plus attempt-5 diagnostic/procedural evidence.
This document describes the validated scope, not a claim of completed commit/push.

## Required bounded regression corpus

167 PASS, zero skipped/deselected, three dependency deprecation warnings:

- test_v41_recording_db_composition.py
- test_v41_attempt5_terminal_ack.py
- test_governed_producer_admission.py
- test_durable_generic_producer_admission.py
- test_v41_owner_handoff.py
- test_v41_owner_ack_successor.py
- test_v41_conservative_freshness.py
- test_v41_injected_rehearsal_launcher.py

All required tests of this Python adapter/handoff correction executed. Local
generation tests allocate only pytest fixtures, not an Attempt 6 or remote identity.
No PostgreSQL test is silently skipped or labelled PASS: PostgreSQL is outside
this bounded rerun because no SQL/schema/transaction behavior changed. Prior
isolated PostgreSQL evidence remains prior evidence, not rerun. Docker inspection
was denied by the local named-pipe permission; no engine/config change attempted.

## Invariants and preserved artifacts

The minimal code delta delegates auth to the existing backend client. No fallback
Auth, fabricated principal, login/refresh or source of producer authority exists.
See PPR069_ATTEMPT5_COMPOSITION_DIAGNOSIS.md for I1-I18 mapping and before/after.
Bindings, 10-effect/5-row/1-Auth ceilings, fail-closed and anti-replay are unchanged.
Attempt 5 remains NO PASS. Runner policy_disabled=false and later independently
observed enabled=false are distinct preserved facts. Existing history policy was
disabled and conformant in the checked fields; no new remote observation occurs.

The procedural correction pre-verifies safety-disable transfer and ack command
before a future run, without granting such a run or extending any deadline.
No SQL, manifest, old launcher/publisher pin, protocol or runtime evidence is
rewritten. Historical scripts intentionally refuse the corrected runner hash.
Attempts 1-5 inventories/hashes are checked before/after any local commit.
Seven pre-existing exclusions, including frontend/next-env.d.ts, remain bytewise
preserved. The old SUBMISSION_UNRESOLVED and network UNESTABLISHED remain unchanged.

## Git boundary

Local HEAD and tracking were both 62834f948a093eff7f7859928abad9a1b61af219 before
preparation. A real remote HEAD check would require network access and is not
performed under this local-only instruction. No fetch, ls-remote, push or remote
application operation is included. A local commit will intentionally be ahead
of tracking; remote synchronization must not be reported as PASS.

Checkpoint targets exactly eight files: this report, the two attempt-5 reports,
the two new test modules, the runner, Current Reality and Execution Evidence.
Exact raw SHA-256 values and status/exclusion/history inventories are frozen in
the accompanying local checkpoint manifest; only affected files are new commit
targets. Existing evidence hashes are preservation checks, not replacements.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No Attempt 6 or distant GO prepared.
