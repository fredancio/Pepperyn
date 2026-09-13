"""Falsifications for authoritative V33-to-minimal-projection composition."""
from dataclasses import replace
import inspect
import json
from pathlib import Path
from services.governed_minimal_projection import (GovernedProjection, MinimalProjectionRefused, ReceiptedFinancialChangeFact, TASK, compose_financial_change_v1, verify_governed_projection)
from services.ownership_authority import (InMemoryOwnershipRepository, InMemoryScopedContextRepository, OwnershipAuthority, OwnershipRecord, ProtectedContextReader, ProtectedResource, ScopedContextRecord)
from services.pseudonymous_correspondence import CorrespondenceScope, GovernedCorrespondenceRegistry, PseudonymousReference
from tests.test_pseudonymous_correspondence import authorized_register

COMPANY="11111111-1111-4111-8111-111111111111"; ENTITY="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ENGAGEMENT="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"; ANALYSIS="10000000-0000-4000-8000-000000000001"; KEY=bytes(range(32))

class DurableRepository:
    def __init__(self): self.records={}; self.bindings=set()
    def find_by_fingerprint(self,s,c,f): return next((r for r in self.records.values() if r.scope==s and r.category==c and r.real_fingerprint==f),None)
    def find_by_pseudonym(self,s,p): return next((r for r in self.records.values() if r.scope==s and r.pseudonym==p),None)
    def find_by_id(self,s,i):
        r=self.records.get(i); return r if r and r.scope==s else None
    def insert(self,r): self.records[r.id]=r
    def bind_analysis(self,i,s,a): self.bindings.add((i,s.company_id,s.entity_id,a))
    def active_analysis_bindings(self,i,s): return ()
    def purge(self,i,s): raise AssertionError("not used")

def refuses(code,operation):
    try: operation()
    except MinimalProjectionRefused as exc:
        assert str(exc)==code; return
    raise AssertionError(f"expected {code}")

def paths(value,prefix=()):
    if isinstance(value,dict): return [p for k,v in value.items() for p in paths(v,prefix+(k,))]
    if isinstance(value,list): return [p for i,v in enumerate(value) for p in paths(v,prefix+(i,))]
    return [prefix]

def fixture():
    source={"metrics":[{"metric_code":"REVENUE","previous":"1000000","current":"1120000"},{"metric_code":"EBITDA","previous":"100000","current":"97000"}]}
    scope=CorrespondenceScope(COMPANY,ENTITY); registry=GovernedCorrespondenceRegistry(DurableRepository(),KEY)
    reference=authorized_register(registry,scope=scope,analysis_id=ANALYSIS,category="COUNTERPARTY",real_identity="V33 SYNTHETIC COUNTERPARTY")
    ownership=OwnershipAuthority(InMemoryOwnershipRepository([OwnershipRecord(ANALYSIS,COMPANY,ENTITY,ENGAGEMENT,COMPANY,ENTITY)]),projection_policy={ProtectedResource.ANALYSIS_RESULT:frozenset(paths(source))})
    principal=ownership._accept_authenticated_principal("principal",COMPANY)
    grant=ownership.resolve_and_mint_read_grant(principal=principal,analysis_id=ANALYSIS,request_id="request",resources=[ProtectedResource.ANALYSIS_RESULT])
    record=ScopedContextRecord(ProtectedResource.ANALYSIS_RESULT,COMPANY,ENTITY,ENGAGEMENT,ANALYSIS,source)
    whole=ProtectedContextReader(InMemoryScopedContextRepository([record])).read_receipted(grant,request_id="request",resource=ProtectedResource.ANALYSIS_RESULT)[0][1]
    receipts={p:ownership.project_read(whole,p) for p in paths(source)}
    facts=[ReceiptedFinancialChangeFact(row["metric_code"],receipts[("metrics",i,"metric_code")],row["previous"],receipts[("metrics",i,"previous")],row["current"],receipts[("metrics",i,"current")]) for i,row in enumerate(source["metrics"])]
    return registry,reference,scope,ownership,grant,facts

def sample():
    r,ref,s,o,g,f=fixture(); return compose_financial_change_v1(registry=r,correspondence_reference=ref,correspondence_scope=s,ownership_authority=o,read_grant=g,request_id="request",facts=f)

def test_authoritative_projection_is_minimal_coarsened_and_deterministic():
    a,b=sample(),sample(); assert a.payload==b.payload and a.payload_hash==b.payload_hash
    assert a.payload["metrics"]==[{"metric":"EBITDA","direction":"DOWN","change_band":"2_TO_5_PERCENT"},{"metric":"REVENUE","direction":"UP","change_band":"10_TO_20_PERCENT"}]

def test_projection_contains_no_exact_values_dates_or_context():
    value=json.dumps(sample().payload,sort_keys=True)
    assert all(x not in value for x in ("1000000","1120000","100000","97000","2026","Belgium","sector"))

def test_forged_but_plausible_pseudonym_is_rejected():
    r,ref,s,o,g,f=fixture(); forged=PseudonymousReference("COUNTERPARTY-AAAAAAAAAAAAAAAA",ref.handle)
    refuses("AUTHORITATIVE_COMPOSITION_REQUIRED",lambda:compose_financial_change_v1(registry=r,correspondence_reference=forged,correspondence_scope=s,ownership_authority=o,read_grant=g,request_id="request",facts=f))

