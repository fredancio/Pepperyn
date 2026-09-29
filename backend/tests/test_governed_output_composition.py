"""Local full composition/ASGI proof only; no deployed session or Beta proof."""
import copy
import hashlib
import json
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from pypdf import PdfReader
from pptx import Presentation

from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
from services.governed_analysis_persistence import save_governed_analysis, _digest
from services.governed_analysis_read import GovernedReadRefused
from services.governed_output import read_owned_output, export_owned_output
from services.generic_producer_candidate import (
    CONTRACT_BINDING, GENERIC_ADMISSION_CONTRACT_SHA256, PRODUCER_ID,
    PRODUCER_VERSION, TASK_ID, TASK_VERSION,
)
from services.v1_analysis_contract import build_openai_request_from_understanding
from routers.governed_output import build_governed_output_router
from test_governed_analysis_persistence import _db, ANALYSIS, COMPANY_A, COMPANY_B, ENTITY_A, ENGAGEMENT_A


@pytest.fixture
def stored():
    raw = Path('tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx').read_bytes()
    execution = run_recorded_registered_mock_analysis(raw, 'pepperyn_v1_heterogeneous_english.xlsx')
    db = _db()
    scope = dict(analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A)
    save_governed_analysis(db, analysis_row=dict(id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A,
        source_data_hash=execution.provenance.raw_source_sha256.lower()),
        engagement_id=ENGAGEMENT_A, envelope=execution.analysis.envelope)
    payload = execution.provenance.model_dump(mode='json') | scope
    db.tables['governed_execution_receipts'] = [scope | dict(payload=payload, sha256=_digest(payload))]
    return db, execution


def as_v40(db, execution):
    """Replace V39 evidence with a fully bound local V40 terminal receipt."""
    request = '50000000-0000-0000-0000-000000000001'
    execution_id = '60000000-0000-0000-0000-000000000001'
    actor = '70000000-0000-0000-0000-000000000001'
    policy = '80000000-0000-0000-0000-000000000001'
    contract = 'A' * 64
    input_text = execution.analysis.envelope.source_facts.model_dump_json()
    source = execution.provenance.raw_source_sha256
    representation = execution.provenance.source_representation_sha256
    bindings = dict(request_id=request, actor_id=actor, execution_id=execution_id,
        analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A,
        engagement_id=ENGAGEMENT_A, producer_id='local-synthetic-analysis-v2',
        producer_version='producer-v2', task_id='financial-analysis', task_version='task-v1',
        admission_contract_sha256=contract, raw_source_sha256=source,
        source_representation_sha256=representation,
        producer_input_sha256=hashlib.sha256(input_text.encode()).hexdigest().upper())
    claimed = '2026-09-28T12:00:00+00:00'
    completed = '2026-09-28T12:00:01+00:00'
    terminal = '2026-09-28T12:00:02+00:00'
    envelope_sha = _digest(execution.analysis.envelope.model_dump(mode='json'))
    candidate = dict(schema_version='producer-execution-candidate-2',
        evidence_status='UNADMITTED_CANDIDATE', bindings=bindings,
        envelope_sha256=envelope_sha, started_at=claimed, completed_at=completed)
    composition = 'B' * 64
    db.tables['governed_execution_receipts'] = []
    db.tables['analyses'][0].update(source_data_hash=source.lower(),
        fichier_nom='pepperyn_v1_heterogeneous_english.xlsx')
    db.tables['producer_policies_v2'] = [dict(id=policy, specification=dict(
        company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A,
        producer_id=bindings['producer_id'], producer_version=bindings['producer_version'],
        task_id=bindings['task_id'], task_version=bindings['task_version'],
        source_sha256=source, filename=db.tables['analyses'][0]['fichier_nom']),
        contract_sha256=contract, contract_version='local-synthetic-durable-admission-2',
        enabled=False, origin='SYNTHETIC', egress='DENY')]
    db.tables['execution_admissions_v2'] = [dict(bindings, policy_id=policy,
        bindings=bindings, input_text=input_text, filename=db.tables['analyses'][0]['fichier_nom'],
        composition_sha256=composition, state='COMPLETE', claim_id='90000000-0000-0000-0000-000000000001',
        issued_at='2026-09-28T11:59:59+00:00', claimed_at=claimed, terminal_at=terminal)]
    receipt = dict(schema_version='governed-execution-receipt-2',
        evidence_scope='LOCAL_SYNTHETIC_ONLY', egress='DENY', candidate=candidate,
        composition_sha256=composition, policy_id=policy,
        issued_at='2026-09-28T11:59:59+00:00', claimed_at=claimed)
    db.tables['execution_receipts_v2'] = [dict(execution_id=execution_id,
        analysis_id=ANALYSIS, receipt=receipt, created_at=terminal)]
    return bindings


