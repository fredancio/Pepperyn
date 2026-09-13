-- Record authoritative origin for all new V33 correspondences.
-- Existing V33 rows remain readable but are explicitly unattested and cannot
-- enter governed provider projection.

ALTER TABLE public.pseudonymous_correspondence
  ADD COLUMN IF NOT EXISTS registration_version TEXT,
  ADD COLUMN IF NOT EXISTS registration_request_sha256 CHAR(64),
  ADD COLUMN IF NOT EXISTS registration_authority_sha256 CHAR(64),
  ADD COLUMN IF NOT EXISTS registration_source_receipt_sha256 CHAR(64);

ALTER TABLE public.pseudonymous_correspondence
  ADD CONSTRAINT pseudonymous_registration_version_valid
    CHECK (registration_version IS NULL OR registration_version = 'ownership-v1'),
  ADD CONSTRAINT pseudonymous_registration_request_hash_valid
    CHECK (registration_request_sha256 IS NULL OR registration_request_sha256 ~ '^[a-f0-9]{64}$'),
  ADD CONSTRAINT pseudonymous_registration_authority_hash_valid
    CHECK (registration_authority_sha256 IS NULL OR registration_authority_sha256 ~ '^[a-f0-9]{64}$'),
  ADD CONSTRAINT pseudonymous_registration_source_hash_valid
    CHECK (registration_source_receipt_sha256 IS NULL OR registration_source_receipt_sha256 ~ '^[a-f0-9]{64}$');

CREATE OR REPLACE FUNCTION public.require_authorized_correspondence_registration_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
  IF NEW.registration_version IS DISTINCT FROM 'ownership-v1'
     OR NEW.registration_request_sha256 IS NULL
     OR NEW.registration_authority_sha256 IS NULL
     OR NEW.registration_source_receipt_sha256 IS NULL THEN
    RAISE EXCEPTION 'authorized correspondence registration required';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_require_authorized_correspondence_registration_v1
  ON public.pseudonymous_correspondence;
CREATE TRIGGER trg_require_authorized_correspondence_registration_v1
  BEFORE INSERT ON public.pseudonymous_correspondence
  FOR EACH ROW EXECUTE FUNCTION public.require_authorized_correspondence_registration_v1();
