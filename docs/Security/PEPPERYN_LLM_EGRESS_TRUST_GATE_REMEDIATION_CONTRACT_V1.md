# PEPPERYN — LLM EGRESS TRUST GATE REMEDIATION CONTRACT V1

**Date:** 2026-08-28

**Status:** Candidate executable security contract — Founder arbitration required; no implementation authorized

**Canonical code baseline:** `main@9b17e0f3bebc33045f2197979c592368c3f39abc`

**Evidence provenance:** [`PEPPERYN_LLM_EGRESS_TRUST_BOUNDARY_DISCOVERY_V1.md`](PEPPERYN_LLM_EGRESS_TRUST_BOUNDARY_DISCOVERY_V1.md), commit `c60d0592e4d5097c8e4941a142ce4f442cd53bc9`

## 1. Contract objective and root cause

This contract defines the smallest coherent remediation that can admit a synthetic and then governed real-client Founder rehearsal. It does not authorize production changes.

The root cause is not a defective string replacer. Pepperyn has **distributed authority over external disclosure**:

- provider clients are instantiated/called in several production modules;
- callers render arbitrary prompts before any common policy point;
- file pseudonymization, authorization, memory ownership, context selection, retry, logging and re-identification are separate optional decisions;
- a re-identified result is treated as ordinary internal data and can cross externally again;
- fallback compatibility is preferred over proof that the same boundary still holds.

Therefore path-by-path calls to `anonymize_text()` cannot close the system. The minimum systemic correction is one mandatory provider-call authority, structured disclosure envelopes, pre-access authorization, entity/Engagement-scoped context, and tests at the actual provider boundary.

## 2. Four distinct security contracts

### A. Identity and disclosure

Controls what may enter a provider payload. The policy is task-specific and classifies every dynamic segment. Pseudonymization reduces identity exposure but does not make financial data anonymous.

### B. Authorization and ownership

Proves the authenticated tenant owns every requested analysis/entity/Engagement before any cache, correspondence, memory, result or provider access. A resolver issues distinct protected-read and egress grants; the egress authority does not resolve ownership itself.

### C. Client/entity isolation

Selects context only from the authorized Entity/Engagement. Tenant-wide memory is not client memory. Cross-entity use requires a separately versioned portfolio task and aggregation policy.

### D. Provider/data governance

Governs intentional residual disclosure: exact financial values, provider retention/training/logging/region/contract and subprocessors. Code controls minimization; external assurance controls what happens after permitted disclosure. Neither substitutes for the other.

## 3. Phase 1 invariant disposition

| # | Phase 1 candidate | Disposition | Executable V1 rule |
|---|---|---|---|
| 1 | One enforceable egress authority | **ACCEPT** | Static architecture test permits production provider invocation in exactly one module/package. |
| 2 | No direct identity except an approved task exception | **MODIFY** | D1 direct personal identity and D2 real organization identity are **FORBIDDEN for every V1 provider task**. No V1 exception. A future exception requires a new policy version and Founder/security arbitration. |
| 3 | Re-identify only after final inference | **ACCEPT** | Any object marked/restored as re-identified is rejected by the authority. Re-identification is an internal terminal transformation after the request chain closes. |
| 4 | Restored result unsafe for re-egress | **ACCEPT** | `IdentityState.REIDENTIFIED` is structurally inadmissible in an outbound envelope. A new projection must originate from the pseudonymous source/result. |
| 5 | Missing correspondence/policy/provenance fails closed | **MODIFY** | Policy and authorization evidence are always mandatory. Correspondence is mandatory only for tasks with identity-bearing or re-identifiable input/output. Its absence yields a typed refusal, never a weaker path. |
| 6 | Retry/fallback equivalence | **ACCEPT** | Retry changes only an allowed model/attempt field. It reuses the same validated immutable envelope/policy; no caller-built retry payload. |
| 7 | Authorize every analysis/entity/Engagement | **ACCEPT** | Ownership is resolved before any protected read. Missing, foreign or mismatched ownership returns a denial and produces zero provider calls. |
| 8 | Entity/Engagement-scoped memory | **ACCEPT** | Single-client tasks require `entity_id`; decision/action context requires `engagement_id` or deterministically entity-owned legacy data. Company-only rows are quarantined from external prompts. |
| 9 | Minimum task-specific projection | **ACCEPT** | Each task policy is a closed allow-list of fields/classes. Unlisted fields are rejected, not silently dropped. |
| 10 | Govern raw free text | **MODIFY** | Arbitrary free text is forbidden in real-client V1 under the absolute D1/D2 rule. Only structured intent is admitted. Any later free-text feature requires a separately arbitrated exception that explicitly weakens that invariant. |
| 11 | Test captured payloads/logs | **ACCEPT** | Conformance tests intercept immediately before SDK/network dispatch and inspect the fully rendered provider request plus emitted audit/log records. |
| 12 | Keep minimization, pseudonymization and provider controls distinct | **ACCEPT** | A release gate reports all three independently; no single PASS implies anonymity or overall trust. |

## 4. Egress authority design

### 4.1 Decision

Use one narrow **`LlmEgressAuthority`** as the only production component allowed to invoke an external model SDK. This is the minimum design that makes bypass structurally testable.

It does not replace prompt/domain adapters. Each cognitive task owns its static instructions and creates a typed task projection. The authority owns only boundary enforcement and dispatch.

### 4.2 Accepted input contract

