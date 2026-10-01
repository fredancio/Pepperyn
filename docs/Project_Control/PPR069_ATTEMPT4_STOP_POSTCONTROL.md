# PPR-069 attempt 4 - stopped before authentication

Status: STOPPED FAIL-CLOSED / NO PARTIAL REMOTE STATE IN CHECKED SCOPE / NO REHEARSAL PASS.
Date: 2026-10-01. Execution baseline: 736d670405bfaae0e6f441ca1abf76719018b05b.

## Evidence and qualification

The Founder reported no execution of policy-insert.sql. The runner stopped at
POLICY_INSERT with RemoteProtocolError, policy_observed=false,
policy_disabled=false and automatic_retry_permitted=false. effects.json records
auth_logins=0 and effects=[]. The source places Auth after successful policy
observation and post-policy checks. No technical authentication was reached.
Absence was not inferred from policy_observed=false.

A separately authorized postcontrol was executed once through the SQL editor
of Pepperyn Integration Test (ejixkplrgobgwqnhidwt), in a REPEATABLE READ READ ONLY
transaction followed by ROLLBACK. Complete result timestamp:
2026-10-01T14:47:10.764672+00:00; transaction_read_only=on.

- Attempt policy 7d25327c-a7e4-47d5-a072-0c47762ae869: 0 rows.
- Admission matching policy/execution/request/analysis identity: 0 rows.
- Analysis 4ee7a1cd-75ed-49d3-8956-10bf3aa6f1c4: 0 rows.
- Governed envelope for that analysis: 0 rows.
- V41 receipt matching execution/analysis: 0 rows.
- Total V41 policies: 1; admissions: 0; receipts: 0.
- Historical policy 5cf919e2-77e3-46ce-ab0e-c237d62cfe2d present and disabled.
- Its expected contract and evidence hashes match; recomputed contract-text
  digest and specification evidence digest validate; contract JSON matches text.

These checks establish no partial state for the frozen attempt, not a global
database non-regression proof or a successful rehearsal. Historical integrity
is established for the checked contract/specification and disabled-state fields,
not by a fresh byte-for-byte snapshot of every historical column.

Runtime evidence is preserved under Pepperyn-runtime/v41-injected-4:
refused.json, effects.json, baseline-before.json, the frozen artifacts and
stop-read-only-postcontrol-result.json. The latter's SHA-256 is
E628E0F5FF033AADAEE55072B69E8BE0E5E4BC44AD8AB86035CC9EEE85469DA7.
No attempt artifact was reset, replaced or cleaned up. The earlier precontrol
UI submission remains SUBMISSION_UNRESOLVED. The subsequently accepted complete
precontrol and conservative time-bound evidence do not resolve that uncertainty.

## Local cause analysis: established versus unknown

wait_policy performs a remote SELECT, then sleeps one second, repeatedly until
the frozen owner deadline. A transport exception is not caught there and
propagates to the outer fail-closed handler. During POLICY_INSERT, that wait is
the only operation after the displayed owner-action marker. Thus the error
arose on the policy observation path, before authentication or execution.

The precise transport cause is NOT ESTABLISHED. No exception message, traceback,
request correlation or response metadata was preserved in refused.json; the
wrapper also suppresses Python stderr. It is not possible to distinguish a
remote disconnect, intermediary/network failure or another protocol failure
from the exception class alone. The Supabase UI displayed a technical-issue
banner during the later postcontrol; this is context, not causal evidence.
No claim of timeout, SQL refusal or malformed policy is supported by this error.

The long human transfer/verification interval currently requires the polling
connection to keep succeeding. This is an evidenced orchestration exposure,
not proof of the underlying network fault. No local reproduction of the actual
remote failure is claimed, and no product tests were rerun for this doc-only slice.

## Smallest proposed continuation - not implemented or authorized for execution

Retire attempt 4 permanently; never use its insertion artifact or identities.
For a separately approved successor, replace network polling during the human
handoff with an explicit local acknowledgement, retaining one owner insert and
one bounded read to observe it. The acknowledgement grants no authority: fresh
deadline/freshness checks, exact persisted policy/scope/history validation and
the single Auth must still succeed in the original security order. A read error
still terminates the attempt without retry. A cancelled/expired handoff cannot
authorize a late insert. Any unknown post-insert state must be reported for a
separately bounded safety read/disable decision, never assumed absent.

Use a redacted diagnostic allowlist (stage, exception class/cause class and local
timestamp; no keys, tokens, headers or raw payloads) to avoid another opaque stop.
Do not add automatic transport retries or catch-and-continue behavior.

Before preparing new identities: locally falsify acknowledgement without policy,
foreign policy, expired handoff, remote-read failure before/after owner insert,
and duplicate acknowledgement. Require zero Auth before complete policy checks,
no replay, unchanged effect/row ceilings and preserved historical artifacts.
This is a proposal only: no new runner, identities, deadline or successor exists
as a result of this analysis. Any protocol amendment and new remote execution
must be presented separately for the applicable Founder authorization.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No provider execution, admission or B1 PASS inferred.
