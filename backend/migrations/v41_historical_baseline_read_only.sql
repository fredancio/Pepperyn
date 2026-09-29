-- V41 deployment baseline: counts and deterministic hashes only; no row content.
BEGIN TRANSACTION READ ONLY;
WITH row_snapshots AS (
 SELECT 'analyses' AS name,count(*) AS row_count,
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex') AS rows_sha256
   FROM public.analyses t
 UNION ALL SELECT 'governed_analysis_envelopes',count(*),
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')
   FROM public.governed_analysis_envelopes t
 UNION ALL SELECT 'governed_execution_receipts',count(*),
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')
   FROM public.governed_execution_receipts t
 UNION ALL SELECT 'producer_policies_v2',count(*),
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')
   FROM public.producer_policies_v2 t
 UNION ALL SELECT 'execution_admissions_v2',count(*),
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')
   FROM public.execution_admissions_v2 t
 UNION ALL SELECT 'execution_receipts_v2',count(*),
   encode(sha256(convert_to(COALESCE(string_agg(to_jsonb(t)::text,E'\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')
   FROM public.execution_receipts_v2 t
), relevant_tables AS (
 SELECT c.oid,c.relname,n.nspname,c.relrowsecurity,c.relforcerowsecurity,c.relacl,
   pg_get_userbyid(c.relowner) AS owner
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relname IN ('analyses','governed_analysis_envelopes',
   'governed_execution_receipts','producer_policies_v2','execution_admissions_v2','execution_receipts_v2')
), catalog_items AS (
 SELECT 'table' AS kind,relname AS name,
   jsonb_build_object('schema',nspname,'rls',relrowsecurity,'force_rls',relforcerowsecurity,
     'acl',relacl,'owner',owner)::text AS definition
 FROM relevant_tables
 UNION ALL
 SELECT 'constraint',rt.relname||'.'||co.conname,
   jsonb_build_object('type',co.contype,'validated',co.convalidated,
     'definition',pg_get_constraintdef(co.oid,true))::text
 FROM relevant_tables rt JOIN pg_constraint co ON co.conrelid=rt.oid
 UNION ALL
 SELECT 'trigger',rt.relname||'.'||tr.tgname,pg_get_triggerdef(tr.oid,true)
 FROM relevant_tables rt JOIN pg_trigger tr ON tr.tgrelid=rt.oid AND NOT tr.tgisinternal
 UNION ALL
 SELECT 'function',p.proname||'('||pg_get_function_identity_arguments(p.oid)||')',
   jsonb_build_object('result',pg_get_function_result(p.oid),'definer',p.prosecdef,
     'config',p.proconfig,'acl',p.proacl,'owner',pg_get_userbyid(p.proowner),
     'body_sha256',encode(sha256(convert_to(p.prosrc,'UTF8')),'hex'))::text
 FROM pg_proc p WHERE p.pronamespace='public'::regnamespace
   AND p.proname IN ('persist_governed_analysis_v1','check_execution_scope_v2')
), catalog_snapshot AS (
 SELECT count(*) AS item_count,
   encode(sha256(convert_to(COALESCE(string_agg(kind||'|'||name||'|'||definition,E'\n'
     ORDER BY kind,name,definition),''),'UTF8')),'hex') AS catalog_sha256
 FROM catalog_items
)
SELECT jsonb_build_object(
 'phase','V41_HISTORICAL_BASELINE_READ_ONLY',
 'status',CASE WHEN (SELECT count(*) FROM row_snapshots)=6
   AND (SELECT count(*) FROM relevant_tables)=6
   AND to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NOT NULL
   AND to_regprocedure('public.check_execution_scope_v2(uuid,uuid,uuid,uuid)') IS NOT NULL
   THEN 'V41_HISTORICAL_BASELINE_PASS' ELSE 'REFUSED' END,
 'rows',(SELECT jsonb_agg(to_jsonb(r) ORDER BY name) FROM row_snapshots r),
 'catalog',(SELECT to_jsonb(c) FROM catalog_snapshot c),
 'write_performed',false,'row_content_returned',false
) AS v41_historical_baseline;
ROLLBACK;
