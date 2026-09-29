"""Actual isolated-PostgreSQL proof for the unadmitted v3 receipt store."""

import copy
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest

from sandbox.heterogeneous_workbooks import _mock_response, run_recorded_registered_mock_analysis
from services.generic_producer_candidate import (
    CONTRACT_BINDING,
    GENERIC_ADMISSION_CONTRACT_SHA256,
    GenericProducerReceiptContractV3,
    PRODUCER_ID,
    PRODUCER_VERSION,
    TASK_ID,
    TASK_VERSION,
    build_openai_request_from_understanding,
    parse_openai_response,
    verify_generic_receipt_contract_v3,
)
from services.governed_analysis_persistence import _binding, _canonical_bytes, _digest
from services.v1_analysis_contract import GovernedAnalysisEnvelope
from test_v40_postgres import (
    ACTOR, COMPANY, ENGAGEMENT, ENTITY, NAME, RAW, ROOT, js, literal, sql,
)


@pytest.fixture(scope="module")
def v3sql(sql):
    preflight = json.loads(sql(
        (ROOT / "migrations/v41_preflight_read_only.sql").read_text(encoding="utf-8")
    ))
    assert preflight["status"] == "PREFLIGHT_PASS"
    assert preflight["write_performed"] is False
    sql((ROOT / "migrations/v41_generic_producer_receipts_v3.sql").read_text(encoding="utf-8"))
    postflight = json.loads(sql(
        (ROOT / "migrations/v41_postflight_read_only.sql").read_text(encoding="utf-8")
    ))
    assert postflight["status"] == "POSTFLIGHT_PASS"
    assert len(postflight["tables"]) == 3 and len(postflight["functions"]) == 4
    for table in (
        "generic_producer_policies_v3",
        "generic_execution_admissions_v3",
        "generic_execution_receipts_v3",
    ):
        assert sql(f"SELECT count(*) FROM {table}") == "0"
        for role in ("anon", "authenticated"):
            assert sql(f"SET ROLE {role}; SELECT * FROM {table}", fail=True)
        for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert sql(
                f"SELECT has_table_privilege('service_role','{table}','{privilege}')"
            ) == "f"
    return sql


