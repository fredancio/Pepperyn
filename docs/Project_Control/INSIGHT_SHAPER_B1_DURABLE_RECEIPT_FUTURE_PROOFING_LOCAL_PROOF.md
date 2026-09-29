# B1 — Durable Receipt Future-Proofing — Local Proof

**Status:** LOCAL PASS / NOT DEPLOYED / PRODUCER UNADMITTED
**Evidence date:** 2026-09-29
**Evidence ID:** PPR-065

## Purpose

Preserve the historical meaning of one admitted producer execution when input,
projection, task or output contracts evolve. This is provenance/versioning
hardening only. It adds no business metric, analytical dimension, provider
transport or real-data authority.

The governed invariant is:

`contract prechecked = contract composed = contract executed = contract persisted`

The receipt binds one indivisible contract composed of:

`admitted fact schema + positive projection policy + task + output contract`

No component is resolved through `latest`, reconstructed from current defaults or
accepted independently from the other three.

## Local implementation

- `DurableContractBindingV1` freezes the exact identities, versions and SHA-256
  digests of the admitted fact schema, positive projection policy, task contract
  and output contract, together with the producer profile and receipt version.
- The admission-contract digest is the canonical digest of that entire binding.
  `ExecutionBindingsV2`, the contract binding and the future receipt must carry
  the same value.
- Historical reread accepts only an exact entry in the supported-contract registry.
  Unknown, missing or changed versions refuse; there is no implicit current/latest
  fallback.
- The local V41 candidate stores both canonical binding text and parsed JSON. A
  database CHECK proves their equality and proves that the declared whole-binding
  digest is the digest of the canonical text. Individually plausible metadata
  cannot therefore assert an unrelated digest.
- V41 reserve/claim/complete functions preserve the existing backend-only,
  single-use, atomic pattern. Completion rechecks every material component and
  persists analysis, envelope, durable receipt and COMPLETE state atomically.
- V41 creates no enabled producer policy and exposes no registration function.
  The genuine producer remains unadmitted.

V39 and V40 definitions, rows and meanings are untouched. V41 is a new candidate
migration and is not applied to Integration Test.

## Falsification evidence

Actual isolated PostgreSQL:

- 15/15 V41 tests PASS;
- 68/68 targeted V40/V41 PostgreSQL tests PASS;
- registry refusal when canonical binding text, parsed binding and declared
  whole-contract digest disagree;
- refusal of substitutions to each of the four required versions;
- refusal of mix-and-match components that are individually well formed but were
  never admitted as one binding;
- refusal of unknown bindings and absence of any `latest` fallback;
- refusal and atomic rollback for fact schema, projection, task, output, binding
  digest and envelope mismatch;
- concurrent claim has one winner; replay is refused;
- independent-process reread reconstructs the contract only from persisted proof;
- V39/V40 objects and historical rows are not reinterpreted.

Related application contracts: 134/134 PASS. Repository egress controls: 34 PASS,
one unchanged global scan FAIL with eight pre-existing findings. That failure
remains OPEN and is not part of this LOCAL PASS.

An earlier over-broad PostgreSQL selection was interrupted after environmental
Windows temporary-directory/orchestration problems and is not claimed as PASS.
The directly affected V40/V41 selection above was then executed completely.

## Acceptance contract result

| Criterion | Local result |
| --- | --- |
| Exact input-schema identity | PASS |
| Exact positive-projection identity | PASS |
| Exact task identity | PASS |
| Exact output-contract identity | PASS |
| Whole-contract binding | PASS |
| Admission binding without substitution/fallback | PASS |
| Immutable historical V1 meaning | PASS locally; no live V41 history exists |
| Unknown/unsupported version fails closed | PASS |
| Explicit future version evolution | PASS by contract; no V2 is created |
| End-to-end persisted provenance | PASS in isolated PostgreSQL only |
| Adversarial substitution/recombination/mutation | PASS |
| V39/V40 non-regression | PASS in targeted local selection |

## Explicit limits and remaining B1 debt

- V41 is local and not deployed; no remote schema or row exists.
- No genuine producer policy has been registered, admitted or invoked.
- The product runtime does not yet reserve/claim/complete or owner-reread V41.
- UI and XLSX/PDF/PPTX have no live V41 provenance proof.
- No provider transport, provider-account guarantee, real data or professional
  financial reliability is proven.
- The repository-wide egress scan remains FAIL/OPEN.
- External Provider and Real-data Admission remain CLOSED.

Therefore PPR-065 is a bounded LOCAL PASS for durable receipt future-proofing. It
does not close B1 and does not authorize deployment or admission.
