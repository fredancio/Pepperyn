# V40 first refusal — policy containment and read-only diagnosis

Status: POLICY_DISABLED_VERIFIED / ADAPTER_SCHEMA_INCOMPATIBILITY_PROVEN /
HISTORICAL_FIRST_EXCEPTION_UNRECOVERED. B1 OPEN; generic UNADMITTED;
External Provider CLOSED; Real-data Admission CLOSED.

## Authorized single mutation

Founder explicitly authorized disabling only policy
`cab54f0d-8b8c-4e77-bae6-7cc0660de0d7` after the failed rehearsal.
One transaction locked the three V40 registries, required exactly one enabled
synthetic DENY policy and three admissions matching the pre-read SHA-256,
updated only that policy's enabled field to false, checked row count exactly 1,
full policy equality except enabled, admissions equality and receipt absence.
Observed acknowledgment: `V40_EXACT_TEST_POLICY_DISABLED_ONCE`.

An independent READ ONLY transaction then confirmed enabled=false, policy count
1, admission count 3 and receipt count 0. All other policy fields were unchanged.
Before/after hashes (PostgreSQL JSONB aggregate text, UTF8 SHA256) identical:

| Object | SHA-256 |
| --- | --- |
| all V40 admissions | 193a878f3b896212db174c1e3ed1adb52f01ae70786fab907b3eaef30dfb09b6 |
| analyses | cab9bc0abf7b54de15d4b2055a2b018ef35397a9fcd07337beca83a639a0d708 |
| governed envelopes | c4810697f6c8d20773ca9152b5c0016be58aa11adeda5ff82840e7881dd0de10 |
| V39 execution receipts | c794733a7083009055c37af715d06873227f79f20ad78946c51ebf634ae1e897 |

These hashes prove preservation across this disable, not retroactive final
historical comparison for the incomplete rehearsal. No admission update/delete,
new row, schema change, replay, login or cleanup. The disable is a separately
authorized containment operation, not a nineteenth rehearsal slot or a PASS.

## What PostgreSQL actually refused

The positive admission remains REFUSED with no analysis/envelope/v2 receipt.
The live gateway log shows POST complete_execution_v2 HTTP 200 at 15:25:35
Europe/Brussels (13:25:35 UTC); this means the RPC returned its governed REFUSED
object, not a successful completion. The function's nested EXCEPTION WHEN OTHERS
rolls back the trio and records REFUSED, losing the original SQLSTATE, constraint
name and context. The local runner also retained no completion payload/exception.

The filtered Postgres log view contained nine events over the relevant hour:
checkpoint messages and five expected P0001 scope/source/claim refusals. No
positive-completion exception/23514 appeared. The claim refusal at 13:25:35 is
the separate race loser; it must not be reclassified as the completion cause.

Expiry is excluded by durable timestamps: positive issued 13:25:33.902628Z,
claimed 13:25:35.310525Z, REFUSED 13:25:35.682675Z, expiry 13:30:33.902564Z.
This does not exclude another earlier binding/time validation condition.

## Exact incompatibility established without a write

The pinned `services/durable_producer_admission.py:116` always serializes
`type_document='FINANCIAL_WORKBOOK'`. Current source SHA-256 equals the launch pin:
`74AB61CB8741A78A1A1F6D22EDD47BC24B0A008C66E5A15B522AFB73C5ED2152`.

The actually deployed `persist_governed_analysis_v1(jsonb,jsonb)` definition
inserts `p_analysis->>'type_document'` unchanged into public.analyses. Its deployed
constraint `analyses_type_document_check` allows only:
COMPTE_RESULTAT / BUDGET / PREVISIONNEL / TRESORERIE / BILAN / COMMERCIAL / AUTRE /
INCONNU. PostgreSQL READ ONLY evaluation of the adapter literal against this
exact set returned false. Therefore this payload cannot pass the INSERT if
execution reaches it; that violation would have SQLSTATE 23514.

Important evidence limit: 23514 is the consequence of this proven incompatibility,
NOT a recovered historical SQLSTATE. Without the original exception or complete
historical payload, we cannot certify that this was the FIRST exception reached
on that request, rather than an earlier V40 binding check. Do not promote this
diagnosis into an exact historical traceback or a new V40 PASS.

## Classification and minimal proposed correction (not implemented)

1. Defect in the application adapter's serialization against the existing legacy
   analyses taxonomy, not evidence that the V40 atomicity/ownership contract must
   be weakened. No change to the database allowed-value constraint is justified.
2. Test coverage gap: `tests/test_v40_postgres.py:65-68` creates a reduced analyses
   table without this CHECK. The whole local orchestration inherited that gap.
3. Map the adapter's document metadata to the existing governed taxonomy; for an
   unclassified composite financial workbook, AUTRE is the existing V39 rehearsal
   precedent, without discarding richer source/envelope information. Review this
   mapping rather than pretending FINANCIAL_WORKBOOK is already database-valid.
4. Reproduce actual relevant analyses constraints in isolated local SQL tests;
   prove the invalid literal's rejection and the corrected complete chain there.
   Add a safe diagnostic strategy preserving SQLSTATE/constraint/context codes
   without credentials/source contents before any new remote rehearsal. A database
   diagnostic implementation, if chosen, would require separate migration approval.

No code correction or new local PostgreSQL run was made in this read-only phase.
The adapter/test correction itself can be local-only; it does not require changing
V39 or the deployed V40 schema. Further local write-based reproduction requires
leaving this diagnostic-only GO. A new remote persistence proof requires a new
explicit rehearsal GO: the current policy is irreversibly disabled and admissions
terminal. Preserve all four rows and the original journal; never reopen/reuse them.
