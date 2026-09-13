-- Durable encrypted correspondence registry. This migration opens neither
-- external-provider transport nor real-data admission.

CREATE TABLE IF NOT EXISTS public.pseudonymous_correspondence (
  id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  category TEXT NOT NULL CHECK (category ~ '^[A-Z][A-Z0-9_]{1,31}$'),
  pseudonym TEXT NOT NULL CHECK (pseudonym ~ '^[A-Z][A-Z0-9_]{1,31}-[A-F0-9]{16}$'),
  real_fingerprint CHAR(64) NOT NULL CHECK (real_fingerprint ~ '^[A-F0-9]{64}$'),
  encrypted_value TEXT NOT NULL CHECK (length(encrypted_value) >= 24),
  nonce TEXT NOT NULL CHECK (length(nonce) = 16),
  ciphertext_sha256 CHAR(64) NOT NULL CHECK (ciphertext_sha256 ~ '^[A-F0-9]{64}$'),
  crypto_version TEXT NOT NULL CHECK (crypto_version = 'v1-aes256gcm-hmacsha256'),
  mapping_version INTEGER NOT NULL CHECK (mapping_version = 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT pseudonymous_correspondence_entity_scope_fk
    FOREIGN KEY (entity_id, company_id)
    REFERENCES public.entities (id, company_id) ON DELETE RESTRICT,
  CONSTRAINT pseudonymous_correspondence_scope_id_unique
    UNIQUE (id, company_id, entity_id),
  CONSTRAINT pseudonymous_correspondence_real_unique
    UNIQUE (company_id, entity_id, category, real_fingerprint),
  CONSTRAINT pseudonymous_correspondence_alias_unique
    UNIQUE (company_id, entity_id, pseudonym)
);

CREATE TABLE IF NOT EXISTS public.pseudonymous_correspondence_bindings (
  correspondence_id UUID NOT NULL,
  analysis_id UUID NOT NULL,
  company_id UUID NOT NULL,
  entity_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (correspondence_id, analysis_id),
  CONSTRAINT pseudonymous_binding_correspondence_scope_fk
    FOREIGN KEY (correspondence_id, company_id, entity_id)
    REFERENCES public.pseudonymous_correspondence (id, company_id, entity_id) ON DELETE RESTRICT,
  CONSTRAINT pseudonymous_binding_analysis_scope_fk
    FOREIGN KEY (analysis_id, company_id, entity_id)
    REFERENCES public.analyses (id, company_id, entity_id) ON DELETE CASCADE
);

ALTER TABLE public.pseudonymous_correspondence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pseudonymous_correspondence_bindings ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.pseudonymous_correspondence
  FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE public.pseudonymous_correspondence_bindings
  FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT ON TABLE public.pseudonymous_correspondence TO service_role;
GRANT SELECT, INSERT ON TABLE public.pseudonymous_correspondence_bindings TO service_role;

CREATE OR REPLACE FUNCTION public.reject_pseudonymous_correspondence_update()
RETURNS trigger LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
  RAISE EXCEPTION 'pseudonymous correspondence is immutable';
END;
$$;

DROP TRIGGER IF EXISTS trg_reject_pseudonymous_correspondence_update
  ON public.pseudonymous_correspondence;
CREATE TRIGGER trg_reject_pseudonymous_correspondence_update
  BEFORE UPDATE ON public.pseudonymous_correspondence
  FOR EACH ROW EXECUTE FUNCTION public.reject_pseudonymous_correspondence_update();

CREATE OR REPLACE FUNCTION public.purge_pseudonymous_correspondence_v1(
  p_correspondence_id UUID,
  p_company_id UUID,
  p_entity_id UUID
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.pseudonymous_correspondence_bindings
    WHERE correspondence_id = p_correspondence_id
      AND company_id = p_company_id AND entity_id = p_entity_id
  ) THEN
    RAISE EXCEPTION 'correspondence retention required';
  END IF;
  DELETE FROM public.pseudonymous_correspondence
  WHERE id = p_correspondence_id
    AND company_id = p_company_id AND entity_id = p_entity_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'correspondence unavailable';
  END IF;
  RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION public.purge_pseudonymous_correspondence_v1(UUID, UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.purge_pseudonymous_correspondence_v1(UUID, UUID, UUID)
  TO service_role;

DO $$
BEGIN
  IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.pseudonymous_correspondence'::regclass)
     OR NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.pseudonymous_correspondence_bindings'::regclass) THEN
    RAISE EXCEPTION 'v33 convergence failed: RLS disabled';
  END IF;
END $$;
