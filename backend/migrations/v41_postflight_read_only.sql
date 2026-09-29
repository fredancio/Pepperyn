BEGIN READ ONLY;
WITH expected_tables(name) AS (VALUES
  ('generic_producer_policies_v3'),
  ('generic_execution_admissions_v3'),
  ('generic_execution_receipts_v3')
), table_checks AS (
  SELECT e.name,
    c.oid IS NOT NULL AS present,
    COALESCE(c.relrowsecurity,false) AS rls_enabled,
    CASE WHEN c.oid IS NULL THEN NULL ELSE
      (SELECT count(*) FROM pg_trigger t WHERE t.tgrelid=c.oid AND NOT t.tgisinternal)
    END AS immutable_trigger_count,
    jsonb_build_object(
      'anon_select',has_table_privilege('anon','public.'||e.name,'SELECT'),
      'authenticated_select',has_table_privilege('authenticated','public.'||e.name,'SELECT'),
      'service_select',has_table_privilege('service_role','public.'||e.name,'SELECT'),
      'service_insert',has_table_privilege('service_role','public.'||e.name,'INSERT'),
      'service_update',has_table_privilege('service_role','public.'||e.name,'UPDATE'),
      'service_delete',has_table_privilege('service_role','public.'||e.name,'DELETE')
    ) AS privileges
  FROM expected_tables e LEFT JOIN pg_class c
    ON c.oid=to_regclass('public.'||e.name)
), expected_functions(name) AS (VALUES
  ('reserve_generic_execution_v3'),('claim_generic_execution_v3'),
  ('close_generic_execution_v3'),('complete_generic_execution_v3')
), function_checks AS (
  SELECT e.name,
    count(p.oid)=1 AS present,
    COALESCE(bool_and(p.prosecdef),false) AS security_definer,
    COALESCE(bool_or(has_function_privilege('anon',p.oid,'EXECUTE')),false) AS anon_execute,
    COALESCE(bool_or(has_function_privilege('authenticated',p.oid,'EXECUTE')),false) AS authenticated_execute,
    COALESCE(bool_or(has_function_privilege('service_role',p.oid,'EXECUTE')),false) AS service_execute
  FROM expected_functions e LEFT JOIN pg_proc p ON p.proname=e.name GROUP BY e.name
)
SELECT jsonb_build_object(
  'phase','V41_POST_DEPLOYMENT_INSPECTION',
  'status',CASE WHEN
    (SELECT bool_and(present AND rls_enabled AND immutable_trigger_count=1
      AND NOT (privileges->>'anon_select')::boolean
      AND NOT (privileges->>'authenticated_select')::boolean
      AND (privileges->>'service_select')::boolean
      AND NOT (privileges->>'service_insert')::boolean
      AND NOT (privileges->>'service_update')::boolean
      AND NOT (privileges->>'service_delete')::boolean) FROM table_checks)
    AND (SELECT bool_and(present AND security_definer AND NOT anon_execute
      AND NOT authenticated_execute AND service_execute) FROM function_checks)
    AND (SELECT count(*) FROM public.generic_producer_policies_v3)=0
    AND (SELECT count(*) FROM public.generic_execution_admissions_v3)=0
    AND (SELECT count(*) FROM public.generic_execution_receipts_v3)=0
    THEN 'POSTFLIGHT_PASS' ELSE 'REFUSED' END,
  'tables',(SELECT jsonb_agg(to_jsonb(t) ORDER BY name) FROM table_checks t),
  'functions',(SELECT jsonb_agg(to_jsonb(f) ORDER BY name) FROM function_checks f),
  'policy_rows',(SELECT count(*) FROM public.generic_producer_policies_v3),
  'admission_rows',(SELECT count(*) FROM public.generic_execution_admissions_v3),
  'receipt_rows',(SELECT count(*) FROM public.generic_execution_receipts_v3),
  'write_performed',false
) AS v41_postflight;
ROLLBACK;
