-- ppr067-hardening-postflight-1
-- Exact structural verification after one separately authorized application of
-- prepared_v41_validation_hardening.sql. This script performs no write.
BEGIN TRANSACTION READ ONLY;

WITH expected_functions(
  name, arguments, result, defaults, definer, lf_hash, crlf_hash
) AS (VALUES
  ('claim_generic_execution_v3',
   'p_execution uuid, p_actor uuid, p_composition text',
   'jsonb', NULL::text, true,
   '420ebbd115e06029e932cfe8c289f8102abb473cdd0f4dd4f626af3cc6d285ae',
   'dde4fcc4d001b160a5fc3234cb8cbc58167a8b073f68babd5fe06b1bc51ab444'),
  ('close_generic_execution_v3',
   'p_execution uuid, p_actor uuid',
   'text', NULL::text, true,
   'd89cc5c10baa78c4d9389f4e971410d3eb4bec22bc41f0cdb9f11810628528d7',
   '22b42dba0cf34b62333f69a0fa21b7c2a61587102e53ac65b0e3f0bcc00014ae'),
  ('complete_generic_execution_v3',
   'p_execution uuid, p_actor uuid, p_claim uuid, p_receipt jsonb, p_analysis jsonb, p_envelope jsonb, p_envelope_text text',
   'jsonb', NULL::text, true,
   'aafa916300af7b47fe619c0e833515ef838a2fd35db3bb3a5ed45427c019cc32',
   'e10c16fc82af6e8b631b602f4defd4409ed057d5d055c7a162ec9e6e1aa0f287'),
  ('guard_generic_execution_v3',
   '', 'trigger', NULL::text, false,
   '41a59ba0cf223915db3d42c44a935cd0470d61bef4dfa5a0bd8349c3705e9935',
   '176f58d59f89bbbcd4d1eebd9257dd4ff81013c57484b500a1cf37b8fdfc9055'),
  ('reserve_generic_execution_v3',
   'p_policy uuid, p_bindings jsonb, p_contract_binding jsonb, p_source_facts jsonb, p_projection_text text, p_filename text, p_ttl integer',
   'jsonb', '30', true,
   'd8c004ce0b0df839929e55594c921610a65849c691e28fcd6b86fd05ea4a7e2d',
   '5e5b154d93146c7cce09778d558b00e3f6e0e336f487b8a480e29baed86e46c3')
), observed_functions AS (
  SELECT e.*, p.oid, p.prosecdef, p.proconfig, l.lanname,
    pg_get_userbyid(p.proowner) AS owner,
    pg_get_function_identity_arguments(p.oid) AS actual_arguments,
    pg_get_function_result(p.oid) AS actual_result,
    pg_get_expr(p.proargdefaults, 0) AS actual_defaults,
    encode(sha256(convert_to(p.prosrc, 'UTF8')), 'hex') AS raw_sha256,
    encode(sha256(convert_to(
      replace(p.prosrc, chr(13) || chr(10), chr(10)), 'UTF8'
    )), 'hex') AS lf_sha256,
    position(chr(13) IN replace(p.prosrc, chr(13) || chr(10), '')) = 0
      AS no_bare_cr,
    has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_execute,
    has_function_privilege('authenticated', p.oid, 'EXECUTE')
      AS authenticated_execute,
    has_function_privilege('service_role', p.oid, 'EXECUTE') AS service_execute
  FROM expected_functions e
  LEFT JOIN pg_proc p
    ON p.proname = e.name AND p.pronamespace = 'public'::regnamespace
  LEFT JOIN pg_language l ON l.oid = p.prolang
), function_checks AS (
  SELECT *, COALESCE(
    oid IS NOT NULL
    AND raw_sha256 IN (lf_hash, crlf_hash)
    AND lf_sha256 = lf_hash
    AND no_bare_cr
    AND actual_arguments = arguments
    AND actual_result = result
    AND actual_defaults IS NOT DISTINCT FROM defaults
    AND prosecdef = definer
    AND owner = 'postgres'
    AND proconfig = ARRAY['search_path=pg_catalog, public']::text[]
    AND lanname = 'plpgsql'
    AND NOT anon_execute
    AND NOT authenticated_execute
    AND service_execute = definer,
    false
  ) AS conformant
  FROM observed_functions
), expected_tables(name) AS (VALUES
  ('generic_producer_policies_v3'),
  ('generic_execution_admissions_v3'),
  ('generic_execution_receipts_v3')
), table_checks AS (
  SELECT e.name,
    c.oid IS NOT NULL AS present,
    COALESCE(c.relrowsecurity, false) AS rls_enabled,
    CASE WHEN c.oid IS NULL THEN NULL ELSE
      (SELECT count(*) FROM pg_trigger t
       WHERE t.tgrelid = c.oid AND NOT t.tgisinternal)
    END AS immutable_trigger_count,
    CASE WHEN c.oid IS NULL THEN NULL ELSE
      (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid)
    END AS policy_count,
    pg_get_userbyid(c.relowner) AS owner,
    has_table_privilege('anon', 'public.' || e.name, 'SELECT')
      AS anon_select,
    has_table_privilege('authenticated', 'public.' || e.name, 'SELECT')
      AS authenticated_select,
    has_table_privilege('service_role', 'public.' || e.name, 'SELECT')
      AS service_select,
    has_table_privilege('service_role', 'public.' || e.name, 'INSERT')
      AS service_insert,
    has_table_privilege('service_role', 'public.' || e.name, 'UPDATE')
      AS service_update,
    has_table_privilege('service_role', 'public.' || e.name, 'DELETE')
      AS service_delete
  FROM expected_tables e
  LEFT JOIN pg_class c ON c.oid = to_regclass('public.' || e.name)
), counts AS (
  SELECT
    (SELECT count(*) FROM public.generic_producer_policies_v3) AS policy_rows,
    (SELECT count(*) FROM public.generic_execution_admissions_v3)
      AS admission_rows,
    (SELECT count(*) FROM public.generic_execution_receipts_v3) AS receipt_rows
), verdict AS (
  SELECT
    (SELECT count(*) = 5 AND count(DISTINCT name) = 5
       AND bool_and(conformant) FROM function_checks)
    AND
    (SELECT count(*) = 3 AND count(DISTINCT name) = 3
       AND bool_and(
         present AND rls_enabled AND immutable_trigger_count = 1
         AND policy_count = 0 AND owner = 'postgres'
         AND NOT anon_select AND NOT authenticated_select
         AND service_select AND NOT service_insert
         AND NOT service_update AND NOT service_delete
       ) FROM table_checks)
    AND (SELECT policy_rows = 0 AND admission_rows = 0 AND receipt_rows = 0
         FROM counts) AS pass
)
SELECT jsonb_build_object(
  'check_version', 'ppr067-hardening-postflight-1',
  'status', CASE WHEN (SELECT pass FROM verdict)
    THEN 'PPR067_HARDENING_STRUCTURAL_POSTFLIGHT_PASS' ELSE 'REFUSED' END,
  'functions', (SELECT jsonb_agg(jsonb_build_object(
    'name', name, 'raw_sha256', raw_sha256, 'lf_sha256', lf_sha256,
    'conformant', conformant
  ) ORDER BY name) FROM function_checks),
  'tables', (SELECT jsonb_agg(to_jsonb(t) ORDER BY name) FROM table_checks t),
  'rows', (SELECT to_jsonb(c) FROM counts c),
  'write_performed', false,
  'producer_admitted', false,
  'b1_global_proven', false,
  'external_provider_used', false,
  'real_data_used', false
) AS ppr067_hardening_postflight;

ROLLBACK;
