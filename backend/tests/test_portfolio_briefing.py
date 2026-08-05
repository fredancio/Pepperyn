"""
Tests unitaires — Portfolio Intelligence, Incréments 1 + 2 (Capability 7).

Couvre :
  - regroupement des BriefingItem par entity_id (une carte par client)
  - sélection du point le plus prioritaire par client
  - tri des cartes par priorité (urgent > to_check > done > closed)
  - exclusion des arcs sans entity_id (pas de carte client possible)
  - résolution des noms de clients via la table entities
  - liste vide si aucun arc actif / pas de Supabase
  - absence de troncature (limit=None demandé explicitement, voir
    arc_service.build_portfolio_briefing)
  - Incrément 2 : compteur d'autres points actifs (Mission 2), affichage
    filtré de why_it_matters (Mission 3), tie-break de tri par ancienneté
    puis nom de client (Mission 4)

build_portfolio_briefing() est un pur regroupement de build_review_briefing()
déjà testé dans test_review_briefing.py — ces tests ne re-testent donc pas
la classification par priorité elle-même, uniquement l'agrégation.

Toutes les interactions Supabase sont mockées — même pattern que
test_review_briefing.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


def days_ago(n: int) -> str:
    """ISO timestamp à n jours dans le passé — pour contrôler age_days dans les tests."""
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def make_arc_service_with_mock(supabase_mock):
    from services.arc_service import ArcService
    svc = ArcService()
    svc._supabase = supabase_mock
    return svc


def make_arc(**overrides) -> dict:
    base = {
        "id": "arc-1",
        "status": "execution",
        "execution_status": "in_progress",
        "recommendation_text": "Renégocier le contrat d'assurance flotte.",
        "decision_text": None,
        "execution_notes": None,
        "learning_text": None,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "decision_confirmed_at": "2026-06-01T00:00:00Z",
        "execution_updated_at": None,
        "closed_at": None,
        "entity_id": None,
    }
    base.update(overrides)
    return base


def make_supabase_with_tables(decision_arcs_data, entities_data=None):
    """
    Mock Supabase table-aware : decision_arcs et entities répondent
    indépendamment — nécessaire car build_portfolio_briefing interroge les
    deux tables successivement (contrairement à build_review_briefing seul).
    """
    entities_data = entities_data if entities_data is not None else []

    def from_side_effect(table):
        m = MagicMock()
        for method in ("select", "eq", "neq", "in_", "order", "limit"):
            getattr(m, method).return_value = m
        if table == "decision_arcs":
            m.execute.return_value = MagicMock(data=decision_arcs_data)
        elif table == "entities":
            m.execute.return_value = MagicMock(data=entities_data)
        else:
            m.execute.return_value = MagicMock(data=[])
        return m

    sb = MagicMock()
    sb.from_.side_effect = from_side_effect
    return sb


class TestPortfolioGrouping:

    def test_one_card_per_entity(self):
        """Deux arcs pour le même client → une seule carte pour ce client."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="intention", created_at="2020-01-01T00:00:00Z"),
            make_arc(id="arc-2", entity_id="entity-A", status="execution", execution_status="in_progress"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert len(cards) == 1
        assert cards[0]["entity_id"] == "entity-A"

    def test_top_item_is_most_prioritary(self):
        """La carte porte le point le plus prioritaire du client (urgent avant to_check)."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-to-check", entity_id="entity-A", status="execution", execution_status="in_progress"),
            make_arc(id="arc-urgent", entity_id="entity-A", status="intention", created_at="2020-01-01T00:00:00Z"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["top_item"]["arc_id"] == "arc-urgent"
        assert cards[0]["top_item"]["priority"] == "urgent"

    def test_multiple_clients_produce_multiple_cards_sorted_by_priority(self):
        sb = make_supabase_with_tables([
            make_arc(id="arc-b", entity_id="entity-B", status="learning_proposed"),  # done
            make_arc(id="arc-a", entity_id="entity-A", status="intention", created_at="2020-01-01T00:00:00Z"),  # urgent
        ], entities_data=[
            {"id": "entity-A", "name": "Client A"},
            {"id": "entity-B", "name": "Client B"},
        ])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert len(cards) == 2
        assert cards[0]["entity_id"] == "entity-A"  # urgent avant done
        assert cards[1]["entity_id"] == "entity-B"

    def test_arcs_without_entity_id_are_excluded(self):
        """Un arc jamais rattaché à un client ne peut produire de carte client."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-orphan", entity_id=None, status="intention", created_at="2020-01-01T00:00:00Z"),
        ])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards == []

    def test_empty_when_no_active_arcs(self):
        sb = make_supabase_with_tables([])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards == []

    def test_returns_empty_list_when_no_supabase(self):
        from services.arc_service import ArcService
        svc = ArcService()
        svc._supabase = None
        cards = svc.build_portfolio_briefing(company_id="company-1")
        assert cards == []

    def test_entity_name_resolved_from_entities_table(self):
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="execution", execution_status="in_progress"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["entity_name"] == "Client A"

    def test_entity_name_falls_back_when_not_found(self):
        """Nom introuvable (ex. requête entities échouée) → repli explicite, jamais de crash."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="execution", execution_status="in_progress"),
        ], entities_data=[])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["entity_name"] == "Client"

    def test_no_truncation_to_five_clients(self):
        """
        Vérifie que le bug limit=0 de build_review_briefing (retombe sur
        items[:5] car 0 est falsy en Python) n'affecte pas le Portfolio :
        avec plus de 5 clients actifs, build_portfolio_briefing ne doit PAS
        se limiter à 5 cartes.
        """
        arcs = [
            make_arc(id=f"arc-{i}", entity_id=f"entity-{i}", status="execution", execution_status="in_progress")
            for i in range(8)
        ]
        entities_data = [{"id": f"entity-{i}", "name": f"Client {i}"} for i in range(8)]
        sb = make_supabase_with_tables(arcs, entities_data=entities_data)
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert len(cards) == 8

    def test_top_item_keeps_full_briefing_item_structure(self):
        """top_item reste un BriefingItem complet (utile pour l'Incrément 2)."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="execution", execution_status="in_progress"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        top_item = cards[0]["top_item"]
        for field in ("arc_id", "priority", "title", "temporal_context",
                      "why_it_matters", "questions_to_ask", "entity_id", "age_days"):
            assert field in top_item


# ── Tests : compteur d'autres points actifs (Incrément 2, Mission 2) ─────────

class TestPortfolioCounter:

    def test_zero_when_only_one_active_point(self):
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="execution", execution_status="in_progress"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["other_active_count"] == 0

    def test_counts_other_active_points_excluding_the_one_shown(self):
        """3 points actifs pour le même client → top_item + 2 autres."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-urgent", entity_id="entity-A", status="intention", created_at=days_ago(30)),
            make_arc(id="arc-to-check-1", entity_id="entity-A", status="execution", execution_status="in_progress"),
            make_arc(id="arc-to-check-2", entity_id="entity-A", status="execution", execution_status="complete"),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["top_item"]["arc_id"] == "arc-urgent"
        assert cards[0]["other_active_count"] == 2

    def test_closed_points_never_counted(self):
        """Un point 'closed' ne demande plus de préparation — jamais compté."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-urgent", entity_id="entity-A", status="intention", created_at=days_ago(30)),
            make_arc(id="arc-closed-1", entity_id="entity-A", status="closed", closed_at=days_ago(5)),
            make_arc(id="arc-closed-2", entity_id="entity-A", status="closed", closed_at=days_ago(10)),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["other_active_count"] == 0

    def test_top_item_itself_never_double_counted(self):
        """Si le point affiché est lui-même 'closed' (cas limite), il n'est pas recompté."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-closed", entity_id="entity-A", status="closed", closed_at=days_ago(5)),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["other_active_count"] == 0


# ── Tests : affichage filtré de why_it_matters (Incrément 2, Mission 3) ──────

class TestWhyItMattersDistinctFunction:
    """Teste directement la fonction pure — aucun mock Supabase nécessaire."""

    def test_none_text_is_not_distinct(self):
        from services.arc_service import ArcService
        assert ArcService._is_why_it_matters_distinct(None) is False

    def test_known_redundant_texts_are_not_distinct(self):
        from services.arc_service import ArcService
        redundant_texts = [
            "Toujours sans décision confirmée après au moins une revue.",
            "Décision encore en attente.",
            "Exécution en cours.",
            "Statut en cours de traitement.",
        ]
        for text in redundant_texts:
            assert ArcService._is_why_it_matters_distinct(text) is False, text

    def test_known_distinct_texts_are_distinct(self):
        from services.arc_service import ArcService
        distinct_texts = [
            "Effet pas encore confirmé dans une analyse.",
            "Apprentissage en attente.",
        ]
        for text in distinct_texts:
            assert ArcService._is_why_it_matters_distinct(text) is True, text

    def test_unknown_text_defaults_to_distinct(self):
        """Un texte hors de l'ensemble fermé connu n'est pas présumé redondant."""
        from services.arc_service import ArcService
        assert ArcService._is_why_it_matters_distinct("Un texte jamais vu.") is True


class TestPortfolioWhyItMattersDisplay:

    def test_hidden_when_redundant(self):
        """intention/to_check → 'Décision encore en attente.' — masqué sur la carte."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="intention", created_at=days_ago(3)),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["top_item"]["why_it_matters"] == "Décision encore en attente."
        assert cards[0]["why_it_matters_display"] is None

    def test_shown_when_distinct(self):
        """execution/complete → 'Effet pas encore confirmé dans une analyse.' — affiché."""
        sb = make_supabase_with_tables([
            make_arc(
                id="arc-1", entity_id="entity-A", status="execution",
                execution_status="complete", execution_updated_at=days_ago(12),
            ),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert cards[0]["why_it_matters_display"] == "Effet pas encore confirmé dans une analyse."

    def test_review_briefing_item_unaffected_by_portfolio_filter(self):
        """top_item.why_it_matters reste intact — seul why_it_matters_display est filtré."""
        sb = make_supabase_with_tables([
            make_arc(id="arc-1", entity_id="entity-A", status="intention", created_at=days_ago(3)),
        ], entities_data=[{"id": "entity-A", "name": "Client A"}])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        # Le champ brut, destiné au Review Briefing, n'est jamais supprimé.
        assert cards[0]["top_item"]["why_it_matters"] == "Décision encore en attente."


# ── Tests : tri — tie-break par ancienneté puis nom (Incrément 2, Mission 4) ─

class TestPortfolioTieBreak:

    def test_older_point_ranks_first_within_same_priority(self):
        older = days_ago(40)
        newer = days_ago(25)
        sb = make_supabase_with_tables([
            make_arc(id="arc-newer", entity_id="entity-B", status="intention", created_at=newer),
            make_arc(id="arc-older", entity_id="entity-A", status="intention", created_at=older),
        ], entities_data=[
            {"id": "entity-A", "name": "Client A"},
            {"id": "entity-B", "name": "Client B"},
        ])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        # Les deux sont "urgent" (>21 jours) — le plus ancien (A, 40 jours) passe en premier.
        assert [c["entity_id"] for c in cards] == ["entity-A", "entity-B"]

    def test_final_tie_break_by_entity_name_when_priority_and_age_equal(self):
        same_age = days_ago(30)
        sb = make_supabase_with_tables([
            make_arc(id="arc-zebra", entity_id="entity-zebra", status="intention", created_at=same_age),
            make_arc(id="arc-alpha", entity_id="entity-alpha", status="intention", created_at=same_age),
        ], entities_data=[
            {"id": "entity-zebra", "name": "Zebra Corp"},
            {"id": "entity-alpha", "name": "Alpha Corp"},
        ])
        svc = make_arc_service_with_mock(sb)

        cards = svc.build_portfolio_briefing(company_id="company-1")

        assert [c["entity_name"] for c in cards] == ["Alpha Corp", "Zebra Corp"]
