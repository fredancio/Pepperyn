# Feature and Capability Register

**Coverage claim:** comprehensive for meaningful capabilities discoverable in
the current repository, migrations, tests and current Founder authority. It is
not represented as a byte-exhaustive reconstruction of the unavailable original
Cowork set; those historical gaps remain quarantined in `16`.

**Status vocabulary:** `HISTORICALLY_REFERENCED`, `CONCEPTUALIZED`, `DECIDED`,
`DOCUMENTED`, `PROTOTYPED`, `IMPLEMENTED`, `TESTED`, `LIVE_PROVEN`, `DEFERRED`,
`REJECTED`, `SUPERSEDED`, `UNRESOLVED`.

Every row preserves a capability even when it is not a V1 requirement or not
visible in the UI. Evidence grades are bounded; multiple statuses may describe
different maturity dimensions.

## Product shell and access

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Authentication/session | Restrict client data to authorized users | IMPLEMENTED / TESTED | `routers/auth.py`, frontend auth routes | YES |
| PIN/guest flow | Historical low-friction access | IMPLEMENTED / LEGACY | legacy capability inventory | REVIEW FOR BETA |
| Account deletion | Data lifecycle and user rights | IMPLEMENTED | auth router | YES |
| Organizations/workspaces/entities | Separate professional client contexts | IMPLEMENTED / TESTED | migrations v6/v8; entities router | YES |
| Engagement | Maintain mandate continuity | IMPLEMENTED / TESTED | ADR-002; v19-v22; service | YES |
| Invitations/membership | Controlled collaboration | IMPLEMENTED | v9; auth flow | YES, ADAPT TO EXACTLY TWO USERS |
| Settings | User/product configuration | IMPLEMENTED | settings UI/services | YES AS NEEDED |
| Public registration | Historical commercial shell | IMPLEMENTED BUT PROHIBITED FOR BETA | register route; Founder directive | NO / MUST DISABLE |
| Billing/Stripe | Historical commercial monetization | IMPLEMENTED / TESTED / NOT BETA REQUIRED | billing router/service; v10-v13 | NO |
| Quotas/usage | Bound consumption and abuse | IMPLEMENTED | usage service; v2/v11 | MAY SUPPORT SAFETY |
| Contact/support | Operational communication | IMPLEMENTED / FINFLATE-BRANDED | contact router/page | YES AFTER DEBRANDING |
| Superadmin Control Center | Separate platform authority | IMPLEMENTED / IDENTITY CONFIG OPEN | superadmin router/admin UI | YES, HARDEN |
| Growth/CRM admin | Historical internal capability | IMPLEMENTED / PARKED FOR V1 | crm service/admin growth UI | NO |

## Financial ingestion and understanding

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| File upload and parsing | Accept CFO working material | IMPLEMENTED / TESTED | file parser; analyze route | YES |
| Passive OOXML inspection | Read source without executing workbook behavior | IMPLEMENTED / TESTED | formula/OOXML test corpus | YES |
| Heterogeneous V1 workbook admission | Understand supported variation or refuse honestly | LIVE_PROVEN_SYNTHETIC | heterogeneous falsification document/tests | YES |
| Data quality gate | Stop inadequate input | IMPLEMENTED | data_quality_gate.py | YES |
| Financial normalization | Produce bounded comparable facts | IMPLEMENTED | financial_normalizer.py | YES |
| Temporal column normalization | Identify periods | IMPLEMENTED WITH KNOWN GAPS | temporal_normalizer audit | YES |
| FRU foundation | Understand financial representation rather than fixed templates | DOCUMENTED / PARTIALLY IMPLEMENTED / GENERALIZED DEFERRED | FRU documents/services | BOUNDED V1 ONLY |
| Formula evidence | Preserve derivation structure | IMPLEMENTED / TESTED | formula services/tests | YES WHERE USED |
| Observation structure | Separate leaf/aggregate/KPI and derivation | IMPLEMENTED / TESTED | observation contract/service | YES |
| Sign convention detection | Avoid inverted financial meaning | IMPLEMENTED / TESTED | fru_sign_convention_detector.py | YES |
| Personnel-cost classifier | Establish bounded economic meaning | IMPLEMENTED / TESTED | classifier contract/service | SUPPORTING |
| Concept vocabulary | Stable governed financial concepts | IMPLEMENTED / TESTED | concept_vocabulary.py | YES |
| Canonical financial doctrine v0 | Compare facts against explicit doctrine | IMPLEMENTED / TESTED | financial_doctrine.py | YES, BOUNDED |
| General economic-meaning ontology | Broader professional semantics | CONCEPTUALIZED / DEFERRED | cognitive/deferred corpus | NO |
| Exception & Reconciliation | Preserve conflicting sources and corrections | CONCEPTUALIZED / DEFERRED | deferred register | NOT CURRENTLY |

