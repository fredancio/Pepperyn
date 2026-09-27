"""Explicitly closed-by-default Integration wiring, not Beta admission.

The generic orchestrator/transport is reusable. Its ONLY installed executor is
the V39 registered synthetic mock. No widening of its admission or of the existing
synthetic-company designation. Activating the flag requires Founder approval.
"""
import os
from uuid import UUID
from fastapi import Header, HTTPException, Request
from services.governed_rehearsal_permit import RehearsalPermit

URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'


def mount_governed_pipeline(app, *, database, resolve_auth):
    if os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT', '0') != '1':
        return False

    def configuration():
        try:
            designation = str(UUID(os.getenv('PEPPERYN_SYNTHETIC_V1_COMPANY_ID','')))
        except ValueError:
            raise HTTPException(503, 'Parcours gouverne ferme') from None
        if (os.getenv('PEPPERYN_GOVERNED_PIPELINE_TRANSPORT') != '1'
                or os.getenv('ENVIRONMENT') != 'development'
                or os.getenv('SUPABASE_URL','').rstrip('/') != URL
                or os.getenv('PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO') != '1'):
            raise HTTPException(503, 'Parcours gouverne ferme')
        return designation

    # Misconfigured opt-in refuses startup, not a silent activation elsewhere.
    designation = configuration()
    permit = RehearsalPermit(os.getenv('PEPPERYN_GOVERNED_REHEARSAL_MANIFEST',''),designation)

    def admission(request: Request):
        configuration()
        try:
            permit.check()
            if not request.client or request.client.host not in {'127.0.0.1','::1'}:
                raise ValueError('LOOPBACK_ONLY')
            if request.method != 'POST' and request.path_params.get('analysis_id') != permit.data['analysis_id']:
                raise ValueError('REHEARSAL_ONLY')
        except Exception:
            raise HTTPException(503,'Repetition fermee ou hors perimetre') from None

    async def company(authorization: str | None = Header(default=None),
                      x_auth_type: str | None = Header(default=None)):
        designation = configuration()
        company_id, _, auth_type = await resolve_auth(authorization, x_auth_type)
        if auth_type == 'guest' or company_id != designation:
            raise HTTPException(404, 'Ressource introuvable')
        return company_id

    from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
    from routers.governed_output import build_governed_output_router
    from routers.governed_ingestion import build_governed_ingestion_router
    dependencies = dict(authenticated_company=company, require_admission=admission, database=database)
    app.include_router(build_governed_ingestion_router(**dependencies, executor=run_recorded_registered_mock_analysis,
                                                     reserve=permit.reserve))
    app.include_router(build_governed_output_router(**dependencies))
    return True
