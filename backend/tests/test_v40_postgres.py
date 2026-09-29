"""Opt-in actual local PostgreSQL tests. Never use a cloud URL or credentials.

PEPPERYN_LOCAL_PG_CONTAINER must name the separately created isolated container.
Creates only new uniquely named test databases; never drops existing databases.
"""
import copy
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from sandbox.heterogeneous_workbooks import _mock_response, run_recorded_registered_mock_analysis
from services.governed_analysis_persistence import _binding, _canonical_bytes, _digest

CONTAINER = os.getenv("PEPPERYN_LOCAL_PG_CONTAINER")
pytestmark = pytest.mark.skipif(not CONTAINER, reason="Explicit isolated local PostgreSQL required")
ROOT = Path(__file__).parents[1]
ACTOR, COMPANY, ENTITY, ENGAGEMENT = [str(uuid4()) for _ in range(4)]
NAME = "pepperyn_v1_heterogeneous_english.xlsx"
RAW = (ROOT / "tests/golden/fixtures" / NAME).read_bytes()


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def js(value):
    return literal(json.dumps(value, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"


@pytest.fixture(scope="module")
def sql():
    inspected = subprocess.run(["docker", "inspect", "--format",
        '{{.HostConfig.NetworkMode}}|{{json .HostConfig.PortBindings}}|{{index .Config.Labels "pepperyn.purpose"}}|{{json .HostConfig.Binds}}',
        CONTAINER], capture_output=True, text=True, check=True).stdout.strip()
    assert inspected in {"none|{}|b1-synthetic-sql-test|null", "none|null|b1-synthetic-sql-test|null"}, inspected
    database = "b1_v40_" + uuid4().hex
    def query(statement, *, fail=False, db=database):
        result = subprocess.run(["docker", "exec", "-i", "-u", "postgres", CONTAINER,
            "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-d", db],
            input=statement.encode('utf-8'), capture_output=True, timeout=45)
        if fail:
            assert result.returncode != 0, "Expected SQL refusal"
            return result.stderr.decode('utf-8')
        assert result.returncode == 0, result.stderr
        return result.stdout.decode('utf-8').strip()
    query("CREATE DATABASE " + database, db="postgres")
    query("""
      DO $$ BEGIN
        IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
        IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
        IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='service_role') THEN CREATE ROLE service_role NOLOGIN BYPASSRLS; END IF;
      END $$;
      CREATE TABLE companies(id uuid PRIMARY KEY);
      CREATE TABLE profiles(id uuid PRIMARY KEY,company_id uuid NOT NULL REFERENCES companies(id));
      CREATE TABLE entities(id uuid PRIMARY KEY,company_id uuid NOT NULL REFERENCES companies(id));
      CREATE TABLE engagements(id uuid PRIMARY KEY,entity_id uuid NOT NULL UNIQUE REFERENCES entities(id));
    """)
    query((ROOT/'tests/fixtures/v40_analyses_schema.sql').read_text(encoding='utf-8'))
    for filename in ("v27_governed_analysis_envelopes.sql", "v39_governed_execution_receipts.sql"):
        query((ROOT / "migrations" / filename).read_text(encoding="utf-8"))
    preflight=(ROOT/'migrations/v40_preflight_read_only.sql').read_text(encoding='utf-8')
    assert json.loads(query(preflight))['status']=='PREFLIGHT_PASS'
    query((ROOT/'migrations/v40_prospective_execution_admission.sql').read_text(encoding='utf-8'))
    postflight=json.loads(query((ROOT/'migrations/v40_postflight_read_only.sql').read_text(encoding='utf-8')))
    assert postflight['policy_rows']==postflight['admission_rows']==postflight['receipt_rows']==0
    assert len(postflight['tables'])==3 and len(postflight['functions'])==6
    for table in postflight['tables']:
        assert table['rls_enabled'] and table['policy_count']==0 and table['immutable_trigger_count']==1
        for role,privileges in table['privileges'].items():
            assert privileges==dict(select=role=='service_role',insert=False,update=False,delete=False,truncate=False)
    for function in postflight['functions']:
        assert not function['anon_execute'] and not function['authenticated_execute']
        assert function['service_execute']==function['security_definer']
    assert json.loads(query(preflight))['status']=='REFUSED'
    assert query("SELECT count(*) FROM producer_policies_v2") == "0"
    query(f"INSERT INTO companies VALUES ({literal(COMPANY)}); INSERT INTO profiles VALUES ({literal(ACTOR)},{literal(COMPANY)});"
          f"INSERT INTO entities VALUES ({literal(ENTITY)},{literal(COMPANY)}); INSERT INTO engagements VALUES ({literal(ENGAGEMENT)},{literal(ENTITY)});")
    query.database = database
    return query


@pytest.mark.parametrize('variant,expected', [
    ('lf',True), ('crlf',True), ('literal',False), ('space',False),
    ('bare_cr',False), ('default',False), ('definer',False),
])
def test_definition_verifier_local_only(sql, variant, expected):
    migration = (ROOT/'migrations/v40_prospective_execution_admission.sql').read_text()
    original = re.search(r'CREATE FUNCTION public.reserve_execution_v2\([\s\S]*?END \$\$;',migration)[0]
    original = original.replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
    changed = original
    if variant == 'crlf':
        changed = changed.replace('\n','\r\n')
    elif variant == 'literal':
        changed = changed.replace("'UNDERSTOOD'", "'UNKNOWN'")
    elif variant == 'space':
        changed = changed.replace('  k TEXT;', '   k TEXT;')
    elif variant == 'bare_cr':
        changed = changed.replace('  k TEXT;', '  k\r TEXT;')
    elif variant == 'default':
        changed = changed.replace('DEFAULT 30','DEFAULT 31')
    elif variant == 'definer':
        changed = changed.replace('SECURITY DEFINER','SECURITY INVOKER')
    # Only the unique disposable local database from the guarded fixture.
    try:
        sql(changed)
        report = json.loads(sql((ROOT/'migrations/v40_definition_conformance_read_only.sql').read_text()))
        assert (report['status']=='BOUNDED_DEFINITION_CONFORMANCE_PASS') is expected
        assert report['write_performed'] is False
        assert len(report['functions']) == 6
        assert all('raw_sha256' in row and 'lf_sha256' in row for row in report['functions'])
    finally:
        sql(original)


def setup(sql, *, ttl=120):
    execution = run_recorded_registered_mock_analysis(RAW, NAME)
    envelope = execution.analysis.envelope
    input_text = envelope.source_facts.model_dump_json()
    policy = str(uuid4())
    spec = dict(company_id=COMPANY, entity_id=ENTITY, engagement_id=ENGAGEMENT,
        producer_id="test-only-uninstalled-producer", producer_version="version-1",
        task_id="test-only-analysis", task_version="version-1", source_sha256=sha256(RAW).hexdigest().upper(), filename=NAME)
    contract = _digest({'profile':spec,'policy':'LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2'})
    sql(f"INSERT INTO producer_policies_v2(id,specification,contract_sha256,enabled) VALUES ({literal(policy)},{js(spec)},{literal(contract)},true)")
    bindings = dict(request_id=str(uuid4()), actor_id=ACTOR, execution_id=str(uuid4()), analysis_id=str(uuid4()),
        **{k:spec[k] for k in ('company_id','entity_id','engagement_id','producer_id','producer_version','task_id','task_version')},
        admission_contract_sha256=contract, raw_source_sha256=spec['source_sha256'],
        source_representation_sha256=envelope.source_facts.source_representation_sha256,
        producer_input_sha256=sha256(input_text.encode()).hexdigest().upper())
    return dict(policy=policy,b=bindings,input=input_text,envelope=envelope,ttl=ttl)


def reserve_sql(case):
    return f"SET ROLE service_role; SELECT reserve_execution_v2({literal(case['policy'])},{js(case['b'])},{literal(case['input'])},{literal(NAME)},{case['ttl']})"


def reserve(sql, case):
    return json.loads(sql(reserve_sql(case)))


def claim_sql(case, reservation, actor=ACTOR):
    return f"SET ROLE service_role; SELECT claim_execution_v2({literal(case['b']['execution_id'])},{literal(actor)},{literal(reservation['composition_sha256'])})"


def claim(sql, case, reservation):
    return json.loads(sql(claim_sql(case, reservation)))


def bundle(case, claimed):
    b, env = case['b'], case['envelope']
    envelope_json = env.model_dump(mode="json")
    envelope_json['governed_analysis']['invocation_nonce']=b['request_id'].replace('-','').upper()
    eh = _digest(envelope_json)
    envelope = dict(analysis_id=b['analysis_id'],company_id=COMPANY,entity_id=ENTITY,engagement_id=ENGAGEMENT,
        envelope_json=envelope_json,envelope_sha256=eh,source_representation_sha256=b['source_representation_sha256'],
        envelope_schema_version='v1-governed-analysis-1',binding_sha256=_binding(
            analysis_id=b['analysis_id'],company_id=COMPANY,entity_id=ENTITY,engagement_id=ENGAGEMENT,
            envelope_sha256=eh,source_sha256=b['source_representation_sha256']))
    result = env.analysis_result.model_dump(mode="json")
    result['id'] = b['analysis_id']
    analysis = dict(id=b['analysis_id'],company_id=COMPANY,entity_id=ENTITY,fichier_nom=NAME,
        source_data_hash=b['raw_source_sha256'].lower(),analyse_json=result,status='completed')
    candidate = dict(schema_version='producer-execution-candidate-2',evidence_status='UNADMITTED_CANDIDATE',
        bindings=b,envelope_sha256=eh,started_at=claimed['claimed_at'],completed_at=datetime.now(timezone.utc).isoformat())
    return candidate,analysis,envelope,_canonical_bytes(envelope_json).decode()


def finish(sql, case, claimed, parts=None):
    candidate,analysis,envelope,text = parts or bundle(case,claimed)
    return json.loads(sql(f"SET ROLE service_role; SELECT complete_execution_v2({literal(case['b']['execution_id'])},"
        f"{literal(ACTOR)},{literal(claimed['claim_id'])},{js(candidate)},{js(analysis)},{js(envelope)},{literal(text)})"))


def no_result(sql, case):
    key = literal(case['b']['analysis_id'])
    assert sql(f"SELECT (SELECT count(*) FROM analyses WHERE id={key}) + "
               f"(SELECT count(*) FROM governed_analysis_envelopes WHERE analysis_id={key}) + "
               f"(SELECT count(*) FROM execution_receipts_v2 WHERE analysis_id={key})") == '0'


def test_atomic_positive_fresh_process_and_replay(sql):
    case=setup(sql); r=reserve(sql,case); c=claim(sql,case,r)
    assert finish(sql,case,c)['status']=='COMPLETE'
    key=literal(case['b']['analysis_id'])
    assert sql(f"SELECT count(*) FROM analyses a JOIN governed_analysis_envelopes e ON e.analysis_id=a.id "
               f"JOIN execution_receipts_v2 r ON r.analysis_id=a.id WHERE a.id={key}")=='1'
    sql(claim_sql(case,r),fail=True)
    with pytest.raises(AssertionError): finish(sql,case,c)
    assert sql(f"SELECT state FROM execution_admissions_v2 WHERE analysis_id={key}")=='COMPLETE'


def test_concurrent_claims_one_winner(sql):
    case=setup(sql); r=reserve(sql,case)
    def attempt():
        try: return claim(sql,case,r)['status']
        except AssertionError: return 'REFUSED'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _:attempt(),range(2)))==['CLAIMED','REFUSED']
    # First claimant exits with no result; a fresh process cannot execute again.
    sql(claim_sql(case,r),fail=True)
    no_result(sql,case)


