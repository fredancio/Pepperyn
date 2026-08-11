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

**[AMENDED 2026-08-11 — Composition Completeness Review]** Case/spacing/punctuation variance is **normalization, not a stored alias**, unless a demonstrated case survives that a normalization rule cannot cover. Storing `"EBITDA"`, `"Ebitda"`, `"ebitda"` as three separate strings on `ConceptEntry.lexical_aliases` is redundant: a single deterministic normalization function (`casefold()` + `strip()`, applied at match time to both the candidate text and every registered identifier/alias) covers all three, plus any unanticipated case/whitespace variant, without enumeration. `lexical_aliases` remains in the shape (§4) but is **reserved for genuinely irreducible textual alternates** — forms that are not a mechanical transform of the identifier, e.g. a punctuation-free acronym vs. a fully spelled-out expansion (`"EBITDA"` vs. `"Earnings Before Interest Taxes Depreciation and Amortization"`), if such a case is ever demonstrated. **v0's actual content needs zero stored aliases**: row 133's caption contains the literal substring `"EBITDA"`, matched entirely by normalization. `ConceptEntry.lexical_aliases` for the `EBITDA` entry is corrected from 3 entries to `()`.

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
    provenance: str
    version: int
```

No `proposition: str` field (per `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md` §5 — explanation is rendered, never stored independently, §10 below).

**[AMENDED 2026-08-11 — Composition Completeness Review]** `applicability: str` is **removed from the executable dataclass entirely** — see §12 (corrected) below. Every field remaining on `DoctrineStatement` is now read by at least one function in v0; this is made an explicit invariant of the executable schema, not an accident.

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

## 12. Applicability — explicitly not executable in v0 [CORRECTED 2026-08-11]

**Corrected finding (Composition Completeness / False-Mismatch Review, 2026-08-11):** the mission asked directly whether non-computable `applicability` belongs on the executable v0 object or should remain documentary metadata. Original contract kept it as a typed `str` field on `DoctrineStatement`, never read — a real inconsistency: a field that is provably never consumed by any function is not part of the machine-readable schema, and leaving it on the executable dataclass invites a future implementer to assume it must be wired up, or to silently start reading it without a fresh scoping decision. **Corrected: `applicability` is removed from `DoctrineStatement` entirely** and lives only as a plain code comment / docstring next to each registry entry's construction (curator-facing prose, e.g. `# applicability: general management/financial-accounting convention, not a specific GAAP/IFRS citation`) — never a dataclass field, never parsed, never looked up by identifier at runtime. This makes the invariant structural rather than merely observed: a field that isn't on the dataclass cannot accidentally be read. The corresponding test (§27, test 8) is corrected from "applicability never read" to "`DoctrineStatement` carries no `applicability` field."

**Unchanged:** the Doctrine registry construction helper (§25) must reject, at build/test time, any attempt to register two `DoctrineStatement` entries for the same `concept` — v0 has no mechanism to choose between competing entries, so it must not be possible to create the ambiguity in the first place. Enforced by a registry-construction function that raises on a duplicate `concept`, never by a bare dict literal (which would silently keep only the last one).

## 13. Formula dependency input — corrected: bounded recursive forward closure [CORRECTED 2026-08-11]

**Original claim (now falsified):** single-hop forward extraction suffices for the core `MISMATCH` determination. **Falsified by the Composition Completeness / False-Mismatch Adversarial Review (2026-08-11), CASE B:** `EBITDA = Revenue - OPEX_TOTAL`, `OPEX_TOTAL = ExternalCosts + PersonnelCost`. A single-hop extractor sees only `OPEX_TOTAL` as EBITDA's direct reference. If `OPEX_TOTAL` is classified as its own concept (not `PERSONNEL_COST`), the old logic (`missing = {PERSONNEL_COST} - {OPEX_TOTAL}` is non-empty, and `unclassified_references` is empty because `OPEX_TOTAL` *was* successfully classified — just not as `PERSONNEL_COST`) returns **`MISMATCH`**, even though `PersonnelCost` is genuinely, transitively present one level down. This is a false `MISMATCH`, and it directly violates this document's own governing invariant (§37 amendment, below): *a `MISMATCH` may be emitted only when a required concept is proven absent from the economically relevant composition, not merely absent from direct formula references.* The original claim's error was conflating two independent facts (see §16, corrected): "this reference has been identified as concept X" does **not** imply "this reference's own internal composition has been fully examined for other concepts."

