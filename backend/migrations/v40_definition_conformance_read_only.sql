-- v40-definition-crlf-1: exact reviewed bodies only, not general SQL normalization.
-- Raw fingerprints remain evidence. No prior inspection record is replaced.
BEGIN TRANSACTION READ ONLY;
WITH expected(name, arguments, result, defaults, definer, lf_hash, crlf_hash) AS (VALUES
 ('check_execution_scope_v2','p_actor uuid, p_company uuid, p_entity uuid, p_engagement uuid','void',NULL::text,false,'cc29b03aab84f711e0a8fa54ae20d1da90a3d10c1d26faed0f20cbe1affec0d1','e458b5fc0665f4ad6943fa846bec1519910d156a40d7b123b86ffbb7f8f5989c'),
 ('claim_execution_v2','p_execution uuid, p_actor uuid, p_composition text','jsonb',NULL,true,'3a170fde161d4a9ca4c7cc448b852f6b1dd76280f4cc0d3e26475eb854f5aade','aeaa04e6c2e28ccdb4299f78bac3ae8bfc3607fde43d91e80c3b7e576a0691e5'),
 ('close_execution_v2','p_execution uuid, p_actor uuid','text',NULL,true,'b406d4fbfd3339c96a152ff577a5ba4371e5421514691af13c2bd4d0a24092af','9509ee67927d6e009fd01c192cc64b0be0123215a35e56f4ad5c79ef117df965'),
 ('complete_execution_v2','p_execution uuid, p_actor uuid, p_claim uuid, p_candidate jsonb, p_analysis jsonb, p_envelope jsonb, p_envelope_text text','jsonb',NULL,true,'14643c0e8357ba0326a5c92d2c18aa5640b783ae3e597285cf3468fb006ad46c','c2ea21274c1617c4ca170943136e55618df280e38c786496d70e330b9b61cb07'),
 ('guard_prospective_execution_v2','','trigger',NULL,false,'e01317257ab2b8172d697d464ca13b1005cd57556e469a1ac499e852f221a65c','6c241cc8f425bc602dac4ce9d92467b0fdc731cf4c72a9cf411330acb390f65e'),
 ('reserve_execution_v2','p_policy uuid, p_bindings jsonb, p_input text, p_filename text, p_ttl integer','jsonb','30',true,'f0021960f852b5e61061d2626fa36e4a3cbfe8a21c2a0c12e012e19da50a1704','d1b37aefa86491aea73203b87f72715a1d05835a1f3fec20e2e05740312dab12')
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
 SELECT *, COALESCE(oid IS NOT NULL AND raw_sha256 IN (lf_hash,crlf_hash)
   AND lf_sha256=lf_hash AND no_bare_cr AND actual_arguments=arguments
   AND actual_result=result AND actual_defaults IS NOT DISTINCT FROM defaults
   AND prosecdef=definer AND proconfig=ARRAY['search_path=pg_catalog, public']::text[]
   AND lanname='plpgsql' AND NOT anon_execute AND NOT authenticated_execute
   AND service_execute=definer,false) AS conformant
 FROM observed
)
SELECT jsonb_build_object('check_version','v40-definition-crlf-1',
 'status',CASE WHEN count(*)=6 AND count(DISTINCT name)=6 AND bool_and(conformant)
   THEN 'BOUNDED_DEFINITION_CONFORMANCE_PASS' ELSE 'REFUSED' END,
 'functions',jsonb_agg(jsonb_build_object('name',name,'raw_sha256',raw_sha256,
   'lf_sha256',lf_sha256,'conformant',conformant) ORDER BY name),
 'write_performed',false,'producer_admitted',false,'b1_global_proven',false)
FROM checked;
ROLLBACK;
