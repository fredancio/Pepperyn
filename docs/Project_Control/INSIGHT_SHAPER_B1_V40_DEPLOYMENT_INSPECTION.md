# V40 Integration Test deployment — STOP on definition fingerprint mismatch

CURRENT STATUS: APPLIED / REPRESENTATIONAL_DISCREPANCY_RESOLVED by separately
authorized read-only diagnosis below. Original failed exact-byte control and
STOP record remain unchanged. No remote correction or new admission is implied.

2026-09-28. Founder authorized structural V40 only. Target independently observed
in Supabase UI: Pepperyn Integration Test, ejixkplrgobgwqnhidwt. No other project
was selected or modified. SQL Editor query:
https://supabase.com/dashboard/project/ejixkplrgobgwqnhidwt/sql/47b9a67e-e2eb-42ce-9e8c-f670bc077d05

Status: APPLIED_ONCE / STRUCTURAL_CHECKS_OBSERVED / DEFINITION_CONFORMANCE_UNRESOLVED.
NOT a final deployment-conformance PASS. STOP: no corrective action or additional
remote query after the mismatch. No producer admitted, B1 OPEN, External Provider
CLOSED, Real-data Admission CLOSED. No business write or execution RPC invoked.

## Preflight and application

Prepared read-only preflight returned PREFLIGHT_PASS, write_performed=false.
All eight checks true: supported_postgresql, schema_create_authorized,
scope_uuid_columns, roles_present, v27_present, v39_present, new_tables_absent,
new_functions_absent. SQL reports project_identity_verified=false by design;
project identity was separately established from the UI title and project URL.

Migration file and full editor text (CRLF normalized to LF for the editor
comparison) both SHA-256:
D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24.
One Run of the exact V40 transaction returned `Success. No rows returned`.
No migration replay, replacement, cleanup, policy insertion or activation.

## Observed postflight

All three tables present, RLS enabled, zero RLS policies, one guard trigger each:

| Table | Rows | anon/authenticated | service_role |
|---|---:|---|---|
| producer_policies_v2 | 0 | No table privileges | SELECT only |
| execution_admissions_v2 | 0 | No table privileges | SELECT only |
| execution_receipts_v2 | 0 | No table privileges | SELECT only |

INSERT/UPDATE/DELETE/TRUNCATE denied to all three roles; supplementary inspection
also found TRIGGER/REFERENCES false for all three roles on all three tables.
Six functions observed with search_path=pg_catalog, public. anon/authenticated
EXECUTE=false for all. Service role EXECUTE=true only for reserve_execution_v2,
claim_execution_v2, close_execution_v2 and complete_execution_v2 (SECURITY DEFINER).
check_execution_scope_v2 and guard_prospective_execution_v2 are invoker functions,
not executable by those three roles.

Three enabled BEFORE DELETE OR UPDATE row triggers point to
guard_prospective_execution_v2: policy_v2_guard, admission_v2_guard,
receipt_v2_guard. 21 constraints observed and validated: expected primary keys,
unique request/analysis/claim identifiers, restrictive scope/policy/receipt foreign
keys, JSON/hash/size/state checks and fixed synthetic/deny/contract-version checks.
No adversarial writes were attempted: these are deployed catalog observations,
not a new live atomicity/authentication/isolation rehearsal.

## Existing-state preservation

Read-only pre/post snapshots matched exactly for all 21 pre-existing public
tables. Each fingerprint is count plus SHA-256 of canonically ordered JSON rows;
no row contents were returned. Not a global database audit outside this scope.

