# V40 successor 1 — bounded live persistence proof

Observed 2026-09-28, Pepperyn Integration Test only
(`ejixkplrgobgwqnhidwt`). Status: **BOUNDED_V40_SUCCESSOR_PASS**.
B1 OPEN; actual generic producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No new authorization is implied by this report.

## Authority and executable provenance

The Founder authorized the corrected successor once, after fresh conformant
preconditions, with at most 19 effect-capable requests including one Auth login
and at most seven new durable control/application rows. The predecessor remains
failed historical evidence. No launcher, identity or policy from that failure
was reused. No V39/V40 SQL was changed or reapplied.

Executed wrapper: scripts/rehearse-v40-successor-1.ps1, SHA-256
841537DE4A29367D2C5D0A88A529D3FC111D85536DE6B67C7257CB68F094D2CC.
Entry point: backend/sandbox/run_v40_successor.py. Runtime evidence is retained
outside Git in Pepperyn-runtime/v40-successor-1; no restart/reset is permitted.

## Fresh pre-Auth controls

The founder process stopped at V40_SUCCESSOR_WAITING_READ_ONLY_CATALOG_NO_AUTH.
The agent verified the named project in its authenticated Supabase SQL Editor.
All catalog/history queries used READ ONLY transactions followed by ROLLBACK.

- All six function bodies matched the reviewed raw and CRLF-to-LF fingerprints;
  arguments, return/default values, language, security-definer flags, search_path
  and execute grants matched v40-definition-crlf-1. Result:
  BOUNDED_DEFINITION_CONFORMANCE_PASS. Original raw hashes were not replaced.
- Three V40 tables: RLS enabled; zero policies; one enabled immutable guard
  trigger per table with the expected function; validated constraints. Anon and
  authenticated roles have no inspected SELECT/INSERT/UPDATE/DELETE/TRUNCATE
  privileges; service_role has SELECT only. Registry counts were 1 / 3 / 0.
- The analyses storage path still has the observed 30 columns with the expected
  types/defaults/nullability, ten validated constraints and no noninternal
  trigger. AUTRE remains allowed. Governed-envelope constraints remain validated.
- The exact old disabled policy and all three old admission rows matched the
  candidate snapshot in PostgreSQL, including inputs, bindings and timestamps.
  The independently recorded old-admission JSONB hash still matched:
  193a878f3b896212db174c1e3ed1adb52f01ae70786fab907b3eaef30dfb09b6.
  Result: V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS.
- Catalog ticket SHA-256:
  3919BBAD3E444E45C7BEDF46DFF1B5CA393ABD46A62DAB5976A03E755EB3BEA1.
  The SQL Editor introduced four CRLF line endings. A separate READ ONLY hash
  check established raw 67D710582DB55DED995700528347B871B632E0B474801562B21AE1AD299A0604
  and exact original hash after CRLF-to-LF only. No general normalization or
  schema correction was used. The full historical equality guard passed.
- The readiness record was written only after these observations. The launcher
  then rechecked scope/history and froze ten distinct prospective identities,
  checked their absence read-only and recorded them at zero Auth/effect attempts.
  Only afterward did the single login and authenticated composition occur.

Prechecked identity commitment:
9A3EFADA3015EBF585CE158DED170A3AD265211EBAD3ADE565DD83768F4C30DD.
The composed manifest matched that plan; final durable binding checks matched
the same manifest. Allocation itself conveyed no authority.

## Exact durable delta and terminal state

New policy: 8c410a9c-92e0-4c90-afb3-05b310b1f02f, now disabled,
origin SYNTHETIC, egress DENY. Old policy
cab54f0d-8b8c-4e77-bae6-7cc0660de0d7 remains disabled and byte-content-equivalent
under the preserved PostgreSQL JSONB history guard.

| Case | Execution identity | Analysis identity | Final state | Result trio |
| --- | --- | --- | --- | --- |
| ROLLBACK | 41840dde-cd01-419d-b34a-0b60f26267a5 | 2794fd0a-177b-46e1-89e7-c234eb04c648 | REFUSED | absent |
| ABANDON | bd374d57-be40-4d3f-9561-f0dc6271e75a | e63c947a-45db-4147-81e7-39588e783d70 | CLOSED | absent |
| POSITIVE | 9158d97c-bfbc-474f-81e3-40619c3bfdb7 | 162a5aa6-8ff1-4031-b726-b866006f0939 | COMPLETE | exactly one |

Exactly seven added rows: producer_policies_v2 +1; execution_admissions_v2 +3;
analyses +1; governed_analysis_envelopes +1; execution_receipts_v2 +1.
Final totals are two policies, six admissions, one v2 receipt. The four old
control rows plus seven new rows form eleven retained evidence rows.
No old V39 receipt was added, rewritten or requalified.

## Effects, concurrency and refusals

The completed local journal is closed=1 and contains exactly nineteen unique
slots. There is exactly one AUTH_ONCE, two owner mutations and sixteen RPC
attempts. Auth session effects are explicitly included in the authorization;
they are not misrepresented as part of the seven application/control rows.
Read-only inspection calls are not counted as effect-capable requests.

1. AUTH_ONCE; POLICY_INSERT.
2. INVALID_SCOPE and INVALID_SOURCE: P0001 refusals, no new admission/result.
3. ROLLBACK_RESERVE / CLAIM / COMPLETE / RECLAIM: intentional late envelope
   failure, terminal REFUSED, no partial analysis/envelope/receipt; reclaim denied.
4. ABANDON_RESERVE / CLAIM / RECLAIM / CLOSE: independent processes, second claim
   denied, explicit CLOSED and no result trio.
