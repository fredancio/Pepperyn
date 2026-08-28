# PEPPERYN — LLM EGRESS TRUST BOUNDARY DISCOVERY V1

**Date:** 2026-08-28

**Evidence baseline:** canonical source `main@9b17e0f3bebc33045f2197979c592368c3f39abc`

**Mission mode:** Phase 1 read-only discovery; no implementation or security-contract promotion

## 1. Executive verdict

The Mission 3 blocker is **confirmed and materially broader than Conversation Engine V2**, but two earlier formulations require precision.

1. File-derived `parsed_data` is deep-copied and pseudonymized before the core analysis pipeline. That protection is real and worth preserving.
2. The primary pipeline then appends separately sourced, non-pseudonymized relationship, enterprise-memory and decision-memory sections to Call 1. A retry repeats the same disclosure. Call 2 and scoring can receive resulting text that has propagated those identifiers or contexts.
3. Conversation Engine V2 does not send the complete `ExecutiveCase V2` object or its `metadata.company_name` field. It sends a selected projection. However, that projection is constructed from the already re-identified analysis result and is not pseudonymized again. Its narrative fields can therefore carry restored identities, while exact financial values and decision context are deliberately included.
4. PDF/PPTX cache misses trigger a separate Claude Opus Executive Case Builder call. That prompt explicitly includes the real `company_name` and a broad projection of the already re-identified result. This active export-time LLM boundary was absent from the older ten-site trust inventory.
5. `/api/analyze/text` sends the user's query verbatim.
6. Legacy chat protects messages only when a non-empty in-process correspondence table is found. Missing/restarted/multi-instance state silently disables protection. New free-text names not already registered are not generically detected.
7. The `/api/chat` route does not verify that the supplied `analysis_id` belongs to the authenticated company before reading analysis/correspondence/ExecutiveCase caches. Separately, enterprise and decision memory are queried by `company_id`, not `entity_id`, so a multi-client professional's contexts can be mixed before external inference.

The current implementation cannot defend the public claims that identifying and sensitive information is removed before every AI call, that only necessary information is sent, that AI never knows real client/supplier/collaborator identity, or that each client has isolated contextual memory.

**Security disposition:** real-client use remains blocked pending a remediation contract and corrective implementation.

## 2. Current outbound-call map

All identified AI calls use the Anthropic Python client and Claude models. No OpenAI or other model-provider execution path was found on canonical main.

