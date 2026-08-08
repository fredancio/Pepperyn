# EPISTEMIC_DIALOGUE_FOUNDATION.md

**Status:** PROPOSED — architectural discovery, read-only mission, not yet approved, not yet implemented.
**Branch:** `architecture/fru-epistemic-dialogue-2026-08-08` (not merged).
**Companion documents:** `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.

---

## 1. Professional responsibility

**Epistemic Dialogue:** resolve material uncertainty that cannot be reliably resolved from available Evidence and existing enterprise knowledge, then convert useful human clarification into reusable, scoped, and revisable knowledge.

This gives operational shape to `PEPPERYN_PROFESSION_MODEL.md`'s responsibility #5 ("Questionner" — *"détecter ce qui ne colle pas, exiger une explication, refuser le silence sur une anomalie"*), which that document itself flags as its most important unaddressed gap: *"nommée dans le Modèle Idéal depuis le début mais n'a jamais reçu de phase d'implémentation dans le Blueprint."* This mission is the first phase of that implementation, not a chat feature invented independently of it.

## 2. Chat is a surface, not the domain (Mission 29)

The domain event is never `ChatMessage`. A human typing a sentence is the *medium*; the meaningful thing that happened is always one of a small set of domain events:

- `HumanConfirmedInterpretation`
- `HumanCorrectedConvention`
- `DecisionAccepted`
- `ExecutionConfirmed`

Designing `ChatMessage → Knowledge` as a direct pipeline would collapse this distinction and make the system's memory dependent on transcript parsing rather than domain semantics — exactly the failure the mission warns against. The chat UI is one possible input surface for these events; a structured confirmation banner, a form, or a future voice interface could equally produce the same domain event. **Epistemic Dialogue's domain logic must not assume chat is the only surface**, even though chat is the only surface under active consideration today.

This also resolves why `conversation_engine.py` cannot simply be extended: today it is a single-mode, explain-only Q&A wrapper around a pre-computed `ExecutiveCase V2` (confirmed by direct reading: *"Préparer le payload LLM et appeler Claude Sonnet pour répondre aux questions d'un CEO"*, no concept of dialogue type or clarification exists in it), and — separately and more seriously — it is the **confirmed, most severe active Trust Boundary bypass** in the repository today (`ANONYMIZATION_CAPABILITY_REVIEW.md`: the re-identified, full case dossier is sent to Claude Sonnet on every turn). Epistemic Dialogue is a new capability that could eventually use a chat surface; it must not be built by extending this specific mechanism as it exists today. See §11.

## 3. Question lifecycle

```
OBSERVE (Evidence + FRU)
  → REASON (deterministic rule, or LLM hypothesis clearly marked as such)
  → RECALL (existing Confirmed Context in KnowledgeModel — has this org already taught us this?)
  → ASSESS UNCERTAINTY (FACT / STRONG_INFERENCE / HYPOTHESIS / UNKNOWN)
  → ASSESS MATERIALITY (could a wrong answer materially distort analysis or decision?)
  → ASK IF NECESSARY (§4 — only when uncertainty × materiality actually justifies interruption)
  → HUMAN CONFIRMS / CORRECTS / PROVIDES CONTEXT
  → DOMAIN EVENT emitted (never the raw transcript, §2)
  → LEARN (KnowledgeModel entry created/promoted, or DecisionArc updated, depending on dialogue type, §8)
  → REMEMBER (at the correct, explicit, never-assumed-global scope, §7)
  → REUSE (next occurrence checks RECALL first, §5)
  → DETECT FUTURE CONTRADICTION (§6)
