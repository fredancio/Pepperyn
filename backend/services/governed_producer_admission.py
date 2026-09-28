"""Uninstalled, local synthetic admission-composition preparation.

Reuses backend Auth.get_user, authoritative ownership and existing capability
registry. NO generic producer is admitted, no persistence/egress method exists.
The capability is process-local and cannot support a distributed Beta launch.
Trusted backend composition chooses the profile; never accept it from HTTP.
"""
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID, uuid4

from pydantic import Field

from services.governed_analysis_read import _one
from services.governed_analysis_persistence import _digest
from services.governed_workbook_ingestion import ingest_governed_workbook
from services.ownership_authority import OwnershipAuthority, OwnershipRecord, OwnershipScope
from services.producer_execution_contract import ExecutionBindingsV2, _Closed, Digest, VersionedName


class AdmissionRefused(ValueError):
    pass


PREPARATION_CONTRACT = "LOCAL_SYNTHETIC_NO_EGRESS_NO_PERSISTENCE_V1"
DURABLE_CONTRACT = "LOCAL_SYNTHETIC_DURABLE_CANDIDATE_V2"


class LocalSyntheticProfile(_Closed):
    """Server-owned bounded policy, not an API parameter or self-registration."""
    company_id: UUID
    entity_id: UUID
    engagement_id: UUID
    producer_id: VersionedName
    producer_version: VersionedName
    task_id: VersionedName
    task_version: VersionedName
    source_sha256: Digest
    filename: str = Field(min_length=6, max_length=180, pattern=r"^[a-zA-Z0-9_.-]+\.xlsx$")


@dataclass(frozen=True)
class PreparedComposition:
    authorization: object
    bindings: ExecutionBindingsV2
    input_json: str
    filename: str


class _ProspectiveRepository:
    def __init__(self, db):
        self.db = db

    def resolve_prospective(self, scope):
        db = self.db
        company = _one(db.from_("companies").select("id").eq("id", scope.company_id).limit(2).execute())
        entity = _one(db.from_("entities").select("id,company_id")
                      .eq("id", scope.entity_id).eq("company_id", scope.company_id).limit(2).execute())
        engagement = _one(db.from_("engagements").select("id,entity_id")
                          .eq("id", scope.engagement_id).eq("entity_id", scope.entity_id).limit(2).execute())
        if (company.get("id") != scope.company_id or entity.get("id") != scope.entity_id
                or entity.get("company_id") != scope.company_id
                or engagement.get("id") != scope.engagement_id
                or engagement.get("entity_id") != scope.entity_id):
            raise AdmissionRefused("PARENT_BINDING_REFUSED")
        # Any pre-existing or partial identity prevents reuse; this is not a lock.
        for table, key in (("analyses", "id"), ("governed_analysis_envelopes", "analysis_id"),
                           ("governed_execution_receipts", "analysis_id")):
            rows = db.from_(table).select(key).eq(key, scope.analysis_id).limit(1).execute().data
            if not isinstance(rows, list) or rows:
                raise AdmissionRefused("PROSPECTIVE_ID_UNAVAILABLE")
        return OwnershipRecord(scope.analysis_id, scope.company_id, scope.entity_id,
                               scope.engagement_id, scope.company_id, scope.entity_id)


def _commitment(prepared):
    return _digest({"bindings": prepared.bindings.model_dump(mode="json"),
                    "input_json": prepared.input_json, "filename": prepared.filename,
                    "policy": "LOCAL_SYNTHETIC_NO_EGRESS_NO_PERSISTENCE_V1"})


