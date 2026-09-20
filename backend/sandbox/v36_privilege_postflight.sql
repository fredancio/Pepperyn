-- READ ONLY catalog inspection. No application rows, users, secrets or RPC invocation.
BEGIN READ ONLY;
WITH targets(name, identity_read) AS (VALUES
    ('sessions',false),('analyses',false),('evidence_ledger_entries',false),
    ('arc_analysis_links',false),('decision_arcs',false),('knowledge_model',false),
    ('profiles',true),('companies',true)
), checks AS (
    SELECT name,
        coalesce(c.relrowsecurity,false) AS rls_enabled,
        c.oid IS NOT NULL AS table_present,
        NOT EXISTS (
            SELECT 1 FROM (VALUES ('anon'),('authenticated')) r(role_name)
            CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) p(priv)
            WHERE NOT (identity_read AND role_name='authenticated' AND priv='SELECT')
              AND has_table_privilege(role_name,c.oid,priv)
        ) AS forbidden_table_grants_absent,
        NOT EXISTS (
            SELECT 1 FROM (VALUES ('anon'),('authenticated')) r(role_name)
            CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('REFERENCES')) p(priv)
            WHERE NOT (identity_read AND role_name='authenticated' AND priv='SELECT')
              AND has_any_column_privilege(role_name,c.oid,priv)
        ) AS forbidden_column_grants_absent,
        (NOT identity_read OR has_table_privilege('authenticated',c.oid,'SELECT')) AS identity_read_preserved,
        (SELECT bool_and(has_table_privilege('service_role',c.oid,priv))
         FROM (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')) p(priv)) AS service_crud_preserved,
        CASE WHEN identity_read THEN
            (SELECT count(*)=1 AND bool_and(polcmd='*' AND polpermissive AND polroles=ARRAY[0::oid]
                AND polwithcheck IS NULL AND pg_get_expr(polqual,polrelid)=CASE name
                  WHEN 'profiles' THEN '(id = auth.uid())' ELSE '(admin_user_id = auth.uid())' END)
             FROM pg_policy WHERE polrelid=c.oid)
            ELSE NOT EXISTS(SELECT 1 FROM pg_policy WHERE polrelid=c.oid)
        END AS policy_baseline_preserved
    FROM targets LEFT JOIN pg_class c ON c.oid=to_regclass(format('public.%I',name))
), rpc AS (
    SELECT to_regprocedure('public.create_entity_with_engagement(uuid,uuid,text,text,text,text)') AS id
)
SELECT jsonb_build_object(
    'phase','V36_CATALOG_POSTFLIGHT',
    'tables',(SELECT jsonb_agg(to_jsonb(checks) ORDER BY name) FROM checks),
    'table_checks_pass',(SELECT bool_and(table_present AND rls_enabled AND forbidden_table_grants_absent
        AND forbidden_column_grants_absent AND identity_read_preserved AND service_crud_preserved AND policy_baseline_preserved) FROM checks),
    'rpc_checks_pass',coalesce(NOT has_function_privilege('anon',id,'EXECUTE')
        AND NOT has_function_privilege('authenticated',id,'EXECUTE')
        AND has_function_privilege('service_role',id,'EXECUTE'),false),
    'write_performed',false,'application_rows_read',false,
    'two_user_adversarial_proof',false,'production_proof',false
) AS v36_postflight FROM rpc;
ROLLBACK;
