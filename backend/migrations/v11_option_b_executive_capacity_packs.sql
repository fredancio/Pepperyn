-- v11_option_b_executive_capacity_packs.sql
-- WP1C.2 : Executive Capacity Packs — Architecture Option B
--
-- Ajoute bonus_analyses_remaining sur companies comme propriété permanente du compte.
-- Indépendant des compteurs mensuels usage_limits.
-- La colonne n'est jamais remise à zéro.
-- Sur plan FREE : le solde est conservé mais suspendu (non consommable) jusqu'à
--   réactivation PRO / SCALE.
--
-- À exécuter dans Supabase SQL Editor.

ALTER TABLE public.companies
    ADD COLUMN IF NOT EXISTS bonus_analyses_remaining INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.companies.bonus_analyses_remaining
    IS 'Stock permanent d''analyses bonus Executive Capacity Packs. '
       'Indépendant des compteurs mensuels usage_limits. '
       'Jamais remis à zéro lors d''un reset mensuel. '
       'Suspendu (non consommable) sur plan FREE, conservé en base. '
       'Réactivé dès le passage en PRO / SCALE / ENTERPRISE.';

-- ─── ROLLBACK ────────────────────────────────────────────────────────────────
-- ALTER TABLE public.companies DROP COLUMN IF EXISTS bonus_analyses_remaining;
