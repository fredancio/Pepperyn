# B1 — V41 injected durable rehearsal successor protocol

**Status:** PREPARED LOCALLY / NOT EXECUTED / DISTINCT FOUNDER GO REQUIRED
**Target:** Pepperyn Integration Test `ejixkplrgobgwqnhidwt` only

## Purpose and preserved history

This successor preserves the claim, ceilings and trust boundaries of PPR-069.
It exists only because the first owner handoff expired before the exact policy
insert was executed.  The first policy
`5cf919e2-77e3-46ce-ab0e-c237d62cfe2d` remains an immutable failed-attempt
proof: present, disabled and never reusable.  Its attempt directory and source
snapshot remain preserved.

The successor may prove one bounded synthetic V41 execution with:

`LOCAL_TEST_ADMISSION / INJECTED_LOCAL_ONLY / provider_execution_attested=false`

It cannot prove global producer admission, external egress, an OpenAI
invocation, provider attestation, real-data admission, financial reliability or
production readiness.

## Minimal orchestration correction

The first runner authenticated before asking the Founder to insert the policy
and accepted an owner SQL artifact that remained executable after the runner's
20-minute observation window.  A late valid insert could therefore commit
after the process had already refused.

The successor changes no admission semantics.  It changes only the handoff:

1. freeze four new UUIDs and an owner-action deadline;
2. prove read-only that the failed policy is the sole V41 policy, is disabled
   and unchanged, that the other V41 registries are empty and that all new
   identities are absent;
3. ask for the exact successor policy insert before Auth;
4. require PostgreSQL itself to reject that insert after the frozen deadline;
5. observe and validate the exact policy, revalidate the historical baseline,
   scope and empty dependent registries;
6. only then authenticate technical account 1 exactly once and immediately
   continue the deterministic sequence.

The effect ceiling remains ten.  Its order becomes:

`POLICY_INSERT → AUTH_LOGIN → FOREIGN_SCOPE_RESERVE →`
`SUBSTITUTED_REQUEST_RESERVE → EXACT_RESERVE → EXACT_CLAIM →`
`INJECTED_COMPLETE → COMPLETION_REPLAY → POLICY_DISABLE →`
`POST_DISABLE_RESERVE`

No token exists while waiting for the Founder.  A policy insert attempted after
the runner deadline is transactionally refused by its own SQL and cannot create
a late active policy.

## Frozen scope and ceilings

- four new and non-substitutable policy/request/execution/analysis UUIDs;
- technical account 1 and its existing company/entity/engagement only;
- approved synthetic workbook and frozen hashes only;
- maximum five new durable rows;
- maximum ten effect-capable requests including one Auth login, one policy
  insert and one irreversible policy disable;
- no refresh, second login, retry, replacement identity or cleanup.

## Fresh read-only precontrol

Before owner SQL or Auth, fail closed unless:

- PPR-067 structures and functions remain conformant;
- V39/V40/V41 historical baselines remain unchanged;
- failed policy `5cf919e2-77e3-46ce-ab0e-c237d62cfe2d` is present, disabled
  and matches its frozen contract/specification evidence;
- it is the sole existing V41 policy;
- V41 admissions and receipts are empty;
- the failed attempt has no analysis, envelope or receipt;
- all four successor identities are absent everywhere relevant;
- the exact technical-account scope and fixture hashes remain conformant;
- egress and Real-data Admission remain CLOSED.

## Ordered execution after the handoff

After exact policy observation and the single Auth login, retain PPR-069 steps:

1. foreign-scope reservation refusal with no row;
2. substituted request/contract refusal with no row;
3. exact reserve;
4. exact claim;
5. one backend-selected injected completion;
6. completion replay refusal;
7. irreversible disable of only the successor policy;
8. post-disable reservation refusal;
9. independent-process owner recovery;
10. owner reread plus UI and XLSX/PDF/PPTX verification;
11. exact historical non-regression postcontrol.

Any divergence after the successor policy exists permits only its exact
irreversible disable, followed by stop and preservation.  The failed policy is
never updated, reactivated, deleted or reused.

## PASS / FAIL

PASS retains every PPR-069 criterion, with two additions:

- the PostgreSQL-enforced owner-action deadline and runner observation boundary
  are identical;
- the prechecked, inserted and persisted successor identity is identical, while
  the failed policy remains disabled and byte-for-byte evidence-equivalent.

Late owner SQL acceptance, a second policy outside the two known identities,
historical-policy drift, Auth before policy validation, any second login,
unknown state, ceiling risk or unavailable safety disable is FAIL.  There is no
automatic retry.

## Required next authorization

A distinct Founder GO is required for one successor execution.  It must retain
the original ten-effect/five-row bounds and authorize only the new successor
identities plus exact safety disable.  This preparation authorizes no remote
write, authentication, admission, provider, egress or real data.
