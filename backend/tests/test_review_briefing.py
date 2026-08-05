"""
Tests unitaires — Review Briefing (Capability 3, Incrément 2).

Couvre les points listés dans la mission GO IMPLEMENT (2026-08-05) :
  1. lecture des arcs actifs
  2. exclusion des arcs abandoned
  3. structure du BriefingItem retourné
  5. ordre des priorités
  6. génération des questions templatées
  7. absence de causalité inventée
  8. "Ne plus suivre" appelle la transition abandoned
  9. l'arc n'est jamais supprimé
  10. l'historique et les liens restent intacts
  13. motif enregistré dans abandoned_reason
  14. aucun libellé utilisateur ne prétend que le sujet est réglé ou résolu

Toutes les interactions Supabase sont mockées — aucune connexion réseau,
même pattern que test_arc_service.py.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ── Helpers de mock (repris de test_arc_service.py) ──────────────────────────

def make_supabase_mock():
    mock = MagicMock()
    for method in ("from_", "select", "insert", "update", "eq", "neq", "limit",
                   "single", "order", "execute"):
        getattr(mock, method).return_value = mock
    return mock


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


# ── Tests : lecture et exclusion ──────────────────────────────────────────────

class TestBuildReviewBriefingRead:

    def test_reads_active_arcs(self):
        """Les arcs actifs retournés par la requête produisent des BriefingItem."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[make_arc(id="arc-1"), make_arc(id="arc-2")])

        items = svc.build_review_briefing(company_id="company-1")

        assert len(items) == 2
        assert {i["arc_id"] for i in items} == {"arc-1", "arc-2"}

    def test_excludes_abandoned_arcs(self):
        """Un arc 'abandoned' présent dans la réponse ne doit jamais apparaître (filtre défensif)."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[
            make_arc(id="arc-active", status="execution"),
            make_arc(id="arc-abandoned", status="abandoned"),
        ])

        items = svc.build_review_briefing(company_id="company-1")

        assert len(items) == 1
        assert items[0]["arc_id"] == "arc-active"

    def test_returns_empty_list_when_no_supabase(self):
        """Aucune connexion Supabase → liste vide, jamais d'exception."""
        from services.arc_service import ArcService
        svc = ArcService()
        svc._supabase = None
        items = svc.build_review_briefing(company_id="company-1")
        assert items == []

    def test_respects_limit(self):
        """Jamais plus de `limit` éléments retournés."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(
            data=[make_arc(id=f"arc-{i}", status="intention", created_at="2026-01-01T00:00:00Z")
                  for i in range(10)]
        )

        items = svc.build_review_briefing(company_id="company-1", limit=5)

        assert len(items) == 5

    def test_entity_id_filter_applied_when_provided(self):
        """Un entity_id fourni doit être appliqué comme filtre eq() sur la requête."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[])

        svc.build_review_briefing(company_id="company-1", entity_id="entity-42")

        # eq() a été appelé au moins une fois avec ('entity_id', 'entity-42')
        eq_calls = [c.args for c in sb.eq.call_args_list]
        assert ("entity_id", "entity-42") in eq_calls


# ── Tests : structure et ordre de priorité ────────────────────────────────────