```text
EgressRequest
  request_id: opaque internal audit id
  task: EgressTask
  policy_id: exact versioned DisclosurePolicy id
  egress_authorization: opaque resolver-minted single-use handle
  identity_state: PSEUDONYMOUS | NO_IDENTITY
  correspondence_handle: optional opaque handle
  instruction_ref: immutable approved static-instruction id + content hash
  segments: ordered tuple<DisclosureSegment>
  route: ProviderRouteRequest

DisclosureSegment
  field_id: task-policy field id
  data_class: DisclosureClass
  necessity: REQUIRED | CONDITIONALLY_ALLOWED
  source_provenance_receipt: opaque projector/getter-minted receipt
  value: canonical JSON-compatible scalar/list/object

AuthorizationBundle (opaque immutable resolver records, not caller data)
  protected_read_grant: request-bound capability for allow-listed getters/resources
  egress_authorization: distinct single-use capability for provider egress
  authenticated_company_id
  entity_id: optional only when task policy permits no entity
  engagement_id: optional
  analysis_id: optional
  ownership_facts: exact checked relationships
  policy_scope
  issued_for_request_id
  task + policy_id + issuer/version + nonce + expiry
  admission_mode: SYNTHETIC_ONLY | REAL_DATA_ALLOWED

SourceProvenanceReceipt
  canonical_value_hash
  company_id + optional entity_id/engagement_id/analysis_id
  origin: SYNTHETIC | REAL
  source_type + field_id + request_nonce
  issuer/version + integrity proof
```

An arbitrary caller-rendered system/user prompt is not a valid production input. The authority renders the final provider payload from the approved static instruction and recursively schema-validated ordered segments. A caller-supplied class label is never trusted by itself: `field_id` selects an exact policy schema and every nested value must conform.

Every dynamic segment also carries a non-forgeable `SourceProvenanceReceipt` issued only by an authorized protected getter/projector. The receipt binds the canonical value hash, company/Entity/Engagement/analysis scope, real/synthetic origin, source type, field id and request nonce. The authority recomputes the exact value hash and validates the receipt. A segment without a receipt is admissible only when its field is an approved static constant. `data_origin` and `source_scope` are not caller assertions; they are derived exclusively from verified receipts, authorization and the deployment kill switch.

### 4.3 Output contract

```text
EgressResult
  request_id
  task
  provider_route_used
  attempt_count
  content: UNTRUSTED_PROVIDER_OUTPUT
  usage: input/output token counts
  audit_receipt: payload hash + class counts + policy id + outcome

EgressRefusal
  code: AUTHORIZATION_DENIED | SCOPE_MISMATCH | POLICY_MISSING |
        FIELD_NOT_ALLOWED | IDENTITY_FORBIDDEN | SECRET_SUSPECTED |
        CORRESPONDENCE_UNAVAILABLE | LEGACY_CONTEXT_UNATTRIBUTED |
        PROVIDER_POLICY_GATE_CLOSED | ROUTE_NOT_ALLOWED
  safe message
  audit receipt without content
```

### 4.4 Responsibilities

- validate exact task-policy version and static-instruction hash;
- validate the egress authorization matches request, task, policy and every verified provenance receipt;
- resolve and consume only authentic, unexpired, single-use egress authorizations minted by the ownership resolver; reject replay;
- recompute each dynamic value hash and validate its provenance receipt issuer/version, nonce, scope, origin, source type and field;
- enforce the closed field/data-class allow-list and conditional predicates;
- resolve an authorized correspondence handle without exposing the table to task code;
- pseudonymize approved identity-bearing/free-text segments immediately before rendering;
- reject D1/D2 remnants and suspected D8 credentials using deterministic sentinel/pattern controls, acknowledging detection is defense-in-depth rather than proof of absence;
- render the final provider payload;
- route only to provider/model combinations allowed by policy;
- execute retries from the same immutable validated request;
- return `UNTRUSTED_PROVIDER_OUTPUT` and non-content audit metadata;
- provide the single interception point for tests.
- enforce a server-derived data-origin admission mode bound jointly to the attestation and deployment kill switch; callers cannot select synthetic/real mode.

### 4.5 Prohibited responsibilities

- no financial reasoning, classification, scoring or recommendation;
- no domain prompt authorship or task-field selection;
- no analysis/entity/Engagement lookup;
- no memory retrieval;
- no ownership adjudication;
- no user-plan/business entitlement logic;
- no re-identification;
- no persistence of prompts/responses or correspondence values;
- no logging of payload content, free text, user message prefixes or provider response text.
- no assertion that provider output is pseudonymous, identity-free or safe for another inference.

### 4.6 Authorization prerequisites

The calling route/service must obtain an opaque `AuthorizationBundle` from a single internal ownership resolver **before** reading:

1. analysis/result caches or DB result;
2. ExecutiveCase caches;
3. correspondence state;
4. entity/Engagement memory;
5. decision/action history;
6. any provider-bound projection.

Only the resolver may mint the two immutable capabilities in the bundle. Both bind company, Entity, Engagement, analysis, task, policy, request nonce, issuer/version, expiry and server-derived admission mode, but they are not interchangeable:

- `ProtectedReadGrant` is accepted only by explicitly allow-listed getters/projectors, may be reused only for its enumerated resources during the same request lifetime, and can never authorize network egress;
- `EgressAuthorization` is accepted only by the egress authority, is consumed exactly once, and can never authorize a protected read.

The authority validates issuer, version, integrity, expiry, nonce, task, policy and scope before consuming the egress capability. Direct construction is unavailable to ordinary task code and no client-supplied capability is accepted.

