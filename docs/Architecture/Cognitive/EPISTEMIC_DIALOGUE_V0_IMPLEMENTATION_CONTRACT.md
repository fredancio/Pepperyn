# EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md

**Status:** PROPOSED — architecture/documentation mission, read-only, not yet approved, not yet implemented.
**Branch:** `architecture/epistemic-dialogue-v0-2026-08-09` (not merged).
**Depends on:** `docs/Architecture/Cognitive/KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md` — MERGED, CANONICAL, `main` commit `773cb0b` (migrations v24/v25, `services/knowledge_model_service.py`, adversarially reviewed, structurally protected against branching). This document does not reopen, re-derive, or restate Knowledge Model's own design — it treats `confirm()`/`recall()` as a fixed, trusted API.
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

## 5. Persistence question — examined, resolved: NOT persisted in v0

Tested against every listed consequence, and every one resolves cleanly under a purely **ephemeral, freshly-regenerated** model — the same discipline already applied to Candidate inside `KnowledgeModel` itself, not a new pattern invented here:

- **User quits before answering** — nothing was confirmed, so nothing is lost. The next time REASON+RECALL run (next upload, next visit), an equivalent `ClarificationNeed` regenerates deterministically, because FRU and `recall()` are both deterministic.
- **Returns tomorrow** — same reasoning; regeneration is idempotent, not a re-ask of something already settled, because nothing was ever settled.
- **Multiple uploads intervene** — an ephemeral model naturally uses only the *latest* upload's candidate; there is no stale, accumulating queue of unresolved questions to reconcile.
- **New Evidence makes the question moot** — the next loop run re-checks RECALL fresh; if knowledge now exists (someone else answered, or a deterministic promotion occurred), Case A fires and no new `ClarificationNeed` is even created.
- **Another user of the same Entity answers first** — same mechanism: whoever's answer reaches `confirm()` first is reflected in RECALL for everyone afterward. (The write-time race this implies is a real, separate concern — see §13 case 11 and the Biggest Risk in the final report; it is a `KnowledgeModel`-layer question, not solved by Epistemic Dialogue's own persistence choice.)
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

## 8. Question quality — domain content vs. presentation wording

**Structure is domain; phrasing is presentation.** `ClarificationNeed`'s four fields (§4) guarantee that *any* future rendering surface can construct a question containing all three required epistemic components — **OBSERVATION** (what was seen/recalled), **HYPOTHESIS** (the candidate), **MINIMAL CONFIRMATION REQUEST** (a yes/no or a correction, never an open interrogative) — without needing anything beyond those four fields. That guarantee belongs to the domain.

The exact sentence is presentation, and for v0 is a **deterministic Python string template, zero LLM** (§10), proven sufficient by construction for the two required cases:

- Case B (confirmation-form): *"J'ai parcouru votre fichier et il semble que vos charges soient présentées en valeurs positives. Est-ce exact ?"* — generated from `candidate_value` alone (`recalled_value is None`).
- Case C (contradiction-form): *"Jusqu'ici vos charges étaient présentées en valeurs positives. Ce fichier semble utiliser des signes négatifs. Cette convention a-t-elle changé ?"* — generated from both `recalled_value` and `candidate_value`, explicitly naming what changed rather than repeating the generic original question (this is also what keeps Case C from *reading* like "asking twice," even though it touches the same tuple).

A future LLM-generated variant may replace the template's wording later (§10) without changing what `ClarificationNeed` must structurally guarantee.

## 9. Human authority — four boundary stages, one gate

A human can confirm, correct, indicate a convention change, or provide context absent from the data. **A human response never automatically becomes canonical knowledge.** Four distinct stages, with Epistemic Dialogue as the sole gate between the third and fourth:

