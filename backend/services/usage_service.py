"""
Usage Service — Pepperyn Release 1.0  (WP1C)

Moteur de quotas et de suivi d'usage.

Source des quotas : config/product_catalog.py (PLAN_LIMITS, get_plan).
Aucune constante métier locale.

═══════════════════════════════════════════════════════════════════════════════
RÈGLES CONTRACTUELLES
═══════════════════════════════════════════════════════════════════════════════
Interactions :
  Le quota est UNIQUEMENT mensuel (PlanLimits.chat_monthly_cap).
  Il n'existe aucune limite d'Interactions par Analyse.
  L'utilisateur répartit ses Interactions librement entre ses Analyses.

Ordre de consommation des Analyses :
  1. Analyses bonus (Executive Capacity Packs) — bonus_analyses en DB — EN PREMIER.
  2. Quota mensuel du Plan — analyses_count en DB — ensuite.
  Reset mensuel : analyses_count → 0. bonus_analyses INCHANGÉ.
  Les Analyses bonus non consommées persistent indéfiniment.

═══════════════════════════════════════════════════════════════════════════════
TABLES SUPABASE
═══════════════════════════════════════════════════════════════════════════════
  usage_limits :
    company_id      UUID    NOT NULL
    year_month      TEXT    NOT NULL  -- ex: "2026-07"
    analyses_count  INT     DEFAULT 0
    chat_count      INT     DEFAULT 0
    bonus_analyses  INT     DEFAULT 0  -- Analyses bonus Executive Capacity Packs
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

from config.product_catalog import PLAN_LIMITS, get_plan  # source unique des quotas


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

    # ─── Ligne d'usage ───────────────────────────────────────────────────────

    def _get_or_create_usage_row(self, company_id: str) -> dict:
        """Récupère ou crée la ligne d'usage du mois courant (reset mensuel automatique)."""
        sb = self._get_supabase()
        if not sb:
            return {"analyses_count": 0, "chat_count": 0, "bonus_analyses": 0}

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

            # Nouveau mois → insertion d'une ligne vierge (reset mensuel automatique)
            sb.from_("usage_limits").insert({
                "company_id": company_id,
                "year_month": year_month,
                "analyses_count": 0,
                "chat_count": 0,
            }).execute()
            return {"analyses_count": 0, "chat_count": 0, "bonus_analyses": 0}

        except Exception:
            return {"analyses_count": 0, "chat_count": 0, "bonus_analyses": 0}

    # ─── Analyses ────────────────────────────────────────────────────────────

    def can_run_analysis(self, company_id: str, plan: str) -> Tuple[bool, str]:
        """
        Vérifie si la company peut lancer une Analyse ce mois.

        Ordre de consommation :
          1. Analyses bonus (Executive Capacity Packs) — en premier.
          2. Quota mensuel du Plan — ensuite.

        Returns (allowed: bool, reason: str).
        DOIT être appelé avant chaque Analyse — jamais contourné.
        """
        try:
            limits = get_plan(plan)
        except KeyError:
            limits = get_plan("free")

        max_analyses = limits.analyses

        # Plan illimité (Enterprise)
        if max_analyses is None:
            return True, ""

        usage = self._get_or_create_usage_row(company_id)
        analyses_used = usage.get("analyses_count", 0) or 0
        bonus = usage.get("bonus_analyses", 0) or 0
        total_allowed = max_analyses + bonus

        if analyses_used >= total_allowed:
            if bonus > 0:
                return False, (
                    f"Quota de {max_analyses} Analyses/mois + {bonus} Analyses bonus épuisé "
                    f"(Plan {plan.upper()}). "
                    "Achetez un Executive Capacity Pack ou passez au plan supérieur."
                )
            return False, (
                f"Quota de {max_analyses} Analyse{'s' if max_analyses > 1 else ''}/mois épuisé "
                f"(Plan {plan.upper()}). "
                "Achetez un Executive Capacity Pack ou passez au plan supérieur."
            )
        return True, ""

    def get_usage_this_month(self, company_id: str, plan: str) -> dict:
        """
        Résumé d'usage du mois en cours.

        Calcule l'ordre de consommation (bonus en premier, mensuel ensuite)
        et prépare les champs nécessaires à WP1D (dashboard frontend).

        Retourne un dict avec :
          - analyses : consommation mensuelle, bonus, total disponible
          - interactions : quota mensuel global
          - entités : limite du Plan
          - renouvellement : date du prochain reset mensuel
        """
        try:
            limits = get_plan(plan)
        except KeyError:
            limits = get_plan("free")

        max_analyses = limits.analyses
        max_interactions = limits.chat_monthly_cap
        max_entities = limits.max_entities

        usage = self._get_or_create_usage_row(company_id)
        analyses_used = usage.get("analyses_count", 0) or 0
        interactions_used = usage.get("chat_count", 0) or 0
        bonus = usage.get("bonus_analyses", 0) or 0

        # Ordre de consommation : bonus en premier, quota mensuel ensuite.
        # analyses_count monte linéairement — les premières consomment le bonus,
        # les suivantes le quota mensuel.
        bonus_used = min(analyses_used, bonus)
        monthly_used = max(0, analyses_used - bonus)
        bonus_remaining = max(0, bonus - analyses_used)

        total_allowed = (max_analyses + bonus) if max_analyses is not None else None
        analyses_remaining = (
            max(0, total_allowed - analyses_used) if total_allowed is not None else None
        )
        monthly_remaining = max(0, max_analyses - monthly_used) if max_analyses is not None else None
        interactions_remaining = (
            max(0, max_interactions - interactions_used)
            if max_interactions is not None else None
        )

        # Date du prochain renouvellement mensuel (1er du mois suivant, UTC)
        now = datetime.now(timezone.utc)
        if now.month == 12:
            renewal = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            renewal = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)

        return {
            "plan": plan,
            "year_month": _current_year_month(),
            # ── Analyses ──────────────────────────────────────────────────────
            "analyses_used":              analyses_used,
            "analyses_limit":             max_analyses,        # quota mensuel du Plan
            "analyses_bonus":             bonus,               # total bonus disponible
            "analyses_bonus_used":        bonus_used,          # bonus déjà consommés
            "analyses_bonus_remaining":   bonus_remaining,     # bonus encore disponibles
            "analyses_monthly_used":      monthly_used,        # quota mensuel consommé
            "analyses_monthly_remaining": monthly_remaining,   # quota mensuel restant
            "analyses_total_allowed":     total_allowed,       # quota + bonus
            "analyses_remaining":         analyses_remaining,  # total restant
            # ── Aliases compat legacy (billing.py GET /usage) ─────────────────
            "bonus_analyses":             bonus,
            "total_allowed":              total_allowed,
            # ── Interactions ──────────────────────────────────────────────────
            "interactions_used":          interactions_used,
            "interactions_limit":         max_interactions,
            "interactions_remaining":     interactions_remaining,
            # ── Entités ───────────────────────────────────────────────────────
            "max_entities":               max_entities,
            # ── Renouvellement ────────────────────────────────────────────────
            "renewal_date":               renewal.isoformat(),
        }

    def add_bonus_analyses(self, company_id: str, quantity: int) -> None:
        """
        Ajoute des Analyses bonus au mois courant.

        Note : billing.py utilise désormais la RPC apply_stripe_webhook (WP1B.3)
        qui est atomique. Cette méthode est conservée pour la compatibilité des
        appels existants non encore migrés.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            usage = self._get_or_create_usage_row(company_id)
            current_bonus = usage.get("bonus_analyses", 0) or 0
            sb.from_("usage_limits").update({
                "bonus_analyses": current_bonus + quantity
            }).eq("company_id", company_id).eq("year_month", year_month).execute()
        except Exception:
            pass

    def increment_analysis(self, company_id: str) -> None:
        """
        Incrémente analyses_count après une Analyse réussie.

        Appelé par analyze.py après chaque Analyse complétée avec succès.
        L'ordre de consommation (bonus en premier) est implicite : analyses_count
        étant incrémenté linéairement, les premières analyses consomment le bonus,
        les suivantes le quota mensuel du Plan.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            self._get_or_create_usage_row(company_id)

            result = (
                sb.from_("usage_limits")
                .select("analyses_count")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            current = (result.data[0].get("analyses_count", 0) if result.data else 0) or 0

            sb.from_("usage_limits").update({
                "analyses_count": current + 1
            }).eq("company_id", company_id).eq("year_month", year_month).execute()

        except Exception:
            pass

    # ─── Interactions ─────────────────────────────────────────────────────────
    #
    # Une Interaction = un message chat envoyé par l'utilisateur.
    # Le quota est mensuel et global. Aucune limite par Analyse.
    # L'utilisateur répartit ses Interactions librement entre ses Analyses.

    def get_monthly_chat_count(self, company_id: str) -> int:
        """Retourne le nombre d'Interactions envoyées ce mois pour une company."""
        sb = self._get_supabase()
        if not sb:
            return 0
        year_month = _current_year_month()
        try:
            result = (
                sb.from_("usage_limits")
                .select("chat_count")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            return (result.data[0].get("chat_count", 0) if result.data else 0) or 0
        except Exception:
            return 0

    def can_chat(
        self,
        company_id: str,
        analysis_id: Optional[str],
        plan: str,
    ) -> Tuple[bool, str, str]:
        """
        Vérifie si la company peut envoyer une Interaction (message chat).

        Une Interaction est une ressource mensuelle globale.
        Seul le quota mensuel du Plan (PlanLimits.chat_monthly_cap) s'applique.
        Il n'existe aucune limite d'Interactions par Analyse.

        Returns (allowed: bool, reason: str, model_tier: str).
        model_tier est toujours 'normal' — conservé pour compatibilité avec analyze.py.
        """
        try:
            limits = get_plan(plan)
        except KeyError:
            limits = get_plan("free")

        monthly_cap = limits.chat_monthly_cap
        if monthly_cap is not None:
            monthly_count = self.get_monthly_chat_count(company_id)
            if monthly_count >= monthly_cap:
                return (
                    False,
                    f"Quota mensuel de {monthly_cap} Interactions épuisé "
                    f"(Plan {plan.upper()}). "
                    "Passez au plan supérieur pour continuer ce mois.",
                    "normal",
                )

        return True, "", "normal"

    def increment_chat(self, analysis_id: Optional[str], company_id: Optional[str] = None) -> None:
        """
        Incrémente le compteur d'Interactions après un message.

        Met à jour usage_limits.chat_count (quota mensuel global).
        Appelé par analyze.py après chaque Interaction complétée avec succès.
        """
        sb = self._get_supabase()
        if not sb:
            return

        # Compteur mensuel global (quota Interactions du Plan)
        if company_id:
            year_month = _current_year_month()
            try:
                self._get_or_create_usage_row(company_id)
                result = (
                    sb.from_("usage_limits")
                    .select("chat_count")
                    .eq("company_id", company_id)
                    .eq("year_month", year_month)
                    .execute()
                )
                current = (result.data[0].get("chat_count", 0) if result.data else 0) or 0
                sb.from_("usage_limits").update({
                    "chat_count": current + 1
                }).eq("company_id", company_id).eq("year_month", year_month).execute()
            except Exception:
                pass

    # ─── Tracking activité ────────────────────────────────────────────────────

    def track_activity(
        self,
        company_id: str,
        event_type: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Enregistre un événement d'activité dans user_activity.
        Événements : file_uploaded | analysis_started | chat_message | export_generated
        Non-bloquant — erreurs ignorées silencieusement.
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
