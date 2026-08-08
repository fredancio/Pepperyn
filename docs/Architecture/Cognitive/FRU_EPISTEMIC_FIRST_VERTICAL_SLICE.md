# FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md

**Status:** PROPOSED — architectural discovery, read-only mission, not yet approved, not yet implemented, not yet authorized to build.
**Branch:** `architecture/fru-epistemic-dialogue-2026-08-08` (not merged).
**Companion documents:** `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md`.
**Discipline applied:** the same shrink-twice-through-arbitration discipline that reduced FTE from a 9-section ADR-003 v3 design to a single-field FTE v0 (Mission 41's explicit instruction). Mission 42's illustrative candidate is challenged and narrowed below, not adopted as-is.

---

## 1. Challenging Mission 42's candidate

The mission brief's illustrative first slice (observe Phidani's positive amounts + account codes + arithmetic → form interpretation → confirmation question → store → reuse → contradiction-on-divergence) is directionally right but larger than a disciplined v0 in three specific ways:

1. It implicitly assumes a working persisted `KnowledgeModel` to "store the learned convention at the correct scope." **`KnowledgeModel` does not exist as code today** — confirmed: `STRATEGIC_DEFERRED_WORK_REGISTER.md` §2.1 and `2.6` both list it as "conçu conceptuellement, non implémenté." This is not a detail; it is the single largest blocker below (§5).
2. It does not explicitly forbid LLM involvement, leaving the door open to §7/§26's "hypothesis generation" role bleeding into v0 — which would immediately trigger the Trust Gateway blocker (`EPISTEMIC_DIALOGUE_FOUNDATION.md` §11), an unrelated, larger, already-tracked piece of work.
3. It bundles detection + question + confirmation + persistence + reuse + contradiction into one slice — six moving parts, more than FTE v0's own five-phase minimal contract took on at once.

The slice proposed below removes exactly these three: it is deterministic-only (zero LLM), it does not persist anything new (no migration, matching this mission's explicit "no new table" constraint), and it proves the mechanism narrative (detect → ask once → recall → don't re-ask → detect contradiction) through **tests against an explicit in-memory/simulated knowledge store**, exactly the same way FTE's own architecture contract was proven through Golden Case tests before any schema was authorized.

## 2. Golden Case

Real Phidani.xlsx, same file already validated end-to-end by the FTE Walking Skeleton (`implementation/phidani-walking-skeleton-v1-2026-08-08`, not merged). One question only: **sign-display convention for expenses.**

Deterministic signals genuinely available in this specific file (confirmed by direct inspection during the Walking Skeleton mission, reused here rather than re-verified from scratch): Belgian PCMN-style account codes present (e.g. `70` = Chiffre Affaires, `60`–`66` range = charges), and live subtotal formulas (`row 6 = "=BM4+BM5"`) — i.e. this file happens to carry *both* signal types named in the FRU foundation document §6.

## 3. What is IN

