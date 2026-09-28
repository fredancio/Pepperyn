"""Local-only falsification of frozen pre-Auth to composed identity binding."""
import copy
from dataclasses import FrozenInstanceError
from uuid import uuid4
import pytest

from sandbox.v40_successor_identities import IdentityPlan, IdentityConsumption
from sandbox.v40_successor_history import assert_fresh_identities
from test_governed_producer_admission import system, prepare, unchanged
from services.governed_producer_admission import LocalProducerAdmissionPreparation,AdmissionRefused


def test_plan_frozen_and_consumed_once():
    plan=IdentityPlan.create();hash_=plan.commitment();take=IdentityConsumption(plan,hash_)
    with pytest.raises(FrozenInstanceError):plan.policy_id=uuid4()
    for expected in plan.triples:assert take()==expected
    with pytest.raises(ValueError):take()
    m=plan.manifest();m['cases']['POSITIVE']['analysis_id']=str(uuid4())
    assert plan.commitment()==hash_
    with pytest.raises(ValueError):plan.verify(m,hash_)


@pytest.mark.parametrize('field',['analysis_id','request_id','execution_id','policy_id','label','commitment'])
def test_substitution_refused(field):
    plan=IdentityPlan.create();m=plan.manifest();h=plan.commitment()
    if field=='policy_id':m[field]=str(uuid4())
    elif field=='label':m['cases']['POSITIVE'],m['cases']['ROLLBACK']=m['cases']['ROLLBACK'],m['cases']['POSITIVE']
    elif field=='commitment':h='0'*64
    else:m['cases']['POSITIVE'][field]=str(uuid4())
    with pytest.raises(ValueError):plan.verify(m,h)


def test_internal_mutation_still_detected():
    plan=IdentityPlan.create();take=IdentityConsumption(plan,plan.commitment())
    object.__setattr__(plan,'policy_id',uuid4())
    with pytest.raises(ValueError):take()


def test_authenticated_composer_uses_exact_prechecked_ids_no_uuid_generation(system,monkeypatch):
    import services.governed_producer_admission as module
    db,profile,_=system
    plan=IdentityPlan.create();m=plan.manifest();h=plan.commitment()
    service=LocalProducerAdmissionPreparation(db,profile=profile,identity_source=IdentityConsumption(plan,h))
    def forbidden():raise AssertionError('POSTCHECK_REGENERATION_FORBIDDEN')
    monkeypatch.setattr(module,'uuid4',forbidden)
    before=copy.deepcopy(db.tables)
    composed=dict(policy_id=m['policy_id'],cases={})
    for label in ('ROLLBACK','ABANDON','POSITIVE'):
        p=prepare(service)
        composed['cases'][label]=p.bindings.model_dump(mode='json')
    plan.verify(composed,h)
    with pytest.raises(AdmissionRefused):prepare(service)
    unchanged(db,before)


def test_allocation_is_not_authentication_or_caller_authority(system):
    db,profile,_=system;plan=IdentityPlan.create()
    take=IdentityConsumption(plan,plan.commitment())
    service=LocalProducerAdmissionPreparation(db,profile=profile,identity_source=take)
    before=copy.deepcopy(db.tables)
    with pytest.raises(AdmissionRefused):prepare(service,authorization='Bearer foreign')
    with pytest.raises(TypeError):prepare(service,analysis_id=str(uuid4()))
    assert take._next==0
    unchanged(db,before)
