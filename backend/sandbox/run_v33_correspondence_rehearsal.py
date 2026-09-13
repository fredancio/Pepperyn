"""One-record synthetic rehearsal for deployed V33 correspondence storage.

Run in two separate Python processes with the same backend environment. The
script never prints the key, opaque handle or clear synthetic identity.
"""

from __future__ import annotations

import argparse
import json
import os

from supabase import create_client

from services.pseudonymous_correspondence import (
    CorrespondenceRefused,
    CorrespondenceScope,
    GovernedCorrespondenceRegistry,
    SupabaseCorrespondenceRepository,
)


ANALYSIS_ID = "75132a71-c80c-4469-aba8-5171d947a9d0"
SYNTHETIC_IDENTITY = "V33 SYNTHETIC COUNTERPARTY — NO REAL IDENTITY"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("register", "verify", "inspect"), required=True)
    args = parser.parse_args()
    url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    designated_company = os.getenv("PEPPERYN_SYNTHETIC_V1_COMPANY_ID", "")
    if not url or not service_key or not designated_company:
        print(json.dumps({"status": "REFUSED", "code": "V33_ENVIRONMENT_INCOMPLETE"}))
        return 2
    stage = "client_initialization"
    try:
        supabase = create_client(url, service_key)
        stage = "synthetic_scope_read"
        rows = (supabase.from_("governed_analysis_envelopes")
            .select("analysis_id,company_id,entity_id").eq("analysis_id", ANALYSIS_ID)
            .eq("company_id", designated_company).limit(2).execute()).data or []
        if len(rows) != 1:
            raise CorrespondenceRefused("V33_SYNTHETIC_SCOPE_NOT_FOUND")
        scope = CorrespondenceScope(rows[0]["company_id"], rows[0]["entity_id"])
        if args.phase == "inspect":
            return _inspect_persistence(supabase, scope)
        stage = "registry_initialization"
        registry = GovernedCorrespondenceRegistry.from_environment(
            SupabaseCorrespondenceRepository(supabase)
        )
        if args.phase == "register":
            stage = "registration"
            reference = registry.register(
                scope=scope, analysis_id=ANALYSIS_ID, category="COUNTERPARTY",
                real_identity=SYNTHETIC_IDENTITY,
            )
        else:
            # Deliberately read-only: registration may already have succeeded
            # in a prior process even when its surrounding shell later failed.
            stage = "existing_mapping_read"
            reference = registry.reference_existing(
                scope=scope, category="COUNTERPARTY",
                real_identity=SYNTHETIC_IDENTITY,
            )
        stage = "local_rehydration"
        rehydrated = registry.rehydrate(
            {"subject": reference.pseudonym}, scope=scope, handles=[reference.handle],
        )
        if rehydrated.get("subject") != SYNTHETIC_IDENTITY:
            raise CorrespondenceRefused("V33_REHYDRATION_MISMATCH")
        print(json.dumps({
            "status": "PASS", "phase": args.phase,
            "analysis_id": ANALYSIS_ID, "pseudonym": reference.pseudonym,
            "rehydration_verified": True, "external_provider_used": False,
            "real_identity_used": False,
        }, ensure_ascii=False))
        return 0
    except CorrespondenceRefused as exc:
        print(json.dumps({"status": "REFUSED", "phase": args.phase,
            "stage": stage, "code": str(exc), "write_performed": False}))
        return 2
    except Exception as exc:
        # Emit only structural diagnostics. Exception messages can contain URLs,
        # query values or credentials and must never cross this boundary.
        print(json.dumps({"status": "REFUSED", "phase": args.phase,
            "stage": stage, "code": "V33_RUNTIME_FAILURE",
            "exception_type": type(exc).__name__, "write_performed": False}))
        return 2


def _inspect_persistence(supabase, scope: CorrespondenceScope) -> int:
    """Read only structural metadata; never emit protected field values."""
    expected = (
        "id", "company_id", "entity_id", "category", "pseudonym",
        "real_fingerprint", "encrypted_value", "nonce", "ciphertext_sha256",
        "crypto_version", "mapping_version",
    )
    result = {
        "status": "INSPECTED", "phase": "inspect", "analysis_id": ANALYSIS_ID,
        "external_provider_used": False, "write_performed": False,
    }
    try:
        base = (supabase.from_("pseudonymous_correspondence").select("id")
            .eq("company_id", scope.company_id).eq("entity_id", scope.entity_id)
            .eq("category", "COUNTERPARTY").limit(3).execute()).data or []
        result["mapping_count_bounded"] = len(base)
    except Exception as exc:
        result.update(status="REFUSED", stage="mapping_base_read",
            supabase_code=getattr(exc, "code", None))
        print(json.dumps(result))
        return 2
    available = []
    unavailable = []
    for column in expected:
        try:
            (supabase.from_("pseudonymous_correspondence").select(column)
                .eq("company_id", scope.company_id).eq("entity_id", scope.entity_id)
                .eq("category", "COUNTERPARTY").limit(1).execute())
            available.append(column)
        except Exception as exc:
            unavailable.append({"column": column, "supabase_code": getattr(exc, "code", None)})
    result["columns_available"] = available
    result["columns_unavailable"] = unavailable
    try:
        bindings = (supabase.from_("pseudonymous_correspondence_bindings")
            .select("analysis_id").eq("analysis_id", ANALYSIS_ID)
            .eq("company_id", scope.company_id).eq("entity_id", scope.entity_id)
            .limit(3).execute()).data or []
        result["binding_count_bounded"] = len(bindings)
    except Exception as exc:
        result["binding_read"] = {"status": "REFUSED", "supabase_code": getattr(exc, "code", None)}
    result["schema_complete"] = not unavailable
    print(json.dumps(result))
    return 0 if not unavailable else 2


if __name__ == "__main__":
    raise SystemExit(main())