- **One deterministic detector**, narrowly scoped: given (a) a row's account-code range where present, and (b) a declared subtotal's arithmetic relationship to its detail rows where present, propose a `HYPOTHESIS` or `STRONG_INFERENCE`-tier Candidate: "this reporting context displays expenses as positive absolute values." Degrades honestly to `UNKNOWN` when neither signal is available or when they disagree — never guesses (directly inherits FTE's "false UNKNOWN preferable to false classification" discipline).
- **One Understanding Dialogue question**, generated only when the Candidate is present but not deterministically certain, phrased as confirmation per principle 2 ("I reviewed your file. It appears that expenses are presented as positive values... Is that correct?") — never the open interrogative form.
- **One simulated knowledge record**, proving RECALL/never-ask-twice/Contradiction mechanics against an **explicit, test-only, in-memory structure** (mirroring exactly how `_RecordingSupabaseMock`/`_seeded_sandbox` proved the FTE Walking Skeleton's Engagement/DecisionArc continuity without needing real Postgres). This proves the *behavior* — ask once, recall on reprocessing, raise Contradiction on a later divergent file — without committing to a schema.
- **Explicit, named blocker documentation** (§5) rather than silent scope-narrowing — the gap between "this slice" and "real persisted Enterprise Understanding Memory" must be visible, not hidden by a convenient test double.

## 4. What is OUT

- All five other dialogue types (Context, Contradiction-as-its-own-full-mechanism-beyond-this-one-scenario, Decision, Execution, Learning).
- Any LLM call, anywhere, for any reason — zero, matching FTE v0's own zero-LLM discipline for its first increment.
- Multi-sheet / multi-Entity scope hierarchy (`EPISTEMIC_DIALOGUE_FOUNDATION.md` §7) — this slice operates at a single, fixed scope (one Entity, one reporting template) and does not attempt to prove the general hierarchy.
- `BusinessHistory` integration — sibling concern, not exercised here.
- Any chat UI wiring, `conversation_engine.py` changes, or any other production surface.
- Any real persistence: no migration, no new table, no write to Supabase — matching the parent mission's explicit constraint and this document's own §1 critique of Mission 42's candidate.
- Enterprise Familiarization integration — related but explicitly a separate mission (`EPISTEMIC_DIALOGUE_FOUNDATION.md` §2 already establishes Familiarization as a *consumer* of FRU content, not something this slice needs to wire up).
- Account-code-range knowledge for any chart of accounts other than the minimum needed to interpret Phidani's own codes — this slice is explicitly NOT a general chart-of-accounts library; using more than Phidani needs here would itself become PHIDANI-SPECIFIC PEPPERYN in the other direction (over-building for a case of one).

## 5. Blockers — named, not silently worked around

1. **`KnowledgeModel` does not exist as code.** This is the real, load-bearing blocker. Before any *persisted* version of this slice can be authorized, a "Knowledge Model v0 Minimal Implementation Contract" mission — structured the same way `FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md` was: professional responsibility → minimal invariant → smallest persisted primitive → arbitration — needs to happen first. This document recommends that mission as the actual next step, not this slice's persistence layer.
2. **Trust Gateway does not exist.** Any future version of this slice that adds LLM-based label hypothesis generation is blocked until `TRUST_BOUNDARY_CLOSURE_PLAN.md` is implemented. Named so it is never silently assumed available.
3. **File-parser formula/structure exposure not verified.** Whether `services/file_parser.py`/`services/financial_normalizer.py` currently exposes formula references (not just evaluated values) to any downstream consumer was not checked in this read-only mission — implementation-verification was out of scope. This slice's detector must not assume formula-reference access exists until confirmed.
4. **Belgian PCMN range table does not exist as a reusable, named resource anywhere in the codebase** (confirmed absent by the same research pass that grounded this mission — no chart-of-accounts constant table was found). A minimal, explicitly-scoped-to-Phidani range table would need to be introduced, clearly labeled as a narrow first case per Mission 32, not a general solution.

## 6. Tests required (if/when this slice is authorized for implementation)

Mirroring the FTE Walking Skeleton's own test architecture discipline (unit/invariant tests separate from one real-file Golden Case integration test):

- Detector: Belgian-range + arithmetic agree → `STRONG_INFERENCE`; disagree → `UNKNOWN` (never guesses); neither signal present → `UNKNOWN`.
- Question generation: fires only when Candidate is present and not already Confirmed at the applicable scope (simulated store); does not fire when arithmetic alone already resolves with certainty (§4 in the Epistemic Dialogue foundation: "must not ask" case).
- RECALL/never-ask-twice: second identical file, same simulated store state → no question generated. This is the direct test of the Repeated Clarification Rate invariant named in `EPISTEMIC_DIALOGUE_FOUNDATION.md` §4.4 — the single most important test in this slice, because it is what makes the "never ask twice" principle a structural guarantee rather than a hope.
- Contradiction: third file with divergent signs, same simulated store pre-seeded with a Confirmed entry → Contradiction event raised, phrased as the targeted (not generic) question form (§6 of the Epistemic Dialogue foundation).
- Isolation: zero LLM import anywhere in the slice's code (AST-based check, not substring — the lesson already learned twice in this repository's own test history, `TestTemporalRoleIsolation` and its reuse in the Walking Skeleton test).
- Real-file discipline: at least one test reads the actual Phidani.xlsx, not a synthetic reconstruction — same Golden Case rule already governing every other mission in this engagement.

## 7. Relationship to Enterprise Familiarization — determined, not merged

Distinct missions, confirmed by direct comparison: Familiarization (`PEPPERYN_PROFESSION_MODEL.md` Ch.5) is a *phase of Engagement's lifecycle* — a burst of accelerated ingestion when a new client's historical data arrives. FRU/Epistemic Dialogue is a *capability* exercised every time representation is uncertain, whether during Familiarization's burst or during ordinary monthly review. Familiarization will consume FRU's output faster and in greater volume than steady-state review does, but it does not own FRU, and FRU does not require Familiarization to exist first — confirmed by this slice itself, which is scoped entirely within an ordinary two-pass review scenario, not an onboarding burst.

---
*Companion documents: `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md`.*
