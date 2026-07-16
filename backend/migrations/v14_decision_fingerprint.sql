-- v14_decision_fingerprint.sql
-- WP5A — Decision Fingerprint + Source Data Hash
--
-- Contexte
-- --------
-- Un Decision Fingerprint est un signal d'identité décisionnelle, pas un test de
-- stabilité. Il permet d'identifier si deux analyses ont produit les mêmes conclusions
-- (urgence, scores, problèmes prioritaires). La Stability Suite (WP5B+) comparera
-- les champs bruts avec leurs tolérances explicites (ICD-001 : ±1 point, même urgence,
-- mêmes catégories de problèmes). Le fingerprint n'est PAS le verdict ICD-001.
--
-- Limite connue du binning v1
-- ---------------------------
-- Un score à la frontière d'une tranche (ex. 3→4 : FAIBLE→MOYEN) produira des
-- fingerprints différents, même si la variation est dans la tolérance ICD-001 (±1).
-- C'est documenté et attendu : le fingerprint est une identité, pas une tolérance.
--
-- Colonnes ajoutées
-- -----------------
-- decision_fingerprint         : SHA-256[:32] (128 bits) des champs décisionnels binned.
--                                Calculé une seule fois à la création, jamais recalculé.
--                                Format : 32 caractères hexadécimaux.
-- decision_fingerprint_version : "v1". Permet de filtrer les comparaisons par version
--                                d'algorithme. Deux fingerprints de versions différentes
--                                ne doivent jamais être comparés directement.
-- source_data_hash             : SHA-256(file_bytes bruts, 64 hex chars).
--                                Identifie le fichier octet pour octet — pas encore les
--                                données financières canoniques. Un même fichier Excel
--                                resauvegardé sans modification peut produire un hash
--                                différent si les métadonnées Office changent.
--                                Distinct et indépendant du decision_fingerprint.
--                                Le normalized_data_hash (contenu parsé) reste hors WP5A.
--
-- Idempotence
-- -----------
-- IF NOT EXISTS sur chaque colonne et sur l'index. Safe à ré-exécuter.
--
-- Rétrocompatibilité
-- ------------------
-- DEFAULT NULL sur toutes les colonnes. Les lignes historiques restent NULL, c'est prévu.
-- Aucun NOT NULL. Aucun backfill dans cette migration. Le NOT NULL sera ajouté en v15
-- après vérification de la couverture sur la production.

DO $$
BEGIN

  -- ── decision_fingerprint ─────────────────────────────────────────────────────
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name  = 'analyses'
      AND column_name = 'decision_fingerprint'
  ) THEN
    ALTER TABLE public.analyses ADD COLUMN decision_fingerprint TEXT DEFAULT NULL;
    COMMENT ON COLUMN public.analyses.decision_fingerprint IS
      'FIN-001 — SHA-256[:32] (128 bits) de {v, urgence, scores_binned, top3_problèmes_triés}. '
      'Calculé une fois à la création, jamais recalculé. '
      'Signal d''identité décisionnelle — pas un verdict ICD-001. '
      'Une variation ±1 à la frontière d''une tranche peut produire un fingerprint différent. '
      'La Stability Suite (WP5B+) gère les tolérances sur les champs bruts.';
  END IF;

  -- ── decision_fingerprint_version ─────────────────────────────────────────────
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name  = 'analyses'
      AND column_name = 'decision_fingerprint_version'
  ) THEN
    ALTER TABLE public.analyses ADD COLUMN decision_fingerprint_version TEXT DEFAULT NULL;
    COMMENT ON COLUMN public.analyses.decision_fingerprint_version IS
      'Version de l''algorithme de fingerprint : "v1", "v2", … '
      'Ne jamais comparer directement des fingerprints de versions différentes. '
      'L''index composite (version, fingerprint) impose cet invariant au niveau requête.';
  END IF;

  -- ── source_data_hash ─────────────────────────────────────────────────────────
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name  = 'analyses'
      AND column_name = 'source_data_hash'
  ) THEN
    ALTER TABLE public.analyses ADD COLUMN source_data_hash TEXT DEFAULT NULL;
    COMMENT ON COLUMN public.analyses.source_data_hash IS
      'SHA-256(file_bytes bruts) — 64 caractères hexadécimaux. '
      'Identité du fichier source octet pour octet. Distinct du decision_fingerprint '
      '(données sources ≠ conclusions décisionnelles). '
      'Limite v1 : sensible aux métadonnées Office (resauvegarde sans modification '
      'peut changer ce hash). Le normalized_data_hash viendra en v2.';
  END IF;

END $$;

-- ── Index composite (version, fingerprint) ────────────────────────────────────
-- Justification : garantit qu'une requête de comparaison de fingerprints s'appuie
-- toujours sur la version, évitant les comparaisons accidentelles entre algorithmes.
-- Utilisé par les futures requêtes de la Stability Suite (WP5B+) :
--   WHERE decision_fingerprint_version = 'v1' AND decision_fingerprint = $1
-- Partiel (WHERE NOT NULL) : exclut les lignes historiques NULL — index minimal.
CREATE INDEX IF NOT EXISTS idx_analyses_decision_fingerprint
  ON public.analyses (decision_fingerprint_version, decision_fingerprint)
  WHERE decision_fingerprint IS NOT NULL;

-- ── ROLLBACK (ne pas exécuter en production — conservé pour référence) ─────────
-- DROP INDEX IF EXISTS idx_analyses_decision_fingerprint;
-- ALTER TABLE public.analyses DROP COLUMN IF EXISTS source_data_hash;
-- ALTER TABLE public.analyses DROP COLUMN IF EXISTS decision_fingerprint_version;
-- ALTER TABLE public.analyses DROP COLUMN IF EXISTS decision_fingerprint;
