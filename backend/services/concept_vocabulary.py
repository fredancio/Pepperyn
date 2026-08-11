"""
concept_vocabulary.py — Concept Vocabulary v0.

Canonical contract: docs/Architecture/Cognitive/CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md
(merged main 2026-08-11, commit 2fc20bb; corrected ecdfe97, fa2b7d9).

RESPONSIBILITY (contract §2/§23): answers exactly one question — "which
canonical concept are we referring to?" Never "does this observed row
belong to that concept?" — that remains entirely Economic Meaning's job,
unimplemented here and untouched by this module (contract §13/§14).

WHAT THIS MODULE IS NOT:
  - Not a classifier. `match_concept` performs purely mechanical,
    normalized, whole-word lexical matching against registered
    identifiers and their (v0: empty) stored aliases — it never recognizes
    a semantically-loaded synonym ("Rémunérations" → PERSONNEL_COST). That
    boundary is load-bearing (contract §5/§23) and is enforced by a
    dedicated negative test in tests/test_concept_vocabulary.py.
  - Not a taxonomy, not a hierarchy, no is-a relation, no graph, no
    embeddings, no semantic search (contract §9/§24).
  - Not tenant-scoped, not runtime-writable. Read-only at runtime,
    Git-versioned, human-reviewed via ordinary PR (contract §7/§26).

LEXICAL NORMALIZATION, NOT STORED CASE ALIASES (contract §5, corrected
2026-08-11): case/spacing variance ("EBITDA" / "Ebitda" / " ebitda ") is
handled by `normalize()` (casefold + strip), never by enumerating each
variant as a stored alias. `ConceptEntry.lexical_aliases` is reserved for
a genuinely irreducible future case (e.g. an acronym vs. a full written-out
expansion) — v0's two registered concepts need zero entries there.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

ConceptId = str


@dataclass(frozen=True)
class ConceptEntry:
    """One canonical concept (contract §4/§6).

    `id` is a stable, human-readable, git-diffable identifier — no UUID, no
    hierarchy, no is-a relation.
    """

    id: ConceptId
    lexical_aliases: tuple[str, ...]
    provenance: str
    version: int


def normalize(text: str) -> str:
    """Deterministic lexical normalization (contract §5, corrected
    2026-08-11): casefold + strip. Covers case and surrounding-whitespace
    variance with no stored alias required. Pure, no I/O."""
    return text.strip().casefold()


_CONCEPT_ENTRIES: tuple[ConceptEntry, ...] = (
    ConceptEntry(
        id="EBITDA",
        lexical_aliases=(),
        provenance=(
            "CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md §5/§17 — "
            "EBITDA is the Golden Case's candidate concept, self-declared by "
            "Phidani row 133's caption ('Marge brute d'exploitation (EBITDA)')."
        ),
        version=1,
    ),
    ConceptEntry(
        id="PERSONNEL_COST",
        lexical_aliases=(),
        provenance=(
            "CANONICAL_FINANCIAL_DOCTRINE_V0_IMPLEMENTATION_CONTRACT.md §5/§17 — "
            "the required_prior_deductions target for the EBITDA doctrine entry. "
            "Not lexically matched against real Phidani captions in v0 (its "
            "presence/absence is supplied by a deterministic test fixture standing "
            "in for Economic Meaning, contract §14 Pattern A) — registered here "
            "only so Doctrine's cross-reference validation (contract §7) has a "
            "concept identifier to point at."
        ),
        version=1,
    ),
)


def _build_registry(entries: tuple[ConceptEntry, ...]) -> dict[ConceptId, ConceptEntry]:
    """Fail-closed construction (contract §12/§25): duplicate concept ids
    raise, never silently overwrite."""
    registry: dict[ConceptId, ConceptEntry] = {}
    for entry in entries:
        if entry.id in registry:
            raise ValueError(f"Duplicate concept id in Concept Vocabulary: {entry.id!r}")
        registry[entry.id] = entry
    return registry


CONCEPT_VOCABULARY: dict[ConceptId, ConceptEntry] = _build_registry(_CONCEPT_ENTRIES)


def get_concept(concept_id: ConceptId) -> Optional[ConceptEntry]:
    """Read-only lookup by canonical identifier. Unknown identifiers return
    None — never fabricated (fail closed)."""
    return CONCEPT_VOCABULARY.get(concept_id)


def _candidate_forms(entry: ConceptEntry) -> tuple[str, ...]:
    """The identifier plus its (v0: empty) stored aliases — the exact set
    of literal strings this concept can be lexically recognized by."""
    return (entry.id,) + entry.lexical_aliases


def match_concept(text: str) -> Optional[ConceptId]:
    """Lexical, whole-word, normalized match of `text` against every
    registered concept's identifier and stored aliases (contract §5/§6).

    Purely mechanical — casefold+strip equality of whole words, nothing
    semantic. This is the ONLY recognition mechanism Concept Vocabulary
    provides; it is deliberately incapable of recognizing a semantic
    synonym ("Rémunérations", "Charges de personnel", "Payroll") because no
    such mapping is stored here — that boundary belongs to Economic
    Meaning, out of scope for this slice (contract §5/§23, mission §3).

    Returns the first matching concept id (deterministic — registry
    iteration order is fixed at construction), or None if no registered
    concept's identifier/alias appears as a normalized whole word in
    `text`. Never guesses a "nearest" concept.
    """
    normalized_text = normalize(text)
    for entry in CONCEPT_VOCABULARY.values():
        for form in _candidate_forms(entry):
            pattern = r"\b" + re.escape(normalize(form)) + r"\b"
            if re.search(pattern, normalized_text):
                return entry.id
    return None
