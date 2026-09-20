# A24 / V36 - deployed privilege containment

Date: 2026-09-19. Status: LOCAL_POSTGRES_TESTED / INTEGRATION_DEPLOYED_CATALOG_VERIFIED / NOT_CHECKPOINTED.
External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## Why / before

The backend's ownership checks cannot protect a table or SECURITY DEFINER RPC
that a browser can access directly with Supabase client roles. A two-CFO beta
must close both paths before asserting adversarial isolation. This is not a
new business capability and does not change doctrine or admit real data.

Agent observed the authenticated Supabase UI for Pepperyn Integration Test,
project `ejixkplrgobgwqnhidwt`. SQL Editor queries used BEGIN READ ONLY and
ROLLBACK, catalog functions only. No application rows, account records, keys,
financial contents, or RPC bodies were read; no RPC was invoked.

Observed:

- Advisor: six RLS-disabled tables and one sensitive-column warning on analyses.
- `sessions`, `analyses`, `evidence_ledger_entries`, `arc_analysis_links`,
  `decision_arcs`, `knowledge_model`: RLS false, policy count zero.
- Effective anon/authenticated CRUD grants observed in the first metadata query
  for the visible results including analyses, links, arcs, ledger and knowledge.
  Do not claim an HTTP exploit was executed or data exfiltration established.
- All eight V36 target tables have effective service_role SELECT/INSERT/UPDATE/DELETE.
- `profiles`: RLS true; sole permissive PUBLIC ALL policy `(id = auth.uid())`,
  no explicit WITH CHECK. `companies`: same structure with `(admin_user_id = auth.uid())`.
  A null WITH CHECK is not an absent check: PostgreSQL reuses USING for ALL.
  It does not itself bind the profile's company_id to an authorized company.
- `create_entity_with_engagement(uuid,uuid,text,text,text,text)`: SECURITY DEFINER,
  executable by anon and authenticated. Current repository v19 accepts supplied
  scope and frontend never calls it; backend engagement service is its consumer.
- `persist_governed_analysis_v1` and `purge_pseudonymous_correspondence_v1`:
  client execution false. `handle_new_user`: trigger-returning function with
  client execution true; not equivalent to an ordinary callable RPC. Unchanged.

Inspection of frontend source found direct profile/company SELECT joins, legacy
messages reads and testimonial reads, but no direct writes to the eight targets
or calls to the restricted RPC. Deployed policy catalog showed no policies on
other tables referencing sessions/analyses/profiles in this bounded query.
Backend `get_supabase` service client uses SUPABASE_SERVICE_KEY. None of these
observations proves absence of other vulnerable RPCs, views or control-plane paths.

## Change / after intended

`backend/migrations/v36_confine_legacy_client_privileges.sql` atomically:

1. Requires exact existing tables, service capability, ordinary client roles,
   no policies on six backend-only tables and exact observed identity policies.
2. Removes PUBLIC/anon/authenticated table AND independent column grants on eight
   explicit tables; enables RLS; restores authenticated SELECT only on the two
   already-readable identity tables under unchanged own-row policies.
3. Removes client/PUBLIC execution of the exact entity-creation RPC. Preserves
   its pre-existing effective service execution through an explicit grant.
4. Checks effective rights including inherited grants and service continuity.
   Unexpected rights cause an exception and whole-transaction rollback.

No row insert/update/delete, table drop, policy replacement, function-body change,
default privilege change, Auth configuration, account creation or credential change.
No historical migration rewritten. Service bypass remains an explicit trust boundary:
backend tenant checks still mandatory. No FORCE RLS on owners. No claim that an
already-corrupted identity mapping has been audited or repaired.

## Local evidence

`backend/tests/test_v36_privileges.mjs`: 9 scenarios PASS using isolated PGlite
0.3.14 PostgreSQL engine, synthetic rows and two local claim identities. This is
actual local SQL execution, not regex-only evidence and not Supabase Auth/API proof.
Tests cover client SELECT/INSERT/UPDATE/DELETE denial, own-row reads, attempted
profile reassignment, service CRUD/RPC preservation, column grants, repeat execution,
unchanged row snapshots, postflight before/after, missing table, unexpected policy,
identity-policy drift, inherited grants and missing service permissions with rollback.

Reproduce with Node and the pinned PGlite package installed outside the repository:
`node backend/tests/test_v36_privileges.mjs <absolute-package-path>/dist/index.js`.
No package added to production dependencies; no DB connection or external model.
Backend regression: 56 PASS across synthetic routes, source dossiers, governed
portfolio and temporal continuity. Frontend: 115 PASS / 16 suites.

## Deployment protocol / stop boundaries

Next action is approval to apply this exact V36 migration to Integration Test only.
Do not apply to another project or production. Agent may execute via the already
authenticated SQL Editor once exact remote change is authorized; Founder need not
copy SQL, provide credentials or select technical alternatives.

