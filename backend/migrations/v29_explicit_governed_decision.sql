-- v29 — Add an explicit, immutable professional-decision transition to the
-- governed V1 recommendation registry.
--
-- This migration does not infer a decision from an intention, validate any
-- prerequisite, or create a DecisionArc.

ALTER TABLE public.decision_feedback
  ADD COLUMN IF NOT EXISTS decision_kind TEXT,
  ADD COLUMN IF NOT EXISTS decision_text TEXT,
  ADD COLUMN IF NOT EXISTS decision_confirmed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS decision_confirmation_source TEXT,
  ADD COLUMN IF NOT EXISTS prerequisites_acknowledged BOOLEAN;

ALTER TABLE public.decision_feedback
  DROP CONSTRAINT IF EXISTS decision_feedback_status_check;

ALTER TABLE public.decision_feedback
  ADD CONSTRAINT decision_feedback_status_check CHECK (status IN (
    'planned', 'unsure', 'done', 'partially_done', 'not_done',
    'rejected', 'no_longer_relevant', 'decided'
  ));

ALTER TABLE public.decision_feedback
  DROP CONSTRAINT IF EXISTS decision_feedback_decision_kind_check;

ALTER TABLE public.decision_feedback
  ADD CONSTRAINT decision_feedback_decision_kind_check CHECK (
    decision_kind IS NULL OR decision_kind IN (
      'accepted_conditional', 'modified', 'rejected'
    )
  );

ALTER TABLE public.decision_feedback
  DROP CONSTRAINT IF EXISTS decision_feedback_explicit_decision_check;

ALTER TABLE public.decision_feedback
  ADD CONSTRAINT decision_feedback_explicit_decision_check CHECK (
    (
      decision_kind IS NULL
      AND decision_text IS NULL
      AND decision_confirmed_at IS NULL
      AND decision_confirmation_source IS NULL
      AND prerequisites_acknowledged IS NULL
      AND status <> 'decided'
    ) OR (
      decision_kind IS NOT NULL
      AND decision_text IS NOT NULL
      AND length(btrim(decision_text)) > 0
      AND decision_confirmed_at IS NOT NULL
      AND decision_confirmation_source = 'explicit'
      AND prerequisites_acknowledged IS NOT NULL
      AND status = 'decided'
    )
  );

CREATE OR REPLACE FUNCTION public.prevent_confirmed_decision_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.decision_confirmed_at IS NOT NULL THEN
      RAISE EXCEPTION 'A confirmed governed decision is immutable';
    END IF;
    RETURN OLD;
  END IF;
  IF OLD.decision_confirmed_at IS NOT NULL AND (
    NEW.status IS DISTINCT FROM OLD.status OR
    NEW.decision_kind IS DISTINCT FROM OLD.decision_kind OR
    NEW.decision_text IS DISTINCT FROM OLD.decision_text OR
    NEW.decision_confirmed_at IS DISTINCT FROM OLD.decision_confirmed_at OR
    NEW.decision_confirmation_source IS DISTINCT FROM OLD.decision_confirmation_source OR
    NEW.prerequisites_acknowledged IS DISTINCT FROM OLD.prerequisites_acknowledged
  ) THEN
    RAISE EXCEPTION 'A confirmed governed decision is immutable';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS prevent_confirmed_decision_mutation ON public.decision_feedback;
CREATE TRIGGER prevent_confirmed_decision_mutation
  BEFORE UPDATE OR DELETE ON public.decision_feedback
  FOR EACH ROW EXECUTE FUNCTION public.prevent_confirmed_decision_mutation();

COMMENT ON COLUMN public.decision_feedback.decision_confirmation_source IS
  'Must be explicit; an intention can never be promoted automatically.';
COMMENT ON COLUMN public.decision_feedback.prerequisites_acknowledged IS
  'Acknowledges that listed validations still condition the decision; does not assert they are complete.';
