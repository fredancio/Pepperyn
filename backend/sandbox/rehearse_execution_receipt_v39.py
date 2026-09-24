"""One-shot, Founder-authorized V39 Integration Test rehearsal. Never auto-retry.

Only persist phase can write remotely. Verify is a separate process and GET-only
for business data. The durable local manifest is a stop latch, not a resume token.
"""
import argparse
import copy
import hashlib
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import NAMESPACE_URL, UUID, uuid5
from unittest.mock import patch

import httpx

from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
from sandbox.provision_isolation_accounts import URL, EMAILS
from services.governed_analysis_persistence import (
    _digest, load_execution_provenance, save_governed_analysis,
)

AUTHORIZATION = "V39_FOUR_CALLS_THREE_ROWS_TECHNICAL_ONE"
TABLES = ("analyses", "governed_analysis_envelopes", "governed_execution_receipts")
FIXTURE = Path(__file__).resolve().parents[1] / "tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx"
RAW_SHA = "FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93"


def require(condition):
    if not condition:
        raise ValueError("V39_REFUSED")


class Query:
    def __init__(self, db, table):
        require(table in TABLES)
        self.db, self.table, self.params = db, table, {}

    def select(self, fields):
        self.params["select"] = fields
        return self

    def eq(self, field, value):
        require(field in ("id", "analysis_id", "company_id", "entity_id", "engagement_id"))
        self.params[field] = "eq." + str(value)
        return self

    def limit(self, value):
        self.params["limit"] = str(value)
        return self

    def execute(self):
        return SimpleNamespace(data=self.db.get(self.table, self.params))


class Database:
    """Transport without retries, redirects, provider clients or generic writes."""
    def __init__(self, key):
        self.client = httpx.Client(base_url=URL, headers={"apikey": key, "Authorization": "Bearer " + key},
                                   timeout=30, follow_redirects=False, trust_env=False)

    def get(self, table, params):
        require(table in TABLES + ("companies", "entities", "engagements"))
        response = self.client.get("/rest/v1/" + table, params=params)
        require(response.status_code == 200)
        data = response.json()
        require(isinstance(data, list))
        return data

    def from_(self, table):
        return Query(self, table)

    def close(self):
        self.client.close()


def resolve_scope(db, bundle, anon):
    require(bundle["project_url"] == URL and bundle["purpose"] == "A24_TECHNICAL_ISOLATION_ONLY")
    require([a["email"] for a in bundle["accounts"]] == EMAILS)
    account = bundle["accounts"][0]
    with httpx.Client(base_url=URL, headers={"apikey": anon}, timeout=30,
                      follow_redirects=False, trust_env=False) as client:
        login = client.post("/auth/v1/token?grant_type=password", json={"email": account["email"], "password": account["password"]})
        require(login.status_code == 200)
        token = login.json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        response = client.get("/auth/v1/user", headers=headers)
        require(response.status_code == 200)
        user = response.json()
        require(user["email"] == EMAILS[0] and user["role"] == "authenticated")
        uid = str(UUID(user["id"]))
        response = client.get("/rest/v1/profiles", headers=headers,
                              params={"select": "id,company_id", "id": "eq." + uid, "limit": "2"})
        require(response.status_code == 200)
        profiles = response.json()
        require(len(profiles) == 1 and profiles[0]["id"] == uid)
        company = str(UUID(profiles[0]["company_id"]))
    rows = db.get("companies", {"select": "id,admin_user_id,name", "id": "eq." + company, "limit": "2"})
    require(len(rows) == 1 and rows[0]["admin_user_id"] == uid and rows[0]["name"] == "Pepperyn A24 Isolation Synthetic 1")
    rows = db.get("entities", {"select": "id,company_id,name,is_primary", "company_id": "eq." + company, "limit": "2"})
    require(len(rows) == 1 and rows[0]["company_id"] == company and rows[0]["is_primary"] is True
            and rows[0]["name"] == "Pepperyn A24 Isolation Synthetic 1")
    entity = str(UUID(rows[0]["id"]))
    rows = db.get("engagements", {"select": "id,entity_id", "entity_id": "eq." + entity, "limit": "2"})
    require(len(rows) == 1 and rows[0]["entity_id"] == entity)
    return {"company_id": company, "entity_id": entity, "engagement_id": str(UUID(rows[0]["id"]))}


def ids(scope):
    return {name: str(uuid5(NAMESPACE_URL, "pepperyn:v39:rehearsal:v1:" + scope["company_id"] + ":" + name))
            for name in ("binding_negative", "rollback_negative", "positive")}


def snapshot(db, scope):
    result = {}
    for table in TABLES:
        rows = db.get(table, {"select": "*", "company_id": "eq." + scope["company_id"], "limit": "101"})
        require(len(rows) < 100 and all(r["company_id"] == scope["company_id"] for r in rows))
        key = "id" if table == "analyses" else "analysis_id"
        result[table] = {r[key]: _digest(r) for r in rows}
        require(len(result[table]) == len(rows))
    return result