- Reverify project name/reference before execution; no keys required.
- Execute migration once in its own query, complete BEGIN-to-COMMIT text.
- On any error stop; do not remove guards or retry blindly. If editor session
  remains in failed transaction, ROLLBACK only, then diagnose.
- On success execute `backend/sandbox/v36_privilege_postflight.sql` read-only.
  Require all table and RPC checks true. This is catalog proof only.
- Exercise actual own-client UI/backend read paths and then bounded adversarial
  requests using two distinct verified test users and synthetic scopes. No service
  key is a substitute for a user token. Never log credentials or response contents.
- Test foreign company/entity/engagement/analysis/dossier/history/export access,
  direct REST table access, RPC invocation and self-reassignment attempts, plus
  valid own-user paths. Writes require explicit bounded synthetic setup/protocol;
  do not mutate existing Founder evidence as a negative test.

No automatically executable rollback reopens the vulnerability. Failure during
migration rolls back transactionally. After commit, diagnose compatibility and use
a reviewed forward correction; any permissive reversal requires explicit security
approval. No existing business data is intentionally destroyed or rewritten.

## Remaining proof debt

V36 application and catalog postflight are now proven as recorded below.
Two-user identities/fixtures and credential custody must be established
without inferring permission to create accounts from an open dashboard session.
Full browser/API adversarial isolation, broader RPC/view/storage/default-grant
surface, prior identity integrity, production topology/RLS, financial professional
reliability, PG-3/PG-4 and Real-data Admission remain OPEN. Local claim-switch tests
are not actual two-user Supabase authentication. No Beta gate is closed here.

## Durability

Base HEAD `1bd73b2fa6649b6e9de44908064271506b1627f1`, following implementation
checkpoint `20900c097de48a7e281327853a1417f81f49608f`. Founder reported remote equality.
A24 local files await a later meaningful batch checkpoint. Generated
`frontend/next-env.d.ts` is pre-existing and intentionally untouched/excluded.

## Authorized deployment and live postflight - 2026-09-19

Founder explicitly authorized "GO application V36 sur Pepperyn Integration Test".
Agent checked project name and reference in the authenticated SQL Editor and
executed V36 once. File SHA-256:
`4BF56BA216F3B2B43493EB42CFF07DB626102C1EDA50FDA1B85403F5303F69CA`.
UI result: `Success. No rows returned`. No error or retry.

Immediately executed the versioned postflight SELECT in BEGIN READ ONLY / ROLLBACK.
Observed `phase=V36_CATALOG_POSTFLIGHT`, `table_checks_pass=true`,
`rpc_checks_pass=true`. For EACH of analyses, arc_analysis_links, companies,
decision_arcs, evidence_ledger_entries, knowledge_model, profiles and sessions:
table_present, rls_enabled, service_crud_preserved, identity_read_preserved,
policy_baseline_preserved, forbidden_table_grants_absent and
forbidden_column_grants_absent all true.
Postflight reports write_performed=false, application_rows_read=false,
two_user_adversarial_proof=false, production_proof=false. These last flags apply
to the inspection; the preceding migration DID change privileges and RLS.

Bounded post-deployment UI: localhost backend /health returned 200 and current
OpenAPI includes source attention/dossier routes. Portfolio initially displayed
source unavailable; a single read-only retry subsequently displayed the existing
Optilux Synthetic Internal Pilot conflict dossier with its exact ID, source hash,
REVENUE contradiction and no-resolution statement. Cause of the transient failure
not established; do not silently reinterpret it as a completed first-load PASS.
No source capture, analysis or business-write button used. This one-user rendering
does not prove two-user isolation, all routes/exports or security-gate closure.

Subsequent same-session read-only navigation to the exact synthetic client showed
the selected Optilux client, two existing history entries and the existing conflict
source dossier, with capture disabled and no file selected. No new write performed.

Next authorization boundary: two dedicated technical Supabase Auth users with
synthetic-only scopes, distinct from admitting the two professional Beta testers.
No new users, passwords, invitations or second sessions created during this slice.
Do not reuse service-role credentials as user credentials or treat local claim
switching as independent Auth sessions. Any technical-account provisioning needs
explicit account-access approval and secrets must stay local, never in evidence.

## Technical account preparation (authorized, not yet executed)

Founder authorized "GO comptes techniques d'isolation". Agent environment contains
neither Supabase key; no browser credential extraction or process-memory access used.
Prepared `scripts/provision-integration-isolation-a24.ps1` and
`backend/sandbox/provision_isolation_accounts.py` for one Founder-local execution.
Fixed target Integration Test, fixed non-deliverable technical emails
`pepperyn-isolation-a24-a@pepperyn-test.invalid` and
`pepperyn-isolation-a24-b@pepperyn-test.invalid`. These are NOT the approved professional
Beta testers and do not alter the Beta allowlist or signup configuration.

