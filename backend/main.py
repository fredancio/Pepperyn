"""
Pepperyn Backend — FastAPI main application v2.0
"""
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


# ── Supabase client factories ─────────────────────────────────

@lru_cache(maxsize=1)
def get_supabase_anon() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_supabase_service() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    env = os.getenv("ENVIRONMENT", "development")
    supabase_url = os.getenv("SUPABASE_URL", "not set")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    print(f"\n🚀 Pepperyn API v2.0 starting...")
    print(f"   Environment : {env}")
    print(f"   Supabase    : {supabase_url}")
    print(f"   Anthropic   : {'✓ configured' if anthropic_key else '✗ MISSING'}")
    print(f"   Max file    : {os.getenv('MAX_FILE_SIZE_MB', '5')}MB\n")

    yield

    print("\n👋 Pepperyn API stopping...\n")


# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="Pepperyn API",
    description="API backend pour Pepperyn — Assistant IA Financier B2B",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [o.strip() for o in cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────

from routers.auth import router as auth_router
from routers.analyze import router as analyze_router
from routers.feedback import router as feedback_router
from routers.webhooks import router as webhooks_router

app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(feedback_router)
app.include_router(webhooks_router)


# ── Admin endpoints ───────────────────────────────────────────

@app.post("/api/admin/update-pin")
async def update_pin(
    request: dict,
    authorization: Optional[str] = Header(default=None),
):
    """
    Update company PIN. Admin only.
    Invalidates all existing guest tokens (they reference pin_updated_at).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    new_pin = request.get("new_pin", "")
    if not new_pin or not new_pin.isdigit() or len(new_pin) != 4:
        raise HTTPException(status_code=400, detail="Le PIN doit contenir exactement 4 chiffres")

    token = authorization.split(" ", 1)[1]
    supabase = get_supabase_service()

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token admin invalide")

        # Use the stored procedure (validates ownership)
        result = supabase.rpc("update_company_pin", {"new_pin": new_pin}).execute()
        if not result.data:
            raise HTTPException(
                status_code=403,
                detail="Vous n'êtes pas administrateur d'une entreprise, ou le PIN est identique."
            )

        return {
            "success": True,
            "message": "PIN mis à jour avec succès. Les sessions invités actives sont révoquées."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/admin/company")
async def get_company_info(
    authorization: Optional[str] = Header(default=None),
):
    """Get company info for the authenticated admin."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    token = authorization.split(" ", 1)[1]
    supabase = get_supabase_service()

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token invalide")

        profile_response = (
            supabase.from_("profiles")
            .select("*, company:companies(*)")
            .eq("id", user_response.user.id)
            .single()
            .execute()
        )

        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        return {"success": True, "data": profile_response.data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/admin/analytics")
async def get_analytics(
    authorization: Optional[str] = Header(default=None),
):
    """Get usage analytics for the authenticated admin's company."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")

    token = authorization.split(" ", 1)[1]
    supabase = get_supabase_service()

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token invalide")

        # Get company_id
        profile = (
            supabase.from_("profiles")
            .select("company_id")
            .eq("id", user_response.user.id)
            .single()
            .execute()
        )
        if not profile.data:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        company_id = profile.data["company_id"]

        # Fetch usage logs for current month
        from datetime import datetime, timezone
        start_of_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        logs = (
            supabase.from_("usage_logs")
            .select("tokens_input, cout_estime_euros, duree_ms")
            .eq("company_id", company_id)
            .gte("created_at", start_of_month)
            .execute()
        )

        analyses_count = len(logs.data) if logs.data else 0
        total_cost = sum(r.get("cout_estime_euros", 0) or 0 for r in (logs.data or []))
        avg_duration = (
            sum(r.get("duree_ms", 0) or 0 for r in (logs.data or [])) / max(analyses_count, 1)
        )

        return {
            "success": True,
            "data": {
                "analyses_ce_mois": analyses_count,
                "cout_estime_euros": round(total_cost, 2),
                "duree_moyenne_ms": round(avg_duration),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ── Health / Root ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@app.get("/")
async def root():
    return {
        "message": "Pepperyn API v2.0 — Assistant IA Financier",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
