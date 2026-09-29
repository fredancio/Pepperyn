# B1 — Bounded producer admission semantics — local proof

**Status:** LOCAL PASS / NOT CHECKPOINTED / REHEARSAL NOT EXECUTED
**Evidence date:** 2026-09-29
**Evidence ID:** PPR-069

## Decision implemented

DEC-035 separates immutable candidate identity, bounded policy authorization,
single execution admission, external egress and provider attestation. The
PPR-065 profile remains historically `UNADMITTED`; its exact SHA-256 remains
`2C371E0BA997BA7D8496C8F5AB2FC4BBB94D54ECADF897CB2AEAA3B966991F73`.
Neither V39, V40, V41 nor the durable whole-contract binding was modified.

One closed backend model now defines the only policy eligible for the injected
rehearsal. It binds DEC-035, exact tenant/entity/engagement, source, filename,
producer/task versions, profile and contract hashes. It requires
`LOCAL_TEST_ADMISSION`, `INJECTED_LOCAL_ONLY`, false provider attestation,
synthetic origin, closed egress, closed real-data admission and globally
`UNADMITTED` producer state.

Before reserve, the backend reads exactly one policy row and validates this
contract. The immutable database policy remains the authority for its precise
scope; the producer receives no policy-registration, identity, scope or
persistence authority. Reread validates the same policy but accepts its later
disabled state so historical evidence remains readable.

## Falsification

The targeted backend selection passes 90 tests. It refuses before reserve when
the decision, admission scope, candidate/global state, transport, attestation,
egress, scope or enabled state is substituted. It also preserves the existing
request/source/actor, producer-type, response-validation and uncertain-result
refusals. The exact historical profile hash is asserted and an attempted
`admission_state=ADMITTED` model is rejected.

The UI selection passes 7 tests and TypeScript compilation passes. A V41 local
receipt is shown only when it remains local-test, injected, non-attested and
globally unadmitted. The same qualification appears in XLSX/PDF/PPTX metadata.

The complete isolated PostgreSQL PPR-067/V41 selection passes 187 tests with no
skip or NOT EXECUTED case. It ran in a local PostgreSQL 16 container with network
mode none, no ports and no host bind. The container was stopped afterward. An
earlier run without the opt-in container failed during fixture setup and is not
requalified as product evidence.

## Limits

No Integration Test read or write occurred. No policy was registered, no Auth
session created, no producer globally admitted, no provider invoked and no real
data used. PPR-069 does not close B1 or either external gate. The live rehearsal
remains subject to a distinct Founder GO.
