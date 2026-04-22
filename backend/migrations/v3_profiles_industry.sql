-- Migration v3 — Ajout industry et business_model sur profiles
-- À exécuter dans l'éditeur SQL Supabase.
-- Safe à ré-exécuter (IF NOT EXISTS).


-- ─── 1. Colonnes sur profiles ────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'industry'
  ) THEN
    ALTER TABLE profiles ADD COLUMN industry TEXT DEFAULT '';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'business_model'
  ) THEN
    ALTER TABLE profiles ADD COLUMN business_model TEXT DEFAULT '';
  END IF;
END $$;


-- ─── 2. Trigger de création de profil ───────────────────────────────────────
-- Met à jour la fonction handle_new_user pour copier industry et business_model
-- depuis les metadata Supabase Auth vers la table profiles.
-- Si cette fonction n'existe pas encore dans votre projet, créez-la.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, prenom, industry, business_model)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'prenom', ''),
    COALESCE(NEW.raw_user_meta_data->>'industry', ''),
    COALESCE(NEW.raw_user_meta_data->>'business_model', '')
  )
  ON CONFLICT (id) DO UPDATE SET
    industry       = COALESCE(EXCLUDED.industry, profiles.industry),
    business_model = COALESCE(EXCLUDED.business_model, profiles.business_model);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recrée le trigger si besoin (safe : DROP IF EXISTS puis CREATE)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