| Table | Count | SHA-256 before = after |
|---|---:|---|
| analyses | 9 | cab9bc0abf7b54de15d4b2055a2b018ef35397a9fcd07337beca83a639a0d708 |
| entities | 7 | 72658e33ef77fe4f5a03eb118f007ccaef5d4534e6a5301a9c79829fcf273cff |
| profiles | 4 | c17598025e14a5f5b0e80b612ae2e6636418adbe0a7e9f8c4a4121257d38c18c |
| sessions | 0 | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 |
| companies | 5 | 418fda844b39a6c5cb1090a9d53ff7d930b3ee9ca2997b5ab02b1a90a58648b3 |
| workspaces | 5 | a42977d5de923c520547f0ed9196cc8e4ac5ee2bfd9a76db42ade9ecc126e7fb |
| engagements | 7 | cdc0145674f31f31ebc893769379cd04124d7218efabf43a134ed6612793bb4c |
| decision_arcs | 0 | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 |
| user_patterns | 2 | 41e4c78b7d703a8220d3ce577692c96a18a8f74f34931e3d61b157a4f45ab4bd |
| knowledge_model | 0 | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 |
| decision_feedback | 3 | 6317af2c202f1fb1e607663379bfd32c1b029fe8afe9964b9de0c01fed21d294 |
| arc_analysis_links | 0 | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 |
| evidence_ledger_entries | 1 | f612e7c9f3518a8671ba29fc718ea78a0a437869ca0e66e899f00b87e0e62cc0 |
| governed_analysis_envelopes | 6 | df98de2966dab7830ee30e54c70b4bfe270d2702895f2df51e5b197a83aaa993 |
| governed_decision_followups | 1 | 8cc17a9fa9c1b4806e7d52fb0944f3e9a12e7bad43bf16a713c3a1b5b8c1c385 |
| governed_execution_receipts | 2 | c794733a7083009055c37af715d06873227f79f20ad78946c51ebf634ae1e897 |
| pseudonymous_correspondence | 2 | d91017182f7cc62a260228beb83e904b7a7331aa100e37799ceb04450f23e056 |
| governed_decision_executions | 1 | fcadc21baa822943c23aceb064dc8230a61ea6f26c62fadf60c658a795925f26 |
| synthetic_source_dossiers_v1 | 1 | 63e04189208057e78b673d4a5aab973a91fa7939e2f6355bd74552b2fd908e2d |
| pseudonymous_correspondence_bindings | 2 | 8a12123bb5cb40ecdfea742dc98a46c8fe50bb6376a82b11a154cde0c845e5c2 |
| governed_decision_prerequisite_evidence | 1 | 71faee7698574c92e134cd2d79fdc2ffd4110df4613e757b773348f8b75db2f1 |

Existing public function definitions and ACL aggregate hash before=after:
6bd69df267eca55fe1ff98dc52a10a67a58e8af312c927210b4c577b4f0b6bab.
Existing public table names/ACL/RLS flags aggregate hash before=after:
2772420405da5926fe7b09d3c28dece925bf4d5bb6ee1ed5b841d7d1960fbb43.
New V40 objects were excluded from these pre-existing-state aggregates. This
supports unchanged V39 functions/receipts and existing histories. No other
environment operation occurred. SQL Editor query text is the only incidental
dashboard artifact besides the authorized database DDL.

## Stop condition actually triggered

A supplementary read-only check compared SHA-256(pg_proc.prosrc UTF-8) against
the bodies extracted from the exact LF migration. All six comparisons returned
false: guard_prospective_execution_v2, check_execution_scope_v2,
reserve_execution_v2, claim_execution_v2, close_execution_v2,
complete_execution_v2. Cause UNKNOWN. Editor comparison normalized CRLF; this
does NOT prove that newline normalization explains the database discrepancies.
No semantic equivalence, corruption or security regression is inferred.

Per Founder STOP instruction, no subsequent remote query, corrective SQL or
re-execution was performed. Next recommended action requires a distinct GO for
read-only diagnosis of those six stored definitions versus the authorized file.
No mutation is needed or authorized for that diagnosis. Do not mark full
deployment conformance PASS until the discrepancy is explained with evidence.

## Separate authorized diagnostic — 2026-09-28

Founder authorized only read-only identification/comparison of six stored
definitions. Two READ ONLY transactions ending ROLLBACK read pg_proc bodies,
signatures, language/security/search_path metadata, hashes and newline counts.
No function invoked, no DDL/DML, no policy activation or result created.

Cause established: stored bodies use CRLF; expected file bodies use LF. For all
six functions, SHA-256 of the expected body with LF replaced by CRLF equals the
raw PostgreSQL SHA-256 exactly. Independently, PostgreSQL computed the normalized
body hash by replacing only CRLF with LF: all six match the expected LF hashes
and byte lengths, and all six have zero bare CR characters. No trimming, token
rewriting, whitespace collapse, case folding or comment removal was used.

