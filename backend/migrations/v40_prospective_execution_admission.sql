-- PREPARED: separate synthetic/local-only admission protocol. NOT deployed.
-- V39 remains unchanged. Empty policy table: deployment admits no producer.
BEGIN;
DO $$ BEGIN
  IF to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NULL
     OR to_regclass('public.governed_execution_receipts') IS NULL THEN
    RAISE EXCEPTION 'V40 prerequisites missing';
  END IF;
  IF to_regclass('public.producer_policies_v2') IS NOT NULL
     OR to_regclass('public.execution_admissions_v2') IS NOT NULL
     OR to_regclass('public.execution_receipts_v2') IS NOT NULL THEN
    RAISE EXCEPTION 'V40 already or partially installed; inspect without overwriting';
  END IF;
END $$;

CREATE TABLE public.producer_policies_v2 (
  id UUID PRIMARY KEY,
  specification JSONB NOT NULL CHECK (jsonb_typeof(specification) = 'object'),
  contract_sha256 TEXT NOT NULL CHECK (contract_sha256 ~ '^[A-F0-9]{64}$'),
  contract_version TEXT NOT NULL DEFAULT 'local-synthetic-durable-admission-2'
    CHECK (contract_version = 'local-synthetic-durable-admission-2'),
  enabled BOOLEAN NOT NULL DEFAULT false,
  origin TEXT NOT NULL DEFAULT 'SYNTHETIC' CHECK (origin = 'SYNTHETIC'),
  egress TEXT NOT NULL DEFAULT 'DENY' CHECK (egress = 'DENY')
);

CREATE TABLE public.execution_admissions_v2 (
  execution_id UUID PRIMARY KEY,
  request_id UUID NOT NULL UNIQUE,
  analysis_id UUID NOT NULL UNIQUE,
  actor_id UUID NOT NULL,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  policy_id UUID NOT NULL REFERENCES public.producer_policies_v2(id) ON DELETE RESTRICT,
  bindings JSONB NOT NULL CHECK (jsonb_typeof(bindings) = 'object'),
  input_text TEXT NOT NULL CHECK (octet_length(input_text) BETWEEN 2 AND 1000000),
  filename TEXT NOT NULL,
  composition_sha256 TEXT NOT NULL CHECK (composition_sha256 ~ '^[A-F0-9]{64}$'),
  state TEXT NOT NULL CHECK (state IN ('RESERVED','CLAIMED','COMPLETE','REFUSED','CLOSED')),
  issued_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  expires_at TIMESTAMPTZ NOT NULL,
  claim_id UUID UNIQUE,
  claimed_at TIMESTAMPTZ,
  terminal_at TIMESTAMPTZ,
  FOREIGN KEY (entity_id, company_id) REFERENCES public.entities(id,company_id) ON DELETE RESTRICT,
  FOREIGN KEY (engagement_id, entity_id) REFERENCES public.engagements(id,entity_id) ON DELETE RESTRICT
);

CREATE TABLE public.execution_receipts_v2 (
  execution_id UUID PRIMARY KEY REFERENCES public.execution_admissions_v2(execution_id) ON DELETE RESTRICT,
  analysis_id UUID NOT NULL UNIQUE REFERENCES public.governed_analysis_envelopes(analysis_id) ON DELETE RESTRICT,
  receipt JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE public.producer_policies_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.execution_admissions_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.execution_receipts_v2 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.producer_policies_v2, public.execution_admissions_v2, public.execution_receipts_v2
  FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON public.producer_policies_v2, public.execution_admissions_v2, public.execution_receipts_v2 TO service_role;
-- No policy-registration RPC: deployment alone cannot activate a producer.

CREATE FUNCTION public.guard_prospective_execution_v2() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'V40 evidence deletion refused'; END IF;
  IF TG_TABLE_NAME = 'producer_policies_v2' THEN
    IF (to_jsonb(NEW) - 'enabled') IS DISTINCT FROM (to_jsonb(OLD) - 'enabled')
       OR NOT OLD.enabled OR NEW.enabled THEN RAISE EXCEPTION 'V40 policy mutation refused'; END IF;
    RETURN NEW; -- only irreversible disable of a policy, not re-enable/rewrite
  END IF;
  IF TG_TABLE_NAME = 'execution_receipts_v2' THEN RAISE EXCEPTION 'V40 immutable receipt'; END IF;
  IF (to_jsonb(NEW) - ARRAY['state','claim_id','claimed_at','terminal_at'])
       IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['state','claim_id','claimed_at','terminal_at'])
     OR NOT ((OLD.state = 'RESERVED' AND NEW.state IN ('CLAIMED','CLOSED'))
          OR (OLD.state = 'CLAIMED' AND NEW.state IN ('COMPLETE','REFUSED','CLOSED')))
     OR (OLD.state = 'CLAIMED' AND (NEW.claim_id IS DISTINCT FROM OLD.claim_id
                                 OR NEW.claimed_at IS DISTINCT FROM OLD.claimed_at)) THEN
    RAISE EXCEPTION 'V40 immutable composition or invalid transition';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER policy_v2_guard BEFORE UPDATE OR DELETE ON public.producer_policies_v2
  FOR EACH ROW EXECUTE FUNCTION public.guard_prospective_execution_v2();