def expected_delta(before, after, positive=None):
    for table in TABLES:
        expected = set(before[table]) | ({positive} if positive else set())
        require(set(after[table]) == expected)
        require(all(after[table][k] == value for k, value in before[table].items()))


class Capture:
    """Use production serializer without doing an RPC."""
    def rpc(self, name, params):
        require(name == "persist_governed_execution_v1")
        self.params = copy.deepcopy(params)
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=params["p_analysis"]["id"]))


def prepare(scope, analysis_id):
    with patch("socket.socket.connect", side_effect=RuntimeError("MOCK_NETWORK_REFUSED")), patch(
            "socket.socket.connect_ex", side_effect=RuntimeError("MOCK_NETWORK_REFUSED")):
        execution = run_recorded_registered_mock_analysis(FIXTURE.read_bytes(), FIXTURE.name)
    require(execution.provenance.raw_source_sha256 == RAW_SHA)
    row = {"id": analysis_id, "company_id": scope["company_id"], "entity_id": scope["entity_id"],
           "fichier_nom": FIXTURE.name, "fichier_type": "xlsx", "type_document": "AUTRE",
           "contexte_utilisateur": "V39_PROSPECTIVE_SYNTHETIC_RECEIPT_REHEARSAL_V1",
           "mode": "complete", "analyse_json": execution.analysis.envelope.analysis_result.model_dump(mode="json"),
           "score_confiance": 0, "tokens_input": 0, "cout_estime_euros": 0,
           "duree_traitement_ms": 0, "status": "completed", "chat_count": 0,
           "source_data_hash": RAW_SHA.lower(), "fichier_taille_bytes": FIXTURE.stat().st_size}
    capture = Capture()
    save_governed_analysis(capture, analysis_row=row, engagement_id=scope["engagement_id"],
                          envelope=execution.analysis.envelope, execution_provenance=execution.provenance)
    return execution, row, capture.params


def save_manifest(path, state, *, new=False):
    # Contains identifiers/hashes only, never credentials or business row contents.
    if new:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(state, stream, sort_keys=True)
    else:
        temporary = path.with_suffix(".pending")
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(state, stream, sort_keys=True)
        os.replace(temporary, path)


class Budget:
    def __init__(self, db, state, path):
        self.db, self.state, self.path = db, state, path

    def call(self, params):
        require(self.state["attempts"] < 4)
        require(params["p_analysis"]["id"] in self.state["ids"].values())
        for key, value in self.state["scope"].items():
            require(params["p_envelope"][key] == value)
        self.state["attempts"] += 1
        save_manifest(self.path, self.state)  # latch BEFORE transport, including timeout
        return self.db.client.post("/rest/v1/rpc/persist_governed_execution_v1", json=params)

    def rpc(self, name, params):
        require(name == "persist_governed_execution_v1")
        def execute():
            response = self.call(params)
            require(response.status_code == 200)
            return SimpleNamespace(data=response.json())
        return SimpleNamespace(execute=execute)


def refused(response, code, message_fragment):
    require(400 <= response.status_code < 500)
    data = response.json()
    require(data.get("code") == code and message_fragment in data.get("message", ""))


def verify_read(db, state):
    scope = state["scope"] | {"analysis_id": state["ids"]["positive"]}
    record = load_execution_provenance(db, **scope)
    require(record is not None and _digest(record.model_dump(mode="json")) == state["record_hash"])
    current = snapshot(db, state["scope"])
    expected_delta(state["before"], current, state["ids"]["positive"])
    if "after" in state:
        require(current == state["after"])
    return current


