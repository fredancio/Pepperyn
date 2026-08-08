"""
test_decision_arc_engagement.py — DecisionArc ↔ Engagement (mission dédiée,
2026-08-07).

Couvre :
  - _resolve_current_engagement_id : résolution déterministe, jamais une
    heuristique ; défense en profondeur tenant (mismatch de company) ;
    jamais d'exception propagée.
  - create_arc_from_feedback : engagement_id attaché à la création quand
    résolvable ; arc créé normalement (comportement inchangé) quand
    l'analyse d'origine ne porte pas d'entity_id — cas de TOUTES les
    fixtures existantes de test_arc_service.py, donc rétrocompatibilité
    vérifiée explicitement ici.
  - backfill_decision_arc_engagements : idempotent, jamais de valeur
    fabriquée pour les arcs non résolvables, erreur isolée n'abat pas les
    autres arcs.

Réserve nommée (voir aussi le rapport final de la mission) : le carve-out
d'immutabilité ajouté à arc_immutability_guard() par
v21_decision_arc_engagement.sql (permettant à un arc CLOSED de recevoir
engagement_id une seule fois) ne peut être vérifié que contre une vraie
instance Postgres — les doubles Python utilisés ici n'exécutent aucun
trigger SQL. Cette limitation est structurelle à ce sandbox (déjà
documentée pour RLS/policies tout au long de ce projet), pas un aveu
d'untested code : la logique Python ci-dessus (resolution, backfill) est
intégralement testée ; seul le trigger SQL lui-même reste à vérifier en
environnement réel avant déploiement.
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.arc_service import ArcService, _resolve_current_engagement_id


# ─────────────────────────────────────────────────────────────────────────────
# _resolve_current_engagement_id
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveCurrentEngagementId:

    def test_resolves_when_entity_and_company_match(self):
        sb = MagicMock()
        sb.from_.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[{"id": "engagement-1"}])
        )

        result = _resolve_current_engagement_id(
            supabase=sb,
            entity_id="entity-1",
            entity_company_id="company-1",
            expected_company_id="company-1",
        )

        assert result == "engagement-1"

    def test_returns_none_when_entity_id_absent(self):
        sb = MagicMock()
        result = _resolve_current_engagement_id(
            supabase=sb,
            entity_id=None,
            entity_company_id="company-1",
            expected_company_id="company-1",
        )
        assert result is None
        # Aucune requête ne doit être émise — court-circuit avant tout appel.
        sb.from_.assert_not_called()

    def test_returns_none_on_company_mismatch_defense_in_depth(self):
        """
        Mission 17 (tenant isolation) : un entity_id résolu depuis
        l'analyse d'origine ne doit jamais être utilisé si son company_id
        ne correspond pas à celui attendu — même si, par construction
        ailleurs dans le dépôt, ce mismatch ne devrait jamais se produire.
        """
        sb = MagicMock()
        result = _resolve_current_engagement_id(
            supabase=sb,
            entity_id="entity-1",
            entity_company_id="company-OTHER",
            expected_company_id="company-1",
        )
        assert result is None
        sb.from_.assert_not_called()

    def test_returns_none_when_no_engagement_found(self):
        sb = MagicMock()
        sb.from_.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[])
        )
        result = _resolve_current_engagement_id(
            supabase=sb,
            entity_id="entity-1",
            entity_company_id="company-1",
            expected_company_id="company-1",
        )
        assert result is None

    def test_query_failure_returns_none_not_exception(self):
        sb = MagicMock()
        sb.from_.side_effect = RuntimeError("DB indisponible")
        result = _resolve_current_engagement_id(
            supabase=sb,
            entity_id="entity-1",
            entity_company_id="company-1",
            expected_company_id="company-1",
        )
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# create_arc_from_feedback — attachement à la création
# ─────────────────────────────────────────────────────────────────────────────

FEEDBACK_BASE = {
    "company_id": "company-1",
    "origin_analysis_id": "analysis-1",
    "recommendation_id": "rec-001",
    "decision_source": "plan_action_haute",
    "recommendation_text": "Émettre toutes les factures de septembre immédiatement.",
}


def make_arc_service_with_mock(supabase_mock):
    svc = ArcService()
    svc._supabase = supabase_mock
    return svc


class TestCreateArcEngagementAttachment:

    def test_engagement_id_attached_when_resolvable(self):
        """
        L'analyse d'origine porte entity_id + company_id cohérents avec
        l'arc → engagement_id doit apparaître dans le payload d'insertion.
        """
        sb = MagicMock()
        inserted_payload = {}

        def from_side_effect(table):
            m = MagicMock()
            if table == "analyses":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    MagicMock(data={
                        "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
                        "decision_fingerprint": "fp_test_abc123",
                        "entity_id": "entity-1",
                        "company_id": "company-1",
                    })
                )
            elif table == "engagements":
                m.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
                    MagicMock(data=[{"id": "engagement-1"}])
                )
            elif table == "decision_arcs":
                def capture_insert(payload):
                    inserted_payload.update(payload)
                    inner = MagicMock()
                    inner.execute.return_value = MagicMock(data=[{"id": "arc-uuid-eng"}])
                    return inner
                m.insert.side_effect = capture_insert
            elif table == "arc_analysis_links":
                m.insert.return_value.execute.return_value = MagicMock(data=[])
            return m

        sb.from_.side_effect = from_side_effect
        svc = make_arc_service_with_mock(sb)

        result = svc.create_arc_from_feedback(**FEEDBACK_BASE)

        assert result["created"] is True
        assert inserted_payload.get("engagement_id") == "engagement-1"

    def test_arc_created_normally_when_origin_analysis_has_no_entity_id(self):
        """
        Rétrocompatibilité explicite : reproduit exactement la forme des
        fixtures VALID_ANALYSIS_DATA de test_arc_service.py (aucune clé
        entity_id/company_id) — l'arc doit se créer sans erreur, sans
        engagement_id, sans requête supplémentaire sur `engagements`.
        """
        sb = MagicMock()
        inserted_payload = {}
        engagements_queried = []

        def from_side_effect(table):
            m = MagicMock()
            if table == "analyses":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    MagicMock(data={
                        "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
                        "decision_fingerprint": "fp_test_abc123",
                        # Pas de entity_id / company_id — comme en production
                        # aujourd'hui (aucun appelant réel ne les fournit).
                    })
                )
            elif table == "engagements":
                engagements_queried.append(True)
            elif table == "decision_arcs":
                def capture_insert(payload):
                    inserted_payload.update(payload)
                    inner = MagicMock()
                    inner.execute.return_value = MagicMock(data=[{"id": "arc-uuid-noeng"}])
                    return inner
                m.insert.side_effect = capture_insert
            elif table == "arc_analysis_links":
                m.insert.return_value.execute.return_value = MagicMock(data=[])
            return m

        sb.from_.side_effect = from_side_effect
        svc = make_arc_service_with_mock(sb)

        result = svc.create_arc_from_feedback(**FEEDBACK_BASE)

        assert result["created"] is True
        assert "engagement_id" not in inserted_payload
        assert engagements_queried == []  # aucune requête engagements émise

    def test_arc_still_created_when_engagement_lookup_fails(self):
        """La résolution Engagement est un enrichissement — jamais bloquant."""
        sb = MagicMock()
        inserted_payload = {}

        def from_side_effect(table):
            m = MagicMock()
            if table == "analyses":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    MagicMock(data={
                        "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
                        "decision_fingerprint": "fp_test_abc123",
                        "entity_id": "entity-1",
                        "company_id": "company-1",
                    })
                )
            elif table == "engagements":
                m.select.side_effect = RuntimeError("DB indisponible")
            elif table == "decision_arcs":
                def capture_insert(payload):
                    inserted_payload.update(payload)
                    inner = MagicMock()
                    inner.execute.return_value = MagicMock(data=[{"id": "arc-uuid-fail"}])
                    return inner
                m.insert.side_effect = capture_insert
            elif table == "arc_analysis_links":
                m.insert.return_value.execute.return_value = MagicMock(data=[])
            return m

        sb.from_.side_effect = from_side_effect
        svc = make_arc_service_with_mock(sb)

        result = svc.create_arc_from_feedback(**FEEDBACK_BASE)

        assert result["created"] is True
        assert "engagement_id" not in inserted_payload


# ─────────────────────────────────────────────────────────────────────────────
# backfill_decision_arc_engagements
# ─────────────────────────────────────────────────────────────────────────────

class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, table, store):
        self.table = table
        self.store = store
        self._filters = {}
        self._limit = None
        self._mode = "select"
        self._payload = None
        self._single_mode = False

    def select(self, *_a, **_k):
        self._mode = "select"
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def limit(self, n):
        self._limit = n
        return self

    def single(self):
        # Miroir du comportement Supabase réel : .data devient un dict
        # unique (ou None), jamais une liste — nécessaire ici car
        # backfill_decision_arc_engagements() fait `.get()` directement sur
        # analysis_result.data, exactement comme le vrai client.
        self._single_mode = True
        return self

    def update(self, payload):
        self._mode = "update"
        self._payload = dict(payload)
        return self

    def execute(self):
        rows = self.store.setdefault(self.table, [])

        if self._mode == "select":
            filtered = [r for r in rows if all(r.get(k) == v for k, v in self._filters.items())]
            if self._limit is not None:
                filtered = filtered[: self._limit]
            if self._single_mode:
                return _FakeResult(filtered[0] if filtered else None)
            return _FakeResult(filtered)

        if self._mode == "update":
            for r in rows:
                if all(r.get(k) == v for k, v in self._filters.items()):
                    r.update(self._payload)
            return _FakeResult([])

        return _FakeResult([])


class FakeSupabase:
    """Double de test en mémoire — même pattern que test_engagement_service.py."""

    def __init__(self, initial_data=None):
        self.store = {k: list(v) for k, v in (initial_data or {}).items()}

    def from_(self, table):
        return _FakeQuery(table, self.store)


class TestBackfillDecisionArcEngagements:

    def _svc(self, fake):
        svc = ArcService()
        svc._supabase = fake
        return svc

    def test_resolves_arcs_deterministically(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1", "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats == {"resolved": 1, "unresolved": 0, "already_present": 0, "errors": 0}
        assert fake.store["decision_arcs"][0]["engagement_id"] == "engagement-1"

    def test_unresolved_stays_null_never_fabricated(self):
        """Analyse d'origine sans entity_id → reste non résolu, jamais deviné."""
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1", "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": None, "company_id": "company-1"}],
            "engagements": [],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats == {"resolved": 0, "unresolved": 1, "already_present": 0, "errors": 0}
        assert fake.store["decision_arcs"][0]["engagement_id"] is None

    def test_idempotent_second_run_skips_resolved_arcs(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1", "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)
        svc.backfill_decision_arc_engagements()

        stats_second_run = svc.backfill_decision_arc_engagements()

        assert stats_second_run == {"resolved": 0, "unresolved": 0, "already_present": 1, "errors": 0}

    def test_already_resolved_engagement_never_recalculated(self):
        """
        Un arc portant déjà engagement_id ne doit jamais être relu, même si
        l'Engagement résolu aujourd'hui serait différent (même discipline
        que backfill_engagements pour T2A — note de revue n°2).
        """
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1",
                 "engagement_id": "engagement-ALREADY-SET"},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-DIFFERENT", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats == {"resolved": 0, "unresolved": 0, "already_present": 1, "errors": 0}
        assert fake.store["decision_arcs"][0]["engagement_id"] == "engagement-ALREADY-SET"

    def test_isolated_error_does_not_abort_other_arcs(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1", "engagement_id": None},
                {"id": "arc-2", "origin_analysis_id": "a2", "company_id": "company-1", "engagement_id": None},
            ],
            "analyses": [
                {"id": "a2", "entity_id": "entity-2", "company_id": "company-1"},
            ],
            "engagements": [{"id": "engagement-2", "entity_id": "entity-2"}],
        })
        svc = self._svc(fake)

        # arc-1 référence une analyse absente de la table `analyses` du
        # double (a1 non défini) → .single().execute() lève une exception
        # dans le vrai client Supabase ; ici, l'absence de ligne produit une
        # liste vide, donc adata = {} — simulons plutôt une vraie panne pour
        # ce test via un wrapper.
        real_from_ = fake.from_
        calls = {"n": 0}

        def flaky_from_(table):
            if table == "analyses":
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("panne transitoire")
            return real_from_(table)

        fake.from_ = flaky_from_

        stats = svc.backfill_decision_arc_engagements()

        assert stats["errors"] == 1
        assert stats["resolved"] == 1  # arc-2 traité malgré l'échec sur arc-1

    def test_empty_decision_arcs_yields_zero_stats_no_error(self):
        fake = FakeSupabase({"decision_arcs": [], "analyses": [], "engagements": []})
        svc = self._svc(fake)
        stats = svc.backfill_decision_arc_engagements()
        assert stats == {"resolved": 0, "unresolved": 0, "already_present": 0, "errors": 0}

    def test_cross_company_mismatch_never_attached(self):
        """
        Mission 17 : une analyse dont le company_id diverge de celui de
        l'arc ne doit jamais produire d'attachement — même si un Engagement
        existe par ailleurs pour cette Entity.
        """
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-A", "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-B"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats == {"resolved": 0, "unresolved": 1, "already_present": 0, "errors": 0}
        assert fake.store["decision_arcs"][0]["engagement_id"] is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
