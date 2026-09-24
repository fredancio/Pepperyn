"""Owned terminal composition, independent of sandbox and provider transport.

Authentication/admission are prerequisites imposed by the calling transport.
Renderers are not security capabilities: only this service loads authoritative
receipt/memory/temporal inputs; HTTP callers cannot supply metadata or envelopes.
"""
from uuid import UUID

from services.governed_analysis_read import GovernedReadRefused, load_owned_analysis_context
from services.governed_analysis_persistence import load_execution_provenance, _digest
from services.governed_memory_read import recommendations_tracking
from services.governed_temporal_continuity import load_governed_temporal_comparison
from services import governed_export_rendering as rendering


def load_owned_output(db, *, analysis_id: str, company_id: str):
    envelope, entity, engagement = load_owned_analysis_context(
        db, analysis_id=analysis_id, company_id=company_id)
    analysis_id, company_id = str(UUID(analysis_id)), str(UUID(company_id))
    try:
        receipt = load_execution_provenance(db, analysis_id=analysis_id, company_id=company_id,
                                          entity_id=entity, engagement_id=engagement)
        if receipt is not None and receipt.envelope_sha256 != _digest(envelope.model_dump(mode="json")):
            raise ValueError("OUTPUT_ENVELOPE_CHANGED")
        memory = recommendations_tracking(envelope, analysis_id, db, feedback_required=True)
        temporal = load_governed_temporal_comparison(db, analysis_id=analysis_id, company_id=company_id)
        provenance = {"status": "UNATTESTED", "receipt": None}
        metadata = (
            ("Perimetre", "Origine non attestee"), ("Fournisseur", "UNKNOWN"),
            ("Reseau externe", "UNKNOWN"),
            ("Provenance d'execution", "Aucun recu durable disponible; aucune requalification historique."),
        )
        if receipt is not None:
            provenance = {"status": "VERIFIED_RECEIPT", "receipt": receipt.model_dump(mode="json")}
            metadata = (
                ("Perimetre", "Donnees synthetiques enregistrees"),
                ("Fournisseur", "Fournisseur simule local"),
                ("Reseau externe", "Aucun transport fournisseur dans cet executeur local"),
                ("Provenance d'execution", "Recu durable verifie; pas une certification de l'infrastructure"),
                ("Execution UUID", str(receipt.execution_id)),
                ("Executeur", receipt.executor),
                ("Execution terminee", receipt.completed_at.isoformat()),
                ("Source brute SHA-256", receipt.raw_source_sha256),
                ("Representation SHA-256", receipt.source_representation_sha256),
                ("Enveloppe SHA-256", receipt.envelope_sha256),
            )
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
