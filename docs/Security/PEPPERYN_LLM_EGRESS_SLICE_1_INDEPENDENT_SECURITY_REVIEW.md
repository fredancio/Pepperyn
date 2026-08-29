# PEPPERYN — LLM EGRESS TRUST GATE — SLICE 1 INDEPENDENT SECURITY REVIEW

**Review date:** 2026-08-29  
**Original implementation commit:** `b21cfa2fe96cba166332561519f3743cf5bbfca2`  
**Final reviewed implementation commit:** `dfdf6b98b3a8572760828a39e682ef7a78b2f624`  
**Branch:** `work/llm-egress-trust-gate-slice-1`  
**Contract:** `PEPPERYN_LLM_EGRESS_TRUST_GATE_REMEDIATION_CONTRACT_V1.md`  
**Founder arbitration:** F1–F7 authoritative  
**Review mode:** independent adversarial promotion review; synthetic sentinels only; no live provider call

## A. Review target and independence

The review began from the exact clean target commit `b21cfa2`. The independent reviewer ran in the separate `slice1_promotion_review` context, distinct from the implementation context. Its objective was to falsify claims C1–C15, not to confirm the implementation report. The reviewer made no repository changes.

Three bounded corrective commits were produced by the implementation context after independent failures:

1. `a7416b982358459fc1a55e5a21b4a002eb174f36` — preserve provider taint and widen bypass detection;
2. `72669399c73b7089d342cb27d4c88090b586a39a` — retain structured provider provenance;
3. `dfdf6b98b3a8572760828a39e682ef7a78b2f624` — make provider derivations opaque and close remaining process-launch scanner vectors.

Each correction remained inside Slice 1. No Slice 2 capability, ownership resolver, correspondence store, provider configuration or real-data admission was implemented.

## B. Methods

- whole-tree source and AST inspection for SDK, raw HTTP, provider host/key, dynamic import, process/CLI and legacy fallback mechanisms;
- exact P1–P11 reconciliation against the Phase 1 discovery inventory;
- synthetic capture at the final serialized boundary;
- mutation, retry, logging, re-identified input and hostile provider-output probes;
- ordinary and lazy export-path inspection;
- route and internal-call inspection for `/api/analyze/text`;
- targeted authority suite, complete backend suite and standalone legacy model test;
- repeated independent falsification after every corrective cycle;
- Git diff, status and whitespace checks.

The static scanner is a regression defense, not a claim that arbitrary malicious Python is mathematically impossible. The stronger positive Slice 1 boundary is that production transport is closed, provider credentials are not read, legacy production requests cannot mint admission and the sole final dispatch function refuses.

## C. P1–P11 path inventory

| Path | Historical function | Final classification | Evidence |
|---|---|---|---|
| P1 | Document classification | **MIGRATED** | `DOCUMENT_CLASSIFICATION` enters the closed authority. |
| P2 | Evidence Graph | **MIGRATED** | `EVIDENCE_EXTRACTION` enters the authority; parsed output becomes opaque provider-derived data. |
| P3 | Financial Analyst pre-pass | **MIGRATED** | `FINANCIAL_PREPASS` enters the authority; structured output cannot enter P4/P5. |
| P4 | Strategic CFO pre-pass | **MIGRATED** | `STRATEGIC_PREPASS` enters the authority; P3-derived input is rejected. |
| P5 | Main analysis Call 1 | **MIGRATED** | `FINANCIAL_ANALYSIS` enters the authority; every provider-bound input is checked before prompt construction. |
| P6 | Verification Call 2 | **MIGRATED** | `ANALYSIS_VERIFICATION` enters the authority; P5/provider-derived input is refused. |
| P7 | Analysis quality score | **MIGRATED** | `ANALYSIS_QUALITY_SCORE` enters the authority; provider-derived analysis is refused before formatting. |
| P8 | `/api/analyze/text` | **DISABLED** | Authenticated route returns HTTP 410 and has no model dispatch or compatibility alias. |
| P9 | Legacy analysis chat | **MIGRATED** | `ANALYSIS_CHAT` enters the closed authority; provider-derived analysis context is refused. |
| P10 | Conversation Engine V2 | **MIGRATED** | `ANALYSIS_CHAT` enters the same authority; content-prefix logging was removed. |
| P11 | Lazy Executive Case Builder for PDF/PPTX | **DETERMINISTICALLY ELIMINATED** | Opus import/call and fallback-to-provider path were removed; Python mapping is unconditional. |

