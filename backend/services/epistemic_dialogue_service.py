"""
epistemic_dialogue_service.py — Epistemic Dialogue v0, first executable
vertical slice.

Scope, per `docs/Architecture/Cognitive/EPISTEMIC_DIALOGUE_V0_IMPLEMENTATION_CONTRACT.md`
(final arbitration, verdict A, canonical on `main` since `6dcfe17`): the
smallest complete loop proving Pepperyn can observe -> infer -> recall ->
compare -> decide whether to ask -> receive human clarification ->
validate it -> remember it -> reuse it -> detect contradiction later, for
exactly one subject (`EXPENSE_SIGN_CONVENTION`).

THIS IS NOT a general Epistemic Dialogue engine, NOT a general chat
system, NOT an LLM mission. It proves the cognitive loop end-to-end
before any of those are generalized (mission brief, 2026-08-09).

WHAT THIS MODULE DOES:
  - REASON: consumes a `Candidate` from `fru_sign_convention_detector`
    (this module never reasons about raw data itself).
  - RECALL: calls `knowledge_model_service.recall()` — the ONLY
    permitted interface into Knowledge Model, never reopened or
    reimplemented (contract's own explicit instruction).
  - COMPARE: this module's own, genuinely new logic (contract §3) —
    decides ASK / NO ASK / UNRESOLVED from RECALL's result and the
    Candidate.
  - `ClarificationNeed` construction — always AFTER `recall()` has
    already run in the same function body (RECALL-BEFORE-ASK, contract
    §6, verified structurally by `test_epistemic_dialogue_v0.py`'s
    AST-based test, not merely by convention).
  - Human answer interpretation (deterministic, this one subject only)
    and the four-stage authority gate (contract §9) before any
    `knowledge_model_service.confirm()` call.
  - Recovery from `ConcurrentRootConflictError`/`ChainBranchError`
    (contract §9's new paragraph, final arbitration 2026-08-09): never
    retries with the same value, never invents a winner — re-RECALLs
    and reconciles against whatever PostgreSQL actually confirmed.
  - A deterministic question-rendering helper (contract §8) — presentation
    wording, kept separate from the domain decision above it.

WHAT THIS MODULE NEVER DOES (negative contract):
  - No LLM call, anywhere, for any reason (verified structurally,
    `test_epistemic_dialogue_v0.py`).
  - No persistence of `ClarificationNeed` — ephemeral by design (contract
    §5), constructed fresh on every call, never written to any table.
  - No new migration, no new table — Knowledge goes into the existing
    canonical `knowledge_model` table only, via `confirm()`.
  - No coupling to `conversation_engine.py` or any chat surface — this
    module's public functions accept/return plain data, never a chat
    message object (contract §11, independently re-verified against the
    real file in the final arbitration).
  - No mutation of Knowledge — only ever calls `confirm()` (an insert),
    never anything resembling an update.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from backend.services.fru_sign_convention_detector import (
    ABSOLUTE_POSITIVE,
    SIGNED_NATURAL,
    Candidate,
)
from backend.services.knowledge_model_service import (
    ChainBranchError,
    ConcurrentRootConflictError,
    KnowledgeChainIntegrityError,
    KnowledgeRow,
    confirm,
    recall,
)

_LEGAL_VALUES = frozenset({ABSOLUTE_POSITIVE, SIGNED_NATURAL})


@dataclass(frozen=True)
class ClarificationNeed:
    """
    The contract's ephemeral first domain object (§4) — exactly four
    fields, no more. Never persisted (contract §5). Never itself passed
    to KnowledgeModel — consumed entirely within this module and
    produces, at most, one `confirm()` call (via `resolve_clarification`).

    Deliberately NOT added, per the mission's explicit instruction and
    the contract's own complexity test (§4): timestamps, confidence
    scores, conversation IDs, analysis IDs, question IDs, status enums,
    metadata. None of the required adversarial cases (contract §4's six,
    this mission's Phase 15 matrix) forced any of these.
    """
    entity_id: str
    subject: str
    candidate_value: Optional[str]
    recalled_value: Optional[str]


@dataclass(frozen=True)
class EpistemicOutcome:
    """Result of REASON -> RECALL -> COMPARE (§5). Exactly one of four
    statuses, each corresponding to a contract §6 case:
      - "ASK": Case A (no knowledge) or Case C (contradiction). A
        `ClarificationNeed` is attached.
      - "NO_ASK_ALREADY_KNOWN": Case B — recalled value already agrees
        with the candidate. "Never ask twice" in its purest form.
      - "UNRESOLVED_NO_CANDIDATE": mission Phase 5 Case D — FRU's own
        Candidate is UNKNOWN. No ClarificationNeed is even constructed;
        asking "is nothing true?" would be nonsensical, not cautious.
        No persistence invented for this case (mission's own instruction).
      - "INTEGRITY_ESCALATION": contract §6 Case D — RECALL found a
        corrupted/ambiguous chain (`KnowledgeChainIntegrityError`). Never
        treated as "no knowledge" — a distinct, named outcome, routed
        to escalation rather than an ordinary question (the end user
        answering "is X true" does nothing to repair a broken chain).
    """
    status: str
    clarification_need: Optional[ClarificationNeed] = None


def reason_recall_compare(
    supabase: Any, entity_id: str, subject: str, candidate: Candidate,
) -> EpistemicOutcome:
    """
    REASON -> RECALL -> COMPARE -> decide ASK/NO-ASK/UNRESOLVED.

    RECALL-BEFORE-ASK (contract §6): `recall()` is called, and its
    result is already bound to `recalled_value`, before this function's
    only `ClarificationNeed(...)` construction — never the reverse. This
    is the structural property `test_epistemic_dialogue_v0.py` checks
    via AST, not merely documented here as a convention.
    """
    if candidate.tier == "UNKNOWN":
        # Mission Phase 5, Case D: no defensible candidate exists at all.
        # Nothing to compare, nothing to ask about. RECALL is not even
        # needed here — the "never ask without recalling" invariant is
        # vacuously satisfied, since no ASK ever happens on this path.
        return EpistemicOutcome(status="UNRESOLVED_NO_CANDIDATE")

    try:
        recalled = recall(supabase, entity_id, subject)
    except KnowledgeChainIntegrityError:
        # Contract §6 Case D: never silently degrade a corrupted chain
        # into "we never learned this" (Case A/B). Distinct escalation.
        return EpistemicOutcome(status="INTEGRITY_ESCALATION")

    recalled_value = recalled.value if recalled is not None else None

    if recalled_value == candidate.value:
        # Case B (contract §6): agrees -> never ask twice.
        return EpistemicOutcome(status="NO_ASK_ALREADY_KNOWN")

    # Case A (recalled_value is None) or Case C (recalled_value differs)
    # both fall through to the same construction — COMPARE's outcome is
    # an input to ASSESS UNCERTAINTY, not a second branch (contract §3).
    need = ClarificationNeed(
        entity_id=entity_id,
        subject=subject,
        candidate_value=candidate.value,
        recalled_value=recalled_value,
    )
    return EpistemicOutcome(status="ASK", clarification_need=need)


@dataclass(frozen=True)
class InterpretedAnswer:
    """Stage 2 of the human-authority gate (contract §9)."""
    outcome: str  # "CONFIRM" | "CORRECT_TO" | "DECLINE" | "UNINTERPRETABLE"
    value: Optional[str] = None  # legal registry value, set for CONFIRM/CORRECT_TO only


def interpret_human_answer(
    raw_answer: Optional[str], candidate_value: Optional[str],
) -> InterpretedAnswer:
    """
    Deterministic interpretation for this one subject only (mission
    Phase 6) — no free text, no LLM. Maps to exactly one of CONFIRM /
    CORRECT_TO(value) / DECLINE / UNINTERPRETABLE (contract §9 stage 2).

    An answer proposing anything outside the subject's legal registry
    is never coerced — it is UNINTERPRETABLE, per contract §9 stage 3.
    """
    if raw_answer is None:
        return InterpretedAnswer(outcome="DECLINE")
    normalized = raw_answer.strip().upper()
    if normalized in ("", "DECLINE", "I_DONT_KNOW", "IDK", "JE_NE_SAIS_PAS"):
        return InterpretedAnswer(outcome="DECLINE")
    if normalized in ("YES", "OUI", "CONFIRM", "CONFIRMED"):
        if candidate_value is None:
            # Nothing was actually proposed to confirm — treat as
            # uninterpretable rather than fabricating a confirmed value.
            return InterpretedAnswer(outcome="UNINTERPRETABLE")
        return InterpretedAnswer(outcome="CONFIRM", value=candidate_value)
    if normalized in _LEGAL_VALUES:
        if normalized == candidate_value:
            return InterpretedAnswer(outcome="CONFIRM", value=candidate_value)
        return InterpretedAnswer(outcome="CORRECT_TO", value=normalized)
    return InterpretedAnswer(outcome="UNINTERPRETABLE")


@dataclass(frozen=True)
class ResolutionResult:
    """Outcome of attempting to resolve a `ClarificationNeed` against a
    human answer (mission Phase 6/10)."""
    status: str  # "CONFIRMED" | "NO_WRITE_DECLINED" | "NO_WRITE_AMBIGUOUS" | "RECONCILED_TO_EXISTING"
    knowledge_row: Optional[KnowledgeRow] = None


def resolve_clarification(
    supabase: Any,
    need: ClarificationNeed,
    raw_human_answer: Optional[str],
    confirmed_by: str,
    confirmed_at: datetime,
) -> ResolutionResult:
    """
    Stage 2-4 of the human-authority gate (contract §9), plus
    concurrency recovery (contract §9's new paragraph / mission Phase
    10). This is the ONLY function in this module that may call
    `knowledge_model_service.confirm()`.

    Ambiguous or declined answers never reach `confirm()` — human text
    is never written blindly as canonical knowledge (mission Phase 6).
    """
    interpreted = interpret_human_answer(raw_human_answer, need.candidate_value)

    if interpreted.outcome == "DECLINE":
        return ResolutionResult(status="NO_WRITE_DECLINED")
    if interpreted.outcome == "UNINTERPRETABLE":
        return ResolutionResult(status="NO_WRITE_AMBIGUOUS")

    value_to_confirm = interpreted.value  # legal by construction (interpret_human_answer)

    # ClarificationNeed carries recalled_value (a value), never a row id
    # (deliberately minimal, contract §4) — re-RECALL here to obtain the
    # actual predecessor row to supersede, only when one exists.
    relates_to_knowledge_id = None
    if need.recalled_value is not None:
        predecessor = recall(supabase, need.entity_id, need.subject)
        relates_to_knowledge_id = predecessor.id if predecessor is not None else None

    try:
        row = confirm(
            supabase,
            need.entity_id,
            need.subject,
            value_to_confirm,
            confirmed_by=confirmed_by,
            confirmed_at=confirmed_at,
            relates_to_knowledge_id=relates_to_knowledge_id,
        )
        return ResolutionResult(status="CONFIRMED", knowledge_row=row)
    except (ConcurrentRootConflictError, ChainBranchError):
        # Contract §9 (final arbitration, 2026-08-09): PostgreSQL already
        # chose a winner — never retry with the same value, never invent
        # one, never tell the human their answer was "wrong" (it wasn't;
        # someone else's confirmation simply landed first). Re-RECALL and
        # reconcile against whatever is now canonical.
        winner = recall(supabase, need.entity_id, need.subject)
        return ResolutionResult(status="RECONCILED_TO_EXISTING", knowledge_row=winner)


def render_clarification_question(need: ClarificationNeed) -> str:
    """
    Deterministic v0 rendering (contract §8) — presentation wording,
    kept separate from the domain decision above. Zero LLM. A future
    surface (chat, banner, onboarding step...) may replace this
    template's wording without changing what `ClarificationNeed` itself
    guarantees (OBSERVATION + HYPOTHESIS + MINIMAL CONFIRMATION REQUEST).

    Not a generic natural-language question engine — exactly the two
    forms the contract's Golden Loop (§12) requires for this one subject.
    """
    if need.recalled_value is None:
        # Confirmation-form (Case A / contract §8).
        if need.candidate_value == ABSOLUTE_POSITIVE:
            return (
                "J'ai parcouru votre fichier et il semble que vos charges "
                "soient présentées en valeurs positives, leur nature étant "
                "déterminée par les postes/comptes plutôt que par un signe "
                "négatif. Est-ce bien votre convention ?"
            )
        return (
            "J'ai parcouru votre fichier et il semble que vos charges "
            "soient présentées avec des valeurs signées (négatives pour "
            "les charges). Est-ce bien votre convention ?"
        )

    # Contradiction-form (Case C / contract §8) — names what changed,
    # never repeats the generic original question.
    prior_desc = (
        "en valeurs positives" if need.recalled_value == ABSOLUTE_POSITIVE
        else "avec des signes négatifs"
    )
    new_desc = (
        "en valeurs positives" if need.candidate_value == ABSOLUTE_POSITIVE
        else "des signes négatifs"
    )
    return (
        f"Jusqu'ici vos charges étaient présentées {prior_desc}. Ce fichier "
        f"semble utiliser {new_desc}. Cette convention a-t-elle changé ?"
    )