The resolver reads only minimum ownership metadata. Every protected cache/content getter requires the `ProtectedReadGrant`; knowing an ID cannot call a content getter directly. Authorized getters/projectors mint value-bound provenance receipts. Negative tests cover forged, expired, replayed, wrong-task and wrong-policy capabilities, attempting to use a read grant for egress or an egress authorization for reading, and cache-hit/cache-miss paths.

### 4.7 Retry and fallback

- After first validation, the authority freezes the exact rendered semantic bytes, instruction bytes/hash and policy snapshot. Provider retry/escalation reuses that frozen object.
- Allowed change: route/attempt metadata explicitly listed by policy.
- Forbidden change: segments, identity state, authorization scope, instruction content or policy.
- A cognitive fallback that needs a different payload is a new `EgressRequest` and must pass the full gate.
- A deterministic internal fallback does not traverse the authority.
- Failure never falls back to a less protected legacy call.
- Configuration or policy changes between attempts cannot alter semantic bytes; only enumerated transport/model fields may differ.

### 4.8 Observability and logging

Allowed audit fields: request id, task, policy id, static instruction hash, scope identifiers in access-controlled audit form, provider/model, attempt count, segment class counts, canonical payload hash, token counts, timestamps, result/refusal code.

Forbidden: segment values, rendered prompts, provider response content, correspondence mappings, raw messages, filenames containing client identity, or the first characters of user text.

Governed sinks include application logs, authority audit, provider SDK/HTTP debug output, exception middleware, APM/error reporting, reverse-proxy traces and serialization-error handlers. SDK/body logging is disabled; central redaction applies before every configured sink. Production debug mode may not weaken these rules.

### 4.9 Narrow internal composition

There is one public choke point, but not one monolithic implementation. Internally it composes:

1. `AttestationVerifier`;
2. `DisclosurePolicyValidator`;
3. `CorrespondenceTransformer` (opaque handles only);
4. `ProviderPayloadRenderer`;
5. `AuditEmitter`;
6. `ModelProviderTransport`.

Only `ModelProviderTransport` may perform network egress. None retrieves domain context or performs cognition. Ordinary task code cannot import the transport. Provider credentials are injected into transport headers only after content validation, are redacted everywhere, and are never admissible as a disclosure segment.

Static controls also reject known provider hosts, provider credential names and generic network/shell transport construction in model-related production modules outside the authorized transport. Because the backend legitimately uses HTTP elsewhere, deployment egress controls should, where technically available, restrict model-provider hosts to the authorized runtime identity/path rather than banning all HTTP globally.

## 5. Disclosure classes and task policies

### 5.1 Classes

```text
DIRECT_PERSON_IDENTITY (D1)
ORGANIZATION_IDENTITY (D2)
PSEUDONYMOUS_IDENTITY (D9)
EXACT_FINANCIAL_FACT (D4-exact)
AGGREGATED_FINANCIAL_FACT (D4-aggregate)
OPERATIONAL_CONTEXT (D3)
ENTERPRISE_MEMORY (D6)
DECISION_ACTION_COMMENT (D7)
USER_FREE_TEXT (D5)
CREDENTIAL_OR_SECRET (D8)
PROVENANCE
TECHNICAL_METADATA
STATIC_INSTRUCTION
COMBINATION_IDENTIFIABLE_DATA (D10 policy dimension)
BOUNDED_TEXT (deterministic rendering from closed grammar + receipted structured values)
```

All dynamic data is classified. `CREDENTIAL_OR_SECRET` is forbidden universally. D1/D2 are forbidden for all V1 external tasks. Pseudonyms are scoped per analysis/Entity and must not be stable across unrelated clients. D10 is an additional policy dimension over combinations: each task declares permitted metric/period/context combinations, maximum granularity, required coarsening and accountable residual-risk acceptance.

`BOUNDED_TEXT` is not arbitrary prose. Its template/grammar is approved and immutable under the task-policy version; every inserted value is a closed-vocabulary token, number/date, registered pseudonym or separately receipted structured value. The authority can parse and validate the rendered value against that grammar. Arbitrary narrative from profiles, enterprise memory, recommendations, decisions, user comments, rejection reasons or prior model output is forbidden in V1 even when labelled D3/D6/D7.

### 5.2 Task matrix

Legend: **R** required, **C** conditionally allowed by predicate, **F** forbidden, **U** Founder/provider policy unresolved.

| Task | D1/D2 | D9 | Exact financial | Aggregated financial | Operational context | Memory | Decisions/comments | User free text | Provenance/metadata |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `DOCUMENT_CLASSIFICATION` | F | C | F | C | C | F | F | F | R |
| `EVIDENCE_EXTRACTION` | F | C | **R** | R | C | F | F | F | R |
| `FINANCIAL_ANALYSIS` | F | C | **R** | R | C | C | C | F | R |
| `FINANCIAL_PREPASS` | F | C | **R** | R | C | F | F | F | R |
| `STRATEGIC_PREPASS` | F | C | C | R | C | F | F | F | R |
| `ANALYSIS_VERIFICATION` | F | C | **R** | R | C | C | C | F | R |
| `ANALYSIS_QUALITY_SCORE` | F | C | F | C | C | F | F | F | C |
| `ANALYSIS_CHAT` | F | C | C | R | C | C | C | **F in real-client V1** | R |
| `EXPORT_NARRATIVE` | F | C | C | C | C | F | C | F | R |
| `TEXT_ONLY_GENERAL_QA` | F | F | F | C | C | F | F | **F in V1** | C |

