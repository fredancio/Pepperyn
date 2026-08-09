# EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md

**Status:** PROPOSED — architecture/documentation mission, read-only, not yet approved, not yet implemented. **Final Contract Arbitration pass completed 2026-08-09** (this revision): the Case-B concurrent-first-confirmation reservation named below is now closed by canonical Knowledge Model v0; verdict raised from B to A accordingly (see Final Report).
**Branch:** `architecture/epistemic-dialogue-v0-2026-08-09` (promoted to `main` in this arbitration pass).
**Depends on:** `docs/Architecture/Cognitive/KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md` — MERGED, CANONICAL, `main` commits `773cb0b` (base: migrations v24/v25, `services/knowledge_model_service.py`, adversarially reviewed, structurally protected against successor branching) and `a7a1049` (root-uniqueness repair: migration v26, `UNIQUE(entity_id, subject) WHERE relates_to_knowledge_id IS NULL`, closes the concurrent-first-confirmation race, validated live on real PostgreSQL including genuine two-thread concurrency). This document does not reopen, re-derive, or restate Knowledge Model's own design — it treats `confirm()`/`recall()` as a fixed, trusted API.
**Companion documents (doctrinally reconciled 2026-08-09, surgical corrections only):** `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.

---

## 1. Professional responsibility

**Epistemic Dialogue:** given a material uncertainty that reasoning alone cannot resolve, decide whether Pepperyn already knows the answer before ever considering whether to ask a human — and if a human does answer, decide whether that answer is authoritative enough to become new canonical knowledge.

The governing question, restated precisely: *when a competent professional meets a material uncertainty that neither the data nor what they already know about this company can resolve, how do they decide whether it's worth interrupting someone to ask?* Epistemic Dialogue is the operational answer to that question — nothing else.

It is explicitly **not**: the chat, a chatbot, a general conversational engine, `KnowledgeModel` (the memory it consults), FRU (the reasoning that produces what it evaluates), Evidence (what was observed), an LLM agent, or a decision system. It is a cognitive capacity for managing uncertainty that may require human clarification — chat is one possible delivery surface for its output, not its identity (§11).

This gives the fifth of five now-distinct foundational questions, alongside the four already established: Evidence ("what did I observe?"), FTE ("when does this belong?"), FRU ("what do these numbers mean here?"), Knowledge Model ("what has this company already taught me?"), and now Epistemic Dialogue ("what must I ask the human because I cannot reasonably know it alone?").

## 2. Doctrinal reconciliation (Phase 1 — completed before any design work below)

Five stale claims, all originating from `COGNITIVE_CAPABILITY_MAP.md`'s pre-arbitration "propriété d'Engagement" wording and from describing Candidate Context as something `KnowledgeModel` itself stores, were corrected surgically (no rewrite) in the two affected documents:

1. `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md` §9, Engagement row — was "POTENTIAL OWNER," now "ACQUISITION CONTEXT only," with the correction dated and sourced to the final Knowledge Model arbitration (`3be19e4`).
2. Same document, §9, BusinessHistory row — "Same owner (Engagement)" corrected to "Same true owner — Entity."
3. `EPISTEMIC_DIALOGUE_FOUNDATION.md` §7 — knowledge scope boundary corrected from "Entity/Engagement" to "Entity," with Engagement re-described as acquisition context, not a scope boundary.
4. Same document, §8 memory-family table — "already named and owned by Engagement" corrected to "Owned by Entity, not Engagement," with the Candidate→Confirmed promotion language corrected to state plainly that no Candidate is ever persisted inside `KnowledgeModel`.
5. Same document, §5 — "the Candidate Context is promoted to Confirmed Context" and "the original hypothesis is retained only as a superseded Candidate" corrected: the Candidate was never persisted in the first place (ephemeral, held by Epistemic Dialogue only); what a correction actually does is insert a new CONFIRMED row via `relates_to_knowledge_id`, leaving the prior CONFIRMED row untouched.

Verified by grep across all three documents after correction: no remaining "propriété d'Engagement" / "owned by Engagement" / "superseded Candidate" / "promoted to Confirmed" language survives. No document currently asserts anything the final Knowledge Model contract contradicts.

## 3. The epistemic loop, tested against code and doctrine

```
OBSERVE          — Evidence's responsibility. Not touched here.
  ↓
REASON           — FRU's responsibility. Produces a Candidate (value + confidence
                    tier: FACT/STRONG_INFERENCE/HYPOTHESIS/UNKNOWN). Epistemic
                    Dialogue consumes this; does not reinterpret raw data itself.
  ↓
RECALL           — KnowledgeModel's exposed function, called BY Epistemic
                    Dialogue. KnowledgeModel owns the mechanism; Epistemic
                    Dialogue owns the OBLIGATION to call it (§6).
  ↓