| Function | LF bytes | Stored bytes | CRLF pairs | LF SHA-256 (expected = normalized stored) |
|---|---:|---:|---:|---|
| check_execution_scope_v2 | 787 | 799 | 12 | cc29b03aab84f711e0a8fa54ae20d1da90a3d10c1d26faed0f20cbe1affec0d1 |
| claim_execution_v2 | 1240 | 1257 | 17 | 3a170fde161d4a9ca4c7cc448b852f6b1dd76280f4cc0d3e26475eb854f5aade |
| close_execution_v2 | 277 | 283 | 6 | b406d4fbfd3339c96a152ff577a5ba4371e5421514691af13c2bd4d0a24092af |
| complete_execution_v2 | 4115 | 4171 | 56 | 14643c0e8357ba0326a5c92d2c18aa5640b783ae3e597285cf3468fb006ad46c |
| guard_prospective_execution_v2 | 1112 | 1130 | 18 | e01317257ab2b8172d697d464ca13b1005cd57556e469a1ac499e852f221a65c |
| reserve_execution_v2 | 3481 | 3533 | 52 | f0021960f852b5e61061d2626fa36e4a3cbfe8a21c2a0c12e012e19da50a1704 |

Raw stored hashes, preserved separately from the normalization result:

- check_execution_scope_v2: e458b5fc0665f4ad6943fa846bec1519910d156a40d7b123b86ffbb7f8f5989c
- claim_execution_v2: aeaa04e6c2e28ccdb4299f78bac3ae8bfc3607fde43d91e80c3b7e576a0691e5
- close_execution_v2: 9509ee67927d6e009fd01c192cc64b0be0123215a35e56f4ad5c79ef117df965
- complete_execution_v2: c2ea21274c1617c4ca170943136e55618df280e38c786496d70e330b9b61cb07
- guard_prospective_execution_v2: 6c241cc8f425bc602dac4ce9d92467b0fdc731cf4c72a9cf411330acb390f65e
- reserve_execution_v2: d1b37aefa86491aea73203b87f72715a1d05835a1f3fec20e2e05740312dab12

Observed signatures, return types (void/jsonb/text/jsonb/trigger/jsonb), plpgsql,
security-definer flags and search_path match the migration. Only reserve has
a default argument, p_ttl=30, as expected. Source inspection finds no multiline
quoted literal or nested dollar-quoted body in these six bodies. Therefore the
newline differences affect code/comment line separators, not literal data or
instructions. Semantic equivalence is established for this exact six-function
comparison; no general whitespace-insensitive SQL equivalence rule is claimed.

The first accessibility rendering of JSON compacted spaces and did not reproduce
the raw stored hash. It was rejected as a byte source. The decisive comparison
uses hashes/lengths computed in PostgreSQL and the exact expected file, not the
rendered body string. Migration hash remains
D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24.

This identifies the byte-level cause, not which upstream clipboard/editor layer
introduced CRLF. No claim that PostgreSQL itself rewrote the bodies is made.

## Proposed robust control, not retroactive replacement

Keep the initial raw mismatch and this separately authorized diagnostic. A future
versioned V40 verifier should record both raw and CRLF-to-LF hashes, reject bare
CR, require six exact names/signatures and compare language, return/default types,
security/search_path and privileges separately. Restrict normalization acceptance
to these reviewed bodies; refuse changed/multiline literal semantics. Do not trim
or normalize arbitrary SQL whitespace. Add negative local tests for changed
tokens/literals/signatures before adopting the verifier. No verifier or migration
was changed in this diagnostic; this is a proposal only.

Resolution: representation-only discrepancy explained; no remote correction is
necessary. Prior deployed structure/permission/vacuity evidence remains separate
and valid within its observation scope. No live execution/atomicity/isolation
rehearsal occurred. Generic producer UNADMITTED; B1 OPEN; both gates CLOSED.
Any future remote writing or activation requires a distinct Founder GO.

## Authorized local verifier implementation

The subsequent Founder GO approved the minimal verifier. Added separate
v40_definition_conformance_read_only.sql, version v40-definition-crlf-1. Existing
migration and original postflight remain unchanged. It retains raw and normalized
hashes, accepts only the two pinned LF/CRLF forms of each reviewed body, refuses
bare CR and checks exactly six functions, signatures/defaults/returns/language/
security/search_path and role execution permissions. No general whitespace
normalization. No remote verifier run occurred during this implementation.

