-- PREPARED LOCALLY ONLY. Distinct v3 contract; never reinterpret V39/V40.
-- Empty policy registry means migration deployment alone admits no producer.
BEGIN;

DO $$ BEGIN
  IF to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NULL
     OR to_regprocedure('public.check_execution_scope_v2(uuid,uuid,uuid,uuid)') IS NULL
     OR to_regclass('public.execution_receipts_v2') IS NULL THEN
    RAISE EXCEPTION 'V41 prerequisites missing';
  END IF;
  IF to_regclass('public.generic_producer_policies_v3') IS NOT NULL
     OR to_regclass('public.generic_execution_admissions_v3') IS NOT NULL
     OR to_regclass('public.generic_execution_receipts_v3') IS NOT NULL THEN
    RAISE EXCEPTION 'V41 already or partially installed; inspect without overwriting';
  END IF;
END $$;

CREATE TABLE public.generic_producer_policies_v3 (
  id UUID PRIMARY KEY,
  specification JSONB NOT NULL CHECK (jsonb_typeof(specification) = 'object'),
  contract_binding JSONB NOT NULL CHECK (jsonb_typeof(contract_binding) = 'object'),
  contract_binding_text TEXT NOT NULL CHECK (
    contract_binding_text::jsonb = contract_binding
    AND upper(encode(sha256(convert_to(contract_binding_text,'UTF8')),'hex')) = contract_binding_sha256
  ),
  contract_binding_sha256 TEXT NOT NULL CHECK (contract_binding_sha256 ~ '^[A-F0-9]{64}$'),
  enabled BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE public.generic_execution_admissions_v3 (
  execution_id UUID PRIMARY KEY,
  request_id UUID NOT NULL UNIQUE,
  analysis_id UUID NOT NULL UNIQUE,
  actor_id UUID NOT NULL,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  policy_id UUID NOT NULL REFERENCES public.generic_producer_policies_v3(id) ON DELETE RESTRICT,
  bindings JSONB NOT NULL CHECK (jsonb_typeof(bindings) = 'object'),
  contract_binding JSONB NOT NULL CHECK (jsonb_typeof(contract_binding) = 'object'),
  source_facts JSONB NOT NULL CHECK (jsonb_typeof(source_facts) = 'object'),
  projection_text TEXT NOT NULL CHECK (octet_length(projection_text) BETWEEN 2 AND 1000000),
  filename TEXT NOT NULL,
  composition_sha256 TEXT NOT NULL CHECK (composition_sha256 ~ '^[A-F0-9]{64}$'),
  state TEXT NOT NULL CHECK (state IN ('RESERVED','CLAIMED','COMPLETE','REFUSED','CLOSED')),
  issued_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  expires_at TIMESTAMPTZ NOT NULL,
  claim_id UUID UNIQUE,
  claimed_at TIMESTAMPTZ,
  terminal_at TIMESTAMPTZ,
  FOREIGN KEY (entity_id,company_id) REFERENCES public.entities(id,company_id) ON DELETE RESTRICT,
  FOREIGN KEY (engagement_id,entity_id) REFERENCES public.engagements(id,entity_id) ON DELETE RESTRICT
);

CREATE TABLE public.generic_execution_receipts_v3 (
  execution_id UUID PRIMARY KEY REFERENCES public.generic_execution_admissions_v3(execution_id) ON DELETE RESTRICT,
  analysis_id UUID NOT NULL UNIQUE REFERENCES public.governed_analysis_envelopes(analysis_id) ON DELETE RESTRICT,
  receipt JSONB NOT NULL CHECK (jsonb_typeof(receipt) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE public.generic_producer_policies_v3 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generic_execution_admissions_v3 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generic_execution_receipts_v3 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.generic_producer_policies_v3,public.generic_execution_admissions_v3,
  public.generic_execution_receipts_v3 FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT ON public.generic_producer_policies_v3,public.generic_execution_admissions_v3,
  public.generic_execution_receipts_v3 TO service_role;
-- No registration RPC. An empty registry cannot admit or execute anything.

CREATE FUNCTION public.guard_generic_execution_v3() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog,public AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'V41 evidence deletion refused'; END IF;
  IF TG_TABLE_NAME = 'generic_producer_policies_v3' THEN
    IF (to_jsonb(NEW) - 'enabled') IS DISTINCT FROM (to_jsonb(OLD) - 'enabled')
       OR NOT OLD.enabled OR NEW.enabled THEN RAISE EXCEPTION 'V41 policy mutation refused'; END IF;
    RETURN NEW;
  END IF;
  IF TG_TABLE_NAME = 'generic_execution_receipts_v3' THEN
    RAISE EXCEPTION 'V41 immutable receipt';
  END IF;
  IF (to_jsonb(NEW) - ARRAY['state','claim_id','claimed_at','terminal_at'])
       IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['state','claim_id','claimed_at','terminal_at'])
     OR NOT ((OLD.state='RESERVED' AND NEW.state IN ('CLAIMED','CLOSED'))
          OR (OLD.state='CLAIMED' AND NEW.state IN ('COMPLETE','REFUSED','CLOSED')))
     OR (OLD.state='CLAIMED' AND (NEW.claim_id IS DISTINCT FROM OLD.claim_id
                              OR NEW.claimed_at IS DISTINCT FROM OLD.claimed_at)) THEN
    RAISE EXCEPTION 'V41 immutable composition or invalid transition';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER generic_policy_v3_guard BEFORE UPDATE OR DELETE ON public.generic_producer_policies_v3
  FOR EACH ROW EXECUTE FUNCTION public.guard_generic_execution_v3();
CREATE TRIGGER generic_admission_v3_guard BEFORE UPDATE OR DELETE ON public.generic_execution_admissions_v3
  FOR EACH ROW EXECUTE FUNCTION public.guard_generic_execution_v3();
CREATE TRIGGER generic_receipt_v3_guard BEFORE UPDATE OR DELETE ON public.generic_execution_receipts_v3
  FOR EACH ROW EXECUTE FUNCTION public.guard_generic_execution_v3();

CREATE FUNCTION public.reserve_generic_execution_v3(
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
    'expires_at',expiry);
END $$;

CREATE FUNCTION public.claim_generic_execution_v3(p_execution UUID,p_actor UUID,p_composition TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,public AS $$
DECLARE a public.generic_execution_admissions_v3%ROWTYPE; claim UUID:=gen_random_uuid(); stamp TIMESTAMPTZ;
BEGIN
  SELECT * INTO STRICT a FROM public.generic_execution_admissions_v3
    WHERE execution_id=p_execution FOR UPDATE;
  IF a.actor_id IS DISTINCT FROM p_actor OR a.composition_sha256 IS DISTINCT FROM p_composition
     OR a.state <> 'RESERVED' OR clock_timestamp() >= a.expires_at THEN
    RAISE EXCEPTION 'V41 claim refused';
  END IF;
  PERFORM 1 FROM public.generic_producer_policies_v3 WHERE id=a.policy_id AND enabled FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V41 policy disabled'; END IF;
  PERFORM public.check_execution_scope_v2(a.actor_id,a.company_id,a.entity_id,a.engagement_id);
  stamp:=clock_timestamp();
  IF stamp >= a.expires_at THEN RAISE EXCEPTION 'V41 claim expired during check'; END IF;
  UPDATE public.generic_execution_admissions_v3 SET state='CLAIMED',claim_id=claim,claimed_at=stamp
    WHERE execution_id=p_execution;
  RETURN jsonb_build_object('status','CLAIMED','execution_id',a.execution_id,'claim_id',claim,
    'claimed_at',stamp,'composition_sha256',a.composition_sha256,'bindings',a.bindings,
    'contract_binding',a.contract_binding,'source_facts',a.source_facts,
    'projection_text',a.projection_text);
END $$;

CREATE FUNCTION public.close_generic_execution_v3(p_execution UUID,p_actor UUID)
RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,public AS $$
BEGIN
  UPDATE public.generic_execution_admissions_v3 SET state='CLOSED',terminal_at=clock_timestamp()
    WHERE execution_id=p_execution AND actor_id=p_actor AND state IN ('RESERVED','CLAIMED');
  IF NOT FOUND THEN RAISE EXCEPTION 'V41 close refused'; END IF;
  RETURN 'CLOSED';
END $$;

CREATE FUNCTION public.complete_generic_execution_v3(
  p_execution UUID,p_actor UUID,p_claim UUID,p_receipt JSONB,
  p_analysis JSONB,p_envelope JSONB,p_envelope_text TEXT
) RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog,public AS $$
DECLARE a public.generic_execution_admissions_v3%ROWTYPE; r JSONB:=p_receipt; result_id UUID; k TEXT;
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
    PERFORM 1 FROM public.generic_producer_policies_v3 WHERE id=a.policy_id AND enabled FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION 'policy disabled'; END IF;
    PERFORM public.check_execution_scope_v2(a.actor_id,a.company_id,a.entity_id,a.engagement_id);
    IF jsonb_typeof(r) IS DISTINCT FROM 'object' OR (r-receipt_required) <> '{}'::jsonb
       OR r->>'schema_version' IS DISTINCT FROM 'governed-generic-producer-receipt-3'
       OR r->>'evidence_status' IS DISTINCT FROM 'ADMITTED_EXECUTION'
       OR r->'bindings' IS DISTINCT FROM a.bindings
       OR r->'contract_binding' IS DISTINCT FROM a.contract_binding
       OR r->>'contract_binding_sha256' IS DISTINCT FROM a.bindings->>'admission_contract_sha256'
       OR r->>'projection_sha256' IS DISTINCT FROM a.bindings->>'producer_input_sha256'
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
      IF (r->>k) !~ '^[A-F0-9]{64}$' THEN RAISE EXCEPTION 'V41 receipt digest refused'; END IF;
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

REVOKE ALL ON FUNCTION public.guard_generic_execution_v3() FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.reserve_generic_execution_v3(UUID,JSONB,JSONB,JSONB,TEXT,TEXT,INTEGER),
  public.claim_generic_execution_v3(UUID,UUID,TEXT),public.close_generic_execution_v3(UUID,UUID),
  public.complete_generic_execution_v3(UUID,UUID,UUID,JSONB,JSONB,JSONB,TEXT)
  FROM PUBLIC,anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.reserve_generic_execution_v3(UUID,JSONB,JSONB,JSONB,TEXT,TEXT,INTEGER),
  public.claim_generic_execution_v3(UUID,UUID,TEXT),public.close_generic_execution_v3(UUID,UUID),
  public.complete_generic_execution_v3(UUID,UUID,UUID,JSONB,JSONB,JSONB,TEXT)
  TO service_role;
COMMIT;
