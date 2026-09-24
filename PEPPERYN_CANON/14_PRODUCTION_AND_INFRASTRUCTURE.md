# Production and infrastructure

## Evidence rule

Current Founder inventory/target update dated 2026-09-24 supersedes the unknown
inventory statements below only to the extent explicitly recorded here. It is
Founder-reported control-plane evidence, not an independent deployed security audit.

- Vercel Pepperyn project is connected to `fredancio/Pepperyn`; Production follows
  main; other branches are Preview; no custom staging; Production rolled back
  to an old revision. Previews/history preserved.
- Railway: worthy-light / Pepperyn Online at
  `pepperyn-production.up.railway.app`, US West, old Git deployment. Preserve it;
  no Beta secrets. fabulous-tranquility service Removed/pending deletion: do not
  delete or reuse as part of this decision.
- OVH: pepperyn.com holder Finflate SRL; domain, contacts, DNS, associations and
  Free Hosting frozen. Existing ns20/dns20 OVH DNS, Vercel www CNAME, apex A and
  redirect mechanism, MX/SPF/DKIM/DMARC/Resend records remain untouched. Domain
  expiry reported 2027-02-28. Free Hosting eu-west-gra reports 0 MB/0 DB/Git
  inactive; this is NOT proof of absent redirect/mail dependencies.
- Founder private-browser check 2026-09-23: apex and www return Vercel 404
  DEPLOYMENT_NOT_FOUND. Old public domain presence currently unavailable;
  alternate URLs/Previews not audited or declared debranded.
- insightshaper.com personally purchased through Founder's personal OVH account;
  new public/Beta target. No DNS/service configuration authorized yet.

Accepted minimal target: existing Integration Test unchanged; separate synthetic
staging with Vercel Preview/recipe branch, new EU Railway and EU Supabase; separate
Beta Vercel/EU Railway/EU Supabase and secrets. Region-specific provisioning and
effective safeguards remain to be verified. No new VPS or OVH application hosting.
Preserve public/mail availability; do not combine legacy-domain administrative
work with Beta release. Legacy domain recovery is no longer on B5's critical path.

Configuration files and historical deployment guides show capability or intent;
they do not prove the effective external configuration. Production must be
verified from the controlling services before release.

## Git/GitHub

- Current repository: `https://github.com/fredancio/Pepperyn.git`.
- Current branch at handover preparation: `work/synthetic-founder-rehearsal-v1`.
- Git/GitHub is authoritative for code and committed Canon.
- Active repository clones must not be stored in Dropbox/file-sync folders.
- Branch protection, backup/export and final production branch strategy remain
  to be verified.

## Supabase

- Confirmed environment: `Pepperyn Integration Test`, project previously
  evidenced as `ejixkplrgobgwqnhidwt`; it is not production.
- Used for database, authentication and governed persistence.
- Migrations through v34 exist; live application evidence is recorded for the
  later governed migrations in Integration Test.
- Production project, secrets, RLS/privilege audit, backup/restore, retention,
  deletion and migration promotion are open.

## Vercel

- `frontend/vercel.json` proves repository support for Vercel headers.
- It does not establish the current Vercel project, team ownership, environment
  variables, deployment branch, domain binding or production role.
- Current and target role: `UNKNOWN UNTIL CONTROL-PLANE VERIFIED`.

## Railway

- `backend/Procfile` provides `uvicorn main:app --host 0.0.0.0 --port $PORT`,
  compatible with a managed runtime such as Railway.
- No repository evidence proves the effective Railway project, service,
  variables, region, domain, deploy revision or whether Railway is still active.
- Current and target role: `UNKNOWN UNTIL CONTROL-PLANE VERIFIED`.

## OVH and DNS

- Founder states the Pepperyn domain is managed through OVH.
- `DEPLOIEMENT_VPS_OVH.md` is a historical deployment guide, not current-state
  proof; it proposes a VPS topology and contains placeholders.
- Effective DNS records, registrar access, VPS status, SSL termination and
  current `www.pepperyn.com` routing remain unknown.
- Production DNS changes require Founder approval.

## Required environment separation

`DEVELOPMENT -> INTEGRATION TEST -> STAGING/PRIVATE BETA VALIDATION -> PRODUCTION / PRIVATE BETA -> insightshaper.com`

This target supersedes DEC-016's historical www.pepperyn.com destination, without
altering the environment-isolation requirement or authorizing activation.

Each environment requires separate database, secrets, provider policy,
correspondence keys, logging/observability and deployment evidence. Integration
Test must never be promoted by renaming.

## Production evidence package

- exact deployed Git revision and reproducible build;
- inventory of environment variables without secret values;
- database/migration/RLS/privilege attestation;
- authentication and exact beta-user authorization;
- key custody/rotation/recovery;
- domain, DNS and TLS evidence;
- health, rollback and recovery rehearsal;
- private logging/observability validation;
- backup, restore and deletion rehearsal;
- deployed debranding and security-gate evidence.
