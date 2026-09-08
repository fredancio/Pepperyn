-- v28 — Restore the Decision Feedback registry required by the governed V1
-- intention rehearsal.
--
-- This migration is deliberately narrow and idempotent. It does not create a
-- DecisionArc, backfill an intention, or alter analyses/governed envelopes.

CREATE TABLE IF NOT EXISTS public.decision_feedback (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  report_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
  recommendation_id TEXT NOT NULL,
  recommendation_text TEXT NOT NULL,
  recommendation_source TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT decision_feedback_report_recommendation_key
    UNIQUE (report_id, recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_decision_feedback_company_id
  ON public.decision_feedback(company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_feedback_report_id
  ON public.decision_feedback(report_id);

DO $$
DECLARE
  current_definition TEXT;
BEGIN
  SELECT pg_get_constraintdef(oid)
    INTO current_definition
    FROM pg_constraint
   WHERE conrelid = 'public.decision_feedback'::regclass
     AND conname = 'decision_feedback_status_check';

  IF current_definition IS NOT NULL
     AND position('unsure' IN current_definition) = 0 THEN
    ALTER TABLE public.decision_feedback
      DROP CONSTRAINT decision_feedback_status_check;
    current_definition := NULL;
  END IF;

  IF current_definition IS NULL THEN
    ALTER TABLE public.decision_feedback
      ADD CONSTRAINT decision_feedback_status_check CHECK (status IN (
        'planned', 'unsure', 'done', 'partially_done', 'not_done',
        'rejected', 'no_longer_relevant'
      ));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
     WHERE tgrelid = 'public.decision_feedback'::regclass
       AND tgname = 'update_decision_feedback_updated_at'
       AND NOT tgisinternal
  ) THEN
    CREATE TRIGGER update_decision_feedback_updated_at
      BEFORE UPDATE ON public.decision_feedback
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
  END IF;
END $$;

ALTER TABLE public.decision_feedback ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
     WHERE schemaname = 'public'
       AND tablename = 'decision_feedback'
       AND policyname = 'decision_feedback_company_own'
  ) THEN
    CREATE POLICY decision_feedback_company_own
      ON public.decision_feedback
      FOR ALL
      USING (
        company_id IN (
          SELECT id FROM public.companies WHERE admin_user_id = auth.uid()
        )
      )
      WITH CHECK (
        company_id IN (
          SELECT id FROM public.companies WHERE admin_user_id = auth.uid()
        )
      );
  END IF;
END $$;

COMMENT ON TABLE public.decision_feedback IS
  'Explicit user intention/feedback on a recommendation. An intention is not a confirmed professional decision.';
