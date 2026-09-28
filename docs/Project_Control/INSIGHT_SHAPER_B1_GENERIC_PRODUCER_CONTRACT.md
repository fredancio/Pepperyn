# B1 — distinct governed producer contract

Status: local contract preparation, NOT an installed/admitted generic producer.
Date: 2026-09-28. External Provider CLOSED; Real-data Admission CLOSED.
Authority: Founder continuation after durable R5 checkpoint c1e22508.

## Why this boundary exists

The parser can ingest more than the registered workbook. This does not authorize
execution, disclosure or durable certification. V39 and execution-provenance-1
truthfully describe only registered-workbook-mock-v1. General execution must not
borrow that identity or erase its source guard. Existing R5/V39 evidence remains
immutable and verifiable by its original reader.

This contract concerns analysis-processing execution, not execution of a CFO's
professional decision. It creates no DecisionArc, ExpectedImpact, ActualOutcome
or Learning. FR-EXPECTED-2 remains unchanged; structural validity is not
professional financial reliability.

## Versioned contract and implementation boundary

`backend/services/producer_execution_contract.py` defines
`producer-execution-candidate-2`, deliberately NOT `execution-provenance-1`.
It is a proposed execution description with permanent status
`UNADMITTED_CANDIDATE`, not a receipt, grant, issuer, signature or permission.
It binds request, execution, prospective analysis, company, entity, engagement,
producer/version, task/version, admission-contract digest, raw source digest,
source-representation digest, actual producer-input digest and envelope digest.
Timestamps must be timezone-aware and ordered. No source bytes or identity map
belongs in this description. Reserved registered-mock identity is rejected.

The local validator compares every binding to expected execution data, validates
the envelope structure, checks its representation hash and content digest, and
returns only the still-unadmitted candidate. Nested copied Pydantic models are
revalidated. Errors exposed by the validator are fixed, content-free codes.

**Matching data is not authority.** An attacker supplying both matching candidate
and expected data has proved nothing. Hashes are not signatures. Repeating this
pure validation is allowed and is not replay protection. The module has no route,
transport, DB writer, admission issuer or integration into the application mount.
No provider mode/origin claim is inferred from a candidate or producer name.

## Required trusted execution composition (not yet implemented)

1. Resolve authenticated principal and authoritative company/entity/engagement
   ownership server-side. A prospective analysis cannot borrow a protected-read
   grant which requires an already persisted analysis. Reserve its exact request,
   execution and analysis identifiers once under separately governed admission.
2. Select a registered, versioned producer and task policy in backend composition,
   never from form fields or arbitrary executable identifiers. Establish its
   actual mode, data-origin admission, permitted input/output classes and limits.
   No such generic production profile is registered by this slice.
3. Build expected bindings from actual admitted bytes, governed ingestion,
   authoritative scope, selected policy and the exact input passed to the adapter.
   No caller-supplied hash, plausible pseudonym or unreceipted value is authority.
4. For an external producer, enforce positive task-specific admission:
   task -> allowed data classes -> necessity -> governed source -> privacy
   transformation -> projection -> egress policy -> provider. Bind the verified
   projection, disclosure/request and validated response receipts through the
   existing capability mechanisms. A digest in this candidate is not a substitute.
   FINANCIAL_CHANGE_MINIMAL_V1 does not authorize a general financial-analysis
   task. PG/RD and actual account configuration must separately permit the use.
5. Quarantine producer output, validate actual request/source references and
   epistemic separation using existing governed analysis contracts. Structural
   validity cannot promote inference to fact. Local rehydration remains separately
   authorized, terminal-only and unable to feed a future provider projection.
6. Issue a **different admitted receipt contract**, only after these actual checks.
   Keep the candidate distinct; never accept client JSON as completed execution.
   Define producer-specific mode, origin and validation evidence truthfully.
7. Introduce separately versioned atomic persistence only after the final admitted
   receipt is defined: analysis, envelope and receipt bound to the same scope,
   request and source; unique execution/request; no partial rows, retry under a
   substitute ID or fallback to receipt-less persistence. Deployment and remote
   rehearsal require distinct Founder authorization. Do not alter V39 to accept
   candidates. Prepare rollback/replay/foreign-scope tests before deployment.
