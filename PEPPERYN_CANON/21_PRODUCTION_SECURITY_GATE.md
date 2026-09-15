# Production Security Gate

## Scope

The gate applies to the exact production topology and revision intended for the
two-user Private Beta. Development and Integration Test evidence is supporting,
not substitutive.

## Required controls and evidence

- authentication, session and account lifecycle;
- exact two-user authorization and admin separation;
- tenant/company/entity/engagement/analysis isolation;
- Supabase RLS, table/RPC/storage privileges and service-role confinement;
- backend endpoint authorization and IDOR/BOLA falsification;
- upload validation, size/type limits, malicious OOXML/archive handling;
- input validation, injection, XSS, CSRF where applicable and CORS allowlist;
- rate limits and multi-worker abuse resistance;
- dependency vulnerability and build integrity review;
- secret management and absence from Git/frontend/logs;
- production correspondence-key custody, rotation, backup and recovery;
- provider credentials, policy, egress and response governance;
- rehydration authority and REIDENTIFIED re-egress prohibition;
- logging/observability privacy review;
- backup, restore, deletion, retention and disaster recovery;
- multi-tenant adversarial testing;
- TLS/domain/DNS and deployment rollback.

OWASP ASVS may organize the verification, but every PASS must refer to Pepperyn's
actual topology and evidence. Critical/high findings must be closed or explicitly
accepted by the Founder where acceptance is legally and ethically permissible.

**Current status:** `DEFINED AT CONTROL LEVEL / NOT EXECUTED / NOT PASS`.
