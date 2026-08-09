-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v25 : Knowledge Model v0 — protection structurelle du branchement
-- Table : knowledge_model
-- Contrainte : UNIQUE(relates_to_knowledge_id)
--
-- Contexte : revue adversariale indépendante pré-fusion de
--   implementation/knowledge-model-v0-2026-08-08 (commit e2cf588), verdict
--   B — MERGE AFTER SMALL CORRECTIONS. Constat : confirm() protège le
--   branchement par une vérification applicative SELECT-puis-INSERT, en
--   deux appels PostgREST séparés, sans verrouillage entre les deux — deux
--   appels confirm() concurrents (ou un simple double-clic/retry réseau
--   sur la même confirmation) peuvent tous deux lire "aucun successeur"
--   puis insérer chacun une ligne relates_to_knowledge_id = même
--   prédécesseur, produisant deux têtes de chaîne concurrentes. Ce risque
--   est réel, pas seulement théorique — voir le rapport de revue.
--
-- Correction, exactement la portée autorisée (rien de plus) :
--   une connaissance CONFIRMED donnée ne peut avoir qu'UN SEUL successeur
--   direct. Garantie relationnelle minimale : contrainte UNIQUE sur
--   relates_to_knowledge_id. Postgres traite chaque NULL comme distinct
--   dans une contrainte UNIQUE (NULL <> NULL) — les lignes racines
--   (relates_to_knowledge_id IS NULL, un nouveau sujet jamais encore
--   confirmé) restent illimitées, seules les valeurs non-NULL (un
--   prédécesseur donné) sont contraintes à l'unicité.
--
-- Ce que cette migration N'AJOUTE PAS (hors périmètre, mission explicite) :
--   - Aucune transaction applicative, aucun verrouillage distribué.
--   - Aucun arbitrage par confirmed_at — RECALL (services/
--     knowledge_model_service.py) reste inchangé, sa détection fail-safe
--     d'un branchement historique/corrompu (KnowledgeChainIntegrityError
--     si plusieurs têtes) reste la défense en profondeur, désormais
--     appuyée par cette contrainte qui empêche la création même du cas
--     qu'elle détectait auparavant après coup.
--   - Aucune table, aucun statut, aucun champ métier nouveau.
--   - Aucun renforcement cross-Entity / cross-subject au niveau DB
--     (recommandation non bloquante de la revue, explicitement hors
--     périmètre de cette mission).
--
-- Comportement observable : la seconde tentative de deux confirm()
-- concurrents (ou un double-submit séquentiel non protégé par le garde
-- applicatif, ex. contournement direct de la table) échoue désormais avec
-- une violation de contrainte UNIQUE Postgres, plutôt que de réussir
-- silencieusement à créer une seconde tête de chaîne. C'est une garantie
-- DB, indépendante du service et de la politique RLS de cette table.
--
-- Rollback : ALTER TABLE public.knowledge_model
--              DROP CONSTRAINT knowledge_model_one_successor_per_predecessor;
--            (aucune autre table, aucune donnée existante n'est touchée)
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.knowledge_model
  ADD CONSTRAINT knowledge_model_one_successor_per_predecessor
  UNIQUE (relates_to_knowledge_id);

COMMENT ON CONSTRAINT knowledge_model_one_successor_per_predecessor
  ON public.knowledge_model IS
  'Au plus un successeur CONFIRMED direct par prédécesseur (revue '
  'adversariale pré-fusion, verdict B, correction bloquante #1). Empêche '
  'structurellement le branchement — deux confirm() concurrents sur le '
  'même prédécesseur ne peuvent plus produire deux têtes de chaîne. '
  'NULL (ligne racine) reste illimité — seule une valeur non-NULL '
  'donnée est contrainte à l''unicité (sémantique standard Postgres '
  'UNIQUE sur colonne nullable).';

-- ── Fin migration v25 ────────────────────────────────────────────────────────