def as_v41(db, execution, *, transport='INJECTED_LOCAL_ONLY', attested=False):
    """Replace V39 evidence with a complete, explicitly qualified V41 receipt."""
    request = '51000000-0000-0000-0000-000000000001'
    execution_id = '61000000-0000-0000-0000-000000000001'
    actor = '71000000-0000-0000-0000-000000000001'
    policy = '81000000-0000-0000-0000-000000000001'
    nonce = request.replace('-', '').upper()
    source_facts = execution.analysis.envelope.source_facts
    request_payload = build_openai_request_from_understanding(
        source_facts, invocation_nonce=nonce, model='gpt-5')
    projection_text = json.dumps(request_payload, ensure_ascii=False, allow_nan=False,
                                 sort_keys=True, separators=(',', ':'))
    source = execution.provenance.raw_source_sha256
    representation = execution.provenance.source_representation_sha256
    contract = CONTRACT_BINDING.model_dump(mode='json')
    bindings = dict(request_id=request, actor_id=actor, execution_id=execution_id,
        analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A,
        engagement_id=ENGAGEMENT_A, producer_id=PRODUCER_ID,
        producer_version=PRODUCER_VERSION, task_id=TASK_ID, task_version=TASK_VERSION,
        admission_contract_sha256=GENERIC_ADMISSION_CONTRACT_SHA256,
        raw_source_sha256=source, source_representation_sha256=representation,
        producer_input_sha256=hashlib.sha256(projection_text.encode()).hexdigest().upper())
    envelope_sha = _digest(execution.analysis.envelope.model_dump(mode='json'))
    db.tables['governed_execution_receipts'] = []
    db.tables['execution_receipts_v2'] = []
    db.tables['analyses'][0].update(source_data_hash=source.lower(),
        fichier_nom='pepperyn_v1_heterogeneous_english.xlsx')
    specification = dict(company_id=COMPANY_A, entity_id=ENTITY_A,
        engagement_id=ENGAGEMENT_A, producer_id=PRODUCER_ID,
        producer_version=PRODUCER_VERSION, task_id=TASK_ID, task_version=TASK_VERSION,
        source_sha256=source, filename=db.tables['analyses'][0]['fichier_nom'],
        data_origin='SYNTHETIC_ONLY', transport_mode=transport,
        provider_execution_attested=attested,
        admission_scope='LOCAL_TEST_ADMISSION' if transport == 'INJECTED_LOCAL_ONLY'
        else 'GENERIC_PRODUCER_ADMITTED')
    specification['policy_evidence_sha256'] = hashlib.sha256(json.dumps(
        specification, ensure_ascii=False, sort_keys=True).encode()).hexdigest().upper()
    db.tables['generic_producer_policies_v3'] = [dict(id=policy,
        specification=specification, contract_binding=contract,
        contract_binding_sha256=GENERIC_ADMISSION_CONTRACT_SHA256, enabled=False)]
    db.tables['generic_execution_admissions_v3'] = [dict(bindings,
        policy_id=policy, bindings=bindings, contract_binding=contract,
        source_facts=source_facts.model_dump(mode='json'), projection_text=projection_text,
        filename=db.tables['analyses'][0]['fichier_nom'], state='COMPLETE',
        claim_id='91000000-0000-0000-0000-000000000001',
        claimed_at='2026-09-29T10:00:00+00:00', terminal_at='2026-09-29T10:00:02+00:00')]
    receipt = dict(schema_version='governed-generic-producer-receipt-3',
        evidence_status='ADMITTED_EXECUTION', bindings=bindings, contract_binding=contract,
        contract_binding_sha256=GENERIC_ADMISSION_CONTRACT_SHA256,
        request_sha256=bindings['producer_input_sha256'], response_sha256='D' * 64,
        projection_sha256=bindings['producer_input_sha256'], envelope_sha256=envelope_sha,
        provider_policy_evidence_sha256=specification['policy_evidence_sha256'])
    db.tables['generic_execution_receipts_v3'] = [dict(execution_id=execution_id,
        analysis_id=ANALYSIS, receipt=receipt, created_at='2026-09-29T10:00:01+00:00')]
    return bindings