8. Version-dispatch readers and terminal labels; retain v1 historical semantics.
   The current governed_output v1 mock labels must not be reused for a different
   producer. Carry the admitted provenance through UI and all three exports,
   then demonstrate fresh recovery and adversarial ownership using the real
   admitted path. Missing receipt stays unverified, never retro-certified.

These are integration obligations, not claims of implemented security. No
generic producer, global D10 policy, multiprovider framework or new privacy
programme is introduced. Close only the next necessary gate per DEC-032.

## Evidence and explicit debt

Local tests cover every expected binding substitution (including each scope
dimension and request/producer/task/source/input), envelope digest mismatch,
reserved mock identity, malformed copied models, naive/reversed timestamps,
unknown fields and content-free errors. The candidate is refused by the existing
V39 application persistence adapter **before RPC**. This is not a new live SQL
proof. Existing v1 persistence/pipeline regression tests remain green.

2026-09-28: 69 tests PASS across test_producer_execution_contract,
test_execution_provenance, test_governed_pipeline and
test_governed_analysis_persistence. Local synthetic/in-memory evidence only.
First run: 40 PASS and 17 setup errors due to inaccessible default pytest temp
directory. Rerun used a unique writable --basetemp; no application defect was
inferred or hidden. No remote call, permit, business mutation or gate activation.

OPEN: trusted admission issuer/coordinator, actual general producer, task privacy
coverage for external use, admitted receipt/persistence version, actual transport,
terminal version dispatch, end-to-end/professional/live isolation proof. B1 OPEN.
The next technical dependency is the trusted producer/task admission composition,
not another R5 window and not relaxation of V39. Candidate-schema validation
alone cannot close any of these debts.

## Founder composition invariants — local preparation update

The 2026-09-28 Founder framework is reconciled and traced in
INSIGHT_SHAPER_B1_ADMISSION_COMPOSITION.md. Tenant maps to company_id, client
company to entity_id; V19 engagement ownership remains transitive. The candidate
now requires actor_id. Existing OwnershipAuthority has a prospective, single-use
process-local preparation capability binding the whole composition, with an
unmounted backend adapter for verified actor, exact parents/source/profile and
immutable input. 199 targeted regression tests PASS; a separate pre-existing
repository-wide network-import scan remains unresolved and is not counted PASS.
This supersedes only the absence of local preparation above: no actual generic
producer, admitted durable receipt, distributed replay or new SQL guarantee is
implemented. Candidate remains UNADMITTED; V39 and all gates are unchanged.

## Durable follow-on — superseding local implementation status

V40 and its unmounted backend RPC adapter now implement a separate local-synthetic
durable contract, with 29 actual PostgreSQL tests and 211 targeted Python tests.
This supersedes the absence-of-SQL statement above, not the admission decision.
No actual generic producer, remote deployment, HTTP mount or v2 terminal dispatch
is proven. No policy installed outside isolated local test databases. V39 and
historical mock receipts unchanged. See B1_DURABLE_ADMISSION_V40.md for exact
scope, independent client-process recovery versus unproven server restart,
atomicity/refusal evidence and next required remote authorization. B1 OPEN.

## Subsequent live V40 successor evidence — 2026-09-28

The deployment/remote-proof absences in the earlier dated preparation record
above are superseded only within the bounded synthetic V40 scope. The distinct
successor reached BOUNDED_V40_SUCCESSOR_PASS: nineteen effects / one Auth / seven
new rows, frozen pre-Auth identities equal composed and persisted identities,
race/rollback/replay refusal and independent process recovery; both test policies
disabled and old evidence intact. See B1_V40_SUCCESSOR_LIVE_EVIDENCE.md.
The real generic producer remains UNADMITTED. Its actual controlled connection,
task-specific privacy/egress admission where applicable, v2 terminal dispatch
and end-to-end proof remain OPEN. No V39 reinterpretation or B1/gate closure.