5. POSITIVE_RESERVE / CLAIM_B / CLAIM_A / COMPLETE: the two independent claim
   workers raced; exactly one claim succeeded and one was refused. Exactly one
   completion and result trio. The journal records B before A; this is scheduling,
   not an additional attempt or proof of which worker won.
6. Recovery used a fresh independent process after both race workers had exited.
   Exact seven-row state and bindings verified. Worker PID distinctness and exit
   success are mandatory runner assertions; PID numbers are not retained in the
   final JSON and are not invented here.
7. POSITIVE_RECLAIM refused; POSITIVE_RECOMPLETE P0001 refused; persisted state
   unchanged. POLICY_DISABLE executed once after these checks.

The owner tickets were executed exactly once, under their locks and full
before/after historical guards. Their prepared contents were independently
hashed in READ ONLY SQL before each mutation (CRLF-to-LF representation only):

- POLICY_INSERT: AEE7DA95BE49001F87830A083B44D22FD831C1D644820844887F8F9E4970AEE8;
  observed POLICY_INSERT_ACK.
- POLICY_DISABLE: C234CF34166DA94D96F6E398271C949B49688EC3B4329325F50821CEE1BDA725;
  observed POLICY_DISABLE_ACK.

No second login, refresh, retry, cleanup, identity substitution or schema write
was performed. Credentials/tokens remained in the existing protected loading path
and process memory/pipes; no secret value was emitted by this review. No external
AI provider or real financial data was used. This is not a general log/DLP audit.

## Independent final READ ONLY observation

At 2026-09-28T17:35:26.553697+00:00, separate SQL inspection confirmed:

- both policies disabled and SYNTHETIC / DENY;
- exact new execution/request/analysis identities and terminal states;
- one positive analysis, one envelope and one v2 receipt;
- admission/receipt/candidate bindings, composition, envelope and source hashes,
  company/entity/engagement ties consistent (binding_matches=true);
- zero partial result rows for the two negative cases;
- full four-row historical equality and recorded old-admission hash still PASS.

Postcheck hashes, excluding only the single new positive analysis/envelope,
equal the prior preserved PostgreSQL hashes:

| Historical object | SHA-256 |
| --- | --- |
| analyses | cab9bc0abf7b54de15d4b2055a2b018ef35397a9fcd07337beca83a639a0d708 |
| governed envelopes | c4810697f6c8d20773ca9152b5c0016be58aa11adeda5ff82840e7881dd0de10 |
| V39 receipts | c794733a7083009055c37af715d06873227f79f20ad78946c51ebf634ae1e897 |

The application also checked the eleven-table historical baseline repeatedly and
at final state, excluding only the authorized positive analysis/envelope delta.
Its result reports old_rows_unchanged=true and historical_rows_unchanged=4.
The two original local manifest/refusal hashes still match their pinned values.

## Retained artifact integrity

Files under Pepperyn-runtime/v40-successor-1 (outside Git):

| Artifact | SHA-256 |
| --- | --- |
| result.json | A85503B3AF129A71242F9B704E32B01AD8E4F191E682032A4583B2E8DA8953B7 |
| manifest.json | FDB53C8AE7DA34637E601CB65DE9697D85095A098E4EB78C73209F6F7B901F50 |
| prechecked-identities.json | 4164D219BF835BEDF0C5D8E33D857BDE2056C1597A6FC5686DDB9DBC91208A22 |
| effects.sqlite (closed journal) | A83E2AAAC9109A7F73EB3221A70BADA3489A3064751A1B637CD1DD2485DFB19E |

Final result: BOUNDED_V40_SUCCESSOR_PASS; effect_attempts=19; auth_attempts=1;
new_durable_rows=7; independent_recovery=true;
prechecked_composed_persisted_identity_match=true;
business_write_performed=true. This is a new live evidence record, not a rewrite
of either the failed first rehearsal or the earlier local-only validation.

## B1 reevaluation and next dependency

This closes the bounded live PostgreSQL admission/concurrency/atomic-result/
independent-application-process-recovery proof for the registered synthetic mock.
It does not prove database/host restart, global isolation, production readiness,
professional financial reliability, HTTP/Uvicorn/browser v2 integration, or
terminal/export version dispatch. The receipt explicitly retains
LOCAL_SYNTHETIC_ONLY and the producer candidate remains UNADMITTED_CANDIDATE.

B1 therefore remains OPEN. The next real gap is the controlled connection of an
actual generic producer with its own task/source/privacy/execution contract,
followed by version-aware governed outputs/exports and appropriate end-to-end
proof. The current egress scan debt remains OPEN (previously 34 PASS / one global
FAIL with eight findings); no fresh global-egress PASS is claimed. External use
also requires task-positive privacy admission and the independent Provider Gate.
No actual generic producer admission or activation is authorized by this rehearsal.
Do not create another mock rehearsal merely to repeat this now acquired proof.

## Repository durability

HEAD remains c1e22508fff296385014f7d82718e3e64220aa64; Git index untouched.
This live report and V40 implementation/preparation changes are local/uncommitted,
not a pushed checkpoint. Existing strategic/DEC-032 and next-env exclusions remain
preserved. No claim of synchronized Git durability is made for this new evidence.
Post-documentation checks: all 21 executed source/SQL/fixture pins still match;
tracked-document diff whitespace check PASS; new report whitespace check PASS;
PPR-061 parses uniquely in the Canon CSV. No executable was changed and no test
or live rehearsal was replayed during closeout. The local origin tracking ref
still equals HEAD; no fresh GitHub fetch or push was performed.
