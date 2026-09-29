"""Before/after falsification in the existing guarded, network-none PG fixture.

Historical acceptance is a reproduced defect, never an admission PASS.
No product transport, Auth, remote client or producer is invoked by these tests.
"""
import copy
import json
import re
from uuid import uuid4

import pytest

from test_v40_postgres import ACTOR, COMPANY, ENTITY, ENGAGEMENT, ROOT, js, literal, sql
from test_generic_receipt_v3_postgres import (
    v3sql, setup, reserve, reserve_sql, claim, complete, assert_no_result,
)
import test_generic_receipt_v3_postgres as existing


@pytest.fixture(scope="module", params=["historical", "hardened"])
def checked_db(request, v3sql):
    original = (ROOT / "migrations/v41_generic_producer_receipts_v3.sql").read_text(encoding="utf-8")
    if request.param == "hardened":
        metadata = catalog_without_corrected_bodies(v3sql)
        history = unchanged_tables_snapshot(v3sql)
        v3sql((ROOT / "migrations/prepared_v41_validation_hardening.sql").read_text(encoding="utf-8"))
        assert catalog_without_corrected_bodies(v3sql) == metadata
        assert unchanged_tables_snapshot(v3sql) == history
    yield v3sql, request.param == "hardened"
    if request.param == "hardened":
        for name in ("reserve_generic_execution_v3", "complete_generic_execution_v3"):
            definition = re.search(r"CREATE FUNCTION public\." + name + r"\([\s\S]*?END \$\$;", original)[0]
            v3sql(definition.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))


def catalog_without_corrected_bodies(db):
    # proargdefaults contains parser character offsets: CREATE OR REPLACE adds
    # eleven characters without changing DEFAULT 30. Compare its deparsed SQL
    # arguments, retaining every other catalog attribute and unmodified body.
    return db("SELECT jsonb_agg((to_jsonb(p) - ARRAY['prosrc','proargdefaults']) || "
              "jsonb_build_object('arguments',pg_get_function_arguments(p.oid),'prosrc', "
              "CASE WHEN proname IN ('reserve_generic_execution_v3','complete_generic_execution_v3') "
              "THEN '<only authorized body change>' ELSE prosrc END) ORDER BY p.oid) "
              "FROM pg_proc p WHERE pronamespace='public'::regnamespace")


def no_result_and_terminal(db, case):
    assert_no_result(db, case)
    assert db("SELECT state FROM generic_execution_admissions_v3 WHERE execution_id="
              + literal(case.bindings["execution_id"])) == "REFUSED"
    assert db("SELECT count(*) FROM generic_execution_receipts_v3 WHERE execution_id="
              + literal(case.bindings["execution_id"])) == "0"


def unchanged_tables_snapshot(db):
    tables = json.loads(db("SELECT json_agg(tablename ORDER BY tablename) FROM pg_tables "
                          "WHERE schemaname='public' AND tablename <> 'generic_execution_admissions_v3'"))
    assert all(re.fullmatch(r"[a-z0-9_]+", table) for table in tables)
    return db(" UNION ALL ".join(
        "SELECT " + literal(table) + " || ':' || coalesce(string_agg(row_data, ',' ORDER BY row_data),'') "
        + "FROM (SELECT to_jsonb(t)::text AS row_data FROM public." + table + " t) s"
        for table in tables
    ))


@pytest.mark.parametrize("scope", ["company", "entity", "engagement"])
def test_policy_cannot_authorize_another_valid_owned_scope(checked_db, scope):
    db, hardened = checked_db
    case = setup(db)
    actor, company, entity, engagement = ACTOR, COMPANY, ENTITY, ENGAGEMENT
    if scope == "company":
        actor, company = str(uuid4()), str(uuid4())
        db(f"INSERT INTO companies VALUES ({literal(company)}); "
           f"INSERT INTO profiles VALUES ({literal(actor)},{literal(company)});")
    if scope in {"company", "entity"}:
        entity = str(uuid4())
        db(f"INSERT INTO entities VALUES ({literal(entity)},{literal(company)})")
    # Local fixture has UNIQUE(entity_id); a foreign engagement belongs to a
    # second valid entity. No mutation of the existing ownership rows.
    if scope == "engagement":
        entity = str(uuid4())
        db(f"INSERT INTO entities VALUES ({literal(entity)},{literal(company)})")
    engagement = str(uuid4())
    db(f"INSERT INTO engagements VALUES ({literal(engagement)},{literal(entity)})")
    changed = dict(case.bindings, actor_id=actor, company_id=company,
                   entity_id=entity, engagement_id=engagement)
    if hardened:
        db(reserve_sql(case, bindings=changed), fail=True)
        assert db("SELECT count(*) FROM generic_execution_admissions_v3 WHERE execution_id="
                  + literal(case.bindings["execution_id"])) == "0"
    else:
        assert json.loads(db(reserve_sql(case, bindings=changed)))["status"] == "RESERVED"
    assert_no_result(db, case)


