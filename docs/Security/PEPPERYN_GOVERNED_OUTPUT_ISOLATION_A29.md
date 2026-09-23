# A29 — bounded governed analysis/export ownership rehearsal

Status: LOCAL_TESTED; real-session execution pending. External Provider and
Real-data Admission CLOSED. No deployment or business mutation authorized here.

## Why / before / after

A26 proved populated histories; A28 proved two legacy unsure writes, not output
isolation. Governed GET routes require one designated synthetic company. Removing
that guard or treating two guard-generated 404s as ownership proof is forbidden.
No product route or guard is changed. This isolated harness mounts only the four
existing analysis/XLSX/PDF/PPTX GET routes. Each sequential phase designates exactly
one already verified A24 company inside the disposable Python process. The open
backend on port 8000 and its environment are untouched.

Real Supabase user sessions and existing A26 records are used for the protected
run; no auth resolver or ownership check is mocked there. The service factory is
wrapped with a read-only method allowlist. Only reference/auth reads are allowed;
no insert/update/delete/upsert/RPC or product write route is exposed. Signing in
creates authentication sessions, not business data. No files are exported to disk.
Existing JWT and A24 secrets are restored from their separate DPAPI files; V33 is
untouched. Missing Supabase keys are entered masked. No credential regeneration.

## Positive-first contract

Two stable A26 IDs and exact technical ownership/entity markers are verified.
For each admitted user and each of four outputs: own response must be 200;
exports must parse as actual XLSX/PDF/PPTX; content must include own durable UUID
and exclude foreign UUID. Then the SAME admitted user requests the foreign ID:
404 Analyse introuvable is required, proving passage beyond designation to the
ownership loader. Other-user requests must give designation 404, and anonymous
requests 401. Expected totals: eight positive outputs and twenty-four denials.
One unexpected result refuses the run; no retry, fixture repair or reseeding.

## Calibration

This exercises actual route functions over in-process ASGI, actual Supabase
sessions/persistence in the protected run, and deterministic export parsers.
It does NOT prove the running Uvicorn transport, its middleware, browser flow,
deployed production RLS, global isolation, concurrent multi-tenant serving,
render quality or professional financial reliability. A26 fixtures share
synthetic financial content: the check proves scoped identity/provenance, not
arbitrary distinguishable financial-content noninterference. No gate is closed
globally; live_server_transport_proven remains false even on bounded PASS.

Local tests use auth/database doubles, real route functions and export parsers;
these are not real-session evidence. Existing A26 and A28 rows remain preserved.

## Execution

scripts/verify-governed-outputs-a29.ps1 restores existing protected credentials
and verifies the Python runner hash. -CheckOnly verifies existence/integrity
without secret reads or network; PASS obtained. Founder execution is needed for
CurrentUser DPAPI and masked local keys. No backend restart is needed.

Final local regression: 45 tests PASS across A29, V1 routes, governed exports and
temporal exports. No real-session A29 result yet; no global claim.

## Founder A29 result — 2026-09-23

BOUNDED_A29_ASGI_OUTPUT_ISOLATION_PASS: eight positive outputs, twenty-four
denials, real user sessions and persisted A26, no business writes, DPAPI unchanged.
live_server_transport_proven=false; global/write/production proof=false;
external_provider_used=false; real_data_used=false. This supersedes pending A29
execution only. No replay after PASS. Fixtures/feedbacks preserved.

## A30 — transport delta, prepared not live-proven

The next runner uses a temporary 127.0.0.1 ephemeral socket, Uvicorn, main.app,
its lifespan and middleware. Private Beta is enabled for exactly the two already
verified technical IDs. The service read-only adapter remains; an outer allowlist
admits only GET/OPTIONS on health and the four output paths for exact A26 IDs.
No route ownership or single-designated-company guard is replaced. Designation
changes sequentially inside this disposable process, never on backend port 8000.
The socket/server is stopped in finally. No business write route is reachable.

Expected A30: eight positive outputs and twenty-four denials with real sessions,
live_server_transport_proven=true ONLY for this temporary loopback read surface.
It does not prove port 8000 configuration, browser/CORS journeys, production,
simultaneous multi-company operation, global isolation or general write safety.
The outer read allowlist and read-only service adapter are explicit test-specific
containment, not evidence that every production route is safe.

62 local tests PASS including socket release, disallowed methods/paths, product
Private Beta middleware and export regressions. A30 wrapper CheckOnly PASS.
Actual protected execution remains pending. A29 old source hash is obsolete:
do not rerun A29. Use only integrity-checked verify-governed-outputs-a30.ps1.
Existing DPAPI/JWT reused, no key generation, V33 untouched, both gates CLOSED.

## Founder A30 result — 2026-09-23

Executed once: BOUNDED_A30_UVICORN_OUTPUT_ISOLATION_PASS, 8 positive outputs,
24 denials. Scope REAL_SESSIONS_A26_TEMPORARY_LOOPBACK_UVICORN_READ_SURFACE.
live_server_transport_proven=true only in that scope. No business writes, real
data or external provider; global/write/production proof=false. DPAPI unchanged.
This supersedes A30 pending execution, not normal-server/browser proof debt.

Next: actual browser navigation/history/reload/download, not another equivalent
HTTP matrix. Availability check: port 8000 health reachable (development);
in-app browser http://127.0.0.1:3000/app/chat refused connection. Frontend start
and its locally held public Supabase configuration are required before browser
work. No browser PASS, no automatic login or session injection, no new analysis.
