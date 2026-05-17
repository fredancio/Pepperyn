-- Migration v6 — Workspaces, Entités & bonus_analyses
-- À exécuter dans l'éditeur SQL Supabase :
--   https://supabase.com/dashboard/project/ljcqbwbjeoeiugcoxfcf/sql/new
-- Safe à ré-exécuter (IF NOT EXISTS / OR REPLACE / ADD COLUMN IF NOT EXISTS).
--
-- Ce que fait cette migration :
--   1. Ajoute bonus_analyses dans usage_limits (crédits Stripe)
--   2. Ajoute les colonnes manquantes (organisation, nom, user_type, usage_type) dans profiles
--   3. Crée les tables workspaces et entities
--   4. Remplace handle_new_user par une version complète qui crée
--      company + profile + workspace + entity en un seul trigger atomique
--   5. Rétro-crée workspace+entity pour les comptes existants


-- ============================================================
-- 1. COLONNE bonus_analyses dans usage_limits
-- ============================================================
ALTER TABLE public.usage_limits
  ADD COLUMN IF NOT EXISTS bonus_analyses INT DEFAULT 0;

COMMENT ON COLUMN public.usage_limits.bonus_analyses
  IS 'Analyses bonus achetées via add-ons Stripe, s''ajoutent au quota mensuel du plan.';


-- ============================================================
-- 2. COLONNES manquantes dans profiles
--    (organisation, nom, user_type, usage_type — collectés à l''inscription)
-- ============================================================
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS nom           TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS organisation  TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS user_type     TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS usage_type    TEXT DEFAULT '';


-- ============================================================
-- 3. TABLES workspaces & entities
-- ============================================================

