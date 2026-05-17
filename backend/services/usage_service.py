"""
Usage Service — Pepperyn V11.

Gère les limites d'usage, le reset mensuel automatique et le tracking chat.
Toute logique de limite est ici — AUCUNE logique côté frontend.

Plans V11 (source : master plan Final) :
  FREE       → 1 analyse/mois   · 3 interactions contextuelles/analyse
  PRO        → 15 analyses/mois · usage conversationnel étendu (soft cap Sonnet)
  POWER      → 75 analyses/mois · usage avancé inclus
  SCALE      → 250 analyses/mois· usage intensif inclus
  ENTERPRISE → illimité

Add-ons (crédits supplémentaires, achetables via Stripe) :
  Starter Pack : +10 analyses  → 19€
  Growth Pack  : +50 analyses  → 69€
  Scale Pack   : +200 analyses → 199€

Tables Supabase requises :
  usage_limits :
    company_id      UUID    NOT NULL
    year_month      TEXT    NOT NULL  -- ex: "2026-04"
    analyses_count  INT     DEFAULT 0
    chat_count      INT     DEFAULT 0
    bonus_analyses  INT     DEFAULT 0  -- crédits achetés en add-on
    PRIMARY KEY (company_id, year_month)

  user_activity :
    id           UUID    DEFAULT gen_random_uuid() PRIMARY KEY
    company_id   UUID    NOT NULL
    event_type   TEXT    NOT NULL
    metadata     JSONB   DEFAULT '{}'
    created_at   TIMESTAMPTZ DEFAULT now()
"""
from datetime import datetime, timezone
from typing import Optional, Tuple


# ─── Plan limits V11 ─────────────────────────────────────────────────────────

PLAN_LIMITS: dict[str, dict] = {
    # V11 plans
    "free":           {"analyses": 1,    "chat_per_analysis": 3,    "chat_soft_cap": None},
    "pro":            {"analyses": 15,   "chat_per_analysis": None,  "chat_soft_cap": 500},
    "power":          {"analyses": 75,   "chat_per_analysis": None,  "chat_soft_cap": 2000},
    "scale":          {"analyses": 250,  "chat_per_analysis": None,  "chat_soft_cap": None},
    "enterprise":     {"analyses": None, "chat_per_analysis": None,  "chat_soft_cap": None},
    # Legacy plan names (kept for backward compat)
    "premium":        {"analyses": 75,   "chat_per_analysis": None,  "chat_soft_cap": 2000},
    "standard":       {"analyses": 15,   "chat_per_analysis": None,  "chat_soft_cap": 500},
    "standard_beta":  {"analyses": 15,   "chat_per_analysis": None,  "chat_soft_cap": 500},
}

# Add-on packs (prêts à brancher sur Stripe)
ADDON_PACKS: dict[str, dict] = {
    "starter": {"analyses": 10,  "price_eur": 19,  "label": "Starter Pack"},
    "growth":  {"analyses": 50,  "price_eur": 69,  "label": "Growth Pack"},
    "scale":   {"analyses": 200, "price_eur": 199, "label": "Scale Pack"},
}


def _current_year_month() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


