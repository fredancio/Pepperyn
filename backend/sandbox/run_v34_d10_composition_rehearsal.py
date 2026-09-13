"""Read-only live D10 composition against the one V34-attested mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from supabase import create_client

from services.governed_analysis_persistence import load_governed_envelope
from services.governed_minimal_projection import (
    POLICY_ID, TASK, ReceiptedFinancialChangeFact,
    compose_financial_change_v1, projection_binding_hash,
    verify_governed_projection,
)
from services.ownership_authority import (
    InMemoryOwnershipRepository, InMemoryScopedContextRepository,
    OwnershipAuthority, OwnershipRecord, ProtectedContextReader,
    ProtectedResource, ScopedContextRecord,
)
from services.pseudonymous_correspondence import (
    CorrespondenceScope, GovernedCorrespondenceRegistry,
    SupabaseCorrespondenceRepository,
    verify_projection_correspondence_binding,
)


ANALYSIS_ID = "75132a71-c80c-4469-aba8-5171d947a9d0"
EXPECTED_SYNTHETIC_ENTITY = "Optilux Synthetic Internal Pilot"
CATEGORY = "ENTITY"
FIXTURE_ID = "PEPPERYN_V1_D10_COMPOSITION_REHEARSAL"
FIXTURE_SHA256 = "D740CE1312509032663F6FB3A3C83AD8650C605319BABBA8E9390B15E8FE1DC2"
_FIXTURE = (Path(__file__).parents[1] / "tests" / "golden" / "fixtures"
            / "pepperyn_v1_d10_composition_rehearsal.json")


def _emit(status: str, phase: str, **fields: object) -> None:
    print(json.dumps({
        "status": status, "phase": phase, "analysis_id": ANALYSIS_ID,
        "external_provider_used": False, "real_data_used": False,
        "write_performed": False, **fields,
    }, sort_keys=True))


def _fixture() -> dict:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest().upper() != FIXTURE_SHA256:
        raise RuntimeError("D10_FIXTURE_HASH_MISMATCH")
    if (
        payload.get("fixture_id") != FIXTURE_ID
        or payload.get("evidence_role") != "D10_COMPOSITION_REHEARSAL_ONLY"
        or payload.get("synthetic") is not True
        or payload.get("external_provider_allowed") is not False
        or payload.get("real_data_allowed") is not False
        or payload.get("periods") != ["PREVIOUS", "CURRENT"]
    ):
        raise RuntimeError("D10_FIXTURE_BOUNDARY_INVALID")
    return payload


def _paths(payload: object, prefix: tuple = ()) -> list[tuple]:
    if isinstance(payload, dict):
        return [path for key, value in payload.items()
                for path in _paths(value, prefix + (key,))]
    if isinstance(payload, list):
        return [path for index, value in enumerate(payload)
                for path in _paths(value, prefix + (index,))]
    return [prefix]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("inspect", "compose"), required=True)
    phase = parser.parse_args().phase
    stage = "environment"
    try:
        url = os.getenv("SUPABASE_URL", "")
        service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        company = os.getenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", "")
        if not url or not service_key or not company or not os.getenv("PEPPERYN_CORRESPONDENCE_KEY", ""):
            raise RuntimeError("D10_ENVIRONMENT_INCOMPLETE")
        db = create_client(url, service_key)
        stage = "governed_scope"
        rows = (db.from_("governed_analysis_envelopes")
                .select("analysis_id,company_id,entity_id,engagement_id")
                .eq("analysis_id", ANALYSIS_ID).eq("company_id", company)
                .limit(2).execute()).data or []
        if len(rows) != 1:
            raise RuntimeError("D10_SCOPE_UNAVAILABLE")
        row = rows[0]
        scope = CorrespondenceScope(row["company_id"], row["entity_id"])
        envelope = load_governed_envelope(
            db, analysis_id=ANALYSIS_ID, company_id=scope.company_id,
            entity_id=scope.entity_id, engagement_id=row["engagement_id"])
        entities = (db.from_("entities").select("id,company_id,name")
                    .eq("id", scope.entity_id).eq("company_id", scope.company_id)
                    .limit(2).execute()).data or []
        if len(entities) != 1 or entities[0].get("name") != EXPECTED_SYNTHETIC_ENTITY:
            raise RuntimeError("D10_SYNTHETIC_ENTITY_NOT_REGISTERED")
        registry = GovernedCorrespondenceRegistry.from_environment(
            SupabaseCorrespondenceRepository(db))
        reference = registry.reference_existing(
            scope=scope, category=CATEGORY,
            real_identity=EXPECTED_SYNTHETIC_ENTITY)
        binding = registry.authorize_projection_reference(reference, scope=scope)
        verify_projection_correspondence_binding(
            binding, company_id=scope.company_id, entity_id=scope.entity_id)
        if phase == "inspect":
            _emit("INSPECTED", phase, mapping_count_bounded=1,
                  authorized_origin=True,
                  mapping_version=binding.mapping_version,
                  governed_envelope_verified=True)
            return 0

        stage = "authoritative_source"
        fixture = _fixture()
        source = {"metrics": fixture["metrics"]}
        request_id = f"d10-live-{ANALYSIS_ID}"
        paths = frozenset(_paths(source))
        authority = OwnershipAuthority(
            InMemoryOwnershipRepository([OwnershipRecord(
                ANALYSIS_ID, scope.company_id, scope.entity_id,
                row["engagement_id"], scope.company_id, scope.entity_id)]),
            projection_policy={ProtectedResource.ANALYSIS_RESULT: paths})
        principal = authority._accept_authenticated_principal(
            "v34-d10-live-rehearsal", scope.company_id)
        grant = authority.resolve_and_mint_read_grant(
            principal=principal, analysis_id=ANALYSIS_ID,
            request_id=request_id, resources=[ProtectedResource.ANALYSIS_RESULT])
        record = ScopedContextRecord(
            ProtectedResource.ANALYSIS_RESULT, scope.company_id, scope.entity_id,
            row["engagement_id"], ANALYSIS_ID, source)
        whole = ProtectedContextReader(
            InMemoryScopedContextRepository([record])).read_receipted(
                grant, request_id=request_id,
                resource=ProtectedResource.ANALYSIS_RESULT)[0][1]
        receipts = {path: authority.project_read(whole, path) for path in paths}
        facts = [ReceiptedFinancialChangeFact(
            item["metric_code"], receipts[("metrics", index, "metric_code")],
            item["previous"], receipts[("metrics", index, "previous")],
            item["current"], receipts[("metrics", index, "current")])
            for index, item in enumerate(source["metrics"])]
        stage = "governed_composition"
        projection = compose_financial_change_v1(
            registry=registry, correspondence_reference=reference,
            correspondence_scope=scope, ownership_authority=authority,
            read_grant=grant, request_id=request_id, facts=facts)
        binding_hash = projection_binding_hash(projection)
        verify_governed_projection(
            projection, task=TASK, payload=projection.payload,
            identity_state="PSEUDONYMOUS")
        _emit("PASS", phase, stage=stage, policy_id=POLICY_ID,
              pseudonym=projection.payload["subject"],
              metric_count=len(projection.payload["metrics"]),
              payload_hash=projection.payload_hash,
              projection_binding_hash=binding_hash,
              source_receipt_count=len(projection.lineage.source_receipt_ids),
              mapping_version=projection.lineage.mapping_version,
              authorized_origin=True, governed_envelope_verified=True,
              projection_consumed_without_transport=True,
              exact_values_disclosed=False)
        return 0
    except Exception as exc:
        _emit("REFUSED", phase, stage=stage, code="D10_LIVE_REHEARSAL_FAILED",
              exception_type=type(exc).__name__)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
