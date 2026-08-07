"""
test_engagement_service.py — T2A : tests unitaires du service Engagement (ADR-002).

Deux groupes de tests, correspondant aux deux responsabilités du module
(voir docstring de services/engagement_service.py) :

  - TestCreateForNewEntity : chemin applicatif (POST /api/entities), RPC
    create_entity_with_engagement() mockée — MagicMock chainable, même
    pattern que test_evidence_ledger_t1c_a.py::make_supabase_mock().

  - TestDetermineInitialStatus / TestBackfillEngagements : backfill
    historique. Utilise un double de test (FakeSupabase) plutôt qu'un
    MagicMock chainable, car backfill_engagements() interroge plusieurs
    tables (entities, engagements, analyses) avec des filtres différents
    à chaque appel — un MagicMock unique ne peut pas exprimer ça de façon
    lisible. FakeSupabase reste un double déterministe en mémoire, sans
    connexion réseau réelle (Supabase est en pause).

Note de revue n°2 (adoption ADR-002) : ces tests vérifient explicitement
l'idempotence stricte du backfill — créer uniquement les absents, ne
jamais dupliquer, ne jamais modifier ni recalculer un Engagement existant.
"""
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from services.engagement_service import (
    create_for_new_entity,
    determine_initial_status,
    backfill_engagements,
)


# ─────────────────────────────────────────────────────────────────────────────
# Double de test — FakeSupabase (backfill uniquement, plusieurs tables)
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
        self._ignore_duplicates = False

    def select(self, *_args, **_kwargs):
        self._mode = "select"
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def limit(self, n):
        self._limit = n
        return self

    def upsert(self, payload, on_conflict=None, ignore_duplicates=False):
        self._mode = "upsert"
        self._payload = dict(payload)
        self._on_conflict = on_conflict
        self._ignore_duplicates = ignore_duplicates
        return self

    def execute(self):
        rows = self.store.setdefault(self.table, [])

        if self._mode == "select":
            filtered = [
                r for r in rows
                if all(r.get(k) == v for k, v in self._filters.items())
            ]
            if self._limit is not None:
                filtered = filtered[: self._limit]
            return _FakeResult(filtered)

        if self._mode == "upsert":
            conflict_key = self._on_conflict or "id"
            existing = [
                r for r in rows
                if r.get(conflict_key) == self._payload.get(conflict_key)
            ]
            if existing and self._ignore_duplicates:
                # Comportement ON CONFLICT DO NOTHING : ligne existante
                # jamais touchée, jamais renvoyée comme "nouvellement créée".
                return _FakeResult([])
            new_row = dict(self._payload)
            new_row.setdefault("id", f"generated-{len(rows)}")
            rows.append(new_row)
            return _FakeResult([new_row])

        return _FakeResult([])


class FakeSupabase:
    """Double de test en mémoire — pas de réseau, comportement déterministe."""

    def __init__(self, initial_data=None):
        self.store = {k: list(v) for k, v in (initial_data or {}).items()}

    def from_(self, table):
        return _FakeQuery(table, self.store)


# ─────────────────────────────────────────────────────────────────────────────
# create_for_new_entity — chemin applicatif (RPC mockée)
# ─────────────────────────────────────────────────────────────────────────────

def make_rpc_supabase_mock(rpc_response_data):
    sb = MagicMock()
    sb.rpc.return_value.execute.return_value = MagicMock(data=rpc_response_data)
    return sb


class TestCreateForNewEntity:

    def test_calls_rpc_create_entity_with_engagement_with_correct_params(self):
        sb = make_rpc_supabase_mock([{"id": "entity-1", "name": "Acme"}])

        create_for_new_entity(
            supabase=sb,
            workspace_id="ws-1",
            company_id="company-1",
            name="Acme",
            industry="tech",
            business_model="saas",
            relation_type="client",
        )

        sb.rpc.assert_called_once_with(
            "create_entity_with_engagement",
            {
                "p_workspace_id": "ws-1",
                "p_company_id": "company-1",
                "p_name": "Acme",
                "p_industry": "tech",
                "p_business_model": "saas",
                "p_relation_type": "client",
            },
        )

    def test_returns_first_row_of_rpc_response(self):
        sb = make_rpc_supabase_mock([{"id": "entity-1", "name": "Acme"}])
        result = create_for_new_entity(
            supabase=sb, workspace_id="ws-1", company_id="company-1", name="Acme",
        )
        assert result == {"id": "entity-1", "name": "Acme"}

    def test_empty_rpc_response_returns_empty_dict(self):
        sb = make_rpc_supabase_mock([])
        result = create_for_new_entity(
            supabase=sb, workspace_id="ws-1", company_id="company-1", name="Acme",
        )
        assert result == {}

    def test_rpc_exception_is_propagated_not_swallowed(self):
        """
        Contrairement à evidence_ledger_service (non-bloquant, enrichissement
        optionnel), la création d'Engagement est un invariant (ADR-002) — une
        erreur doit remonter à l'appelant, jamais être avalée silencieusement.
        """
        sb = MagicMock()
        sb.rpc.return_value.execute.side_effect = RuntimeError("DB indisponible")

        with pytest.raises(RuntimeError):
            create_for_new_entity(
                supabase=sb, workspace_id="ws-1", company_id="company-1", name="Acme",
            )


