-- LOCAL PREPARATION ONLY. NOT AUTHORIZED FOR REMOTE APPLICATION.
-- Successor correction; original V41 migration and historical evidence unchanged.
-- Exactly two function bodies, same signatures/owners/ACLs/security boundary.
-- No policy, registry, result or producer activation.
BEGIN;
DO $guard$
BEGIN
  IF (SELECT upper(encode(sha256(convert_to(replace(prosrc,E'\r\n',E'\n'),'UTF8')),'hex'))
      FROM pg_proc WHERE oid=to_regprocedure('public.reserve_generic_execution_v3(uuid,jsonb,jsonb,jsonb,text,text,integer)'))
      IS DISTINCT FROM '9F66360C4E7320C9FD9C67AC079116AA6BA77396996588A7732280310D499A57'
     OR (SELECT upper(encode(sha256(convert_to(replace(prosrc,E'\r\n',E'\n'),'UTF8')),'hex'))
      FROM pg_proc WHERE oid=to_regprocedure('public.complete_generic_execution_v3(uuid,uuid,uuid,jsonb,jsonb,jsonb,text)'))
      IS DISTINCT FROM '6E4C051D172B001373EA63218FC5D80D2894AB87A7C4FB085B0508287EC29857' THEN
    RAISE EXCEPTION 'POST_V41_BASELINE_REFUSED';
  END IF;
END $guard$;

CREATE OR REPLACE FUNCTION public.reserve_generic_execution_v3(
  p_policy UUID,p_bindings JSONB,p_contract_binding JSONB,p_source_facts JSONB,
  p_projection_text TEXT,p_filename TEXT,p_ttl INTEGER DEFAULT 30
) RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,public AS $$
DECLARE
  pol public.generic_producer_policies_v3%ROWTYPE;
  b JSONB := p_bindings;
  cb JSONB := p_contract_binding;
  k TEXT;
  commitment TEXT;
  expiry TIMESTAMPTZ;
  required TEXT[] := ARRAY['request_id','actor_id','execution_id','analysis_id','company_id','entity_id',
    'engagement_id','producer_id','producer_version','task_id','task_version','admission_contract_sha256',
    'raw_source_sha256','source_representation_sha256','producer_input_sha256'];
  contract_required TEXT[] := ARRAY['schema_version','producer_id','producer_version','fact_schema_id',
    'fact_schema_version','fact_schema_sha256','positive_projection_policy_id',
    'positive_projection_policy_version','positive_projection_policy_sha256','task_id','task_version',
    'task_contract_sha256','output_contract_id','output_contract_version','output_contract_sha256',
    'receipt_contract_version','profile_sha256'];
