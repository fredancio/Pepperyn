"""
Feedback routes — Pepperyn v3.

POST /api/feedback — Record user feedback after an analysis.
Fields: learned_something, would_act, trust_score, frustration, willingness_to_pay
"""
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from models.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackCreate,
    authorization: Optional[str] = Header(default=None),
    x_auth_type: Optional[str] = Header(default=None),
):
    """
    Record user feedback for an analysis.
    Non-blocking — errors are silently ignored after auth check.
    """
    # Resolve auth (reuse logic from analyze router)
    from routers.analyze import _resolve_auth
    company_id, plan, auth_type = await _resolve_auth(authorization, x_auth_type)

    try:
        from main import get_supabase_service
        supabase = get_supabase_service()

        payload = {
            "company_id": company_id,
            "analyse_id": request.analyse_id,
            "learned_something": request.learned_something,
            "would_act": request.would_act,
            "trust_score": request.trust_score,
            "frustration": request.frustration,
            "willingness_to_pay": request.willingness_to_pay,
        }

        supabase.from_("feedback").insert(payload).execute()

    except Exception:
        # Non-blocking — feedback failure must never break the UX
        pass

    return FeedbackResponse(success=True, message="Feedback enregistré")
