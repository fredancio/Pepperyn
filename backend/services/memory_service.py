"""
Memory service — Pepperyn v3.

3 types de mémoire :
  1. Mémoire financière  : historique des métriques clés (revenus, coûts, marges)
  2. Mémoire stratégique : décisions prises par l'utilisateur
  3. Mémoire utilisateur : profil business (depuis le register)

Stockage : table `analyses` dans Supabase (champ analyse_json).
Récupère les N=3 dernières analyses pour enrichir le prompt.
"""
import os
from typing import Any, Optional


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

    # ─── Récupération ────────────────────────────────────────────────────────

    def get_memory_context(self, company_id: str) -> list[dict[str, Any]]:
        """
        Récupère les 3 dernières analyses complètes pour enrichir le prompt.
        Retourne une liste vide si pas d'historique ou erreur.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            result = (
                supabase.from_("analyses")
                .select("analyse_json, created_at, fichier_nom")
                .eq("company_id", company_id)
                .eq("status", "completed")
                .order("created_at", desc=True)
                .limit(3)
                .execute()
            )
            return result.data or []
        except Exception:
            return []

    # ─── Construction du prompt ───────────────────────────────────────────────

    def build_memory_prompt_section(self, memory_context: list[dict[str, Any]]) -> str:
        """
        Construit la section HISTORIQUE du user prompt.
        Retourne une chaîne vide si pas d'historique.
        """
        if not memory_context:
            return ""

        lines = [
            "HISTORIQUE (TRÈS IMPORTANT)",
            "Voici les analyses précédentes de cette entreprise :",
        ]
        for i, m in enumerate(memory_context):
            n = i + 1
            aj = m.get("analyse_json") or {}
            date = m.get("created_at", "")[:10]

            # Extraire les métriques selon le format (v3 ou legacy)
            revenus = (
                aj.get("diagnostic_revenus")
                or (aj.get("revenus") or {}).get("total")
                or "N/A"
            )
            couts = (
                aj.get("diagnostic_couts")
                or (aj.get("couts") or {}).get("total")
                or "N/A"
            )
            marge = (
                aj.get("diagnostic_marges")
                or (aj.get("marges") or {}).get("brute_pct")
                or "N/A"
            )
            decision = aj.get("decision") or aj.get("synthese") or ""

            line = f"- Analyse N-{n} ({date}) : Revenus: {revenus}, Coûts: {couts}, Marge: {marge}"
            if decision:
                line += f" | Décision: {decision[:80]}..."
            lines.append(line)

        lines.append("")
        return "\n".join(lines)

    def build_actions_section(self, memory_context: list[dict[str, Any]]) -> str:
        """
        Construit la section ACTIONS UTILISATEUR du prompt.
        Extrait les décisions passées et leur statut.
        """
        if not memory_context:
            return ""

        decisions = []
        for m in memory_context:
            aj = m.get("analyse_json") or {}
            decision = aj.get("decision")
            if decision:
                decisions.append(f"- {decision[:100]}")

        if not decisions:
            return ""

        return "ACTIONS UTILISATEUR\nDécisions récentes :\n" + "\n".join(decisions[:3])

    # ─── Sauvegarde ───────────────────────────────────────────────────────────

    def save_analysis_memory(self, company_id: str, analyse_json: dict[str, Any]) -> None:
        """
        Met à jour la dernière analyse avec les métriques extraites.
        Appelé après chaque analyse réussie.
        """
        # La sauvegarde principale est déjà faite par _save_to_db dans analyze.py.
        # Cette méthode peut être utilisée pour des enrichissements futurs
        # (ex: table memory dédiée, extraction de métriques structurées).
        pass

    # ─── Memory Insight ───────────────────────────────────────────────────────

    def build_memory_insight(
        self,
        current: dict[str, Any],
        previous: list[dict[str, Any]],
    ) -> Optional[str]:
        """
        Génère le bloc "CE QUI A CHANGÉ" affiché dans AnalysisResult.
        Compare les métriques de l'analyse actuelle avec les précédentes.
        Retourne None si pas de changements significatifs à signaler.
        """
        if not previous:
            return None

        insights = []

        # Extraire métriques actuelles
        curr_decision = current.get("decision") or current.get("synthese") or ""
        curr_problemes = current.get("problemes_critiques") or []

        # Analyser les tendances sur N analyses précédentes
        prev_analyses = [m.get("analyse_json") or {} for m in previous]

        # Détecter tendances récurrentes dans les problèmes
        all_prev_problemes: list[str] = []
        for pa in prev_analyses:
            all_prev_problemes.extend(pa.get("problemes_critiques") or [])

        # Mots-clés récurrents (coûts, marge, etc.)
        cost_keywords = ["coût", "charge", "dépense", "cost"]
        margin_keywords = ["marge", "margin", "rentabilité"]

        cost_count = sum(
            1 for p in all_prev_problemes
            if any(kw in p.lower() for kw in cost_keywords)
        )
        margin_count = sum(
            1 for p in all_prev_problemes
            if any(kw in p.lower() for kw in margin_keywords)
        )

        if cost_count >= 2:
            insights.append("⚠️ Le contrôle des coûts est votre problème récurrent depuis plusieurs analyses.")

        if margin_count >= 2:
            insights.append("⚠️ Votre marge baisse depuis plusieurs analyses consécutives.")

        # Comparer le nombre d'analyses total
        n_analyses = len(previous)
        if n_analyses >= 1:
            prev_decision = prev_analyses[0].get("decision") or ""
            if prev_decision and curr_decision and len(curr_decision) > 20:
                insights.append(
                    f"Analyse précédente : \"{prev_decision[:80]}{'...' if len(prev_decision) > 80 else ''}\""
                )

        if not insights:
            return None

        return "\n".join(insights)
