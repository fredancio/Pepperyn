# PPR-069 exact two-policy history protocol amendment

LOCAL ONLY. No Attempt 6, new execution identity, expiry, SQL/runtime or GO.
Version: v41-disabled-history-2. Baseline: 4ba6b02bb1ec15fb4252c7b1ee2f8c4fe009bec3.
This prospective amendment does not rewrite any prior protocol or evidence.

## Exact expected historical set

Exactly these two IDs, each enabled=false:

- 5cf919e2-77e3-46ce-ab0e-c237d62cfe2d.
- f6b1732f-e558-47a0-9106-f0b3e53c3b05.

For EACH policy, independently require exact specification, contract binding,
contract_binding_text and contract_binding_sha256; forbid extra/missing columns
other than the required created_at column. No >=2, ignored extra row or latest
resolution. Canonical contract text SHA-256:
CDC4BC07EA6F67275B985E76B24467CC3A1A11891EFA1953E0F6137344F73645.
Policy evidence field, from existing frozen owner SQL contract:
A225EF5B20CF9FF143D9C7C5EF2713458839478163571040233A69747E0F8798.
Complete expected specification, Python canonical JSON SHA-256:
BA1B898959C6959F72DCE8E2A5B788EF78E2BBC7228A548911915B412B28F44E.
These are distinct digest representations, not interchangeable checksums.

The six pre-existing tables and their catalog baseline remain the accepted
Attempt 4 snapshot, unchanged. The new structural expectation changes only
policy_rows from 1 to 2; admission_rows=receipt_rows=0. All function, permission,
RLS, binding and scope checks remain exact. Historical analysis IDs
07efdcad-de84-489e-890d-1709b44ef087 and
9a2fb8cf-1e0a-4ce6-b3f6-1d865072efcd must still have no corresponding outputs.

## Temporal and evidence qualification

Previous postcontrols attest checked fields, not all-column row hashes. No
created_at value or full-row remote hash is invented. A future authorized
precontrol must validate known fields, capture both complete rows (including
created_at), and bind them into its single timestamped JSON. Its accepted result,
SQL, manifest and canonical historical-row digest are frozen in an attestation
schema v41-two-policy-attestation-1. Unknown/missing attestation refuses.
This is the FIRST complete-row baseline for subsequent comparisons, not proof
that previously unobserved columns never changed before that observation.

Pre-Auth reads must match that pinned baseline; the initial runtime snapshot
checks it again to close the observation/capture gap. Owner observation uses
exactly the two historical rows plus one current row. Post-insert validation
reuses that same observation, without an added policy poll. Disable observation,
independent recovery and final snapshot must preserve both historical rows.
No observation error proves absence. No timestamp representation fallback.

## Prospective integration contract

Future successor preparation must explicitly bind historical_policy_contract=
v41-disabled-history-2 into its manifest and pin the new code/protocol hashes.
The new SQL builders and runner branches require that version. Original
single-history manifests retain their old semantics and exact SQL output;
unknown versions fail closed. Do NOT use the historical owner-ack launcher or
publisher, whose pins intentionally refuse changed source. Future distinct
entrypoint must use the two-policy attestation verifier, including recovery;
its manifest reader must require the new version and exact SQL bytes.
Creating that entrypoint/manifest and freezing IDs is a separate next tranche.

Before any future launch, prepare and verify BOTH owner SQL transfers and BOTH
ack commands with their exact pins. Resolve transfer-specific representation
issues beforehand. At a live handoff, one SQL execution with unambiguous success
is immediately followed by its local ack, with no chat verification round trip.
The ack remains a local assertion; a single controlled remote observation is
mandatory. Disable deadline stays 1,200 seconds; no reset, extension or late ack.

I1-I18 unchanged. RecordingDb.auth delegates to the existing backend verifier.
10 effects / 5 new durable rows / 1 Auth; no refresh, retry, cleanup or fallback.
LOCAL_TEST_ADMISSION / INJECTED_LOCAL_ONLY / provider_execution_attested=false.
No new authority, provider, real data, admission or execution is granted.
B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. All previous failures remain NO PASS.
