# Private Beta plan

## Scope

- Tester 1: Frédéric Anciaux.
- Tester 2: one Fractional CFO design partner explicitly selected by Frédéric.
- No other user is authorized by default.
- No public signup, open registration, pricing, sale or Stripe dependency.

## Entry gates

All required gates in `12_V1_DEFINITION_OF_DONE.md` need evidence-bound PASS.
In particular: financial reliability, two-user isolation, production security,
provider/real-data gates, debranding, environment separation and recovery.

## Evaluation evidence

The Beta must measure professional correctness and correct refusal, continuity,
decision recall, client prioritization, analysis/reconstruction time, cognitive
load, traceability, trust and whether safe portfolio capacity improves.

## Access model

Authorization must be backend-enforced and configuration/role based. Founder or
admin identity must not be hard-coded into the frontend. The second CFO must not
inherit Frédéric's unauthorized tenant/client context.

## Implemented local admission boundary (A13/A14, not activated)

Backend: `ENVIRONMENT=production` always requires beta admission. Outside
production, `PEPPERYN_PRIVATE_BETA=1` explicitly enables it. Ordinary development
with flag absent/0 is unchanged. Invalid flag/configuration refuses. Backend-only
`PEPPERYN_BETA_USER_IDS` must contain exactly two distinct nonzero Supabase Auth
UUIDs, comma-separated. No Founder identity is hard-coded. Missing/invalid
production configuration refuses startup and HTTP requests. Never place this
configuration in frontend public variables or confuse it with tenant ownership.

Each protected HTTP request resolves the token through Supabase Auth get_user,
then checks the verified user ID against that list. Existing route authorization,
admin roles and tenant/entity/engagement controls still apply. GET /health is the
only unauthenticated application exemption with valid configuration; outer CORS
can answer preflight without invoking an endpoint. PIN login/sharing/update and
billing checkout/portal are unavailable in beta. No auth-service error or token
is returned/logged by this new boundary. This adds a Supabase Auth availability
dependency per request; failures refuse, with no cached admission fallback.

Frontend production (`NODE_ENV=production`) or nonzero server-only
`PEPPERYN_PRIVATE_BETA` blocks `/register` and `/checkout` (and descendants) with
403/no-store. Login/auth callback are unaffected. This is a web-route restriction,
NOT proof that direct Supabase signup, anonymous DB/storage access, public landing
page commercial copy or every legacy commercial surface has been disabled.

Before any activation: Founder selects the second tester; control-plane evidence
must show invitations/account IDs, no public signup, separate owned tenant/client
contexts, tested RLS/RPC/storage privileges, effective environment variables and
deployment revision. Test both users, a third user, anonymous/guest, expired and
revoked access, cross-user IDOR/BOLA, frontend route enforcement and rollback.
Do not enable live mode or provision users from these instructions alone. Provider,
real-data and production approvals remain independently required. No gate PASS.

## Professional login surface (A15, local evidence only)

A15 local implementation: `/login` resolves the same surface policy server-side
per request. In Beta it offers professional password login/recovery and invitation
notice, without guest PIN/signup/purchase prompts or an Administrator role label.
Login redirect is limited to chat/portfolio/settings in Beta. Authentication and
authorization remain unchanged. Production build and mocked UI tests PASS; actual
HTTP/browser/auth/account-lifecycle proof remains open (execution evidence 24).

## Non-goals (unchanged)

Sales, pricing, automated prospecting, public onboarding, broad commercial
analytics and Self-Selling are outside this Beta.