### 5.3 Conditional predicates

- Operational context must be structured closed-vocabulary data or `BOUNDED_TEXT`, entity-scoped and necessary to the task. Best-effort scrubbing of arbitrary narrative is not admissible.
- Memory/decisions require matching Entity/Engagement ownership and field-level selection. Only structured values or `BOUNDED_TEXT` are admissible; raw narrative, comments/reasons and company-wide history are invalid.
- Real-client V1 chat admits only structured/closed-vocabulary intent (`question_type`, approved metric/period selectors and server-owned quick-prompt identifiers). Arbitrary raw user prose is forbidden because incomplete name detection cannot prove the absolute D1/D2 invariant. A future arbitrary-narrative exception—whether chat, operational context, memory, recommendation, decision, comment or reason—requires separate Founder/security arbitration and a revised disclosure invariant.
- Exact values in chat are included only when the selected question context requires quantitative explanation, never simply because they are available.
- No task may receive an entire `AnalysisResult`, `ExecutiveCase`, DB row or memory record as a convenience payload.
- For every task, the policy enumerates permitted joint combinations of exact values, dates, sector and operational context. A combination outside that matrix is rejected or coarsened before dispatch; merely recording D10 risk is insufficient.

### 5.4 Exact financial values

Exact values are necessary for evidence extraction, financial analysis, pre-analysis arithmetic and verification. Transforming them into ranges would materially impair arithmetic, variance, materiality and contradiction checks. They may remain exact while identity remains pseudonymous.

This is an intentional disclosure of commercially sensitive data, not anonymity. It is admissible only when:

1. the task matrix marks it R/C;
2. the values are scoped to the authorized Entity/Engagement and minimum period/metric set;
3. D1/D2 are absent;
4. combination-identification risk is recorded in the audit/policy decision;
5. the provider-policy gate in §12 is open;
6. the task's D10 combination/granularity rule is satisfied and its named residual-risk owner has accepted that policy version.

Exact values are not automatically necessary for document classification, quality scoring, generic text Q&A or deterministic exports.

## 6. Memory and client-isolation contract

### 6.1 Authoritative keys

- `company_id`: tenant boundary and authenticated organization.
- `entity_id`: mandatory client/organization subject for every single-client external task.
- `engagement_id`: mandatory owner for mandate-specific decisions/actions when present; must resolve deterministically to the same `entity_id` and `company_id`.
- `analysis_id`: instance/provenance key; must resolve to the same company/entity and, where recorded, Engagement.

No one key substitutes silently for another.

### 6.2 Retrieval rules

- Enterprise financial memory for a client is retrieved by `(company_id, entity_id)`.
- Decision/action memory is retrieved by `(company_id, entity_id, engagement_id)` when Engagement attribution exists.
- If an external task has no authorized `entity_id`, it receives no client memory.
- Tenant-wide user preference may be included only as closed, non-client, non-sensitive configuration under an explicit field policy.
- Portfolio reasoning is out of V1 scope here. A future portfolio task requires a new aggregate policy and may not reuse single-client raw contexts.

### 6.3 Legacy data

- Company-only memory/decision rows with no deterministic Entity/Engagement attribution are `QUARANTINED_FOR_EGRESS`.
- They remain stored and visible through authorized internal/user history where otherwise permitted, but are never selected for an external prompt.
- No heuristic attribution by chronology, name similarity or latest active client.
- A later deterministic migration may attribute rows only from authoritative foreign keys/provenance; otherwise quarantine persists.

### 6.4 Isolation oracle

Given Client A and Client B synthetic sentinels under the same `company_id`, every captured Client B payload and log must contain zero Client A sentinel bytes/strings/values and no pseudonym stable enough to link A to B. The inverse must also hold.

## 7. Chat authorization contract

For `/api/chat` and any equivalent path, the exact sequence is:

1. authenticate request; resolve server-trusted `company_id`;
2. require `analysis_id` for analysis-bound chat;
3. resolve analysis ownership from authoritative DB/cache metadata without reading analysis content;
4. require `analysis.company_id == authenticated company_id`;
5. resolve `entity_id` and optional `engagement_id`; verify both belong to the same company and match the analysis;
6. issue a request-bound `AuthorizationBundle` containing distinct read and egress capabilities;
7. only then read result/ExecutiveCase/history/memory caches or DB content through getters that require the `ProtectedReadGrant`; callers never receive correspondence mapping values;
8. authorized getters/projectors build the task projection and mint a provenance receipt bound to every dynamic value;
9. invoke `LlmEgressAuthority` with the separate single-use `EgressAuthorization`, verified segment receipts and only the opaque correspondence handle;
10. treat returned content as `UNTRUSTED_PROVIDER_OUTPUT`; terminally restore registered aliases only through the correspondence component/version after the external chain is explicitly closed, then validate for user-output safety;
11. return user output and non-content audit receipt.

Rejections:

- foreign analysis/entity/organization mismatch: `404` externally (avoid resource enumeration), typed `AUTHORIZATION_DENIED` internally;
- missing ownership evidence or legacy analysis without resolvable scope: `409 protected context unavailable` or equivalent stable safe response;
- missing correspondence for analysis-bound identity-bearing chat: `409 protected context unavailable`, zero fallback and zero provider call;
- unauthenticated: existing `401` behavior.

Frontend possession of an ID, UUID entropy and cache locality are not authorization.

