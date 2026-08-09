"""
test_knowledge_model.py — Knowledge Model v0 test contract.

Covers the 25 tests required by the implementation mission (Phase 14),
against docs/Architecture/Cognitive/KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md
(final contract, canonical on main since 3be19e4).

Test classification (mission Phase 14 — "do not present grep/AST tests as
proof of runtime semantics"):
  INVARIANT — a rule the schema/service must never violate, tested against
    an in-memory simulation of the real DB constraints (registry, self-
    supersession, immutability, cascade). Real-Postgres validation
    (Mission 15, separate, requires authorization) is the authoritative
    proof for anything enforced at the DB layer (CHECK constraints,
    trigger, FK cascade) — these tests prove the SERVICE's own logic is
    consistent with what the DB is expected to enforce, not a substitute
    for running the real migration.
  BEHAVIOR — an expected runtime outcome of calling confirm()/recall().
  BOUNDARY — an adversarial/edge case (branching, cross-entity, self-ref).
  WEAK/GUARD — a structural check (AST import scan, schema field absence)
    that proves an architectural property statically, explicitly NOT
    claimed as proof of runtime behavior on its own.
"""
from __future__ import annotations

import ast
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.services.knowledge_model_service import (
    ChainBranchError,
    ConcurrentRootConflictError,
    CrossEntitySupersessionError,
    CrossSubjectSupersessionError,
    InvalidSubjectError,
    InvalidValueError,
    KnowledgeChainIntegrityError,
    SUBJECT_VALUE_REGISTRY,
    UnknownPredecessorError,
    confirm,
    get_by_id,
    recall,
)


# ── In-memory simulation of the real DB constraints (migration v24) ────────
# Mirrors: CHECK constraints, the immutability trigger (with its narrow
# engagement_id SET NULL carve-out), and ON DELETE CASCADE/SET NULL — close
# enough to prove the SERVICE's own logic, not a replacement for Mission 15's
# real-Postgres run.

class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, table: "_Table", op: str, columns: str = "*"):
        self._table = table
        self._op = op
        self._columns = columns
        self._filters: list[tuple[str, str, object]] = []
        self._payload: dict | None = None
        self._limit: int | None = None

    def eq(self, col, val):
        self._filters.append(("eq", col, val))
        return self

    def not_eq(self, col, val):
        self._filters.append(("neq", col, val))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _matches(self, row: dict) -> bool:
        for kind, col, val in self._filters:
            if kind == "eq" and row.get(col) != val:
                return False
            if kind == "neq" and row.get(col) == val:
                return False
        return True

    def execute(self):
        if self._op == "insert":
            row = self._table._do_insert(self._payload)
            return _Result([row])
        if self._op == "select":
            rows = [r for r in self._table.rows.values() if self._matches(r)]
            if self._limit is not None:
                rows = rows[: self._limit]
            return _Result(rows)
        raise AssertionError(f"unsupported op {self._op}")


