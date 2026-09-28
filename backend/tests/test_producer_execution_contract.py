"""Contract preparation only: no generic producer or admission is exercised."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from services.producer_execution_contract import (
    ExecutionBindingsV2, ProducerExecutionCandidateV2, validate_candidate_consistency,
)
from services.governed_analysis_persistence import (
    GovernedPersistenceRefused, save_governed_analysis,
)
from test_execution_provenance import execution
from test_governed_analysis_persistence import (
    _analysis, _db, ANALYSIS, COMPANY_A, ENTITY_A, ENGAGEMENT_A,
)


@pytest.fixture
def candidate(execution):
    # A local fabricated candidate tests schema/binding logic, not a new producer.
    bindings = ExecutionBindingsV2(
        request_id=uuid4(), actor_id=uuid4(), execution_id=uuid4(), analysis_id=ANALYSIS,
        company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        producer_id="test-only-uninstalled-producer", producer_version="version-1",
        task_id="test-only-financial-task", task_version="version-1",
        admission_contract_sha256="A" * 64, producer_input_sha256="B" * 64,
        raw_source_sha256=execution.provenance.raw_source_sha256,
        source_representation_sha256=execution.provenance.source_representation_sha256,
    )
    now = datetime.now(timezone.utc)
    return ProducerExecutionCandidateV2(
        bindings=bindings, envelope_sha256=execution.provenance.envelope_sha256,
        started_at=now, completed_at=now,
    )


def check(candidate, execution, expected=None):
    return validate_candidate_consistency(
        candidate, expected_bindings=expected or candidate.bindings,
        envelope=execution.analysis.envelope,
    )


def test_consistent_candidate_is_not_admitted_even_on_repeat(candidate, execution):
    for _ in range(2):
        assert check(candidate, execution).evidence_status == "UNADMITTED_CANDIDATE"
    # This is deliberately not a replay-prevention ledger or admission grant.


@pytest.mark.parametrize("field", list(ExecutionBindingsV2.model_fields))
def test_every_expected_binding_is_compared(candidate, execution, field):
    data = candidate.bindings.model_dump(mode="json")
    if field in {"request_id", "actor_id", "execution_id", "analysis_id", "company_id", "entity_id", "engagement_id"}:
        data[field] = str(uuid4())
    elif field.endswith("sha256"):
        data[field] = "C" * 64
    else:
        data[field] = "different-version"
    forged = candidate.model_copy(update={"bindings": ExecutionBindingsV2(**data)})
    with pytest.raises(ValueError, match="PRODUCER_CANDIDATE_INCONSISTENT"):
        check(forged, execution, candidate.bindings)


@pytest.mark.parametrize("field,value", [
    ("evidence_status", "ADMITTED"),
    ("schema_version", "execution-provenance-1"),
    ("envelope_sha256", "0" * 64),
    ("started_at", datetime(2000, 1, 1)),
    ("completed_at", datetime(2000, 1, 1, tzinfo=timezone.utc)),
])
def test_copied_candidate_cannot_bypass_validation(candidate, execution, field, value):
    with pytest.raises(ValueError, match="PRODUCER_CANDIDATE_INCONSISTENT"):
        check(candidate.model_copy(update={field: value}), execution)


def test_nested_copied_binding_cannot_reuse_v1_identity(candidate, execution):
    bindings = candidate.bindings.model_copy(update={"producer_id": "registered-workbook-mock-v1"})
    with pytest.raises(ValueError, match="PRODUCER_CANDIDATE_INCONSISTENT"):
        check(candidate.model_copy(update={"bindings": bindings}), execution, bindings)


def test_matching_forged_expected_hash_cannot_override_envelope_source(candidate, execution):
    bindings = candidate.bindings.model_copy(update={"source_representation_sha256": "0" * 64})
    with pytest.raises(ValueError, match="PRODUCER_CANDIDATE_INCONSISTENT"):
        check(candidate.model_copy(update={"bindings": bindings}), execution, bindings)


def test_unknown_fields_and_secret_bearing_errors_are_not_returned(candidate, execution):
    data = candidate.model_dump(mode="json") | {"transport_secret": "DO_NOT_ECHO"}
    with pytest.raises(ValueError) as error:
        check(data, execution, candidate.bindings)
    assert str(error.value) == "PRODUCER_CANDIDATE_INCONSISTENT"


def test_candidate_is_rejected_by_existing_v39_path_before_rpc(candidate, execution):
    db = _db()
    row = _analysis()
    row["source_data_hash"] = execution.provenance.raw_source_sha256.lower()
    with pytest.raises(GovernedPersistenceRefused):
        save_governed_analysis(
            db, analysis_row=row, engagement_id=ENGAGEMENT_A,
            envelope=execution.analysis.envelope, execution_provenance=candidate.model_dump(mode="json"),
        )
    assert not any(entry[0] == "rpc" for entry in db.log)
