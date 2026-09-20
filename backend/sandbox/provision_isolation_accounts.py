"""Founder-authorized Integration-only technical users; no provider/business analysis.

Passwords arrive only in process environment from the DPAPI-protecting wrapper.
Never run this module directly: durable password protection MUST precede writes.
"""
import json
import logging
import os
import warnings
from uuid import UUID

URL = "https://ejixkplrgobgwqnhidwt.supabase.co"
EMAILS = [f"pepperyn-isolation-a24-{suffix}@pepperyn-test.invalid" for suffix in ("a", "b")]


class Refused(Exception):
    pass


def require(value):
    if not value:
        raise Refused()


def provision(bundle, service_key, anon_key, factory):
    stage = "INPUT"
    created = 0
    scopes = []
    try:
        require(bundle["project_url"] == URL and bundle["purpose"] == "A24_TECHNICAL_ISOLATION_ONLY")
        require(bundle["dpapi_roundtrip_verified"] is True)
        require([item["email"] for item in bundle["accounts"]] == EMAILS)
        require(len({item["password"] for item in bundle["accounts"]}) == 2)
        require(all(len(item["password"]) >= 48 for item in bundle["accounts"]))
        require(service_key and anon_key and service_key != anon_key)
        admin = factory(URL, service_key)
        for i, account in enumerate(bundle["accounts"]):
            stage = f"CREATE_{i + 1}"
            marker = f"Pepperyn A24 Isolation Synthetic {i + 1}"
            result = admin.auth.admin.create_user({
                "email": account["email"], "password": account["password"],
                "email_confirm": True,
                "user_metadata": {"organisation": marker, "prenom": "Synthetic", "nom": f"A24-{i + 1}"},
                "app_metadata": {"pepperyn_test_purpose": "A24_TECHNICAL_ISOLATION_ONLY"},
            })
            created += 1
            uid = str(UUID(str(result.user.id)))
            require(result.user.email == account["email"] and result.user.role == "authenticated")
            # A separate anon-key client authenticates each real Auth identity.
            stage = f"AUTHENTICATE_{i + 1}"
            client = factory(URL, anon_key)
            login = client.auth.sign_in_with_password({"email": account["email"], "password": account["password"]})
            require(login.session and login.session.access_token)
            verified = client.auth.get_user(login.session.access_token)
            require(str(verified.user.id) == uid and verified.user.role == "authenticated")
            stage = f"OWN_SCOPE_{i + 1}"
            rows = client.table("profiles").select("id,company_id").eq("id", uid).limit(2).execute().data
            require(len(rows) == 1 and rows[0]["id"] == uid)
            company = str(UUID(rows[0]["company_id"]))
            rows = client.table("companies").select("id,admin_user_id,name").eq("id", company).limit(2).execute().data
            require(len(rows) == 1 and rows[0]["admin_user_id"] == uid and rows[0]["name"] == marker)
            entities = client.table("entities").select("id,company_id,name,is_primary").eq("company_id", company).limit(2).execute().data
            require(len(entities) == 1 and entities[0]["company_id"] == company and entities[0]["name"] == marker and entities[0]["is_primary"] is True)
            scopes.append((uid, company, str(UUID(entities[0]["id"]))))
        stage = "DISTINCT_SCOPES"
        require(all(len({scope[index] for scope in scopes}) == 2 for index in range(3)))
        return {"status": "ACCOUNTS_CREATED_SCOPE_VERIFIED", "accounts_created": created,
                "distinct_users_companies_entities": True, "adversarial_isolation_proven": False,
                "external_provider_used": False, "real_data_used": False}
    except Exception:
        # A timed-out create may have succeeded remotely. Never retry/reset/delete.
        return {"status": "REFUSED", "stage": stage, "acknowledged_creates": created,
                "remote_partial_creation_possible": stage.startswith("CREATE_"),
                "automatic_retry_permitted": False, "secrets_disclosed": False}


def main():
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        from supabase import create_client
        result = provision(json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]),
                           os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"],
                           os.environ["PEPPERYN_ISOLATION_ANON_KEY"], create_client)
    except Exception:
        result = {"status": "REFUSED", "stage": "LOCAL_INPUT_OR_IMPORT", "automatic_retry_permitted": False}
    print(json.dumps(result))
    return 0 if result["status"] == "ACCOUNTS_CREATED_SCOPE_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
