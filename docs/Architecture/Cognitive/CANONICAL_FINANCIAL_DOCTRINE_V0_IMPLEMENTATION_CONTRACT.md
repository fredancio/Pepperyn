# CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md

**Status:** IMPLEMENTATION CONTRACT — established, not yet implemented, not yet promoted.
**Branch:** `architecture/canonical-financial-doctrine-v0-contract-2026-08-11` (not merged).
**Supersedes/refines:** `CANONICAL_FINANCIAL_DOCTRINE_FOUNDATION.md` (`95de5a0`) and `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md` (`2c03ca6`) — this contract is the binding, corrected shape; where it differs from either prior document, this contract governs.
**Scope:** exactly two small capabilities — Concept Vocabulary v0 and Canonical Financial Doctrine v0 — proven against exactly one real Golden Case (Phidani row 133) and three adversarial counter-cases. Nothing else.

---

## 1. Entry gate

Verified clean `main`; branched from it directly. Read in full for this contract: `CANONICAL_FINANCIAL_DOCTRINE_FOUNDATION.md`, `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md`, `HYPOTHESIS_REPRESENTATION_DESIGN_REVIEW.md`, `ECONOMIC_MEANING_REASONING_PROFESSION_MODEL.md`, `OBSERVATION_STRUCTURE_V0_IMPLEMENTATION_CONTRACT.md` (via `observation_structure.py`'s restated contract), `PEPPERYN_CONSTITUTION.md`; re-inspected `observation_structure.py`, `formula_evidence.py`, `fru_sign_convention_detector.py`, `knowledge_model_service.py`, `epistemic_dialogue_service.py`, `financial_truth.py` directly, not from memory.

## 2. Professional responsibilities (stated separately, as required)

**Concept Vocabulary v0** answers exactly one question: *"which canonical concept are we referring to?"* It never answers *"does this observed row belong to that concept?"* — that remains, entirely, Economic Meaning's job, unimplemented here and untouched by this contract.

**Canonical Financial Doctrine v0** answers exactly one question: *"what does this canonical concept conventionally or mathematically require, given that a concept hypothesis already exists?"* It never identifies a concept from raw data — it validates an already-formed hypothesis, never generates one.

## 3. Contract scope freeze

**IN:** (A) a small canonical Concept Vocabulary; (B) a small Canonical Financial Doctrine registry; (C) one deterministic comparison function; (D) the real row-133 `MISMATCH` Golden Case; (E) one synthetic `MATCH` counter-case; (F) honest `UNKNOWN`/`NOT_APPLICABLE` behavior, each with its own adversarial test case; (G) the smallest possible pure formula-reference extractor, only because the Golden Case cannot be tested end-to-end without it.

**OUT**, explicitly, per §34 below: no general Economic Meaning classifier, no Candidate v2 implementation, no KnowledgeModel integration, no Epistemic Dialogue integration, no UI/API/router wiring, no ontology, no taxonomy, no jurisdiction/applicability engine, no LLM, no database, no Supabase, no migration.

## 4. Concept Vocabulary v0 — minimum shape

```python
ConceptId = str  # e.g. "EBITDA", "PERSONNEL_COST" — plain, human-readable, git-diffable

@dataclass(frozen=True)
class ConceptEntry:
    id: ConceptId
    lexical_aliases: tuple[str, ...]  # case/spacing variants of the identifier ITSELF only
    provenance: str
    version: int
```

No UUIDs (not demonstrated necessary — a plain identifier string is stable, diffable, and sufficient). No hierarchy, no is-a relations, no multilingual semantic search — none demonstrated by row 133.

## 5. Lexical-alias boundary — arbitrated explicitly

Tested against the mission's own examples directly. **Choice: A — trivial lexical normalization aliases belong in Vocabulary; economically meaningful synonyms do not.**

**Allowed in Vocabulary (lexical, mechanical, reversible by a human without domain knowledge):** `"EBITDA"`, `"Ebitda"`, `"ebitda"` — case variants of the *same word*, testable by a trivial rule (case/whitespace-insensitive equality to the identifier or a declared alias). A human curator adding these needs no financial expertise, only to recognize the same word spelled differently.

**Never allowed in Vocabulary (semantic recognition, requires domain judgment):** `"Rémunérations"` → `PERSONNEL_COST`, `"Personnel"` → `PERSONNEL_COST`, `"Operating cash earnings"` → `EBITDA`. These require knowing that a *different word* refers to the *same concept* — a professional judgment call, not a spelling normalization. This is Economic Meaning's own signal inventory (`ECONOMIC_MEANING_REASONING_PROFESSION_MODEL.md` §3), never Vocabulary content.

**Consequence for the Golden Case:** row 133's own concept hypothesis (`EBITDA`) is legitimately formed via a Vocabulary lexical-alias match, because the caption *literally contains the word "EBITDA"* — a lexical match, not a semantic inference. Row 161's `PERSONNEL_COST` hypothesis is **not** a Vocabulary match at all (nothing in *"Rémunérations - Charges Sociales - Pensions"* lexically resembles `"PERSONNEL_COST"`) — it must be supplied by Economic Meaning (out of scope, so supplied by a test fixture, §14 below), never smuggled into Vocabulary content.

**This boundary must never be allowed to drift** — the test contract (§27) includes an explicit negative test proving `"Rémunérations"` does not match any Vocabulary alias.

## 6. Concept identity

A plain string identifier (`ConceptId = str`), uppercase-with-underscores by convention (`EBITDA`, `PERSONNEL_COST`), matching the vocabulary style already established elsewhere in this codebase (`SUBJECT_VALUE_REGISTRY`'s subject names, `STRUCTURAL_ROLE_VALUES`). Stable, human-readable, git-diffable, language-independent for internal reference (the identifier itself is English/abbreviation-neutral; captions in any language are matched via lexical aliases or, out of scope, Economic Meaning). No UUID, no hierarchy, no is-a relations.

## 7. Vocabulary ownership / governance

Tenant-independent, read-only at runtime, Git-versioned, human-reviewed via ordinary PR, never writable by end users, Epistemic Dialogue, or an LLM — identical governance to Doctrine itself (`CANONICAL_FINANCIAL_DOCTRINE_FOUNDATION.md` §21–22, unchanged, reapplied here). **Layout: its own small module, `concept_vocabulary.py`, separate from `financial_doctrine.py`** — not merged into the same file, because Vocabulary is the smaller-scoped, more broadly reusable of the two (a future Economic Meaning implementation would need to import Vocabulary but has no reason to import Doctrine directly), and keeping them separate preserves the exact responsibility boundary §5 just drew.

## 8. Doctrine Statement v0 — corrected minimum shape

Every field re-challenged against the computability review's own test (§4 there), not preserved by inertia. `concept_aliases` is **removed from `DoctrineStatement` entirely** — per §5 above, aliases belong to Vocabulary, and duplicating them on Doctrine would create exactly the two-independently-editable-representations risk Constitution Article XII forbids (a Vocabulary alias list and a Doctrine alias list could silently diverge). Doctrine references a concept by its **stable identifier only**.

```python
AuthorityType = Literal["MATHEMATICAL_IDENTITY", "PROFESSIONAL_CONVENTION"]

@dataclass(frozen=True)
class DoctrineStatement:
    id: str
    concept: ConceptId                        # references Vocabulary by identifier, no duplication
    required_prior_deductions: tuple[ConceptId, ...]  # e.g. ("PERSONNEL_COST",)
    authority_type: AuthorityType
    applicability: str                         # documentation-only in v0, never parsed (§12)
    provenance: str
    version: int
```

No `proposition: str` field (per `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md` §5 — explanation is rendered, never stored independently, §10 below).

## 9. Machine-readable semantics — bounded to what row 133 demonstrates

`required_prior_deductions: tuple[ConceptId, ...]` — a flat, membership-testable set of concept identifiers. **Not** a mathematical AST, **not** an expression parser, **not** a constraint DSL, **not** arbitrary predicates, **not** a graph. Row 133 and its counter-case (§18) both resolve fully via set membership; nothing more is demonstrated necessary, and nothing more is built.

## 10. Human-readable explanation — rendered, never stored

```python
def render_explanation(doctrine: DoctrineStatement) -> str:
    required = ", ".join(doctrine.required_prior_deductions)
    return f"{doctrine.concept} conventionally requires the following already deducted beforehand: {required}."
```

Pure, deterministic, zero LLM. This is the *entire* explanatory surface for v0 — no natural-language generation engine, no template beyond this one f-string. It is explanatory only, never semantic authority: nothing consumes its *output* as an input to any decision: the comparison function (§15) never calls this and never depends on its result.

## 11. Authority model — minimality vs. dead-end, decided explicitly

Tested both options the mission names. **Choice: declare both `AuthorityType` values in the type now (`MATHEMATICAL_IDENTITY`, `PROFESSIONAL_CONVENTION`), but populate v0's actual registry content with only one `PROFESSIONAL_CONVENTION` entry (`EBITDA`).** Reasoning: the comparison function (§15) never branches on `authority_type` at all in v0 (that branching is a future orchestration/KnowledgeModel-integration concern, explicitly deferred, §21, §29) — so declaring the full type costs nothing behaviorally, while satisfying the mathematical-identity control case (§22) as a *capability* check without requiring any implementation for it. Deferring the enum value entirely would force a later contract amendment merely to add a type literal — a real, if small, dead-end cost the mission asks to weigh, and the balance favors declaring it now.

## 12. Applicability — explicitly not executable in v0

Confirmed, not overclaimed: **the comparison function (§15) must never read `doctrine.applicability` at all.** It exists purely as curator-facing documentation (`"general management/financial-accounting convention, not a specific GAAP/IFRS citation"`). **Constraint, made structural:** the Doctrine registry construction helper (§25) must reject, at build/test time, any attempt to register two `DoctrineStatement` entries for the same `concept` — v0 has no mechanism to choose between competing entries, so it must not be possible to create the ambiguity in the first place. This is enforced by a registry-construction function that raises on a duplicate `concept`, never by a bare dict literal (which would silently keep only the last one).

## 13. Formula dependency input — the smallest necessary extractor

Row 133's Golden Case cannot be tested end-to-end without extracting which cells a formula references. The computability review confirmed this is mechanically trivial (regex on the formula string, the same technique `fru_sign_convention_detector.py` already uses for its own margin-subtraction search). **Included, minimally:**

```python
def extract_cell_references(formula: str) -> frozenset[str]:
    """Single-hop, forward only. No recursion. Row 133: '=C35-C132' -> {'C35','C132'}."""
```

**No backward ("referenced-by") index is included in this slice.** Re-examined directly (§13 of this contract's own reasoning, corrected relative to `HYPOTHESIS_REPRESENTATION_DESIGN_REVIEW.md` §10, which proposed both directions): the core `MISMATCH` determination for row 133 needs only the **forward** set — whether `PERSONNEL_COST` is confirmed absent from what row 133's own formula directly references. The backward hop (finding that row 166 applies payroll *after* row 133) is useful only for a richer narrative explanation, not for the comparison result itself — explicitly deferred, not required by this Golden Case.

## 14. Economic Meaning prerequisite — resolved via test fixture, not a classifier

Chosen explicitly: **pattern A — a deterministic test fixture supplies pre-classified concepts as given inputs.** No Golden-Case-only classifier is built (rejecting pattern B), no existing FRU/Observation primitive is repurposed for semantic classification (rejecting C, since none currently perform natural-category classification — Observation Structure v0 is deliberately non-semantic, §14 of its own contract). This keeps *"Doctrine works given concept-classified inputs"* strictly separate from *"Economic Meaning correctly classifies payroll"* — the latter is not this slice's problem and is not tested by it. The fixture asserts, as given: *"row 133's formula references cells C35 and C132; neither has been classified `PERSONNEL_COST`; both classifications are confidently known (not merely absent)."* No concept identifiers for what C35/C132 *are* need to be invented or registered in Vocabulary — the fixture only needs to assert what they are **not**, and that this determination is *known*, not *missing* (§16).

## 15. Comparison function — types and semantics, precise

```python
@dataclass(frozen=True)
class ObservedComposition:
    directly_referenced_concepts: frozenset[ConceptId]
    # Concepts CONFIRMED PRESENT among the observation's single-hop forward
    # formula references, per Economic Meaning (supplied by test fixture in v0).
    unclassified_references: frozenset[str]
    # Cell coordinates referenced by the formula whose concept classification
    # is genuinely missing/uncertain -- NOT the same as "confirmed absent."
    # Non-empty here is what forces UNKNOWN rather than MISMATCH (§16).

ComparisonResult = Literal["MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN"]

def compare_against_doctrine(
    candidate_concept: ConceptId,   # precondition: a hypothesis MUST already exist;
                                     # this function is never called with "no candidate" --
                                     # that branch is the caller's, not this function's (§29)
    doctrine: DoctrineStatement,
    observed: ObservedComposition,
) -> ComparisonResult:
    if candidate_concept != doctrine.concept:
        return "NOT_APPLICABLE"
    missing = set(doctrine.required_prior_deductions) - set(observed.directly_referenced_concepts)
    if not missing:
        return "MATCH"
    if observed.unclassified_references:
        return "UNKNOWN"
    return "MISMATCH"
```

**Definitions, rigorous, matching the mission's own required precision:**
- **`MATCH`:** the doctrine entry's concept applies (`candidate_concept == doctrine.concept`), and every required prior deduction is confirmed present.
- **`MISMATCH`:** the concept applies, at least one required prior deduction is confirmed *absent* (not merely unobserved), and no unresolved classification gap could hide it.
- **`NOT_APPLICABLE`:** the candidate concept confidently differs from the doctrine entry's own concept — the wrong entry to even ask.
- **`UNKNOWN`:** the concept applies, but the comparison cannot be completed honestly because at least one referenced cell's own concept classification is missing or uncertain.

**No numeric confidence anywhere in this function or its inputs.**

## 16. MISMATCH safety — the load-bearing distinction, made structural

`ObservedComposition` deliberately carries **two** sets, not one, precisely to prevent the failure mode the mission names: an absent concept in `directly_referenced_concepts` must never automatically mean `MISMATCH`. `unclassified_references` exists *only* to carry this distinction — its presence, checked *before* concluding `MISMATCH`, is what forces `UNKNOWN` when payroll-equivalent rows could not be semantically identified at all. This is the smallest representation that preserves the distinction: two sets, no epistemic graph, no per-concept confidence score.

## 17. Row 133 — the Golden Case, fully specified

```python
candidate_concept = "EBITDA"          # given: caption self-declares it (Vocabulary lexical match, §5)
doctrine = EBITDA_DOCTRINE            # concept="EBITDA", required_prior_deductions=("PERSONNEL_COST",)
observed = ObservedComposition(
    directly_referenced_concepts=frozenset(),   # neither C35 nor C132 confirmed PERSONNEL_COST
    unclassified_references=frozenset(),        # both ARE classified (as something else) -- nothing left unresolved
)
# compare_against_doctrine(candidate_concept, doctrine, observed) == "MISMATCH"
```

Every ingredient traces to its owner (§2 of `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md`, reapplied): raw cell content (Evidence), formula reference extraction (§13, new, deterministic), the concept hypothesis (Vocabulary lexical match, §5), the `PERSONNEL_COST`-absence fact (test fixture standing in for Economic Meaning, §14), the doctrine entry (§8), the comparison (§15). **No hand-coded "row 133 is wrong" branch anywhere** — the result falls out of the general-purpose comparison function given these inputs, nothing else.

## 18. MATCH counter-case

```python
observed_match = ObservedComposition(
    directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
    unclassified_references=frozenset(),
)
# compare_against_doctrine("EBITDA", doctrine, observed_match) == "MATCH"
```

Identical function, identical `candidate_concept`, identical `doctrine` — only the economically relevant input changed. No separate branch, per §11 of the mission.

## 19. UNKNOWN adversary

```python
observed_unknown = ObservedComposition(
    directly_referenced_concepts=frozenset(),
    unclassified_references=frozenset({"C132"}),   # this cell's concept could not be determined
)
# compare_against_doctrine("EBITDA", doctrine, observed_unknown) == "UNKNOWN"
```

Not `MISMATCH` — mandatory, per §16.

## 20. NOT_APPLICABLE adversary

```python
# compare_against_doctrine("REVENUE", doctrine, observed_anything) == "NOT_APPLICABLE"
```

The `EBITDA` doctrine entry is never forced onto an observation confidently hypothesized as a different concept, regardless of what `observed` contains — the concept check short-circuits first.

## 21. Enterprise convention compatibility — preserved, not integrated

`KnowledgeModel` is **not** touched by this slice. The comparison function and its inputs never reference it. Compatibility is preserved structurally: a future `Candidate v2` (deferred, §29) would attach the `compare_against_doctrine` result as one `DOCTRINE`-sourced evidence item and a separate `KnowledgeModel.recall()` result as one `ENTERPRISE_KNOWLEDGE`-sourced evidence item, coexisting on the same Candidate — exactly as `HYPOTHESIS_REPRESENTATION_DESIGN_REVIEW.md` §13/§15 and `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md` §15 already established. No new persistence, no doctrine mutation, no overwrite — confirmed compatible by construction, not extended here.

## 22. Mathematical identity — control case, not implemented

`AuthorityType` declares `MATHEMATICAL_IDENTITY` (§11) precisely so a future entry (e.g. the accounting equation, never populated in v0) could exist without a type change. The comparison function's own logic (§15) does not consult `authority_type` at all — the invariant *"Enterprise Knowledge can never override a `MATHEMATICAL_IDENTITY` entry"* is a **future orchestration policy**, not a v0 data-shape requirement, and this contract confirms (does not build) that the shape does not obstruct it.

## 23. Concept Vocabulary vs. Economic Meaning — explicit invariant

**VOCABULARY** defines canonical identities and their trivial lexical forms only. **ECONOMIC MEANING** (unimplemented, out of scope) decides whether an observed row is likely an instance of one of those concepts, from file-internal evidence (caption semantics, code family, structural position) — never from Vocabulary alone. **DOCTRINE** defines machine-readable professional relationships between canonical concepts, consumed only after a concept hypothesis already exists.

Allowed in Vocabulary: `"EBITDA"` → `EBITDA`; case/spacing normalization only. **Not** allowed in Vocabulary: `"Rémunérations"` → `PERSONNEL_COST` (a semantic recognition rule, Economic Meaning's territory, §5). The Vocabulary must never grow into a classifier — enforced by the negative test in §27.

## 24. Concept Vocabulary vs. ontology — explicit, falsifiable, revisable

**Formal ontology v0: NO. Taxonomy v0: NO. Concept graph: NO. Flat typed references: YES, only `required_prior_deductions`, demonstrated by row 133.** This remains falsifiable — a future real case may justify expansion, but none does today, and none is anticipated speculatively here.

## 25. Git representation

Plain, immutable, frozen dataclasses and `Literal`/tuple types — no enums requiring a separate class hierarchy beyond `Literal`, no dynamic runtime mutation, no ORM. Registries are constructed via a small helper that validates uniqueness at build/import time (raises `ValueError` on a duplicate `concept`, §12) — never a bare dict literal alone. Every change is a plain Git diff on a `.py` file.

## 26. Governance

Financial-domain-literate curator + PR review, identical discipline to `CANONICAL_FINANCIAL_DOCTRINE_FOUNDATION.md` §22, reapplied to Vocabulary. Every populated `ConceptEntry`/`DoctrineStatement` requires non-empty `provenance` and an integer `version`, enforced by a test (§27). Ordinary end users: NO. Epistemic Dialogue: NO. LLM: NO.

## 27. Test contract

1. **Golden Case** — row 133 inputs (§17) → `MISMATCH`.
2. **MATCH counter-case** (§18) → `MATCH`, same function, same path.
3. **UNKNOWN adversary** (§19) → `UNKNOWN`, never `MISMATCH`.
4. **NOT_APPLICABLE adversary** (§20) → `NOT_APPLICABLE`.
5. **Vocabulary lexical match** — `"EBITDA"`, `"Ebitda"`, `"ebitda"` all resolve to concept `EBITDA`.
6. **Vocabulary boundary negative test** — `"Rémunérations"` matches **no** Vocabulary alias for any concept (proves §5/§23's boundary holds, not merely asserted).
7. **Registry uniqueness** — constructing a Doctrine registry with two entries sharing `concept="EBITDA"` raises, never silently overwrites (§12).
8. **`applicability` never read** — a structural/introspection test (mirroring `test_formula_evidence.py`'s own `TestNoMacrosExecuted` pattern) asserting `compare_against_doctrine`'s source never references `.applicability`.
9. **No stored prose field** — `DoctrineStatement.__dataclass_fields__` contains no `proposition`-shaped field (mirrors `test_formula_evidence.py`'s `TestNoNumericValueProduction` pattern exactly).
10. **`render_explanation` is deterministic and derived** — same input, same output, byte-for-byte, across repeated calls.
11. **Formula extractor, single-hop only** — `extract_cell_references("=C35-C132") == frozenset({"C35","C132"})`; no recursion into whatever `C35`/`C132` might themselves reference.
12. **Provenance/version presence** — every populated entry (Vocabulary and Doctrine) has non-empty `provenance` and an integer `version`.

## 28. Estimated production file impact (future implementation, not built here)

- `backend/services/concept_vocabulary.py` (new) — `ConceptEntry`, the Vocabulary registry, lexical-match helper.
- `backend/services/financial_doctrine.py` (new) — `DoctrineStatement`, `AuthorityType`, the Doctrine registry (with duplicate-`concept` guard), `ObservedComposition`, `compare_against_doctrine`, `render_explanation`.
- `backend/services/formula_reference_extractor.py` (new) — `extract_cell_references`, the smallest possible pure function, single-hop only.
- `backend/tests/test_concept_vocabulary.py`, `backend/tests/test_financial_doctrine.py` (new).

**No modification to any existing production module.** `observation_structure.py` and `formula_evidence.py` already supply everything else this slice's Golden Case needs (structural role, formula presence) without being touched — confirmed by direct re-inspection, not assumed.

## 29. Candidate v2 — deferred, confirmed not required

The comparison function (§15) is fully testable with plain, typed inputs — it does not need `Candidate` to exist. Building `Candidate v2` now would smuggle a second, unrelated capability into a slice whose entire purpose is proving Doctrine's own computability. **Deferred.**

## 30. LLM

Zero. No semantic alias generation, no doctrine explanation generation (§10's renderer is a pure f-string, not a model call), no candidate classification. This slice exists specifically to prove the deterministic architecture independent of LLM quality.

## 31. Persistence

Git-versioned code only. No database, no cache, no runtime writes, no dynamically generated Doctrine entry.

## 32. Security / trust

No external calls, no customer data stored in Vocabulary/Doctrine (both are product-global curated content, no tenant fields at all), no Trust Gateway impact (no LLM touchpoint exists in this slice).

## 33. Fail-closed rules, made structural (not merely stated)

- Unknown concept (no `candidate_concept` at all) → the comparison function is never called; this is a caller-side precondition (§15's own signature requires a non-optional `ConceptId`), never a silent fallback inside the function.
- Unknown prerequisite classification → `UNKNOWN`, enforced by `unclassified_references` (§16).
- Missing doctrine entry for a concept → a registry lookup returning nothing; the caller must not fabricate a `MATCH` — out of this slice's tested surface but structurally impossible to get wrong given the registry's own plain-dict shape (a missing key is a `KeyError`/`None`, never silently treated as `MATCH`).
- Multiple applicable doctrine entries for the same concept → **structurally prevented at registry construction time** (§12, §27 test 7), not handled at comparison time.
- Malformed doctrine reference (a `required_prior_deductions` entry naming a `ConceptId` absent from Vocabulary) → a contract/test-time validation failure, never a silent runtime pass-through — enforced by construction-time cross-validation between the two registries (named as a reservation, §35, since it requires the two modules to know about each other at build time — a small, explicit, tested coupling, not a hidden one).
- Unknown concept identifier passed anywhere → a registry lookup error during development/test, never a silent runtime default.

## 34. Explicit OUT list

Economic Meaning general classifier; Candidate v2 implementation; KnowledgeModel integration; Epistemic Dialogue integration; LLM; formal ontology; taxonomy; concept graph; applicability engine; jurisdiction model; multilingual semantic mapping; full EBITDA formula/bridge engine; full finance doctrine catalogue (Gross Margin, EBIT, FCF, Working Capital, ratios, accounting-standards catalogues, Belgian PCMN or IFRS ontologies); `financial_truth.py` correction; renderer changes; API/UI wiring; persistence database; Supabase; FTE changes; Observation Structure redesign; the backward ("referenced-by") dependency index (§13).

## 35. Adversarial contract review — 18 required questions

1. **Are aliases becoming classification rules?** No — §5's boundary is structural and tested negatively (test 6, §27).
2. **Is Doctrine generating candidates?** No — `compare_against_doctrine` requires a non-optional `candidate_concept` precondition (§15); it never forms one.
3. **Is missing payroll confused with confirmed absence?** No — the two-set `ObservedComposition` design exists specifically to prevent this (§16), and test 3 (§27) proves it.
4. **Can UNKNOWN survive end-to-end?** Yes — §19, test 3.
5. **Is prose still secretly canonical?** No — removed as a stored field entirely (§8, §10), tested structurally (test 9).
6. **Are concept identifiers stable and unambiguous?** Yes — plain strings, one canonical spelling per concept, Vocabulary owns the only sanctioned variants (§6).
7. **Is a taxonomy being introduced accidentally?** No — checked directly; `required_prior_deductions` is a flat tuple, no is-a relations anywhere (§9, §24).
8. **Is applicability overclaimed?** No — explicitly never read by the comparison function, enforced by test 8 (§12, §27).
9. **Is row 133 hardcoded?** No — the Golden Case is ordinary input to a general-purpose function; no `if row == 133` branch exists anywhere in the design (§17).
10. **Does MATCH use the identical reasoning path?** Yes — §18, same function, same code path, different input.
11. **Does the validator need an LLM?** No (§30).
12. **Does Candidate v2 actually need to exist yet?** No — confirmed, not merely asserted, by §15's own fully-typed, Candidate-independent test surface (§29).
13. **Is formula dependency extraction broader than necessary?** No — narrowed further than the prior review's own proposal: single-hop forward only, backward index explicitly deferred (§13).
14. **Are Enterprise Knowledge and Doctrine still distinct?** Yes — §21, no KnowledgeModel reference anywhere in this slice's code surface.
15. **Can ordinary users modify Doctrine?** No (§26).
16. **Is any doctrine statement untestable?** No — every populated entry ships with the four-outcome test matrix (§27, tests 1–4) plus provenance/uniqueness checks (tests 7, 12).
17. **Could the first slice be smaller?** Considered directly: removing the formula extractor (§13) would make the Golden Case untestable end-to-end (reduces to an assertion about hand-fed booleans, no longer proving anything about real Phidani data); removing the Vocabulary's alias mechanism (§5) would make the design silently fragile to trivial capitalization variance. Neither reduction survives scrutiny — this is the smallest slice that is still genuinely falsifiable against a real file.
18. **Are we building more than row 133 proves necessary?** No — checked field-by-field (§8, §9) and file-by-file (§28); every artifact traces to a specific, named test requirement.

No answer exposed a defect requiring revision of this contract's substantive shape.

## 36. Named reservations

- The construction-time cross-validation between Vocabulary and Doctrine registries (§33, "malformed doctrine reference") introduces a small, explicit build-time coupling between two otherwise-separate modules — named, not hidden, and testable, but worth flagging as the one place these two small registries must agree with each other.
- `applicability`'s eventual computable form (a scope identifier, a framework label) remains genuinely undesigned — deliberately, since v0's single-entry registry never exercises it (`CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md` §9, reaffirmed, not revisited here).
- The backward ("referenced-by") dependency index remains named but unbuilt (§13) — a real, if optional, enhancement to future explanation quality, not required for correctness.

## 37. Implementation recommendation

**GO.** Every field, every function, every test case traces to a specific requirement demonstrated by the row-133 experiment or its adversarial counter-cases; nothing is speculative; every prior open question this contract could resolve (alias boundary, authority-type minimality, Economic Meaning prerequisite pattern, applicability's honest non-computability, formula-dependency scope) has been resolved with an explicit, falsifiable choice, not deferred further.

---

**CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT — ESTABLISHED. NO CODE WRITTEN. NO MERGE.**
