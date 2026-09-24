"""Legacy closed-synthetic compatibility; NOT a durable execution attestation.

Preserve the disclosures proven for that workflow. Generic callers must use
services.governed_output, which obtains its provenance from owned stored receipts.
"""
from services import governed_export_rendering as rendering

_LEGACY_DISCLOSURE = (
    ("Perimetre", "Donnees synthetiques uniquement"),
    ("Fournisseur", "Fournisseur simulé local"),
    ("Reseau externe", "Aucun réseau externe n'a été utilisé"),
)


def generate_governed_excel(envelope, analysis_id, decisions=None, *, temporal_comparison=None):
    return rendering.generate_governed_excel(envelope, analysis_id, decisions,
        metadata=_LEGACY_DISCLOSURE, temporal_comparison=temporal_comparison)


def generate_governed_pdf(envelope, analysis_id, decisions=None, *, temporal_comparison=None):
    return rendering.generate_governed_pdf(envelope, analysis_id, decisions,
        metadata=_LEGACY_DISCLOSURE, temporal_comparison=temporal_comparison)


def generate_governed_pptx(envelope, analysis_id, decisions=None, *, temporal_comparison=None):
    return rendering.generate_governed_pptx(envelope, analysis_id, decisions,
        metadata=_LEGACY_DISCLOSURE, temporal_comparison=temporal_comparison)
