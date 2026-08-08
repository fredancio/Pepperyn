"""
test_decision_memory_integrity_repair.py — Decision Memory Integrity Repair
(mission dédiée, 2026-08-08).

Répare DEUX défauts d'intégrité préexistants, découverts (pas introduits) par
la revue adversariale DecisionArc ↔ Engagement — traités comme deux défauts
indépendants à l'intérieur du même incrément (consigne explicite de Fred) :

  A. decision_arcs.entity_id jamais peuplé par le chemin de création réel
     (routers/decision_memory.py::submit_decision_feedback ne le fournit
     jamais à create_arc_from_feedback) — casse Portfolio Intelligence et le
     filtre entity_id du Briefing de revue.

  B. decision_arcs.origin_analysis_id est NOT NULL ET ON DELETE SET NULL
     simultanément (v16) — combinaison contradictoire qui bloque la
     suppression ordinaire d'une Analysis référencée par un DecisionArc
     (DELETE /api/analyses/history).

Phase 6 (reproduction) : TestEntityIdDefectReproduction utilise le VRAI
chemin de production (create_arc_from_feedback, pas une fixture à la main)
pour prouver empiriquement le défaut A avant toute correction. Ce test reste
dans la suite finale comme garde-fou de non-régression permanent — il
prouvait le défaut, il prouve maintenant sa correction.

Réserve nommée (comme pour v21) : l'interaction entre l'action FK
`ON DELETE SET NULL` de Postgres et `arc_immutability_guard()` (Phase 15,
carve-out dédié à origin_analysis_id) ne peut être vérifiée que contre une
vraie instance Postgres — aucun trigger SQL n'est exécuté par les doubles de
test Python utilisés ici. La logique Python (résolution, backfill) est
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
# Double de test intégré — plusieurs tables cohérentes entre elles,
# nécessaire pour un scénario bout-en-bout création → lecture.
# ─────────────────────────────────────────────────────────────────────────────

class _FakeResult:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _FakeQuery:
    def __init__(self, table, store):
        self.table = table
        self.store = store
        self._filters = {}
        self._neq_filters = {}
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

    def neq(self, field, value):
        self._neq_filters[field] = value
        return self

    def in_(self, field, values):
        self._filters[f"__in__{field}"] = set(values)
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, n):
        self._limit = n
        return self

    def single(self):
        self._single_mode = True
        return self

    def insert(self, payload):
        self._mode = "insert"
        self._payload = dict(payload)
        return self

    def update(self, payload):
        self._mode = "update"
        self._payload = dict(payload)
        return self

    def _matches(self, row):
        for k, v in self._filters.items():
            if k.startswith("__in__"):
                field = k[len("__in__"):]
                if row.get(field) not in v:
                    return False
            elif row.get(k) != v:
                return False
        for k, v in self._neq_filters.items():
            if row.get(k) == v:
                return False
        return True

    def execute(self):
        rows = self.store.setdefault(self.table, [])

        if self._mode == "select":
            filtered = [r for r in rows if self._matches(r)]
            if self._limit is not None:
                filtered = filtered[: self._limit]
            if self._single_mode:
                return _FakeResult(filtered[0] if filtered else None)
            return _FakeResult(filtered)

        if self._mode == "insert":
            new_row = dict(self._payload)
            new_row.setdefault("id", f"generated-{self.table}-{len(rows)}")
            rows.append(new_row)
            return _FakeResult([new_row])

        if self._mode == "update":
            updated = []
            for r in rows:
                if self._matches(r):
                    r.update(self._payload)
                    updated.append(r)
            return _FakeResult(updated)

        return _FakeResult([])


class FakeSupabase:
    def __init__(self, initial_data=None):
        self.store = {k: list(v) for k, v in (initial_data or {}).items()}

    def from_(self, table):
        return _FakeQuery(table, self.store)


def make_svc(fake):
    svc = ArcService()
    svc._supabase = fake
    return svc


VALID_ANALYSIS = {
    "id": "analysis-march",
    "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
    "decision_fingerprint": "fp_march_001",
    "entity_id": "entity-acme",
    "company_id": "company-1",
}

FEEDBACK_PAYLOAD = {
    "company_id": "company-1",
    "origin_analysis_id": "analysis-march",
    "recommendation_id": "rec-001",
    "decision_source": "plan_action_haute",
    "recommendation_text": "Renégocier le contrat d'assurance flotte.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Reproduction du défaut A via le VRAI chemin de production
# ─────────────────────────────────────────────────────────────────────────────

class TestEntityIdDefectReproductionAndRepair:

    def test_real_creation_path_populates_entity_id_and_portfolio_sees_the_arc(self):
        """
        Avant réparation (preuve historique, voir revue adversariale
        DecisionArc ↔ Engagement 2026-08-08) : create_arc_from_feedback() ne
        recevait jamais entity_id du seul appelant réel
        (routers/decision_memory.py), donc build_portfolio_briefing()
        produisait zéro carte pour tout arc créé via ce chemin — prouvé
        empiriquement à l'époque. Ce test utilise le MÊME chemin réel
        (create_arc_from_feedback, pas une fixture à la main) et prouve
        maintenant que la réparation tient : le DecisionArc résultant porte
        entity_id, et Portfolio Intelligence produit bien une carte.
        """
        fake = FakeSupabase({
            "analyses": [VALID_ANALYSIS],
            "engagements": [{"id": "engagement-acme", "entity_id": "entity-acme"}],
            "entities": [{"id": "entity-acme", "name": "Acme Corp"}],
        })
        svc = make_svc(fake)

        # Chemin de production réel — exactement l'appel fait par
        # routers/decision_memory.py::submit_decision_feedback, sans
        # entity_id explicite (aucun appelant réel ne le fournit).
        result = svc.create_arc_from_feedback(**FEEDBACK_PAYLOAD)
        assert result["created"] is True

        created_arc = fake.store["decision_arcs"][0]
        assert created_arc.get("entity_id") == "entity-acme", (
            "RÉPARATION ATTENDUE : entity_id doit être résolu depuis "
            "analyses.entity_id, exactement comme engagement_id."
        )
        assert created_arc.get("engagement_id") == "engagement-acme"

        cards = svc.build_portfolio_briefing(company_id="company-1")
        assert len(cards) == 1, (
            "DÉFAUT A confirmé si cette liste est vide : Portfolio "
            "Intelligence doit voir un arc créé via le chemin réel."
        )
        assert cards[0]["entity_id"] == "entity-acme"
        assert cards[0]["entity_name"] == "Acme Corp"

    def test_review_briefing_entity_filter_sees_newly_created_arc(self):
        fake = FakeSupabase({
            "analyses": [VALID_ANALYSIS],
            "engagements": [{"id": "engagement-acme", "entity_id": "entity-acme"}],
        })
        svc = make_svc(fake)
        svc.create_arc_from_feedback(**FEEDBACK_PAYLOAD)

        items = svc.build_review_briefing(company_id="company-1", entity_id="entity-acme")
        assert len(items) == 1, (
            "Le filtre entity_id du Briefing de revue doit voir un arc créé "
            "via le chemin réel — DÉFAUT A si cette liste est vide."
        )

    def test_missing_analysis_entity_does_not_fabricate_entity_id(self):
        """Analyse d'origine sans entity_id → l'arc reste sans entity_id, jamais deviné."""
        fake = FakeSupabase({
            "analyses": [{
                "id": "analysis-no-entity",
                "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
                "decision_fingerprint": "fp_x",
                "entity_id": None,
                "company_id": "company-1",
            }],
        })
        svc = make_svc(fake)

        payload = dict(FEEDBACK_PAYLOAD, origin_analysis_id="analysis-no-entity")
        result = svc.create_arc_from_feedback(**payload)

        assert result["created"] is True
        created_arc = fake.store["decision_arcs"][0]
        assert created_arc.get("entity_id") is None
        assert created_arc.get("engagement_id") is None

    def test_cross_company_entity_rejected_at_creation(self):
        """
        Mission 16 (tenant integrity) : une analyse dont l'entity_id résolu
        appartiendrait à une autre company ne doit jamais être attaché,
        même si un Engagement existe par ailleurs pour cette Entity.
        """
        fake = FakeSupabase({
            "analyses": [{
                "id": "analysis-cross",
                "decision_kernel": {"kernel_version": "dk-1", "decisions": []},
                "decision_fingerprint": "fp_cross",
                "entity_id": "entity-other-company",
                "company_id": "company-B",  # diverge du company_id de l'arc
            }],
            "engagements": [{"id": "engagement-x", "entity_id": "entity-other-company"}],
        })
        svc = make_svc(fake)

        payload = dict(FEEDBACK_PAYLOAD, origin_analysis_id="analysis-cross",
                        company_id="company-A")
        result = svc.create_arc_from_feedback(**payload)

        created_arc = fake.store["decision_arcs"][0]
        assert created_arc.get("entity_id") is None
        assert created_arc.get("engagement_id") is None

    def test_single_resolution_source_shared_between_entity_id_and_engagement_id(self):
        """
        Phase 8 : une seule requête `analyses` (déjà existante pour le guard
        DCT) fournit à la fois entity_id et le contexte de résolution
        d'engagement_id — aucune requête `entities` supplémentaire, aucun
        second mécanisme de résolution indépendant.
        """
        fake = FakeSupabase({
            "analyses": [VALID_ANALYSIS],
            "engagements": [{"id": "engagement-acme", "entity_id": "entity-acme"}],
        })
        svc = make_svc(fake)

        analyses_queries = []
        real_from_ = fake.from_

        def counting_from_(table):
            if table == "analyses":
                analyses_queries.append(True)
            return real_from_(table)

        fake.from_ = counting_from_

        svc.create_arc_from_feedback(**FEEDBACK_PAYLOAD)

        assert len(analyses_queries) == 1, (
            "entity_id et engagement_id doivent être résolus depuis la MÊME "
            "lecture de analyses — pas deux requêtes indépendantes qui "
            "pourraient théoriquement diverger."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Historical entity_id backfill
# ─────────────────────────────────────────────────────────────────────────────

class TestBackfillDecisionArcEntityId:

    def _svc(self, fake):
        return make_svc(fake)

    def test_resolves_historical_arcs_deterministically(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1",
                 "entity_id": None, "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats["resolved"] == 1
        arc = fake.store["decision_arcs"][0]
        assert arc["entity_id"] == "entity-1"
        assert arc["engagement_id"] == "engagement-1"

    def test_idempotent_second_run(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1",
                 "entity_id": None, "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-1", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)
        svc.backfill_decision_arc_engagements()
        stats_second = svc.backfill_decision_arc_engagements()

        assert stats_second == {"resolved": 0, "unresolved": 0, "already_present": 1, "errors": 0}

    def test_existing_non_null_entity_id_never_overwritten(self):
        """
        Un arc portant déjà un entity_id (peu importe sa cohérence avec
        l'analyse d'origine) ne doit jamais être réécrit par le backfill —
        même discipline que pour engagement_id.
        """
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1",
                 "entity_id": "entity-ALREADY-SET", "engagement_id": None},
            ],
            "analyses": [{"id": "a1", "entity_id": "entity-DIFFERENT", "company_id": "company-1"}],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-DIFFERENT"}],
        })
        svc = self._svc(fake)

        svc.backfill_decision_arc_engagements()

        arc = fake.store["decision_arcs"][0]
        assert arc["entity_id"] == "entity-ALREADY-SET"

    def test_multiple_arcs_same_entity_all_resolved(self):
        fake = FakeSupabase({
            "decision_arcs": [
                {"id": "arc-1", "origin_analysis_id": "a1", "company_id": "company-1",
                 "entity_id": None, "engagement_id": None},
                {"id": "arc-2", "origin_analysis_id": "a2", "company_id": "company-1",
                 "entity_id": None, "engagement_id": None},
            ],
            "analyses": [
                {"id": "a1", "entity_id": "entity-1", "company_id": "company-1"},
                {"id": "a2", "entity_id": "entity-1", "company_id": "company-1"},
            ],
            "engagements": [{"id": "engagement-1", "entity_id": "entity-1"}],
        })
        svc = self._svc(fake)

        stats = svc.backfill_decision_arc_engagements()

        assert stats["resolved"] == 2
        assert all(a["entity_id"] == "entity-1" for a in fake.store["decision_arcs"])
        assert all(a["engagement_id"] == "engagement-1" for a in fake.store["decision_arcs"])


# ─────────────────────────────────────────────────────────────────────────────
# ORIGIN ANALYSIS — défaut B (contradiction FK NOT NULL + ON DELETE SET NULL)
#
# Deux niveaux de vérification, volontairement distincts :
#
#   1. Le chemin applicatif réel (DELETE /api/analyses/history) : testable
#      avec un double Python — on prouve qu'il ne touche JAMAIS decision_arcs
#      directement, donc que toute la responsabilité de la nullification
#      repose sur l'action FK Postgres elle-même (pas une nouvelle logique
#      applicative qui dupliquerait ou contournerait le trigger).
#
#   2. Le trigger SQL lui-même (arc_immutability_guard(), v22) : AUCUN moteur
#      Postgres n'est disponible dans cette suite de tests (doubles Python
#      purs, voir réserve nommée en tête de fichier). Pour ne pas laisser le
#      point le plus critique de cette réparation (Phase 15, signalé par
#      Fred) reposer uniquement sur une relecture manuelle du SQL, le
#      prédicat du carve-out 2 est reproduit ici en Python, littéralement,
#      et testé contre les scénarios qui comptent. Cette copie DOIT rester
#      synchronisée avec `arc_immutability_guard()` dans
#      migrations/v22_decision_arc_origin_analysis_nullable.sql — toute
#      divergence entre les deux est un défaut bloquant, pas une variante
#      acceptable. La vérification définitive reste la validation sur le
#      projet Supabase dédié (comme pour v21/T1/T2) avant fusion en
#      production.
# ─────────────────────────────────────────────────────────────────────────────

# Tous les champs protégés par le trigger, HORS engagement_id et
# origin_analysis_id (qui varient explicitement selon le carve-out testé).
_PINNED_FIELDS = [
    "status", "company_id", "entity_id",
    "decision_fingerprint", "recommendation_id", "decision_source",
    "recommendation_text", "decision_text", "decision_notes",
    "decision_confirmed_at", "decision_confirmation_source",
    "execution_status", "execution_notes", "execution_updated_at",
    "learning_text", "learning_confirmed", "learning_modified",
    "closed_at", "abandoned_at", "abandoned_reason",
    "created_at", "updated_at",
]


def _base_closed_row():
    row = {f: f"unchanged-{f}" for f in _PINNED_FIELDS}
    row["status"] = "closed"
    row["engagement_id"] = "engagement-X"
    row["origin_analysis_id"] = "analysis-march"
    return row


def _carveout_2_allows(old_row: dict, new_row: dict) -> bool:
    """
    Reproduction littérale du carve-out 2 (v22) de arc_immutability_guard() :
        OLD.origin_analysis_id IS NOT NULL
        AND NEW.origin_analysis_id IS NULL
        AND [tous les autres champs protégés inchangés, engagement_id inclus]
    """
    if old_row["status"] != "closed":
        return True  # hors périmètre du guard CLOSED — non pertinent ici
    if not (old_row.get("origin_analysis_id") is not None
            and new_row.get("origin_analysis_id") is None):
        return False
    for f in _PINNED_FIELDS + ["engagement_id"]:
        if new_row.get(f) != old_row.get(f):
            return False
    return True


class TestOriginAnalysisImmutabilityCarveOut:
    """Mirror du carve-out 2 (v22) — voir en-tête de section."""

    def test_pure_origin_analysis_nullification_on_closed_arc_is_allowed(self):
        """Le scénario que la réparation doit précisément débloquer."""
        old = _base_closed_row()
        new = dict(old, origin_analysis_id=None)
        assert _carveout_2_allows(old, new) is True

    def test_open_non_closed_arc_is_out_of_scope_for_this_carveout(self):
        """Le guard CLOSED ne s'applique pas hors status=closed — comportement v16 inchangé."""
        old = dict(_base_closed_row(), status="intention")
        new = dict(old, origin_analysis_id=None)
        assert _carveout_2_allows(old, new) is True

    def test_reassignment_to_a_different_analysis_is_rejected(self):
        """
        origin_analysis_id doit pouvoir devenir NULL, jamais être RÉASSIGNÉ à
        une autre analyse sur un arc CLOSED — le carve-out ne couvre que la
        transition valeur→NULL, pas valeur→valeur.
        """
        old = _base_closed_row()
        new = dict(old, origin_analysis_id="analysis-different")
        assert _carveout_2_allows(old, new) is False

    def test_engagement_id_change_alongside_nullification_is_rejected(self):
        """
        Le carve-out 2 est délibérément séparé du carve-out 1 (engagement_id) :
        une UPDATE qui toucherait les deux champs à la fois n'est ni l'un ni
        l'autre scénario légitime et doit être refusée — Phase 15 exige un
        carve-out étroit, pas une exception générique de "mutation de
        provenance".
        """
        old = _base_closed_row()
        new = dict(old, origin_analysis_id=None, engagement_id="engagement-OTHER")
        assert _carveout_2_allows(old, new) is False

    def test_unrelated_field_change_alongside_nullification_is_rejected(self):
        old = _base_closed_row()
        new = dict(old, origin_analysis_id=None, decision_text="texte modifié")
        assert _carveout_2_allows(old, new) is False

    def test_arbitrary_update_on_closed_arc_without_origin_analysis_change_is_rejected(self):
        """Non-régression : le nouveau carve-out n'élargit pas l'immuabilité générale."""
        old = _base_closed_row()
        new = dict(old, execution_notes="modifié")
        assert _carveout_2_allows(old, new) is False


