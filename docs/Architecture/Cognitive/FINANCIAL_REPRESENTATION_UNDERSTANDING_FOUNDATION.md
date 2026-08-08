# FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md

**Status:** PROPOSED — architectural discovery, read-only mission, not yet approved, not yet implemented.
**Branch:** `architecture/fru-epistemic-dialogue-2026-08-08` (not merged).
**Position in the documentary hierarchy:** below the Constitution, at the same level as ADR-003 v3 and the FTE Minimal Implementation Contract — a foundation document for a capability inside the existing Cognitive Architecture, not a new document above it.
**Governing test throughout:** `PEPPERYN_PROFESSION_MODEL.md` Ch.7, the law of design — *"Une capacité a sa place dans Pepperyn si elle reproduit fidèlement, ou amplifie... la partie compréhensive, mémorielle, comparative ou préparatoire d'une responsabilité réelle d'un excellent CFO — jamais la partie où ce CFO engage son jugement, sa signature ou la parole de l'organisation face à un tiers."*

---

## 1. Professional responsibility

**Financial Representation Understanding (FRU):** understand how a specific organisation expresses financial reality — its sign convention, its terminology, its structural grouping, its reporting grammar — well enough to translate that organisation's SOURCE REPRESENTATION into Pepperyn's CANONICAL FINANCIAL MEANING, without ever requiring the organisation to adopt Pepperyn's representation model, and without ever overwriting or discarding what the organisation actually provided.

This is the professional act a senior freelance controller performs, unpaid attention, in the first hour inside an unfamiliar company's files: reading labels, account numbers when present, formulas, subtotals, row hierarchy, and forming a working model of "how does this company say things" before trusting any number's economic meaning.

## 2. Problem boundary — what FRU is and is not

FRU answers exactly one question: **"What does this number mean economically?"** — nothing else.

It is explicitly **not**:
- Temporal understanding ("when does this belong?") — that is FTE's declared responsibility (`FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md`), untouched here. Mission 6 (`2019-13`/budget/actual classification) already tests that FRU and FTE stay orthogonal — see §9.
- Provenance / epistemic status ("how do we know?") — that is Evidence's declared responsibility (Evidence Ledger, `evidence_capture.py`).
- A universal chart-of-accounts translator, or "the software that understands Belgian PCMN." Belgian codes are one strong *signal* available for Phidani; they are not the foundation. A company with no account numbers at all (management P&L, English labels, internal terminology) must be equally well served (§8, cases 3–5).
- A source-normalization engine. FRU never rewrites the source. §4 makes this a hard boundary.
- Financial judgment. Deciding that a recharge *should* be treated as opex vs. capex for a specific decision is CFO judgment (Profession Model Ch.7, forbidden). FRU only establishes what a number *represents*; a human or a downstream reasoning capability decides what to *do* about it.

## 3. Observation vs. Inference vs. Knowledge

Pepperyn already has two epistemic-status vocabularies in canon, applied at different layers, that this document reconciles rather than replaces (see also `docs/Architecture/Cognitive/COGNITIVE_CONTRACTS_PROPOSAL.md` and `COGNITIVE_CAPABILITY_MAP.md`):

| Layer | Existing vocabulary | Source |
|---|---|---|
| Single assertion (per-fact) | `FACT` / `STRONG_INFERENCE` / `HYPOTHESIS` / `UNKNOWN` | `ConfidenceContract`, `COGNITIVE_CONTRACTS_PROPOSAL.md` |
| Organisational knowledge (accumulated, reusable) | Fact / Confirmed Context / Candidate Context / Unknown / Contradiction | `KnowledgeModel`, `COGNITIVE_CAPABILITY_MAP.md` |

These were never explicitly mapped onto each other before this mission — a gap the research for this document surfaced directly. The mapping:

- **OBSERVATION** — a `FACT`-confidence assertion about raw source data only. "Cell D18 contains 184,000." "The row label is 'Personnel'." Always traceable to a source cell, never an interpretation. This is Evidence's territory, not FRU's — FRU consumes observations, it does not produce them.
- **INFERENCE** — a `STRONG_INFERENCE` or `HYPOTHESIS`-confidence interpretation of one or more observations. "This row appears to represent payroll expense." Produced by a deterministic rule (arithmetic/structural, §6) or by an LLM hypothesis (§7). An inference is never, by itself, organisational knowledge — it is a **Candidate Context** at most.
- **KNOWLEDGE** — a `KnowledgeModel` entry that has reached **Confirmed Context** status: through a deterministic proof strong enough to stand alone (rare), through human confirmation (Epistemic Dialogue's main output, see the companion document), or through repeated consistent observation (borrowing `BusinessHistory`'s own discipline, `ADR-003_Financial_Time_Engine_v3_PROPOSED.md` INV-HISTORY-1: never promote below a minimum number of corroborating occurrences).