| ID | Caller / trigger | Model | Outbound information | Protection before call | Fallback / retry | Verdict |
|---|---|---|---|---|---|---|
| P1 | `run_full_pipeline` → `classify_document`; every accepted file analysis | Haiku | First 5,000 chars of structured `parsed_data` | Receives `anonymized_data` | No retry; parse fallback returns `AUTRE` | **SAFE WITH DOCUMENTED RESIDUAL DISCLOSURE** |
| P2 | Evidence Graph; every file analysis | Sonnet | First 10,000 chars of structured data, values, captions, sheet manifest | Receives `anonymized_data` | Exception returns `{}` and pipeline continues | **SAFE WITH DOCUMENTED RESIDUAL DISCLOSURE** |
| P3 | Financial Analyst pre-pass; only when `USE_ENHANCED_PIPELINE=true` | Selected Sonnet/Opus | First 8,000 chars of structured data | Receives `anonymized_data` | Exception returns `{}` | **SAFE WITH DOCUMENTED RESIDUAL DISCLOSURE** |
| P4 | Strategic CFO pre-pass; enhanced pipeline only | Sonnet | Up to 3,000 chars of P3 findings | Derived from pseudonymized source, but model output may contain contextual detail | Exception returns `{}` | **SAFE WITH DOCUMENTED RESIDUAL DISCLOSURE** |
| P5 | Main analysis Call 1; every file analysis | Sonnet or Opus | Up to 14,000 chars of pseudonymized source data **plus raw profile, relationship, enterprise memory, decision/action memory, quality, evidence and optional pre-analysis** | Only file-derived `parsed_data` is pseudonymized | Repeated with Opus if score < 8 | **UNSAFE FOR REAL CLIENT DATA** |
| P6 | Verification Call 2; every file analysis | Same model as P5 | Up to 6,000 chars source data, full P5 analysis, evidence audit and enhanced CFO decisions | Source data is pseudonymized; P5 output is not re-scrubbed | Repeated with Opus if score < 8 | **UNSAFE FOR REAL CLIENT DATA** |
| P7 | `_score_analysis`; once per verification and again after escalation | Haiku | First 2,000 chars of verified analysis | No egress scrub | Failure silently returns score 7 | **CONTRADICTS PRODUCT PROMISE** when upstream text contains identity/context |
| P8 | `/api/analyze/text`; user submits text-only question | Haiku | Raw `request.query` | None | HTTP 500 on provider error | **UNSAFE FOR REAL CLIENT DATA** if client context is entered |
| P9 | `/api/chat` legacy fallback | Sonnet | Up to 3,000 chars analysis context, history and current message | Conditional `anonymize_text` only when a non-empty cached table exists | Chosen when V2 case unavailable | **AMBIGUOUS / FAIL-OPEN** |
| P10 | `/api/chat` preferred Conversation Engine V2 | Sonnet | Selected re-identified narratives; exact financial snapshot, cost of inaction/value at risk/opportunity; glossary/role context; history and message | Message/history conditionally pseudonymized; V2 projection is not | Falls back to P9 if V2 build fails | **UNSAFE FOR REAL CLIENT DATA** |
| P11 | First uncached PDF or PPTX export → Executive Case Builder | Opus | Explicit real company name, scores, exact financial impacts, diagnosis, risks, decisions, owners/status/dates, roadmap, scenarios and quality context | None; source is the persisted/re-identified analysis result | On any error, pure-Python mapper succeeds without LLM | **UNSAFE FOR REAL CLIENT DATA** |

### Non-LLM product surfaces checked

- Excel rendering does not call an external model.
- PDF/PPTX rendering is deterministic after the V1 Executive Case exists; only its lazy construction P11 is model-backed.
- Portfolio and Review Briefing routes use deterministic services and contain no provider call.
- DecisionArc, Evidence query, Knowledge, FTE, Observation, Doctrine and Epistemic Dialogue v0 services inspected by existing architecture tests are not provider callers.

Non-AI third-party egress such as CRM/Airtable is not part of this boundary and is explicitly deferred, even though it merits a separate data-egress review.

## 3. Data classification

| Class | Examples in current paths | Identification / sensitivity property |
|---|---|---|
| D1 Direct personal identifiers | Names, email, phone, address, employee/contact names, IBAN, VAT/company numbers | Directly identifies a natural person or account; some values are credential-adjacent or fraud-sensitive. |
| D2 Organization identifiers | Company, client, supplier, subsidiary names; file/sheet labels that name an organization | Directly identifies the enterprise or its counterparties. |
| D3 Client-specific operational context | Sector, business model, relationship type, subsidiary/group role, recurring problems | May identify by description or materially reveal business operations. |
| D4 Financial facts | Revenue, costs, margins, EBITDA, cash, debt, periods and trends | Commercially sensitive; often linkable when combined with D2/D3, dates or public accounts. |
| D5 Management free text | Uploaded notes, user questions, reasons/comments, diagnoses | Unbounded; can contain D1–D4, strategy, disputes, health/employment or other special-category information. |
| D6 Enterprise memory | Prior metrics, financial profile, recurring problems, pending actions | Longitudinal and more identifying than a single snapshot; can expose other engagements under current company scope. |
| D7 Decision/action history | Recommendation text, status, rejection reason, owner, due/review dates | Reveals management intent, performance and governance behavior. |
| D8 Credentials/secrets | API keys, auth tokens, passwords | Must never cross. No path intentionally includes them, but no universal outbound secret scanner exists. |
| D9 Pseudonymous identifiers | `CLIENT_001`, `FOURNISSEUR_001`, analysis UUID | Not anonymous in the strict sense; linkage within a payload/session remains possible. |
| D10 Combination-identifiable data | Exact financial series + sector + geography/context + dates | Can identify an enterprise without a direct name; current Layer 1 does not mitigate this. |

