-- Immutable V1 governed analysis persistence. This migration does not open
-- provider or real-data admission and grants no client-facing table policy.

DO $$
DECLARE
  v_bad_columns integer;
BEGIN
  SELECT count(*) INTO v_bad_columns
  FROM (VALUES
    ('analyses', 'id'), ('analyses', 'company_id'), ('analyses', 'entity_id'),
    ('entities', 'id'), ('entities', 'company_id'),
    ('engagements', 'id'), ('engagements', 'entity_id')
  ) AS required(table_name, column_name)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = required.table_name
      AND c.column_name = required.column_name AND c.data_type = 'uuid'
  );
  IF v_bad_columns <> 0 THEN
    RAISE EXCEPTION 'v27 preflight failed: expected UUID scope columns are absent or incompatible';
  END IF;
END $$;

DO $$
DECLARE
  v_columns integer;
BEGIN
  IF to_regclass('public.governed_analysis_envelopes') IS NOT NULL THEN
    SELECT count(*) INTO v_columns FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'governed_analysis_envelopes'
      AND column_name IN (
        'analysis_id','company_id','entity_id','engagement_id','envelope_json','envelope_sha256',
        'binding_sha256','source_representation_sha256','envelope_schema_version','created_at'
      );
    IF v_columns <> 10 THEN
      RAISE EXCEPTION 'v27 preflight failed: partial governed envelope table';
    END IF;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_analyses_id_company_entity
  ON public.analyses (id, company_id, entity_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_id_company
  ON public.entities (id, company_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_engagements_id_entity
  ON public.engagements (id, entity_id);

CREATE TABLE IF NOT EXISTS public.governed_analysis_envelopes (
  analysis_id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  envelope_json JSONB NOT NULL,
  envelope_sha256 CHAR(64) NOT NULL CHECK (envelope_sha256 ~ '^[A-F0-9]{64}$'),
  binding_sha256 CHAR(64) NOT NULL CHECK (binding_sha256 ~ '^[A-F0-9]{64}$'),
  source_representation_sha256 CHAR(64) NOT NULL CHECK (source_representation_sha256 ~ '^[A-F0-9]{64}$'),
  envelope_schema_version TEXT NOT NULL CHECK (envelope_schema_version = 'v1-governed-analysis-1'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT governed_analysis_analysis_scope_fk
    FOREIGN KEY (analysis_id, company_id, entity_id)
    REFERENCES public.analyses (id, company_id, entity_id) ON DELETE CASCADE,
  CONSTRAINT governed_analysis_entity_scope_fk
    FOREIGN KEY (entity_id, company_id)
    REFERENCES public.entities (id, company_id) ON DELETE RESTRICT,
  CONSTRAINT governed_analysis_engagement_scope_fk
    FOREIGN KEY (engagement_id, entity_id)
    REFERENCES public.engagements (id, entity_id) ON DELETE RESTRICT
);

DO $$
DECLARE
  v_exact_columns integer;
  v_required_constraints integer;
BEGIN
  SELECT count(*) INTO v_exact_columns
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = 'governed_analysis_envelopes'
    AND (
      (column_name IN ('analysis_id','company_id','entity_id','engagement_id') AND data_type = 'uuid' AND is_nullable = 'NO')
      OR (column_name = 'envelope_json' AND data_type = 'jsonb' AND is_nullable = 'NO')
      OR (column_name IN ('envelope_sha256','binding_sha256','source_representation_sha256')
          AND data_type = 'character' AND character_maximum_length = 64 AND is_nullable = 'NO')
      OR (column_name = 'envelope_schema_version' AND data_type = 'text' AND is_nullable = 'NO')
      OR (column_name = 'created_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO')
    );
  IF v_exact_columns <> 10 THEN
    RAISE EXCEPTION 'v27 convergence failed: governed envelope column contract mismatch';
  END IF;

  SELECT count(*) INTO v_required_constraints
  FROM pg_constraint
  WHERE conrelid = 'public.governed_analysis_envelopes'::regclass
    AND conname IN (
      'governed_analysis_envelopes_pkey',
      'governed_analysis_analysis_scope_fk',
      'governed_analysis_entity_scope_fk',
      'governed_analysis_engagement_scope_fk',
      'governed_analysis_envelopes_envelope_sha256_check',
      'governed_analysis_envelopes_binding_sha256_check',
      'governed_analysis_envelopes_source_representation_sha256_check',
      'governed_analysis_envelopes_envelope_schema_version_check'
    );
  IF v_required_constraints <> 8 THEN
    RAISE EXCEPTION 'v27 convergence failed: governed envelope constraint contract mismatch';
  END IF;
END $$;

ALTER TABLE public.governed_analysis_envelopes ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.reject_governed_analysis_update()
RETURNS trigger LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
  RAISE EXCEPTION 'governed analysis envelopes are immutable';
END;
$$;

DROP TRIGGER IF EXISTS trg_reject_governed_analysis_update ON public.governed_analysis_envelopes;
CREATE TRIGGER trg_reject_governed_analysis_update
  BEFORE UPDATE ON public.governed_analysis_envelopes
  FOR EACH ROW EXECUTE FUNCTION public.reject_governed_analysis_update();

CREATE OR REPLACE FUNCTION public.persist_governed_analysis_v1(
  p_analysis JSONB,
  p_envelope JSONB
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_analysis_id UUID := (p_analysis->>'id')::UUID;
  v_company_id UUID := (p_analysis->>'company_id')::UUID;
  v_entity_id UUID := (p_analysis->>'entity_id')::UUID;
  v_engagement_id UUID := (p_envelope->>'engagement_id')::UUID;
BEGIN
  IF v_analysis_id IS DISTINCT FROM (p_envelope->>'analysis_id')::UUID
     OR v_company_id IS DISTINCT FROM (p_envelope->>'company_id')::UUID
     OR v_entity_id IS DISTINCT FROM (p_envelope->>'entity_id')::UUID THEN
    RAISE EXCEPTION 'governed analysis scope mismatch';
  END IF;

  INSERT INTO public.analyses (
    id, company_id, entity_id, fichier_nom, fichier_type, type_document,
    contexte_utilisateur, mode, analyse_json, score_confiance, tokens_input,
    cout_estime_euros, duree_traitement_ms, status, chat_count, session_id,
    fichier_taille_bytes, source_data_hash
  ) VALUES (
    v_analysis_id, v_company_id, v_entity_id, p_analysis->>'fichier_nom',
    p_analysis->>'fichier_type', p_analysis->>'type_document',
    p_analysis->>'contexte_utilisateur', p_analysis->>'mode', p_analysis->'analyse_json',
    COALESCE((p_analysis->>'score_confiance')::INT, 0),
    COALESCE((p_analysis->>'tokens_input')::INT, 0),
    COALESCE((p_analysis->>'cout_estime_euros')::NUMERIC, 0),
    COALESCE((p_analysis->>'duree_traitement_ms')::INT, 0),
    COALESCE(p_analysis->>'status', 'completed'), COALESCE((p_analysis->>'chat_count')::INT, 0),
    NULLIF(p_analysis->>'session_id', '')::UUID,
    NULLIF(p_analysis->>'fichier_taille_bytes', '')::BIGINT,
    p_analysis->>'source_data_hash'
  );

  INSERT INTO public.governed_analysis_envelopes (
    analysis_id, company_id, entity_id, engagement_id, envelope_json, envelope_sha256,
    binding_sha256, source_representation_sha256, envelope_schema_version
  ) VALUES (
    v_analysis_id, v_company_id, v_entity_id, v_engagement_id, p_envelope->'envelope_json',
    p_envelope->>'envelope_sha256', p_envelope->>'binding_sha256',
    p_envelope->>'source_representation_sha256', p_envelope->>'envelope_schema_version'
  );
  RETURN v_analysis_id;
END;
$$;

REVOKE ALL ON FUNCTION public.persist_governed_analysis_v1(JSONB, JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.persist_governed_analysis_v1(JSONB, JSONB) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.persist_governed_analysis_v1(JSONB, JSONB) TO service_role;

DO $$
BEGIN
  IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.governed_analysis_envelopes'::regclass) THEN
    RAISE EXCEPTION 'v27 convergence failed: RLS is disabled';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid = 'public.governed_analysis_envelopes'::regclass
      AND tgname = 'trg_reject_governed_analysis_update' AND NOT tgisinternal
  ) THEN
    RAISE EXCEPTION 'v27 convergence failed: immutability trigger missing';
  END IF;
END $$;
