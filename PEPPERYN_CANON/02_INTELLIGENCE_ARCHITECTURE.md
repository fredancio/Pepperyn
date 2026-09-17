# Intelligence architecture

## Durable intelligence

Pepperyn intelligence is the governed system around replaceable models:

`source -> normalization -> evidence -> deterministic facts -> professional doctrine -> business time -> governed inference -> verification -> epistemic state -> memory -> decision -> follow-up`

## Recovered cognitive concepts

| Concept | Canonical maturity | Authority/source |
|---|---|---|
| Evidence foundation and ownership | DECIDED / IMPLEMENTED | ADR-001, ADR-001A, migrations v18/v23 |
| Engagement continuity | DECIDED / IMPLEMENTED | ADR-002, migrations v19-v22 |
| FTE v0 | IMPLEMENTED / TESTED | `fte_minimal.py`, FTE minimal contract |
| FTE v3 architecture | SUPERSEDED AS EXECUTION AUTHORITY / historical proposal | ADR-003 v3 proposed plus later minimal contract |
| FRU foundation | DOCUMENTED / PARTIALLY IMPLEMENTED | FRU foundation and bounded V1 parser/contracts |
| Observation structure | IMPLEMENTED / TESTED | observation/formula services and contract |
| Knowledge model | IMPLEMENTED / TESTED | migration v24-v26 and service |
| Canonical financial doctrine v0 | IMPLEMENTED / TESTED | doctrine/vocabulary services |
| Epistemic dialogue v0 | IMPLEMENTED / TESTED | service and contract |
| Candidate model | IMPLEMENTED COMPONENT | `candidate.py` |
| Personnel-cost meaning classifier | IMPLEMENTED / TESTED | classifier and contract |
| Multi-agent/adversarial reasoning topology | CONCEPTUALIZED / PROPOSED | Cognitive architecture documents |
| Confidence Ledger / richer belief tiers | HISTORICALLY_REFERENCED / NOT FULLY RECOVERED AS IMPLEMENTATION | cognitive corpus |
| Enterprise Familiarization | DEFERRED | Profession Model and deferred register |
| Exception & Reconciliation | DEFERRED | deferred register |
| Generalized FRU | DEFERRED | product-control decisions |

## Non-negotiable boundaries

Reviewed professional reasoning PR-01..PR-08 is now ADOPTED_AS_REQUIREMENTS,
not a newly implemented reasoning engine. Its scope/semantics/comparability and
minimal-information-request constraints are defined in
`docs/Product/FinancialReliability/professional-reasoning-doctrine-v2.md`.
Existing canonical financial doctrine v0 retains its bounded implementation role;
this review neither expands its ontology nor reinstates superseded architecture.

- deterministic facts are not provider assertions;
- provider output is untrusted until governed validation;
- confidence does not convert an inference into a fact;
- contradictions and unknowns remain visible;
- doctrine promotion is governed, not model-autonomous;
- memory and decisions remain tenant/entity/engagement scoped;
- no agent topology is canonical merely because it was proposed historically.

Exact terminology belongs to the linked source documents. Where Confidence
Ledger or professional belief-tier definitions cannot be recovered exactly,
their status remains `HISTORICALLY_REFERENCED — EXACT DEFINITION NOT YET
RECOVERED`.