## Evidence, knowledge and epistemics

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Evidence Ledger | Durable provenance and auditability | IMPLEMENTED / TESTED / CONSUMPTION BOUNDED | ADR-001/001A; v18/v23 | YES |
| Evidence capture | Bind analysis facts to source | IMPLEMENTED | evidence_capture.py | YES |
| Evidence integrity/query | Verify and retrieve evidence | IMPLEMENTED | evidence services | YES |
| Assertion-level evidence links | Prove a specific recommendation from specific facts | DEFERRED WITH TRIGGER | deferred register §1.3.b | ONLY BEFORE SUCH CLAIM |
| Evidence capture outcome semantics | Distinguish empty/pre-ledger/failure | DEFERRED WITH TRIGGER | deferred register §1.3.a | BEFORE DEPENDENT CONSUMER |
| Candidate epistemic model | Hold noncanonical candidates | IMPLEMENTED COMPONENT | candidate.py | YES |
| Knowledge Model v0 | Preserve scoped learned context without auto-truth | IMPLEMENTED / TESTED | v24-v26; service | YES |
| Epistemic dialogue | Ask/recall when evidence is insufficient | IMPLEMENTED / TESTED | service/contract | YES WHERE WIRED |
| RECALL-before-ASK | Avoid repeatedly burdening the CFO | DECIDED / IMPLEMENTATION COVERAGE UNRESOLVED | epistemic documents | YES |
| UNKNOWN | Honest lack of support | DECIDED / TESTED / LIVE_PROVEN | Constitution; Golden cases | YES |
| CONTRADICTION | Preserve incompatible evidence | DECIDED / TESTED | contracts/tests | YES |
| Confidence Ledger | Durable confidence evolution | HISTORICALLY_REFERENCED / EXACT DEFINITION NOT FULLY RECOVERED | cognitive corpus | UNRESOLVED |
| Professional belief tiers | Separate doctrine/enterprise knowledge/hypothesis | DOCUMENTED / PARTIAL | cognitive/foundation corpus | YES IN PRINCIPLE |
| Candidate-to-canonical doctrine promotion | Prevent model self-authorization | DOCUMENTED / BOUNDED IMPLEMENTATION | doctrine/knowledge contracts | SUPPORTING |

## Analysis and reasoning

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Legacy multi-call LLM pipeline | Produce broad analysis | IMPLEMENTED LEGACY / TRUST DEFECT HISTORICALLY FOUND | llm_service; trust-boundary docs | MUST NOT BYPASS GATES |
| Governed V1 structured analysis | Produce bounded traceable professional analysis | TESTED / LIVE_PROVEN_SYNTHETIC | v1 contract; Golden rehearsal | YES |
| Provider-independent reasoning contract | Replace providers without losing Pepperyn | DECIDED / PARTIAL IMPLEMENTATION | egress/projection services | YES |
| Multi-agent/adversarial reasoning | Reduce anchoring and disagreement risk | CONCEPTUALIZED / PROPOSED / DEFERRED | cognitive architecture | NO UNLESS RELIABILITY GATE REQUIRES |
| Verification stage | Prevent unchecked model output | IMPLEMENTED IN BOUNDED PATHS | V1/provider-return contracts | YES |
| Executive case models | Compose professional analysis | IMPLEMENTED LEGACY + GOVERNED V1 ALTERNATIVE | executive case builders | YES, PATH-SPECIFIC |
| Recommendation generation | Suggest action without deciding | IMPLEMENTED / LIVE_PROVEN SYNTHETIC V1 | governed analysis | YES |
| Required validations | Keep recommendations conditional | IMPLEMENTED / LIVE_PROVEN | governed workflow | YES |

