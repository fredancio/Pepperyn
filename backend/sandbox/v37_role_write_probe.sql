-- Bounded database-role proof, NOT a real JWT/PostgREST session proof.
-- Every DML predicate is false: no row can be inserted/updated/deleted even on failure.
BEGIN;
SET LOCAL statement_timeout = '15s';
DO $probe$
DECLARE
    user_id uuid;
    account_email text;
    denied integer := 0;
BEGIN
    FOREACH account_email IN ARRAY ARRAY[
        'pepperyn-isolation-a24-a@pepperyn-test.invalid',
        'pepperyn-isolation-a24-b@pepperyn-test.invalid'] LOOP
        SELECT id INTO STRICT user_id FROM auth.users WHERE email = account_email;
        PERFORM set_config('request.jwt.claims', json_build_object('sub',user_id,'role','authenticated')::text,true);
        EXECUTE 'SET LOCAL ROLE authenticated';
        IF current_user <> 'authenticated' OR auth.uid() IS DISTINCT FROM user_id THEN
            RAISE EXCEPTION 'V37_PROBE_IDENTITY_REFUSED';
        END IF;
        BEGIN
            INSERT INTO public.decision_feedback (company_id,report_id,recommendation_id,recommendation_text)
                SELECT NULL::uuid,NULL::uuid,'V37_NO_ROW_PROBE','Synthetic no-row probe' WHERE false;
            RAISE EXCEPTION 'V37_INSERT_NOT_DENIED';
        EXCEPTION WHEN insufficient_privilege THEN denied := denied + 1;
        END;
        BEGIN
            UPDATE public.decision_feedback SET comment = 'V37_NO_ROW_PROBE' WHERE false;
            RAISE EXCEPTION 'V37_UPDATE_NOT_DENIED';
        EXCEPTION WHEN insufficient_privilege THEN denied := denied + 1;
        END;
        BEGIN
            DELETE FROM public.decision_feedback WHERE false;
            RAISE EXCEPTION 'V37_DELETE_NOT_DENIED';
        EXCEPTION WHEN insufficient_privilege THEN denied := denied + 1;
        END;
        EXECUTE 'RESET ROLE';
    END LOOP;
    IF denied <> 6 THEN RAISE EXCEPTION 'V37_DENIAL_COUNT_REFUSED'; END IF;
END;
$probe$;
SELECT jsonb_build_object('status','V37_TWO_IDENTITIES_SQL_ROLE_DML_DENIED',
    'denied_operations',6,'authority','SQL_SET_LOCAL_ROLE_AND_CLAIMS_NOT_JWT_SESSIONS',
    'business_write_performed',false,'api_write_isolation_proven',false,
    'global_isolation_proven',false,'production_proof',false) AS result;
ROLLBACK;
