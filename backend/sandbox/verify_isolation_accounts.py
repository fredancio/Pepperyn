"""Bounded A24 two-user live READ probes. No business writes or service key.

Auth password login creates sessions. Only synthetic test-owned rows are requested.
No claim about financial outputs, write isolation, or global security-gate closure.
"""
import json
import logging
import os
import warnings
from uuid import UUID

URL = "https://ejixkplrgobgwqnhidwt.supabase.co"
API = "http://127.0.0.1:8000"
EMAILS = [f"pepperyn-isolation-a24-{s}@pepperyn-test.invalid" for s in ("a", "b")]
TABLES = ["sessions", "analyses", "evidence_ledger_entries", "arc_analysis_links", "decision_arcs", "knowledge_model"]


def verify(bundle, anon_key, factory, get):
    stage = "INPUT"
    passed = []
    def check(name, condition):
        if not condition:
            raise ValueError(name)
        passed.append(name)
    try:
        check("BOUND_INPUT", bundle["project_url"] == URL and bundle["purpose"] == "A24_TECHNICAL_ISOLATION_ONLY"
              and [a["email"] for a in bundle["accounts"]] == EMAILS and bool(anon_key))
        scopes = []
        for i, account in enumerate(bundle["accounts"]):
            stage = f"AUTH_SCOPE_{i+1}"
            client = factory(URL, anon_key)
            session = client.auth.sign_in_with_password({"email": account["email"], "password": account["password"]}).session
            user = client.auth.get_user(session.access_token).user
            uid = str(UUID(str(user.id)))
            check(f"USER_{i+1}_VERIFIED", user.email == EMAILS[i] and user.role == "authenticated")
            profile = client.table("profiles").select("id,company_id").eq("id", uid).limit(2).execute().data
            check(f"USER_{i+1}_OWN_PROFILE", len(profile) == 1 and profile[0]["id"] == uid)
            company = str(UUID(profile[0]["company_id"]))
            companies = client.table("companies").select("id,admin_user_id,name").eq("id", company).limit(2).execute().data
            check(f"USER_{i+1}_OWN_COMPANY", len(companies) == 1 and companies[0]["admin_user_id"] == uid
                  and companies[0]["name"] == f"Pepperyn A24 Isolation Synthetic {i+1}")
            entities = client.table("entities").select("id,company_id").eq("company_id", company).limit(2).execute().data
            check(f"USER_{i+1}_OWN_ENTITY", len(entities) == 1 and entities[0]["company_id"] == company)
            scopes.append((uid, company, str(UUID(entities[0]["id"])), session.access_token))
        check("DISTINCT_SCOPES", all(len({s[k] for s in scopes}) == 2 for k in range(3)))
        for i, own in enumerate(scopes):
            foreign = scopes[1-i]
            headers = {"apikey": anon_key, "Authorization": f"Bearer {own[3]}"}
            for table, key, value in [("profiles", "id", foreign[0]), ("companies", "id", foreign[1]), ("entities", "id", foreign[2])]:
                stage = f"USER_{i+1}_FOREIGN_{table.upper()}"
                status, data = get(URL + f"/rest/v1/{table}?select=id&{key}=eq.{value}&limit=2", headers)
                # Positive own reads above distinguish RLS isolation from total outage.
                check(stage, status == 200 and data == [])
            for table in TABLES:
                stage = f"USER_{i+1}_DENIED_{table.upper()}"
                status, data = get(URL + f"/rest/v1/{table}?select=id&limit=0", headers)
                check(stage, status in (401, 403) and isinstance(data, dict) and data.get("code") == "42501")
            stage = f"USER_{i+1}_BACKEND_OWN"
            status, data = get(API + "/api/entities", {"Authorization": f"Bearer {own[3]}"})
            check(stage, status == 200 and isinstance(data, dict) and data.get("success") is True
                  and isinstance(data.get("data"), list) and [r.get("id") for r in data["data"]] == [own[2]])
            stage = f"USER_{i+1}_BACKEND_SCOPE_SUBSTITUTION"
            status, data = get(API + f"/api/entities?company_id={foreign[1]}&entity_id={foreign[2]}",
                               {"Authorization": f"Bearer {own[3]}"})
            check(stage, status == 200 and isinstance(data, dict) and data.get("success") is True
                  and isinstance(data.get("data"), list) and [r.get("id") for r in data["data"]] == [own[2]])
        stage = "BACKEND_ANONYMOUS"
        status, _ = get(API + "/api/entities", {})
        check(stage, status == 401)
        return {"status": "BOUNDED_TWO_USER_READ_ISOLATION_PASS", "checks_passed": passed,
                "business_write_performed": False, "auth_sessions_created": True,
                "external_provider_used": False, "real_data_used": False,
                "global_isolation_proven": False, "write_isolation_proven": False,
                "analysis_export_isolation_proven": False, "production_proof": False}
    except Exception:
        return {"status": "REFUSED", "stage": stage, "checks_passed": passed,
                "business_write_performed": False, "global_isolation_proven": False}


def live_get(url, headers):
    import httpx
    # Fixed origins; no redirects and no data in output, even on a detected leak.
    if not (url.startswith(URL + "/rest/v1/") or url.startswith(API + "/api/entities")):
        raise ValueError("TARGET_REFUSED")
    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as http:
        response = http.get(url, headers=headers)
        return response.status_code, response.json()


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = verify(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                        os.environ["PEPPERYN_ISOLATION_ANON_KEY"], create_client, live_get)
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT"}
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "BOUNDED_TWO_USER_READ_ISOLATION_PASS" else 1)