## Memory, time, decision and attention

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Analysis history | Restore context after restart | IMPLEMENTED / LIVE_PROVEN SYNTHETIC | history routes; v27 | YES |
| FTE v0 | Normalize business time deterministically | IMPLEMENTED / TESTED | FTE contract/service | YES |
| Governed temporal comparison | Explain later-period changes | IMPLEMENTED / TESTED SYNTHETIC | temporal service/tests; e23dc05 | YES |
| Business/Knowledge/Decision Time distinctions | Avoid temporal category errors | DOCUMENTED / PARTIAL | FTE/cognitive corpus | YES IN PRINCIPLE |
| Decision memory | Remember professional choices | IMPLEMENTED / LIVE_PROVEN | v28-v32; persistence service | YES |
| Intention | Capture nondecision response | IMPLEMENTED / LIVE_PROVEN | v28 | YES |
| Explicit confirmed decision | Separate human decision from recommendation | IMPLEMENTED / LIVE_PROVEN | v29 | YES |
| Decision follow-up | Preserve checkpoint without changing decision | IMPLEMENTED / LIVE_PROVEN | v30 | YES |
| Prerequisite evidence | Justify execution prerequisites only | IMPLEMENTED / LIVE_PROVEN SYNTHETIC | v32 | SUPPORTING |
| Explicit execution | Separate doing from deciding/outcome | IMPLEMENTED / LIVE_PROVEN SYNTHETIC | v31 | YES |
| LaterEvidence/ActualOutcome/Learning | Measure what happened later | DOMAIN DISTINCTION DECIDED / NOT PROVEN IN CURRENT CHAIN | Founder decisions | NOT REQUIRED WITHOUT PROSPECTIVE CONTRACT |
| DecisionArc | Long-lived decision/outcome learning structure | IMPLEMENTED LEGACY / NO IMPLICIT ARC IN V1 | v16-v22; arc service | PRESERVE, DO NOT AUTO-CREATE |
| Portfolio intelligence | Orient CFO across clients | IMPLEMENTED / TESTED | portfolio UI/service | YES |
| Governed attention suppression | Do not present executed work as open | LIVE_PROVEN SYNTHETIC | portfolio checkpoint ac37d9d | YES |
| Intelligent client cards | Reduce reconstruction and expose next attention | IMPLEMENTED PARTIALLY / V1 GAP | Portfolio/Profession Model | YES |
| Review Briefing | Recall relevant open context | IMPLEMENTED / TESTED | review briefing UI/routes | YES |
| Enterprise Familiarization | Build durable company-specific knowledge | DEFERRED WITH DEPENDENCIES | Profession Model/deferred register | MAY BE PARTIAL V1 |

## Deliverables

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Governed XLSX export | CFO-usable traceable working output | LIVE_PROVEN SYNTHETIC | export service/tests/live file | YES |
| Governed PDF export | Stable professional narrative | LIVE_PROVEN SYNTHETIC | export service/tests/live file | YES |
| Governed PPTX export | Client presentation workflow | LIVE_PROVEN SYNTHETIC | export service/tests/live file | YES |
| Export persistence after restart | Reproduce deliverable from durable authority | LIVE_PROVEN SYNTHETIC | persisted analysis rehearsal | YES |
| Export debranding | Active Pepperyn identity | OPEN | active Finflate inventory | YES |

