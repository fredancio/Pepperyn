# B1 — V41 Structural Deployment Protocol

**Status:** PREPARED / NOT AUTHORIZED / NOT EXECUTED
**Target:** Supabase Pepperyn Integration Test (`ejixkplrgobgwqnhidwt`)
**Repository authority:** `9900cfb86c2884ec28ae16a375c2b689d2b24ca8`

## Purpose and strict boundary

Install only the empty durable-contract V41 structure proven locally by PPR-065.
Deployment is not producer admission and cannot create a policy, admission,
analysis, envelope or receipt row. It does not open provider egress or real-data
admission and does not close B1.

V41 retains AC-1..AC-12 and DEC-034 exactly. This protocol does not alter the
meaning of V39, V40 or their historical evidence.

## Versioned artifacts

| Artifact | Raw SHA-256 | CRLF-to-LF SHA-256 |
| --- | --- | --- |
| `v41_preflight_read_only.sql` | `01D023B2C9BF619094B60B127D3EC1A00D71248F1A45C11ECF7C0CD4BD9C51C9` | same |
| `v41_generic_producer_receipts_v3.sql` | `01956BD95487B823FD484A4D9E667CB5862B079364A408CF282E54E6A5DB729C` | same |
| `v41_postflight_read_only.sql` | `756670601CEE51CD5B13F25FC6434501573E39E76446FECA774CD54A6DF5208B` | same |
| `v41_definition_conformance_read_only.sql` | `F89EDC64A8E1108A3861280ABC5C95480956B327760A13A8FBF5C9085E26E0AC` | same |
| `v41_historical_baseline_read_only.sql` | `618EDFD4BBD794B1FD7C228D72ECA28D4AA3F002CD43E46FC749519C4A62354D` | same |

Only these exact committed artifacts may be used. A raw mismatch refuses. For
PostgreSQL-returned definitions, retain both raw hashes and the single versioned
normalization `CRLF -> LF`. No whitespace, case, syntax or formatting
normalization beyond line-ending conversion is allowed.

## Phase 0 — external identity and authority check

Before SQL:

1. Founder visually confirms Supabase project name **Pepperyn Integration Test**
   and project ref `ejixkplrgobgwqnhidwt`.
2. Repository HEAD and the three artifact hashes above are verified.
3. The GO authorizes exactly one conditional migration execution. It authorizes
   no later registration, admission, data row or corrective execution.

Failure or ambiguity stops before SQL mutation. SQL catalog evidence alone does
not prove the Supabase project identity.

## Phase 1 — read-only precontrol

Run `v41_preflight_read_only.sql` once. It must return:

- `status = PREFLIGHT_PASS`;
- `write_performed = false`;
- V39 persistence function present;
- V40 scope function and receipt registry present;
- all three V41 tables absent.

In the same read-only control window, run
`v41_historical_baseline_read_only.sql` and record its confidential manifest
containing only counts and deterministic SHA-256 aggregates, never row content,
for:

- `analyses`;
- `governed_analysis_envelopes`;
- `governed_execution_receipts` (V39);
- `producer_policies_v2`, `execution_admissions_v2`,
  `execution_receipts_v2` (V40).

Also record definitions/ACL/RLS/constraints/triggers for the V39/V40 objects used
by V41, and confirm required roles `anon`, `authenticated`, `service_role` exist.
The baseline is comparison evidence, not permission to interpret or expose rows.

Stop before migration if any V41 object already exists, any prerequisite is
missing, the project is not independently identified, a baseline query fails or
the observed V39/V40 structure differs from the checkpointed assumptions.

## Phase 2 — single transactional migration

Execute the exact `v41_generic_producer_receipts_v3.sql` once. Its explicit
transaction and opening guards must be retained. Do not select partial statements
or rerun after an error.

Objects created exactly:

### Tables

1. `public.generic_producer_policies_v3`
2. `public.generic_execution_admissions_v3`
3. `public.generic_execution_receipts_v3`

Expected immediately after deployment: zero rows in all three.

### Trigger function and triggers

- `public.guard_generic_execution_v3()`;
- one immutable guard trigger on each new table.

The policy guard permits only irreversible `enabled=true -> false`. Admission
composition is immutable except for governed state/claim timestamps. Receipts
cannot be updated or deleted.

### Service functions

- `reserve_generic_execution_v3(uuid,jsonb,jsonb,jsonb,text,text,integer)`;
- `claim_generic_execution_v3(uuid,uuid,text)`;
- `close_generic_execution_v3(uuid,uuid)`;
- `complete_generic_execution_v3(uuid,uuid,uuid,jsonb,jsonb,jsonb,text)`.

The four functions are `SECURITY DEFINER`, have fixed
`search_path = pg_catalog,public`, and are executable only by `service_role`.
The guard function is not callable by PUBLIC, `anon`, `authenticated` or
`service_role`.

### Permissions and RLS

- RLS enabled on all three tables;
- zero RLS policies;
- PUBLIC, `anon` and `authenticated`: no table privileges;
- `service_role`: SELECT only, no direct INSERT/UPDATE/DELETE/TRUNCATE;
- no registration RPC and no producer policy inserted.

