-- Separate source inspections, never canonical analyses. No real-data/provider admission.
-- Deployment requires an explicit integration-environment operation; not auto-run by app.
BEGIN;
CREATE TABLE public.synthetic_source_dossiers_v1 (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL,
  entity_id uuid NOT NULL,
  engagement_id uuid NOT NULL,
  schema_version text NOT NULL CHECK (schema_version = 'synthetic-source-dossier-1'),
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[A-F0-9]{64}$'),
  filename text NOT NULL,
  understanding jsonb NOT NULL CHECK (jsonb_typeof(understanding) = 'object'),
  payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[A-F0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (entity_id, company_id) REFERENCES public.entities(id, company_id) ON DELETE RESTRICT,
  FOREIGN KEY (engagement_id, entity_id) REFERENCES public.engagements(id, entity_id) ON DELETE RESTRICT,
  UNIQUE (company_id, entity_id, engagement_id, source_sha256, schema_version),
  CHECK ((source_sha256, filename) IN (
    ('FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93', 'pepperyn_v1_heterogeneous_english.xlsx'),
    ('8F35CF676B58BFF823CD423BDA70145A9951A55B9F689FF591282F3EAF9C6E51', 'pepperyn_v1_heterogeneous_ambiguous_period.xlsx'),
    ('E89851FF9AAF2FADA84F012CE7BDE846F859C7A62B1531F7C4F7F96A055F9E29', 'pepperyn_v1_heterogeneous_ambiguous_number.xlsx'),
    ('176F8F1A9E6A20B61E61C773AD54000D1D91E769B84C99BD2DA7B8ACB038D7E5', 'pepperyn_v1_heterogeneous_conflict.xlsx')
  ))
);
ALTER TABLE public.synthetic_source_dossiers_v1 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.synthetic_source_dossiers_v1 FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT ON public.synthetic_source_dossiers_v1 TO service_role;
CREATE FUNCTION public.reject_source_dossier_mutation_v1() RETURNS trigger
LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
  RAISE EXCEPTION 'source dossiers are immutable; no implicit resolution or deletion';
END;
$$;
CREATE TRIGGER synthetic_source_dossier_immutable
  BEFORE UPDATE OR DELETE ON public.synthetic_source_dossiers_v1
  FOR EACH ROW EXECUTE FUNCTION public.reject_source_dossier_mutation_v1();
COMMIT;
-- No data backfill, legacy Evidence Ledger rewrite, or automatic production migration.
-- Before any future purge/retention implementation, define authorized lifecycle explicitly.
