# B1 prerequisite — unavailable memory is not absent memory

2026-09-24. Base: c4b414f17f63025032943159bc121c5901f65225.
Status: local implementation/test evidence; not deployed or browser-proven.

## Why / before / after

A CFO must not be invited to repeat an intention, decision, follow-up or execution
because a registry read failed. The integrity-checked financial analysis remains
independently readable; its historical recommendations are not current memory.

Before: decision_feedback outages were caught and converted into empty feedback.
The comment called this UNKNOWN, but the payload/UI did not distinguish it from
verified absence. Follow-up, execution and prerequisite outages were also caught;
even governed exports could silently omit those parts of the memory.

After: persisted recommendation projections explicitly carry AVAILABLE or
UNAVAILABLE. A failed necessary registry read, malformed response, or ambiguous
child binding returns no partial lifecycle state. The UI preserves recommendation
text, rationale, validations and fact references, labels memory unknown and exposes
no mutation form. Reopening after recovery re-reads the authoritative state.
The three governed exports refuse with 503 rather than present partial memory.
Database exception contents are not logged by this projection.

No recommendation becomes a decision. No record is edited, deleted or migrated.
Independent governed-analysis integrity and ownership checks remain in place.
The no-database recommendation helper remains an immutable recommendation identity
projection for existing write validation/new-analysis paths; it is not evidence
of a successful persisted-memory read. Existing write authority checks are unchanged.

## Evidence and limits

Tests in backend/tests/test_v1_synthetic_routes.py inject outages in each of the
four registries, assert analysis remains readable, all three exports refuse,
database state stays unchanged, and exception context does not leak into logs.
Malformed primary responses are not treated as absence. Existing lifecycle and
output ownership regressions remain part of the targeted suite.
Frontend FeedbackCard test asserts unknown state, retained prerequisite context,
no buttons and no misleading absence-of-decision claim.

Final local validation: 60 backend tests PASS across synthetic routes, exports,
output isolation, V28–V32 and Private Beta admission; 17 frontend suites / 121
tests PASS; TypeScript no-emit PASS. The first wider backend run hit Windows
temporary-directory permissions (39 PASS, one setup error); the final run used a
fresh explicitly scoped temporary directory and passed. No failing assertion was
waived. Duplicate/foreign child bindings are refused rather than silently selected.

This is a reusable terminal contract prerequisite for B1, implemented in the
existing designated synthetic surface. It is NOT the generic Beta ingestion path,
an end-to-end FR01–FR12 execution, live outage proof, two-user browser proof, or a
gate closure. FR-EXPECTED-2 is unchanged. No provider or real data was used.

External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.
Local changes pending a grouped durability checkpoint.

Durability update: Founder confirmed d01851f7f86de47a0ccca3a4cb4cbde0f31da443
synchronized. Subsequent local B1 refactoring relocates the same projection to
services/governed_memory_read.py behind the ownership-checked application read;
the router keeps a compatibility wrapper. See INSIGHT_SHAPER_B1_SHARED_READ_BOUNDARY.md.