1. **Answer received** — raw input from whatever surface delivered the question (§11). For v0's Golden Loop, a constrained yes/no/correction signal, not free text.
2. **Answer interpreted** — mapped to exactly one of: `CONFIRM`, `CORRECT_TO(value)`, `DECLINE`, `UNINTERPRETABLE`. For v0's constrained input this mapping is a trivial deterministic function; free-text interpretation (§10) is a v1+ capability, architecturally anticipated but not exercised here.
3. **Knowledge candidate** — only `CONFIRM` and `CORRECT_TO(value)` reach this stage, and only if the resulting value is a *legal* member of the subject's registry (mirroring `KnowledgeModel`'s own value CHECK). An interpreted answer proposing an illegal value is treated as `UNINTERPRETABLE`, never silently coerced.
4. **Confirmed canonical knowledge** — reached only via an explicit `KnowledgeModel.confirm()` call, with `confirmed_by` set to the real human identity (never a system account, never "LLM"), `provenance` remaining `HUMAN_CONFIRMATION` as `KnowledgeModel` already fixes it, and — for Case C — `relates_to_knowledge_id` set to the row being superseded.

**No LLM can reach stage 4 alone**, even where an LLM assists at stage 2 (§10): an LLM's interpretation is itself treated as another candidate requiring the same legality/unambiguity gate as any other input, never trusted as a direct authorization to call `confirm()`.

## 10. LLM role — and why v0 has none

Candidate future responsibilities: reformulating a hypothesis in natural language, phrasing the confirmation question, interpreting free-text answers, explaining *why* Pepperyn is uncertain. Forbidden, permanently: creating canonical truth alone, bypassing RECALL, bypassing Evidence, promoting Knowledge, inventing a company convention that wasn't actually observed or confirmed.

**Trust Gateway impact, decisive for v0.** `TRUST_BOUNDARY_CLOSURE_PLAN.md` is a plan only, not implemented (confirmed in the FRU/Epistemic Dialogue foundation, §11 there). Any LLM call in this loop — even "just" phrasing a question — would require sending entity-specific content through the not-yet-built Trust Gateway. Given that (a) this blocker already forced FRU's own first slice to zero LLM calls, and (b) §8 above proves the two required Golden Loop questions are fully producible by deterministic template with no loss of quality, the conclusion is the same one already reached twice in this engagement: **the v0 implementation contract must specify zero LLM calls.** This is not a compromise forced by the blocker alone — it is independent proof that the *cognitive* loop (deciding whether to ask, about what, and how to gate an answer) does not actually require an LLM to be demonstrated end-to-end. Natural-language richness is a v1+ enhancement, blocked on the Trust Gateway, layered on top of an already-complete decision structure.

## 11. Chat role — tested, holds

**Proposition:** chat is a presentation-and-interaction surface for epistemic events, not the domain itself. **Test:** can a `ClarificationNeed` be created, evaluated, and resolved into a `confirm()` call with zero chat UI involved? Yes — nothing in §4 through §9 references a chat surface, a message, or a conversation. The Golden Loop (§12) is driven entirely by a simulated human answer, exactly matching how every other "first slice" in this engagement has been proven (FTE's Walking Skeleton, Knowledge Model's own Phidani loop test) — through a test harness, not a UI.

