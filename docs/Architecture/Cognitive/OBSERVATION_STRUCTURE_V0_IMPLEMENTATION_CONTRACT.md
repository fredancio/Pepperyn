# OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md

**Status:** PROPOSED — implementation contract, not yet implemented, not yet approved for coding.
**Branch:** `architecture/observation-structure-v0-contract-2026-08-10` (not merged).
**Position in the documentary hierarchy:** below `FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL.md`, at the same level as `FRU_EPISTEMIC_FIRST_VERTICAL_SLICE.md` and `EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md` — this is the implementation contract for the profession-model document's §11-recommended (and §11-corrected, 2026-08-10) next atomic slice: **Detail vs. Aggregate vs. Derived**, resolved here into two orthogonal v0 dimensions, `structural_role` and `derivation_status`.
**Does not duplicate:** `FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL.md` (the five-capability arbitration and the reasoning for why this slice is next — reused, not restated); `FINANCIAL_REPRESENTATION_UNDERSTANDING_FOUNDATION.md` (the OBSERVATION/INFERENCE/KNOWLEDGE epistemic mapping and FACT/STRONG_INFERENCE/HYPOTHESIS/UNKNOWN vocabulary — reused, not reinvented).

---

## 1. Professional responsibility

Before a controller counts, sums, or compares any number in a financial file, they silently answer two separate questions about every row they look at: *"what role does this line play in the report"* (a raw entry, a subtotal, a headline indicator, a heading with no value) and *"was this number computed from other lines in this same file, or is it a source fact"* (because a computed line must never be summed alongside the lines it was computed from, on pain of double-counting). An excellent controller never confuses these two questions, even though a careless reading of the file often makes them look like the same question — this contract exists because Pepperyn made exactly that conflation in its first working draft of this capability, and a real row in a real file (Phidani, row 163) proved it wrong.

## 2. What v0 classifies — resolution of the three candidate questions

The founding question (mission §2) asked whether "structural role," "how the value was produced," and "is it an independent economic observation" are the same dimension, orthogonal, or should not all exist in v0. Resolved as follows, evidenced against real `Phidani.xlsx` rows (all row numbers below refer to the real file, sheet `PHIDANI`):

