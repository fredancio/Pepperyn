"""
Decision Memory service — Pepperyn.

Objectif : faire suivre le cycle
  Recommandation → décision utilisateur → exécution → feedback → résultat
  → adaptation des prochaines recommandations.

Cette couche est DISTINCTE de la mémoire financière (memory_service.py) :
  - memory_service     → CE QUI A CHANGÉ dans les chiffres (financial_metrics,
                          company_profile).
  - decision_memory_service → CE QUE L'UTILISATEUR A FAIT (ou pas) des
                          recommandations, et POURQUOI.

Principes :
  - Ne modifie JAMAIS `analyse_json` / le rapport (layout figé, ne pas
    toucher). Les recommandations restent des chaînes de texte.
  - Un `recommendation_id` déterministe est calculé à la volée à partir de
    (report_id, source, index) — jamais stocké dans le rapport, seulement
    dans `decision_feedback`.
  - Aucun appel à Claude ici : calculs SQL / Python simples uniquement
    (optimisation des coûts variables).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Identifiants déterministes ──────────────────────────────────────────────

def make_recommendation_id(report_id: str, source: str, index: int) -> str:
    """ID stable et court, dérivé de (report_id, source, index)."""
    raw = f"{report_id}:{source}:{index}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


# ─── Extraction des recommandations d'un rapport ─────────────────────────────

# Ordre de préférence : on n'utilise qu'UNE seule source par rapport (la
# première non vide), pour éviter les doublons entre formats v3/v5/v6.
_RECOMMENDATION_SOURCES: list[tuple[str, str]] = [
    ("plan_action_haute", "haute"),
    ("plan_action_secondaire", "moyenne"),
    ("plan_action", "moyenne"),
]


def extract_recommendations(analyse_json: dict[str, Any], report_id: str) -> list[dict[str, Any]]:
    """
    Extrait une liste plate de recommandations exploitables pour le feedback :
      [{id, text, source, priority, index}, ...]

    `report_id` est utilisé uniquement pour calculer un id déterministe —
    rien n'est écrit dans `analyse_json`.
    """
    if not isinstance(analyse_json, dict):
        return []

    for source, default_priority in _RECOMMENDATION_SOURCES:
        items = analyse_json.get(source) or []
        if not items:
            continue
        results = []
        for i, item in enumerate(items):
            text = str(item).strip()
            if not text:
                continue
            priority = default_priority
            low = text.lower()
            if "priorité haute" in low or "priorité: haute" in low:
                priority = "haute"
            elif "priorité moyenne" in low or "priorité: moyenne" in low:
                priority = "moyenne"
            results.append({
                "id": make_recommendation_id(report_id, source, i),
                "text": text,
                "source": source,
                "priority": priority,
                "index": i,
            })
        if results:
            return results

    # Fallback legacy : recommandations structurées (ancien format)
    legacy = analyse_json.get("recommandations") or []
    results = []
    for i, rec in enumerate(legacy):
        action = (rec.get("action") if isinstance(rec, dict) else None) or ""
        action = str(action).strip()
        if not action:
            continue
        results.append({
            "id": make_recommendation_id(report_id, "recommandations", i),
            "text": action,
            "source": "recommandations",
            "priority": (rec.get("priorite") if isinstance(rec, dict) else None) or "moyenne",
            "index": i,
        })
    return results


# ─── Catégorisation simple par mots-clés (pour Phase 2/3) ────────────────────

_ACTION_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("pricing", ["prix", "tarif", "tarification", "hausse de prix", "augmenter le prix", "pricing"]),
    ("cost_reduction", ["coût", "cout", "charge", "dépense", "depense", "réduire", "reduire", "économie", "economie"]),
    ("revenue_action", ["chiffre d'affaires", "ca ", "vente", "client", "acquisition", "commercial"]),
]


def classify_action(text: str) -> str:
    """Catégorie grossière d'une recommandation (pour les patterns Phase 2)."""
    low = text.lower()
    for category, keywords in _ACTION_CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in low:
                return category
    return "other"


# ─── Service ──────────────────────────────────────────────────────────────────