def extract(format, content):
    if format == 'xlsx':
        wb = load_workbook(BytesIO(content))
        return '\n'.join(str(value) for ws in wb for row in ws.iter_rows(values_only=True) for value in row if value is not None)
    if format == 'pdf':
        return '\n'.join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
    return '\n'.join(shape.text for slide in Presentation(BytesIO(content)).slides
                     for shape in slide.shapes if shape.has_text_frame)


@pytest.mark.parametrize('format', ['xlsx', 'pdf', 'pptx'])
def test_owned_receipt_reaches_all_terminal_exports(stored, format):
    db, execution = stored
    before = copy.deepcopy(db.tables)
    text = extract(format, export_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A, format=format))
    assert ANALYSIS in text and str(execution.provenance.execution_id) in text
    assert execution.provenance.raw_source_sha256 in text
    assert execution.provenance.envelope_sha256 in text
    assert 'Fournisseur simule local' in text and 'Recu durable verifie' in text
    assert 'UNKNOWN' in text and 'Comparabilite financiere non etablie' in text
    assert db.tables == before


@pytest.mark.parametrize('format', ['xlsx', 'pdf', 'pptx'])
def test_v40_owned_receipt_reaches_all_terminal_exports(stored, format):
    db, execution = stored
    bindings = as_v40(db, execution)
    before = copy.deepcopy(db.tables)
    output = read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)
    assert output['execution_provenance']['receipt_version'] == 'V40'
    assert output['execution_provenance']['receipt']['producer_id'] == bindings['producer_id']
    text = extract(format, export_owned_output(db, analysis_id=ANALYSIS,
                                               company_id=COMPANY_A, format=format))
    for expected in ('V40 / governed-execution-receipt-2', bindings['producer_id'],
                     bindings['producer_version'], bindings['task_id'],
                     bindings['raw_source_sha256'], bindings['source_representation_sha256'],
                     bindings['producer_input_sha256'], 'producteur generique non admis'):
        assert expected in text
    assert db.tables == before


def test_v40_receipt_selects_its_exact_engagement_not_an_entity_default(stored):
    db, execution = stored
    as_v40(db, execution)
    db.tables['engagements'].append({
        'id': '40000000-0000-0000-0000-000000000002', 'entity_id': ENTITY_A,
    })
    result = read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)
    assert result['execution_provenance']['receipt_version'] == 'V40'


@pytest.mark.parametrize('format', ['xlsx', 'pdf', 'pptx'])
def test_v41_injected_receipt_is_versioned_in_output_without_openai_attestation(stored, format):
    db, execution = stored
    bindings = as_v41(db, execution)
    before = copy.deepcopy(db.tables)
    # A newly constructed reader receives only persisted rows.  This prevents
    # process-local orchestration state from satisfying the reread contract.
    independent_db = _db()
    independent_db.tables = copy.deepcopy(db.tables)
    output = read_owned_output(
        independent_db, analysis_id=ANALYSIS, company_id=COMPANY_A
    )
    receipt = output['execution_provenance']['receipt']
    assert output['execution_provenance']['receipt_version'] == 'V41'
    assert receipt['transport'] == 'INJECTED_LOCAL_ONLY'
    assert receipt['provider_execution_attested'] is False
    text = extract(format, export_owned_output(
        independent_db, analysis_id=ANALYSIS, company_id=COMPANY_A, format=format))
    for expected in ('V41 / governed-generic-producer-receipt-3', PRODUCER_ID,
                     bindings['producer_input_sha256'], 'Reponse injectee locale',
                     'aucune execution OpenAI attestee'):
        assert expected in text
    assert db.tables == before
    assert independent_db.tables == before


def test_v41_declared_openai_transport_without_attestation_is_not_promoted(stored):
    db, execution = stored
    as_v41(db, execution, transport='OPENAI_RESPONSES', attested=False)
    rendered = extract('pdf', export_owned_output(
        db, analysis_id=ANALYSIS, company_id=COMPANY_A, format='pdf'))
    assert 'execution fournisseur non attestee' in rendered
    assert 'execution fournisseur attestee par le backend' not in rendered


