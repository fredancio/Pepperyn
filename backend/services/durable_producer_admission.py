"""V40 RPC adapter, unmounted and synthetic-only. No producer/transport dispatch.

An acknowledgment is necessary but does not open a product/provider/data gate.
Each call is attempted once. Uncertain state requires inspection, never retry,
new IDs, cleanup or fallback to V39/receipt-less persistence.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID

from services.governed_analysis_persistence import _binding, _canonical_bytes, _digest
from services.producer_execution_contract import (
    ExecutionBindingsV2, ProducerExecutionCandidateV2, validate_candidate_consistency,
)
from services.v1_analysis_contract import GovernedAnalysisEnvelope
from services.governed_producer_admission import DURABLE_CONTRACT


class DurableAdmissionRefused(ValueError):
    pass


@dataclass(frozen=True)
class ReservedExecution:
    bindings: ExecutionBindingsV2
    composition_sha256: str
    filename: str


@dataclass(frozen=True)
class ClaimedExecution:
    reservation: ReservedExecution
    claim_id: UUID
    claimed_at: datetime
    input_text: str


class DurableProducerAdmission:
    """Trusted composition only. No HTTP body can supply a policy or authority.

    preparation is the existing authenticated/local synthetic composer. A policy
    must separately exist and be enabled in the new registry. None is installed
    by the migration. This adapter itself never registers or activates one.
    """
    def __init__(self, db, *, preparation, policy_id):
        if getattr(preparation, '_contract_policy', None) != DURABLE_CONTRACT:
            raise DurableAdmissionRefused("DISTINCT_DURABLE_CONTRACT_REQUIRED")
        self._db = db
        self._preparation = preparation
        self._policy_id = str(UUID(str(policy_id)))

    def _actor(self, authorization, bindings):
        principal = self._preparation._principal(authorization)
        if (principal.principal_id != str(bindings.actor_id)
                or principal.company_id != str(bindings.company_id)):
            raise DurableAdmissionRefused("DURABLE_ACTOR_REFUSED")
        return principal.principal_id

    def reserve(self, prepared, *, authorization, raw):
        try:
            text = self._preparation.consume_for_local_validation(prepared, authorization=authorization, raw=raw)
            b = ExecutionBindingsV2.model_validate(prepared.bindings)
            response = self._db.rpc("reserve_execution_v2", dict(
                p_policy=self._policy_id, p_bindings=b.model_dump(mode="json"),
                p_input=text, p_filename=prepared.filename, p_ttl=300)).execute().data
            digest = response.get("composition_sha256", "")
            if (response.get("status") != "RESERVED" or response.get("execution_id") != str(b.execution_id)
                    or len(digest) != 64 or any(c not in "0123456789ABCDEF" for c in digest)):
                raise ValueError("ack")
            return ReservedExecution(b, digest, prepared.filename)
        except Exception:
            raise DurableAdmissionRefused("DURABLE_RESERVATION_UNCERTAIN_NO_RETRY") from None

    def claim(self, reservation, *, authorization):
        try:
            b = reservation.bindings
            actor = self._actor(authorization, b)
            data = self._db.rpc("claim_execution_v2", dict(p_execution=str(b.execution_id), p_actor=actor,
                p_composition=reservation.composition_sha256)).execute().data
            text = data.get("input_text")
            stamp = datetime.fromisoformat(data["claimed_at"])
            if (data.get("status") != "CLAIMED" or data.get("execution_id") != str(b.execution_id)
                    or ExecutionBindingsV2.model_validate(data.get("bindings")) != b
                    or data.get("composition_sha256") != reservation.composition_sha256
                    or type(text) is not str or sha256(text.encode()).hexdigest().upper() != b.producer_input_sha256
                    or stamp.utcoffset() is None):
                raise ValueError("ack")
            return ClaimedExecution(reservation, UUID(data["claim_id"]), stamp, text)
        except Exception:
            raise DurableAdmissionRefused("DURABLE_CLAIM_UNCERTAIN_DO_NOT_EXECUTE") from None

    def complete(self, claimed, *, authorization, envelope):
        """Validate output, build provenance in backend, then make ONE atomic call.

        This does not invoke a producer, certify financial reliability or make a
        candidate independently authoritative. SQL checks the durable claim.
        """
        try:
            b = claimed.reservation.bindings
            actor = self._actor(authorization, b)
            envelope = GovernedAnalysisEnvelope.model_validate(envelope.model_dump(mode="json"))
            if (envelope.source_facts.model_dump(mode="json")
                    != json.loads(claimed.input_text)
                    or envelope.governed_analysis.invocation_nonce != b.request_id.hex.upper()):
                raise ValueError("input/request binding")
            payload = envelope.model_dump(mode="json")
            digest = _digest(payload)
            candidate = ProducerExecutionCandidateV2(bindings=b, envelope_sha256=digest,
                started_at=claimed.claimed_at, completed_at=datetime.now(timezone.utc))
            validate_candidate_consistency(candidate, expected_bindings=b, envelope=envelope)
            result = envelope.analysis_result.model_dump(mode="json")
            result['id'] = str(b.analysis_id)
            analysis = dict(id=str(b.analysis_id),company_id=str(b.company_id),entity_id=str(b.entity_id),
                # Legacy storage taxonomy, as in the V39 composite-workbook path.
                # The detailed FINANCIAL_WORKBOOK result and governed source are
                # preserved unchanged in analyse_json and envelope_json.
                fichier_nom=claimed.reservation.filename,fichier_type='xlsx',type_document='AUTRE',
                analyse_json=result,source_data_hash=b.raw_source_sha256.lower(),status='completed')
            envelope_row = dict(analysis_id=str(b.analysis_id),company_id=str(b.company_id),entity_id=str(b.entity_id),
                engagement_id=str(b.engagement_id),envelope_json=payload,envelope_sha256=digest,
                source_representation_sha256=b.source_representation_sha256,envelope_schema_version='v1-governed-analysis-1',
                binding_sha256=_binding(analysis_id=str(b.analysis_id),company_id=str(b.company_id),
                    entity_id=str(b.entity_id),engagement_id=str(b.engagement_id),envelope_sha256=digest,
                    source_sha256=b.source_representation_sha256))
            response = self._db.rpc("complete_execution_v2", dict(p_execution=str(b.execution_id),p_actor=actor,
                p_claim=str(claimed.claim_id),p_candidate=candidate.model_dump(mode="json"),p_analysis=analysis,
                p_envelope=envelope_row,p_envelope_text=_canonical_bytes(payload).decode())).execute().data
            if response.get('status') != 'COMPLETE' or response.get('analysis_id') != str(b.analysis_id):
                raise ValueError("not completed")
            return {"analysis_id": str(b.analysis_id), "status": "LOCAL_SYNTHETIC_PERSISTED",
                    "generic_producer_admitted": False}
        except Exception:
            raise DurableAdmissionRefused("DURABLE_COMPLETION_REFUSED_OR_UNCERTAIN_NO_RETRY") from None
