# Pepperyn Self-Selling Control Center — Strategic Capability

**Nature:** future strategic capability, internal and admin-only
**Surface:** Pepperyn Control Center
**Status:** DEFERRED — no implementation authorized
**Roadmap authority:** `docs/Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md` §4.5

## 1. Strategic intent

Pepperyn may progressively learn how Pepperyn should be sold. The target is
not a generic CRM and not a prospecting bot. It is a governed commercial
learning system that relates evidence, decisions, actions, outcomes and
learning so that Founder attention moves toward profitable revenue and away
from low-value manual coordination.

This capability is compatible with the longer-term **Growth Brain / Economic
Agency** direction, but does not modify Pepperyn's current CFO Profession Model
or its V1 roadmap. Selling Pepperyn is an internal platform responsibility,
not an invariant of the Fractional CFO profession. The compatibility lies in
the shared discipline: evidence precedes claims and recommendations; meaningful
decisions remain explicit; outcomes correct memory; attention is allocated by
expected value, cost and risk rather than activity volume.

## 2. Intended capability boundary

The future Founder / Admin Commercial Control Center may:

- observe and structure commercial activity;
- follow prospects, organizations, interactions, objections, trials,
  conversions and retention;
- learn which ICPs, narratives, channels and sequences work in observed
  conditions;
- recommend a Next Best Commercial Action with its evidence, expected value,
  cost, risk and uncertainty;
- preserve durable commercial memory across Evidence, Decision, Outcome and
  Learning;
- progressively reduce Founder manual work;
- prepare or execute only bounded actions that the authorized autonomy level
  explicitly permits.

The conceptual architecture to preserve for later arbitration is:

- Sales Brain;
- Prospect Brain;
- Narrative Brain;
- Conversion Brain;
- Commercial Memory;
- Commercial State Machine;
- Next Best Action Engine;
- Growth Evidence Ledger;
- Growth Decision Memory.

These names describe responsibilities, not authorized services, agents,
tables, APIs or deployment units. No implementation topology is fixed here.

## 3. Founder interface direction

The admin cockpit should eventually compress, rather than multiply, Founder
attention. It may summarize:

- overall commercial state;
- active conversations;
- prospects or customers needing intervention;
- strongest conversion opportunities;
- strong and weak narratives;
- experiments in progress;
- decisions awaiting Founder approval;
- actions Pepperyn may observe, analyze, recommend, prepare or execute under
  the active autonomy policy.

The cockpit is a projection of governed commercial state. It must not become a
second source of truth or calculate unsupported conclusions in the interface.

## 4. Progressive autonomy ladder

| Level | Authorized capability in principle | Promotion evidence required |
|---|---|---|
| G0 / V0 | Observe and record | Admin boundary, lawful data capture, provenance and retention defined |
| G1 | Analyze | Reproducible analysis against recorded evidence; uncertainty visible |
| G2 | Recommend | Measured recommendation quality; claims and expected value traceable |
| G3 | Prepare actions | Explicit human approval before dispatch; complete preview and audit trail |
| G4 | Execute bounded actions under rules | Validated sales motion, opt-out/frequency controls, rollback/stop controls and monitored outcomes |
| G5 | Substantial commercial autonomy | Separate Founder authorization supported by sustained empirical evidence; never presumed from lower levels |

Promotion is monotonic only in evidence, not in entitlement. Any material
failure, policy change or unsupported claim may demote or close an autonomy
level. No level authorizes Pepperyn to invent facts, impersonate a human, evade
consent, or execute outside its explicit policy.

## 5. Governance invariants

- No spam or circumvention of consent and opt-out.
- Mandatory contact-frequency limits and suppression handling before any
  outbound execution.
- No invented commercial claim, customer reference, result or capability.
- Claims are limited to evidence Pepperyn can actually substantiate.
- No automation of an unvalidated sales motion.
- Significant recommendations, approvals, actions and outcomes are traceable.
- Missing evidence remains unknown; correlation is not promoted to causation.
- Autonomy advances only from empirical results and explicit authorization.
- Optimization prioritizes margin, profitable revenue and Founder time saved,
  not messages, leads or activity volume in isolation.
- Prospect/customer data remains separated from client financial engagements
  unless an explicit future domain and privacy contract permits a relation.

## 6. Access and trust boundary

The surface is **admin-only** and distinct from ordinary client experience.
Authorization must be enforced by the backend from a secure role or deployment
configuration. An email, identity or privilege must never be hard-coded in the
frontend or treated as trustworthy merely because the interface hides a route.

Future external reads, messages, CRM writes or campaign actions require their
own provider, privacy, authorization, audit and rollback gates. The existence
of the Control Center does not authorize any connector or outbound action.

## 7. NOW / FUTURE classification

### A — REQUIRED NOW

- Preserve this strategic decision and its admin-only/security invariants in
  canonical documentation.
- Keep the current V1 roadmap and active critical path unchanged.
- Treat any current Control Center change as backend-authorized; never add a
  hard-coded frontend administrator identity.

No product code, schema, connector or UI is required now.

### B — CHEAP FUTURE-PROOFING

- Keep the Control Center structurally separate from client-facing navigation
  and authorization when nearby code is touched for an independently required
  change.
- Avoid naming new generic CRM records as canonical commercial truth before the
  future Commercial Memory model is arbitrated.
- Preserve provenance, append-only history and explicit human-approval seams in
  any independently created reusable platform primitive.

These are constraints on otherwise-authorized work, not standalone backlog
items and not permission to refactor current code.

### C — DEFER

- All nine conceptual components listed in §2.
- Prospect/organization/interaction/objection/trial/conversion/retention data
  model and ingestion.
- Founder cockpit widgets and commercial metrics.
- ICP, narrative, channel and sequence learning.
- Next Best Commercial Action scoring or ranking.
- Commercial experiments and attribution.
- CRM, email, calendar, enrichment, advertising or other connectors.
- Every autonomy level from G1 through G5 and any outbound execution.

### D — DO NOT BUILD

- A generic CRM clone or activity dashboard without a learning loop.
- A mass-prospecting or spam bot.
- Autonomous outreach based on an unvalidated sales motion.
- Fabricated claims, testimonials, customer results or false personalization.
- Black-box lead/opportunity scores presented without evidence and uncertainty.
- Vanity-volume optimization that ignores margin, risk and Founder time.
- A second commercial truth store competing with Commercial Memory.
- Frontend-only admin protection or a hard-coded Founder identity.
- Irreversible or materially consequential execution without the authorization
  required by the active autonomy level.

## 8. Reopening trigger

The capability remains deferred until all of the following are true:

1. the current V1 critical path is stabilized and its active gate is not
   displaced by this work;
2. real Founder commercial activity supplies enough lawful, structured
   evidence to define a smallest G0 learning loop;
3. the Founder explicitly opens a bounded increment;
4. admin authorization, privacy/retention, evidence ownership and separation
   from client financial data are reviewed before implementation;
5. the increment has one measurable outcome tied to profitable revenue,
   margin, conversion quality or Founder time saved.

The first eligible increment is G0 only: observe and record one narrow
commercial learning loop. No Brain, engine, connector or automation is implied
by that future opening.

## 9. Current decision

**PRESERVE THE VISION. DEFER THE BUILD. DO NOT MODIFY V1.**

No External Provider gate, real-data admission gate, commercial connector or
autonomy level is opened by this document.
