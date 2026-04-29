-- Migration v5 — Mémoire persistante structurée
-- À exécuter dans l'éditeur SQL Supabase :
--   https://supabase.com/dashboard/project/ljcqbwbjeoeiugcoxfcf/sql/new
-- Safe à ré-exécuter (IF NOT EXISTS / OR REPLACE).

-- ============================================================
-- TABLE : financial_metrics
-- Métriques financières extraites de chaque analyse.
-- Permet de calculer des tendances sans parser du JSON.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.financial_metrics (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id     UUID REFERENCES public.companies(id) ON DELETE CASCADE NOT NULL,
  analyse_id     UUID REFERENCES public.analyses(id)  ON DELETE CASCADE NOT NULL,

  -- Métriques numériques extraites
  revenue        NUMERIC(18, 2),          -- Chiffre d'affaires total
  costs          NUMERIC(18, 2),          -- Coûts totaux
  margin_pct     NUMERIC(8,  4),          -- Marge nette en %
  gross_margin_pct NUMERIC(8, 4),         -- Marge brute en %
  ebitda         NUMERIC(18, 2),          -- EBITDA si disponible

  -- Scores qualitatifs (0-10)
  score_rentabilite  SMALLINT,
  score_risque       SMALLINT,
  score_structure    SMALLINT,

  -- Texte structuré
  document_type      TEXT,
  decision           TEXT,                -- Décision principale recommandée
  problemes          JSONB DEFAULT '[]',  -- Liste des problèmes critiques
  opportunites       JSONB DEFAULT '[]',  -- Liste des opportunités
  plan_action        JSONB DEFAULT '[]',  -- Actions recommandées

  created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_financial_metrics_company_id
  ON public.financial_metrics(company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_metrics_analyse_id
  ON public.financial_metrics(analyse_id);

-- RLS : chaque entreprise ne voit que ses métriques
ALTER TABLE public.financial_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "financial_metrics_company_own" ON public.financial_metrics
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- ============================================================
-- TABLE : company_profile
-- Profil évolutif de l'entreprise, mis à jour après chaque analyse.
-- Une seule ligne par entreprise (upsert).
-- ============================================================
CREATE TABLE IF NOT EXISTS public.company_profile (
  company_id     UUID REFERENCES public.companies(id) ON DELETE CASCADE PRIMARY KEY,

  -- Profil métier
  industry           TEXT,               -- Secteur d'activité détecté
  company_size       TEXT,               -- PME / ETI / Startup / etc.

  -- Tendances calculées
  margin_trend       TEXT DEFAULT 'stable',  -- 'improving' | 'declining' | 'stable'
  revenue_trend      TEXT DEFAULT 'stable',
  avg_score_rentabilite  NUMERIC(5, 2),
  avg_score_risque       NUMERIC(5, 2),

  -- Mémoire qualitative
  recurring_problems JSONB DEFAULT '[]',  -- Problèmes qui reviennent régulièrement
  pending_actions    JSONB DEFAULT '[]',  -- Actions en cours / non résolues
  strengths          JSONB DEFAULT '[]',  -- Points forts récurrents

  -- Compteurs
  total_analyses     INTEGER DEFAULT 0,
  last_analysis_at   TIMESTAMP WITH TIME ZONE,

  -- Résumé narratif généré automatiquement
  financial_summary  TEXT,

  created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_company_profile_updated_at
  BEFORE UPDATE ON public.company_profile
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- RLS
ALTER TABLE public.company_profile ENABLE ROW LEVEL SECURITY;

CREATE POLICY "company_profile_own" ON public.company_profile
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- ============================================================
-- VÉRIFICATION
-- ============================================================
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('financial_metrics', 'company_profile');
