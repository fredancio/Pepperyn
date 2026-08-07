-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v20 : handle_new_user() amendée — T2A (Engagement Foundation)
-- Fonction : handle_new_user() (CREATE OR REPLACE, ne modifie aucune table)
--
-- Fondation : ADR-002 — Engagement Foundation (statut ACCEPTED).
-- Plan d'implémentation : docs/Architecture/blueprint/T2A_Implementation_Plan.md
--   (v2, amendé) §3, §5 — chemin d'inscription.
-- Dépend de : v19_engagements.sql (table engagements doit exister avant cette
--   migration, puisque le corps de la fonction y insère une ligne).
--
-- Pourquoi une nouvelle migration plutôt qu'une édition de v6 en place :
--   Convention déjà établie dans ce dépôt — v6_workspaces_entities.sql avait
--   elle-même intégralement remplacé la version de handle_new_user() définie
--   par v3_profiles_industry.sql, via CREATE OR REPLACE FUNCTION dans un
--   nouveau fichier, sans jamais modifier v3 en place. Une migration déjà
--   appliquée en production reste le témoin historique exact de ce qui a été
--   exécuté ; elle ne se réécrit pas. Voir T2A_Implementation_Plan.md §3.
--
-- Ce que fait cette migration :
--   Reprend intégralement le corps de handle_new_user() tel qu'il existe
--   dans v6 (company + profile + workspace + entity), et y ajoute une 5e
--   étape : la création de l'Engagement de l'entité primaire nouvellement
--   créée. Aucune des quatre étapes existantes n'est modifiée.
--
-- Statut initial : toujours 'prospect'. Une Entity qui vient d'être créée ne
--   peut, par construction, avoir aucune Analysis existante (ADR-002 §3.5,
--   T2A_Implementation_Plan.md §6) — aucune requête sur la table analyses
--   n'est donc nécessaire ici, contrairement au backfill historique.
--
-- Garantie transactionnelle : l'INSERT sur engagements est ajouté à
--   l'intérieur de la même fonction PL/pgSQL que les inserts existants —
--   même transaction Postgres, par construction native, sans mécanisme
--   distinct à concevoir (même principe que create_entity_with_engagement,
--   v19, pour le chemin applicatif).
--
-- Ce que cette migration NE fait PAS :
--   - Ne modifie ni entities, ni workspaces, ni companies, ni profiles
--     (schéma inchangé pour ces quatre tables).
--   - Ne touche pas au trigger on_auth_user_created (déjà attaché depuis v6,
--     réattaché ici uniquement parce que v6 le faisait déjà de façon
--     idempotente — DROP TRIGGER IF EXISTS / CREATE TRIGGER, sans effet si
--     déjà présent à l'identique).
--
-- Rollback : écrire une future migration qui redéclare handle_new_user()
--   avec le corps exact de v6 (sans l'étape Engagement), via
--   CREATE OR REPLACE FUNCTION — pas de migration descendante automatique
--   dans ce dépôt (T2A_Implementation_Plan.md §10). entities et les autres
--   tables existantes ne sont, dans les deux sens, jamais touchées
--   structurellement.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_company_id     UUID;
  v_workspace_id   UUID;
  v_entity_id      UUID;
  v_random_pin     VARCHAR(4);
  v_org_name       TEXT;
  v_industry       TEXT;
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
  )
  RETURNING id INTO v_entity_id;

  -- 5. Create Engagement for the primary entity (T2A, ADR-002)
  --    Toujours 'prospect' : une Entity qui vient d'être créée ne peut avoir
  --    aucune Analysis existante (voir note en tête de fichier).
  INSERT INTO public.engagements (entity_id, status, cadence)
  VALUES (v_entity_id, 'prospect', 'mensuelle');

  RETURN NEW;
END;
$$;

-- Re-attach trigger (idempotent — drop old, create new).
-- Identique à v6 : ce trigger existe déjà, cette instruction est un no-op
-- fonctionnel si déjà présent, conservée pour l'idempotence de la migration.
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ── Fin migration v20 ────────────────────────────────────────────────────────
