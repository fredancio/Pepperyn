# Production and infrastructure

## Evidence rule

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

`DEVELOPMENT -> INTEGRATION TEST -> STAGING/PRIVATE BETA VALIDATION -> PRODUCTION -> www.pepperyn.com`

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
