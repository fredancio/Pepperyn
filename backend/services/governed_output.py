"""Owned terminal composition, independent of sandbox and provider transport.

Authentication/admission are prerequisites imposed by the calling transport.
Renderers are not security capabilities: only this service loads authoritative
receipt/memory/temporal inputs; HTTP callers cannot supply metadata or envelopes.
"""
from uuid import UUID

from services.governed_analysis_read import GovernedReadRefused
from services.governed_execution_reread import load_owned_versioned_execution
from services.governed_memory_read import recommendations_tracking
from services.governed_temporal_continuity import load_governed_temporal_comparison
from services import governed_export_rendering as rendering


def load_owned_output(db, *, analysis_id: str, company_id: str):
    analysis_id, company_id = str(UUID(analysis_id)), str(UUID(company_id))
    envelope, _, provenance, metadata = load_owned_versioned_execution(
        db, analysis_id=analysis_id, company_id=company_id)
    try:
        memory = recommendations_tracking(envelope, analysis_id, db, feedback_required=True)
        temporal = load_governed_temporal_comparison(db, analysis_id=analysis_id, company_id=company_id)
        return envelope, {"analysis_id": analysis_id, "execution_provenance": provenance,
                          "recommendations_tracking": memory, "temporal_comparison": temporal}, metadata
    except Exception:
        raise GovernedReadRefused("UNAVAILABLE") from None


def read_owned_output(db, *, analysis_id: str, company_id: str):
    envelope, output, _ = load_owned_output(db, analysis_id=analysis_id, company_id=company_id)
    result = envelope.analysis_result
    result.id = output["analysis_id"]
    return dict(output, result=result.model_dump(mode="json"))


def export_owned_output(db, *, analysis_id: str, company_id: str, format: str) -> bytes:
    renderers = {"xlsx": rendering.generate_governed_excel,
                 "pdf": rendering.generate_governed_pdf, "pptx": rendering.generate_governed_pptx}
    if format not in renderers:
        raise GovernedReadRefused("FORMAT_REFUSED")
    envelope, output, metadata = load_owned_output(db, analysis_id=analysis_id, company_id=company_id)
    decisions = [item for item in output["recommendations_tracking"] if item.get("decision_confirmed_at")]
    try:
        return renderers[format](envelope, output["analysis_id"], decisions, metadata=metadata,
                                 temporal_comparison=output["temporal_comparison"])
    except Exception:
        raise GovernedReadRefused("UNAVAILABLE") from None