BEGIN
  IF jsonb_typeof(b) IS DISTINCT FROM 'object' OR (b - required) <> '{}'::jsonb
     OR jsonb_typeof(cb) IS DISTINCT FROM 'object' OR (cb - contract_required) <> '{}'::jsonb
     OR p_ttl IS NULL OR p_ttl NOT BETWEEN 1 AND 300 THEN
    RAISE EXCEPTION 'V41 binding shape refused';
  END IF;
  FOREACH k IN ARRAY required LOOP
    IF jsonb_typeof(b->k) IS DISTINCT FROM 'string' OR length(b->>k)=0 THEN
      RAISE EXCEPTION 'V41 binding value refused';
    END IF;
  END LOOP;
  FOREACH k IN ARRAY contract_required LOOP
    IF jsonb_typeof(cb->k) IS DISTINCT FROM 'string' OR length(cb->>k)=0 THEN
      RAISE EXCEPTION 'V41 contract value refused';
    END IF;
  END LOOP;
  FOREACH k IN ARRAY ARRAY['admission_contract_sha256','raw_source_sha256',
    'source_representation_sha256','producer_input_sha256'] LOOP
    IF (b->>k) !~ '^[A-F0-9]{64}$' THEN RAISE EXCEPTION 'V41 binding digest refused'; END IF;
  END LOOP;
  FOREACH k IN ARRAY ARRAY['fact_schema_sha256','positive_projection_policy_sha256',
    'task_contract_sha256','output_contract_sha256','profile_sha256'] LOOP
    IF (cb->>k) !~ '^[A-F0-9]{64}$' THEN RAISE EXCEPTION 'V41 contract digest refused'; END IF;
  END LOOP;
  SELECT * INTO STRICT pol FROM public.generic_producer_policies_v3
    WHERE id=p_policy AND enabled FOR SHARE;
  IF jsonb_typeof(pol.specification->'policy_evidence_sha256') IS DISTINCT FROM 'string'
     OR ((pol.specification->>'policy_evidence_sha256') ~ '^[A-F0-9]{64}$') IS DISTINCT FROM true
     OR upper(encode(sha256(convert_to((pol.specification-'policy_evidence_sha256')::text,'UTF8')),'hex'))
        IS DISTINCT FROM pol.specification->>'policy_evidence_sha256' THEN
    RAISE EXCEPTION 'V41 provider policy evidence refused';
  END IF;
  FOREACH k IN ARRAY ARRAY['company_id','entity_id','engagement_id'] LOOP
    IF jsonb_typeof(pol.specification->k) IS DISTINCT FROM 'string'
       OR b->>k IS DISTINCT FROM pol.specification->>k THEN
      RAISE EXCEPTION 'V41 policy scope refused';
    END IF;
  END LOOP;
  IF cb IS DISTINCT FROM pol.contract_binding
     OR b->>'admission_contract_sha256' IS DISTINCT FROM pol.contract_binding_sha256
     OR cb->>'producer_id' IS DISTINCT FROM b->>'producer_id'
     OR cb->>'producer_version' IS DISTINCT FROM b->>'producer_version'
     OR cb->>'task_id' IS DISTINCT FROM b->>'task_id'
     OR cb->>'task_version' IS DISTINCT FROM b->>'task_version'
     OR cb->>'receipt_contract_version' IS DISTINCT FROM 'governed-generic-producer-receipt-3'
     OR b->>'producer_id' IS DISTINCT FROM pol.specification->>'producer_id'
     OR b->>'producer_version' IS DISTINCT FROM pol.specification->>'producer_version'
     OR b->>'task_id' IS DISTINCT FROM pol.specification->>'task_id'
     OR b->>'task_version' IS DISTINCT FROM pol.specification->>'task_version'
     OR b->>'raw_source_sha256' IS DISTINCT FROM pol.specification->>'source_sha256'
     OR p_filename IS DISTINCT FROM pol.specification->>'filename'
     OR jsonb_typeof(p_source_facts) IS DISTINCT FROM 'object'
     OR p_source_facts->>'status' IS DISTINCT FROM 'UNDERSTOOD'
     OR p_source_facts->>'source_representation_sha256' IS DISTINCT FROM b->>'source_representation_sha256'
     OR p_projection_text IS NULL OR octet_length(p_projection_text) NOT BETWEEN 2 AND 1000000
     OR upper(encode(sha256(convert_to(p_projection_text,'UTF8')),'hex'))
        IS DISTINCT FROM b->>'producer_input_sha256' THEN
    RAISE EXCEPTION 'V41 policy/contract/source/projection refused';
  END IF;
  PERFORM public.check_execution_scope_v2((b->>'actor_id')::uuid,(b->>'company_id')::uuid,
    (b->>'entity_id')::uuid,(b->>'engagement_id')::uuid);
  IF EXISTS (SELECT 1 FROM public.analyses WHERE id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.governed_analysis_envelopes WHERE analysis_id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.governed_execution_receipts WHERE analysis_id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.execution_receipts_v2 WHERE analysis_id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.generic_execution_receipts_v3 WHERE analysis_id=(b->>'analysis_id')::uuid) THEN
    RAISE EXCEPTION 'V41 historical or partial analysis refused';
  END IF;
  commitment := upper(encode(sha256(convert_to(jsonb_build_object(
    'policy_id',p_policy,'bindings',b,'contract_binding',cb,'source_facts',p_source_facts,
    'projection_text',p_projection_text,'filename',p_filename)::text,'UTF8')),'hex'));
  expiry := clock_timestamp()+make_interval(secs=>p_ttl);
  INSERT INTO public.generic_execution_admissions_v3(execution_id,request_id,analysis_id,actor_id,
    company_id,entity_id,engagement_id,policy_id,bindings,contract_binding,source_facts,
    projection_text,filename,composition_sha256,state,expires_at)
  VALUES ((b->>'execution_id')::uuid,(b->>'request_id')::uuid,(b->>'analysis_id')::uuid,
    (b->>'actor_id')::uuid,(b->>'company_id')::uuid,(b->>'entity_id')::uuid,
    (b->>'engagement_id')::uuid,p_policy,b,cb,p_source_facts,p_projection_text,p_filename,
    commitment,'RESERVED',expiry);
  RETURN jsonb_build_object('status','RESERVED','execution_id',b->>'execution_id',
    'composition_sha256',commitment,'contract_binding_sha256',pol.contract_binding_sha256,
    'provider_policy_evidence_sha256',pol.specification->>'policy_evidence_sha256',
    'expires_at',expiry);