RECEIPT_KEYS = (
    "schema_version", "evidence_status", "bindings", "contract_binding",
    "contract_binding_sha256", "request_sha256", "response_sha256",
    "projection_sha256", "envelope_sha256", "provider_policy_evidence_sha256",
)
UNGUARDED = {"request_sha256", "response_sha256", "provider_policy_evidence_sha256"}


@pytest.mark.parametrize("key", RECEIPT_KEYS)
@pytest.mark.parametrize("fault", ["missing", "null", "wrong_type"])
def test_required_receipt_members_are_present_nonnull_and_typed(checked_db, key, fault):
    db, hardened = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    receipt = copy.deepcopy(case.receipt)
    if fault == "missing":
        del receipt[key]
    elif fault == "null":
        receipt[key] = None
    else:
        receipt[key] = int("1" * 64)
    before = unchanged_tables_snapshot(db)
    result = complete(db, case, claimed, receipt=receipt)
    historical_hole = not hardened and key in UNGUARDED
    assert result["status"] == ("COMPLETE" if historical_hole else "REFUSED")
    if historical_hole:
        persisted = json.loads(db("SELECT receipt FROM generic_execution_receipts_v3 WHERE analysis_id="
                                  + literal(case.bindings["analysis_id"])))
        assert persisted == receipt  # Records the exact misleading historical acceptance.
    else:
        no_result_and_terminal(db, case)
        assert unchanged_tables_snapshot(db) == before


@pytest.mark.parametrize("key", ["contract_binding_sha256", "request_sha256", "response_sha256",
                                "projection_sha256", "envelope_sha256", "provider_policy_evidence_sha256"])
@pytest.mark.parametrize("bad", ["", "a" * 64, "A" * 63, "G" * 64])
def test_digest_lexical_contract(checked_db, key, bad):
    db, _ = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    receipt = dict(case.receipt, **{key: bad})
    before = unchanged_tables_snapshot(db)
    assert complete(db, case, claimed, receipt=receipt)["status"] == "REFUSED"
    no_result_and_terminal(db, case)
    assert unchanged_tables_snapshot(db) == before


def test_request_digest_must_match_reserved_request(checked_db):
    db, hardened = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    receipt = dict(case.receipt, request_sha256="A" * 64)
    assert complete(db, case, claimed, receipt=receipt)["status"] == ("REFUSED" if hardened else "COMPLETE")
    if hardened:
        no_result_and_terminal(db, case)


def test_valid_composition_and_replay(checked_db):
    db, _ = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    assert complete(db, case, claimed)["status"] == "COMPLETE"
    before = db("SELECT receipt FROM generic_execution_receipts_v3 WHERE analysis_id=" + literal(case.bindings["analysis_id"]))
    with pytest.raises(AssertionError):
        complete(db, case, claimed)
    assert before == db("SELECT receipt FROM generic_execution_receipts_v3 WHERE analysis_id=" + literal(case.bindings["analysis_id"]))