@pytest.mark.parametrize('fault', [
    'dual_v40', 'unknown_contract', 'scope', 'request', 'response_claim',
    'source', 'projection', 'incomplete', 'missing_policy',
])
def test_v41_incomplete_substituted_or_ambiguous_evidence_refuses(stored, fault):
    db, execution = stored
    as_v41(db, execution)
    if fault == 'dual_v40':
        as_v40(db, execution)
        # Restore a minimal V41 marker so the cross-version ambiguity is observed first.
        as_v41(db, execution)
        db.tables['execution_receipts_v2'] = [dict(execution_id='x', analysis_id=ANALYSIS,
                                                   receipt={}, created_at='x')]
    elif fault == 'unknown_contract':
        db.tables['generic_execution_receipts_v3'][0]['receipt']['contract_binding_sha256'] = 'A' * 64
    elif fault == 'scope':
        db.tables['generic_execution_admissions_v3'][0]['company_id'] = COMPANY_B
    elif fault == 'request':
        db.tables['generic_execution_receipts_v3'][0]['receipt']['request_sha256'] = 'B' * 64
    elif fault == 'response_claim':
        db.tables['generic_producer_policies_v3'][0]['specification']['provider_execution_attested'] = True
    elif fault == 'source':
        db.tables['generic_execution_admissions_v3'][0]['source_facts']['status'] = 'CONTRADICTION'
    elif fault == 'projection':
        db.tables['generic_execution_admissions_v3'][0]['projection_text'] += ' '
    elif fault == 'incomplete':
        db.tables['generic_execution_admissions_v3'][0]['state'] = 'CLAIMED'
    elif fault == 'missing_policy':
        db.tables['generic_producer_policies_v3'] = []
    with pytest.raises(GovernedReadRefused, match='^UNAVAILABLE$'):
        read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


@pytest.mark.parametrize('format', ['xlsx', 'pdf', 'pptx'])
def test_legacy_absence_never_becomes_synthetic_attestation(stored, format):
    db, _ = stored
    db.tables['governed_execution_receipts'] = []
    text = extract(format, export_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A, format=format))
    assert 'Origine non attestee' in text
    assert 'Aucun recu durable' in text
    assert 'Fournisseur simule local' not in text
    assert 'Donnees synthetiques' not in text
    assert read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)['execution_provenance'] == dict(status='UNATTESTED', receipt=None)


@pytest.mark.parametrize('table', ['governed_execution_receipts', 'decision_feedback'])
def test_outage_refuses_instead_of_missing_claim(stored, monkeypatch, table):
    db, _ = stored
    original = db.from_
    def query(name):
        if name == table: raise RuntimeError('sensitive')
        return original(name)
    monkeypatch.setattr(db, 'from_', query)
    with pytest.raises(GovernedReadRefused, match='^UNAVAILABLE$'):
        export_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A, format='pdf')


@pytest.mark.parametrize('table', [
    'execution_receipts_v2', 'execution_admissions_v2', 'producer_policies_v2',
])
def test_v40_registry_outage_refuses_without_v39_or_legacy_fallback(stored, monkeypatch, table):
    db, execution = stored
    as_v40(db, execution)
    original = db.from_
    def query(name):
        if name == table:
            raise RuntimeError('sensitive')
        return original(name)
    monkeypatch.setattr(db, 'from_', query)
    with pytest.raises(GovernedReadRefused, match='^UNAVAILABLE$'):
        read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


@pytest.mark.parametrize('field', ['analysis_id', 'entity_id', 'envelope_sha256', 'raw_source_sha256', 'provider_mode'])
def test_forged_receipt_even_rehashed_refused(stored, field):
    db, _ = stored
    receipt = db.tables['governed_execution_receipts'][0]
    receipt['payload'][field] = 'forged'
    receipt['sha256'] = _digest(receipt['payload'])
    with pytest.raises(GovernedReadRefused, match='UNAVAILABLE'):
        read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


def test_foreign_scope_never_reads_receipt(stored):
    db, _ = stored
    db.log.clear()
    with pytest.raises(GovernedReadRefused, match='NOT_FOUND'):
        read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_B)
    assert not any(x[0] == 'governed_execution_receipts' for x in db.log)