def persist(db, scope, path):
    state = {"project": URL, "scope": scope, "ids": ids(scope), "attempts": 0,
             "stage": "BASELINE", "pid": os.getpid(), "status": "INCOMPLETE",
             "source_sha256": RAW_SHA,
             "rehearsal_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()}
    save_manifest(path, state, new=True)
    budget = Budget(db, state, path)
    try:
        state["before"] = snapshot(db, scope)
        require(all(not (set(rows) & set(state["ids"].values())) for rows in state["before"].values()))
        require(state["before"]["governed_execution_receipts"] == {})
        prepared = {name: prepare(scope, value) for name, value in state["ids"].items()}
        state["execution_ids"] = {name: str(value[0].provenance.execution_id) for name, value in prepared.items()}
        state["prepared_payload_hashes"] = {name: _digest(value[2]) for name, value in prepared.items()}
        save_manifest(path, state)
        state["stage"] = "BINDING_DENIAL"
        bad = copy.deepcopy(prepared["binding_negative"][2])
        bad["p_receipt"]["payload"]["envelope_sha256"] = "0" * 64
        refused(budget.call(bad), "P0001", "V39 execution binding refused")
        expected_delta(state["before"], snapshot(db, scope))
        state["binding_denial"] = "P0001_NO_ROWS"
        state["stage"] = "LATE_ROLLBACK"
        bad = copy.deepcopy(prepared["rollback_negative"][2])
        bad["p_receipt"]["sha256"] = "INVALID"
        refused(budget.call(bad), "23514", "governed_execution_receipts_sha256_check")
        expected_delta(state["before"], snapshot(db, scope))
        state["late_rollback"] = "23514_NO_ANALYSIS_ENVELOPE_OR_RECEIPT"
        state["stage"] = "POSITIVE_WRITE"
        execution, row, positive = prepared["positive"]
        state["record_hash"] = _digest(execution.provenance.model_dump(mode="json"))
        save_governed_analysis(budget, analysis_row=row, engagement_id=scope["engagement_id"],
                              envelope=execution.analysis.envelope, execution_provenance=execution.provenance)
        state["after"] = verify_read(db, state)
        state["stage"] = "EXACT_REPLAY_DENIAL"
        refused(budget.call(positive), "23505", "analyses_pkey")
        verify_read(db, state)
        state["replay_denial"] = "23505_UNCHANGED"
        require(state["attempts"] == 4)
        state["status"] = "V39_PERSISTED_PENDING_SECOND_PROCESS"
        state["stage"] = "FIRST_PROCESS_COMPLETE"
        save_manifest(path, state)
        return state
    except Exception:
        state["status"] = "REFUSED"
        save_manifest(path, state)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("check", "persist", "verify"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    stage, db = "INPUT", None
    try:
        if args.phase == "check":
            scope = {key: str(uuid5(NAMESPACE_URL, "v39-local-only:" + key))
                     for key in ("company_id", "entity_id", "engagement_id")}
            prepare(scope, ids(scope)["positive"])
            print(json.dumps({"status": "V39_LOCAL_CHECK_PASS", "network_used": False, "write_performed": False}))
            return 0
        require(os.environ.get("PEPPERYN_V39_AUTHORIZATION") == AUTHORIZATION)
        service, anon = os.environ["PEPPERYN_ISOLATION_SERVICE_KEY"], os.environ["PEPPERYN_ISOLATION_ANON_KEY"]
        require(service and anon and service != anon)
        if args.phase == "persist":
            require(not args.manifest.exists() and not args.manifest.with_suffix(".pending").exists())
        db = Database(service)
        stage = "AUTH_SCOPE"
        scope = resolve_scope(db, json.loads(os.environ["PEPPERYN_ISOLATION_BOOTSTRAP"]), anon)
        stage = "PERSIST" if args.phase == "persist" else "SECOND_PROCESS_READ"
        if args.phase == "persist":
            state = persist(db, scope, args.manifest)
        else:
            state = json.loads(args.manifest.read_text(encoding="utf-8"))
            require(state["project"] == URL and state["scope"] == scope and state["ids"] == ids(scope))
            require(state["status"] == "V39_PERSISTED_PENDING_SECOND_PROCESS" and state["attempts"] == 4)
            require(state["source_sha256"] == RAW_SHA
                    and state["rehearsal_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper())
            require(state["binding_denial"] == "P0001_NO_ROWS"
                    and state["late_rollback"] == "23514_NO_ANALYSIS_ENVELOPE_OR_RECEIPT"
                    and state["replay_denial"] == "23505_UNCHANGED")
            # Parent wrapper also waits for the first process to terminate.
            require(state["pid"] != os.getpid())
            verify_read(db, state)
        print(json.dumps({"status": state["status"] if args.phase == "persist" else "BOUNDED_V39_PERSISTENCE_RECOVERY_PASS",
                          "phase": args.phase, "rpc_attempts": state["attempts"] if args.phase == "persist" else 0,
                          "new_durable_rows": 3, "existing_scope_rows_unchanged": True,
                          "binding_denial": state["binding_denial"], "late_rollback": state["late_rollback"],
                          "replay_denial": state["replay_denial"],
                          "external_provider_used": False, "real_data_used": False,
                          "b1_global_proven": False, "http_uvicorn_proven": False,
                          "global_isolation_proven": False, "production_proven": False}))
        return 0
    except Exception:
        safe = {"status": "REFUSED", "stage": stage, "automatic_retry_permitted": False}
        if args.manifest.exists():
            try:
                state = json.loads(args.manifest.read_text(encoding="utf-8"))
                if args.phase == "persist":
                    safe.update(stage=state.get("stage", stage), rpc_attempts=state.get("attempts"))
            except Exception:
                pass
        print(json.dumps(safe))
        return 1
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    raise SystemExit(main())
