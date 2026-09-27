"""Upload transport using server-owned executor/admission dependencies."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool
from services.governed_analysis_create import create_owned_analysis, GovernedCreateRefused


def build_governed_ingestion_router(*, authenticated_company, require_admission, database, executor, reserve=None):
    router = APIRouter(prefix='/api/governed', dependencies=[Depends(require_admission)])

    @router.post('/analyses', status_code=201)
    async def upload(file: UploadFile = File(...), entity_id: str = Form(...),
                     company: str = Depends(authenticated_company), db=Depends(database)):
        raw = await file.read(1_000_001)
        if len(raw) > 1_000_000:
            raise HTTPException(413, 'Classeur trop volumineux')
        try:
            return await run_in_threadpool(create_owned_analysis, db, company_id=company, entity_id=entity_id,
                raw=raw, filename=file.filename or '', executor=executor, reserve=reserve)
        except GovernedCreateRefused as exc:
            code = str(exc)
            status = 404 if code == 'NOT_FOUND' else 400 if code in {'INPUT_REFUSED','EXECUTION_REFUSED'} else 503
            raise HTTPException(status, {'code':code,'analysis_id':exc.analysis_id,
                                         'automatic_retry_permitted':False}) from None
    return router
