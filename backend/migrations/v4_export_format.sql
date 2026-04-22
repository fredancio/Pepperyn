-- Migration v4 — Ajout export_format sur analyses
-- À exécuter dans l'éditeur SQL Supabase.
-- Safe à ré-exécuter (IF NOT EXISTS).

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'analyses' AND column_name = 'export_format'
  ) THEN
    ALTER TABLE analyses ADD COLUMN export_format TEXT DEFAULT NULL;
    COMMENT ON COLUMN analyses.export_format IS 'Format d''export choisi par l''utilisateur : excel | pdf | pptx. Un seul format possible par analyse.';
  END IF;
END $$;
