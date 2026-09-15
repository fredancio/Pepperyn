# Source inventory and authority

## Baseline inventory

At revision `6fb05c11394ce33423e81697a3dd13e9513e7794`, the repository contains:

- 89 Markdown documents under `docs/`;
- 15 Markdown documents at repository root;
- 34 SQL migrations;
- 72 backend `test_*.py` files;
- application code for backend and frontend;
- Git history carrying the recovery, synthetic rehearsal, privacy boundary,
  temporal, portfolio and provider-gate checkpoints.

The active document families are Foundation, Domain, Architecture, Product,
Security, Execution, Validation, Audit, Project Control, release evidence and
Archive. Existing inventories are authoritative evidence inputs, not replaced:

- `docs/Audit/DOCUMENT_AUTHORITY_INVENTORY.md`
- `docs/Audit/DOCUMENT_AUTHORITY_MAP.md`
- `docs/Audit/LEGACY_CAPABILITY_INVENTORY.md`
- `docs/Audit/LEGACY_CAPABILITY_REVIEW_MATRIX.md`
- `docs/Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md`
- `docs/Audit/CANONICAL_DOCS_STRUCTURE_PROPOSAL.md`

## Historical-corpus finding

The directive refers to approximately 27 inherited Cowork files. The current
repository contains a materially larger reconciled documentation corpus, but no
single manifest proves a one-to-one identity between those original 27 files
and current paths. Existing authority inventories group several historical
families rather than listing every file individually.

Therefore:

`ORIGINAL_27_FILE_SET = HISTORICALLY_REFERENCED / NOT YET BYTE-IDENTIFIED`

This does not block construction of the Canon from current evidence, but it is
a knowledge-preservation gap. It becomes material if any original source exists
outside Git or if a historical definition cannot be recovered from current
files/history.

## Known unresolved source conflict

The existing authority inventory records 18 divergent files between historical
`governance/mental-model-2026-08-05` and
`governance/foundation-closure-2026-08-05` lines. Their exact authority remains
`BLOCKED / UNRESOLVED`; this canon does not silently arbitrate them.

## Source-grounding rules

1. Capability claims require a source and an evidence grade.
2. `IMPLEMENTED` requires a current code or migration location.
3. `TESTED` requires an executable test location and result scope.
4. `LIVE_PROVEN` requires environment-bound rehearsal evidence.
5. Documentation-only claims remain `DOCUMENTED` or `DECIDED`.
6. Missing UI does not mean abandoned.
7. Deferred and rejected items retain their rationale.
8. A superseded implementation does not erase the historical decision path.

## Inventory work still required before broad Astra autonomy

- byte-identify or explicitly declare unavailable the original Cowork transfer
  set;
- enumerate root and archived historical files individually in the traceability
  dataset;
- reconcile the 18-file historical divergence without silent arbitration;
- bind infrastructure claims to current GitHub, Supabase, Vercel, Railway and
  OVH evidence;
- retain the executed OpenAI DPA as controlled evidence without committing
  unnecessary personal data to Git.
