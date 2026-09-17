from copy import deepcopy
import pytest

from services.financial_reconciliation import reconcile_reported_sum

SCOPE = {"tenant": "synthetic-t", "entity": "synthetic-e", "engagement": "synthetic-g"}


def observations(a=813, b=-317, subtotal=1120):
    return [{"id": f"claim-{i}", "source_ref": f"source-{i}", "metric": metric,
             "reported_value": value, "scope": dict(SCOPE), "unit": "EUR",
             "period": {"kind": "FLOW", "start": "2031-01-01", "end": "2031-12-31", "months": 12}}
            for i, (metric, value) in enumerate([("REVENUE", a), ("COST_OF_SALES", b), ("GROSS_MARGIN", subtotal)])]


def run(rows, **overrides):
    kwargs = dict(scope=SCOPE, reported_metric="GROSS_MARGIN", signed_terms={"REVENUE": 1, "COST_OF_SALES": 1},
                  definition_ref="synthetic-definition", source_sha256="A" * 64)
    kwargs.update(overrides)
    return reconcile_reported_sum(rows, **kwargs)


@pytest.mark.parametrize("a,b,total,derived,delta", [(813, -317, 1120, '496', '624'), (0.3, -0.2, 0.4, '0.1', '0.3'), (-8, 3, 1, '-5', '6')])
def test_reported_derived_and_discrepancy_are_distinct_without_source_mutation(a, b, total, derived, delta):
    rows = observations(a, b, total); before = deepcopy(rows)
    result = run(rows)
    assert result["status"] == "CONTRADICTION"
    assert result["derived_value"] == derived and result["discrepancy"] == delta
    assert result["reported_claims"][0]["value"] == str(total)
    assert len(result["dependency_refs"]) == 3
    assert rows == before
    assert result["canonical_value"] is None and result["decision"] is None
    assert result["causality"] == result["economic_impact"] == "NOT_ESTABLISHED"


def test_arithmetic_match_is_not_financial_or_semantic_approval():
    assert run(observations(subtotal=496))["status"] == "ARITHMETIC_MATCH_ONLY"


def test_missing_definition_or_component_is_unknown_with_bounded_request():
    assert run(observations(), definition_ref=None)["reason"] == "DEFINITION_NOT_ESTABLISHED"
    missing = run(observations()[1:])
    assert missing["reason"] == "MISSING_COMPONENTS" and missing["derived_value"] is None
    assert "REVENUE" in missing["information_request"]["request"]


@pytest.mark.parametrize("field", ["tenant", "entity", "engagement"])
def test_foreign_scope_is_rejected_before_output(field):
    rows = observations(); rows[0]["scope"][field] = "foreign"
    with pytest.raises(ValueError, match="FOREIGN_SCOPE"):
        run(rows)


def test_conflicting_dependency_propagates_without_selecting_or_averaging():
    rows = observations(); other = {**rows[0], "id": "other", "reported_value": 700}
    result = run([*rows, other])
    assert result["status"] == "CONTRADICTION" and result["reason"] == "CONFLICTING_DEPENDENCY"
    assert result["derived_value"] is None and len(result["dependency_refs"]) == 4


@pytest.mark.parametrize("field,value", [("period", {"kind": "STOCK"}), ("unit", "USD")])
def test_mismatched_period_or_unit_cannot_be_summed(field, value):
    rows = observations(); rows[0][field] = value
    assert run(rows)["reason"] == "SCOPE_OR_UNIT_NOT_COMPARABLE"


def test_unsigned_cost_convention_must_be_explicit_not_inferred():
    result = run(observations(b=317, subtotal=496), signed_terms={"REVENUE": 1, "COST_OF_SALES": -1})
    assert result["status"] == "ARITHMETIC_MATCH_ONLY"
    assert run(observations(b=317, subtotal=496))["status"] == "CONTRADICTION"


@pytest.mark.parametrize("value", [float('nan'), float('inf')])
def test_nonfinite_refused(value):
    with pytest.raises(ValueError, match="NONFINITE"):
        run(observations(a=value))


def test_ambiguous_string_is_not_coerced_to_a_number():
    assert run(observations(a="1,234"))["status"] == "AMBIGUOUS"


def test_large_integer_does_not_lose_small_discrepancy_to_decimal_context_rounding():
    result = run(observations(a=10**35, b=-1, subtotal=10**35))
    assert result["discrepancy"] == "1"
    assert int(result["derived_value"]) == 10**35 - 1
