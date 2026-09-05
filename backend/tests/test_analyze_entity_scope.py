from fastapi import HTTPException
import pytest

from routers.analyze import _resolve_analysis_entity_scope


class _Result:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, rows): self.rows = list(rows)
    def select(self, _fields): return self
    def eq(self, field, value): self.rows = [r for r in self.rows if r.get(field) == value]; return self
    def limit(self, n): self.rows = self.rows[:n]; return self
    def execute(self): return _Result(self.rows)


class _Db:
    def __init__(self, tables): self.tables = tables
    def from_(self, table): return _Query(self.tables.get(table, ()))


def test_analysis_entity_scope_requires_same_company_and_one_engagement():
    db = _Db({
        "entities": [{"id": "entity-a", "company_id": "co-a", "name": "A", "is_primary": False, "relation_type": "client"}],
        "engagements": [{"id": "eng-a", "entity_id": "entity-a"}],
    })
    scope, relation = _resolve_analysis_entity_scope(db, company_id="co-a", entity_id="entity-a")
    assert scope == ("co-a", "entity-a", "eng-a")
    assert "CLIENT" in relation


def test_cross_company_entity_is_refused_before_analysis():
    db = _Db({
        "entities": [{"id": "entity-a", "company_id": "co-a", "name": "A"}],
        "engagements": [{"id": "eng-a", "entity_id": "entity-a"}],
    })
    with pytest.raises(HTTPException) as error:
        _resolve_analysis_entity_scope(db, company_id="co-b", entity_id="entity-a")
    assert error.value.status_code == 404


def test_missing_or_ambiguous_engagement_is_refused():
    entity = {"id": "entity-a", "company_id": "co-a", "name": "A"}
    for engagements in ([], [{"id": "one", "entity_id": "entity-a"}, {"id": "two", "entity_id": "entity-a"}]):
        with pytest.raises(HTTPException) as error:
            _resolve_analysis_entity_scope(
                _Db({"entities": [entity], "engagements": engagements}),
                company_id="co-a", entity_id="entity-a",
            )
        assert error.value.status_code == 404
