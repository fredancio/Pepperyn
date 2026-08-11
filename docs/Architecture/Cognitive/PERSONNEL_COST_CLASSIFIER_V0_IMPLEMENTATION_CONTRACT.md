# PERSONNEL_COST_CLASSIFIER_V0_IMPLEMENTATION_CONTRACT.md

**Status:** IMPLEMENTATION CONTRACT — established, not yet implemented, not yet promoted.
**Branch:** `architecture/personnel-cost-classifier-v0-contract-2026-08-11` (not merged).
**Precedes:** `ECONOMIC_MEANING_NEXT_ATOMIC_CAPABILITY_ARBITRATION.md`, commit `9b28eec` (unmerged), which selected this exact slice — Candidate A, corrected to a single-concept classifier.
**Scope:** one professional responsibility — form the narrowest defensible hypothesis about whether one P&L leaf observation is `PERSONNEL_COST`, from file-internal evidence alone, with an honest `CONTRADICTION` state distinct from `UNKNOWN`. Nothing else.

---

## 0. Entry gate

Verified clean `main` at `500725b`; branched directly. Re-read in full for this contract, not from memory: `ECONOMIC_MEANING_NEXT_ATOMIC_CAPABILITY_ARBITRATION.md` (this session, commit `9b28eec`); `ECONOMIC_MEANING_REASONING_PROFESSION_MODEL.md` and `HYPOTHESIS_REPRESENTATION_DESIGN_REVIEW.md` (both still unmerged, read via `git show` from their own 2026-08-10 branches, exactly as in the arbitration mission — their non-canonical status is unchanged since then, re-confirmed by `git branch --contains`); `CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md`; `FINANCIAL_FILE_UNDERSTANDING_PROFESSION_MODEL.md`; `OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md`; `EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md`; `KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md`. `CANONICAL_FINANCIAL_DOCTRINE_FOUNDATION.md` confirmed, again, to exist only on its own unmerged 2026-08-10 branch, explicitly superseded by the now-canonical Doctrine v0 contract (which says so itself) — no new content needed from it. `PEPPERYN_CONSTITUTION.md` and `PRODUCT_BOARD.md` re-read; nothing in either conflicts with this contract's scope.

Re-inspected directly, this session: `fru_sign_convention_detector.py`'s `Candidate(value: Optional[str], tier: str)` — unchanged since the arbitration mission (three tiers, no evidence lists). `concept_vocabulary.py`, `financial_doctrine.py`, `formula_reference_extractor.py`, `observation_structure.py`, `formula_evidence.py` — unchanged, zero external consumers confirmed again by `grep`. `epistemic_dialogue_service.py`, `knowledge_model_service.py` — function inventories unchanged. **No documentation/implementation disagreement found; nothing requires a STOP.**

Re-inspected real `Phidani.xlsx` again, fresh, including cell-level formatting (bold, indent) for rows 134–161, not previously checked — see §14 for what this changed.

**[CORRECTED 2026-08-11 — Epistemic Semantics Adversarial Review, independent, targeting this contract's own commit `5dfde8c`].** The review found a real, load-bearing internal contradiction between §7 (as originally written) and §12: §7 required `CONTRADICTION` to hold when both sides are "independently sufficient to support `STRONG_INFERENCE` on their own," while §12 (row 151) separately concluded that the *same kind* of evidence — `ACCOUNT_CODE_FAMILY` + `STRUCTURAL_POSITION` agreeing, uncorroborated by caption — is only `HYPOTHESIS`-grade, **not** independently `STRONG_INFERENCE`-grade. Applied consistently, this would have made row 122 (the Golden Case) fail its own `CONTRADICTION` bar, since neither side of row 122 is corroborated by a second signal family either. **§6, §7, §9, §11 (formerly numbered as row 52's section), §12, §13, §17, §18, and §28 are corrected below** to a single, uniform, consistently-applied rule — "signal families," not "independent `STRONG_INFERENCE`-worthiness per side" — with no change to any Golden Case's expected outcome (row 122 remains `CONTRADICTION`, row 151 remains `HYPOTHESIS`, row 134/52 remain `STRONG_INFERENCE`) but a materially different, now-consistent justification for each. See the corrected sections themselves for the exact reasoning; this note exists so the correction is not silently invisible in a diff.

## 1. Professional responsibility

Not: *"assign one financial category to every row."* It is: *"form the narrowest defensible hypothesis about whether this observation represents `PERSONNEL_COST`, while preserving supporting evidence, contradicting evidence, and genuine uncertainty — and refusing to answer when the file does not honestly support an answer."* Three possible values (`PERSONNEL_COST`, `OTHER`, `None`), four possible epistemic tiers (`STRONG_INFERENCE`, `HYPOTHESIS`, `CONTRADICTION`, `UNKNOWN`), never a forced exhaustive classification.

## 2. Exact v0 scope

**IN:** a pure, deterministic kernel classifying one P&L leaf observation (already known, by caller precondition, to be inside the P&L and to be a leaf — §11) as `PERSONNEL_COST`/`OTHER`/unclassifiable, using account-code family, structural position relative to already-known aggregate ranges, parent-caption text, and the leaf's own caption text — nothing else.

**OUT (§34, unchanged from the mission brief, restated because every item was checked, not assumed):** general Economic Meaning engine; a revenue or operating-expense classifier; a full payroll taxonomy; multilingual semantic model; fuzzy logic; numeric confidence or probability; Bayesian reasoning; any LLM call; embeddings; ontology expansion; any change to `financial_doctrine.py`'s registry or logic; a Reporting Structure implementation; `KnowledgeModel` integration; `Epistemic Dialogue` integration; a materiality engine; persistence; database; Supabase; API/UI; a generic `Hypothesis` framework; a multi-concept classifier.

## 3. Candidate extension — re-inspected, extended, not replaced

