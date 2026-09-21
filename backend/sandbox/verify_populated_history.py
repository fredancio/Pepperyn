"""A26: history probes use user sessions; V19 reference lookup is service-only.

The service client reads only engagement metadata for an already user-verified
entity. It never performs a history probe, and proves no user authorization.
"""
import json
import logging
import os
import warnings
from uuid import UUID
from sandbox.verify_isolation_accounts import URL, API, EMAILS, live_get
from sandbox.seed_isolation_history import fixture_id


def verify(bundle, anon_key, factory, get, *, service_key):
    stage = "INPUT"
    passed = []
    def check(condition):
        if not condition: raise ValueError("REFUSED")
        passed.append(stage)
    try:
        check(bundle["project_url"] == URL and bundle["purpose"] == "A24_TECHNICAL_ISOLATION_ONLY"
              and [a["email"] for a in bundle["accounts"]] == EMAILS and bool(anon_key)
              and bool(service_key) and service_key != anon_key)
        reference = factory(URL, service_key)
        scopes = []
        for i, account in enumerate(bundle["accounts"], 1):
            stage = f"USER_{i}_AUTH_SCOPE"
            client = factory(URL, anon_key)
            session = client.auth.sign_in_with_password({"email": account["email"], "password": account["password"]}).session
            user = client.auth.get_user(session.access_token).user
            uid = str(UUID(str(user.id)))
            check(user.email == EMAILS[i-1] and user.role == "authenticated")
            profiles = client.table("profiles").select("id,company_id").eq("id", uid).limit(2).execute().data
            check(len(profiles) == 1 and profiles[0]["id"] == uid)
            company = str(UUID(profiles[0]["company_id"]))
            companies = client.table("companies").select("id,admin_user_id,name").eq("id", company).limit(2).execute().data
            check(len(companies) == 1 and companies[0]["id"] == company and companies[0]["admin_user_id"] == uid
                  and companies[0]["name"] == f"Pepperyn A24 Isolation Synthetic {i}")
            entities = client.table("entities").select("id,company_id").eq("company_id", company).limit(2).execute().data
            check(len(entities) == 1 and entities[0]["company_id"] == company)
            entity = str(UUID(entities[0]["id"]))
            stage = f"USER_{i}_ENGAGEMENT_REFERENCE"
            engagements = reference.table("engagements").select("id,entity_id").eq("entity_id", entity).limit(2).execute().data
            check(len(engagements) == 1 and engagements[0]["entity_id"] == entity)
            engagement = str(UUID(engagements[0]["id"]))
            scopes.append((company, entity, fixture_id((uid, company, entity, engagement)), session.access_token))
        stage = "DISTINCT_SCOPE_AND_FIXTURE"
        check(all(len({s[k] for s in scopes}) == 2 for k in range(3)))
        for i, own in enumerate(scopes, 1):
            foreign = scopes[2-i]
            headers = {"Authorization": f"Bearer {own[3]}"}
            baseline = None
            for name, suffix in (
                ("OWN_ENTITY", f"?entity_id={own[1]}"),
                ("OWN_TENANT", ""),
                ("FORGED_COMPANY", f"?company_id={foreign[0]}"),
                ("OWN_ENTITY_FORGED_COMPANY", f"?entity_id={own[1]}&company_id={foreign[0]}"),
            ):
                stage = f"USER_{i}_{name}"
                status, data = get(API + "/api/analyses/history" + suffix, headers)
                check(status == 200 and isinstance(data, dict) and set(data) == {"analyses"} and isinstance(data.get("analyses"), list)
                      and len(data["analyses"]) == 1)
                row = data["analyses"][0]
                check(isinstance(row, dict) and set(row) == {"id", "entity_id", "fichier_nom", "type_document", "score_confiance", "created_at"}
                      and row.get("id") == own[2] and row.get("entity_id") == own[1]
                      and row.get("fichier_nom") == "pepperyn_v1_heterogeneous_english.xlsx"
                      and row.get("type_document") == "AUTRE" and row.get("score_confiance") == 0
                      and isinstance(row.get("created_at"), str) and bool(row["created_at"]))
                if baseline is None: baseline = data
                else: check(data == baseline)
            stage = f"USER_{i}_FOREIGN_ENTITY"
            status, data = get(API + f"/api/analyses/history?entity_id={foreign[1]}", headers)
            check(status == 404 and data == {"detail": "Entité introuvable"})
        stage = "ANONYMOUS_HISTORY"
        status, _ = get(API + "/api/analyses/history", {})
        check(status == 401)
        return {"status": "BOUNDED_POPULATED_HISTORY_ISOLATION_PASS", "checks_passed": sorted(set(passed)),
                "populated_history_isolation_proven": True, "proof_scope": "A26_TWO_SEEDED_ANALYSES_HISTORY_GET_ONLY",
                "business_write_performed": False, "auth_sessions_created": True,
                "engagement_reference_authority": "SERVICE_READ_ONLY",
                "history_probe_authority": "USER_SESSIONS_ONLY",
                "write_isolation_proven": False, "analysis_export_isolation_proven": False,
                "global_isolation_proven": False, "production_proof": False,
                "external_provider_used": False, "real_data_used": False}
    except Exception:
        return {"status": "REFUSED", "stage": stage, "business_write_performed": False,
                "populated_history_isolation_proven": False, "automatic_retry_permitted": False}


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = verify(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                        os.environ["PEPPERYN_ISOLATION_ANON_KEY"], create_client, live_get,
                        service_key=os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"])
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT"}
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "BOUNDED_POPULATED_HISTORY_ISOLATION_PASS" else 1)