# ─────────────────────────────────────────────────────────────────────────────
# ORIGIN ANALYSIS — le chemin applicatif réel ne touche jamais decision_arcs
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteAnalysesHistoryRoute:
    """
    DELETE /api/analyses/history (routers/analyze.py::delete_analyses_history).

    Ce test ne vérifie PAS le comportement du trigger SQL (impossible sans
    Postgres réel, voir section précédente) — il vérifie que la route
    applicative elle-même ne contient et ne doit contenir AUCUNE logique de
    nullification manuelle de decision_arcs.origin_analysis_id : toute la
    responsabilité de cette nullification revient à l'action FK Postgres
    `ON DELETE SET NULL` (v16, inchangée) une fois origin_analysis_id rendu
    nullable (v22). Un futur correctif qui ajouterait une UPDATE manuelle
    ici dupliquerait ce que la base fait déjà et devrait être considéré
    comme une régression de conception, pas une amélioration.
    """

    def test_deletes_only_analyses_and_sessions_scoped_by_company(self):
        import asyncio
        from unittest.mock import MagicMock, AsyncMock, patch as mock_patch

        sb = MagicMock()
        sb.from_.return_value.select.return_value = sb.from_.return_value
        sb.from_.return_value.eq.return_value = sb.from_.return_value
        sb.from_.return_value.delete.return_value = sb.from_.return_value
        sb.from_.return_value.execute.return_value = MagicMock(data=[], count=3)

        from routers import analyze as analyze_router

        with mock_patch.object(
            analyze_router, "_resolve_auth",
            new=AsyncMock(return_value=("company-1", "pro", "user")),
        ), mock_patch("main.get_supabase_service", return_value=sb):
            result = asyncio.run(
                analyze_router.delete_analyses_history(authorization="Bearer token")
            )

        assert result == {"success": True, "deleted": 3}

        touched_tables = [call.args[0] for call in sb.from_.call_args_list]
        assert "decision_arcs" not in touched_tables, (
            "La route ne doit jamais manipuler decision_arcs directement — "
            "la survie/nullification de l'arc est de la seule responsabilité "
            "de l'action FK ON DELETE SET NULL (v22)."
        )
        assert "analyses" in touched_tables
        assert "sessions" in touched_tables


