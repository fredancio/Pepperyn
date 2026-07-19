"""
financial_truth.py — Canonical Financial Truth Layer (Phase 4B)

Source de vérité financière structurée de Pepperyn.
Ce module est la fondation du Financial Truth Layer :
  QuantifiedImpact, EconomicEvent, et leurs types associés.

RÈGLES ABSOLUES :
  1. UNKNOWN ≠ 0. Toute donnée absente reste None.
  2. Les méthodes de calcul ne font JAMAIS de fallback vers 0 quand la donnée est absente.
  3. Ce module est pur Python — aucune dépendance vers des services.
  4. Les renderers de production (PDF/PPTX/Excel) NE lisent PAS ce module en Phase 4B.
     Ils continuent d'utiliser annual_impact (champ legacy conservé).
  5. quantified_impact coexiste avec annual_impact sur les mêmes modèles.
     Le renderer choisit: if quantified_impact is not None → utiliser quantified_impact (Phase 4C+)
                          else → fallback annual_impact (Phase 4B comportement inchangé)

Corresponds to Design V3 FINAL — Sections A, B, C, D, E, F, G, H.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enums — dimensions orthogonales
# ─────────────────────────────────────────────────────────────────────────────

class MetricType(str, Enum):
    """Type de métrique financière — dimension 1 de QuantifiedImpact."""
    REVENUE         = "REVENUE"
    GROSS_MARGIN    = "GROSS_MARGIN"
    EBITDA          = "EBITDA"
    NET_PROFIT      = "NET_PROFIT"
    CASH            = "CASH"
    COST            = "COST"
    COST_SAVING     = "COST_SAVING"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    EXPOSURE        = "EXPOSURE"
    UNKNOWN         = "UNKNOWN"


class PeriodBasis(str, Enum):
    """Base temporelle de l'impact — dimension 2 de QuantifiedImpact."""
    POINT_IN_TIME = "POINT_IN_TIME"   # Montant one-shot, non annualisable
    MONTHLY       = "MONTHLY"
    QUARTERLY     = "QUARTERLY"
    YTD           = "YTD"
    ANNUAL        = "ANNUAL"
    ANNUALIZED    = "ANNUALIZED"      # YTD extrapolé avec AnnualizationMetadata
    UNKNOWN       = "UNKNOWN"


class ImpactNature(str, Enum):
    """Nature de l'impact dans le temps — dimension 3 de QuantifiedImpact."""
    ONE_TIME    = "ONE_TIME"     # Ponctuel — ne se répète pas
    RECURRING   = "RECURRING"   # Récurrent — se répète chaque période
    STRUCTURAL  = "STRUCTURAL"  # Structurel — changement permanent du modèle économique
    UNKNOWN     = "UNKNOWN"


class AnnualizationQuality(str, Enum):
    """
    Qualité de l'annualisation.

    CERTIFIED  : remplit les conditions minimales (≥6 mois mensuels / ≥2 trimestres).
                 Contribue à recurring_annual_exposure.
    RUN_RATE   : calculable mais conditions non atteintes (ex: 4 mois seulement).
                 Affiché "ESTIMATION RUN-RATE". Ne contribue PAS aux totaux certifiés.
    REFUSED    : annualisation impossible (ONE_TIME, saisonnalité, POINT_IN_TIME).
                 Montant brut conservé.
    """
    CERTIFIED = "CERTIFIED"
    RUN_RATE  = "RUN_RATE"
    REFUSED   = "REFUSED"


class GrossMarginSource(str, Enum):
    """
    Source du taux de marge brute (hiérarchie stricte J.4).
    La priorité décroissante est encodée dans la valeur ordinal (ordre de déclaration).
    """
    EXPLICIT_FILE   = "EXPLICIT_FILE"    # 1. Fourni explicitement dans la source
    CANONICAL_FACTS = "CANONICAL_FACTS"  # 2. Calculé depuis Canonical Financial Facts
    USER_HYPOTHESIS = "USER_HYPOTHESIS"  # 3. Hypothèse utilisateur validée
    LLM_EXTRACTED   = "LLM_EXTRACTED"   # 4. Extrait LLM + source_quote fourni
    UNKNOWN         = "UNKNOWN"          # 5. Non disponible → REVENUE reste REVENUE


