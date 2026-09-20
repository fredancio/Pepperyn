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

Supporting local evidence A13/A14: backend verified-user allowlist and frontend
signup-route restriction implemented/tested, not enabled or deployed. This does
not establish effective production Auth, two-user isolation, RLS or signup settings.
The gate status remains unchanged; see Canon 13 and execution evidence 24.

2026-09-19 A24: live Integration Test catalog inspection found six backend tables
without RLS, broad client grants and an exposed SECURITY DEFINER entity-creation
RPC. V36 containment prepared and tested on local PostgreSQL semantics; NOT DEPLOYED.
Identity reads preserved while client identity writes are denied by the candidate.
No actual two-user Supabase adversarial or production PASS. Deployment approval
and postflight remain necessary. See `docs/Security/PEPPERYN_V36_PRIVILEGE_CONTAINMENT_A24.md`.

Subsequent authorized deployment 2026-09-19: V36 executed once in Integration Test;
eight-table and RPC catalog postflight PASS. This supersedes NOT DEPLOYED above,
not the absent two-user/production proof. Scope/hash and transient initial UI read
failure followed by successful read-only retry recorded in the same evidence file.

2026-09-20: Founder-run two-technical-user read suite PASS on Integration Test.
Positive own profiles/companies/entities, cross-user RLS reads, direct protected
table denial and bounded entity API substitution tested. Not write/financial-output
or production proof; Production Security Gate remains NOT PASS.
