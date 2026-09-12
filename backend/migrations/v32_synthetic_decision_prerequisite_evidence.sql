-- v32 — Persist a validated synthetic prerequisite-evidence receipt.
-- This is not later evidence, an outcome, a learning, or an expected impact.

CREATE TABLE IF NOT EXISTS public.governed_decision_prerequisite_evidence (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  report_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
  decision_feedback_id UUID NOT NULL REFERENCES public.decision_feedback(id) ON DELETE RESTRICT,
  recommendation_id TEXT NOT NULL,
  fixture_id TEXT NOT NULL CHECK (fixture_id = 'PEPPERYN_V1_EXECUTION_PREREQUISITES'),
  payload_sha256 TEXT NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL CHECK (period_end >= period_start),
  provenance TEXT NOT NULL CHECK (length(btrim(provenance)) > 0),
  payload JSONB NOT NULL,
  evidence_role TEXT NOT NULL CHECK (evidence_role = 'DECISION_PREREQUISITE_ONLY'),
  synthetic BOOLEAN NOT NULL CHECK (synthetic),
  external_network_used BOOLEAN NOT NULL CHECK (NOT external_network_used),
  real_client_data_used BOOLEAN NOT NULL CHECK (NOT real_client_data_used),
  later_evidence BOOLEAN NOT NULL CHECK (NOT later_evidence),
  actual_outcome_created BOOLEAN NOT NULL CHECK (NOT actual_outcome_created),
  learning_created BOOLEAN NOT NULL CHECK (NOT learning_created),
  expected_impact_created BOOLEAN NOT NULL CHECK (NOT expected_impact_created),
  validation_source TEXT NOT NULL CHECK (validation_source = 'registered_local_fixture'),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (decision_feedback_id)
);

CREATE INDEX IF NOT EXISTS idx_governed_prerequisite_evidence_scope
  ON public.governed_decision_prerequisite_evidence(company_id, report_id);

CREATE OR REPLACE FUNCTION public.validate_governed_prerequisite_evidence_scope()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.decision_feedback df
    WHERE df.id = NEW.decision_feedback_id AND df.company_id = NEW.company_id
      AND df.report_id = NEW.report_id AND df.recommendation_id = NEW.recommendation_id
      AND df.decision_confirmed_at IS NOT NULL
      AND df.decision_kind IN ('accepted_conditional', 'modified')
  ) THEN
    RAISE EXCEPTION 'Prerequisite evidence scope does not match one executable governed decision';
  END IF;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.prevent_governed_prerequisite_evidence_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Governed prerequisite evidence is immutable';
END;
$$;

DROP TRIGGER IF EXISTS validate_governed_prerequisite_evidence_scope ON public.governed_decision_prerequisite_evidence;
CREATE TRIGGER validate_governed_prerequisite_evidence_scope
  BEFORE INSERT ON public.governed_decision_prerequisite_evidence
  FOR EACH ROW EXECUTE FUNCTION public.validate_governed_prerequisite_evidence_scope();
DROP TRIGGER IF EXISTS prevent_governed_prerequisite_evidence_mutation ON public.governed_decision_prerequisite_evidence;
CREATE TRIGGER prevent_governed_prerequisite_evidence_mutation
  BEFORE UPDATE OR DELETE ON public.governed_decision_prerequisite_evidence
  FOR EACH ROW EXECUTE FUNCTION public.prevent_governed_prerequisite_evidence_mutation();

ALTER TABLE public.governed_decision_prerequisite_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.governed_decision_prerequisite_evidence FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.governed_decision_prerequisite_evidence FROM service_role;
GRANT SELECT, INSERT ON TABLE public.governed_decision_prerequisite_evidence TO service_role;

ALTER TABLE public.governed_decision_executions
  ADD COLUMN IF NOT EXISTS prerequisite_evidence_id UUID
  REFERENCES public.governed_decision_prerequisite_evidence(id) ON DELETE RESTRICT;
ALTER TABLE public.governed_decision_executions
  ALTER COLUMN prerequisite_evidence_id SET NOT NULL;

CREATE OR REPLACE FUNCTION public.validate_governed_execution_scope()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.executed_on > CURRENT_DATE THEN RAISE EXCEPTION 'Execution date cannot be future'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.decision_feedback df
    WHERE df.id = NEW.decision_feedback_id AND df.company_id = NEW.company_id
      AND df.report_id = NEW.report_id AND df.recommendation_id = NEW.recommendation_id
      AND df.decision_confirmed_at IS NOT NULL
      AND df.decision_kind IN ('accepted_conditional', 'modified')
      AND NEW.executed_on >= df.decision_confirmed_at::date
  ) THEN RAISE EXCEPTION 'Execution scope does not match one executable governed decision'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.governed_decision_followups gf
    WHERE gf.decision_feedback_id = NEW.decision_feedback_id AND gf.company_id = NEW.company_id
      AND gf.report_id = NEW.report_id AND gf.recommendation_id = NEW.recommendation_id
  ) THEN RAISE EXCEPTION 'A matching governed follow-up is required before execution'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.governed_decision_prerequisite_evidence pe
    WHERE pe.id = NEW.prerequisite_evidence_id AND pe.decision_feedback_id = NEW.decision_feedback_id
      AND pe.company_id = NEW.company_id AND pe.report_id = NEW.report_id
      AND pe.recommendation_id = NEW.recommendation_id
  ) THEN RAISE EXCEPTION 'Matching prerequisite evidence is required before execution'; END IF;
  RETURN NEW;
END;
$$;