class EconomicEventStatus(str, Enum):
    IDENTIFIED          = "IDENTIFIED"           # Exposition identifiée, pas de décision
    ADDRESSED           = "ADDRESSED"            # Décision prise (impact attendu)
    PENDING_OBSERVATION = "PENDING_OBSERVATION"  # Arc ouvert, en attente
    CLOSED_RESOLVED     = "CLOSED_RESOLVED"      # Résolu (residual ≈ 0)
    CLOSED_PARTIAL      = "CLOSED_PARTIAL"       # Résolution partielle
    CLOSED_UNRESOLVED   = "CLOSED_UNRESOLVED"    # Non résolu


class SourceType(str, Enum):
    """
    Type de provenance d'une référence source dans QuantifiedImpact.

    CANONICAL_FACT           : fait extrait et validé depuis l'Evidence Graph.
    LEGACY_PARSE             : montant injecté depuis parse_amount_eur() (Phase 4B fallback).
                               Ne doit jamais être confondu avec une extraction V3 certifiée.
    LLM_EXTRACTED            : classification extraite par le LLM (metric_type, etc.).
    USER_PROVIDED            : donnée saisie ou validée explicitement par l'utilisateur.
    DETERMINISTIC_CALCULATION: valeur calculée de façon déterministe (ex: monthly = annual / 12).
    """
    CANONICAL_FACT            = "CANONICAL_FACT"
    LEGACY_PARSE              = "LEGACY_PARSE"
    LLM_EXTRACTED             = "LLM_EXTRACTED"
    USER_PROVIDED             = "USER_PROVIDED"
    DETERMINISTIC_CALCULATION = "DETERMINISTIC_CALCULATION"


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses de composition
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnnualizationMetadata:
    """Métadonnées d'annualisation — requis si period_basis = ANNUALIZED."""
    periods_elapsed:        int                   # Mois calendaires écoulés (JAMAIS mois non nuls)
    periods_per_year:       int                   # 12 (mensuel) ou 4 (trimestriel)
    quality:                AnnualizationQuality
    annualization_method:   str                   # Ex: "amount / periods_elapsed * periods_per_year"
    is_extrapolated:        bool = True
    seasonality_flag:       bool = False
    non_annualization_reason: Optional[str] = None  # Si quality = REFUSED


@dataclass
class GrossMarginResolution:
    """Résolution du taux de marge brute (hiérarchie J.4)."""
    rate:   Optional[float]   # 0.0–1.0, ou None si source=UNKNOWN
    source: GrossMarginSource


@dataclass
class SourceReference:
    """
    Provenance d'un QuantifiedImpact.
    Au moins fact_id OU (sheet + row_label + period) requis pour contribution certifiée.

    source_type distingue la provenance technique :
      CANONICAL_FACT  → preuve certifiable
      LEGACY_PARSE    → montant injécté depuis parse_amount_eur() (Phase 4B fallback,
                        jamais certifié)
      LLM_EXTRACTED   → classification LLM (metric_type, period_basis, nature)
    """
    fact_id:        Optional[str]        = None   # ID dans l'Evidence Graph
    sheet:          Optional[str]        = None   # Feuille source ("P&L")
    row_label:      Optional[str]        = None   # Label de ligne ("Code 70 - CA")
    period:         Optional[str]        = None   # Période exacte ("Sep 2019")
    observed_value: Optional[float]      = None   # Valeur brute observée
    source_quote:   Optional[str]        = None   # Citation LLM (jamais preuve unique)
    source_type:    Optional[SourceType] = None   # Provenance technique contrôlée

    def is_anchored(self) -> bool:
        """True si la référence est suffisamment ancrée pour contribution certifiée.
        Un LEGACY_PARSE n'est jamais ancré, même avec fact_id=None."""
        if self.source_type == SourceType.LEGACY_PARSE:
            return False
        has_fact_id = self.fact_id is not None
        has_minimal = (
            self.sheet is not None
            and self.row_label is not None
            and self.period is not None
        )
        return has_fact_id or has_minimal


