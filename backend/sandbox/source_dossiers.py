"""Durable synthetic source inspection, distinct from a governed analysis.

No provider, legacy Evidence Ledger mutation, interpretation confirmation or
analysis creation. Caller identity is resolved by the HTTP boundary; this module
also verifies exact entity/engagement ownership before any dossier access.
"""
from __future__ import annotations

import hashlib
import json
from uuid import UUID, uuid5

from sandbox.heterogeneous_workbooks import _registered_understanding, REGISTERED_WORKBOOKS, summarize_understanding
from services.v1_analysis_contract import UnderstandingResult

TABLE = "synthetic_source_dossiers_v1"
VERSION = "synthetic-source-dossier-1"
NAMESPACE = UUID("71b137db-117a-4c76-9258-6af8b2bab454")


class SourceDossierRefused(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest().upper()


def authorized_scope(db, company_id, entity_id):
    try:
        company_id, entity_id = str(UUID(company_id)), str(UUID(entity_id))
        entities = db.from_("entities").select("id,company_id").eq("id", entity_id).eq("company_id", company_id).limit(2).execute().data
        if not entities or len(entities) != 1 or entities[0].get("id") != entity_id or entities[0].get("company_id") != company_id:
            raise SourceDossierRefused("NOT_FOUND")
        engagements = db.from_("engagements").select("id,entity_id").eq("entity_id", entity_id).limit(2).execute().data
        if not engagements or len(engagements) != 1 or engagements[0].get("entity_id") != entity_id:
            raise SourceDossierRefused("NOT_FOUND")
        return dict(company_id=company_id, entity_id=entity_id, engagement_id=str(UUID(engagements[0]["id"])))
    except SourceDossierRefused:
        raise
    except (ValueError, TypeError):
        raise SourceDossierRefused("NOT_FOUND") from None
    except Exception:
        raise SourceDossierRefused("UNAVAILABLE") from None


def _query(db, scope):
    query = db.from_(TABLE).select("*")
    for key, value in scope.items():
        query = query.eq(key, value)
    return query


def _verified(row, scope):
    try:
        if any(row.get(k) != v for k, v in scope.items()) or row.get("schema_version") != VERSION:
            raise ValueError()
        if REGISTERED_WORKBOOKS.get(row["source_sha256"]) != row["filename"]:
            raise ValueError()
        payload = {k: row[k] for k in ("schema_version", "source_sha256", "filename", "understanding", *scope)}
        expected_id = str(uuid5(NAMESPACE, digest({**scope, "source_sha256": row["source_sha256"], "schema_version": VERSION})))
        if row["payload_sha256"] != digest(payload) or row["id"] != expected_id:
            raise ValueError()
        understanding = UnderstandingResult.model_validate(row["understanding"])
        return {"dossier_id": row["id"], **scope, "filename": row["filename"],
                "source_sha256": row["source_sha256"], "payload_sha256": row["payload_sha256"],
                "schema_version": VERSION, "evidence_role": "SOURCE_INSPECTION_NOT_ANALYSIS",
                **summarize_understanding(understanding)}
    except Exception:
        raise SourceDossierRefused("INTEGRITY_FAILED") from None


def load_dossier(db, *, company_id, entity_id, dossier_id):
    scope = authorized_scope(db, company_id, entity_id)
    try:
        dossier_id = str(UUID(dossier_id))
        rows = _query(db, scope).eq("id", dossier_id).limit(2).execute().data
    except ValueError:
        raise SourceDossierRefused("NOT_FOUND") from None
    except Exception:
        raise SourceDossierRefused("UNAVAILABLE") from None
    if not rows or len(rows) != 1:
        raise SourceDossierRefused("NOT_FOUND")
    return _verified(rows[0], scope)


def list_dossiers(db, *, company_id, entity_id):
    scope = authorized_scope(db, company_id, entity_id)
    try:
        rows = _query(db, scope).limit(101).execute().data
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError()
    except Exception:
        raise SourceDossierRefused("UNAVAILABLE") from None
    # Never turn a corrupt/unavailable dossier into an empty successful list.
    return sorted((_verified(row, scope) for row in rows), key=lambda row: row["dossier_id"])


def capture_dossier(db, *, company_id, entity_id, raw, filename):
    scope = authorized_scope(db, company_id, entity_id)
    source_sha256, understanding, _ = _registered_understanding(raw, filename)
    payload = {**scope, "schema_version": VERSION, "source_sha256": source_sha256,
               "filename": filename, "understanding": understanding.model_dump(mode="json")}
    dossier_id = str(uuid5(NAMESPACE, digest({**scope, "source_sha256": source_sha256, "schema_version": VERSION})))
    record = {**payload, "id": dossier_id, "payload_sha256": digest(payload)}
    try:
        db.from_(TABLE).insert(record).execute()
    except Exception as exc:
        # Only a database unique violation can mean an idempotent retry.
        if getattr(exc, "code", None) != "23505":
            raise SourceDossierRefused("UNAVAILABLE") from None
    stored = load_dossier(db, company_id=company_id, entity_id=entity_id, dossier_id=dossier_id)
    if stored["payload_sha256"] != record["payload_sha256"]:
        raise SourceDossierRefused("INTEGRITY_FAILED")
    return stored
