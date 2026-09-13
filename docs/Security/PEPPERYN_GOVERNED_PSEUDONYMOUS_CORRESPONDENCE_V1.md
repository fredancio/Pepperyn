# Pepperyn — Governed Pseudonymous Correspondence V1

**Date:** 2026-09-13
**Status:** implemented and live-rehearsed with one synthetic mapping; not connected to real-data or provider transport

## 1. Preserved invariant

A real identity remains pseudonymously stable only inside the Pepperyn client
boundary that legitimately needs continuity. The same real identity produces
an unrelated pseudonym in another company or entity boundary. No V1 provider
task requires the real identity.

This is pseudonymization, not GDPR anonymization: Pepperyn retains a protected
means of re-identification. Exact financial patterns and indirect identifiers
remain sensitive and D10 remains a separate mandatory provider gate.

## 2. Implemented contract

- Scope is `(company_id, entity_id)`. An analysis binding records every
  governed analysis currently depending on a mapping. This gives continuity
  across periods for one client without creating cross-client correlation.
- The stable pseudonym is a category plus the first 64 bits of a
  scope-bound HMAC-SHA-256 fingerprint. The real identity is never stored as
  plaintext or placed in the pseudonym.
- The real value is encrypted with AES-256-GCM, a fresh 96-bit nonce and
  authenticated associated data binding record ID, scope, category,
  pseudonym, mapping version and crypto version.
- Encryption, pseudonym and opaque-handle keys are independently domain-
  separated from one 256-bit server secret. That secret is distinct from
  database credentials and is loaded only from
  `PEPPERYN_CORRESPONDENCE_KEY` as URL-safe base64.
- Ciphertext SHA-256, AEAD authentication, scope-bound fingerprint, crypto
  version and mapping version are all verified before local rehydration.
- Handles are encrypted/authenticated, contain no real value, expire within
  five minutes and are bound to exact tenant, entity, record and version.
- Callers receive only pseudonym plus opaque handle. Mapping resolution and
  recursive replacement remain inside `GovernedCorrespondenceRegistry`.
- Database tables are backend-only with RLS, immutable mapping rows and no
  UPDATE/DELETE table grant. Bindings are exact analysis/company/entity
  foreign keys. Purge uses a scoped service-role RPC and is refused while any
  analysis binding exists.

## 3. Lifecycle without invented retention periods

The kernel contains no default retention duration. Purge requires both:

1. zero authoritative analysis bindings; and
2. an injected `PurgePolicy` that explicitly authorizes removal.

The future policy may consider evidence, temporal continuity, decisions,
actions and legal/product retention obligations. Until such a policy exists,
the default is fail closed (`PURGE_POLICY_REQUIRED`). No permanent CRM record
is created by this contract.

Canonicalization of two differently written names as the same real-world
identity remains upstream identity-resolution work. This registry guarantees
stability for the same registered identity value; it does not guess that two
strings designate one party.

## 4. Falsification evidence

Eleven deterministic falsifications cover:

- same-client stability across two analyses and independently constructed
  registry instances sharing durable storage (restart/multi-worker model);
- a second-process verification path that performs no insert or binding write;
- second-process verification of a Unicode identity without writing;
- preservation of named fail-closed repository refusals;
- different pseudonyms and fingerprints for the same counterparty across
  different entities and tenants;
- absence of plaintext identity from the stored record;
- ciphertext corruption, handle tampering, wrong scope, wrong key and mapping
  version mismatch failing closed;
- purge refusal without policy and while an analysis reference remains;
- RLS, backend-only grants, immutability and binding guard in migration V33;
- absence of provider, network or egress dependencies from the component.

Migration V33 was applied to Supabase Pepperyn Integration Test on 2026-09-13
with `Success. No rows returned`; no mapping or interface action accompanied
deployment. A later bounded rehearsal created exactly one synthetic mapping
and one exact analysis binding for governed analysis
`75132a71-c80c-4469-aba8-5171d947a9d0`.

A separate process then inspected the deployed schema and bounded state in
strict read-only mode: all eleven required columns were available, mapping
count was one, binding count was one, and no write was performed. A corrected
second-process verification subsequently returned `PASS` with stable
pseudonym `COUNTERPARTY-5B65AC12649E48F1`, successful local rehydration,
`external_provider_used=false` and `real_identity_used=false`. The verification
path neither registered nor bound another record. This proves continuity
through process restart and the shared Supabase repository used by independent
workers for this synthetic record.

The rehearsal exposed and corrected two harness/runtime defects without
altering persisted state: verification originally reused the registration
operation, and secure comparison of a Unicode identity used an unsupported
non-ASCII string form. Verification is now read-only and comparison uses
canonical UTF-8 bytes. A hard-coded shell status emitted after an earlier
failure was explicitly rejected as evidence and is not part of this verdict.

## 5. Deliberately not implemented

- no connection to the real upload, analysis, chat or provider path;
- no real-data admission and no provider transport;
- no D10 combination-identification decision;
- no task-specific minimum provider projections or `BOUNDED_TEXT` renderer;
- no legal retention duration, key rotation ceremony or production key store;
- no claim that historical in-memory mappings have been migrated;
- no provider-response user-output safety promotion.

The live rehearsal does not prove D10, task-specific minimization, the complete
provider-egress contract, production key custody/rotation, PG-3, PG-4 or
Real-data Admission. It uses exclusively synthetic identity material and does
not authorize provider activation.

Before provider activation, the complete chain must separately prove:

`real identity → governed registry → minimized pseudonymous projection → egress authority → untrusted provider response → authorized local rehydration`.

PG-3/PG-4 and Real-data admission remain CLOSED.