@pytest.mark.parametrize('fault', [
    'dual_receipt', 'unknown_receipt_version', 'receipt_scope', 'request_scope', 'admission_scope',
    'missing_admission', 'missing_policy', 'policy_contract', 'policy_source',
    'input_mutation', 'candidate_binding', 'envelope_digest', 'incomplete',
])
def test_v40_incomplete_substituted_or_unknown_evidence_refuses_without_fallback(stored, fault):
    db, execution = stored
    as_v40(db, execution)
    if fault == 'dual_receipt':
        payload = execution.provenance.model_dump(mode='json') | dict(
            analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A)
        db.tables['governed_execution_receipts'] = [dict(payload=payload, sha256=_digest(payload),
            analysis_id=ANALYSIS, company_id=COMPANY_A, entity_id=ENTITY_A, engagement_id=ENGAGEMENT_A)]
    elif fault == 'unknown_receipt_version':
        db.tables['execution_receipts_v2'][0]['receipt']['schema_version'] = 'future'
    elif fault == 'receipt_scope':
        db.tables['execution_receipts_v2'][0]['receipt']['candidate']['bindings']['analysis_id'] = '10000000-0000-0000-0000-000000000002'
    elif fault == 'request_scope':
        db.tables['execution_admissions_v2'][0]['request_id'] = '50000000-0000-0000-0000-000000000002'
    elif fault == 'admission_scope':
        db.tables['execution_admissions_v2'][0]['company_id'] = COMPANY_B
    elif fault == 'missing_admission':
        db.tables['execution_admissions_v2'] = []
    elif fault == 'missing_policy':
        db.tables['producer_policies_v2'] = []
    elif fault == 'policy_contract':
        db.tables['producer_policies_v2'][0]['contract_sha256'] = 'C' * 64
    elif fault == 'policy_source':
        db.tables['producer_policies_v2'][0]['specification']['source_sha256'] = 'C' * 64
    elif fault == 'input_mutation':
        value = json.loads(db.tables['execution_admissions_v2'][0]['input_text'])
        value['status'] = 'CONTRADICTION'
        db.tables['execution_admissions_v2'][0]['input_text'] = json.dumps(value)
    elif fault == 'candidate_binding':
        db.tables['execution_receipts_v2'][0]['receipt']['candidate']['bindings']['task_version'] = 'task-v2'
    elif fault == 'envelope_digest':
        db.tables['execution_receipts_v2'][0]['receipt']['candidate']['envelope_sha256'] = 'C' * 64
    elif fault == 'incomplete':
        db.tables['execution_admissions_v2'][0]['state'] = 'CLAIMED'
    with pytest.raises(GovernedReadRefused, match='^UNAVAILABLE$'):
        read_owned_output(db, analysis_id=ANALYSIS, company_id=COMPANY_A)


def app_for(db, *, company=COMPANY_A, admitted=True):
    def admission():
        if not admitted: raise HTTPException(403, 'Admission closed')
    app = FastAPI()
    app.include_router(build_governed_output_router(authenticated_company=lambda: company,
        require_admission=admission, database=lambda: db))
    return TestClient(app)


def test_unmounted_transport_contract_with_mock_auth(stored):
    db, execution = stored
    before = copy.deepcopy(db.tables)
    client = app_for(db)
    url = '/api/governed/analyses/' + ANALYSIS
    result = client.get(url + '?company_id=' + COMPANY_B)
    assert result.status_code == 200
    assert result.json()['execution_provenance']['receipt']['execution_id'] == str(execution.provenance.execution_id)
    for format in ('xlsx','pdf','pptx'):
        response = client.get(url + '/export.' + format)
        assert response.status_code == 200
        assert str(execution.provenance.execution_id) in extract(format, response.content)
    assert app_for(db,company=COMPANY_B).get(url+'?company_id='+COMPANY_A).status_code == 404
    assert app_for(db,admitted=False).get(url).status_code == 403
    assert client.post(url).status_code == 405
    assert db.tables == before


def test_new_shared_modules_do_not_import_sandbox():
    import ast
    for name in ('governed_output','governed_export_rendering','temporal_export'):
        tree = ast.parse(Path('services',name+'.py').read_text(encoding='utf-8'))
        assert not any(isinstance(node,ast.ImportFrom) and (node.module or '').startswith('sandbox') for node in ast.walk(tree))
