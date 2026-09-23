-- Restore only the missing V7 derived-pattern table. Integration Test GO required.
-- No existing rows touched; no V37/decision_feedback/analysis changes.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
DO $pre$
BEGIN
    IF to_regclass('public.user_patterns') IS NOT NULL THEN
        RAISE EXCEPTION 'V38_ALREADY_PRESENT_STOP_AND_INSPECT';
    END IF;
    IF to_regclass('public.companies') IS NULL
       OR to_regprocedure('public.update_updated_at()') IS NULL
       OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role' AND rolbypassrls) THEN
        RAISE EXCEPTION 'V38_DEPENDENCY_REFUSED';
    END IF;
END;
$pre$;
CREATE TABLE public.user_patterns (
    company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE PRIMARY KEY,
    execution_rate NUMERIC(5,2),
    pricing_execution_rate NUMERIC(5,2),
    pricing_resistance_score NUMERIC(5,2),
    cost_reduction_execution_rate NUMERIC(5,2),
    revenue_action_execution_rate NUMERIC(5,2),
    average_delay_to_execution_days NUMERIC(6,2),
    recurring_blockers JSONB DEFAULT '[]',
    preferred_action_type TEXT,
    total_feedback_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE TRIGGER update_user_patterns_updated_at
    BEFORE UPDATE ON public.user_patterns
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
ALTER TABLE public.user_patterns ENABLE ROW LEVEL SECURITY;
-- Backend-derived state is not writable by clients. Do not restore V7's ALL policy.
REVOKE ALL PRIVILEGES ON public.user_patterns FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON public.user_patterns TO service_role;
DO $post$
DECLARE r text; p text;
BEGIN
    FOREACH r IN ARRAY ARRAY['anon','authenticated'] LOOP
        FOREACH p IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'] LOOP
            IF has_table_privilege(r,'public.user_patterns',p) THEN
                RAISE EXCEPTION 'V38_CLIENT_TABLE_GRANT_REMAINS';
            END IF;
        END LOOP;
        FOREACH p IN ARRAY ARRAY['SELECT','INSERT','UPDATE','REFERENCES'] LOOP
            IF has_any_column_privilege(r,'public.user_patterns',p) THEN
                RAISE EXCEPTION 'V38_CLIENT_COLUMN_GRANT_REMAINS';
            END IF;
        END LOOP;
    END LOOP;
    FOREACH p IN ARRAY ARRAY['SELECT','INSERT','UPDATE'] LOOP
        IF NOT has_table_privilege('service_role','public.user_patterns',p) THEN
            RAISE EXCEPTION 'V38_SERVICE_GRANT_MISSING';
        END IF;
    END LOOP;
END;
$post$;
COMMIT;
