-- Migration v7 — Decision Memory (mémoire comportementale utilisateur)
-- À exécuter dans l'éditeur SQL Supabase :
--   https://supabase.com/dashboard/project/ljcqbwbjeoeiugcoxfcf/sql/new
-- Safe à ré-exécuter (IF NOT EXISTS).
--
-- Objectif : suivre le cycle Recommandation → décision utilisateur →
-- exécution → feedback → résultat → adaptation des prochaines recommandations.
--
-- Cette migration NE MODIFIE PAS la table `analyses` ni le format des
-- rapports (`analyse_json`). Les recommandations restent des chaînes de
-- texte ; un `recommendation_id` déterministe (calculé côté backend à
-- partir de analyse_id + source + index) sert de clé de référence ici.


-- ============================================================
-- TABLE : decision_feedback
-- Une ligne = l'intention/le retour de l'utilisateur sur UNE
-- recommandation d'UN rapport donné.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.decision_feedback (
  id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id           UUID REFERENCES public.companies(id) ON DELETE CASCADE NOT NULL,
  user_id              UUID REFERENCES public.profiles(id)  ON DELETE SET NULL,
  -- NULL si le feedback vient d'un accès invité (PIN)

  report_id            UUID REFERENCES public.analyses(id)  ON DELETE CASCADE NOT NULL,
  -- Alias explicite demandé : report_id = analyses.id

  recommendation_id    TEXT NOT NULL,
  -- Identifiant déterministe : sha1(f"{report_id}:{source}:{index}")[:12]

  recommendation_text  TEXT NOT NULL,
  -- Snapshot du texte de la recommandation au moment du feedback
  -- (traçabilité même si le libellé évoluait dans une future version)

  recommendation_source TEXT,
  -- 'plan_action' | 'plan_action_haute' | 'plan_action_secondaire' | 'recommandations'

  status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
    'planned', 'done', 'partially_done', 'not_done', 'rejected', 'no_longer_relevant'
  )),

  comment TEXT,
  -- Réponse courte à "Pourquoi ?" / "Que s'est-il passé ?"

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Une seule ligne par (rapport, recommandation) — upsert sur évolution du statut
  UNIQUE (report_id, recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_decision_feedback_company_id
  ON public.decision_feedback(company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_feedback_report_id
  ON public.decision_feedback(report_id);

CREATE TRIGGER update_decision_feedback_updated_at
  BEFORE UPDATE ON public.decision_feedback
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- RLS : chaque entreprise ne voit que ses propres feedbacks
ALTER TABLE public.decision_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "decision_feedback_company_own" ON public.decision_feedback
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- ============================================================
-- TABLE : user_patterns
-- Une ligne par entreprise — patterns comportementaux calculés
-- à partir de decision_feedback (SQL/backend, PAS d'appel IA).
-- Schéma créé dès la Phase 1 ; alimenté à partir de la Phase 2.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.user_patterns (
  company_id    UUID REFERENCES public.companies(id) ON DELETE CASCADE PRIMARY KEY,

  execution_rate                 NUMERIC(5, 2),  -- % global de recommandations exécutées
  pricing_execution_rate         NUMERIC(5, 2),  -- % exécuté pour les actions de type "pricing"
  pricing_resistance_score       NUMERIC(5, 2),  -- 0-100 : résistance aux hausses tarifaires
  cost_reduction_execution_rate  NUMERIC(5, 2),
  revenue_action_execution_rate  NUMERIC(5, 2),

  average_delay_to_execution_days NUMERIC(6, 2),
  -- Délai moyen entre la recommandation et le passage à "done"

  recurring_blockers  JSONB DEFAULT '[]',
  -- Liste des motifs de blocage qui reviennent (issus du champ `comment`)

  preferred_action_type TEXT,
  -- Catégorie d'action la plus souvent passée à "done"

  total_feedback_count INTEGER DEFAULT 0,

  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_user_patterns_updated_at
  BEFORE UPDATE ON public.user_patterns
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- RLS
ALTER TABLE public.user_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_patterns_company_own" ON public.user_patterns
  FOR ALL USING (
    company_id IN (SELECT id FROM public.companies WHERE admin_user_id = auth.uid())
  );


-- ============================================================
-- VÉRIFICATION
-- ============================================================
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('decision_feedback', 'user_patterns');
