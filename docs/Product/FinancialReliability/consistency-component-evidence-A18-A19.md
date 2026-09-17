# Source consistency — bounded component evidence A18/A19

Date: 2026-09-17. Base HEAD inspected:
`a2b0c782125bcbdca188bb688a3e4a9f634c8c03` (also local origin tracking ref).
Founder reported the preceding checkpoint pushed and clean. The shortened hash in
the message is not used as a Git precondition. No live remote check in this run.
State: LOCAL_TESTED / NOT_CHECKPOINTED. NOT FR07/FR08 full-case PASS.

## WHY / before / after

PR-04 requires understood incompatible claims to remain CONTRADICTION, not generic
ambiguity or a silently selected value. Previously V1 discarded every claim when
a current-period metric conflicted. A18 retains claims and references, exposes
conflicting metrics and measured spread, preserves other recognized observations,
and supplies an investigation request in synthetic inspection. API `facts` stays
empty for contradictory dossiers; chat labels independent observations not validated.

UNDERSTOOD cannot contain conflicting metrics. Provider requests and governed
analysis envelopes still require UNDERSTOOD; contradictory claims are inspectable,
not newly admitted to analysis/persistence/exports. Numeric/period ambiguity and
oversize refusal remain. Successful envelope serialization has no added fields.
No migration, stored analysis, decision or executed action was changed.

PR-05 requires source-reported and calculated values to coexist. A19 adds an internal
pure signed-sum reconciliation component requiring an explicit definition reference,
same tenant/entity/engagement, equal period metadata/units, source references and
finite values. Missing definition/components produce UNKNOWN and bounded information
requests. Conflicting dependencies prevent a single derived subtotal. Exact Decimal
arithmetic includes sufficient precision for large integers. Arithmetic match is
ARITHMETIC_MATCH_ONLY, not financial approval. No default sign convention, EBITDA,
causality, economic impact, decision or automatic resolution is inferred.

The component is NOT an authorization boundary. Supplied scope, definition reference
and source digest are declarations, not independently authenticated capabilities.
Frozen synthetic inputs are verified by the adapter. Production governed source and
definition composition remains due. No public endpoint/provider projection accepts
these inputs. Existing V33/V34 and pre-provider authority contracts are unchanged.

## Reproducible local measurement

From backend: `python -m sandbox.run_financial_consistency_rehearsal`.
The read-only runner verifies FR-EXPECTED-2 first, computes from input data only and
emits input/code hashes and source lineage. Expected answers never enter product
computation; numerical comparison occurs separately in the test. The annual adapter
rejects foreign scope, unknown source, duplicate observation, mismatched period/unit
and non-synthetic input. It neither registers upload fixtures nor creates analyses.

Frozen manifest SHA256 (UTF-8/LF):
`63003A44CFAB7922977C3355EDCA0C7E782E379A850EFCFD2A6359A94FA878EF`.

| Input | Actual component output | Still unproven |
|---|---|---|
| FR07 | CONTRADICTION; revenue claims 1000000 and 900000 EUR retained; spread 100000; canonical facts empty; both source references preserved | Durable contradiction lifecycle and propagation through dossier/temporal/memory/exports; professional terminal review |
| FR08 | Reported gross margin 1600000; derived 400000 under supplied signed-cost formula; discrepancy 1200000; CONTRADICTION; canonical value null | Governed production definition authority; persistence/temporal/UI/memory/exports integration; professional output review |

Input SHA256 FR07: `11D73CF1F6724B3D5C59FB91D1883188A8927C908CAF9040A24FF8203EA70927`.
Input SHA256 FR08: `4C27203BFB175EAA6F037DCB0DE0B5F438234D76C4DAE817B699604AD49995D3`.
FR07: `F3A00BA060056 -> FR07.O1 / FR07.S1`;
`FFBA3E5DC8621 -> FR07.O2 / FR07.S2`; exact scope/period retained by adapter lineage.

## Falsification / regression

- 175 backend tests PASS: `test_v1*.py`, `test_governed*.py`, plus
  `test_source_contradiction.py`, `test_financial_review_bundle.py`,
  `test_financial_reconciliation.py`, `test_financial_consistency_rehearsal.py`.
- 104 frontend tests / 13 suites PASS; TypeScript no-emit check PASS.
- Arbitrary positive/negative/zero/fractional values and reversed sources; equal
  duplicate claims; separate ambiguity; oversized sets; foreign scope; missing
  definitions/components; conflicting dependencies; mismatched periods/units;
  nonfinite values; large integer exactness. No production FR-specific branch.
- Chat handler/summary are component-tested with API/message-renderer mocks;
  NOT browser E2E or live Founder proof. Frozen review artifacts remain unchanged.
- No professional output approval, global reasoning-engine proof or gate PASS.

## Next critical integration

Carry unresolved source/derived findings through an ownership-bound durable dossier
and terminal outputs without making them canonical facts. Establish governed
definition provenance before wider reconciliation exposure. Then measure complete
applicable contracts and obtain independent output review. This debt is not closed
by additional arithmetic tests or by the present component results.

External Provider CLOSED. Real-data Admission CLOSED. Self-Selling DEFERRED.