# ─────────────────────────────────────────────────────────────────────────────
# BOUNDARIES — non-goals explicites de la mission (Phase 20, vérification finale)
# ─────────────────────────────────────────────────────────────────────────────

class TestRepairStaysWithinMissionBoundaries:
    """
    Vérifie mécaniquement les limites explicites de la mission : aucun appel
    LLM nouveau, aucune logique FTE, aucun couplage Evidence (fact_id) requis
    par cette réparation. Ne prouve pas l'absence totale ailleurs dans le
    dépôt (hors périmètre) — prouve seulement que le diff de CETTE mission
    (arc_service.py, decision_arc.py, migrations v22, ce fichier de test)
    n'en introduit aucun.
    """

    def test_arc_service_module_has_no_new_llm_or_fte_imports(self):
        import inspect
        import services.arc_service as mod

        source = inspect.getsource(mod)
        for forbidden in ("openai", "anthropic", "fte_service", "FTEService", "temporal_engine"):
            assert forbidden not in source, (
                f"'{forbidden}' détecté dans arc_service.py — hors périmètre "
                "de cette réparation (aucun goal FTE/LLM)."
            )

    def test_decision_arc_model_has_no_evidence_fact_id_coupling(self):
        import inspect
        import models.decision_arc as mod

        source = inspect.getsource(mod)
        assert "fact_id" not in source, (
            "Aucun couplage direct à Evidence (fact_id) attendu dans "
            "DecisionArc — cette réparation ne touche pas la frontière "
            "Evidence, déjà tranchée lors d'Evidence Consumer #1."
        )


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
