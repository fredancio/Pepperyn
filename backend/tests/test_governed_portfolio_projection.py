"""Falsification tests for the read-only governed V1 portfolio projection."""
from datetime import datetime, timezone
import pytest

from services.governed_portfolio_service import PortfolioReadUnavailable, build_governed_portfolio_cards, merge_portfolio_cards

NOW = datetime(2026, 9, 12, tzinfo=timezone.utc)


class Query:
    def __init__(self, database, table, calls):
        self.rows = list(database.get(table, [])); self.table = table; self.calls = calls
    def select(self, *_args):
        self.calls.append(("select", self.table)); return self
    def eq(self, key, value):
        self.rows = [row for row in self.rows if row.get(key) == value]; return self
    def in_(self, key, values):
        self.rows = [row for row in self.rows if row.get(key) in values]; return self
    def execute(self):
        return type("Result", (), {"data": self.rows})()


class ReadOnlyDatabase:
    def __init__(self, tables):
        self.tables = tables; self.calls = []
    def from_(self, table):
        return Query(self.tables, table, self.calls)


def decision(identifier, company, report, **overrides):
    row = {"id": identifier, "company_id": company, "report_id": report,
           "recommendation_text": f"Recommendation {identifier}", "status": "decided",
           "decision_kind": "accepted_conditional", "decision_text": f"Decision {identifier}",
           "decision_confirmed_at": "2026-09-01T00:00:00Z",
           "created_at": "2026-08-01T00:00:00Z"}
    row.update(overrides); return row


def base_tables():
    return {
        "decision_feedback": [
            decision("d-a", "tenant-a", "report-a"), decision("d-b", "tenant-a", "report-b"),
            decision("d-c", "tenant-a", "report-c", decision_kind=None, decision_text=None,
                     decision_confirmed_at=None, status="unsure"),
            decision("foreign", "tenant-b", "report-foreign")],
        "governed_analysis_envelopes": [
            {"analysis_id": "report-a", "company_id": "tenant-a", "entity_id": "entity-a"},
            {"analysis_id": "report-b", "company_id": "tenant-a", "entity_id": "entity-b"},
            {"analysis_id": "report-c", "company_id": "tenant-a", "entity_id": "entity-c"},
            {"analysis_id": "report-foreign", "company_id": "tenant-b", "entity_id": "entity-foreign"}],
        "governed_decision_followups": [
            {"decision_feedback_id": "d-a", "company_id": "tenant-a",
             "followup_status": "blocked", "recorded_at": "2026-09-05T00:00:00Z"},
            {"decision_feedback_id": "d-b", "company_id": "tenant-a",
             "followup_status": "pending_validation", "recorded_at": "2026-09-06T00:00:00Z"}],
        "governed_decision_executions": [],
        "entities": [
            {"id": "entity-a", "company_id": "tenant-a", "name": "Alpha"},
            {"id": "entity-b", "company_id": "tenant-a", "name": "Beta"},
            {"id": "entity-c", "company_id": "tenant-a", "name": "Gamma"},
            {"id": "entity-foreign", "company_id": "tenant-b", "name": "Foreign"}],
    }


def test_three_clients_are_ranked_without_cross_tenant_leak_or_writes():
    database = ReadOnlyDatabase(base_tables())
    cards = build_governed_portfolio_cards(database, "tenant-a", now=NOW)
    # Both Gamma and Alpha are urgent; the older unresolved intention ranks
    # first, then the blocked follow-up, then the validation checkpoint.
    assert [card["entity_name"] for card in cards] == ["Gamma", "Alpha", "Beta"]
    assert cards[0]["top_item"]["priority"] == "urgent"
    assert cards[0]["top_item"]["source_type"] == "governed_decision"
    assert all(card["entity_name"] != "Foreign" for card in cards)
    assert {operation for operation, _table in database.calls} == {"select"}


def test_explicit_execution_is_not_invented_as_open_attention():
    tables = base_tables()
    tables["governed_decision_executions"] = [{"decision_feedback_id": "d-a",
        "company_id": "tenant-a", "executed_on": "2026-09-12", "recorded_at": "2026-09-12T00:00:00Z"}]
    cards = build_governed_portfolio_cards(ReadOnlyDatabase(tables), "tenant-a", now=NOW)
    assert "Alpha" not in [card["entity_name"] for card in cards]


def test_missing_or_cross_tenant_scope_fails_closed():
    tables = base_tables()
    tables["governed_analysis_envelopes"][0]["company_id"] = "tenant-b"
    tables["entities"][1]["company_id"] = "tenant-b"
    cards = build_governed_portfolio_cards(ReadOnlyDatabase(tables), "tenant-a", now=NOW)
    assert [card["entity_name"] for card in cards] == ["Gamma"]


def test_legacy_feedback_without_governed_envelope_is_not_projected_twice():
    tables = base_tables()
    tables["decision_feedback"].append(
        decision("legacy", "tenant-a", "legacy-report", decision_kind=None,
                 decision_text=None, decision_confirmed_at=None, status="planned")
    )
    tables["entities"].append(
        {"id": "legacy-entity", "company_id": "tenant-a", "name": "Legacy"}
    )
    cards = build_governed_portfolio_cards(ReadOnlyDatabase(tables), "tenant-a", now=NOW)
    assert "Legacy" not in [card["entity_name"] for card in cards]


@pytest.mark.parametrize("table", ["decision_feedback", "governed_analysis_envelopes",
                                 "governed_decision_followups", "governed_decision_executions", "entities"])
def test_unavailable_required_registry_is_not_an_empty_queue(table):
    class BrokenQuery(Query):
        def execute(self):
            if self.table == table:
                raise RuntimeError("registry unavailable")
            return super().execute()
    class Broken(ReadOnlyDatabase):
        def from_(self, table):
            return BrokenQuery(self.tables, table, self.calls)
    with pytest.raises(PortfolioReadUnavailable):
        build_governed_portfolio_cards(Broken(base_tables()), "tenant-a", now=NOW)


def test_merge_keeps_one_card_per_client_and_counts_both_models():
    legacy = [{"entity_id": "entity-a", "entity_name": "Alpha",
        "top_item": {"priority": "to_check", "age_days": 3, "arc_id": "legacy"},
        "other_active_count": 1, "why_it_matters_display": None}]
    governed = [{"entity_id": "entity-a", "entity_name": "Alpha",
        "top_item": {"priority": "urgent", "age_days": 7, "arc_id": "governed:d-a"},
        "other_active_count": 0, "why_it_matters_display": "Bloqué"}]
    merged = merge_portfolio_cards(legacy, governed)
    assert len(merged) == 1
    assert merged[0]["top_item"]["arc_id"] == "governed:d-a"
    assert merged[0]["other_active_count"] == 2
