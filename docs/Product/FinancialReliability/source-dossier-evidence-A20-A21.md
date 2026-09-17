# A20/A21 — unresolved synthetic source dossiers

Base: `b3f59e2fb0c5e6b50872b1d32a9beb4fef978ae5`, clean working tree inspected.
A18/A19 checkpoints confirmed pushed by Founder; local HEAD verified. No live
remote fetch performed during development. Status: LOCAL_TESTED / NOT_CHECKPOINTED.

## Why this is on the critical path

PR-04/PR-05 require contradictions and provenance to survive terminal consumption
without promotion to canonical facts. Existing V27 analyses require UNDERSTOOD;
loosening that condition would weaken a proven boundary. The inherited V18 Evidence
Ledger captures an existing analysis and swallows write failures by its historical
contract. V24 Knowledge Model stores human-confirmed interpretations, not raw source
claims. Neither is repurposed or silently redefined by this slice.

A source dossier is therefore a distinct, immutable source-inspection snapshot, not
a governed analysis, confirmed knowledge, LaterEvidence, outcome, decision or learning.
It uses the same tenant/company -> entity -> engagement ownership relationship.
No changes to existing analysis, decision, export, temporal or provider contracts.

## Implemented bounded path

Explicit selected client -> registered synthetic workbook -> locally computed
understanding -> scoped immutable record -> checked reload -> referenced UI output.

- `backend/sandbox/source_dossiers.py`: verifies entity ownership and a unique
  engagement before reads/writes; exact four-file hash/name registry; source and
  payload hashes; schema version; scope-bound deterministic dossier identifier;
  insert-only capture and idempotent unique-conflict retry; validated reload/list.
- V35 SQL: separate `synthetic_source_dossiers_v1` table; composite scope FKs;
  exact synthetic registry constraint; RLS; no client table privileges; service
  SELECT/INSERT only; UPDATE/DELETE rejected. No backfill or legacy table mutation.
- Synthetic HTTP capture/list/read endpoints require development mode, synthetic
  feature flag, authentication and designated organization. Entity is explicit;
  tenant never comes from request body. Missing/foreign -> opaque 404;
  unavailable/corrupt -> 503, never a successful empty dossier.
- `SourceDossiers` UI: explicit save, separate read-only list/reload, source hash
  and persistent ID, both contradictory claims and references, no canonical value.
  Client change unmounts old scope; late responses cannot refill another client.
  No automatic write on upload selection, initial load, retry-read or refresh.
- Frontend enabled only with BOTH existing synthetic demo UI flag and new
  `NEXT_PUBLIC_ENABLE_SYNTHETIC_SOURCE_DOSSIERS=1`; new flag is OFF by default.

The registry is an admission allowlist, not FR-answer hardcoding. Runtime modules
do not import FR-EXPECTED-2 or expected-result values. FR-EXPECTED-2 is unchanged.

## Evidence and limitations

Local backend selection: `test_v1*.py`, `test_governed*.py`, `test_financial*.py`,
`test_source*.py`: **389 PASS, 2 SKIP**. The two skips require absent Phidani.xlsx;
no real financial file was introduced or processed. Source dossier suite: 17 tests,
including serialized mock-store reconstruction, retry uniqueness, foreign scopes,
tampering, missing/duplicate engagement, outage versus empty, HTTP gates and SQL
contract text. These mocks do not prove actual SQL constraints or multi-worker races.

Frontend: **111 PASS / 15 suites**, TypeScript no-emit PASS. Component tests cover
explicit capture and remount/reload, unavailable-not-empty, client-switch race;
API tests cover exact entity/ID, malformed responses and no caller-selected tenant.
Not browser E2E, actual authorization/RLS topology, or Founder visual proof.

V35 is NOT DEPLOYED and NOT SQL-EXECUTED. Local PostgreSQL executable not found;
Docker executable exists but no reachable daemon was available. No daemon settings,
credentials, production resource or external account was changed to bypass that.
No Supabase write, new analysis, provider call, real data or existing decision change.

Hashes detect accidental content/scope substitution under the trusted DB boundary;
they are not signatures against a privileged database administrator. The table is
synthetic-only, not an admission path for arbitrary real sources. No production
retention duration is invented; any purge/lifecycle implementation remains explicit.

Not yet closed: persisted reported/derived reconciliation and definition authority,
cross-period unresolved-findings propagation, memory/exports integration, professional
review of complete outputs. No FR07/FR08 full-case or Financial Reliability Gate PASS.

## Next integration proof, after durable checkpoint

1. Apply V35 ONCE in Pepperyn Integration Test only. It assumes V27's scope indexes;
   transaction aborts if preconditions/table creation fail. Do not rerun blindly.
2. Restart synthetic/mock backend with existing gates CLOSED. Enable the new frontend
   flag alongside the existing synthetic-demo flag; restart frontend. No new secret.
3. Open `/app/chat`, select an explicit synthetic client, choose the already registered
   `pepperyn_v1_heterogeneous_conflict.xlsx`; click the explicit source-save button ONCE.
4. Expect CONTRADICTION, retained values/references, persistent dossier ID, no analysis.
5. Reload/restart and reopen that client's same source dossier using read-only controls.
   Expect GET only and identical ID/source hash/claims; other clients must not show it.
6. Record actual SQL/live/visual evidence separately before claiming durable live proof.

Do not apply migration or perform capture merely because this protocol exists.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.
