"""Generate the two authorized owner-only statements. Never execute SQL here."""
import json
from uuid import UUID

from sandbox.v40_rehearsal_orchestration import profile_for, require
from services.governed_analysis_persistence import _digest
from services.governed_producer_admission import DURABLE_CONTRACT


def literal(value):
    return "'"+str(value).replace("'","''")+"'"


def owner_sql(action, manifest):
    require(action in {'POLICY_INSERT','POLICY_DISABLE'})
    policy=str(UUID(manifest['policy_id']))
    profile=profile_for(manifest['profile']).model_dump(mode='json')
    require(profile==manifest['profile'])
    contract=_digest({'profile':profile,'policy':DURABLE_CONTRACT})
    require(contract==manifest['contract_sha256'])
    require(set(manifest['cases'])=={'ROLLBACK','ABANDON','POSITIVE'})
    for b in manifest['cases'].values():
        require(b['admission_contract_sha256']==contract)
        require(all(b[k]==profile[k] for k in ('company_id','entity_id','engagement_id','producer_id','producer_version','task_id','task_version')))
    spec=literal(json.dumps(profile,sort_keys=True,separators=(',',':')))+'::jsonb'
    check=f"id={literal(policy)}::uuid AND specification={spec} AND contract_sha256={literal(contract)} AND enabled AND origin='SYNTHETIC' AND egress='DENY'"
    if action=='POLICY_INSERT':
        guard="""IF EXISTS(SELECT FROM public.producer_policies_v2)
           OR EXISTS(SELECT FROM public.execution_admissions_v2)
           OR EXISTS(SELECT FROM public.execution_receipts_v2)
           THEN RAISE EXCEPTION 'V40 owner insertion precondition refused'; END IF;"""
        write=f"INSERT INTO public.producer_policies_v2(id,specification,contract_sha256,enabled) VALUES ({literal(policy)},{spec},{literal(contract)},true);"
    else:
        expected=','.join('('+literal(b['execution_id'])+'::uuid,'+literal({'ROLLBACK':'REFUSED','ABANDON':'CLOSED','POSITIVE':'COMPLETE'}[label])+')' for label,b in manifest['cases'].items())
        guard=f"""IF (SELECT count(*) FROM public.producer_policies_v2)<>1
           OR NOT EXISTS(SELECT FROM public.producer_policies_v2 WHERE {check})
           OR (SELECT count(*) FROM public.execution_admissions_v2)<>3
           OR (SELECT count(*) FROM public.execution_receipts_v2)<>1
           OR EXISTS(SELECT FROM (VALUES {expected}) e(id,state)
             LEFT JOIN public.execution_admissions_v2 a ON a.execution_id=e.id
             WHERE a.execution_id IS NULL OR a.state<>e.state OR a.policy_id<>{literal(policy)}::uuid)
           THEN RAISE EXCEPTION 'V40 owner disable precondition refused'; END IF;"""
        write=f"UPDATE public.producer_policies_v2 SET enabled=false WHERE {check};"
    return f"""-- Single owner action under the existing bounded V40 GO. No replay.
BEGIN;
LOCK TABLE public.producer_policies_v2, public.execution_admissions_v2, public.execution_receipts_v2 IN SHARE ROW EXCLUSIVE MODE;
DO $v40owner$ BEGIN
{guard}
{write}
END $v40owner$;
SELECT '{action}_ACK' AS status;
COMMIT;
"""