END $$;

CREATE OR REPLACE FUNCTION public.complete_generic_execution_v3(
  p_execution UUID,p_actor UUID,p_claim UUID,p_receipt JSONB,
  p_analysis JSONB,p_envelope JSONB,p_envelope_text TEXT
) RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,public AS $$
DECLARE a public.generic_execution_admissions_v3%ROWTYPE; pol public.generic_producer_policies_v3%ROWTYPE;
  r JSONB:=p_receipt; result_id UUID; k TEXT;
  receipt_required TEXT[]:=ARRAY['schema_version','evidence_status','bindings','contract_binding',
    'contract_binding_sha256','request_sha256','response_sha256','projection_sha256','envelope_sha256',
    'provider_policy_evidence_sha256'];
BEGIN
  SELECT * INTO STRICT a FROM public.generic_execution_admissions_v3
    WHERE execution_id=p_execution FOR UPDATE;
  IF a.state <> 'CLAIMED' OR a.actor_id IS DISTINCT FROM p_actor OR a.claim_id IS DISTINCT FROM p_claim THEN
    RAISE EXCEPTION 'V41 completion authority refused';
  END IF;
  BEGIN
    IF clock_timestamp() >= a.expires_at THEN RAISE EXCEPTION 'expired'; END IF;
    SELECT * INTO STRICT pol FROM public.generic_producer_policies_v3
      WHERE id=a.policy_id AND enabled FOR SHARE;
    PERFORM public.check_execution_scope_v2(a.actor_id,a.company_id,a.entity_id,a.engagement_id);
    FOREACH k IN ARRAY receipt_required LOOP
      IF k IN ('bindings','contract_binding') THEN
        IF jsonb_typeof(r->k) IS DISTINCT FROM 'object' THEN
          RAISE EXCEPTION 'V41 receipt object required';
        END IF;
      ELSE
        IF jsonb_typeof(r->k) IS DISTINCT FROM 'string' THEN
          RAISE EXCEPTION 'V41 receipt string required';
        END IF;
      END IF;
    END LOOP;
    IF jsonb_typeof(r) IS DISTINCT FROM 'object' OR (r-receipt_required) <> '{}'::jsonb
       OR r->>'schema_version' IS DISTINCT FROM 'governed-generic-producer-receipt-3'
       OR r->>'evidence_status' IS DISTINCT FROM 'ADMITTED_EXECUTION'
       OR r->'bindings' IS DISTINCT FROM a.bindings
       OR r->'contract_binding' IS DISTINCT FROM a.contract_binding
       OR r->>'contract_binding_sha256' IS DISTINCT FROM a.bindings->>'admission_contract_sha256'
       OR r->>'request_sha256' IS DISTINCT FROM a.bindings->>'producer_input_sha256'
       OR r->>'projection_sha256' IS DISTINCT FROM a.bindings->>'producer_input_sha256'
       OR r->>'provider_policy_evidence_sha256'
          IS DISTINCT FROM pol.specification->>'policy_evidence_sha256'
       OR upper(encode(sha256(convert_to((pol.specification-'policy_evidence_sha256')::text,'UTF8')),'hex'))
          IS DISTINCT FROM r->>'provider_policy_evidence_sha256'
       OR r->>'envelope_sha256' IS DISTINCT FROM p_envelope->>'envelope_sha256'
       OR upper(encode(sha256(convert_to(p_envelope_text,'UTF8')),'hex'))
          IS DISTINCT FROM r->>'envelope_sha256'
       OR p_envelope_text::jsonb IS DISTINCT FROM p_envelope->'envelope_json'
       OR p_envelope->'envelope_json'->'source_facts' IS DISTINCT FROM a.source_facts
       OR p_envelope->'envelope_json'->'governed_analysis'->>'invocation_nonce'
          IS DISTINCT FROM upper(replace(a.request_id::text,'-',''))
       OR p_envelope->>'source_representation_sha256'
          IS DISTINCT FROM a.bindings->>'source_representation_sha256'
       OR p_envelope->>'analysis_id' IS DISTINCT FROM a.analysis_id::text
       OR p_envelope->>'company_id' IS DISTINCT FROM a.company_id::text
       OR p_envelope->>'entity_id' IS DISTINCT FROM a.entity_id::text
       OR p_envelope->>'engagement_id' IS DISTINCT FROM a.engagement_id::text
       OR p_analysis->>'id' IS DISTINCT FROM a.analysis_id::text
       OR p_analysis->>'company_id' IS DISTINCT FROM a.company_id::text
       OR p_analysis->>'entity_id' IS DISTINCT FROM a.entity_id::text
       OR p_analysis->>'fichier_nom' IS DISTINCT FROM a.filename
       OR p_analysis->>'status' IS DISTINCT FROM 'completed'
       OR upper(p_analysis->>'source_data_hash') IS DISTINCT FROM a.bindings->>'raw_source_sha256' THEN
      RAISE EXCEPTION 'V41 result binding refused';
    END IF;
    FOREACH k IN ARRAY ARRAY['request_sha256','response_sha256','projection_sha256',
      'envelope_sha256','provider_policy_evidence_sha256'] LOOP
      IF ((r->>k) ~ '^[A-F0-9]{64}$') IS DISTINCT FROM true THEN RAISE EXCEPTION 'V41 receipt digest refused'; END IF;
    END LOOP;
    result_id:=public.persist_governed_analysis_v1(p_analysis,p_envelope);
    INSERT INTO public.generic_execution_receipts_v3(execution_id,analysis_id,receipt)
      VALUES(a.execution_id,result_id,r);
    IF clock_timestamp() >= a.expires_at THEN RAISE EXCEPTION 'expired during completion'; END IF;
    UPDATE public.generic_execution_admissions_v3 SET state='COMPLETE',terminal_at=clock_timestamp()
      WHERE execution_id=p_execution;
  EXCEPTION WHEN OTHERS THEN
    UPDATE public.generic_execution_admissions_v3 SET state='REFUSED',terminal_at=clock_timestamp()
      WHERE execution_id=p_execution;
    RETURN jsonb_build_object('status','REFUSED','automatic_retry_permitted',false);
  END;
  RETURN jsonb_build_object('status','COMPLETE','analysis_id',result_id,
    'automatic_retry_permitted',false);
END $$;

COMMIT;
