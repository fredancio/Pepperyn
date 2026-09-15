"""Read-only portfolio projection for the explicit governed V1 workflow.

The V1 decision registry deliberately creates no ``DecisionArc``. This module
lets the existing portfolio surface see an actionable governed checkpoint
without copying it into the legacy arc state machine or creating new truth.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PortfolioReadUnavailable(RuntimeError):
    """Required portfolio evidence could not be read; empty is not established."""

_PRIORITY_ORDER = {"urgent": 0, "to_check": 1, "done": 2, "closed": 3}
_TERMINAL_INTENTIONS = {"rejected", "no_longer_relevant"}


def _days_since(value: Optional[str], now: datetime) -> int:
    if not value:
        return 0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max((now - parsed.astimezone(timezone.utc)).days, 0)
    except (TypeError, ValueError):
        return 0


def _rows_by(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows if row.get(key)}


def _read_rows(query, label: str) -> list[dict]:
    """Never turn an unavailable registry into an empty attention queue."""
    try:
        return list(query.execute().data or [])
    except Exception as exc:
        logger.warning("[GOVERNED PORTFOLIO] %s unavailable: %s", label, type(exc).__name__)
        raise PortfolioReadUnavailable("PORTFOLIO_SOURCE_UNAVAILABLE") from exc


def _to_item(
    decision: dict[str, Any],
    followup: Optional[dict[str, Any]],
    execution: Optional[dict[str, Any]],
    entity_id: str,
    now: datetime,
) -> Optional[dict[str, Any]]:
    """Project persisted states; never infer a transition or an outcome."""
    if decision.get("decision_kind") == "rejected" or decision.get("status") in _TERMINAL_INTENTIONS:
        return None

    confirmed_at = decision.get("decision_confirmed_at")
    title = (decision.get("decision_text") if confirmed_at else None) or decision.get("recommendation_text") or ""

    # Without prospective ExpectedImpact, execution creates no honest open
    # outcome-review task. The execution remains in its governed analysis.
    if execution:
        return None
    if followup and followup.get("followup_status") == "not_pursued":
        return None

    if followup and followup.get("followup_status") == "blocked":
        days = _days_since(followup.get("recorded_at"), now)
        return {
            "arc_id": f"governed:{decision['id']}", "source_type": "governed_decision",
            "entity_id": entity_id, "priority": "urgent", "title": title,
            "temporal_context": f"Suivi bloqué depuis {days} jour{'s' if days != 1 else ''}",
            "why_it_matters": "Une décision confirmée reste bloquée.",
            "questions_to_ask": ["Quelle validation manque encore pour débloquer cette décision ?"],
            "learning_text": None, "age_days": days, "evidence_support": None,
        }

    if not confirmed_at:
        days = _days_since(decision.get("created_at"), now)
        return {
            "arc_id": f"governed:{decision['id']}", "source_type": "governed_decision",
            "entity_id": entity_id, "priority": "urgent" if days > 21 else "to_check",
            "title": title,
            "temporal_context": f"Intention enregistrée il y a {days} jour{'s' if days != 1 else ''}",
            "why_it_matters": "Aucune décision professionnelle n'est confirmée.",
            "questions_to_ask": ["Quelle décision professionnelle retenez-vous ?"],
            "learning_text": None, "age_days": days, "evidence_support": None,
        }

    anchor = (followup or {}).get("recorded_at") or confirmed_at
    days = _days_since(anchor, now)
    status = (followup or {}).get("followup_status")
    if status == "pending_validation":
        context = f"Validations attendues depuis {days} jour{'s' if days != 1 else ''}"
        why = "Les prérequis de la décision restent à valider."
        question = "Les validations préalables sont-elles maintenant réunies ?"
    elif status == "in_progress":
        context = f"Suivi en cours depuis {days} jour{'s' if days != 1 else ''}"
        why = "La décision confirmée est en cours de suivi."
        question = "Quelle est la prochaine étape observable du suivi ?"
    elif status == "completed":
        context = f"Suivi terminé il y a {days} jour{'s' if days != 1 else ''}"
        why = "Aucune exécution effective n'est enregistrée."
        question = "La décision a-t-elle été effectivement exécutée ?"
    else:
        context = f"Décision confirmée il y a {days} jour{'s' if days != 1 else ''}"
        why = "Le premier point de suivi n'est pas encore enregistré."
        question = "Quel est l'état actuel de cette décision ?"

    return {
        "arc_id": f"governed:{decision['id']}", "source_type": "governed_decision",
        "entity_id": entity_id, "priority": "to_check", "title": title,
        "temporal_context": context, "why_it_matters": why,
        "questions_to_ask": [question], "learning_text": None,
        "age_days": days, "evidence_support": None,
    }


def build_governed_portfolio_cards(supabase, company_id: str, *, now: Optional[datetime] = None) -> list[dict]:
    """Build tenant-bound cards from V1 registries, using SELECT only."""
    now = now or datetime.now(timezone.utc)
    decisions = _read_rows(
        supabase.from_("decision_feedback").select(
            "id,company_id,report_id,recommendation_text,status,decision_kind,"
            "decision_text,decision_confirmed_at,created_at"
        ).eq("company_id", company_id), "decision registry",
    )
    if not decisions:
        return []
    decisions = [row for row in decisions if row.get("company_id") == company_id]
    report_ids = [row.get("report_id") for row in decisions if row.get("report_id")]
    if not report_ids:
        return []

    # The immutable envelope is the authoritative discriminator between the
    # governed V1 workflow and legacy feedback rows. Never infer that boundary
    # from recommendation text, status or the presence/absence of an arc.
    envelopes = _read_rows(
        supabase.from_("governed_analysis_envelopes").select(
            "analysis_id,company_id,entity_id"
        ).eq(
            "company_id", company_id
        ).in_("analysis_id", report_ids), "governed envelope scope",
    )
    entity_by_report = {
        row["analysis_id"]: row.get("entity_id") for row in envelopes
        if row.get("analysis_id") and row.get("entity_id") and row.get("company_id") == company_id
    }

    decision_ids = [row["id"] for row in decisions if row.get("id")]
    followups = _read_rows(
        supabase.from_("governed_decision_followups").select(
            "decision_feedback_id,company_id,followup_status,recorded_at"
        ).eq("company_id", company_id).in_("decision_feedback_id", decision_ids),
        "follow-up registry",
    )
    executions = _read_rows(
        supabase.from_("governed_decision_executions").select(
            "decision_feedback_id,company_id,executed_on,recorded_at"
        ).eq("company_id", company_id).in_("decision_feedback_id", decision_ids),
        "execution registry",
    )
    followup_by_decision = _rows_by(
        [row for row in followups if row.get("company_id") == company_id], "decision_feedback_id"
    )
    execution_by_decision = _rows_by(
        [row for row in executions if row.get("company_id") == company_id], "decision_feedback_id"
    )

    items = []
    for decision in decisions:
        entity_id = entity_by_report.get(decision.get("report_id"))
        if not entity_id:
            continue
        item = _to_item(decision, followup_by_decision.get(decision["id"]),
                        execution_by_decision.get(decision["id"]), entity_id, now)
        if item:
            items.append(item)
    if not items:
        return []

    entity_ids = sorted({item["entity_id"] for item in items})
    entities = _read_rows(
        supabase.from_("entities").select("id,company_id,name").eq(
            "company_id", company_id
        ).in_("id", entity_ids), "entity registry",
    )
    names = {
        row["id"]: row.get("name") for row in entities
        if row.get("id") and row.get("name") and row.get("company_id") == company_id
    }

    by_entity: dict[str, list[dict]] = {}
    for item in items:
        if item["entity_id"] in names:
            by_entity.setdefault(item["entity_id"], []).append(item)

    cards = []
    for entity_id, entity_items in by_entity.items():
        entity_items.sort(key=lambda item: (
            _PRIORITY_ORDER.get(item["priority"], 99), -item.get("age_days", 0), item["arc_id"]
        ))
        top = entity_items[0]
        cards.append({"entity_id": entity_id, "entity_name": names[entity_id],
                      "top_item": top, "other_active_count": len(entity_items) - 1,
                      "why_it_matters_display": top.get("why_it_matters")})
    cards.sort(key=lambda card: (
        _PRIORITY_ORDER.get(card["top_item"]["priority"], 99),
        -card["top_item"].get("age_days", 0), card["entity_name"].lower(),
    ))
    return cards


def merge_portfolio_cards(legacy_cards: list[dict], governed_cards: list[dict]) -> list[dict]:
    """Merge two read models without changing either underlying registry."""
    grouped: dict[str, list[dict]] = {}
    for card in [*legacy_cards, *governed_cards]:
        if card.get("entity_id") and card.get("top_item"):
            grouped.setdefault(card["entity_id"], []).append(card)
    merged = []
    for cards in grouped.values():
        cards.sort(key=lambda card: (
            _PRIORITY_ORDER.get(card["top_item"].get("priority"), 99),
            -card["top_item"].get("age_days", 0), card.get("entity_name", "").lower(),
        ))
        top = cards[0]
        total_points = sum(1 + max(int(card.get("other_active_count", 0)), 0) for card in cards)
        merged.append({**top, "other_active_count": total_points - 1})
    merged.sort(key=lambda card: (
        _PRIORITY_ORDER.get(card["top_item"].get("priority"), 99),
        -card["top_item"].get("age_days", 0), card.get("entity_name", "").lower(),
    ))
    return merged