class UsageService:

    def __init__(self):
        self._supabase = None

    def _get_supabase(self):
        if self._supabase is None:
            try:
                from main import get_supabase_service
                self._supabase = get_supabase_service()
            except Exception:
                pass
        return self._supabase

    # ─── Usage row ───────────────────────────────────────────────────────────

    def _get_or_create_usage_row(self, company_id: str) -> dict:
        """Get or create usage row for current month (auto-reset)."""
        sb = self._get_supabase()
        if not sb:
            return {"analyses_count": 0, "chat_count": 0}

        year_month = _current_year_month()
        try:
            result = (
                sb.from_("usage_limits")
                .select("*")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            if result.data:
                return result.data[0]

            # New month → insert fresh row (automatic monthly reset)
            sb.from_("usage_limits").insert({
                "company_id": company_id,
                "year_month": year_month,
                "analyses_count": 0,
                "chat_count": 0,
            }).execute()
            return {"analyses_count": 0, "chat_count": 0}

        except Exception:
            return {"analyses_count": 0, "chat_count": 0}

    # ─── Analysis limits ─────────────────────────────────────────────────────

    def can_run_analysis(self, company_id: str, plan: str) -> Tuple[bool, str]:
        """
        Check if company can run an analysis this month.
        Returns (allowed: bool, reason: str).
        MUST be called before every analysis — never skipped.
        Bonus analyses (add-on packs) count toward the total available.
        """
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        max_analyses = limits["analyses"]

        if max_analyses is None:
            return True, ""

        usage = self._get_or_create_usage_row(company_id)
        current = usage.get("analyses_count", 0)
        bonus = usage.get("bonus_analyses", 0)
        total_allowed = max_analyses + bonus

        if current >= total_allowed:
            if bonus > 0:
                return False, (
                    f"Limite de {max_analyses} analyses/mois + {bonus} crédits bonus épuisée. "
                    "Achetez un pack de crédits supplémentaires ou passez au plan supérieur."
                )
            return False, (
                f"Limite de {max_analyses} analyse{'s' if max_analyses > 1 else ''}/mois atteinte (plan {plan.upper()}). "
                "Achetez des crédits supplémentaires ou passez au plan supérieur."
            )
        return True, ""

    def get_usage_this_month(self, company_id: str, plan: str) -> dict:
        """
        Return usage summary for the current month.
        Used by frontend to display quota progress.
        """
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        max_analyses = limits["analyses"]
        usage = self._get_or_create_usage_row(company_id)
        used = usage.get("analyses_count", 0)
        bonus = usage.get("bonus_analyses", 0)
        total_allowed = (max_analyses + bonus) if max_analyses is not None else None

        return {
            "plan": plan,
            "analyses_used": used,
            "analyses_limit": max_analyses,
            "bonus_analyses": bonus,
            "total_allowed": total_allowed,
            "analyses_remaining": max(0, total_allowed - used) if total_allowed is not None else None,
            "year_month": _current_year_month(),
        }

    def add_bonus_analyses(self, company_id: str, quantity: int) -> None:
        """
        Add bonus analyses to the current month (called after Stripe payment webhook).
        Thread-safe using Supabase atomic update.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            # Ensure row exists
            usage = self._get_or_create_usage_row(company_id)
            current_bonus = usage.get("bonus_analyses", 0)
            sb.from_("usage_limits").update({
                "bonus_analyses": current_bonus + quantity
            }).eq("company_id", company_id).eq("year_month", year_month).execute()
        except Exception:
            pass

    def increment_analysis(self, company_id: str) -> None:
        """
        Increment analysis count AFTER successful analysis.
        Uses upsert to handle race conditions.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            # Ensure row exists first
            self._get_or_create_usage_row(company_id)

            result = (
                sb.from_("usage_limits")
                .select("analyses_count")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            current = (result.data[0].get("analyses_count", 0) if result.data else 0)

            sb.from_("usage_limits").update({
                "analyses_count": current + 1
            }).eq("company_id", company_id).eq("year_month", year_month).execute()

        except Exception:
            pass

    # ─── Chat limits ─────────────────────────────────────────────────────────

    def get_analysis_chat_count(self, analysis_id: str) -> int:
        """Get chat message count for a specific analysis."""
        sb = self._get_supabase()
        if not sb:
            return 0
        try:
            result = (
                sb.from_("analyses")
                .select("chat_count")
                .eq("id", analysis_id)
                .execute()
            )
            return (result.data[0] if result.data else {}).get("chat_count", 0) or 0
        except Exception:
            return 0

    def can_chat(
        self,
        company_id: str,
        analysis_id: Optional[str],
        plan: str,
    ) -> Tuple[bool, str, str]:
        """
        Check if company can send a chat message.
        Returns (allowed: bool, reason: str, model_tier: str)
        model_tier: 'normal' | 'downgraded' (PRO soft cap → Sonnet)
        MUST be called before every chat message.
        """
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        # Per-analysis limit (FREE plan)
        if limits["chat_per_analysis"] is not None and analysis_id:
            current = self.get_analysis_chat_count(analysis_id)
            if current >= limits["chat_per_analysis"]:
                return (
                    False,
                    f"Limite de {limits['chat_per_analysis']} messages par analyse atteinte. "
                    "Démarrez une nouvelle analyse ou passez au plan supérieur.",
                    "normal",
                )

        # Soft cap check (PRO → downgrade to Sonnet, not block)
        if limits["chat_soft_cap"] is not None and analysis_id:
            current = self.get_analysis_chat_count(analysis_id)
            if current >= limits["chat_soft_cap"]:
                return True, "", "downgraded"

        return True, "", "normal"

    def increment_chat(self, analysis_id: Optional[str]) -> None:
        """Increment chat count for a specific analysis AFTER message sent."""
        if not analysis_id:
            return
        sb = self._get_supabase()
        if not sb:
            return
        try:
            result = (
                sb.from_("analyses")
                .select("chat_count")
                .eq("id", analysis_id)
                .execute()
            )
            current = (result.data[0] if result.data else {}).get("chat_count", 0) or 0
            sb.from_("analyses").update({
                "chat_count": current + 1
            }).eq("id", analysis_id).execute()
        except Exception:
            pass

    # ─── Activity tracking ────────────────────────────────────────────────────

    def track_activity(
        self,
        company_id: str,
        event_type: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Log a user activity event to user_activity table.
        Events: file_uploaded | analysis_started | chat_message | export_generated
        Non-blocking — errors silently ignored.
        """
        sb = self._get_supabase()
        if not sb:
            return
        try:
            sb.from_("user_activity").insert({
                "company_id": company_id,
                "event_type": event_type,
                "metadata": metadata or {},
            }).execute()
        except Exception:
            pass
