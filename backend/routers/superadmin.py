"""
routers/superadmin.py — Pepperyn
Dashboard CRM super-admin : liste toutes les companies, plans, usages.
Accessible uniquement à l'email défini dans SUPER_ADMIN_EMAIL.
"""
from __future__ import annotations

import logging
import os
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/superadmin", tags=["superadmin"])

SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "fredanciaux16@gmail.com")


async def _require_superadmin(authorization: Optional[str]) -> str:
    """Vérifie que le token appartient au super-admin. Retourne l'email."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    token = authorization.split(" ", 1)[1]

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        user_resp = supabase.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise HTTPException(status_code=401, detail="Token invalide")

        email = user_resp.user.email or ""
        if email.lower() != SUPER_ADMIN_EMAIL.lower():
            raise HTTPException(status_code=403, detail="Accès refusé")

        return email
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[SUPERADMIN AUTH] {e}")
        raise HTTPException(status_code=401, detail="Authentification échouée")


@router.get("/stats")
async def get_crm_stats(
    authorization: Optional[str] = Header(default=None),
):
    """
    Retourne toutes les companies avec :
    - nom, plan, date de création
    - email + prénom du profil admin
    - nb d'analyses total et ce mois-ci
    """
    await _require_superadmin(authorization)

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        # Toutes les companies
        companies_resp = (
            supabase.from_("companies")
            .select("id, name, plan, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        companies = companies_resp.data or []

        # Tous les profils (pour email + prénom)
        profiles_resp = (
            supabase.from_("profiles")
            .select("company_id, prenom, nom")
            .execute()
        )
        profiles = profiles_resp.data or []

        # Auth users pour les emails (via service role)
        try:
            users_resp = supabase.auth.admin.list_users()
            auth_users = {u.id: u.email for u in (users_resp or [])}
        except Exception:
            auth_users = {}

        # Profils indexés par company_id
        profile_by_company: dict = {}
        for p in profiles:
            cid = p.get("company_id")
            if cid and cid not in profile_by_company:
                profile_by_company[cid] = p

        # Analyses ce mois-ci
        start_of_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        analyses_month_resp = (
            supabase.from_("analyses")
            .select("company_id, created_at")
            .gte("created_at", start_of_month)
            .eq("status", "completed")
            .execute()
        )
        analyses_month = analyses_month_resp.data or []

        # Analyses totales par company
        analyses_total_resp = (
            supabase.from_("analyses")
            .select("company_id")
            .eq("status", "completed")
            .execute()
        )
        analyses_total = analyses_total_resp.data or []

        # Comptages
        month_counts: dict = {}
        for a in analyses_month:
            cid = a.get("company_id")
            if cid:
                month_counts[cid] = month_counts.get(cid, 0) + 1

        total_counts: dict = {}
        for a in analyses_total:
            cid = a.get("company_id")
            if cid:
                total_counts[cid] = total_counts.get(cid, 0) + 1

        # Assemblage
        result = []
        for company in companies:
            cid = company["id"]
            profile = profile_by_company.get(cid, {})

            # Trouver l'email via auth users
            email = ""
            for uid, uemail in auth_users.items():
                # On cherche le profil qui correspond
                pass

            # Profils avec id pour matcher auth
            profile_with_id_resp = (
                supabase.from_("profiles")
                .select("id, prenom, nom")
                .eq("company_id", cid)
                .limit(1)
                .execute()
            )
            profile_data = profile_with_id_resp.data[0] if profile_with_id_resp.data else {}
            user_id = profile_data.get("id", "")
            email = auth_users.get(user_id, "")
            prenom = profile_data.get("prenom", "")
            nom = profile_data.get("nom", "")

            result.append({
                "company_id": cid,
                "company_name": company.get("name", ""),
                "plan": company.get("plan", "free"),
                "created_at": company.get("created_at", ""),
                "email": email,
                "contact_name": f"{prenom} {nom}".strip(),
                "analyses_this_month": month_counts.get(cid, 0),
                "analyses_total": total_counts.get(cid, 0),
            })

        return {
            "success": True,
            "data": result,
            "summary": {
                "total_companies": len(result),
                "by_plan": {
                    plan: sum(1 for c in result if c["plan"] == plan)
                    for plan in ["free", "pro", "power", "scale", "enterprise"]
                },
                "total_analyses_this_month": sum(month_counts.values()),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SUPERADMIN] stats error: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur.")