## 8. Correspondence and re-identification lifecycle

```text
SOURCE
  → authenticated, authorized internal normalization
  → correspondence registration in authoritative protected store
  → pseudonymous task projection
  → governed external inference (possibly several calls/retries)
  → final external inference chain explicitly closed
  → internal re-identification
  → user/persistence projection
```

### 8.1 Correspondence authority

The in-process dictionary is not authoritative. V1 requires a `CorrespondenceRepository` with:

- key scope `(company_id, entity_id, analysis_id)`;
- ownership check before read;
- encryption at rest under a server-controlled key distinct from DB credentials;
- no table values in logs/audit/provider payloads;
- retention/deletion coupled to the analysis/account policy;
- atomic version/checksum so a payload and response use the same mapping version;
- fail-closed behavior on absence, corruption, scope mismatch or decryption failure.
- an API that exposes only opaque handles to callers; mapping resolution occurs inside the trusted `CorrespondenceTransformer` after attestation validation.

The precise storage technology is an implementation choice only if it proves these behaviors. A database migration/environment secret is likely and must be separately authorized in the implementation mission.

### 8.2 Re-egress prohibition

No `REIDENTIFIED` object or `UNTRUSTED_PROVIDER_OUTPUT` may be placed in an `EgressRequest`. Downstream chat/export must use a retained authority-produced pseudonymous projection carrying its payload/provenance receipt, or reconstruct one from authorized source through the boundary. It may never sanitize provider prose or a restored arbitrary object and assume equivalence.

A provider can hallucinate a real name, reproduce a secret-like token or reconstruct identity from exact context. Therefore output state is never inferred from input state. A provider-double negative vector deliberately emits D1/D2, secrets and the other client's sentinels; the output must not be eligible for re-egress and must pass a separate local user-output policy before presentation/restoration.

### 8.3 Legitimate exceptions

No V1 task needs real identity at the provider. Branding, names and user-facing restoration occur locally after the last provider call.

## 9. Export-time Opus decision

| Dimension | A. Deterministic export | B. Governed export inference |
|---|---|---|
| Product quality | Existing Python mapper already produces a complete fallback; narrative differences require regression review | May preserve current generated explanation wording |
| Security | Simplest: zero export provider boundary and local branding | Requires another policy, pseudonymous source and final re-identification |
| Cost/latency | Lower, predictable, offline-capable | Opus cost and latency on cache miss |
| Determinism | High and testable | Provider/model variability despite temperature 0 |
| Regression risk | Medium: golden PDF/PPTX output may change | Lower immediate visual change, higher security/operational complexity |
| Professional output | Must be compared; calculations already deterministic | Potential narrative polish, not proven necessary |

**Architecture recommendation: Alternative A, deterministic export.** The pure-Python fallback proves provider inference is not required for basic export creation. Company branding is applied locally. If field evidence later proves a material narrative-quality loss, a separate optional `EXPORT_NARRATIVE` task can be arbitrated; it is not part of the default V1 path.

Founder decision F1 remains required before implementation because this can change visible deliverables.

## 10. Text-only endpoint decision

No evidence establishes `/api/analyze/text` as required for first-client V1. Its unconstrained free text is costly to govern reliably and overlaps general-purpose AI.

**Recommendation:** remove/disable it from V1 and the public capability surface for the rehearsal. Do not spend the first remediation increment on preserving it. A future free-text `TEXT_ONLY_GENERAL_QA` requires the same separately versioned residual-risk exception as F7-B and must explicitly weaken the absolute D1/D2 invariant; UI warnings or incomplete detection cannot preserve the current absolute rule.

Founder decision F3 remains required because disabling a visible endpoint is a Product decision.

## 11. Legacy-data policy

| Legacy state | Policy | User-visible consequence |
|---|---|---|
| Analysis missing correspondence state | **FAIL CLOSED** for analysis-bound chat/re-egress; deterministic local views/exports may remain | Chat unavailable with safe explanation; no silent legacy fallback |
| Unattributed company-only memory | **QUARANTINE FOR EGRESS** | History retained; not used as AI context |
| Cached/persisted re-identified result | **NO RE-EGRESS** | Use for internal/user display; reconstruct/use pseudonymous projection for AI |
| Existing DecisionArcs/actions without deterministic Entity/Engagement | **QUARANTINE FOR EGRESS** | Retained, not injected |
| Previously generated ExecutiveCase | Treat as `REIDENTIFIED` unless provenance proves otherwise | Local rendering allowed; external reuse forbidden |
| Old analysis with retained source and valid authority | Optional explicit **REPROCESS** through the new boundary | New analysis/version; never silently overwrite history |

No historical user data is deleted by this policy.

Founder decision F2 must select fail-closed user experience versus a context-free chat mode. Architecture recommends fail closed for any analysis-bound claim; a clearly separate generic help mode could exist later.

## 12. Provider-policy gate

Source code cannot prove what happens after an allowed payload reaches the provider. Before governed real-client data is admitted, an accountable owner must record current primary evidence for:

- API data training/use policy;
- default and contracted retention periods;
- abuse/safety logging and human access;
- region/data residency and cross-border transfer;
- DPA/contractual terms and enterprise/API privacy guarantees;
- subprocessors;
- deletion/retention controls and any zero-retention eligibility;
- account/workspace settings actually active for Pepperyn;
- incident notification and audit evidence appropriate to the risk.

