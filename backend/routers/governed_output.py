"""Unmounted Beta read/export transport; no implicit admission defaults.

main.py intentionally does not mount this factory. Production integration must
provide real authenticated-company resolution AND the independently approved
admission dependency. Neither a URL parameter nor an environment flag is a grant.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from services.governed_analysis_read import GovernedReadRefused
from services.governed_output import read_owned_output, export_owned_output


def build_governed_output_router(*, authenticated_company, require_admission, database):
    router = APIRouter(prefix="/api/governed", dependencies=[Depends(require_admission)])

    def refuse(exc):
        code = 404 if str(exc) in {"NOT_FOUND", "FORMAT_REFUSED"} else 503
        return HTTPException(code, "Ressource introuvable" if code == 404 else "Lecture gouvernee indisponible")

    @router.get("/analyses/{analysis_id}")
    def read(analysis_id: str, company: str = Depends(authenticated_company), db=Depends(database)):
        try:
            return read_owned_output(db, analysis_id=analysis_id, company_id=company)
        except GovernedReadRefused as exc:
            raise refuse(exc) from None

    @router.get("/analyses/{analysis_id}/export.{format}")
    def export(analysis_id: str, format: str, company: str = Depends(authenticated_company), db=Depends(database)):
        try:
            content = export_owned_output(db, analysis_id=analysis_id, company_id=company, format=format)
        except GovernedReadRefused as exc:
            raise refuse(exc) from None
        media = {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
        return Response(content, media_type=media[format],
                        headers={"Content-Disposition": f'attachment; filename="governed-analysis.{format}"'})

    return router
