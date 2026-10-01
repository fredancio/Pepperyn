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

## Single-result precontrol correction — local evidence

Attempt 3 exposed only the last frozen-scope PASS in Supabase SQL Editor.
Local inspection established that the inherited structural block required
zero policies while the successor scope correctly required one disabled
historical policy. Neither missing result is inferred to be PASS.

The generator now composes all three queries into one repeatable-read,
read-only transaction and one JSON result. It adapts only the successor count
to one, retaining exact historical-policy identity/evidence checks, all five
function checks, table protections and the historical snapshot output. The
original deployment SQL and runtime attempt artifacts remain unchanged.

Executed validation: 9 tests PASS, zero skipped, including two actual isolated
PostgreSQL tests. The full generated SQL accepts the expected disabled history
and refuses missing/active/extra policies, evidence/binding mismatches, scope
drift, search_path drift and authenticated-role SELECT access. The read leaves
the historical policy unchanged and dependent/application tables empty. The
existing expired-insert and valid-insert PostgreSQL test also passes.

An initial validation invocation had 4 PASS / 4 setup errors from an inaccessible
default pytest temporary directory. The complete invocation with a dedicated
new local temporary directory produced the 9 PASS above. No remote query,
authentication or write occurred. Historical baseline comparison remains a
required separate evaluation of the returned hashes. The broader historical
110-test evidence is not claimed as rerun for this correction.
