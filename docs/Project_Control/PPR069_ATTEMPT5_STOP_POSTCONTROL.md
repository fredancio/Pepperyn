# PPR-069 attempt 5 - terminal handoff diagnostic

Status: FAIL-CLOSED / NO REHEARSAL PASS. Date: 2026-10-01.
Execution checkpoint: 62834f948a093eff7f7859928abad9a1b61af219.
This report adds evidence; it does not replace runtime artifacts or their verdicts.

## Separate observations

- Policy: f6b1732f-e558-47a0-9106-f0b3e53c3b05.
- Request: 7a32da83-eded-48ff-bba1-7f2239381bcd.
- Execution: f820bc9a-f10b-405a-af2c-4246c199390e.
- Analysis: 9a2fb8cf-1e0a-4ce6-b3f6-1d865072efcd.

The accepted precontrol at 2026-10-01T16:24:06.832274Z matched the six
historical counts/digests, catalog count/digest and structural baseline.
The Founder executed insertion once and published insert Owner Ack once.
effects.json records POLICY_INSERT / OBSERVED_EXACT_EFFECT and AUTH_LOGIN /
ACKNOWLEDGED, auth_logins=1. These two entries are not a complete remote-effects
inventory: the later manual disable was not acknowledged by the runner.

refused.json preserves stage=COMPOSITION, error_type=AdmissionRefused,
policy_observed=true, policy_disabled=false, automatic_retry_permitted=false,
observation_limit=NOT_PROOF_OF_REMOTE_ABSENCE. The original composition exception
message/traceback is not retained. Its exact underlying condition is NOT yet
established; OWNER_HANDOFF_TERMINATED is a subsequent publisher error, not that
initial failure. No successful execution, admission or financial proof follows.

The Founder reports one successful policy-disable.sql execution, followed by
the publisher refusing OWNER_HANDOFF_TERMINATED / LOCAL_OPERATION_REFUSED_NO_RETRY.
The supplied Supabase screenshot shows Success. No rows returned / 0 rows;
that is a statement result, not an assertion that no row was updated.

A separately authorized SELECT-only postcontrol, already obtained at
2026-10-01T18:28:08.390968Z on Pepperyn Integration Test, returned:

- Attempt policy present, enabled=false.
- Zero matching admissions, analyses, envelopes, V39/V40/V41 receipts.
- Total V41 policies=2, admissions=0, receipts=0.
- Historical policy 5cf919e2-77e3-46ce-ab0e-c237d62cfe2d present, enabled=false,
  contract binding CDC4BC07EA6F67275B985E76B24467CC3A1A11891EFA1953E0F6137344F73645
  and evidence A225EF5B20CF9FF143D9C7C5EF2713458839478163571040233A69747E0F8798
  conformant to the expected values.

The checked historical fields show no alteration. This is not a new full-table
or all-column non-regression proof. The result was recovered from the complete
SQL-editor cell in the prior read-only turn; no new remote query was made for
this local diagnostic. SQL editor query reference:
d9f374de-59d3-4f57-98a9-e62dd07fd121 (project ejixkplrgobgwqnhidwt).

Thus one new policy remains durably preserved and disabled; no application trio
exists. Runner policy_disabled=false means no successful confirmation before
termination. Independently observed enabled=false is a separate later fact.
Neither is overwritten or retroactively promoted to a rehearsal PASS.

## Exact publisher cause and timing limits

run_v41_owner_ack_successor.publish.check() first refuses when refused.json OR
result.json exists. This occurs before the expiry check and before opening the
pending acknowledgement. Attempt 5 has refused.json, no result.json, and neither
owner-disable-ack.pending nor owner-disable-ack.json. The reported exception
therefore identifies the refused.json terminal guard, not a remote SQL failure,
network call, hash mismatch or disabled-policy check. The publisher made no
remote observation and could not determine enabled from this error.

The disable started marker fixes deadline_utc=2026-10-01T18:24:43.023441Z.
The runner's wait_policy(enabled=False) creates this deadline as now+1200s;
local acknowledgement waiting checks now < deadline. Missing acknowledgement at
expiry raises and the safety handler then writes the terminal refusal. Local
filesystem LastWriteTimeUtc places the disable marker at 18:04:43 and refused.json
at 18:24:43. There is no disable ack. This corroborates the expiry sequence.
Filesystem times are supporting evidence, not server execution timestamps.
The inner safety exception was swallowed by the existing handler: its exact
exception message was not recorded, so it is not represented as a recovered log.
The precise SQL execution instant and publisher invocation instant are not
independently attested by these local files. Founder establishes their ordering.

## Minimal correction - no guard weakening

BEFORE: terminal-state and deadline controls correctly reject late acknowledgement;
however transfer verification and its representation decision were performed
during the already running 20-minute safety window.

CHANGE: preparation/order correction, not a publisher bypass. Before any future
authorized run, prepare and verify both owner SQL transfers, the separate disable
ack command and its pins, and resolve any transfer-specific representation issue.
During a handoff, check live waiting state and deadline, execute the exact SQL
once, and publish the corresponding ack immediately after unambiguous success.
Do not interpose another chat round trip between successful SQL and its ack.
The recipient must have the commands and refusal instructions before the clock
starts. If this cannot be arranged, do not start a future run.

AFTER: same identity/SQL binding, one-shot action, single independent observation,
20-minute disable deadline, no late ack acceptance, no extension/reset/retry,
no Auth/egress authority from acknowledgement. Unknown remote state still needs
separately authorized read-only evidence; never retry SQL to discover its effect.

No runtime source, pinned launcher/publisher, frozen protocol, historical hash,
SQL or attempt identity has been modified. Accepting an ack after refused.json,
removing that file, or extending this attempt would defeat the correct guard.
This correction removes avoidable preparation delay, not all possible human or
network latency. It is not live validation of a future intervention.

## Local falsification actually executed

backend/tests/test_v41_attempt5_terminal_ack.py adds seven cases using copied
existing identities in pytest temporary folders, without allocating a successor:

1. refused.json blocks disable before publication; files unchanged.
2. result.json does likewise.
3. Exact deadline refuses even without a terminal file; no pending/final ack.
4. Prepared immediate ack permits one validated observation; duplicate/replay denied.
5. Missing ack expires with zero observations.
6. Terminal state appearing during publication preserves pending evidence, no final ack.
7. Ack plus remotely still-enabled policy cannot produce a disable PASS.

Execution with existing owner-handoff regressions: 35 PASS, zero skipped, three
dependency warnings. Initial invocation failed all seven setups because pytest's
default external temporary directory was inaccessible; no assertions ran there.
Rerun used a fresh writable local basetemp, with no deletion or permission change.
No PostgreSQL tests or prior 84-test claim were requalified as rerun.

## Remaining boundary

The original COMPOSITION AdmissionRefused remains separately unresolved and is
a blocker before proposing another rehearsal. This report neither fixes nor
attributes it to the acknowledgement deadline. No successor prepared, no new
identity allocated, no remote GO requested, no credentials read, no Auth, no
network access or remote mutation in this diagnostic/test slice.

Attempt 4 SUBMISSION_UNRESOLVED and UNESTABLISHED network cause remain unchanged.
B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. Attempt 5 remains terminal and must not be reused.