@pytest.mark.parametrize('field', ['actor_id','company_id','entity_id','engagement_id','producer_id','producer_version',
    'task_id','task_version','admission_contract_sha256','raw_source_sha256','source_representation_sha256','producer_input_sha256'])
def test_reservation_substitution_no_durable_admission(sql,field):
    case=setup(sql)
    case['b'][field]=str(uuid4()) if field.endswith('_id') and field not in {'producer_id','task_id'} else ('0'*64 if field.endswith('sha256') else 'foreign')
    sql(reserve_sql(case),fail=True)
    assert sql(f"SELECT count(*) FROM execution_admissions_v2 WHERE execution_id={literal(case['b']['execution_id'])}")=='0'
    no_result(sql,case)


@pytest.mark.parametrize('kind',['receipt','scope','source','envelope','input','status'])
def test_completion_mismatch_terminal_refusal(sql,kind):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    candidate,analysis,envelope,text=bundle(case,c)
    candidate=copy.deepcopy(candidate)
    if kind=='receipt': candidate['bindings']['execution_id']=str(uuid4())
    if kind=='scope': analysis['entity_id']=str(uuid4())
    if kind=='source': analysis['source_data_hash']='0'*64
    if kind=='envelope': envelope['envelope_sha256']='0'*64
    if kind=='input': candidate['bindings']['producer_input_sha256']='0'*64
    if kind=='status': candidate['evidence_status']='ADMITTED'
    assert finish(sql,case,c,(candidate,analysis,envelope,text))['status']=='REFUSED'
    no_result(sql,case)
    assert sql(f"SELECT state FROM execution_admissions_v2 WHERE execution_id={literal(case['b']['execution_id'])}")=='REFUSED'
    sql(claim_sql(case,r),fail=True)


