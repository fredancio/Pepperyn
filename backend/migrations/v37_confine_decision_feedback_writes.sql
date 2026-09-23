-- A27: backend-authorized feedback writes only. Integration Test approval required.
-- Preserve existing SELECT/RLS and service CRUD. No application-row mutation.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

DO $v37$
DECLARE
    target oid := to_regclass('public.decision_feedback');
    columns_sql text;
    role_name text;
    privilege_name text;
BEGIN
    IF target IS NULL OR NOT EXISTS (
        SELECT 1 FROM pg_class WHERE oid = target AND relkind = 'r' AND relrowsecurity
    ) THEN
        RAISE EXCEPTION 'V37_TABLE_BASELINE_REFUSED';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role' AND rolbypassrls) THEN
        RAISE EXCEPTION 'V37_SERVICE_ROLE_REFUSED';
    END IF;
    FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name AND NOT rolsuper AND NOT rolbypassrls) THEN
            RAISE EXCEPTION 'V37_CLIENT_ROLE_REFUSED';
        END IF;
    END LOOP;
    FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'] LOOP
        IF NOT has_table_privilege('service_role', target, privilege_name) THEN
            RAISE EXCEPTION 'V37_SERVICE_BASELINE_REFUSED';
        END IF;
    END LOOP;
    -- Preserve already effective service CRUD if any grant originated at PUBLIC.
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.decision_feedback TO service_role;
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
        ON public.decision_feedback FROM PUBLIC, anon, authenticated;
    SELECT string_agg(format('%I', attname), ', ' ORDER BY attnum)
        INTO columns_sql FROM pg_attribute
        WHERE attrelid = target AND attnum > 0 AND NOT attisdropped;
    FOREACH privilege_name IN ARRAY ARRAY['INSERT', 'UPDATE', 'REFERENCES'] LOOP
        EXECUTE format('REVOKE %s (%s) ON public.decision_feedback FROM PUBLIC, anon, authenticated',
                       privilege_name, columns_sql);
    END LOOP;
    -- Inherited privileges must not silently survive; failure rolls back all DDL.
    FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        FOREACH privilege_name IN ARRAY ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'] LOOP
            IF has_table_privilege(role_name, target, privilege_name) THEN
                RAISE EXCEPTION 'V37_EFFECTIVE_TABLE_WRITE_REMAINS';
            END IF;
        END LOOP;
        FOREACH privilege_name IN ARRAY ARRAY['INSERT', 'UPDATE', 'REFERENCES'] LOOP
            IF has_any_column_privilege(role_name, target, privilege_name) THEN
                RAISE EXCEPTION 'V37_EFFECTIVE_COLUMN_WRITE_REMAINS';
            END IF;
        END LOOP;
    END LOOP;
    FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'] LOOP
        IF NOT has_table_privilege('service_role', target, privilege_name) THEN
            RAISE EXCEPTION 'V37_SERVICE_PRIVILEGE_LOST';
        END IF;
    END LOOP;
END;
$v37$;
COMMIT;
