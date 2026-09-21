"""A26 read-only differential diagnosis; privileged reads are NOT user proof."""
import json
import logging
import os
import warnings
from uuid import UUID
from sandbox.inspect_populated_history_scope import inspect
from sandbox.verify_isolation_accounts import URL, live_get
from sandbox.seed_isolation_history import fixture_id
from services.governed_analysis_persistence import load_governed_envelope


def diagnose(bundle, service_key, anon_key, factory, get):
    stage = "AUTHORITATIVE_SCOPE_READ"
    try:
        scopes = []
        result = inspect(bundle, service_key, anon_key, factory, verified_scopes=scopes)
        if result["status"] != "A26_SCOPES_INSPECTED" or len(scopes) != 2:
            raise ValueError()
        db = factory(URL, service_key)
        findings = []
        for i, (uid, company, entity, engagement) in enumerate(scopes, 1):
            stage = f"USER_{i}_SESSION"
            client = factory(URL, anon_key)
            account = bundle["accounts"][i-1]
            session = client.auth.sign_in_with_password(account).session
            user = client.auth.get_user(session.access_token).user
            if str(UUID(str(user.id))) != uid or user.email != account["email"] or user.role != "authenticated":
                raise ValueError()
            stage = f"USER_{i}_DIRECT_ENGAGEMENT_DIAGNOSTIC"
            status, data = get(URL + f"/rest/v1/engagements?select=id,entity_id&entity_id=eq.{entity}&limit=2",
                               {"apikey": anon_key, "Authorization": f"Bearer {session.access_token}"})
            classification = "OTHER_RESPONSE"
            if status in (401, 403) and isinstance(data, dict) and data.get("code") == "42501":
                classification = "DATABASE_PERMISSION_DENIED"
            elif status == 200 and data == []:
                classification = "EMPTY_UNDER_USER_SESSION"
            elif status == 200 and isinstance(data, list):
                classification = "MATCHING_ROW" if data == [{"id": engagement, "entity_id": entity}] else "UNEXPECTED_ROWS"
            stage = f"USER_{i}_PERSISTED_PAIR_BINDING"
            aid = fixture_id((uid, company, entity, engagement))
            rows = db.table("analyses").select("id,company_id,entity_id,status,contexte_utilisateur,analyse_json").eq("id", aid).eq("company_id", company).eq("entity_id", entity).limit(2).execute().data
            envelope = load_governed_envelope(db, analysis_id=aid, company_id=company, entity_id=entity, engagement_id=engagement)
            binding = (isinstance(rows, list) and len(rows) == 1 and rows[0].get("id") == aid
                       and rows[0].get("company_id") == company and rows[0].get("entity_id") == entity
                       and rows[0].get("status") == "completed"
                       and rows[0].get("contexte_utilisateur") == "A26_TECHNICAL_SYNTHETIC_ISOLATION_FIXTURE_V1"
                       and rows[0].get("analyse_json") == envelope.analysis_result.model_dump(mode="json"))
            findings.append({"technical_account": i, "direct_engagement_http_status": status,
                             "direct_engagement_classification": classification,
                             "persisted_seed_binding_verified": binding})
        return {"status": "A26_ENGAGEMENT_DIAGNOSED", "findings": findings,
                "business_write_performed": False, "external_provider_used": False, "real_data_used": False,
                "populated_history_isolation_proven": False, "global_isolation_proven": False,
                "write_isolation_proven": False, "analysis_export_isolation_proven": False, "production_proof": False}
    except Exception:
        return {"status": "REFUSED", "stage": stage, "business_write_performed": False}


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = diagnose(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                          os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"], os.environ["PEPPERYN_ISOLATION_ANON_KEY"],
                          create_client, live_get)
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT", "business_write_performed": False}
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "A26_ENGAGEMENT_DIAGNOSED" else 1)