def test_unreceipted_or_changed_values_and_metrics_are_rejected():
    for field,value in (("current_value","999999999"),("metric_code","CASH")):
        r,ref,s,o,g,f=fixture(); f[0]=replace(f[0],**{field:value})
        refuses("AUTHORITATIVE_COMPOSITION_REQUIRED",lambda r=r,ref=ref,s=s,o=o,g=g,f=f:compose_financial_change_v1(registry=r,correspondence_reference=ref,correspondence_scope=s,ownership_authority=o,read_grant=g,request_id="request",facts=f))

def test_foreign_v33_scope_fails_closed():
    r,ref,s,o,g,f=fixture(); foreign=CorrespondenceScope("22222222-2222-4222-8222-222222222222",ENTITY)
    refuses("AUTHORITATIVE_COMPOSITION_REQUIRED",lambda:compose_financial_change_v1(registry=r,correspondence_reference=ref,correspondence_scope=foreign,ownership_authority=o,read_grant=g,request_id="request",facts=f))

def test_legacy_unattested_v33_mapping_cannot_enter_projection():
    r,ref,s,o,g,f=fixture(); repository=r._repository
    record=next(iter(repository.records.values()))
    repository.records[record.id]=replace(record,registration_authority_sha256=None)
    refuses("AUTHORITATIVE_COMPOSITION_REQUIRED",lambda:compose_financial_change_v1(registry=r,correspondence_reference=ref,correspondence_scope=s,ownership_authority=o,read_grant=g,request_id="request",facts=f))

def test_provenance_and_ownership_survive_in_projection_receipt():
    line=sample().lineage; assert line is not None
    assert (line.company_id,line.entity_id,line.engagement_id,line.analysis_id,line.request_id)==(COMPANY,ENTITY,ENGAGEMENT,ANALYSIS,"request")
    assert line.correspondence_id and line.mapping_version==1 and len(line.source_receipt_ids)==6 and len(line.source_hashes)==6

def test_projection_source_receipts_are_single_use():
    r,ref,s,o,g,f=fixture(); kwargs=dict(registry=r,correspondence_reference=ref,correspondence_scope=s,ownership_authority=o,read_grant=g,request_id="request",facts=f)
    compose_financial_change_v1(**kwargs); refuses("AUTHORITATIVE_COMPOSITION_REQUIRED",lambda:compose_financial_change_v1(**kwargs))

def test_projection_receipt_is_exact_task_payload_and_identity_bound():
    p=sample(); verify_governed_projection(p,task=TASK,payload=p.payload,identity_state="PSEUDONYMOUS")
    p=sample(); refuses("PROJECTION_SCOPE_MISMATCH",lambda:verify_governed_projection(p,task="OTHER",payload=p.payload,identity_state="PSEUDONYMOUS"))
    p=sample(); refuses("PROJECTION_SCOPE_MISMATCH",lambda:verify_governed_projection(p,task=TASK,payload={**p.payload,"extra":"x"},identity_state="PSEUDONYMOUS"))
    p=sample(); refuses("PROJECTION_SCOPE_MISMATCH",lambda:verify_governed_projection(p,task=TASK,payload=p.payload,identity_state="NO_IDENTITY"))

def test_projection_cannot_be_forged_or_have_lineage_removed():
    p=sample(); refuses("PROJECTION_FORGED",lambda:GovernedProjection(p.task,p.policy_id,p.payload,p.payload_hash,p.identity_state,p.residual_risk,p.lineage,object()))
    forged=object.__new__(GovernedProjection)
    for k,v in p.__dict__.items(): object.__setattr__(forged,k,v)
    object.__setattr__(forged,"lineage",None)
    refuses("PROJECTION_FORGED_OR_REPLAYED",lambda:verify_governed_projection(forged,task=TASK,payload=p.payload,identity_state="PSEUDONYMOUS"))

def test_projection_contract_has_no_free_form_identity_or_context_input():
    assert tuple(inspect.signature(compose_financial_change_v1).parameters)==(
        "registry","correspondence_reference","correspondence_scope",
        "ownership_authority","read_grant","request_id","facts")

def test_egress_authority_refuses_missing_projection_before_transport():
    import services.llm_egress as e
    request=e._mint_synthetic_test_request(task=TASK,provider_payload=sample().payload); request=type(request)(**{**request.__dict__,"governed_projection":None})
    called=[]; original=e._dispatch_final_request; e._dispatch_final_request=lambda frozen:called.append(frozen)
    try:
        try:e.LlmEgressAuthority().dispatch(request)
        except e.EgressRefused as exc: assert exc.code is e.EgressRefusalCode.MINIMAL_PROJECTION_REQUIRED
        else:raise AssertionError("transport reached")
    finally:e._dispatch_final_request=original
    assert called==[]

def test_projection_check_precedes_transport_call():
    source=(Path(__file__).parents[1]/"services"/"llm_egress.py").read_text(encoding="utf-8")
    dispatch=source[source.index("    def dispatch("):source.index("\n\n_CLOSED_AUTHORITY")]
    assert dispatch.index("verify_governed_projection(")<dispatch.index("_dispatch_final_request(")
