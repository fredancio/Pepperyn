# B1 — shared governed application read boundary

2026-09-24. Base d01851f7f86de47a0ccca3a4cb4cbde0f31da443.
Status: IMPLEMENTED / LOCAL_TESTED / NOT LIVE_PROVEN; B1 remains OPEN.

## Purpose and change

BEFORE: ownership resolution and lifecycle projection were implemented inside
the designated synthetic router. Moving that entire router into production would
also move its fixture/demo assumptions and weaken its intentional admission boundary.

AFTER: services/governed_analysis_read.py provides a reusable application read
without fixture, provider, HTTP or sandbox imports. It receives the company from
server-side authentication, verifies analysis/company, entity/company and the unique
engagement, then loads the exact integrity-checked governed envelope. It never
falls back to legacy analyse_json. The fresh compatibility result retains analysis
identity and governed facts; lifecycle state is projected only after ownership
and integrity succeed.

services/governed_memory_read.py holds the existing memory projection, including
explicit UNAVAILABLE state and strict export refusal. It is an internal helper
for an already authorized envelope, NOT an independent public authorization API.
Passing an arbitrary company string is not authentication. Any future transport
must derive it from its authenticated session and enforce admission separately.

The existing synthetic router delegates to these services. Authentication,
designated-company checks, startup mounting and all write operations remain
unchanged. No generic HTTP route is mounted or newly opened. Export renderers stay
synthetic-only and retain their existing disclosure text. No data or migrations
changed. Analysis lookup outages/integrity errors now return 503 rather than
misrepresenting an unavailable record as not found; foreign/missing ownership
remains opaque 404. Raw exception content is not returned.

## Local falsification / regression

88 tests PASS: shared reads, governed persistence, synthetic routes, exports,
output isolation, V28–V32, Beta admission and temporal continuity.

New application tests cover two distinct mocked persisted scopes without demo or
designated-company environment flags; own reads succeed and cross-company reads
fail. Database snapshots remain unchanged. Additional checks cover failure at
each ownership/persistence lookup, corrupted envelope integrity with a tempting
legacy fallback, invalid identifiers and ambiguous engagement selection.
Existing route/output regressions continue to enforce the designated-client guard.

This is NOT a new live two-user proof, actual Supabase/RLS proof, provider proof,
generic financial analysis or professional Financial Reliability Gate execution.
No new FR-EXPECTED-2 expected result or scenario-specific runtime logic was added.

## Next implementation boundary / no premature promotion

The service is reusable outside the sandbox; the product route is not yet a Beta
path. B1 still requires governed generic ingestion and authorized persistence,
source/period/definition handling and terminal composition with B2/B3 protections.
Do not activate a route merely because its read service is reusable.

Current governed envelopes do not themselves attest an execution provider/data
origin. Existing sandbox exports contain fixed synthetic/local-mock/no-network
disclosures supported by that closed workflow. Do not reuse those disclosures for
arbitrary future envelopes or infer them from a filename/flag. Durable execution
provenance and its authority must be designed before generic export activation;
historical records must not be retro-certified. This is a technical B1/B3 task,
not a request to open a provider or to ask the Founder to choose a schema.

Production-mode routing, generic ingestion, actual task privacy coverage and all
professional output acceptance remain open. External Provider CLOSED; Real-data
Admission CLOSED; Self-Selling DEFERRED. Local changes awaiting grouped checkpoint.
