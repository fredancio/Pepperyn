-- v41-definition-crlf-1: exact reviewed bodies only, not general SQL normalization.
-- Raw fingerprints remain evidence. No prior inspection record is replaced.
BEGIN TRANSACTION READ ONLY;
WITH expected(name, arguments, result, defaults, definer, lf_hash, crlf_hash) AS (VALUES
 ('claim_generic_execution_v3','p_execution uuid, p_actor uuid, p_composition text','jsonb',NULL::text,true,'420ebbd115e06029e932cfe8c289f8102abb473cdd0f4dd4f626af3cc6d285ae','dde4fcc4d001b160a5fc3234cb8cbc58167a8b073f68babd5fe06b1bc51ab444'),
 ('close_generic_execution_v3','p_execution uuid, p_actor uuid','text',NULL,true,'d89cc5c10baa78c4d9389f4e971410d3eb4bec22bc41f0cdb9f11810628528d7','22b42dba0cf34b62333f69a0fa21b7c2a61587102e53ac65b0e3f0bcc00014ae'),
 ('complete_generic_execution_v3','p_execution uuid, p_actor uuid, p_claim uuid, p_receipt jsonb, p_analysis jsonb, p_envelope jsonb, p_envelope_text text','jsonb',NULL,true,'6e4c051d172b001373ea63218fc5d80d2894ab87a7c4fb085b0508287ec29857','3d12a27c23fd8dbb2f54f362ae8abbac74bb0a9a06be3dcfeabc732b56a9dd4d'),
 ('guard_generic_execution_v3','','trigger',NULL,false,'41a59ba0cf223915db3d42c44a935cd0470d61bef4dfa5a0bd8349c3705e9935','176f58d59f89bbbcd4d1eebd9257dd4ff81013c57484b500a1cf37b8fdfc9055'),
 ('reserve_generic_execution_v3','p_policy uuid, p_bindings jsonb, p_contract_binding jsonb, p_source_facts jsonb, p_projection_text text, p_filename text, p_ttl integer','jsonb','30',true,'9f66360c4e7320c9fd9c67ac079116aa6ba77396996588a7732280310d499a57','8db30acdc7edec04aca48b9348ade9099f9e1dd4c615b6032effcab74c574512')
), observed AS (
 SELECT e.*,p.oid,p.prosecdef,p.proconfig,l.lanname,
   pg_get_function_identity_arguments(p.oid) AS actual_arguments,
   pg_get_function_result(p.oid) AS actual_result,
   pg_get_expr(p.proargdefaults,0) AS actual_defaults,
   encode(sha256(convert_to(p.prosrc,'UTF8')),'hex') AS raw_sha256,
   encode(sha256(convert_to(replace(p.prosrc,chr(13)||chr(10),chr(10)),'UTF8')),'hex') AS lf_sha256,
   position(chr(13) IN replace(p.prosrc,chr(13)||chr(10),''))=0 AS no_bare_cr,
   has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
   has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
   has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM expected e LEFT JOIN pg_proc p ON p.proname=e.name AND p.pronamespace='public'::regnamespace
 LEFT JOIN pg_language l ON l.oid=p.prolang
), checked AS (
 SELECT *,COALESCE(oid IS NOT NULL AND raw_sha256 IN (lf_hash,crlf_hash)
   AND lf_sha256=lf_hash AND no_bare_cr AND actual_arguments=arguments
   AND actual_result=result AND actual_defaults IS NOT DISTINCT FROM defaults
   AND prosecdef=definer AND proconfig=ARRAY['search_path=pg_catalog, public']::text[]
   AND lanname='plpgsql' AND NOT anon_execute AND NOT authenticated_execute
   AND service_execute=definer,false) AS conformant
 FROM observed
)
SELECT jsonb_build_object('check_version','v41-definition-crlf-1',
 'status',CASE WHEN count(*)=5 AND count(DISTINCT name)=5 AND bool_and(conformant)
   THEN 'V41_DEFINITION_CONFORMANCE_PASS' ELSE 'REFUSED' END,
 'functions',jsonb_agg(jsonb_build_object('name',name,'raw_sha256',raw_sha256,
   'lf_sha256',lf_sha256,'conformant',conformant) ORDER BY name),
 'write_performed',false,'producer_admitted',false,'b1_global_proven',false)
FROM checked;
ROLLBACK;