## Privacy, provider and platform trust

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Legacy anonymization layer | Reduce direct identifiers | IMPLEMENTED / COVERAGE HISTORICALLY INCOMPLETE | anonymization audit/service | SUPERSEDED FOR GOVERNED PATHS, PRESERVE UNTIL RETIRED SAFELY |
| Central LLM egress authority | Stop distributed provider discretion | IMPLEMENTED / TESTED | llm_egress.py | YES |
| Ownership authority | Bind requests to exact scope | IMPLEMENTED / TESTED | ownership_authority.py | YES |
| Provider policy capability | Bind effective deployment policy | IMPLEMENTED / TESTED / PROVIDER CLOSED | provider_policy.py | YES |
| V33 correspondence | Local encrypted pseudonym continuity | LIVE_PROVEN SYNTHETIC | v33/service/tests | YES |
| V34 registration authority | Prevent caller-authoritative mapping | LIVE_PROVEN SYNTHETIC | v34/service/tests | YES |
| D10 minimal projection | Task-specific minimization | LIVE_PROVEN FOR ONE TASK | projector/tests/live rehearsal | YES PER USED TASK |
| Projection receipt | Preserve exact payload/provenance binding | TESTED / LIVE-PROVEN BOUNDED | D10 service | YES |
| Response quarantine | Treat provider output as untrusted | TESTED MOCK | provider response service | YES |
| Authorized rehydration | Resolve identity only locally and with capability | TESTED MOCK | provider response/correspondence services | YES |
| REIDENTIFIED re-egress prohibition | Enforce one-way boundary | TESTED BOUNDED | return/projection/egress tests | YES |
| Provider Gate | Require contractual/account/project evidence | PG-2 PASS; PG-3/PG-4 OPEN | Provider Gate document | YES |
| Real-data Admission | Prevent premature confidential data | CLOSED | sandbox/admission document | YES |
| Production key custody | Protect correspondence secrets operationally | OPEN | security model | YES |
| Rate limiting | Resist abuse | IMPLEMENTED IN-MEMORY / MULTI-WORKER DEBT | rate_limiter.py; legacy matrix | YES FOR PRODUCTION |
| Logs/privacy leakage control | Prevent secret/client data leakage | PARTIAL / PRODUCTION AUDIT OPEN | logging paths/security gate | YES |
| Backup/recovery/deletion | Preserve availability and lifecycle rights | PARTIAL / LIVE PROOF OPEN | Supabase/auth/infrastructure docs | YES |

## Strategy and deferred capability

| Capability | Why | Current status | Evidence/source | V1 |
|---|---|---|---|---|
| Self-Selling Control Center | Learn how Pepperyn should be sold under governance | DOCUMENTED / PARKED / DEFERRED | self-selling vision; deferred register | NO |
| Decision Simulation Engine | Explore decision consequences | ACCEPTED SUPPORTING VISION / DEFERRED | Vision references/deferred register | NO |
| BYOM/local/private model | Provider optionality/privacy | DEFERRED | deferred register | NO |
| Other professions | Long-term extensibility | DEFERRED | Profession Model/deferred register | NO |
| ERP/API/MCP connectors | Reduce manual ingestion | DEFERRED | deferred register / Code MCP | NO |
| Commercial pricing/subscriptions | Monetization | LEGACY IMPLEMENTED / BETA DEFERRED | billing code; Founder decision | NO |

## Removal rule

Two-user beta admission / public-registration surface: IMPLEMENTED, LOCAL_TESTED,
NOT ACTIVATED (24 A13/A14; 13 configuration). Additive to route ownership/admin
checks, not a replacement for actual Supabase signup/RLS/storage evidence.

Session-result context: LOCAL_TESTED (24 A10–A12). Stale reads and synthetic
operation results cannot overwrite newer selected contexts; governed errors
are explicit in synthetic mode. Legacy direct read remains available outside
that mode, including single-message histories. Not global async/RLS proof.

