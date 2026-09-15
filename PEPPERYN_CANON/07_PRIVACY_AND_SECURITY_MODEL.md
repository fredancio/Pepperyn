# Privacy and security model

## Governing principle

Default disclosure to an external model is `DENY / MINIMIZE`, not `SEND`.
Provider compliance controls are defense-in-depth and never replace Pepperyn's
deterministic privacy boundary.

## Implemented bounded chain

1. Ownership-controlled governed source.
2. V34 authority for initial V33 registration.
3. Encrypted, versioned V33 correspondence scoped to the authorized continuity
   boundary.
4. Exact V33 state used by a task-specific D10 projector.
5. Projection receipt binding scope, policy, provenance and payload.
6. Provider policy and central egress authority.
7. Untrusted provider response quarantine.
8. Exact response/projection/request validation.
9. Expiring ownership-bound local rehydration capability.
10. Terminal-only `REIDENTIFIED` output rejected by projection and egress.

## Evidence-calibrated status

- V33 durability/restart/multi-process: `LIVE_PROVEN_SYNTHETIC`.
- V34 authorized origin: `LIVE_PROVEN_SYNTHETIC`.
- `FINANCIAL_CHANGE_MINIMAL_V1`: `LIVE_PROVEN_BOUNDED_SYNTHETIC`.
- Provider response and rehydration: `TESTED_WITH_MOCK_PROVIDER`.
- Re-egress prohibition: `TESTED_BOUNDED_PATHS`.
- D10 globally: `REDUCED_NOT_ANONYMOUS / OPEN BY TASK`.
- Production key custody: `OPEN`.
- PG-3/PG-4: `OPEN`.
- External Provider: `CLOSED`.
- Real-data Admission: `CLOSED`.

## Lifecycle

Correspondence retention/purge must remain explicit and configurable. No legal
retention period is invented here. A mapping persists only while legitimate
evidence, temporal continuity, decisions/actions or legal/product retention
requires it. Cross-client correlation is denied by default.

## Production prerequisites

Production requires separate secrets, managed encryption-key custody, rotation
and recovery design, complete task-policy coverage, production RLS/privilege
proof, logging-leakage review, provider account evidence and adversarial tenant
isolation.