The current mechanism is therefore **pseudonymization of recognized values**, not comprehensive anonymization of financial content.

## 4. Exact anonymization and re-identification lifecycle

### File analysis

1. The uploaded file is parsed in memory into `parsed_data`.
2. `anonymize_parsed_data(parsed_data)` deep-copies the structure.
3. It recognizes sensitive columns by a fixed French/English keyword list, registers string values of at least three characters, detects email/IBAN/VAT patterns globally, then recursively substitutes known values in **values**.
4. The correspondence table stays in process memory. It is not included in core LLM payload construction.
5. `anonymized_data` goes to P1–P6, but P5 separately appends unprocessed context from Supabase/profile/form inputs.
6. Provider output is parsed.
7. `deanonymize_recursive` restores recognized aliases inside `analysis_result` **after core external inference**. This ordering is correct for the core file-derived payload.
8. The restored result is placed in `_analysis_result_cache` and persisted.
9. The correspondence table is cached only if non-empty.
10. Later chat/export paths use the restored result, but do not reapply the boundary consistently.
11. Raw file bytes are explicitly deleted only after the LLM pipeline and Excel generation. They are not sent as raw bytes, but the public statement that source files are deleted before sending anything to AI is not true of execution timing.

### Recognition limits

- Column-name rules do not detect arbitrary names in unclassified free text.
- Free-text regex detection covers email, IBAN and VAT-like identifiers, not arbitrary person/organization names, phones or addresses.
- Dictionary keys are not classified/substituted; values are.
- New free-text identifiers are only protected when `anonymize_text` is actually called.
- No transformation reduces exact financial-series uniqueness or combination-identification risk.

## 5. Conversation Engine V2 finding

### Corrected claim

Mission 3 was directionally correct but **overstated payload breadth** by describing a complete re-identified dossier.

The V2 builder receives `analysis_result.model_dump()` after re-identification and constructs an `ExecutiveCase V2` that includes metadata, quality, summary, scores, performance, snapshot, drivers, decisions and methodology. However, `conversation_engine._build_system_prompt()` selects only:

- plain-language narrative context;
- three decisions/actions;
- exact cost of inaction, value at risk and opportunity;
- revenue, EBITDA and gross margin when available;
- core problem, strategic risk and recommendation;
- glossary and role instructions.

It does **not** directly serialize the complete object and does not insert `metadata.company_name` or `analysis_id` into the provider payload.

### Why the blocker remains confirmed

- The selected narrative fields originate from the already re-identified result. If Call 1/2 produced an alias that was restored to a client, supplier, employee or organization name, the selected narrative can carry that real value to P10.
- Exact financial values and decision context are intentionally sent and may identify the entity through combination.
- The V2 projection bypasses `anonymize_text`; only the user message and history are conditionally processed.
- The route silently proceeds without a table when the cache is absent/empty.
- A server restart or different worker loses the in-memory table while persisted/re-identified analysis data can remain available elsewhere.
- The route does not call `_verify_export_access(analysis_id, company_id)` before using its caches. This is a confirmed authorization omission at the chat boundary, even though exploitation would also require knowledge/guessing of an analysis UUID and relevant in-process state.
- The logger records the first 60 characters of `user_message`. When protection was skipped, direct identifiers can enter application logs.

This behavior appears accidental/architecturally omitted rather than a documented exception: comments claim chat confidentiality, while the V2 case was added as a separate preferred route without applying the same table to its system context.

## 6. Main analysis pipeline findings

### Sound portions

