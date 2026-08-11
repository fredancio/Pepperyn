"""
candidate.py — shared `Candidate`/`EvidenceItem` representation.

Canonical contract: docs/Architecture/Cognitive/PERSONNEL_COST_CLASSIFIER_V0_IMPLEMENTATION_CONTRACT.md
(§3/§4, corrected through commit c547ee5).

RELOCATION, NOT NEW ARCHITECTURE (contract §3): `Candidate` originated in
`fru_sign_convention_detector.py` (`value: Optional[str]`,
`tier: str ∈ {STRONG_INFERENCE, HYPOTHESIS, UNKNOWN}`) with no evidence
lists. `personnel_cost_classifier.py` is a second real consumer that
genuinely needs two more things `Candidate` could not previously
represent: (1) a `CONTRADICTION` tier value, and (2) `supporting_evidence`/
`contradicting_evidence` — the exact, bounded extension the prior
Economic Meaning arbitration named as required. Rather than defining a
second, independently-drifting `Candidate` shape inside the new
classifier module, this single shared module is the one place both
`fru_sign_convention_detector.py` and `personnel_cost_classifier.py`
import from — "relocate, do not duplicate" (implementation mission §4).

`fru_sign_convention_detector.py` re-exports `Candidate` from here for
full backward compatibility with its existing real consumers
(`epistemic_dialogue_service.py`, `backend/tests/test_epistemic_dialogue_v0.py`,
both of which do `from backend.services.fru_sign_convention_detector import
Candidate`) — nothing in FRU's own behavior changes: it never sets
`tier="CONTRADICTION"` and never populates the evidence-list fields, so
the extension is purely additive from FRU's point of view.

WHAT THIS MODULE IS NOT (contract §2/§34):
  - Not a generic `Hypothesis`/`Evidence` framework — exactly the two
    dataclasses below, nothing else.
  - No numeric confidence, probability, fuzzy membership, or hidden score
    anywhere on either dataclass (contract §4's own explicit prohibition).
  - No behavior, no methods beyond the dataclasses themselves — arbitration
    logic (family resolution, tier computation) lives in the consuming
    modules (`personnel_cost_classifier.py`'s `_arbitrate`), not here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EvidenceItem:
    """One piece of evidence a `Candidate` cites (contract §4).

    `source_type`: the exact signal that produced this item —
        "ACCOUNT_CODE_FAMILY" | "STRUCTURAL_POSITION" | "PARENT_CAPTION" |
        "CAPTION_LEXICAL" for the personnel-cost classifier; other future
        consumers may use their own `source_type` vocabulary.
    `source_pointer`: a cell-coordinate reference only (e.g. "C122") —
        never a copy of caption/formula text. Points back to the real
        source for audit; does not duplicate Evidence Ledger content.
    `origin`: "DETERMINISTIC" | "INTERPRETIVE". Every v0 signal in the
        personnel-cost classifier is DETERMINISTIC (contract §26, no LLM).
        Kept as a required field now (rather than added later) because a
        future open-vocabulary/LLM-assisted slice would need it and
        retrofitting it later would touch every existing evidence item.

    No stored numeric strength anywhere on this dataclass — strength is
    not a property of an individual item at all (contract §4/§6).
    """

    source_type: str
    source_pointer: str
    origin: str  # "DETERMINISTIC" | "INTERPRETIVE"


@dataclass(frozen=True)
class Candidate:
    """A classifier's output hypothesis (contract §3).

    `value`: the resolved classification, or `None` when unresolved
        (`UNKNOWN`) or in conflict (`CONTRADICTION`).
    `tier`: the epistemic tier — "STRONG_INFERENCE" | "HYPOTHESIS" |
        "CONTRADICTION" | "UNKNOWN". `CONTRADICTION` is a value on this
        existing field, never a new top-level class or a member of the
        same vocabulary as `value` (contract §3/§7 — "a status, not a
        third economic value").
    `supporting_evidence`: evidence for `value`'s specific claim.
    `contradicting_evidence`: evidence for the opposing claim — non-empty
        together with `supporting_evidence` only when `tier=CONTRADICTION`
        (contract §8's impossible-state table, enforced by
        `personnel_cost_classifier.py`'s own construction, not by a
        validator living in this module).

    Both evidence-list fields default to `()` so existing callers that
    construct a `Candidate` with only `value`/`tier` (FRU's own usage)
    continue to work unchanged.
    """

    value: Optional[str]
    tier: str  # "STRONG_INFERENCE" | "HYPOTHESIS" | "CONTRADICTION" | "UNKNOWN"
    supporting_evidence: tuple[EvidenceItem, ...] = ()
    contradicting_evidence: tuple[EvidenceItem, ...] = ()
