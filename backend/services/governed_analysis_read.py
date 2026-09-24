"""Ownership-bound application reads; no fixture, HTTP or provider dependency.

company_id is supplied by server authentication, never an HTTP request body.
This service is not an admission gate. Transport must still enforce admission.
"""
from uuid import UUID

from models.schemas import AnalyzeResponse
from services.governed_analysis_persistence import GovernedPersistenceRefused, load_governed_envelope
from services.governed_memory_read import recommendations_tracking


class GovernedReadRefused(RuntimeError):
    pass


def _one(response):
    rows = response.data
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise GovernedReadRefused("UNAVAILABLE")
    if len(rows) != 1:
        raise GovernedReadRefused("NOT_FOUND")
    return rows[0]


def load_owned_analysis(db, *, analysis_id: str, company_id: str):
    try:
        analysis_id, company_id = str(UUID(analysis_id)), str(UUID(company_id))
    except (ValueError, TypeError, AttributeError):
        raise GovernedReadRefused("NOT_FOUND") from None
    try:
        row = _one(db.from_("analyses").select("id,company_id,entity_id")
                   .eq("id", analysis_id).eq("company_id", company_id).limit(2).execute())
        if row.get("id") != analysis_id or row.get("company_id") != company_id:
            raise GovernedReadRefused("NOT_FOUND")
        entity_id = str(UUID(row["entity_id"]))
        entity = _one(db.from_("entities").select("id,company_id")
                      .eq("id", entity_id).eq("company_id", company_id).limit(2).execute())
        if entity.get("id") != entity_id or entity.get("company_id") != company_id:
            raise GovernedReadRefused("NOT_FOUND")
        engagement = _one(db.from_("engagements").select("id,entity_id")
                          .eq("entity_id", entity_id).limit(2).execute())
        if engagement.get("entity_id") != entity_id:
            raise GovernedReadRefused("NOT_FOUND")
        engagement_id = str(UUID(engagement["id"]))
        return load_governed_envelope(
            db, analysis_id=analysis_id, company_id=company_id,
            entity_id=entity_id, engagement_id=engagement_id,
        )
    except GovernedReadRefused:
        raise
    except GovernedPersistenceRefused as exc:
        if str(exc) == "GOVERNED_ANALYSIS_NOT_FOUND":
            raise GovernedReadRefused("NOT_FOUND") from None
        raise GovernedReadRefused("UNAVAILABLE") from None
    except Exception:
        raise GovernedReadRefused("UNAVAILABLE") from None


def read_owned_analysis(db, *, analysis_id: str, company_id: str) -> AnalyzeResponse:
    envelope = load_owned_analysis(db, analysis_id=analysis_id, company_id=company_id)
    analysis_id = str(UUID(analysis_id))
    # Fresh compatibility view; never mutate the immutable governed envelope.
    result = envelope.analysis_result
    result.id = analysis_id
    return AnalyzeResponse(
        success=True, message="Analyse gouvernée rechargée", analyse_id=analysis_id,
        result=result, tokens_used=0, cout_estime=0,
        recommendations_tracking=recommendations_tracking(envelope, analysis_id, db),
    )
