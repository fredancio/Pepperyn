"""
routers/superadmin.py — Pepperyn
Dashboard CRM super-admin : liste toutes les companies, plans, usages.
Accessible uniquement à l'email défini dans SUPER_ADMIN_EMAIL.

Endpoints :
  GET /api/superadmin/stats   → CRM (liste companies + usages)
  GET /api/superadmin/growth  → Dashboard Growth (acquisition, MRR, activation)
"""
from __future__ import annotations

import logging
import os
from typing import Optional
from datetime import datetime, timezone, timedelta

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


# ─── Tarification (€/mois) ────────────────────────────────────────────────────
_PLAN_MRR: dict[str, int] = {
    "free":       0,
    "pro":       59,
    "power":    129,
    "scale":    349,
    "enterprise": 999,  # estimé
}


def _iso_week_label(dt: datetime) -> str:
    """Retourne 'YYYY-Www' pour grouper par semaine ISO."""
    return dt.strftime("%G-W%V")


def _week_label_short(iso_week: str) -> str:
    """'2026-W28' → 'S28'."""
    return "S" + iso_week.split("-W")[1]


@router.get("/growth")
async def get_growth_dashboard(
    authorization: Optional[str] = Header(default=None),
):
    """
    Dashboard Growth — lecture seule, super-admin uniquement.

    Retourne :
      - kpis         : MRR, nouveaux ce mois, taux d'activation, analyses ce mois
      - weekly_signups  : acquisitions par semaine (12 dernières semaines)
      - weekly_analyses : analyses par semaine   (12 dernières semaines)
      - plan_funnel  : distribution des plans + MRR contributif
      - top_companies : top 10 par nb d'analyses total (pour identifier les power users)
    """
    await _require_superadmin(authorization)

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        now = datetime.now(timezone.utc)
        twelve_weeks_ago = (now - timedelta(weeks=12)).isoformat()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        # ── 1. Toutes les companies ───────────────────────────────────────────
        companies_resp = (
            supabase.from_("companies")
            .select("id, plan, created_at")
            .execute()
        )
        companies = companies_resp.data or []

        # ── 2. Analyses totales (pour activation + top companies) ────────────
        all_analyses_resp = (
            supabase.from_("analyses")
            .select("company_id, created_at")
            .eq("status", "completed")
            .execute()
        )
        all_analyses = all_analyses_resp.data or []

        # ── 3. Analyses ce mois (pour KPI mensuel) ───────────────────────────
        month_analyses_resp = (
            supabase.from_("analyses")
            .select("company_id")
            .eq("status", "completed")
            .gte("created_at", start_of_month)
            .execute()
        )
        month_analyses = month_analyses_resp.data or []

        # ── 4. Séries temporelles — 12 dernières semaines ────────────────────
        recent_companies_resp = (
            supabase.from_("companies")
            .select("created_at")
            .gte("created_at", twelve_weeks_ago)
            .execute()
        )
        recent_companies = recent_companies_resp.data or []

        recent_analyses_resp = (
            supabase.from_("analyses")
            .select("created_at")
            .eq("status", "completed")
            .gte("created_at", twelve_weeks_ago)
            .execute()
        )
        recent_analyses = recent_analyses_resp.data or []

        # ── 5. Construire les 12 semaines (même sans données) ────────────────
        weeks: list[str] = []
        for i in range(11, -1, -1):
            week_start = now - timedelta(weeks=i)
            weeks.append(_iso_week_label(week_start))

        signup_by_week: dict[str, int] = {w: 0 for w in weeks}
        for c in recent_companies:
            dt_str = c.get("created_at", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    wk = _iso_week_label(dt)
                    if wk in signup_by_week:
                        signup_by_week[wk] += 1
                except Exception:
                    pass

        analysis_by_week: dict[str, int] = {w: 0 for w in weeks}
        for a in recent_analyses:
            dt_str = a.get("created_at", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    wk = _iso_week_label(dt)
                    if wk in analysis_by_week:
                        analysis_by_week[wk] += 1
                except Exception:
                    pass

        weekly_signups = [
            {"week": w, "label": _week_label_short(w), "count": signup_by_week[w]}
            for w in weeks
        ]
        weekly_analyses = [
            {"week": w, "label": _week_label_short(w), "count": analysis_by_week[w]}
            for w in weeks
        ]

        # ── 6. Plan funnel + MRR ─────────────────────────────────────────────
        plan_counts: dict[str, int] = {}
        for c in companies:
            p = c.get("plan", "free")
            plan_counts[p] = plan_counts.get(p, 0) + 1

        plan_funnel = [
            {
                "plan": plan,
                "count": plan_counts.get(plan, 0),
                "mrr": (plan_counts.get(plan, 0)) * _PLAN_MRR.get(plan, 0),
            }
            for plan in ["enterprise", "scale", "power", "pro", "free"]
        ]
        total_mrr = sum(p["mrr"] for p in plan_funnel)

        # ── 7. Activation rate ───────────────────────────────────────────────
        companies_with_analyses: set[str] = {
            a["company_id"] for a in all_analyses if a.get("company_id")
        }
        total_companies = len(companies)
        activation_rate = (
            round(len(companies_with_analyses) / total_companies * 100)
            if total_companies > 0 else 0
        )

        # ── 8. Top 10 companies par analyses totales ─────────────────────────
        analysis_count_by_company: dict[str, int] = {}
        for a in all_analyses:
            cid = a.get("company_id")
            if cid:
                analysis_count_by_company[cid] = analysis_count_by_company.get(cid, 0) + 1

        # Enrichir avec les infos de la company
        company_by_id = {c["id"]: c for c in companies}
        top_companies_raw = sorted(
            analysis_count_by_company.items(), key=lambda x: x[1], reverse=True
        )[:10]

        top_companies = [
            {
                "company_id": cid,
                "plan": company_by_id.get(cid, {}).get("plan", "free"),
                "analyses_total": count,
            }
            for cid, count in top_companies_raw
        ]

        # ── 9. KPIs sommaires ────────────────────────────────────────────────
        new_this_month = sum(
            1 for c in companies
            if (c.get("created_at") or "") >= start_of_month
        )

        return {
            "success": True,
            "kpis": {
                "mrr_estimate":          total_mrr,
                "total_companies":       total_companies,
                "new_companies_month":   new_this_month,
                "activation_rate":       activation_rate,
                "analyses_this_month":   len(month_analyses),
                "paying_companies":      sum(
                    plan_counts.get(p, 0)
                    for p in ["pro", "power", "scale", "enterprise"]
                ),
            },
            "weekly_signups":  weekly_signups,
            "weekly_analyses": weekly_analyses,
            "plan_funnel":     plan_funnel,
            "top_companies":   top_companies,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SUPERADMIN] growth error: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur.")
