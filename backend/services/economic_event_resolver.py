"""
economic_event_resolver.py — Résolveur d'événements économiques (Phase 4B)

Responsabilité unique :
  Résoudre (créer ou identifier) un EconomicEvent à partir d'une liste de
  QuantifiedImpacts et d'un contexte d'extraction LLM.

RÈGLES ABSOLUES :
  1. Le LLM propose une event_category et une correspondance potentielle.
     Il NE génère JAMAIS l'event_id directement.
  2. L'event_id est TOUJOURS calculé de façon déterministe via build_event_hash().
  3. Aucune persistence DB en Phase 4B.
  4. Aucune liaison EconomicEvent ↔ DecisionArc en Phase 4B.

Usage :
    resolver = EconomicEventResolver(company_id="optilux")
    event = resolver.resolve(
        impact=qi,
        event_category="BILLING_DELAY",
        source_fact_ids=["fact_001"],
        period="Sep 2019",
        entity=None,
    )
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from models.financial_truth import (
    EconomicEvent,
    EconomicEventStatus,
    MetricType,
    QuantifiedImpact,
    VALID_EVENT_CATEGORIES,
    build_event_hash,
    normalize_period,
)

logger = logging.getLogger(__name__)


class EconomicEventResolver:
    """
    Résolveur hybride (déterministe + LLM sémantique).

    Maintient un registre in-memory des événements résolus pour la durée
    d'une analyse. Le registre est vidé entre les analyses.
    """

    def __init__(self, company_id: str):
        self.company_id = company_id
        self._registry: dict[str, EconomicEvent] = {}  # event_id → EconomicEvent

    def resolve(
        self,
        impact: QuantifiedImpact,
        event_category: str,
        source_fact_ids: Optional[list[str]] = None,
        period: Optional[str] = None,
        entity: Optional[str] = None,
    ) -> EconomicEvent:
        """
        Résout ou crée un EconomicEvent pour l'impact donné.

        Si un event avec le même hash existe déjà dans le registre, retourne
        l'événement existant (sans modification). Sinon, crée un nouvel événement.

        Args:
            impact: Le QuantifiedImpact à lier à l'événement.
            event_category: Catégorie normalisée (ex: "BILLING_DELAY").
                           Si invalide, remplacée par "OTHER".
            source_fact_ids: IDs des faits Evidence Graph sources.
            period: Période de l'impact (ex: "Sep 2019").
            entity: Entité concernée (compte, département…) ou None.

        Returns:
            EconomicEvent existant ou nouvellement créé.
        """
        # Normalisation de la catégorie
        category = self._validate_category(event_category)

        # Résolution de la période depuis l'impact si absente
        effective_period = period or impact.source_period or "UNKNOWN"

        # IDs sources
        fact_ids = source_fact_ids or []

        # Calcul du hash déterministe
        event_id = build_event_hash(
            company_id=self.company_id,
            metric_type=impact.metric_type,
            source_fact_ids=fact_ids,
            period=effective_period,
            entity=entity,
            event_category=category,
        )

        # Mise à jour du economic_event_id sur l'impact (mutation légère)
        if impact.economic_event_id is None:
            impact.economic_event_id = event_id

        # Retour de l'événement existant si déjà dans le registre
        if event_id in self._registry:
            logger.debug(f"[resolver] Event cache hit: {event_id} ({category})")
            return self._registry[event_id]

        # Création d'un nouvel événement
        now = datetime.now(timezone.utc).isoformat()
        event = EconomicEvent(
            event_id=event_id,
            event_category=category,
            company_id=self.company_id,
            metric_type=impact.metric_type,
            period=normalize_period(effective_period),
            entity=entity,
            identified_exposure=impact,
            status=EconomicEventStatus.IDENTIFIED,
            source_fact_ids=list(fact_ids),
            created_at=now,
            updated_at=now,
        )
        self._registry[event_id] = event
        logger.debug(f"[resolver] Created event: {event_id} ({category}, {impact.metric_type.value})")
        return event

    def find_by_id(self, event_id: str) -> Optional[EconomicEvent]:
        """Recherche un événement par son ID dans le registre."""
        return self._registry.get(event_id)

    def find_similar(
        self,
        metric_type: MetricType,
        period: str,
        entity: Optional[str] = None,
    ) -> list[EconomicEvent]:
        """
        Trouve les événements du même type métrique et de la même période.
        Utilisé par le LLM pour proposer des correspondances.
        """
        normalized = normalize_period(period)
        return [
            ev for ev in self._registry.values()
            if (ev.metric_type == metric_type
                and ev.period == normalized
                and (entity is None or ev.entity == entity))
        ]

    def all_events(self) -> list[EconomicEvent]:
        """Retourne tous les événements du registre courant."""
        return list(self._registry.values())

    def clear(self) -> None:
        """Vide le registre (entre deux analyses)."""
        self._registry.clear()

    def _validate_category(self, category: str) -> str:
        """Retourne la catégorie normalisée, ou 'OTHER' si invalide."""
        normalized = (category or "OTHER").strip().upper()
        if normalized not in VALID_EVENT_CATEGORIES:
            logger.warning(
                f"[resolver] Invalid event_category '{category}', using 'OTHER'"
            )
            return "OTHER"
        return normalized

    def summary(self) -> dict:
        """Résumé du registre (pour logging et tests)."""
        return {
            "company_id": self.company_id,
            "total_events": len(self._registry),
            "by_category": _count_by(self._registry.values(), lambda e: e.event_category),
            "by_status": _count_by(self._registry.values(), lambda e: e.status.value),
            "by_metric": _count_by(self._registry.values(), lambda e: e.metric_type.value),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count_by(items, key_fn) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        k = key_fn(item)
        result[k] = result.get(k, 0) + 1
    return result


def resolve_simulation_metric(
    impacts: list[QuantifiedImpact],
    ebitda_base: Optional[float] = None,
) -> "SimulationMetricResult":  # noqa: F821
    """
    Résolveur de métrique homogène pour la simulation consolidée (J.1).

    Algoritme (priorité stricte) :
    1. Si EBITDA disponible ET impacts compatibles → metric=EBITDA
    2. Si métrique unique (hors UNKNOWN/EXPOSURE) → metric=cette métrique
    3. Sinon → metric=None (pas de simulation consolidée)

    Note : Appelé par Phase 4C (CostOfInactionV2). En Phase 4B, présent pour
    validation uniquement — ne modifie aucun livrable de production.
    """
    from models.financial_truth import (
        ImpactNature,
        MetricType,
        SimulationMetricResult,
    )

    _EBITDA_COMPATIBLE = frozenset({MetricType.EBITDA, MetricType.COST, MetricType.COST_SAVING})

    recurring = [i for i in impacts if not i.is_unresolved()
                 and i.nature in (ImpactNature.RECURRING, ImpactNature.STRUCTURAL)]

    if not recurring:
        return SimulationMetricResult(
            metric=None,
            reason="Aucun impact récurrent non-résolu disponible",
        )

    # Étape 1 — EBITDA disponible ?
    if ebitda_base is not None:
        ebitda_compatible = [
            i for i in recurring
            if i.metric_type in _EBITDA_COMPATIBLE
        ]
        revenue_with_gm = [
            i for i in recurring
            if (i.metric_type == MetricType.REVENUE
                and i.gross_margin is not None
                and i.gross_margin.rate is not None)
        ]
        integrable = ebitda_compatible + revenue_with_gm
        unconvertible = [i for i in recurring if i not in integrable]

        if integrable:
            reason_parts = [f"EBITDA disponible, {len(integrable)} impact(s) compatible(s)"]
            if unconvertible:
                reason_parts.append(
                    f"{len(unconvertible)} impact(s) non convertis affichés séparément"
                )
            conv = None
            if revenue_with_gm:
                conv = revenue_with_gm[0].gross_margin
            return SimulationMetricResult(
                metric=MetricType.EBITDA,
                reason=" — ".join(reason_parts),
                unconvertible=unconvertible,
                conversion_used=conv,
            )

    # Étape 2 — Métrique unique ?
    metric_types = {i.metric_type for i in recurring
                    if i.metric_type not in (MetricType.UNKNOWN, MetricType.EXPOSURE)}
    if len(metric_types) == 1:
        unique = next(iter(metric_types))
        return SimulationMetricResult(
            metric=unique,
            reason=f"Métrique unique {unique.value} — EBITDA non disponible",
        )

    # Étape 3 — Hétérogène
    types_str = ", ".join(sorted(t.value for t in metric_types)) or "UNKNOWN"
    return SimulationMetricResult(
        metric=None,
        reason=f"Métriques hétérogènes ({types_str}) sans conversion possible",
        unconvertible=list(recurring),
    )
