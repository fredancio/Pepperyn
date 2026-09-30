# B1 — V41 injected rehearsal successor local proof

**Status:** LOCAL PASS / NOT CHECKPOINTED / NOT REMOTELY EXECUTED
**Evidence date:** 2026-09-30

## Attempt 1 preserved outcome

The first PPR-069 rehearsal is a bounded failed attempt, not execution proof.
Its runner authenticated once at approximately `22:37:06Z`, then waited 1,200
seconds for the owner policy insert and refused at `22:57:06Z`.  The exact SQL
was subsequently committed at `23:05:18Z`, after the process had stopped, so it
could not observe or disable the row.

Read-only diagnosis found exactly one V41 row: policy
`5cf919e2-77e3-46ce-ab0e-c237d62cfe2d`, active, with the authorized local-only
contract.  There were no V41 admissions or receipts and no corresponding
analysis or envelope.  The separately authorized safety artifact then changed
only `enabled=true` to `enabled=false`.  Read-only postcontrol returned
`V41_INJECTED_POLICY_SAFETY_DISABLE_POSTCONTROL_PASS` with one disabled policy
and every dependent count at zero.

The attempt directory is preserved.  A source snapshot records the five local
orchestration artifacts and their SHA-256 values.  The failed policy is never
reusable or reactivateable.

## Exact cause

The owner SQL had no database-enforced validity deadline.  The runner's local
20-minute observation deadline and the SQL's validity boundary were therefore
not the same boundary.  Authentication also occurred before the human handoff,
unnecessarily coupling the delay to the single in-memory session.

## Minimal successor correction

No admission semantic, authority or ceiling changed.  The successor:

- requires the failed policy as the sole, disabled and evidence-matching V41
  historical policy;
- freezes four new identities and never reuses attempt-1 identities;
- embeds the same frozen owner-action deadline in the manifest and SQL;
- makes PostgreSQL reject a late insert transactionally;
- observes and revalidates the exact successor policy before the one Auth login;
- retains ten effect-capable requests and five new durable rows;
- preserves the original falsifications, completion, recovery, UI/exports and
  irreversible disable requirements.

## Local evidence

- focused successor launcher: `7 PASS`;
- governed admission/reread/output regression: `110 PASS`;
- isolated PostgreSQL successor test: `1 PASS`;
- frontend provenance: `7 PASS`, live fixture test `1 SKIPPED` because no live
  successor result exists;
- successor wrapper executed from `C:\Users\ADMIN-FRED`: local integrity PASS,
  no credential read, network, Auth or remote write;
- first broader regression invocation from the repository root was invalid
  because tests resolve fixtures relative to `backend`; the corrected identical
  selection from the required `backend` working directory produced `110 PASS`.

## Limits and next boundary

The first prepared successor directory, `v41-injected-2`, expired without SQL,
Auth or remote access and remains unchanged as local non-execution evidence.
The second successor is prepared for `v41-injected-3` with new identities and
an exact 24-hour deadline shared by its manifest, runner and PostgreSQL guard.
This timing-only revision must be checkpointed before its local preparation or
any remote precontrol. Any eventual GO remains bounded to the existing PPR-069
claim; B1 remains OPEN, the producer remains UNADMITTED, and External Provider
and Real-data Admission remain CLOSED.