def test_existing_envelope_constraint_rolls_back_analysis_without_schema_change(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    parts=bundle(case,c)
    # Reuse the existing V27 CHECK after its analysis INSERT. No fault trigger.
    parts[2]['binding_sha256']='INVALID'
    assert finish(sql,case,c,parts)['status']=='REFUSED'
    no_result(sql,case)
    assert sql(f"SELECT state FROM execution_admissions_v2 WHERE execution_id={literal(case['b']['execution_id'])}")=='REFUSED'
    sql(claim_sql(case,r),fail=True)


def test_late_receipt_failure_rolls_back_entire_result_and_burns_attempt(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    # Fault injection ONLY into this uniquely created synthetic test database.
    sql("CREATE FUNCTION test_late_receipt_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'test fault'; END $$; "
        "CREATE TRIGGER test_late_failure BEFORE INSERT ON execution_receipts_v2 FOR EACH ROW EXECUTE FUNCTION test_late_receipt_failure();")
    try:
        assert finish(sql,case,c)['status']=='REFUSED'
        no_result(sql,case)
        sql(claim_sql(case,r),fail=True)
    finally:
        sql("DROP TRIGGER test_late_failure ON execution_receipts_v2; DROP FUNCTION test_late_receipt_failure();")


def test_expiry_closure_and_no_reenable(sql):
    case=setup(sql,ttl=1);r=reserve(sql,case)
    sql('SELECT pg_sleep(1.1)')
    sql(claim_sql(case,r),fail=True);no_result(sql,case)
    case=setup(sql);r=reserve(sql,case)
    sql(f"SET ROLE service_role; SELECT close_execution_v2({literal(case['b']['execution_id'])},{literal(ACTOR)})")
    sql(claim_sql(case,r),fail=True);no_result(sql,case)


def test_backend_only_permissions_and_immutable_material(sql):
    case=setup(sql);r=reserve(sql,case)
    for role in ('anon','authenticated'):
        sql('SET ROLE '+role+'; SELECT * FROM execution_admissions_v2',fail=True)
        sql('SET ROLE '+role+'; '+claim_sql(case,r).split(';',1)[1],fail=True)
    for table in ('producer_policies_v2','execution_admissions_v2','execution_receipts_v2'):
        for privilege in ('INSERT','UPDATE','DELETE','TRUNCATE'):
            assert sql(f"SELECT has_table_privilege('service_role','{table}','{privilege}')")=='f'
    sql("UPDATE execution_admissions_v2 SET input_text='{}' WHERE execution_id="+literal(case['b']['execution_id']),fail=True)
    sql("DELETE FROM execution_admissions_v2 WHERE execution_id="+literal(case['b']['execution_id']),fail=True)
    no_result(sql,case)


def test_duplicate_reservation_cannot_rebind_same_analysis_or_request(sql):
    case=setup(sql);reserve(sql,case)
    for field in ('execution_id','request_id','analysis_id'):
        swapped=copy.deepcopy(case);swapped['b'][field]=str(uuid4())
        sql(reserve_sql(swapped),fail=True)
    no_result(sql,case)


def test_disable_policy_after_claim_and_reenable_refused(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    sql(f"UPDATE producer_policies_v2 SET enabled=false WHERE id={literal(case['policy'])}")
    assert finish(sql,case,c)['status']=='REFUSED'
    sql(f"UPDATE producer_policies_v2 SET enabled=true WHERE id={literal(case['policy'])}",fail=True)
    no_result(sql,case)


def test_membership_revoked_between_claim_and_completion(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    foreign=str(uuid4())
    sql(f"INSERT INTO companies VALUES ({literal(foreign)}); UPDATE profiles SET company_id={literal(foreign)} WHERE id={literal(ACTOR)}")
    try:
        assert finish(sql,case,c)['status']=='REFUSED';no_result(sql,case)
    finally:
        sql(f"UPDATE profiles SET company_id={literal(COMPANY)} WHERE id={literal(ACTOR)}")


def test_completion_expiry_refuses_and_cannot_claim_again(sql):
    case=setup(sql,ttl=2);r=reserve(sql,case);c=claim(sql,case,r)
    sql('SELECT pg_sleep(2.1)')
    assert finish(sql,case,c)['status']=='REFUSED';no_result(sql,case)
    sql(claim_sql(case,r),fail=True)


def test_new_backend_adapter_uses_actual_sql_without_v39_fallback(sql):
    from types import SimpleNamespace
    from services.durable_producer_admission import DurableProducerAdmission, ReservedExecution
    from services.producer_execution_contract import ExecutionBindingsV2
    case=setup(sql)
    calls=[]
    class Adapter:
        def rpc(self,name,params):
            calls.append(name)
            args=','.join(js(v) if isinstance(v,dict) else literal(v) for v in params.values())
            return SimpleNamespace(execute=lambda:SimpleNamespace(data=json.loads(sql(
                f'SET ROLE service_role; SELECT {name}({args})'))))
    preparation=SimpleNamespace(
        _contract_policy='LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2',
        _principal=lambda auth:SimpleNamespace(principal_id=ACTOR,company_id=COMPANY),
        consume_for_local_validation=lambda prepared,**kwargs:case['input'])
    b=ExecutionBindingsV2(**case['b'])
    prepared=SimpleNamespace(bindings=b,filename=NAME)
    service=DurableProducerAdmission(Adapter(),preparation=preparation,policy_id=case['policy'])
    reservation=service.reserve(prepared,authorization='synthetic-test-auth',raw=RAW)
    # A fresh coordinator owns no process-local grant; durable claim is in SQL.
    service=DurableProducerAdmission(Adapter(),preparation=preparation,policy_id=case['policy'])
    claimed=service.claim(reservation,authorization='synthetic-test-auth')
    envelope=case['envelope'].model_dump(mode='json')
    envelope['governed_analysis']['invocation_nonce']=b.request_id.hex.upper()
    from services.v1_analysis_contract import GovernedAnalysisEnvelope
    result=service.complete(claimed,authorization='synthetic-test-auth',envelope=GovernedAnalysisEnvelope.model_validate(envelope))
    assert result['status']=='LOCAL_SYNTHETIC_PERSISTED' and result['generic_producer_admitted'] is False
    assert calls==['reserve_execution_v2','claim_execution_v2','complete_execution_v2']


def test_unadmitted_generic_candidate_composes_through_actual_v40_sql_without_egress(sql):
    """V40 proves mechanics only; its receipt must remain local/synthetic."""
    import asyncio
    from types import SimpleNamespace
    from services.durable_producer_admission import DurableProducerAdmission
    from services.generic_producer_candidate import (
        InjectedOpenAIResponsesCandidate, PRODUCER_ID, PRODUCER_VERSION,
        TASK_ID, TASK_VERSION,
    )
    from services.governed_producer_adapter import GovernedProducerAdapter, GovernedProducerCoordinator
    from services.producer_execution_contract import ExecutionBindingsV2
    case=setup(sql)
    policy=str(uuid4())
    # The old setup policy is left unused; a distinct local-only policy binds
    # the exact genuine-producer candidate identity without admitting it.
    spec=dict(company_id=COMPANY,entity_id=ENTITY,engagement_id=ENGAGEMENT,
        producer_id=PRODUCER_ID,producer_version=PRODUCER_VERSION,
        task_id=TASK_ID,task_version=TASK_VERSION,
        source_sha256=sha256(RAW).hexdigest().upper(),filename=NAME)
    contract=_digest({'profile':spec,'policy':'LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2'})
    sql(f"INSERT INTO producer_policies_v2(id,specification,contract_sha256,enabled) VALUES ({literal(policy)},{js(spec)},{literal(contract)},true)")
    b=dict(case['b'],producer_id=PRODUCER_ID,producer_version=PRODUCER_VERSION,
        task_id=TASK_ID,task_version=TASK_VERSION,admission_contract_sha256=contract,
        request_id=str(uuid4()),execution_id=str(uuid4()),analysis_id=str(uuid4()))
    case=dict(case,policy=policy,b=b)
    calls=[]
    class Db:
        def rpc(self,name,params):
            calls.append(name)
            args=','.join(js(v) if isinstance(v,dict) else literal(v) for v in params.values())
            return SimpleNamespace(execute=lambda:SimpleNamespace(data=json.loads(sql(
                f'SET ROLE service_role; SELECT {name}({args})'))))
    preparation=SimpleNamespace(
        _contract_policy='LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2',
        _principal=lambda auth:SimpleNamespace(principal_id=ACTOR,company_id=COMPANY),
        consume_for_local_validation=lambda prepared,**kwargs:case['input'])
    bindings=ExecutionBindingsV2(**b)
    prepared=SimpleNamespace(bindings=bindings,filename=NAME)
    admission=DurableProducerAdmission(Db(),preparation=preparation,policy_id=policy)
    reservation=admission.reserve(prepared,authorization='synthetic-test-auth',raw=RAW)
    invocation_seen=[]
    def transport(request):
        invocation_seen.append(request)
        understanding=case['envelope'].source_facts
        nonce=bindings.request_id.hex.upper()
        return _mock_response(understanding,nonce)
    producer=InjectedOpenAIResponsesCandidate(transport)
    adapter=GovernedProducerAdapter(producer=producer,producer_id=PRODUCER_ID,
        producer_version=PRODUCER_VERSION,task_id=TASK_ID,task_version=TASK_VERSION,
        admission_contract_sha256=contract)
    result=asyncio.run(GovernedProducerCoordinator(admission=admission,adapter=adapter).execute(
        reservation,authorization='synthetic-test-auth'))
    assert result['status']=='LOCAL_SYNTHETIC_PERSISTED'
    assert result['generic_producer_admitted'] is False
    assert calls==['reserve_execution_v2','claim_execution_v2','complete_execution_v2']
    assert len(invocation_seen)==1
    evidence=producer.consume_local_evidence()
    assert evidence.evidence_status=='UNADMITTED_LOCAL_CONFORMANCE'
    receipt=json.loads(sql(f"SELECT receipt::text FROM execution_receipts_v2 WHERE analysis_id={literal(b['analysis_id'])}"))
    assert receipt['evidence_scope']=='LOCAL_SYNTHETIC_ONLY'
    assert receipt['egress']=='DENY'
    persisted=receipt['candidate']['bindings']
    assert persisted==bindings.model_dump(mode='json')
    for identity in ('request_id','execution_id','analysis_id','actor_id','company_id','entity_id','engagement_id'):
        assert persisted[identity]==b[identity]
    assert persisted['producer_id']==PRODUCER_ID
    assert persisted['producer_version']==PRODUCER_VERSION
    assert persisted['task_id']==TASK_ID and persisted['task_version']==TASK_VERSION
    assert sql(f"SELECT count(*) FROM governed_execution_receipts WHERE analysis_id={literal(b['analysis_id'])}")=='0'


def test_independent_process_recovery_preserves_completed_and_abandoned_claim(sql):
    completed=setup(sql);r=reserve(sql,completed);c=claim(sql,completed,r)
    assert finish(sql,completed,c)['status']=='COMPLETE'
    abandoned=setup(sql);r2=reserve(sql,abandoned);claim(sql,abandoned,r2)
    before=sql("SELECT upper(encode(sha256(convert_to(jsonb_agg(to_jsonb(a) ORDER BY execution_id)::text,'UTF8')),'hex')) FROM execution_admissions_v2 a")
    # Every sql() call starts/exits a separate psql process. This is recovery
    # across client processes, NOT database-server/host restart or backup proof.
    assert sql("SELECT upper(encode(sha256(convert_to(jsonb_agg(to_jsonb(a) ORDER BY execution_id)::text,'UTF8')),'hex')) FROM execution_admissions_v2 a")==before
    sql(claim_sql(abandoned,r2),fail=True)
    assert sql(f"SELECT state FROM execution_admissions_v2 WHERE execution_id={literal(completed['b']['execution_id'])}")=='COMPLETE'
    no_result(sql,abandoned)