@pytest.mark.parametrize("field", ["company_id", "entity_id", "engagement_id"])
@pytest.mark.parametrize("fault", ["missing", "null", "numeric"])
def test_policy_requires_each_scope_member(checked_db, field, fault):
    db, hardened = checked_db
    case = setup(db)
    new_policy = str(uuid4())
    expression = "specification - " + literal(field)
    if fault != "missing":
        expression = "jsonb_set(specification, ARRAY[" + literal(field) + "], '" + ("null" if fault == "null" else "42") + "'::jsonb)"
    db("INSERT INTO generic_producer_policies_v3(id,specification,contract_binding,contract_binding_text,contract_binding_sha256,enabled) "
       "SELECT " + literal(new_policy) + "," + expression + ",contract_binding,contract_binding_text,contract_binding_sha256,true "
       "FROM generic_producer_policies_v3 WHERE id=" + literal(case.policy_id))
    case.policy_id = new_policy
    if hardened:
        db(reserve_sql(case), fail=True)
        assert db("SELECT count(*) FROM generic_execution_admissions_v3 WHERE execution_id="
                  + literal(case.bindings["execution_id"])) == "0"
    else:
        assert reserve(db, case)["status"] == "RESERVED"
    assert_no_result(db, case)


@pytest.mark.parametrize("check", [
    existing.test_v3_atomic_persistence_and_independent_historical_reread,
    existing.test_v3_concurrent_claim_has_one_winner_and_no_implicit_retry,
    existing.test_v3_registry_refuses_declared_digest_not_matching_canonical_binding,
    existing.test_v3_rejects_mix_and_match_of_individually_well_formed_components,
])
def test_existing_invariants_before_and_after(checked_db, check):
    check(checked_db[0])


@pytest.mark.parametrize("fault", ["fact_schema", "projection", "task", "output", "binding_digest", "envelope"])
def test_existing_atomic_refusals_before_and_after(checked_db, fault):
    existing.test_v3_completion_mismatch_rolls_back_and_burns_claim(checked_db[0], fault)


def test_storage_taxonomy_failure_leaves_only_refused_admission(checked_db):
    db, _ = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    case.analysis["type_document"] = "FINANCIAL_WORKBOOK"
    before = unchanged_tables_snapshot(db)
    assert complete(db, case, claimed)["status"] == "REFUSED"
    no_result_and_terminal(db, case)
    assert unchanged_tables_snapshot(db) == before


def test_failure_after_analysis_insert_rolls_back_entire_trio(checked_db):
    db, _ = checked_db
    case = setup(db)
    claimed = claim(db, case, reserve(db, case))
    # This row field reaches V27 only after the analysis INSERT; its CHECK
    # fails on the envelope INSERT inside the same completion subtransaction.
    case.envelope["binding_sha256"] = "INVALID"
    before = unchanged_tables_snapshot(db)
    assert complete(db, case, claimed)["status"] == "REFUSED"
    no_result_and_terminal(db, case)
    assert unchanged_tables_snapshot(db) == before


@pytest.mark.parametrize("stage", ["claim", "complete"])
def test_expired_admission_never_creates_result(checked_db, stage):
    db, _ = checked_db
    case = setup(db)
    reservation = json.loads(db(reserve_sql(case).replace(",120)", ",1)")))
    claimed = claim(db, case, reservation) if stage == "complete" else None
    db("SELECT pg_sleep(1.1)")
    before = unchanged_tables_snapshot(db)
    if stage == "claim":
        with pytest.raises(AssertionError):
            claim(db, case, reservation)
        assert_no_result(db, case)
    else:
        assert complete(db, case, claimed)["status"] == "REFUSED"
        no_result_and_terminal(db, case)
    assert unchanged_tables_snapshot(db) == before


def test_correction_precondition_rejects_reapplication(checked_db):
    db, hardened = checked_db
    if not hardened:
        # Historical phase is still exactly the baseline accepted by the patch.
        return
    before = catalog_without_corrected_bodies(db), unchanged_tables_snapshot(db)
    patch = (ROOT / "migrations/prepared_v41_validation_hardening.sql").read_text(encoding="utf-8")
    assert "POST_V41_BASELINE_REFUSED" in db(patch, fail=True)
    assert (catalog_without_corrected_bodies(db), unchanged_tables_snapshot(db)) == before


def test_disabled_policy_refuses_claim_without_result(checked_db):
    db, _ = checked_db
    case = setup(db)
    reservation = reserve(db, case)
    db("UPDATE generic_producer_policies_v3 SET enabled=false WHERE id=" + literal(case.policy_id))
    before = unchanged_tables_snapshot(db)
    with pytest.raises(AssertionError):
        claim(db, case, reservation)
    assert_no_result(db, case)
    assert unchanged_tables_snapshot(db) == before
