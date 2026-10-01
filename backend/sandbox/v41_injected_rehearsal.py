"""Frozen identities and owner SQL for the bounded V41 injected rehearsal.

This module has no network client, credential reader or retry path.  It only
creates exact local artifacts consumed by the separately authorized one-shot
runner.  Owner SQL is intentionally limited to one insert and one irreversible
disable because ``service_role`` has read/execute authority but no table DML.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID, uuid4

from services.bounded_producer_policy import BoundedLocalTestPolicyV1
from services.generic_producer_candidate import (
    CONTRACT_BINDING,
    GENERIC_ADMISSION_CONTRACT_SHA256,
)


PROJECT_URL = "https://ejixkplrgobgwqnhidwt.supabase.co"
CHECKPOINT_HEAD = "ccab95c2b6bfeaaae59ecbcbfea1da38f8231ca5"
PROTOCOL_RELATIVE = (
    "docs/Project_Control/"
    "INSIGHT_SHAPER_B1_V41_INJECTED_DURABLE_REHEARSAL_SUCCESSOR_PROTOCOL.md"
)
PROTOCOL_SHA256 = "FB7AA56B9209392B6E64E4C125DACF4551CA27F129A91E175269152FE7B8861F"
FIXTURE_NAME = "pepperyn_v1_heterogeneous_english.xlsx"
FIXTURE_SHA256 = "FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93"
SCOPE_BASELINE_SHA256 = "35759DA949A93E0FB4DF030DBE8F9760B27C115D0EF9E2C1E833E830F6CD6F63"
SCOPE = {
    "actor_id": "89c2541d-3f40-43ee-a97e-06f90ffeb8e0",
    "company_id": "1962090e-4dda-45ee-8b29-1a5afd9d387b",
    "entity_id": "9abe5caa-1a8a-48ee-a7be-11df7df0c41a",
    "engagement_id": "6310b4c5-1f06-4cf5-8fa5-cf20e9160e08",
}
FAILED_POLICY_ID = "5cf919e2-77e3-46ce-ab0e-c237d62cfe2d"
FAILED_POLICY_EVIDENCE_SHA256 = (
    "A225EF5B20CF9FF143D9C7C5EF2713458839478163571040233A69747E0F8798"
)
FAILED_POLICY_CONTRACT_BINDING_SHA256 = (
    "CDC4BC07EA6F67275B985E76B24467CC3A1A11891EFA1953E0F6137344F73645"
)
FAILED_ANALYSIS_ID = "07efdcad-de84-489e-890d-1709b44ef087"
OWNER_ACTION_WINDOW_SECONDS = 86400


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest().upper()


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


def freeze_manifest(repo: Path, attempt: Path, *, protocol_relative=PROTOCOL_RELATIVE,
                    protocol_sha256=PROTOCOL_SHA256, checkpoint_head=CHECKPOINT_HEAD,
                    precontrol_builder=None) -> dict[str, Any]:
    if attempt.exists():
        raise ValueError("V41_ATTEMPT_ALREADY_EXISTS")
    protocol = repo / protocol_relative
    fixture = repo / "backend/tests/golden/fixtures" / FIXTURE_NAME
    scope_baseline = (
        Path("C:/Users/ADMIN-FRED/Documents/Codex/Pepperyn-runtime")
        / "v40-service-readonly-preflight-19.json"
    )
    if (
        file_sha256(protocol) != protocol_sha256
        or file_sha256(fixture) != FIXTURE_SHA256
        or file_sha256(scope_baseline) != SCOPE_BASELINE_SHA256
    ):
        raise ValueError("V41_LOCAL_BASELINE_REFUSED")
    recorded = json.loads(scope_baseline.read_text(encoding="utf-8"))
    if recorded.get("project") != PROJECT_URL or recorded.get("scope") != SCOPE:
        raise ValueError("V41_SCOPE_BASELINE_REFUSED")
    identities = {
        "policy_id": str(uuid4()),
        "request_id": str(uuid4()),
        "execution_id": str(uuid4()),
        "analysis_id": str(uuid4()),
    }
    if len(set(identities.values())) != 4:
        raise ValueError("V41_IDENTITY_COLLISION")
    created_at = datetime.now(timezone.utc)
    manifest = {
        "schema_version": "v41-injected-rehearsal-successor-manifest-1",
        "project_url": PROJECT_URL,
        "checkpoint_head": checkpoint_head,
        "protocol_sha256": protocol_sha256,
        "created_at": created_at.isoformat(),
        "owner_action_deadline": (
            created_at + timedelta(seconds=OWNER_ACTION_WINDOW_SECONDS)
        ).isoformat(),
        "predecessor": {
            "policy_id": FAILED_POLICY_ID,
            "policy_evidence_sha256": FAILED_POLICY_EVIDENCE_SHA256,
            "contract_binding_sha256": FAILED_POLICY_CONTRACT_BINDING_SHA256,
            "analysis_id": FAILED_ANALYSIS_ID,
            "required_enabled": False,
            "outcome": "FAILED_OWNER_ACTION_TIMEOUT_SAFETY_DISABLED",
        },
        "scope": SCOPE,
        "source": {"filename": FIXTURE_NAME, "sha256": FIXTURE_SHA256},
        "identities": identities,
        "ceilings": {"effect_capable_requests": 10, "durable_rows": 5, "auth_logins": 1},
        "policy_contract": {
            "admission_scope": "LOCAL_TEST_ADMISSION",
            "transport_mode": "INJECTED_LOCAL_ONLY",
            "provider_execution_attested": False,
            "producer_global_status": "UNADMITTED",
            "egress_authorization": "CLOSED",
            "real_data_admission": "CLOSED",
        },
    }
    manifest["manifest_sha256"] = sha256(canonical_bytes(manifest)).hexdigest().upper()
    attempt.mkdir(parents=False)
    write_new(attempt / "manifest.json", manifest)
    (attempt / "precontrol.sql").write_text(
        (precontrol_builder or precontrol_sql)(repo, manifest), encoding="utf-8", newline="\n"
    )
    (attempt / "policy-insert.sql").write_text(
        policy_insert_sql(manifest), encoding="utf-8", newline="\n"
    )
    (attempt / "policy-disable.sql").write_text(
        policy_disable_sql(manifest), encoding="utf-8", newline="\n"
    )
    return manifest


def read_manifest(attempt: Path, *, protocol_sha256=PROTOCOL_SHA256,
                  checkpoint_head=CHECKPOINT_HEAD) -> dict[str, Any]:
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    digest_payload = dict(manifest)
    observed = digest_payload.pop("manifest_sha256", None)
    expected = sha256(canonical_bytes(digest_payload)).hexdigest().upper()
    if observed != expected:
        raise ValueError("V41_MANIFEST_MUTATED")
    for value in manifest["identities"].values():
        UUID(value)
    if (
        manifest.get("project_url") != PROJECT_URL
        or manifest.get("checkpoint_head") != checkpoint_head
        or manifest.get("protocol_sha256") != protocol_sha256
        or manifest.get("scope") != SCOPE
        or manifest.get("source") != {"filename": FIXTURE_NAME, "sha256": FIXTURE_SHA256}
        or manifest.get("predecessor") != {
            "policy_id": FAILED_POLICY_ID,
            "policy_evidence_sha256": FAILED_POLICY_EVIDENCE_SHA256,
            "contract_binding_sha256": FAILED_POLICY_CONTRACT_BINDING_SHA256,
            "analysis_id": FAILED_ANALYSIS_ID,
            "required_enabled": False,
            "outcome": "FAILED_OWNER_ACTION_TIMEOUT_SAFETY_DISABLED",
        }
    ):
        raise ValueError("V41_MANIFEST_SCOPE_REFUSED")
    created_at = datetime.fromisoformat(manifest["created_at"])
    deadline = datetime.fromisoformat(manifest["owner_action_deadline"])
    if (
        created_at.utcoffset() is None
        or deadline.utcoffset() is None
        or (deadline - created_at).total_seconds() != OWNER_ACTION_WINDOW_SECONDS
    ):
        raise ValueError("V41_OWNER_ACTION_DEADLINE_REFUSED")
    return manifest


def specification_without_evidence(manifest: Mapping[str, Any]) -> dict[str, Any]:
    scope = manifest["scope"]
    policy = BoundedLocalTestPolicyV1(
        company_id=scope["company_id"], entity_id=scope["entity_id"],
        engagement_id=scope["engagement_id"], source_sha256=FIXTURE_SHA256,
        filename=FIXTURE_NAME, policy_evidence_sha256="0" * 64,
    ).model_dump(mode="json")
    policy.pop("policy_evidence_sha256")
    return policy


def _sql_json(value: Mapping[str, Any]) -> str:
    text = canonical_bytes(value).decode("utf-8")
    if "$v41$" in text:
        raise ValueError("V41_SQL_DELIMITER_REFUSED")
    return "$v41$" + text + "$v41$"


def policy_insert_sql(manifest: Mapping[str, Any]) -> str:
    from sandbox import v41_two_policy_history as history
    if history.enabled(manifest):
        return history.sql(None, manifest, insert=True)
    policy_id = str(UUID(manifest["identities"]["policy_id"]))
    deadline = datetime.fromisoformat(str(manifest["owner_action_deadline"]))
    if deadline.utcoffset() is None:
        raise ValueError("V41_OWNER_ACTION_DEADLINE_REFUSED")
    deadline_sql = deadline.isoformat().replace("'", "''")
    spec = _sql_json(specification_without_evidence(manifest))
    binding = CONTRACT_BINDING.model_dump(mode="json")
    binding_json = _sql_json(binding)
    raw_binding_text = canonical_bytes(binding).decode("utf-8")
    if sha256(raw_binding_text.encode("utf-8")).hexdigest().upper() != GENERIC_ADMISSION_CONTRACT_SHA256:
        raise ValueError("V41_CONTRACT_TEXT_REFUSED")
    binding_text = raw_binding_text.replace("'", "''")
    return f"""-- v41-injected-successor-policy-insert-1; exactly one authorized row\nBEGIN;\nDO $owner$\nDECLARE base jsonb := {spec}::jsonb; final jsonb; changed integer;\nBEGIN\n  IF clock_timestamp() > '{deadline_sql}'::timestamptz THEN\n    RAISE EXCEPTION 'V41_OWNER_ACTION_DEADLINE_EXPIRED';\n  END IF;\n  IF (SELECT count(*) FROM public.generic_producer_policies_v3) <> 1\n     OR NOT EXISTS (\n       SELECT 1 FROM public.generic_producer_policies_v3\n       WHERE id='{FAILED_POLICY_ID}'::uuid AND enabled=false\n         AND contract_binding_sha256='{FAILED_POLICY_CONTRACT_BINDING_SHA256}'\n         AND specification->>'policy_evidence_sha256'='{FAILED_POLICY_EVIDENCE_SHA256}'\n     )\n     OR (SELECT count(*) FROM public.generic_execution_admissions_v3) <> 0\n     OR (SELECT count(*) FROM public.generic_execution_receipts_v3) <> 0\n     OR EXISTS (SELECT 1 FROM public.generic_producer_policies_v3 WHERE id='{policy_id}'::uuid) THEN\n    RAISE EXCEPTION 'V41_SUCCESSOR_PREINSERT_STATE_REFUSED';\n  END IF;\n  final := base || jsonb_build_object('policy_evidence_sha256',\n    upper(encode(sha256(convert_to(base::text,'UTF8')),'hex')));\n  INSERT INTO public.generic_producer_policies_v3(\n    id,specification,contract_binding,contract_binding_text,contract_binding_sha256,enabled)\n  VALUES ('{policy_id}'::uuid,final,{binding_json}::jsonb,\n    '{binding_text}','{GENERIC_ADMISSION_CONTRACT_SHA256}',true);\n  GET DIAGNOSTICS changed = ROW_COUNT;\n  IF changed <> 1 THEN RAISE EXCEPTION 'V41_POLICY_INSERT_COUNT_REFUSED'; END IF;\nEND $owner$;\nCOMMIT;\n"""


def policy_disable_sql(manifest: Mapping[str, Any]) -> str:
    policy_id = str(UUID(manifest["identities"]["policy_id"]))
    return f"""-- v41-injected-policy-disable-1; irreversible safety closure\nBEGIN;\nDO $owner$\nDECLARE changed integer;\nBEGIN\n  UPDATE public.generic_producer_policies_v3 SET enabled=false\n    WHERE id='{policy_id}'::uuid AND enabled=true;\n  GET DIAGNOSTICS changed = ROW_COUNT;\n  IF changed <> 1 THEN RAISE EXCEPTION 'V41_POLICY_DISABLE_COUNT_REFUSED'; END IF;\nEND $owner$;\nCOMMIT;\n"""


def precontrol_sql(repo: Path, manifest: Mapping[str, Any]) -> str:
    from sandbox import v41_two_policy_history as history
    if history.enabled(manifest):
        return history.sql(repo, manifest)
    structural = (repo / "backend/migrations/ppr067_hardening_postflight_read_only.sql").read_text(encoding="utf-8")
    historical = (repo / "backend/migrations/v41_historical_baseline_read_only.sql").read_text(encoding="utf-8")
    ids = manifest["identities"]
    scope = manifest["scope"]
    identity_sql = f"""