@pytest.mark.parametrize(
    "variant,expected",
    [("lf", True), ("crlf", True), ("semantic", False), ("space", False)],
)
def test_v41_definition_verifier_accepts_only_pinned_line_endings(v3sql, variant, expected):
    migration = (ROOT / "migrations/v41_generic_producer_receipts_v3.sql").read_text(
        encoding="utf-8"
    )
    original = re.search(
        r"CREATE FUNCTION public\.close_generic_execution_v3\([\s\S]*?END \$\$;",
        migration,
    )[0].replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)
    changed = original
    if variant == "crlf":
        changed = changed.replace("\n", "\r\n")
    elif variant == "semantic":
        changed = changed.replace("RETURN 'CLOSED';", "RETURN 'REFUSED';")
    elif variant == "space":
        changed = changed.replace("BEGIN", "BEGIN ", 1)
    try:
        v3sql(changed)
        report = json.loads(v3sql(
            (ROOT / "migrations/v41_definition_conformance_read_only.sql").read_text(
                encoding="utf-8"
            )
        ))
        assert (report["status"] == "V41_DEFINITION_CONFORMANCE_PASS") is expected
        assert report["write_performed"] is False
        assert len(report["functions"]) == 5
        assert all(
            "raw_sha256" in row and "lf_sha256" in row
            for row in report["functions"]
        )
    finally:
        v3sql(original)


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def setup(v3sql):
    recorded = run_recorded_registered_mock_analysis(RAW, NAME)
    source_facts = recorded.analysis.envelope.source_facts
    request_id, execution_id, analysis_id, policy_id = [str(uuid4()) for _ in range(4)]
    nonce = request_id.replace("-", "").upper()
    request = build_openai_request_from_understanding(
        source_facts, invocation_nonce=nonce, model="gpt-5"
    )
    projection_text = _canonical(request)
    response = _mock_response(source_facts, nonce)
    analysis = parse_openai_response(response, source_facts, nonce)
    envelope = GovernedAnalysisEnvelope(governed_analysis=analysis, source_facts=source_facts)
    payload = envelope.model_dump(mode="json")
    envelope_sha = _digest(payload)
    contract = CONTRACT_BINDING.model_dump(mode="json")
    spec = {
        "company_id": COMPANY,
        "entity_id": ENTITY,
        "engagement_id": ENGAGEMENT,
        "producer_id": PRODUCER_ID,
        "producer_version": PRODUCER_VERSION,
        "task_id": TASK_ID,
        "task_version": TASK_VERSION,
        "source_sha256": sha256(RAW).hexdigest().upper(),
        "filename": NAME,
    }
    bindings = {
        "request_id": request_id,
        "actor_id": ACTOR,
        "execution_id": execution_id,
        "analysis_id": analysis_id,
        "company_id": COMPANY,
        "entity_id": ENTITY,
        "engagement_id": ENGAGEMENT,
        "producer_id": PRODUCER_ID,
        "producer_version": PRODUCER_VERSION,
        "task_id": TASK_ID,
        "task_version": TASK_VERSION,
        "admission_contract_sha256": GENERIC_ADMISSION_CONTRACT_SHA256,
        "raw_source_sha256": spec["source_sha256"],
        "source_representation_sha256": source_facts.source_representation_sha256,
        "producer_input_sha256": sha256(projection_text.encode()).hexdigest().upper(),
    }
    receipt = GenericProducerReceiptContractV3(
        evidence_status="ADMITTED_EXECUTION",
        bindings=bindings,
        contract_binding=CONTRACT_BINDING,
        contract_binding_sha256=GENERIC_ADMISSION_CONTRACT_SHA256,
        request_sha256=sha256(projection_text.encode()).hexdigest().upper(),
        response_sha256=sha256(_canonical(response).encode()).hexdigest().upper(),
        projection_sha256=bindings["producer_input_sha256"],
        envelope_sha256=envelope_sha,
        provider_policy_evidence_sha256="E" * 64,
    ).model_dump(mode="json")
    result = envelope.analysis_result.model_dump(mode="json")
    result["id"] = analysis_id
    analysis_row = {
        "id": analysis_id,
        "company_id": COMPANY,
        "entity_id": ENTITY,
        "fichier_nom": NAME,
        "fichier_type": "xlsx",
        "type_document": "AUTRE",
        "analyse_json": result,
        "source_data_hash": spec["source_sha256"].lower(),
        "status": "completed",
    }
    envelope_row = {
        "analysis_id": analysis_id,
        "company_id": COMPANY,
        "entity_id": ENTITY,
        "engagement_id": ENGAGEMENT,
        "envelope_json": payload,
        "envelope_sha256": envelope_sha,
        "source_representation_sha256": source_facts.source_representation_sha256,
        "envelope_schema_version": "v1-governed-analysis-1",
        "binding_sha256": _binding(
            analysis_id=analysis_id, company_id=COMPANY, entity_id=ENTITY,
            engagement_id=ENGAGEMENT, envelope_sha256=envelope_sha,
            source_sha256=source_facts.source_representation_sha256,
        ),
    }
    v3sql(
        "INSERT INTO generic_producer_policies_v3(id,specification,contract_binding,"
        "contract_binding_text,contract_binding_sha256,enabled) VALUES ("
        f"{literal(policy_id)},{js(spec)},{js(contract)},{literal(_canonical(contract))},"
        f"{literal(GENERIC_ADMISSION_CONTRACT_SHA256)},true)"
    )
    return SimpleNamespace(
        policy_id=policy_id, bindings=bindings, contract=contract,
        source=source_facts.model_dump(mode="json"), projection_text=projection_text,
        receipt=receipt, analysis=analysis_row, envelope=envelope_row,
        envelope_text=_canonical(payload),
    )


def reserve_sql(case, *, bindings=None, contract=None):
    return (
        "SET ROLE service_role; SELECT reserve_generic_execution_v3("
        f"{literal(case.policy_id)},{js(bindings or case.bindings)},"
        f"{js(contract or case.contract)},{js(case.source)},"
        f"{literal(case.projection_text)},{literal(NAME)},120)"
    )


def reserve(v3sql, case):
    return json.loads(v3sql(reserve_sql(case)))


def claim_sql(case, reservation):
    return (
        "SET ROLE service_role; SELECT claim_generic_execution_v3("
        f"{literal(case.bindings['execution_id'])},{literal(ACTOR)},"
        f"{literal(reservation['composition_sha256'])})"
    )


def claim(v3sql, case, reservation):
    return json.loads(v3sql(claim_sql(case, reservation)))


def complete(v3sql, case, claimed, *, receipt=None):
    return json.loads(v3sql(
        "SET ROLE service_role; SELECT complete_generic_execution_v3("
        f"{literal(case.bindings['execution_id'])},{literal(ACTOR)},"
        f"{literal(claimed['claim_id'])},{js(receipt or case.receipt)},"
        f"{js(case.analysis)},{js(case.envelope)},{literal(case.envelope_text)})"
    ))


def assert_no_result(v3sql, case):
    key = literal(case.bindings["analysis_id"])
    assert v3sql(
        f"SELECT (SELECT count(*) FROM analyses WHERE id={key})+"
        f"(SELECT count(*) FROM governed_analysis_envelopes WHERE analysis_id={key})+"
        f"(SELECT count(*) FROM generic_execution_receipts_v3 WHERE analysis_id={key})"
    ) == "0"