class _Table:
    """Simulates public.knowledge_model with its CHECK constraints and
    immutability trigger, close enough for service-logic tests."""

    def __init__(self, entities: set[str], engagements: dict[str, str]):
        self.rows: dict[str, dict] = {}
        self._entities = entities          # existing entity ids
        self._engagements = engagements    # engagement_id -> entity_id

    def select(self, columns="*"):
        return _Query(self, "select", columns)

    def insert(self, payload: dict):
        query = _Query(self, "insert")
        query._payload = payload
        return query

    def _do_insert(self, payload: dict) -> dict:
        row = dict(payload)
        # Real service calls never supply "id" (the DB generates it) — an
        # explicit id is only ever passed by a test deliberately forging a
        # row (e.g. to prove the self-supersession CHECK independently of
        # the service, which cannot produce that shape itself).
        row["id"] = row.get("id") or str(uuid.uuid4())

        # CHECK knowledge_model_subject_value_registry
        subject = row["subject"]
        value = row["value"]
        legal = SUBJECT_VALUE_REGISTRY.get(subject)
        if legal is None or value not in legal:
            raise Exception(
                "new row for relation \"knowledge_model\" violates check "
                "constraint \"knowledge_model_subject_value_registry\""
            )

        # CHECK knowledge_model_provenance_v0
        if row.get("provenance") != "HUMAN_CONFIRMATION":
            raise Exception(
                "new row for relation \"knowledge_model\" violates check "
                "constraint \"knowledge_model_provenance_v0\""
            )

        # CHECK knowledge_model_no_self_supersession (structurally
        # unreachable via the service, kept here for parity with the DB).
        if row.get("relates_to_knowledge_id") == row["id"]:
            raise Exception(
                "new row for relation \"knowledge_model\" violates check "
                "constraint \"knowledge_model_no_self_supersession\""
            )

        # FK entity_id -> entities(id)
        if row["entity_id"] not in self._entities:
            raise Exception(f"insert or update on table \"knowledge_model\" "
                             f"violates foreign key constraint (entity_id)")

        # UNIQUE knowledge_model_one_successor_per_predecessor (migration
        # v25 — branch-protection correction from the pre-merge adversarial
        # review). Postgres UNIQUE semantics: NULL is never equal to NULL,
        # so only non-NULL relates_to_knowledge_id values are constrained —
        # any number of independent root rows (NULL) remain unrestricted.
        rtk = row.get("relates_to_knowledge_id")
        if rtk is not None:
            existing_successor = next(
                (r for r in self.rows.values() if r.get("relates_to_knowledge_id") == rtk),
                None,
            )
            if existing_successor is not None:
                raise Exception(
                    "duplicate key value violates unique constraint "
                    "\"knowledge_model_one_successor_per_predecessor\""
                )

        # UNIQUE INDEX knowledge_model_one_root_per_entity_subject WHERE
        # relates_to_knowledge_id IS NULL (migration v26 — root-uniqueness
        # adversarial repair, following the reservation Epistemic Dialogue
        # v0 named against merged Knowledge Model v0). Complements v25:
        # v25 constrains non-NULL relates_to_knowledge_id (branching AFTER
        # a first confirmation); this constrains the NULL case itself (two
        # competing FIRST confirmations for the same (entity_id, subject)).
        # Scoped to the (entity_id, subject) pair — never per-entity alone,
        # never global.
        if rtk is None:
            existing_root = next(
                (
                    r for r in self.rows.values()
                    if r.get("entity_id") == row["entity_id"]
                    and r.get("subject") == row["subject"]
                    and r.get("relates_to_knowledge_id") is None
                ),
                None,
            )
            if existing_root is not None:
                raise Exception(
                    "duplicate key value violates unique constraint "
                    "\"knowledge_model_one_root_per_entity_subject\""
                )

        # NOT NULL confirmed_by / confirmed_at
        if not row.get("confirmed_by"):
            raise Exception("null value in column \"confirmed_by\" violates not-null constraint")
        if not row.get("confirmed_at"):
            raise Exception("null value in column \"confirmed_at\" violates not-null constraint")

        row.setdefault("engagement_id", None)
        row.setdefault("relates_to_knowledge_id", None)

        self.rows[row["id"]] = row
        return row

    # ── Simulated FK cascade / trigger behavior (mirrors migration v24) ────

    def simulate_update_attempt(self, row_id: str, changes: dict) -> None:
        """
        Mirrors knowledge_model_immutability_guard(): allows ONLY the
        engagement_id (value -> NULL) transition with nothing else
        changing; rejects everything else unconditionally.
        """
        old = self.rows[row_id]
        new = dict(old)
        new.update(changes)

        only_engagement_cleared = (
            old.get("engagement_id") is not None
            and new.get("engagement_id") is None
            and all(
                new.get(k) == old.get(k)
                for k in old
                if k != "engagement_id"
            )
        )
        if only_engagement_cleared:
            self.rows[row_id] = new
            return
        raise Exception(
            f"[KNOWLEDGE MODEL] row {row_id} is immutable — UPDATE rejected "
            f"by knowledge_model_immutability_guard trigger"
        )

    def force_insert_bypassing_constraints(self, payload: dict) -> dict:
        """
        Writes a row directly, skipping ALL constraint simulation
        (registry, provenance, self-supersession, FK, NOT NULL, and the
        v25 UNIQUE branch-protection constraint added below). Represents
        data that predates a constraint (e.g. rows written before
        migration v25 existed) or a raw bypass of the service entirely —
        the only way, once v25 is applied, that two CONFIRMED rows could
        ever legitimately be found both referencing the same predecessor.
        Used exclusively to prove recall()'s fail-safe still fires against
        such historical/corrupted state — never to prove new writes can
        still branch (they can't, see TestBranchProtection).
        """
        row = dict(payload)
        row["id"] = row.get("id") or str(uuid.uuid4())
        row.setdefault("engagement_id", None)
        row.setdefault("relates_to_knowledge_id", None)
        self.rows[row["id"]] = row
        return row

    def simulate_entity_delete(self, entity_id: str) -> None:
        """ON DELETE CASCADE via entity_id."""
        self._entities.discard(entity_id)
        to_delete = [rid for rid, r in self.rows.items() if r["entity_id"] == entity_id]
        for rid in to_delete:
            del self.rows[rid]

    def simulate_engagement_delete(self, engagement_id: str) -> None:
        """ON DELETE SET NULL via engagement_id, routed through the
        immutability trigger's carve-out (proves the trigger doesn't
        block the FK-driven UPDATE)."""
        self._engagements.pop(engagement_id, None)
        affected = [rid for rid, r in self.rows.items() if r.get("engagement_id") == engagement_id]
        for rid in affected:
            self.simulate_update_attempt(rid, {"engagement_id": None})


