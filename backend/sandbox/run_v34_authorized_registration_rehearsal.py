"""One bounded live rehearsal of ownership-authorized V34 registration.

The only admitted identity is read from the exact designated synthetic entity
and must equal the registered integration-test label. No provider is called and
no protected value, handle or credential is printed.
"""
from __future__ import annotations
import argparse
import json
import os
from supabase import create_client
from services.ownership_authority import (InMemoryOwnershipRepository,
    InMemoryScopedContextRepository, OwnershipAuthority, OwnershipRecord,
    ProtectedContextReader, ProtectedResource, ScopedContextRecord)
from services.pseudonymous_correspondence import (CorrespondenceScope,
    GovernedCorrespondenceRegistry, SupabaseCorrespondenceRepository,
    verify_projection_correspondence_binding)

ANALYSIS_ID="75132a71-c80c-4469-aba8-5171d947a9d0"
EXPECTED_SYNTHETIC_ENTITY="Optilux Synthetic Internal Pilot"
CATEGORY="ENTITY"

def emit(status,phase,**fields):
    print(json.dumps({"status":status,"phase":phase,"analysis_id":ANALYSIS_ID,
        "external_provider_used":False,"real_data_used":False,**fields}))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--phase",choices=("inspect","register","verify"),required=True)
    phase=parser.parse_args().phase; stage="environment"
    url=os.getenv("SUPABASE_URL",""); key=os.getenv("SUPABASE_SERVICE_KEY",""); company=os.getenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID","")
    if not url or not key or not company or not os.getenv("PEPPERYN_CORRESPONDENCE_KEY",""):
        emit("REFUSED",phase,stage=stage,code="V34_ENVIRONMENT_INCOMPLETE",write_performed=False); return 2
    try:
        db=create_client(url,key); stage="governed_scope"
        rows=(db.from_("governed_analysis_envelopes").select("analysis_id,company_id,entity_id,engagement_id")
            .eq("analysis_id",ANALYSIS_ID).eq("company_id",company).limit(2).execute()).data or []
        if len(rows)!=1: raise RuntimeError("V34_SCOPE_UNAVAILABLE")
        row=rows[0]; scope=CorrespondenceScope(row["company_id"],row["entity_id"])
        stage="synthetic_entity_source"
        entities=(db.from_("entities").select("id,company_id,name").eq("id",scope.entity_id)
            .eq("company_id",scope.company_id).limit(2).execute()).data or []
        if len(entities)!=1 or entities[0].get("name")!=EXPECTED_SYNTHETIC_ENTITY:
            raise RuntimeError("V34_SYNTHETIC_ENTITY_NOT_REGISTERED")
        if phase=="inspect": return inspect(db,scope)
        identity=entities[0]["name"]; request_id=f"v34-{ANALYSIS_ID}"
        stage="ownership_authority"
        authority=OwnershipAuthority(InMemoryOwnershipRepository([OwnershipRecord(
            ANALYSIS_ID,scope.company_id,scope.entity_id,row["engagement_id"],
            scope.company_id,scope.entity_id)]),projection_policy={
                ProtectedResource.ENTITY_CONTEXT:frozenset({("identity",)})})
        principal=authority._accept_authenticated_principal("v34-synthetic-rehearsal",scope.company_id)
        grant=authority.resolve_and_mint_read_grant(principal=principal,analysis_id=ANALYSIS_ID,
            request_id=request_id,resources=[ProtectedResource.ENTITY_CONTEXT])
        source={"identity":identity}; context=ScopedContextRecord(ProtectedResource.ENTITY_CONTEXT,
            scope.company_id,scope.entity_id,row["engagement_id"],ANALYSIS_ID,source)
        whole=ProtectedContextReader(InMemoryScopedContextRepository([context])).read_receipted(
            grant,request_id=request_id,resource=ProtectedResource.ENTITY_CONTEXT)[0][1]
        identity_receipt=authority.project_read(whole,("identity",))
        registry=GovernedCorrespondenceRegistry.from_environment(SupabaseCorrespondenceRepository(db))
        if phase=="register":
            stage="authorized_registration"
            authorization=authority.mint_correspondence_registration_authorization(grant=grant,
                request_id=request_id,category=CATEGORY,real_identity=identity,
                identity_receipt=identity_receipt)
            reference=registry.register(scope=scope,analysis_id=ANALYSIS_ID,category=CATEGORY,
                real_identity=identity,registration_request_id=request_id,
                registration_authorization=authorization)
            emit("PASS",phase,stage=stage,pseudonym=reference.pseudonym,
                write_performed=True,authorized_origin=True); return 0
        stage="durable_origin_verify"
        reference=registry.reference_existing(scope=scope,category=CATEGORY,real_identity=identity)
        binding=registry.authorize_projection_reference(reference,scope=scope)
        verify_projection_correspondence_binding(binding,company_id=scope.company_id,entity_id=scope.entity_id)
        emit("PASS",phase,stage=stage,pseudonym=binding.pseudonym,write_performed=False,
            authorized_origin=True,mapping_version=binding.mapping_version); return 0
    except Exception as exc:
        emit("REFUSED",phase,stage=stage,code="V34_REHEARSAL_FAILED",
            exception_type=type(exc).__name__,write_performed=False); return 2

def inspect(db,scope):
    rows=(db.from_("pseudonymous_correspondence").select(
        "id,registration_version,registration_request_sha256,registration_authority_sha256,registration_source_receipt_sha256")
        .eq("company_id",scope.company_id).eq("entity_id",scope.entity_id)
        .eq("category",CATEGORY).limit(3).execute()).data or []
    emit("INSPECTED","inspect",write_performed=False,mapping_count_bounded=len(rows),
        authorized_origin_count=sum(1 for row in rows if row.get("registration_version")=="ownership-v1"
            and all(row.get(k) for k in ("registration_request_sha256","registration_authority_sha256","registration_source_receipt_sha256"))))
    return 0

if __name__=="__main__": raise SystemExit(main())