CREATE TRIGGER admission_v2_guard BEFORE UPDATE OR DELETE ON public.execution_admissions_v2
  FOR EACH ROW EXECUTE FUNCTION public.guard_prospective_execution_v2();
CREATE TRIGGER receipt_v2_guard BEFORE UPDATE OR DELETE ON public.execution_receipts_v2
  FOR EACH ROW EXECUTE FUNCTION public.guard_prospective_execution_v2();

CREATE FUNCTION public.check_execution_scope_v2(p_actor UUID,p_company UUID,p_entity UUID,p_engagement UUID)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  -- Share locks last until the caller transaction ends; ownership changes cannot
  -- interleave with the final result transaction. Auth itself is backend-owned.
  PERFORM 1 FROM public.profiles WHERE id=p_actor AND company_id=p_company FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 actor scope refused'; END IF;
  PERFORM 1 FROM public.companies WHERE id=p_company FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 tenant absent'; END IF;
  PERFORM 1 FROM public.entities WHERE id=p_entity AND company_id=p_company FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 entity scope refused'; END IF;
  PERFORM 1 FROM public.engagements WHERE id=p_engagement AND entity_id=p_entity FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 engagement scope refused'; END IF;
END $$;

CREATE FUNCTION public.reserve_execution_v2(p_policy UUID,p_bindings JSONB,p_input TEXT,p_filename TEXT,p_ttl INTEGER DEFAULT 30)
RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE
  pol public.producer_policies_v2%ROWTYPE;
  b JSONB := p_bindings;
  k TEXT;
  commitment TEXT;
  expiry TIMESTAMPTZ;
  required TEXT[] := ARRAY['request_id','actor_id','execution_id','analysis_id','company_id','entity_id',
    'engagement_id','producer_id','producer_version','task_id','task_version','admission_contract_sha256',
    'raw_source_sha256','source_representation_sha256','producer_input_sha256'];
