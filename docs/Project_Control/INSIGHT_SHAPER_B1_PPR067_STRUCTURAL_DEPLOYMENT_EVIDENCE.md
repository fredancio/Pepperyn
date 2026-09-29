# B1 - PPR-067 structural hardening deployment evidence

**Status:** LIVE STRUCTURAL PASS / EVIDENCE NOT CHECKPOINTED / PRODUCER UNADMITTED

**Evidence date:** 2026-09-29

**Target:** Pepperyn Integration Test (`ejixkplrgobgwqnhidwt`)

## Authority and scope

The Founder authorized one structural application of the checkpointed PPR-067
hardening. The permitted transaction contained its original-definition guard and
exactly two `CREATE OR REPLACE FUNCTION` statements:

- `public.reserve_generic_execution_v3(...)`;
- `public.complete_generic_execution_v3(...)`.

No schema, grant, policy, trigger or application row change was authorized. No
producer policy, admission, analysis, envelope or receipt was authorized. The
Generic Producer, External Provider and Real-data Admission gates remained closed.

## Exact artifacts

- deployment transaction SHA-256:
  `7839106C6DFC6C4C03C30438F35C8C1C16050BF2CC1F204D0744281EBE385F16`;
- preflight SHA-256:
  `2DCB24BAA9DD5CEC5E6C4604193126417222EC59651BC19E4F85E3EB6F6F7A4B`;
- postflight SHA-256:
  `E8C7D8BFAEBA46814CF2EC006FA28E703F2B9B3CE587E65BACB20577DE150BAA`;
- historical baseline SHA-256:
  `618EDFD4BBD794B1FD7C228D72ECA28D4AA3F002CD43E46FC749519C4A62354D`.

The first attempted editor transfer of the deployment artifact was visibly
corrupted and was rejected before execution. No SQL from that transfer ran. The
artifact was then transferred in bounded segments, reassembled, and verified in
the browser. The delivered editor content matched the checkpointed artifact after
only the documented `CRLF -> LF` normalization. It was executed exactly once.

## Fresh preflight

`PPR067_HARDENING_READ_ONLY_PREFLIGHT_PASS` was returned before the write.

- all five V41 functions matched the original V41 definitions;
- the three V41 tables retained owner `postgres`, RLS enabled, zero policies and
  one immutable trigger each;
- `anon` and `authenticated` had no table select; `service_role` had select only
  and no insert/update/delete;
- policy/admission/receipt row counts were `0/0/0`;
- no producer was admitted, no provider was used and no real data was used.

The pre-write historical baseline returned
`V41_HISTORICAL_BASELINE_PASS` with catalog count 59 and catalog SHA-256
`8b4517f438d5bfc2ffa08ecbe3dc599858e382eaf9bb9c332b906c3932b7c7fa`.

## Application and structural postflight

The transaction completed with `Success. No rows returned`. The independent
read-only postflight returned
`PPR067_HARDENING_STRUCTURAL_POSTFLIGHT_PASS`.

- `reserve_generic_execution_v3` LF SHA-256:
  `d8c004ce0b0df839929e55594c921610a65849c691e28fcd6b86fd05ea4a7e2d`;
- `complete_generic_execution_v3` LF SHA-256:
  `aafa916300af7b47fe619c0e833515ef838a2fd35db3bb3a5ed45427c019cc32`;
- unchanged `claim`, `close` and `guard` definitions remained conformant;
- all five signatures, returns, defaults, owners, `SECURITY DEFINER`, search
  paths, language and execution privileges remained conformant;
- all three V41 tables retained the exact preflight RLS, ACL, ownership, trigger
  and zero-policy state;
- policy/admission/receipt row counts remained `0/0/0`.

The post-write historical baseline returned the same 1,028-character canonical
JSON as the pre-write baseline. Counts and deterministic row hashes for analyses,
V39 envelopes/receipts, V40 admissions/receipts and policies were identical;
the catalog count and catalog hash were also identical.

## Bounded conclusion

PPR-067 is structurally deployed on Pepperyn Integration Test. This proves only
that the two authorized hardening definitions replaced their original V41
definitions while the rest of V41 and the historical baseline remained unchanged.

It does not admit or activate the Generic Producer, create a durable execution,
prove an authenticated rehearsal, attest a provider response, close B1, authorize
external egress, satisfy PG-3/PG-4, or admit real data. The required next remote
step remains a separately authorized bounded synthetic/injected V41 rehearsal.

`B1 OPEN · Generic Producer UNADMITTED · External Provider CLOSED · Real-data Admission CLOSED`