A **Contradiction** is not a fifth epistemic tier — it is an event: a new observation conflicts with an existing Confirmed Context entry. It triggers Contradiction Dialogue (companion document §on contradiction) rather than silently overwriting or silently ignoring the prior knowledge.

This gives Pepperyn the explainability the mission demands: for any claim, it can always answer *why* — source-proven observation, deterministic rule, LLM hypothesis (never alone sufficient), human confirmation, or historical record — instead of these collapsing into an undifferentiated "the system said so."

## 4. Source representation vs. economic meaning

Two objects that must never merge into one:

- **SOURCE REPRESENTATION** — exactly what the organisation provided. `Payroll = +100`, in the file, at the position, with the label, the organisation chose. Immutable, never corrected, never "fixed" to match a canonical sign convention. This is what Evidence already captures and what the Golden Case discipline already protects (`GOLDEN_CASE_001_PHIDANI.md`).
- **CANONICAL FINANCIAL MEANING** — Pepperyn's own interpretation layer: economic nature = payroll expense; economic effect in a P&L rollup = `-100`. This is FRU's output, applied at read/reasoning time, never applied by mutating the source.

Concretely: FRU never asks "should this cell be rewritten as -100?" It asks "when Pepperyn reasons about this organisation's P&L, what sign does this row's economic effect carry?" — and answers it as a **projection**, the same discipline FTE already uses for `PeriodObservation` (`FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md` §10: projection only, never a persisted first-class object duplicating a source fact). The persisted fact is the interpretation *rule* ("this reporting context displays expenses as positive absolute values"), not a rewritten value.

## 5. Deterministic / AI / Human roles

Applying `COGNITIVE_CAPABILITY_MAP.md`'s existing deterministic/probabilistic boundary discipline (Mission 3 of that document) to FRU specifically:

| Signal | Role | Why |
|---|---|---|
| Declared subtotal vs. sum of its detail rows | **Deterministic** | Pure arithmetic — if `Revenue − Payroll − OtherCosts = declared Result`, that's proof, not inference, of how Payroll's sign behaves economically. Confirmed available in Phidani's real workbook: row totals are live formulas (`=BM4+BM5`), not static values — formula structure is a genuine, underused deterministic signal (§8, cases 7–8). |
| Known chart-of-accounts range (e.g. Belgian PCMN 60–66 = charges, 70/74–76 = produits) | **Deterministic, but scoped** | Strong when the convention is recognized and codes are present. Must never become the universal foundation (§2) — it is one signal among several, absent entirely for companies with no account numbers. |
| Repeated consistent observation across periods | **Deterministic (statistical)**, mirrors `BusinessHistory` | Never LLM. INV-HISTORY-1's discipline (never promote below a minimum occurrence count) applies equally here. |
| Label semantics ("Management allocation" probably means...) | **Interpretive / LLM**, hypothesis only | Legitimate for hypothesis generation, ambiguity explanation, question phrasing. Illegitimate as the final promotion decision — already the explicit rule in `COGNITIVE_CAPABILITY_MAP.md` Mission 3 ("promotion Candidate→Confirmed Context = LLM interdit for the final decision"). This document does not weaken that rule; it inherits it. |
| Business context absent from the numbers (why a recharge exists, what a line economically *is* when genuinely ambiguous) | **Human authority** | Constitution Article II: *"une explication commerciale, humaine ou opérationnelle à un écart financier ne se déduit jamais des chiffres seuls."* Applies identically to representation questions — some things are not inferable from data by construction, not merely by current model weakness. |

Confidence, per §27 of the mission brief: **do not invent a new numeric or qualitative scale.** Reuse the existing `FACT / STRONG_INFERENCE / HYPOTHESIS / UNKNOWN` taxonomy rather than adding a competing one — a fabricated `0.873` is not more rigorous than `STRONG_INFERENCE`, it is less honest about what it is.

## 6. Structural evidence — the underused signal

§25 of the mission brief asked whether formulas/subtotals/arithmetic relationships can provide deterministic semantic evidence. Direct answer: **yes, and this repository's own real Golden Case already proves it works mechanically** — the Walking Skeleton mission (`FRU sibling discovery`, see §9) confirmed Phidani's real workbook carries live formula references (`row 6 = "=BM4+BM5"`), not static computed values. This means:

- A subtotal's formula range can, in principle, deterministically prove which detail rows compose it — stronger evidence than any label-based LLM hypothesis, because it requires no semantic guessing at all.
- This is architecturally attractive specifically because it keeps the **Trust Boundary** simple: arithmetic relationships can be evaluated entirely on already-parsed structural data, with zero need to send content to an LLM (§10).
- It is not free: it requires the file parser to expose formula/reference structure (not just evaluated values) to whatever component performs FRU's structural checks — today's `file_parser.py`/`financial_normalizer.py` path was not verified in this mission to expose this (explicitly out of scope: this is READ-ONLY architecture discovery, not implementation verification). **Named as a blocker for the first vertical slice**, see the companion slice document.

## 7. LLM role — explicit boundary

Legitimate: semantic hypothesis generation over labels/terminology Pepperyn cannot resolve deterministically; explaining *why* an ambiguity exists; formulating the clarification question itself (never inventing the underlying uncertainty — the uncertainty must already exist, per Epistemic Dialogue's non-negotiable principle 1, companion document).

Illegitimate: "the LLM said this is payroll, therefore it is canonical payroll" (mission's own explicit example, §26). An LLM hypothesis is, at best, a `HYPOTHESIS`-confidence Candidate Context — it can motivate a clarification question, it cannot itself promote to Confirmed Context. This inherits, does not invent, the existing rule in `COGNITIVE_CAPABILITY_MAP.md`.

## 8. Adversarial representation matrix (condensed)

Full 15-case reasoning was performed per Mission 33; the rows below are the ones that changed the architecture, not an exhaustive transcript:

| Case | Alone? | Inference? | Ask? | Remember at | Invalidated by |
|---|---|---|---|---|---|
| 1. Belgian COA, positive expenses (Phidani) | Account-range signal | Arithmetic subtotal check corroborates | Confirmation-style, if arithmetic doesn't cleanly close | This reporting template, within Entity | Later file shows negative values for previously positive-only accounts |
| 2. Belgian COA, signed expenses | Yes — arithmetic resolves cleanly | — | No | Same | Same |
| 3. Management P&L, no codes | Weak (labels only) | Label + arithmetic if subtotals exist | Yes, if arithmetic absent and labels ambiguous — no deterministic backup exists | Entity + reporting format | Format change |
| 5. Idiosyncratic internal terminology | No | LLM hypothesis + arithmetic corroboration | Yes — canonical target for a real clarification | Specific label → economic nature, narrow scope | New label appears with no precedent |
| 7/8. Explicit subtotals / live formulas | **Yes — strongest deterministic signal available** | — | No (unless subtotal inconsistent) | — | Formula structure changes |
| 9. Genuinely ambiguous sign, no arithmetic backup | No | Weak | **Yes — canonical "must ask" case** | Narrow | — |
| 10. Convention changes over time | — | — | **Contradiction Dialogue, not silent overwrite, not blind persistence** | Old scope/time preserved as historically true | — |
| 11. Different conventions across two sheets in one file | — | — | Scope must be finer than "workbook" | Sheet / reporting-block level | — |
| 12. Different conventions across two Entities | — | — | Never leaks | Entity-scoped minimum, matches `KnowledgeModel` ownership | — |
| 13. Expenses genuinely zero vs. formula-summed blanks | **Direct convergence with the Financial Time Engine Walking Skeleton's own central finding** (`PHIDANI_WALKING_SKELETON` final report, 2026-08-08): a column/row that *looks* populated (a formula evaluates to `0`) can be an absence rendered as a zero, exactly what Constitution Article III forbids. FRU and the Walking Skeleton's empty-column gap are two independent symptoms of the same underlying question — "does this cell represent a genuine observation?" — approached from two different axes (representation vs. temporal). Neither is FRU's mission to fix; both should inform the same future "data presence" primitive if one is ever built. |
| 15. Ambiguous internal recharge | No | Weak, multiple plausible natures | **Yes — canonical example already in the mission brief** | Narrow, line-specific | New evidence about the recharge's nature |

Case 6 (mixed actual/budget/forecast) was used specifically to confirm FRU and FTE stay orthogonal: FRU never touches *when* a column belongs, only *what* a row means economically — the two axes compose independently, exactly as §6 of the mission brief anticipated, and neither this document nor its companion adds a joint dimension.

## 9. Relationship to current canonical foundations

| Foundation | Relationship |
|---|---|
| **Evidence Ledger** | PROVIDER of observations FRU consumes (facts, labels, values). FRU never re-implements Evidence capture. UNCHANGED. |
| **FTE v0** | UNCHANGED, orthogonal axis (§2, §8 case 6). No joint object proposed. |
| **Engagement** | POTENTIAL OWNER of the resulting knowledge (see §Knowledge scope in companion documents) — matches `KnowledgeModel`'s existing declared ownership in `COGNITIVE_CAPABILITY_MAP.md` ("faculté 2, propriété d'Engagement"). |
| **DecisionArc** | OUT OF SCOPE for FRU directly. Epistemic Dialogue's other dialogue types (Decision, Execution) touch DecisionArc; Understanding/Contradiction Dialogue (FRU's concern) touch `KnowledgeModel` only. |
| **Enterprise Familiarization** | CONSUMER — Familiarization (`PEPPERYN_PROFESSION_MODEL.md` Ch.5, still "conçu, non implémenté") explicitly ingests historical data to "remplir accéléré le Knowledge Model" — FRU is the semantic content that fills part of that model faster, not a separate mechanism. See the companion slice document for why they remain distinct missions. |
| **Knowledge Model discussions** | **This is the same object.** FRU is not a new bounded context — it is the operational elaboration of content `KnowledgeModel` (`COGNITIVE_CAPABILITY_MAP.md`, faculté 2, "Comprendre l'organisation") already claims to hold but had not yet specified: sign conventions, terminology, structural grouping. Proposing FRU as a competing store would violate the One New Truth Rule directly. |
| **BusinessHistory** | SIBLING, not the same thing. `ADR-003_Financial_Time_Engine_v3_PROPOSED.md` §2.2 already fully specifies `BusinessHistory` as "quel comportement s'est répété" (temporal/statistical pattern, faculté 3 "Se souvenir"). FRU is "que signifie ce nombre" (representation/semantic, faculté 2 "Comprendre l'organisation"). Same owner (Engagement), different registry, never merged. |
| **Cognitive Architecture (Case Framer / target pipeline)** | CONSUMER — FRU's confirmed knowledge should populate the `CognitiveCaseFile`'s organisation section (`COGNITIVE_CONTRACTS_PROPOSAL.md`), assembled by the future Case Framer, exactly as the existing selection rule already demands ("chaque section est peuplée par pertinence... jamais par défaut 'tout ce qui existe'"). FRU does not become a new pipeline stage. |
| **Trust / anonymization** | POTENTIAL CONFLICT if implemented carelessly — see §10. |
| **Review Briefing / Conversation Engine** | OUT OF SCOPE for this document; the surface question belongs to the Epistemic Dialogue companion document. `conversation_engine.py` is flagged there as currently unsuitable as a dialogue surface (confirmed active Trust Boundary bypass). |

## 10. Trust Boundary implication

FRU's deterministic signals (§6: arithmetic/formula/subtotal checks, account-code-range matching) require **no LLM call at all** and can be evaluated entirely on already-parsed structural data — this keeps a large, useful portion of FRU inside the Trust Boundary with zero new exposure.

FRU's *interpretive* signals (§7: label semantic hypothesis) require sending label text — and by extension, some surrounding structural context — to an LLM. Per `TRUST_BOUNDARY_CLOSURE_PLAN.md`, this must go through the (currently unimplemented) Trust Gateway; no component may call an LLM provider directly. **This is a real, named blocker**, not a implementation detail to solve later without consequence: any FRU capability that reaches for LLM label interpretation is blocked until the Trust Gateway exists. The first vertical slice (companion document) is scoped to avoid this blocker entirely by using deterministic signals only.

## 11. Failure modes this document explicitly guards against

- **Belgian-PCMN-only Pepperyn** — §2, §5: account-code ranges are one signal, explicitly not the foundation.
- **Source-rewriting Pepperyn** — §4: source representation is never mutated.
- **Fake-precision Pepperyn** — §5: reuse the existing qualitative confidence taxonomy, reject invented numeric confidence.
- **Second-truth-system Pepperyn** — §9: FRU is not a new store; it is `KnowledgeModel` content.
- **LLM-as-canonical-truth Pepperyn** — §7: inherits, does not weaken, the existing "LLM never decides the final promotion" rule.

---
*Companion documents: `EPISTEMIC_DIALOGUE_FOUNDATION.md`, `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md`.*