# ─────────────────────────────────────────────────────────────────────────────
# determine_initial_status — backfill historique uniquement (ADR-002 §3.5)
# ─────────────────────────────────────────────────────────────────────────────

class TestDetermineInitialStatus:

    def test_active_when_analysis_exists(self):
        fake = FakeSupabase({"analyses": [{"id": "a1", "entity_id": "entity-1"}]})
        assert determine_initial_status("entity-1", fake) == "active"

    def test_prospect_when_no_analysis(self):
        fake = FakeSupabase({"analyses": []})
        assert determine_initial_status("entity-1", fake) == "prospect"

    def test_prospect_when_analyses_belong_to_other_entities_only(self):
        fake = FakeSupabase({"analyses": [{"id": "a1", "entity_id": "entity-OTHER"}]})
        assert determine_initial_status("entity-1", fake) == "prospect"


# ─────────────────────────────────────────────────────────────────────────────
# backfill_engagements — idempotence stricte (note de revue n°2)
# ─────────────────────────────────────────────────────────────────────────────

class TestBackfillEngagements:

    def test_creates_engagement_for_each_entity_without_one(self):
        fake = FakeSupabase({
            "entities": [{"id": "e1"}, {"id": "e2"}],
            "engagements": [],
            "analyses": [{"id": "a1", "entity_id": "e1"}],
        })
        stats = backfill_engagements(fake)

        assert stats == {"created": 2, "already_present": 0, "errors": 0}
        engagements = {r["entity_id"]: r for r in fake.store["engagements"]}
        assert engagements["e1"]["status"] == "active"     # a une Analysis
        assert engagements["e2"]["status"] == "prospect"   # aucune Analysis
        assert engagements["e1"]["cadence"] == "mensuelle"
        assert engagements["e2"]["cadence"] == "mensuelle"

    def test_second_run_is_idempotent_creates_nothing_new(self):
        fake = FakeSupabase({
            "entities": [{"id": "e1"}, {"id": "e2"}],
            "engagements": [],
            "analyses": [{"id": "a1", "entity_id": "e1"}],
        })
        backfill_engagements(fake)
        count_after_first_run = len(fake.store["engagements"])

        stats_second_run = backfill_engagements(fake)

        assert stats_second_run == {"created": 0, "already_present": 2, "errors": 0}
        assert len(fake.store["engagements"]) == count_after_first_run  # aucun doublon

    def test_existing_engagement_is_never_modified_or_recalculated(self):
        """
        Note de revue n°2 (adoption ADR-002) : « ne jamais recalculer
        silencieusement son statut lors d'une réexécution ». Ce test place
        un Engagement existant dans un état qui NE correspondrait PAS à la
        règle de backfill (status='active' alors qu'aucune Analysis
        n'existe) — pour prouver que backfill_engagements() ne le corrige
        jamais, ne le lit même pas pour son statut.
        """
        fake = FakeSupabase({
            "entities": [{"id": "e1"}],
            "engagements": [{"id": "existing-1", "entity_id": "e1", "status": "active",
                              "cadence": "mensuelle"}],
            "analyses": [],  # aucune Analysis — la règle de backfill dirait "prospect"
        })
        stats = backfill_engagements(fake)

        assert stats == {"created": 0, "already_present": 1, "errors": 0}
        assert fake.store["engagements"][0]["status"] == "active"  # inchangé

    def test_empty_entities_list_yields_zero_stats_no_error(self):
        fake = FakeSupabase({"entities": [], "engagements": [], "analyses": []})
        stats = backfill_engagements(fake)
        assert stats == {"created": 0, "already_present": 0, "errors": 0}

    def test_isolated_error_on_one_entity_does_not_abort_the_others(self):
        """
        T2A_Implementation_Plan.md §5 : traitement entity par entity, sans
        transaction globale — une erreur isolée ne doit pas annuler le
        travail déjà fait sur les autres.
        """
        fake = FakeSupabase({
            "entities": [{"id": "e1"}, {"id": "e2"}],
            "engagements": [],
            "analyses": [],
        })

        real_from_ = fake.from_

        def flaky_from_(table):
            if table == "analyses":
                # Simule un échec de la sous-requête de statut, mais
                # uniquement pour la première entity rencontrée.
                if not getattr(flaky_from_, "_failed_once", False):
                    flaky_from_._failed_once = True
                    raise RuntimeError("panne transitoire")
            return real_from_(table)

        fake.from_ = flaky_from_

        stats = backfill_engagements(fake)

        assert stats["errors"] == 1
        assert stats["created"] == 1  # la 2e entity a bien été traitée malgré l'échec sur la 1re


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
