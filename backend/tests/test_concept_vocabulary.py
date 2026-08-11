"""
test_concept_vocabulary.py — services/concept_vocabulary.py.

Covers: normalization-based lexical matching, the semantic-alias negative
boundary (mission §3/§30 — the load-bearing test proving Vocabulary never
became a classifier), registry uniqueness, and provenance/version presence.

Classification (mission §35): each test is tagged INVARIANT, BEHAVIOR,
BOUNDARY, or WEAK/GUARD in its docstring.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from services.concept_vocabulary import (
    CONCEPT_VOCABULARY,
    ConceptEntry,
    _build_registry,
    get_concept,
    match_concept,
    normalize,
)


class TestNormalization:
    def test_casefold_and_strip(self):
        """BEHAVIOR."""
        assert normalize("EBITDA") == "ebitda"
        assert normalize("Ebitda") == "ebitda"
        assert normalize(" ebitda ") == "ebitda"

    def test_no_stored_case_aliases_needed(self):
        """INVARIANT (mission §3, contract §5 corrected 2026-08-11). The
        registered EBITDA entry carries zero stored lexical_aliases — case
        variance is handled entirely by normalize(), not enumeration."""
        entry = get_concept("EBITDA")
        assert entry.lexical_aliases == ()


class TestLexicalMatchResolvesThroughNormalization:
    @pytest.mark.parametrize("text", ["EBITDA", "Ebitda", " ebitda ", "ebitda"])
    def test_trivial_variants_all_resolve(self, text):
        """INVARIANT (mission §3/§30). Case/spacing variants must resolve
        through normalization, not stored case variants."""
        assert match_concept(text) == "EBITDA"

    def test_whole_word_match_inside_real_caption(self):
        """INVARIANT (contract §5/§17). Real Phidani row 133 caption:
        'Marge brute d'exploitation (EBITDA)' — the concept hypothesis is
        legitimately formed via a lexical, not semantic, match."""
        assert match_concept("Marge brute d'exploitation (EBITDA)") == "EBITDA"

    def test_no_match_returns_none_not_a_guess(self):
        """BOUNDARY (mission §30). An unknown label returns no concept
        rather than a nearest guess."""
        assert match_concept("Chiffre d'affaires net") is None


class TestSemanticAliasNegativeBoundary:
    """INVARIANT (mission §3/§13/§30, contract §5/§23 — the boundary this
    entire contract line repeatedly protects). Semantically-loaded
    synonyms must NEVER become Vocabulary mappings — that recognition
    belongs entirely to Economic Meaning, which is not implemented here."""

    @pytest.mark.parametrize(
        "synonym",
        [
            "Rémunérations",
            "Charges de personnel",
            "Payroll",
            "Charges Sociales - Pensions",
        ],
    )
    def test_semantic_synonyms_do_not_resolve_to_personnel_cost(self, synonym):
        assert match_concept(synonym) is None

    def test_ebitda_entry_carries_no_semantic_synonym_alias(self):
        """BOUNDARY. Direct inspection of the registered entry: no
        semantically-loaded string appears among its stored forms."""
        entry = get_concept("EBITDA")
        forbidden = {"marge brute d'exploitation", "operating cash earnings"}
        stored_forms = {normalize(a) for a in entry.lexical_aliases}
        assert stored_forms.isdisjoint(forbidden)

    def test_no_pcmn_account_code_rule_in_vocabulary(self):
        """BOUNDARY (mission §30). No account-code-to-concept rule (e.g.
        "62" -> PERSONNEL_COST) exists anywhere in the registry — Doctrine
        consumes already-classified concepts only."""
        assert match_concept("62") is None
        assert match_concept("620250") is None

    def test_no_multilingual_semantic_inference(self):
        """BOUNDARY. No translation/semantic-inference table exists."""
        assert match_concept("Personalkosten") is None  # German
        assert match_concept("costo del personale") is None  # Italian


class TestRegistryUniqueness:
    def test_duplicate_concept_id_rejected(self):
        """INVARIANT (mission §4/§29). Duplicate concept ids fail closed
        at construction time, never silently overwrite."""
        duplicate = (
            ConceptEntry(id="EBITDA", lexical_aliases=(), provenance="x", version=1),
            ConceptEntry(id="EBITDA", lexical_aliases=(), provenance="y", version=1),
        )
        with pytest.raises(ValueError):
            _build_registry(duplicate)

    def test_registry_immutable_no_runtime_mutation_api(self):
        """BOUNDARY (mission §29/§33). No function in this module offers a
        write/register/mutate operation."""
        import services.concept_vocabulary as mod

        public_names = [n for n in dir(mod) if not n.startswith("_")]
        write_like = [n for n in public_names if any(w in n.lower() for w in ("register", "add", "mutate", "update", "delete", "write"))]
        assert write_like == []


class TestUnknownIdentifier:
    def test_unknown_identifier_returns_none_never_fabricated(self):
        """INVARIANT (mission §4). Unknown identifiers fail closed —
        get_concept never fabricates an entry."""
        assert get_concept("NOT_A_REAL_CONCEPT") is None


class TestProvenanceAndVersion:
    def test_every_registered_concept_has_provenance_and_version(self):
        """BEHAVIOR (mission §35 item 20)."""
        for entry in CONCEPT_VOCABULARY.values():
            assert entry.provenance and isinstance(entry.provenance, str)
            assert isinstance(entry.version, int) and entry.version >= 1


class TestMinimalContent:
    def test_exactly_two_concepts_v0(self):
        """BOUNDARY (mission §2 — "do not add concepts for future
        convenience"). v0 registers exactly EBITDA and PERSONNEL_COST."""
        assert set(CONCEPT_VOCABULARY.keys()) == {"EBITDA", "PERSONNEL_COST"}
