# A25 - History availability and ownership boundary

Date: 2026-09-20. Base: 78059c213c2e6eb57092abc3bb5433eb5c915a40.
Status: LOCAL_TESTED / FOUNDER_LIVE_BOUNDED_HISTORY_SCOPE_PASS / NOT_CHECKPOINTED.
Classification: V1 - FIX / BLOCKER. Functional and documentary closeout complete;
Git durability remains pending a grouped checkpoint.

## Why and before

The CFO must distinguish no previous analysis from an unavailable history.
The legacy GET caught every database exception and returned 200 with an empty
list. Foreign entity IDs also appeared as empty successful reads. Neither result
can support an adversarial isolation claim. The frontend already has a scoped
unavailability state and a read retry; it must receive truthful backend failures.

## After

`backend/routers/analyze.py::get_analyses_history` retains authenticated company
authority and the completed/latest-20 query. Explicit entity selection requires
an exact company/entity ownership read before querying analyses. Missing/foreign
entities return 404; unavailable or malformed reads return sanitized 503 rather
than empty success. Returned rows must match the authenticated company, requested
entity if present and completed status, with unique nonempty IDs. Internal binding
columns are removed from the public response. A genuinely successful empty list
remains 200. No writes, providers, auth redesign or migration are introduced.

## Local evidence

- `backend/tests/test_history_read_boundary.py`: six real FastAPI route tests
  using synthetic DB and authentication doubles. Covers populated two-company and
  same-company/two-entity reads; foreign/missing/empty entity refusal before analysis
  access; genuine empty success; database outages; malformed/null/duplicate/foreign
  responses; incomplete analyses; unauthenticated denial; sanitized error/log output.
- Provisioning and read-rehearsal unittest suite: seven methods PASS, including
  history outage, false-empty legacy behavior, unrelated denial and unexpected
  populated technical-account history. No live credentials or network used.
- Frontend: all 16 suites / 116 tests PASS, including HTTP history failure versus
  successful empty and existing stale-client response suppression.
- PowerShell `-CheckOnly -IncludeHistory`: PASS without secret restoration or network.

These tests do not establish live JWT/Auth correctness, RLS-production, populated
live history isolation, write or export isolation, or professional reliability.

## Prepared bounded live continuation

The existing A24 verifier supports explicit `-IncludeHistory` (Python
`--include-history`). Default A24 behavior remains bounded reads. With the opt-in,
the same existing technical accounts repeat A24 prerequisites and then require:
own entity history 200 with an empty list; exact foreign entity history 404 with
the expected refusal; anonymous history 401. Old backend false-empty behavior
therefore cannot pass. Expected status: `BOUNDED_HISTORY_SCOPE_READ_PASS`.

No accounts are created and no business write is attempted. Auth logins create
sessions. Existing DPAPI bundle is restored without regeneration and checked
unchanged; no service key is needed for the verifier. All broader proof flags,
including `populated_history_isolation_proven`, remain false. Unknown responses
and outages refuse; response bodies and secrets are not printed on failure.

## Founder live result and final closeout - 2026-09-20

After the reported backend restart, Founder executed the history opt-in once and
reported `BOUNDED_HISTORY_SCOPE_READ_PASS` and `EXISTING_DPAPI_UNCHANGED: PASS`.
This is Founder-run evidence, not an independently captured agent HTTP trace.
The verified runner requires the own empty-history positive controls, exact
foreign-entity refusals and anonymous refusal described above. No business write
or provider call was made by the rehearsal; authentication creates sessions.

All returned wider proof flags explicitly remain false:
`populated_history_isolation_proven`, `global_isolation_proven`,
`write_isolation_proven`, `analysis_export_isolation_proven`, `production_proof`.
The outage-to-503 behavior and populated row binding are locally tested only;
no live outage was induced and no populated-history proof is inferred.

Final local rerun: six history HTTP tests plus seven provisioning/read tests PASS;
all 16 frontend suites / 116 tests PASS. No live rehearsal repeated by the agent.
This closes A25 in its bounded scope, not the Private Beta isolation gate.
Changes remain in the working tree for a future grouped Git checkpoint;
the pre-existing generated `frontend/next-env.d.ts` delta remains excluded.

Founder explicitly requested stopping after this work. No next development slice
started. The attached V1 Operating Protocol (attachment
`1597d09f-62ed-4373-bf96-8eee16706f60/Texte collé.txt`) was read: convergence over
expansion, existing stack by default, scope freeze and evidence-based acceptance
apply. A wider V1 state reconciliation precedes any significant new development
when Founder resumes; it is not silently treated as completed by this closeout.

External Provider and Real-data Admission CLOSED; Self-Selling DEFERRED.
