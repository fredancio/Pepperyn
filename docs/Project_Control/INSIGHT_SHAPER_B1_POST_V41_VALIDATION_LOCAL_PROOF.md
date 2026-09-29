# B1 - post-V41 validation hardening

Status: BOUNDED LOCAL PASS / CORRECTION NOT DEPLOYED / PRODUCER UNADMITTED.
Evidence ID: PPR-067. Evidence date: 2026-09-29.
Authority: Founder GO - TRANCHE LOCALE POST-V41.
Baseline: cb7dd50e8e6b9eeea3179608360386c8c240c363.

## Scope and actual defects

This is a local correction of existing policy/scope and receipt completeness
requirements, not a new admission doctrine or producer contract. V41 structural
deployment PASS remains valid within its recorded scope. No remote operation,
policy activation, real-data use or actual provider invocation is performed.

The historical V41 SQL reproduced these holes in isolated PostgreSQL:

- A policy's company/entity/engagement is not compared to the reservation's
  scope. The existing actor/parent check establishes ownership of the requested
  scope but not authority of this particular policy over that scope.
- The receipt key subtraction rejects extra keys but not missing required
  keys. Missing/null request, response and provider-policy-evidence digests
  pass because PostgreSQL IF does not treat NULL as true. A 64-digit JSON number
  also passes the textual regular expression although the Python contract
  requires a string. These malformed receipts can reach COMPLETE historically.
- A well-formed but unrelated request digest also reaches COMPLETE historically;
  the claimed producer input in the V41 test contract is the complete canonical
  request, so the two digests must be equal.

Historical-positive assertions in the new tests record these defects. They are
never labelled valid admissions or a product-contract PASS.

## Minimal separately prepared correction

`backend/migrations/prepared_v41_validation_hardening.sql` changes only the bodies
of reserve_generic_execution_v3 and complete_generic_execution_v3 in disposable
local databases. Signatures, ownership, SECURITY DEFINER status, ACLs, search_path,
other functions, tables and authority allocation remain unchanged.

The correction:

1. requires each policy scope member to be a string equal to the corresponding
   reservation member before insertion;
2. requires every receipt member, with object types for bindings/contract_binding
   and string types for the other members;
3. requires digest lexical validation to be explicitly true, including NULL refusal;
4. binds request_sha256 to the already committed producer_input_sha256.

It neither authenticates a provider nor claims that a random response/policy
digest is authentic. Those provenance obligations remain backend composition
work. No authority moves from the backend to the database or vice versa.

The script is transactional and refuses unless both original function-body
digests match, with CRLF-to-LF as the sole normalization. Reapplication refuses.
It has no registration, invocation, grant or cleanup step. It is NOT a remote
deployment procedure and requires a distinct authorization before any such use.

The applied migration file remains byte-identical, SHA-256:
01956BD95487B823FD484A4D9E667CB5862B079364A408CF282E54E6A5DB729C.

Prepared correction SHA-256:
3134D6B5BFEC47C2B649E06FAC47DCC72AA5549DF96D27FF4F84759F6E384218.
Mechanical comparison of both function bodies against V41 confirms exactly the
four changes above and no other body delta. This is a local candidate, not a GO.

## Validation and honest limits

Runtime: existing pepperyn-b1-pg16-20260928; verified network mode none, no exposed
ports, no host binds, label b1-synthetic-sql-test. Tests create unique synthetic
databases through the existing guarded fixture. No cloud credentials or Auth.

Before correction: initial 59 historical cases PASS as defect characterizations.
Expanded first run: 80 historical cases PASS, then one local SQL syntax error
before the corrected phase. The generated regex replacement had expanded a
literal dollar marker and duplicated text. It was repaired locally; the failed
transaction did not partially install the correction. This run is not an overall
PASS. No remote correction or retry occurred.

