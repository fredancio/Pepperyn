# PPR-069 Owner Ack successor: local preparation evidence

Status: LOCAL PASS / NOT REMOTELY EXECUTED / CHECKPOINT PENDING.
Preparation baseline: ff14a3237152388c6b32989f29f5fd80f39874e9.
Date: 2026-10-01. Target: Pepperyn Integration Test only.

## Frozen distinct attempt

Directory: Pepperyn-runtime/v41-injected-5. Created once locally.
Created: 2026-10-01T16:02:17.336525+00:00.
Deadline: 2026-10-02T16:02:17.336525+00:00 (18:02:17.336525 Brussels).
No expiry extension or reset is authorized. All four identities differ from
attempts 1-4; those attempts remain preserved under the 32-file history inventory.

- policy: f6b1732f-e558-47a0-9106-f0b3e53c3b05
- request: 7a32da83-eded-48ff-bba1-7f2239381bcd
- execution: f820bc9a-f10b-405a-af2c-4246c199390e
- analysis: 9a2fb8cf-1e0a-4ce6-b3f6-1d865072efcd

SHA-256 file hashes:

| Artifact | SHA-256 |
| --- | --- |
| manifest.json | 31AAAC4D01DD11209A3F15B412B89D6BC785943A96025A23E667E5825761E7B6 |
| precontrol.sql | 0A24E82D836D30C0763822FD23500A5A50CDAD7C781953EA4C0C439B687B95B7 |
| policy-insert.sql | 30FB057EDC265C0846543EB198A6F7BE45F9F67581893A8816BD75E21C2FB86D |
| policy-disable.sql | 87CF8ECCC4F2FC17061EC9CBF31F0299ADD8762039E1875F4918E85EE0B55D0A |
| PPR069_OWNER_ACK_SUCCESSOR_PROTOCOL.md | CD8167C8BE8AB4D4C283B580350F34AB8923D59DD3A150C2E8F94BA70B3332F1 |
| rehearse-v41-owner-ack-successor.ps1 | EA7256776B36E9433ACD3E1C2F4C6AD7D062B8534464DA2FD25E7B68807D2114 |
| publish-v41-owner-ack.ps1 | 17C37E6B83C021B0B14F523C6BA8E78DB83AB466B9D36ACB56A478DB15EDE3E7 |

The internal canonical manifest digest is distinct from the file-byte hash:
8C7590CE25CF38885B3BC5A0F87DF010A00AF0F5927A18FAEFECF0AF2A432A16.

## Composition and local validation

The new entrypoint configures only orchestration paths/readers on the existing
runner, including its independent recovery entrypoint, so future recovery writes
the UI proof into the new directory, not attempt 4. The factory accepts explicit
protocol/baseline parameters with unchanged historical defaults. No migration,
producer contract, V39/V40/V41 semantics or SQL functions changed.

The publisher verifies frozen artifacts, exact marker/deadline/action and complete
fresh attestation, requires explicit Founder action confirmation, exclusively
writes pending JSON, fsyncs, rechecks and publishes by Windows rename with no
overwrite. Local acknowledgement is only an assertion of action. The runner's
single remote observation and subsequent baseline checks remain necessary before
Auth; no provider or egress authority is delegated to the publisher.

The generated precontrol adds a PostgreSQL statement timestamp to the one JSON.
The local attestor compares full structural/history/identity evidence and binds
the complete recovered result to the manifest/SQL hashes. No accepted result or
live attestation has yet been created for this successor. Unknown, incomplete,
future, expired or substituted evidence refuses. No attempt-4 temporal fallback.

Actually executed:

- Full local selection: 84 PASS, zero skipped/deselected, 3 dependency warnings;
  repeated through the new wrapper's non-execution mode: 84 PASS in 4.23s.
- The TWO previously NOT EXECUTED generation tests were additionally run as a
  separate selection: 2 PASS, 6 unrelated tests deselected, 2.00s. Their historical
  status in previous proofs is not rewritten; this is new execution evidence.
- PostgreSQL isolated: 2 PASS, zero skipped, 25.11s. New timestamped precontrol
  exercised the existing full adversarial matrix; owner SQL deadline/history
  acceptance/refusal also passed. Container pepperyn-b1-policy-test verified
  network=none, no ports, no host mounts; then started and stopped, not deleted.
- Publisher LocalCheckOnly PASS; PowerShell parsing PASS. No credentials read.
- Publisher-to-runner local composition: no network while awaiting local action,
  then exactly one fake policy observation. Tests also cover substitution,
  missing marker, pending/replay, terminal state, expiry, malformed/incomplete
  evidence, failed atomic rename, disabled safety handoff and historical refusal.

Initial Docker inspection was denied by the sandbox; a separately approved local
Docker invocation resolved access. This was not a remote or product failure.
No attempt to reproduce the unknown real RemoteProtocolError is claimed.
No full product/UI/export or financial reliability suite was rerun in this slice.

## Preservation and next authorization

Attempts 1-4 and old wrapper remain unchanged. SUBMISSION_UNRESOLVED and the
UNESTABLISHED transport cause remain unchanged. Attempt 4 remains terminal,
zero partial remote state in the checked scope, no rehearsal PASS.

Before remote use, checkpoint the exact prepared code/protocol/hash evidence and
confirm synchronization. The minimal first distant GO should authorize only one
execution of this new precontrol.sql on Integration Test, JSON recovery and
historical comparison, no Auth or write. Only after that proof, present the
distinct one-shot rehearsal GO with the exact identities/hashes above, ten
effect-capable requests, five durable rows, one Auth and exact safety-disable
scope. No prior GO is silently transferred to this successor.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No live PASS or remote readiness inferred.
