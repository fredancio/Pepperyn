# A32 — Temporal refusal and decision-memory presentation

Date: 2026-09-23. External Provider and Real-data Admission CLOSED.
Self-Selling DEFERRED. Two distinct reservations from A31, not a new analysis.

## Temporal refusal: cause and retained boundary

The running application returns the exact reason `Plusieurs analyses gouvernées
existent pour la période courante.` for analysis
`75132a71-c80c-4469-aba8-5171d947a9d0`. Inspection of
`backend/services/governed_temporal_continuity.py` identifies the unique branch:
after loading integrity-checked envelopes within the exact company/entity/
engagement, another envelope has the same normalized annual period key as the
target. The loader refuses before choosing a prior period or computing deltas.
This is reference-selection ambiguity, not evidence that financial values differ.
It also refuses equal values and normalized fiscal/calendar label collisions.

No backend comparison rule was changed. No latest-wins, source deduplication,
automatic supersession, deletion, or mutation was introduced. The UI now explains
the non-unique reference and asks for governed source/version/period resolution;
it expressly warns against deleting an analysis to force comparison. Resolving
authority is not claimed implemented by this explanatory UI.

Evidence limit: the branch and its live refusal are established; competing row
IDs/count, their creation history, and any justified supersession have NOT been
independently enumerated in a database audit during A32. No inference of corrupt
data or redundant disposable records is made. CONTRADICTION remains correct
under the current uniqueness contract; professional temporal comparability is
not certified.

## Decision-memory correction

`FeedbackCard` previously rendered the intention-only sentence unconditionally
for every saved intention, even when `decision_confirmed_at` or an acknowledged
explicit confirmation set `decided`. It now uses that existing decision state to
show `Intention conservée — décision confirmée séparément ci-dessous.` and the
header `Mémoire décisionnelle`. Intention-only states retain their original
non-confirmation wording. No intention, follow-up or execution is promoted.

`AnalysisResult` also displayed immutable original analysis text under DÉCISION,
which could be mistaken for current lifecycle state. Governed results now label
this as the initial proposed position, explicitly historical and not updated by
later decisions, and direct the user to the decision-memory card. The original
analysis text and persisted records are preserved, not silently rewritten.
Legacy rendering is unchanged. No export generator or payload was changed.

## Verification

- Entire frontend suite: 17 suites / 120 tests PASS; TypeScript no-emit PASS.
- Backend targeted temporal continuity, temporal exports, governed exports and
  output isolation: 41 tests PASS. Tests retain refusal for equal/different values
  in competing current-period envelopes, no automatic reference choice, only
  reads. Existing scoped selection and earlier-period refusal regressions pass.
- UI tests cover intention-only, immediate confirmation, persisted decision and
  execution, preserved initial text, and temporal explanatory text without deltas.
- Agent actual browser on frontend 3000/backend 8000: reload and reopening the
  same existing Optilux analysis show both corrected presentations, retained
  CONTRADICTION and retained decision/follow-up/prerequisite/execution content.
  No new analysis, lifecycle submission, export download or business-write UI
  action during A32. No independent database mutation audit claimed.
- Working diff whitespace check excludes the intentionally preserved
  `frontend/next-env.d.ts`; its existing whitespace issue is not corrected here.

## Remaining scope

A31/A32 is a single existing Founder browser session, NOT two-user browser
isolation. A29/A30 remain their separately bounded two-user ASGI/temporary-Uvicorn
proofs. Global isolation, broader writes, production, Financial Reliability Gate,
Provider Gate and Real-data Admission remain open/closed as previously defined.
Current edits are local tested work until the next Founder durability checkpoint.
The next isolation proof must exercise authorized browser sessions without
exposing credentials or weakening the designated synthetic-client guard; no
need to repeat A29/A30 merely to collect additional identical PASS records.
