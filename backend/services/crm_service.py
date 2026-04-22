"""
crm_service.py — Synchronisation Supabase → Airtable CRM

Supabase = source de vérité (stockage, auth, limites d'usage)
Airtable = dashboard CRM uniquement (pilotage business, comportement utilisateur)

Tables Airtable attendues :
  • Users CRM   — une fiche par utilisateur (upsert sur user_id)
  • Analyses    — une ligne par analyse
  • Events      — une ligne par action utilisateur

Variables d'env requises :
  AIRTABLE_API_TOKEN      — Personal Access Token (commence par pat...)
  AIRTABLE_BASE_ID        — ID de la base Airtable (appXXXXXXXX, dans l'URL)
  AIRTABLE_USERS_TABLE    — Nom exact de la table Users CRM (ex: "Users CRM")
  AIRTABLE_ANALYSES_TABLE — Nom exact de la table Analyses
  AIRTABLE_EVENTS_TABLE   — Nom exact de la table Events

Toutes les fonctions sont NON-BLOQUANTES : une erreur Airtable n'impacte jamais
l'utilisateur. Les erreurs sont loggées mais jamais levées.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

AIRTABLE_BASE_URL   = "https://api.airtable.com/v0"
API_TOKEN           = os.getenv("AIRTABLE_API_TOKEN", "")
BASE_ID             = os.getenv("AIRTABLE_BASE_ID", "")
USERS_TABLE         = os.getenv("AIRTABLE_USERS_TABLE", "Users CRM")
ANALYSES_TABLE      = os.getenv("AIRTABLE_ANALYSES_TABLE", "Analyses")
EVENTS_TABLE        = os.getenv("AIRTABLE_EVENTS_TABLE", "Events")

# ─── Noms de champs Airtable ─────────────────────────────────────────────────
# Doit correspondre EXACTEMENT aux noms créés dans votre base Airtable.
# Si vous avez nommé un champ différemment, modifiez ici uniquement.

USERS_FIELDS = {
    "user_id":              "User ID",
    "email":                "emails",
    "name":                 "Name",
    "industry":             "Industry",
    "business_model":       "business_model",
    "plan":                 "plan",
    "analyses_count":       "analyses_count",
    "chat_messages_count":  "chat_message_count",
    "last_analysis_date":   "Last_analysis_date",
    "created_at":           "Created_at",
}

ANALYSES_FIELDS = {
    "analysis_id":          "analysis_id",
    "user_id":              "user_id",        # Linked Record → Users CRM
    "file_name":            "file_name",
    "revenue":              "revenue",
    "costs":                "costs",
    "margin":               "margin",
    "score_profitability":  "score_profitability",
    "score_risk":           "score_risk",
    "score_structure":      "score_structure",
    "summary":              "summary",
    "model_used":           "model_used",
    "tokens_used":          "tokens_used",
    "cost_estimate":        "cost_estimate",
    "created_at":           "created_at",
}

EVENTS_FIELDS = {
    "event_id":     "event_id",
    "user_id":      "user_id",       # Linked Record → Users CRM
    "event_type":   "event_type",
    "metadata":     "metadata",
    "created_at":   "created_at",
}


# ─── Helpers internes ────────────────────────────────────────────────────────

def _is_configured() -> bool:
    return bool(API_TOKEN and BASE_ID)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }


def _table_url(table_name: str) -> str:
    return f"{AIRTABLE_BASE_URL}/{BASE_ID}/{table_name}"


def _now_iso() -> str:
    """Retourne la date+heure courante en ISO 8601 complet (pour les champs DateTime)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _today() -> str:
    """Retourne la date du jour au format YYYY-MM-DD (pour les champs Date Airtable)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get_user_record_id(user_id: str) -> Optional[str]:
    """
    Recherche l'enregistrement Airtable d'un utilisateur par son user_id.
    Retourne le recordId Airtable (recXXXXXX) ou None si introuvable.
    """
    if not user_id:
        logger.warning("[CRM] _get_user_record_id: user_id is empty/None — skipping")
        return None
    try:
        url = _table_url(USERS_TABLE)
        formula = f"{{{USERS_FIELDS['user_id']}}}='{user_id}'"
        with httpx.Client(timeout=10) as client:
            r = client.get(url, headers=_headers(), params={
                "filterByFormula": formula,
                "maxRecords": 1,
            })
            if not r.is_success:
                logger.warning(f"[CRM] _get_user_record_id HTTP {r.status_code}: {r.text[:300]}")
                return None
            records = r.json().get("records", [])
            return records[0]["id"] if records else None
    except Exception as e:
        logger.warning(f"[CRM] _get_user_record_id({user_id}) error: {e}")
        return None


def _get_user_field(user_id: str, field_name: str) -> Any:
    """Retourne la valeur d'un champ d'un utilisateur existant."""
    try:
        url = _table_url(USERS_TABLE)
        formula = f"{{{USERS_FIELDS['user_id']}}}='{user_id}'"
        with httpx.Client(timeout=10) as client:
            r = client.get(url, headers=_headers(), params={
                "filterByFormula": formula,
                "fields[]": field_name,
                "maxRecords": 1,
            })
            r.raise_for_status()
            records = r.json().get("records", [])
            if records:
                return records[0].get("fields", {}).get(field_name)
    except Exception as e:
        logger.warning(f"[CRM] _get_user_field error: {e}")
    return None


# ─── Fonctions publiques ──────────────────────────────────────────────────────

def upsert_user(
    user_id: str,
    email: str = "",
    name: str = "",
    industry: str = "",
    business_model: str = "",
    plan: str = "free",
) -> Optional[str]:
    """
    Crée ou met à jour un utilisateur dans la table 'Users CRM' Airtable.
    Retourne le recordId Airtable (utile pour les champs linked records).
    Appelé à la première analyse ou à l'inscription.
    Non-bloquant — les erreurs sont loggées mais jamais levées.
    """
    if not _is_configured():
        return None
    if not user_id:
        logger.warning("[CRM] upsert_user: user_id est vide/None — skipping")
        return None

    try:
        existing_id = _get_user_record_id(user_id)
        url = _table_url(USERS_TABLE)

        if existing_id:
            # Utilisateur existant → mise à jour du plan uniquement
            with httpx.Client(timeout=10) as client:
                r = client.patch(url, headers=_headers(), json={
                    "records": [{
                        "id": existing_id,
                        "fields": {
                            USERS_FIELDS["plan"]: plan,
                        }
                    }]
                })
                if not r.is_success:
                    logger.warning(f"[CRM] upsert_user PATCH HTTP {r.status_code}: {r.text[:300]}")
                    return existing_id
                logger.info(f"[CRM] upsert_user updated — {user_id}")
                return existing_id
        else:
            # Nouvel utilisateur → construction des champs (éviter les champs vides invalides)
            fields: dict[str, Any] = {
                USERS_FIELDS["user_id"]:             user_id,
                USERS_FIELDS["name"]:                name or "",
                USERS_FIELDS["industry"]:            industry or "",
                USERS_FIELDS["business_model"]:      business_model or "",
                USERS_FIELDS["plan"]:                plan,
                USERS_FIELDS["analyses_count"]:      0,
                USERS_FIELDS["chat_messages_count"]: 0,
                USERS_FIELDS["created_at"]:          _today(),
            }
            # Email : champ de type Email dans Airtable → ne pas envoyer si vide
            if email:
                fields[USERS_FIELDS["email"]] = email

            with httpx.Client(timeout=10) as client:
                r = client.post(url, headers=_headers(), json={
                    "records": [{"fields": fields}]
                })
                if not r.is_success:
                    logger.warning(f"[CRM] upsert_user POST HTTP {r.status_code}: {r.text[:300]}")
                    return None
                new_id = r.json()["records"][0]["id"]
                logger.info(f"[CRM] upsert_user created — {user_id} → {new_id}")
                return new_id

    except Exception as e:
        logger.warning(f"[CRM] upsert_user error for {user_id}: {e}")
        return None


def log_analysis(
    user_id: str,
    analyse_id: str,
    filename: str,
    analysis_result: dict,
    model_used: str = "claude-opus-4-6",
    tokens_used: int = 0,
    cost_estimate: float = 0.0,
    email: str = "",
    industry: str = "",
    business_model: str = "",
    plan: str = "free",
) -> None:
    """
    1. Crée/met à jour l'utilisateur dans Users CRM.
    2. Insère une ligne dans Analyses.
    3. Met à jour l'utilisateur : analyses_count +1, last_analysis_date.
    4. Log l'event "analysis_started".
    Non-bloquant — les erreurs sont loggées mais jamais levées.
    """
    if not _is_configured():
        return

    today = _today()

    # ── Étape 1 : Upsert utilisateur, récupérer son recordId ─────────────────
    user_record_id = upsert_user(
        user_id=user_id,
        email=email,
        industry=industry,
        business_model=business_model,
        plan=plan,
    )

    # ── Étape 2 : Insérer l'analyse ───────────────────────────────────────────
    try:
        analysis_fields: dict[str, Any] = {
            ANALYSES_FIELDS["analysis_id"]:         analyse_id,
            ANALYSES_FIELDS["file_name"]:           filename,
            ANALYSES_FIELDS["revenue"]:             analysis_result.get("diagnostic_revenus", ""),
            ANALYSES_FIELDS["costs"]:               analysis_result.get("diagnostic_couts", ""),
            ANALYSES_FIELDS["margin"]:              analysis_result.get("diagnostic_marges", ""),
            ANALYSES_FIELDS["summary"]:             (analysis_result.get("resume_executif") or "")[:500],
            ANALYSES_FIELDS["model_used"]:          model_used,
            ANALYSES_FIELDS["tokens_used"]:         tokens_used,
            ANALYSES_FIELDS["cost_estimate"]:       round(cost_estimate, 4),
            ANALYSES_FIELDS["created_at"]:          today,
        }
        # Scores (optionnels)
        if analysis_result.get("score_rentabilite") is not None:
            analysis_fields[ANALYSES_FIELDS["score_profitability"]] = analysis_result["score_rentabilite"]
        if analysis_result.get("score_risque") is not None:
            analysis_fields[ANALYSES_FIELDS["score_risk"]] = analysis_result["score_risque"]
        if analysis_result.get("score_structure") is not None:
            analysis_fields[ANALYSES_FIELDS["score_structure"]] = analysis_result["score_structure"]
        # Lien vers Users CRM (si le champ est de type Linked Record)
        if user_record_id:
            analysis_fields[ANALYSES_FIELDS["user_id"]] = [user_record_id]

        url = _table_url(ANALYSES_TABLE)
        with httpx.Client(timeout=10) as client:
            r = client.post(url, headers=_headers(), json={
                "records": [{"fields": analysis_fields}]
            })
            if not r.is_success:
                logger.warning(f"[CRM] log_analysis POST HTTP {r.status_code}: {r.text[:400]}")
            else:
                logger.info(f"[CRM] log_analysis inserted — {analyse_id} for {user_id}")

    except Exception as e:
        logger.warning(f"[CRM] log_analysis insert error: {e}")

    # ── Étape 3 : Mettre à jour le compteur d'analyses et la date ────────────
    if user_record_id:
        try:
            current_count = _get_user_field(user_id, USERS_FIELDS["analyses_count"]) or 0
            url = _table_url(USERS_TABLE)
            with httpx.Client(timeout=10) as client:
                r = client.patch(url, headers=_headers(), json={
                    "records": [{
                        "id": user_record_id,
                        "fields": {
                            USERS_FIELDS["analyses_count"]:     int(current_count) + 1,
                            USERS_FIELDS["last_analysis_date"]: today,
                        }
                    }]
                })
                r.raise_for_status()
                logger.info(f"[CRM] user analyses_count → {int(current_count)+1} for {user_id}")
        except Exception as e:
            logger.warning(f"[CRM] log_analysis user update error: {e}")

    # ── Étape 4 : Log event ───────────────────────────────────────────────────
    log_event(
        user_id=user_id,
        event_type="analysis_started",
        metadata={
            "analyse_id": analyse_id,
            "file_name": filename,
            "model": model_used,
            "tokens": tokens_used,
            "cost_estimate": cost_estimate,
        },
        user_record_id=user_record_id,
    )


def log_event(
    user_id: str,
    event_type: str,
    metadata: Optional[dict] = None,
    user_record_id: Optional[str] = None,
) -> None:
    """
    Insère un event dans la table 'Events' Airtable.
    event_type : signup | login | file_upload | analysis_started |
                 chat_message | export_generated
    Non-bloquant — les erreurs sont loggées mais jamais levées.

    Logs serveur systématiques pour monitoring :
      console → [CRM EVENT] user_id | event_type | metadata
    """
    if not _is_configured():
        return

    # Log serveur (monitoring)
    logger.info(f"[CRM EVENT] user={user_id} | type={event_type} | meta={metadata}")

    try:
        event_fields: dict[str, Any] = {
            EVENTS_FIELDS["event_id"]:   str(uuid.uuid4()),
            EVENTS_FIELDS["event_type"]: event_type,
            EVENTS_FIELDS["metadata"]:   json.dumps(metadata or {}, ensure_ascii=False),
            EVENTS_FIELDS["created_at"]: _today(),
        }
        # Lien vers Users CRM
        _uid = user_record_id or _get_user_record_id(user_id)
        if _uid:
            event_fields[EVENTS_FIELDS["user_id"]] = [_uid]

        url = _table_url(EVENTS_TABLE)
        with httpx.Client(timeout=10) as client:
            r = client.post(url, headers=_headers(), json={
                "records": [{"fields": event_fields}]
            })
            r.raise_for_status()
            logger.info(f"[CRM] log_event OK — {event_type} for {user_id}")

    except Exception as e:
        logger.warning(f"[CRM] log_event error ({event_type} / {user_id}): {e}")


def log_chat(
    user_id: str,
    analysis_id: Optional[str] = None,
    model_used: str = "",
) -> None:
    """
    Incrémente chat_messages_count dans Users CRM + log event "chat_message".
    Appelé après chaque message de chat réussi.
    Non-bloquant — les erreurs sont loggées mais jamais levées.
    """
    if not _is_configured():
        return

    user_record_id = _get_user_record_id(user_id)

    if user_record_id:
        try:
            current_count = _get_user_field(user_id, USERS_FIELDS["chat_messages_count"]) or 0
            url = _table_url(USERS_TABLE)
            with httpx.Client(timeout=10) as client:
                r = client.patch(url, headers=_headers(), json={
                    "records": [{
                        "id": user_record_id,
                        "fields": {
                            USERS_FIELDS["chat_messages_count"]: int(current_count) + 1,
                        }
                    }]
                })
                r.raise_for_status()
                logger.info(f"[CRM] log_chat → chat_count={int(current_count)+1} for {user_id}")
        except Exception as e:
            logger.warning(f"[CRM] log_chat count error: {e}")

    log_event(
        user_id=user_id,
        event_type="chat_message",
        metadata={
            "analysis_id": analysis_id,
            "model": model_used,
        },
        user_record_id=user_record_id,
    )


def update_user_plan(user_id: str, new_plan: str) -> None:
    """
    Met à jour le plan d'un utilisateur dans le CRM.
    Appelé lors d'un upgrade/downgrade de plan (Stripe webhook).
    Non-bloquant.
    """
    if not _is_configured():
        return
    try:
        existing_id = _get_user_record_id(user_id)
        if existing_id:
            url = _table_url(USERS_TABLE)
            with httpx.Client(timeout=10) as client:
                r = client.patch(url, headers=_headers(), json={
                    "records": [{
                        "id": existing_id,
                        "fields": {USERS_FIELDS["plan"]: new_plan}
                    }]
                })
                r.raise_for_status()
                logger.info(f"[CRM] update_user_plan → {new_plan} for {user_id}")
    except Exception as e:
        logger.warning(f"[CRM] update_user_plan error: {e}")
