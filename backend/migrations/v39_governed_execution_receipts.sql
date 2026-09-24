-- PREPARED ONLY. No backfill, no provider or real-data admission.
-- Apply once, after V27, only to an explicitly approved target.
BEGIN;

DO $$
BEGIN
  IF to_regclass('public.governed_analysis_envelopes') IS NULL
     OR to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NULL THEN
    RAISE EXCEPTION 'V39 prerequisite unavailable';
  END IF;
  IF to_regclass('public.governed_execution_receipts') IS NOT NULL
     OR to_regprocedure('public.persist_governed_execution_v1(jsonb,jsonb,jsonb)') IS NOT NULL THEN
    RAISE EXCEPTION 'V39 already or partially installed; inspect, do not overwrite';
  END IF;
END $$;

CREATE TABLE public.governed_execution_receipts (
  analysis_id UUID PRIMARY KEY REFERENCES public.governed_analysis_envelopes(analysis_id) ON DELETE RESTRICT,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  execution_id UUID NOT NULL UNIQUE,
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  sha256 TEXT NOT NULL CHECK (sha256 ~ '^[A-F0-9]{64}$'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (analysis_id, company_id, entity_id)
    REFERENCES public.analyses(id, company_id, entity_id) ON DELETE RESTRICT,
  FOREIGN KEY (engagement_id, entity_id)
    REFERENCES public.engagements(id, entity_id) ON DELETE RESTRICT
);

ALTER TABLE public.governed_execution_receipts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.governed_execution_receipts FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON public.governed_execution_receipts TO service_role;

CREATE FUNCTION public.reject_execution_receipt_mutation()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'Execution receipts are immutable; governed purge is not implemented';
END $$;
REVOKE ALL ON FUNCTION public.reject_execution_receipt_mutation() FROM PUBLIC, anon, authenticated, service_role;
CREATE TRIGGER execution_receipt_immutable
  BEFORE UPDATE OR DELETE ON public.governed_execution_receipts
  FOR EACH ROW EXECUTE FUNCTION public.reject_execution_receipt_mutation();

CREATE FUNCTION public.persist_governed_execution_v1(p_analysis JSONB, p_envelope JSONB, p_receipt JSONB)
RETURNS UUID LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE
  r JSONB := p_receipt->'payload';
  a UUID;
BEGIN
  IF jsonb_typeof(r) IS DISTINCT FROM 'object'
     OR r->>'schema_version' IS DISTINCT FROM 'execution-provenance-1'
     OR r->>'executor' IS DISTINCT FROM 'registered-workbook-mock-v1'
     OR r->>'data_origin' IS DISTINCT FROM 'REGISTERED_SYNTHETIC'
     OR r->>'provider_mode' IS DISTINCT FROM 'LOCAL_MOCK'
     OR r->>'transport' IS DISTINCT FROM 'NONE'
     OR r->>'analysis_id' IS DISTINCT FROM p_envelope->>'analysis_id'
     OR r->>'company_id' IS DISTINCT FROM p_envelope->>'company_id'
     OR r->>'entity_id' IS DISTINCT FROM p_envelope->>'entity_id'
     OR r->>'engagement_id' IS DISTINCT FROM p_envelope->>'engagement_id'
     OR r->>'envelope_sha256' IS DISTINCT FROM p_envelope->>'envelope_sha256'
     OR r->>'source_representation_sha256' IS DISTINCT FROM p_envelope->>'source_representation_sha256'
     OR r->>'raw_source_sha256' IS DISTINCT FROM upper(p_analysis->>'source_data_hash')
     OR r->>'raw_source_sha256' IS DISTINCT FROM 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
     OR p_analysis->>'fichier_nom' IS DISTINCT FROM 'pepperyn_v1_heterogeneous_english.xlsx'
     OR r->>'completed_at' IS NULL
     OR r->>'execution_id' IS NULL
     OR (r - ARRAY['schema_version','execution_id','executor','data_origin','provider_mode',
          'transport','raw_source_sha256','source_representation_sha256','envelope_sha256',
          'completed_at','analysis_id','company_id','entity_id','engagement_id']) <> '{}'::jsonb THEN
    RAISE EXCEPTION 'V39 execution binding refused';
  END IF;
  PERFORM (r->>'completed_at')::timestamptz;
  -- This call inserts a NEW analysis and envelope. Existing IDs fail: no retro-certification.
  -- Any later receipt failure rolls the entire function statement back.
  a := public.persist_governed_analysis_v1(p_analysis, p_envelope);
  INSERT INTO public.governed_execution_receipts
    (analysis_id, company_id, entity_id, engagement_id, execution_id, payload, sha256)
  VALUES (a, (r->>'company_id')::uuid, (r->>'entity_id')::uuid,
          (r->>'engagement_id')::uuid, (r->>'execution_id')::uuid, r, p_receipt->>'sha256');
  RETURN a;
END $$;
REVOKE ALL ON FUNCTION public.persist_governed_execution_v1(JSONB,JSONB,JSONB) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.persist_governed_execution_v1(JSONB,JSONB,JSONB) TO service_role;

COMMIT;
