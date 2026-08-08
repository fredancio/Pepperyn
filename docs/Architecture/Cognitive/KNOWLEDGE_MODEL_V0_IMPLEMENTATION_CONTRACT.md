# KNOWLEDGE MODEL v0 — MINIMAL IMPLEMENTATION CONTRACT

**Status:** PROPOSED, read-only architecture mission — not approved, not implemented.
**Branch:** `architecture/knowledge-model-v0-2026-08-08` (not merged).
**Relationship to prior work:** operationalizes `KnowledgeModel` as already named (not invented) in `docs/Architecture/Cognitive/COGNITIVE_CAPABILITY_MAP.md` (faculté 2, "Comprendre l'organisation" — property of Engagement, states *Fact/Confirmed Context/Candidate Context/Unknown/Contradiction*, each carrying origin/date/confidence/scope), and supplies the missing mechanism that document already flagged without designing: *"Promotion Candidate Context → Confirmed Context... LLM interdit pour la décision finale — validation humaine ou règle déterministe explicite requise."* Applies the same shrink-to-minimal discipline that produced FTE v0.

---

## 1. Professional responsibility

Learn a durable, reusable interpretive convention about a specific organisation; recall it before ever asking again; detect when new evidence no longer fits it; and revise without erasing what was true before. Not "remember everything" — remember exactly what a competent controller would carry forward from one engagement to the next.

## 2. Boundary vs. Evidence / DecisionArc / chat

- **Not Evidence.** Evidence = "what did we observe" (immutable source fact). Knowledge = "how should we interpret this organisation." Knowledge may be *supported by* Evidence; it is never a second Evidence Ledger (§33 below).
- **Not chat history.** A transcript is not knowledge. The domain event `HumanConfirmedInterpretation` — not the sentence that produced it — is what may justify a Knowledge row. Raw conversation is never persisted here to fake memory.
- **Not LLM memory.** An LLM hypothesis is, at best, a Candidate. It cannot self-promote to Confirmed — inherited, unweakened, from the rule already fixed in `COGNITIVE_CAPABILITY_MAP.md` (§1 above).
- **Not DecisionArc.** DecisionArc tracks commitments and their trajectory. Knowledge tracks interpretive convention. A decision may later produce a learning that becomes Knowledge, but that is a separate, future act, not this contract's concern.

## 3. Epistemic lifecycle

Two row-bearing statuses only: **CANDIDATE** and **CONFIRMED**. *Unknown* is not persisted — per Constitution Article III, absence stays absence; the lack of a row already means Unknown, and inventing a row to say "we don't know" would itself be a fabricated presence. **Contradiction is not a third status** — this repository's own `ContradictionRecord` framing already settled this: *"objet orthogonal, pas un 5e statut."* A contradiction is represented as a new CANDIDATE row that references the CONFIRMED row it conflicts with (§16).

## 4. Ownership