Current `Candidate` (`fru_sign_convention_detector.py`, re-confirmed unchanged, §0): `value: Optional[str]`, `tier: str ∈ {STRONG_INFERENCE, HYPOTHESIS, UNKNOWN}`. Cannot represent: two independently strong, opposing pieces of evidence (collapses to `UNKNOWN`, indistinguishable from no evidence at all — the exact defect the arbitration mission's Golden Case, §12, exists to expose).

**Extension, each field justified against a real case, none accepted blindly:**

```python
@dataclass(frozen=True)
class EvidenceItem:
    source_type: str       # "ACCOUNT_CODE_FAMILY" | "STRUCTURAL_POSITION" | "PARENT_CAPTION" | "CAPTION_LEXICAL"
    source_pointer: str    # cell coordinate reference only, e.g. "C122" — never a copy of caption/formula text
    origin: str             # "DETERMINISTIC" | "INTERPRETIVE" — every v0 signal is DETERMINISTIC (§7)

@dataclass(frozen=True)
class Candidate:
    value: Optional[str]                             # "PERSONNEL_COST" | "OTHER" | None
    tier: str                                          # "STRONG_INFERENCE" | "HYPOTHESIS" | "CONTRADICTION" | "UNKNOWN"
    supporting_evidence: tuple[EvidenceItem, ...] = ()   # evidence for PERSONNEL_COST specifically
    contradicting_evidence: tuple[EvidenceItem, ...] = ()  # evidence for a positive non-personnel (OTHER) claim
```

`CONTRADICTION` is a new tier value on the *existing* field, not a new field and not a new value in a separate enum — `tier` remains one string field throughout. No new top-level class beyond `EvidenceItem` (a small, typed record, not a generic `Evidence` framework). **This is the exact, bounded extension the prior arbitration named as required (§7 there) — nothing broader is built here.**

**Where does this live?** Not inside `fru_sign_convention_detector.py` (a different subject, `EXPENSE_SIGN_CONVENTION`, would be a poor fit for `PERSONNEL_COST` logic) and not duplicated. Since Economic Meaning is now a second real consumer of the `Candidate` shape (the condition the unmerged Hypothesis Representation Design Review itself named as the trigger for promotion, §26 there, independently re-confirmed valid here), `Candidate` and `EvidenceItem` should be promoted into their own small, shared module — recommended path: `backend/services/candidate.py` — imported by both `fru_sign_convention_detector.py` (updated to import, not redefine, in a future, separate mission — **not touched by this contract**, named as a reservation, §33) and the new classifier module (§30). This is a minimal relocation, not new architecture.

## 4. EvidenceItem contract

Per field, tested against "which real case fails without it" (mirroring the already-proven method from the unmerged design review):

- **`source_type`** — required. Without it, `OTHER`'s load-bearing rule (§6) and explainability cannot distinguish "a specific caption claim" from "a generic structural fact."
- **`source_pointer`** — required, reference only. Never duplicates Evidence Ledger / Observation Structure content — points back to a real cell coordinate for audit.
- **`origin`** — required, but degenerate in v0: every signal is `DETERMINISTIC` (no LLM, §26). Kept because a future slice (open-vocabulary caption matching via LLM, explicitly deferred) would need to distinguish it, and adding the field now costs nothing while retrofitting it later would touch every existing evidence item.
- **No stored numeric strength anywhere on `EvidenceItem`** — strength is not a property of the item at all; it is a property of which of the two named **signal families** (§6) the item's `source_type` belongs to, and the tier is computed from family-presence/agreement (§7), never stored as free-floating data on the item itself — per the mission's own explicit prohibition and the already-established discipline from Doctrine v0 and the unmerged design review alike.
- **No `observed_value`/raw text field** — evidence items reference; they do not duplicate. The caption string itself lives in Evidence Ledger / the raw workbook; `source_pointer` is enough to look it up.
- **`relation` (supports/contracts) is not a stored field** — it is which *list* (`supporting_evidence` vs. `contradicting_evidence`) an item is placed in, avoiding a redundant field that would only ever agree with its own container.

## 5. OTHER semantics — the load-bearing rule

**OTHER never means "not classified as PERSONNEL_COST."** `OTHER` is legitimate only when `contradicting_evidence` contains at least one item that is itself **positive, specific evidence for a non-personnel interpretation** — not merely the absence of personnel evidence. Concretely: a caption like `"Frais de téléphone"` (row 52) is positive evidence for a specific, nameable, non-personnel economic reality (a telecommunications utility cost) — this earns `OTHER`. A caption like `"Frais divers"` (row 151) asserts nothing positive about *any* category — its absence of personnel-specificity does **not**, by itself, license `OTHER`; it only fails to corroborate `PERSONNEL_COST` further. **[CORRECTED] Formal rule, restated under §6/§7's family model: `value = OTHER` requires at least one signal family (§6) to be present and to contribute a specific, non-residual claim toward `OTHER` — the same specificity bar `PERSONNEL_COST` must clear (§7's `HYPOTHESIS` row, mirrored), never a lower one merely because "personnel" was ruled out.** `OTHER` at `STRONG_INFERENCE` grade (row 52) requires *both* families present and agreeing on `OTHER`, symmetric with how `PERSONNEL_COST` reaches `STRONG_INFERENCE` (row 134) — never a shortcut where `OTHER` needs less corroboration than `PERSONNEL_COST` does. This is enforced by a dedicated test (§31 item 1) and is the single most falsifiable claim in this contract (§33).

## 6. Signal families — where an EvidenceItem's strength actually lives [CORRECTED, formalized]

**Strength does not live on an individual `EvidenceItem`, and it does not live on an individual `source_type` either.** It lives at the level of exactly **two named signal families**, each family being present or absent as a whole, never partially:

- **`STRUCTURAL` family** — the union of `ACCOUNT_CODE_FAMILY`, `STRUCTURAL_POSITION`, and `PARENT_CAPTION`. These three `source_type`s are correlated (all three derive from "where, physically and codewise, does this leaf sit"), so they are **counted as one family, never as up to three independent votes** — the exact "correlated signals inflated into a fake majority" risk named in the prior arbitration (§7 there) and re-applied here as a first-class rule, not an ad hoc aside. The family is *present* if at least one of the three sub-signals is available and none of the available ones disagrees with the others; it is *absent* only if none of the three is available (§14 covers the degraded sub-cases: missing/malformed code, absent parent caption — the family can still be present via the remaining sub-signals).
- **`LEXICAL` family** — `CAPTION_LEXICAL` alone. Present only when the leaf's own caption matches a recognized keyword (§13/§15); absent otherwise (a non-specific caption like `"Frais divers"` produces **no item at all**, not a weak item — there is no third "present but weak" state anywhere in this v0 model, §18).

**This directly answers where strength resides: not on the item, not on the `source_type` in isolation, but on which of these exactly two families is present, and whether the families that are present agree.** No other grouping is needed or built in v0 — every real and synthetic case in this contract is fully explained by a two-family model.

## 7. UNKNOWN and CONTRADICTION semantics — one uniform rule, corrected [CORRECTED — resolves the §6/§12 inconsistency named at entry gate]