-- Workspaces
CREATE TABLE IF NOT EXISTS public.workspaces (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id  UUID REFERENCES public.companies(id) ON DELETE CASCADE NOT NULL,
  name        TEXT NOT NULL DEFAULT 'Mon espace',
  is_default  BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workspaces_company_id
  ON public.workspaces(company_id);

-- Un seul workspace "default" par company
CREATE UNIQUE INDEX IF NOT EXISTS idx_workspaces_default_per_company
  ON public.workspaces(company_id)
  WHERE is_default = TRUE;

CREATE OR REPLACE TRIGGER update_workspaces_updated_at
  BEFORE UPDATE ON public.workspaces
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "workspaces_company_own" ON public.workspaces;
CREATE POLICY "workspaces_company_own" ON public.workspaces
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- Entities
CREATE TABLE IF NOT EXISTS public.entities (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id    UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  company_id      UUID REFERENCES public.companies(id)  ON DELETE CASCADE NOT NULL,
  name            TEXT NOT NULL DEFAULT 'Entité principale',
  industry        TEXT,
  business_model  TEXT,
  is_primary      BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_workspace_id
  ON public.entities(workspace_id);

CREATE INDEX IF NOT EXISTS idx_entities_company_id
  ON public.entities(company_id);

-- Une seule entité "primary" par workspace
CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_primary_per_workspace
  ON public.entities(workspace_id)
  WHERE is_primary = TRUE;

CREATE OR REPLACE TRIGGER update_entities_updated_at
  BEFORE UPDATE ON public.entities
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "entities_company_own" ON public.entities;
CREATE POLICY "entities_company_own" ON public.entities
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- ============================================================
-- 4. FONCTION handle_new_user (version complète v6)
--    Remplace la version v3 qui ne créait que le profil.
--    Crée en un seul trigger atomique :
--      - company (avec PIN aléatoire)
--      - profile (avec toutes les métadonnées d'inscription)
--      - workspace (nommé d'après l'organisation)
--      - entity (entité principale)
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_company_id   UUID;
  v_workspace_id UUID;
  v_random_pin   VARCHAR(4);
  v_org_name     TEXT;
  v_industry     TEXT;
  v_business_model TEXT;
BEGIN
  -- Extract metadata from Supabase Auth
  v_org_name       := COALESCE(NULLIF(NEW.raw_user_meta_data->>'organisation', ''), 'Mon entreprise');
  v_industry       := COALESCE(NEW.raw_user_meta_data->>'industry', '');
  v_business_model := COALESCE(NEW.raw_user_meta_data->>'business_model', '');

  -- Generate random 4-digit PIN
  v_random_pin := LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0');

  -- 1. Create company
  INSERT INTO public.companies (admin_user_id, pin_code, name, plan)
  VALUES (NEW.id, v_random_pin, v_org_name, 'free')
  RETURNING id INTO v_company_id;

  -- 2. Create profile
  INSERT INTO public.profiles (
    id, email, prenom, nom, company_id,
    industry, business_model,
    organisation, user_type, usage_type
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'prenom', ''),
    COALESCE(NEW.raw_user_meta_data->>'nom', ''),
    v_company_id,
    v_industry,
    v_business_model,
    v_org_name,
    COALESCE(NEW.raw_user_meta_data->>'user_type', ''),
    COALESCE(NEW.raw_user_meta_data->>'usage_type', '')
  )
  ON CONFLICT (id) DO UPDATE SET
    company_id     = COALESCE(EXCLUDED.company_id, profiles.company_id),
    industry       = COALESCE(NULLIF(EXCLUDED.industry, ''), profiles.industry),
    business_model = COALESCE(NULLIF(EXCLUDED.business_model, ''), profiles.business_model),
    organisation   = COALESCE(NULLIF(EXCLUDED.organisation, ''), profiles.organisation),
    nom            = COALESCE(NULLIF(EXCLUDED.nom, ''), profiles.nom),
    user_type      = COALESCE(NULLIF(EXCLUDED.user_type, ''), profiles.user_type),
    usage_type     = COALESCE(NULLIF(EXCLUDED.usage_type, ''), profiles.usage_type);

  -- 3. Create default workspace
  INSERT INTO public.workspaces (company_id, name, is_default)
  VALUES (v_company_id, v_org_name, TRUE)
  RETURNING id INTO v_workspace_id;

  -- 4. Create primary entity
  INSERT INTO public.entities (
    workspace_id, company_id, name,
    industry, business_model, is_primary
  )
  VALUES (
    v_workspace_id,
    v_company_id,
    COALESCE(NULLIF(v_org_name, 'Mon entreprise'), 'Entité principale'),
    NULLIF(v_industry, ''),
    NULLIF(v_business_model, ''),
    TRUE
  );

  RETURN NEW;
END;
$$;

-- Re-attach trigger (drop old, create new)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ============================================================
-- 5. RÉTRO-CRÉATION workspace + entity pour comptes existants
--    Idempotent — ne traite que les companies sans workspace.
-- ============================================================
DO $$
DECLARE
  rec            RECORD;
  v_workspace_id UUID;
BEGIN
  FOR rec IN
    SELECT
      c.id           AS company_id,
      c.name         AS company_name,
      p.organisation,
      p.industry,
      p.business_model
    FROM public.companies c
    LEFT JOIN public.profiles p ON p.company_id = c.id
    WHERE c.id NOT IN (SELECT company_id FROM public.workspaces)
  LOOP
    -- Create workspace
    INSERT INTO public.workspaces (company_id, name, is_default)
    VALUES (
      rec.company_id,
      COALESCE(NULLIF(rec.organisation, ''), rec.company_name, 'Mon espace'),
      TRUE
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_workspace_id;

    -- Create entity if workspace was inserted
    IF v_workspace_id IS NOT NULL THEN
      INSERT INTO public.entities (
        workspace_id, company_id, name,
        industry, business_model, is_primary
      )
      VALUES (
        v_workspace_id,
        rec.company_id,
        COALESCE(NULLIF(rec.organisation, ''), rec.company_name, 'Entité principale'),
        NULLIF(rec.industry, ''),
        NULLIF(rec.business_model, ''),
        TRUE
      )
      ON CONFLICT DO NOTHING;
    END IF;
  END LOOP;
END;
$$;


-- ============================================================
-- VÉRIFICATION
-- ============================================================
SELECT
  'workspaces' AS table_name,
  COUNT(*) AS rows
FROM public.workspaces
UNION ALL
SELECT
  'entities',
  COUNT(*)
FROM public.entities
UNION ALL
SELECT
  'usage_limits avec bonus_analyses',
  COUNT(*)
FROM public.usage_limits
WHERE bonus_analyses IS NOT NULL;
