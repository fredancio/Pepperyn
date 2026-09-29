# B1 — Minimal V41 injected durable rehearsal protocol

**Status:** PREPARED LOCALLY / NOT EXECUTED / FOUNDER GO REQUIRED
**Target:** Pepperyn Integration Test `ejixkplrgobgwqnhidwt` only

## Exact claim

This rehearsal may prove one bounded synthetic V41 execution from immutable
local-test policy through durable output and policy disablement. It cannot prove
global producer admission, external egress, an OpenAI invocation, provider
attestation, real-data admission, financial reliability or production readiness.

The only allowed policy semantics are:

`LOCAL_TEST_ADMISSION / INJECTED_LOCAL_ONLY / provider_execution_attested=false`

The policy also records DEC-035, global producer `UNADMITTED`, synthetic origin,
egress CLOSED and real-data admission CLOSED.

## Frozen scope and ceilings

Before Auth, one launcher freezes the policy, request, execution and analysis
UUIDs. They may never be regenerated or substituted. It also freezes the exact
technical-account-1 company/entity/engagement, the approved synthetic workbook
and its raw/source-representation hashes, filename, contract binding and policy
specification.

Maximum new durable rows: five:

1. one V41 policy;
2. one V41 admission;
3. one analysis;
4. one governed envelope;
5. one V41 receipt.

Maximum effect-capable requests: ten, including exactly one Auth login, one
policy insert and one irreversible policy disable. There is no token refresh,
second login, retry, replacement identifier or cleanup. Read-only checks and
the three in-memory exports do not increase those ceilings.

## Fresh read-only precontrol

Before Auth or write, fail closed unless all conditions hold:

- project URL and visual project identity are Integration Test only;
- Git/protocol hashes equal the future checkpointed PPR-069 baseline;
- PPR-067 function definitions, V41 tables, owners, RLS, ACLs and triggers match
  their deployed evidence;
- the historical catalog/row baseline matches the post-PPR-067 baseline;
- V41 registries are empty;
- all four frozen identifiers are absent from V41 and application tables;
- technical account 1 and its exact company/entity/engagement binding exist;
- the synthetic source filename and hashes match the repository fixture;
- External Provider and Real-data Admission remain CLOSED;
- no provider credential or provider transport is available to the process.

## Ordered execution

1. Authenticate technical account 1 once; keep the token only in memory.
2. Through the separately Founder-authorized privileged SQL operation, insert
   exactly the frozen enabled policy and have PostgreSQL calculate its own
   `policy_evidence_sha256` from the specification excluding that field.
3. Attempt one foreign-scope reservation; require refusal and zero new admission.
4. Attempt one substituted-contract/request reservation; require refusal and
   zero new admission.
5. Reserve the exact frozen composition once.
6. Claim it once under the authenticated actor.
7. Execute the exact backend-selected injected adapter once. Validate the
   response, build analysis/envelope/receipt in the backend and complete once.
8. Attempt one replay of completion; require refusal and unchanged five rows.
9. Disable the policy exactly once. If any divergence occurs after policy
   insertion, this irreversible disable is the only authorized safety closure;
   preserve every row and stop.
10. Attempt one new reservation with the disabled policy; require refusal and
    unchanged five rows.
11. Start a second independent Python process with no orchestration state. Read
    the result as its owner and verify policy, admission, request, response,
    envelope, receipt, DEC-035 and non-global admission bindings.
12. Through a temporary authenticated GET-only application surface, verify the
    UI and generate XLSX/PDF/PPTX. Each must state local injected response, no
    OpenAI attestation, globally unadmitted producer and no external network.

## PASS

PASS requires exactly five new rows, the policy disabled, the admission COMPLETE,
one analysis/envelope/receipt trio, three adversarial refusals with no extra row,
independent recovery, owner-only reread, matching UI/exports, unchanged history,
unchanged PPR-065/V39/V40 evidence, one Auth login, at most ten effect-capable
requests, no egress and no real data.

## FAIL

Any precontrol divergence refuses before Auth. Any unexpected acceptance,
ambiguous response, identity mismatch, row/effect ceiling risk, partial result,
unknown database result, second-login need, refresh need or unavailable safety
disable ends the rehearsal. Do not retry, replace identifiers, delete rows,
repair remotely or infer PASS. Preserve the observed state for diagnosis.

## Smallest distinct Founder GO

Authorize one execution of this checkpointed protocol on Integration Test: one
Auth login; at most ten effect-capable requests; at most five durable rows; one
exact policy insert; two pre-reserve refusals; one reserve/claim/injected
completion; one replay refusal; one irreversible policy disable; one
post-disable refusal; independent read-only recovery; owner GET/UI and three
read-only exports. The GO must also authorize the safety disable after any
post-insert failure. It authorizes no global admission, provider, egress, real
data, schema change, cleanup or retry.
