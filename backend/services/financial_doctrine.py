"""
financial_doctrine.py — Canonical Financial Doctrine v0.

Canonical contract: docs/Architecture/Cognitive/CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md
(merged main 2026-08-11, commit 2fc20bb; corrected ecdfe97 [composition
completeness / false-mismatch fix], fa2b7d9 [MATCH/MISMATCH asymmetry,
max_depth removal — Final Semantic Arbitration]).

RESPONSIBILITY (contract §2): answers exactly one question — "what does
this canonical concept conventionally or mathematically require, given
that a concept hypothesis already exists?" Never identifies a concept from
raw data (Vocabulary/Economic Meaning's job) — Doctrine validates an
already-formed hypothesis, never generates one.

WHAT THIS MODULE IS NOT:
  - Not a classifier, not Economic Meaning, not KnowledgeModel, not
    Epistemic Dialogue, not an LLM caller. Consumes already-classified
    canonical concepts only (contract §12/§21, mission §13/§31).
  - Not persistence. No DB, no migration, no Supabase, no network call.
    Git-versioned code only (contract §25/§31).
  - Not a graph engine, not a formal ontology (contract §9/§24/§33).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from services.concept_vocabulary import CONCEPT_VOCABULARY, ConceptId
from services.formula_reference_extractor import ObservedComposition

AuthorityType = Literal["MATHEMATICAL_IDENTITY", "PROFESSIONAL_CONVENTION"]

ComparisonResult = Literal["MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN"]


@dataclass(frozen=True)
class DoctrineStatement:
    """Contract §8 (corrected). Every field is read by at least one
    function in v0 — this is a structural invariant of the executable
    schema, not an accident:

      - `concept_aliases` does NOT exist here — moved entirely to
        Concept Vocabulary (contract §5/§8) to avoid two independently
        editable representations of the same alias fact.
      - `applicability` does NOT exist here — moved to documentary
        metadata only (a plain code comment, see the registry below),
        never a dataclass field, never parsed, never read by
        `compare_against_doctrine` (contract §12, corrected 2026-08-11).
      - `proposition: str` does NOT exist here — explanation is rendered
        from these structured fields (`render_explanation` below), never
        stored as independently-editable prose (contract §10).
    """

    id: str
    concept: ConceptId
    required_prior_deductions: tuple
    authority_type: AuthorityType
    provenance: str
    version: int


def _validate_concept_exists(concept_id: ConceptId, *, context: str) -> None:
    """Cross-registry validation (contract §7): every concept Doctrine
    references must exist in Concept Vocabulary. Fails at construction
    time — never a silent runtime fallback to an arbitrary string."""
    if concept_id not in CONCEPT_VOCABULARY:
        raise ValueError(
            f"Unknown concept {concept_id!r} referenced by {context} — "
            f"not registered in Concept Vocabulary."
        )


def _build_registry(statements: tuple) -> dict:
    """Fail-closed construction (contract §12/§25): duplicate `concept`
    entries raise, never silently overwrite. v0 has no mechanism to choose
    between competing entries for the same concept, so that ambiguity must
    never be constructible in the first place."""
    registry: dict = {}
    for stmt in statements:
        _validate_concept_exists(stmt.concept, context=f"DoctrineStatement {stmt.id!r} (concept)")
        for required in stmt.required_prior_deductions:
            _validate_concept_exists(
                required, context=f"DoctrineStatement {stmt.id!r} (required_prior_deductions)"
            )
        if stmt.concept in registry:
            raise ValueError(
                f"Duplicate doctrine entry for concept {stmt.concept!r} "
                f"(existing: {registry[stmt.concept].id!r}, new: {stmt.id!r}) — "
                f"v0 has no mechanism to choose between competing entries."
            )
        registry[stmt.concept] = stmt
    return registry


# applicability (documentary only, contract §12 — never a dataclass field,
# never parsed, never read by compare_against_doctrine):
#   EBITDA_REQUIRES_PERSONNEL_COST_DEDUCTED — general management /
#   financial-accounting convention (personnel/payroll cost is
#   conventionally deducted before an EBITDA subtotal), not a specific
#   GAAP/IFRS citation. Curator-facing prose only.
_DOCTRINE_STATEMENTS: tuple = (
    DoctrineStatement(
        id="EBITDA_REQUIRES_PERSONNEL_COST_DEDUCTED",
        concept="EBITDA",
        required_prior_deductions=("PERSONNEL_COST",),
        authority_type="PROFESSIONAL_CONVENTION",
        provenance=(
            "CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md §17 — "
            "Phidani row 133 Golden Case. Populate only PROFESSIONAL_CONVENTION "
            "in v0 (contract §11) — MATHEMATICAL_IDENTITY is declared in the "
            "AuthorityType literal for future extensibility but has no v0 entry."
        ),
        version=1,
    ),
)

DOCTRINE_REGISTRY: dict = _build_registry(_DOCTRINE_STATEMENTS)


def get_doctrine(concept_id: ConceptId) -> Optional[DoctrineStatement]:
    """Read-only lookup. No doctrine entry for a concept is a legitimate,
    honest state — never fabricated as MATCH or MISMATCH (contract §28:
    the caller must treat a missing entry as comparison-unavailable /
    UNKNOWN, never call `compare_against_doctrine` with a fabricated
    entry)."""
    return DOCTRINE_REGISTRY.get(concept_id)


def compare_against_doctrine(
    candidate_concept: ConceptId,
    doctrine: DoctrineStatement,
    observed: ObservedComposition,
) -> ComparisonResult:
    """Pure, deterministic (contract §15; asymmetry made explicit and
    protected 2026-08-11 Final Semantic Arbitration, contract §16a).

    `candidate_concept` is a precondition: a concept hypothesis MUST
    already exist. This function is never called with "no candidate" —
    that branch belongs to the caller (contract §29).

    `observed.composition_complete` is consulted ONLY in the branch where
    a required concept has not already been positively found. MATCH never
    reads it: proving a concept's presence is existential (one witness
    suffices); proving its absence is universal (the whole closure must be
    examined) — contract §16a.

    Never reads `doctrine.applicability` — that field does not exist on
    this dataclass at all (contract §12, corrected 2026-08-11).
    """
    if candidate_concept != doctrine.concept:
        return "NOT_APPLICABLE"
    missing = set(doctrine.required_prior_deductions) - set(observed.directly_referenced_concepts)
    if not missing:
        return "MATCH"
    if not observed.composition_complete:
        return "UNKNOWN"
    return "MISMATCH"


def render_explanation(doctrine: DoctrineStatement) -> str:
    """Mechanically derived from structured fields — never stored prose
    (contract §10). Deterministic: identical input always produces
    byte-for-byte identical output. Explanatory only: nothing in
    `compare_against_doctrine` consumes this function's output."""
    required = ", ".join(doctrine.required_prior_deductions) or "(none)"
    return (
        f"{doctrine.concept} conventionally requires the following already "
        f"deducted beforehand: {required}."
    )
