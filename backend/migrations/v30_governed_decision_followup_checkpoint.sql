-- v30 — Capture one explicit, immutable follow-up checkpoint for a governed
-- V1 decision. This does not mutate the decision or create a DecisionArc.

CREATE TABLE IF NOT EXISTS public.governed_decision_followups (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  report_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
  decision_feedback_id UUID NOT NULL REFERENCES public.decision_feedback(id) ON DELETE RESTRICT,
  recommendation_id TEXT NOT NULL,
  followup_status TEXT NOT NULL CHECK (followup_status IN (
    'pending_validation', 'in_progress', 'blocked', 'completed', 'not_pursued'
  )),
  professional_note TEXT NOT NULL CHECK (length(btrim(professional_note)) > 0),
  prerequisites_confirmed_complete BOOLEAN NOT NULL DEFAULT FALSE,
  confirmation_source TEXT NOT NULL CHECK (confirmation_source = 'explicit'),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT governed_decision_followups_one_checkpoint
    UNIQUE (decision_feedback_id)
);

CREATE INDEX IF NOT EXISTS idx_governed_decision_followups_scope
  ON public.governed_decision_followups(company_id, report_id);

CREATE OR REPLACE FUNCTION public.prevent_governed_followup_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'A governed decision follow-up checkpoint is immutable';
END;
$$;

DROP TRIGGER IF EXISTS prevent_governed_followup_mutation
  ON public.governed_decision_followups;
CREATE TRIGGER prevent_governed_followup_mutation
  BEFORE UPDATE OR DELETE ON public.governed_decision_followups
  FOR EACH ROW EXECUTE FUNCTION public.prevent_governed_followup_mutation();

ALTER TABLE public.governed_decision_followups ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.governed_decision_followups FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.governed_decision_followups FROM service_role;
GRANT SELECT, INSERT ON TABLE public.governed_decision_followups TO service_role;

COMMENT ON TABLE public.governed_decision_followups IS
  'One explicit immutable V1 follow-up checkpoint; never inferred and never a DecisionArc.';