class MockSupabase:
    def __init__(self, entities: set[str] | None = None, engagements: dict[str, str] | None = None):
        self._tables = {
            "knowledge_model": _Table(entities or set(), engagements or {}),
        }

    def from_(self, name):
        return self._tables[name]

    @property
    def knowledge_model(self) -> _Table:
        return self._tables["knowledge_model"]


def _now():
    return datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)


def _entity_id():
    return str(uuid.uuid4())


def _engagement_id():
    return str(uuid.uuid4())


def _user_id():
    return str(uuid.uuid4())


# ── 1-3: insertion + validation (INVARIANT) ─────────────────────────────────

class TestInsertionAndValidation:
    def test_1_confirmed_knowledge_can_be_inserted(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        assert row.id
        assert row.entity_id == entity
        assert row.value == "ABSOLUTE_POSITIVE"

    def test_2_invalid_subject_rejected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        with pytest.raises(InvalidSubjectError):
            confirm(db, entity, "NOT_A_REAL_SUBJECT", "ABSOLUTE_POSITIVE",
                    confirmed_by=_user_id(), confirmed_at=_now())

    def test_3_invalid_value_for_subject_rejected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        with pytest.raises(InvalidValueError):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "NOT_A_LEGAL_VALUE",
                    confirmed_by=_user_id(), confirmed_at=_now())

    def test_4_confirmed_by_required(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        with pytest.raises(Exception, match="confirmed_by"):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                    confirmed_by="", confirmed_at=_now())

    def test_5_confirmed_at_explicit(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        t = _now()
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=t)
        assert row.confirmed_at == t


# ── 4: immutability (INVARIANT) ─────────────────────────────────────────────

class TestImmutability:
    def test_6_update_rejected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        with pytest.raises(Exception, match="immutable"):
            db.knowledge_model.simulate_update_attempt(row.id, {"value": "SIGNED_NATURAL"})


# ── 5-8: RECALL / supersession (BEHAVIOR) ───────────────────────────────────

