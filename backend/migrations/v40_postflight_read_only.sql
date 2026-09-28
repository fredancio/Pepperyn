-- Schema proof only. All three new tables must still be empty after deployment.
BEGIN TRANSACTION READ ONLY;
SELECT jsonb_build_object(
 'phase','V40_SCHEMA_INSPECTION_ONLY',
 'tables',(SELECT jsonb_agg(jsonb_build_object('table',c.relname,'rls_enabled',c.relrowsecurity,
   'policy_count',(SELECT count(*) FROM pg_policy WHERE polrelid=c.oid),
   'immutable_trigger_count',(SELECT count(*) FROM pg_trigger WHERE tgrelid=c.oid AND NOT tgisinternal),
   'privileges',(SELECT jsonb_object_agg(role,jsonb_build_object(
     'select',has_table_privilege(role,c.oid,'SELECT'),'insert',has_table_privilege(role,c.oid,'INSERT'),
     'update',has_table_privilege(role,c.oid,'UPDATE'),'delete',has_table_privilege(role,c.oid,'DELETE'),
     'truncate',has_table_privilege(role,c.oid,'TRUNCATE')))
     FROM unnest(ARRAY['anon','authenticated','service_role']) role)))
   FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname IN ('producer_policies_v2','execution_admissions_v2','execution_receipts_v2')),
 'functions',(SELECT jsonb_agg(jsonb_build_object('name',p.proname,'security_definer',p.prosecdef,
   'configuration',p.proconfig,'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),
   'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
   'service_execute',has_function_privilege('service_role',p.oid,'EXECUTE')))
   FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public'
   AND p.proname IN ('guard_prospective_execution_v2','check_execution_scope_v2','reserve_execution_v2',
     'claim_execution_v2','close_execution_v2','complete_execution_v2')),
 'policy_rows',(SELECT count(*) FROM public.producer_policies_v2),
 'admission_rows',(SELECT count(*) FROM public.execution_admissions_v2),
 'receipt_rows',(SELECT count(*) FROM public.execution_receipts_v2),
 'write_performed',false,'producer_admitted',false,'external_provider','CLOSED','real_data_admission','CLOSED'
) AS v40_postflight;
ROLLBACK;
