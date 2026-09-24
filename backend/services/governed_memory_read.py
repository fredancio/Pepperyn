"""Read-only lifecycle projection of an already ownership-verified envelope.

Internal application helper, not authentication or a public API. Caller must first
load the envelope through the ownership boundary. No fixture or provider dependency.
"""
import logging
from services.decision_memory_service import make_recommendation_id

logger = logging.getLogger(__name__)


class GovernedMemoryUnavailable(RuntimeError):
    pass


def recommendations_tracking(
    envelope, analysis_id: str, supabase=None, *, feedback_required: bool = False,
) -> list[dict]:
    """Project governed recommendations into the existing intention UI contract.

    This is deliberately an intention/feedback projection only. It neither
    creates a DecisionKernel nor represents a recommendation as a confirmed
    professional decision.
    """
    priority = {"P1": "haute", "P2": "moyenne", "P3": "basse"}
    items = [
        {
            "id": make_recommendation_id(analysis_id, "plan_action", index),
            "text": item.action,
            "rationale": item.rationale,
            "fact_ids": list(item.fact_ids),
            "prerequisite_validation": list(item.prerequisite_validation),
            "source": "plan_action",
            "priority": priority[item.priority],
            "index": index,
        }
        for index, item in enumerate(envelope.governed_analysis.recommendations)
    ]
    if supabase is None:
        return items

    def unavailable(stage: str) -> list[dict]:
        # Do not confuse a failed read with a verified absence. Do not log
        # database exception bodies, which can contain sensitive context.
        logger.warning("[V1 MEMORY] read unavailable stage=%s", stage)
        if feedback_required:
            raise GovernedMemoryUnavailable("GOVERNED_MEMORY_UNAVAILABLE")
        return [dict(item, memory_read_state="UNAVAILABLE") for item in items]

    def read_rows(response):
        rows = response.data
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Invalid memory response")
        return rows

    try:
        rows = read_rows(
            supabase.from_("decision_feedback").select(
                "id,recommendation_id,status,comment,decision_kind,decision_text,"
                "decision_confirmed_at,decision_confirmation_source,prerequisites_acknowledged"
            )
            .eq("report_id", analysis_id).execute()
        )
        feedback = {row["recommendation_id"]: row for row in rows}
        feedback_ids = [row["id"] for row in rows]
        if len(feedback) != len(rows) or any(not value for value in feedback_ids):
            raise ValueError("Invalid memory identity")
    except Exception:
        return unavailable("INTENTION")
    followups = {}
    executions = {}
    prerequisite_evidence = {}

    def bound_rows(rows):
        result = {row["decision_feedback_id"]: row for row in rows}
        if len(result) != len(rows) or not set(result).issubset(feedback_ids):
            raise ValueError("Invalid memory binding")
        return result

    if feedback_ids:
        try:
            followup_rows = read_rows(
                supabase.from_("governed_decision_followups").select(
                    "decision_feedback_id,followup_status,professional_note,"
                    "prerequisites_confirmed_complete,confirmation_source,recorded_at"
                ).eq("report_id", analysis_id).execute()
            )
            followups = bound_rows(followup_rows)
        except Exception:
            return unavailable("FOLLOWUP")
        try:
            execution_rows = read_rows(
                supabase.from_("governed_decision_executions").select(
                    "decision_feedback_id,executed_on,professional_note,"
                    "prerequisites_confirmed_complete,confirmation_source,recorded_at"
                ).eq("report_id", analysis_id).execute()
            )
            executions = bound_rows(execution_rows)
        except Exception:
            return unavailable("EXECUTION")
        try:
            evidence_rows = read_rows(
                supabase.from_("governed_decision_prerequisite_evidence").select(
                    "id,decision_feedback_id,fixture_id,payload_sha256,period_start,period_end,"
                    "provenance,evidence_role,recorded_at"
                ).eq("report_id", analysis_id).execute()
            )
            prerequisite_evidence = bound_rows(evidence_rows)
        except Exception:
            return unavailable("PREREQUISITES")
    for item in items:
        item["memory_read_state"] = "AVAILABLE"
        saved = feedback.get(item["id"])
        item["status"] = saved.get("status") if saved else None
        item["comment"] = saved.get("comment") if saved else None
        item["decision_kind"] = saved.get("decision_kind") if saved else None
        item["decision_text"] = saved.get("decision_text") if saved else None
        item["decision_confirmed_at"] = saved.get("decision_confirmed_at") if saved else None
        item["decision_confirmation_source"] = (
            saved.get("decision_confirmation_source") if saved else None
        )
        item["prerequisites_acknowledged"] = (
            saved.get("prerequisites_acknowledged") if saved else None
        )
        item["followup"] = followups.get(saved.get("id")) if saved else None
        item["execution"] = executions.get(saved.get("id")) if saved else None
        item["prerequisite_evidence"] = prerequisite_evidence.get(saved.get("id")) if saved else None
    return items
