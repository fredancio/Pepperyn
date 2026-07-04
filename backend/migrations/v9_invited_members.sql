-- v9_invited_members.sql
-- Table des membres invités (email associé à une entreprise)
-- Permet la connexion email + PIN pour les invités, sans créer de compte Supabase.
--
-- ⚙️  À exécuter dans Supabase SQL Editor (une seule fois, idempotent).

CREATE TABLE IF NOT EXISTS public.invited_members (
  id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id  UUID        REFERENCES public.companies(id) ON DELETE CASCADE NOT NULL,
  email       TEXT        NOT NULL,
  invited_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(company_id, email)   -- même email peut être invité dans plusieurs espaces (rare mais possible)
);

CREATE INDEX IF NOT EXISTS idx_invited_members_email   ON public.invited_members(email);
CREATE INDEX IF NOT EXISTS idx_invited_members_company ON public.invited_members(company_id);

-- RLS : l'admin de la company peut tout voir/modifier ; les guests ne voient rien.
ALTER TABLE public.invited_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "invited_members_admin_own"
  ON public.invited_members
  FOR ALL
  USING (
    company_id IN (
      SELECT id FROM public.companies WHERE admin_user_id = auth.uid()
    )
  );
