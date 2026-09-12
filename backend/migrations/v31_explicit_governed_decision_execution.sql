-- v31 — Record one explicit execution checkpoint for a governed V1 decision.
-- Execution remains distinct from the decision, later evidence, outcome and learning.

CREATE TABLE IF NOT EXISTS public.governed_decision_executions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  report_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
  decision_feedback_id UUID NOT NULL REFERENCES public.decision_feedback(id) ON DELETE RESTRICT,
  recommendation_id TEXT NOT NULL,
  executed_on DATE NOT NULL,
  professional_note TEXT NOT NULL CHECK (length(btrim(professional_note)) > 0),
  prerequisites_confirmed_complete BOOLEAN NOT NULL CHECK (prerequisites_confirmed_complete),
  confirmation_source TEXT NOT NULL CHECK (confirmation_source = 'explicit'),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT governed_decision_executions_one_checkpoint UNIQUE (decision_feedback_id)
);

CREATE INDEX IF NOT EXISTS idx_governed_decision_executions_scope
  ON public.governed_decision_executions(company_id, report_id);

CREATE OR REPLACE FUNCTION public.validate_governed_execution_scope()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.executed_on > CURRENT_DATE THEN
    RAISE EXCEPTION 'Execution date cannot be future';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.decision_feedback df
    WHERE df.id = NEW.decision_feedback_id
      AND df.company_id = NEW.company_id
      AND df.report_id = NEW.report_id
      AND df.recommendation_id = NEW.recommendation_id
      AND df.decision_confirmed_at IS NOT NULL
      AND df.decision_kind IN ('accepted_conditional', 'modified')
      AND NEW.executed_on >= df.decision_confirmed_at::date
  ) THEN
    RAISE EXCEPTION 'Execution scope does not match one executable governed decision';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.governed_decision_followups gf
    WHERE gf.decision_feedback_id = NEW.decision_feedback_id
      AND gf.company_id = NEW.company_id
      AND gf.report_id = NEW.report_id
      AND gf.recommendation_id = NEW.recommendation_id
  ) THEN
    RAISE EXCEPTION 'A matching governed follow-up is required before execution';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS validate_governed_execution_scope ON public.governed_decision_executions;
CREATE TRIGGER validate_governed_execution_scope
  BEFORE INSERT ON public.governed_decision_executions
  FOR EACH ROW EXECUTE FUNCTION public.validate_governed_execution_scope();

CREATE OR REPLACE FUNCTION public.prevent_governed_execution_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'A governed decision execution checkpoint is immutable';
END;
$$;

DROP TRIGGER IF EXISTS prevent_governed_execution_mutation ON public.governed_decision_executions;
CREATE TRIGGER prevent_governed_execution_mutation
  BEFORE UPDATE OR DELETE ON public.governed_decision_executions
  FOR EACH ROW EXECUTE FUNCTION public.prevent_governed_execution_mutation();

ALTER TABLE public.governed_decision_executions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.governed_decision_executions FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.governed_decision_executions FROM service_role;
GRANT SELECT, INSERT ON TABLE public.governed_decision_executions TO service_role;

COMMENT ON TABLE public.governed_decision_executions IS
  'One explicit immutable V1 execution checkpoint; not a decision, later evidence, outcome, learning or DecisionArc.';