The implementation contract may proceed with synthetic sentinels while this gate is closed. A real-client rehearsal may not. Data origin is derived from verified value-bound provenance receipts and the resolver/deployment state, then checked against the egress authorization and deployment-level real-data kill switch. A caller cannot label data synthetic; copying a REAL-receipted value into a synthetic projection, changing its value, or relabelling its scope invalidates the receipt and is refused.

No provider guarantee is asserted here. A separate current-source verification must cite provider/account documents and the effective Pepperyn agreement/configuration.

Founder decision F6 defines the assurance threshold and accountable evidence owner.

## 13. Ordered remediation slices

### Slice 1 — Egress authority and architectural choke point

- **Objective:** make bypass mechanically detectable and move P1–P10 behind one authority; P11 is not migrated if deterministic export is approved.
- **Risks retired:** distributed provider clients, arbitrary retries, missing captured boundary.
- **Likely components:** new narrow egress package; `llm_service.py`, `conversation_engine.py`, `executive_case_builder.py` pending F1, `routers/analyze.py`; new security tests.
- **Dependencies:** approved task/envelope contract; synthetic-only provider doubles.
- **Authorized scope:** types, authority, adapters preserving existing semantic prompts/results, static allow-list.
- **Forbidden:** prompt/product semantic changes, memory redesign, provider/account change.
- **Tests:** A/B/C/E/J in §14 plus forged/replayed attestation, raw-HTTP bypass, data-origin spoofing and existing targeted analysis/export regressions.
- **Rollback:** one local branch/commit series; no schema change in this slice.
- **Exit gate:** all production provider SDK calls occur at one allow-listed dispatch line; captured synthetic payload parity established; no new backend regression.

### Slice 2 — Ownership attestation and entity-scoped context

- **Objective:** authorize before protected reads and eliminate company-wide client-memory mixing.
- **Risks retired:** foreign analysis/entity access, Client A context in Client B, unscoped legacy memory.
- **Likely components:** analyze/chat routes, ownership resolver, memory and decision-memory queries, focused tests; additive DB query/index work only if separately authorized.
- **Dependencies:** authoritative analysis↔entity↔Engagement relationships; F5 legacy policy.
- **Authorized:** strict scoped retrieval and quarantine.
- **Forbidden:** heuristic attribution or broad memory migration.
- **Tests:** F/G/H plus cache/DB parity and zero provider calls on denial.
- **Rollback:** query/route changes reversible; quarantine does not delete data.
- **Exit gate:** foreign/missing scope fails before content read; two-client sentinel matrix passes.

### Slice 3 — Durable correspondence and terminal re-identification

- **Objective:** remove in-process fail-open state and prevent restored objects from re-egress.
- **Risks retired:** restart/multi-worker protection loss, V2 restored narrative leakage, legacy silent fallback.
- **Likely components:** correspondence repository/interface/storage, analysis lifecycle, chat/V2 adapter, deletion path, schema/secret only after explicit authorization.
- **Dependencies:** approved storage/key design and F2.
- **Authorized:** scoped encrypted correspondence state and pseudonymous retained projection.
- **Forbidden:** plaintext mappings, logging mappings, silent migration guesses.
- **Tests:** C/F/G, mapping version mismatch, deletion, restart/multi-worker simulation, reidentified-envelope rejection.
- **Rollback:** additive storage; old in-memory fallback must not reactivate on rollback in real-client mode.
- **Exit gate:** missing/corrupt correspondence produces zero provider calls; V2 captured payload has no D1/D2 sentinel.

### Slice 4 — Task minimization and unsafe-surface retirement

- **Objective:** apply field policies, remove unnecessary export inference and dispose of text-only endpoint.
- **Risks retired:** P5 over-broad context, P6/P7 propagation, P8 raw text, P11 real-identity export.
- **Likely components:** task adapters/prompt projections, main pipeline, scoring, export orchestration, text endpoint/UI as decided.
- **Dependencies:** F1/F3/F4 decisions; provider gate can remain synthetic-only.
- **Authorized:** closed projections and deterministic export.
- **Forbidden:** financial reasoning redesign or marketing rewrite beyond necessary truthful surface disposition.
- **Tests:** B/C/D/E/I/J plus golden output/analysis semantic regressions.
- **Rollback:** per-task adapters independently reversible while authority remains mandatory.
- **Exit gate:** every task matrix rule passes; default PDF/PPTX makes zero provider calls if F1=A; text-only behavior matches F3.

### Slice 5 — Independent security promotion gate and rehearsal admission

- **Objective:** prove the complete boundary and decide synthetic→real admission.
- **Risks retired:** local test false confidence, logging leakage, undocumented provider residual risk.
- **Components:** test harness, architecture scan, provider evidence record, security review report; no product feature.
- **Dependencies:** Slices 1–4, F1–F7, provider assurance gate.
- **Tests:** complete §14 suite plus protected kernel/backend regressions and independent adversarial review.
- **Rollback:** no behavior change; failed gate blocks promotion.
- **Exit gate:** zero critical/high findings, exact allowed residual disclosure documented, Founder signs real-client admission.

## 14. Security test contract

Tests intercept the exact fully rendered request at the sole provider dispatch boundary. Unit tests of the anonymizer alone cannot satisfy this contract.

### A. Provider-call allow-list

AST/static scan fails if production code imports/instantiates Anthropic/OpenAI/provider SDKs or calls provider dispatch outside the authority module. Dynamic test asserts every simulated task increments the authority spy.

### B. Captured outbound payloads

