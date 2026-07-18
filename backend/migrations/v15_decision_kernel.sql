-- v15_decision_kernel.sql
-- WP5C — Decision Kernel JSONB + colonne version dénormalisée
--
-- Contexte
-- --------
-- Le Decision Kernel dk-1 est la source de vérité unique des décisions Pepperyn.
-- Il est produit par l'extracteur déterministe (decision_kernel_extractor.py) depuis
-- un AnalysisResult post-pipeline, sérialisé en JSONB, et persisté dans cette colonne.
--
-- Schema du Kernel : SPEC-DK-001 Rev 3.1 (DESIGN FROZEN, 2026-07-17).
-- Version implémentée : dk-1. Versions futures (dk-2, dk-3...) utiliseront la même
-- colonne JSONB — decision_kernel_version permettra de distinguer les générations.
--
-- Colonnes ajoutées
-- -----------------
-- decision_kernel         : JSONB NULL — objet DecisionKernel dk-1 complet.
--                           NULL pour les analyses antérieures à WP5C (legacy).
--                           Jamais modifié après scellement (KERNEL-INV-001).
--
-- decision_kernel_version : TEXT NULL — valeur dénormalisée de
--                           decision_kernel->>'kernel_version' (ex: 'dk-1').
--                           Alimentée explicitement par l'application (analyze.py, Commit 5).
--                           Jamais 'dk-1' par défaut SQL — les analyses legacy restent NULL,
--                           distinction volontaire entre "pas de Kernel" et "Kernel dk-1".
--                           Permet les requêtes de migration futures sans parsing JSONB.
--
-- Politique de DEFAULT NULL
-- -------------------------
-- Aucune valeur par défaut non-NULL n'est définie sur ces colonnes.
-- Les analyses historiques conservent decision_kernel IS NULL et
-- decision_kernel_version IS NULL après exécution de cette migration.
-- Aucun backfill. Aucune modification des lignes existantes.
--
-- Idempotence
-- -----------
-- ADD COLUMN protégée par IF NOT EXISTS sur information_schema.columns.
-- Index protégés par CREATE INDEX IF NOT EXISTS.
-- Safe à ré-exécuter en cas de replay ou de redéploiement.
--
-- Index
-- -----
-- GIN partiel sur decision_kernel (WHERE NOT NULL) :
--   pour les requêtes @>, ?, ?| sur le contenu du Kernel
--   (Memory Service, Stability Suite, audits JSONB).
--
-- B-tree partiel sur decision_kernel_version (WHERE NOT NULL) :
--   pour les requêtes WHERE decision_kernel_version = 'dk-1'
--   utilisées lors des migrations et des analytics par version.
--   Partiel : n'indexe que les analyses qui ont effectivement un Kernel —
--   les lignes legacy (NULL) sont exclues de l'index, le maintenant minimal.
--
-- Impact sur les analyses historiques
-- ------------------------------------
-- Aucun. ALTER TABLE ... ADD COLUMN DEFAULT NULL est non-bloquant en PostgreSQL 11+
-- (pas de réécriture de table). Les analyses existantes gardent NULL sur les deux
-- colonnes. L'application lit decision_kernel avec un guard `if kernel is not None`.
--
-- Périmètre
-- ---------
-- Cette migration ne touche qu'à la table public.analyses.
-- Aucune politique RLS, aucun trigger, aucune autre table n'est modifié.

DO $$
BEGIN

  -- ── decision_kernel ───────────────────────────────────────────────────────────
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name   = 'analyses'
      AND column_name  = 'decision_kernel'
  ) THEN
    ALTER TABLE public.analyses ADD COLUMN decision_kernel JSONB DEFAULT NULL;
    COMMENT ON COLUMN public.analyses.decision_kernel IS
      'WP5C — Decision Kernel dk-1 sérialisé en JSONB. Source de vérité unique des décisions. '
      'NULL pour les analyses antérieures à WP5C. Jamais modifié après scellement (KERNEL-INV-001). '
      'Schema : SPEC-DK-001 Rev 3.1. Version : voir decision_kernel_version.';
  END IF;

  -- ── decision_kernel_version ───────────────────────────────────────────────────
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name   = 'analyses'
      AND column_name  = 'decision_kernel_version'
  ) THEN
    ALTER TABLE public.analyses ADD COLUMN decision_kernel_version TEXT DEFAULT NULL;
    COMMENT ON COLUMN public.analyses.decision_kernel_version IS
      'WP5C — Version dénormalisée du schéma Kernel (ex: ''dk-1'', ''dk-2''). '
      'Miroir de decision_kernel->>''kernel_version''. Alimentée explicitement par l''application. '
      'NULL pour les analyses sans Kernel. Jamais de DEFAULT ''dk-1'' au niveau SQL : '
      'la valeur NULL distingue l''absence de Kernel d''un Kernel dk-1.';
  END IF;

END $$;

-- ── Index GIN sur le contenu du Kernel (partiel) ─────────────────────────────
-- Opérateur : jsonb_ops (défaut — couvre @>, ?, ?|, ?&).
-- Partiel (WHERE NOT NULL) : exclut les lignes legacy sans Kernel.
-- Utilisé par : Memory Service, Stability Suite, audits @>.
CREATE INDEX IF NOT EXISTS idx_analyses_decision_kernel_gin
    ON public.analyses
    USING GIN (decision_kernel)
    WHERE decision_kernel IS NOT NULL;

-- ── Index B-tree partiel sur la version ──────────────────────────────────────
-- Partiel (WHERE NOT NULL) : n'indexe que les analyses ayant un Kernel actif.
-- Les analyses legacy (decision_kernel_version IS NULL) sont exclues.
-- Seules les analyses auxquelles l'application a explicitement persisté une version
-- (dk-1, dk-2...) figurent dans cet index — cohérent avec l'invariant "pas de
-- DEFAULT 'dk-1' au niveau SQL".
-- Utilisé par : WHERE decision_kernel_version = 'dk-1' (migrations, analytics).
CREATE INDEX IF NOT EXISTS idx_analyses_dk_version
    ON public.analyses (decision_kernel_version)
    WHERE decision_kernel_version IS NOT NULL;

-- ── ROLLBACK (ne pas exécuter en production — conservé pour référence) ────────
-- DROP INDEX IF EXISTS idx_analyses_dk_version;
-- DROP INDEX IF EXISTS idx_analyses_decision_kernel_gin;
-- ALTER TABLE public.analyses DROP COLUMN IF EXISTS decision_kernel_version;
-- ALTER TABLE public.analyses DROP COLUMN IF EXISTS decision_kernel;
