# PEPPERYN — LLM EGRESS TRUST GATE — SLICE 2

**Status:** PASS — independently reviewed; no S0/S1/S2 remains

**Starting reviewed lineage:** `6aeb01f41924c38c946b2642384047a6c20435dd`

**Final reviewed implementation:** `1b7fe1fa4cfebe60c0d398e4f420704b07d1aa19`

**Final evidence HEAD:** `be95c426bcb4f0d5552e36d97a18b0153b7dbb48`

## Implemented boundary

- Ownership is resolved before protected chat/cache reads.
- Scope is the exact `company_id → entity_id → engagement_id → analysis_id` chain.
- Analysis/company, entity/company and engagement/entity coherence are verified; missing, conflicting or ambiguous scope fails closed.
- `ProtectedReadGrant`, projected read receipts, disclosure receipts and `EgressAuthorization` are issuer-, grant-, request-, resource- and scope-bound.
- Protected caches retain immutable original scope plus a deterministic canonical content hash; reads never relabel cache values from the current request.
- Projection is explicitly allow-listed. Every dynamic outbound leaf is bound to one exact destination path and a registered projected-read receipt. Key authorization is path-specific; duplicate values cannot cover an unrelated destination.
- Projected receipts, disclosure receipts and egress authorizations are single-use. Concurrent check/consume operations are lock-protected.
- Capability TTL is finite, positive and bounded to 300 seconds; expired/consumed registry state is pruned.
- Company-only and unattributed legacy memory and decision/action context are quarantined from external inference.
- `LlmEgressAuthority` rejects missing, invalid, copied, tampered, expired or replayed authorization before provider dispatch.
- Real-data/provider transport remains technically closed.

## Protected read boundary

The migrated chat path protects correspondence, analysis-result and ExecutiveCase V2 caches. Relationship lookup now proves company ownership and a unique current engagement before it may contribute context. Existing company-wide memory and decision-memory prompt injection was removed because the current records cannot prove entity/engagement attribution.

## Adversarial corrections

Independent review cycles found and caused correction of:

1. missing company/entity coherence;
2. retroactive cache self-labelling;
3. caller-declared rather than value-bound disclosure receipts;
4. non-atomic egress replay protection;
5. unbounded/non-finite TTL and registry retention;
6. existential rather than exhaustive payload coverage;
7. cross-authority/cross-grant receipt acceptance;
8. whole-object receipt semantics that discouraged minimum projection;
9. non-canonical `repr()` cache hashing;
10. `dataclasses.replace()` field-tampering bypasses;
11. value-set rather than destination-path coverage;
12. non-atomic projected/disclosure receipt consumption.

Final independent re-review concluded **PASS — no S0/S1/S2 remains**. The final concurrency test reviewed in the worktree is retained in evidence commit `be95c42`.

## Test evidence

- Combined Slice 1 + Slice 2 security/conformance: **71 passed**.
- Backend: **1458 passed / 12 failed / 50 skipped / 3 warnings**.
- The twelve backend failures are the exact historical unrelated renderer/EDM/PDF failures present before Slice 2.
- Standalone legacy executive-decision model: **89 OK / 4 FAIL**, unchanged.
- Compilation and `git diff --check`: pass (line-ending notices only).

## Known limitations and next gates

- No live or real-client provider transport is enabled.
- Durable correspondence lifecycle, terminal re-identification, real-data provenance, task policies/projection schemas, provider account controls and the explicit real-data admission capability remain later gates.
- Current entity→engagement resolution relies on the canonical present-day one-engagement-per-entity constraint. A future cardinality change requires explicit engagement selection.
- Python module privacy and architecture checks are in-process controls, not a cryptographic trust boundary against arbitrary code execution inside the same process.

**SLICE 2 SECURITY REVIEW PASSED**