Provider double uses a mock HTTP transport immediately after SDK serialization and stores URL, headers and exact body bytes. Test canonicalization is byte-stable. Assertions operate on the actual transport request, not intermediate segments or merely SDK arguments. Credential headers are asserted present only at transport, redacted from every observation.

### C. Synthetic identity sentinels

Inject distinct D1/D2 sentinels through file columns, sheet cells, relation name, profile, memory, decisions/comments, chat/history and export. None may appear in captured payload or logs. Expected scoped pseudonyms must appear where the policy permits them.

Inject a previously unknown name outside the correspondence table into D3 operational context, D6 memory and D7 decision/comment narratives. Each arbitrary narrative must be refused before dispatch. Equivalent closed structured fields and valid `BOUNDED_TEXT` renderings must pass.

### D. Exact-financial-value assertions

- P2/P3/P5/P6: exact sentinel amounts required and must remain numerically identical.
- classification/scoring/text-only/deterministic export: exact sentinels forbidden unless a stated conditional case is invoked.
- chat: table-driven quantitative versus non-quantitative cases.

### E. Retry/fallback equivalence

Force timeout, rate error, low score and model escalation. Captured attempts must have identical canonical disclosure segments/payload content except allow-listed route/attempt metadata. No legacy direct call may occur.

Mutate policy/configuration/instruction sources between attempts; frozen semantic body bytes must remain identical.

### F. Correspondence-loss fail closed

Simulate restart, missing row, decryption failure, version mismatch and different worker. Identity-bearing tasks return `CORRESPONDENCE_UNAVAILABLE`, emit no provider call and do not log input.

### G. Foreign-analysis authorization

Authenticated Company B requests Company A analysis/entity/Engagement across chat, export and analysis context. Response is non-enumerating denial; protected cache getters and provider double are not invoked.

### H. Cross-client memory isolation

Two Entities under one company use disjoint identity, amount, decision and comment sentinels. Each payload contains only its own allowed context. Unattributed company-only legacy row appears in neither.

### I. Export provider assertion

If F1=A, uncached PDF and PPTX generation with real-identity sentinels results in zero provider calls and passes approved golden/semantic output checks.

### J. Log-content assertion

Capture application/audit logs across success, refusal, exception and retry. No D1–D8 value, raw message prefix, prompt or response text may appear. Required safe audit metadata must appear.

Capture all governed sinks: application, authority audit, SDK/HTTP debug, exception middleware, APM/error reporting, reverse proxy and serialization failures.

### Additional negative vectors

- unlisted field/class, wrong policy version or instruction hash → refusal;
- `IdentityState.REIDENTIFIED` → refusal;
- scope mismatch between segment and attestation → refusal;
- secret-like synthetic token → refusal;
- arbitrary pre-rendered prompt input → type/validation failure;
- provider/account gate closed in real-data mode → refusal; synthetic mode remains available.
- forged/expired/replayed/wrong-task/wrong-policy read or egress capability on cache hit and miss → refusal before protected action;
- read grant used for egress, egress authorization used for reading, or second egress consumption → refusal;
- Client A value relabelled with Client B scope, altered after receipt issuance, or inserted without a receipt → refusal;
- raw HTTP/alternate SDK/provider-host constant outside transport → static/deployment test failure;
- production-origin provenance submitted through a synthetic caller → refusal;
- provider output containing D1/D2/secret/cross-client sentinels → `UNTRUSTED_PROVIDER_OUTPUT`, no re-egress.

## 15. Founder arbitrations

### F1 — Export path

- **A:** deterministic default export. **Recommended.** Lower cost/latency, simplest boundary; visible narrative regression must be tested. Reversible through a later governed optional task.
- **B:** governed pseudonymous Opus export. Preserves potential narrative polish, but adds cost, variability and boundary complexity.

### F2 — Legacy analysis without correspondence

- **A:** fail closed for analysis-bound chat. **Recommended.** Safest; some old chats unavailable.
- **B:** explicit context-free generic help mode, never represented as analysis-aware. Product complexity; can be added later.
- Silent legacy fallback is not an option.

### F3 — Text-only endpoint

- **A:** disable/defer for first-client V1. **Recommended.** Removes undifferentiated, high-entropy egress and cost.
- **B:** retain free text only if F7-B is also approved under one shared versioned residual-risk exception that weakens the absolute D1/D2 invariant. Detection/user-friction risk and implementation effort remain.

### F4 — Exact financial values

- **A:** permit exact pseudonymous values only for the R/C tasks and predicates in §5. **Recommended.** Preserves professional arithmetic; requires provider gate and accepts documented commercial sensitivity.
- **B:** require aggregation/ranges for all calls. Lower disclosure but likely damages evidence, arithmetic and materiality; would require product validation before adoption.
- Blanket unspecified residual exposure is not an option.

### F5 — Unattributed legacy memory

- **A:** quarantine from external inference until deterministic attribution. **Recommended.** Retains data, sacrifices some continuity.
- **B:** fund deterministic provenance migration where authoritative links exist; unresolved rows still quarantined. More cost, reversible/additive.
- Heuristic attribution is not an option.

### F6 — Provider/account assurance threshold

- **A:** require documented current API terms/DPA, no-training assurance, bounded retention/logging, subprocessor/region disclosure and verification of effective Pepperyn account settings before real data. **Recommended minimum.** May delay real rehearsal but not synthetic implementation.
- **B:** additionally require eligible zero-data-retention/private processing before real data. Stronger security, potentially higher cost or unavailable capability.
- Source-code minimization without an explicit provider threshold is not sufficient.