class TestBriefingItemStructureAndOrder:

    def test_priority_order_urgent_before_to_check_before_done_before_closed(self):
        """L'ordre de sortie doit être 🔥 > ⚠ > ✓ > ○."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[
            make_arc(id="closed", status="closed", closed_at="2026-05-01T00:00:00Z"),
            make_arc(id="urgent", status="intention", created_at="2026-01-01T00:00:00Z"),
            make_arc(id="done", status="learning_proposed"),
            make_arc(id="to_check", status="execution", execution_status="in_progress"),
        ])

        items = svc.build_review_briefing(company_id="company-1", limit=10)

        priorities = [i["priority"] for i in items]
        assert priorities == ["urgent", "to_check", "done", "closed"]

    def test_briefing_item_has_required_fields(self):
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[make_arc()])

        items = svc.build_review_briefing(company_id="company-1")

        item = items[0]
        for field in ("arc_id", "source_type", "priority", "title",
                      "temporal_context", "why_it_matters", "questions_to_ask"):
            assert field in item
        assert item["source_type"] == "decision_arc"

    def test_closed_card_has_no_questions(self):
        """Une carte 'closed' ne reçoit jamais de question — rien d'ouvert à discuter."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[
            make_arc(status="closed", closed_at="2026-05-01T00:00:00Z", learning_text="Apprentissage validé."),
        ])

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["questions_to_ask"] == []
        assert items[0]["learning_text"] == "Apprentissage validé."

    def test_intention_stale_becomes_urgent(self):
        """Une recommandation non décidée depuis plus de 21 jours devient 'urgent'."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        sb.execute.return_value = MagicMock(data=[
            make_arc(status="intention", created_at="2020-01-01T00:00:00Z"),
        ])

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["priority"] == "urgent"

    def test_intention_recent_stays_to_check(self):
        """Une recommandation récente (< seuil) reste 'to_check', pas 'urgent'."""
        from datetime import datetime, timezone
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        recent = datetime.now(timezone.utc).isoformat()
        sb.execute.return_value = MagicMock(data=[
            make_arc(status="intention", created_at=recent),
        ])

        items = svc.build_review_briefing(company_id="company-1")

        assert items[0]["priority"] == "to_check"


# ── Tests : questions templatées et absence de causalité/de fausse résolution ─

class TestQuestionsAndSemanticGuards:

    FORBIDDEN_RESOLUTION_TERMS = ["réglé", "résolu", "résolue", "exécuté avec succès"]
    FORBIDDEN_CAUSAL_TERMS = ["a causé", "est la conséquence de", "grâce à votre", "a provoqué"]

    ALL_STATUSES = [
        dict(status="intention", created_at="2020-01-01T00:00:00Z"),
        dict(status="intention", created_at="2026-06-01T00:00:00Z"),
        dict(status="execution", execution_status="in_progress"),
        dict(status="execution", execution_status="complete", execution_updated_at="2026-06-01T00:00:00Z"),
        dict(status="consequences_linked"),
        dict(status="learning_proposed"),
        dict(status="closed", closed_at="2026-05-01T00:00:00Z"),
    ]

    def test_every_active_status_produces_at_least_one_question_except_closed(self):
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)

        for case in self.ALL_STATUSES:
            arc = make_arc(**case)
            item = svc._arc_to_briefing_item(arc)
            if item["priority"] == "closed":
                assert item["questions_to_ask"] == []
            else:
                assert len(item["questions_to_ask"]) >= 1, f"Pas de question pour {case}"

    def test_no_label_claims_resolution(self):
        """
        RÈGLE (correction sémantique 2026-08-05) : aucun libellé généré ne doit
        affirmer qu'un sujet est réglé/résolu/exécuté au-delà de ce que
        execution_status garantit. 'Exécuté' seul est acceptable (c'est un
        fait d'execution_status) — mais jamais comme équivalent de "terminé
        avec succès" ou "réglé".
        """
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)

        for case in self.ALL_STATUSES:
            arc = make_arc(**case)
            item = svc._arc_to_briefing_item(arc)
            text_blob = " ".join(filter(None, [
                item.get("why_it_matters"),
                *item.get("questions_to_ask", []),
            ])).lower()
            for term in self.FORBIDDEN_RESOLUTION_TERMS:
                assert term not in text_blob, (
                    f"Terme de résolution non autorisé '{term}' dans : {text_blob}"
                )

    def test_no_causal_language_in_briefing_text(self):
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)

        for case in self.ALL_STATUSES:
            arc = make_arc(**case)
            item = svc._arc_to_briefing_item(arc)
            text_blob = " ".join(filter(None, [
                item.get("why_it_matters"),
                *item.get("questions_to_ask", []),
            ])).lower()
            for term in self.FORBIDDEN_CAUSAL_TERMS:
                assert term not in text_blob


# ── Tests : "Ne plus suivre" (abandon_arc) ────────────────────────────────────

class TestAbandonArc:

    def _setup_arc(self, sb, status="execution"):
        select_result = MagicMock(data={"id": "arc-1", "status": status})
        update_result = MagicMock(data=[{"id": "arc-1"}])

        def from_side_effect(table):
            m = MagicMock()
            m.select.return_value = m
            m.eq.return_value = m
            m.single.return_value = m
            m.execute.return_value = select_result

            def capture_update(payload):
                inner = MagicMock()
                inner.eq.return_value = inner
                inner.execute.return_value = update_result
                inner._payload = payload
                from_side_effect.last_update_payload = payload
                return inner
            m.update.side_effect = capture_update
            return m

        sb.from_.side_effect = from_side_effect
        return from_side_effect

    def test_abandon_calls_abandoned_transition(self):
        """'Ne plus suivre' met bien status='abandoned', jamais un autre statut."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        capture = self._setup_arc(sb, status="execution")

        result = svc.abandon_arc(arc_id="arc-1", company_id="company-1")

        assert result["abandoned"] is True
        assert capture.last_update_payload["status"] == "abandoned"
        assert "abandoned_at" in capture.last_update_payload

    def test_abandon_never_deletes_the_row(self):
        """Aucun appel .delete() n'est effectué — transition de champs uniquement."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        self._setup_arc(sb, status="execution")

        svc.abandon_arc(arc_id="arc-1", company_id="company-1")

        sb.delete.assert_not_called()

    def test_abandon_refuses_on_closed_arc(self):
        """Un arc CLOSED ne peut pas être transitionné vers abandoned."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        self._setup_arc(sb, status="closed")

        with pytest.raises(ValueError, match="CLOSED"):
            svc.abandon_arc(arc_id="arc-1", company_id="company-1")

    def test_abandon_is_idempotent_on_already_abandoned(self):
        """Ré-appeler 'Ne plus suivre' sur un arc déjà abandoned ne lève pas d'erreur."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        self._setup_arc(sb, status="abandoned")

        result = svc.abandon_arc(arc_id="arc-1", company_id="company-1")

        assert result["abandoned"] is True
        assert result.get("already_abandoned") is True

    def test_reason_is_recorded_in_abandoned_reason(self):
        """Le motif choisi par l'utilisateur est enregistré tel quel dans abandoned_reason."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        capture = self._setup_arc(sb, status="execution")

        svc.abandon_arc(arc_id="arc-1", company_id="company-1", reason="Traité en dehors de Pepperyn")

        assert capture.last_update_payload["abandoned_reason"] == "Traité en dehors de Pepperyn"

    def test_reason_is_optional(self):
        """Le motif est optionnel — aucune erreur si non fourni."""
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        capture = self._setup_arc(sb, status="execution")

        result = svc.abandon_arc(arc_id="arc-1", company_id="company-1")

        assert result["abandoned"] is True
        assert capture.last_update_payload["abandoned_reason"] is None

    def test_arc_not_found_raises(self):
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)

        def from_side_effect(table):
            m = MagicMock()
            m.select.return_value = m
            m.eq.return_value = m
            m.single.return_value = m
            m.execute.return_value = MagicMock(data=None)
            return m
        sb.from_.side_effect = from_side_effect

        with pytest.raises(ValueError, match="introuvable"):
            svc.abandon_arc(arc_id="unknown-arc", company_id="company-1")

    def test_update_payload_never_touches_learning_or_recommendation_fields(self):
        """
        L'historique doit rester intact : seuls status/abandoned_at/abandoned_reason
        sont modifiés — jamais recommendation_text, decision_text, learning_text.
        """
        sb = make_supabase_mock()
        svc = make_arc_service_with_mock(sb)
        capture = self._setup_arc(sb, status="execution")

        svc.abandon_arc(arc_id="arc-1", company_id="company-1", reason="Devenu non pertinent")

        payload_keys = set(capture.last_update_payload.keys())
        assert payload_keys == {"status", "abandoned_at", "abandoned_reason"}
        assert "recommendation_text" not in payload_keys
        assert "decision_text" not in payload_keys
        assert "learning_text" not in payload_keys
