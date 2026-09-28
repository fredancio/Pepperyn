# V40 local storage correction and successor rehearsal proposal

Authority: Founder GO for local correction/validation only. No remote mutation,
new Auth, policy, admission, analysis, migration or rehearsal under this GO.
Previous failed evidence remains REFUSED and its policy remains disabled.

## Exact correction and semantics

`DurableProducerAdmission.complete` now sends `p_analysis.type_document=AUTRE`
instead of FINANCIAL_WORKBOOK. This is the legacy storage classification, not
the governed financial-document ontology. The precedent is the exact V39
English-workbook rehearsal in `sandbox/rehearse_execution_receipt_v39.py:prepare`,
using the same fixture/hash and AUTRE. A composite workbook is not silently
reclassified as a single income statement or balance sheet.

The analysis JSON keeps its FINANCIAL_WORKBOOK type and all its detailed fields;
the entire governed envelope and source facts are unchanged. A new adapter test
compares both full JSON objects, not only the type string. The local PostgreSQL
positive test also compares the persisted detailed result and envelope exactly.
No new schema value, taxonomy expansion or V39/V40 change was made.

Adapter current SHA256:
2C41597CE9D8EC0E85EDDBD7EF74DF95B421B65F77A4B4E2B0B0EC2E9BB1805B.
The old rehearsal wrapper deliberately retains its old pin and existing-attempt
refusal. It is NOT a launch command for this revision; do not repin/reset/reuse it.

## Local parity basis and remaining limits

Basis: actual Integration Test catalog/function/trigger reads performed during
the preceding read-only diagnostic, 2026-09-28. This step did not access the
remote database. `tests/fixtures/v40_analyses_schema.sql` is a LOCAL fixture, not
a deployment migration. It recreates all 30 observed analyses columns with their
types/nullability/defaults and all ten observed constraints.

| Previously simplified item | Local correction / review |
| --- | --- |
| document taxonomy | exact eight-value CHECK; FINANCIAL_WORKBOOK rejected |
| file formats | xlsx/xls/pdf/csv CHECK |
| mode/status/score | quick/complete; four statuses; score 0..100 CHECKs |
| tenant/entity/session/user references | exact FK target and ON DELETE behavior |
| file size | integer (32-bit), not previous bigint |
| entity | nullable as deployed; V40 exact scope checks still mandatory |
| chat_count | NOT NULL DEFAULT 0 as deployed |
| omitted columns/defaults | 30-column catalog contract, nine non-null defaults |
| analyses triggers | none observed; fixture asserts none |
| envelope | actual V27 migration: 8 constraints, composite scope FKs, unique scope indexes, immutable update trigger |
| V39/V40 | original migration files unchanged; real SQL runs locally, never relaxed to accept invalid metadata |
| V40 roles/guards | existing tests exercise actual RPCs, denied direct DML, immutable states and composition |

Parent tables remain synthetic/minimal, and the local Auth/PostgREST boundary is
mocked; this is NOT complete Supabase infrastructure parity, live RLS, clock-sync,
provider, professional reliability or production proof. Auxiliary historical
tables outside the result transaction are reduced in the whole-run mock reader.
Fresh deployed function/constraint/scope checks remain mandatory before any
future remote attempt. Client/server time skew is not erased by local SQL proof;
candidate timestamp validation must remain fail-closed.

The invalid literal now yields actual local SQLSTATE 23514 naming
analyses_type_document_check through the unchanged V27 function; V40 catches it
and records REFUSED with no result trio. This local reproduction does NOT recover
the first exception of the old remote attempt. That historical distinction stays.

## Validation results

- 56 local PostgreSQL tests PASS in 227.93s: storage parity, four whole-run
  orchestration cases and existing SQL admission/atomicity falsifications.
- Final detailed 30-column/type/nullability/nine-default assertion and storage
  suite rerun: 15 PASS in 17.18s (overlaps the 56; not 15 additional distinct tests).
- 138 application/composition/candidate/launcher/budget/transport/handoff tests
  PASS in 7.66s. These include exact full-result/envelope semantic preservation.
- Egress selection: 34 PASS / 1 unchanged FAIL (eight pre-existing static scan
  findings). No complete-suite PASS or closure of that debt is claimed.
- Git diff whitespace check for tracked code touched in this correction: PASS.
  Index untouched; frontend/next-env.d.ts and unrelated strategic deltas preserved.

Database falsifications now cover invalid taxonomy, file type, mode, status,
score below/above range, foreign tenant/entity/session/user, NULL chat_count,
and 32-bit file-size overflow. Actual PostgreSQL SQLSTATE/constraint evidence
is asserted locally. The original invalid type is rejected through V27; V40's
rollback leaves no trio, while corrected AUTRE completes with detailed JSON equal.
Actual V27 inserts an explicit NULL for absent mode; the observed CHECK permits
NULL. Tests preserve that behavior rather than pretending the column default
will replace an explicit NULL. No second schema incompatibility occurred in the
corrected tested path; that is bounded evidence, not universal schema parity.

V39 SHA256 remains FED32557CBA5B93AA7DFAF7E850C4924342DFDFA26CAEC83A2AB0C9A7A3B389D;
V40 SHA256 remains D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24.
All SQL test writes were to newly created databases in the existing isolated
Docker container, with no network, no published ports and synthetic data only.
No remote access or mutation occurred during this correction/validation step.

## Successor rehearsal proposal — NOT AUTHORIZED / NOT RELEASED

Do not use the former empty-registry runner: the historical four control rows
now legitimately exist. A distinct successor must be prepared and validated
locally against a populated baseline before it can be presented as READY.

Proposed unchanged effect ceiling: 19 effect-capable requests, including one Auth
login, one new test-policy INSERT, the same 16 RPC/refusal slots, and one policy
disable. Token memory-only, no refresh/second login/retry. Same Integration Test
project, technical account 1, scope and exact synthetic English source.

Proposed maximum delta: seven new durable rows (policy 1 + admissions 3 + one
analysis/envelope/receipt trio); combined historical/current V40-related total
would be eleven rows. Old policy must remain disabled and its three terminal
admissions remain byte-equivalent under canonical row hashes. New policy and
prospective IDs must be explicitly distinct and fixed in an exclusive successor
manifest; no replacement IDs after a failed attempt. No historical promotion.

Before Auth/writes: verify original evidence/journal unchanged, old four-row
baseline exact, new IDs absent, business baselines unchanged, deployed objects
conform, AUTRE CHECK accepted, and local release hashes validated. Do not merely
change an empty-table count to ignore existing rows.

Positive, race, rollback, replay and independent-process recovery remain required.
Each refusal must show no forbidden result delta; preserve all pre-existing
rows/hashes throughout. Final PASS requires exactly the seven-row delta, states
REFUSED/CLOSED/COMPLETE for new admissions, new policy disabled, old four rows
unchanged and all 19 slots accounted for. No cleanup or silent recovery on failure.

Before release, retain safe phase/result diagnostics (no payloads or credentials)
and acknowledge that the current remote SQL catch does not expose its original
exception. Do not promise historical SQLSTATE observability without an approved
change. No database diagnostic migration is included in this proposal.

A distinct Founder GO is mandatory for any successor remote rehearsal. The old
GO cannot be recycled. B1 OPEN; generic UNADMITTED; both external/data gates CLOSED.
