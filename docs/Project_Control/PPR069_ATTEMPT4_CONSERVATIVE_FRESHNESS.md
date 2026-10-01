# Attempt 4 — explicitly qualified conservative freshness

Status: LOCAL PASS / NOT CHECKPOINTED / NO REMOTE OPERATION.
Authority: explicit Founder decision of 2026-10-01 accepting only the proven
lower bound 2026-10-01T07:24:01Z. This is a local attestation addendum, not a
modification of the frozen protocol, manifest, SQL or historical contracts.

The complete cell result supplied in Code demandé.txt was compared to the
checkpointed historical baseline: all six counts/row digests and the 59-item
catalog digest match. The accepted JSON is preserved as a local test fixture
(formatting only changed); no SQL was rerun to obtain it.
The original attempted UI submission remains SUBMISSION_UNRESOLVED.

## Representation and proof

The new attestation schema is v41-injected-successor-precontrol-attestation-2.
It has freshness_evidence instead of observed_at. Mixed schemas are refused.
Its kind is PROVEN_CONSERVATIVE_LOWER_BOUND; its qualification is
NOT_EXECUTION_OR_OBSERVATION_TIME. Authority and provenance are explicit:
FOUNDER_ATTEMPT4_CONSERVATIVE_BOUND_2026_10_01 and
FROZEN_IDENTITIES_PRESENT_IN_ACCEPTED_PRECONTROL_RESULT.
It pins the immutable attempt-4 manifest digest and the accepted result file
digest, checks the four identities, statuses and historical snapshot digest.
The v1 observed_at path keeps its original semantics; no historical report is
rewritten or upgraded. Unsupported versions refuse.

Let L = the approved lower bound, E = the unknown successful execution time,
and N = validation time. The qualified evidence establishes L <= E <= N.
Therefore 0 <= N-E <= N-L. Requiring N-L < 86400 seconds proves age < 24h
without claiming E or an observation timestamp. The validator additionally
requires manifest creation <= N < the original frozen owner deadline.

At 2026-10-02T07:24:01Z, validation refuses, although the original manifest
deadline is 0.869336 second later. This is conservative, never an extension.
The same check is repeated after the owner-policy wait and before Auth.
An expired post-wait check enters the existing safety-stop path, not a retry.

## Validation actually executed

31 PASS, zero skipped, 3 dependency deprecation warnings, 2.26 seconds:
test_v41_conservative_freshness.py and
test_v41_injected_rehearsal_launcher.py.
Cases include one microsecond before 24h, exactly 24h, beyond 24h, original
deadline, naive timestamp, time before identity creation, qualification and
provenance substitution, manifest/deadline mutation, missing evidence, altered
result, historical mismatch, mixed schemas and legacy/unknown versions.
An intermediate invocation from the repository root failed collection because
sandbox was not importable; rerunning from backend resolved that launch-context
error. It is not counted as a product PASS. PostgreSQL tests were not rerun in
this slice; no SQL or database function changed.

The wrapper pins the revised runner, new tests and accepted-result fixture and
includes both test modules in its local checks. No live precontrol-ready.json
has been created and no runner execute mode was invoked. A checkpoint and the
applicable execution authorization remain separate prerequisites.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No remote Auth, policy, admission or rehearsal.
