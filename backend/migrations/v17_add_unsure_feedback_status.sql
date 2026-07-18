-- v17_add_unsure_feedback_status.sql
-- fix(arc): BUG #ARC-001 — ajouter 'unsure' au CHECK constraint de decision_feedback
--
-- Contexte
-- --------
-- Le fix BUG #ARC-001 (commit 12730b8) a introduit un nouveau statut 'unsure'
-- pour distinguer "Je ne sais pas encore" (indécision) de "Je vais appliquer"
-- (intention = status='planned' → Arc créé).
--
-- La table decision_feedback a un CHECK constraint sur status qui listait
-- explicitement les valeurs valides. 'unsure' n'y figurait pas, ce qui provoquait
-- une violation de contrainte CHECK (erreur 23514) dès qu'un utilisateur
-- sélectionnait "Je ne sais pas encore" — détecté lors de la validation staging.
--
-- Correction
-- ----------
-- DROP de l'ancienne contrainte → ADD CONSTRAINT avec 'unsure' inclus.
-- Idempotente : vérifie l'existence avant de modifier.
-- Aucune donnée existante n'est affectée (0 lignes avec status='unsure' en DB).
--
-- Sémantique post-correction
-- --------------------------
--   'planned'            → intention ferme → Arc Décisionnel créé
--   'unsure'             → indécision      → feedback persisté, aucun Arc
--   'done'               → fait
--   'partially_done'     → partiellement fait
--   'not_done'           → pas fait
--   'rejected'           → rejeté
--   'no_longer_relevant' → non pertinent
--
-- Rollback
-- --------
-- ALTER TABLE public.decision_feedback
--   DROP CONSTRAINT decision_feedback_status_check;
-- ALTER TABLE public.decision_feedback
--   ADD CONSTRAINT decision_feedback_status_check
--   CHECK (status IN (
--     'planned', 'done', 'partially_done', 'not_done', 'rejected', 'no_longer_relevant'
--   ));

DO $$
BEGIN
  -- Supprimer l'ancienne contrainte (sans 'unsure')
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.decision_feedback'::regclass
      AND conname  = 'decision_feedback_status_check'
  ) THEN
    ALTER TABLE public.decision_feedback
      DROP CONSTRAINT decision_feedback_status_check;
  END IF;

  -- Ajouter la nouvelle contrainte (avec 'unsure')
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.decision_feedback'::regclass
      AND conname  = 'decision_feedback_status_check'
  ) THEN
    ALTER TABLE public.decision_feedback
      ADD CONSTRAINT decision_feedback_status_check
      CHECK (status IN (
        'planned',
        'unsure',
        'done',
        'partially_done',
        'not_done',
        'rejected',
        'no_longer_relevant'
      ));
  END IF;
END $$;
