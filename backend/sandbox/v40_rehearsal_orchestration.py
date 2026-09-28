"""Bounded V40 rehearsal core; no CLI, credential loading or schema mutation.

Uses the existing authenticated composer and durable adapter. Runtime transport,
owner SQL coordination and process launch are supplied by the pinned launcher,
never by an HTTP caller. Until whole-run tests pass this is NOT a released runner.
"""
import copy
import json
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

from sandbox.preflight_v40_rehearsal import FIXTURE, RAW_SHA, EXISTING, digest, inspect
from sandbox.heterogeneous_workbooks import _mock_response
from services.governed_analysis_persistence import _digest, _binding
from services.governed_producer_admission import LocalSyntheticProfile, LocalProducerAdmissionPreparation, DURABLE_CONTRACT
from services.durable_producer_admission import DurableProducerAdmission, DurableAdmissionRefused
from services.v1_analysis_contract import GovernedAnalysisEnvelope, UnderstandingResult, parse_openai_response, to_analysis_result


def require(value):
    if not value:
        raise ValueError('V40_ORCHESTRATION_REFUSED')


def profile_for(scope):
    return LocalSyntheticProfile(**{k:scope[k] for k in ('company_id','entity_id','engagement_id')},
        producer_id='v40-rehearsal-local-test-only', producer_version='version-1',
        task_id='v40-rehearsal-synthetic-analysis', task_version='version-1',
        source_sha256=RAW_SHA, filename=FIXTURE.name)


class Query:
    def __init__(self, db, table):
        self.db,self.table,self.filters,self.maximum=db,table,{},1000
    def select(self, columns):
        return self
    def eq(self, field, value):
        require(field in {'id','analysis_id','company_id','entity_id','engagement_id'})
        self.filters[field]=str(value)
        return self
    def limit(self, count):
        require(type(count) is int and 0<count<=1000)
        self.maximum=count
        return self
    def execute(self):
        rows=self.db.reader.rows(self.table)
        return SimpleNamespace(data=[r for r in rows if all(r.get(k)==v for k,v in self.filters.items())][:self.maximum])


class Backend:
    """Minimal Supabase-shaped facade, no unrestricted mutation or Auth login."""
    def __init__(self, reader, transport, session, profile, policy_id, *, identity_source=None):
        self.reader,self.transport,self.session=reader,transport,session
        self.policy_id=policy_id
        self.preparation=LocalProducerAdmissionPreparation(self,profile=profile,ttl_seconds=300,contract_policy=DURABLE_CONTRACT,identity_source=identity_source)
        self.service=DurableProducerAdmission(self,preparation=self.preparation,policy_id=policy_id)
        self.auth=SimpleNamespace(get_user=self.get_user)
        self.slot=None;self.last=None;self.last_parameters=None

    @property
    def authorization(self):
        return 'Bearer '+self.session.access_token

    def get_user(self, token):
        require(token==self.session.access_token)
        return SimpleNamespace(user=SimpleNamespace(id=self.transport.verify_actor(self.session)))

    def from_(self, table):
        return Query(self,table)

    def arm(self, slot):
        require(self.slot is None)
        self.slot=slot;self.last=None;self.last_parameters=None

    def rpc(self, name, params):
        def execute():
            require(self.slot is not None)
            slot=self.slot; self.slot=None
            payload=copy.deepcopy(params)
            if slot=='ROLLBACK_COMPLETE':
                require(name=='complete_execution_v2')
                # Authorized late-failure fixture only: unchanged V27 CHECK.
                payload['p_envelope']['binding_sha256']='INVALID'
            self.last_parameters=payload
            self.last=self.transport.rpc_once(slot,name=name,payload=payload,session=self.session)
            return SimpleNamespace(data=self.last)
        return SimpleNamespace(execute=execute)

    def call(self, slot, name, params):
        self.arm(slot)
        return self.rpc(name,params).execute().data


def mock_envelope(claimed):
    require(sha256(FIXTURE.read_bytes()).hexdigest().upper()==RAW_SHA)
    b=claimed.reservation.bindings
    require(b.raw_source_sha256==RAW_SHA and b.producer_id=='v40-rehearsal-local-test-only')
    understanding=UnderstandingResult.model_validate_json(claimed.input_text)
    require(sha256(claimed.input_text.encode()).hexdigest().upper()==b.producer_input_sha256)
    nonce=b.request_id.hex.upper()
    # Existing deterministic fixture producer, with the admitted request nonce.
    # No provider request is built and no V39 receipt is manufactured/relabelled.
    response=_mock_response(understanding,nonce)
    return to_analysis_result(parse_openai_response(response,understanding,nonce),understanding)


def reserve(db, prepared, label):
    db.arm(label+'_RESERVE')
    return db.service.reserve(prepared,authorization=db.authorization,raw=FIXTURE.read_bytes())


