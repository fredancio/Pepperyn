"""Bounded parity with the observed Integration Test analyses catalog.

Local SQL only; no historical exception is retroactively inferred from this test.
"""
import json
from uuid import uuid4

import pytest

from test_v40_postgres import (sql, pytestmark, COMPANY, ENTITY, literal, js,
                              setup, reserve, claim, bundle, finish, no_result)


def test_observed_column_types_nullability_and_constraints(sql):
    columns=json.loads(sql("""SELECT jsonb_object_agg(column_name,
      jsonb_build_array(data_type,is_nullable)) FROM information_schema.columns
      WHERE table_schema='public' AND table_name='analyses'"""))
    groups={
        'uuid':'id session_id company_id user_id entity_id',
        'text':'guest_token fichier_nom fichier_type type_document contexte_utilisateur mode excel_export_url excel_export_nom status error_message export_format decision_fingerprint decision_fingerprint_version source_data_hash decision_kernel_version',
        'integer':'fichier_taille_bytes score_confiance tokens_input tokens_output duree_traitement_ms chat_count',
        'jsonb':'analyse_json decision_kernel', 'numeric':'cout_estime_euros',
        'timestamp with time zone':'created_at',
    }
    expected={name:[kind,'NO' if name in {'id','company_id','chat_count'} else 'YES']
              for kind,names in groups.items() for name in names.split()}
    assert len(expected)==30 and columns==expected
    defaults=json.loads(sql("""SELECT jsonb_object_agg(column_name,column_default)
      FROM information_schema.columns WHERE table_schema='public' AND table_name='analyses'
      AND column_default IS NOT NULL"""))
    assert defaults=={'id':'gen_random_uuid()','mode':"'complete'::text",'analyse_json':"'{}'::jsonb",
                     'tokens_input':'0','tokens_output':'0','cout_estime_euros':'0',
                     'status':"'pending'::text",'created_at':'now()','chat_count':'0'}
    checks=json.loads(sql("""SELECT jsonb_agg(conname ORDER BY conname)
      FROM pg_constraint WHERE conrelid='analyses'::regclass"""))
    assert checks==sorted(['analyses_pkey','analyses_company_id_fkey','analyses_entity_id_fkey',
        'analyses_session_id_fkey','analyses_user_id_fkey','analyses_fichier_type_check',
        'analyses_mode_check','analyses_score_confiance_check','analyses_status_check',
        'analyses_type_document_check'])
    assert sql("SELECT count(*) FROM pg_trigger WHERE tgrelid='analyses'::regclass AND NOT tgisinternal")=='0'


@pytest.mark.parametrize('column,value,state,constraint',[
    ('type_document','FINANCIAL_WORKBOOK','23514','analyses_type_document_check'),
    ('fichier_type','exe','23514','analyses_fichier_type_check'),
    ('mode','mock','23514','analyses_mode_check'),
    ('status','SUCCESS','23514','analyses_status_check'),
    ('score_confiance',101,'23514','analyses_score_confiance_check'),
    ('score_confiance',-1,'23514','analyses_score_confiance_check'),
    ('session_id',str(uuid4()),'23503','analyses_session_id_fkey'),
    ('user_id',str(uuid4()),'23503','analyses_user_id_fkey'),
    ('company_id',str(uuid4()),'23503','analyses_company_id_fkey'),
    ('entity_id',str(uuid4()),'23503','analyses_entity_id_fkey'),
    ('chat_count',None,'23502','chat_count'),
    ('fichier_taille_bytes',2147483648,'22003','out of range'),
])
def test_database_detects_real_storage_incompatibilities(sql,column,value,state,constraint):
    row=dict(id=str(uuid4()),company_id=COMPANY,entity_id=ENTITY,type_document='AUTRE')
    row[column]=value
    values=','.join('NULL' if v is None else literal(v) for v in row.values())
    error=sql('\\set VERBOSITY verbose\n'+f"INSERT INTO analyses ({','.join(row)}) VALUES ({values})",fail=True)
    assert state in error and constraint in error
    assert sql(f"SELECT count(*) FROM analyses WHERE id={literal(row['id'])}")=='0'


def test_actual_v27_invalid_literal_sqlstate_and_v40_atomic_refusal(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    parts=list(bundle(case,c));parts[1]['type_document']='FINANCIAL_WORKBOOK'
    error=sql('\\set VERBOSITY verbose\n'+
        f"SELECT persist_governed_analysis_v1({js(parts[1])},{js(parts[2])})",fail=True)
    assert '23514' in error and 'analyses_type_document_check' in error
    assert 'persist_governed_analysis_v1' in error
    no_result(sql,case)
    assert finish(sql,case,c,parts)['status']=='REFUSED'
    no_result(sql,case)
    assert sql(f"SELECT state FROM execution_admissions_v2 WHERE execution_id={literal(case['b']['execution_id'])}")=='REFUSED'


def test_autre_preserves_rich_result_and_envelope(sql):
    case=setup(sql);r=reserve(sql,case);c=claim(sql,case,r)
    parts=list(bundle(case,c));parts[1]['type_document']='AUTRE'
    assert parts[1]['analyse_json']['type_document']=='FINANCIAL_WORKBOOK'
    assert finish(sql,case,c,parts)['status']=='COMPLETE'
    actual=json.loads(sql(f"SELECT jsonb_build_object('type',a.type_document,'result',a.analyse_json,'envelope',e.envelope_json) FROM analyses a JOIN governed_analysis_envelopes e ON a.id=e.analysis_id WHERE a.id={literal(case['b']['analysis_id'])}"))
    assert actual==dict(type='AUTRE',result=parts[1]['analyse_json'],envelope=parts[2]['envelope_json'])