BEGIN
  IF jsonb_typeof(b) IS DISTINCT FROM 'object' OR (b - required) <> '{}'::jsonb
     OR p_ttl IS NULL OR p_ttl NOT BETWEEN 1 AND 300 THEN RAISE EXCEPTION 'V40 binding shape refused'; END IF;
  FOREACH k IN ARRAY required LOOP
    IF jsonb_typeof(b->k) IS DISTINCT FROM 'string' OR length(b->>k)=0 THEN
      RAISE EXCEPTION 'V40 binding value refused';
    END IF;
  END LOOP;
  FOREACH k IN ARRAY ARRAY['admission_contract_sha256','raw_source_sha256','source_representation_sha256','producer_input_sha256'] LOOP
    IF (b->>k) !~ '^[A-F0-9]{64}$' THEN RAISE EXCEPTION 'V40 digest refused'; END IF;
  END LOOP;
  SELECT * INTO STRICT pol FROM public.producer_policies_v2 WHERE id=p_policy AND enabled FOR SHARE;
  FOREACH k IN ARRAY ARRAY['company_id','entity_id','engagement_id','producer_id','producer_version','task_id','task_version'] LOOP
    IF b->>k IS DISTINCT FROM pol.specification->>k THEN RAISE EXCEPTION 'V40 policy binding refused'; END IF;
  END LOOP;
  IF b->>'producer_id' = 'registered-workbook-mock-v1'
     OR b->>'admission_contract_sha256' IS DISTINCT FROM pol.contract_sha256
     OR b->>'raw_source_sha256' IS DISTINCT FROM pol.specification->>'source_sha256'
     OR p_filename IS DISTINCT FROM pol.specification->>'filename'
     OR p_input IS NULL OR octet_length(p_input) NOT BETWEEN 2 AND 1000000
     OR upper(encode(sha256(convert_to(p_input,'UTF8')),'hex')) IS DISTINCT FROM b->>'producer_input_sha256'
     OR (p_input::jsonb)->>'source_representation_sha256' IS DISTINCT FROM b->>'source_representation_sha256'
     OR (p_input::jsonb)->>'status' IS DISTINCT FROM 'UNDERSTOOD' THEN
    RAISE EXCEPTION 'V40 policy/source/input refused';
  END IF;
  PERFORM public.check_execution_scope_v2((b->>'actor_id')::uuid,(b->>'company_id')::uuid,
    (b->>'entity_id')::uuid,(b->>'engagement_id')::uuid);
  IF EXISTS (SELECT 1 FROM public.analyses WHERE id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.governed_analysis_envelopes WHERE analysis_id=(b->>'analysis_id')::uuid)
     OR EXISTS (SELECT 1 FROM public.governed_execution_receipts WHERE analysis_id=(b->>'analysis_id')::uuid) THEN
    RAISE EXCEPTION 'V40 historical or partial analysis refused';
  END IF;
  commitment := upper(encode(sha256(convert_to(jsonb_build_object(
    'policy_id',p_policy,'bindings',b,'input_text',p_input,'filename',p_filename)::text,'UTF8')),'hex'));
  expiry := clock_timestamp() + make_interval(secs=>p_ttl);
  INSERT INTO public.execution_admissions_v2(execution_id,request_id,analysis_id,actor_id,
    company_id,entity_id,engagement_id,policy_id,bindings,input_text,filename,composition_sha256,state,expires_at)
  VALUES ((b->>'execution_id')::uuid,(b->>'request_id')::uuid,(b->>'analysis_id')::uuid,(b->>'actor_id')::uuid,
    (b->>'company_id')::uuid,(b->>'entity_id')::uuid,(b->>'engagement_id')::uuid,p_policy,b,p_input,p_filename,
    commitment,'RESERVED',expiry);
  RETURN jsonb_build_object('status','RESERVED','execution_id',b->>'execution_id',
    'composition_sha256',commitment,'expires_at',expiry);
END $$;