def claim(db, reservation, slot):
    db.arm(slot)
    try:
        result=db.service.claim(reservation,authorization=db.authorization)
        return {'status':'CLAIMED','claimed':result}
    except DurableAdmissionRefused:
        require(db.last=={'status':'SQL_REFUSED','sqlstate':'P0001'})
        return {'status':'EXPECTED_CLAIM_REFUSAL'}


def complete(db, claimed, slot):
    db.arm(slot)
    try:
        result=db.service.complete(claimed,authorization=db.authorization,envelope=mock_envelope(claimed))
        require(slot=='POSITIVE_COMPLETE' and result['status']=='LOCAL_SYNTHETIC_PERSISTED')
    except DurableAdmissionRefused:
        require(slot=='ROLLBACK_COMPLETE' and db.last=={'status':'REFUSED','automatic_retry_permitted':False})
    return {'status':db.last['status'],'parameters':db.last_parameters}


def verify_state(reader, before, manifest, states, *, positive=None, enabled=True):
    """Exact registry deltas plus preserved baseline; absence is part of proof."""
    policies=reader.rows('producer_policies_v2')
    require(len(policies)==1)
    p=policies[0]
    require(p['id']==manifest['policy_id'] and p['specification']==manifest['profile']
            and p['contract_sha256']==manifest['contract_sha256'] and p['enabled'] is enabled
            and p['origin']=='SYNTHETIC' and p['egress']=='DENY'
            and p['contract_version']=='local-synthetic-durable-admission-2')
    admissions=reader.rows('execution_admissions_v2')
    require(len(admissions)==len(states) and len(admissions)<=3)
    by_id={r['execution_id']:r for r in admissions}
    require(len(by_id)==len(admissions))
    for label,expected in states.items():
        b=manifest['cases'][label]
        row=by_id.get(b['execution_id'])
        require(row is not None and row['state']==expected and row['bindings']==b
                and row['policy_id']==manifest['policy_id'] and row['filename']==FIXTURE.name)
        require(all(row[k]==b[k] for k in ('actor_id','company_id','entity_id','engagement_id','analysis_id','request_id')))
        require(sha256(row['input_text'].encode()).hexdigest().upper()==b['producer_input_sha256'])
        if expected in ('CLAIMED','COMPLETE','REFUSED','CLOSED'):
            require(row['claim_id'] is not None and row['claimed_at'] is not None)
        if expected in ('COMPLETE','REFUSED','CLOSED'):
            require(row['terminal_at'] is not None)
    receipts=reader.rows('execution_receipts_v2')
    require(len(receipts)==(1 if positive else 0))
    for table in EXISTING:
        rows=reader.rows(table)
        if positive and table in ('analyses','governed_analysis_envelopes'):
            key='id' if table=='analyses' else 'analysis_id'
            added=[r for r in rows if r[key]==positive]
            require(len(added)==1)
            rows=[r for r in rows if r[key]!=positive]
        require({'count':len(rows),'sha256':digest(sorted(rows,key=digest))}==before['baseline'][table])
    if positive:
        b=manifest['cases']['POSITIVE'];require(positive==b['analysis_id'])
        a=by_id[b['execution_id']];receipt=receipts[0]
        envelope=next(r for r in reader.rows('governed_analysis_envelopes') if r['analysis_id']==positive)
        analysis=next(r for r in reader.rows('analyses') if r['id']==positive)
        r=receipt['receipt'];candidate=r['candidate']
        require(receipt['execution_id']==b['execution_id'] and receipt['analysis_id']==positive)
        require(r['schema_version']=='governed-execution-receipt-2' and r['evidence_scope']=='LOCAL_SYNTHETIC_ONLY'
                and r['egress']=='DENY' and r['policy_id']==manifest['policy_id']
                and r['composition_sha256']==a['composition_sha256'] and candidate['bindings']==b
                and r['claimed_at']==a['claimed_at'] and r['issued_at']==a['issued_at'])
        require(candidate['schema_version']=='producer-execution-candidate-2' and candidate['evidence_status']=='UNADMITTED_CANDIDATE')
        require(candidate['envelope_sha256']==envelope['envelope_sha256']==_digest(envelope['envelope_json']))
        require(envelope['envelope_json']['source_facts']==json.loads(a['input_text']))
        require(envelope['envelope_json']['governed_analysis']['invocation_nonce']==b['request_id'].replace('-','').upper())
        require(envelope['binding_sha256']==_binding(analysis_id=positive,company_id=b['company_id'],entity_id=b['entity_id'],
            engagement_id=b['engagement_id'],envelope_sha256=envelope['envelope_sha256'],source_sha256=b['source_representation_sha256']))
        require(all(envelope[k]==b[k] for k in ('company_id','entity_id','engagement_id')))
        require(analysis['company_id']==b['company_id'] and analysis['entity_id']==b['entity_id']
                and analysis['source_data_hash'].upper()==RAW_SHA and analysis['status']=='completed')
        expected_result=GovernedAnalysisEnvelope.model_validate(envelope['envelope_json']).analysis_result.model_dump(mode='json')
        expected_result['id']=positive
        require(analysis['analyse_json']==expected_result)
    return {'status':'EXACT_STATE_VERIFIED','durable_rows':1+len(admissions)+(3 if positive else 0)}