- P1/P2 and optional P3 consume `anonymized_data`, not raw `parsed_data`.
- P4 consumes P3's derived findings.
- Core output re-identification occurs after P1–P7 external inference.
- The correspondence table itself is not serialized into these prompts.
- No prompt/payload logging was found in the primary pipeline.

### Unsafe mixed-context portion

P5 combines protected file-derived data with these unprotected sources:

- `industry` and `business_model` from the company profile;
- `relation_section`, containing the real entity name from an `entities` lookup;
- `memory_section`, containing company-wide prior financial metrics, narrative summaries, recurring problems, actions and decisions;
- `actions_section`, containing prior recommendation text, user status and free-text reasons/comments;
- raw form `context` can flow into the `industry` fallback when profile industry is absent.

P5 can therefore disclose D1–D7 despite correctly pseudonymizing the uploaded file.

P6 receives P5's generated analysis and can propagate any resulting identity/context. It does not receive the three raw sections as separate parameters; that nuance corrects the older audit wording. P7 then receives the first 2,000 characters of the verified text. A low score repeats P5/P6/P7 through Opus, multiplying disclosure rather than bypassing it via a different sanitizer.

### Cross-client context

Both `MemoryService.get_memory_context()` and `DecisionMemoryService` query by `company_id`. They do not scope by `entity_id` or Engagement. A Fractional CFO account managing several clients can therefore inject one client's historic metrics, recommendations or comments into another client's analysis prompt. This contradicts the product statement that each client has its own contextual memory.

The relationship lookup also accepts the submitted `entity_id` without an observed `company_id` ownership predicate before placing its name in P5. This must be closed or conclusively guarded by an earlier invariant; no earlier ownership validation was found in the analyze route.

## 7. Promise-versus-implementation matrix

| Current representation | Implementation evidence | Result |
|---|---|---|
| Identifying information is removed before AI treatment | File-derived recognized values are replaced, but P5, P8, P10 and P11 send unsanitized/re-identified context | **Contradicted** |
| Filtering/anonymization/rationalization occurs before every AI call | No common mandatory boundary; several direct `client.messages.create` sites | **Contradicted** |
| AI never knows real client, supplier or collaborator identity | P5 relation/memory/action context, P10 restored narratives, P11 explicit company name | **Contradicted** |
| Only information necessary for the task is sent | P5 includes broad company memory; P10 includes a large fixed context per turn; P11 uses Opus despite a working pure-Python fallback | **Not defensible** |
| Each client has isolated history/context/memory | Memory is company-scoped and chat lacks explicit analysis ownership verification | **Contradicted for multi-client accounts** |
| Correspondence table is stored in a secure user space | It is only an in-process dictionary keyed by analysis UUID | **Overstated / contradicted** |
| Raw source files are not sent directly to models | Parsed structured projections, not raw file bytes, are sent | **Supported** |
| Source file is deleted before anything is sent to AI | `del file_bytes` occurs after the LLM pipeline | **Contradicted as timing**, although raw bytes are not passed to Anthropic |
| Provider does not retain activity beyond request processing | Repository has no zero-retention option, contract, account setting or attestation | **Unknown / externally governed** |
| API data is not used to train public models | Product copy attributes this to provider policy; no repository enforcement | **Contractual claim requiring current provider/account evidence** |

The strongest currently defensible statement is narrow: **Pepperyn parses files locally/in process and pseudonymizes recognized identifiers in structured file-derived values before the core analysis calls; it does not send the raw file bytes to Anthropic. Coverage is not universal across contextual, chat and export-time calls.**

## 8. Concrete unsafe or ambiguous paths

### Confirmed unsafe

1. P5 raw relationship, enterprise-memory and decision-memory injection.
2. P5 multi-client memory mixing by `company_id`.
3. P6/P7 propagation of P5-produced identifying/contextual text.
4. P8 verbatim text query.
5. P10 re-identified narrative projection and exact financial context.
6. P11 explicit company identity plus restored executive/financial/decision data.
7. Missing explicit ownership verification in `/api/chat`; missing entity-company predicate in analysis relationship lookup.