No path is missed or ambiguous. No P11 provider path remains to migrate.

## D. C1–C15 verdicts

| Claim | Verdict | Basis |
|---|---|---|
| C1–C5 | **SUPPORTED** | All current model paths are accounted for and P1–P7/P9–P10 terminate at one closed authority; no current bypass found. |
| C6 | **SUPPORTED** | P8 is unavailable through HTTP 410 and has no alternate internal model path. |
| C7 | **SUPPORTED** | P11 is removed; ordinary and lazy PDF/PPTX rendering perform zero model dispatch. |
| C8 | **SUPPORTED** | Production final transport always refuses; this is not an environment convention. |
| C9 | **SUPPORTED FOR SLICE 1** | Caller metadata cannot open the production boundary; only the test mint can create synthetic admission and production use is statically forbidden. |
| C10 | **SUPPORTED** | Canonical JSON bytes and hash are created once immediately before the sole boundary. |
| C11 | **SUPPORTED** | Retry reuses the identical frozen request bytes and hash. |
| C12 | **SUPPORTED** | Provider text and parsed JSON are opaque non-native values; implicit conversion, formatting, indexing, slicing, concatenation, arithmetic and truth testing fail. No authorized extraction exists in Slice 1. |
| C13 | **SUPPORTED** | Success, retry and refusal logs contain task/hash/attempt metadata, not payload or response content. |
| C14 | **SUPPORTED** | Authority contains validation, canonicalization, freeze/retry and boundary mechanics only; no financial reasoning, retrieval or domain decision. |
| C15 | **SUPPORTED** | Passing count increased only with security tests; exact failure inventory remained unchanged. |

## E. Executable evidence

### Final authority/security suite

`33 passed`

Coverage includes:

- exact final canonical body capture;
- immutable bytes/hash across retries;
- production transport and admission fail closed;
- re-identified input refusal;
- invalid canonical JSON refusal;
- metadata-only logs;
- opaque hostile provider output and structured JSON derivation;
- P2/P3/P4/P5/P6/P7 re-egress refusal;
- deterministic export and P8 retirement;
- repository-wide provider bypass scan;
- negative fixtures for SDK, HTTP, dynamic import, credential, synchronous/asynchronous subprocess, `getattr` and `os.spawn*` forms;
- content hashes pinning the unrelated CRM `httpx` and file-parser `subprocess` exceptions.

### Backend regression

**Before Slice 1:** `1387 passed / 12 failed / 50 skipped / 3 warnings`  
**Original Slice 1:** `1401 passed / 12 failed / 50 skipped / 3 warnings`  
**Final reviewed implementation:** `1420 passed / 12 failed / 50 skipped / 3 warnings`

The exact same twelve node IDs remained:

