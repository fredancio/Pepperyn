"""
Usage Service — Pepperyn Release 1.0  (WP1C.1)

Moteur de quotas et de suivi d'usage.

Source des quotas : config/product_catalog.py (PLAN_LIMITS, get_plan).
Aucune constante métier locale.

═══════════════════════════════════════════════════════════════════════════════
SÉMANTIQUE DE bonus_analyses
═══════════════════════════════════════════════════════════════════════════════
bonus_analyses représente le SOLDE RESTANT d'Analyses bonus (pas le total acheté).

  Achat d'un pack       → bonus_analyses += quantité  (via RPC apply_stripe_webhook)
  Analyse lancée        → si bonus_analyses > 0 : bonus_analyses -= 1
                          sinon : analyses_count += 1
  Renouvellement mensuel→ analyses_count → 0 ; bonus_analyses INCHANGÉ (solde reporté)

Cette sémantique garantit :
  - un bonus consommé ne réapparaît jamais
  - un bonus non consommé persiste indéfiniment d'un mois à l'autre
  - les packs sont des achats ponctuels, pas des quotas mensuels

═══════════════════════════════════════════════════════════════════════════════
ORDRE DE CONSOMMATION DES ANALYSES
═══════════════════════════════════════════════════════════════════════════════
  1. Analyses bonus (Executive Capacity Packs) — bonus_analyses — EN PREMIER.
  2. Quota mensuel du Plan — analyses_count — ensuite.

═══════════════════════════════════════════════════════════════════════════════
RÈGLE INTERACTIONS
═══════════════════════════════════════════════════════════════════════════════
Le quota d'Interactions est UNIQUEMENT mensuel (chat_monthly_cap).
Il n'existe aucune limite d'Interactions par Analyse.

═══════════════════════════════════════════════════════════════════════════════
TABLES SUPABASE
═══════════════════════════════════════════════════════════════════════════════
  usage_limits :
    company_id      UUID    NOT NULL
    year_month      TEXT    NOT NULL  -- ex: "2026-07"
    analyses_count  INT     DEFAULT 0  -- quota mensuel consommé (hors bonus)
    chat_count      INT     DEFAULT 0  -- Interactions mensuelles consommées
    bonus_analyses  INT     DEFAULT 0  -- SOLDE RESTANT d'Analyses bonus
    PRIMARY KEY (company_id, year_month)

  Reset mensuel automatique :
    analyses_count → 0  (nouvelle ligne, nouveau mois)
    chat_count     → 0
    bonus_analyses → REPORTÉ depuis la ligne du mois précédent

  user_activity :
    id           UUID    DEFAULT gen_random_uuid() PRIMARY KEY
    company_id   UUID    NOT NULL
    event_type   TEXT    NOT NULL
    metadata     JSONB   DEFAULT '{}'
    created_at   TIMESTAMPTZ DEFAULT now()

═══════════════════════════════════════════════════════════════════════════════
NOTE D'ATOMICITÉ
═══════════════════════════════════════════════════════════════════════════════
La décrémentation de bonus_analyses utilise le verrouillage optimiste :
  UPDATE ... SET bonus_analyses = N-1 WHERE bonus_analyses = N

Si une modification concurrente est détectée (result.data vide après update),
la consommation bascule automatiquement sur le quota mensuel.

Pour une garantie d'atomicité totale (deux consommations concurrentes du dernier
bonus), une RPC PostgreSQL dédiée serait idéale — documenté comme dette technique
à adresser en post-launch si la concurrence par company devient significative.

═══════════════════════════════════════════════════════════════════════════════
CAS LIMITE DOCUMENTÉ — RPC + NOUVEAU MOIS
═══════════════════════════════════════════════════════════════════════════════
Si un webhook Stripe crédite un pack dans un nouveau mois AVANT qu'une requête
Python crée la ligne mensuelle, le report du solde précédent est ignoré par le
RPC (qui crée la ligne avec juste le nouveau pack).
Ce cas est extrêmement rare en production (achat avant toute analyse du mois)
et sera adressé par une mise à jour du RPC apply_stripe_webhook en post-launch.
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
        """
        Récupère ou crée la ligne d'usage du mois courant.

        Reset mensuel automatique :
          - Nouvelle ligne créée pour chaque nouveau mois.
          - analyses_count et chat_count démarrent à 0.
          - bonus_analyses est REPORTÉ depuis la ligne du mois précédent
            (solde restant non consommé).

        Le report du bonus garantit qu'un bonus non consommé
        en juillet reste disponible en août.
        """
        sb = self._get_supabase()
        if not sb:
            return {"analyses_count": 0, "chat_count": 0, "bonus_analyses": 0}

        year_month = _current_year_month()
        try:
            # Chercher la ligne du mois courant
            result = (
                sb.from_("usage_limits")
                .select("*")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            if result.data:
                return result.data[0]

            # Nouveau mois → lire le solde bonus du mois précédent pour le reporter
            prev_result = (
                sb.from_("usage_limits")
                .select("bonus_analyses")
                .eq("company_id", company_id)
                .lt("year_month", year_month)
                .order("year_month", desc=True)
                .limit(1)
                .execute()
            )
            carried_bonus = (
                (prev_result.data[0].get("bonus_analyses", 0) if prev_result.data else 0) or 0
            )

            # Insérer la nouvelle ligne avec le solde bonus reporté
            # ignore_duplicates=True gère les insertions concurrentes sans erreur
            sb.from_("usage_limits").upsert({
                "company_id": company_id,
                "year_month": year_month,
                "analyses_count": 0,
                "chat_count": 0,
                "bonus_analyses": carried_bonus,
            }, on_conflict="company_id,year_month", ignore_duplicates=True).execute()

            # Relire pour obtenir la ligne réelle (en cas de création concurrente)
            result2 = (
                sb.from_("usage_limits")
                .select("*")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            if result2.data:
                return result2.data[0]

            return {"analyses_count": 0, "chat_count": 0, "bonus_analyses": carried_bonus}

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
        bonus = usage.get("bonus_analyses", 0) or 0
        monthly_used = usage.get("analyses_count", 0) or 0

        # Autorisé si bonus disponible OU quota mensuel non épuisé
        if bonus > 0:
            return True, ""
        if monthly_used < max_analyses:
            return True, ""

        # Les deux épuisés
        return False, (
            f"Quota de {max_analyses} Analyse{'s' if max_analyses > 1 else ''}/mois épuisé "
            f"(Plan {plan.upper()}). "
            "Achetez un Executive Capacity Pack ou passez au plan supérieur."
        )

    def get_usage_this_month(self, company_id: str, plan: str) -> dict:
        """
        Résumé d'usage du mois en cours.

        bonus_analyses est déjà le SOLDE RESTANT → pas de calcul comparatif.

        Prépare les champs nécessaires à WP1D (dashboard frontend).
        """
        try:
            limits = get_plan(plan)
        except KeyError:
            limits = get_plan("free")

        max_analyses = limits.analyses
        max_interactions = limits.chat_monthly_cap
        max_entities = limits.max_entities

        usage = self._get_or_create_usage_row(company_id)
        monthly_used = usage.get("analyses_count", 0) or 0
        interactions_used = usage.get("chat_count", 0) or 0
        bonus_remaining = usage.get("bonus_analyses", 0) or 0

        # Quota mensuel restant (hors bonus)
        monthly_remaining = max(0, max_analyses - monthly_used) if max_analyses is not None else None

        # Total restant = bonus restant + quota mensuel restant
        total_remaining = (
            (bonus_remaining + monthly_remaining)
            if monthly_remaining is not None
            else None
        )

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
            "analyses_used":              monthly_used,          # quota mensuel consommé
            "analyses_limit":             max_analyses,          # quota mensuel du Plan
            "analyses_bonus_remaining":   bonus_remaining,       # solde bonus restant
            "analyses_monthly_used":      monthly_used,
            "analyses_monthly_remaining": monthly_remaining,
            "analyses_remaining":         total_remaining,       # total restant (bonus + mensuel)
            # ── Aliases compat legacy (billing.py GET /usage) ─────────────────
            "bonus_analyses":             bonus_remaining,       # solde restant (renommé pour clarté)
            "total_allowed":              (max_analyses + bonus_remaining) if max_analyses is not None else None,
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
        Ajoute des Analyses bonus au solde restant.

        Note : billing.py utilise désormais la RPC apply_stripe_webhook (WP1B.3)
        qui est atomique. Cette méthode est conservée pour la compatibilité.
        Elle lit le solde actuel avant d'écrire (non atomique) — utiliser la RPC
        pour les nouveaux appels.
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
        Comptabilise une Analyse après son succès.

        Ordre de consommation :
          1. Si bonus_analyses > 0 → décrémente bonus_analyses de 1.
          2. Sinon → incrémente analyses_count de 1.

        Utilise le verrouillage optimiste pour la décrémentation du bonus :
          UPDATE ... SET bonus_analyses = N-1 WHERE bonus_analyses = N
        Si une modification concurrente est détectée, bascule sur le quota mensuel.

        Appelé par analyze.py après chaque Analyse complétée avec succès.
        """
        sb = self._get_supabase()
        if not sb:
            return

        year_month = _current_year_month()
        try:
            self._get_or_create_usage_row(company_id)
            self._consume_one_analysis(company_id, year_month)
        except Exception:
            pass

    def _consume_one_analysis(self, company_id: str, year_month: str) -> str:
        """
        Consomme une Analyse : bonus en premier, quota mensuel ensuite.

        Verrouillage optimiste pour la décrémentation du bonus :
          - Lit le solde actuel.
          - Tente de le décrémenter UNIQUEMENT si la valeur n'a pas changé.
          - Si concurrence détectée (result.data vide) → 3 tentatives max.
          - Après 3 échecs → bascule sur le quota mensuel.

        Retourne 'bonus' ou 'monthly' selon la source consommée.
        """
        sb = self._get_supabase()
        if not sb:
            return "monthly"

        MAX_RETRIES = 3

        for attempt in range(MAX_RETRIES):
            try:
                row = (
                    sb.from_("usage_limits")
                    .select("bonus_analyses, analyses_count")
                    .eq("company_id", company_id)
                    .eq("year_month", year_month)
                    .execute()
                )
                if not row.data:
                    break  # ligne absente → quota mensuel

                current = row.data[0]
                bonus = current.get("bonus_analyses", 0) or 0

                if bonus > 0:
                    # Verrouillage optimiste : n'écrit que si bonus_analyses = bonus
                    result = (
                        sb.from_("usage_limits")
                        .update({"bonus_analyses": bonus - 1})
                        .eq("company_id", company_id)
                        .eq("year_month", year_month)
                        .eq("bonus_analyses", bonus)   # guard de concurrence
                        .execute()
                    )
                    if result.data:
                        return "bonus"  # décrémentation réussie
                    # Sinon : modification concurrente détectée → retry
                    continue

                # Aucun bonus → consommer le quota mensuel
                monthly = current.get("analyses_count", 0) or 0
                sb.from_("usage_limits").update({
                    "analyses_count": monthly + 1
                }).eq("company_id", company_id).eq("year_month", year_month).execute()
                return "monthly"

            except Exception:
                break

        # Fallback après retries épuisés : incrémenter le quota mensuel
        try:
            row = (
                sb.from_("usage_limits")
                .select("analyses_count")
                .eq("company_id", company_id)
                .eq("year_month", year_month)
                .execute()
            )
            monthly = (row.data[0].get("analyses_count", 0) if row.data else 0) or 0
            sb.from_("usage_limits").update({
                "analyses_count": monthly + 1
            }).eq("company_id", company_id).eq("year_month", year_month).execute()
        except Exception:
            pass
        return "monthly"

    # ─── Interactions ─────────────────────────────────────────────────────────

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
        Incrémente le compteur d'Interactions mensuel après un message.
        Met à jour uniquement usage_limits.chat_count.
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