### Ambiguous / fail-open

1. P9 conditional protection disappears when correspondence cache is missing/empty.
2. Free-text names not previously registered are not detected.
3. Combination-identification from exact financial series is neither measured nor transformed.
4. Provider retention, regional processing, subprocessors and account-level zero-retention controls are not evidenced in the repository.
5. Environment-dependent enhanced pipeline adds P3/P4 calls; the repository does not establish the production value of `USE_ENHANCED_PIPELINE`.

## 9. Minimum-necessary-disclosure findings

| Data/context | Necessity for stated task | Finding |
|---|---|---|
| Financial structure and relevant values for analysis | **REQUIRED / PROBABLY REQUIRED** | Exactness may be needed for arithmetic and materiality, but each call should receive only its task subset. |
| Direct person/client/supplier names | **UNNECESSARY** for current analysis/chat/export tasks | Aliases preserve reference consistency. |
| Real company name in P11 | **UNNECESSARY** for reasoning and rendering | Cover branding can be applied locally after inference; pure-Python fallback proves external inference is not required to render. |
| Entire prior enterprise memory in every analysis | **UNKNOWN / OVER-BROAD** | Relevant, entity-scoped facts may help continuity; company-wide narrative/history is not justified. |
| User feedback/rejection comments | **PROBABLY REQUIRED only for a specific continuity task** | Must be entity-scoped, minimized and scrubbed; not a default global context. |
| Full P5 analysis in verification | **PROBABLY REQUIRED** | Verification needs the claim set, but identity is not needed. |
| Full V2 fixed context on every chat turn | **OPTIONAL / OVER-BROAD** | Retrieve the minimal relevant slice per question or at least scrub/minimize the fixed projection. |
| Exact financial values in V2 chat | **PROBABLY REQUIRED for numeric questions; OPTIONAL otherwise** | Task-aware disclosure could reduce unnecessary exposure. |
| Executive Case Opus restructuring | **UNNECESSARY for basic export correctness** | Deterministic fallback already exists; generative narratives could be a separately governed optional enhancement. |

Residual financial exposure is not inherently unavoidable in its current breadth. Exact values can be necessary for calculation, but the architecture can reduce exposure through task-specific projections, local deterministic calculation, ranges/derived metrics where exactness is not needed, and exclusion of identity and irrelevant history. Provider contractual/privacy controls remain material defense-in-depth, not a substitute for minimization.

## 10. Threat and falsification findings

| Failure case | Result |
|---|---|
| Direct identifier leakage from recognized file columns | Core Layer 1 resists it; exact/substring and global email/IBAN/VAT substitution are sound within scope. |
| Organization-name leakage | Confirmed through P5 relation context and P11; possible through P10 restored narrative. |
| Free-text identifier leakage | Confirmed for P5 comments/context and P8; P9/P10 fail open without table and do not recognize arbitrary new names. |
| Memory re-identification | Confirmed: memory is never passed through the file correspondence table before P5. |
| Prompt reconstruction of identity | Confirmed possible through combined D3/D4/D6 even where names are replaced. |
| Retry/fallback bypass | Opus retry repeats P5 disclosure; legacy-chat fallback has weaker conditional protection. |
| Alternate chat bypass | Confirmed: P9 and P10 have different boundary behavior. |
| Logs containing client content | P10 logs first 60 characters of the effective user message; raw when protection skipped. Core pipeline payloads were not found in logs. |
| Structured fields overlooked | Fixed column vocabulary and value-only traversal leave arbitrary free-text names and combination identifiers. |
| Cross-client context leakage | Confirmed at prompt construction by company-scoped memory; chat authorization omission adds a second risk. |
| Re-identification at wrong boundary | Correct after core analysis, wrong for downstream P10/P11 because restored outputs re-cross externally. |
| Provider receives more than necessary | Confirmed for P11; strongly indicated for P5/P10. |
| Tests pass while boundary is unsafe | Confirmed structurally: EDX/model tests cover mapping/render behavior, while no test captures actual outbound payloads or enforces a universal boundary. |

