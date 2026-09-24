-- Read-only catalog inspection. No application rows or credentials read.
BEGIN TRANSACTION READ ONLY;
SELECT jsonb_build_object(
  'phase', 'V39_READ_ONLY_PREFLIGHT',
  'write_performed', false,
  'application_rows_read', false,
  'project_identity_verified', false,
  'checks', jsonb_build_object(
    'receipt_table_absent', to_regclass('public.governed_execution_receipts') IS NULL,
    'receipt_rpc_absent', to_regprocedure('public.persist_governed_execution_v1(jsonb,jsonb,jsonb)') IS NULL,
    'receipt_trigger_function_absent', to_regprocedure('public.reject_execution_receipt_mutation()') IS NULL,
    'envelope_present', to_regclass('public.governed_analysis_envelopes') IS NOT NULL,
    'v27_rpc_present', to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NOT NULL,
    'scope_indexes_present', to_regclass('public.uq_analyses_id_company_entity') IS NOT NULL
        AND to_regclass('public.uq_engagements_id_entity') IS NOT NULL,
    'schema_create_authorized', has_schema_privilege(current_user, 'public', 'CREATE'),
    'roles_present', (SELECT count(*) = 3 FROM pg_roles WHERE rolname IN ('anon','authenticated','service_role'))
  )
) AS v39_preflight;
ROLLBACK;
