# A27 — Legacy feedback write authority

## Classification and stop condition

FIX-BLOCKER for two-user Private Beta. An authenticated caller must not attach
feedback to another tenant's report or bypass the governed decision lifecycle.
Completion requires local falsification, deployed database containment and bounded
two-user adversarial verification; local tests alone do not close write isolation.

## Baseline and diagnosis — 2026-09-21

A26 checkpoint HEAD is `4094416b69ec0e3af893ab56f65238edc2eb2196`, synchronized
according to Founder. Its populated-history proof remains bounded to two seeded
histories; neither pair was modified or repopulated. `frontend/next-env.d.ts`
remains excluded and untouched.

Legacy POST `/api/decision-feedback` previously passed caller report and
recommendation fields to a privileged upsert without report ownership validation.
Its subsequent pattern/arc side effects could therefore be reached without that
authority. The shared upsert is also used by the separately authorized V1 intention
route; changing that generic method would regress established V1 behavior.

Read-only catalog inspection performed through the authenticated Supabase SQL
Editor, visibly Pepperyn Integration Test / `ejixkplrgobgwqnhidwt`, query
`480a2186-b88c-4ebb-8b1d-8ec8b46f86ff`. Transaction BEGIN READ ONLY / ROLLBACK;
no application rows read or changed. Observed:

- `decision_feedback` RLS enabled;
- sole ALL/PUBLIC policy `decision_feedback_company_own`, USING and WITH CHECK
  require company_id in companies owned by auth.uid(); no report ownership check;
- anon/authenticated/service_role each have effective INSERT/UPDATE/DELETE;
- separate company and report foreign keys, no composite report/company binding;
- V29 explicit-decision checks present, but do not establish caller authority.

This establishes a deployed control gap, not a successful exploitation. Anonymous
effective grants do not themselves imply anonymous row access through RLS. No
adversarial write was attempted. Existing V36 scope did not include this table.

## Local correction

`DecisionMemoryService.upsert_legacy_feedback` validates exact owned completed
analysis, refuses governed envelopes, derives recommendation ID/text/source from
persisted analysis, and refuses an existing foreign feedback binding. Missing or
foreign report is 404; governed/mismatched recommendation is 409; unavailable or
malformed dependency is sanitized 503. Guards precede upsert, patterns and arcs.
Generic `upsert_feedback` and the proven V1 route remain unchanged. Legacy valid
feedback is retained; no new analysis or decision semantics introduced.

V37 prepared, NOT APPLIED: revoke client/PUBLIC write-related table and column
privileges on decision_feedback only. Preserve SELECT, RLS policies and existing
service CRUD. Transactional preconditions and effective privilege postconditions
refuse inherited-grant drift; no row rewrite, deletion, seed or permissive rollback.
Frontend search found no direct decision_feedback database consumer.

## Validation and limits

Local synthetic HTTP tests: owned legacy success; foreign/missing report refusal;
governed planned-feedback bypass refusal; forged recommendation fields; incomplete
report; foreign existing feedback; each dependency unavailable. No live credentials.
Proportional suite includes V1 synthetic routes, decision-memory integrity repair
and history read boundary. Migration tests check static scope/guards only, not SQL
execution. Results recorded in Canon 24.

Remaining: V37 Founder deployment approval and actual PostgreSQL/postflight proof;
backend reload; bounded two-user negative POST and direct database denial proof;
positive authorized writes, concurrency/TOCTOU and broader analysis/export isolation.
No global isolation, RLS-production or professional reliability claim. Service-role
callers are privileged; this is not a composite-FK guarantee for all possible writers.
Do not run probes against an old backend or repeat A26 seed. Plan any mutation
rehearsal with explicit bounds and unchanged-state checks before execution.

External Provider CLOSED. Real-data Admission CLOSED. Self-Selling DEFERRED.
Local work NOT_CHECKPOINTED. No remote permission or business mutation performed.

## Authorized V37 deployment and bounded SQL proof — 2026-09-21

Founder GO authorizes only prepared V37 in Integration Test. Applied once via
SQL Editor query `5afade76-18e4-412e-ac8a-0c10593a8ae7`: Success. No rows returned.
This supersedes NOT_APPLIED and no remote permission change above. No application
data statement exists in V37; A26 pairs were not targeted or modified.

Independent read-only postflight query `16594972-1b1b-40a3-ac8e-885a8938a15f`:
RLS true; one policy retained; anon/authenticated effective INSERT/UPDATE/DELETE/
TRUNCATE/REFERENCES/TRIGGER false, column INSERT/UPDATE/REFERENCES false;
SELECT remains true subject to existing RLS. Service CRUD true. No business rows
read or written by catalog inspection. Production not touched.

SQL adversarial query `324cca49-abb0-43cb-b475-a0c1341c0c1e`, equivalent to
`backend/sandbox/v37_role_write_probe.sql`, resolved only the two exact A24
technical identities and set local authenticated role plus JWT claims; asserted
current_user/auth.uid. INSERT SELECT WHERE false, UPDATE WHERE false and DELETE
WHERE false all raised insufficient_privilege for each identity: six denials.
Transaction rolled back. Output V37_TWO_IDENTITIES_SQL_ROLE_DML_DENIED.
This is actual PostgreSQL role enforcement, NOT real JWT/PostgREST sessions,
cross-report ownership, positive writes or global write isolation proof.

Next protected-local runner: `scripts/verify-feedback-privileges-a27.ps1`, reuses
unchanged A24 DPAPI bundle and only anon key (masked local prompt when absent).
No service key/JWT guest/V33 key needed. Two real user logins; POST has NULL
company/report (NOT NULL required by deployed schema), PATCH/DELETE target NULL
primary key. Thus no business row may change even if permission enforcement fails.
Only HTTP403 + PostgreSQL42501 + exact table-permission denial qualify; unrelated
validation errors cannot PASS. Six probes, no retry. No Pepperyn backend restart
required for this direct-table layer. API tests remain separately pending.

49 local tests PASS plus PowerShell CheckOnly PASS. Actual user-session runner
NOT_EXECUTED: anon key absent from agent process. Founder local masked entry needed.
No account reset/creation, no A26 reseed, no data deletion. Local NOT_CHECKPOINTED.

## Founder real-session result — 2026-09-21

Executed once: BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS, six denied operations,
TWO_REAL_AUTHENTICATED_USER_SESSIONS, DECISION_FEEDBACK_DIRECT_TABLE_PRIVILEGES_ONLY.
DPAPI unchanged; business_write_performed false. This supersedes session-run
pending above, not API/global/positive-write debt. api_write_isolation_proven,
write_isolation_proven, analysis_export_isolation_proven, global_isolation_proven
and production_proof remain false. Evidence is Founder-reported live output.
Next API protocol: PEPPERYN_FEEDBACK_API_REHEARSAL_A28.md. No A26 modification.
