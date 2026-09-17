from copy import deepcopy
import pytest

from sandbox.run_financial_consistency_rehearsal import annual_source_adapter, run
from sandbox.verify_financial_review_bundle import BUNDLE, read_json


def test_frozen_component_outputs_match_numeric_contract_without_claiming_gate_pass():
    result = run()
    # Expectations are read after product output; never supplied to the product computation.
    contracts = {c["case_id"]: c for c in read_json(BUNDLE / "expected-contracts-v2.json")["cases"]}
    expected = {n["semantic_label"]: n["value"] for n in contracts["FR08"]["numerical_expectations"]}
    conflict, reconcile = [c["output"] for c in result["cases"]]
    assert conflict["status"] == reconcile["status"] == "CONTRADICTION"
    assert conflict["facts"] == [] and len(conflict["source_claims"]) == 2
    assert set(result["cases"][0]["fact_lineage"]) == {c["fact_id"] for c in conflict["source_claims"]}
    assert {v["observation_id"] for v in result["cases"][0]["fact_lineage"].values()} == {"FR07.O1", "FR07.O2"}
    assert int(conflict["discrepancies"][0]["absolute_spread"]) == contracts["FR07"]["numerical_expectations"][0]["value"]
    assert int(reconcile["derived_value"]) == expected["derived_gross_margin"]
    assert int(reconcile["reported_claims"][0]["value"]) == expected["reported_gross_margin"]
    assert int(reconcile["discrepancy"]) == expected["unresolved_discrepancy"]
    assert reconcile["canonical_value"] is None
    assert not result["full_case_pass"] and result["financial_reliability_gate"] == "OPEN_NOT_PASS"
    assert not result["provider_used"] and not result["database_writes"]


@pytest.mark.parametrize("mutation", ["scope", "period", "unit", "source", "synthetic"])
def test_adapter_refuses_scope_loss_and_unsupported_conversion(mutation):
    case = deepcopy(next(c for c in read_json(BUNDLE / "synthetic-inputs-v2.json")["cases"] if c["case_id"] == "FR07"))
    if mutation == "scope": case["observations"][0]["scope"]["entity"] = "foreign"
    if mutation == "period": case["observations"][0]["period"]["months"] = 3
    if mutation == "unit": case["observations"][0]["unit"] = "USD"
    if mutation == "source": case["observations"][0]["source_ref"] = "unknown"
    if mutation == "synthetic": case["synthetic_only"] = False
    with pytest.raises(ValueError):
        annual_source_adapter(case)