Owner: **Engagement** — unchanged from existing doctrine, by the same reasoning already applied to `BusinessHistory` ("même logique... pas un objet flottant global"). Ownership (who is accountable for the row's lifecycle) and scope of applicability (how narrowly it is trusted to apply) are different questions — see §5.

## 5. Scope — minimum model for v0

**Engagement only.** No first-class `ReportingContext`/`SourceContext`/`TemplateContext` object for v0 — confirmed via direct repository search that no such concept has ever been proposed here; inventing one now, before a real multi-sheet/multi-template case exists in a Golden Case, would be speculative. Phidani itself is a single-sheet workbook — the two-sheet-divergent-convention scenario named in the mission brief does not arise in the actual first Golden Case.

**Not a dead end:** the scope is stored as an opaque `scope_key` (v0 value: `engagement_id` alone), not hard-coded as "engagement_id column, full stop." A future template-level discriminator can compose into the same key (e.g. `engagement_id + template_fingerprint`) without a schema rewrite — satisfies the complexity test (§45 of the mission brief): removing a first-class `ReportingContext` object leaves the v0 loop fully intact; keeping the key opaque-but-composable avoids blocking its later reintroduction.

## 6. Temporal validity

Two clocks, never conflated (same discipline as FTE's Business Time vs. Knowledge Time):
- `confirmed_at` — **knowledge time**: when Pepperyn learned this. Explicit, set only on promotion to CONFIRMED, never a bare `created_at` default (mirrors `observed_period_end`'s "explicit, never a DB default" rule).
- Business-time applicability (`valid_from_business_time`/`valid_to_business_time`, e.g. "this convention held from July onward") is **deferred**, not designed now — the v0 test contract (§ Test Contract) does not require retroactive dating, and adding a nullable date column later is additive, not destructive. Explicitly not a dead end.

## 7. Provenance / authority

`provenance` is a small controlled enum: `HUMAN_CONFIRMATION` (only value actually exercised by v0) plus `DETERMINISTIC_RULE` (reserved, admitted by the enum, not implemented — see §12). Never `LLM_HYPOTHESIS` as a promotion-capable provenance — an LLM hypothesis is input to REASON, never a provenance value a CONFIRMED row can carry. `confirmed_by` (actor identity, nullable, required when provenance = HUMAN_CONFIRMATION) is included now — cheap, and forward-compatible with future multi-user authority (§37 of the brief); role-based enforcement is explicitly deferred.

## 8. Resolution rules

Given `(engagement_id, subject)`, return the single most recent CONFIRMED row (by `confirmed_at`) with no unresolved CANDIDATE referencing it via `relates_to_knowledge_id` (§16). If an unresolved reference exists, resolution returns **ambiguous / pending** rather than silently trusting the old CONFIRMED value — directly enforces "must not silently adapt" (mission brief §16). No scoring engine; with exactly one scope level in v0, the "narrower scope wins" precedence question (mission brief §36) is **structurally inapplicable** — named for future design, not built now.

**Database-architect review caught a real trap here, worth naming explicitly:** do NOT add a uniqueness constraint like "at most one CONFIRMED row per `(engagement_id, subject)`." That would break supersession outright — superseded rows must remain CONFIRMED forever (§17's own "old knowledge remains historically true"); only the *resolution rule's* recency ordering determines which one is "current," never a DB constraint. The only safe uniqueness guarantee is "at most one row is the resolution result," which is a query-time property, not a storage-time one.

## 9. Supersession / contradiction — one field, two meanings by row status

A single nullable self-referencing column, `relates_to_knowledge_id`, serves both:
- On a **CANDIDATE** row: "this challenges that existing CONFIRMED row" → an active, unresolved contradiction.
- On a **CONFIRMED** row: "this supersedes that formerly-CONFIRMED row" → history preserved, not rewritten.

Rejected a second dedicated `supersedes_knowledge_id` field: the complexity test (§45) shows the v0 loop (TEST 1–5) is fully satisfied by one field: the CANDIDATE-with-reference *is* the contradiction record; once confirmed, the same reference *becomes* the supersession record. No `UPDATE` ever touches a CONFIRMED row.

## 10. Minimal persistence design

**PERSISTENCE REQUIRED: YES.** Without it, "never ask twice" cannot hold structurally — this is the mission's own stated reason for existing (§0) and is not weakened by anything found in this analysis.

**Immutability:** rows are insert-only, mirroring `evidence_ledger_entries`' unconditional `BEFORE UPDATE` trigger (`evidence_ledger_immutability_guard`, v18) exactly — no partial precedent for "revise in place" exists anywhere in this repository, and inventing one here would be a new, unjustified pattern. Revision = new row + `relates_to_knowledge_id` (§9).

**Schema shape — three options evaluated:**
- **A. Fully generic** (free-text subject, JSONB value) — rejected: becomes an uncontrolled semantic dumping ground, the exact risk the mission brief names in §21.
- **B. Typed-but-constrained** (small curated `subject` enum, extended deliberately with each reviewed migration; plain-string `value`, not JSONB) — **chosen.** One table serves every future knowledge type without becoming a triple store; no `predicate` column — for v0's single subject (`expense_sign_convention`), `subject` already fully disambiguates what `value` means; a `predicate` field is deferred until a second subject actually needs one (complexity test again).
- **C. One dedicated table per knowledge type** (e.g. `expense_sign_conventions`) — rejected outright: mission brief §21 explicitly forbids a new table per concept.

## 11. Minimal data contract

| Field | Meaning | Why required now | Nullable | Immutable | Reads | Writes |
|---|---|---|---|---|---|---|
| `id` | PK | Identity | No | Yes | all | system |
| `company_id` | Tenant, direct CASCADE | **Not** mirrored from `engagements` (which omits it) — deliberately. `engagement_id` uses SET NULL (§ deletion semantics below), which would break the CASCADE chain a GDPR company erasure needs. A direct, hard `company_id` FK is the only way to guarantee full erasure regardless of what happens to `engagement_id`. Matches `decision_arcs`/`evidence_ledger_entries` precedent, not `engagements`' precedent. | No | Yes | all | system |
| `engagement_id` | Owner | §4 | Yes (`ON DELETE SET NULL`, matching `decision_arcs.engagement_id` precedent — knowledge outlives an orphaned Engagement reference the same way Evidence/DecisionArc already do) | Yes | all | system |
| `subject` | Constrained enum, "what this is about" | §5/§21 boundary | No | Yes | all | system |
| `value` | The assertion (plain string for v0) | §10 | No | Yes | all | system |
| `status` | CANDIDATE / CONFIRMED | §3 | No | Yes (new row on transition, never UPDATE) | all | system |
| `relates_to_knowledge_id` | Self-FK, §9 | Contradiction + supersession, one mechanism | Yes | Yes | all | system |
| `provenance` | HUMAN_CONFIRMATION / DETERMINISTIC_RULE (reserved) | §7 | No | Yes | all | system |
| `confirmed_by` | Actor identity | §7/§37 — not redundant with `provenance`: `provenance` names the *mechanism* (human vs. deterministic rule), `confirmed_by` names *who*, needed for forward-compatible authority/audit even though v0 has a single-user assumption today | Yes | Yes | all | system |
| `confirmed_at` | Knowledge time | §6 | Yes (null while CANDIDATE) | Yes | all | system |
| `created_at` | Row insertion time, DB default | Repo-wide convention | No | Yes | all | system |

Fields explicitly removed after the "first-slice justification" test (§41 of the brief): `analysis_id`/`evidence_ids` (§33 — Knowledge must not copy Evidence; a future consumer can join through Evidence's own `analyse_id` if truly needed — not required for TEST 1–5), `valid_from_business_time`/`valid_to_business_time` (§6), `predicate` (§10).

**Writes are server-side only** — no client-facing table access, mirroring `save_evidence_capture`'s existing discipline. This is a Trust/privacy requirement (§27 of the brief), not an implementation detail.

## 12. Deterministic promotion — CONDITIONAL

Not a blanket yes or no. When a deterministic signal (arithmetic/subtotal check, account-code range — per the FRU foundation document) closes with **no residual ambiguity** (FRU matrix Case 2: signed Belgian COA, arithmetic resolves cleanly), direct promotion to CONFIRMED without asking is legitimate — a competent controller would not interrupt anyone for a fact the numbers already prove outright. When the signal is present but not fully closing (FRU matrix Case 1: Phidani itself — positive-display convention, arithmetic corroborates but doesn't independently prove sign direction with certainty), human confirmation remains required. The condition is completeness of proof, not convenience.

**LLM promotion: NO — absolute, no condition.**

## 13. First Phidani learning loop

1. FRU (simulated input for this contract — not built here) proposes CANDIDATE: `subject=expense_sign_convention, value=ABSOLUTE_POSITIVE`.
2. RECALL: no CONFIRMED row exists for `(engagement_id, expense_sign_convention)` → resolution returns nothing.
3. Epistemic Dialogue raises one ClarificationNeed (owned by Epistemic Dialogue, not this contract — §25 of the brief; Knowledge Model only needs to answer RECALL, it does not own the question object).
4. Human confirms → CANDIDATE promoted to **new CONFIRMED row**, `provenance=HUMAN_CONFIRMATION`, `confirmed_at` set.
5. Second equivalent upload: RECALL finds the CONFIRMED row → no clarification raised. **This is the enforceable core of "never ask twice"** — RECALL is a mandatory, structural pre-condition of ASK, not a prompt instruction.
6. Contradictory fixture (signed values appear): FRU proposes a new CANDIDATE with `relates_to_knowledge_id` pointing at the existing CONFIRMED row → resolution now returns *ambiguous/pending*, not the stale CONFIRMED value. Epistemic Dialogue raises a targeted change question. Human confirms → the new row is promoted to CONFIRMED (`relates_to_knowledge_id` now reads as supersession); the old CONFIRMED row is untouched, still queryable, still historically true for its own `confirmed_at` window.

## 14. Never-ask-twice invariant

Structural, not aspirational: ASK cannot legally fire without a prior RECALL call against this contract's resolution rule (§8). The v0 test contract's TEST 3 is the direct proof of this — see Test Contract below.

## 15. Failure semantics (mission §44, condensed to what changes v0's design)

- Knowledge applied too broadly → guarded by Engagement-only scope (§5) plus the explicit non-dead-end `scope_key`.
- Same question repeated → guarded structurally by §14.
- Stale knowledge applied forever → guarded by §9/§16's contradiction mechanism; **named limitation**, not solved: a detector that misses a contradiction (signal doesn't trip) leaves stale knowledge silently applied — same class of limitation already named in the Epistemic Dialogue foundation document.
- LLM silently promotes → structurally impossible, `provenance` enum has no LLM-capable value (§12).
- Human answer overwrites history → impossible by construction, rows are insert-only (§10).
- Two conflicting CONFIRMED rows at the same scope → cannot occur in v0: promotion always inserts a fresh row referencing the one it replaces (§9); the resolution rule (§8) only ever surfaces the newest. Multi-scope conflict (mission §36) is out of scope for v0 (§8).
- Missing/unknown reporting context → non-issue, v0 has no such object (§5).
- Analysis deleted → non-issue by design: no `analysis_id` FK exists on this table (§11).
- Entity/Engagement deleted → row survives (`engagement_id` SET NULL), same precedent as Evidence/DecisionArc.
- Company/GDPR deleted → row is purged (direct `company_id` CASCADE — §11, the one deliberate departure from the "mirror `engagements`" instinct).
- Second Engagement, different sheet convention → correctly produces two independent rows, no cross-contamination (Engagement-scoped by construction).
- Temporary exception mistaken for permanent rule → **named, not solved**: v0 has no "this confirmation is explicitly temporary" flag; a human answering "yes, but only this once" would still be recorded as an ordinary CONFIRMED row. Deferred to a future increment, flagged honestly rather than silently ignored.

## 16. Contradiction — mechanics recap

Created by: a new observation's CANDIDATE carrying `relates_to_knowledge_id` pointing at an existing CONFIRMED row with a *different* `value` for the same `(engagement_id, subject)`. References: the conflicting CONFIRMED row plus the new observation that triggered it. Before human resolution: the old CONFIRMED row remains queryable and answers RECALL as "ambiguous/pending" (§8) — never silently trusted, never silently discarded.

## 17. Explicit OUT (v0)

Multi-scope hierarchy beyond Engagement; `ReportingContext`/template discriminator as a first-class object; `predicate` field; business-time retroactive validity; deterministic promotion for anything short of complete proof; any LLM call; any client-writable path; repeated-observation-without-human promotion (BusinessHistory's INV-HISTORY-1 threshold is explicitly **not** reused here — the mission brief itself warns against leaking one domain's unvalidated heuristic into another; v0's loop does not need this promotion path at all); Familiarization bulk-ingestion optimization; linkage to Evidence/Analysis rows; role-based write authority beyond "server-side only."

**Named, deferred concern (AI-reliability-persona review):** two concurrent uploads producing contradicting CANDIDATEs against the same CONFIRMED row at nearly the same time is not addressed by this contract — v0 assumes sequential, single-session confirmation. Concurrency handling is deferred, not silently assumed away.

## 18. Open blockers

- FRU's real detector does not exist yet (by design — this contract accepts a *properly structured* candidate from any future FRU provider; it is not blocked on FRU's implementation, per mission brief §24).
- Epistemic Dialogue's `ClarificationNeed` object is not designed here — owned by that companion mission, not this one (§25 of the brief).
- Trust Gateway remains unimplemented — irrelevant to this specific contract since v0 has zero LLM involvement, but blocks any *future* increment that adds LLM-assisted hypothesis generation upstream of this table.

## 19. Test contract

- **TEST 1** — no CONFIRMED row exists → RECALL returns nothing → clarification permitted.
- **TEST 2** — human confirms → CONFIRMED row created, `confirmed_at`/`confirmed_by`/`provenance` set.
- **TEST 3** — same `(engagement_id, subject)` queried again → RECALL resolves the CONFIRMED row → clarification forbidden. *(Direct proof of §14.)*
- **TEST 4** — contradictory CANDIDATE with `relates_to_knowledge_id` inserted → RECALL returns ambiguous/pending, not the stale value → change-clarification permitted.
- **TEST 5** — human confirms the change → new CONFIRMED row exists; original CONFIRMED row is unmodified and still independently queryable (by `id`, not by RECALL) → history preserved, not rewritten.
- **Immutability** — any attempted `UPDATE` on an existing row is rejected (mirrors the Evidence Ledger trigger test pattern exactly).
- **Tenant isolation** — a row created under one `company_id`/`engagement_id` is never returned by a RECALL scoped to another.
- **No-LLM** — AST-based import check (not substring — the lesson already applied twice in this repository) proving zero LLM-service import in whatever module implements resolution/promotion.

---

## GO / NO-GO

**GO WITH RESERVATIONS.** The contract is minimal, tested against real precedent (Evidence Ledger's immutability, `engagements`'/`decision_arcs`' deletion semantics), and passes its own complexity test — every field traces to a specific test in §19; nothing was included by convenience. The reservation: this is architecture only. The two real blockers before code — FRU's actual detector and Epistemic Dialogue's `ClarificationNeed` design — belong to their own missions, not this one, and this contract's persistence layer should not be built in isolation from at least a stub of both, or v0 risks becoming exactly the kind of dormant, unconsumed table this engagement has repeatedly named and avoided (`financial_truth.py`'s own history is the standing warning).