Client availability and history request scoping: LOCAL_TESTED (24 A8/A9).
Errors are not empty clients/history; stale responses cannot replace current
client history. Atomic creation/auth/plan doctrine preserved; no live RLS claim.

Later-period multi-client composition: LOCAL_TESTED (24 A7) from synthetic
parsed sources through real persisted envelope verification and HTTP reads.
Workbook admission/browser proof and real RLS remain open.

Temporal safeguards and bounded terminal disclosure: LOCAL_TESTED (24 A5/A6).
Ambiguous chronology/nonfinite values refuse comparison. Arithmetic-only scope
does not supersede full financial period semantics or professional validation.

Temporal terminal consumption: LOCAL_TESTED panel for the existing bounded
comparison endpoint (24 A4). Multi-client reload: LOCAL_TESTED through real
envelope integrity with mocked storage/auth (24 A3). Neither promotes the
general temporal reliability or two-user Beta gate.

Portfolio read availability: IMPLEMENTED / TESTED distinction between source
failure and a successful empty queue; execution evidence 24 A2. This does not
certify completeness when stored rows themselves are missing or inconsistent.

Post-takeover: selected-client synthetic mock ingestion is IMPLEMENTED / TESTED
at its HTTP-to-persistence-call boundary (execution evidence 24, A1). Two-user
and live multi-client continuity remain unproven; no gate is promoted.

No row may disappear because its UI is absent or because it is outside V1.
Additional bounded A15 capability: professional Beta login entry suppresses
legacy PIN/signup/purchase UX without granting any role. LOCAL_TESTED and local
production build PASS; HTTP/browser/live Auth unproven. A16 financial casebook is
DOCUMENTED_DRAFT awaiting independent professional expected-result review, not
implemented financial inference or gate closure. Sources: execution evidence 24
and `docs/Product/PEPPERYN_PRIVATE_BETA_FINANCIAL_REVIEW_CASEBOOK_V1.md`.

Retirement requires a source-grounded `REJECTED` or `SUPERSEDED` decision, impact
analysis and Founder escalation when a capability or guarantee is material.

A17 supersedes A16 draft review status: Founder-transmitted professional review
with clarifications is preserved and frozen as FR-EXPECTED-2. Professional
reasoning PR-01..PR-08 is ADOPTED_AS_REQUIREMENTS / IMPLEMENTATION_PARTIAL, not a
newly implemented engine. Synthetic input/expected-result artifacts and integrity
checker are PREPARED / STRUCTURALLY_TESTED; financial execution NOT_STARTED.
Source: `docs/Product/FinancialReliability/casebook-v2.md`, full review and frozen
manifest. No ontology widening, self-certified financial answer or gate promotion.

A18/A19 (2026-09-17): source contradiction inspection is IMPLEMENTED / LOCAL_TESTED:
retain conflicting and independent source claims without canonical promotion;
measure discrepancy without resolving it; preserve references to chat consumption.
Signed reported/derived reconciliation is IMPLEMENTED / COMPONENT_TESTED ONLY:
explicit definition and same-scope inputs; UNKNOWN requests; conflict dependency
refusal; no semantic/causal/economic/decision promotion. Production definition
authority and durable contradiction lifecycle remain unproven. FR07/FR08 local
component outputs are not full-case PASS. Source/evidence:
`docs/Product/FinancialReliability/consistency-component-evidence-A18-A19.md`.

A20/A21: unresolved synthetic source dossier capture/reload is IMPLEMENTED /
LOCAL_MOCK_HTTP_UI_TESTED / NOT_DEPLOYED. WHY: source contradictions must survive
without pretending to be completed analyses or confirmed interpretations. V35
preserves tenant/entity/engagement scope and immutability; existing V18/V24/V27
semantics unchanged. No full persistence/exports/professional gate PASS. See
`docs/Product/FinancialReliability/source-dossier-evidence-A20-A21.md`.
