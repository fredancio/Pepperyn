# PPR-069 two-policy history adaptation - local evidence

2026-10-01. LOCAL PASS / NOT CHECKPOINTED / NO REMOTE OPERATION.
Base HEAD/tracking 4ba6b02bb1ec15fb4252c7b1ee2f8c4fe009bec3.

BEFORE: singleton SQL and runner guards deterministically reject the accepted
post-Attempt-5 state. Four diagnostic tests retain that reproduction.
CHANGE: explicit v41-disabled-history-2 adapter, exact independently validated
policies, unchanged legacy path, versioned structural expectation, complete-row
capture/attestation and comparisons before Auth, after insert/disable, on
independent recovery and final non-regression. Historical SQL files untouched.
AFTER: only the exact expected two-policy set is accepted in the new branch.

## Tests actually executed

Final Python corpus: 218 PASS / 0 skipped / 0 deselected. Includes all 167 local
correction tests, four readiness tests and 47 new two-history tests. Tests cover
each historical policy missing, extra, duplicate, enabled, substituted, wrong
specification/evidence/binding/text/digest, extra column, invalid/mutated time;
unknown version; baseline/catalog/scope/freshness drift; altered SQL/manifest/
attestation; no current-state fallback; postpolicy single-observation reuse;
independent recovery refusal before token use; historical SQL byte preservation.

Four actual PostgreSQL tests PASS on the final production code: new two-history
matrix plus injected-successor, complete precontrol and timestamped owner-ack
regressions. The combined run was 220 PASS (216 Python + 4 PostgreSQL); subsequent
addition of two Python coverage cases yielded the final 218 Python PASS above.
No required test ignored. Three existing dependency deprecation warnings only.

PostgreSQL: existing postgres:16 image, dedicated container
pepperyn-history-local-20261001, network=none, no published port or host bind,
label pepperyn.purpose=b1-synthetic-sql-test. Fixture verifies isolation before
creating synthetic local databases. No cloud URL/credential used. SQL matrix:
missing one/both rows, valid exact pair, each activated/substituted/changed policy,
extra row, one bounded insert, duplicate refusal, unchanged historical rows and
zero analysis/admission/envelope/receipt. Fixture corruption is transactionally
rolled back in LOCAL databases only, never a remote repair or altered migration.
Test DB fixture identifiers/deadlines are not an Attempt 6 allocation.

First regression run: 212 PASS / 4 FAIL because historical test doubles accepted
snapshot(db), while the new caller passed a second argument. Preserved the legacy
call signature on the legacy branch; subsequent full runs PASS. No guard was
weakened and no test was removed. No unknown-cause escalation trigger.

## Scope and guarantees

No source of identity/admission authority changes: I1-I18 remain the existing
contracts. The new module only checks history. No admission, effect-budget,
one-shot, Auth, replay, producer, privacy or egress semantics changed. Existing
RecordingDb.auth tests PASS. Existing immediate-ack/terminal-guard tests PASS.
Historical wrappers/publishers and their hashes are not repinned or reused.

Seven exclusions and 45 historical runtime files remain hash-identical to the
local-fix inventory. Attempt 5 NO PASS; runner policy_disabled=false and later
observed enabled=false remain separate. SUBMISSION_UNRESOLVED and UNESTABLISHED
are not reclassified. No migration, SQL runtime artifact or Attempt 6 created.

## Residual limits and readiness

READY for the separate LOCAL successor-freezing tranche after this adaptation
is checkpointed; NOT READY for remote launch. Future entrypoint/manifest must
explicitly wire the new version/attestation path, pin hashes and pre-prepare both
owner transfers/ack commands. No old launcher can substitute for that work.
Fresh remote conformity and complete historical-row capture remain unproven;
known-fields validation is not retroactive evidence for unknown created_at.
Timestamp serialization mismatch must refuse, not normalize silently. Human
delay/network failure remains possible; safety deadlines remain unchanged.
No live rehearsal, full browser or provider attestation inferred from these tests.

See PPR069_TWO_POLICY_HISTORY_PROTOCOL.md and the sibling hash inventory.
Git index remains empty; no commit/push or remote HEAD query in this tranche.
B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. Global egress debt not requalified.
