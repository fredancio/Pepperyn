"""
routers/entities.py — Pepperyn V11
Endpoints pour les workspaces et entités.

GET  /api/entities          → liste les entités de la company connectée
POST /api/entities          → crée une nouvelle entité (POWER+ seulement)
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entities", tags=["entities"])


async def _resolve_company(authorization: Optional[str]) -> tuple[str, str]:
    """Résout le token → (company_id, plan)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    token = authorization.split(" ", 1)[1]

    import os
    from jose import jwt, JWTError
    JWT_SECRET = os.getenv("JWT_GUEST_SECRET", "pepperyn_guest_secret_key_change_in_prod")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") == "guest":
            return payload["company_id"], payload.get("plan", "free")
    except JWTError:
        pass

    from main import get_supabase_service
    supabase = get_supabase_service()
    try:
        user_resp = supabase.auth.get_user(token)
        if user_resp and user_resp.user:
            profile = (
                supabase.from_("profiles")
                .select("company_id, company:companies(plan)")
                .eq("id", user_resp.user.id)
                .limit(1)
                .execute()
            )
            if profile.data:
                company_id = profile.data[0].get("company_id")
                plan = (profile.data[0].get("company") or {}).get("plan", "free")
                if company_id:
                    return company_id, plan
    except Exception as e:
        logger.warning(f"[ENTITIES AUTH] {e}")

    raise HTTPException(status_code=401, detail="Token invalide")


@router.get("")
async def list_entities(
    authorization: Optional[str] = Header(default=None),
):
    """
    Retourne la liste des entités de la company connectée.
    Utilisé par la sidebar pour afficher les entités disponibles.
    """
    company_id, plan = await _resolve_company(authorization)

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        result = (
            supabase.from_("entities")
            .select("id, name, industry, business_model, is_primary, relation_type, workspace_id, created_at")
            .eq("company_id", company_id)
            .order("is_primary", desc=True)
            .order("created_at", desc=False)
            .execute()
        )
        return {
            "success": True,
            "data": result.data or [],
            "plan": plan,
        }
    except Exception as e:
        logger.error(f"[ENTITIES] list error: {e}")
        return {"success": True, "data": [], "plan": plan}


class CreateEntityRequest(BaseModel):
    name: str
    industry: Optional[str] = None
    business_model: Optional[str] = None
    # "filiale" = filiale du groupe (l'analyse situe son poids/risque au niveau
    # de l'entité principale) ; "client" = client suivi par l'utilisateur
    # (l'analyse aide à évaluer la relation) ; None = non renseigné.
    relation_type: Optional[Literal["filiale", "client"]] = None


@router.post("")
async def create_entity(
    body: CreateEntityRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Crée une nouvelle entité dans le workspace par défaut.
    Requiert le plan POWER ou supérieur.
    """
    company_id, plan = await _resolve_company(authorization)

    # Plan gating — multi-entities requires PRO+
    PLAN_LEVEL = {"free": 0, "pro": 1, "power": 2, "scale": 3, "enterprise": 4}
    if PLAN_LEVEL.get(plan, 0) < PLAN_LEVEL["pro"]:
        raise HTTPException(
            status_code=403,
            detail="La gestion multi-entités est disponible à partir du plan PRO."
        )

    if not body.name or len(body.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Le nom de l'entité doit contenir au moins 2 caractères.")

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        # Get default workspace
        ws = (
            supabase.from_("workspaces")
            .select("id")
            .eq("company_id", company_id)
            .eq("is_default", True)
            .limit(1)
            .execute()
        )
        if not ws.data:
            raise HTTPException(status_code=404, detail="Workspace par défaut introuvable.")

        workspace_id = ws.data[0]["id"]

        result = (
            supabase.from_("entities")
            .insert({
                "workspace_id": workspace_id,
                "company_id": company_id,
                "name": body.name.strip(),
                "industry": body.industry,
                "business_model": body.business_model,
                "is_primary": False,
                "relation_type": body.relation_type,
            })
            .execute()
        )
        return {"success": True, "data": result.data[0] if result.data else {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENTITIES] create error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de l'entité.")
