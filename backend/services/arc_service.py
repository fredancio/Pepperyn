"""
Arc Service — Pepperyn MVP Decision Arc (v16).

Responsabilités :
  - Créer un arc depuis un feedback 'planned' (source de vérité unique : backend)
  - Détecter les conséquences candidates après chaque nouvelle analyse
  - Confirmer / rejeter un lien conséquence
  - Proposer et valider le learning
  - Backfill des arcs manquants (reconstruction idempotente)

Architecture additive — aucun appel ici ne bloque le pipeline principal.
Chaque méthode a son propre try/except au niveau de l'appelant.

Règles fondamentales :
  - decision_text IS NOT NULL requis pour CLOSED
  - decision_confirmed_at ≠ date réelle de décision (c'est la date de prise de connaissance)
  - link_hypothesis : niveaux 1-3 uniquement (observation, association, hypothèse)
  - Un refus de lien ne ferme pas l'arc — il reste en EXECUTION
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve_current_engagement_id(
    supabase,
    entity_id: Optional[str],
    entity_company_id: Optional[str],
    expected_company_id: str,
) -> Optional[str]:
    """
    Résout l'Engagement courant d'une Entity, de façon strictement
    déterministe — jamais une heuristique (mission DecisionArc ↔ Engagement,
    Mission 10 : "no date-gap inference. No fact_id inference. No
    Analysis-text inference. Only deterministic current domain relationships").

    Hypothèse explicite, valable AUJOURD'HUI uniquement : la contrainte SQL
    UNIQUE(entity_id) sur engagements (v19) garantit qu'au plus un
    Engagement existe par Entity — cette fonction retourne donc, sans
    ambiguïté, LE seul Engagement possible pour cette Entity. Cette
    hypothèse cessera d'être vraie le jour où la cardinalité sera relâchée
    (déclencheur déjà nommé : STRATEGIC_DEFERRED_WORK_REGISTER.md §1.2.a —
    "la première fonctionnalité qui a besoin de créer un second mandat
    professionnel pour une Organisation existante"). Cette fonction devra
    alors être revue pour résoudre l'Engagement COURANT (actif/non-churned)
    plutôt que "l'Engagement" au singulier — non construit par anticipation
    ici (Article IX), `.limit(1)` documente explicitement cette hypothèse
    plutôt que de la laisser implicite.

    Défense en profondeur tenant (Mission 17) : n'attache jamais un
    Engagement dont l'Entity résolue n'appartient pas à expected_company_id
    — même logique que evidence_query_service.py (filtre explicite même si
    la donnée amont est déjà supposée cohérente par construction ailleurs
    dans le dépôt).

    Args:
        supabase: client Supabase (service role).
        entity_id: entity_id de l'analyse d'origine (analyses.entity_id),
                   PAS decision_arcs.entity_id — voir note du module
                   arc_service et v21_decision_arc_engagement.sql sur le
                   non-peuplement de ce dernier par le chemin de création réel.
        entity_company_id: company_id porté par la même ligne `analyses`
                            que entity_id (déjà lu dans la même requête par
                            l'appelant — aucune requête `entities`
                            supplémentaire nécessaire).
        expected_company_id: company_id attendu (celui de l'arc en cours de
                              création/backfill).

    Returns:
        L'id de l'Engagement résolu, ou None (jamais une exception, jamais
        une valeur fabriquée) si : entity_id absent, mismatch de company,
        aucun Engagement trouvé, ou toute erreur de lecture — cette
        résolution est un enrichissement optionnel, elle ne doit jamais
        bloquer la création ou le backfill de l'arc.
    """
    if not entity_id or entity_company_id != expected_company_id:
        return None
    try:
        result = (
            supabase.from_("engagements")
            .select("id")
            .eq("entity_id", entity_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0]["id"] if rows else None
    except Exception as e:
        logger.warning(
            "[ARC] Résolution Engagement échouée pour entity_id=%s : %s",
            entity_id, e,
        )
        return None


# ── Review Briefing — classification et gabarits (Capability 3) ──────────────
#
# Toute cette section est déterministe et testable sans base de données :
# entrée = liste d'arcs + date du jour, sortie = liste de BriefingItem.
# Aucun appel LLM — voir REVIEW_BRIEFING_IMPLEMENTATION_PLAN.md section 6.

BRIEFING_PRIORITY_ORDER = {"urgent": 0, "to_check": 1, "done": 2, "closed": 3}

# Seuil de bascule vers "urgent" pour une recommandation non décidée.
# Hypothèse de départ, non calibrée sur un usage réel — voir plan section 5,
# explicitement modifiable sans autre impact.
URGENT_INTENTION_THRESHOLD_DAYS = 21


class ArcService:

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

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Création d'arc ────────────────────────────────────────────────────────

    def create_arc_from_feedback(
        self,
        company_id: str,
        origin_analysis_id: str,
        recommendation_id: str,
        decision_source: str,
        recommendation_text: str,
        entity_id: Optional[str] = None,
    ) -> dict:
        """
        Crée un arc DCT-conforme depuis un feedback 'planned'.
        Idempotent : UNIQUE(origin_analysis_id, recommendation_id) → ON CONFLICT DO NOTHING.
        Retourne {created: bool, arc_id: str|None, arc_status: str|None}.

        Guard DCT : vérifie que l'analyse source possède un DecisionKernel dk-1 valide
        et un decision_fingerprint. Lève ValueError si absent.
        """
        supabase = self._get_supabase()
        if not supabase:
            return {"created": False, "arc_id": None, "arc_status": None}

        # ── Guard DCT : Situation doit être explicitement référencée ──────────
        # entity_id/company_id ajoutés au select (mission DecisionArc ↔
        # Engagement) uniquement pour résoudre engagement_id ci-dessous —
        # aucune requête supplémentaire nécessaire pour cette lecture.
        # Rétrocompatible : les fixtures de test existantes ne portent pas
        # ces clés, .get() renvoie alors None et la résolution est
        # simplement sautée (voir _resolve_current_engagement_id).
        try:
            analysis_result = (
                supabase.from_("analyses")
                .select("decision_kernel, decision_fingerprint, entity_id, company_id")
                .eq("id", origin_analysis_id)
                .single()
                .execute()
            )
        except Exception as e:
            raise ValueError(
                f"[ARC] Arc DCT-conforme impossible : analyses.{origin_analysis_id} "
                f"introuvable — {e}"
            )

        data = analysis_result.data or {}
        decision_kernel = data.get("decision_kernel")
        decision_fingerprint = data.get("decision_fingerprint")

        if not decision_kernel or not decision_fingerprint:
            raise ValueError(
                f"[ARC] Arc DCT-conforme impossible : analyses.{origin_analysis_id} "
                f"n'a pas de DecisionKernel dk-1 valide "
                f"(kernel={'présent' if decision_kernel else 'absent'}, "
                f"fingerprint={'présent' if decision_fingerprint else 'absent'}). "
                f"Arc non créé."
            )

        # Résolution Engagement (mission DecisionArc ↔ Engagement) — best
        # effort, jamais bloquant. N'émet une requête `engagements` que si
        # l'analyse d'origine porte un entity_id (voir docstring de
        # _resolve_current_engagement_id pour pourquoi c'est analyses.entity_id,
        # pas decision_arcs.entity_id, qui sert de source ici).
        engagement_id = _resolve_current_engagement_id(
            supabase=supabase,
            entity_id=data.get("entity_id"),
            entity_company_id=data.get("company_id"),
            expected_company_id=company_id,
        )

        # ── Insertion idempotente ─────────────────────────────────────────────
        row = {
            "company_id": company_id,
            "origin_analysis_id": origin_analysis_id,
            "decision_fingerprint": decision_fingerprint,
            "recommendation_id": recommendation_id,
            "decision_source": decision_source if decision_source in (
                "plan_action_haute", "plan_action"
            ) else "plan_action",
            "recommendation_text": recommendation_text,
            "status": "intention",
        }
        if entity_id:
            row["entity_id"] = entity_id
        if engagement_id:
            row["engagement_id"] = engagement_id

        try:
            result = (
                supabase.from_("decision_arcs")
                .insert(row)
                .execute()
            )
        except Exception as e:
            # UNIQUE constraint → arc déjà existant
            err_str = str(e)
            if "unique" in err_str.lower() or "duplicate" in err_str.lower():
                logger.info(
                    "[ARC] Arc déjà existant pour origin=%s rec=%s — idempotence OK",
                    origin_analysis_id, recommendation_id,
                )
                return {"created": False, "arc_id": None, "arc_status": "intention"}
            raise

        if not result.data:
            return {"created": False, "arc_id": None, "arc_status": None}

        arc_id = result.data[0]["id"]

        # Créer le lien 'origin'
        try:
            supabase.from_("arc_analysis_links").insert({
                "arc_id": arc_id,
                "analysis_id": origin_analysis_id,
                "link_type": "origin",
                "confirmed_by_user": True,
                "link_hypothesis": "Analyse source de cet arc décisionnel.",
            }).execute()
        except Exception as e:
            logger.warning("[ARC] Lien origin non créé pour arc %s : %s", arc_id, e)

        logger.info(
            "[ARC] Arc créé — arc_id=%s company_id=%s recommendation_id=%s",
            arc_id, company_id, recommendation_id,
        )
        return {"created": True, "arc_id": arc_id, "arc_status": "intention"}

    # ── Transition INTENTION → EXECUTION (via check-in) ───────────────────────

    def register_execution_from_checkin(
        self,
        arc_id: str,
        checkin_status: str,
        execution_notes: Optional[str] = None,
    ) -> dict:
        """
        Fait avancer l'arc de INTENTION à EXECUTION suite à un check-in done/partially_done.

        Sémantique :
          decision_confirmed_at = now() → quand Pepperyn a appris qu'une décision avait été prise
                                          ≠ date réelle à laquelle la décision a été prise
          decision_confirmation_source = 'inferred_from_execution'
          decision_text reste NULL (la décision est inférée, pas documentée)

        La documentation de decision_text interviendra lors de la validation du learning (CLOSED).
        """
        supabase = self._get_supabase()
        if not supabase:
            return {}

        execution_status = "complete" if checkin_status == "done" else "partial"
        now = self._now()

        result = (
            supabase.from_("decision_arcs")
            .update({
                "status": "execution",
                "execution_status": execution_status,
                "execution_notes": execution_notes,
                "execution_updated_at": now,
                # Pepperyn apprend qu'une décision a existé — pas quand elle a été prise
                "decision_confirmed_at": now,
                "decision_confirmation_source": "inferred_from_execution",
                # decision_text reste NULL : décision inférée ≠ décision documentée
            })
            .eq("id", arc_id)
            .eq("status", "intention")  # transition depuis INTENTION uniquement
            .execute()
        )

        if result.data:
            logger.info(
                "[ARC] EXECUTION inférée — arc_id=%s execution_status=%s "
                "decision_confirmation_source=inferred_from_execution",
                arc_id, execution_status,
            )
        return result.data[0] if result.data else {}

    # ── Détection de conséquences candidates ─────────────────────────────────

    def detect_consequence_candidates(
        self,
        company_id: str,
        new_analysis_id: str,
        analyse_json: dict,
    ) -> list[dict]:
        """
        Appelé après _save_to_db() dans analyze.py.
        Pour chaque arc en status='execution' de cette company, évalue si
        la nouvelle analyse présente des évolutions dignes d'être reliées à l'arc.

        RÈGLE CAUSALE : link_hypothesis contient uniquement des associations
        temporelles (niveaux 1-3). Jamais de causalité affirmée.

        Retourne une liste de candidats à présenter à l'utilisateur.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        # Récupérer les arcs EXECUTION de cette company
        try:
            arcs_result = (
                supabase.from_("decision_arcs")
                .select("id, status, recommendation_text, decision_text, "
                        "created_at, execution_status")
                .eq("company_id", company_id)
                .eq("status", "execution")
                .execute()
            )
        except Exception as e:
            logger.error("[ARC] detect_consequence_candidates — fetch arcs failed: %s", e)
            return []

        arcs = arcs_result.data or []
        if not arcs:
            return []

        candidates = []
        for arc in arcs:
            # Vérifier si un lien existe déjà pour cette analyse
            try:
                existing = (
                    supabase.from_("arc_analysis_links")
                    .select("id")
                    .eq("arc_id", arc["id"])
                    .eq("analysis_id", new_analysis_id)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    continue  # lien déjà créé pour ce couple (arc, analyse)
            except Exception:
                pass

            hypothesis = self._build_consequence_hypothesis(arc, analyse_json)
            if not hypothesis:
                continue

            # Insérer le candidat (non-bloquant si échec)
            try:
                supabase.from_("arc_analysis_links").insert({
                    "arc_id": arc["id"],
                    "analysis_id": new_analysis_id,
                    "link_type": "consequence_candidate",
                    "link_hypothesis": hypothesis,
                    "confirmed_by_user": None,  # NULL = en attente de review
                }).execute()
            except Exception as e:
                logger.warning(
                    "[ARC] Candidat non persisté pour arc %s : %s", arc["id"], e
                )
                continue

            candidates.append({
                "arc_id": arc["id"],
                "arc_status": arc["status"],
                "recommendation_text": arc["recommendation_text"],
                "decision_text": arc.get("decision_text"),
                "hypothesis": hypothesis,
                "analysis_id": new_analysis_id,
            })

        if candidates:
            logger.info(
                "[ARC] %d candidat(s) détecté(s) pour company_id=%s analyse=%s",
                len(candidates), company_id, new_analysis_id,
            )

        return candidates

    def _build_consequence_hypothesis(self, arc: dict, analyse_json: dict) -> Optional[str]:
        """
        Construit une hypothèse temporelle/corréllationnelle (jamais causale).
        Retourne None si aucun signal significatif n'est détecté.

        Niveau causal max : 3 (hypothèse de lien)
        Autorisé : "est survenu après", "est corrélé à", "une évolution observée depuis"
        Interdit : "a causé", "grâce à", "est la conséquence de"
        """
        score_rentabilite = analyse_json.get("score_rentabilite")
        score_risque = analyse_json.get("score_risque")
        decision_field = (arc.get("decision_text") or arc.get("recommendation_text", ""))
        decision_short = decision_field[:60] + ("..." if len(decision_field) > 60 else "")

        signals = []
        if score_rentabilite is not None:
            signals.append(f"score de rentabilité à {score_rentabilite}/10")
        if score_risque is not None:
            signals.append(f"score de risque à {score_risque}/10")

        # Signal sur les métriques financières
        revenus = analyse_json.get("revenus") or {}
        if isinstance(revenus, dict) and revenus.get("total"):
            signals.append("évolution du chiffre d'affaires")

        if not signals:
            return None

        signal_str = " et ".join(signals[:2])  # max 2 signaux par hypothèse
        return (
            f"Depuis votre décision de « {decision_short} », "
            f"une nouvelle analyse montre : {signal_str}. "
            f"Ces évolutions sont survenues après votre décision — "
            f"souhaitez-vous relier cette analyse à votre arc décisionnel ?"
        )

    # ── Confirmation / rejet d'un lien conséquence ───────────────────────────

    def confirm_consequence_link(
        self,
        arc_id: str,
        analysis_id: str,
        confirmed: bool,
        rejection_reason: Optional[str] = None,
    ) -> dict:
        """
        L'utilisateur confirme ou rejette un lien conséquence.

        Si confirmé → arc avance à CONSEQUENCES_LINKED + learning proposé.
        Si rejeté   → lien mis à jour, arc reste en EXECUTION (pas d'abandon).

        RÈGLE : refuser un lien ≠ abandonner l'arc.
        """
        supabase = self._get_supabase()
        if not supabase:
            return {}

        now = self._now()

        link_update = {
            "link_type": "consequence_confirmed" if confirmed else "consequence_rejected",
            "confirmed_by_user": confirmed,
            "reviewed_at": now,
        }
        if rejection_reason:
            link_update["user_rejection_reason"] = rejection_reason

        try:
            supabase.from_("arc_analysis_links").update(link_update).eq(
                "arc_id", arc_id
            ).eq("analysis_id", analysis_id).execute()
        except Exception as e:
            logger.error("[ARC] confirm_consequence_link — update link failed: %s", e)
            raise

        if confirmed:
            # Avancer l'arc
            try:
                supabase.from_("decision_arcs").update({
                    "status": "consequences_linked",
                }).eq("id", arc_id).execute()
            except Exception as e:
                logger.error(
                    "[ARC] confirm_consequence_link — update arc status failed: %s", e
                )
                raise

            # Proposer le learning automatiquement
            learning_text = None
            try:
                arc_data_result = (
                    supabase.from_("decision_arcs")
                    .select("*")
                    .eq("id", arc_id)
                    .single()
                    .execute()
                )
                if arc_data_result.data:
                    learning_text = self._propose_learning(arc_id, arc_data_result.data)
            except Exception as e:
                logger.warning("[ARC] propose_learning failed après confirmation: %s", e)

            logger.info(
                "[ARC] Conséquence confirmée — arc_id=%s → CONSEQUENCES_LINKED",
                arc_id,
            )
            return {
                "confirmed": True,
                "arc_id": arc_id,
                "arc_status": "learning_proposed",
                "learning_text": learning_text,
            }
        else:
            logger.info(
                "[ARC] Conséquence rejetée — arc_id=%s reste en EXECUTION "
                "(pas d'abandon, d'autres analyses peuvent proposer des candidats)",
                arc_id,
            )
            return {
                "confirmed": False,
                "arc_id": arc_id,
                "arc_status": "execution",
            }

    # ── Proposition de learning ───────────────────────────────────────────────

    def _propose_learning(self, arc_id: str, arc: dict) -> Optional[str]:
        """
        Génère et persiste un learning proposé depuis l'historique de l'arc.
        Avance l'arc à LEARNING_PROPOSED.
        MVP : template Python sans appel LLM (rapide, prédictible).
        """
        supabase = self._get_supabase()
        if not supabase:
            return None

        recommendation_text = arc.get("recommendation_text", "")
        decision_text = arc.get("decision_text")
        execution_status = arc.get("execution_status", "not_started")
        execution_notes = arc.get("execution_notes")

        status_labels = {
            "complete": "intégralement mise en œuvre",
            "partial": "partiellement mise en œuvre",
            "in_progress": "en cours de mise en œuvre",
            "not_started": "non mise en œuvre à ce jour",
        }

        parts = [f"Recommandation initiale : {recommendation_text}"]

        if decision_text and decision_text.strip() != recommendation_text.strip():
            parts.append(f"Décision effectivement prise : {decision_text}")
        else:
            parts.append("(La décision reste à documenter avant la clôture de cet arc.)")

        parts.append(
            f"Exécution : {status_labels.get(execution_status, execution_status)}"
        )

        if execution_notes:
            parts.append(f"Notes : {execution_notes}")

        parts.append(
            "À compléter : quels apprentissages cette trajectoire apporte-t-elle "
            "pour les décisions futures ?"
        )

        learning_text = "\n\n".join(parts)

        try:
            supabase.from_("decision_arcs").update({
                "status": "learning_proposed",
                "learning_text": learning_text,
            }).eq("id", arc_id).execute()
        except Exception as e:
            logger.error("[ARC] _propose_learning — update status failed: %s", e)

        logger.info("[ARC] Learning proposé — arc_id=%s", arc_id)
        return learning_text

    # ── Validation du learning et fermeture ──────────────────────────────────

    def validate_learning(
        self,
        arc_id: str,
        learning_text: str,
        decision_text: Optional[str] = None,
    ) -> dict:
        """
        Valide le learning et ferme l'arc.

        GUARD FERMETURE : decision_text IS NOT NULL requis.
        Si decision_text est NULL et aucun decision_text n'est fourni → ValueError.

        Si decision_text fourni (confirmation rétrospective) :
          - decision_text est écrit (IMMUTABLE ensuite)
          - decision_confirmation_source → 'explicit'
          - decision_confirmed_at → now()
        """
        supabase = self._get_supabase()
        if not supabase:
            return {}

        # Récupérer l'arc courant
        try:
            arc_result = (
                supabase.from_("decision_arcs")
                .select("decision_text, decision_confirmation_source, learning_text, status")
                .eq("id", arc_id)
                .single()
                .execute()
            )
        except Exception as e:
            raise ValueError(f"[ARC] Arc {arc_id} introuvable — {e}")

        arc = arc_result.data
        if not arc:
            raise ValueError(f"[ARC] Arc {arc_id} introuvable.")

        if arc.get("status") == "closed":
            raise ValueError(f"[ARC] Arc {arc_id} est déjà CLOSED.")

        existing_decision_text = arc.get("decision_text")
        final_decision_text = decision_text or existing_decision_text

        # ── GUARD : decision_text obligatoire pour CLOSED ─────────────────────
        if not final_decision_text or not final_decision_text.strip():
            raise ValueError(
                f"[ARC] Fermeture impossible — decision_text est NULL sur arc {arc_id}. "
                f"L'utilisateur doit confirmer la décision effectivement prise avant CLOSED. "
                f"(Recommendation connue + Execution connue ≠ Decision documentée.)"
            )

        now = self._now()
        original_learning = arc.get("learning_text", "")
        is_modified = learning_text.strip() != (original_learning or "").strip()

        update: dict = {
            "status": "closed",
            "learning_text": learning_text,
            "learning_confirmed": True,
            "learning_modified": is_modified,
            "closed_at": now,
        }

        # Confirmation rétrospective : decision_text fourni ici pour la première fois
        if not existing_decision_text and final_decision_text:
            update["decision_text"] = final_decision_text
            update["decision_confirmation_source"] = "explicit"
            update["decision_confirmed_at"] = now
            logger.info(
                "[ARC] decision_text confirmé rétrospectivement — arc_id=%s", arc_id
            )

        try:
            supabase.from_("decision_arcs").update(update).eq("id", arc_id).execute()
        except Exception as e:
            logger.error("[ARC] validate_learning — update to CLOSED failed: %s", e)
            raise

        logger.info("[ARC] Arc CLOSED — arc_id=%s", arc_id)
        return {
            "arc_id": arc_id,
            "status": "closed",
            "closed_at": now,
            "decision_confirmation_source": update.get(
                "decision_confirmation_source",
                arc.get("decision_confirmation_source"),
            ),
        }

    # ── Review Briefing — synthèse opérationnelle ─────────────────────────────

    @staticmethod
    def _days_since(iso_timestamp: Optional[str]) -> int:
        """Nombre de jours entiers écoulés depuis un timestamp ISO. 0 si absent/invalide."""
        if not iso_timestamp:
            return 0
        try:
            ts = iso_timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - dt
            return max(delta.days, 0)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _format_date_fr(iso_timestamp: Optional[str]) -> str:
        """Formate un timestamp ISO en date française courte. Chaîne vide si absent/invalide."""
        if not iso_timestamp:
            return ""
        try:
            ts = iso_timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            mois = [
                "janvier", "février", "mars", "avril", "mai", "juin",
                "juillet", "août", "septembre", "octobre", "novembre", "décembre",
            ]
            return f"{dt.day} {mois[dt.month - 1]} {dt.year}"
        except (ValueError, TypeError, IndexError):
            return ""

    def _arc_to_briefing_item(self, arc: dict) -> dict:
        """
        Traduit un DecisionArc en BriefingItem — classification par priorité
        et génération templatée de why_it_matters / questions_to_ask.

        RÈGLE : jamais de causalité inventée, jamais un libellé qui affirme
        qu'un sujet est "réglé"/"résolu"/"exécuté" au-delà de ce que
        execution_status garantit réellement.
        """
        status = arc.get("status")
        execution_status = arc.get("execution_status", "not_started")
        recommendation_text = arc.get("recommendation_text", "") or ""
        decision_text = arc.get("decision_text")
        title = decision_text or recommendation_text

        base = {
            "arc_id": arc.get("id"),
            "source_type": "decision_arc",
            # Nécessaire pour le regroupement par client dans
            # build_portfolio_briefing() — additif, ne change rien pour les
            # consommateurs existants du Briefing de revue.
            "entity_id": arc.get("entity_id"),
            "title": title,
            "learning_text": None,
            # Interne uniquement — utilisé par _attach_evidence_support()
            # pour résoudre la preuve Evidence Ledger de cet item, jamais
            # exposé tel quel dans la réponse API finale (retiré avant
            # retour par build_review_briefing, Evidence Consumer #1).
            "_origin_analysis_id": arc.get("origin_analysis_id"),
        }

        if status == "intention":
            days = self._days_since(arc.get("created_at"))
            if days > URGENT_INTENTION_THRESHOLD_DAYS:
                return {
                    **base,
                    "priority": "urgent",
                    "temporal_context": f"Recommandé il y a {days} jours",
                    "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
                    "questions_to_ask": [
                        "Où en êtes-vous sur cette recommandation ?",
                        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?",
                    ],
                    "age_days": days,
                }
            return {
                **base,
                "priority": "to_check",
                "temporal_context": f"Recommandé il y a {days} jours",
                "why_it_matters": "Décision encore en attente.",
                "questions_to_ask": ["Qu'avez-vous décidé pour cette recommandation ?"],
                "age_days": days,
            }

        if status == "execution":
            if execution_status == "complete":
                days = self._days_since(
                    arc.get("execution_updated_at") or arc.get("decision_confirmed_at")
                )
                return {
                    **base,
                    "priority": "to_check",
                    "temporal_context": f"Exécuté il y a {days} jours",
                    "why_it_matters": "Effet pas encore confirmé dans une analyse.",
                    "questions_to_ask": ["Quel effet avez-vous observé depuis ?"],
                    "age_days": days,
                }
            days = self._days_since(arc.get("decision_confirmed_at") or arc.get("updated_at"))
            return {
                **base,
                "priority": "to_check",
                "temporal_context": f"Décidé il y a {days} jours",
                "why_it_matters": "Exécution en cours.",
                "questions_to_ask": ["Où en est l'exécution depuis notre dernier échange ?"],
                "age_days": days,
            }

        if status in ("consequences_linked", "learning_proposed"):
            days = self._days_since(arc.get("updated_at"))
            return {
                **base,
                "priority": "done",
                "temporal_context": f"Effet confirmé il y a {days} jours",
                "why_it_matters": "Apprentissage en attente.",
                "questions_to_ask": ["Cet effet s'est-il maintenu depuis ?"],
                "age_days": days,
            }

        if status == "closed":
            days = self._days_since(arc.get("closed_at"))
            date_str = self._format_date_fr(arc.get("closed_at"))
            return {
                **base,
                "priority": "closed",
                "temporal_context": f"Clôturé le {date_str}" if date_str else "Clôturé",
                "why_it_matters": None,
                # Jamais de question sur une carte close — rien d'ouvert à discuter
                # (voir REVIEW_BRIEFING_IMPLEMENTATION_PLAN.md section 1B).
                "questions_to_ask": [],
                "learning_text": arc.get("learning_text"),
                "age_days": days,
            }

        # status == "decision" (réservé, non atteignable en MVP) ou valeur
        # inattendue — traité comme "à vérifier" sans sur-affirmer un état.
        days = self._days_since(arc.get("updated_at"))
        return {
            **base,
            "priority": "to_check",
            "temporal_context": f"Mis à jour il y a {days} jours",
            "why_it_matters": "Statut en cours de traitement.",
            "questions_to_ask": [],
            "age_days": days,
        }

    def build_review_briefing(
        self,
        company_id: str,
        entity_id: Optional[str] = None,
        limit: Optional[int] = 5,
    ) -> list[dict]:
        """
        Construit le Briefing de revue : arcs actifs (jamais 'abandoned'),
        classés par priorité, avec questions prêtes à poser. Lecture seule.

        entity_id : filtre optionnel sur le client actuellement sélectionné
        (frontend/components/chat/ChatContainer.tsx::selectedEntityId) — sans
        ce filtre, un cabinet avec plusieurs clients verrait un mélange
        d'arcs de clients différents, ce qui contredit l'objectif même du
        composant ("quand le cabinet ouvre un client"). Rétrocompatible :
        entity_id=None renvoie tous les arcs actifs de la company.

        Sémantique de `limit` (Incrément 2, Mission 5 — corrige l'ancienne
        convention où `limit=0` retombait silencieusement sur `items[:5]`,
        0 étant falsy en Python) :
          - limit=None → aucune limite, tous les items actifs retournés.
          - limit=0    → zéro résultat, littéral, jamais réinterprété.
          - limit > 0  → au plus `limit` items.
          - limit < 0  → ValueError explicite (valeur interdite, pas de
            convention implicite silencieuse).
        """
        if limit is not None and limit < 0:
            raise ValueError(
                f"[ARC] build_review_briefing — limit doit être >= 0 ou None (reçu {limit})."
            )

        supabase = self._get_supabase()
        if not supabase:
            return []

        query = (
            supabase.from_("decision_arcs")
            .select(
                "id, status, execution_status, recommendation_text, decision_text, "
                "execution_notes, learning_text, created_at, updated_at, "
                "decision_confirmed_at, execution_updated_at, closed_at, entity_id, "
                "origin_analysis_id"
            )
            .eq("company_id", company_id)
            .neq("status", "abandoned")
        )
        if entity_id:
            query = query.eq("entity_id", entity_id)

        try:
            result = query.order("updated_at", desc=True).execute()
        except Exception as e:
            logger.error("[ARC] build_review_briefing — fetch failed: %s", e)
            return []

        # Filtre défensif redondant avec le .neq() de la requête ci-dessus —
        # garantit l'exclusion même si la couche de mock/DB ne l'applique pas.
        arcs = [a for a in (result.data or []) if a.get("status") != "abandoned"]
        items = [self._arc_to_briefing_item(arc) for arc in arcs]
        self._attach_evidence_support(items, company_id, supabase)
        items.sort(key=lambda item: BRIEFING_PRIORITY_ORDER.get(item["priority"], 99))
        if limit is None:
            return items
        return items[:limit]

    def _attach_evidence_support(self, items: list[dict], company_id: str, supabase) -> None:
        """
        Evidence Ledger Consumer #1 — attache, en lecture seule, la preuve
        canonique disponible pour chaque BriefingItem via son analyse
        d'origine (decision_arcs.origin_analysis_id → evidence_ledger_entries
        .analyse_id, déjà UNIQUE côté DB — pas besoin de résoudre par
        Engagement/entity_id ici, cf. Mission 6 de la mission Evidence
        Consumer #1 : la clé analyse_id est déjà unique et sans ambiguïté,
        donc la question de cardinalité Entity:Engagement ne se pose même
        pas pour ce chemin de lecture).

        RÈGLE : aucun fallback vers analyses.analyse_json. Une analyse sans
        ligne dans evidence_ledger_entries reçoit `evidence_support = None`
        — jamais une preuve reconstruite depuis une autre source.

        Mute `items` en place (ajoute "evidence_support", retire la clé
        interne "_origin_analysis_id"). Ne lève jamais d'exception —
        enrichissement optionnel, jamais un bloqueur du Briefing de revue.
        """
        analysis_ids = [item.get("_origin_analysis_id") for item in items]
        support_by_analysis: dict = {}
        try:
            from services.evidence_query_service import get_evidence_support_by_analysis
            support_by_analysis = get_evidence_support_by_analysis(
                supabase=supabase,
                analysis_ids=[a for a in analysis_ids if a],
                company_id=company_id,
            )
        except Exception as e:
            logger.error("[ARC] _attach_evidence_support — lookup failed: %s", e)
            support_by_analysis = {}

        for item in items:
            origin_analysis_id = item.pop("_origin_analysis_id", None)
            item["evidence_support"] = (
                support_by_analysis.get(origin_analysis_id) if origin_analysis_id else None
            )

    # ── Portfolio Intelligence — synthèse multi-clients (Incrément 1 + 2) ─────

    # Textes why_it_matters jugés redondants avec l'icône de priorité, le
    # statut et le contexte temporel — voir
    # docs/Product/portfolio-card-review/PORTFOLIO_INFORMATION_HIERARCHY.md
    # section 3.2. Ensemble fermé et documenté, pas une heuristique sur le
    # texte : ces chaînes viennent d'un nombre fini et connu de gabarits
    # dans _arc_to_briefing_item, jamais d'un texte libre ou généré par LLM.
    _WHY_IT_MATTERS_REDUNDANT_TEXTS = frozenset({
        "Toujours sans décision confirmée après au moins une revue.",
        "Décision encore en attente.",
        "Exécution en cours.",
        "Statut en cours de traitement.",
    })

    @staticmethod
    def _is_why_it_matters_distinct(why_it_matters: Optional[str]) -> bool:
        """
        Fonction pure et déterministe (Mission 3, Incrément 2) : décide si
        why_it_matters apporte, sur la carte Portfolio, une information
        distincte de l'icône de priorité, du statut, du contexte temporel
        et du titre — seul cas où il doit être rendu.

        Ne s'applique qu'à PortfolioCard.why_it_matters_display — le Review
        Briefing par client continue d'afficher BriefingItem.why_it_matters
        sans filtre, inchangé (le texte y est lu une fois, pas scanné sur
        80 cartes).
        """
        if not why_it_matters:
            return False
        return why_it_matters not in ArcService._WHY_IT_MATTERS_REDUNDANT_TEXTS

    def build_portfolio_briefing(self, company_id: str) -> list[dict]:
        """
        Construit le Portfolio : une carte par client, portant son point le
        plus prioritaire parmi ses BriefingItem actifs, complétée par un
        compteur d'autres points actifs et un why_it_matters filtré.

        Pur regroupement du Briefing de revue existant par entity_id — aucun
        nouveau calcul de domaine, aucune nouvelle source de donnée, aucune
        nouvelle classification. Lecture seule.

        Appelle build_review_briefing(limit=None) — demande explicitement
        l'absence de limite (Incrément 2, Mission 5), plutôt que l'ancienne
        valeur arbitraire limit=1000.

        Un arc sans entity_id (jamais rattaché à un client) est exclu — il
        n'y a pas de carte client à laquelle le rattacher (voir
        PORTFOLIO_INTELLIGENCE_MVP.md : la carte est structurée par client).

        RÈGLE MÉTIER (Portfolio Home Product Validation, 2026-08-05 —
        correctif "Closed-Only Clients") : un point "closed" ne constitue
        jamais une raison active de préparer un client. Il est exclu ici de
        l'agrégation active — jamais choisi comme point principal, jamais
        compté, et un client dont TOUS les points sont "closed" (ou
        "abandoned", déjà exclu par build_review_briefing) ne produit
        aucune carte. Périmètre volontairement limité au Portfolio : le
        Review Briefing (build_review_briefing) continue d'afficher les
        points "closed" sans filtre, car un client déjà ouvert dans le chat
        doit pouvoir consulter son historique clos — seul le Portfolio, qui
        répond à "quel client dois-je préparer maintenant", exclut le clos.
        """
        items = self.build_review_briefing(company_id=company_id, entity_id=None, limit=None)
        if not items:
            return []

        # items est déjà trié par priorité (urgent → to_check → done → closed) ;
        # active_items retire les points "closed" avant tout regroupement —
        # un point clos ne peut donc plus jamais devenir top_item, ni gonfler
        # le compteur "+N autres points à suivre". Le premier item rencontré
        # pour un entity_id, dans active_items, est son point actif le plus
        # prioritaire.
        active_items = [item for item in items if item.get("priority") != "closed"]

        by_entity: dict[str, dict] = {}
        active_counts: dict[str, int] = {}
        for item in active_items:
            eid = item.get("entity_id")
            if not eid:
                continue
            active_counts[eid] = active_counts.get(eid, 0) + 1
            if eid not in by_entity:
                by_entity[eid] = item

        # Un client dont tous les points sont "closed" (ou "abandoned") n'a
        # aucune entrée dans active_items — aucune carte n'est créée pour
        # lui, conformément à la règle métier ci-dessus.
        if not by_entity:
            return []

        entity_ids = list(by_entity.keys())
        entity_names: dict[str, str] = {}
        supabase = self._get_supabase()
        if supabase:
            try:
                result = (
                    supabase.from_("entities")
                    .select("id, name")
                    .in_("id", entity_ids)
                    .execute()
                )
                for row in result.data or []:
                    entity_names[row["id"]] = row["name"]
            except Exception as e:
                logger.warning(
                    "[ARC] build_portfolio_briefing — lecture des noms clients échouée: %s", e
                )

        cards = []
        for eid, item in by_entity.items():
            entity_name = entity_names.get(eid, "Client")
            total_active = active_counts.get(eid, 0)
            # top_item est désormais toujours actif par construction (jamais
            # "closed", voir active_items ci-dessus) — il fait donc toujours
            # partie de total_active ; on ne le recompte pas comme "autre point".
            other_active_count = max(total_active - 1, 0)
            why_it_matters = item.get("why_it_matters")
            why_it_matters_display = (
                why_it_matters if self._is_why_it_matters_distinct(why_it_matters) else None
            )
            cards.append({
                "entity_id": eid,
                "entity_name": entity_name,
                "top_item": item,
                "other_active_count": other_active_count,
                "why_it_matters_display": why_it_matters_display,
            })

        # Tri (Mission 4) : priorité du point le plus prioritaire, puis, à
        # égalité, ancienneté décroissante de ce même point (le plus ancien
        # en premier — age_days vient de _arc_to_briefing_item, calculé
        # depuis created_at/decision_confirmed_at/execution_updated_at/
        # updated_at/closed_at selon le statut, voir cette méthode), puis,
        # à double égalité, nom du client par ordre alphabétique (tie-break
        # final stable, sans signification métier au-delà du déterminisme).
        cards.sort(key=lambda c: (
            BRIEFING_PRIORITY_ORDER.get(c["top_item"]["priority"], 99),
            -c["top_item"].get("age_days", 0),
            (c["entity_name"] or "").lower(),
        ))
        return cards

    # ── "Ne plus suivre" — transition ABANDONED ───────────────────────────────

    def abandon_arc(
        self,
        arc_id: str,
        company_id: str,
        reason: Optional[str] = None,
    ) -> dict:
        """
        "Ne plus suivre" côté UI — Review Briefing.

        RÈGLE SÉMANTIQUE (correction 2026-08-05) : abandoned signifie
        uniquement "ce point ne doit plus apparaître dans le briefing actif".
        Ne signifie JAMAIS réglé/résolu/exécuté — cette méthode ne déduit
        aucun résultat métier, elle enregistre un arrêt de suivi.

        Ne supprime rien : la ligne, l'historique et arc_analysis_links
        restent intacts. Idempotent si l'arc est déjà abandoned.

        Lève ValueError si l'arc est introuvable (ou n'appartient pas à
        company_id) ou si l'arc est déjà CLOSED (le trigger d'immutabilité
        le refuserait de toute façon — vérifié ici en amont pour renvoyer
        une erreur explicite plutôt qu'une exception de trigger SQL).
        """
        supabase = self._get_supabase()
        if not supabase:
            return {"abandoned": False, "arc_id": arc_id}

        try:
            arc_result = (
                supabase.from_("decision_arcs")
                .select("id, status")
                .eq("id", arc_id)
                .eq("company_id", company_id)
                .single()
                .execute()
            )
        except Exception as e:
            raise ValueError(f"[ARC] Arc {arc_id} introuvable — {e}")

        arc = arc_result.data
        if not arc:
            raise ValueError(f"[ARC] Arc {arc_id} introuvable.")

        current_status = arc.get("status")
        if current_status == "closed":
            raise ValueError(
                f"[ARC] Arc {arc_id} est CLOSED et immuable — impossible de le "
                f"retirer du briefing via 'Ne plus suivre'."
            )
        if current_status == "abandoned":
            # Idempotent : déjà retiré du briefing actif, pas une erreur.
            return {"abandoned": True, "arc_id": arc_id, "already_abandoned": True}

        now = self._now()
        update = {
            "status": "abandoned",
            "abandoned_at": now,
            "abandoned_reason": reason,
        }

        try:
            supabase.from_("decision_arcs").update(update).eq("id", arc_id).execute()
        except Exception as e:
            logger.error("[ARC] abandon_arc — update failed pour arc %s: %s", arc_id, e)
            raise

        logger.info(
            "[ARC] Arc retiré du briefing actif ('Ne plus suivre') — arc_id=%s reason=%s",
            arc_id, reason or "(non précisé)",
        )
        return {"abandoned": True, "arc_id": arc_id, "abandoned_at": now}

    # ── Backfill ──────────────────────────────────────────────────────────────

    def backfill_missing_arcs(self, company_id: Optional[str] = None) -> dict:
        """
        Identifie les decision_feedback avec status='planned' sans arc correspondant
        et les crée. Idempotent (UNIQUE constraint).

        Appelable via POST /api/admin/arcs/backfill?company_id=xxx
        """
        supabase = self._get_supabase()
        if not supabase:
            return {"created": 0, "failed": 0, "skipped": 0}

        query = (
            supabase.from_("decision_feedback")
            .select("*")
            .eq("status", "planned")
        )
        if company_id:
            query = query.eq("company_id", company_id)

        try:
            result = query.execute()
        except Exception as e:
            logger.error("[ARC] backfill — fetch feedbacks failed: %s", e)
            return {"created": 0, "failed": 0, "skipped": 0}

        created = failed = skipped = 0

        for fb in result.data or []:
            try:
                out = self.create_arc_from_feedback(
                    company_id=fb["company_id"],
                    origin_analysis_id=fb["report_id"],
                    recommendation_id=fb["recommendation_id"],
                    decision_source=fb.get("recommendation_source") or "plan_action",
                    recommendation_text=fb.get("recommendation_text") or "",
                )
                if out.get("created"):
                    created += 1
                else:
                    skipped += 1  # déjà existant (idempotence)
            except ValueError as e:
                # Guard DCT : analyse sans kernel → skip silencieux
                logger.info("[ARC] backfill skip — %s", e)
                skipped += 1
            except Exception as e:
                logger.error(
                    "[ARC] backfill failed pour feedback %s : %s", fb.get("id"), e
                )
                failed += 1

        logger.info(
            "[ARC] Backfill terminé — créés=%d skipped=%d échecs=%d",
            created, skipped, failed,
        )
        return {"created": created, "failed": failed, "skipped": skipped}

    # ── DecisionArc ↔ Engagement — backfill historique ─────────────────────────

    def backfill_decision_arc_engagements(self) -> dict:
        """
        Backfill idempotent de engagement_id pour les DecisionArc existants
        (mission DecisionArc ↔ Engagement, Mission 8).

        Résolution déterministe UNIQUEMENT : pour chaque arc sans
        engagement_id, lit origin_analysis_id → analyses.(entity_id,
        company_id), puis résout via _resolve_current_engagement_id (même
        fonction que le chemin de création — voir sa docstring pour le
        choix de analyses.entity_id plutôt que decision_arcs.entity_id).
        Si non résolvable : reste NULL, jamais deviné (Mission 8 —
        "Prefer NULL / unresolved over fabricated ownership").

        Idempotent : un arc portant déjà un engagement_id n'est jamais relu
        ni recalculé (même discipline que backfill_engagements pour
        Engagement — note de revue n°2 de T2A, réappliquée ici).

        Traitement arc par arc, sans transaction globale — une erreur
        isolée n'annule pas le travail déjà fait sur les autres (même
        principe que backfill_engagements).

        Note opérationnelle : les arcs CLOSED ne peuvent recevoir
        engagement_id que grâce au carve-out étroit ajouté par
        v21_decision_arc_engagement.sql à arc_immutability_guard() — sans
        lui, cette UPDATE échouerait pour tout arc déjà CLOSED (voir
        commentaire de la migration). Ce comportement ne peut être vérifié
        que contre une vraie instance Postgres (le trigger n'existe pas
        dans les doubles de test Python) — voir réserve nommée dans le
        rapport final de la mission.

        Returns:
            {"resolved": int, "unresolved": int, "already_present": int, "errors": int}
        """
        supabase = self._get_supabase()
        if not supabase:
            return {"resolved": 0, "unresolved": 0, "already_present": 0, "errors": 0}

        stats = {"resolved": 0, "unresolved": 0, "already_present": 0, "errors": 0}

        try:
            arcs_result = (
                supabase.from_("decision_arcs")
                .select("id, origin_analysis_id, company_id, engagement_id")
                .execute()
            )
        except Exception as e:
            logger.error("[ARC] backfill_decision_arc_engagements — fetch arcs failed: %s", e)
            return stats

        for arc in arcs_result.data or []:
            if arc.get("engagement_id"):
                stats["already_present"] += 1
                continue

            arc_id = arc.get("id")
            origin_analysis_id = arc.get("origin_analysis_id")
            arc_company_id = arc.get("company_id")

            try:
                analysis_result = (
                    supabase.from_("analyses")
                    .select("entity_id, company_id")
                    .eq("id", origin_analysis_id)
                    .single()
                    .execute()
                )
                adata = analysis_result.data or {}

                engagement_id = _resolve_current_engagement_id(
                    supabase=supabase,
                    entity_id=adata.get("entity_id"),
                    entity_company_id=adata.get("company_id"),
                    expected_company_id=arc_company_id,
                )

                if not engagement_id:
                    stats["unresolved"] += 1
                    continue

                supabase.from_("decision_arcs").update(
                    {"engagement_id": engagement_id}
                ).eq("id", arc_id).execute()
                stats["resolved"] += 1

            except Exception as e:
                logger.error(
                    "[ARC] backfill_decision_arc_engagements — arc_id=%s failed: %s",
                    arc_id, e,
                )
                stats["errors"] += 1

        logger.info(
            "[ARC] Backfill DecisionArc↔Engagement terminé — résolus=%d "
            "non-résolus=%d déjà-présents=%d erreurs=%d",
            stats["resolved"], stats["unresolved"], stats["already_present"], stats["errors"],
        )
        return stats

    # ── Integrity check ───────────────────────────────────────────────────────

    def count_missing_arcs(self, company_id: Optional[str] = None) -> dict:
        """
        Compte les decision_feedback 'planned' sans arc correspondant.
        Utilisé par GET /api/admin/arcs/integrity.
        """
        supabase = self._get_supabase()
        if not supabase:
            return {"planned_feedbacks": 0, "existing_arcs": 0}

        query = (
            supabase.from_("decision_feedback")
            .select("id", count="exact")
            .eq("status", "planned")
        )
        if company_id:
            query = query.eq("company_id", company_id)

        try:
            result = query.execute()
            return {"planned_feedbacks": result.count or 0}
        except Exception as e:
            logger.error("[ARC] count_missing_arcs failed: %s", e)
            return {"planned_feedbacks": 0}


# Singleton — importé directement dans les routers et hooks
arc_service = ArcService()
