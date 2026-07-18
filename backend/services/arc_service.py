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
        try:
            analysis_result = (
                supabase.from_("analyses")
                .select("decision_kernel, decision_fingerprint")
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
