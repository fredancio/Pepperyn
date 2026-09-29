# B1 — genuine generic-producer candidate local proof

Date: 2026-09-28. Status: **LOCAL PASS, UNADMITTED**.

External Provider: CLOSED. Real-data Admission: CLOSED. B1: OPEN.

## Exact candidate fixed by backend

The candidate is no longer an unspecified callable. The trusted backend profile
is fixed to:

- producer: `openai-responses-financial-analysis`;
- producer version: `gpt-5-contract-v1`;
- task: `governed-financial-analysis`;
- task version: `v1-governed-single-call`;
- model: `gpt-5`;
- provider origin: `EXTERNAL_PROVIDER_PENDING`;
- data origin: `SYNTHETIC_ONLY`;
- egress state: `CLOSED`;
- admission state: `UNADMITTED`.

This selection follows the existing OpenAI Provider Gate, provider-policy model
allowlist and governed V1 analysis contract. It does not infer effective provider
configuration or authorize a call.

## Positive projection and injected transport

`generic_producer_candidate.py` composes the exact Responses request from the
already claimed immutable `UnderstandingResult` and backend-bound request nonce.
The producer-facing request contains only governed source facts, the correlation
nonce and static task instructions/schema. Raw workbook bytes, real-world
identity, correspondence maps, free-form client context, Auth, business-scope
identifiers and persistence capabilities are excluded.

The request builder added to `v1_analysis_contract.py` accepts an existing
governed snapshot and nonce; the historical builder delegates to it and retains
its random-nonce behavior. No SDK, provider URL, credential or network primitive
exists in the candidate. The only transport is a one-use injected callable used
by local tests. Provider-shaped output is JSON-isolated and passes the existing
strict response, source, nonce and fact-lineage checks before PPR-063 can rebuild
the envelope. Reuse, malformed output and any source/nonce substitution refuse
without conformance evidence or fallback.

## Distinct future receipt contract

`governed-generic-producer-receipt-3` is defined separately from V39 and V40. It
binds the complete existing execution bindings plus profile, request, response,
projection, envelope and provider-policy-evidence digests. Its validator requires
the exact candidate producer/task/version and a distinct admission-contract
digest. No issuer or persistence implementation in this slice can mint authority
from that type. The local injected evidence is deliberately labelled
`UNADMITTED_LOCAL_CONFORMANCE`, never `ADMITTED_EXECUTION`.

V40 is not widened. The isolated PostgreSQL composition uses a fresh local-only
V40 policy solely to exercise its already proven mechanics. The durable receipt
remains `LOCAL_SYNTHETIC_ONLY`, `egress=DENY` and
`generic_producer_admitted=false`; all precontrolled execution/scope/producer/task
identities equal the composed and persisted bindings. No V39 receipt is created.
This proves composition compatibility and atomicity, not the future v3 receipt
storage contract and not real provider behavior.

## Falsification and evidence

- 52 focused candidate/adapter/analysis-contract tests PASS.
- 235 related non-PostgreSQL tests PASS; the known repository-wide global egress
  scan is deliberately excluded from that PASS and remains separately OPEN.
- All 37 formerly NOT EXECUTED V40 PostgreSQL cases were actually executed in
  the isolated `pepperyn-b1-pg16-20260928` container and PASS.
- One additional actual-PostgreSQL candidate-composition case PASS, for **38
  PostgreSQL PASS** total. It verifies exact precontrolled = composed = persisted
  identities, one invocation, V40 atomic completion, local-synthetic/egress-DENY
  receipt truth and absence of V39 fallback.
- The targeted static scan returns zero findings for the new candidate module.
- The unchanged repository-wide scan remains FAIL with its eight pre-existing
  findings; four adjacent confinement checks PASS. It is not requalified.
- Socket-denial tests observe zero product network attempts.

The first new PostgreSQL test run exposed a test-helper error: the test added
`policy_id` to the closed `ExecutionBindingsV2` payload. The closed schema refused
it before SQL. Only the test was corrected; product bindings were not widened.
Final complete PostgreSQL rerun: 38 PASS in 66.84 seconds.

## Remaining admission protocol — not executed

Before the producer may change from `UNADMITTED`:

1. implement and locally prove a separately versioned durable v3 admission and
   receipt store matching `governed-generic-producer-receipt-3`; never reinterpret
   V39 or V40;
2. run rollback, concurrency, expiry, replay, mix-and-match, foreign-scope and
   receipt-mismatch tests against that exact storage contract;
3. close the task-specific egress chain using governed projection, ownership
   authorization, effective provider-policy evidence and quarantined response;
4. close PG-3/PG-4 before any OpenAI transport; close the global egress scan debt
   before external activation;
5. obtain a distinct Founder GO before any migration, remote policy/admission,
   provider call or live synthetic rehearsal;
6. after admitted execution, prove fresh owned reread and identical provenance in
   UI, XLSX, PDF and PPTX; then perform adversarial scope tests.

Real financial inputs remain independently blocked by RD-1 through RD-5. A future
synthetic provider PASS could not open Real-data Admission or establish Financial
Reliability.