class LocalProducerAdmissionPreparation:
    """No production registration exists. Constructor is trusted composition.

    A known hash does not prove synthetic origin: the configured profile must be
    supplied only by trusted local synthetic test/rehearsal composition. This
    class is not mounted and exposes no general source-registration endpoint.
    """
    def __init__(self, db, *, profile: LocalSyntheticProfile, ttl_seconds=30, contract_policy=PREPARATION_CONTRACT, identity_source=None):
        if contract_policy not in {PREPARATION_CONTRACT, DURABLE_CONTRACT}:
            raise AdmissionRefused("UNSUPPORTED_COMPOSITION_CONTRACT")
        self._db = db
        # Trusted backend constructor only, never a prepare()/HTTP parameter.
        # A rehearsal may consume a prechecked one-shot identity allocation.
        self._identity_source = identity_source
        self._contract_policy = contract_policy
        self._profile = LocalSyntheticProfile.model_validate_json(profile.model_dump_json())
        self._authority = OwnershipAuthority(_ProspectiveRepository(db), ttl_seconds=ttl_seconds)

    def _principal(self, authorization):
        if (not isinstance(authorization, str) or not authorization.startswith("Bearer ")
                or not authorization[7:].strip()):
            raise AdmissionRefused("AUTHENTICATION_REQUIRED")
        user = self._db.auth.get_user(authorization[7:]).user
        actor = str(UUID(user.id))
        profile = _one(self._db.from_("profiles").select("id,company_id")
                       .eq("id", actor).limit(2).execute())
        if profile.get("id") != actor:
            raise AdmissionRefused("ACTOR_BINDING_REFUSED")
        company = str(UUID(profile["company_id"]))
        return self._authority._accept_authenticated_principal(actor, company)

    def prepare(self, *, authorization, entity_id, engagement_id, raw, filename):
        try:
            principal = self._principal(authorization)
            p = self._profile
            if ((principal.company_id, str(UUID(entity_id)), str(UUID(engagement_id)))
                    != (str(p.company_id), str(p.entity_id), str(p.engagement_id))):
                raise AdmissionRefused("SCOPE_REFUSED")
            if (type(raw) is not bytes or filename != p.filename
                    or sha256(raw).hexdigest().upper() != p.source_sha256):
                raise AdmissionRefused("SOURCE_REFUSED")
            # Resolve authority before the parser observes the source.
            ids = self._identity_source() if self._identity_source is not None else (uuid4(), uuid4(), uuid4())
            if (type(ids) is not tuple or len(ids) != 3 or any(type(v) is not UUID for v in ids)
                    or (self._identity_source is not None and len(set(ids)) != 3)):
                raise AdmissionRefused("IDENTITY_ALLOCATION_REFUSED")
            analysis_id, request_id, execution_id = ids
            scope = OwnershipScope(principal.company_id, str(p.entity_id), str(p.engagement_id), str(analysis_id))
            self._authority._repository.resolve_prospective(scope)
            ingested = ingest_governed_workbook(raw, filename)
            if ingested.understanding.status != "UNDERSTOOD":
                raise AdmissionRefused("UNDERSTANDING_REFUSED")
            # Immutable exact input; not the parser's mutable local representation.
            input_json = ingested.understanding.model_dump_json()
            bindings = ExecutionBindingsV2(
                request_id=request_id, execution_id=execution_id, actor_id=principal.principal_id,
                analysis_id=scope.analysis_id, company_id=scope.company_id,
                entity_id=scope.entity_id, engagement_id=scope.engagement_id,
                producer_id=p.producer_id, producer_version=p.producer_version,
                task_id=p.task_id, task_version=p.task_version,
                admission_contract_sha256=_digest({"profile": p.model_dump(mode="json"),
                    "policy": self._contract_policy}),
                raw_source_sha256=ingested.source_sha256,
                source_representation_sha256=ingested.understanding.source_representation_sha256,
                producer_input_sha256=sha256(input_json.encode()).hexdigest().upper(),
            )
            prepared = PreparedComposition(None, bindings, input_json, filename)
            grant = self._authority.authorize_prospective_execution(
                principal=principal, scope=scope, composition_sha256=_commitment(prepared))
            return PreparedComposition(grant, bindings, input_json, filename)
        except Exception:
            raise AdmissionRefused("COMPOSITION_PREPARATION_REFUSED") from None

    def consume_for_local_validation(self, prepared, *, authorization, raw):
        """Consume once and return bounded input; never execute/save/dispatch.

        Wrong raw bytes or a later validation failure leave the grant consumed.
        A failed authentication does not reveal or return the prepared input.
        """
        try:
            principal = self._principal(authorization)
            self._authority.consume_prospective_execution(
                prepared.authorization, principal=principal, composition_sha256=_commitment(prepared))
            if (type(raw) is not bytes
                    or sha256(raw).hexdigest().upper() != prepared.bindings.raw_source_sha256):
                raise AdmissionRefused("SOURCE_CHANGED")
            return prepared.input_json
        except Exception:
            raise AdmissionRefused("COMPOSITION_CONSUMPTION_REFUSED") from None

    def close(self, prepared):
        self._authority.close_prospective_execution(prepared.authorization)