def run_protocol(db, before, *, publish, owner, workers):
    """Called only after fresh catalog gate + one budgeted login. No retries.

    owner receives exact manifest and action; workers must use independent
    processes and the SAME memory session. Callbacks are trusted launcher code.
    """
    require(inspect(db.reader)==before)
    require(db.transport.verify_actor(db.session)==before['scope']['actor_id'])
    profile=profile_for(before['scope'])
    require(profile==db.preparation._profile)
    prepared={label:db.preparation.prepare(authorization=db.authorization,
        entity_id=before['scope']['entity_id'],engagement_id=before['scope']['engagement_id'],
        raw=FIXTURE.read_bytes(),filename=FIXTURE.name) for label in ('ROLLBACK','ABANDON','POSITIVE')}
    manifest={'policy_id':db.policy_id,'profile':profile.model_dump(mode='json'),
              'contract_sha256':_digest({'profile':profile.model_dump(mode='json'),'policy':DURABLE_CONTRACT}),
              'cases':{k:p.bindings.model_dump(mode='json') for k,p in prepared.items()}}
    require(len({b['analysis_id'] for b in manifest['cases'].values()})==3)
    publish(manifest)  # Exclusive immutable file, never credentials/capabilities.
    owner('POLICY_INSERT',manifest)
    states={};verify_state(db.reader,before,manifest,states)
    base=dict(p_policy=db.policy_id,p_bindings=manifest['cases']['ROLLBACK'],
              p_input=prepared['ROLLBACK'].input_json,p_filename=FIXTURE.name,p_ttl=300)
    for slot,field,value in [('INVALID_SCOPE','company_id','00000000-0000-0000-0000-000000000000'),
                              ('INVALID_SOURCE','raw_source_sha256','0'*64)]:
        params=copy.deepcopy(base);params['p_bindings'][field]=value
        require(db.call(slot,'reserve_execution_v2',params)=={'status':'SQL_REFUSED','sqlstate':'P0001'})
        verify_state(db.reader,before,manifest,states)
    rollback=reserve(db,prepared['ROLLBACK'],'ROLLBACK')
    states['ROLLBACK']='RESERVED';verify_state(db.reader,before,manifest,states)
    claimed=claim(db,rollback,'ROLLBACK_CLAIM');require(claimed['status']=='CLAIMED')
    require(complete(db,claimed['claimed'],'ROLLBACK_COMPLETE')['status']=='REFUSED')
    states['ROLLBACK']='REFUSED';verify_state(db.reader,before,manifest,states)
    require(claim(db,rollback,'ROLLBACK_RECLAIM')['status']=='EXPECTED_CLAIM_REFUSAL')
    verify_state(db.reader,before,manifest,states)
    abandoned=reserve(db,prepared['ABANDON'],'ABANDON')
    first=workers('ABANDON_CLAIM',abandoned);require(first['status']=='CLAIMED')
    states['ABANDON']='CLAIMED';verify_state(db.reader,before,manifest,states)
    second=workers('ABANDON_RECLAIM',abandoned);require(second['status']=='EXPECTED_CLAIM_REFUSAL')
    require(first['pid']!=second['pid'])
    verify_state(db.reader,before,manifest,states)
    require(db.call('ABANDON_CLOSE','close_execution_v2',{'p_execution':str(abandoned.bindings.execution_id),
            'p_actor':db.session.actor_id})=={'status':'CLOSED'})
    states['ABANDON']='CLOSED';verify_state(db.reader,before,manifest,states)
    positive=reserve(db,prepared['POSITIVE'],'POSITIVE')
    result=workers('POSITIVE_RACE',positive)
    require(result['status']=='COMPLETE' and result['claim_refusals']==1 and len(set(result['pids']))==2)
    states['POSITIVE']='COMPLETE';pid=manifest['cases']['POSITIVE']['analysis_id']
    verify_state(db.reader,before,manifest,states,positive=pid)
    recovery=workers('RECOVER',{'before':before,'manifest':manifest,'states':states,'positive':pid})
    require(recovery['status']=='EXACT_STATE_VERIFIED' and recovery['durable_rows']==7
            and recovery['pid'] not in result['pids'])
    require(claim(db,positive,'POSITIVE_RECLAIM')['status']=='EXPECTED_CLAIM_REFUSAL')
    require(db.call('POSITIVE_RECOMPLETE','complete_execution_v2',result['parameters'])=={'status':'SQL_REFUSED','sqlstate':'P0001'})
    verify_state(db.reader,before,manifest,states,positive=pid)
    owner('POLICY_DISABLE',manifest)
    verify_state(db.reader,before,manifest,states,positive=pid,enabled=False)
    return {'status':'BOUNDED_V40_REHEARSAL_PASS','new_durable_rows':7,
            'admission_states':states,'independent_recovery':True,'old_rows_unchanged':True,
            'external_provider_used':False,'real_data_used':False,'generic_producer_admitted':False,'b1_global_proven':False}
