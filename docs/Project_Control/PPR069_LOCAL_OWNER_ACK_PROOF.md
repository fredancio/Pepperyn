# PPR-069 local owner acknowledgement

Status: BOUNDED LOCAL PASS / NOT CHECKPOINTED / NOT REMOTELY EXECUTABLE.
Date: 2026-10-01. No successor identities or attempt directory allocated.

## Change and authority

OwnerPolicyHandoff replaces remote polling inside wait_policy with local-file
waiting. An acknowledgement must match exactly its schema, action, frozen
manifest digest, policy identity and SQL digest. It is a scheduling signal,
not proof of insertion/disablement and not permission for authentication.
The existing piped secret packet is untouched; no interactive stdin secret
channel is reused for acknowledgement.

Before waiting, an exclusive local started marker consumes that handoff. Any
failure, missing/invalid acknowledgement, expiry or read error is terminal.
A second call refuses before reading remotely. The runner additionally refuses
previously started/terminated attempts before constructing a remote client.
Attempt 4 remains retired; its evidence and identities are not modified.

Local manifest/SQL integrity and time are checked before, during and after the
human wait, and after the single observation. Insertion also retains the
existing precontrol freshness validator. Disablement retains its bounded
1,200-second safety window rather than inheriting an expired insertion window.
The deadline cannot be renewed within the same consumed handoff.

After a valid acknowledgement, exactly one SELECT of the V41 policy registry
observes both the expected historical and target policy. The target enabled
state, complete bounded specification, exact scope and contract are validated
before Auth. Missing/foreign/extra policies refuse. The later postpolicy check
reuses this observation rather than issuing a second policy SELECT; the existing
separate admission/receipt/history read checks remain mandatory. Thus "single
read" means one policy observation per handoff, not elimination of other safety
reads in the protocol. Database admission checks remain authoritative at reserve.

Insertion, normal disablement and safety-disable observation use the same local
handoff. No network client is invoked while waiting for the human. Remote errors
still propagate without retry or fallback. Failure output explicitly states
NOT_PROOF_OF_REMOTE_ABSENCE. Unknown post-insert state still needs the governed
safety procedure; no automatic corrective write is added.

The former polling dependency is removed without weakening remote evidence:
an acknowledgement alone cannot pass; an actual successful remote observation
and all existing checks are still required. This does not fix or diagnose the
underlying attempt-4 transport fault. A single read can still fail closed.

## Executed local validation

Final selection: 57 PASS, 2 deselected, 3 dependency warnings, 2.37 seconds.
Modules: test_v41_owner_handoff.py, test_v41_conservative_freshness.py and
test_v41_injected_rehearsal_launcher.py. The two manifest-generation tests were
deliberately deselected to avoid allocating new identities; they are NOT
requalified as PASS. Existing fixed IDs were used only in isolated temporary
test copies. No prepare/execute command or live credentials were used.

Coverage includes local waiting with zero remote reads, exactly one observation,
positive insert/disable, missing policy, wrong identity/scope/contract, open
egress claim, disabled policy, altered historical policy, additional policy,
acknowledgement substitution/missing/invalid JSON, expiry during wait/read,
freshness refusal, SQL mutation, same-process replay and persistent marker replay.
A synthetic RemoteProtocolError propagates unchanged after one call, not as an
empty result. Orchestrator rejection tests demonstrate zero Auth, empty effects
and no result artifact. The retired-attempt guard preserves an existing refusal.
Existing selected tests retain ten-effect and single-Auth budget checks and the
conservative strict-24-hour boundary. No SQL/schema changed; PostgreSQL and full
product/UI/export suites were not rerun or requalified in this tranche.

## Protocol consequences and remaining work

The historical checkpointed protocol, SQL artifacts and Windows wrapper pins
remain unchanged. The wrapper consequently rejects the modified runner. There
is intentionally no ready successor, new deadline, live acknowledgement file or
new execution permission.

A future separately approved preparation must specify the acknowledgement file
handoff (write a complete file atomically, never amend it), its exact schema and
local publication procedure, checkpoint the runner/dependencies and amend the
owner-action instructions. Owner SQL remains one-shot and deadline guarded.
The human must not insert after the local waiter has stopped; an uncertain
SQL outcome must not be retried. No automatic retry may be added to read or Auth.
Before any future distant action, the applicable Founder GO must name the new
frozen artifacts and retain the ten-effect/five-row/one-Auth ceilings. This local
PASS alone neither prepares nor authorizes that action.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No provider attestation or rehearsal PASS.
