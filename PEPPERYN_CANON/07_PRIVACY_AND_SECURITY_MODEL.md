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

## Founder ruling — Privacy & AI Contract, 2026-09-28

Authority: Founder decision "Decision — Audit Privacy & AI Contract" in this
Work, following the supplied Privacy & AI Contract V1 (attachment
76e73524-9c12-4584-a10f-7087211f6caa/Texte collé.txt). This is an architectural
constraint, not new functionality
or evidence of legal compliance. See DEC-032 in the Decision Register.

The existing architecture is compatible; no major privacy refactor is required.
Continue B1 and the current roadmap. Do not interpret this contract as a new
cross-cutting Privacy/GDPR programme. Treat only the next gap that prevents the
next gate, at the point that gate is needed. Compatibility does not close any
admission condition or broaden existing bounded evidence.

Provider admission must be positive and task-bound:

`TASK -> ALLOWED DATA CLASSES -> NECESSITY -> GOVERNED SOURCE -> PRIVACY
TRANSFORMATION -> PROJECTION -> EGRESS POLICY -> PROVIDER`.

Never substitute "all available data minus obvious sensitive fields". Data is
not admissible because it is available, parsed, truncated or historically
anonymized; the task must authorize its category, provenance and transformation.
Pepperyn retains durable state and decision authority; the provider remains a
replaceable reasoning component. This preserves, rather than replaces, the V33/
V34, D10, quarantine, authorized rehydration and terminal-only boundaries above.

Blockers before the affected use, not automatic immediate implementation:

1. Governed privacy projection for each Beta task sent to an external provider.
2. Distinct versioned execution/provenance contract for the next real producer;
   never falsely label it as the registered mock or silently widen V39.
3. Effective tenant/entity/engagement/resource isolation for the relevant context.
4. Never claim complete deletion when partial errors exist. The audit found this
   exact risk in legacy delete_account; correction remains gate-timed, not done.
5. Secrets, logs, backup/restore and retention sufficiently established for real
   Beta use; no invented retention period or local-DPAPI-to-Beta equivalence.
6. Effective provider configuration evidence, not documentation-only inference.

Non-objectives unless a specific product requirement or gate makes them necessary:
general DLP, sophisticated Privacy Gateway, RAG, multi-provider engine, fully
automated GDPR deletion, complete Confidence Ledger, cross-company learning or
an additional governance platform. Preserve inherited/deferred knowledge; do not
silently reject it or make it a V1 delivery condition.

External Provider and Real-data Admission remain CLOSED until their own gates
are satisfied. No deployment, data mutation, transport activation, automatic
correction or legal-compliance claim is authorized by this ruling.
