-- Run only after visually confirming Pepperyn Integration Test project identity.
BEGIN TRANSACTION READ ONLY;
WITH checks AS (
 SELECT
   current_setting('server_version_num')::int >= 140000 AS supported_postgresql,
   has_schema_privilege(current_user,'public','CREATE') AS schema_create_authorized,
   NOT EXISTS (
     SELECT 1 FROM (VALUES ('profiles','id'),('profiles','company_id'),('companies','id'),
       ('entities','id'),('entities','company_id'),('engagements','id'),('engagements','entity_id')) r(t,c)
     WHERE NOT EXISTS (SELECT 1 FROM information_schema.columns x WHERE x.table_schema='public'
       AND x.table_name=r.t AND x.column_name=r.c AND x.data_type='uuid')
   ) AS scope_uuid_columns,
   (SELECT count(*)=3 FROM pg_roles WHERE rolname IN ('anon','authenticated','service_role')) AS roles_present,
   to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NOT NULL AS v27_present,
   to_regprocedure('public.persist_governed_execution_v1(jsonb,jsonb,jsonb)') IS NOT NULL AS v39_present,
   NOT EXISTS (SELECT 1 FROM (VALUES ('producer_policies_v2'),('execution_admissions_v2'),('execution_receipts_v2')) t(n)
     WHERE to_regclass('public.'||t.n) IS NOT NULL) AS new_tables_absent,
   NOT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
     WHERE n.nspname='public' AND p.proname IN ('guard_prospective_execution_v2','check_execution_scope_v2',
       'reserve_execution_v2','claim_execution_v2','close_execution_v2','complete_execution_v2')) AS new_functions_absent
), report AS (SELECT to_jsonb(checks) AS checks FROM checks)
SELECT jsonb_build_object('phase','V40_READ_ONLY_PREFLIGHT','checks',checks,
  'status',CASE WHEN NOT EXISTS(SELECT 1 FROM jsonb_each(checks) WHERE value IS DISTINCT FROM 'true'::jsonb)
    THEN 'PREFLIGHT_PASS' ELSE 'REFUSED' END,
  'write_performed',false,'application_rows_read',false,'project_identity_verified',false,
  'producer_admitted',false) AS v40_preflight FROM report;
ROLLBACK;