- **`structural_role`** — WHAT ROLE this observation plays in the report's own structure. Kept as a first-class v0 dimension.
- **`derivation_status`** — HOW the observation's value was produced, as observable from within this file. Kept as a first-class, **separate** v0 dimension.
- **"Independent economic observation"** — split in two on inspection, and **not** kept as a third v0 dimension:
  - *Arithmetic independence* ("is it safe to sum this into a total alongside other rows without double-counting?") is a pure, mechanical **consequence of `derivation_status`** (`DERIVED` ⇒ not arithmetically independent; `SOURCE_VALUE` ⇒ independent) — no separate field is needed; a consumer computes it as `derivation_status != DERIVED` if convenient.
  - *Analytical meaningfulness* ("is this a fact worth citing to a human as its own observation, regardless of whether it is arithmetically redundant?") is **not** determinable from structure alone (Phidani row 133, `"B1 Marge brute d'exploitation (EBITDA)"`, formula `=C35-C132`, is arithmetically 100% redundant with its two inputs yet is the single most citable number in the file) — this belongs to the future Economic Nature / Reporting Structure capability (#2/#3 in the profession-model document), explicitly **OUT** of this slice.

**Proof the two kept dimensions are genuinely orthogonal, not derivable from each other** (the founding tension named in the mission brief and in Fred's closing note): Phidani row 163 (`630`, `"D. Amortissements - Réductions Valeur"`, formula `=C162`) has `structural_role = AGGREGATE` (bold, lettered statutory caption, correct hierarchy position — the official "D." line of the Belgian minimum schema) yet `derivation_status = DERIVED` via a **trivial single-cell passthrough**, not a genuine multi-row sum — its role says "aggregate," its derivation mechanism looks nothing like the textbook "sum of many leaves" (row 161, `62`, `=SUM(C134:C160)`) that motivated the original model. Conversely, a hardcoded manual Excel total (mission §3 case 10, not present in Phidani, constructed conceptually) would show `structural_role = AGGREGATE` (from caption/position evidence alone) while `derivation_status = SOURCE_VALUE` (no formula observable in this file) — the mirror-image proof. Neither field can be reliably computed from the other; both are required.

## 3. v0 classification semantics

### 3.1 `structural_role` — four values, non-exclusive-in-reality but exclusive-by-convention in v0

| Value | Meaning | Real Phidani example |
|---|---|---|
| `LEAF` | A raw, individually-posted line — the smallest unit the report shows. | Row 134, `620250`, `"Rémunération brute employés"`, `863540.12`. |
| `AGGREGATE` | A subtotal/total line belonging to the report's own statutory or organisational hierarchy. | Row 161, `62`, `"C. Rémunérations..."`, `=SUM(C134:C160)`; row 165, `60/64`, `"II Coût Ventes-Prestations"`, `=C34+C132+C161+C163+C164`. |
| `KPI` | A headline/management indicator that nets or combines already-aggregated lines, distinct from a plain hierarchy subtotal. | Row 133, `B1`, `"Marge brute d'exploitation (EBITDA)"`, `=C35-C132`. Proven necessary by this row alone — it does not fit `AGGREGATE`'s "sum of a homogeneous set of children" shape, nor `LEAF`. |
| `SECTION_HEADER` | A row that carries no observation value at all — a pure caption. | Row 3, `"Compte de résultats"` (no code, no value); row 369, `"PASSIF"` (no code, no value). |

**Compound-row decision (mission §3 test 7 — a row that is simultaneously a section boundary and carries a subtotal value, e.g. row 165, roman-numeral `"II"`, bold, formula-derived):** classified by its **value-bearing behaviour**, i.e. `AGGREGATE`, not `SECTION_HEADER`. The fact that its caption *also* marks a section boundary is real and useful but belongs to the future Reporting Structure capability (#3a in the profession-model document) — v0 does not attempt to represent "this row is both a subtotal and a section boundary" as a compound state. Named explicitly, not silently dropped.

**KPI-vs-AGGREGATE ambiguity is tolerated, not escalated (see §8 — no Epistemic Dialogue in v0):** distinguishing a textbook statutory subtotal from a headline KPI sometimes depends on organisation-specific caption convention (Phidani's ad-hoc `"B0"`/`"B1"`/`"B2"`/`"B3"` code family, which is this report template's own invention, not a Belgian universal signal — flagged explicitly, never generalized). Because both values carry the **same downstream consequence** (arithmetically not independent, per §2), v0 is permitted to return the coarser value or `UNKNOWN` role when the finer distinction is not resolvable, without blocking or asking a human.

### 3.2 `derivation_status` — four values, evidence-graded

| Value | Meaning | Real Phidani example |
|---|---|---|
| `SOURCE_VALUE` | No formula observed in this cell in this file. | Row 134, `620250`, `863540.12` (literal). |
| `DERIVED` | A formula is present in this cell, referencing other cell(s) in this file — regardless of whether it references one cell (row 163, `=C162`) or fifty (row 161, `=SUM(C134:C160)`), and regardless of whether the formula sums, subtracts, nets, or (conceptually, per §7) computes a ratio. **v0 deliberately does not sub-type the arithmetic operation** — sum vs. difference vs. ratio is an economic-nature/structure question (#2/#3), not an "is this safe to sum" question, and every one of those shapes has the identical downstream consequence. | Row 163 (`=C162`, single-reference); row 161 (`=SUM(...)`, multi-reference); row 133 (`=C35-C132`, difference of two already-`DERIVED` rows — "derived from derived," a real shape, not specially flagged as a distinct value). |
| `NOT_APPLICABLE` | No value is present in this cell at all — a distinct state from `UNKNOWN`, because no derivation question even arises when there is nothing to derive. | Row 3 (`"Compte de résultats"`, no value in the value column); a blank future period cell (e.g. an October 2019 cell in a file that stops at September). |
| `UNKNOWN` | A value is present, but this file offers no formula-mode evidence for how it was produced (see §5's parser gap) and no fallback was attempted (see §6, §9 — no fabricated fallback). | The conceptual no-formula-export adversary (mission §8) — not present in Phidani, which is 100% formula-consistent for every sampled subtotal. |

**Epistemic honesty on `SOURCE_VALUE` (mission §3 case 9, direct answer):** `SOURCE_VALUE` means *"no derivation evidence is observable within this file,"* never a claim that the number was not, in reality, computed somewhere upstream (an ERP module, a prior spreadsheet). Pepperyn cannot see past the boundary of the file it was given — this is stated as a permanent epistemic limit of this classifier, not a gap to close.

**Zero and absence stay distinct (Article III, extended here):** a literal `0` value is `SOURCE_VALUE`, not `NOT_APPLICABLE` and not `UNKNOWN` — a true zero is a fact, never confused with "nothing here."

## 4. Row / column scope — v0 is row-axis only, by evidence, not by symmetry

The profession-model document broadened the underlying problem to both axes (row aggregates *and* the real file's `"YEAR YYYY"` column aggregates). This mission confirms the **two-dimension vocabulary is axis-agnostic in concept** — `derivation_status` for a `"YEAR"` column is exactly the same kind of fact (does this column's value derive from other observations, here other *columns* of the same row, rather than other *rows* of the same column) — but the **evidence is not symmetric across axes**: `SECTION_HEADER` was observed only on the row axis (no column in Phidani carries "no value, pure caption" the way row 3 or row 369 do); a column-level `KPI`-equivalent (a variance or percentage column) is plausible but was not observed in Phidani at all (the file has no budget/forecast columns, confirmed in the profession-model mission). Per mission §5's explicit instruction not to force symmetry: **v0 implements the row axis only.** The vocabulary (`structural_role`, `derivation_status`) is deliberately defined generically enough (§3's wording never says "row") that a future column-axis extension would reuse it rather than redesign it — but that extension is explicitly deferred, not built now.

## 5. Deterministic evidence hierarchy — and the one real implementation gap

In decreasing reliability, as actually available today:

1. **Formula presence in the observation's own cell** (`derivation_status`'s primary and, in v0, only signal) — proven reliable across every sampled real-file row this and the prior mission inspected. **Requires `openpyxl.load_workbook(path, data_only=False)`** — formula-mode access.
2. **Caption/position/hierarchy evidence** (`structural_role`'s primary signal set) — section-title-row detection (no code, no value → `SECTION_HEADER`), bold/`outline_level`/indentation as corroborating-but-not-independently-reliable signals (row 231, `"650 A. Charges Dettes"`, is a genuine formula-derived subtotal with `bold=False` — proving bold alone is not trustworthy), account-code presence/absence and caption text pattern (lettered/roman-numeral captions) as weaker, Belgian-schema-flavoured corroboration.
3. **Formula reference extraction** (which cell(s) a `DERIVED` observation's formula points to) — cheaply available via the same regex-based approach `fru_sign_convention_detector.py` already uses for its margin-subtraction pattern search. **Not exposed as a v0 output field** (see §12 — no current consumer), but the extraction mechanism is a trivial byproduct of computing `derivation_status` and should not be thrown away if computed in passing.

**Signals technically observable but not currently used by anything, named per mission §6's explicit instruction not to silently omit them:** merged-cell ranges (`ws.merged_cells.ranges`); row-level `bold`/`outline_level`/indentation (present and informative in Phidani per the profession-model mission's inspection, currently read by nothing).

**The one real, currently-existing implementation gap (mission §6, §9 — must be named, not silently assumed solved):** the shared production Excel parser, `backend/services/file_parser.py`, reads files with `openpyxl(..., data_only=True)` as its **primary** strategy — i.e. it reads cached formula *results*, never formula *text*. Its documented last-resort fallback (plain pandas) reads "formulas as strings" only in a degraded path, unreliable as a primary signal source. **Formula presence is therefore not observable today from the shared, general-purpose file-ingestion pipeline that the rest of Pepperyn consumes.** It is observable only because `fru_sign_convention_detector.py`'s own adapter function independently re-opens the raw file a second time with a dedicated `data_only=False` call, coupled to a raw file path rather than to any shared parsed representation. Any v0 implementation of `derivation_status` inherits this same choice: either perform its own independent formula-mode read (as FRU already does — duplicating I/O, a known and so-far-tolerated cost) or wait for `file_parser.py` to be extended to also expose formula-mode structure. **This contract does not resolve that choice** — it is named here as the real blocker to implementation-time decide, not papered over (see §14).

## 6. No-formula case (mandatory, mission §8) — UNKNOWN is the correct v0 answer

Constructed conceptually — no real no-formula file was available. If every formula in Phidani were replaced by its computed value (a materialised/flattened export, or Case I/L from the adversarial matrices): `derivation_status` degrades honestly to `UNKNOWN` for every row that would otherwise have been `DERIVED` — there is no safe fallback signal in v0. Two theoretically possible fallbacks were considered and **explicitly rejected for v0**, per the mission's own "do not fabricate a fallback" instruction: (a) inferring structure from caption/position/ordering alone — this can still inform `structural_role` at `HYPOTHESIS` tier (independently of `derivation_status`, another proof the two dimensions are separable — §2), but cannot safely resolve `derivation_status`, since a leaf and a materialised rollup are visually and positionally indistinguishable once both are literal numbers; (b) an arithmetic cross-check (recomputing whether a candidate aggregate's value equals the sum of the rows structurally identified as its children, and inferring `DERIVED` if it matches) — a real, named, deferred idea (also named in the profession-model document's §16), not implemented here: no real no-formula file exists yet to calibrate against, and a false-positive cross-check match (a leaf value that coincidentally equals a plausible sum) would produce a confidently wrong classification, worse than an honest `UNKNOWN`.

## 7. Relationship to Evidence, FTE, FRU, Knowledge Model, Epistemic Dialogue

**Evidence** — no new evidence-capture mechanism needed. `structural_role`/`derivation_status` are new interpretive metadata about already-observed cells, shaped compatibly with existing `SourceReference` (sheet/row_label/period), but this contract does not require attaching them to `Evidence` — that is an extension decision for whichever consumer needs it (see §9).

**FTE** — no relationship; FTE operates on temporal column classification, entirely orthogonal to per-row structural classification.

**FRU (`fru_sign_convention_detector.py`)** — the **direct, proven, current consumer**. FRU's existing inline "structural rollup exclusion" (its own docstring's words) is, precisely, an unnamed, single-purpose implementation of exactly `derivation_status` — it already checks "is this row's period-column cell a formula" and excludes it from `charge_values` if so. FRU does **not** need `structural_role` at all — it only ever needed the `SOURCE_VALUE`/`DERIVED` distinction. This is named explicitly because it resolves §14's field-necessity test concretely: `derivation_status` has a real, live, already-implemented consumer; `structural_role`'s consumers (#2, #3) are future and not yet authorized.

**Knowledge Model** — **not needed by v0.** `structural_role`/`derivation_status` are near-fully deterministic per file (formula-mode evidence, when available, resolves them without needing organisational memory) and are re-derived correctly on every read — nothing here is worth remembering per Entity. Challenged directly (mission §12): could an organisation's *habit* of exporting with or without formulas be worth remembering, to pre-empt Case F/L's `UNKNOWN` degradation? Possibly, in principle — but this would be a memory about **the shape of an organisation's exports over time**, a distinct, future, terminology/pattern-flavoured capability (#5-adjacent in the profession-model document), not something Observation Structure v0 itself needs to persist or consume. **No new `SUBJECT_VALUE_REGISTRY` entry, no new KnowledgeModel subject.**

**Epistemic Dialogue — not needed by v0, deliberately.** The one plausible trigger (mission §13's own example: *"I cannot determine whether 'Operating Contribution' is a subtotal or an independent KPI"*) is directly answered by §3.1's tolerance rule: both candidate roles (`AGGREGATE`, `KPI`) carry the identical downstream consequence (arithmetically not independent, via `derivation_status` alone), so resolving the ambiguity with certainty is never required for v0's own purpose. **v0 remains fully deterministic, with `UNKNOWN`/coarser-role degradation as its only uncertainty behaviour — no human question is authorised or required by this slice.**

## 8. Primitives future #2 (Economic Nature) / #3 (Reporting Structure) will need — not implemented here

Per mission §11 (do not implement #2/#3, but ensure v0 supplies the right primitives): future #2 needs to know whether a row is `LEAF` before attempting to classify its economic nature "as itself" (an `AGGREGATE`'s nature is derivative of what it aggregates — a different question). Future #3 needs the `SECTION_HEADER` boundary signal (§3.1) to reconstruct where one statement/section ends and another begins, and would benefit from the formula reference-extraction byproduct named in §5.3 (the parent/child edges a `DERIVED` observation's formula implies) to reconstruct hierarchy — **not exposed as a required v0 output field** (§12 — no current consumer), documented here only as a forward-compatible extension point so a future implementer does not have to rediscover it.

## 9. Downstream responsibility and persistence — challenged, rejected

Hypothesis tested (mission §9): is the classifier's output an ephemeral projection, deterministic metadata attached to Evidence, a persisted fact, or something else? **No case examined in this mission required persistence.** The output is a **pure, ephemeral projection** over a parsed workbook — recomputed fresh on every read, exactly like `fte_minimal.py`'s own precedent ("a pure projection over data that already exists... no new persistent object"). It may later be attached as optional metadata on a captured `SourceReference` if a future consumer needs traceability of the classification itself, but that is an extension, not a v0 requirement. **This classifier must never become a new canonical Evidence Ledger or a competing source of truth** — it answers a narrower, purely structural question than Evidence does, and produces no fact Evidence itself is responsible for capturing.

## 10. Output contract — fields tested, one field, one convenience derivation, one deferred extension point

| Field | Professional question | Current consumer | Derivable from another field? | UNKNOWN behaviour | Axis-independent? | Deterministic? | In v0? |
|---|---|---|---|---|---|---|---|
| `structural_role` | What role does this line play in the report? | Future #2/#3 only (not FRU) | No (§2, row 163 proof) | First-class `UNKNOWN` value | Row axis proven; column axis unconfirmed (§4) | No — often `HYPOTHESIS` tier | **Yes** — see reasoning below |
| `derivation_status` | Was this value computed from other observations in this file? | **FRU, today, already** (§7) | No | First-class `UNKNOWN`, plus distinct `NOT_APPLICABLE` for no-value cells | Yes, cleanly (§4) | Yes, near-fully (limited only by the §5 parser gap) | **Yes** |
| independence (arithmetic) | Is this safe to sum into a total? | Would be FRU, if exposed | **Yes** — pure function of `derivation_status` | N/A | Yes | Yes | **No** — not a stored field; expose as a convenience derivation (`derivation_status != DERIVED`) if a consumer wants it, never a third dimension. |
| `derived_from` (reference set of cells a `DERIVED` observation points to) | Which other observations does this depend on? | Future #3 only | No, but cheaply co-extractable with `derivation_status` (§5.3) | Empty/absent | Yes, conceptually | Yes, to the extent formula parsing succeeds (partial) | **No — deferred.** No current consumer (§7); named as a documented extension point, not built now, per "no field without a current falsifiable need." |

**On including `structural_role` despite having no current consumer:** applying the field-removal rule strictly would argue for shipping `derivation_status` alone (FRU's actual, proven need) and nothing else. This contract recommends including `structural_role` anyway, for two stated reasons, not as a silent exception to the rule: (1) the marginal cost is low — both fields are computed from the same single row scan of the same workbook; (2) shipping `derivation_status` alone would re-encode exactly the same terminology confusion this mission was convened to resolve (a classifier answering "is this derived" while a document elsewhere in canon calls the same concept "structural role") — recording both, correctly separated, in one place prevents a second near-identical mission later. This is stated as a judgment call, not asserted as a mechanical consequence of §14's own test.

**Confidence vocabulary:** both fields reuse the existing `FACT`/`STRONG_INFERENCE`/`HYPOTHESIS`/`UNKNOWN` tiers (`ConfidenceContract`, already canonical) — no new scoring engine, no fabricated numeric confidence, per Constitution Article XII (single representation) and the mission's explicit instruction (§15).

## 11. Real Phidani Golden Case

| Row | Code | Caption | Formula (col C) | `structural_role` | `derivation_status` |
|---|---|---|---|---|---|
| 134 | `620250` | Rémunération brute employés | `863540.12` (literal) | `LEAF` (STRONG) | `SOURCE_VALUE` (STRONG) |
| 161 | `62` | C. Rémunérations - Charges Sociales - Pensions | `=SUM(C134:C160)` | `AGGREGATE` (STRONG) | `DERIVED` (STRONG) |
| 165 | `60/64` | II Coût Ventes - Prestations | `=C34+C132+C161+C163+C164` | `AGGREGATE` (STRONG — compound-row rule, §3.1) | `DERIVED` (STRONG) |
| 3 | *(none)* | Compte de résultats | *(no value)* | `SECTION_HEADER` (STRONG) | `NOT_APPLICABLE` (STRONG) |
| 163 | `630` | D. Amortissements - Réductions Valeur | `=C162` | `AGGREGATE` (STRONG) | `DERIVED` (STRONG) — **the single-cell-passthrough case, the central falsifier of the original one-enum model (§2)** |
| 133 | `B1` | Marge brute d'exploitation (EBITDA) | `=C35-C132` | `KPI` (HYPOTHESIS — Phidani's `"B"`-code family is this report template's own convention, not a universal signal) | `DERIVED` (STRONG) — "derived from derived" (row 35 and row 132 are themselves `DERIVED`), a real shape, not separately flagged as its own value (§3.2) |
| — | — | *(conceptual, no-formula-export adversary — not present in Phidani)* | *(literal number where a formula would normally be)* | `HYPOTHESIS`-tier `AGGREGATE` at best (caption/position only), or `UNKNOWN` | `UNKNOWN` (honest, §6) |

Row/column axis: monthly leaf columns and `"YEAR YYYY"` aggregate columns are real and were identified (profession-model mission §3), but are **excluded from this Golden Case's required assertions** per §4's scope decision — named as a future test, not a v0 requirement.

## 12. Adversarial fixtures (defined, not implemented — mission §17)

A–P mapped against §3's semantics: **A** (leaf/direct) → `LEAF`+`SOURCE_VALUE`, both STRONG. **B** (aggregate/SUM) → `AGGREGATE`+`DERIVED`, both STRONG. **C** (derived single-cell reference) → the row-163 shape, real-file-grounded, not purely synthetic. **D** (derived ratio KPI) → **purely synthetic** (confirmed: no division/ratio formula exists anywhere in Phidani — verified directly, not assumed), `DERIVED`+`KPI` (HYPOTHESIS role). **E** (section header/no value) → `SECTION_HEADER`+`NOT_APPLICABLE`, both STRONG, real-file-grounded (rows 3/369). **F** (hardcoded subtotal, no formula) → `derivation_status = UNKNOWN`, `structural_role` at best `HYPOTHESIS` — the central proof of §6's no-fabrication discipline. **G** (formula/value missing) → `NOT_APPLICABLE`, not `UNKNOWN` — real analog exists (row 256, `"B3 XIII Résultat à affecter"`, blank in some period columns). **H** (formula contradicts caption) → resolved as the row-163 case, not a new failure mode: `derivation_status` trusts the formula; `structural_role` trusts caption/position; the two are allowed to point at different underlying mechanisms without being reconciled into one value (§2's whole point). **I** (row order misleading) → already proven and implemented (Correction 2, prior mission) — `derivation_status` must never be inferred from position/order alone. **J/K** (annual aggregate / monthly leaf columns) → deferred, column axis (§4). **L** (materialised ERP export, whole-file) → file-scale version of F; a **mixed** file (some rows formula-driven, others materialised) is a realistic scenario not covered by Phidani (100% formula-consistent) — named as untested. **M** (zero-valued leaf) → `SOURCE_VALUE`, not `NOT_APPLICABLE`/`UNKNOWN` — a true zero is a fact (§3.2, Article III). **N** (blank future cell) → `NOT_APPLICABLE`. **O** (malformed account code — the real `"72.44444444444444"` corruption found in the profession-model mission) → **does not affect either field** — neither depends on successful account-code parsing; stated as a positive, empirically-grounded robustness property of this design. **P** (mixed P&L + balance-sheet sheet) → v0's `SECTION_HEADER` output is exactly the raw material a future #3a would consume to find the boundary; v0 itself does not need to know which statement a row belongs to.

## 13. IN

- Row-axis `structural_role` classification: `LEAF` / `AGGREGATE` / `KPI` / `SECTION_HEADER` / `UNKNOWN`, confidence-tiered (`STRONG_INFERENCE`/`HYPOTHESIS`/`UNKNOWN`).
- Row-axis `derivation_status` classification: `SOURCE_VALUE` / `DERIVED` / `NOT_APPLICABLE` / `UNKNOWN`.
- Extraction as a small, reusable, pure module (out of `fru_sign_convention_detector.py`'s inline logic), consumed by FRU (replacing its current inline exclusion with a call to the extracted primitive, behaviour-preserving) and available, undocumented-as-required-but-available, to future #2/#3 work.
- The Golden Case and adversarial fixtures in §11/§12, as a test contract (not yet written as executable tests).

## 14. OUT

- Column-axis classification (§4 — deferred, vocabulary kept forward-compatible).
- `derived_from` reference-set extraction as a required output field (§10 — deferred extension point).
- Any economic-nature or reporting-structure semantic classification (#2/#3 — explicitly untouched).
- Any arithmetic cross-check fallback for the no-formula case (§6 — explicitly rejected for v0).
- Resolving the `file_parser.py` formula-mode access gap (§5) — this contract names the blocker; it does not decide whether the v0 implementation performs its own independent file read (as FRU already does) or waits for `file_parser.py` to be extended. **This is the one open implementation-time decision this contract leaves unresolved on purpose.**
- Any new persistence, migration, Supabase interaction, or LLM call.
- KnowledgeModel or Epistemic Dialogue integration (§7 — neither needed).
- Merged-cell and bold/outline corroborating signals as *required* evidence (named as available in §5, not required for v0's minimum viable classification, since formula-presence alone already resolves `derivation_status`, and caption/position alone already resolves most of `structural_role`, at the confidence tiers stated in §11's Golden Case).

## 15. Minimum code impact

One new, small, pure module (e.g. `backend/services/observation_structure.py`), factoring out the row-scan logic already present, unnamed, inside `fru_sign_convention_detector.py::detect_expense_sign_convention_from_workbook`'s loop (§7 of that module's docstring, "STRUCTURAL, NOT SEMANTIC, ROLLUP EXCLUSION"). `fru_sign_convention_detector.py` would then call the extracted primitive instead of performing its own inline formula check — a behaviour-preserving refactor for FRU, not a behaviour change. No change to `file_parser.py`, `evidence_capture.py`, `evidence_ledger_service.py`, `knowledge_model_service.py`, or `epistemic_dialogue_service.py` is required by this slice (the §5 parser-gap decision, if it lands on "extend `file_parser.py`," would be the one exception — explicitly out of this contract's scope, per §14).

## 16. Test contract

Golden Case (§11, real Phidani rows 3/133/134/161/163/165 plus the one conceptual no-formula adversary) as the primary regression anchor; adversarial fixtures A–P (§12) as the synthetic matrix, mirroring the structure already established for FRU's own `TestWorkbookAdapterSynthetic`/`TestThresholdBoundary` test classes; an explicit robustness test reproducing the real corrupted-code row (Case O) to prove the classifier tolerates it; an explicit test proving `structural_role` and `derivation_status` are computed and asserted **independently** for row 163 (the case that falsified the original one-enum model) — this specific test is the single most important regression guard this contract requires, since a future refactor that silently re-merges the two dimensions would not be caught by any other test in this contract.

## 17. Blockers

1. **The `file_parser.py` formula-mode access gap (§5, §14)** — the one substantive open decision before coding: independent second read (FRU's current pattern, tolerated debt) vs. extending the shared parser (larger, not authorized here).
2. **Column-axis scope decision (§4)** — not a blocker to shipping row-axis v0, but a real, named gap between what the profession-model document originally implied ("Row/Column...") and what this contract actually authorizes (row only).
3. No other blocker identified — Evidence, FTE, KnowledgeModel, and Epistemic Dialogue are all confirmed not required (§7).

## 18. Implementation recommendation

**GO, row-axis only, both fields, with blocker 1 resolved at implementation time (not before).** This is the smallest slice that (a) removes the real, already-identified coupling preventing #2/#3 from reusing FRU's inline logic, (b) is falsifiable against a real Golden Case without fabricated confidence, (c) corrects a real domain modelling error (the one-enum conflation) before it propagates into a second implementation, and (d) adds no new architecture, persistence, or LLM dependency.

---

**OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT ESTABLISHED. NO CODE WRITTEN.**
