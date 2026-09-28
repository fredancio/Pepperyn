"""Strict owned reread of durable V39 and V40 execution evidence.

This module is a reader, never an admission or execution capability.  Ownership
is established from the analysis and entity before either receipt registry is
consulted.  A present receipt must validate completely; it can never fall back
to legacy/unattested output.
"""
from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from uuid import UUID

from services.governed_analysis_persistence import (
    GovernedPersistenceRefused,
    _digest,
    load_execution_provenance,
    load_governed_envelope,
)
from services.governed_analysis_read import GovernedReadRefused, _one, load_owned_analysis_context
from services.producer_execution_contract import (
    ExecutionBindingsV2,
    ProducerExecutionCandidateV2,
    validate_candidate_consistency,
)

V40_RECEIPT_VERSION = "governed-execution-receipt-2"
V40_CONTRACT_VERSION = "local-synthetic-durable-admission-2"


def _uuid(value) -> str:
    return str(UUID(str(value)))


def _rows(query) -> list[dict]:
    rows = query.limit(2).execute().data
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows) or len(rows) > 1:
        raise ValueError("ambiguous registry response")
    return rows


def _aware(value) -> datetime:
    stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.utcoffset() is None:
        raise ValueError("naive timestamp")
    return stamp


def _owned_identity(db, analysis_id: str, company_id: str):
    analysis_id, company_id = _uuid(analysis_id), _uuid(company_id)
    analysis = _one(db.from_("analyses").select(
        "id,company_id,entity_id,source_data_hash,fichier_nom"
    ).eq("id", analysis_id).eq("company_id", company_id).limit(2).execute())
    if analysis.get("id") != analysis_id or analysis.get("company_id") != company_id:
        raise GovernedReadRefused("NOT_FOUND")
    entity_id = _uuid(analysis.get("entity_id"))
    entity = _one(db.from_("entities").select("id,company_id").eq(
        "id", entity_id).eq("company_id", company_id).limit(2).execute())
    if entity.get("id") != entity_id or entity.get("company_id") != company_id:
        raise GovernedReadRefused("NOT_FOUND")
    return analysis_id, company_id, entity_id, analysis


def _v39(db, *, analysis_id, company_id, entity_id, row):
    engagement_id = _uuid(row.get("engagement_id"))
    if any(row.get(key) != value for key, value in {
        "analysis_id": analysis_id, "company_id": company_id, "entity_id": entity_id,
    }.items()):
        raise ValueError("V39 scope mismatch")
    envelope = load_governed_envelope(db, analysis_id=analysis_id, company_id=company_id,
                                      entity_id=entity_id, engagement_id=engagement_id)
    receipt = load_execution_provenance(db, analysis_id=analysis_id, company_id=company_id,
                                        entity_id=entity_id, engagement_id=engagement_id)
    if receipt is None:
        raise ValueError("V39 receipt disappeared")
    projected = receipt.model_dump(mode="json")
    return envelope, engagement_id, {
        "status": "VERIFIED_RECEIPT", "receipt_version": "V39", "receipt": projected,
    }, (
        ("Version du recu", "V39 / execution-provenance-1"),
        ("Perimetre", "Donnees synthetiques enregistrees"),
        ("Fournisseur", "Fournisseur simule local / registered-workbook-mock-v1"),
        ("Reseau externe", "Aucun transport fournisseur dans cet executeur local"),
        ("Provenance d'execution", "Recu durable verifie (V39); pas une certification de l'infrastructure"),
        ("Execution UUID", str(receipt.execution_id)),
        ("Execution terminee", receipt.completed_at.isoformat()),
        ("Source brute SHA-256", receipt.raw_source_sha256),
        ("Representation SHA-256", receipt.source_representation_sha256),
        ("Enveloppe SHA-256", receipt.envelope_sha256),
    )


