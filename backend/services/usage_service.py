"""
Usage Service — Pepperyn Release 1.0  (WP1C.2 — Option B)

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

Executive Capacity Packs — Option B :
  Le stock bonus est une PROPRIÉTÉ PERMANENTE DU COMPTE.
  Stocké dans companies.bonus_analyses_remaining.
  Jamais remis à zéro. Jamais lié à un mois.
  Consommé EN PREMIER (avant le quota mensuel du plan).
  Plans éligibles à la consommation : _BONUS_ELIGIBLE_PLANS.
  Plan FREE : stock conservé mais SUSPENDU (non consommable).
              Réactivé automatiquement au passage PRO / SCALE.

Ordre de consommation des Analyses :
  1. Stock bonus permanent (companies.bonus_analyses_remaining) — EN PREMIER,
     si le plan est éligible.
  2. Quota mensuel du Plan (usage_limits.analyses_count) — ensuite.
  Reset mensuel : analyses_count → 0. bonus_analyses_remaining INCHANGÉ.

Atomicité :
  Décrémentation bonus : UPDATE … WHERE bonus_analyses_remaining = N
                         (verrou optimiste — retry x3 sur conflit concurrent)
  Incrémentation mensuelle : UPDATE … WHERE analyses_count = M
                              (verrou optimiste — retry x3 sur conflit concurrent)

═══════════════════════════════════════════════════════════════════════════════
TABLES SUPABASE
═══════════════════════════════════════════════════════════════════════════════
  companies :
    id                       UUID    PRIMARY KEY
    plan                     TEXT    -- plan actuel
    bonus_analyses_remaining INT     DEFAULT 0  -- stock permanent Executive Capacity Packs
    (+ autres colonnes non lues ici)

  usage_limits :
    company_id      UUID    NOT NULL
    year_month      TEXT    NOT NULL  -- ex: "2026-07"
    analyses_count  INT     DEFAULT 0  -- quota mensuel consommé
    chat_count      INT     DEFAULT 0  -- interactions mensuelles consommées
    bonus_analyses  INT     DEFAULT 0  -- VESTIGE Option A : non lu, non écrit par ce service
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

# Plans autorisés à consommer le stock bonus Executive Capacity Packs.
# FREE est exclu : le stock est conservé mais suspendu.
_BONUS_ELIGIBLE_PLANS: frozenset = frozenset({
    "pro", "scale", "enterprise",
    "standard", "standard_beta", "premium",  # alias legacy
})

_OPTIMISTIC_RETRIES = 3  # tentatives max pour les verrous optimistes


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

    # ─── Stock bonus permanent (companies) ────────────────────────────────────

    def _get_bonus_remaining(self, company_id: str) -> int:
        """
        Lit companies.bonus_analyses_remaining — stock permanent.
        Retourne 0 si la ligne est absente ou la colonne NULL.
        """
        sb = self._get_supabase()
        if not sb:
            return 0
        try:
            result = (
                sb.from_("companies")
                .select("bonus_analyses_remaining")
                .eq("id", company_id)
                .execute()
            )
            return (result.data[0].get("bonus_analyses_remaining", 0) if result.data else 0) or 0
        except Exception:
            return 0

    def _decrement_bonus(self, company_id: str) -> bool:
        """
        Décrémente companies.bonus_analyses_remaining de 1.

        Verrou optimiste : READ → UPDATE WHERE bonus_analyses_remaining = N.
        Retourne True si la décrémentation a réussi, False si concurrent conflict.
        """
        sb = self._get_supabase()
        if not sb:
            return False
        try:
            result = (
                sb.from_("companies")
                .select("bonus_analyses_remaining")
                .eq("id", company_id)
                .execute()
            )
            current = (result.data[0].get("bonus_analyses_remaining", 0) if result.data else 0) or 0
            if current <= 0:
                return False

            updated = (
                sb.from_("companies")
                .update({"bonus_analyses_remaining": current - 1})
                .eq("id", company_id)
                .eq("bonus_analyses_remaining", current)   # verrou optimiste
                .execute()
            )
            # PostgreSQL retourne la liste des lignes mises à jour.
            # Si 0 lignes → conflit concurrent (quelqu'un a décrémenté entre-temps).
            return bool(updated.data)
        except Exception:
            return False

    # ─── Ligne d'usage mensuel (usage_limits) ─────────────────────────────────

    def _get_or_create_usage_row(self, company_id: str) -> dict:
        """
        Récupère ou crée la ligne d'usage du mois courant.

        Option B : insertion simplifiée — pas de carry-forward, pas de bonus_analyses.
        Le reset mensuel est automatique : chaque nouveau mois crée une ligne vierge.
        """
        sb = self._get_supabase()
        if not sb:
            return {"analyses_count": 0, "chat_count": 0}

        year_month = _current_year_month()
        try:
            result = (
                sb.from_("usage_limits")
                .select("analyses_count, chat_count")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            if result.data:
                return result.data[0]

            # Nouveau mois → ligne vierge (reset mensuel automatique).
            sb.from_("usage_limits").insert({
                "company_id": company_id,
                "year_month": year_month,
                "analyses_count": 0,
                "chat_count": 0,
            }).execute()
            return {"analyses_count": 0, "chat_count": 0}

        except Exception:
            return {"analyses_count": 0, "chat_count": 0}

    def _increment_monthly_count(self, company_id: str, year_month: str) -> None:
        """
        Incrémente usage_limits.analyses_count de 1 avec verrou optimiste.

        READ → UPDATE WHERE analyses_count = current.
        Retry jusqu'à _OPTIMISTIC_RETRIES fois en cas de conflit concurrent.
        """
        sb = self._get_supabase()
        if not sb:
            return

        for _ in range(_OPTIMISTIC_RETRIES):
            try:
                result = (
                    sb.from_("usage_limits")
                    .select("analyses_count")
                    .eq("company_id", company_id)
                    .eq("year_month", year_month)
                    .execute()
                )
                current = (result.data[0].get("analyses_count", 0) if result.data else 0) or 0

                updated = (
                    sb.from_("usage_limits")
                    .update({"analyses_count": current + 1})
                    .eq("company_id", company_id)
                    .eq("year_month", year_month)
                    .eq("analyses_count", current)   # verrou optimiste
                    .execute()
                )
                if updated.data:
                    return   # succès
                # Sinon : conflit — retry
            except Exception:
                return

    # ─── Analyses ────────────────────────────────────────────────────────────

    def can_run_analysis(self, company_id: str, plan: str) -> Tuple[bool, str]:
        """
        Vérifie si la company peut lancer une Analyse.

        Ordre de consommation :
          1. Stock bonus permanent (companies.bonus_analyses_remaining) — en premier,
             si le plan est dans _BONUS_ELIGIBLE_PLANS.
          2. Quota mensuel du Plan (usage_limits.analyses_count) — ensuite.

        Plan FREE avec bonus suspendu → message spécifique indiquant la suspension.

        Returns (allowed: bool, reason: str).
        DOIT être appelé avant chaque Analyse — jamais contourné.
        """
        try:
            limits = get_plan(plan)
        except KeyError:
            limits = get_plan("free")

        max_analyses = limits.analyses

        # Enterprise → illimité
        if max_analyses is None:
            return True, ""

        plan_key = plan.lower()

        # Plans éligibles : vérifier le stock bonus permanent en premier
        if plan_key in _BONUS_ELIGIBLE_PLANS:
            bonus = self._get_bonus_remaining(company_id)
            if bonus > 0:
                return True, ""

        # Plan FREE avec bonus suspendu
        if plan_key not in _BONUS_ELIGIBLE_PLANS:
            bonus = self._get_bonus_remaining(company_id)
            if bonus > 0:
                return False, (
                    f"Quota de {max_analyses} Analyse{'s' if max_analyses > 1 else ''}/mois épuisé "
                    f"(Plan {plan.upper()}). "
                    f"Vous disposez de {bonus} Analyse{'s' if bonus > 1 else ''} bonus suspendues — "
                    "passez en PRO ou SCALE pour les utiliser."
                )

        # Quota mensuel
        usage = self._get_or_create_usage_row(company_id)
        analyses_count = usage.get("analyses_count", 0) or 0

        if analyses_count >= max_analyses:
            return False, (
                f"Quota de {max_analyses} Analyse{'s' if max_analyses > 1 else ''}/mois épuisé "
                f"(Plan {plan.upper()}). "
                "Achetez un Executive Capacity Pack ou passez au plan supérieur."
            )

        return True, ""

    def increment_analysis(self, company_id: str) -> None:
        """
        Incrémente le compteur après une Analyse réussie.

        Lit plan + bonus_analyses_remaining en une seule requête companies.
        Si plan éligible et stock > 0 : décrémente bonus (verrou optimiste, retry x3).
        Sinon : incrémente analyses_count mensuel (verrou optimiste, retry x3).

        Appelé par analyze.py SANS paramètre plan — plan lu en DB ici.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            # Lecture plan + bonus en une seule requête
            result = (
                sb.from_("companies")
                .select("plan, bonus_analyses_remaining")
                .eq("id", company_id)
                .execute()
            )
            if not result.data:
                # Fallback : incrémenter le mensuel
                self._get_or_create_usage_row(company_id)
                self._increment_monthly_count(company_id, year_month)
                return

            row = result.data[0]
            plan_key = (row.get("plan") or "free").lower()
            bonus = row.get("bonus_analyses_remaining", 0) or 0

            if plan_key in _BONUS_ELIGIBLE_PLANS and bonus > 0:
                # Décrémentation bonus avec verrou optimiste (retry)
                for _ in range(_OPTIMISTIC_RETRIES):
                    ok = self._decrement_bonus(company_id)
                    if ok:
                        return
                    # Conflit → re-lire bonus
                    bonus = self._get_bonus_remaining(company_id)
                    if bonus <= 0:
                        break
                # Plus de bonus ou retries épuisés → mensuel
                self._get_or_create_usage_row(company_id)
                self._increment_monthly_count(company_id, year_month)
            else:
                # Pas de bonus disponible → mensuel
                self._get_or_create_usage_row(company_id)
                self._increment_monthly_count(company_id, year_month)

        except Exception:
            pass

    def get_usage_this_month(self, company_id: str, plan: str) -> dict:
        """
        Résumé d'usage du mois en cours.

        Bonus : lu depuis companies.bonus_analyses_remaining (stock permanent).
        Analyses mensuelles : lu depuis usage_limits.analyses_count (compteur mensuel).
        bonus_suspended : True si plan FREE avec bonus > 0.

        Retourne un dict avec :
          - analyses : compteur mensuel, bonus permanent, totaux
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
        analyses_count = usage.get("analyses_count", 0) or 0
        interactions_used = usage.get("chat_count", 0) or 0

        bonus = self._get_bonus_remaining(company_id)

        plan_key = plan.lower()
        bonus_suspended = (plan_key not in _BONUS_ELIGIBLE_PLANS) and bonus > 0

        # En Option B le stock bonus est permanent et indépendant du mensuel.
        # analyses_count = mensuelles consommées uniquement.
        monthly_used = analyses_count
        monthly_remaining = max(0, max_analyses - monthly_used) if max_analyses is not None else None

        if max_analyses is not None:
            if plan_key in _BONUS_ELIGIBLE_PLANS:
                total_allowed = max_analyses + bonus
            else:
                total_allowed = max_analyses   # bonus suspendu → non comptabilisé dans total
            analyses_remaining = max(0, total_allowed - monthly_used) if not bonus_suspended else monthly_remaining
        else:
            total_allowed = None
            analyses_remaining = None

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
            "analyses_used":              monthly_used,
            "analyses_limit":             max_analyses,        # quota mensuel du Plan
            "analyses_bonus":             bonus,               # stock permanent bonus
            "analyses_bonus_remaining":   bonus,               # identique en Option B (pas de consommation via count)
            "analyses_bonus_suspended":   bonus_suspended,     # True si FREE avec bonus
            "analyses_monthly_used":      monthly_used,
            "analyses_monthly_remaining": monthly_remaining,
            "analyses_total_allowed":     total_allowed,
            "analyses_remaining":         analyses_remaining,
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
        Ajoute des Analyses bonus au stock permanent du compte.

        Écrit dans companies.bonus_analyses_remaining (Option B).
        Non-atomique (READ-THEN-WRITE) — usage interne / tests uniquement.
        En production : la RPC apply_stripe_webhook est atomique (WP1B.3).
        """
        sb = self._get_supabase()
        if not sb:
            return
        try:
            current_bonus = self._get_bonus_remaining(company_id)
            sb.from_("companies").update({
                "bonus_analyses_remaining": current_bonus + quantity
            }).eq("id", company_id).execute()
        except Exception:
            pass

    # ─── Interactions ─────────────────────────────────────────────────────────
    #
    # Une Interaction = un message chat envoyé par l'utilisateur.
    # Le quota est mensuel et global. Aucune limite par Analyse.

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