**Corrected design:** the extractor is retained as a primitive (`extract_cell_references`, single-hop, unchanged, still useful and still the base case) but is now invoked **recursively**, forming a **forward dependency closure** — not a graph engine (§33 reaffirms why not; see also Q6/Q8 in the §38 amendment record). Every cell reachable by repeatedly following formula references from the root cell is visited; recursion terminates at any cell with no formula (a `RAW_INPUT` cell, per Observation Structure v0's own `derivation_status`, which already exists and is reused here without modification) and is guarded by a `visited`/on-stack cycle detector (a detected cycle marks the closure incomplete, never crashes, never silently ignores the cycle):

```python
def resolve_composition(
    root_cell: str,
    get_formula: Callable[[str], str | None],   # None => RAW_INPUT, terminal
    classify_cell: Callable[[str], ConceptId | None],  # None => unclassifiable
) -> "ObservedComposition":
    resolved: set[ConceptId] = set()
    unclassified: set[str] = set()
    complete = True
    on_stack: set[str] = set()
    done: set[str] = set()

    def expand(cell: str) -> None:
        nonlocal complete
        if cell in done:
            return                      # diamond dependency, already fully resolved -- not a cycle
        if cell in on_stack:
            complete = False            # true cycle -- fail closed, never guess, never loop
            return
        on_stack.add(cell)
        concept = classify_cell(cell)
        if concept is not None:
            resolved.add(concept)
        else:
            unclassified.add(cell)
            complete = False
        formula = get_formula(cell)
        if formula is not None:         # FORMULA_DERIVED: must expand fully, regardless of
            for ref in extract_cell_references(formula):   # its own classification (§16) --
                expand(ref)                                   # an aggregate label never excuses
        on_stack.discard(cell)                                # skipping its own composition
        done.add(cell)

    root_formula = get_formula(root_cell)
    if root_formula is not None:
        for ref in extract_cell_references(root_formula):
            expand(ref)
    return ObservedComposition(
        directly_referenced_concepts=frozenset(resolved),
        unclassified_references=frozenset(unclassified),
        composition_complete=complete,
    )
```

**[CORRECTED 2026-08-11 Final Semantic Arbitration] No `max_depth` parameter.** The original design carried an unjustified constant (`max_depth: int = 8`) with no evidence behind the specific value — a real defect the mission asked to either justify or remove; no justification exists, so it is removed from the domain contract entirely (see §13a below for the full termination-mechanism derivation). Termination is now guaranteed solely by the `on_stack` cycle guard plus the `done` memoization operating over any real workbook's finite cell universe — no depth bound is needed for correctness.

**Terminology corrected:** the prior draft called this "single-direction DAG traversal with a fail-closed cycle guard" — self-contradictory, since a true DAG has no cycles and would need no guard against them. Corrected, precise name: **forward dependency traversal with cycle detection**. The input is *expected* to be acyclic (Excel disallows circular references by default), but this is not *assumed* — the cycle guard exists precisely because that expectation is not itself proven for every possible input file (a legacy file with iterative calculation enabled, or a corrupted/hand-edited file, could violate it), and a violation must fail closed (`UNKNOWN`), not crash or silently misreport.

**Deterministic, terminating, single-direction (forward only), no fixed-point iteration, no backward inference** — still not a graph engine (§33). **The backward ("referenced-by") index remains out of scope, unchanged from the original contract** — it was never the gap CASE B exposed; the gap was insufficient forward depth, not a missing direction.

## 13a. Termination mechanism — derived, not assumed [2026-08-11 Final Semantic Arbitration]

**Question:** is a `visited`/`on_stack` cycle guard, operating over a finite workbook cell universe, already sufficient to guarantee termination, without any depth constant? **Answer: yes, derived as follows.** Any real workbook contains a finite number of cells, `N`. `resolve_composition`'s recursion visits a given cell at most once per active call stack (`on_stack` guard: a repeat within the current path stops immediately) and, once fully resolved, never re-expands it from a different path (`done` memoization: a repeat via a different path is a diamond dependency, not a cycle, and is skipped without re-walking its subtree). Therefore the total number of `expand()` invocations across an entire `resolve_composition` call is bounded by `N`, regardless of the reference graph's shape — acyclic, cyclic, deeply chained, or richly diamond-shaped. No depth constant is required to prove this; it follows directly from the two set-guards plus the finiteness of the workbook.

**What, if anything, remains a legitimate concern?** Only a *runtime engineering* one, entirely separate from domain semantics: a sufficiently large or pathologically shaped real-world workbook could still make a naive **recursive** (call-stack-based) Python implementation hit Python's own interpreter stack-depth limit (independent of any cycle — a very long but perfectly valid, finite, acyclic chain could do this) before it hits any semantic obstacle. This is a property of the chosen implementation technique (recursive function calls), not of the domain problem — an iterative, explicit-stack traversal (a straightforward, well-known rewrite of the same `expand()` logic using a manual stack instead of the Python call stack) sidesteps it entirely and is left as an implementation choice, out of scope for a documentation-only contract. **If, and only if, a future implementation chooses a recursive technique and therefore wants a defensive cutoff, that cutoff must be: (1) not a contract-level semantic constant — no number belongs in this document; (2) framed explicitly as an engineering safety limit, never as "financial doctrine"; (3) required, without exception, to yield `UNKNOWN` (via `composition_complete=False`) if triggered, never to be silently treated as proof of absence.** This document does not specify such a cutoff, does not need to, and explicitly declines to invent one merely to have a number on the page.

## 13b. Required-concept-scoped completeness — challenged and rejected for v0 [2026-08-11 Final Semantic Arbitration]

**Question:** must `composition_complete` require *every* reachable node to carry *some* classification, or could it require only that *no unresolved reachable node could still conceal a required concept* — e.g. treating a node classified `TAX` or `DEPRECIATION` as irrelevant to a `PERSONNEL_COST` membership test, and not demanding its own children be resolved?

**The narrower formulation is the semantically correct target** — it is precisely what a human professional means by "I've looked everywhere payroll could plausibly be." **It is not achievable in v0 without fabricating knowledge Pepperyn does not have.** To treat a `TAX`-classified branch as safely ignorable for a `PERSONNEL_COST` check requires asserting that `TAX` and `PERSONNEL_COST` are semantically disjoint — that no `TAX`-labeled aggregate could ever, in any real file, nest a reference to personnel cost. That is a taxonomy-level disjointness relation, and Concept Vocabulary v0 is deliberately flat with no is-a or exclusion relations (§9, §24) — inventing one here, even implicitly, to shrink the completeness check, would reintroduce exactly the premature ontology this whole document line has repeatedly rejected. Nor is it structurally safe to substitute "classified as something else" for "provably cannot contain X": a classification only names a cell's own identity; per §16, it says nothing about whether that cell's own formula (if it has one) has been examined — so even a `TAX`-classified aggregate cell must still have its own composition expanded before it can be excluded from suspicion, exactly as any other aggregate.

**Resolution: retain the conservative global rule** — `composition_complete` requires every reachable node in the closure to be classified (and no cycle to remain unresolved), full stop, with no concept-specific narrowing. **This is not the same failure the MATCH/MISMATCH asymmetry (§16a) already avoids**: §16a's shortcut is a purely logical one (an existential claim needs only one witness) that requires no semantic knowledge at all; the narrowing challenged here would require *domain* knowledge about which concepts can and cannot co-occur, which is a different, and currently unavailable, kind of fact. The mission's own instruction is followed exactly: the narrower formulation is impossible to prove without a taxonomy, so it is not fabricated, and the conservative global rule is retained. The practical cost is bounded and already the safe direction to err: some closures that a human would call "obviously complete enough" will still report `UNKNOWN` in v0 rather than `MISMATCH` — never the reverse.

## 14. Economic Meaning prerequisite — resolved via test fixture, not a classifier

Chosen explicitly: **pattern A — a deterministic test fixture supplies pre-classified concepts as given inputs.** No Golden-Case-only classifier is built (rejecting pattern B), no existing FRU/Observation primitive is repurposed for semantic classification (rejecting C, since none currently perform natural-category classification — Observation Structure v0 is deliberately non-semantic, §14 of its own contract). This keeps *"Doctrine works given concept-classified inputs"* strictly separate from *"Economic Meaning correctly classifies payroll"* — the latter is not this slice's problem and is not tested by it. The fixture asserts, as given: *"row 133's formula references cells C35 and C132; neither has been classified `PERSONNEL_COST`; both classifications are confidently known (not merely absent)."* No concept identifiers for what C35/C132 *are* need to be invented or registered in Vocabulary — the fixture only needs to assert what they are **not**, and that this determination is *known*, not *missing* (§16).

## 15. Comparison function — types and semantics, precise

```python
@dataclass(frozen=True)
class ObservedComposition:
    directly_referenced_concepts: frozenset[ConceptId]
    # Concepts CONFIRMED PRESENT anywhere in the FULLY EXPANDED forward
    # dependency closure (§13, corrected 2026-08-11) -- not merely the
    # root formula's direct references. Populated by resolve_composition.
    unclassified_references: frozenset[str]
    # DIAGNOSTIC ONLY (corrected 2026-08-11): cell coordinates anywhere in
    # the closure whose concept could not be classified. Retained for
    # render_explanation (§10); no longer read by compare_against_doctrine
    # (composition_complete, below, is the decision-bearing signal).
    composition_complete: bool
    # NEW FIELD (2026-08-11 correction). True only if EVERY cell reachable
    # via the forward closure was successfully classified AND no depth
    # limit / cycle was hit. False on any unresolved branch. This is the
    # field that actually distinguishes "known absent" from "not fully
    # examined" -- see §16.

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
    if not observed.composition_complete:      # CORRECTED 2026-08-11: was
        return "UNKNOWN"                        # `if observed.unclassified_references:`
    return "MISMATCH"
```

**[AMENDED 2026-08-11]** The branch condition changed from testing `unclassified_references` directly to testing `composition_complete`. The two are related but not identical: `composition_complete` is `False` whenever *any* cell in the closure is unclassified, *or* a depth limit was hit, *or* a cycle was detected — a strict superset of failure modes `unclassified_references` alone could signal. Using the narrower field as the gate (the original design) would have let a depth-cutoff or cycle silently fall through to `MISMATCH` — a second false-mismatch path, distinct from CASE B, closed by this same correction.

**Definitions, rigorous, matching the mission's own required precision [corrected 2026-08-11; asymmetry made explicit 2026-08-11 Final Semantic Arbitration]:**
- **`MATCH`:** the doctrine entry's concept applies (`candidate_concept == doctrine.concept`), and every required prior deduction is confirmed present *somewhere in the (possibly still-incomplete) forward closure*. **`composition_complete` is never consulted for `MATCH`** — positive proof does not require global completeness (§16a).
- **`MISMATCH`:** the concept applies, at least one required prior deduction is confirmed *absent from the entire closure* — provable only once the closure is fully resolved (`composition_complete == True`) — and no unresolved branch could be hiding it.
- **`NOT_APPLICABLE`:** the candidate concept confidently differs from the doctrine entry's own concept — the wrong entry to even ask.
- **`UNKNOWN`:** the concept applies, but absence cannot be proven honestly because the closure is incomplete (an unclassified cell or a detected cycle — `composition_complete == False`).

**No numeric confidence anywhere in this function or its inputs.** **Formalization, validated (not merely accepted) by CASE A/B/C of the 2026-08-11 Final Semantic Arbitration:** `required ⊆ observed → MATCH`; `required ⊄ observed AND composition_complete → MISMATCH`; `required ⊄ observed AND NOT composition_complete → UNKNOWN`. This is set-notation for exactly the `missing`-based logic already in the pseudocode above — confirmed equivalent, not a new rule.

## 16. MISMATCH safety — the load-bearing distinction, corrected and made structural [CORRECTED 2026-08-11]

**Original design (insufficient, per CASE B):** `ObservedComposition` carried two sets, with `unclassified_references` gating `MISMATCH` vs. `UNKNOWN`. This correctly separated "known absent" from "not identified" for the single-hop case, but it conflated a second, independent pair of facts that CASE B exposes: **"this reference has been classified as concept X"** does **not** imply **"this reference's own internal formula has been examined for other concepts."** A cell classified as `OPEX_TOTAL` (found, not unclassified) can still contain `PERSONNEL_COST` one level deeper — the original design had no way to represent "classified, but not yet expanded," so it silently treated *any* classified-but-non-matching reference as final, proof-grade absence. That is the false-`MISMATCH` mechanism CASE B demonstrates.

**Derived answer to "does a classified aggregate imply its children are fully known?" — NO**, and this must be derived, not assumed: concept identity (*what a cell represents*) and composition resolution (*whether that cell's own formula has been fully expanded*) are orthogonal facts. Classifying a cell is necessary but not sufficient to rule out nested occurrences of the required concept beneath it.

**Corrected representation:** `composition_complete: bool` (§15) is the single, load-bearing decision field, produced only by fully expanding the forward closure (§13) — never by inspecting the root formula's direct references alone, and never inferred from a reference's own concept label. `unclassified_references` is retained but demoted to a diagnostic/explanatory field only. `directly_referenced_concepts` is retained but its scope is corrected from "root formula's direct references" to "every concept found anywhere in the closure." This remains the smallest representation that preserves the distinction: two sets plus one boolean, no epistemic graph, no per-concept confidence score, no fixed-point computation.

## 16a. MATCH/MISMATCH asymmetry — required and derived [2026-08-11 Final Semantic Arbitration]

**Question attacked:** must `composition_complete` be required equally for `MATCH` and `MISMATCH`? **Strong hypothesis under attack:** positive proof of a required concept is sufficient for `MATCH` even when unrelated composition remains incomplete. **Survives the attack — confirmed true, derived from professional semantics, not assumed:**

Proving a required concept is *present* is an **existential** claim — "personnel cost appears somewhere in this composition" — settled the instant one confirmed occurrence is found; nothing else in the closure needs to be looked at. Proving a required concept is *absent* is a **universal** claim — "personnel cost appears nowhere in this composition" — which cannot be honestly settled until every branch that could conceivably contain it has been examined. This is the same asymmetry a human reviewer applies: an accountant who spots a payroll line item already subtracted does not need to also classify every other line on the statement to conclude payroll was deducted; but to conclude payroll was **never** deducted, the same accountant must have looked at (or have good reason to trust the absence from) the whole calculation, not just part of it.

**Consequence, already present but not previously made explicit:** `compare_against_doctrine` (§15) checks `missing = required - observed` and returns `MATCH` immediately if empty — **before** `composition_complete` is ever read. This was already the code's behavior; this arbitration makes it an explicit, justified design rule rather than an implicit side effect of statement ordering, and adds CASE A (§20a) as the regression test that pins it down.

**CASE A worked example:** `EBITDA → OPEX_TOTAL → {PERSONNEL_COST (found), UNKNOWN_COMPONENT (unresolved)}`. `directly_referenced_concepts = {OPEX_TOTAL, PERSONNEL_COST}`, `unclassified_references = {<UNKNOWN_COMPONENT cell>}`, `composition_complete = False`. `required = {PERSONNEL_COST}`. `missing = {PERSONNEL_COST} - {OPEX_TOTAL, PERSONNEL_COST} = ∅` → `MATCH`, `composition_complete`'s `False` value is computed but never consulted. Correct: the unresolved, unrelated `UNKNOWN_COMPONENT` cannot retroactively un-find personnel cost.

**Does this let "irrelevant" incompleteness leak into a false MISMATCH anywhere?** No — by construction, `composition_complete` is only ever consulted in the branch where `missing` is non-empty, i.e. exactly when a genuine open question remains about whether an unresolved part of the closure could still contain a required concept. It is never consulted, and therefore never at risk of over-demanding irrelevant completeness, in the branch where the answer is already positively known.

## 17. Row 133 — the Golden Case, fully specified

```python
candidate_concept = "EBITDA"          # given: caption self-declares it (Vocabulary lexical match, §5)
doctrine = EBITDA_DOCTRINE            # concept="EBITDA", required_prior_deductions=("PERSONNEL_COST",)
observed = ObservedComposition(
    directly_referenced_concepts=frozenset(),   # PERSONNEL_COST confirmed absent from the
                                                  # FULLY EXPANDED closure of C35 and C132 --
                                                  # neither cell nor anything they recursively
                                                  # reference (§13) resolves to PERSONNEL_COST
    unclassified_references=frozenset(),        # diagnostic only (§16) -- nothing unresolved
    composition_complete=True,                  # [NEW FIELD, 2026-08-11] the closure was fully
                                                  # expanded; this is what licenses MISMATCH
)
# compare_against_doctrine(candidate_concept, doctrine, observed) == "MISMATCH"
```

Every ingredient traces to its owner (§2 of `CANONICAL_FINANCIAL_DOCTRINE_COMPUTABILITY_REVIEW.md`, reapplied): raw cell content (Evidence), the forward dependency closure (§13, corrected 2026-08-11), the concept hypothesis (Vocabulary lexical match, §5), the `PERSONNEL_COST`-absence fact (test fixture standing in for Economic Meaning, §14), the doctrine entry (§8), the comparison (§15). **No hand-coded "row 133 is wrong" branch anywhere** — the result falls out of the general-purpose comparison function given these inputs, nothing else. **Note (2026-08-11):** row 133's real composition happens to terminate within the closure without ever reaching the personnel-cost rows (134-160 are outside C35's and C132's reference ranges), so the corrected recursive design reaches the identical, now more rigorously justified, `MISMATCH` — the Golden Case's expected result is unchanged, but its proof is stronger.

## 18. MATCH counter-case

```python
observed_match = ObservedComposition(
    directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
    unclassified_references=frozenset(),
    composition_complete=True,
)
# compare_against_doctrine("EBITDA", doctrine, observed_match) == "MATCH"
```

Identical function, identical `candidate_concept`, identical `doctrine` — only the economically relevant input changed. No separate branch, per §11 of the mission.

## 19. UNKNOWN adversary

```python
observed_unknown = ObservedComposition(
    directly_referenced_concepts=frozenset(),
    unclassified_references=frozenset({"C132"}),   # this cell's concept could not be determined
    composition_complete=False,                     # [CORRECTED 2026-08-11] the decision-bearing
                                                       # field; unclassified_references alone no
                                                       # longer drives the branch (§15)
)
# compare_against_doctrine("EBITDA", doctrine, observed_unknown) == "UNKNOWN"
```

Not `MISMATCH` — mandatory, per §16.

## 20. NOT_APPLICABLE adversary

```python
# compare_against_doctrine("REVENUE", doctrine, observed_anything) == "NOT_APPLICABLE"
```

The `EBITDA` doctrine entry is never forced onto an observation confidently hypothesized as a different concept, regardless of what `observed` contains — the concept check short-circuits first.

## 20a. Nested composition adversarial cases — Composition Completeness Review, 2026-08-11

Required by the mission's CASE A-E; not part of the original 20-subsection structure, appended here as the direct product of this review.

**CASE A — direct deduction.** `EBITDA = Revenue - PersonnelCost`, `PersonnelCost` a direct, terminal (`RAW_INPUT` or otherwise non-aggregate) reference, classified `PERSONNEL_COST`.
```python
resolve_composition(...) == ObservedComposition(
    directly_referenced_concepts=frozenset({"PERSONNEL_COST"}),
    unclassified_references=frozenset(), composition_complete=True,
)
# -> MATCH.  Identical in substance to §18; confirms the corrected mechanism
# reproduces the simple, non-nested case exactly as before.
```

**CASE B — nested deduction (the falsifying case).** `EBITDA = Revenue - OPEX_TOTAL`, `OPEX_TOTAL = ExternalCosts + PersonnelCost`, both `OPEX_TOTAL` and `PersonnelCost` cells fully classified.
```python
# resolve_composition expands OPEX_TOTAL (FORMULA_DERIVED) into ExternalCosts + PersonnelCost,
# regardless of OPEX_TOTAL's own classification (§16: a label never excuses skipping expansion).
resolve_composition(...) == ObservedComposition(
    directly_referenced_concepts=frozenset({"OPEX_TOTAL", "EXTERNAL_COSTS", "PERSONNEL_COST"}),
    unclassified_references=frozenset(), composition_complete=True,
)
# -> MATCH.  The original single-hop design returned MISMATCH here -- falsified, corrected (§13/§15/§16).
```

**CASE C — nested unknown.** `OPEX_TOTAL` exists but at least one of its own components cannot be resolved (unclassifiable cell, or its formula cannot be parsed).
```python
resolve_composition(...) == ObservedComposition(
    directly_referenced_concepts=frozenset({"OPEX_TOTAL"}),
    unclassified_references=frozenset({"<unresolved cell>"}), composition_complete=False,
)
# -> UNKNOWN, never MISMATCH. Confirms composition_complete (not unclassified_references
# alone, and not "OPEX_TOTAL was classified") is what gates the branch.
```

**CASE D — nested known absence.** `OPEX_TOTAL` composition fully resolved, contains `EXTERNAL_COSTS` only; `PERSONNEL_COST` confirmed absent from the entire two-level closure.
```python
resolve_composition(...) == ObservedComposition(
    directly_referenced_concepts=frozenset({"OPEX_TOTAL", "EXTERNAL_COSTS"}),
    unclassified_references=frozenset(), composition_complete=True,
)
# -> MISMATCH.  This is the corrected, honest form of a true mismatch: proven only because
# the FULL closure (not just OPEX_TOTAL's own label) was examined and found not to contain it.
```

**CASE E — multiple levels.** `EBITDA -> OPERATING_COSTS -> STAFF_AND_SERVICES -> PERSONNEL_COST`, three hops deep.
```python
# resolve_composition recurses through OPERATING_COSTS and STAFF_AND_SERVICES in turn;
# PERSONNEL_COST is found at depth 3. [2026-08-11: no max_depth constant exists any
# longer, per §13/§13a -- termination is guaranteed by the cycle guard alone, so depth
# 3 requires no special headroom check at all.]
# -> MATCH, by the same unmodified recursive mechanism -- no case-specific handling.
```
CASE E's only purpose is to confirm the mechanism is depth-generic, not case-specific — it was never gated by any fixed hop count, and, after the §13 correction, is not gated by any constant at all.

**CASE A — MATCH despite an irrelevant incomplete branch [2026-08-11 Final Semantic Arbitration].** `EBITDA → OPEX_TOTAL → {PERSONNEL_COST (found), UNKNOWN_COMPONENT (unresolved)}`. Worked in full in §16a. `composition_complete=False` (the `UNKNOWN_COMPONENT` branch), yet the result is `MATCH`, because `compare_against_doctrine` never consults `composition_complete` once `missing` is already empty. This is the regression test proving the MATCH/MISMATCH asymmetry (§16a) is real, not accidental.

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

## 27. Test contract [extended 2026-08-11]

1. **Golden Case** — row 133 inputs (§17) → `MISMATCH`.
2. **MATCH counter-case** (§18) → `MATCH`, same function, same path.
3. **UNKNOWN adversary** (§19) → `UNKNOWN`, never `MISMATCH`.
4. **NOT_APPLICABLE adversary** (§20) → `NOT_APPLICABLE`.
5. **Vocabulary lexical match** — `"EBITDA"`, `"Ebitda"`, `"ebitda"` all resolve to concept `EBITDA` **via normalization** (corrected 2026-08-11: not via stored alias lookup — assert the registered `lexical_aliases` tuple for `EBITDA` is empty while the match still succeeds).
6. **Vocabulary boundary negative test** — `"Rémunérations"` matches **no** Vocabulary concept, normalized or aliased (proves §5/§23's boundary holds, not merely asserted).
7. **Registry uniqueness** — constructing a Doctrine registry with two entries sharing `concept="EBITDA"` raises, never silently overwrites (§12).
8. **[CORRECTED 2026-08-11] `applicability` is not a field** — a structural/introspection test asserting `"applicability" not in {f.name for f in dataclasses.fields(DoctrineStatement)}` (replaces the original "applicability never read" test, made structurally stronger — the field cannot be read because it no longer exists).
9. **No stored prose field** — `DoctrineStatement.__dataclass_fields__` contains no `proposition`-shaped field (mirrors `test_formula_evidence.py`'s `TestNoNumericValueProduction` pattern exactly).
10. **`render_explanation` is deterministic and derived** — same input, same output, byte-for-byte, across repeated calls.
11. **Formula extractor, single-hop primitive** — `extract_cell_references("=C35-C132") == frozenset({"C35","C132"})`; the primitive itself still does not recurse (recursion is `resolve_composition`'s responsibility, tested separately, per test 13).
12. **Provenance/version presence** — every populated entry (Vocabulary and Doctrine) has non-empty `provenance` and an integer `version`.
13. **[NEW 2026-08-11] Nested MATCH (CASE B)** — `resolve_composition` over a two-level `EBITDA -> OPEX_TOTAL -> PersonnelCost` fixture yields `PERSONNEL_COST` in `directly_referenced_concepts` despite it never being a direct reference of the root formula; `compare_against_doctrine` on the result → `MATCH`. **This is the regression test that would have caught the falsified original design.**
14. **[NEW 2026-08-11] Nested UNKNOWN (CASE C)** — an unresolvable component inside `OPEX_TOTAL` forces `composition_complete=False` → `UNKNOWN`, never `MISMATCH`.
15. **[NEW 2026-08-11] Nested MISMATCH (CASE D)** — `OPEX_TOTAL` fully resolved, contains only `EXTERNAL_COSTS` → `composition_complete=True`, `PERSONNEL_COST` absent from the full closure → `MISMATCH`.
16. **[NEW 2026-08-11] Multi-level closure (CASE E)** — a three-hop chain resolves `PERSONNEL_COST` at depth 3 without depth-specific code paths → `MATCH`.
17. **[NEW 2026-08-11] Cycle guard** — a synthetic self-referencing or mutually-referencing formula pair does not infinite-loop; `composition_complete=False`, function returns, never raises `RecursionError` (proves the `on_stack` guard alone is sufficient — no depth constant involved, §13a).
18. **[CORRECTED 2026-08-11 Final Semantic Arbitration] Deep-but-valid finite chain terminates without a depth constant** — a synthetic acyclic chain of at least 9 hops (deliberately exceeding the old, now-removed, `max_depth=8`) resolves correctly to `MATCH`/`MISMATCH` as appropriate, proving termination and correctness do not depend on any fixed hop count. (Replaces the original "depth-bound guard" test, which tested a constant this correction removes.)
19. **[NEW 2026-08-11] Diamond dependency is not miscounted as a cycle** — the same cell referenced from two different branches of the same closure is resolved once (memoized via `done`), and does **not** set `composition_complete=False`.
20. **[NEW 2026-08-11 Final Semantic Arbitration] MATCH ignores an irrelevant incomplete branch (CASE A, §20a)** — a required concept found positively, alongside a separate unresolved/unclassifiable branch, still yields `MATCH`; asserts `composition_complete=False` was computed but did not gate the result. **This is the test that pins down the MATCH/MISMATCH asymmetry (§16a) as an explicit, protected contract, not an accident of statement ordering.**
21. **[NEW 2026-08-11 Final Semantic Arbitration] `resolve_composition` accepts no `max_depth` parameter** — a structural/introspection test asserting the function's signature carries no depth-related parameter, keeping the domain contract honest that no such constant exists.

## 28. Estimated production file impact (future implementation, not built here)

- `backend/services/concept_vocabulary.py` (new) — `ConceptEntry`, the Vocabulary registry, lexical-match helper.
- `backend/services/financial_doctrine.py` (new) — `DoctrineStatement`, `AuthorityType`, the Doctrine registry (with duplicate-`concept` guard), `ObservedComposition`, `compare_against_doctrine`, `render_explanation`.
- `backend/services/formula_reference_extractor.py` (new) — `extract_cell_references` (single-hop primitive, unchanged) **and** `resolve_composition` (bounded recursive forward closure, [corrected 2026-08-11], §13) — same file, since the closure is built directly on top of the primitive and both are pure, dependency-free functions over formula strings and two injected lookups.
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
- Unknown or incomplete prerequisite classification → `UNKNOWN`, enforced by `composition_complete`, but **only when a required concept has not already been positively found** — `composition_complete` is never consulted once `missing` is empty (§16a: existential proof needs no completeness check; only the universal "confirmed absent" claim does).
- A detected cycle during forward closure expansion → `composition_complete=False`, never a crash, never a silent misreport (§13, §13a, tests 17/19, §27). **[CORRECTED 2026-08-11 Final Semantic Arbitration]** No depth-cutoff exists any longer — termination is guaranteed by the cycle guard alone (§13a); if a future implementation adds an engineering-only recursion-depth safety cutoff, it must independently fail closed to `UNKNOWN` and must never appear as a domain-level constant in this contract.
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

## 36. Named reservations [updated 2026-08-11]

- The construction-time cross-validation between Vocabulary and Doctrine registries (§33, "malformed doctrine reference") introduces a small, explicit build-time coupling between two otherwise-separate modules — named, not hidden, and testable, but worth flagging as the one place these two small registries must agree with each other.
- `applicability` moved out of the executable object entirely (§12, corrected 2026-08-11) — its eventual computable form remains genuinely undesigned, now even more clearly deferred since it is not even a data field to design around.
- The backward ("referenced-by") dependency index remains named but unbuilt (§13) — a real, if optional, enhancement to future explanation quality, not required for correctness; **reaffirmed unchanged by this review**, since the CASE B gap was forward-depth, not direction.
- **[REMOVED 2026-08-11 Final Semantic Arbitration]** The prior reservation about `max_depth=8` being an unjustified constant is now moot — the constant itself was removed from the domain contract (§13/§13a), not merely re-justified. No depth constant remains anywhere in this document.
- **[NEW 2026-08-11]** If a future *implementation* chooses a recursive (rather than iterative/explicit-stack) technique for `resolve_composition` and therefore wants a defensive recursion-depth safety cutoff for engineering reasons, that cutoff is an implementation-level concern, must never be presented as a domain/semantic constant, and must fail closed to `UNKNOWN` if triggered (§13a). This document deliberately specifies no such number.
- **[NEW 2026-08-11]** The narrower, required-concept-scoped completeness definition (§13b) — "no unresolved node could conceal a required concept" — is the semantically ideal target but is not provable in v0 without a concept-disjointness/taxonomy fact Pepperyn does not have. Named as a real, deliberately deferred future refinement, not fabricated now.
- Diamond-dependency memoization (`done` set in `resolve_composition`) is an implementation-level correctness detail for this contract's own pseudocode, not a new architectural concept — flagged so a future implementer does not mistake ordinary DAG memoization for graph-engine machinery.

## 37. Implementation recommendation [reaffirmed 2026-08-11, twice]

**GO — with two rounds of adversarial attack now completed and two real defects corrected before any code was written.** Round 1 (§13/§15/§16) found and fixed a false-`MISMATCH` path under nested composition. Round 2 (§16a, §13/§13a/§13b) found and fixed an unjustified `max_depth` constant (removed entirely, replaced by a derived termination proof) and made an already-correct-but-implicit MATCH/MISMATCH asymmetry explicit, tested, and protected against regression. No further semantic gap was found; the narrower, taxonomy-dependent completeness refinement (§13b) was deliberately not built, for the same reason no ontology has been built anywhere in this document line — it is not yet demonstrated necessary or safely provable. Every field, every function, every test case traces to a specific requirement demonstrated by the row-133 experiment or an adversarial counter-case; nothing is speculative, and nothing remaining is arbitrary.

---

## 38. AMENDMENT — Composition Completeness / False-Mismatch Adversarial Review (2026-08-11)

**Invariant attacked:** a `MISMATCH` may be emitted only when Pepperyn can prove a required concept is absent from the economically relevant composition — not merely absent from direct formula references. **Result: the invariant did not hold in the original contract.** CASE B (nested deduction) produced a false `MISMATCH`. Corrected in place (§8, §12, §13, §15, §16, §17-20, §20a, §27, §33, §36, §37 above).

**Explicit answers to the eight required questions:**

1. **Is `directly_referenced_concepts` sufficient?** No, not with single-hop scope. Corrected to mean "every concept found in the fully expanded closure" (§15/§16) — with that corrected scope, yes, it remains sufficient as the presence signal.
2. **Is `unclassified_references` sufficient?** No, not as the sole gating field — it could not distinguish "unclassified" from "classified as something else but not yet expanded" (the CASE B failure mode). Demoted to diagnostic-only; `composition_complete` is now the gating field (§15/§16).
3. **What exactly proves known absence?** A required concept is provably absent only when the entire forward dependency closure — every cell reachable by recursively following formula references from the root, terminating at raw inputs — has been fully classified, no branch was truncated by depth limit or cycle, and the concept does not appear anywhere in that closure (§16).
4. **Must composition carry a complete/incomplete state?** Yes — `composition_complete: bool`, added to `ObservedComposition` (§15). This is the central structural correction.
5. **Does a classified aggregate imply its children are fully known?** No — derived, not assumed, directly from the CASE B trace: classifying `OPEX_TOTAL` tells you its identity, not whether its own formula has been examined. Identity and composition-resolution are independent facts (§16).
6. **Is bounded recursive dependency traversal now demonstrated necessary?** Yes — demonstrated by CASE B (falsifies single-hop) and CASE E (falsifies any small fixed hop count). A generously-bounded (not graph-general) recursive forward closure is required (§13).
7. **Does this contradict the prior "single-hop only" decision?** It corrects an overclaim in that decision. The extractor primitive itself (`extract_cell_references`) is unchanged and still single-hop; what changed is that it must now be invoked recursively (`resolve_composition`) rather than exactly once. The *direction* (forward-only, no backward index) is reaffirmed unchanged — CASE B's gap was depth, not direction.
8. **Can the solution remain deterministic and graph-engine-free?** Yes. Bounded depth-first recursion over what is, in well-formed spreadsheets, a DAG, with a cycle guard that fails closed (→ `UNKNOWN`) rather than looping, requires no fixed-point iteration, no backward inference, no general graph algorithms — it is a closure computation, not a graph engine (§13, §33).

**Secondary arbitrations:**

- **Alias normalization vs. stored aliases:** normalization preferred, per the mission's own steer, and no demonstrated case in v0 requires a stored alias — `EBITDA`'s three case variants collapse to one normalization rule; `lexical_aliases` remains in the shape as a reserved escape hatch for a genuinely irreducible future case (e.g. acronym vs. full expansion), populated with zero entries today (§5).
- **`applicability` — executable field or documentary metadata:** corrected to documentary metadata only, removed from `DoctrineStatement` entirely (§8, §12). A field no function ever reads does not belong on an executable dataclass — the stronger invariant is now structural (the field cannot be misread because it does not exist), not merely observed.

**Nothing else in the contract was found unsound.** The correction is confined to formula-dependency scope and its two direct downstream consumers (`ObservedComposition`, `compare_against_doctrine`); the Vocabulary/Doctrine ownership boundary, the four-way result vocabulary, the governance model, the Git-only representation, and the fail-closed registry-uniqueness rule all survive unchanged.

---

## 39. AMENDMENT — Composition Completeness Final Semantic Arbitration (2026-08-11)

Target of this review: the correction committed at `ecdfe97`. Two newly introduced assumptions were tested to falsification-or-survival before any implementation could be authorized.

**1 — MATCH/MISMATCH asymmetry.** Survives: `composition_complete` is not, and must not be, required for `MATCH` — only for `MISMATCH`/`UNKNOWN`. Derived from the existential/universal proof asymmetry (§16a), not assumed. CASE A added as the protecting regression test (§20a, test 20, §27). The subset formulation `required ⊆ observed → MATCH; required ⊄ observed AND complete → MISMATCH; required ⊄ observed AND NOT complete → UNKNOWN` is confirmed equivalent to the existing `missing`-based pseudocode, not a new rule layered on top.

**2 — `max_depth=8`.** No justifying evidence existed. Removed entirely from the domain contract (§13, §13a) — not re-derived to a different number. Termination is guaranteed by the `on_stack` cycle guard plus `done` memoization operating over any real workbook's finite cell universe; this was proven, not assumed (§13a). Any future recursion-depth safety cutoff, if an implementation needs one for engineering reasons, is explicitly named as out-of-domain, must fail closed to `UNKNOWN`, and is not specified here.

**3 — DAG terminology.** Corrected throughout to "forward dependency traversal with cycle detection" (§13) — the prior "DAG traversal with a fail-closed cycle guard" was self-contradictory.

**4 — Required-concept-scoped completeness.** Challenged directly (§13b). The narrower formulation is the correct semantic target but is not provable in v0 without concept-disjointness/taxonomy knowledge that does not exist and was not fabricated. The conservative global completeness rule is retained, with the cost (occasional `UNKNOWN` where a human might feel confident) named as the deliberately safe direction to err.

```
POSITIVE PROOF SUFFICIENT FOR MATCH: YES
MATCH REQUIRES GLOBAL COMPLETENESS: NO
MISMATCH REQUIRES COMPLETENESS: YES
COMPLETENESS DEFINITION: entire reachable forward dependency closure classified (global, conservative) — not scoped to doctrine-relevant concepts only, per §13b
IRRELEVANT UNKNOWN COMPONENT: does not block MATCH (resolved by the §16a asymmetry, not by narrowing completeness); still blocks MISMATCH/UNKNOWN determination, since it cannot be ruled out without fabricated disjointness knowledge
REQUIRED-CONCEPT-SCOPED COMPLETENESS POSSIBLE: NO, not provable in v0 without a taxonomy -- conservative global rule retained
MAX_DEPTH_8 JUSTIFIED: NO evidence existed -- constant removed entirely, not re-justified
DEPTH LIMIT DOMAIN SEMANTIC: NO -- any depth-related cutoff, if ever added, is engineering-only, never domain semantics
TERMINATION MECHANISM: on_stack cycle guard + done memoization over a finite workbook cell universe -- proven sufficient without any depth constant
CYCLE BEHAVIOR: composition_complete=False, fail closed to UNKNOWN, never raises, never loops
DAG TERMINOLOGY: corrected to "forward dependency traversal with cycle detection" -- acyclicity is expected, not assumed
CONTRACT CORRECTION REQUIRED: YES -- applied in place on the same branch/document (§13, §13a, §13b, §15, §16a, §20a, §27, §33, §36, §37, this §39)
IMPLEMENTATION READINESS: GO
FINAL VERDICT: A
```

---

**CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT — ESTABLISHED, CORRECTED 2026-08-11 (twice). NO CODE WRITTEN. NO MERGE.**