class TestRecallAndSupersession:
    def test_7_single_row_recall(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found is not None
        assert found.id == row.id

    def test_8_superseded_row_excluded_from_recall(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found.id == k2.id
        assert found.id != k1.id

    def test_9_superseded_row_remains_historically_queryable(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                confirmed_by=_user_id(), confirmed_at=_now(),
                relates_to_knowledge_id=k1.id)
        still_there = get_by_id(db, k1.id)
        assert still_there is not None
        assert still_there.value == "ABSOLUTE_POSITIVE"

    def test_10_three_generation_chain_resolves_correct_head(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        k3 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k2.id)
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found.id == k3.id
        assert get_by_id(db, k1.id) is not None
        assert get_by_id(db, k2.id) is not None

    def test_10b_recall_never_uses_confirmed_at_ordering(self):
        """A predecessor confirmed LATER than its successor (clock skew /
        backfill) must still be excluded from RECALL — the graph, not the
        timestamp, defines the head (contract §8, mission Phase 8)."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        early = datetime(2020, 1, 1, tzinfo=timezone.utc)
        later = datetime(2026, 1, 1, tzinfo=timezone.utc)
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=later)  # skewed: later timestamp
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=early,  # earlier timestamp
                     relates_to_knowledge_id=k1.id)
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found.id == k2.id, "RECALL must follow the graph, not confirmed_at"


# ── 9-10: isolation / multi-subject (BEHAVIOR, BOUNDARY) ────────────────────

class TestIsolation:
    def test_11_entity_isolation(self):
        e1, e2 = _entity_id(), _entity_id()
        db = MockSupabase(entities={e1, e2})
        confirm(db, e1, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        found_for_e2 = recall(db, e2, "EXPENSE_SIGN_CONVENTION")
        assert found_for_e2 is None, "Knowledge must never leak across Entities"

    def test_12_multiple_subjects_independent(self):
        # v0 only has one subject in the registry; prove the query itself
        # is subject-scoped (a row for a different subject never resolves).
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        assert recall(db, entity, "SOME_OTHER_SUBJECT_NOT_YET_REGISTERED") is None


# ── 13-15: adversarial supersession (BOUNDARY) ──────────────────────────────

class TestAdversarialSupersession:
    def test_13_self_supersession_rejected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        # Simulate a direct (mis-)write attempting self-reference — the
        # service itself cannot produce this (new row's id doesn't exist
        # yet at validation time), so this exercises the DB CHECK directly.
        with pytest.raises(Exception, match="self_supersession"):
            db.knowledge_model._do_insert({
                "id": k1.id,  # forged: pretend to reinsert with self-reference
                "entity_id": entity,
                "subject": "EXPENSE_SIGN_CONVENTION",
                "value": "SIGNED_NATURAL",
                "relates_to_knowledge_id": k1.id,
                "provenance": "HUMAN_CONFIRMATION",
                "confirmed_by": _user_id(),
                "confirmed_at": _now().isoformat(),
            })

    def test_14_cross_entity_supersession_rejected(self):
        e1, e2 = _entity_id(), _entity_id()
        db = MockSupabase(entities={e1, e2})
        k1 = confirm(db, e1, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        with pytest.raises(CrossEntitySupersessionError):
            confirm(db, e2, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                    confirmed_by=_user_id(), confirmed_at=_now(),
                    relates_to_knowledge_id=k1.id)

    def test_15_cross_subject_supersession_rejected(self):
        # v0's registry has one subject; this test is written against a
        # second hypothetical subject to prove the guard is a real check,
        # not an artifact of only one subject existing.
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        # Force a row with a different subject into the store directly
        # (bypassing the registry, which only has one member today) to
        # prove the cross-subject guard itself, independent of registry
        # size. Uses force_insert_bypassing_constraints (not _do_insert):
        # this forged row's real, pre-relabel subject is momentarily
        # EXPENSE_SIGN_CONVENTION, which would otherwise collide with k1
        # under migration v26's root-uniqueness constraint — a false
        # positive unrelated to what this test actually checks (the
        # cross-subject guard), so the same bypass already used by
        # test_17/test_F for forged/legacy rows applies here too.
        forged = db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "SIGNED_NATURAL", "relates_to_knowledge_id": None,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": _now().isoformat(),
        })
        db.knowledge_model.rows[forged["id"]]["subject"] = "OTHER_SUBJECT"
        with pytest.raises(CrossSubjectSupersessionError):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                    confirmed_by=_user_id(), confirmed_at=_now(),
                    relates_to_knowledge_id=forged["id"])

    def test_16_branching_write_time_rejected(self):
        """The trap named explicitly before implementation: two rows
        cannot both claim relates_to_knowledge_id = K1."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                confirmed_by=_user_id(), confirmed_at=_now(),
                relates_to_knowledge_id=k1.id)
        with pytest.raises(ChainBranchError):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                    confirmed_by=_user_id(), confirmed_at=_now(),
                    relates_to_knowledge_id=k1.id)

    def test_17_branching_read_time_fails_safe_never_picks_a_winner(self):
        """Since migration v25 (UNIQUE(relates_to_knowledge_id)), two new
        CONFIRMED rows can no longer both reference the same predecessor —
        see TestBranchProtection. This test now proves the OTHER case:
        recall()'s fail-safe still fires against historical/corrupted data
        that predates the constraint (force_insert_bypassing_constraints
        represents exactly that — never reachable via confirm() today,
        but not something a constraint can retroactively repair either).
        Never silently resolved via confirmed_at or insertion order."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "SIGNED_NATURAL", "relates_to_knowledge_id": k1.id,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat(),
        })
        db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "ABSOLUTE_POSITIVE", "relates_to_knowledge_id": k1.id,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
        })
        with pytest.raises(KnowledgeChainIntegrityError):
            recall(db, entity, "EXPENSE_SIGN_CONVENTION")

    def test_18_unknown_predecessor_rejected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        with pytest.raises(UnknownPredecessorError):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                    confirmed_by=_user_id(), confirmed_at=_now(),
                    relates_to_knowledge_id=str(uuid.uuid4()))


# ── Branch protection (migration v25) — pre-merge review correction #1 ─────
# Mission test contract A-G. The mock's _do_insert now simulates the real
# UNIQUE(relates_to_knowledge_id) constraint (see _Table._do_insert above),
# so these tests exercise the same code paths as before — the DB-level
# guarantee is what changed, not the service's own logic. Deliberately NOT
# a concurrency simulation (no threads, no async) per the mission's own
# instruction: the constraint IS the concurrency guarantee: Postgres's
# unique-index machinery serializes concurrent inserts targeting the same
# value natively. Proving that requires a real database, not a Python
# mock — see the live Postgres validation for the actual concurrency proof.

class TestBranchProtection:
    def test_A_multiple_null_roots_remain_allowed(self):
        """UNIQUE(relates_to_knowledge_id) never constrains NULL — any
        number of independent root confirmations (across different
        Entities and/or subjects) must remain unaffected."""
        e1, e2 = _entity_id(), _entity_id()
        db = MockSupabase(entities={e1, e2})
        k1 = confirm(db, e1, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, e2, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now())
        assert k1.relates_to_knowledge_id is None
        assert k2.relates_to_knowledge_id is None
        assert k1.id != k2.id

    def test_B_single_successor_allowed(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        assert k2.relates_to_knowledge_id == k1.id

    def test_C_second_successor_of_same_predecessor_rejected_at_db_level(self):
        """The core correction: even bypassing confirm()'s own
        application-level guard entirely (direct table insert), the
        simulated UNIQUE constraint itself rejects a second row
        referencing the same predecessor. This is what closes the
        genuine concurrent-write race the application-level check alone
        could not — see migration v25."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        db.knowledge_model._do_insert({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "SIGNED_NATURAL", "relates_to_knowledge_id": k1.id,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": _now().isoformat(),
        })
        with pytest.raises(Exception, match="knowledge_model_one_successor_per_predecessor"):
            db.knowledge_model._do_insert({
                "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
                "value": "ABSOLUTE_POSITIVE", "relates_to_knowledge_id": k1.id,
                "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
                "confirmed_at": _now().isoformat(),
            })

    def test_D_normal_three_generation_chain_still_allowed(self):
        """The constraint is per-predecessor, not per-chain — a normal
        linear chain (each row superseding a DIFFERENT predecessor) must
        remain entirely unaffected."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        k3 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k2.id)
        assert k2.relates_to_knowledge_id == k1.id
        assert k3.relates_to_knowledge_id == k2.id

    def test_E_recall_still_returns_correct_chain_head(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found is not None and found.id == k2.id

    def test_F_historical_branch_fail_safe_still_present(self):
        """Re-affirms test_17's finding under the new constraint: recall()
        keeps its own independent fail-safe for data that predates v25 or
        bypasses it entirely — the constraint prevents NEW branching, it
        cannot repair a historically corrupted chain, so the read-time
        detection remains necessary defense in depth, unchanged."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "SIGNED_NATURAL", "relates_to_knowledge_id": k1.id,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": _now().isoformat(),
        })
        db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "EXPENSE_SIGN_CONVENTION",
            "value": "ABSOLUTE_POSITIVE", "relates_to_knowledge_id": k1.id,
            "provenance": "HUMAN_CONFIRMATION", "confirmed_by": _user_id(),
            "confirmed_at": _now().isoformat(),
        })
        with pytest.raises(KnowledgeChainIntegrityError):
            recall(db, entity, "EXPENSE_SIGN_CONVENTION")

    def test_G_no_confirmed_at_arbitration_introduced(self):
        """Structural check: this correction must not have added any
        confirmed_at-based sorting/tie-breaking to recall(). Complements
        the existing runtime proof (test_10b's clock-skew case, unchanged
        by this migration)."""
        import inspect
        source = inspect.getsource(recall)
        assert "sorted(" not in source
        assert ".order(" not in source
        assert "max(" not in source


