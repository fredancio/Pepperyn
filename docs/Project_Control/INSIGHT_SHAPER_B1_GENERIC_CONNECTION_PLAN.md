# B1 — minimal generic producer connection plan

2026-09-28. Repository assessment after the bounded V40 successor PASS.
B1 OPEN; generic producer UNADMITTED; External Provider and Real-data Admission
CLOSED. This plan creates no policy, admission, transport or remote write.

## Actual implementation, not an inferred producer

Three different components must not be conflated:

1. The historical general pipeline is services/llm_service.py:run_full_pipeline.
   It performs classification, evidence extraction, optional analyst/CFO passes,
   analysis, review and scoring/escalation, then returns AnalysisResult. Its
   dispatch_legacy_synthetic calls are deliberately closed. Its text parsing,
   optional context/memory and fallback result are not a GovernedAnalysisEnvelope
   or proof of source-grounded truth. Wiring that callable directly into V40
   would not establish task-specific privacy or governed producer-return binding.
2. services/v1_analysis_contract.py already has the structured financial-analysis
   request/parser, source facts, epistemic validation and envelope conversion.
   This is the reusable governed contract, not an admitted transport/producer.
   build_openai_request is not an egress grant; its generated nonce must not
   replace the request identity already bound by backend admission.
3. The only connected executor in governed_pipeline_mount is the exact registered
   sandbox mock. The V40 rehearsal uses another explicitly synthetic test profile.
   Neither becomes a generic producer by renaming or replacing its fixture guard.

## Available guarantees and exact missing joins

| Join | Reuse | Missing / limit |
| --- | --- | --- |
| Actor to source preparation | LocalProducerAdmissionPreparation; OwnershipAuthority; governed workbook ingestion | Current profile authorizes one named synthetic source hash; not general real-data admission |
| Preparation to durable execution | DurableProducerAdmission; V40 reserve/claim/complete; exact backend bindings | No registered actual producer selected and invoked by a trusted coordinator |
| Producer input to output | UnderstandingResult; GovernedFinancialAnalysis; envelope validator; quarantine primitives | Actual producer adapter must consume exactly claimed input and return only untrusted bounded content; no scope/identity/receipt authority |
| External task | Existing ownership, projection, provider policy and return capabilities | FINANCIAL_CHANGE_MINIMAL_V1 does not cover full analysis, classification, review or scoring; legacy chained provider output cannot be fed into another prompt implicitly |
| Durable output to reread | load_owned_analysis_context; immutable envelope validation | No V40 receipt/admission/policy reader or cross-version dispatch |
| Reread to terminal | governed_output and shared XLSX/PDF/PPTX renderers; memory and temporal loaders | Current receipt reader only consults V39; its verified labels explicitly mean registered synthetic local mock |
| Mount | Router factories with mandatory Auth/admission dependencies | Existing mount is a closed R5/mock rehearsal composition, not reusable permission for a new producer |

V40 hard-codes SYNTHETIC, DENY, local-synthetic-durable-admission-2 and
LOCAL_SYNTHETIC_ONLY. It can support a separately approved local synthetic
producer profile within that contract, but cannot truthfully certify an external
provider or real-data execution. Do not remove those labels/checks, reinterpret
the receipt, or treat its name/version fields as external-provider authorization.

## Minimal composition and order

No new general orchestration platform, IAM, registry framework or prompt engine.

1. Secure the accumulated V40 implementation and evidence in Git before changing
   their consumers. Keep the original failed run and all strategic exclusions.
2. Add a strict V40 receipt reader behind the existing owned-output service.
   Authenticate/resolve ownership first; resolve the exact receipt-bound
   engagement rather than silently choosing a different current engagement.
   Validate analysis/envelope/admission/policy/input/candidate digests and scope;
   require COMPLETE. A policy disabled after completion does not invalidate
   historical evidence, but can never authorize another execution.
3. Dispatch explicitly among verified V39, verified V40-local-synthetic and
   genuinely unattested legacy evidence. Two conflicting receipts, malformed or
   unknown versions, unavailable registry, missing required admission/envelope,
   or scope mismatch refuse; they do not downgrade to UNATTESTED or V39 fallback.
   Historical absence remains distinguishable from lookup failure. Use shared
   renderer metadata and frontend types, preserving the existing v1 labels.
4. Connect a backend-selected producer adapter to the existing reserve -> claim
   -> validation -> complete sequence, not to producer-owned persistence.
   Producer receives only the immutable task input and necessary correlation
   identity. It receives no DB client, Auth token, claim capability, policy
   registration or caller-controlled scope. Backend constructs the envelope and
   candidate from its own source snapshot; validates references/nonce/epistemic
   states; and persists once through the applicable atomic contract.
5. For actual external reasoning, first define the smallest analysis task's
   positive data-class/provenance/privacy contract and connect the existing
   projection/return mechanisms. Do not reactivate all historical LLM passes
   automatically. Preserve their intended capabilities in the corpus; explicitly
   assess which are necessary to the professional contract before claiming Beta
   completeness. Use injected responses only as local wiring tests, never as
   evidence of a real generic producer or financial reliability.
6. External/real-data execution requires a separately truthful receipt/policy
   version and its own approval, not a V40 flag change. Reuse V40's proven
   transition/atomicity pattern where applicable; review the minimum migration
   only when the admitted task/producer contract is fixed. No schema is proposed
   for application in this phase.