**Removing chat does not destroy Epistemic Dialogue.** The reverse test the mission proposes — "if removing the chat UI destroys the architecture, the architecture is probably wrong" — passes: `ClarificationNeed`, RECALL-before-ASK, COMPARE, materiality-by-subject, and the confirm-gating logic in §9 all function identically whether the question is ultimately delivered via chat, an upload-confirmation banner, an onboarding step, a review-screen prompt, or a notification. Chat is one interchangeable delivery mechanism among several, not Epistemic Dialogue's identity.

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
| Detector uncertain (FRU returns `UNKNOWN`) | **Required now** | No candidate exists to confirm — Epistemic Dialogue creates no `ClarificationNeed` and stays silent; asking "is nothing true?" would be nonsensical, not cautious. |
| Knowledge absent (Case B) | **Required now** | §6. |
| Knowledge agrees (Case A) | **Required now** | §6. |
| Knowledge contradicts (Case C) | **Required now** | §6. |
| Knowledge ambiguous/corrupt (Case D) | **Required now** (behavior); escalation mechanism **safe to defer** | Must never silently degrade to Case B (§6). |
| User says "I don't know" | **Required now** | Interprets to `DECLINE` — no `confirm()` call, nothing persisted, uncertainty stays open; may resurface on the next upload without violating "never ask twice" (nothing was ever confirmed). |
| User gives an irrelevant answer | **Required now** (basic catch-all `UNINTERPRETABLE`); rich free-text handling **safe to defer** | Never silently guesses a value. |
| User contradicts themselves across turns | **Safe to defer** | Requires session-level state tracking beyond v0's single-turn, ephemeral `ClarificationNeed`. |
| Question ignored | **Required now, free** | Already correctly handled by §5's ephemeral design — no new code needed. |
| New Evidence arrives before answer | **Required now, free** | Same reason — fresh RECALL on every run. |
| Two humans answer differently | **Safe to defer, but named precisely** | For Case C (supersession), `KnowledgeModel`'s `UNIQUE(relates_to_knowledge_id)` (v25) already prevents two competing successors. For Case B (two people confirming a **brand-new** subject simultaneously — two competing `NULL`-predecessor roots), no equivalent protection exists yet at the `KnowledgeModel` layer; this is an inherited, previously-named residual gap (KM v0's adversarial review), not a new discovery, and not something Epistemic Dialogue can close on its own. See Biggest Risk in the final report. |
| Same Entity, future multiple Engagements | **Required now, already correct** | Everything is scoped by `entity_id`, never `engagement_id` — Engagement is recorded only as acquisition context on the eventual `confirm()` call. |
| Convention differs by sheet/template | **Architectural blocker, deferred upstream** | Requires a scope dimension `KnowledgeModel` v0 explicitly does not have (its own §5) — not solvable inside Epistemic Dialogue. |
| Knowledge exists but scope becomes insufficient | **Architectural blocker, deferred upstream** | Same reason. |

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
MULTIPLE HUMAN ANSWERS:              Case C protected by KnowledgeModel's existing UNIQUE constraint (v25);
                                      Case B (competing brand-new confirmations) NOT yet protected — named,
                                      inherited, not solved here
NEW EVIDENCE BEFORE ANSWER:          Handled for free by ephemeral design — fresh RECALL every run
FIRST IMPLEMENTATION SLICE:          FRU stub detector -> Epistemic Dialogue (new logic) -> KnowledgeModel
                                      recall()/confirm() (unchanged) -> simulated human answer
NEW PERSISTENCE REQUIRED:            NO
NEW MIGRATION REQUIRED:              NO
NEW LLM CALL REQUIRED:               NO
TRUST BOUNDARY IMPACT:               NONE for v0 (zero LLM calls); Trust Gateway remains a hard blocker for any
                                      future LLM-assisted phrasing/interpretation
ARCHITECTURAL CONFLICT:              NONE found against Knowledge Model v0 or the reconciled foundations
BIGGEST RISK:                        Case-B concurrent-first-confirmation race at the KnowledgeModel layer
                                      (two competing NULL-predecessor roots for a brand-new (entity, subject))
                                      is not closed by the existing UNIQUE(relates_to_knowledge_id) constraint,
                                      which only protects successor branching — inherited, named, not invented
                                      here, not solved in this document
BIGGEST COMPETITIVE OPPORTUNITY:     RECALL-before-ASK as a structural, code-shape guarantee rather than a
                                      convention — most conversational AI either always asks or never
                                      remembers; a provably-enforced memory-before-question invariant is a
                                      genuine, demonstrable differentiator once wired to a real surface
IMPLEMENTATION READINESS:            Contract is implementable as specified; one named, non-blocking residual
                                      risk (Case B race) to weigh before or shortly after a first implementation
DOCUMENT:                            docs/Architecture/Cognitive/EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md
BRANCH:                              architecture/epistemic-dialogue-v0-2026-08-09
CURRENT BRANCH:                      main (after this mission)
FINAL VERDICT:                       B — READY WITH NAMED RESERVATIONS
```

**Why B, not A:** every phase resolved to a specific, testable design with no unresolved architectural question — except the Case-B concurrent-first-confirmation gap, which this document correctly refuses to silently paper over (consistent with the discipline this whole engagement has followed) and correctly refuses to solve unilaterally, since it belongs to `KnowledgeModel`'s own migration surface, not to this document's scope. That single named reservation, not any doubt about the loop's own design, is what keeps this at B.

---
*Companion documents (doctrinally corrected 2026-08-09): `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.*