`Candidate.tier` is a pure function of **how many of the two families (§6) are present, and, if both are present, whether they agree** — the single, uniform rule replacing the two previously-inconsistent bars (a flawed `CONTRADICTION`-only bar, and a separately-stated `STRONG_INFERENCE` rule that silently used a different, stricter standard for the same evidence):

| `STRUCTURAL` family | `LEXICAL` family | Relationship | `tier` |
|---|---|---|---|
| absent | absent | — | `UNKNOWN` |
| present | absent | — | `HYPOTHESIS` |
| absent | present | — | `HYPOTHESIS` |
| present | present | agree | `STRONG_INFERENCE` |
| present | present | disagree | `CONTRADICTION` |

**`UNKNOWN`** (`value=None`): both families absent — no code, no position, no parent caption, no recognized caption keyword. Never a forced choice, never `OTHER`-by-default (§5).

**`HYPOTHESIS`**: exactly one family present, nothing to disagree with it — an honest "uncorroborated, unopposed" state, whichever single family produced it (row 151, §12, is the `STRUCTURAL`-only real instance; a `LEXICAL`-only instance is structurally possible, §28, not yet observed in the Golden Case set).

**`STRONG_INFERENCE`**: both families present and agreeing — this is the correct, sole meaning of "two or more independently-agreeing signals": it always means *two families*, never merely two sub-signals within the same family (row 134's code+position+caption all agreeing is two families — `STRUCTURAL` and `LEXICAL` — not three independent votes; the three-item `STRUCTURAL` sub-signals are still counted once, per §6).

**`CONTRADICTION`** (`value=None`, §8): both families present, and they disagree. **Corrected, load-bearing point:** this does **not** require either family to be "independently `STRONG_INFERENCE`-worthy on its own" — no family, by itself (uncorroborated by the other), is ever `STRONG_INFERENCE`-grade in this model; `STRONG_INFERENCE` is *defined* as requiring both families to agree, so no single family could ever satisfy that bar alone without contradicting its own definition. The correct, consistent bar for `CONTRADICTION` is simply: **both families are present** (each contributing at least one specific, non-residual claim, per §5's own specificity bar) **and they point to different values.** This is exactly what makes row 122 a real `CONTRADICTION` (`STRUCTURAL` present, pointing `OTHER`; `LEXICAL` present, pointing `PERSONNEL_COST`) without requiring either family to clear a bar that, by the table above, nothing can clear alone. A categorical (family-presence, family-agreement) rule — no numeric threshold anywhere. **A status, not a third economic value:** `tier=CONTRADICTION` is never stored as if it were a member of the same vocabulary as `PERSONNEL_COST`/`OTHER` — it is a value of the separate `tier` field only (§3), enforced structurally by §28's impossible-state table.

**Reservation, named explicitly:** this two-family model has no room for a case where *three or more* independent, uncorrelated signal families might someday exist (e.g., if a future slice added a genuinely independent third evidence source unrelated to either `STRUCTURAL` or `LEXICAL`) — such a case, with e.g. 2-agree-vs-1-disagree, is not covered and would require revisiting this table, not merely re-applying it. Not present in any Golden Case in this contract; recorded in §34.

## 8. Contradiction-value arbitration (§29) — resolved, not chosen by convenience

Four options were named: (A) `value=None`; (B) always privilege `PERSONNEL_COST`; (C) hold both competing values explicitly; (D) other.

**(B) rejected outright** — silently privileging one side defeats the entire point of representing a contradiction; it is a disguised, hardcoded tie-breaker, exactly the "confidence average" / silent-resolution failure mode §33 forbids in spirit.

**(C) considered seriously, not dismissed.** For future dialogue (§24), a targeted contradiction question needs to reference *both* competing interpretations by name. Tested whether a dedicated `competing_values: tuple[ConceptId, ...]` field is required to support this. **Finding: in this specific, closed, two-value vocabulary (`PERSONNEL_COST`/`OTHER` only, per the arbitration mission's own scope correction), it is not** — the two competing values are already fully and unambiguously reconstructable from which evidence list is non-empty (`supporting_evidence` non-empty ⇒ the `PERSONNEL_COST` side; `contradicting_evidence` non-empty ⇒ the `OTHER` side). A `competing_values` field would only ever restate `("PERSONNEL_COST", "OTHER")` as literal strings whenever `tier == CONTRADICTION` — redundant, not informative, in a two-value vocabulary.

**(A) selected: `value = None, tier = CONTRADICTION`, both evidence lists populated.** Informationally equivalent to (C) for this slice, and smaller — satisfies the mission's own "do not overbuild a state machine unless needed" (§30) without losing anything a two-valued classifier can lose. **Named reservation, not a hedge:** this equivalence is a property of the *two-value* scope specifically. If a future slice widens the vocabulary beyond `PERSONNEL_COST`/`OTHER` (out of scope here, §2), option (A) would start silently losing information that (C) would preserve, and the arbitration would need to be redone, not merely re-applied — recorded here so it is not forgotten.

## 9. Golden Case: row 122 — reconstructed from the real workbook, not hardcoded

Real coordinates (re-verified this session): `A122=618000`, `B122="Rémunération Brute Alain Corchia"`, `C122=60000` (literal, no formula). Position: inside row 132's `SUM(C36:C131)` range (confirmed: `_expand_range` on `"C36:C131"`, already implemented in `formula_reference_extractor.py`, would include `C122`). Parent caption: row 132, `"B. Services — Biens Divers"`.

**Evidence extracted by the reusable signal rules (§13), not by row-specific logic:**
- `ACCOUNT_CODE_FAMILY` on `"618000"` → prefix `"61"` → the code-family rule (§13) maps prefix `61` to a moderate, non-personnel-family signal → contributes to `contradicting_evidence`.
- `STRUCTURAL_POSITION` on `C122` → inside `C36:C131` (the `61`-aggregate range), **not** inside `C134:C160` (the `62`-aggregate range) → contributes to `contradicting_evidence`.
- `PARENT_CAPTION` on `"B. Services — Biens Divers"` → no personnel keyword recognized (§13's closed keyword list) → contributes nothing positive, does not oppose either.
- `CAPTION_LEXICAL` on `"Rémunération Brute Alain Corchia"` → recognized personnel keyword `"Rémunération"` combined with a personal-name pattern → contributes to `supporting_evidence`.

**[CORRECTED]** `ACCOUNT_CODE_FAMILY`+`STRUCTURAL_POSITION` together constitute the `STRUCTURAL` family (§6), present and pointing `OTHER`-direction; `CAPTION_LEXICAL` constitutes the `LEXICAL` family (§6), present and pointing `PERSONNEL_COST`-direction. Both families present, disagreeing → `CONTRADICTION`, per §7's corrected table — **this does not require either family to independently reach `STRONG_INFERENCE` alone** (nothing does, by §7's own definition); it requires only that both families are present, each contributing a specific claim (§5's own specificity bar — code+position is a real, positive structural fact about aggregate membership, not a residual one, exactly like row 52's structural signal; caption is a real, specific personnel claim, exactly like row 134's). **Expected: `value=None, tier=CONTRADICTION`, `supporting_evidence=(CAPTION_LEXICAL@C122,)`, `contradicting_evidence=(ACCOUNT_CODE_FAMILY@A122, STRUCTURAL_POSITION@C122)`.** Rows 125/128 are structurally identical (same code family, same range, same caption pattern) — kept as corroborating repeats in the test suite, not independent Golden Cases.

## 10. Positive control: row 134

`A134=620250`, `B134="Rémunération brute employés"`, `C134=863540.12`, inside `C134:C160` (the `62`-aggregate, itself directly containing this leaf, not merely near it), parent caption `"C. Rémunérations — Charges Sociales — Pensions"`.

**[CORRECTED] Grounded, not by code or caption alone:** the `STRUCTURAL` family (code-family `62` + structural position inside the `62` range, §6) is present and points `PERSONNEL_COST`; the `LEXICAL` family (caption `"Rémunération brute employés"`, recognized personnel keyword) is present and agrees. **Both families present, agreeing → `STRONG_INFERENCE`**, per §7's corrected table — not "three independently-agreeing signals" (code+position is one family, not two). **Expected: `value=PERSONNEL_COST, tier=STRONG_INFERENCE`**, all three `EvidenceItem`s in `supporting_evidence` (two from the `STRUCTURAL` family, one from `LEXICAL`), `contradicting_evidence=()`.

## 11. Negative control: row 52

`A52=612100`, `B52="Frais de téléphone"`, `C52=1039.54`, inside `C36:C131` (the `61`-aggregate), parent caption `"B. Services — Biens Divers"`.

**[CORRECTED] Positive, specific evidence for non-personnel, named exactly (§5):** the `STRUCTURAL` family (code `61`-family + position inside `C36:C131`, §6) is present and points `OTHER`; the `LEXICAL` family (`CAPTION_LEXICAL` recognizing `"téléphone"` as a specific, non-personnel utility/communication-cost term — §13's closed keyword list, symmetric: it contains a small number of recognized *non*-personnel terms as well as personnel terms, both Golden-Case-scoped, never a general dictionary) is present and agrees. **Both families present, agreeing → `STRONG_INFERENCE`**, per §7's corrected table. **Expected: `value=OTHER, tier=STRONG_INFERENCE`**, all three items in `contradicting_evidence`, `supporting_evidence=()`. **This is not "OTHER because nothing said personnel" — it is OTHER because the `LEXICAL` family made a specific, positive non-personnel claim, exactly the bar §5 sets, corroborated by the `STRUCTURAL` family.**

## 12. Ambiguous case: row 151 — re-examined critically, not preserved by default

`A151=623150`, `B151="Frais divers"`, `C151=22926.45`, inside `C134:C160`, parent caption `"C. Rémunérations — Charges Sociales — Pensions"`.

**Fresh finding this session (§0):** re-checked cell formatting (bold/indent) for every row 134–161 — no differentiating signal exists (all leaves share identical formatting); ruled out as a source of additional evidence. **A candidate fifth signal, "neighbor consistency"** (rows 149–158 are all unambiguous personnel-benefit items in the same `623xxx` sub-family) **was seriously considered and explicitly rejected**: on inspection, every neighbor's own claim to being personnel-related derives entirely from the *same* structural-position fact (being inside `C134:C160`) already counted — treating neighbor consistency as a second, independent signal here would double-count one fact under two names, exactly the "correlated signals inflated into a fake majority" risk the arbitration document warned about (§7 there). **Rejected as a v0 signal for this reason, not merely unconsidered.**

**[CORRECTED, re-derived under §6/§7's formal model]** With that rejection, row 151 has exactly the `STRUCTURAL` family (§6) present — code-family + structural position, correlated, counted once — supporting `PERSONNEL_COST`; the `LEXICAL` family is **absent** (`"Frais divers"` matches no keyword and produces no `EvidenceItem` at all — not a weak item, simply nothing, exactly per §6's "no third present-but-weak state" rule). One family present, the other absent → **`HYPOTHESIS`**, directly from §7's table — no separate "independently sufficient" test is needed or applied; this is the same rule that gives row 134/52 `STRONG_INFERENCE` (both families present) and row 122 `CONTRADICTION` (both families present, disagreeing), now consistently applied rather than argued case-by-case. **Re-confirmed after critical review, not merely inherited from the prior arbitration.** **Expected: `value=PERSONNEL_COST, tier=HYPOTHESIS`**, `supporting_evidence=(ACCOUNT_CODE_FAMILY@A151, STRUCTURAL_POSITION@C151)` (one family, two sub-signal items, per §6), `contradicting_evidence=()`.

## 13. Allowed v0 signals — closed list, each Golden-Case-justified

| Signal | Family (§6) | Observes | May support | Cannot prove | Locale/enterprise dependence | Deterministic? |
|---|---|---|---|---|---|---|
| `ACCOUNT_CODE_FAMILY` | `STRUCTURAL` | 2-digit account-code prefix | A family-typical hypothesis (`62`→personnel-typical, `60`/`61`→services-typical) | Definitive category — row 122 is the direct, real counter-example | Belgian PCMN-specific; general mechanism | Yes, mechanically; the *family→hypothesis* mapping is a hand-authored, Golden-Case-scoped rule, not universal truth |
| `STRUCTURAL_POSITION` | `STRUCTURAL` | Row-range membership inside an already-known aggregate's summed range (reuses `formula_reference_extractor._expand_range`, no new range logic invented) | Which "family block" a leaf sits in | Economic nature of what is actually booked there (row 122) | Phidani's own layout; mechanism general | Yes |
| `PARENT_CAPTION` | `STRUCTURAL` | Caption of the nearest already-known aggregate a leaf rolls into | Corroborates `STRUCTURAL_POSITION` | Same limitation as position | French/Belgian captions here; mechanism general | Yes (lookup); text-to-signal mapping is the same small keyword rule as `CAPTION_LEXICAL` |
| `CAPTION_LEXICAL` | `LEXICAL` | The leaf's own caption text, against a small, closed, Golden-Case-scoped keyword list (personnel: "rémunération", "salaire", "personnel"-adjacent name patterns; non-personnel: "téléphone", "assurance", "loyer"-class utility/service terms) | A specific claim in either direction | Anything outside the closed list; language- and enterprise-specific naming | French-only in v0; explicitly named as fragile (§14 below) | Yes, mechanically; keyword *selection* is a hand-authored judgment, not a general NLP capability |

**Exactly two families, per §6 — the `Family` column above is not decorative, it is the load-bearing grouping every tier decision (§7) is computed from.**

**Explicitly excluded, considered and rejected, not merely omitted:** neighbor consistency (§12 — circular with `STRUCTURAL_POSITION`); formula reference/derivation (§8 of the mission — every Golden Case leaf is a literal value, not a formula; `derived_from`/`resolve_composition` answers a different question, composition of *derived* cells, irrelevant to classifying literal inputs); sign (already proven unreliable for this dimension, arbitration doc §5 row 160, not re-litigated here since no Golden Case in this contract turns on sign).

## 14. PCMN boundary — explicit prohibition, tested

**The contract prohibits, as an invariant: account code → canonical classification, treated as universal truth, anywhere in the kernel.** `ACCOUNT_CODE_FAMILY` and `STRUCTURAL_POSITION` alone (i.e. the `STRUCTURAL` family present, `LEXICAL` absent) never reach `STRONG_INFERENCE` — this is not a special rule, it falls directly out of §7's table: `STRONG_INFERENCE` requires *both* families present and agreeing, and `STRUCTURAL` alone is structurally incapable of satisfying that by definition. Tested explicitly: (a) code supports `PERSONNEL_COST`, caption agrees → row 134, both families present and agreeing, `STRONG_INFERENCE`; (b) code supports another family, caption strongly indicates personnel → row 122, both families present and disagreeing, `CONTRADICTION` — the central proof this prohibition is real, not decorative; (c) code missing → `STRUCTURAL` family may still be present via position/parent-caption alone, or absent entirely, degrading to `LEXICAL`-only evidence at best (row-151-shaped, `HYPOTHESIS`, §12/§18); (d) code malformed (mirrors the real row-234 corruption pattern found in prior discovery work) → treated identically to missing, degrades the same way, never crashes; (e) non-Belgian code (a code that does not parse to any recognized 2-digit prefix) → `ACCOUNT_CODE_FAMILY` sub-signal absent, same graceful degradation as (c)/(d), proving the prefix table is a lookup that fails closed, not a hard-coded assumption that every code is Belgian.

## 15. Caption boundary — explicit, scoped

No synonym dictionary. The keyword list in §13 is **exactly** the minimum needed by the Golden Cases in this contract (§9–§12) plus the two clearly-analogous negative-control terms already present in Phidani (`"téléphone"`, and — checked against the ablation set, §32 — no others are required). Any future addition requires a new, real Golden Case to justify it, per the same discipline already governing Concept Vocabulary's own closed registry. No LLM anywhere in this list's construction or application.

## 16. No-evidence case (synthetic, explicitly labeled)

Constructed observation: code = `None` (no account code cell), caption = `""` (empty string), not inside any known aggregate range. All four signals return nothing. **Expected: `value=None, tier=UNKNOWN`, both evidence lists empty. Never `OTHER`** — directly tests §6's own rule.

## 17. Both-families-present-and-disagreeing case [renamed from "strong/strong conflict" — corrected]

**[CORRECTED]** The mission's own naming ("strong/strong conflict") presupposed a per-side strength grading (each side individually "strong" or "weak") that §6/§7's corrected model does not use — there is no per-side strength scale, only family presence and agreement. Renamed accordingly: the real, load-bearing case is **both families present, disagreeing**. Real instance: row 122 (§9) — the `STRUCTURAL` family (code+position) present, pointing `OTHER`; the `LEXICAL` family (caption) present, pointing `PERSONNEL_COST`. Per §7's table, this is exactly and only `CONTRADICTION`. **`Candidate.value = None`, per §8's resolution, not a hedge — both evidence lists populated and readable.**

## 18. One-family-present and no-family-present cases, re-derived under the corrected model [CORRECTED — supersedes the original "strong/weak"/"weak/weak" framing]

**[CORRECTED, substantive]** Re-examining these two named cases under §6/§7's formal model exposes that the mission's original "strong/weak" and "weak/weak" labels described a **three-level strength scale (strong / weak-but-present / absent) that does not exist anywhere in this contract's actual evidence model.** An `EvidenceItem` is either produced (the signal matched something specific) or it is not produced at all (§6) — there is no intermediate "present but too weak to count" state. Correcting both cases:

**"Strong/weak" (synthetic) is, once re-examined, structurally identical to row 151 (§12) — one family present, the other absent — not a distinct third case.** A leaf coded `62xxxx`, positioned inside `C134:C160` (`STRUCTURAL` family present, personnel-direction), captioned `"Frais afférents"` (generic "related costs" — matches no keyword in §13's closed list, exactly like `"Frais divers"`) produces **no `LEXICAL` `EvidenceItem` at all**, not a weak one. **Expected: `HYPOTHESIS`** — directly from §7's table (`STRUCTURAL` present, `LEXICAL` absent), the identical rule and identical outcome as row 151, on a different concrete input. Kept in the test contract (§30 item 7) only to prove the rule generalizes beyond the one real Phidani instance, **relabeled here as a generality check, not a new tier boundary.**

**"Weak/weak" (synthetic) is, once re-examined, structurally identical to §16's no-evidence case — both families absent — not a distinct third case either.** Code = `None` (malformed/missing, §14 case d/e; `STRUCTURAL` family absent if position/parent-caption are also unavailable in this construction), caption = `"Divers"` alone (matches no keyword; `LEXICAL` family absent). **Expected: `value=None, tier=UNKNOWN`** — directly from §7's table (both families absent), the identical rule and identical outcome as §16, on a different concrete input. Kept in the test contract (§30 item 8) as a generality check, **relabeled here as such, not a new tier boundary.**

**Consequence, stated plainly (resolves the mission's own point 1, the apparent `UNKNOWN`-definition contradiction):** there is no real inconsistency between "`UNKNOWN` = no evidence" and "weak/weak → `UNKNOWN`" once "weak" is correctly understood as "absent" rather than "present but insufficient" — the two statements describe the same state. The original contract's use of the word "weak" to mean two different things (sometimes "absent," sometimes, confusingly, implying "present but insufficient" in §7's now-corrected text) is exactly what created the appearance of a contradiction; it is removed here, not merely re-explained.

## 19. Statement location — input precondition, not a new result value

**No new `NOT_APPLICABLE`-style enum value.** Per the mission's own stated preference, and per the precedent already used twice successfully in this engagement (Observation Structure v0, Doctrine v0), this classifier takes a **caller-supplied precondition**: the caller is responsible for invoking it only on coordinates already known to be P&L leaf observations (via Observation Structure v0's existing `structural_role` output, or via the same hand-scoped Golden-Case-coordinate pattern Doctrine v0 already used, contract §14 Pattern A). **Behavior on a non-leaf or non-P&L coordinate is explicitly undefined in v0** — not guaranteed safe, not tested, named as a reservation (§33), not silently assumed to degrade gracefully. Building an internal precondition check would require exactly the Reporting Structure / `#3a` capability this contract is barred from building (§20).

## 20. Reporting Structure dependency

Not built. Every signal in §13 operates on coordinates and ranges the caller already knows (mirroring `resolve_composition`'s own existing `root_cell`-supplied-by-caller pattern in `formula_reference_extractor.py`) — no statement-boundary detection, no automatic "am I in the P&L" check exists inside this module. If a future caller lacks that knowledge, this classifier is simply not usable yet for that input — no hidden fallback capability is implied or built.

## 21. Doctrine role — proven independent, not merely asserted

**`financial_doctrine.py` is never imported by the new classifier module.** Tested directly (planned, §31 item 16): an AST-based import-boundary test, identical in technique to the one already shipping in `test_financial_doctrine.py` (`ast.Import`/`ast.ImportFrom` module-name check, deliberately not a substring search, so a docstring that *names* Doctrine while explaining it is unused does not false-fail). This classifier's own hypothesis formation happens **entirely before and independently of** any Doctrine consultation — Doctrine, unmodified by this contract, may later consume this classifier's `PERSONNEL_COST` output as `classify_cell`'s real implementation (retiring the `§14 Pattern A` fixture named in the Doctrine v0 contract), but that wiring is **explicitly out of scope for this contract** (§2) and is not built here.

## 22. Concept Vocabulary role

The classifier **may** reference `concept_vocabulary.py` for the canonical `PERSONNEL_COST` identifier string (avoiding a second, independently-drifting literal), via `get_concept("PERSONNEL_COST")` or the module constant — an identity lookup only. **It must never call `match_concept`** — Vocabulary's lexical matcher is proven (existing tests) to reject `"Rémunération"`-shaped text, and calling it here would either do nothing (safe but pointless) or invite a future edit to Vocabulary's alias list to "make it work" (exactly the semantic-alias boundary violation the whole engagement forbids). Tested directly (§31 item 15): an AST-based check that `match_concept` is never called from the classifier module.

## 23. Enterprise Knowledge

Not integrated. Every Golden Case (§9–§12) and every synthetic case (§16–§18) resolves correctly from one file's own evidence — no case motivates persistence or entity memory. `KnowledgeModel`'s existing `SUBJECT_VALUE_REGISTRY` remains structurally compatible for a *future* slice (a confirmed `"618 = officer compensation, personnel-flavored"` fact, entity-scoped) — not built, not required, named only as a compatible future extension point, per the prior arbitration's own §11 finding, unchanged.

## 24. Epistemic Dialogue

Not integrated. Output shape is sufficient for a future mapping (`STRONG_INFERENCE`→ likely no question; `HYPOTHESIS`→ possible closed confirmation if material; `CONTRADICTION`→ a targeted contradiction question referencing both evidence lists directly, no new field needed per §8's resolution; `UNKNOWN`→ possible future open clarification) — this mapping is descriptive of future compatibility, not built, not authorized here.

## 25. Materiality

Out of scope entirely. The kernel answers "what do we believe," never "should a human be interrupted." No amount thresholds anywhere in this contract.

## 26. LLM

Zero. Every Golden Case and every synthetic adversarial case in this contract resolves deterministically. No Trust Gateway design, no prompt, no call.

## 27. Persistence

None. `Candidate` remains fully ephemeral, recomputed per read, exactly like every prior v0 slice in this engagement (`fte_minimal.py`, Observation Structure v0, Doctrine v0).

## 28. Minimum output contract — allowed value/tier combinations, impossible states rejected [cross-checked against §7's corrected 5-state table for completeness]

**Completeness check, done explicitly rather than assumed:** §7 defines exactly five raw states (both-absent, `STRUCTURAL`-only, `LEXICAL`-only, both-agree, both-disagree), mapping onto exactly four `tier` values (`STRUCTURAL`-only and `LEXICAL`-only both map to `HYPOTHESIS`, since §7's table does not distinguish *which* single family produced a `HYPOTHESIS`). The value/tier table below is the direct image of that mapping — every row here traces to one or more of §7's five raw states, and no raw state is missing an entry.

| value | tier | Valid? | Why |
|---|---|---|---|
| `PERSONNEL_COST` | `STRONG_INFERENCE` | Yes | Row 134 |
| `PERSONNEL_COST` | `HYPOTHESIS` | Yes | Row 151 |
| `OTHER` | `STRONG_INFERENCE` | Yes | Row 52 |
| `OTHER` | `HYPOTHESIS` | Yes | The mirror of row 151, not yet observed in the Golden Case set but structurally possible (weak, uncontested non-personnel signal) |
| `None` | `UNKNOWN` | Yes | §16 |
| `None` | `CONTRADICTION` | Yes | Row 122 |
| `PERSONNEL_COST` or `OTHER` | `CONTRADICTION` | **Rejected, impossible state** | §8 — a resolved value is definitionally incompatible with an unresolved-conflict tier |
| `PERSONNEL_COST` or `OTHER` | `UNKNOWN` | **Rejected, impossible state** | `UNKNOWN` requires both evidence lists empty (§6), which cannot produce a non-`None` value |
| `None` | `STRONG_INFERENCE` or `HYPOTHESIS` | **Rejected, impossible state** | A resolved tier requires a resolved value |

No dedicated state-machine class is built to enforce this — a single, small, directly-testable validity-check function (or a construction-time invariant, decided at implementation time, not here) suffices; six valid combinations do not warrant new abstraction.

## 29. Minimum kernel design

Recommended: **one small new module**, `backend/services/personnel_cost_classifier.py` (not two), containing clearly separated pure functions — `_extract_evidence(observation) -> tuple[supporting, contradicting]` and `_arbitrate(supporting, contradicting) -> Candidate` — mirroring `fru_sign_convention_detector.py`'s own existing one-file, separated-functions shape more closely than Doctrine v0's two-file split. **Why one file, not two, explicitly justified (not a default):** Doctrine v0 split extraction (`formula_reference_extractor.py`) from comparison (`financial_doctrine.py`) because the extractor is a genuinely reusable, doctrine-agnostic primitive with a named future consumer (any later doctrine entry). This classifier's evidence-extraction logic (§13) is Golden-Case/PCMN-scoped and has no known second consumer today — splitting it out now would be speculative generality, revisited only if/when a second concept classifier is actually built and evidence-extraction logic proves genuinely shared (a named, deferred question, not a promise). No DB, no LLM, no global mutable state, no API — pure functions of their arguments only, identical discipline to every prior v0 kernel in this engagement.

## 30. Test contract

Real Phidani rows used wherever available; synthetic cases explicitly labeled as such in their own test names/docstrings.

1. Row 122 → `CONTRADICTION` — **INVARIANT**
2. Row 134 → `STRONG_INFERENCE` `PERSONNEL_COST` — **INVARIANT** (calibration floor)
3. Row 52 → `STRONG_INFERENCE` `OTHER` — **INVARIANT** (the `OTHER`-semantics load-bearing test, §5)
4. Row 151 → `HYPOTHESIS` `PERSONNEL_COST` — **BEHAVIOR**
5. No-evidence synthetic → `UNKNOWN`, never `OTHER` — **INVARIANT**
6. Both-families-disagreeing synthetic (§17) — row 122 itself already covers this; no separate synthetic needed — **INVARIANT**, covered by test 1
7. One-family-present synthetic (§18, "strong/weak" relabeled) → `HYPOTHESIS` — **WEAK/GUARD** (generality check: same rule and outcome as row 151/test 4 on a different concrete input, not a distinct tier boundary — reclassified from BOUNDARY, §18 correction)
8. No-family-present synthetic (§18, "weak/weak" relabeled) → `UNKNOWN` — **WEAK/GUARD** (generality check: same rule and outcome as test 5 on a different concrete input, not a distinct tier boundary — reclassified from BOUNDARY, §18 correction)
9. Code absent → degrades to caption-only, never crashes — **BOUNDARY**
10. Caption absent → degrades to code/position-only, never crashes — **BOUNDARY**
11. Malformed code (row-234-shaped) → degrades gracefully, never crashes, never fabricates — **BOUNDARY**
12. Non-Belgian/unrecognized code prefix → signal absent, graceful degradation — **BOUNDARY**
13. Sign irrelevance — a negative-valued leaf inside the `62` range with an otherwise-`STRONG_INFERENCE`-worthy caption (row 160-shaped) does not change classification — **WEAK/GUARD** (documents a known-correct non-effect, not a risk actively being mitigated by new code)
14. Structural-role precondition documented as caller responsibility, not enforced internally — **BOUNDARY** (a documentation/signature test, not a runtime behavior test)
15. Vocabulary boundary — `match_concept` never called (AST-based) — **INVARIANT**
16. Doctrine not consulted — `financial_doctrine` never imported (AST-based) — **INVARIANT**
17. `KnowledgeModel` not consulted — no import of `knowledge_model_service` — **INVARIANT**
18. LLM zero — no import of `llm_service` or any HTTP/network primitive — **INVARIANT**
19. Evidence provenance preserved — every `EvidenceItem.source_pointer` on a real-row test traces to the exact real cell used — **BEHAVIOR**
20. Candidate impossible-state guards (§28's rejected rows) — construction-time or validity-check rejection — **INVARIANT**

## 31. Ablation test contract

**Row 134 (positive control), evidence removed one at a time:**
- Remove `CAPTION_LEXICAL` (simulate caption empty) → code+position alone remain, agreeing, uncontradicted → expect degrade from `STRONG_INFERENCE` to `HYPOTHESIS` (one combined structural signal, uncorroborated — same shape as row 151).
- Remove `ACCOUNT_CODE_FAMILY` + `STRUCTURAL_POSITION` (simulate code/position absent) → caption alone remains, specific and unambiguous → expect `HYPOTHESIS` (caption alone, uncorroborated).
- Remove `PARENT_CAPTION` only → no expected change (row 134's parent caption was corroborating, not decisive, since code+position+caption already independently agree without it).

**Row 122 (Golden Case), evidence removed one at a time:**
- Remove `CAPTION_LEXICAL` → only the structural signal (code+position) remains, unopposed → expect the contradiction to **disappear**, degrading to `STRONG_INFERENCE` `OTHER` (exactly row 52's shape) — proves the contradiction is reasoning from the caption's real content, not hardcoded to row 122's coordinates.
- Remove `ACCOUNT_CODE_FAMILY` + `STRUCTURAL_POSITION` → only caption remains, unopposed → expect degrade to `HYPOTHESIS` `PERSONNEL_COST` (caption alone, uncorroborated) — the contradiction disappears from the other side too, proving symmetry, not a one-sided hardcode.

**This directly satisfies §33's falsification criterion "removing supporting evidence does not change the result" — the ablation tests exist specifically to make that failure mode visible if it ever occurs.**

## 32. Falsification criteria (contract-level invariants, restated as test-enforceable claims)

The implementation is wrong if any of the following is ever observed: row 122 resolves confidently to one value without a surfaced conflict (test 1, §30); any leaf with empty evidence returns `OTHER` (test 5); `concept_vocabulary.match_concept` is called anywhere in the classifier (test 15); a Belgian account code is treated as decisive without corroboration (§14, tests 9–12); `CONTRADICTION` carries a stored numeric average or score of any kind (no such field exists anywhere in §3 — a structural guarantee, not just a test); `UNKNOWN` is unreachable by construction (test 5 proves it is reachable); an ablation test (§31) shows no change when evidence is removed; `financial_doctrine.py` is imported by the classifier (test 16); any row-122-specific literal (a hardcoded coordinate check, e.g. `if cell == "C122"`) appears anywhere in the kernel — checked by direct source review at implementation time, not automatable as a single test, named explicitly as a manual review gate.

## 33. Explicitly OUT (restated, unchanged from §2, per the mission's own required heading)

General Economic Meaning engine; Revenue classifier; Opex classifier; full payroll taxonomy; multilingual semantic model; fuzzy logic; numeric confidence; Bayesian model; LLM; embeddings; ontology expansion; Doctrine expansion; Reporting Structure implementation; KnowledgeModel integration; Epistemic Dialogue integration; materiality engine; persistence; DB; Supabase; API/UI; Candidate generic framework (beyond the bounded `EvidenceItem`/`CONTRADICTION` extension, §3); multi-concept classifier.

## 34. Named reservations (not fixed, not silently dropped)

1. **`Candidate`/`EvidenceItem` relocation to a shared module** (§3) is recommended but not performed in this documentation-only contract — the next implementation mission must either perform the move or explicitly re-justify keeping it local.
2. **Behavior on non-P&L/non-leaf input is undefined** (§19/§20) — a future mission wiring this classifier to a real caller must supply the precondition itself; this contract does not guarantee safety without it.
3. **The `(A) value=None` contradiction representation is scope-dependent** (§8) — revisit if the vocabulary ever grows beyond two values.
4. **`financial_truth.py`'s `confidence: float = 0.5` remains unrecorded in `STRATEGIC_DEFERRED_WORK_REGISTER.md`** — unchanged since the prior arbitration, still not this contract's scope to fix.
5. **The two unmerged 2026-08-10 documents remain unmerged** — unchanged since the prior arbitration; still a promotion-gate question for whoever authorizes implementation.
6. **[Added by the Epistemic Semantics Adversarial Review] The two-family model (§6/§7) has no defined behavior for a hypothetical third, independent signal family** (e.g. an asymmetric case with 2 families agreeing vs. 1 disagreeing) — not needed by any case in this contract, but a future slice that adds a genuinely independent third evidence source must re-derive §7's table, not merely extend it by analogy.

## 35. Adversarial self-review (16 required questions)

1. **Does `OTHER` mean "not personnel" by default?** No — §5's rule requires positive, specific evidence; test 5 (§30) directly guards against the default-`OTHER` failure mode.
2. **Can `UNKNOWN` occur naturally?** Yes — §16, both real-shaped and synthetic paths reach it; not merely a theoretical branch.
3. **Is `CONTRADICTION` a status, not a category?** Yes — checked directly against the data shape (§3): it is a `tier` value, never stored alongside `PERSONNEL_COST`/`OTHER` as if a third member of the same vocabulary; §28's impossible-state table enforces this structurally.
4. **Did account code become authority?** No — §14, tested against five explicit degradation cases; row 122 is the direct proof it is not.
5. **Did caption become authority?** No — row 151 (§12) proves an absent `LEXICAL` family does not manufacture a stronger tier than the `STRUCTURAL` family alone supports; §18's one-family-present synthetic proves the same in the mirror direction — a non-matching caption never manufactures `CONTRADICTION`.
17. **[Added by this review] Was the `CONTRADICTION` bar internally consistent with the `HYPOTHESIS` bar before this correction?** No — this is the exact defect this review found and fixed (§0's correction note, §6/§7): the original §7 required each side to be "independently `STRONG_INFERENCE`-worthy," while the original §12 established that the same evidence (code+position alone) is only `HYPOTHESIS`-worthy, making row 122's own `CONTRADICTION` verdict unreachable under a consistent reading. Corrected to a single family-presence/agreement table (§7) that produces the same four Golden Case outcomes without the contradiction.
18. **[Added by this review] Does the corrected model still explain every case in the contract with only two named families?** Yes — checked directly against all four real Golden Cases (122, 134, 52, 151) and both synthetic cases (§16, §18): every one resolves via §7's five-row table with no residual case requiring a third family or a per-item strength scale. A genuine limit is named, not hidden: a future three-or-more-independent-family scenario is out of scope and would require revisiting the table (§7's own reservation, §34 item 6).
6. **Are evidence strength and hypothesis tier separate?** Yes — `EvidenceItem` has no strength field; `Candidate.tier` is computed via the rule table (§7/§13), never blended from a stored score.
7. **Is any numeric score hidden?** No — checked directly against every field defined in §3/§4; none is numeric.
8. **Did we build semantic aliases in Vocabulary?** No — `concept_vocabulary.py` is not modified by this contract (§2 OUT list); the classifier's own keyword list (§13/§15) lives entirely inside the new module, never inside Vocabulary, and is proven never to call `match_concept` (§22, test 15).
9. **Did Doctrine influence candidate generation?** No — §21, structurally impossible by the current `compare_against_doctrine` signature (re-confirmed, not merely cited from the prior arbitration), and tested directly (test 16).
10. **Did we assume Reporting Structure not yet available?** Correctly, yes — §19/§20 name it as a real, unbuilt dependency and use the input-precondition pattern instead of pretending it exists.
11. **Did we overfit Phidani?** Named honestly where true: `ACCOUNT_CODE_FAMILY` (PCMN-specific) and `CAPTION_LEXICAL` (French-only) are both explicitly flagged as Phidani/French-scoped (§13); the *mechanism* (evidence accumulation, contradiction detection) is not.
12. **Does row 122 truly require `CONTRADICTION`?** Re-derived directly in §9 under the corrected §6/§7 model, not assumed from the prior arbitration and not resting on the now-removed "independently `STRONG_INFERENCE`" claim — both the `STRUCTURAL` and `LEXICAL` families are present, each contributing a specific, non-residual claim, and they disagree, which is §7's exact and only bar for `CONTRADICTION`.
13. **Does row 151 truly justify `HYPOTHESIS`?** Re-examined critically in §12 this session, including a fresh formatting check and an explicit rejection of a plausible-looking fifth signal (neighbor consistency) that would have wrongly promoted it — the conclusion survived, but only after being genuinely tested, not merely repeated.
14. **Can the output later support dialogue?** Yes, by construction (§24) — every tier maps to a plausible future dialogue action without needing new fields.
15. **Could the slice be smaller?** Considered: a version without `CONTRADICTION` (plain existing `Candidate`) was tested directly against row 122 in the prior arbitration and found to either risk a wrong answer or silently discard information (arbitration doc §7) — not skipped by preference, tried and found insufficient.
16. **What observation would falsify the signal rules?** A real Phidani row where code+position+caption all agree but the true economic nature is something else entirely (none found in this file); or a row where the caption keyword list produces a false positive (e.g., a company named "Rémunération SA" as a vendor, coincidentally containing the keyword) — not present in Phidani, named as a real, general risk of any keyword-based signal, not fabricated to sound safe.

**No answer above requires revising this contract's conclusions.**

---

**PERSONNEL_COST_CLASSIFIER_V0_IMPLEMENTATION_CONTRACT — ESTABLISHED. NOT YET IMPLEMENTED. NOT YET PROMOTED.**