Expected authority chain:

`backend actor + owned scope + actual source -> admitted task/producer profile
-> durable reservation/claim -> bounded producer invocation -> quarantined output
-> backend validation/envelope -> atomic analysis + envelope + receipt
-> authenticated owned versioned reread -> same provenance in UI/XLSX/PDF/PPTX`

Producer output is evidence to validate, not authority for any arrow. Successful
serialization, model scores, a known hash or a COMPLETE state alone do not prove
professional correctness, allowed disclosure or admitted data origin.

## Acceptance, refusal and required evidence

| Accept condition | Refuse condition | Expected evidence |
| --- | --- | --- |
| Exact authenticated composition and consumed claim | Caller scope/profile/ID swap; replay; expired/closed admission; mixed valid components | No producer invocation and no result trio; existing evidence unchanged |
| Actual claimed input reaches selected versioned producer | Source mutation; different task/version/input; raw context added | Zero unauthorized invocation/egress and no misleading receipt |
| Output references exact source/request and passes governed validation | Unknown fact IDs; changed nonce; facts overwritten; malformed/contradictory output falsely resolved | Quarantine/refusal; no canonical promotion or durable result trio |
| Atomic validated result | Receipt/envelope mismatch or late SQL error | No partial trio; terminal refusal and no retry under substitute ID |
| Fresh owned versioned reread | Foreign actor/entity/engagement; unavailable/unknown/dual receipt; altered digests | Safe refusal, no leaked source/identity and no legacy fallback |
| Correct provenance in all outputs | V40 labeled V39 mock; candidate called generic-admitted; dropped lineage or epistemic qualification | UI and parsed XLSX/PDF/PPTX assertions plus v1 regression checks |
| Historical evidence remains stable | Disabled policy reused or failed history promoted | No new invocation; old hashes and original meanings unchanged |

Start with local fake repositories and isolated synthetic PostgreSQL for the
reader/adapter composition; no new remote row is needed to implement or falsify
those joins. Then test the real application boundary with the selected producer
only when its gates and explicit protocol permit it. Provider-independent local
tests cannot close external execution, FR-EXPECTED-2 or real-data Beta gates.

## Remote boundary and future protocol

No remote operation is needed for this assessment or local consumer preparation.
The existing V40 success row can later support a separately authorized GET-only
owned reread/export rehearsal, without new analyses, policies or admissions.
Its exact user, result UUID, permitted reads/exports, transport duration and
closure controls must be supplied in that future executable protocol; do not
reuse any closed R5 or V40 execution permit.

A genuine producer rehearsal needs its own fixed task/model/version, approved
data classes and privacy projection, input hashes and identities, effect/row
ceilings, provider configuration/PG status, no-retry rules and postchecks. These
are not yet established, so no executable remote-write protocol is READY and no
GO for an unspecified producer is requested. External use requires Provider Gate
approval even for synthetic inputs; real inputs independently require RD approval.

Completed local slice: strict version-aware V39/V40 owned reread and shared
terminal provenance. The exact receipt-bound engagement and V40 policy/admission/
candidate/source/envelope composition are validated before UI or XLSX/PDF/PPTX;
unknown, dual, incomplete, substituted or unavailable evidence refuses without
fallback. This is LOCAL_TESTED, not a live V40 output proof.

Next local slice: controlled backend producer-adapter composition using the
already governed claim and quarantine contracts. It must remain injected/local,
must not activate or admit the genuine generic producer, and must prove that the
producer receives no authority over scope, admission, identity or persistence.

## Durability preparation before consumer implementation

Checkpoint scope: 40 implementation/test/launcher files, then 15 Canon/control
documents, with the nine prior strategic/DEC-032/next-env exclusions preserved.
The script defaults to read-only checks; only explicit Founder execution can
stage the enumerated paths, verify exact staged blobs, commit and push normally.
No reset/restore/cleanup/configuration change or automatic recovery is permitted.
Raw working SHA-256 values are pinned. Staged blobs may differ only by the pinned
CRLF-to-LF representation; their actual IDs are then frozen for commit validation.

Preparation found one superfluous EOF blank line in the old, permanently failed
scripts/rehearse-v40-19.ps1. Only that trailing blank line was removed for Git's
whitespace check; no statement, pin, identity, retry rule or behavior was changed.
Original file SHA-256 BB89BD468CF41D06D948048ED47FDAE37C4B41F862F5EF9BC5BA1F2673677D37;
checkpoint copy SHA-256 2D4908AD54409B28784F899F5C9C6F56400467A98F820F90D220892A968779E8.
This does not modify/requalify runtime evidence or authorize that old launcher.
The executed successor wrapper and its 21 source/fixture/SQL pins remain intact.

Checkpoint validation: Windows PowerShell read-only mode PASS with 40 + 15 files,
nine preserved exclusions, empty index, exact HEAD and working hashes; zero Git
writes and no network. Targeted contract/composition/adapter/definition/process/
budget/launcher/successor regression: 178 PASS (8.07s), no cache provider, fresh
isolated temporary test directory. These are local tests; no cloud rehearsal,
Auth login or producer activation was repeated. Global egress debt remains OPEN.