def _v40(db, *, analysis_id, company_id, entity_id, analysis, receipt_row):
    execution_id = _uuid(receipt_row.get("execution_id"))
    if receipt_row.get("analysis_id") != analysis_id:
        raise ValueError("V40 analysis mismatch")
    admissions = _rows(db.from_("execution_admissions_v2").select("*").eq(
        "execution_id", execution_id).eq("analysis_id", analysis_id))
    if len(admissions) != 1:
        raise ValueError("V40 admission unavailable")
    admission = admissions[0]
    policy_id = _uuid(admission.get("policy_id"))
    policies = _rows(db.from_("producer_policies_v2").select("*").eq("id", policy_id))
    if len(policies) != 1:
        raise ValueError("V40 policy unavailable")
    policy = policies[0]
    engagement_id = _uuid(admission.get("engagement_id"))
    envelope = load_governed_envelope(db, analysis_id=analysis_id, company_id=company_id,
                                      entity_id=entity_id, engagement_id=engagement_id)

    receipt = receipt_row.get("receipt")
    expected_receipt_keys = {
        "schema_version", "evidence_scope", "egress", "candidate", "composition_sha256",
        "policy_id", "issued_at", "claimed_at",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_receipt_keys:
        raise ValueError("V40 receipt shape")
    if (receipt.get("schema_version") != V40_RECEIPT_VERSION
            or receipt.get("evidence_scope") != "LOCAL_SYNTHETIC_ONLY"
            or receipt.get("egress") != "DENY"
            or _uuid(receipt.get("policy_id")) != policy_id
            or receipt.get("composition_sha256") != admission.get("composition_sha256")):
        raise ValueError("V40 receipt contract")

    candidate = ProducerExecutionCandidateV2.model_validate(receipt.get("candidate"))
    bindings = ExecutionBindingsV2.model_validate(admission.get("bindings"))
    validate_candidate_consistency(candidate, expected_bindings=bindings, envelope=envelope)
    if any(str(getattr(bindings, key)) != str(admission.get(key)) for key in (
        "request_id", "execution_id", "analysis_id", "actor_id", "company_id", "entity_id", "engagement_id",
    )):
        raise ValueError("V40 admission binding")
    if (str(bindings.execution_id) != execution_id or str(bindings.analysis_id) != analysis_id
            or str(bindings.company_id) != company_id or str(bindings.entity_id) != entity_id
            or admission.get("state") != "COMPLETE" or not admission.get("claim_id")
            or not admission.get("claimed_at") or not admission.get("terminal_at")):
        raise ValueError("V40 terminal scope")
    if (_aware(receipt.get("issued_at")) != _aware(admission.get("issued_at"))
            or _aware(receipt.get("claimed_at")) != _aware(admission.get("claimed_at"))
            or candidate.started_at < _aware(admission.get("claimed_at"))
            or candidate.completed_at > _aware(receipt_row.get("created_at"))
            or _aware(receipt_row.get("created_at")) > _aware(admission.get("terminal_at"))):
        raise ValueError("V40 chronology")

    specification = policy.get("specification")
    if (not isinstance(specification, dict)
            or type(policy.get("enabled")) is not bool
            or policy.get("contract_version") != V40_CONTRACT_VERSION
            or policy.get("origin") != "SYNTHETIC" or policy.get("egress") != "DENY"
            or policy.get("contract_sha256") != bindings.admission_contract_sha256
            or any(str(specification.get(key)) != str(getattr(bindings, key)) for key in (
                "company_id", "entity_id", "engagement_id", "producer_id", "producer_version",
                "task_id", "task_version",
            ))
            or specification.get("source_sha256") != bindings.raw_source_sha256
            or specification.get("filename") != admission.get("filename")):
        raise ValueError("V40 policy binding")
    source = json.loads(admission.get("input_text"))
    if (sha256(admission.get("input_text").encode()).hexdigest().upper()
            != bindings.producer_input_sha256
            or source != envelope.source_facts.model_dump(mode="json")
            or analysis.get("source_data_hash", "").upper() != bindings.raw_source_sha256
            or analysis.get("fichier_nom") != admission.get("filename")):
        raise ValueError("V40 source binding")

    projected = {
        "schema_version": V40_RECEIPT_VERSION,
        "execution_id": execution_id,
        "request_id": str(bindings.request_id),
        "producer_id": bindings.producer_id,
        "producer_version": bindings.producer_version,
        "task_id": bindings.task_id,
        "task_version": bindings.task_version,
        "contract_version": V40_CONTRACT_VERSION,
        "admission_contract_sha256": bindings.admission_contract_sha256,
        "evidence_scope": "LOCAL_SYNTHETIC_ONLY",
        "egress": "DENY",
        "transport": "NONE",
        "data_origin": "REGISTERED_SYNTHETIC",
        "raw_source_sha256": bindings.raw_source_sha256,
        "source_representation_sha256": bindings.source_representation_sha256,
        "producer_input_sha256": bindings.producer_input_sha256,
        "envelope_sha256": candidate.envelope_sha256,
        "composition_sha256": admission.get("composition_sha256"),
        "policy_id": policy_id,
        "policy_enabled_at_read": policy.get("enabled") is True,
        "completed_at": candidate.completed_at.isoformat(),
    }
    return envelope, engagement_id, {
        "status": "VERIFIED_RECEIPT", "receipt_version": "V40", "receipt": projected,
    }, (
        ("Version du recu", "V40 / governed-execution-receipt-2"),
        ("Perimetre", "Execution synthetique locale admise et persistee"),
        ("Fournisseur", f"Producteur synthetique local {bindings.producer_id} / {bindings.producer_version}"),
        ("Tache", f"{bindings.task_id} / {bindings.task_version}"),
        ("Reseau externe", "EGRESS DENY; aucun transport fournisseur"),
        ("Provenance d'execution", "Recu V40 durable verifie; producteur generique non admis"),
        ("Execution UUID", execution_id),
        ("Contrat d'admission", V40_CONTRACT_VERSION),
        ("Source brute SHA-256", bindings.raw_source_sha256),
        ("Representation SHA-256", bindings.source_representation_sha256),
        ("Entree producteur SHA-256", bindings.producer_input_sha256),
        ("Enveloppe SHA-256", candidate.envelope_sha256),
        ("Composition SHA-256", admission.get("composition_sha256")),
    )


def load_owned_versioned_execution(db, *, analysis_id: str, company_id: str):
    """Return envelope plus terminal provenance; refuse any present invalid evidence."""
    try:
        analysis_id, company_id, entity_id, analysis = _owned_identity(db, analysis_id, company_id)
        v39 = _rows(db.from_("governed_execution_receipts").select(
            "analysis_id,company_id,entity_id,engagement_id"
        ).eq("analysis_id", analysis_id).eq("company_id", company_id).eq("entity_id", entity_id))
        v40 = _rows(db.from_("execution_receipts_v2").select(
            "execution_id,analysis_id,receipt,created_at"
        ).eq("analysis_id", analysis_id))
        if v39 and v40:
            raise ValueError("multiple receipt versions")
        if v39:
            return _v39(db, analysis_id=analysis_id, company_id=company_id,
                        entity_id=entity_id, row=v39[0])
        if v40:
            return _v40(db, analysis_id=analysis_id, company_id=company_id,
                        entity_id=entity_id, analysis=analysis, receipt_row=v40[0])
        envelope, _, engagement_id = load_owned_analysis_context(
            db, analysis_id=analysis_id, company_id=company_id)
        return envelope, engagement_id, {"status": "UNATTESTED", "receipt": None}, (
            ("Version du recu", "Aucun"),
            ("Perimetre", "Origine non attestee"),
            ("Fournisseur", "UNKNOWN"),
            ("Reseau externe", "UNKNOWN"),
            ("Provenance d'execution", "Aucun recu durable disponible; aucune requalification historique."),
        )
    except GovernedReadRefused:
        raise
    except GovernedPersistenceRefused:
        raise GovernedReadRefused("UNAVAILABLE") from None
    except Exception:
        raise GovernedReadRefused("UNAVAILABLE") from None