No credentials/secrets were printed or found intentionally included in a model payload. Absence of a universal secret scanner remains a defense-in-depth gap, not evidence of current secret leakage.

## 11. Existing test coverage

### Present and useful

- Cognitive deterministic services have static dependency tests proving no Anthropic/OpenAI coupling.
- EDX tests exercise Executive Case mapping and rendering behavior.
- Conversation Engine contains a local synthetic payload self-test.
- Anonymization implementation is deterministic and directly inspectable.
- Export ownership checks exist for PDF/PPTX/download endpoints.

### Missing at the trust boundary

- No tracked test was found for `anonymization_service.py` behavior.
- No test intercepts every `client.messages.create` call and asserts the exact outbound payload.
- No negative test injects sentinel person/company/client names through file, relation, memory, decision comments, chat and export.
- No restart/missing-table/multi-worker fail-closed test exists.
- No route test proves `/api/chat` analysis ownership or entity ownership in `/api/analyze`.
- No test proves entity/Engagement-scoped memory isolation.
- No static test forbids direct provider calls outside one approved egress component.
- No test checks logs for raw sentinel values.
- Existing EDX tests can pass through deterministic/fallback paths without proving P11 safe.

Full-suite execution was deliberately omitted: it would not answer these missing-boundary questions and Phase 1 authorized cheap targeted inspection only.

## 12. Candidate security invariants

These are proposed for architecture/Founder review, not yet canonical:

1. Every external model call must pass through one enforceable egress authority; production modules may not instantiate/import provider clients directly elsewhere.
2. No D1/D2 value crosses external inference unless a versioned task contract declares it strictly required and Founder/security review approves that exception.
3. Re-identification occurs only inside Pepperyn after the **last** external inference that consumes that datum.
4. A restored result must be treated as unsafe for re-egress until a fresh outbound projection and policy validation pass.
5. Missing correspondence/provenance/policy authority fails closed; restart, cache miss or fallback cannot silently weaken protection.
6. Retry, escalation and fallback routes inherit the exact same disclosure contract as the primary route.
7. Every `analysis_id`, `entity_id` and Engagement context is authorized against the authenticated company before cache/DB read or model egress.
8. Enterprise memory and decision history are entity/Engagement-scoped for client work; cross-entity context requires an explicit portfolio-purpose contract and aggregation policy.
9. Each call receives the minimum task-specific projection; optional history and exact values are omitted unless required.
10. Raw user free text is classified/scrubbed or explicitly blocked before model egress; arbitrary names cannot rely solely on a fixed column vocabulary.
11. Tests assert captured outbound payloads and logs with synthetic sentinels, not merely that an anonymization function exists.
12. Pseudonymization, provider contractual controls and financial-data minimization are separate defenses; none may be represented as full anonymity by itself.

## 13. Smallest ordered implementation slices

### Slice 0 — Contract and executable egress inventory

- **Boundary:** all P1–P11 direct Anthropic call sites.
- **Likely files:** new narrow trust/egress policy component; `llm_service.py`, `conversation_engine.py`, `executive_case_builder.py`, `routers/analyze.py`; security tests.
- **Test:** static allow-list plus captured payload registry; build fails on an unregistered direct call.
- **Risk:** overbuilding a generic security platform.
- **Contract first:** **required**.

### Slice 1 — Authorization and client-context isolation before egress

- **Boundary:** `/api/analyze` entity lookup, `/api/chat` analysis lookup, memory and decision-memory selection.
- **Likely files:** `routers/analyze.py`, `memory_service.py`, `decision_memory_service.py`, focused route/service tests.
- **Test:** foreign analysis/entity rejected; Client A sentinel never appears in Client B prompt; cache hit/miss parity.
- **Risk:** legacy histories may lack entity/Engagement attribution and need honest omission rather than heuristic assignment.
- **Contract first:** yes, especially legacy-memory behavior.

