"""A26 read-only prerequisite: exact existing A24 technical scopes only.

No insert/update/delete/RPC/provider. Does not certify populated history isolation.
Authentication creates sessions. Diagnostic output contains no row content/secrets.
"""
import json
import logging
import os
import warnings
from uuid import UUID

from sandbox.provision_isolation_accounts import URL, EMAILS, require


def inspect(bundle, service_key, anon_key, factory, *, verified_scopes=None):
    stage = "INPUT"
    try:
        require(bundle["project_url"] == URL and bundle["purpose"] == "A24_TECHNICAL_ISOLATION_ONLY")
        require([a["email"] for a in bundle["accounts"]] == EMAILS)
        require(len(bundle["accounts"]) == 2 and bool(service_key) and bool(anon_key) and service_key != anon_key)
        admin = factory(URL, service_key)
        scopes = []
        states = []
        for i, account in enumerate(bundle["accounts"], 1):
            stage = f"AUTH_SCOPE_{i}"
            client = factory(URL, anon_key)
            session = client.auth.sign_in_with_password({"email": account["email"], "password": account["password"]}).session
            user = client.auth.get_user(session.access_token).user
            uid = str(UUID(str(user.id)))
            require(user.email == EMAILS[i-1] and user.role == "authenticated")
            profile = client.table("profiles").select("id,company_id").eq("id", uid).limit(2).execute().data
            require(isinstance(profile, list) and len(profile) == 1 and profile[0]["id"] == uid)
            company = str(UUID(profile[0]["company_id"]))
            companies = admin.table("companies").select("id,admin_user_id,name").eq("id", company).limit(2).execute().data
            require(len(companies) == 1 and companies[0]["id"] == company
                    and companies[0]["admin_user_id"] == uid
                    and companies[0]["name"] == f"Pepperyn A24 Isolation Synthetic {i}")
            entities = admin.table("entities").select("id,company_id,name,is_primary").eq("company_id", company).limit(2).execute().data
            require(len(entities) == 1 and entities[0]["company_id"] == company
                    and entities[0]["name"] == companies[0]["name"] and entities[0]["is_primary"] is True)
            entity = str(UUID(entities[0]["id"]))
            stage = f"ENGAGEMENT_{i}"
            engagements = admin.table("engagements").select("id,entity_id").eq("entity_id", entity).limit(2).execute().data
            require(len(engagements) == 1 and engagements[0]["entity_id"] == entity)
            engagement = str(UUID(engagements[0]["id"]))
            scopes.append((uid, company, entity, engagement))
            stage = f"EXISTING_HISTORY_{i}"
            # Tenant-bound metadata only. At most two records; never expose bodies.
            rows = admin.table("analyses").select("id,company_id,entity_id,status").eq("company_id", company).limit(2).execute().data
            require(isinstance(rows, list) and len(rows) <= 2)
            require(all(isinstance(r, dict) and r.get("company_id") == company for r in rows))
            stage = f"EXISTING_ENVELOPES_{i}"
            envelopes = admin.table("governed_analysis_envelopes").select("analysis_id,company_id,entity_id,engagement_id").eq("company_id", company).limit(2).execute().data
            require(isinstance(envelopes, list) and len(envelopes) <= 2)
            require(all(isinstance(r, dict) and r.get("company_id") == company for r in envelopes))
            states.append({"technical_account": i, "analysis_count_bounded": len(rows),
                           "envelope_count_bounded": len(envelopes),
                           "empty_history_and_envelopes": rows == [] and envelopes == []})
        stage = "DISTINCT_SCOPES"
        require(all(len({s[k] for s in scopes}) == 2 for k in range(4)))
        if verified_scopes is not None:
            verified_scopes.extend(scopes)
        return {"status": "A26_SCOPES_INSPECTED", "scopes": states,
                "both_scopes_empty": all(s["empty_history_and_envelopes"] for s in states),
                "business_write_performed": False, "auth_sessions_created": True,
                "populated_history_isolation_proven": False, "write_isolation_proven": False,
                "analysis_export_isolation_proven": False, "global_isolation_proven": False,
                "production_proof": False, "external_provider_used": False, "real_data_used": False}
    except Exception:
        return {"status": "REFUSED", "stage": stage, "business_write_performed": False,
                "automatic_retry_permitted": False}


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = inspect(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                         os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"],
                         os.environ["PEPPERYN_ISOLATION_ANON_KEY"], create_client)
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT", "business_write_performed": False}
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "A26_SCOPES_INSPECTED" else 1)