CREATE FUNCTION public.claim_execution_v2(p_execution UUID,p_actor UUID,p_composition TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE a public.execution_admissions_v2%ROWTYPE; claim UUID := gen_random_uuid(); stamp TIMESTAMPTZ;
BEGIN
  SELECT * INTO STRICT a FROM public.execution_admissions_v2 WHERE execution_id=p_execution FOR UPDATE;
  IF a.actor_id IS DISTINCT FROM p_actor OR a.composition_sha256 IS DISTINCT FROM p_composition
     OR a.state <> 'RESERVED' OR clock_timestamp() >= a.expires_at THEN
    RAISE EXCEPTION 'V40 claim refused';
  END IF;
  PERFORM 1 FROM public.producer_policies_v2 WHERE id=a.policy_id AND enabled FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 policy disabled'; END IF;
  PERFORM public.check_execution_scope_v2(a.actor_id,a.company_id,a.entity_id,a.engagement_id);
  stamp := clock_timestamp();
  IF stamp >= a.expires_at THEN RAISE EXCEPTION 'V40 claim expired during check'; END IF;
  UPDATE public.execution_admissions_v2 SET state='CLAIMED',claim_id=claim,claimed_at=stamp WHERE execution_id=p_execution;
  -- Caller MUST commit this RPC before executing. An ambiguous response never permits execution.
  RETURN jsonb_build_object('status','CLAIMED','execution_id',a.execution_id,'claim_id',claim,
    'claimed_at',stamp,'composition_sha256',a.composition_sha256,'bindings',a.bindings,'input_text',a.input_text);
END $$;

CREATE FUNCTION public.close_execution_v2(p_execution UUID,p_actor UUID)
RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  UPDATE public.execution_admissions_v2 SET state='CLOSED',terminal_at=clock_timestamp()
    WHERE execution_id=p_execution AND actor_id=p_actor AND state IN ('RESERVED','CLAIMED');
  IF NOT FOUND THEN RAISE EXCEPTION 'V40 close refused'; END IF;
  RETURN 'CLOSED';
END $$;

CREATE FUNCTION public.complete_execution_v2(p_execution UUID,p_actor UUID,p_claim UUID,
  p_candidate JSONB,p_analysis JSONB,p_envelope JSONB,p_envelope_text TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE a public.execution_admissions_v2%ROWTYPE; r JSONB := p_candidate; result_id UUID; receipt JSONB;
BEGIN
  SELECT * INTO STRICT a FROM public.execution_admissions_v2 WHERE execution_id=p_execution FOR UPDATE;
  IF a.state <> 'CLAIMED' OR a.actor_id IS DISTINCT FROM p_actor OR a.claim_id IS DISTINCT FROM p_claim THEN
    RAISE EXCEPTION 'V40 completion authority refused';
  END IF;
  -- Nested transaction: late failure removes the entire result trio, while the
  -- outer transaction records REFUSED. Never raise again after recording it.
  BEGIN
    IF clock_timestamp() >= a.expires_at THEN RAISE EXCEPTION 'expired'; END IF;
    PERFORM 1 FROM public.producer_policies_v2 WHERE id=a.policy_id AND enabled FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION 'policy disabled'; END IF;
    PERFORM public.check_execution_scope_v2(a.actor_id,a.company_id,a.entity_id,a.engagement_id);
    IF jsonb_typeof(r) IS DISTINCT FROM 'object'
       OR (r - ARRAY['schema_version','evidence_status','bindings','envelope_sha256','started_at','completed_at']) <> '{}'::jsonb
       OR r->>'schema_version' IS DISTINCT FROM 'producer-execution-candidate-2'
       OR r->>'evidence_status' IS DISTINCT FROM 'UNADMITTED_CANDIDATE'
       OR r->'bindings' IS DISTINCT FROM a.bindings
       OR COALESCE(r->>'started_at','') !~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
       OR COALESCE(r->>'completed_at','') !~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
       OR (r->>'started_at')::timestamptz < a.claimed_at
       OR (r->>'completed_at')::timestamptz < (r->>'started_at')::timestamptz
       OR (r->>'completed_at')::timestamptz > clock_timestamp()
       OR r->>'envelope_sha256' IS DISTINCT FROM p_envelope->>'envelope_sha256'
       OR upper(encode(sha256(convert_to(p_envelope_text,'UTF8')),'hex')) IS DISTINCT FROM r->>'envelope_sha256'
       OR p_envelope_text::jsonb IS DISTINCT FROM p_envelope->'envelope_json'
       OR (p_envelope->'envelope_json'->'source_facts') IS DISTINCT FROM a.input_text::jsonb
       OR p_envelope->'envelope_json'->'governed_analysis'->>'invocation_nonce'
          IS DISTINCT FROM upper(replace(a.request_id::text,'-',''))
       OR p_envelope->>'source_representation_sha256' IS DISTINCT FROM a.bindings->>'source_representation_sha256'
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
      RAISE EXCEPTION 'V40 result binding refused';
    END IF;
    result_id := public.persist_governed_analysis_v1(p_analysis,p_envelope);
    receipt := jsonb_build_object('schema_version','governed-execution-receipt-2',
      'evidence_scope','LOCAL_SYNTHETIC_ONLY','egress','DENY','candidate',r,
      'composition_sha256',a.composition_sha256,'policy_id',a.policy_id,
      'issued_at',a.issued_at,'claimed_at',a.claimed_at);
    INSERT INTO public.execution_receipts_v2(execution_id,analysis_id,receipt) VALUES (a.execution_id,result_id,receipt);
    IF clock_timestamp() >= a.expires_at THEN RAISE EXCEPTION 'expired during completion'; END IF;
    UPDATE public.execution_admissions_v2 SET state='COMPLETE',terminal_at=clock_timestamp() WHERE execution_id=p_execution;
  EXCEPTION WHEN OTHERS THEN
    UPDATE public.execution_admissions_v2 SET state='REFUSED',terminal_at=clock_timestamp() WHERE execution_id=p_execution;
    RETURN jsonb_build_object('status','REFUSED','automatic_retry_permitted',false);
  END;
  RETURN jsonb_build_object('status','COMPLETE','analysis_id',result_id,'automatic_retry_permitted',false);
END $$;

REVOKE ALL ON FUNCTION public.guard_prospective_execution_v2(),
  public.check_execution_scope_v2(UUID,UUID,UUID,UUID) FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.reserve_execution_v2(UUID,JSONB,TEXT,TEXT,INTEGER),
  public.claim_execution_v2(UUID,UUID,TEXT),public.close_execution_v2(UUID,UUID),
  public.complete_execution_v2(UUID,UUID,UUID,JSONB,JSONB,JSONB,TEXT) FROM PUBLIC,anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.reserve_execution_v2(UUID,JSONB,TEXT,TEXT,INTEGER),
  public.claim_execution_v2(UUID,UUID,TEXT),public.close_execution_v2(UUID,UUID),
  public.complete_execution_v2(UUID,UUID,UUID,JSONB,JSONB,JSONB,TEXT) TO service_role;
COMMIT;