### Slice 2 — Main pipeline mixed-context closure

- **Boundary:** P5–P7 including Opus escalation.
- **Likely files:** egress projection/policy component, prompt builders/call wrappers, relation/memory/action producers.
- **Test:** synthetic D1–D7 sentinels absent or approved aliases in captured P5/P6/P7 and retry payloads; financial semantics unchanged.
- **Risk:** loss of continuity/context if fields are simply dropped.
- **Contract first:** yes; define minimum task fields.

### Slice 3 — Chat fail-closed closure

- **Boundary:** P9/P10, table lifecycle and logging.
- **Likely files:** `routers/analyze.py`, `conversation_engine.py`, persistent/authoritative correspondence access selected by contract, chat tests.
- **Test:** V2 and legacy paths, restart/missing table, new free-text identity, history, logs, fallback and foreign analysis ID.
- **Risk:** chat temporarily unavailable for old analyses; preferable to silent disclosure, but migration/user behavior needs a decision.
- **Contract first:** yes.

### Slice 4 — Export-time Opus elimination or governed minimization

- **Boundary:** P11.
- **Likely files:** `executive_case_builder.py`, export orchestration and EDX tests.
- **Preferred smallest option:** use the already implemented deterministic mapper for export construction; keep any generative narrative enhancement separate and opt-in only if later justified.
- **Test:** PDF/PPTX generation makes zero provider calls and remains semantically/regressively equivalent where required.
- **Risk:** narrative/output differences against current golden exports.
- **Contract first:** compare deterministic output requirements before removal.

### Slice 5 — Text-only endpoint truth boundary

- **Boundary:** P8.
- **Likely files:** `routers/analyze.py`, common egress policy and endpoint tests.
- **Test:** raw identifiers/secrets rejected or transformed; product wording matches actual scope.
- **Risk:** false positives in unconstrained user text.
- **Contract first:** Founder/product decision on supported use.

Provider-contract verification and truthful copy correction follow technical proof; copy must not be weakened as a substitute for remediation.

## 14. Founder decisions required after evidence

The following decisions are now sufficiently evidenced for later arbitration:

1. **Export P11:** remove the Opus restructuring call in favor of deterministic mapping, or retain a separately governed optional narrative task with a minimized payload. Recommendation: remove it from the default export path.
2. **Legacy analyses after cache loss:** block chat until protected context can be reconstructed, or provide a context-free mode. Recommendation: fail closed; never silently send restored context.
3. **Text-only P8:** prohibit client-specific data, add a governed scrubber, or retire the endpoint from real-client workflows.
4. **Financial residual disclosure:** approve a task-by-task policy defining which exact values are necessary. Do not issue a blanket acceptance of pseudonymous financial exposure.
5. **Provider assurance:** obtain current account/contract evidence for training, retention, logging, region and subprocessors before making those claims. This is defense-in-depth and does not waive code minimization.
6. **Legacy memory attribution:** omit unscoped legacy memory or fund a deterministic migration; never heuristically attach it to a client.

No super-admin identity decision is required for this LLM boundary. Platform administration remains out of scope.

## 15. Explicitly deferred security topics

- General Control Center/RBAC and Founder identity.
- Full authentication and session audit beyond IDs used immediately before LLM egress.
- Supabase RLS review outside the contextual queries identified here.
- Non-AI third-party egress, including CRM/Airtable, analytics and billing providers.
- Infrastructure penetration testing, deployment hardening, secret rotation and provider configuration changes.
- Enterprise security, private deployment, data residency and certifications.
- Broad privacy-policy/legal review beyond contradictions directly supported by current code.
- Portfolio Attention and all unrelated product development.

---

**Phase 1 control decision:** the blocker is confirmed. A bounded remediation contract is required before production behavior changes or real-client field use begins.
