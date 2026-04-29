"""
Memory service — Pepperyn v4 (mémoire persistante structurée).

Architecture :
  1. financial_metrics  : métriques extraites de chaque analyse (table dédiée)
  2. company_profile    : profil évolutif de l'entreprise (1 ligne par company)
  3. Prompt enrichi     : tendances, profil, historique, problèmes récurrents

Flux :
  Après chaque analyse → save_analysis_memory()
    → insert financial_metrics
    → upsert company_profile (tendances recalculées)

  Avant chaque analyse → get_memory_context() + build_memory_prompt_section()
    → requête financial_metrics (6 dernières)
    → requête company_profile
    → section MÉMOIRE injectée dans le prompt Claude
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _safe_float(value: Any) -> Optional[float]:
    """Convertit en float sans planter."""
    try:
        if value is None:
            return None
        return float(str(value).replace(",", ".").replace(" ", "").replace(" ", ""))
    except (ValueError, TypeError):
        return None


def _extract_metrics(analyse_json: dict) -> dict:
    """
    Extrait les métriques numériques d'un analyse_json.
    Supporte le format v3 (diagnostics textuels) et le format legacy (objets).
    """
    revenue = None
    costs = None
    margin_pct = None
    gross_margin_pct = None

    # Format legacy : objets structurés
    rev_obj = analyse_json.get("revenus") or {}
    if isinstance(rev_obj, dict):
        revenue = _safe_float(rev_obj.get("total"))

    cout_obj = analyse_json.get("couts") or {}
    if isinstance(cout_obj, dict):
        costs = _safe_float(cout_obj.get("total"))

    marge_obj = analyse_json.get("marges") or {}
    if isinstance(marge_obj, dict):
        margin_pct = _safe_float(marge_obj.get("nette_pct") or marge_obj.get("brute_pct"))
        gross_margin_pct = _safe_float(marge_obj.get("brute_pct"))

    return {
        "revenue": revenue,
        "costs": costs,
        "margin_pct": margin_pct,
        "gross_margin_pct": gross_margin_pct,
    }


def _compute_trend(values: list) -> str:
    """
    Calcule une tendance à partir d'une liste de valeurs (la plus récente en premier).
    Retourne 'improving', 'declining' ou 'stable'.
    """
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return "stable"
    recent = sum(clean[:2]) / len(clean[:2])
    older_vals = clean[2:4] if len(clean) > 2 else [clean[-1]]
    older = sum(older_vals) / len(older_vals)
    if older == 0:
        return "stable"
    delta_pct = (recent - older) / abs(older) * 100
    if delta_pct > 3:
        return "improving"
    if delta_pct < -3:
        return "declining"
    return "stable"


def _count_recurring(items_lists: list, threshold: int = 2) -> list:
    """
    Trouve les éléments qui reviennent dans plusieurs listes.
    """
    from collections import Counter
    all_items: list = []
    for lst in items_lists:
        if isinstance(lst, list):
            all_items.extend([str(x)[:120] for x in lst])
    counts = Counter(all_items)
    return [item for item, count in counts.most_common(5) if count >= threshold]


# ─── Service ────────────────────────────────────────────────────────────────

class MemoryService:

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

    # ── Sauvegarde après analyse ─────────────────────────────────────────────

    def save_analysis_memory(
        self,
        company_id: str,
        analyse_id: str,
        analyse_json: dict,
    ) -> None:
        """
        Appelé après chaque analyse réussie.
        1. Insère les métriques dans financial_metrics
        2. Met à jour company_profile avec les nouvelles tendances
        """
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            self._save_financial_metrics(supabase, company_id, analyse_id, analyse_json)
        except Exception as e:
            logger.warning(f"[MEMORY] save_financial_metrics failed: {e}")

        try:
            self._update_company_profile(supabase, company_id)
        except Exception as e:
            logger.warning(f"[MEMORY] update_company_profile failed: {e}")

    def _save_financial_metrics(
        self, supabase, company_id: str, analyse_id: str, analyse_json: dict
    ) -> None:
        """Insère une ligne dans financial_metrics."""
        metrics = _extract_metrics(analyse_json)

        row: dict = {
            "company_id": company_id,
            "analyse_id": analyse_id,
            "document_type": analyse_json.get("type_document"),
            "decision": (analyse_json.get("decision") or "")[:500] or None,
            "problemes": analyse_json.get("problemes_critiques") or [],
            "opportunites": analyse_json.get("opportunites_v3") or [],
            "plan_action": analyse_json.get("plan_action") or [],
            "score_rentabilite": analyse_json.get("score_rentabilite"),
            "score_risque": analyse_json.get("score_risque"),
            "score_structure": analyse_json.get("score_structure"),
        }
        # Ajouter les métriques numériques seulement si présentes
        for k, v in metrics.items():
            if v is not None:
                row[k] = v

        supabase.from_("financial_metrics").insert(row).execute()
        logger.info(f"[MEMORY] Métriques sauvegardées pour analyse {analyse_id}")

    def _update_company_profile(self, supabase, company_id: str) -> None:
        """
        Recalcule et upsert le profil de l'entreprise à partir des 10 dernières métriques.
        """
        result = (
            supabase.from_("financial_metrics")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return

        # Tendances
        margin_trend = _compute_trend([r.get("margin_pct") for r in rows])
        revenue_trend = _compute_trend([r.get("revenue") for r in rows])

        # Scores moyens
        scores_r = [r["score_rentabilite"] for r in rows if r.get("score_rentabilite")]
        scores_ri = [r["score_risque"] for r in rows if r.get("score_risque")]
        avg_rentabilite = round(sum(scores_r) / len(scores_r), 2) if scores_r else None
        avg_risque = round(sum(scores_ri) / len(scores_ri), 2) if scores_ri else None

        # Problèmes récurrents et points forts
        all_problems = [r.get("problemes") or [] for r in rows]
        all_opps = [r.get("opportunites") or [] for r in rows]
        recurring_problems = _count_recurring(all_problems, threshold=2)
        strengths = _count_recurring(all_opps, threshold=2)

        # Actions en attente = plan_action de la dernière analyse
        pending_actions = (rows[0].get("plan_action") or [])[:5]

        # Résumé narratif
        trend_fr = {"improving": "en amélioration", "declining": "en déclin", "stable": "stable"}
        rev_fr = {"improving": "en hausse", "declining": "en baisse", "stable": "stable"}
        last_decision = rows[0].get("decision") or ""
        summary = (
            f"Entreprise analysée {len(rows)} fois. "
            f"Marge {trend_fr.get(margin_trend, 'stable')}. "
            f"Chiffre d'affaires {rev_fr.get(revenue_trend, 'stable')}."
        )
        if last_decision:
            summary += f" Dernière recommandation : {last_decision[:150]}."

        profile_row = {
            "company_id": company_id,
            "margin_trend": margin_trend,
            "revenue_trend": revenue_trend,
            "avg_score_rentabilite": avg_rentabilite,
            "avg_score_risque": avg_risque,
            "recurring_problems": recurring_problems,
            "pending_actions": pending_actions,
            "strengths": strengths,
            "total_analyses": len(rows),
            "last_analysis_at": rows[0].get("created_at"),
            "financial_summary": summary,
        }

        supabase.from_("company_profile").upsert(
            profile_row, on_conflict="company_id"
        ).execute()
        logger.info(f"[MEMORY] Profil entreprise mis à jour pour {company_id}")

    # ── Récupération avant analyse ───────────────────────────────────────────

    def get_memory_context(self, company_id: str) -> dict:
        """
        Récupère le contexte mémoire complet :
          - 6 dernières métriques (financial_metrics)
          - profil de l'entreprise (company_profile)
        Retourne un dict {metrics: [...], profile: {...}} ou {} si erreur.
        """
        supabase = self._get_supabase()
        if not supabase:
            return {}

        metrics: list = []
        profile: dict = {}

        try:
            metrics_result = (
                supabase.from_("financial_metrics")
                .select("*")
                .eq("company_id", company_id)
                .order("created_at", desc=True)
                .limit(6)
                .execute()
            )
            metrics = metrics_result.data or []
        except Exception as e:
            logger.warning(f"[MEMORY] get metrics failed: {e}")

        try:
            profile_result = (
                supabase.from_("company_profile")
                .select("*")
                .eq("company_id", company_id)
                .limit(1)
                .execute()
            )
            rows = profile_result.data or []
            profile = rows[0] if rows else {}
        except Exception as e:
            logger.warning(f"[MEMORY] get profile failed: {e}")

        return {"metrics": metrics, "profile": profile}

    # ── Construction du prompt ───────────────────────────────────────────────

    def build_memory_prompt_section(self, context: Any) -> str:
        """
        Construit la section MÉMOIRE ENTREPRISE injectée dans le prompt Claude.
        Accepte aussi bien un dict {metrics, profile} qu'une liste (rétrocompat).
        """
        # Rétrocompatibilité : ancienne signature passait une liste
        if isinstance(context, list):
            if not context:
                return ""
            # Ancien format — on fait le minimum
            lines = ["HISTORIQUE (TRÈS IMPORTANT)", "Analyses précédentes :"]
            for i, m in enumerate(context[:3]):
                aj = m.get("analyse_json") or {}
                date = m.get("created_at", "")[:10]
                decision = aj.get("decision") or ""
                lines.append(f"- N-{i+1} ({date}) : {decision[:80]}")
            return "\n".join(lines)

        if not isinstance(context, dict) or (not context.get("metrics") and not context.get("profile")):
            return ""

        metrics: list = context.get("metrics") or []
        profile: dict = context.get("profile") or {}

        lines = ["═══ MÉMOIRE ENTREPRISE (PRIORITÉ HAUTE) ═══"]

        # Profil global
        if profile:
            lines.append("\n📊 PROFIL FINANCIER DE L'ENTREPRISE :")
            total = profile.get("total_analyses", 0)
            lines.append(f"  • {total} analyse(s) réalisée(s) avec Pepperyn")
            if profile.get("financial_summary"):
                lines.append(f"  • {profile['financial_summary']}")
            m_trend = profile.get("margin_trend", "stable")
            r_trend = profile.get("revenue_trend", "stable")
            icons = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            lines.append(
                f"  • Marge : {icons.get(m_trend)} {m_trend} | "
                f"CA : {icons.get(r_trend)} {r_trend}"
            )
            if profile.get("avg_score_rentabilite"):
                lines.append(f"  • Score rentabilité moyen : {profile['avg_score_rentabilite']}/10")

        # Problèmes récurrents
        recurring = profile.get("recurring_problems") or []
        if recurring:
            lines.append("\n⚠️ PROBLÈMES RÉCURRENTS (non résolus) :")
            for p in recurring[:4]:
                lines.append(f"  • {p}")
            lines.append(
                "  → Insiste sur leur persistance. "
                "Évalue si des progrès ont été réalisés."
            )

        # Actions en attente
        pending = profile.get("pending_actions") or []
        if pending:
            lines.append("\n✅ ACTIONS RECOMMANDÉES PRÉCÉDEMMENT :")
            for a in pending[:3]:
                lines.append(f"  • {a}")
            lines.append("  → Évalue si ces actions ont été mises en place.")

        # Historique chiffré
        if metrics:
            lines.append(f"\n📁 HISTORIQUE CHIFFRÉ ({len(metrics)} analyses) :")
            for i, m in enumerate(metrics):
                date = (m.get("created_at") or "")[:10]
                parts = [f"  • N-{i+1} ({date})"]
                if m.get("revenue"):
                    parts.append(f"CA: {float(m['revenue']):,.0f}€")
                if m.get("costs"):
                    parts.append(f"Coûts: {float(m['costs']):,.0f}€")
                if m.get("margin_pct") is not None:
                    parts.append(f"Marge: {float(m['margin_pct']):.1f}%")
                if m.get("score_rentabilite"):
                    parts.append(f"Score: {m['score_rentabilite']}/10")
                if m.get("decision"):
                    parts.append(f"→ \"{str(m['decision'])[:80]}\"")
                lines.append(" | ".join(parts))

        lines.append("═══ FIN MÉMOIRE ═══\n")
        return "\n".join(lines)

    # ── Memory Insight affiché à l'utilisateur ───────────────────────────────

    def build_memory_insight(
        self,
        current: dict,
        context: Any,
    ) -> Optional[str]:
        """
        Génère le bloc affiché dans l'interface après une analyse.
        Accepte un dict {metrics, profile} ou une liste (rétrocompat).
        """
        # Rétrocompatibilité
        if isinstance(context, list):
            previous = context
            if not previous:
                return None
            insights = []
            prev_analyses = [m.get("analyse_json") or {} for m in previous]
            all_probs: list = []
            for pa in prev_analyses:
                all_probs.extend(pa.get("problemes_critiques") or [])
            cost_count = sum(1 for p in all_probs if any(
                kw in p.lower() for kw in ["coût", "charge", "dépense"]
            ))
            if cost_count >= 2:
                insights.append("⚠️ Le contrôle des coûts est un problème récurrent.")
            prev_decision = prev_analyses[0].get("decision") or ""
            if prev_decision:
                insights.append(f"Analyse précédente : \"{prev_decision[:80]}\"")
            return "\n".join(insights) if insights else None

        metrics = (context or {}).get("metrics") or []
        profile = (context or {}).get("profile") or {}
        if not metrics and not profile:
            return None

        insights = []

        m_trend = profile.get("margin_trend")
        if m_trend == "declining":
            insights.append("📉 Votre marge est en déclin depuis plusieurs analyses.")
        elif m_trend == "improving":
            insights.append("📈 Votre marge s'améliore — continuez sur cette lancée.")

        if profile.get("revenue_trend") == "declining":
            insights.append("📉 Votre chiffre d'affaires est en baisse sur les dernières analyses.")

        recurring = profile.get("recurring_problems") or []
        if recurring:
            insights.append(f"⚠️ Problème récurrent : \"{recurring[0][:80]}\"")

        if metrics:
            prev_decision = metrics[0].get("decision") or ""
            if prev_decision:
                insights.append(
                    f"Analyse précédente : \"{prev_decision[:80]}"
                    f"{'...' if len(prev_decision) > 80 else ''}\""
                )

        return "\n".join(insights) if insights else None
