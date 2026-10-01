# Attempt 5 composition refusal - local root cause and correction

Status: LOCAL FIX VALIDATED / NOT CHECKPOINTED / NOT REMOTELY EXECUTED.
Date: 2026-10-01. Historical baseline: 62834f948a093eff7f7859928abad9a1b61af219.
Attempt 5 remains terminal FAIL-CLOSED / NO PASS.

## Root cause established from the actual call chain

execute() reaches COMPOSITION after POLICY_INSERT observation and AUTH_LOGIN.
It constructs RecordingDb(service), then calls prepare_execution(recorded,
token, manifest). LocalProducerAdmissionPreparation.prepare() immediately calls
_principal(), which requires self._db.auth.get_user(existing_token).

At the checkpoint, RecordingDb exposes only db, rpc_params, from_ and rpc.
It has no auth attribute or fallback attribute forwarding. Thus, even with a
valid underlying Supabase client and token, evaluating self._db.auth raises
AttributeError before get_user or any ownership query is invoked. prepare()
catches Exception and raises AdmissionRefused("COMPOSITION_PREPARATION_REFUSED")
from None. The runner records only the exception class and stage.

Expected: the exact underlying backend client's auth interface, with get_user
validating the token from the single previous login.
Observed: missing RecordingDb.auth (AttributeError), not an actor UUID mismatch,
foreign company, source hash mismatch or PostgreSQL rejection.
Introduction point: the recording adapter boundary in execute(), before the
authenticated composition's first check. Classification: implementation defect
in rehearsal adapter composition; the fail-closed contract correctly refused to
proceed without a verifiable authenticated actor (I1 prerequisite).

This deterministic defect is unavoidable on the checkpointed path and reproduces
the observed stage/type. The original live traceback was not retained; no claim
is made to have recovered its hidden message or inspected the original token.
No further live failure behind this first obstruction is ruled out by this fix.

## BEFORE evidence

New local tests call the actual prepare_execution with the governed workbook and
existing frozen identities, local fake Auth and read-only fake database. Direct
backend composition succeeds, while the historical adapter returns precisely
COMPOSITION_PREPARATION_REFUSED before Auth verification, table access or RPC.
Direct attribute inspection establishes AttributeError on missing auth.

The first test invocation yielded 6 PASS / 2 FAIL: the missing adapter attribute
and a test-fixture KeyError for an absent empty analyses list. The fixture setup
was corrected with setdefault, without modifying production behavior.
The controlled pre-fix rerun yielded 7 PASS / 1 FAIL, the sole failing expectation
being RecordingDb.auth identity with the underlying client's Auth object.

## Minimal correction and authority

RecordingDb gains one read-only property:

```python
@property
def auth(self):
    return self.db.auth
```

No synthetic principal, auth cache, token replacement, second login, refresh,
fallback, bypass, generic __getattr__, provider authority or gate change is added.
The consumer still calls the original backend get_user on the existing token.
The adapter's deep-copy RPC recording remains unchanged.
Local expected/actual bindings, facts, frozen request, policy identity and raw
source bytes are equal between the direct path and corrected adapter path.

## Invariant impact (I1-I18)

- I1: restores the intended backend token-verification interface, without trusting
  a producer-supplied identity. Invalid and foreign tokens continue to refuse.
- I2-I4: original authoritative tenant/company/entity/engagement resolution stays
  mandatory. Missing entity/engagement and foreign actor are tested negative.
- I5-I10: frozen identity allocation, raw source digest, producer/task versions,
  contract and whole-composition bindings unchanged; exact equality tested.
- I11: no transport/egress code changed. Local tests block socket connection;
  injected/fake inputs confer no provider or real-data authority.
- I12-I15: expiration, consumption/replay, immutability, receipt consistency and
  atomic persistence implementations unchanged. Occupied prospective identity
  refuses; durable-coordinator adversarial unit regressions executed. No new
  live or PostgreSQL atomicity/concurrency proof is claimed in this slice.
- I16-I18: authority remains backend-only; the producer receives no new argument
  or object. Provenance contracts and historical V39/V40/V41 are untouched.
  Attempt 5 failure and later independent disabled-state observation stay distinct.

## AFTER tests actually executed

104 PASS / zero skipped / three dependency warnings:

- test_v41_recording_db_composition.py: 8 cases, historical reproduction, exact
  direct-versus-adapter composition, invalid/foreign token, entity/engagement,
  occupied identity refusal and unchanged isolated RPC capture.
- test_governed_producer_admission.py.
- test_durable_generic_producer_admission.py.
- test_v41_owner_handoff.py.

No real credentials, Auth login, network or remote mutation occurred. No
PostgreSQL, provider, UI/export or remote rehearsal proof was rerun/requalified.
No successor or new distant identity was prepared. Temporary tests reuse existing
identity values in memory; they do not modify the runtime attempt directory.

## Residual state

The historical wrapper pins intentionally still reference the original runner
hash. They are NOT updated to admit the modified source or restart attempt 5.
Any future execution needs separately reviewed/checkpointed artifacts and its own
authorization; none is proposed here. The procedural safety-handoff correction
from PPR069_ATTEMPT5_STOP_POSTCONTROL.md remains applicable independently.
No change to SQL/migrations, policy history, 10-effects/5-rows/1-Auth ceilings,
SUBMISSION_UNRESOLVED, or the attempt-4 UNESTABLISHED network cause.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. Local fix PASS is not a rehearsal PASS.