1. `test_edx_002.py::test_pptx_generates_without_edx002_shows_methodology`
2. `test_edx_002.py::test_pptx_has_17_slides_with_edx002`
3. `test_rule_001_zero_manual_intervention.py::TestEDMSourceValues::test_edm_source_values`
4. `test_rule_001_zero_manual_intervention.py::TestPDFContent::test_pdf_required_tokens_present`
5. `test_rule_001_zero_manual_intervention.py::TestPDFContent::test_pdf_no_forbidden_tokens`
6. `test_rule_001_zero_manual_intervention.py::TestPPTXContent::test_pptx_has_20_slides`
7. `test_rule_002_zero_truncation.py::TestNoContentSlicesInSource::test_no_content_slices_in_pptx_renderer`
8. `test_rule_002_zero_truncation.py::TestNoContentSlicesInSource::test_no_content_slices_in_pdf_renderer`
9. `test_rule_002_zero_truncation.py::TestPDFCompleteness::test_all_decisions_complete_in_pdf`
10. `test_rule_002_zero_truncation.py::TestPDFCompleteness::test_all_destroyers_complete_in_pdf`
11. `test_rule_003_renderer_responsibility.py::TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`
12. `test_rule_003_renderer_responsibility.py::TestRendererSelfContainment::test_pptx_handles_extreme_text_length`

Classification: all twelve are **KNOWN PRE-EXISTING / UNRELATED** to the egress boundary. They concern established PPTX slide-count/content expectations, EDM financial sign/source expectations, PDF content extraction (including unavailable `pdftotext` in this runtime), and renderer completeness. None invokes the removed P11 provider path, the authority, synthetic admission, retry or output-taint code. They do not mask a Slice 1 security regression.

### Standalone legacy model

`89 OK / 4 FAIL`

The four failures are pre-existing cost-of-inaction/scenario numeric expectation differences. They execute deterministic Executive Decision Model calculations and do not exercise provider dispatch, credentials, admission, payload serialization or output provenance. Classification: **KNOWN PRE-EXISTING / UNRELATED**.

## F. Findings and corrections

### Initial independent result — FAIL

1. **S2:** compatibility adapter erased `UNTRUSTED_PROVIDER_OUTPUT` typing.
2. **S2:** bypass scanner covered only selected model modules and syntaxes.
3. **S3:** test admission/minter are Python-private rather than cryptographic capabilities.

### First correction and re-review — FAIL

- Added text taint and direct P5→P6/P7/chat guards.
- Expanded scanning repository-wide and added negative fixtures.
- Re-review demonstrated taint laundering through regex/JSON/native operations and remaining static process forms.

### Second correction and re-review — FAIL

- Marked structured JSON and guarded known P2/P3/P4/classification chains.
- Pinned unrelated networking/process modules and expanded scanner forms.
- Re-review demonstrated that subclasses of native values could still lose provenance through ordinary transformations.

### Final correction and re-review — PASS

- Replaced native subclasses with opaque provider-derived values that reject implicit native operations.
- Removed all Slice 1 extraction paths.
- Added hostile structured-output and transformation-laundering tests.
- Added remaining asynchronous/dynamic/`os.spawn*` process probes.
- Final independent review found no S0, S1 or S2.

## G. Remaining S3 and later-slice limitations

### S3 — synthetic test authority is private by convention

The test admission token, mint and final function remain Python-private rather than cryptographically unforgeable. This is non-blocking because production transport is closed, no provider credential is read and current production use of the mint is statically prohibited. Before any real transport is introduced, Slice 2 must replace this mechanism with resolver-minted, integrity-protected, expiring, scoped and single-use capabilities.

The following remain correctly assigned to later slices and were not treated as Slice 1 defects:

- real provenance and value-bound receipts;
- ownership and protected-read capabilities;
- Entity/Engagement-scoped context and memory;
- durable encrypted correspondence;
- final task-specific minimization and bounded narrative policy;
- provider/account assurance and real-data admission;
- deployment-level provider network restriction.

## H. Architecture and promotion verdict

Slice 1 is a sound, non-misleading foundation for later controls:

- one public authority and one final closed dispatch boundary;
- no current external-model bypass;
- no provider credential accessible to production paths;
- immutable captured request bytes;
- fail-closed retries and admission;
- opaque provider output with no implicit re-egress;
- deterministic export and retired text-only endpoint;
- no cognition or context ownership inside the authority.

**Final promotion verdict: PASS — no S0/S1/S2 remains.**

SLICE 1 SECURITY REVIEW PASSED — ELIGIBLE FOR PROMOTION
