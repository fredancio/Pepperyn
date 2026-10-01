# PPR-069 successor readiness after Attempt 5

Date: 2026-10-01. Local baseline: 4ba6b02bb1ec15fb4252c7b1ee2f8c4fe009bec3.
Synchronization accepted from Founder; no remote query made in this review.
Verdict: NOT READY TO FREEZE A SUCCESSOR. No new attempt allocated.

## Evidence and deterministic blocker

RecordingDb.auth forwarding and the pre-prepared SAFETY_DISABLE/ack procedure
remain accepted. The existing successor additionally assumes exactly ONE
historical V41 policy. The accepted Attempt 5 postcontrol established TWO:
5cf919e2-77e3-46ce-ab0e-c237d62cfe2d and
f6b1732f-e558-47a0-9106-f0b3e53c3b05, both disabled.
This review does not claim a fresh remote observation.

- v41_injected_rehearsal.policy_insert_sql: count must equal 1 before INSERT.
- v41_injected_rehearsal.precontrol_sql: frozen-scope count must equal 1.
- run_v41_injected_rehearsal.prepolicy_remote: exactly one historical policy.
- postpolicy_remote and validate_observed_owner_policies: exactly two policies
  after insertion, whereas a new successor would have three.
- run_v41_owner_ack_successor.validate_result compares the entire structural
  object with the Attempt 4 fixture, whose policy_rows is still 1.

Thus changing only IDs, source pins and deadline would deterministically refuse.
The refusal is legitimate for the old protocol; it is not a RecordingDb.auth
regression, not a remote schema defect and not an unknown network cause.

## Local falsification

test_v41_successor_history_readiness.py: four passing diagnostic tests show the
two-history prepolicy refusal before scope/Auth, three-policy observation refusal,
the two SQL singleton guards and the unchanged one-policy structural fixture.
Rows are minimal local fakes, not a claim of complete remote row contents.
Together with the eight existing correction/regression modules: 171 PASS,
zero skipped, three dependency deprecation warnings. No PostgreSQL execution in
this review; previous database evidence is neither rerun nor requalified.

## Minimum remaining preparation

A distinct successor must explicitly preserve BOTH historical policies and their
bindings, enabled=false, and absent historical application chains. Do not just
relax a count to >=2 or exclude the second policy from history checks.
Retain the six-table/catalog historical baseline unchanged. Version the successor
structural expectation separately to account only for the known extra disabled
policy; do not rewrite the original fixture or claim a new full-row baseline was
observed. The accepted postcontrol attests checked fields, not all-column hashes.
A future separately authorized read-only precontrol must establish any missing
full-row preservation evidence before any insertion/Auth. Compare subsequent
observations to that pinned result, not to an unvalidated current-state fallback.

Apply this same exact set through SQL guards, pre-Auth observation, post-insert,
disable observation and recovery. Test missing/extra/reactivated/substituted or
mutated history, as well as the unchanged one-shot scenario. Prepare both SQL
transfers and both ack commands before starting any clocked intervention.
Only then freeze new identities, hashes and a 24-hour deadline. This is a bounded
history/precondition adaptation, not a change to I1-I18 or producer authority.
No Astra trigger identified merely from this deterministic cardinality mismatch.

No successor manifest, expiry, SQL or execution launcher generated in this review.
No Auth, network, credentials, database operation, Git commit or push performed.
Attempt 5 remains NO PASS; runner policy_disabled=false and later observed
enabled=false remain separate. SUBMISSION_UNRESOLVED and UNESTABLISHED unchanged.
Ceilings remain 10 effects / 5 new rows / 1 Auth, no refresh/retry/cleanup.
B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No distant GO requested.