class DecisionMemoryService:

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

    # ── Lecture : dernier rapport + feedback existant ────────────────────────

    def get_latest_report_with_feedback(self, company_id: str) -> Optional[dict[str, Any]]:
        """
        Renvoie le dernier rapport complété de l'entreprise, avec pour chaque
        recommandation le statut/commentaire déjà enregistré (ou None).

        Format :
          {
            "report_id": "...",
            "fichier_nom": "...",
            "created_at": "...",
            "recommendations": [
              {"id", "text", "source", "priority", "status", "comment"}, ...
            ]
          }
        Renvoie None si aucun rapport ou en cas d'erreur.
        """
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            res = (
                supabase.from_("analyses")
                .select("id, fichier_nom, created_at, analyse_json")
                .eq("company_id", company_id)
                .eq("status", "completed")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if not rows:
                return None
            report = rows[0]
            report_id = report["id"]
            analyse_json = report.get("analyse_json") or {}

            recommendations = extract_recommendations(analyse_json, report_id)
            if not recommendations:
                return None

            # Récupérer le feedback déjà enregistré pour ce rapport
            feedback_map: dict[str, dict[str, Any]] = {}
            try:
                fb_res = (
                    supabase.from_("decision_feedback")
                    .select("recommendation_id, status, comment")
                    .eq("report_id", report_id)
                    .execute()
                )
                for row in fb_res.data or []:
                    feedback_map[row["recommendation_id"]] = row
            except Exception as e:
                logger.warning(f"[DECISION MEMORY] feedback lookup failed: {e}")

            for rec in recommendations:
                fb = feedback_map.get(rec["id"])
                rec["status"] = fb.get("status") if fb else None
                rec["comment"] = fb.get("comment") if fb else None

            return {
                "report_id": report_id,
                "fichier_nom": report.get("fichier_nom"),
                "created_at": report.get("created_at"),
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.warning(f"[DECISION MEMORY] get_latest_report_with_feedback failed: {e}")
            return None

    # ── Écriture : feedback utilisateur ──────────────────────────────────────

    def upsert_feedback(
        self,
        company_id: str,
        report_id: str,
        recommendation_id: str,
        recommendation_text: str,
        recommendation_source: Optional[str],
        status: str,
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Insère ou met à jour le feedback pour (report_id, recommendation_id)."""
        supabase = self._get_supabase()
        if not supabase:
            return False

        row: dict[str, Any] = {
            "company_id": company_id,
            "report_id": report_id,
            "recommendation_id": recommendation_id,
            "recommendation_text": recommendation_text[:2000],
            "recommendation_source": recommendation_source,
            "status": status,
            "comment": (comment or "")[:1000] or None,
        }
        if user_id:
            row["user_id"] = user_id

        try:
            supabase.from_("decision_feedback").upsert(
                row, on_conflict="report_id,recommendation_id"
            ).execute()
            return True
        except Exception as e:
            logger.error(f"[DECISION MEMORY] upsert_feedback failed: {e}")
            return False

    # ── Construction du prompt ───────────────────────────────────────────────

    def build_decision_memory_prompt_section(self, company_id: str) -> str:
        """
        Construit la section MÉMOIRE DÉCISIONNELLE injectée dans le prompt
        Claude (paramètre `actions_section`, déjà supporté par
        `_build_user_prompt_call1`).

        Phase 1 : statuts + commentaires sur les recommandations du dernier
        rapport. Phase 2/3 ajouteront les patterns comportementaux agrégés
        (table `user_patterns`).
        """
        supabase = self._get_supabase()
        if not supabase:
            return ""

        try:
            latest = self.get_latest_report_with_feedback(company_id)
        except Exception as e:
            logger.warning(f"[DECISION MEMORY] build_decision_memory_prompt_section failed: {e}")
            return ""

        lines: list[str] = []

        # Recommandations précédentes + statut + commentaire
        if latest:
            with_feedback = [r for r in latest["recommendations"] if r.get("status")]
            if with_feedback:
                lines.append("═══ MÉMOIRE DÉCISIONNELLE (PRIORITÉ HAUTE) ═══")
                lines.append(
                    "Voici ce que l'utilisateur a indiqué pour les recommandations du "
                    "rapport précédent :"
                )
                status_fr = {
                    "planned": "prévu mais pas encore fait",
                    "done": "FAIT",
                    "partially_done": "partiellement fait",
                    "not_done": "PAS FAIT",
                    "rejected": "REJETÉ par l'utilisateur",
                    "no_longer_relevant": "n'est plus pertinent",
                }
                for r in with_feedback:
                    status_label = status_fr.get(r["status"], r["status"])
                    line = f'  • "{r["text"][:160]}" → {status_label}'
                    if r.get("comment"):
                        line += f' | Raison/commentaire : "{r["comment"][:200]}"'
                    lines.append(line)

                lines.append(
                    "\n→ INSTRUCTION IMPORTANTE : ne répète pas mécaniquement une "
                    "recommandation marquée \"PAS FAIT\" ou \"REJETÉ\". Analyse la "
                    "raison donnée par l'utilisateur et propose une version plus "
                    "réaliste, plus progressive ou mieux adaptée à son contexte. "
                    "Les recommandations marquées \"FAIT\" peuvent être suivies "
                    "d'une action de consolidation, pas répétées à l'identique."
                )

        # Patterns comportementaux (Phase 2+) — inclus dès que disponibles
        try:
            patterns_res = (
                supabase.from_("user_patterns")
                .select("*")
                .eq("company_id", company_id)
                .limit(1)
                .execute()
            )
            patterns_rows = patterns_res.data or []
        except Exception:
            patterns_rows = []

        if patterns_rows:
            p = patterns_rows[0]
            pattern_lines = []
            if p.get("execution_rate") is not None:
                pattern_lines.append(f"  • Taux d'exécution global des recommandations : {p['execution_rate']}%")
            if p.get("pricing_resistance_score") is not None:
                pattern_lines.append(f"  • Résistance aux hausses tarifaires : {p['pricing_resistance_score']}/100")
            if p.get("cost_reduction_execution_rate") is not None:
                pattern_lines.append(f"  • Taux d'exécution des actions de réduction de coûts : {p['cost_reduction_execution_rate']}%")
            if p.get("preferred_action_type"):
                pattern_lines.append(f"  • Type d'action le plus souvent mis en œuvre : {p['preferred_action_type']}")
            recurring = p.get("recurring_blockers") or []
            if recurring:
                pattern_lines.append(f"  • Blocages récurrents évoqués : {', '.join(str(b) for b in recurring[:5])}")

            if pattern_lines:
                if not lines:
                    lines.append("═══ MÉMOIRE DÉCISIONNELLE (PRIORITÉ HAUTE) ═══")
                lines.append("\n📊 PROFIL COMPORTEMENTAL DE L'UTILISATEUR :")
                lines.extend(pattern_lines)
                lines.append(
                    "  → Adapte le ton et la nature des prochaines recommandations "
                    "en fonction de ce profil."
                )

        if not lines:
            return ""

        lines.append("═══ FIN MÉMOIRE DÉCISIONNELLE ═══\n")
        return "\n".join(lines)
