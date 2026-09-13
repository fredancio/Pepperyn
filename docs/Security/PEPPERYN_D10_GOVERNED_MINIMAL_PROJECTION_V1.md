# Pepperyn — D10 Governed Minimal Projection V1

**Date:** 2026-09-13

**Status:** bounded task policy and authorized V33 composition implemented before the closed egress transport

## 1. Exact claim

This slice does not claim anonymity and does not close D10 for every future
Pepperyn capability. It closes one conservative V1 task contract:
`FINANCIAL_CHANGE_INTERPRETATION_V1` under policy
`FINANCIAL_CHANGE_MINIMAL_V1`.

For this task, provider-bound dynamic data may contain only:

- one V33-shaped pseudonym;
- fixed period roles `PREVIOUS` and `CURRENT` (not dates);
- one occurrence of each allow-listed metric code;
- deterministic direction and coarse percentage-change band.

Exact financial values are accepted only as local projector inputs. They do
not survive into the output. Organization/person names, arbitrary aliases,
dates, geography, sector, filenames, correspondence handles, free text,
credentials and unlisted fields have no representation in the closed output
schema. Metric order is canonicalized so input ordering is not an extra
disclosure channel.

The retained pseudonym and pattern of coarse bands can still be personal or
commercially sensitive and potentially identifying when combined with other
knowledge. The policy therefore reports `D10_REDUCED_NOT_ANONYMOUS`; it never
promotes pseudonymization or coarsening to GDPR anonymization.

## 2. Boundary enforcement

The projector issues a sealed in-process `GovernedProjection` binding:

- exact task;
- exact policy version;
- canonical payload hash;
- identity state;
- explicit residual-risk classification.

`LlmEgressAuthority` verifies that proof after canonical serialization and
provider-policy verification, but before ownership-capability consumption or
the sole transport call. A missing, forged, unknown-policy, wrong-task,
wrong-identity-state or payload-mismatched proof fails closed as
`MINIMAL_PROJECTION_REQUIRED`. Mutation after projection changes the canonical
hash and is refused.

Existing closed synthetic egress tests use a separately labelled
`SYNTHETIC_TEST_ONLY` receipt. It is compatibility evidence only and can never
be represented as a real-data D10 policy. Production real-data admission still
has no minting path and remains closed.

## 3. Authoritative V33 composition

The production task projector no longer accepts a pseudonym string and raw
financial values. Its only public composition path requires:

- a `PseudonymousReference` whose opaque handle is resolved again by the V33
  registry against exact company/entity scope;
- an ownership-issued protected-read grant bound to company, entity,
  engagement, analysis, request and `ANALYSIS_RESULT`;
- a separate projected read receipt for every metric code, previous value and
  current value;
- exact hash equality between each supplied transformation input and the value
  held by the receipt issuer.

The ownership authority consumes those source receipts once and issues a
source authorization. V33 scope and ownership scope must match. The final
projection receipt retains company/entity/engagement/analysis/request scope,
correspondence record/version, every source receipt ID and every source hash,
without retaining the protected clear values. Projection receipts are also
issuer-registered and single-use at the egress boundary; copied, modified or
replayed dataclass-shaped objects are refused.

Initial V33 registration is now separately ownership-authorized. The mapping
must originate from a projected `ENTITY_CONTEXT` receipt and a short-lived,
single-use capability bound to exact company/entity/engagement/analysis,
request, category and identity hash. V34 persists only digests of that origin
authority. The projector refuses correspondence without this attestation.

## 4. Falsification evidence

Thirteen composition falsifications, plus seventeen V33 registry/registration
falsifications, prove:

- deterministic coarsening and canonical ordering;
- exact values, dates and contextual identifiers absent from serialized output;
- direct names and non-V33 aliases refused;
- unlisted, duplicate and excessive metrics refused;
- Boolean, non-finite and malformed financial values refused;
- receipt binding to exact task, payload and identity state;
- forged and unknown-policy receipts refused;
- residual risk explicitly remains non-anonymous;
- missing projection stops before transport;
- static ordering keeps projection verification before the transport call;
- a fully authorized synthetic request reaches only the captured final boundary
  with byte-exact projected content.
- plausible but unbound pseudonyms, altered receipted values and altered
  allow-listed metric codes are refused;
- foreign V33 scope and reused source receipts fail closed;
- exact ownership scope, correspondence version, source receipt IDs and source
  hashes survive into the projection lineage;
- the public composition signature exposes no free-form identity/context slot;
- forged, modified or replayed projection objects cannot reuse the issuer seal.

The changed modules compile in the isolated backend runtime. No provider was
called and no database or interface write was performed.

## 5. Open boundaries

## 5. Live V34 composition proof

The founder-run read-only rehearsal on 2026-09-13 verified the persisted
governed envelope for analysis
`75132a71-c80c-4469-aba8-5171d947a9d0`, resolved exactly one V34-attested
`ENTITY` mapping at version 1, and composed a two-metric
`FINANCIAL_CHANGE_MINIMAL_V1` projection from the hash-pinned synthetic-only
composition fixture. Six protected-source receipts survived into lineage. The
projection receipt was verified and consumed without transport. The emitted
proof records state `write_performed=false`, `external_provider_used=false`,
`real_data_used=false` and `exact_values_disclosed=false`.

This closes the previously explicit live V34-to-D10 composition proof debt. It
does not retro-certify the legacy V33 mapping and does not create a governed
analysis, temporal fact, outcome or learning.

## 6. Open boundaries

This slice still does not prove:

- suitability of these coarse fields for every cognitive task;
- D10 treatment for exact-value tasks, free text, sector, geography or dates;
- a live source → correspondence → projection rehearsal using the new
  V34-attested mapping (the mock return and authorized terminal rehydration
  portion is now deterministically falsified, not live-provider proven);
- production key custody/rotation;
- PG-3, PG-4 or Real-data Admission.

No current analysis, export, decision, temporal or Portfolio behavior is
modified. External Provider and Real-data Admission remain **CLOSED**.