### F7 — Real-client arbitrary narrative input

- **A:** structured/closed-vocabulary values and `BOUNDED_TEXT` only for chat, operational context, memory, recommendations, decisions, comments and reasons in the first real-client rehearsal. **Architecture recommendation.** Preserves the absolute D1/D2 prohibition and bounded testability, but reduces narrative/conversational richness.
- **B:** authorize one separately versioned residual-risk exception for arbitrary narrative after best-effort pseudonymization. Better product continuity and conversational UX, but arbitrary new identity cannot be proven absent and the absolute identity invariant must be weakened explicitly.
- Silent reliance on regex/name detection while claiming zero D1/D2 is not an option.

All seven choices are reversible prospectively; none authorizes silent disclosure of previously protected data.

## 16. Adversarial review record

An independent reviewer must attempt to falsify this draft before final status. Required attacks:

- direct SDK/import or alternate HTTP provider bypass;
- retry/fallback mutation;
- re-identified second-call and export leakage;
- cache/content access before authorization;
- indirect identity reconstruction and exact-value linkage;
- free-text/new-name/secret leakage;
- same-tenant cross-client memory contamination;
- legacy compatibility weakening;
- logging under errors/retries/debug;
- tests intercepting an internal pre-sanitized object rather than final SDK bytes;
- authority growth into cognitive/context ownership.

Material findings and corrections are appended below after independent review.

### Independent review result

**Reviewer:** `adversarial_review` (Raman), independent of the contract author.

**Scope:** all required bypass/fallback/re-egress/authorization/reconstruction/free-text/memory/legacy/export/provider/logging/test-confidence/god-service attacks.

**Initial verdict:** **FAIL — not executable for Phase 3 authorization.**

Material findings and applied corrections:

1. **HIGH — caller-forgeable authorization:** replaced ordinary attestation data with resolver-minted, opaque, integrity-protected, expiring and request/task/policy-bound capabilities; the later revalidation further split protected-read and single-use egress authority.
2. **HIGH — D1/D2 invariant contradicted by arbitrary free text:** real-client V1 chat is now closed-vocabulary/structured; free text requires F7 and a revised invariant.
3. **HIGH — provider output falsely labelled pseudonymous:** output is now always `UNTRUSTED_PROVIDER_OUTPUT`, prohibited from re-egress and covered by hostile-output vectors.
4. **HIGH — SDK/raw-HTTP/test interception bypass:** added sole injected transport, host/credential/transport scans, post-serialization mock HTTP capture and optional deployment network restriction.
5. **HIGH — synthetic-mode spoofing:** added server-derived data origin, attestation binding and deployment real-data kill switch.
6. **MEDIUM — distributed correspondence authority:** callers now carry handles only; trusted transformer resolves/version-locks mappings.
7. **MEDIUM — D10 only recorded:** restored executable combination-identification policies and coarsening/admission rules.
8. **MEDIUM — retry configuration race:** frozen rendered semantic bytes, instruction and policy snapshot across attempts.
9. **MEDIUM — incomplete log sinks:** expanded governed/redacted sink set and conformance capture.
10. **MEDIUM — authority god-service risk:** retained one public choke point but split six narrow internal components; only transport can egress.

The corrected draft was returned to the independent reviewer for final re-validation; final verdict is recorded below before commit.

### Independent re-validation

**Second verdict:** **FAIL — three material contradictions remained.**

Applied corrections:

1. Split the former attestation into a request-scoped `ProtectedReadGrant` and a distinct single-use `EgressAuthorization`, with mutually exclusive consumers and replay semantics.
2. Replaced caller-declared `source_scope`/`data_origin` with non-forgeable, value-hash-bound `SourceProvenanceReceipt` objects minted by authorized getters/projectors and verified against exact segment content.
3. Made arbitrary text forbidden for both real-client chat and `TEXT_ONLY_GENERAL_QA` in V1. F3-B and F7-B now share one explicit future residual-risk exception that must weaken the absolute D1/D2 rule.

**Third verdict:** **FAIL — one material contradiction remained.** The absolute D1/D2 prohibition was still incompatible with arbitrary D3/D6/D7 narratives from profiles, memory, recommendations, decisions and comments.

Applied correction: introduced executable `BOUNDED_TEXT` with a closed grammar and receipted structured substitutions; arbitrary narrative is now forbidden across all V1 context classes, not only chat/text-only. F7 now governs any future arbitrary-narrative exception, and hostile unknown-name vectors cover D3/D6/D7.

**Final independent re-validation verdict:** **PASS.** No remaining HIGH/MEDIUM material defect. The reviewer confirmed that `BOUNDED_TEXT`, D3/D6/D7/chat/text-only narrative restrictions, F7 exception governance and hostile unknown-name vectors are mutually consistent. Founder arbitrations F1–F7 and the provider-policy evidence gate remain declared preconditions, not contract defects.

## 17. Promotion and stop conditions

Phase 3 implementation may be scoped only after Founder decisions F1–F7. Synthetic implementation can proceed while provider assurance evidence is collected, but real-client mode remains technically gated off.

Any implementation proposal that accepts arbitrary rendered prompts, permits a second provider dispatch site, reuses company-wide memory for a client task, silently tolerates missing correspondence, or lets a re-identified object re-enter the authority is non-conformant without further arbitration.

This document does not modify product behavior, provider configuration, database state, prompts or deployment.