Tests: pinned-source contract 1 PASS; local PostgreSQL suite 36 PASS in 65.58s,
including seven verifier variants (LF/CRLF positive; literal, space, bare-CR,
default and definer mutations refused). Initial CRLF test failed because Windows
text-mode subprocess stdin added newline translation; the harness now sends exact
UTF-8 bytes. Verifier acceptance was not broadened. Original 29 SQL regressions
also passed with that binary transport. Separate constraint-based late rollback
test: 1 PASS, 36 deselected; reuses V27 CHECK, no test fault trigger required.

Next deployed multi-process proof needs new remote-write authority. Its proposed
bounded scope is documented in B1_V40_LIVE_REHEARSAL_PROTOCOL.md. No true generic
producer has been connected or admitted. Documentation and source remain local
pending a later durability checkpoint; no Git write here.

## Subsequent rehearsal prechecks — no execution proof

Founder ran the separate service-only preflight once and reported
V40_SERVICE_READ_ONLY_PREFLIGHT_PASS. The saved report was read locally and
matches that result. File: Pepperyn-runtime/v40-service-readonly-preflight-19.json;
SHA-256: 35759DA949A93E0FB4DF030DBE8F9760B27C115D0EF9E2C1E833E830F6CD6F63.
Project: ejixkplrgobgwqnhidwt. Synthetic technical account 1 scope:

- actor: 89c2541d-3f40-43ee-a97e-06f90ffeb8e0;
- company: 1962090e-4dda-45ee-8b29-1a5afd9d387b;
- entity: 9abe5caa-1a8a-48ee-a7be-11df7df0c41a;
- engagement: 6310b4c5-1f06-4cf5-8fa5-cf20e9160e08.

Three V40 registries empty; registered English fixture hash exact. Eleven
pre-existing table snapshots captured: analyses 9; envelopes 6; V39 receipts 2;
feedback 3; user_patterns 2; arcs 0; arc links 0; followups 1; executions 1;
prerequisite evidence 1; source dossiers 1. These are a baseline, not proof of
immutability across a future rehearsal. The script did not authenticate a user
or inspect pg_catalog: authenticated_actor_proven and
schema_catalog_verified_by_this_script remain false in the original report.
Effect/Auth attempts both zero; business_write_performed false; rehearsal_ready
false. No report field has been retrospectively promoted.

Following this report, agent used the existing authenticated SQL Editor session
on the UI-verified Integration Test project for THREE separate READ ONLY /
ROLLBACK queries (no table mutation, no RPC invocation, no technical-user login):

1. v40-definition-crlf-1: BOUNDED_DEFINITION_CONFORMANCE_PASS. All six functions
   conform; raw CRLF and normalized LF hashes exactly as recorded in the prior
   diagnostic; signatures/defaults/search_path/security/execute permissions match.
2. v40_postflight_read_only: three empty registries; RLS true, zero client
   policies, one guard each. anon/authenticated have no SELECT/INSERT/UPDATE/
   DELETE/TRUNCATE; service_role has SELECT only. Only four SECURITY DEFINER RPCs
   are executable by service_role; both helpers denied to it. All six functions
   denied to anon/authenticated.
3. Constraint/trigger SELECT: all 21 constraints validated and definitions
   inspected against V40 (scope FKs, unique identities, state/domain checks,
   SYNTHETIC/DENY/version checks). Three expected BEFORE DELETE OR UPDATE guards
   target guard_prospective_execution_v2(), enabled O. No altered definition found.

The third query reads pg_constraint with pg_get_constraintdef and pg_trigger with
pg_get_triggerdef, restricted to the three named V40 tables. No dynamic SQL or
function call with application effects. Query results were read from the SQL
Editor result cell; these are separately obtained structural observations, not
fields certified by the earlier HTTP preflight. No V39/V40 reapplication or
correction. None of the 19 effect slots consumed by these SELECT-only queries.
This does not claim absence of ordinary SQL Editor telemetry/query-history effects.

Conclusion: preparation may continue inside the existing GO. It is NOT yet safe
to launch the live rehearsal: whole-run orchestration/local validation remains
unfinished; Auth and durable behavior unproven. Fresh structural/scope checks must
precede eventual writes; these observations are not a permanent admission permit.
