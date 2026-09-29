BEGIN READ ONLY;
SELECT jsonb_build_object(
  'phase','V41_READ_ONLY_PRECHECK',
  'status',CASE WHEN
    to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NOT NULL
    AND to_regprocedure('public.check_execution_scope_v2(uuid,uuid,uuid,uuid)') IS NOT NULL
    AND to_regclass('public.execution_receipts_v2') IS NOT NULL
    AND to_regclass('public.generic_producer_policies_v3') IS NULL
    AND to_regclass('public.generic_execution_admissions_v3') IS NULL
    AND to_regclass('public.generic_execution_receipts_v3') IS NULL
    THEN 'PREFLIGHT_PASS' ELSE 'REFUSED' END,
  'checks',jsonb_build_object(
    'V40_PREREQUISITES_PRESENT',
      to_regprocedure('public.check_execution_scope_v2(uuid,uuid,uuid,uuid)') IS NOT NULL
      AND to_regclass('public.execution_receipts_v2') IS NOT NULL,
    'PERSISTENCE_PRESENT',to_regprocedure('public.persist_governed_analysis_v1(jsonb,jsonb)') IS NOT NULL,
    'V41_OBJECTS_ABSENT',to_regclass('public.generic_producer_policies_v3') IS NULL
      AND to_regclass('public.generic_execution_admissions_v3') IS NULL
      AND to_regclass('public.generic_execution_receipts_v3') IS NULL
  ),
  'write_performed',false,
  'migration_applied',false
) AS v41_preflight;
ROLLBACK;