Admin create_user with email_confirm=true is deliberate test-account provisioning,
not a claim that a real mailbox was verified. No invite or sign_up method is used.
Reference: https://supabase.com/docs/reference/python/auth-admin-createuser
states create_user sends no confirmation email. New Auth users trigger the existing
company/profile/workspace/entity/engagement bootstrap; these are the only intended
new scopes. No financial data, analysis, decision or existing Founder row is changed.

48 random bytes per password; Windows DPAPI CurrentUser protects the bundle at
`Pepperyn-runtime/secrets/a24-isolation-accounts.dpapi`, outside Git and separate
from JWT/correspondence keys. The file is created exclusively, durably flushed and
decrypted/compared before network writes. Existing file refuses; partial/uncertain
create stops without retry, delete, overwrite or password reset. Preserve file on
failure for controlled recovery. No automatic purge or indefinite-retention claim.
Restore later with the same Windows account and entropy
`Pepperyn|IntegrationTest|A24IsolationAccounts|v1`; never print decrypted contents.
Service/anon keys are reused from local process or requested through masked prompts,
never persisted by this script. Password tokens are never output. Temporary child
process variables are restored; backend process/environment is not modified.

Each created user signs in independently through an anon-key client; get_user
checks the identity; own profile/company/primary entity reads verify the automatic
scope. Distinct user/company/entity tuples required. This is provisioning and own
scope verification, NOT cross-user adversarial proof, and creates no provider use.

Validation: Windows PowerShell parser and -CheckOnly PASS (no secrets/network/writes).
Three unittest methods / eight mock scenarios PASS: valid path, wrong project,
wrong purpose, missing custody attestation, second-create timeout, foreign Auth
identity, foreign company ownership, absent bootstrap. Live execution PENDING.
No test output is treated as remote creation. Next blocker is local credential
entry/execution by Founder; no additional architectural decision is needed.

## Founder provisioning result and bounded read rehearsal preparation

Founder reports `A24_TECHNICAL_ACCOUNTS: CREATED_AND_SCOPE_VERIFIED` and
`WINDOWS_DPAPI_CURRENT_USER: PASS`. Accept as Founder-run live provisioning evidence;
not an agent-observed two-user adversarial PASS. No provisioning rerun permitted.

Prepared `backend/sandbox/verify_isolation_accounts.py` with
`scripts/verify-integration-isolation-a24.ps1`. Restore existing DPAPI bundle only;
no regeneration, overwrite, reset or service key. Two actual Auth password logins
create sessions (therefore not globally zero writes); all subsequent probes are GET,
no business writes, provider, analysis or export generation. Fixed Integration Test
and loopback backend origins; direct GET transport refuses redirects.

Bounded proof sought: own populated profile/company/entity for both identities;
foreign profile/company/entity filtered empty in both directions; all six protected
tables reject direct REST SELECT with SQL 42501 (limit=0, no row disclosure); backend
entity list remains own-only even with foreign company/entity query parameters;
anonymous backend entity list refused. Positive own reads distinguish isolation
from blanket outage. Any 5xx, unrelated denial or foreign row fails the suite;
response bodies, tokens, passwords and IDs are not printed.

Mocks: five unittest methods cover 15 scenarios across provisioning and read runner,
including foreign rows, permissive access, backend cross-scope substitution, outage
and unrelated 403. Windows PowerShell parser and CheckOnly PASS. Read suite NOT LIVE
EXECUTED. Requires Founder-local key/custody execution; account creation not repeated.

This does not test write attempts, privileged RPC invocation, populated cross-user
analyses/exports/dossiers or browser-session separation. Existing designated-company
synthetic V1 gates are not broadened to admit these technical accounts. Inspection
also found legacy history catches errors and returns empty lists; such responses
cannot prove successful access/isolation and are intentionally not promoted by this
suite. Wider failure semantics and populated-output probes remain explicit debt.

## Founder live read rehearsal - 2026-09-20

After backend restart with the existing DPAPI JWT (no rotation), Founder executed
the hash-guarded read rehearsal once and reported:
`BOUNDED_TWO_USER_READ_ISOLATION_PASS`, `EXISTING_DPAPI_UNCHANGED: PASS`.
The runner's positive own-scope and bilateral negative read checks described above
are now FOUNDER_RUN_LIVE_PROVEN for these two technical accounts in Integration Test.
This is not an agent-captured HTTP trace or proof for the professional Beta users.
No secret was transmitted in chat. No account reprovisioning or business write.

Explicit returned limits: global_isolation_proven=false, write_isolation_proven=false,
analysis_export_isolation_proven=false, production_proof=false. External Provider
and Real-data Admission CLOSED. Self-Selling DEFERRED. Remaining debts above unchanged.

V36 is deployed while the implementation/protocol/evidence lot is still uncommitted.
A grouped durability checkpoint is now required before adding a new implementation
slice. Next technical priority: reliable history failure/ownership semantics before
using populated history and financial output paths as isolation evidence. Never
count legacy empty-on-error history as a successful isolation negative control.
