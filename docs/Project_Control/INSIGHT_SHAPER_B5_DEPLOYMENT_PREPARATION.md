# B5 — deployment preparation, not deployment authorization

2026-09-24; repository inspected at c4b414f17f63025032943159bc121c5901f65225.
No cloud account, resource, key, DNS record or running service changed.

## Concrete repository constraint

backend/main.py recognizes production for API-documentation suppression and
physical exclusion of the synthetic router. private_beta_access.py requires two
distinct allowed users in production or when PEPPERYN_PRIVATE_BETA=1. The synthetic
router additionally requires ENVIRONMENT=development and its explicit demo flag.
Consequently, setting ENVIRONMENT=staging does NOT establish a hardened staging
policy and does NOT yield a working synthetic application. Do not use a new label
as an inferred security profile or relax the designated-client guard.

Production-mode frontend is already a restricted Beta surface through
frontend/lib/private-beta-policy.ts, but this is UX, not backend authorization.
frontend/lib/supabase.ts needs both NEXT_PUBLIC_SUPABASE_URL and the public anon
key at build time. A frontend built for Integration Test is not a Beta artifact.
backend/Procfile starts main:app with the platform port; it does not enforce
environment separation. Existing Vercel headers prove no deployment topology.

## Minimum promotion recipe to prepare before requesting provisioning

| Boundary | Required configuration/evidence |
|---|---|
| Integration Test | Preserve existing project, credentials, rows and development synthetic surface |
| Staging | Separate EU Supabase/Railway and Vercel Preview; production security mode, technical synthetic users, no real data |
| Private Beta | Separate EU Supabase/Railway and Vercel frontend; production security mode, exactly Founder and authorized partner after B6 approval |
| Public target | insightshaper.com only after explicit DNS/activation approval; pepperyn.com untouched |

For both future environments: ENVIRONMENT=production, PEPPERYN_PRIVATE_BETA=1,
two environment-specific PEPPERYN_BETA_USER_IDS; synthetic sandbox flags disabled.
This is a TARGET recipe, not a claim the present revision can serve the Golden
Workflow in that mode: B1 must first supply the governed non-sandbox path.
Synthetic staging fixtures will use that same generic path after it is available;
do not promote the current sandbox by changing its designation or environment test.

Pin frontend and backend to the same reviewed revision. Record resource IDs,
effective EU regions, revision/build identifiers, exact allowed CORS origin,
frontend API URL and Supabase URL. No wildcard origins or inherited Integration
Test variables. Store service credentials only on the backend. Public anon key is
not an authorization bypass; verify deployed grants/RLS and session ownership.
Keep private Beta secrets out of Preview and of the legacy Railway US West service.

Use separate JWT signing and correspondence keys under managed custody; never copy
local DPAPI files or V33/V34 keys. Key custody/restore approval remains B7, not a
configuration checkbox. Do not put provider credentials in either environment while
the Provider Gate is closed. No env flag can independently authorize real data.

Before traffic/admission: verify Auth public signup disabled, allowed redirect URLs,
invite-only B6 flow, third-user denial, own/foreign histories/writes/exports/browser
access, all actual migrations and grants, closed provider transport, logs without
secrets, backup/restore/deletion, revision rollback and Financial Reliability Gate.
Migration promotion needs a reviewed dependency/order inventory; applying v1..v38
blindly to a fresh database is NOT an approved procedure. No database clone or
Integration Test business/account/correspondence copy is authorized.

## Ordering / authorization stop

Continue B1/B2/B3 locally now. Do not purchase staging merely to rediscover that
production-mode governed routes are absent. Before provisioning, present exact
resource/region/cost proposal and get Founder authorization. Before applying any
migrations, validate an empty-target plan and obtain the required remote-operation
approval. Public operator contact details are still required for publication, not
for this internal recipe. No partner account is created during preparation.

B5 remains PREPARED IN PART / NOT DEPLOYED / NOT PASS. No additional Axx proof is
created. External Provider and Real-data Admission remain CLOSED.
