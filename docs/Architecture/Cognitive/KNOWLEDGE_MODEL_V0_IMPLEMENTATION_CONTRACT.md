# KNOWLEDGE MODEL v0 — MINIMAL IMPLEMENTATION CONTRACT

**Status:** PROPOSED, read-only architecture mission — not approved, not implemented.
**Branch:** `architecture/knowledge-model-v0-2026-08-08` (not merged).
**Revision history:** v1 (commit `d522476`) proposed Engagement ownership, a persisted CANDIDATE status, an opaque `scope_key`, and dual timestamps. **v2 (this revision) — Final Contract Adversarial Arbitration** — corrects all four after direct challenge: true ownership is Entity, not Engagement; CANDIDATE is never persisted (KnowledgeModel only ever stores confirmed facts); `scope_key` is removed in favor of the explicit `entity_id` FK; `confirmed_at`/`created_at` collapse into one field. These are corrections, not a reopening of the overall direction, which the arbitration mission explicitly reaffirmed as accepted.
**Relationship to prior work:** operationalizes `KnowledgeModel` as already named (not invented) in `docs/Architecture/Cognitive/COGNITIVE_CAPABILITY_MAP.md` (faculté 2, "Comprendre l'organisation" — states *Fact/Confirmed Context/Candidate Context/Unknown/Contradiction*, each carrying origin/date/confidence/scope), and supplies the missing mechanism that document already flagged without designing: *"Promotion Candidate Context → Confirmed Context... LLM interdit pour la décision finale — validation humaine ou règle déterministe explicite requise."*

---

## 1. Professional responsibility

Learn a durable, reusable interpretive convention about a specific organisation; recall it before ever asking again; detect when new evidence no longer fits it; and revise without erasing what was true before.

## 2. Boundary vs. Evidence / DecisionArc / chat

- **Not Evidence.** Evidence = what was observed. Knowledge = how to interpret it. Knowledge may be *supported by* Evidence; never a second Evidence Ledger.
- **Not chat history.** The domain event `HumanConfirmedInterpretation` — not the sentence that produced it — is what may justify a Knowledge row. Raw conversation is never persisted here.
- **Not LLM memory.** An LLM hypothesis never reaches this table at all in v0 (§3) — it is ephemeral input to Epistemic Dialogue, not a KnowledgeModel object.
- **Not DecisionArc.** DecisionArc tracks commitments. Knowledge tracks interpretive convention.

## 3. Epistemic lifecycle — corrected: KnowledgeModel v0 has no persisted CANDIDATE status