```

Every question must be traceable backward through this chain to a named knowledge gap (Mission 31). "The LLM decided to chat" is never a valid trace.

## 4. When Pepperyn must ask / must not ask

Four non-negotiable principles, unchanged from the mission brief because direct testing against the existing canon confirmed all four are consistent with it, none needed to be weakened:

1. **Ask only after reasoning.** REASON and RECALL must both be exhausted first. Directly enforces Constitution Article XI's compliance test (*"peut-il être relié à une source, ou introduit-elle une assertion invérifiable?"*) applied to the *decision to ask*, not just to answers.
2. **Prefer confirmation over interrogation.** "I reviewed your file. Expenses appear to be presented as positive values, classified by account nature. Is that correct?" — not "How are expenses represented?" This is a direct demonstration of the COMPETENT quality (§9) and is the only form the first vertical slice's single question takes.
3. **Ask only when uncertainty × materiality justifies interruption** — deliberately not reduced to a formula in this document either; the mission is explicit that a numeric threshold would be false precision (mirrors the same rejection in the FRU companion document §5).
4. **Never ask twice what the organisation already taught, unless new evidence materially contradicts it.** Operationalized as the RECALL step above — a genuine architectural obligation (RECALL must run, and must actually be checked, before ASK), not merely a UX nicety. This is the **Repeated Clarification Rate invariant** the mission names in §30: for a stable organisation, structural clarification burden should trend toward zero as `KnowledgeModel` accumulates confirmed entries. What makes this *enforceable* rather than aspirational: the ASK step must be structurally incapable of firing without first querying `KnowledgeModel` for an existing Confirmed Context at the applicable scope — this is a testable invariant (companion slice document names the exact test), not a policy asked of the LLM's good behavior.

**While a question is pending** (adversarial review, CFO persona): an unanswered clarification must never block core value delivery. Pepperyn continues reasoning using its current `HYPOTHESIS`/`STRONG_INFERENCE`-tier interpretation, explicitly labeled as provisional wherever it surfaces, rather than stalling analysis on a human response that may never come. The question and the analysis are independent outputs of the same REASON step, not a gate on each other.

**When Pepperyn must not ask** (Mission 14, "never ask the human to do Pepperyn's job"): if a competent professional could reasonably resolve the answer from the available source — an explicit account code range, a closing arithmetic check, an already-confirmed convention — Pepperyn must resolve it itself. The clarification budget is reserved for genuine, materially consequential, company-specific meaning — never for column/row/month identification a deterministic parser should already handle (that is Evidence's and FTE's job, already solved; asking about it would be LAZY PEPPERYN, §12).

## 5. Human confirmation / correction and memory implications

A human response to an Understanding Dialogue question does exactly one of three things:

- **Confirms** the proposed interpretation → the Candidate Context (from FRU's Inference tier) is promoted to Confirmed Context, at the scope the question was actually asked at (never wider — §7).
- **Corrects** the proposed interpretation → a *different* Confirmed Context is recorded, and the original hypothesis is retained only as a superseded Candidate, never silently deleted (mirrors the One New Truth Rule's own pattern: freeze the old as a historical projection, don't merge it into the new). Adversarial review (AI reliability persona) flagged one distinction this document deliberately leaves open rather than resolving here: a correction can mean either "this organisation is a genuine, legitimate exception" or "the deterministic detector itself is systematically wrong." Distinguishing these — e.g. via correction-rate monitoring across organisations — is a real future concern, explicitly out of scope for this foundation and for the first vertical slice.
- **Declines to answer / defers** → the uncertainty remains open; Pepperyn must not treat silence as confirmation, mirroring Constitution Article III's prohibition on treating absence as a positive claim.

## 6. Contradiction / change behaviour

New observation conflicts with an existing Confirmed Context → **Contradiction**, never one of: silent overwrite, blind continued application of the old rule, or re-asking the original question as if nothing had ever been learned (all three explicitly named as failure modes in Mission 18 and again in Mission 35 as AMNESIAC/DOGMATIC PEPPERYN).

The correct behaviour is a **targeted** Contradiction Dialogue that names what changed: *"Until now, your reporting presented expenses as positive values. In this file, several expenses appear negative. Has your reporting convention changed?"* — never the generic original question. If confirmed, the new Confirmed Context supersedes the old one *going forward*; the old knowledge remains historically true for its former scope/time window (a direct analogue of Evidence's own immutability discipline and of `origin_analysis_id`'s provenance-not-identity treatment in the DecisionArc work). This is professional memory, not amnesia and not dogma.

## 7. Knowledge scope (Mission 17) — a hierarchy, not a flag

Human confirmation must never be assumed to mean a universal, eternal rule. The FRU companion document's adversarial matrix (cases 11–12) proves scope can legitimately be finer than "one company forever": two sheets in one file can carry different conventions; two Entities absolutely must never share knowledge.

**Principle, not schema** (per the mission's own explicit instruction not to design the schema here): every Confirmed Context entry must carry an **explicit, recorded scope descriptor**, never an implicit or assumed one, and that scope must default to the *narrowest defensible boundary the evidence actually supports* — widening only through repeated, consistent confirming observation, borrowing `BusinessHistory`'s own INV-HISTORY-1 discipline (never promote confidence, here specifically scope-breadth, from a single occurrence). The realistic minimum boundary, given `KnowledgeModel`'s existing declared ownership (`COGNITIVE_CAPABILITY_MAP.md`: "propriété d'Engagement"), is **Entity/Engagement** — never global across organisations, never silently assumed workbook-wide when a sheet-level or template-level distinction is what the evidence actually supports.

## 8. Memory relationship — three families, tested for genuine distinctness (Mission 20)

| Family | Question it answers | Owner (existing canon) | Epistemic Dialogue's relationship |
|---|---|---|---|
| **Evidence Memory** | "What have we observed?" | Evidence Ledger | Epistemic Dialogue *reads* Evidence as REASON/OBSERVE input; never writes to it — Evidence stays immutable, source-only. |
| **Enterprise Understanding Memory** | "How should we interpret this organisation and its representation?" | **This is `KnowledgeModel`, already named and owned by Engagement in `COGNITIVE_CAPABILITY_MAP.md` — not a new memory family.** | Epistemic Dialogue's Understanding and Contradiction Dialogue types are the mechanism that promotes Candidate → Confirmed Context inside it. This is precisely the operational gap that document already named without designing ("LLM interdit for the final decision... requires human confirmation or explicit deterministic rule") — Epistemic Dialogue is the design for that missing mechanism, not a new store next to it. |
| **Decision Memory** | "What did we recommend, decide, execute, observe, learn?" | DecisionArc | Epistemic Dialogue's Decision and Execution Dialogue types produce DecisionArc-relevant events; Learning Dialogue (causal interpretation) most plausibly annotates DecisionArc too, though this mission does not resolve that placement definitively — named as an open question, not fabricated as settled. |

**Conclusion on Mission 19's core claim:** the memory the mission calls "Enterprise Understanding Memory" is real and genuinely distinct from Evidence and Decision Memory — but it already exists conceptually as `KnowledgeModel`. Naming it a fourth, new memory family would violate the One New Truth Rule. The genuine, non-duplicative contribution of this mission is not a new memory — it is the dialogue *mechanism* that fills the existing one.

## 9. Professional personality as system behaviour — challenged mapping

| Quality | Mission's mapping | This document's assessment |
|---|---|---|
| COMPETENT | tries to resolve reliably before asking | Confirmed correct; operationalized as REASON+RECALL before ASK (§3). |
| HUMBLE | never turns insufficiently-supported inference into fact | Confirmed correct; directly enforced by inheriting the existing "LLM never decides final promotion" rule (FRU companion §5/§7) rather than a new humility mechanism. |
| CURIOUS | asks when material unresolved ambiguity remains | Confirmed correct, with the explicit rejection of a numeric uncertainty×materiality formula (§4.3) preserved. |
| DISCIPLINED | remembers reusable knowledge, applies in correct scope | Confirmed correct; "correct scope" is the hard part, addressed in §7 as a hierarchy, not a flag. |
| VIGILANT | detects contradiction | Confirmed correct; §6 makes this a named event type, not a side effect. |
| ECONOMICAL WITH HUMAN ATTENTION | doesn't interrupt for low-value questions | Confirmed correct — and this document adds one refinement: economy is not just about *whether* to ask but about *batching*. A file that raises three genuinely material ambiguities should ideally surface them as one coherent review moment, not three separate interruptions. This is named as a design consideration for the eventual full mechanism, explicitly **not** part of the first vertical slice (companion document), which handles exactly one question.

No quality in the mapping needed to be removed; all six survive the challenge.

## 10. Dialogue types — common foundation, real differences

All six provisional types (Understanding, Context, Contradiction, Decision, Execution, Learning) share the same underlying shape: **Knowledge Gap → Clarification Need → Question → Human Response → Domain Event → Memory Update**. This is the "common Epistemic Dialogue foundation" Mission 28 asks whether exists — it does, and it is this five-step shape, not a shared implementation of any one step.

What genuinely differs between types:
- **Which gap triggers it** (an unresolved FRU interpretation vs. a business-context absence vs. a detected contradiction vs. a recommendation awaiting commitment vs. an execution status vs. a causal/learning question).
- **Which memory family the resulting domain event updates** (`KnowledgeModel` for Understanding/Contradiction; `DecisionArc` for Decision/Execution; Learning's placement is an open question, §8).
- **Who has authority to answer** (Constitution Article II reserves Context Dialogue's answers to the human exclusively, by construction — no amount of evidence ever resolves "why did the business do this" without asking; Understanding Dialogue, by contrast, is frequently resolvable without asking at all, per FRU §5–6).

This mission scopes the first vertical slice to exactly one type — Understanding Dialogue — specifically because it is the one FRU already supplies rich deterministic and inferential input for, making it the cheapest type to build honestly (companion slice document).

## 11. Trust Boundary implication

Two independent constraints compound here, not one:

1. Any dialogue step that sends label text or ambiguity context to an LLM for hypothesis generation or question phrasing must go through the (unimplemented) Trust Gateway — same constraint already named in the FRU companion document §10.
2. The only existing chat mechanism, `conversation_engine.py`, is independently confirmed as the most severe active Trust Boundary bypass in the repository (full re-identified case sent to the LLM every turn). Building Epistemic Dialogue's chat surface as an extension of this mechanism would compound an already-known, already-prioritized violation rather than avoid it.

**Conclusion:** the first vertical slice (companion document) is scoped to require zero LLM calls and zero dependency on `conversation_engine.py`, precisely to keep this discovery decoupled from both open Trust Boundary problems rather than adding a third dependency on their resolution.

## 11a. A named limitation (adversarial review, skeptical-engineer persona)

If an organisation changes both its account-code scheme and its sign convention in the same reporting cycle, a detector keyed on code-range + arithmetic could, in principle, fail to trigger Contradiction (both signals moved together, so neither alone looks inconsistent with itself). This is named honestly as a limitation of any code/arithmetic-only detector, not solved here — a materially rare scenario, but the kind of edge case that should be tested for explicitly whenever a real detector is built, not discovered in production.

## 12. Failure modes this document explicitly guards against

ARROGANT (guesses instead of asking) — guarded by §4's materiality principle and the FRU companion's "ask only when arithmetic/codes don't resolve it" cases.
LAZY (asks instead of reasoning) — guarded by §4's "ask only after reasoning" and §14's "never ask the human to do Pepperyn's job."
AMNESIAC (asks the same question every month) — guarded structurally by RECALL being a mandatory pre-ASK step (§4.4), not a policy.
DOGMATIC (keeps applying old knowledge despite contradiction) — guarded by §6 making Contradiction a first-class event type, never silent.
OVERCONFIDENT (LLM interpretation becomes fact) — guarded by inheriting FRU's existing LLM/human boundary, not weakening it (§4, FRU companion §7).
OVERENGINEERED (universal ontology nobody needs) — guarded by §8's conclusion that Enterprise Understanding Memory is not a new family, and by scoping the first slice to one dialogue type only.
MAPPING PEPPERYN (customer configures everything manually) — guarded by §4's "ask only when a competent professional couldn't resolve it alone."
PHIDANI-SPECIFIC (only works because rules were encoded for one Golden Case) — the companion slice document names this risk explicitly and requires the first slice's detector to degrade honestly to UNKNOWN off-Phidani rather than silently failing or guessing.

---
*Companion documents: `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.*
