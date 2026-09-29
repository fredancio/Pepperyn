# B1 — V41 Structural Deployment Evidence

**Status:** STRUCTURAL DEPLOYMENT PASS / REGISTRIES EMPTY / PRODUCER UNADMITTED

**Evidence date:** 2026-09-29

**Environment:** Pepperyn Integration Test `ejixkplrgobgwqnhidwt`

## Scope and preserved refusal

The Founder authorized one application of the checkpointed V41 structural
migration after fresh read-only precontrols. The migration created only the
empty durable-contract V3 policy, admission and receipt registries and their
documented protections. It did not create a policy row, admission, analysis,
envelope or receipt and did not invoke a producer.

The first definition-conformance postcontrol returned `REFUSED`. That result is
retained as evidence and is not overwritten or reinterpreted as a PASS. All five
raw deployed body hashes differed from the LF expectations while all five hashes
after the single authorized normalization `CRLF -> LF` matched exactly.

Local diagnosis established that the checkpointed verifier had accidentally
copied every LF hash into its CRLF column. The raw remote hashes were exactly the
CRLF hashes independently recomputed from the committed LF bodies:

| Function | LF hash | CRLF/raw deployed hash |
|---|---|---|
| `claim_generic_execution_v3` | `420ebbd115e06029e932cfe8c289f8102abb473cdd0f4dd4f626af3cc6d285ae` | `dde4fcc4d001b160a5fc3234cb8cbc58167a8b073f68babd5fe06b1bc51ab444` |
| `close_generic_execution_v3` | `d89cc5c10baa78c4d9389f4e971410d3eb4bec22bc41f0cdb9f11810628528d7` | `22b42dba0cf34b62333f69a0fa21b7c2a61587102e53ac65b0e3f0bcc00014ae` |
| `complete_generic_execution_v3` | `6e4c051d172b001373ea63218fc5d80d2894ab87a7c4fb085b0508287ec29857` | `3d12a27c23fd8dbb2f54f362ae8abbac74bb0a9a06be3dcfeabc732b56a9dd4d` |
| `guard_generic_execution_v3` | `41a59ba0cf223915db3d42c44a935cd0470d61bef4dfa5a0bd8349c3705e9935` | `176f58d59f89bbbcd4d1eebd9257dd4ff81013c57484b500a1cf37b8fdfc9055` |
| `reserve_generic_execution_v3` | `9f66360c4e7320c9fd9c67ac079116aa6ba77396996588a7732280310d499a57` | `8db30acdc7edec04aca48b9348ade9099f9e1dd4c615b6032effcab74c574512` |

No V41 definition or migration was changed. Only the local read-only verifier's
five CRLF expectations were corrected. No normalization other than exact
`CRLF -> LF` is accepted. Three static contract tests and four isolated
PostgreSQL falsifications passed: LF and CRLF bodies are accepted; semantic and
whitespace mutations refuse.

The refused verifier is retained in Git history at SHA-256
`F89EDC64A8E1108A3861280ABC5C95480956B327760A13A8FBF5C9085E26E0AC`.
The corrected read-only verifier has SHA-256
`8BCCB41C2A9599DB07218AEC34AA47B6EEE573BD3D9CD2A5C6491CBF28A61FE4`.
The applied migration remains unchanged at SHA-256
`01956BD95487B823FD484A4D9E667CB5862B079364A408CF282E54E6A5DB729C`.

## Live read-only results

- fresh precontrol: `PREFLIGHT_PASS`;
- pre-migration historical baseline: `V41_HISTORICAL_BASELINE_PASS`;
- one migration execution: `Success. No rows returned`;
- structural/ACL/RLS postcontrol: `POSTFLIGHT_PASS`;
- initial definition postcontrol: `REFUSED`, retained above;
- corrected definition postcontrol: `V41_DEFINITION_CONFORMANCE_PASS`, all five
  functions conformant, `write_performed=false`;
- post-migration historical baseline: `V41_HISTORICAL_BASELINE_PASS`;
- final structural/emptiness postcontrol: `POSTFLIGHT_PASS`.

The pre- and post-migration application/V39/V40 snapshots are identical:

| Surface | Rows | SHA-256 |
|---|---:|---|
| `analyses` | 10 | `383bd5c9d22c89f1f204e5b6bce1f176dbe913e265d305119dc9eae7ed9844c9` |
| `execution_admissions_v2` | 6 | `a75f7490c4d3139a8105fa29fc0c4759230a8034ec91c65eafaad30df2aa225d` |
| `execution_receipts_v2` | 1 | `a073a966d7a556a2d66ad79efbc5d92a802a5ab6b8b594839d50e1b3ed11d9ba` |
| `governed_analysis_envelopes` | 7 | `fa6be4d85082428cd0c4980bc91dbfb906bd12c54b7ecb073c2912b46cd6bd15` |
| `governed_execution_receipts` | 2 | `a79bf3cb87a90289f86d874412837d1a64f58c0ab707d0880d659e999cb7df48` |
| `producer_policies_v2` | 2 | `4f60b68d4c84f40baef38ea0a6b0024415fb85dcf21de6211b29c082b7d05394` |

The relevant pre-existing catalog remains 59 items with SHA-256
`8b4517f438d5bfc2ffa08ecbe3dc599858e382eaf9bb9c332b906c3932b7c7fa`.

All three V41 registries contain zero rows. Each has RLS enabled and one immutable
guard trigger. `anon` and `authenticated` have no direct SELECT; `service_role`
has SELECT only and no direct INSERT, UPDATE or DELETE. The four service entry
functions remain service-only `SECURITY DEFINER`; the exact definition control
also attests the non-definer guard and the five function search paths and ACLs.

## Exact limits

This proves only the conforming deployment of the empty V41 structure on the
Integration Test project and the non-regression of the captured historical
surfaces. It does not admit or invoke the genuine producer, prove the product
runtime path, close B1, close the repository-wide egress scan, authorize an
external provider or admit real data.

State remains: B1 `OPEN`; genuine producer `UNADMITTED`; global egress
`OPEN/FAIL`; External Provider `CLOSED`; Real-data Admission `CLOSED`.
