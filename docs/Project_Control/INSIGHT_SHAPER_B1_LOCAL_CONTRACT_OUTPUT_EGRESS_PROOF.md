# Insight Shaper B1 — local contract, output and egress proof

**Status:** LOCAL PASS / NOT CHECKPOINTED / NOT DEPLOYED / PRODUCER UNADMITTED
**Evidence date:** 2026-09-29
**Evidence ID:** PPR-068

## Decision boundary

This proof covers the three deterministic post-V41 tranches authorized after the
consolidated Astra review. It does not deploy the PPR-067 hardening, register or
enable a remote policy, admit a producer, authorize external egress, attest an
OpenAI execution or admit real data. B1 remains OPEN.

The three boundaries remain distinct:

`Generic Producer Admission != External Egress Authorization != Attested Provider Execution`

## Exact local composition

The backend now composes one fixed historical V1 contract:

`governed source -> immutable facts schema -> positive projection -> frozen request -> V41 reserve/claim -> injected response capture -> validation -> backend-built analysis/envelope/receipt`

The historical V1 binding is a literal registry entry. It is not reconstructed
from the current models and no `latest` fallback exists. A current-model mutation
without a new version refuses candidate execution. The frozen request contains
only the governed source facts, invocation nonce and static task contract. Raw
bytes, tenant identifiers, authorization material and persistence capabilities
are excluded.

The V41 coordinator is not mounted. It accepts only the exact backend-selected
adapter type, rechecks actor/company and the frozen composition, performs one
reserve, one claim and one completion, and never retries an uncertain result.
The producer cannot provide analysis identity, scope, policy, admission,
provenance or persistence rows. An injected response remains explicitly
`provider_execution_attested=false`.

## PostgreSQL hardening and falsification

The undeployed PPR-067 successor now also binds the immutable policy evidence.
PostgreSQL computes the policy evidence digest from its own `jsonb` text
representation before reserve. Completion requires the same digest in the
receipt and recomputes it from the immutable policy. Python does not attempt to
reconstruct PostgreSQL `jsonb` serialization during reread.

Final isolated PostgreSQL selection:

- `test_generic_receipt_v3_postgres.py`;
- `test_post_v41_validation_postgres.py`;
- **187 PASS, zero skipped/not executed**, 388.45 seconds;
- container had no network and was stopped cleanly after the run.

The first full run after the policy-evidence extension produced 69 hardened
failures because the fixture used sorted Python JSON rather than PostgreSQL
`jsonb::text`. This was a test-fixture representation defect, not a product PASS.
The fixture now asks PostgreSQL to compute the digest, then uses the returned
value in the receipt. A focused 3-case check passed before the complete rerun.

The campaign covers valid composition, policy/scope substitution, all required
receipt fields, lexical digests, request mismatch, contract recombination,
source/task/version substitution, expiration, concurrency, replay, atomic late
failure and independent persisted-receipt reread. Refusals assert no result trio
and no misleading receipt.

## Versioned reread and terminal outputs

Owned reread dispatches V39, V40 and V41 explicitly and refuses ambiguous,
unknown, incomplete or inconsistent evidence. For V41 it verifies the exact
analysis, admission, policy, source, request, envelope and receipt bindings.
Policy evidence is checked against the receipt; its original database-side
derivation is trusted only because policy and receipt are immutable and the
completion function validates the digest atomically.

A fresh reader constructed only from persisted rows reproduces the V41 result.
The same server-owned provenance reaches the UI and XLSX/PDF/PPTX. Injected
responses state that no OpenAI execution is attested. A declared OpenAI transport
with `provider_execution_attested=false` is also displayed as non-attested and
can never acquire an attested label by inference.

## Global egress findings

The eight historical findings were reproduced as direct network imports in five
bounded sandbox modules:

- `output_live_transport.py`: `socket` and `httpx` (two);
- `preflight_connected_b1.py`: `httpx` (one);
- `rehearse_execution_receipt_v39.py`: `httpx` (one);
- `verify_feedback_privileges.py`: two `urllib` imports (two);
- `verify_isolation_accounts.py`: `httpx` plus `urllib.parse` (two).

They were not globally whitelisted. All five callers now use one content-pinned
test capability that accepts only the exact Integration Test Supabase origin and
`/rest/v1/` or `/auth/v1/` paths, plus two exact loopback read paths. Redirects,
environment proxies and automatic retries are disabled. Product services cannot
import that capability. The loopback Uvicorn helper no longer owns a network
import. The existing registered synthetic provider sandbox remains separately
content-pinned and is not reachable from the new V41 coordinator.

Global egress verification:

- repository egress suite: **36 PASS**, including the repository-wide scan;
- adjacent bounded transport/rehearsal selection: **61 PASS plus 7 subtests**;
- no provider request, remote request or credential use occurred.

This closes the eight-finding static debt locally. It does not authorize any
external transport or establish provider-policy compliance.

## Other executed validation

- targeted backend contract/admission/reread/output/egress selection: **223 PASS**;
- final coordinator plus V41 output selection: **58 PASS**;
- frontend V39/V40/V41 provenance: **7 PASS**;
- TypeScript `tsc --noEmit`: PASS;
- known `.pytest_cache` permission warnings remain warnings only.

No PostgreSQL case in this protocol remains NOT EXECUTED.

## Remaining blockers

Before durable Generic Producer admission on Integration Test:

1. checkpoint this local implementation and evidence;
2. deploy the prepared PPR-067 validation hardening under a distinct Founder GO;
3. prove the deployed function definitions, ACL/RLS, empty/expected registries
   and historical baselines remain conformant;
4. under a separate bounded GO, register one synthetic/injected V41 policy and
   demonstrate `reserve -> claim -> injected validation -> atomic completion ->
   independent reread -> UI -> XLSX/PDF/PPTX`, including adversarial refusal;
5. decide Generic Producer `ADMITTED` only from that durable proof.

External Provider remains CLOSED. PG-3/PG-4, provider configuration guarantees,
actual OpenAI transport and attested provider execution are separate blockers
before external egress, not substitutes for Generic Producer admission. Real-data
Admission RD-1..RD-5 and the Financial Reliability Gate remain separate. No real
data or production claim follows from this proof.
