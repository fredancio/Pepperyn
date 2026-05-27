"""
routers/contact.py — Pepperyn
Endpoint pour recevoir les demandes de contact (plan SCALE).
Stocke dans Supabase, visible dans le CRM admin.
"""
from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contact", tags=["contact"])


class ContactRequest(BaseModel):
    prenom_nom: str
    email: str
    entreprise: Optional[str] = None
    taille_equipe: Optional[str] = None
    defis: Optional[List[str]] = None
    utilise_ia: Optional[str] = None
    message: Optional[str] = None
    souhaite_contact: bool = True


@router.post("")
async def submit_contact(body: ContactRequest):
    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        result = supabase.from_("contact_requests").insert({
            "prenom_nom": body.prenom_nom,
            "email": body.email,
            "entreprise": body.entreprise,
            "taille_equipe": body.taille_equipe,
            "defis": body.defis or [],
            "utilise_ia": body.utilise_ia,
            "message": body.message,
            "souhaite_contact": body.souhaite_contact,
        }).execute()

        logger.info(f"[CONTACT] New request from {body.email}")
        return {"success": True}

    except Exception as e:
        logger.error(f"[CONTACT] Error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/requests")
async def list_contact_requests(authorization: str | None = None):
    """Pour le CRM admin — liste toutes les demandes."""
    from fastapi import Header, HTTPException
    import os

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        result = (
            supabase.from_("contact_requests")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return {"success": True, "data": result.data or []}
    except Exception as e:
        return {"success": True, "data": [], "error": str(e)}