# ─────────────────────────────────────────────────────────────────────────────
# QuantifiedImpact V3 — modèle central
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QuantifiedImpact:
    """
    Représentation canonique d'un impact financier.

    Trois dimensions orthogonales :
      metric_type  : ce qui est mesuré (EBITDA, REVENUE, COST, …)
      period_basis : comment c'est mesuré (ANNUAL, MONTHLY, YTD, …)
      nature       : dans le temps (ONE_TIME, RECURRING, STRUCTURAL)

    INVARIANT : amount = None signifie "donnée absente".
                amount = 0.0 signifie "vrai zéro observé".
                JAMAIS : montant inconnu → 0.0
    """

    # ── Classification financière ──────────────────────────────────────────
    amount:       Optional[float]   # None si "Données insuffisantes"
    currency:     str               = "EUR"
    metric_type:  MetricType        = MetricType.UNKNOWN
    period_basis: PeriodBasis       = PeriodBasis.UNKNOWN
    nature:       ImpactNature      = ImpactNature.UNKNOWN

    # ── Confiance et provenance ────────────────────────────────────────────
    confidence:        float                        = 0.5
    source_references: list[SourceReference]        = field(default_factory=list)
    gross_margin:      Optional[GrossMarginResolution] = None

    # ── Traçabilité temporelle ─────────────────────────────────────────────
    source_period:     Optional[str]  = None   # Texte exact : "Sep 2019", "YTD Jan-Jun 2019"
    temporal_role:     Optional[str]  = None   # De temporal_normalizer : CURRENT_ACTUAL, etc.
    is_current_period: bool           = True   # False → exclu des totaux courants
    annualization:     Optional[AnnualizationMetadata] = None

    # ── Anti-double-comptage ──────────────────────────────────────────────
    economic_event_id: Optional[str] = None   # ID stable et déterministe

    # ── Indicateurs ───────────────────────────────────────────────────────
    is_extrapolated:   bool = False

    # ─────────────────────────────────────────────────────────────────────
    # Méthodes de calcul — retournent JAMAIS de valeur si amount is None
    # ─────────────────────────────────────────────────────────────────────

    def recurring_annual_equivalent(self) -> Optional[float]:
        """
        Équivalent annuel CERTIFIÉ. Retourne None si :
          - amount is None
          - nature ∈ {ONE_TIME, UNKNOWN}
          - period_basis = UNKNOWN ou POINT_IN_TIME
          - ANNUALIZED avec quality ≠ CERTIFIED
          - YTD avec quality = REFUSED
        """
        if self.amount is None:
            return None
        if self.nature in (ImpactNature.ONE_TIME, ImpactNature.UNKNOWN):
            return None
        match self.period_basis:
            case PeriodBasis.ANNUAL:
                return self.amount
            case PeriodBasis.MONTHLY:
                return self.amount * 12
            case PeriodBasis.QUARTERLY:
                return self.amount * 4
            case PeriodBasis.ANNUALIZED:
                if (self.annualization
                        and self.annualization.quality == AnnualizationQuality.CERTIFIED):
                    return self.amount
                return None
            case PeriodBasis.YTD:
                if self.annualization and self.annualization.quality != AnnualizationQuality.REFUSED:
                    n = self.annualization.periods_elapsed
                    p = self.annualization.periods_per_year
                    if n > 0:
                        return self.amount / n * p
                return None
            case _:
                return None

    def run_rate_annual(self) -> Optional[float]:
        """
        Équivalent annuel indicatif (RUN_RATE inclus).
        Ne contribue PAS aux totaux certifiés.
        Calculé même si quality = RUN_RATE.
        """
        if self.amount is None:
            return None
        if self.nature in (ImpactNature.ONE_TIME, ImpactNature.UNKNOWN):
            return None
        match self.period_basis:
            case PeriodBasis.ANNUAL:
                return self.amount
            case PeriodBasis.MONTHLY:
                return self.amount * 12
            case PeriodBasis.QUARTERLY:
                return self.amount * 4
            case PeriodBasis.ANNUALIZED | PeriodBasis.YTD:
                if self.annualization and self.annualization.periods_elapsed > 0:
                    n = self.annualization.periods_elapsed
                    p = self.annualization.periods_per_year
                    return self.amount / n * p
                return None
            case _:
                return None

    def one_time_amount(self) -> Optional[float]:
        """Montant ponctuel. None si nature ≠ ONE_TIME ou ANNUALIZED."""
        if self.amount is None:
            return None
        if self.nature != ImpactNature.ONE_TIME:
            return None
        if self.period_basis == PeriodBasis.ANNUALIZED:
            return None  # ONE_TIME + ANNUALIZED = incohérent
        return self.amount

    def is_unresolved(self) -> bool:
        """
        True si cet impact ne peut pas contribuer aux totaux certifiés.
        Critères :
          - amount manquant
          - metric_type UNKNOWN ou EXPOSURE
          - period_basis UNKNOWN
          - nature UNKNOWN
          - impact non-courant
          - ANNUALIZED + REFUSED
        """
        if self.amount is None:
            return True
        if self.metric_type in (MetricType.UNKNOWN, MetricType.EXPOSURE):
            return True
        if self.period_basis == PeriodBasis.UNKNOWN:
            return True
        if self.nature == ImpactNature.UNKNOWN:
            return True
        if not self.is_current_period:
            return True
        if (self.period_basis == PeriodBasis.ANNUALIZED
                and self.annualization
                and self.annualization.quality == AnnualizationQuality.REFUSED):
            return True
        return False

    def annualization_quality(self) -> Optional[AnnualizationQuality]:
        """Qualité d'annualisation, ou None si non applicable."""
        if self.annualization is None:
            return None
        return self.annualization.quality

    def to_dict(self) -> dict:
        """Sérialisation pour persistence et logging."""
        return {
            "amount": self.amount,
            "currency": self.currency,
            "metric_type": self.metric_type.value,
            "period_basis": self.period_basis.value,
            "nature": self.nature.value,
            "confidence": self.confidence,
            "source_period": self.source_period,
            "temporal_role": self.temporal_role,
            "is_current_period": self.is_current_period,
            "is_extrapolated": self.is_extrapolated,
            "economic_event_id": self.economic_event_id,
            "gross_margin": (
                {
                    "rate": self.gross_margin.rate,
                    "source": self.gross_margin.source.value,
                }
                if self.gross_margin else None
            ),
            "annualization": (
                {
                    "periods_elapsed": self.annualization.periods_elapsed,
                    "periods_per_year": self.annualization.periods_per_year,
                    "quality": self.annualization.quality.value,
                    "seasonality_flag": self.annualization.seasonality_flag,
                    "annualization_method": self.annualization.annualization_method,
                }
                if self.annualization else None
            ),
            "source_references": [
                {
                    "fact_id": r.fact_id,
                    "sheet": r.sheet,
                    "row_label": r.row_label,
                    "period": r.period,
                    "observed_value": r.observed_value,
                    "source_quote": r.source_quote,
                    "source_type": r.source_type.value if r.source_type else None,
                }
                for r in self.source_references
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "QuantifiedImpact":
        """Désérialisation depuis un dict (LLM output ou persistence)."""
        if not isinstance(d, dict):
            raise ValueError(f"Expected dict, got {type(d)}")

        gross_margin = None
        gm = d.get("gross_margin")
        if gm and isinstance(gm, dict):
            try:
                gross_margin = GrossMarginResolution(
                    rate=gm.get("rate"),
                    source=GrossMarginSource(gm.get("source", "UNKNOWN")),
                )
            except (ValueError, KeyError):
                gross_margin = None

        annualization = None
        ann = d.get("annualization")
        if ann and isinstance(ann, dict):
            try:
                annualization = AnnualizationMetadata(
                    periods_elapsed=int(ann.get("periods_elapsed", 0)),
                    periods_per_year=int(ann.get("periods_per_year", 12)),
                    quality=AnnualizationQuality(
                        ann.get("quality", AnnualizationQuality.REFUSED.value)
                    ),
                    annualization_method=ann.get("annualization_method", ""),
                    seasonality_flag=bool(ann.get("seasonality_flag", False)),
                )
            except (ValueError, KeyError, TypeError):
                annualization = None

        source_references = []
        for ref in d.get("source_references") or []:
            if isinstance(ref, dict):
                _st_raw = ref.get("source_type")
                _st = None
                if _st_raw:
                    try:
                        _st = SourceType(_st_raw)
                    except ValueError:
                        _st = None
                source_references.append(SourceReference(
                    fact_id=ref.get("fact_id"),
                    sheet=ref.get("sheet"),
                    row_label=ref.get("row_label"),
                    period=ref.get("period"),
                    observed_value=ref.get("observed_value"),
                    source_quote=ref.get("source_quote"),
                    source_type=_st,
                ))

        return cls(
            amount=d.get("amount"),
            currency=d.get("currency", "EUR"),
            metric_type=_safe_enum(MetricType, d.get("metric_type"), MetricType.UNKNOWN),
            period_basis=_safe_enum(PeriodBasis, d.get("period_basis"), PeriodBasis.UNKNOWN),
            nature=_safe_enum(ImpactNature, d.get("nature"), ImpactNature.UNKNOWN),
            confidence=float(d.get("confidence", 0.5)),
            source_period=d.get("source_period"),
            temporal_role=d.get("temporal_role"),
            is_current_period=bool(d.get("is_current_period", True)),
            is_extrapolated=bool(d.get("is_extrapolated", False)),
            economic_event_id=d.get("economic_event_id"),
            gross_margin=gross_margin,
            annualization=annualization,
            source_references=source_references,
        )


# ─────────────────────────────────────────────────────────────────────────────
# EconomicEvent — modèle minimal Phase 4B (sans persistence DB)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EconomicEvent:
    """
    Événement économique sous-jacent à un ou plusieurs QuantifiedImpacts.
    Phase 4B : modèle uniquement, aucune persistence DB, aucune liaison DecisionArc.
    """
    event_id:         str                  # Hash déterministe SHA-256 (16 hex chars)
    event_category:   str                  # Catégorie normalisée (BILLING_DELAY, etc.)
    company_id:       str
    metric_type:      MetricType
    period:           str                  # Période canonique normalisée (YYYY-MM ou FY YYYY)
    entity:           Optional[str]        # Compte, produit, département

    identified_exposure: QuantifiedImpact
    status:              EconomicEventStatus = EconomicEventStatus.IDENTIFIED
    source_fact_ids:     list[str]          = field(default_factory=list)

    # Liaison avec décisions (Phase 4B : IDs uniquement, pas d'objets)
    executive_decision_ids: list[str] = field(default_factory=list)
    decision_arc_ids:       list[str] = field(default_factory=list)

    # Phase 4D+ : impact correctif
    expected_corrective_impact:  Optional[QuantifiedImpact] = None
    realized_corrective_impact:  Optional[QuantifiedImpact] = None
    residual_exposure:           Optional[float]            = None

    created_at: str = ""
    updated_at: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Catégories normalisées d'événements économiques
# ─────────────────────────────────────────────────────────────────────────────

VALID_EVENT_CATEGORIES = frozenset({
    "BILLING_DELAY",
    "REVENUE_GAP",
    "COST_OVERRUN",
    "MARGIN_EROSION",
    "CASH_SHORTFALL",
    "BFR_TENSION",
    "STRUCTURAL_COST",
    "OTHER",
})


# ─────────────────────────────────────────────────────────────────────────────
# SimulationMetricResult — résultat du résolveur de métrique homogène
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SimulationMetricResult:
    metric:          Optional[MetricType]          # None si aucune simulation consolidée
    reason:          str                            # Toujours explicite
    unconvertible:   list[QuantifiedImpact]         = field(default_factory=list)
    conversion_used: Optional[GrossMarginResolution] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internes
# ─────────────────────────────────────────────────────────────────────────────

def _safe_enum(enum_class, value, default):
    """Convertit une valeur en enum, retourne default si invalide."""
    if value is None:
        return default
    try:
        return enum_class(str(value).upper())
    except ValueError:
        return default


def normalize_period(period: str) -> str:
    """
    Normalise une période textuelle vers un format canonique.
    Ex : "Sep 2019" → "2019-09", "FY 2019" → "FY-2019", "Jan-Jun 2019" → "2019-01-06"
    """
    import re
    p = (period or "").strip()

    # FY YYYY
    if re.match(r"^FY\s*\d{4}$", p, re.IGNORECASE):
        m_fy = re.search(r"\d{4}", p)
        return f"FY-{m_fy.group()}" if m_fy else p

    # YYYY-MM déjà normalisé
    if re.match(r"^\d{4}-\d{2}$", p):
        return p

    # Mois YYYY ou MMM YYYY
    _MONTHS = {
        "jan": "01", "fév": "02", "feb": "02", "mar": "03",
        "avr": "04", "apr": "04", "mai": "05", "may": "05",
        "jun": "06", "jui": "07", "jul": "07", "aoû": "08", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "déc": "12", "dec": "12",
    }
    m = re.match(r"([a-zéû]{3})[a-zéû]*[.\s\-]*(\d{4})", p, re.IGNORECASE)
    if m:
        month_abbr = m.group(1).lower()
        year = m.group(2)
        month_num = _MONTHS.get(month_abbr)
        if month_num:
            return f"{year}-{month_num}"

    # Fallback : retourner tel quel nettoyé
    return p.replace(" ", "-")


def build_event_hash(
    company_id: str,
    metric_type: MetricType,
    source_fact_ids: list[str],
    period: str,
    entity: Optional[str],
    event_category: str,
) -> str:
    """
    Hash SHA-256 déterministe pour identifier un EconomicEvent.
    Même inputs → même hash. Collision quasi impossible dans un contexte entreprise.
    """
    canonical_key = "|".join([
        str(company_id),
        metric_type.value,
        *sorted(source_fact_ids),
        normalize_period(period),
        entity or "",
        event_category.upper(),
    ])
    return hashlib.sha256(canonical_key.encode()).hexdigest()[:16]
