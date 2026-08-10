# FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL.md

**Status:** PROPOSED — architecture / professional-domain discovery, read-only mission, not yet approved, not yet implemented.
**Branch:** `architecture/financial-file-understanding-profession-model-2026-08-10` (not merged).
**Position in the documentary hierarchy:** below the Constitution and the Profession Model, at the same level as `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md`, `EPISTEMIC_DIALOGUE_FOUNDATION.md` and `FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md`. This document does not replace any of them — it arbitrates the *set* of professional capabilities financial-file understanding decomposes into, of which FRU (one subject: sign convention) is the first, narrowest, already-implemented instance.
**Does not duplicate:** `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md` (FRU's own epistemic method — OBSERVATION/INFERENCE/KNOWLEDGE, the deterministic/LLM/human triad — is reused here, not restated); `COGNITIVE_CAPABILITY_MAP.md` (the 8-faculté DDD ownership table — this document extends it with the pre-analysis capabilities it does not yet name); `PEPPERYN_PROFESSION_MODEL.md` (the 12 CFO responsibilities and the law of design — this document operationalizes responsibility "Comprendre" for the specific case of an unfamiliar financial file).
**Governing test throughout:** `PEPPERYN_PROFESSION_MODEL.md` Ch.7 — *"Une capacité a sa place dans Pepperyn si elle reproduit fidèlement, ou amplifie... la partie compréhensive, mémorielle, comparative ou préparatoire d'une responsabilité réelle d'un excellent CFO — jamais la partie où ce CFO engage son jugement, sa signature ou la parole de l'organisation face à un tiers."*

**Correction (2026-08-10, "Observation Structure v0" domain-arbitration mission, narrow, no rewrite of substance elsewhere in this document):** §11's recommended next slice, as originally worded — *"Row/Column Observation Classification: LEAF vs AGGREGATE vs SECTION_HEADER"* — silently assumed two things the follow-up mission found unsupported by the real file: (1) that structural role and derivation (formula-derived vs. source value) are the same dimension, collapsible into one enum; and (2) that row and column axes belong in the same v0 slice. Real Phidani evidence disproves (1) directly — row 163 (`630 "D. Amortissements"`, formula `=C162`) plays the AGGREGATE structural role (lettered statutory caption, bold, correct hierarchy position) while its derivation is a trivial single-cell passthrough, not a genuine multi-row sum; conversely a hypothetical hardcoded manual total would show AGGREGATE-shaped position/caption evidence while its derivation reads as `SOURCE_VALUE` (no formula observed). The corrected model — **two independent dimensions, `structural_role` and `derivation_status`, never merged** — is the one carried into `OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md`, together with a fourth structural-role value (`KPI`, proven necessary by Phidani row 133, `"B1 Marge brute d'exploitation (EBITDA)"` — derived from two already-derived rows, arithmetically non-independent yet analytically the single most citable fact in the file) and a narrowed v0 scope (row axis only; column axis explicitly deferred, not abandoned). This paragraph corrects §11's wording; the rest of this document's conclusions (five-capability arbitration, #2/#3 relationship, dependency graph, prioritisation) are unaffected and stand as originally written.

---

## 0. Why this document exists

FTE established a deterministic answer to "when does this belong?". FRU + Epistemic Dialogue v0 established a working, executable, organisationally-learning answer to exactly one narrow instance of "what does this representation mean?" — expense sign convention, one subject, one Belgian-shaped file. Building that one instance surfaced, empirically and repeatedly (subtotal contamination, the 90% floating-point boundary, the concurrency-recovery ambiguity), a larger truth: a competent financial controller does not analyse a company's numbers before first understanding how that company represents them. Pepperyn must earn the same right. This document asks, before any further widening of FRU: what does "understanding a financial file" actually decompose into as a set of professional capabilities, and in what order do they become necessary?

## 1. Governing principle

**Pepperyn must not analyse financial meaning it has not first earned the right to understand.**

Operationalised as a sequence — not assumed to map 1:1 onto software components:

**OBSERVE → UNDERSTAND → RECALL → CLARIFY IF NECESSARY → THEN ANALYSE**

OBSERVE is Evidence's territory (already real). RECALL and CLARIFY IF NECESSARY are KnowledgeModel's and Epistemic Dialogue's territory (already real, proven on one subject). ANALYSE is existing agent/reasoning territory (already real, and explicitly out of scope for correction here). UNDERSTAND is the gap this document investigates: it is not one capability, it is a family, and this mission's job is to determine its members, not to build them.

## 2. Cognitive workflow of an excellent controller opening an unfamiliar file

Before mapping onto Pepperyn, the professional sequence itself, stage by stage (implicit question → evidence inspected → deterministic vs interpretive → what may stay uncertain vs blocks analysis → what triggers a question → what gets remembered → what would reopen the understanding):

1. **"What am I looking at?"** — one sheet or several; one statement or several stacked together (P&L, balance sheet, cash flow); a title/section row, or none. Evidence: sheet names, section-header rows (text-only rows with no code and no value), sheet count. Mostly deterministic (presence/absence of a title row is a fact); interpretive only when no title exists at all. Blocks nothing by itself — sets the frame for every later stage. Remembered at Entity scope (an organisation's export shape rarely changes month to month). Reopened if the sheet/section layout changes shape (new sheet appears, section title disappears).
2. **"Which rows are raw entries and which are computed rollups?"** — leaf vs aggregate vs derived. Evidence: formula presence in the value cells (deterministic, strongest), corroborated by bold/outline/indentation (weaker, not independently reliable — see §6). Interpretive only in the total absence of formulas (source exports flattened values). Blocks everything downstream if wrong — a rollup miscounted as a leaf silently doubles every total built on it. Rarely worth remembering per se (recomputed correctly file by file); an organisation's *habit* of exporting with or without formulas could, weakly, be worth remembering (see §12).
3. **"What does each raw line mean economically?"** — revenue, purchases, payroll, financial charges, etc. Evidence, in decreasing strength: account code range (where a coding plan exists and is legible), the caption of the aggregate the line rolls into (very strong once §2 and §1 are known), the line's own label text, its position relative to named sections. Genuinely interpretive once codes are absent or unfamiliar — this is where an LLM hypothesis or a human answer legitimately enters. Blocks only the specific line/metric it concerns, never the whole file (Article III: absence is never upgraded to zero, materiality decides whether a metric is excluded). Strongly worth remembering per Entity — this is exactly FRU's existing pattern, generalised.
4. **"What style of statement is this — and is it even the same statement all the way down?"** — statutory vs management, by-nature vs by-function, and, prior to style, whether the sheet is P&L-only or silently continues into balance-sheet territory. Evidence: section-title rows, caption vocabulary (roman-numeral/lettered captions are themselves a style signal), code-range discontinuities. Partly deterministic (a section-title row is a fact), partly interpretive (inferring "by-nature" from caption wording alone). Worth remembering per Entity; reopened if caption vocabulary or code ranges shift.
5. **"What scenario is each column?"** — actual, budget, forecast, revised forecast, prior year, YTD. Evidence: header text patterns, position relative to other columns. Already substantially deterministic in Pepperyn today (§7, capability #4). Blocks the specific column's data from being mixed into actuals if unresolved; never blocks the whole file.
6. **"Does this organisation use its own vocabulary I need to learn?"** — cost centres, product families, internal KPI names, house terms for standard concepts. Evidence: repetition across uploads, explicit human definition. The most open-ended and the most dependent on accumulated memory rather than any single file. Never blocks core P&L analysis; blocks only analyses that explicitly require the dimension in question.

## 3. The five candidate capabilities — arbitrated, not ratified

The mission's five items were given as hypotheses to attack. Findings below draw on canonical documents, the current codebase (`fru_sign_convention_detector.py`, `temporal_normalizer.py`, `fte_minimal.py`, `financial_truth.py`, `evidence_ledger_service.py`, `knowledge_model_service.py`, `epistemic_dialogue_service.py`) and a fresh, targeted inspection of the real `Phidani.xlsx` (§6).

### #1 — Detail vs Aggregate vs Derived — CONFIRMED, broadened, highest priority

Real, not hypothetical: the subtotal-contamination defect (Correction 2, this session) is direct proof a naive implementation gets this wrong. Fresh inspection this mission found the problem is **not row-specific**: `Phidani.xlsx` repeats the same detail/aggregate distinction on the **column axis** — every 13th column is a `YEAR \nYYYY` aggregate of the twelve preceding monthly columns (e.g. column D = "YEAR 2014" aggregating columns... well, column C alone for 2014 since data starts mid-year, but the pattern is columns E–P aggregate into column Q "YEAR 2015", etc.). `temporal_normalizer.py` currently classifies a `YEAR 2018` header with the same `PeriodRole` (`HISTORICAL_ACTUAL`) as an ordinary monthly column — it is saved from being double-counted only because `fte_minimal.py`'s `_resolved_actual_periods()` separately requires a resolvable month, which a bare "YEAR" header never has. This is a **currently-latent, unexploited risk**: any future capability that reads `temporal_normalizer`'s `columns_by_role` lists directly, without FTE's month-filter, would silently sum annual totals alongside their own monthly components. Flagged in §16/§20, not fixed (out of scope).

Real hierarchy is also deeper than binary leaf/rollup: Phidani shows at least three tiers — leaf (`630200`) → lettered subtotal (`630 "D. Amortissements..."`) → roman-numeral subtotal (`60/64 "II Coût Ventes-Prestations"`, itself a compound code aggregating several lettered subtotals). The current FRU exclusion logic only performs a binary "is this row's value cell a formula" exclusion; it does not model the tiers themselves.

Deterministic core: formula-presence in the value cell, confirmed reliable across every sampled row in the real file (`_code_range_signal`'s existing rollup exclusion already relies on exactly this). Bold formatting and `outline_level` are present and mostly corroborating but were observed to disagree at least once (row 231, `650 "A. Charges Dettes"`, is a formula-derived subtotal with `bold=False`) — not independently trustworthy, only formula-presence is.

Case I (no formulas, exported values only) is the one adversarial case that defeats the current signal entirely (§7) — a real, named limitation, not fixed here.

Currently implemented only as logic embedded inside `fru_sign_convention_detector.py`'s row loop, coupled to sign-convention detection specifically — not exposed as a reusable primitive.

### #2 — Economic Nature of Line Items — CONFIRMED, distinct, dependent on #1

Prior art exists and must not be confused with this capability: `backend/models/financial_truth.py`'s `MetricType` enum (`REVENUE/GROSS_MARGIN/EBITDA/NET_PROFIT/CASH/COST/COST_SAVING/WORKING_CAPITAL/EXPOSURE/UNKNOWN`) already classifies something adjacent — but at the *aggregated impact/insight* level, populated by an LLM (`SourceType.LLM_EXTRACTED`), architecturally dormant per `CURRENT_DOMAIN_MODEL.md` (production renderers still read the legacy `annual_impact` field, not `QuantifiedImpact`). This is a different problem solved at a different layer (post-analysis insight classification, not pre-analysis line-item classification) — named as an architectural point of attention in §17, not a conflict requiring resolution now, but a future implementation of #2 must explicitly decide its relationship to `MetricType` before writing code.

Real file adds a third evidence source beyond the illustrative "codes/labels/position/arithmetic": the **caption of the parent aggregate a leaf rolls into** is, once §1 is solved, very strong evidence on its own (e.g. every leaf under `630 "D. Amortissements"` is depreciation/impairment by construction of the file, independent of the leaf's own label). This is Belgian-schema-flavoured (the lettered/roman-numeral captions follow the *schéma minimum normalisé*) but the *mechanism* — inherit nature from the nearest confidently-classified ancestor — is not: it degrades gracefully to weaker evidence in Case C/E where no such captions exist. A fourth, minor evidence source was also observed: some labels carry an explicit sign annotation in the text itself (`"Capital non appelé (-)"`, `"Utilisations et reprises (-)"`) — noted for completeness, not evaluated further (out of scope of this mission, adjacent to FRU rather than #2 proper).

Genuinely dependent on #1: the question "what does this leaf mean" presupposes knowing it is a leaf; an aggregate row's "nature" is derivative of what it aggregates, a different question.

### #3 — Implicit P&L/Reporting Structure — CONFIRMED, broadened to include statement-boundary detection

The illustrative list (statutory/management/by-nature/by-function/contribution-margin/EBITDA-oriented/bespoke) presupposes the file *is* a P&L. Fresh inspection of the real file disproves that assumption: `Phidani.xlsx` is a single continuous sheet that begins with a section-title row `"Compte de résultats"` (row 3, no code, no value — pure text) and, from row ~366 onward, silently continues into balance-sheet territory (`"29/58 ACTIFS CIRCULANTS"`, a blank-coded row captioned `"ACTIF"`, then a text-only row `"PASSIF"`) — sharing the exact same code space, the same indent/bold/formula conventions, and the same lettered/roman-numeral caption grammar as the P&L section above it. A controller reading this file does not ask "which P&L style is this" in isolation — they first ask "where does the P&L end and the balance sheet begin," a question the illustrative list never named. This document folds that question into capability #3 as a sub-question (**#3a — statement-boundary detection**, largely structural/label-driven: presence/absence of section-title rows, code-range discontinuities) rather than inventing a sixth capability, and keeps the illustrative P&L-style question as **#3b**.

Phidani's own P&L is by-nature (rémunérations, amortissements, achats — not grouped by function/product), directly legible from its captions — an observation, not a generalisable claim about all Belgian files.

### #4 — Scenario Semantics — CONFIRMED distinct from FTE, but already ~80% built

Major finding this mission: this capability is **not green-field**. `temporal_normalizer.py`'s `TemporalColumn` already carries deterministic, regex-based boolean signals — `is_budget`, `is_forecast`, `is_ytd`, `is_prior_year`, `is_current_explicit` — covering four of the five illustrative scenario types today, in production, feeding both FTE v0 and the LLM context. Two real gaps: no distinct "Revised Forecast" pattern (would currently classify as plain `FORECAST`, losing the distinction) and no "Plan" pattern (French "plan" matches none of `_BUDGET_PATTERNS`/`_FORECAST_PATTERNS`, would fall through to `UNKNOWN` or misclassify).

An architectural point worth naming: `PeriodRole` **conflates** two orthogonal questions in one enum — *which year* (current vs. historical, an FTE-adjacent temporal question) and *what kind of data* (actual vs. budget vs. forecast vs. YTD, the genuine scenario-semantics question). This works today only because FTE v0 reads a narrow subset (`CURRENT_ACTUAL`/`HISTORICAL_ACTUAL`) and no Scenario Semantics consumer exists yet to be confused by the rest. If Scenario Semantics is ever built as a real capability, it should consume `TemporalColumn`'s boolean signals directly (a **projection** over `temporal_normalizer`'s existing output), not re-derive or duplicate `PeriodRole`.

Real file gives **zero** empirical coverage: Phidani contains no budget/forecast/YTD columns at all, only actuals and year-aggregates. The capability is real and distinct, but structurally unverified against the one real Golden Case available; would need a synthetic Case-G-style fixture to prove even the existing signals end-to-end.

Given it is already substantially solved deterministically and unverified only for lack of a real mixed-scenario file, this capability is **not** a priority for new investment right now.

### #5 — Company-specific terminology/dimensions — CONFIRMED in principle, zero empirical grounding, lowest priority now

Phidani gives no evidence at all for this capability (single legal entity, no cost-centre/product/region dimension visible anywhere in the inspected structure) — entirely hypothetical relative to the one real file available; Case F would need a different fixture to even test.

Architectural tension worth flagging, not resolving: `KnowledgeModel` v0's `SUBJECT_VALUE_REGISTRY` is, by explicit contract, a **curated, closed enum per subject** (sign convention today: two legal values). Company-specific terminology (cost-centre names, KPI names) is **open-vocabulary and unbounded per organisation** — it does not obviously fit the existing registry mechanism without an extension (an "open-vocabulary subject" kind KnowledgeModel does not have today). Named as a real, unresolved architectural question in §17; not to be designed or implemented here.

## 4. Missing capabilities discovered

No genuine sixth capability was found. Two extensions to existing items, both empirically forced by the real file, both folded into the nearest existing capability per the mission's own preference for extending over inventing:

- **Statement-boundary detection (P&L vs balance sheet vs cash flow)** — folded into #3 as #3a (§3).
- **Column-axis detail/aggregate** — folded into #1, which is now understood as axis-agnostic (any grouping — rows, columns, and by extension future dimensions like cost centre — can mix leaves and rollups; §3, §7 case F).

One cross-cutting reliability finding, not a capability: a genuinely corrupted value was observed in the CODES column itself during this inspection (row 234, code literal `72.44444444444444` — almost certainly a compound code like `"65/6"` that Excel silently coerced into a division result). This is empirical proof that even a nominally-structural field (account code) can carry raw data corruption in a real file — reinforcing, not weakening, the existing discipline that code-range evidence must remain HYPOTHESIS-tier (per `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md` §3), never treated as guaranteed-clean structural ground truth.

## 5. #2 ↔ #3 relationship

Chosen: **(D) one capability with two projections, for the mechanistic reason given in (C).** Neither pure sequence (A) nor full independence (B) survives contact with the real file: Phidani's lettered/roman-numeral subtotal captions are simultaneously the primary evidence for *reporting structure* (they define the by-nature P&L style, §3b) and, once §1 resolves which leaves roll into which caption, the primary evidence for *economic nature* of those same leaves (§3, #2) — one underlying evidentiary substrate (the parsed caption/hierarchy), two query surfaces consumers need separately (aggregation math needs structure; commentary/insight generation needs nature). Case D (functional P&L, payroll distributed across multiple functional captions) independently confirms the coupling is real and not merely convenient: the *same* economic nature (payroll) appears under *several different* structural buckets, meaning a controller must hold a structural view and a nature view of the same leaf simultaneously, revising one in light of the other, not resolving them in a clean one-way sequence. The qualifier matters, though: Case C (management P&L, no codes) shows the two are not *fully* fused — structure can sometimes be read from section headers alone even when individual-line nature stays ambiguous — so (D) is the correct verdict, not (C) taken to its strongest (fully inseparable) reading.

## 6. Relationship to FTE, Evidence, KnowledgeModel, Epistemic Dialogue

**FTE** — confirmed orthogonal, no overlap once distinguished: FTE answers *when* (business-time boundary of the newest observed data); #4 (Scenario Semantics) answers *what kind of the same when* (actual vs. budget vs. forecast); #1–#3 answer *what does this line mean and is it raw or computed*, none of which FTE touches. #4 legitimately shares its evidence source with FTE (both read `temporal_normalizer`'s output) but neither reads the other's derived state — FTE never reads `PeriodRole`'s scenario-flavoured entries, and #4 (if built) should never re-implement FTE's business-time boundary logic.

**Evidence** — all five capabilities produce new *interpretive* facts about already-observed cells (a leaf/aggregate classification, a nature classification, a structure classification); none require a new evidence-capture mechanism. Their outputs are shaped exactly like existing `SourceReference` (sheet/row_label/period/observed_value), consistent with `financial_truth.py`'s existing shape — no new source of truth required for the evidence layer itself.

**KnowledgeModel** — clear candidates for per-Entity memory: #2 (a leaf's or a caption's inferred nature, once confirmed, should never be re-asked), #3 (once an Entity's reporting style/statement layout is confirmed, recall it rather than re-infer every upload), #5 (terminology, by definition memory-first). #1 is, by contrast, near-fully deterministic per file and does *not* obviously need organisational memory — with one weak exception noted for completeness: whether an organisation habitually exports with or without formulas could, in principle, be worth remembering (relevant to Case I), but this is speculative and not confirmed as a real need. #4 needs minimal KnowledgeModel support beyond, possibly, a company's non-standard scenario vocabulary (a #5-flavoured memory, not a #4-specific one).

**Epistemic Dialogue** — every capability that can produce a materially-confident-but-not-certain classification is a candidate for the same RECALL-before-ASK, never-ask-twice loop already proven for FRU's sign convention (§7 names where). Materiality-by-subject must be defined per new subject before any question is authorised — not attempted here.

## 7. Uncertainty behaviour, deterministic/interpretive boundary, LLM role, human role

**Deterministic (near-certain):** #1's formula-presence signal (proven reliable across every sampled real-file row); FTE and `temporal_normalizer`'s existing regex signals; statement-boundary detection via section-title-row presence/absence (#3a, mostly).

**Strong-inference-tier (deterministic-with-known-exceptions):** #2's code-range evidence and parent-caption inheritance; #4's existing boolean signals (reliable but structurally unverified against a real mixed-scenario file, §3).

**Genuinely interpretive (LLM or human territory):** #2's freeform label semantics when no code and no confidently-classified ancestor caption exist (Case C/E); #3b's P&L-style judgment when captions are bespoke; #5 in its entirety (open vocabulary, by construction).

**LLM role:** none of the five capabilities requires a *new* LLM call for its deterministic core. Interpretive residue (freeform label semantics) is the same class of problem the existing, already-flagged-as-a-gap file-normalization LLM step touches (`COGNITIVE_CAPABILITY_MAP.md`'s deterministic/probabilistic boundary table) — a candidate for widened *use* of an existing call, decided at implementation time, not a new call authorised here.

**Human role:** the same four-stage authority gate already proven for FRU v0, extended to whichever new subjects get built. One addition specifically relevant here, carried over verbatim from Fred's closing note on the prior mission (§9): #2/#3/#5 will legitimately produce more no-defensible-candidate cases than #1's binary sign convention did (an unfamiliar caption or an unrecognised code range does not always yield even a weak hypothesis) — this is exactly the situation the deferred "third form of epistemic humility" exists for, and its importance is reinforced, not diminished, by this mission's findings.

**Materiality / UNKNOWN behaviour:** default is proceed-with-limitation — exclude only the specific line/metric affected, never block whole-file analysis (Article III: absence stays absence). Human clarification is warranted only when a misclassification would materially move a headline metric (e.g. a large revenue line silently misclassified as balance-sheet noise), not merely because uncertainty exists. No new scoring engine — same materiality-by-subject discipline as Epistemic Dialogue v0, to be defined per new subject at implementation time.

## 8. Enterprise Familiarization verdict

**Emergent, not a sixth capability, not new architecture.** `PEPPERYN_PROFESSION_MODEL.md` Ch.5 already ratifies Enterprise Familiarization as a real, qualitatively-distinct Engagement lifecycle phase, not a new bounded context — this mission does not need to re-decide that. What this mission adds: the mechanism that *produces* the familiarization effect is exactly the combination already built — FRU-style capabilities (#1–#5) feeding KnowledgeModel, mediated by Epistemic Dialogue — operating repeatedly over an Entity's first several uploads, each upload asking fewer questions than the last as more subjects reach Confirmed status. No separate inference engine is needed to produce this effect; it already falls out of the existing architecture once more than one subject exists. A thin *measurement/reporting* projection (e.g. "share of known subjects Confirmed for this Entity") would have real product value later, surfaced for the user, but is a read-model over data these capabilities already produce — not a new capability, and explicitly not part of the next atomic slice recommended below.

## 9. Adversarial representation matrix (cases A–J)

| Case | Verdict | Why |
|---|---|---|
| A — Phidani-like (coded, formula rollups) | Holds | Calibration case itself; §3, §6. |
| B — naturally signed, no ABS convention | Holds, no new gap | #1's formula signal is convention-independent; FRU's `SIGNED_NATURAL` already exists for exactly this. |
| C — management P&L, no codes | Holds, degrades gracefully | #1 unaffected (formula-presence is code-independent). #2 loses its strongest evidence but falls back to parent-caption/label text at lower confidence tiers — does not break, produces more HYPOTHESIS/UNKNOWN, correctly. |
| D — functional P&L, payroll distributed across functions | Holds, and strengthens §5's verdict | Confirms #2/#3 must be held simultaneously for the same leaf, not resolved in a clean sequence — direct empirical support for the (D)/(C) relationship verdict. |
| E — bespoke terminology | Holds | Stresses #5 primarily; #2 degrades exactly as in Case C. |
| F — multi-dimensional (cost centres/products/regions) | Holds, generalises §3/§4 finding | Confirms #1's leaf/aggregate distinction must be phrased dimension-agnostically (already found true for rows and columns in Phidani itself), not row-specific. |
| G — mixed Actual/Budget/Forecast in one workbook | Holds | Squarely #4's territory, already ~80% solved via `temporal_normalizer`'s boolean signals (§3); confirms #4 is real and FTE-orthogonal, adds no new gap. |
| H — visually misleading row position vs. formula-revealed hierarchy | Holds | Exactly the principle Correction 2 already proved and implemented for FRU (formula truth over visual/position truth) — no new gap, reinforces existing discipline. |
| I — no formulas, exported values only | **Breaks #1's current, only signal** | Formula-presence is the sole deterministic signal in the current implementation; without it, #1 has no fallback (arithmetic cross-check against sibling sums, or corroborating bold/indent signals, are structurally present in the real file but not currently used as fallback evidence). Real, named limitation — not fixed here (§16). |
| J — partially understood file (some rows confident, others ambiguous) | Holds — this is the normal case | Already supported by the existing tiered STRONG_INFERENCE/HYPOTHESIS/UNKNOWN model and the "materiality, not discomfort" principle; nothing new required. |

## 10. Dependency graph

Illustrative only — not to be assumed correct beyond what §3–§9 established:

```
#1 (Detail/Aggregate/Derived, axis-agnostic)
        │
        ▼
#3a (statement-boundary: P&L / balance sheet / cash flow)
        │
        ▼
  ┌─────┴─────┐
  ▼           ▼
 #2          #3b
(Economic   (P&L style)
 Nature)      │
  └─────┬─────┘
   mutually constraining (§5)

#4 (Scenario Semantics)  — parallel, independent of #1/#2/#3, shares evidence with FTE only
#5 (Terminology)         — parallel, most independent; benefits from #1–#3 richness but not blocked by it

KnowledgeModel + Epistemic Dialogue operate transversally across all five (§6), exactly as already proven for FRU's one subject.
```

## 11. Prioritisation (qualitative) and recommended next atomic slice

Against the ten named criteria (catastrophic-error potential, real-file frequency, dependency value, deterministic solvability, need for organisational learning, need for LLM interpretation, ease of a falsifiable Golden Case, overfitting risk to Phidani, architectural dead-end risk, immediate contribution to professional credibility) — no fabricated scores; qualitative summary:

- **#1** ranks highest: catastrophic-error potential is proven, not hypothetical (the contamination defect already happened); it is a hard prerequisite for #2 and #3b (§10); it is the most deterministically solvable of the five; it has the richest, already-inspected real Golden Case (leaf/aggregate rows across two axes, §3–§4); overfitting risk is low precisely because the core signal (formula presence) is not Belgian-specific; the one real gap (Case I) is nameable and safely deferrable with an honest UNKNOWN, not a dead end.
- **#2** and **#3** rank next, genuinely coupled (§5), both blocked on #1, both carry real LLM/overfitting risk if rushed — correctly sequenced *after* #1, not concurrently with it.
- **#4** ranks low for new investment: already ~80% solved deterministically; the remaining gap (Revised Forecast/Plan vocabulary, exposing boolean signals as a projection) is small and low-risk but not urgent.
- **#5** ranks lowest for now: zero empirical grounding in the one real file available, no falsifiable Golden Case can be built today, and it carries an unresolved KnowledgeModel-fit question (§3) better left open than forced.

**Recommended next atomic slice — confirmed, not "Build FRU" or "Understand financial files":**

**Row/Column Observation Classification: LEAF vs AGGREGATE vs SECTION_HEADER**, extracted as a small, reusable, axis-agnostic deterministic primitive — out of `fru_sign_convention_detector.py` (where the leaf/rollup exclusion logic currently lives, coupled to sign-convention detection) into its own module, consumed by FRU today and available to future #2/#3 work without duplication. One professional responsibility (§3 #1, broadened per §4/§9); one bounded input (a parsed workbook's cells — value, formula-or-not, code, label, position); one deterministic kernel (formula-presence, the only signal proven reliable in this mission); one real Golden Case (Phidani, both axes, §3); explicit UNKNOWN behaviour for Case I (no formula evidence → UNKNOWN, never inferred from position/bold alone); no interaction with KnowledgeModel (§6 — not confirmed as needed) or Epistemic Dialogue required for this slice (the classification is near-fully deterministic per file, nothing to ask a human); no premature general engine (no arithmetic-cross-check fallback for Case I built now — deferred, §16, no real Case-I file exists yet to calibrate against).

## 12. Explicitly deferred (this mission, not to be started now)

- Capability #2 (Economic Nature) and #3 (Reporting Structure) implementation — sequenced after the next slice, per §10/§11.
- Capability #4's Revised Forecast/Plan vocabulary gap and its exposure as a projection over `temporal_normalizer`.
- Capability #5 (Terminology) in its entirety, including the open-vocabulary KnowledgeModel extension question (§3).
- The arithmetic-cross-check fallback for Case I (no-formula files).
- The Enterprise Familiarization measurement/reporting projection (§8).
- The relationship between a future #2 implementation and `financial_truth.py`'s `MetricType` (§3, §17).
- The "third form of epistemic humility" (open-ended clarification when no defensible candidate exists) — named again here per Fred's explicit request, not designed, not implemented; remains the next evolution of Epistemic Dialogue itself, orthogonal to which professional capability is built next.
- Any smart-question pattern for any of the five capabilities (mission §11 — explicitly not to be implemented).

## 13. Named architectural conflicts / reservations

1. `temporal_normalizer.py`'s `PeriodRole` conflates temporal-year and scenario-kind in one enum (§3 #4) — not a defect today (no consumer confused by it), a real constraint on how #4 should be built if it ever is (consume the boolean signals, not `PeriodRole`).
2. `financial_truth.py`'s `MetricType` is a real, dormant, LLM-driven prior classification adjacent to but not the same problem as capability #2 (§3, §12) — must be explicitly arbitrated, not silently duplicated or contradicted, whenever #2 is built.
3. KnowledgeModel v0's closed, curated `SUBJECT_VALUE_REGISTRY` does not obviously fit capability #5's open-vocabulary needs (§3, §12) — a real, unresolved architectural question, not a defect, left open.
4. The column-axis detail/aggregate latent risk (§3, §4) — `temporal_normalizer`'s `columns_by_role` output does not itself guard against a future consumer double-counting a `YEAR` aggregate column alongside its own monthly components; only `fte_minimal.py`'s incidental month-requirement currently prevents this, for FTE's own purposes only. Flagged, not fixed.
5. A corrupted value observed in the real file's CODES column itself (§4) — empirical grounds to keep code-range evidence at HYPOTHESIS tier permanently, not a one-off data-quality complaint to raise with the source.

---

## Adversarial self-review (15 questions, mandatory before finalising)

1. **Are we accidentally designing around Phidani specifically?** Partially guarded: §3/§9 repeatedly test the decomposition against 10 non-Phidani-shaped cases and explicitly separate what is Belgian-specific (caption vocabulary, code ranges) from what is general (formula-presence, the leaf/aggregate distinction itself, the mutual-constraint mechanism in §5). Residual risk: only one real file was available for empirical grounding — acknowledged explicitly in §3 (#4, #5) rather than papered over.
2. **Are Belgian codes becoming hidden universal truth?** No — every use of Belgian code ranges in this document is explicitly qualified as one evidence source among several, degrading gracefully in Cases C/E (§9), and §4's corrupted-code finding is used as an argument *against* trusting codes unconditionally, not for it.
3. **Are formulas mistaken for the only hierarchy source?** Named directly as a real gap, not silently assumed away — Case I (§9) is documented as breaking the current, sole signal, and the arithmetic-cross-check fallback is explicitly deferred rather than assumed unnecessary.
4. **Can Detail/Aggregate/Derived be determined independently of Economic Nature?** Yes, and the document says so (§10 dependency direction) — #1 requires no economic-nature judgment, only structural evidence.
5. **Are Economic Nature and Reporting Structure falsely separated, or falsely fused?** Addressed directly in §5 with a falsifiability test (Case C) against the strongest fully-fused reading — the (D)-with-(C)-mechanism verdict is a considered middle position, not a default.
6. **Are we confusing Scenario Semantics with FTE?** Explicitly distinguished in §6, including the shared-evidence-but-not-shared-derived-state nuance.
7. **Are we inventing taxonomy before observing enough organisations?** No taxonomy is proposed — §3's illustrative economic-nature categories are inherited from the mission brief as illustrative only, and §11's recommended slice deliberately contains no economic-nature taxonomy at all, only a structural leaf/aggregate primitive.
8. **Are we creating another source of truth?** Checked explicitly against `MetricType` (§3, §13) and against KnowledgeModel's registry shape (§3, §13) — both named as open questions for later, not silently resolved by fiat here.
9. **Are we asking the LLM to define canonical meaning?** No — §7 explicitly scopes LLM involvement to interpretive residue only, never the deterministic core, and authorises no new call.
10. **Could KnowledgeModel remember at the wrong scope?** Not tested by implementation (none proposed here); §6 restricts KnowledgeModel candidacy to Entity-scoped facts consistent with the existing FRU pattern, and explicitly marks #1's memory candidacy as weak/unconfirmed rather than asserting it.
11. **Could Pepperyn ask something a competent controller should answer from the file alone?** The recommended next slice (§11) asks nothing of a human — it is fully deterministic with an honest UNKNOWN fallback, by design.
12. **Could Pepperyn silently analyse materially ambiguous data?** §7's materiality rule (exclude the affected metric, never the whole file, escalate only when headline-material) is carried over unchanged from the proven Epistemic Dialogue v0 pattern, not weakened here.
13. **Does the next slice genuinely unlock later capability?** Yes — §10/§11 show #2 and #3b are structurally blocked on #1; the slice is a named, direct prerequisite, not a convenient-but-unrelated starting point.
14. **Could the slice be smaller?** Considered and rejected: a smaller slice (e.g. only the sign-detector's existing inline exclusion, left as-is) would not remove the coupling to sign-convention detection that currently prevents #2/#3 work from reusing it — extraction is the smallest change that removes a real, already-identified blocker for the next capability.
15. **Is any new architecture actually necessary?** No — the recommended slice is a pure extraction/generalisation of logic that already exists and already works (`fru_sign_convention_detector.py`'s rollup exclusion), not a new bounded context, no new persistence, no new table, consistent with the mission's explicit preference for projection/service over invented architecture.

No answer above exposed a defect requiring revision of the document's substantive conclusions; §4's corrupted-code and column-axis findings were incorporated as they were discovered during this same drafting pass rather than after.

---

**FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL ESTABLISHED. NO CODE WRITTEN. NO CAPABILITY IMPLEMENTED.**
