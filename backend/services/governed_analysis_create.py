"""Owned upload orchestration with an explicitly selected trusted executor.

Not an admission authority. No executor supplied through request data, no legacy
save fallback, no retry on uncertain persistence. Analysis-processing execution
does not create a professional decision execution/outcome/learning.
"""
from uuid import UUID, uuid4
from hashlib import sha256

from services.governed_analysis_read import GovernedReadRefused, _one
from services.governed_analysis_persistence import save_governed_analysis


class GovernedCreateRefused(RuntimeError):
    def __init__(self, code, *, analysis_id=None):
        super().__init__(code)
        self.analysis_id = analysis_id


def create_owned_analysis(db, *, company_id, entity_id, raw, filename, executor, reserve=None):
    try:
        company_id, entity_id = str(UUID(company_id)), str(UUID(entity_id))
    except (ValueError, TypeError, AttributeError):
        raise GovernedCreateRefused('NOT_FOUND') from None
    try:
        entity = _one(db.from_('entities').select('id,company_id').eq('id',entity_id)
                      .eq('company_id',company_id).limit(2).execute())
        if entity.get('id') != entity_id or entity.get('company_id') != company_id:
            raise GovernedReadRefused('NOT_FOUND')
        engagement = _one(db.from_('engagements').select('id,entity_id').eq('entity_id',entity_id).limit(2).execute())
        if engagement.get('entity_id') != entity_id:
            raise GovernedReadRefused('NOT_FOUND')
        engagement_id = str(UUID(engagement['id']))
    except GovernedReadRefused as exc:
        raise GovernedCreateRefused(str(exc)) from None
    except Exception:
        raise GovernedCreateRefused('UNAVAILABLE') from None
    if not isinstance(raw, bytes) or not raw or len(raw) > 1_000_000:
        raise GovernedCreateRefused('INPUT_REFUSED')
    analysis_id = (reserve(db,company_id=company_id,entity_id=entity_id,engagement_id=engagement_id,
                           raw=raw,filename=filename) if reserve else str(uuid4()))
    try:
        execution = executor(raw, filename)
        if execution.provenance.raw_source_sha256 != sha256(raw).hexdigest().upper():
            raise ValueError('SOURCE_BINDING')
        result = execution.analysis.envelope.analysis_result.model_dump(mode='json')
    except Exception:
        raise GovernedCreateRefused('EXECUTION_REFUSED') from None
    result['id'] = analysis_id
    try:
        save_governed_analysis(db, analysis_row={
            'id':analysis_id,'company_id':company_id,'entity_id':entity_id,
            'fichier_nom':filename,'fichier_type':'xlsx','type_document':'AUTRE',
            'contexte_utilisateur':'','mode':'complete','analyse_json':result,
            'score_confiance':0,'tokens_input':0,'cout_estime_euros':0,'duree_traitement_ms':0,
            'status':'completed','chat_count':0,'source_data_hash':execution.provenance.raw_source_sha256.lower(),
            'fichier_taille_bytes':len(raw),
        }, engagement_id=engagement_id, envelope=execution.analysis.envelope,
           execution_provenance=execution.provenance)
    except Exception:
        raise GovernedCreateRefused('PERSISTENCE_UNCERTAIN', analysis_id=analysis_id) from None
    return {'analysis_id':analysis_id,'status':'PERSISTED','automatic_retry_permitted':False}