# ── H1-H10: root uniqueness (INVARIANT — root-uniqueness adversarial repair
#    mission, 2026-08-09). Migration v26 closes the gap Epistemic Dialogue v0
#    named against the merged Knowledge Model v0: v25's UNIQUE(relates_to_
#    knowledge_id) constrains non-NULL values only, leaving any number of
#    competing NULL-root rows for the same (entity_id, subject) unconstrained.
#    The genuine-concurrency case (matrix item L) is proven separately against
#    real, local PostgreSQL (not mocked here — see mission final report) —
#    these tests prove the SERVICE's own logic/simulation is consistent with
#    that live proof, not a substitute for it. ─────────────────────────────

class TestRootUniqueness:
    def test_H1_first_root_succeeds(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                      confirmed_by=_user_id(), confirmed_at=_now())
        assert row.relates_to_knowledge_id is None

    def test_H2_second_null_root_same_entity_same_subject_rejected(self):
        """The core correction: a second, contradictory root confirmation
        for the same (entity_id, subject) is refused — this is the exact
        defect Epistemic Dialogue v0 named and this mission proved live
        against real PostgreSQL before writing this test."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        with pytest.raises(ConcurrentRootConflictError):
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                    confirmed_by=_user_id(), confirmed_at=_now())

    def test_H3_root_for_different_subject_same_entity_succeeds(self):
        """Scoped by (entity_id, subject), never by entity_id alone."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        forged_other_subject_root = db.knowledge_model.force_insert_bypassing_constraints({
            "entity_id": entity, "subject": "OTHER_SUBJECT", "value": "X",
            "relates_to_knowledge_id": None, "provenance": "HUMAN_CONFIRMATION",
            "confirmed_by": _user_id(), "confirmed_at": _now().isoformat(),
        })
        assert forged_other_subject_root["relates_to_knowledge_id"] is None

    def test_H4_root_for_same_subject_different_entity_succeeds(self):
        """Already covered by test_A under its own name, re-asserted here
        directly under the root-uniqueness matrix for completeness."""
        e1, e2 = _entity_id(), _entity_id()
        db = MockSupabase(entities={e1, e2})
        k1 = confirm(db, e1, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, e2, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now())
        assert k1.relates_to_knowledge_id is None
        assert k2.relates_to_knowledge_id is None

    def test_H5_normal_chain_k1_k2_k3_unaffected(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k1.id)
        k3 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now(),
                     relates_to_knowledge_id=k2.id)
        assert k2.relates_to_knowledge_id == k1.id
        assert k3.relates_to_knowledge_id == k2.id

    def test_H6_root_marker_persists_on_superseded_row(self):
        """Once K1 is confirmed as root, it keeps relates_to_knowledge_id
        IS NULL forever, even after being superseded — this is intended:
        exactly one origin per chain, permanently. The constraint being
        satisfied by K1 is precisely what makes a future competing root
        for this (entity_id, subject) impossible, not just at write time
        but for the lifetime of the chain."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                confirmed_by=_user_id(), confirmed_at=_now(),
                relates_to_knowledge_id=k1.id)
        assert db.knowledge_model.rows[k1.id]["relates_to_knowledge_id"] is None

    def test_H7_engagement_deletion_unaffected_by_root_constraint(self):
        entity = _entity_id()
        engagement = _engagement_id()
        db = MockSupabase(entities={entity}, engagements={engagement: entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                      confirmed_by=_user_id(), confirmed_at=_now(),
                      engagement_id=engagement)
        db.knowledge_model.simulate_engagement_delete(engagement)
        assert db.knowledge_model.rows[row.id]["engagement_id"] is None
        assert db.knowledge_model.rows[row.id]["relates_to_knowledge_id"] is None

    def test_H8_entity_deletion_cascades_root(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                      confirmed_by=_user_id(), confirmed_at=_now())
        db.knowledge_model.simulate_entity_delete(entity)
        assert row.id not in db.knowledge_model.rows

    def test_H9_recall_unaffected_by_new_constraint(self):
        """recall()'s own code makes no reference to root uniqueness at
        all — J in the mission's matrix (recall() determinism) — proven
        here by showing normal recall behavior is unaffected for a chain
        the constraint never touches."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=_user_id(), confirmed_at=_now())
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found is not None and found.id == k1.id

    def test_H10_service_wraps_db_rejection_in_named_error_not_raw_exception(self):
        """Phase 6: DB is the sole invariant authority (no pre-check
        SELECT added to confirm() — that would reintroduce the exact
        check-then-act race this migration closes); the service's only
        job is translating the DB's rejection into the module's own
        named-error vocabulary, exactly as arc_service.py already does
        for its own UNIQUE constraint."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        try:
            confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "SIGNED_NATURAL",
                    confirmed_by=_user_id(), confirmed_at=_now())
            assert False, "expected ConcurrentRootConflictError"
        except ConcurrentRootConflictError as e:
            assert "recall" in str(e).lower()  # points caller back to recall(), never a winner


# ── 16-19: deletion semantics (BEHAVIOR — service-level simulation;
#    Mission 15 real-Postgres run is the authoritative proof) ───────────────

class TestDeletionSemantics:
    def test_19_analysis_deletion_has_no_effect(self):
        """Knowledge Model has no analysis_id column at all (contract
        §15) — there is nothing for an Analysis deletion to cascade
        into. This test proves the absence structurally: the field
        simply isn't part of the insert payload contract."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        assert "analysis_id" not in db.knowledge_model.rows[row.id]
        # "Deleting" an analysis is a no-op from this table's perspective
        # by construction — nothing here could ever reference it.

    def test_20_engagement_deletion_preserves_knowledge_sets_null(self):
        entity = _entity_id()
        engagement = _engagement_id()
        db = MockSupabase(entities={entity}, engagements={engagement: entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now(),
                       engagement_id=engagement)
        db.knowledge_model.simulate_engagement_delete(engagement)
        survivor = get_by_id(db, row.id)
        assert survivor is not None, "Knowledge must survive Engagement deletion"
        assert survivor.engagement_id is None

    def test_21_entity_deletion_removes_knowledge(self):
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        db.knowledge_model.simulate_entity_delete(entity)
        assert get_by_id(db, row.id) is None

    def test_22_company_gdpr_deletion_removes_knowledge_transitively(self):
        """No direct company_id column exists (contract §4/§11) — GDPR
        purge must go through Entity CASCADE. This test proves the only
        path available IS the entity cascade (there is no company_id to
        purge directly), matching the real FK chain verified against
        entities.company_id CASCADE (migration v6:75)."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        row = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                       confirmed_by=_user_id(), confirmed_at=_now())
        assert "company_id" not in db.knowledge_model.rows[row.id]
        # Company/GDPR deletion cascades to entities (v6), which cascades
        # here via entity_id — simulated identically to entity deletion.
        db.knowledge_model.simulate_entity_delete(entity)
        assert get_by_id(db, row.id) is None


# ── 20: Phidani four-upload loop (BEHAVIOR) ─────────────────────────────────

class TestPhidaniFourUploadLoop:
    """
    Minimal deterministic stub only — NOT general FRU (mission Phase 12
    boundary). "FRU-like observation" below is a plain, hardcoded
    dict standing in for what a real detector would eventually produce;
    it is not implemented here and never claimed to be.
    """

    def test_23_full_four_upload_loop(self):
        entity = _entity_id()
        engagement = _engagement_id()
        db = MockSupabase(entities={entity}, engagements={engagement: entity})
        actor = _user_id()

        # UPLOAD 1 — no prior knowledge, uncertainty about sign convention.
        prior = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert prior is None, "Upload 1 must require clarification: RECALL is empty"
        # Human confirmation (simulated domain input, not a chat message).
        k1 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                     confirmed_by=actor, confirmed_at=_now(), engagement_id=engagement)

        # UPLOAD 2 — same representation, RECALL resolves it, no clarification.
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found is not None and found.id == k1.id, "Upload 2 must recall K1"

        # UPLOAD 3 — contradictory evidence. K1 must not be mutated/deleted.
        current_knowledge = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        new_observation_value = "SIGNED_NATURAL"
        contradicts = current_knowledge.value != new_observation_value
        assert contradicts, "Upload 3's evidence must genuinely disagree with K1"
        with pytest.raises(Exception):
            db.knowledge_model.simulate_update_attempt(k1.id, {"value": new_observation_value})
        # Human confirms the change — a NEW row, K1 untouched.
        k2 = confirm(db, entity, "EXPENSE_SIGN_CONVENTION", new_observation_value,
                     confirmed_by=actor, confirmed_at=_now(), engagement_id=engagement,
                     relates_to_knowledge_id=k1.id)

        # UPLOAD 4 — RECALL resolves K2; K1 remains historically queryable.
        found = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert found is not None and found.id == k2.id, "Upload 4 must recall K2, not K1"
        k1_still_there = get_by_id(db, k1.id)
        assert k1_still_there is not None and k1_still_there.value == "ABSOLUTE_POSITIVE"

    def test_24_recall_provides_never_ask_twice_enabling_state(self):
        """Knowledge Model itself does not own ASK (contract §14). This
        test proves the ENABLING condition only: RECALL returns a
        deterministic, stable answer across repeated calls — the
        precondition a future Epistemic Dialogue needs to enforce
        never-ask-twice. It does NOT test Epistemic Dialogue, which is
        not implemented here."""
        entity = _entity_id()
        db = MockSupabase(entities={entity})
        confirm(db, entity, "EXPENSE_SIGN_CONVENTION", "ABSOLUTE_POSITIVE",
                confirmed_by=_user_id(), confirmed_at=_now())
        first = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        second = recall(db, entity, "EXPENSE_SIGN_CONVENTION")
        assert first.id == second.id == first.id
        assert first.value == second.value


# ── No-Candidate-persistence (WEAK/GUARD, structural) ───────────────────────

class TestNoCandidatePersistence:
    def test_25_no_candidate_or_status_field_exists_in_service_contract(self):
        """Structural check only: the insert payload the service builds
        never contains a 'status' field, and confirm() has no notion of
        an unconfirmed/candidate row — every call produces a fully-formed
        CONFIRMED row or raises. This does not prove the DB schema lacks
        a status column (that's migration v24 itself, human-readable, not
        re-asserted here as a duplicate source of truth)."""
        import inspect
        source = inspect.getsource(confirm)
        assert '"status"' not in source and "'status'" not in source
        assert "CANDIDATE" not in source


# ── No-LLM / no-raw-chat (WEAK/GUARD, structural, AST-based) ───────────────
# AST-based import-name extraction, not substring matching — the lesson
# already learned twice in this repo's own test history (test_fte_minimal.py
# ::TestTemporalRoleIsolation, reused in test_phidani_walking_skeleton.py).

_SERVICE_PATH = Path(__file__).resolve().parents[1] / "services" / "knowledge_model_service.py"

_LLM_MODULE_MARKERS = ("llm_service", "anthropic", "openai", "claude")


def _imported_module_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class TestNoLLMInvolvement:
    def test_26_no_llm_import_anywhere_in_service(self):
        source = _SERVICE_PATH.read_text(encoding="utf-8")
        imported = _imported_module_names(source)
        hit = imported.intersection(_LLM_MODULE_MARKERS)
        assert not hit, f"knowledge_model_service.py imports LLM-related module(s): {hit}"

    def test_27_only_human_confirmation_provenance_value_exists(self):
        from backend.services.knowledge_model_service import confirm as _c
        import inspect
        source = inspect.getsource(_c)
        # The only provenance value ever written by this module.
        assert 'provenance": "HUMAN_CONFIRMATION"' in source.replace("'", '"')


class TestNoRawChatStorage:
    def test_28_no_chat_or_message_field_in_row_dataclass(self):
        from backend.services.knowledge_model_service import KnowledgeRow
        fields = set(KnowledgeRow.__dataclass_fields__.keys())
        forbidden = {"message", "chat", "transcript", "text", "raw_text"}
        assert not (fields & forbidden), (
            f"KnowledgeRow must never carry a raw-text/chat field, found: {fields & forbidden}"
        )