COMPARE          — Epistemic Dialogue's own, genuinely new logic. Neither FRU
                    (doesn't know what was previously confirmed) nor
                    KnowledgeModel (doesn't reason about new observations) can
                    do this. Feeds directly into the next step, not a branch.
  ↓
ASSESS UNCERTAINTY + MATERIALITY  — Epistemic Dialogue's decision, informed by
                    COMPARE's outcome (agreement / absence / contradiction) and
                    FRU's own confidence tier.
  ↓
CONTINUE WITHOUT ASKING  or  CREATE CLARIFICATION NEED   — Epistemic Dialogue's
                    decision (§4, §6).
  ↓
ASK HUMAN        — the DECISION and CONTENT belong to Epistemic Dialogue
                    (§8); the DELIVERY (chat, banner, notification...) belongs
                    to a presentation surface (§11).
  ↓
RECEIVE ANSWER   — presentation surface delivers raw input; Epistemic Dialogue
                    owns interpreting it into a domain-relevant signal.
  ↓
VALIDATE / INTERPRET ANSWER  — Epistemic Dialogue's gate (§9), optionally
                    LLM-assisted for free text (§10), never LLM-decided.
  ↓
CONFIRM KNOWLEDGE when justified  — calls KnowledgeModel.confirm(). Epistemic
                    Dialogue is the caller; KnowledgeModel is the store and
                    the sole source of persistence guarantees.
  ↓
REUSE            — not a distinct mechanism; simply the next OBSERVE→RECALL
                    cycle finding a CONFIRMED row where it previously found
                    none.
```

This sequence survives the analysis with one clarification, not a rejection: **COMPARE is not a branch, it's an input.** Whether RECALL returned nothing (§6 Case B) or something that must be checked against the new candidate (§6 Cases A/C), the result feeds uniformly into ASSESS UNCERTAINTY — there is one decision point, not two.

**No double responsibility found.** Each step above has exactly one owner. The one step genuinely new to this document — COMPARE — is small and does not duplicate anything FRU, Knowledge Model, or Evidence already do.

## 4. ClarificationNeed — demonstrated, not assumed, then reduced

**Is a first domain object needed at all?** Yes — demonstrated, not assumed. For RECALL-before-ASK to be a *structurally* enforceable invariant (§6, the mission's own central demand) rather than a policy someone could forget to follow, the code path that decides to ask must be physically incapable of doing so without already holding a RECALL result. That requires *something* to carry, between the "decide to ask" moment and the "receive an answer" moment, at minimum: which entity and subject this concerns, what was recalled (or its absence), and what is currently hypothesized. No existing object does this — FRU's Candidate doesn't know what was recalled; KnowledgeModel's rows don't exist until confirmed. So yes: a first object, `ClarificationNeed`, is genuinely required.

**Complexity test on its shape** — the mission's own illustrative six-item list is not adopted wholesale. Two of the six collapse into fields already covered ("what Pepperyn is trying to understand" = `entity_id`+`subject`, "what existing knowledge was recalled" = `recalled_value`), and two more are **rejected outright** rather than schematized:

- *"why is this materially important"* — not a stored explanation. For v0, materiality is a fixed property of the *subject itself* (§6), not a per-instance justification string. Storing a redundant explanation for a fact already implied by which subject triggered creation would fail the complexity test.
- *"what minimal question would resolve the uncertainty"* — not a stored question. The question text is a pure, deterministic function of `candidate_value` + `recalled_value` (§8); storing it would create a second, driftable source of truth for something derivable on demand.

**Minimal v0 shape, four fields, nothing else:**

| Field | Meaning |
|---|---|
| `entity_id` | Same scope as `KnowledgeModel` (Entity is the true owner, §2). |
| `subject` | Same curated registry `KnowledgeModel` already enforces. |
| `candidate_value` | FRU's current hypothesis — what would be passed to `confirm()` if the human agrees. |
| `recalled_value` | The result of the mandatory RECALL call — `None` (Case B) or the currently applicable knowledge (Cases A/C). This single field is what "why is this uncertain" reduces to: absent, or present-and-disagreeing. |

`ClarificationNeed` is never itself passed to `KnowledgeModel` — it is consumed entirely within Epistemic Dialogue and produces, at most, one `confirm()` call.

**Re-attacked against six adversarial cases (final arbitration, 2026-08-09):** (1) knows-nothing → Case B, `recalled_value=None`; (2) already-knows-same → Case A, no object constructed; (3) new-evidence-contradicts → Case C; (4) evidence-insufficient-for-a-candidate → no `candidate_value` exists, so no `ClarificationNeed` is constructed at all (§6, detector-`UNKNOWN` case) — a precondition, not a fifth field; (5) human-confirms → `candidate_value` passed directly to `confirm()`; (6) human-rejects-and-supplies-an-alternative → the alternative value (`CORRECT_TO(value)`, §9) is a **transient** part of the answer-handling flow, consumed directly by the `confirm()` call in the same turn — it is never written back into `ClarificationNeed`, which represents the *question* state, not the *answer* state. All six resolve within the existing four fields; none forces a fifth.

## 5. Persistence question — examined, resolved: NOT persisted in v0

Tested against every listed consequence, and every one resolves cleanly under a purely **ephemeral, freshly-regenerated** model — the same discipline already applied to Candidate inside `KnowledgeModel` itself, not a new pattern invented here:

- **User quits before answering** — nothing was confirmed, so nothing is lost. The next time REASON+RECALL run (next upload, next visit), an equivalent `ClarificationNeed` regenerates deterministically, because FRU and `recall()` are both deterministic.
- **Returns tomorrow** — same reasoning; regeneration is idempotent, not a re-ask of something already settled, because nothing was ever settled.
- **Multiple uploads intervene** — an ephemeral model naturally uses only the *latest* upload's candidate; there is no stale, accumulating queue of unresolved questions to reconcile.
- **New Evidence makes the question moot** — the next loop run re-checks RECALL fresh; if knowledge now exists (someone else answered, or a deterministic promotion occurred), Case A fires and no new `ClarificationNeed` is even created.
- **Another user of the same Entity answers first** — same mechanism: whoever's answer reaches `confirm()` first is reflected in RECALL for everyone afterward. **Closed 2026-08-09** (previously the contract's largest named reservation, see §13 case "two humans answer differently" and §9's new paragraph on `ConcurrentRootConflictError`): `KnowledgeModel` v26 now makes this structurally impossible to race — the second, losing `confirm()` call receives a named rejection from PostgreSQL itself, not a silent double-write.
- **Question becomes obsolete / convention changes** — both handled for free by fresh COMPARE on every run; no staleness-tracking logic needs to be built.

**Conclusion: persistence is not introduced because no real professional need forces it.** All the scenarios that *sound* like they need durable state are actually solved by cheap, correct regeneration. A future session-level UX convenience (e.g., not losing an unanswered prompt if the user navigates away mid-review) is a presentation-surface concern (§11) that can be added later without touching this domain model — it would not retroactively justify canonical persistence of `ClarificationNeed` itself.

## 6. RECALL BEFORE ASK — the central invariant, made structurally testable

**Formal rule:** the function responsible for constructing a `ClarificationNeed` must require `recalled_value` as a **mandatory, no-default parameter** — not an optional flag a caller could omit. Testable two ways, mirroring this repo's own established discipline: (a) a signature-level test asserting the constructor cannot be called without it, and (b) an AST-based test (same pattern as `TestTemporalRoleIsolation`/`TestNoLLMInvolvement` elsewhere in this codebase) asserting the module that constructs `ClarificationNeed` always calls `recall()` first in the same function body. This makes the invariant a property of the *code shape*, not a convention someone could forget.

**The five cases:**

- **Case A — knowledge exists and agrees.** `recalled_value == candidate_value` → no `ClarificationNeed` created. This is "never ask twice" in its purest form.
- **Case B — no knowledge exists.** `recalled_value is None` → materiality is checked against the *subject* (below); if material, create a `ClarificationNeed` (confirmation-form question, §8). v0 never auto-confirms without asking — `KnowledgeModel`'s own provenance is fixed to `HUMAN_CONFIRMATION` only, so there is no deterministic-promotion path in v0 to shortcut this.
- **Case C — knowledge exists but contradicts.** `recalled_value != candidate_value` → inherently material for v0's one subject (a sign-convention error inverts essentially every downstream number) → create a `ClarificationNeed` with the **contradiction-form** template, never the plain confirmation-form template (§8).
- **Case D — KnowledgeModel is ambiguous/corrupt.** `recall()` raises `KnowledgeChainIntegrityError` (already a real, implemented behavior in the merged service). **This must never be caught and treated as Case B.** Silently degrading "we found a corrupted chain" into "we never learned this" is a materially false and worse claim than surfacing the corruption. Required behavior: Epistemic Dialogue catches this exception explicitly and routes it to a distinct escalation path (an integrity alert, not a question to the reviewing user — the end user answering "is X true" does nothing to repair a broken canonical chain). The escalation *mechanism* itself is safe to defer (§13); the *behavior* of never asking a normal question in this case is required now.
- **Case E — uncertainty immaterial.** No interruption, regardless of A/B/C, if the subject is not material (below).

**Materiality in v0, without a scoring engine.** Per the mission's own instruction not to invent numeric thresholds prematurely: materiality is a **named, fixed property of the subject itself**, not a computed score. v0's subject registry (mirroring `KnowledgeModel`'s own `SUBJECT_VALUE_REGISTRY` pattern) carries exactly one entry, `EXPENSE_SIGN_CONVENTION`, hardcoded `ALWAYS_MATERIAL` — because a wrong sign convention is about as unambiguously material as a single interpretive fact can be, not because v0 has solved the general materiality problem. This is honestly narrow (§15), not falsely general.

## 7. Never ask twice — precise formalization

**Does not mean:** "Pepperyn never asks the same sentence twice." **Means:** "Pepperyn does not re-request a confirmation that is already confirmed and still applicable."

The identity of a "question," for the purpose of this rule, is exactly the canonical tuple **`(entity_id, subject)`** — never fuzzy text matching, never a semantic-similarity engine (explicitly rejected per the mission's own instruction: canonical identifiers already suffice). Distinguishing the six named situations:

- **Repeated question** (Case A) — same tuple, `recall()` agrees → suppressed. This is the mechanism working correctly.
- **Genuine contradiction / convention change** (Case C) — same tuple, but this is *not* a repeat: it's a differently-worded, differently-purposed question (confirming a *change*, not re-establishing a settled fact). `KnowledgeModel`'s chain-head resolution already guarantees only the *current* head is ever compared against — a superseded row can never trigger a repeat-ask.
- **Narrower scope** — would be a *different* tuple once `KnowledgeModel` gains a scope dimension beyond Entity (explicitly deferred there, §5 of its own contract) — correctly out of scope for v0, and correctly not something Epistemic Dialogue could add unilaterally even if it wanted to (the scope dimension belongs to `KnowledgeModel`, not to this layer).
- **New subject** — a different tuple entirely, trivially independent.
- **Corrupt/ambiguous Knowledge** (Case D) — never conflated with either "repeat" or "new" — its own distinct escalation path (§6).

**Falsifiability checks (final arbitration, 2026-08-09)** — made explicit rather than left implicit:

- **Same convention, months later, not just "tomorrow"** — `recall()`'s chain-head resolution is purely graph-structural (`relates_to_knowledge_id`), never `confirmed_at`-based (§6, §7); no code path reads elapsed time. A confirmation from months ago is exactly as authoritative as one from seconds ago — "never ask twice" does not decay.
- **New Entity does not inherit another Entity's suppression** — `recall()` is always scoped by `entity_id` (`services/knowledge_model_service.py`: `.eq("entity_id", entity_id)`, confirmed by direct reading, unchanged by this arbitration). A brand-new Entity's first upload always resolves `recalled_value=None` regardless of what any other Entity has confirmed for the same subject — Case B fires independently, the question is never suppressed by a different company's history.

## 8. Question quality — domain content vs. presentation wording

**Structure is domain; phrasing is presentation.** `ClarificationNeed`'s four fields (§4) guarantee that *any* future rendering surface can construct a question containing all three required epistemic components — **OBSERVATION** (what was seen/recalled), **HYPOTHESIS** (the candidate), **MINIMAL CONFIRMATION REQUEST** (a yes/no or a correction, never an open interrogative) — without needing anything beyond those four fields. That guarantee belongs to the domain.

The exact sentence is presentation, and for v0 is a **deterministic Python string template, zero LLM** (§10), proven sufficient by construction for the two required cases:

- Case B (confirmation-form): *"J'ai parcouru votre fichier et il semble que vos charges soient présentées en valeurs positives. Est-ce exact ?"* — generated from `candidate_value` alone (`recalled_value is None`).
- Case C (contradiction-form): *"Jusqu'ici vos charges étaient présentées en valeurs positives. Ce fichier semble utiliser des signes négatifs. Cette convention a-t-elle changé ?"* — generated from both `recalled_value` and `candidate_value`, explicitly naming what changed rather than repeating the generic original question (this is also what keeps Case C from *reading* like "asking twice," even though it touches the same tuple).

A future LLM-generated variant may replace the template's wording later (§10) without changing what `ClarificationNeed` must structurally guarantee.

**Structural requirements, derived (final arbitration, 2026-08-09):** a good question must (1) state what Pepperyn observed, (2) state its interpretation, (3) expose uncertainty honestly, (4) request confirmation narrowly, (5) never ask the user to explain accounting fundamentals Pepperyn should infer itself. (1)/(2)/(4) map directly to OBSERVATION/HYPOTHESIS/CONFIRMATION-REQUEST above. (3) is satisfied by construction, not a fourth missing component: the HYPOTHESIS is always phrased non-assertively ("il semble que," "appears to be"), never as a flat claim — honesty about uncertainty is the phrasing convention, not a separate field. (5) is not this section's concern at all — it is the *decision to ask* (§4 of the foundation document, "when Pepperyn must not ask"), already governing *whether* a question exists before this section ever decides *how* to phrase it; re-litigating it here would blur content and wording exactly as this section warns against.

## 9. Human authority — four boundary stages, one gate

A human can confirm, correct, indicate a convention change, or provide context absent from the data. **A human response never automatically becomes canonical knowledge.** Four distinct stages, with Epistemic Dialogue as the sole gate between the third and fourth:

1. **Answer received** — raw input from whatever surface delivered the question (§11). For v0's Golden Loop, a constrained yes/no/correction signal, not free text.
2. **Answer interpreted** — mapped to exactly one of: `CONFIRM`, `CORRECT_TO(value)`, `DECLINE`, `UNINTERPRETABLE`. For v0's constrained input this mapping is a trivial deterministic function; free-text interpretation (§10) is a v1+ capability, architecturally anticipated but not exercised here.
3. **Knowledge candidate** — only `CONFIRM` and `CORRECT_TO(value)` reach this stage, and only if the resulting value is a *legal* member of the subject's registry (mirroring `KnowledgeModel`'s own value CHECK). An interpreted answer proposing an illegal value is treated as `UNINTERPRETABLE`, never silently coerced.
4. **Confirmed canonical knowledge** — reached only via an explicit `KnowledgeModel.confirm()` call, with `confirmed_by` set to the real human identity (never a system account, never "LLM"), `provenance` remaining `HUMAN_CONFIRMATION` as `KnowledgeModel` already fixes it, and — for Case C — `relates_to_knowledge_id` set to the row being superseded.

**No LLM can reach stage 4 alone**, even where an LLM assists at stage 2 (§10): an LLM's interpretation is itself treated as another candidate requiring the same legality/unambiguity gate as any other input, never trusted as a direct authorization to call `confirm()`.

**New: handling `ConcurrentRootConflictError` at the stage-4 call site (final arbitration, 2026-08-09).** Now that `KnowledgeModel` v26 structurally rejects a losing concurrent `confirm()` call rather than silently allowing it, Epistemic Dialogue's own confirm-call site must define what happens when its `confirm()` call is the one rejected. Required behavior: catch the exception, call `recall()` again immediately, and treat whatever it now returns as authoritative — i.e. re-enter Case A (§6) with the winning value. Explicitly forbidden: retrying the write with the same value (the DB already told us a different value won), presenting this to the human as if *their* answer was rejected (it wasn't wrong — someone else's confirmation simply landed first), or silently discarding the event without re-checking RECALL. This mirrors `ConcurrentRootConflictError`'s own docstring instruction (`services/knowledge_model_service.py`): "the caller must call recall() again to see the canonical value that won, never assume its own value was the one confirmed." No winner-selection logic is introduced here — PostgreSQL already chose; Epistemic Dialogue only has to notice and recover, cleanly, into the exact behavior it already has for Case A.

## 10. LLM role — and why v0 has none

Candidate future responsibilities: reformulating a hypothesis in natural language, phrasing the confirmation question, interpreting free-text answers, explaining *why* Pepperyn is uncertain. Forbidden, permanently: creating canonical truth alone, bypassing RECALL, bypassing Evidence, promoting Knowledge, inventing a company convention that wasn't actually observed or confirmed.

**Trust Gateway impact, decisive for v0.** `TRUST_BOUNDARY_CLOSURE_PLAN.md` is a plan only, not implemented (confirmed in the FRU/Epistemic Dialogue foundation, §11 there). Any LLM call in this loop — even "just" phrasing a question — would require sending entity-specific content through the not-yet-built Trust Gateway. Given that (a) this blocker already forced FRU's own first slice to zero LLM calls, and (b) §8 above proves the two required Golden Loop questions are fully producible by deterministic template with no loss of quality, the conclusion is the same one already reached twice in this engagement: **the v0 implementation contract must specify zero LLM calls.** This is not a compromise forced by the blocker alone — it is independent proof that the *cognitive* loop (deciding whether to ask, about what, and how to gate an answer) does not actually require an LLM to be demonstrated end-to-end. Natural-language richness is a v1+ enhancement, blocked on the Trust Gateway, layered on top of an already-complete decision structure.

## 11. Chat role — tested, holds

**Proposition:** chat is a presentation-and-interaction surface for epistemic events, not the domain itself. **Test:** can a `ClarificationNeed` be created, evaluated, and resolved into a `confirm()` call with zero chat UI involved? Yes — nothing in §4 through §9 references a chat surface, a message, or a conversation. The Golden Loop (§12) is driven entirely by a simulated human answer, exactly matching how every other "first slice" in this engagement has been proven (FTE's Walking Skeleton, Knowledge Model's own Phidani loop test) — through a test harness, not a UI.

**Removing chat does not destroy Epistemic Dialogue.** The reverse test the mission proposes — "if removing the chat UI destroys the architecture, the architecture is probably wrong" — passes: `ClarificationNeed`, RECALL-before-ASK, COMPARE, materiality-by-subject, and the confirm-gating logic in §9 all function identically whether the question is ultimately delivered via chat, an upload-confirmation banner, an onboarding step, a review-screen prompt, or a notification. Chat is one interchangeable delivery mechanism among several, not Epistemic Dialogue's identity.

**Directly verified against the real file (final arbitration, 2026-08-09), not just argued:** `backend/services/conversation_engine.py` was read in full. It contains zero references to `KnowledgeModel`, `ClarificationNeed`, or any dialogue-type concept — confirming the foundation document's claim (§2) that today's chat has no coupling to this domain to break. It also contains no anonymization call before building its LLM payload, independently corroborating the already-named, already-tracked Trust Boundary bypass (`EPISTEMIC_DIALOGUE_FOUNDATION.md` §11) — inspected here only to confirm the risk is real and correctly named, not repaired in this mission.

## 12. First Phidani loop — the Golden Loop, walked through and internally consistent

Single subject: `EXPENSE_SIGN_CONVENTION`. Walked against every rule above to confirm it actually produces the required sequence, not merely asserted:

**Upload 1.** FRU candidate = `ABSOLUTE_POSITIVE`. `recall(entity, EXPENSE_SIGN_CONVENTION)` → `None`. Case B. Subject is `ALWAYS_MATERIAL` → `ClarificationNeed{candidate_value=ABSOLUTE_POSITIVE, recalled_value=None}` created. Question (confirmation-form, §8): *"J'ai parcouru votre fichier et il semble que vos charges soient présentées en valeurs positives. Est-ce exact ?"* Human: `YES` → interpreted `CONFIRM` → `confirm(entity, EXPENSE_SIGN_CONVENTION, ABSOLUTE_POSITIVE, confirmed_by=<human>, confirmed_at=now)` → **K1** inserted, `relates_to_knowledge_id=None`.

**Upload 2.** Same convention, candidate = `ABSOLUTE_POSITIVE`. `recall()` → K1 (`ABSOLUTE_POSITIVE`). COMPARE: agrees → Case A → no `ClarificationNeed`. **NO QUESTION.**

**Upload 3.** Contradictory fixture, candidate = `SIGNED_NATURAL`. `recall()` → still K1 (`ABSOLUTE_POSITIVE`). COMPARE: disagrees → Case C → `ClarificationNeed{candidate_value=SIGNED_NATURAL, recalled_value=ABSOLUTE_POSITIVE}`. Question (contradiction-form, §8): *"Jusqu'ici vos charges étaient présentées en valeurs positives. Ce fichier semble utiliser des signes négatifs. Cette convention a-t-elle changé ?"* Human confirms the change → interpreted `CONFIRM` → `confirm(entity, EXPENSE_SIGN_CONVENTION, SIGNED_NATURAL, confirmed_by=<human>, confirmed_at=now, relates_to_knowledge_id=K1.id)` → **K2** inserted; K1 untouched, still independently queryable (already guaranteed by `KnowledgeModel` itself).

**Upload 4.** Candidate = `SIGNED_NATURAL`. `recall()` → K2 (chain-head). COMPARE: agrees → Case A → **NO QUESTION.** K1 remains historically queryable, never returned by ordinary `recall()`.

The walkthrough is internally consistent with every rule stated above — no rule had to be bent to make this scenario work.

## 13. Failure cases — classified

| Case | Classification | Note |
|---|---|---|
| Detector uncertain (FRU returns `UNKNOWN`) | **Required now** (silence); open-ended clarification **explicitly deferred, not solved** (named 2026-08-09) | No candidate exists to confirm — Epistemic Dialogue creates no `ClarificationNeed` and asks no *targeted* confirm/correct question. This is a deliberate v0 boundary, not the intended final professional behavior — see the paragraph immediately following this table. |
| Knowledge absent (Case B) | **Required now** | §6. |
| Knowledge agrees (Case A) | **Required now** | §6. |
| Knowledge contradicts (Case C) | **Required now** | §6. |
| Knowledge ambiguous/corrupt (Case D) | **Required now** (behavior); escalation mechanism **safe to defer** | Must never silently degrade to Case B (§6). |
| User says "I don't know" | **Required now** | Interprets to `DECLINE` — no `confirm()` call, nothing persisted, uncertainty stays open; may resurface on the next upload without violating "never ask twice" (nothing was ever confirmed). |
| User gives an irrelevant answer | **Required now** (basic catch-all `UNINTERPRETABLE`); rich free-text handling **safe to defer** | Never silently guesses a value. |
| User contradicts themselves across turns | **Safe to defer** | Requires session-level state tracking beyond v0's single-turn, ephemeral `ClarificationNeed`. |
| Question ignored | **Required now, free** | Already correctly handled by §5's ephemeral design — no new code needed. |
| New Evidence arrives before answer | **Required now, free** | Same reason — fresh RECALL on every run. |
| Two humans answer differently | **Required now — now structurally closed, not deferred** (updated 2026-08-09) | For Case C (supersession), `KnowledgeModel`'s `UNIQUE(relates_to_knowledge_id)` (v25) prevents two competing successors. For Case B (two people confirming a **brand-new** subject simultaneously — two competing `NULL`-predecessor roots), `KnowledgeModel` v26 (`UNIQUE(entity_id, subject) WHERE relates_to_knowledge_id IS NULL`, root-uniqueness repair, validated live including genuine two-thread concurrency) now closes this too. Both cases: the losing `confirm()` call is rejected by PostgreSQL, not silently allowed — Epistemic Dialogue's own recovery behavior for the rejection is specified in §9. **Corrected 2026-08-09 (independent adversarial review, correction 1):** the loser's recovery outcome must itself distinguish *benign* reconciliation (the winner confirmed the same value this actor attempted) from a *genuine conflict* (the winner confirmed a different value) — re-RECALL alone is necessary but not sufficient; the recovered value must be compared against this actor's own attempted value before reporting an outcome to the caller. |
| Same Entity, future multiple Engagements | **Required now, already correct** | Everything is scoped by `entity_id`, never `engagement_id` — Engagement is recorded only as acquisition context on the eventual `confirm()` call. |
| Convention differs by sheet/template | **Architectural blocker, deferred upstream** | Requires a scope dimension `KnowledgeModel` v0 explicitly does not have (its own §5) — not solvable inside Epistemic Dialogue. |
| Knowledge exists but scope becomes insufficient | **Architectural blocker, deferred upstream** | Same reason. |

**Explicit v0 boundary — a third form of epistemic humility, deliberately not yet built (named 2026-08-09, independent adversarial review, correction 3).** This document has always specified two forms of humility Epistemic Dialogue must have: (1) "I think I understood — confirm me" (Case A/B), and (2) "what I now understand contradicts what you taught me — did the convention change?" (Case C). The FRU-`UNKNOWN` row above reveals a third, distinct form that v0 intentionally does **not** implement: "I cannot form a hypothesis solid enough to ask you a closed question — help me understand your convention." A future Epistemic Dialogue must be capable of something equivalent to: *"Je ne parviens pas à déterminer de manière suffisamment fiable la convention utilisée pour ces montants. Pouvez-vous m'indiquer comment ils doivent être interprétés ?"* — asked only when uncertainty is material, deterministic reasoning has been exhausted, RECALL contains no answer, and no sufficiently defensible candidate exists. This future capability must preserve the exact governing principle this v0 slice already proves end-to-end: competence first → uncertainty recognized → relevant human question → answer remembered → question not repeated unless evidence changes. It is not implemented here because it requires a general natural-language question engine and free-text answer interpretation, both explicitly out of scope for this vertical slice (§8, §10). **This is recorded here so "UNKNOWN → silence" can never later be mistaken for the desired final architecture** — it is a deferred capability, not a solved problem, and not the same thing as "Pepperyn has nothing more to learn here."

## 14. First implementation contract — smallest justified slice

The chain the mission proposes survives the analysis and matches this engagement's own established precedent closely, not coincidentally:

```
FRU deterministic detector (STUB, per FRU's own not-yet-built first slice)
  → Epistemic Dialogue (ClarificationNeed, COMPARE, materiality-by-subject, question templates, answer gate — THE new work)
    → KnowledgeModel.recall() / .confirm() (already built, merged, canonical — zero changes)
      → simulated human answer (structured test input, not a chat UI — same pattern as every prior "first slice" in this engagement)
```

**FRU's detector is a stub, honestly labeled, not the real thing** — `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md` already named its own blockers (formula/structure exposure in the parser unverified) and never claimed to be implemented; an Epistemic Dialogue v0 implementation mission would need a minimal deterministic fixture standing in for it, exactly as Knowledge Model v0's own "Phidani four-upload learning loop" test used a minimal stub rather than real FRU.

**Correctly excluded**, per the mission's own list and confirmed independently by every section above: real chat UI (§11), LLM (§10), a generic multi-type dialogue engine (v0 is Understanding Dialogue only, one subject), multi-subject FRU, Familiarization, DecisionArc, recommendations, agents. None of these are load-bearing for proving the cognitive loop; all would be scope creep against the stated goal of demonstrating a complete loop, not building the rest of Pepperyn.

## 15. Adversarial self-test

**Central question:** is this a collaborator that knows when to ask, or a sophisticated conditional form?

- **Rules artificially specific to Phidani?** Partially, honestly: the materiality table (§6) has exactly one entry, and it's hardcoded `ALWAYS_MATERIAL`. This is real but narrow — it works because `EXPENSE_SIGN_CONVENTION` happens to be a subject where the materiality answer is genuinely unambiguous, not because v0 has solved general materiality. Named explicitly, not hidden.
- **False learning?** No — inherited directly from `KnowledgeModel`'s own hardened, adversarially-reviewed CONFIRMED-only design; nothing here weakens it.
- **Useless questions?** Actively guarded against, not just claimed: Case A and the detector-`UNKNOWN` case are both designed to produce *silence*, not merely documented to prefer it.
- **Repetition?** RECALL-before-ASK plus chain-head resolution structurally prevents re-asking a *confirmed* fact. An unresolved, declined, or ignored question legitimately resurfacing on a later upload is not repetition-as-flaw — it is honest persistence of real uncertainty, and conflating the two would be a mistake, not a discovery.
- **Badly-scoped memory?** This was a real, previously-live risk (Engagement-scoping) — now genuinely closed by the Knowledge Model arbitration, not merely asserted closed.
- **Abusive promotion?** No path exists: `confirm()` is only ever reached through the four-stage gate in §9, `provenance` stays fixed, no LLM path exists in v0.
- **Hidden LLM dependency?** Stress-tested directly: question generation is a deterministic template (§8); answer interpretation for v0's constrained input is a deterministic mapping (§9); FRU's detector is deterministic by its own scoping. No step in the v0 contract secretly requires an LLM.
- **Hidden chat dependency?** Tested directly in §11 and found absent.
- **Inability to handle "I don't know"?** Explicitly designed for (`DECLINE`, §9, §13), not an oversight discovered late.

**What makes this more than a conditional form:** a clever form doesn't refuse to exist without first consulting memory. §6's RECALL-before-ASK, made structurally testable rather than merely documented, is the one property here a form-based system would have no reason to build. That is the genuine, defensible claim — not that Epistemic Dialogue v0 already understands materiality or company culture broadly, which it honestly does not yet.

## 16. Adversarial matrix A–L (final arbitration, 2026-08-09)

Every outcome below is derived from rules already established in §3–§15 — no new rule is introduced except where explicitly cross-referenced (§9's `ConcurrentRootConflictError` handling, item K).

| # | Scenario | Outcome |
|---|---|---|
| A | No prior knowledge + strong candidate | **ASK** — Case B (§6), confirmation-form (§8). |
| B | Same prior knowledge + same candidate | **DO NOT ASK** — Case A (§6); no `ClarificationNeed` constructed. |
| C | Prior knowledge + contradictory candidate | **ASK** — Case C (§6), contradiction-form (§8). |
| D | No prior knowledge + no defensible candidate | **REMAIN UNKNOWN** — FRU returns `UNKNOWN`, no `candidate_value` exists, no `ClarificationNeed` constructed (§13, detector-`UNKNOWN` row). |
| E | Human confirms candidate | **CONFIRM** — stage 4 (§9); `SUPERSEDE` variant if this was Case C (`relates_to_knowledge_id` set). |
| F | Human rejects candidate, supplies valid alternative | **CONFIRM** (with the human-supplied value, §4 Case-6 note) — `SUPERSEDE` if a prior row existed. |
| G | Human gives ambiguous answer | **REMAIN UNKNOWN** — `UNINTERPRETABLE` (§9); no `confirm()` call, nothing persisted. |
| H | Second upload after confirmation | **DO NOT ASK** — `recall()` now returns the confirmed row → Case A (§12 Upload 2/4). |
| I | Different Entity | **ASK** — `recall()` scoped by `entity_id` returns `None` regardless of other Entities' knowledge → Case B, never suppressed (§7 falsifiability note). |
| J | Different subject | **ASK or DO NOT ASK, independently** — each `(entity_id, subject)` tuple resolves its own Case A–E entirely independently of any other subject (§7). |
| K | Concurrent human confirmation | **CONFIRM (one writer) + re-RECALL→Case A (the other)** — now structurally protected by `KnowledgeModel` v25 (successor race) and v26 (root race, closed 2026-08-09); the losing `confirm()` call is rejected by PostgreSQL and recovered exactly as specified in §9's new paragraph, never retried, never reported to the human as their answer being wrong. |
| L | Knowledge changes legitimately over time | **SUPERSEDE** — this is Case C under a different name; identical to item C/E, included here for completeness against the mission's own list. |

No ambiguous outcome found. Item K is the only row whose outcome changed by this arbitration pass (previously would have read "structurally unprotected, see Biggest Risk" — see §5/§9/§13 updates above).

---

## FINAL REPORT

```
DOCTRINAL RECONCILIATION:            DONE — 5/5 stale claims corrected surgically, verified no contradiction remains
EPISTEMIC DIALOGUE PROFESSIONAL RESPONSIBILITY:  decide whether Pepperyn already knows the answer before ever
                                      considering asking a human, and gate whether a human's answer becomes
                                      canonical knowledge
DOMAIN OWNER:                        Epistemic Dialogue owns ClarificationNeed, COMPARE, materiality-by-subject,
                                      question content, and the confirm()-gate; it does not own RECALL's
                                      mechanism, FRU's reasoning, or Evidence's observations
CLARIFICATION NEED:                  DEMONSTRATED as necessary (not assumed), reduced from 6 illustrative
                                      fields to 4 (entity_id, subject, candidate_value, recalled_value)
CLARIFICATION NEED PERSISTENCE:      NOT PERSISTED — ephemeral, freshly regenerated; every listed consequence
                                      resolves cleanly without durable state
RECALL BEFORE ASK:                   Formalized as a structurally testable invariant (mandatory constructor
                                      parameter + AST-based call-order test), five cases (A-E) fully specified
NEVER ASK TWICE:                     Formalized as identity-by-(entity_id, subject) tuple only; no semantic
                                      similarity engine; contradiction is a differently-phrased question, not
                                      a repeat
MATERIALITY:                         Fixed, named property per subject (v0: one subject, ALWAYS_MATERIAL) —
                                      not a scoring engine, honestly narrow
CONTRADICTION:                       Not silently overwritten, not silently ignored, not re-asked as if new —
                                      a targeted contradiction-form question naming what changed
HUMAN AUTHORITY:                     Four gated stages (received → interpreted → candidate → confirmed);
                                      Epistemic Dialogue is the sole gate at the last transition
KNOWLEDGE PROMOTION:                 Only via explicit KnowledgeModel.confirm(), human-attributed, legal-value
                                      gated — never automatic, never LLM-authorized alone
LLM ROLE:                            v0 = ZERO LLM calls. Trust Gateway not implemented; proven unnecessary for
                                      v0 by the deterministic template (§8) and deterministic answer-mapping (§9)
CHAT ROLE:                           Presentation/delivery surface only — tested directly, architecture survives
                                      chat's removal
FRU RELATIONSHIP:                    Upstream producer of the Candidate (REASON step); Epistemic Dialogue never
                                      reinterprets raw data itself
KNOWLEDGE MODEL RELATIONSHIP:        Downstream memory, called via recall()/confirm() only — zero changes
                                      required to the merged v0 implementation
EVIDENCE RELATIONSHIP:               Out of scope, upstream of FRU — Epistemic Dialogue never touches Evidence
                                      directly
FIRST PHIDANI LOOP:                  Walked through end to end against every rule in this document — internally
                                      consistent, matches the required 4-upload scenario exactly
UNKNOWN BEHAVIOR:                    Absence of a KnowledgeModel row = Unknown; no ClarificationNeed created
                                      when FRU itself returns UNKNOWN (nothing meaningful to confirm)
AMBIGUOUS KNOWLEDGE BEHAVIOR:        KnowledgeChainIntegrityError must never be treated as Case B; distinct
                                      escalation path required, ordinary question forbidden
IGNORED QUESTION:                    Handled for free by ephemeral design — no special-case code needed
MULTIPLE HUMAN ANSWERS:              Case C protected by KnowledgeModel's UNIQUE constraint (v25); Case B
                                      (competing brand-new confirmations) now ALSO protected (v26, closed
                                      2026-08-09) — the losing confirm() call is rejected by PostgreSQL and
                                      recovered via re-RECALL, never retried, never reported as the human's
                                      answer being wrong (§9, §16 item K)
NEW EVIDENCE BEFORE ANSWER:          Handled for free by ephemeral design — fresh RECALL every run
FIRST IMPLEMENTATION SLICE:          FRU stub detector -> Epistemic Dialogue (new logic) -> KnowledgeModel
                                      recall()/confirm() (unchanged) -> simulated human answer
NEW PERSISTENCE REQUIRED:            NO
NEW MIGRATION REQUIRED:              NO
NEW LLM CALL REQUIRED:               NO
TRUST BOUNDARY IMPACT:               NONE for v0 (zero LLM calls); Trust Gateway remains a hard blocker for any
                                      future LLM-assisted phrasing/interpretation
ARCHITECTURAL CONFLICT:              NONE found against Knowledge Model v0 (base + root-uniqueness repair) or
                                      the reconciled foundations
BIGGEST RISK (PREVIOUSLY):           Case-B concurrent-first-confirmation race at the KnowledgeModel layer —
                                      CLOSED 2026-08-09 by migration v26 (UNIQUE(entity_id, subject) WHERE
                                      relates_to_knowledge_id IS NULL), proven live including genuine two-
                                      thread concurrency against real PostgreSQL (local + Pepperyn Integration
                                      Test). This document's own §5/§9/§13/§16 updated to describe the
                                      resulting architecture, not merely mark the old risk "resolved."
REMAINING RESIDUAL ITEM:             Not a defect: §9's ConcurrentRootConflictError recovery behavior (catch
                                      → re-RECALL → treat as Case A) is a v0 design decision correctly derived
                                      from KnowledgeModel's own exception contract, but has not yet been
                                      exercised by a real test — normal pre-implementation status, to be
                                      covered by the first implementation slice's own test contract, not a
                                      reason to withhold promotion (matches the precedent set by every other
                                      contract promoted to canonical in this engagement before its own
                                      implementation phase)
BIGGEST COMPETITIVE OPPORTUNITY:     RECALL-before-ASK as a structural, code-shape guarantee rather than a
                                      convention — most conversational AI either always asks or never
                                      remembers; a provably-enforced memory-before-question invariant is a
                                      genuine, demonstrable differentiator once wired to a real surface
IMPLEMENTATION READINESS:            Contract is implementable as specified; no blocking architectural gap
                                      remains — the one prior blocking reservation (Case B race) is closed
DOCUMENT:                            docs/Architecture/Cognitive/EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md
BRANCH:                              architecture/epistemic-dialogue-v0-2026-08-09
CURRENT BRANCH:                      main (after this mission)
FINAL VERDICT:                       A — CANONICAL AND READY FOR IMPLEMENTATION
```

**Why A, not B (revised 2026-08-09):** the single reservation that kept the prior arbitration at B — the Case-B concurrent-first-confirmation gap — is now structurally closed by canonical Knowledge Model v0 (migration v26), proven live including genuine two-thread concurrency, not merely asserted closed. This arbitration pass re-attacked every other section (§3–§15) against the mission's own fresh adversarial demands (RECALL-before-ASK ownership, `ClarificationNeed`'s six-case re-attack, never-ask-twice falsifiability, the human-authority gate, contradiction/supersession sequencing, question-quality structure, the chat boundary — independently verified against the real `conversation_engine.py`, not just argued — the LLM boundary, the first slice, and a full A–L adversarial matrix, §16) and found no new blocking gap, only small clarifications worth making explicit (§4, §7, §8) and one genuinely new, correctly-scoped design decision (§9's `ConcurrentRootConflictError` recovery). Nothing here was marked "resolved" without describing the architecture that now actually exists — matching this engagement's own established discipline of not papering over the difference between a reservation being closed and a reservation being ignored.

---
*Companion documents (doctrinally corrected 2026-08-09): `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.*
