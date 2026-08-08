"""
knowledge_model_service.py — Knowledge Model v0 (CONFIRMED enterprise
knowledge only).

Scope, per docs/Architecture/Cognitive/KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md
(final contract, arbitration included, canonical on main since 3be19e4):
the smallest capability that lets Pepperyn retain one thing an organisation
taught it, and prove it never asks for that same thing again while the
underlying reality hasn't changed.

WHAT THIS MODULE DOES:
  - CONFIRM: insert exactly one CONFIRMED knowledge row. Every row is
    already fully formed at insertion — there is no persisted CANDIDATE
    state to promote (contract §3). A confirmation that supersedes a
    prior row must name it explicitly (relates_to_knowledge_id).
  - RECALL: resolve the applicable knowledge for (entity_id, subject) —
    the CONFIRMED row that no other CONFIRMED row references via
    relates_to_knowledge_id (the head of the supersession chain, a
    structural/graph property, contract §8). Never resolved by
    confirmed_at ordering, never by insertion order, never by an LLM.

WHAT THIS MODULE NEVER DOES (contract §2, §17 — negative contract):
  - No Evidence capture, no raw observation storage (Evidence Ledger's job).
  - No chat/transcript storage — only the structured confirmed
    interpretation may ever reach this table.
  - No LLM call, anywhere, for any reason. No provenance value other than
    HUMAN_CONFIRMATION exists in v0.
  - No mutation of an existing row. Change is expressed only through a
    new row (see supersede()).
  - No silent resolution of an ambiguous chain. If RECALL ever finds more
    than one head for the same (entity_id, subject) — which CONFIRM's own
    write-time guard is designed to prevent, but a direct/concurrent write
    outside this module could still produce — it raises
    KnowledgeChainIntegrityError rather than picking a winner by
    timestamp or any other heuristic. This is a named, open reservation:
    the contract defines the head structurally but does not specify a
    database-level constraint preventing two rows from both superseding
    the same predecessor; see migration v24's own comment. A true
    concurrent race (two simultaneous CONFIRM calls for the same
    predecessor) is not fully closed by the application-level guard
    alone — flagged explicitly for adversarial review, not silently
    solved here.
  - RECALL-before-ASK enforcement is NOT this module's responsibility.
    This module guarantees RECALL is deterministic; whether ASK is
    actually preceded by a RECALL call is Epistemic Dialogue's own future
    obligation (contract §14).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Subject / value registry (contract §10) ─────────────────────────────────
# Curated, closed. Adding a subject means adding one registry entry and one
# CHECK clause in migration v24 — never a schema change, never a generic
# triple store. v0 has exactly one subject.

SUBJECT_VALUE_REGISTRY: dict[str, tuple[str, ...]] = {
    "EXPENSE_SIGN_CONVENTION": ("ABSOLUTE_POSITIVE", "SIGNED_NATURAL"),
}


class KnowledgeModelError(Exception):
    """Base class for all Knowledge Model v0 domain errors."""


class InvalidSubjectError(KnowledgeModelError):
    """Subject is not in the curated registry."""


class InvalidValueError(KnowledgeModelError):
    """Value is not a legal value for the given subject."""


class UnknownPredecessorError(KnowledgeModelError):
    """relates_to_knowledge_id does not resolve to an existing row."""


class CrossEntitySupersessionError(KnowledgeModelError):
    """A row may only supersede a row owned by the same Entity."""


class CrossSubjectSupersessionError(KnowledgeModelError):
    """A row may only supersede a row about the same subject."""


class SelfSupersessionError(KnowledgeModelError):
    """A row may never supersede itself."""


class ChainBranchError(KnowledgeModelError):
    """
    Write-time guard (contract Q9 / mission Phase 9): the given predecessor
    is already superseded by another CONFIRMED row. Prevents a second row
    from creating a second, competing chain head. This is prevention, not
    resolution — no winner is ever chosen; the write is simply refused.
    """


class KnowledgeChainIntegrityError(KnowledgeModelError):
    """
    Read-time fail-safe (contract Q9 / mission Phase 9): RECALL found more
    than one CONFIRMED chain head for the same (entity_id, subject). Never
    silently resolved by confirmed_at or any other heuristic — this is an
    explicit, named integrity failure that must surface, not be hidden.
    """


@dataclass(frozen=True)
class KnowledgeRow:
    """Read-only projection of a knowledge_model row."""
    id: str
    entity_id: str
    engagement_id: Optional[str]
    subject: str
    value: str
    relates_to_knowledge_id: Optional[str]
    provenance: str
    confirmed_by: str
    confirmed_at: datetime

    @staticmethod
    def from_row(row: dict[str, Any]) -> "KnowledgeRow":
        raw_confirmed_at = row["confirmed_at"]
        confirmed_at = (
            raw_confirmed_at
            if isinstance(raw_confirmed_at, datetime)
            else datetime.fromisoformat(str(raw_confirmed_at).replace("Z", "+00:00"))
        )
        return KnowledgeRow(
            id=row["id"],
            entity_id=row["entity_id"],
            engagement_id=row.get("engagement_id"),
            subject=row["subject"],
            value=row["value"],
            relates_to_knowledge_id=row.get("relates_to_knowledge_id"),
            provenance=row["provenance"],
            confirmed_by=row["confirmed_by"],
            confirmed_at=confirmed_at,
        )


def _validate_subject_value(subject: str, value: str) -> None:
    if subject not in SUBJECT_VALUE_REGISTRY:
        raise InvalidSubjectError(
            f"'{subject}' is not a recognized Knowledge Model v0 subject. "
            f"Known subjects: {sorted(SUBJECT_VALUE_REGISTRY)}."
        )
    legal_values = SUBJECT_VALUE_REGISTRY[subject]
    if value not in legal_values:
        raise InvalidValueError(
            f"'{value}' is not a legal value for subject '{subject}'. "
            f"Legal values: {legal_values}."
        )


def confirm(
    supabase: Any,
    entity_id: str,
    subject: str,
    value: str,
    confirmed_by: str,
    confirmed_at: datetime,
    engagement_id: Optional[str] = None,
    relates_to_knowledge_id: Optional[str] = None,
) -> KnowledgeRow:
    """
    Insert exactly one CONFIRMED knowledge row. Server-side only (contract
    §13) — callers must supply an already-server-side Supabase client
    (SERVICE_KEY), never a client-provided one.

    Raises (never silently coerces or drops the request):
      InvalidSubjectError / InvalidValueError — subject/value fails the
        registry (contract §10). Mirrored by the DB CHECK constraint
        (migration v24) — this is defense in depth, not the only guard.
      UnknownPredecessorError — relates_to_knowledge_id doesn't resolve.
      CrossEntitySupersessionError / CrossSubjectSupersessionError /
        SelfSupersessionError — supersession must stay within the same
        Entity and the same subject, and a row may never supersede itself
        (mission Phase 9 test list items 13-15).
      ChainBranchError — the predecessor already has a successor; refuses
        to create a second, competing chain head (see module docstring).

    Does NOT catch/swallow exceptions — unlike evidence_ledger_service's
    non-blocking write, a Knowledge confirmation is the entire point of
    the call; a silent failure here would be indistinguishable from
    "nothing was ever taught," which this module exists specifically to
    prevent (contract §14).
    """
    _validate_subject_value(subject, value)

    if relates_to_knowledge_id is not None:
        predecessor = get_by_id(supabase, relates_to_knowledge_id)
        if predecessor is None:
            raise UnknownPredecessorError(
                f"relates_to_knowledge_id={relates_to_knowledge_id} does not "
                f"resolve to an existing Knowledge row."
            )
        if predecessor.entity_id != entity_id:
            raise CrossEntitySupersessionError(
                f"Cannot supersede knowledge owned by a different Entity "
                f"(predecessor.entity_id={predecessor.entity_id}, "
                f"new row entity_id={entity_id})."
            )
        if predecessor.subject != subject:
            raise CrossSubjectSupersessionError(
                f"Cannot supersede knowledge about a different subject "
                f"(predecessor.subject={predecessor.subject}, "
                f"new row subject={subject})."
            )
        # SelfSupersessionError is structurally unreachable here (the new
        # row's id does not exist yet at validation time) — guarded anyway
        # at the DB level (knowledge_model_no_self_supersession CHECK,
        # migration v24) as the authoritative enforcement point.

        # Write-time branch guard (contract Q9): refuse a second row that
        # would supersede an already-superseded predecessor. Prevention,
        # not resolution — see ChainBranchError docstring.
        existing_successor = (
            supabase.from_("knowledge_model")
            .select("id")
            .eq("relates_to_knowledge_id", relates_to_knowledge_id)
            .execute()
        )
        if existing_successor.data:
            raise ChainBranchError(
                f"Knowledge row {relates_to_knowledge_id} is already "
                f"superseded by {existing_successor.data[0]['id']}. Refusing "
                f"to create a second, competing chain head. This does not "
                f"close the race condition for two truly simultaneous "
                f"CONFIRM calls — see module docstring."
            )

    insert_payload: dict[str, Any] = {
        "entity_id": entity_id,
        "subject": subject,
        "value": value,
        "provenance": "HUMAN_CONFIRMATION",
        "confirmed_by": confirmed_by,
        "confirmed_at": confirmed_at.isoformat(),
    }
    if engagement_id is not None:
        insert_payload["engagement_id"] = engagement_id
    if relates_to_knowledge_id is not None:
        insert_payload["relates_to_knowledge_id"] = relates_to_knowledge_id

    logger.info(
        "[KNOWLEDGE MODEL] CONFIRM entity=%s subject=%s relates_to=%s",
        entity_id, subject, relates_to_knowledge_id,
    )
    result = supabase.from_("knowledge_model").insert(insert_payload).execute()
    return KnowledgeRow.from_row(result.data[0])


def get_by_id(supabase: Any, knowledge_id: str) -> Optional[KnowledgeRow]:
    """Direct row lookup — used for supersession validation and for
    historical inspection of a superseded row (contract §13, upload 4:
    "K1 still queryable historically")."""
    result = (
        supabase.from_("knowledge_model")
        .select("*")
        .eq("id", knowledge_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return KnowledgeRow.from_row(rows[0]) if rows else None


def recall(supabase: Any, entity_id: str, subject: str) -> Optional[KnowledgeRow]:
    """
    Resolve the applicable CONFIRMED knowledge for (entity_id, subject).

    Chain-head rule (contract §8, mission Phase 8): the CONFIRMED row that
    no other CONFIRMED row for the same (entity_id, subject) references
    via relates_to_knowledge_id. NEVER resolved by confirmed_at ordering,
    created_at ordering, MAX(timestamp), confidence, or any LLM judgment —
    the graph relationship alone defines supersession.

    Returns None if no CONFIRMED row exists for this (entity_id, subject)
    — Unknown, per Article III: absence of a row already means Unknown,
    never fabricated as a default.

    Raises KnowledgeChainIntegrityError if more than one head is found —
    see module docstring. This module never leaks knowledge across
    Entities: the query is always scoped by entity_id, never by subject
    alone.
    """
    result = (
        supabase.from_("knowledge_model")
        .select("*")
        .eq("entity_id", entity_id)
        .eq("subject", subject)
        .execute()
    )
    rows = [KnowledgeRow.from_row(r) for r in (result.data or [])]
    if not rows:
        return None

    referenced_ids = {r.relates_to_knowledge_id for r in rows if r.relates_to_knowledge_id}
    heads = [r for r in rows if r.id not in referenced_ids]

    if len(heads) == 0:
        # Structurally unreachable if the write-time guard in confirm()
        # was the only path used to write this data (every chain has
        # exactly one row with no successor) — but a direct DB write
        # bypassing this service could produce a cycle. Fail loud rather
        # than silently returning None (which would be indistinguishable
        # from "never taught," a materially different and worse claim
        # than "the data is inconsistent").
        raise KnowledgeChainIntegrityError(
            f"No CONFIRMED chain head found for entity_id={entity_id} "
            f"subject={subject} among {len(rows)} row(s) — the chain may "
            f"contain a cycle. Never silently resolved."
        )
    if len(heads) > 1:
        raise KnowledgeChainIntegrityError(
            f"{len(heads)} competing CONFIRMED chain heads found for "
            f"entity_id={entity_id} subject={subject} "
            f"(ids={[h.id for h in heads]}). Two rows both claim to be "
            f"unsuperseded for the same subject — never resolved by "
            f"confirmed_at or any other heuristic. This is the open "
            f"branching-integrity reservation named in migration v24; "
            f"surface this to a human rather than guessing."
        )
    return heads[0]
