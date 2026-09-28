"""Adapter falsification with no network/database writes; SQL proof is separate."""
import copy
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.durable_producer_admission import DurableAdmissionRefused, DurableProducerAdmission
from services.governed_producer_admission import LocalProducerAdmissionPreparation, DURABLE_CONTRACT
from services.v1_analysis_contract import GovernedAnalysisEnvelope
from test_governed_producer_admission import system, prepare, RAW
from test_execution_provenance import execution


@pytest.fixture
def adapter(system):
    db, profile, _ = system
    preparation=LocalProducerAdmissionPreparation(db,profile=profile,contract_policy=DURABLE_CONTRACT)
    prepared=prepare(preparation)
    calls=[]
    mode={'fail':None,'tamper':None}
    def rpc(name,params):
        calls.append((name,copy.deepcopy(params)))
        if mode['fail']==name: raise RuntimeError('DO_NOT_DISCLOSE')
        if name=='reserve_execution_v2':
            result=dict(status='RESERVED',execution_id=str(prepared.bindings.execution_id),composition_sha256='A'*64)
        elif name=='claim_execution_v2':
            result=dict(status='CLAIMED',execution_id=str(prepared.bindings.execution_id),
                composition_sha256='A'*64,bindings=prepared.bindings.model_dump(mode='json'),
                input_text=prepared.input_json,claim_id=str(uuid4()),claimed_at=datetime.now(timezone.utc).isoformat())
        else: result=dict(status='COMPLETE',analysis_id=str(prepared.bindings.analysis_id))
        if mode['tamper']: result.update(mode['tamper'])
        return SimpleNamespace(execute=lambda:SimpleNamespace(data=result))
    db.rpc=rpc
    service=DurableProducerAdmission(db,preparation=preparation,policy_id=uuid4())
    return db,service,prepared,calls,mode


def test_preparation_only_contract_cannot_be_promoted(system):
    db,_,preparation=system
    with pytest.raises(DurableAdmissionRefused,match='DISTINCT_DURABLE_CONTRACT_REQUIRED'):
        DurableProducerAdmission(db,preparation=preparation,policy_id=uuid4())


@pytest.mark.parametrize('phase',['reserve_execution_v2','claim_execution_v2','complete_execution_v2'])
def test_uncertainty_no_retry_or_fallback(adapter,execution,phase):
    db,service,p,calls,mode=adapter
    before=copy.deepcopy(db.tables)
    mode['fail']=phase
    with pytest.raises(DurableAdmissionRefused) as error:
        r=service.reserve(p,authorization='Bearer owner',raw=RAW)
        c=service.claim(r,authorization='Bearer owner')
        envelope=execution.analysis.envelope.model_dump(mode='json')
        envelope['governed_analysis']['invocation_nonce']=p.bindings.request_id.hex.upper()
        service.complete(c,authorization='Bearer owner',envelope=GovernedAnalysisEnvelope.model_validate(envelope))
    assert 'DO_NOT_DISCLOSE' not in str(error.value)
    assert [n for n,_ in calls].count(phase)==1
    assert all(n.endswith('_v2') for n,_ in calls)
    assert db.tables==before


@pytest.mark.parametrize('tamper',[{'status':'UNKNOWN'},{'execution_id':str(uuid4())},
    {'bindings':{}},{'input_text':'{}'},{'composition_sha256':'0'*64},{'claimed_at':'2026-01-01'}])
def test_claim_ack_substitution_cannot_release_execution(adapter,tamper):
    db,service,p,calls,mode=adapter
    r=service.reserve(p,authorization='Bearer owner',raw=RAW)
    before=copy.deepcopy(db.tables)
    mode['tamper']=tamper
    with pytest.raises(DurableAdmissionRefused,match='DO_NOT_EXECUTE'):
        service.claim(r,authorization='Bearer owner')
    assert len(calls)==2 and db.tables==before


def test_foreign_actor_refused_before_claim_rpc(adapter):
    _,service,p,calls,_=adapter
    r=service.reserve(p,authorization='Bearer owner',raw=RAW)
    with pytest.raises(DurableAdmissionRefused): service.claim(r,authorization='Bearer foreign')
    assert len(calls)==1


def test_envelope_request_mismatch_no_completion_rpc(adapter,execution):
    db,service,p,calls,_=adapter
    r=service.reserve(p,authorization='Bearer owner',raw=RAW)
    c=service.claim(r,authorization='Bearer owner')
    before=copy.deepcopy(db.tables)
    with pytest.raises(DurableAdmissionRefused):
        service.complete(c,authorization='Bearer owner',envelope=execution.analysis.envelope)
    assert len(calls)==2 and db.tables==before


def test_legacy_taxonomy_does_not_erase_governed_semantics(adapter,execution):
    _,service,p,calls,_=adapter
    r=service.reserve(p,authorization='Bearer owner',raw=RAW)
    c=service.claim(r,authorization='Bearer owner')
    data=execution.analysis.envelope.model_dump(mode='json')
    data['governed_analysis']['invocation_nonce']=p.bindings.request_id.hex.upper()
    envelope=GovernedAnalysisEnvelope.model_validate(data)
    service.complete(c,authorization='Bearer owner',envelope=envelope)
    name,params=calls[-1]
    assert name=='complete_execution_v2'
    assert params['p_analysis']['type_document']=='AUTRE'
    expected=envelope.analysis_result.model_dump(mode='json')
    expected['id']=str(p.bindings.analysis_id)
    assert expected['type_document']=='FINANCIAL_WORKBOOK'
    assert params['p_analysis']['analyse_json']==expected
    assert params['p_envelope']['envelope_json']==data
