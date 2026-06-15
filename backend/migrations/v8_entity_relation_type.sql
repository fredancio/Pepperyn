-- Migration v8 — Type de relation des entités secondaires
-- À exécuter dans l'éditeur SQL Supabase :
--   https://supabase.com/dashboard/project/ljcqbwbjeoeiugcoxfcf/sql/new
-- Safe à ré-exécuter (ADD COLUMN IF NOT EXISTS).
--
-- Contexte :
--   Une entité secondaire (is_primary = FALSE) peut représenter soit :
--     - une FILIALE de l'entité principale (groupe / holding) → l'analyse
--       doit situer son poids et son risque au niveau du groupe.
--     - un CLIENT suivi par l'utilisateur (expert-comptable, fractional CFO)
--       → l'analyse doit aider à évaluer la relation avec ce client.
--
--   NULL = non renseigné (entité principale, ou entité créée avant cette
--   migration) → aucun changement de comportement.

ALTER TABLE public.entities
  ADD COLUMN IF NOT EXISTS relation_type TEXT;

ALTER TABLE public.entities
  DROP CONSTRAINT IF EXISTS entities_relation_type_check;

ALTER TABLE public.entities
  ADD CONSTRAINT entities_relation_type_check
  CHECK (relation_type IS NULL OR relation_type IN ('filiale', 'client'));

COMMENT ON COLUMN public.entities.relation_type
  IS 'Type de relation de l''entité secondaire avec l''entité principale : '
     '"filiale" (filiale du groupe) ou "client" (client suivi par l''utilisateur). '
     'NULL pour l''entité principale ou si non renseigné.';


-- ============================================================
-- VÉRIFICATION
-- ============================================================
SELECT id, name, is_primary, relation_type
FROM public.entities
ORDER BY is_primary DESC, created_at;
