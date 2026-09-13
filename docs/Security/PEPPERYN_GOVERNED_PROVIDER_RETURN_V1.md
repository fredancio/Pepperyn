# Pepperyn governed provider return V1

**Status:** deterministic mock-provider boundary implemented and falsified  
**Admission:** External Provider CLOSED; Real-data Admission CLOSED

## 1. Closed contract

For `FINANCIAL_CHANGE_INTERPRETATION_V1`, the sole accepted return is a
JSON-shaped mock response frozen and SHA-256 receipted at the transport
boundary. The receipt binds the response to the exact request ID, task,
serialized projection payload and sealed projection binding. Provider output
is quarantined as untrusted and never becomes a governed fact or decision.

Validation accepts only `FINANCIAL_CHANGE_RESPONSE_V1`: the exact V33 subject,
every projected metric exactly once, its unchanged deterministic direction,
and one allow-listed assessment code. Free text, extra fields, omissions,
unknown subjects, new metrics and substitutions fail closed.

## 2. Authorized local rehydration

Rehydration requires a fresh ownership grant for `CORRESPONDENCE` and a
short-lived, single-use capability bound to the exact tenant/company, entity,
engagement, analysis, request, task, projection binding and correspondence
record. The V33 reference is resolved again under that scope before the local
registry may restore the identity.

The result is an opaque `TerminalOnlyReidentified` object. It exposes content
only through terminal rendering. Both the egress serializer and the governed
projection canonicalizer reject this marker recursively, including when it is
nested. Reidentified output therefore has no route back into provider egress
or a future projection.

## 3. Falsification evidence

The focused trust-boundary suite proves response freezing and mutation
detection, exact projection/request binding, single-use receipts, single-use
validated inferences, explicit rehydration authority, and refusal of forged,
replayed, foreign-scope, substituted, incomplete, free-form and unknown-
pseudonym returns. It also proves recursive refusal of terminal reidentified
content by both egress and projection paths.

Together with the D10, V33 and V34 suites, 101 focused tests pass. The changed
Python modules compile. No provider, real data, Supabase write or interface
action was used for this slice.

## 4. Explicitly open

- Live D10 composition using the V34-attested mapping has not been rehearsed.
- Provider-response semantics remain non-canonical inference; no fact,
  decision, outcome or learning is created.
- Richer D10 task policies, production key custody, real provider transport,
  PG-3/PG-4 and Real-data Admission remain open.

