-- V36: reviewed Integration Test privilege containment. No application-row writes.
-- Execute only in the explicitly approved project after reading the A24 protocol.
-- Historical migrations remain unchanged. No automatic permissive rollback.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

DO $v36$
DECLARE
    backend_tables constant text[] := ARRAY[
        'sessions', 'analyses', 'evidence_ledger_entries',
        'arc_analysis_links', 'decision_arcs', 'knowledge_model'];
    identity_tables constant text[] := ARRAY['profiles', 'companies'];
    table_name text;
    role_name text;
    privilege_name text;
    column_names text;
    target oid;
    rpc oid := to_regprocedure('public.create_entity_with_engagement(uuid,uuid,text,text,text,text)');
BEGIN
    -- Refuse missing/unexpected scope, not partial best-effort repair.
    IF rpc IS NULL OR NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE oid = rpc AND prosecdef
    ) THEN
        RAISE EXCEPTION 'V36_RPC_SCHEMA_REFUSED';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role' AND rolbypassrls)
       OR NOT has_function_privilege('service_role', rpc, 'EXECUTE') THEN
        RAISE EXCEPTION 'V36_SERVICE_ROLE_REFUSED';
    END IF;
    FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name AND NOT rolsuper AND NOT rolbypassrls) THEN
            RAISE EXCEPTION 'V36_CLIENT_ROLE_REFUSED';
        END IF;
    END LOOP;
    FOREACH table_name IN ARRAY backend_tables || identity_tables LOOP
        target := to_regclass(format('public.%I', table_name));
        IF target IS NULL OR NOT EXISTS (
            SELECT 1 FROM pg_class WHERE oid = target AND relkind = 'r'
        ) THEN
            RAISE EXCEPTION 'V36_TABLE_SCHEMA_REFUSED: %', table_name;
        END IF;
        FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'] LOOP
            IF NOT has_table_privilege('service_role', target, privilege_name) THEN
                RAISE EXCEPTION 'V36_SERVICE_PRIVILEGE_REFUSED: %', table_name;
            END IF;
        END LOOP;
        IF table_name = ANY(backend_tables) AND EXISTS (
            SELECT 1 FROM pg_policy WHERE polrelid = target
        ) THEN
            RAISE EXCEPTION 'V36_UNREVIEWED_POLICY_REFUSED: %', table_name;
        END IF;
        IF table_name = ANY(identity_tables) THEN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE oid = target AND relrowsecurity)
               OR NOT has_table_privilege('authenticated', target, 'SELECT') THEN
                RAISE EXCEPTION 'V36_IDENTITY_READ_BASELINE_REFUSED: %', table_name;
            END IF;
            IF (SELECT count(*) FROM pg_policy WHERE polrelid = target) <> 1
               OR NOT EXISTS (
                   SELECT 1 FROM pg_policy WHERE polrelid = target
                     AND polcmd = '*' AND polpermissive AND polroles = ARRAY[0::oid]
                     AND polwithcheck IS NULL
                     AND pg_get_expr(polqual, polrelid) = CASE table_name
                         WHEN 'profiles' THEN '(id = auth.uid())'
                         ELSE '(admin_user_id = auth.uid())' END
               ) THEN
                RAISE EXCEPTION 'V36_IDENTITY_POLICY_DRIFT_REFUSED: %', table_name;
            END IF;
        END IF;
    END LOOP;

    FOREACH table_name IN ARRAY backend_tables || identity_tables LOOP
        target := to_regclass(format('public.%I', table_name));
        -- Revoking table privileges alone does not revoke independent column grants.
        SELECT string_agg(format('%I', attname), ', ' ORDER BY attnum)
          INTO column_names FROM pg_attribute
          WHERE attrelid = target AND attnum > 0 AND NOT attisdropped;
        EXECUTE format('REVOKE ALL PRIVILEGES ON TABLE public.%I FROM PUBLIC, anon, authenticated', table_name);
        FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'REFERENCES'] LOOP
            EXECUTE format('REVOKE %s (%s) ON TABLE public.%I FROM PUBLIC, anon, authenticated',
                           privilege_name, column_names, table_name);
        END LOOP;
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        IF table_name = ANY(identity_tables) THEN
            -- Existing own-row policies remain in force; no new read audience.
            EXECUTE format('GRANT SELECT ON TABLE public.%I TO authenticated', table_name);
        END IF;
    END LOOP;
    REVOKE ALL PRIVILEGES ON FUNCTION public.create_entity_with_engagement(uuid,uuid,text,text,text,text)
        FROM PUBLIC, anon, authenticated;
    -- Preserve the prechecked service permission when it previously came from PUBLIC.
    GRANT EXECUTE ON FUNCTION public.create_entity_with_engagement(uuid,uuid,text,text,text,text)
        TO service_role;

    -- Effective-right checks catch inherited grants/ownership missed by direct REVOKE.
    FOREACH table_name IN ARRAY backend_tables || identity_tables LOOP
        target := to_regclass(format('public.%I', table_name));
        FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'] LOOP
                IF NOT (table_name = ANY(identity_tables) AND role_name = 'authenticated' AND privilege_name = 'SELECT')
                   AND has_table_privilege(role_name, target, privilege_name) THEN
                    RAISE EXCEPTION 'V36_EFFECTIVE_TABLE_GRANT_REMAINS';
                END IF;
            END LOOP;
            FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'REFERENCES'] LOOP
                IF NOT (table_name = ANY(identity_tables) AND role_name = 'authenticated' AND privilege_name = 'SELECT')
                   AND has_any_column_privilege(role_name, target, privilege_name) THEN
                    RAISE EXCEPTION 'V36_EFFECTIVE_COLUMN_GRANT_REMAINS';
                END IF;
            END LOOP;
        END LOOP;
        FOREACH privilege_name IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'] LOOP
            IF NOT has_table_privilege('service_role', target, privilege_name) THEN
                RAISE EXCEPTION 'V36_SERVICE_PRIVILEGE_LOST';
            END IF;
        END LOOP;
    END LOOP;
    IF has_function_privilege('anon', rpc, 'EXECUTE')
       OR has_function_privilege('authenticated', rpc, 'EXECUTE')
       OR NOT has_function_privilege('service_role', rpc, 'EXECUTE') THEN
        RAISE EXCEPTION 'V36_RPC_PRIVILEGES_REFUSED';
    END IF;
END;
$v36$;
COMMIT;