### Constraints

Postcontrol must enumerate and compare every primary key, unique constraint,
foreign key and CHECK definition. Material checks include canonical contract
binding text/JSON/digest equality, digest formats, bounded projection size,
allowed admission states, exact entity/company and engagement/entity ownership,
and receipt linkage to governed envelopes.

## Phase 3 — read-only postcontrol

Run `v41_postflight_read_only.sql` once. Required result:

- `status = POSTFLIGHT_PASS`;
- exactly three expected tables, each RLS-enabled with one guard trigger;
- exactly four expected service functions, service-only executable and
  `SECURITY DEFINER`;
- `policy_rows = admission_rows = receipt_rows = 0`;
- `write_performed = false`.

Then run `v41_definition_conformance_read_only.sql`. It must return
`V41_DEFINITION_CONFORMANCE_PASS`, five conformant functions and
`write_performed=false`. This control performs the stronger definition
attestation:

1. enumerate exact function signatures in schema `public`, including the guard;
2. capture `pg_get_functiondef`, function owner, `prosecdef`, `proconfig` and ACL;
3. capture `pg_get_triggerdef`, `pg_get_constraintdef`, table ACL, RLS and policy
   count;
4. compare raw returned definitions and CRLF-to-LF hashes against the isolated
   PostgreSQL reference produced from the committed migration;
5. accept a representation difference only when raw values differ but the
   versioned CRLF-to-LF values are identical; preserve both values in evidence;
6. treat every other difference as unresolved, never as formatting noise.

Finally rerun `v41_historical_baseline_read_only.sql`. Every V39/V40 and application-table
count/hash and every relevant pre-existing object definition must be identical.
The only catalog delta may be the explicitly listed V41 objects.

## Fail-closed conditions

Stop without retry, replacement SQL or cleanup when any of the following occurs:

- wrong or unverified project;
- artifact hash or repository authority mismatch;
- prerequisite missing or any V41 object partially/already present;
- migration error or ambiguous SQL Editor result;
- any new V41 row;
- unexpected table, function, trigger, policy, privilege, owner, search path,
  constraint or signature;
- any V39/V40/application baseline change;
- definition mismatch not explained solely by proven CRLF-to-LF conversion;
- inability to complete postcontrol.

No failure may be repaired by reapplying V41 or improvising `CREATE OR REPLACE`,
`ALTER`, `DROP`, DML or permission changes under the deployment GO.

## Rollback rule

An error before `COMMIT` relies only on PostgreSQL transaction rollback. After a
successful commit, there is no automatic rollback: the new objects remain empty
and inaccessible while the discrepancy is diagnosed read-only. Dropping or
altering committed V41 objects is destructive and requires a separate Founder GO
with fresh dependency and emptiness checks.

## Risk evaluation

**Overall: LOW-to-MODERATE for the authorized structural operation.**

- Data-mutation risk is low: the migration is transactional, creates only new
  objects and the required post-state is three empty registries.
- Authority-expansion risk is low when the exact ACL/RLS checks pass: there is no
  registration RPC, clients have no table access and service role has only SELECT
  plus the four bounded functions.
- Operational risk is moderate because a wrong project selection, an unexpected
  remote schema or an unreviewed representation mismatch could create misleading
  deployment evidence. Independent project confirmation, exact hashes and the
  before/after baseline address this risk.
- Recovery risk is moderate after commit: automatic DROP/reapply would be less
  safe than quarantining empty inaccessible objects and diagnosing them.
- Product/gate risk remains unchanged: an empty V41 structure cannot prove an
  admitted producer, egress safety, real-data admission or B1 completion.

## PASS evidence

A structural PASS requires all of the following together:

- independently verified target project;
- exact artifact hashes;
- `PREFLIGHT_PASS` with recorded V39/V40/application baseline;
- one successful transactional migration execution;
- `POSTFLIGHT_PASS`;
- exact object/signature/constraint/trigger/RLS/ACL/owner/search-path attestation;
- all three registries empty;
- identical before/after baseline hashes and counts;
- no second execution and no corrective mutation.

## What structural PASS does not prove

It does not prove or authorize:

- registration or admission of the genuine producer;
- any reserve/claim/complete execution;
- product-runtime V41 integration, owner reread, UI or exports;
- provider transport, account controls, PG-3/PG-4 or global egress safety;
- real-data admission, financial reliability, tenant isolation globally,
  Private Beta readiness or production readiness.

B1 therefore remains OPEN; the genuine producer remains UNADMITTED; External
Provider and Real-data Admission remain CLOSED. The repository-wide egress scan
remains OPEN/FAIL with its eight pre-existing findings.

## Smallest later Founder GO

The smallest sufficient GO would authorize only:

1. fresh read-only Phase 0/1 controls on Pepperyn Integration Test;
2. one execution of the exact V41 migration if and only if every precontrol
   passes;
3. read-only Phase-3 structural, definition and unchanged-baseline controls.

It would explicitly authorize no row creation, producer registration/admission,
analysis, receipt, provider use, real data, retry, repair or rollback.