def test_v3_registry_refuses_declared_digest_not_matching_canonical_binding(v3sql):
    policy_id = str(uuid4())
    contract = CONTRACT_BINDING.model_dump(mode="json")
    v3sql(
        "INSERT INTO generic_producer_policies_v3(id,specification,contract_binding,"
        "contract_binding_text,contract_binding_sha256,enabled) VALUES ("
        f"{literal(policy_id)},'{{}}'::jsonb,{js(contract)},"
        f"{literal(_canonical(contract))},{literal('A' * 64)},false)",
        fail=True,
    )
    assert v3sql(
        "SELECT count(*) FROM generic_producer_policies_v3 WHERE id=" + literal(policy_id)
    ) == "0"


def test_v3_atomic_persistence_and_independent_historical_reread(v3sql):
    case = setup(v3sql)
    reserved = reserve(v3sql, case)
    claimed = claim(v3sql, case, reserved)
    assert reserved["contract_binding_sha256"] == GENERIC_ADMISSION_CONTRACT_SHA256
    assert claimed["contract_binding"] == case.contract
    assert complete(v3sql, case, claimed)["status"] == "COMPLETE"
    key = literal(case.bindings["analysis_id"])
    persisted = json.loads(v3sql(
        "SELECT r.receipt::text FROM generic_execution_receipts_v3 r "
        "JOIN generic_execution_admissions_v3 a USING(execution_id) "
        f"WHERE r.analysis_id={key} AND a.state='COMPLETE'"
    ))
    reread = verify_generic_receipt_contract_v3(persisted)
    assert reread.contract_binding == CONTRACT_BINDING
    assert reread.contract_binding_sha256 == GENERIC_ADMISSION_CONTRACT_SHA256
    assert str(reread.bindings.analysis_id) == case.bindings["analysis_id"]
    v3sql(claim_sql(case, reserved), fail=True)
    v3sql(
        f"UPDATE generic_execution_receipts_v3 SET receipt='{{}}'::jsonb WHERE analysis_id={key}",
        fail=True,
    )


@pytest.mark.parametrize("field", [
    "fact_schema_version",
    "positive_projection_policy_version",
    "task_version",
    "output_contract_version",
])
def test_v3_reservation_rejects_version_substitution_without_state(v3sql, field):
    case = setup(v3sql)
    altered = dict(case.contract)
    altered[field] = "v2-never-admitted"
    v3sql(reserve_sql(case, contract=altered), fail=True)
    assert v3sql(
        "SELECT count(*) FROM generic_execution_admissions_v3 WHERE execution_id="
        + literal(case.bindings["execution_id"])
    ) == "0"
    assert_no_result(v3sql, case)


def test_v3_rejects_mix_and_match_of_individually_well_formed_components(v3sql):
    case = setup(v3sql)
    altered = dict(case.contract)
    altered["fact_schema_sha256"] = "A" * 64
    v3sql(reserve_sql(case, contract=altered), fail=True)
    assert_no_result(v3sql, case)


@pytest.mark.parametrize("fault", [
    "fact_schema", "projection", "task", "output", "binding_digest", "envelope"
])
def test_v3_completion_mismatch_rolls_back_and_burns_claim(v3sql, fault):
    case = setup(v3sql)
    reserved = reserve(v3sql, case)
    claimed = claim(v3sql, case, reserved)
    receipt = copy.deepcopy(case.receipt)
    if fault in {"fact_schema", "projection", "task", "output"}:
        field = {
            "fact_schema": "fact_schema_sha256",
            "projection": "positive_projection_policy_sha256",
            "task": "task_contract_sha256",
            "output": "output_contract_sha256",
        }[fault]
        receipt["contract_binding"][field] = "B" * 64
    elif fault == "binding_digest":
        receipt["contract_binding_sha256"] = "C" * 64
    else:
        receipt["envelope_sha256"] = "D" * 64
    assert complete(v3sql, case, claimed, receipt=receipt)["status"] == "REFUSED"
    assert_no_result(v3sql, case)
    assert v3sql(
        "SELECT state FROM generic_execution_admissions_v3 WHERE execution_id="
        + literal(case.bindings["execution_id"])
    ) == "REFUSED"
    v3sql(claim_sql(case, reserved), fail=True)


def test_v3_concurrent_claim_has_one_winner_and_no_implicit_retry(v3sql):
    case = setup(v3sql)
    reserved = reserve(v3sql, case)

    def attempt(_):
        try:
            return claim(v3sql, case, reserved)["status"]
        except AssertionError:
            return "REFUSED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["CLAIMED", "REFUSED"]
    assert_no_result(v3sql, case)


def test_v39_v40_objects_and_rows_are_not_reinterpreted(v3sql):
    assert v3sql("SELECT count(*) FROM governed_execution_receipts") == "0"
    assert v3sql("SELECT count(*) FROM execution_receipts_v2") == "0"
    assert v3sql("SELECT count(*) FROM producer_policies_v2") == "0"
    assert v3sql(
        "SELECT count(*) FROM pg_proc WHERE proname IN "
        "('reserve_execution_v2','claim_execution_v2','complete_execution_v2')"
    ) == "3"
