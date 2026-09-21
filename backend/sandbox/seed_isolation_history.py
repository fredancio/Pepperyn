"""Explicitly authorized A26 seed. Two V27 pairs, no retries or gate changes."""
import json
import logging
import os
import warnings
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sandbox.inspect_populated_history_scope import inspect
from sandbox.provision_isolation_accounts import URL, require
from sandbox.heterogeneous_workbooks import run_registered_mock_analysis
from services.governed_analysis_persistence import save_governed_analysis, load_governed_envelope

AUTHORIZATION = "A26_TWO_SYNTHETIC_PAIRS_ONLY"
FIXTURE = Path(__file__).resolve().parents[1] / "tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx"


def fixture_id(scope):
    return str(uuid5(NAMESPACE_URL, "pepperyn:integration:a26:v1:" + ":".join(scope)))


def seed(bundle, service_key, anon_key, factory, *, authorization):
    stage = "AUTHORIZATION"
    attempts = acknowledged = verified = 0
    try:
        require(authorization == AUTHORIZATION)
        stage = "PRECHECK_BOTH_SCOPES"
        scopes = []
        result = inspect(bundle, service_key, anon_key, factory, verified_scopes=scopes)
        require(result["status"] == "A26_SCOPES_INSPECTED" and result["both_scopes_empty"] is True and len(scopes) == 2)
        stage = "PREPARE_BOTH_PAYLOADS"
        prepared = []
        for scope in scopes:
            _, company, entity, engagement = scope
            mock = run_registered_mock_analysis(FIXTURE.read_bytes(), FIXTURE.name)
            require(mock.provider_mode == "DETERMINISTIC_MOCK_NO_NETWORK")
            analysis_id = fixture_id(scope)
            mock.envelope.analysis_result.id = analysis_id
            row = {
                "id": analysis_id, "company_id": company, "entity_id": entity,
                "fichier_nom": mock.filename, "fichier_type": "xlsx", "type_document": "AUTRE",
                "contexte_utilisateur": "A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1",
                "mode": "complete", "analyse_json": mock.envelope.analysis_result.model_dump(mode="json"),
                "score_confiance": 0, "tokens_input": 0, "cout_estime_euros": 0,
                "duree_traitement_ms": 0, "status": "completed", "chat_count": 0,
                "source_data_hash": mock.source_sha256.lower(),
            }
            prepared.append((row, engagement, mock.envelope))
        stage = "RECHECK_BOTH_SCOPES"
        latest = []
        check = inspect(bundle, service_key, anon_key, factory, verified_scopes=latest)
        require(check["status"] == "A26_SCOPES_INSPECTED" and check["both_scopes_empty"] is True and latest == scopes)
        db = factory(URL, service_key)
        for i, (row, engagement, envelope) in enumerate(prepared, 1):
            stage = f"WRITE_PAIR_{i}"
            attempts += 1
            save_governed_analysis(db, analysis_row=row, engagement_id=engagement, envelope=envelope)
            acknowledged += 1
            stage = f"VERIFY_PAIR_{i}"
            loaded = load_governed_envelope(db, analysis_id=row["id"], company_id=row["company_id"],
                                           entity_id=row["entity_id"], engagement_id=engagement)
            require(loaded.model_dump(mode="json") == envelope.model_dump(mode="json"))
            stored = db.table("analyses").select("id,company_id,entity_id,status,source_data_hash,contexte_utilisateur,analyse_json").eq("id", row["id"]).eq("company_id", row["company_id"]).eq("entity_id", row["entity_id"]).limit(2).execute().data
            require(isinstance(stored, list) and len(stored) == 1
                    and all(stored[0].get(k) == row[k] for k in ("id", "company_id", "entity_id", "status", "source_data_hash", "contexte_utilisateur", "analyse_json")))
            verified += 1
        return {"status": "A26_SYNTHETIC_PAIRS_SEEDED", "acknowledged_pairs": acknowledged,
                "verified_pairs": verified, "business_write_performed": True,
                "populated_history_isolation_proven": False, "write_isolation_proven": False,
                "analysis_export_isolation_proven": False, "global_isolation_proven": False,
                "production_proof": False, "external_provider_used": False, "real_data_used": False}
    except Exception:
        return {"status": "REFUSED", "stage": stage, "attempted_pairs": attempts,
                "acknowledged_pairs": acknowledged, "verified_pairs": verified,
                "remote_partial_write_possible": attempts > 0, "automatic_retry_permitted": False}


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = seed(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                      os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"], os.environ["PEPPERYN_ISOLATION_ANON_KEY"],
                      create_client, authorization=os.environ.get("PEPPERYN_A26_SEED_AUTHORIZATION"))
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT", "automatic_retry_permitted": False}
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "A26_SYNTHETIC_PAIRS_SEEDED" else 1)