**Arbitration finding (Q3):** the v1 contract's CANDIDATE status created an unresolvable tension with immutability (confirming K1 would require either an illegal UPDATE or an awkward two-row dance for every single confirmation). Re-examining the professional question directly: does KnowledgeModel itself need to *store* an unconfirmed hypothesis, or can the hypothesis remain entirely inside Epistemic Dialogue's own ephemeral `ClarificationNeed` (already declared, in the v1 contract's own §2 boundary and §25 of the FRU/Epistemic Dialogue mission, to belong to Epistemic Dialogue, not here) until the moment it is actually confirmed?

**Resolution: it can, and should.** KnowledgeModel v0 stores exactly one row-bearing state: **CONFIRMED.** A candidate interpretation is never written to this table. It is proposed by FRU, held and reasoned about by Epistemic Dialogue, and only reaches KnowledgeModel at the instant a human (or, conditionally, a deterministic rule — §12) actually confirms it — at which point exactly one row is inserted, fully formed, already CONFIRMED. *Unknown* is still never persisted (absence of a row means Unknown, Article III). Contradiction is still not a status (§16) — it is a live comparison Epistemic Dialogue performs between new evidence and RECALL's result; it never requires KnowledgeModel to hold an intermediate "disputed" row.

This closes the immutability tension directly: there is no CANDIDATE→CONFIRMED transition inside this table to represent, because nothing is ever written before confirmation.

## 4. Ownership — corrected: Entity, not Engagement

**Arbitration finding (Q1):** the v1 contract said "owner = Engagement" while proposing `engagement_id ON DELETE SET NULL` — an owner whose own deletion doesn't delete what it owns is not actually the owner. Tested against the professional scenario the arbitration posed directly: Engagement A learns "this company displays expenses positively"; Engagement A ends; Engagement B begins with the same company. A competent controller returning to a client after a gap does not relearn how that client's own reports are built — that knowledge belongs to the *organisation itself*, not to the professional mandate that happened to be active when it was learned.

**Resolution:**
- **TRUE OWNER = Entity.** `entity_id`, `NOT NULL`, `ON DELETE CASCADE` — mirrors `engagements.entity_id`'s own precedent exactly (a true owning FK cascades; a transitional attachment doesn't). Verified: `entities.company_id ON DELETE CASCADE NOT NULL` (`v6_workspaces_entities.sql:75`) — so Entity deletion already cascades from Company deletion, and Knowledge cascades from Entity deletion, giving a full, transitive GDPR-safe chain with **no separate `company_id` column needed** (same reasoning `engagements` itself already relies on for omitting it).
- **ACQUISITION CONTEXT = Engagement.** `engagement_id`, nullable, `ON DELETE SET NULL` — records *which* professional mandate was active when the knowledge was learned, for audit/display only. Its deletion must never delete the knowledge itself.
- **APPLICABILITY SCOPE v0 = Entity** (§5) — for v0, scope and ownership now coincide, which is what makes `scope_key` (v1's abstraction) unnecessary (§5).

## 5. Scope — corrected: SCOPE_KEY = REMOVE

**Arbitration finding (Q2):** v1 described scope as "Engagement-only" in prose but as an "opaque composable `scope_key`" conceptually, while the actual field list never included `scope_key` at all — the contract told two stories. Re-derived from §4's ownership correction: since the true applicability scope for v0 is now Entity (the same object that owns the row), **no separate scope abstraction is needed at all** — `entity_id` *is* the scope. Complexity test: does the four-upload loop need anything beyond the explicit `entity_id` column to resolve correctly? No. **SCOPE_KEY: REMOVE.** A future template/sheet-level discriminator (FRU matrix case 11) remains a legitimate future need, but is deferred to when a real multi-template Golden Case exists — Phidani is single-sheet and does not require it now, and adding a second discriminating column later (e.g. a nullable `template_fingerprint`) is additive, not a schema rewrite, so nothing is foreclosed.

## 6. Temporal validity — corrected: one timestamp, not two

**Arbitration finding (Q9, complexity attack):** with CANDIDATE removed (§3), row creation and confirmation are now the same event — `created_at` and `confirmed_at` would always be identical in v0, making one of them dead weight. **Resolution:** a single field, `confirmed_at`, explicit (not a bare framework default — same discipline as FTE's `observed_period_end`), doubles as both "row exists" and "knowledge time." If a future increment reintroduces async candidate persistence (e.g. a `ClarificationNeed` that outlives a session before resolution), a separate `created_at` should be reintroduced at that point — a clean, additive change, not a redesign.

Business-time applicability (`valid_from_business_time`/`valid_to_business_time`) remains **deferred**, unchanged from v1 — not required by the test contract, additive later.

## 7. Provenance / authority — corrected: DETERMINISTIC_RULE removed from v0's enum

**Arbitration finding (Q9):** the four-upload test loop (§13) never exercises deterministic-only promotion — every confirmation in the required test contract is human-mediated. Per the complexity test, an enum value the loop never uses is over-provisioning, not future-proofing (adding one enum literal later, when deterministic promotion is actually built, is a trivial migration, not a dead end). **Resolution: `provenance` is fixed to `HUMAN_CONFIRMATION` for v0** (technically no longer needs to be an enum with unused members — kept as a single-value controlled field rather than a boolean, so the future addition is a value, not a type change). `confirmed_by` (actor identity) is now `NOT NULL` — every row is a confirmed fact by construction (§3), so an actor always exists. Not redundant with `provenance`: `provenance` names the mechanism (currently always human), `confirmed_by` names who — a real, distinct need already validated in the original adversarial review and unchanged by this arbitration.

## 8. Resolution rule — corrected: chain-head, not "most recent"

**Arbitration finding (Q7):** "most recent CONFIRMED by `confirmed_at`" is fragile — a superseded row could reappear if a later row is ever deleted, filtered incorrectly, or inserted with clock-skewed timestamps. **Resolution:** given `(entity_id, subject)`, the applicable Knowledge is **the unique CONFIRMED row that no other CONFIRMED row for the same `(entity_id, subject)` references via `relates_to_knowledge_id`** — the head of the supersession chain, a structural property, not a timestamp comparison. If no CONFIRMED row exists at all → Unknown, clarification permitted. `confirmed_at` remains useful for display/audit ordering but is no longer the resolution mechanism.

No unique DB constraint on `(entity_id, subject, status=CONFIRMED)` — that would break supersession outright, since superseded rows correctly remain CONFIRMED forever. Uniqueness is a query-time property (the chain has one head), never a storage-time one.

Multi-scope conflict resolution (mission §36 of the original brief) remains structurally inapplicable — v0 has one scope level.

## 9. Contradiction / supersession — one field, now unambiguous

**Arbitration finding (Q3):** with CANDIDATE removed, `relates_to_knowledge_id` no longer needs a status-dependent dual meaning. On the only status that exists, CONFIRMED, it means exactly one thing: **this row supersedes that row.** Contradiction itself is not a KnowledgeModel-visible write at all — it is Epistemic Dialogue detecting, at RECALL time, that newly observed evidence disagrees with the resolved CONFIRMED row, and raising a targeted question *before* anything is written here. Nothing is persisted for an unresolved contradiction; if the human confirms the change, exactly one new CONFIRMED row is inserted, with `relates_to_knowledge_id` pointing at the row it supersedes.

## 10. Minimal persistence design

**PERSISTENCE REQUIRED: YES** — unchanged; without it, never-ask-twice cannot hold.

**Immutability:** insert-only, mirroring `evidence_ledger_entries`' unconditional `BEFORE UPDATE` trigger (v18) exactly. With CANDIDATE removed, this is now trivially satisfiable — there is no in-table transition to forbid, only ordinary inserts.

**Schema shape:** unchanged from v1's conclusion — one typed-but-constrained table (curated `subject` enum, plain-string `value`, no JSONB, no `predicate`), rejecting both a fully generic triple-store and a table-per-knowledge-type.

**Semantic safety (Q5, new):** `value` is not an unconstrained string in practice. Each `subject` maps to its own small, closed set of legal `value`s via an application-level registry (v0: `EXPENSE_SIGN_CONVENTION → {ABSOLUTE_POSITIVE, SIGNED_NATURAL}`, exactly two legal values), mirrored by a DB `CHECK` constraint enumerating the current legal `(subject, value)` pairs. This prevents synonym drift (`"positive"` vs `"ABSOLUTE_POSITIVE"` never both existing as competing truths) without building a generic ontology — extending to a second subject means adding one registry entry and one `CHECK` clause, never a schema change.

## 11. Minimal data contract

| Field | Meaning | Nullable | Writes |
|---|---|---|---|
| `id` | PK | No | system |
| `entity_id` | **True owner** (§4), `ON DELETE CASCADE` | No | system |
| `engagement_id` | Acquisition context only (§4), `ON DELETE SET NULL` | Yes | system |
| `subject` | Constrained enum, "what this is about" | No | system |
| `value` | The assertion, constrained per-subject (§10) | No | system |
| `relates_to_knowledge_id` | Self-FK — supersession only, unambiguous (§9) | Yes | system |
| `provenance` | Fixed `HUMAN_CONFIRMATION` for v0 (§7) | No | system |
| `confirmed_by` | Actor identity, now required (§7) | No | system |
| `confirmed_at` | Single explicit timestamp, doubles as knowledge time (§6) | No | system |

All reads/writes server-side only (unchanged from v1) — no client-facing table access.

**Removed since v1** (all failed the complexity test — §9 of the arbitration mission): `company_id` (transitively covered by `entity_id` CASCADE, §4), `scope_key` (§5), `status` (only CONFIRMED exists, §3), `created_at` (merged into `confirmed_at`, §6), `DETERMINISTIC_RULE` enum member (§7).

## 12. Deterministic promotion — unchanged: CONDITIONAL

When a deterministic signal closes with no residual ambiguity, direct promotion without asking is legitimate; when merely corroborating, human confirmation remains required. **LLM promotion: NO — absolute.** (v0's actual test loop, §13, only exercises the human path; deterministic promotion remains a named, allowed-but-unexercised capability, not a v0 deliverable.)

## 13. First Phidani learning loop (revised for the corrected model)

**Upload 1.** No prior Knowledge. FRU proposes (ephemeral, held by Epistemic Dialogue, never written here) `EXPENSE_SIGN_CONVENTION = ABSOLUTE_POSITIVE`. RECALL(entity=Phidani, subject=EXPENSE_SIGN_CONVENTION) → no CONFIRMED row → nothing. Epistemic Dialogue asks for confirmation. Human: yes. **STORE:** exactly one row —
`K1 = {id, entity_id=Phidani, engagement_id=A, subject=EXPENSE_SIGN_CONVENTION, value=ABSOLUTE_POSITIVE, relates_to_knowledge_id=NULL, provenance=HUMAN_CONFIRMATION, confirmed_by=user, confirmed_at=t1}`.

**Upload 2.** Same convention. RECALL → chain-head is K1 (no row references it) → returns `ABSOLUTE_POSITIVE`. New evidence agrees. **ASK does not occur.**

**Upload 3.** Contradictory signed-expense fixture. RECALL → still returns K1. New evidence's inferred value (`SIGNED_NATURAL`) disagrees with K1 → Epistemic Dialogue detects the contradiction as a live comparison — **nothing is written to KnowledgeModel at this point.** Targeted question raised: "Until now, this reporting presented expenses as positive values. In this file, several are negative. Has the convention changed?" Human: "Yes, since this file." **STORE:**
`K2 = {id, entity_id=Phidani, engagement_id=A, subject=EXPENSE_SIGN_CONVENTION, value=SIGNED_NATURAL, relates_to_knowledge_id=K1.id, provenance=HUMAN_CONFIRMATION, confirmed_by=user, confirmed_at=t3}`.
K1 is untouched, still independently queryable by `id`.

**Upload 4.** Signed convention continues. RECALL(Phidani, EXPENSE_SIGN_CONVENTION) → K2 is the chain-head (nothing references it; K1 is referenced by K2, so it is excluded) → returns `SIGNED_NATURAL`. K1 remains historically inspectable (direct lookup, or by following `relates_to_knowledge_id` backward from K2) but is never again returned by ordinary RECALL. **FOUR-UPLOAD LOOP: PASS.**

## 14. Never-ask-twice — corrected claim (Q4)

**Arbitration finding:** the v1 contract's "structurally enforceable" claim overreached. KnowledgeModel v0 can guarantee exactly one thing: **RECALL is deterministic** — given the same stored state, it always returns the same, correct, currently-applicable answer (or honestly nothing). It **cannot**, by itself, guarantee that Epistemic Dialogue actually *calls* RECALL before raising a question — that discipline lives entirely in Epistemic Dialogue's own code and belongs to its own test contract (e.g. a call-graph-level test asserting ASK never fires without a preceding RECALL in the same reasoning trace). **RECALL-BEFORE-ASK OWNER: Epistemic Dialogue, not KnowledgeModel.** This is a narrower, more honest claim than the original.

## 15. Provenance sufficiency (Q6)

`confirmed_by` + `confirmed_at` + `provenance` answers "why do we believe this" completely for v0's professional question (who, when, by what mechanism) without storing raw chat or linking to the originating analysis. Explicitly, no `analysis_id`/dialogue-event FK — Knowledge must survive deletion of any source analysis, and does, by never referencing one. Deeper "show me the exact conversation" traceability, if ever wanted, is Epistemic Dialogue's own future domain-event log to build — not this table's job.

## 16. Failure semantics (condensed, re-verified against the corrected model)

Knowledge applied too broadly → Entity-scoped by construction, `entity_id` not `engagement_id`, corrects a v1 gap where Engagement-scoping would have wrongly forgotten knowledge across Engagement boundaries. Same question repeated → guarded by RECALL determinism (§14), enforcement lives in Epistemic Dialogue. Stale knowledge applied forever → guarded by the contradiction comparison at RECALL time; **named limitation unchanged from v1**: a detector that never trips leaves stale knowledge silently applied. LLM silently promotes → structurally impossible, no LLM-capable provenance value exists. Human answer overwrites history → impossible, insert-only. Two conflicting CONFIRMED chain-heads → cannot occur: every new CONFIRMED insert for an existing `(entity_id, subject)` requires a `relates_to_knowledge_id` pointing at the prior head, by construction of the confirmation flow (§13) — there is exactly one head at all times. Entity deleted → Knowledge is correctly purged too now (§4 — a deliberate correction from v1, where knowledge would have wrongly survived an Entity that no longer exists; institutional knowledge about an organisation that has been fully removed has no remaining subject). Engagement deleted → Knowledge survives (`engagement_id` SET NULL), directly satisfying the arbitration's own professional scenario (Engagement B still benefits from what Engagement A learned). Company/GDPR deleted → purged transitively via `entity_id` CASCADE → `entities.company_id` CASCADE, verified in migration. Concurrent contradictory uploads → still deferred, unchanged from v1.

## 17. Explicit OUT (v0) — updated

Everything from v1's OUT list, plus (newly excluded by this arbitration): a persisted CANDIDATE status; a separate `scope_key` abstraction; a second timestamp column; an unused `DETERMINISTIC_RULE` enum member; a direct `company_id` column.

## 18. Open blockers — unchanged

FRU's real detector; Epistemic Dialogue's `ClarificationNeed` object and its own RECALL-before-ASK enforcement (now explicitly its responsibility, §14, not assumed here); Trust Gateway (irrelevant to v0's zero-LLM design, blocks future increments only).

## 19. Test contract — updated for the corrected model

- **TEST 1** — no CONFIRMED row for `(entity_id, subject)` → RECALL returns nothing → clarification permitted.
- **TEST 2** — human confirms → exactly one CONFIRMED row inserted directly (no prior row of any kind existed).
- **TEST 3** — same `(entity_id, subject)` recalled again → resolves to the same row → clarification forbidden.
- **TEST 4** — contradictory evidence compared against RECALL's result *outside* this table → disagreement detected → **no row written** → change-clarification permitted.
- **TEST 5** — human confirms the change → new CONFIRMED row inserted with `relates_to_knowledge_id` pointing at the prior head → prior row unmodified, independently queryable, no longer returned by RECALL.
- **Chain-head correctness** — with three or more chained rows, RECALL always returns the one row nothing else references, never influenced by `confirmed_at` ordering alone (proves §8's correction).
- **Cross-Engagement persistence** — knowledge confirmed under Engagement A is returned by RECALL under Engagement B for the same Entity (direct proof of §4's ownership correction).
- **Entity-deletion purge** — deleting the owning Entity removes its Knowledge rows (direct proof of §16's corrected deletion semantics).
- **Immutability** — any attempted `UPDATE` on an existing row is rejected.
- **Semantic safety** — an attempt to write a `value` not in the registered set for its `subject` is rejected at the service layer and by the DB `CHECK` constraint (§10).
- **No-LLM** — AST-based import check, zero LLM-service import in the resolution/promotion module.

---

## GO / NO-GO

**GO.** All five arbitration questions resolved with corrections, not workarounds; the ownership fix in particular (§4) was load-bearing — the v1 contract would have silently broken the exact professional scenario ("Engagement B should still benefit from what Engagement A learned") this whole mission exists to encode. The contract is smaller than v1 (five fields removed, none added), and every remaining field and rule traces to a specific test in §19. Same reservation as before, restated because it remains true: build this only alongside at least a stub of FRU's detector and Epistemic Dialogue's `ClarificationNeed`, never in isolation.