-- v41-injected-frozen-identity-precontrol-1
BEGIN TRANSACTION READ ONLY;
SELECT jsonb_build_object(
  'status', CASE WHEN
    EXISTS (SELECT 1 FROM public.profiles WHERE id='{scope['actor_id']}'::uuid AND company_id='{scope['company_id']}'::uuid)
    AND EXISTS (SELECT 1 FROM public.entities WHERE id='{scope['entity_id']}'::uuid AND company_id='{scope['company_id']}'::uuid)
    AND EXISTS (SELECT 1 FROM public.engagements WHERE id='{scope['engagement_id']}'::uuid AND entity_id='{scope['entity_id']}'::uuid)
    AND (SELECT count(*) FROM public.generic_producer_policies_v3) = 1
    AND EXISTS (
      SELECT 1 FROM public.generic_producer_policies_v3
      WHERE id='{FAILED_POLICY_ID}'::uuid AND enabled=false
        AND contract_binding_sha256='{FAILED_POLICY_CONTRACT_BINDING_SHA256}'
        AND specification->>'policy_evidence_sha256'='{FAILED_POLICY_EVIDENCE_SHA256}'
    )
    AND (SELECT count(*) FROM public.generic_execution_admissions_v3) = 0
    AND (SELECT count(*) FROM public.generic_execution_receipts_v3) = 0
    AND NOT EXISTS (SELECT 1 FROM public.analyses WHERE id='{FAILED_ANALYSIS_ID}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.governed_analysis_envelopes WHERE analysis_id='{FAILED_ANALYSIS_ID}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.generic_execution_receipts_v3 WHERE analysis_id='{FAILED_ANALYSIS_ID}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.generic_producer_policies_v3 WHERE id='{ids['policy_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.generic_execution_admissions_v3 WHERE execution_id='{ids['execution_id']}'::uuid OR request_id='{ids['request_id']}'::uuid OR analysis_id='{ids['analysis_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.analyses WHERE id='{ids['analysis_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.governed_analysis_envelopes WHERE analysis_id='{ids['analysis_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.governed_execution_receipts WHERE analysis_id='{ids['analysis_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.execution_receipts_v2 WHERE analysis_id='{ids['analysis_id']}'::uuid)
    AND NOT EXISTS (SELECT 1 FROM public.generic_execution_receipts_v3 WHERE analysis_id='{ids['analysis_id']}'::uuid)
  THEN 'V41_INJECTED_SUCCESSOR_FROZEN_SCOPE_PRECONTROL_PASS' ELSE 'REFUSED' END,
  'policy_id','{ids['policy_id']}','request_id','{ids['request_id']}',
  'execution_id','{ids['execution_id']}','analysis_id','{ids['analysis_id']}',
  'write_performed',false,'auth_performed',false
) AS v41_injected_frozen_scope_precontrol;
ROLLBACK;
"""
    # Preserve the deployment verifier itself. Its empty-policy requirement
    # belongs to deployment, while the successor expects the disabled evidence
    # policy. The exact identity and evidence checks remain in frozen_scope.
    old_counts = "policy_rows = 0 AND admission_rows = 0 AND receipt_rows = 0"
    if structural.count(old_counts) != 1:
        raise ValueError("V41_STRUCTURAL_TEMPLATE_DRIFT")
    structural = structural.replace(old_counts,
        "policy_rows = 1 AND admission_rows = 0 AND receipt_rows = 0")

    def query_body(text: str) -> str:
        begin = "BEGIN TRANSACTION READ ONLY;"
        end = "ROLLBACK;"
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("V41_PRECONTROL_TEMPLATE_DRIFT")
        before, body = text.split(begin)
        body, after = body.split(end)
        if after.strip() or any(
            line.strip() and not line.lstrip().startswith("--")
            for line in before.splitlines()
        ):
            raise ValueError("V41_PRECONTROL_TEMPLATE_DRIFT")
        body = body.strip()
        if not body.endswith(";"):
            raise ValueError("V41_PRECONTROL_TEMPLATE_DRIFT")
        return body[:-1]

    return (
        "-- v41-successor-single-result-precontrol-2\n"
        "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;\n"
        "WITH structural AS (\n" + query_body(structural) + "\n),\n"
        "historical AS (\n" + query_body(historical) + "\n),\n"
        "frozen_scope AS (\n" + query_body(identity_sql) + "\n)\n"
        "SELECT jsonb_build_object(\n"
        " 'check_version','v41-successor-single-result-precontrol-2',\n"
        " 'status',CASE WHEN\n"
        "  s->>'status'='PPR067_HARDENING_STRUCTURAL_POSTFLIGHT_PASS'\n"
        "  AND h->>'status'='V41_HISTORICAL_BASELINE_PASS'\n"
        "  AND f->>'status'='V41_INJECTED_SUCCESSOR_FROZEN_SCOPE_PRECONTROL_PASS'\n"
        " THEN 'V41_SUCCESSOR_PRECONTROL_CHECKS_PASS' ELSE 'REFUSED' END,\n"
        " 'structural',s,'historical',h,'frozen_scope',f,\n"
        " 'historical_comparison_required',true,\n"
        " 'write_performed',false,'auth_performed',false\n"
        ") AS v41_successor_precontrol\n"
        "FROM (SELECT ppr067_hardening_postflight AS s FROM structural) a\n"
        "CROSS JOIN (SELECT v41_historical_baseline AS h FROM historical) b\n"
        "CROSS JOIN (SELECT v41_injected_frozen_scope_precontrol AS f FROM frozen_scope) c;\n"
        "ROLLBACK;\n"
    )
