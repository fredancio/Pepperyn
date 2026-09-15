# Architecture model

## Layers

1. **Product shell:** authentication, entities, portfolio, chat, history,
   settings, administration and exports.
2. **Financial/domain core:** parsing, normalization, evidence, time, doctrine,
   epistemic state, analysis, decisions and continuity.
3. **Trust platform:** ownership authority, persistence, pseudonymous
   correspondence, D10 projection, provider policy/egress, response quarantine
   and authorized rehydration.
4. **Infrastructure:** GitHub, Supabase, frontend/backend runtime, deployment,
   DNS, secrets, backup and observability.

## Ownership hierarchy

User/tenant, company/entity, engagement and analysis/request identifiers are
security boundaries, not presentation metadata. Capabilities must bind the
smallest exact scope required and fail closed on mismatch, replay, expiry or
foreign ownership.

## Provider boundary

`governed source -> ownership capability -> V34-attested correspondence -> task-specific minimal projection -> sealed receipt -> egress policy -> untrusted response -> quarantine/validation -> rehydration capability -> terminal output`

`REIDENTIFIED` is a terminal type. It is ineligible for provider projection and
egress. The currently proven projection policy is bounded and cannot be treated
as a universal disclosure policy.

## Persistence doctrine

- authoritative records are durable and ownership-bound;
- decision/intention/follow-up/execution concepts remain separate;
- append-only evidence is preferred for governed history;
- an Integration Test database is not production;
- in-memory caches are not durable authority;
- migration presence is not evidence that production has applied it.

## Contestable implementation

Frameworks, internal module layout, libraries, provider/model choice and agent
topology may change if the same or stronger capability is demonstrated under
the No Silent Regression contract.