Second expanded run: 84 historical cases PASS, then the additional catalog
equality assertion refused. Read-only comparison of both local databases proved
that proargdefaults differed only at its parser location, 196 versus 207:
CREATE OR REPLACE adds eleven characters. Both deparsed signatures retain
p_ttl integer DEFAULT 30, owner postgres, the same postgres/service_role ACL,
SECURITY DEFINER and search_path. The metadata check now compares deparsed
arguments in place of that internal parse tree while retaining all other catalog
attributes. This is not function-body normalization and changes no SQL behavior.
The separate function-body precondition still permits CRLF-to-LF only.

Final complete before/after PostgreSQL result: 168 PASS, zero skipped, in 328.86s.
This comprises 84 historical-characterization cases and 84 hardened cases.
The historical cases include 22 acceptances that characterize the reproduced
holes; their hardened equivalents refuse. Historical test success is not
requalification of those acceptances. The final run supersedes neither earlier
failure record; both are retained above.
Application regression: 111 PASS, five dependency/model warnings.
V39 provenance/persistence regression: 26 PASS.

Final selections actually executed:

- test_post_v41_validation_postgres.py: 168 PostgreSQL PASS;
- test_generic_producer_candidate.py, test_governed_producer_adapter.py,
  test_durable_producer_admission.py, test_producer_execution_contract.py,
  test_governed_output_composition.py, test_governed_output_isolation.py,
  test_v41_definition_contract.py: 111 application PASS;
- test_execution_provenance.py and test_governed_analysis_persistence.py:
  26 V39 regression PASS.

305 final selected cases PASS; no PostgreSQL case in this protocol skipped.
No repository-wide test-suite PASS is claimed. The seven pre-existing exclusions
retain their exact prior SHA-256 values, including frontend/next-env.d.ts.

Adversarial scope covers foreign but valid ownership compositions, missing/null/
numeric policy scope, every receipt member missing/null/wrong-type, malformed
digests, mismatched request digest, contract/envelope substitutions, concurrent
claim, replay, expiry, disabled policy, storage taxonomy failure and a later
envelope INSERT failure after the analysis INSERT. Refusals check absence of the
result trio and, for receipt/storage/expiry probes, exact unchanged snapshots of
all other public test tables. Successful execution remains synthetic test data.

The fixture's schema does not include every production memory/arc/artifact
surface. The correction adds no call or DML to those surfaces and the tests use
only SQL and the existing deterministic mock helper. This is not an end-to-end
product memory or global egress proof. Existing socket-denial candidate tests are
included in application regression; the PostgreSQL container has no network.

## Remaining gaps and stop boundary

No assertion that response_sha256 or provider_policy_evidence_sha256 is authentic
follows from format validation. Actual request/source projection consistency,
trusted response evidence, product V41 coordinator/owned reread/UI/exports and
historical V1/V2 coexistence remain separate work from the review. No changes to
those contracts or implementations are part of this slice.

Global egress remains OPEN/FAIL; it was not rerun or requalified. B1 OPEN, generic
producer UNADMITTED, External Provider CLOSED, Real-data Admission CLOSED.
No Git index/commit/push and no next B1 tranche: a new explicit GO is required.

## Post-review extension (PPR-068; original PPR-067 campaign preserved)

The later authorized local B1 tranche did not rewrite this 168-case record. It
extended the still-undeployed successor functions with an immutable provider
policy-evidence binding and expanded the complete PostgreSQL selection to 187
PASS, zero skipped/not executed. PostgreSQL—not Python—derives the digest from
its `jsonb` representation. The first expanded full run's hardened failures and
their fixture-serialization cause are retained in the separate PPR-068 record.

PPR-067 was subsequently deployed structurally under a distinct Founder GO. The
fresh preflight, exact guarded application, conformant postflight, empty registries
and identical historical baseline are recorded without rewriting this local
campaign in `INSIGHT_SHAPER_B1_PPR067_STRUCTURAL_DEPLOYMENT_EVIDENCE.md`.
See also `INSIGHT_SHAPER_B1_LOCAL_CONTRACT_OUTPUT_EGRESS_PROOF.md`.
