# PHASE 4B — DESIGN V3 FINAL : Financial Truth Layer
## QuantifiedImpact · EconomicEvent · DecisionArc · Decision Capital

> **Statut :** V3 FINAL — décisions métier J.1–J.5 intégrées.  
> **Prérequis :** Phase 4A commitée (`83c035e`, `883a50c`) et validée production.  
> **Aucun code avant validation explicite.**

---

## Source of Truth — Chaîne cible

```
Canonical Financial Facts
    └── QuantifiedImpact          (ce qui est financièrement mesuré)
          └── EconomicEvent       (l'événement économique sous-jacent)
                └── ExecutiveDecision  (ce que l'organisation décide)
                      └── DecisionArc  (suivi de l'exécution)
                            └── ObservedConsequences  (ce qui se passe réellement)
                                  └── RealizedImpact  (mesure post-fait)
                                        └── Decision Capital  (mémoire institutionnelle)

Le LLM raisonne sur cette structure.
Il ne crée pas la vérité financière — il l'extrait, la propose, la structure.
La vérité est toujours ancrée dans les Canonical Financial Facts.
```

---

## A. `QuantifiedImpact` V3

### A.1 Enums (inchangés depuis V2, rappelés pour complétude)

```python
class MetricType(str, Enum):
    REVENUE, GROSS_MARGIN, EBITDA, NET_PROFIT, CASH,
    COST, COST_SAVING, WORKING_CAPITAL, EXPOSURE, UNKNOWN

class PeriodBasis(str, Enum):
    POINT_IN_TIME, MONTHLY, QUARTERLY, YTD, ANNUAL, ANNUALIZED, UNKNOWN

class ImpactNature(str, Enum):
    ONE_TIME, RECURRING, STRUCTURAL, UNKNOWN
```

### A.2 `AnnualizationQuality` — Nouveau (J.2)

```python
class AnnualizationQuality(str, Enum):
    CERTIFIED  = "CERTIFIED"
    # Remplit tous les critères minimaux.
    # Contribue à recurring_annual_exposure dans CostOfInactionV2.

    RUN_RATE   = "RUN_RATE"
    # Extrapolation calculable mais conditions minimales non atteintes
    # (ex : 4 mois seulement, ou saisonnalité non vérifiable).
    # Affiché avec label "ESTIMATION RUN-RATE" dans les livrables.
    # NE CONTRIBUE PAS aux totaux certifiés sans avertissement explicite.

    REFUSED    = "REFUSED"
    # Annualisation structurellement impossible ou non fiable.
    # Impact traité comme YTD brut, figure dans unresolved_impacts.
```

### A.3 `AnnualizationMetadata` V3

```python
@dataclass
class AnnualizationMetadata:
    periods_elapsed:    int          # Périodes calendaires écoulées
                                     # JAMAIS "mois actifs" ou "mois non nuls"
    periods_per_year:   int          # 12 pour mensuel, 4 pour trimestriel
    quality:            AnnualizationQuality   # CERTIFIED / RUN_RATE / REFUSED
    annualization_method: str        # Ex: "amount / periods_elapsed * periods_per_year"
    is_extrapolated:    bool = True
    seasonality_flag:   bool = False # True si saisonnalité significative détectée
    non_annualization_reason: Optional[str] = None  # Si quality = REFUSED
```

### A.4 `GrossMarginResolution` V3 (J.4)

```python
@dataclass
class GrossMarginResolution:
    rate: Optional[float]      # 0.0–1.0, ou None si UNKNOWN
    source: GrossMarginSource

class GrossMarginSource(str, Enum):
    EXPLICIT_FILE      = "EXPLICIT_FILE"      # 1. Fourni explicitement dans la source
    CANONICAL_FACTS    = "CANONICAL_FACTS"    # 2. Calculé depuis Canonical Financial Facts
    USER_HYPOTHESIS    = "USER_HYPOTHESIS"    # 3. Hypothèse utilisateur validée
    LLM_EXTRACTED      = "LLM_EXTRACTED"      # 4. Extrait LLM confirmable
    UNKNOWN            = "UNKNOWN"            # 5. Non disponible
```

**Hiérarchie stricte :** priorité dans l'ordre 1→5. Le LLM est niveau 4, jamais niveau 1.  
**Si `source = UNKNOWN` :** REVENUE reste REVENUE, aucune conversion vers EBITDA n'a lieu.

### A.5 `SourceReference` V3

```python
@dataclass
class SourceReference:
    fact_id:        Optional[str]    # ID dans l'Evidence Graph (lien canonique)
    sheet:          Optional[str]    # Feuille source ("P&L")
    row_label:      Optional[str]    # Label de ligne ("Code 70 - CA")
    period:         Optional[str]    # Période exacte ("Sep 2019")
    observed_value: Optional[float]  # Valeur brute observée
    source_quote:   Optional[str]    # Citation LLM (complément, jamais preuve unique)
    # Règle : au moins fact_id OU (sheet + row_label + period) requis
    # pour contribution aux totaux certifiés.
```

### A.6 `QuantifiedImpact` V3 — Modèle complet

```python
@dataclass
class QuantifiedImpact:

    # ── Classification financière ──────────────────────────────────────────────
    amount:          Optional[float]       # None si "Données insuffisantes"
    currency:        str = "EUR"
    metric_type:     MetricType
    period_basis:    PeriodBasis
    nature:          ImpactNature

    # ── Confiance et provenance ───────────────────────────────────────────────
    confidence:         float                       # 0.0–1.0
    source_references:  list[SourceReference]       # Vide → non certifié
    gross_margin:       Optional[GrossMarginResolution] = None
    # Requis si conversion REVENUE → EBITDA envisagée

    # ── Traçabilité temporelle ────────────────────────────────────────────────
    source_period:    Optional[str]         # Texte exact : "Sep 2019", "YTD Jan-Jun 2019"
    temporal_role:    Optional[str]         # De temporal_normalizer : CURRENT_ACTUAL, etc.
    is_current_period: bool = True          # False → exclu des totaux courants
    annualization:    Optional[AnnualizationMetadata] = None
    # Requis si period_basis = ANNUALIZED

    # ── Anti-double-comptage ─────────────────────────────────────────────────
    economic_event_id: Optional[str] = None
    # ID stable et déterministe (voir section E)

    # ── Indicateurs ───────────────────────────────────────────────────────────
    is_extrapolated:   bool = False

    # ── Méthodes ─────────────────────────────────────────────────────────────

    def recurring_annual_equivalent(self) -> Optional[float]:
        """
        Retourne l'équivalent annuel CERTIFIÉ uniquement si :
          - nature ∈ {RECURRING, STRUCTURAL}
          - amount is not None
          - period_basis ∉ {UNKNOWN, POINT_IN_TIME}
          - Si ANNUALIZED : annualization.quality == CERTIFIED
          - Si YTD : annualization.quality in {CERTIFIED, RUN_RATE}
            (RUN_RATE retourne la valeur mais flag is_run_rate = True)
        """
        if self.amount is None: return None
        if self.nature in (ImpactNature.ONE_TIME, ImpactNature.UNKNOWN): return None
        match self.period_basis:
            case PeriodBasis.ANNUAL:     return self.amount
            case PeriodBasis.MONTHLY:    return self.amount * 12
            case PeriodBasis.QUARTERLY:  return self.amount * 4
            case PeriodBasis.ANNUALIZED:
                if self.annualization and self.annualization.quality == AnnualizationQuality.CERTIFIED:
                    return self.amount
                return None
            case PeriodBasis.YTD:
                if self.annualization and self.annualization.quality != AnnualizationQuality.REFUSED:
                    n, p = self.annualization.periods_elapsed, self.annualization.periods_per_year
                    return self.amount / n * p
                return None
            case _: return None

    def run_rate_annual(self) -> Optional[float]:
        """
        Équivalent annuel indicatif (RUN_RATE) — ne contribue pas aux totaux certifiés.
        Calculé même si quality = RUN_RATE.
        Retourné avec flag séparé pour affichage différencié.
        """
        if self.amount is None: return None
        if self.nature in (ImpactNature.ONE_TIME, ImpactNature.UNKNOWN): return None
        if self.period_basis == PeriodBasis.YTD and self.annualization:
            n, p = self.annualization.periods_elapsed, self.annualization.periods_per_year
            return self.amount / n * p
        return self.recurring_annual_equivalent()

    def one_time_amount(self) -> Optional[float]:
        """Montant ponctuel. None si nature ≠ ONE_TIME."""
        if self.amount is None: return None
        if self.nature != ImpactNature.ONE_TIME: return None
        if self.period_basis == PeriodBasis.ANNUALIZED: return None  # Interdit
        return self.amount

    def is_unresolved(self) -> bool:
        return (
            self.amount is None
            or self.metric_type == MetricType.UNKNOWN
            or self.period_basis == PeriodBasis.UNKNOWN
            or self.nature == ImpactNature.UNKNOWN
            or not self.is_current_period
            or self.metric_type == MetricType.EXPOSURE
            or (self.period_basis == PeriodBasis.ANNUALIZED
                and self.annualization
                and self.annualization.quality == AnnualizationQuality.REFUSED)
        )
```

---

## B. POLITIQUE D'ANNUALISATION FINALE (J.2)

### B.1 Seuils minimaux pour `AnnualizationQuality.CERTIFIED`

| PeriodBasis | Condition minimale | Condition cumulatives |
|-------------|-------------------|-----------------------|
| MONTHLY (→ ANNUALIZED) | `periods_elapsed ≥ 6` | + nature ∈ {RECURRING, STRUCTURAL} |
| QUARTERLY (→ ANNUALIZED) | `periods_elapsed ≥ 2` | + idem |
| YTD (annualisation) | `periods_elapsed ≥ 6` (mensuel) | + période courante identifiée |
| | `periods_elapsed ≥ 2` (trimestriel) | + aucune saisonnalité significative |
| | | + `temporal_role = CURRENT_ACTUAL` |

### B.2 Logique de décision

```
Si periods_elapsed ≥ seuil ET seasonality_flag = False ET nature ∈ {RECURRING, STRUCTURAL} :
    quality = CERTIFIED
    → contribue à recurring_annual_exposure

Si periods_elapsed < seuil ET calcul réalisable ET seasonality_flag non détectée :
    quality = RUN_RATE
    → calculé et affiché avec label "ESTIMATION RUN-RATE (N mois écoulés)"
    → NE contribue PAS à recurring_annual_exposure sans avertissement explicite
    → peut figurer dans un bloc "Indicateurs indicatifs" séparé

Si nature = ONE_TIME OU period_basis = POINT_IN_TIME OU saisonnalité confirmée :
    quality = REFUSED
    → montant brut conservé dans one_time_exposures ou unresolved_impacts
    → aucune extrapolation affichée

RÈGLE FONDAMENTALE :
    periods_elapsed = nombre de mois CALENDAIRES depuis début de période
    Ex : "Jan 2019 → Sep 2019" = 9, même si Sep = 0 (mois fermé = mois compté)
    JAMAIS : compter uniquement les mois avec valeur > 0
```

### B.3 Affichage différencié dans les livrables

```
CERTIFIED :   "48 000 €/an"                   (sans annotation)
RUN_RATE :    "≈ 48 000 €/an (run-rate 6M)"   (annotation obligatoire)
REFUSED :     valeur brute YTD uniquement       (pas d'extrapolation affichée)
```

---

## C. `resolve_simulation_metric()` — Résolveur de métrique homogène (J.1)

```
resolve_simulation_metric(
    impacts: list[QuantifiedImpact],
    canonical_facts: CanonicalFactsContext,
) → SimulationMetricResult

@dataclass
class SimulationMetricResult:
    metric:          Optional[MetricType]  # None si aucune simulation consolidée possible
    reason:          str                   # Toujours explicite
    unconvertible:   list[QuantifiedImpact]  # Impacts non intégrés à la simulation
    conversion_used: Optional[GrossMarginResolution]  # Si conversion appliquée
```

**Algorithme (dans l'ordre strict) :**

```
Étape 1 — EBITDA disponible et impacts compatibles ?
    ebitda_base = canonical_facts.get("ebitda")
    Si ebitda_base is not None ET fiable :
        recurring = [i for i non unresolved, nature ∈ RECURRING/STRUCTURAL]
        ebitda_compatible = [i for i in recurring
                             if i.metric_type ∈ {EBITDA, COST, COST_SAVING}]
        revenue_with_gm = [i for i in recurring
                           if i.metric_type = REVENUE
                           AND i.gross_margin is not None
                           AND i.gross_margin.source ≠ UNKNOWN]
        unconvertible = recurring \ (ebitda_compatible ∪ revenue_with_gm)

        Si ebitda_compatible ∪ revenue_with_gm ≠ ∅ :
            → metric = EBITDA
            → reason = "EBITDA disponible et X impacts compatibles"
              + (si unconvertible ≠ ∅ : "Y impacts non convertis affichés séparément")
            → return

Étape 2 — Autre métrique homogène ?
    metric_types = {i.metric_type for i in recurring if not i.is_unresolved()}
    Si len(metric_types) == 1 et metric_types ≠ {UNKNOWN} et metric_types ≠ {EXPOSURE} :
        → metric = unique_type
        → reason = f"Métrique unique : {unique_type.value} (EBITDA non disponible)"
        → return

Étape 3 — Aucune simulation consolidée possible
    → metric = None
    → reason = f"Métriques hétérogènes ({', '.join(...)}) sans conversion possible — impacts affichés séparément"
    → unconvertible = tous les impacts récurrents
```

**Note :** Si `metric = None`, les livrables affichent chaque bucket métrique séparément. Jamais un total synthétique.

---

## D. HIÉRARCHIE GROSS MARGIN RATE FINALE (J.4)

```
Pour convertir un impact REVENUE en EBITDA-equivalent :

1. EXPLICIT_FILE
   gross_margin_rate est présent dans le fichier source analysé
   (ex : ligne "Taux de marge brute : 42%" dans le P&L)
   → priorité absolue, aucune validation supplémentaire

2. CANONICAL_FACTS
   gross_margin = gross_profit / revenue, calculé de façon déterministe
   depuis les Canonical Financial Facts (codes comptables reconnus)
   → fiable si les deux composants sont disponibles avec confidence ≥ 0.8

3. USER_HYPOTHESIS
   L'utilisateur a saisi un taux dans la feuille Hypothèses ou l'interface dédiée
   → valide, mais marqué "Hypothèse utilisateur" dans les livrables

4. LLM_EXTRACTED
   Le LLM a extrait un taux depuis le texte source, confirmable par citation
   → acceptable uniquement si source_quote fourni et cohérent avec le contexte
   → confiance maximale = 0.6 (jamais CERTIFIED)

5. UNKNOWN
   Aucun des niveaux 1–4 disponible
   → REVENUE reste REVENUE
   → Aucune conversion vers EBITDA
   → Affiché séparément avec note : "Taux de marge non documenté —
     impact revenue non intégré à la simulation EBITDA"
   → Cellule Hypothèses proposée pour saisie manuelle (option future)
```

---

## E. `EconomicEvent` — Modèle et Resolver (J.3)

### E.1 Modèle `EconomicEvent`

```python
class EconomicEventStatus(str, Enum):
    IDENTIFIED          = "IDENTIFIED"
    # Exposition identifiée, aucune décision encore prise.

    ADDRESSED           = "ADDRESSED"
    # Une ExecutiveDecision référence cet événement (resolves_event_id défini).
    # L'impact correctif est ATTENDU, pas encore observé.

    PENDING_OBSERVATION = "PENDING_OBSERVATION"
    # Le DecisionArc est ouvert, en attente des conséquences observées.

    CLOSED_RESOLVED     = "CLOSED_RESOLVED"
    # Arc fermé. realized_corrective_impact mesurable. residual_exposure ≈ 0.

    CLOSED_PARTIAL      = "CLOSED_PARTIAL"
    # Arc fermé. Correction partielle. residual_exposure > 0.

    CLOSED_UNRESOLVED   = "CLOSED_UNRESOLVED"
    # Arc fermé. Impact persistant. La décision n'a pas produit l'effet attendu.


@dataclass
class EconomicEvent:
    # ── Identité (déterministe, stable) ──────────────────────────────────────
    event_id:          str              # Hash opaque stable (voir resolver E.2)
    event_category:    str              # Catégorie normalisée ("BILLING_DELAY",
                                        # "COST_OVERRUN", "REVENUE_GAP", etc.)
    company_id:        str
    metric_type:       MetricType
    period:            str              # Période canonique de référence
    entity:            Optional[str]   # Compte, produit, département

    # ── Exposition initiale ───────────────────────────────────────────────────
    identified_exposure: QuantifiedImpact   # Ce qui a été mesuré/identifié
    status:            EconomicEventStatus  # = IDENTIFIED à la création
    source_fact_ids:   list[str]           # IDs Evidence Graph — provenance

    # ── Liaison avec les décisions ────────────────────────────────────────────
    executive_decision_ids: list[str] = field(default_factory=list)
    # IDs des décisions qui adressent cet événement.
    # Populé quand une ExecutiveDecision définit resolves_event_id = self.event_id.

    decision_arc_ids: list[str] = field(default_factory=list)
    # IDs des DecisionArcs qui suivent les décisions liées.

    # ── Impact correctif (post-observation) ──────────────────────────────────
    expected_corrective_impact: Optional[QuantifiedImpact] = None
    # Copié depuis ExecutiveDecision.quantified_impact au moment du lien.
    # ATTENDU — pas encore réalisé.

    realized_corrective_impact: Optional[QuantifiedImpact] = None
    # None jusqu'à la fermeture du DecisionArc.
    # Mesuré depuis ObservedConsequences après observation réelle.

    residual_exposure: Optional[float] = None
    # Calculé uniquement après fermeture de l'Arc ET si métriques compatibles :
    # residual = identified_exposure.amount - realized_corrective_impact.amount
    # None si métriques incompatibles ou realized = None.

    # ── Méta ──────────────────────────────────────────────────────────────────
    created_at:  str = ""
    updated_at:  str = ""
```

### E.2 `EconomicEventResolver` — Hybride déterministe + LLM (J.3)

**Principe :** le LLM propose une catégorie sémantique et une correspondance potentielle. Le resolver construit l'ID de façon déterministe. Le LLM ne décide jamais seul de l'identité finale.

```
resolve_economic_event_id(
    company_id:        str,
    metric_type:       MetricType,
    source_fact_ids:   list[str],     # IDs Evidence Graph (triés)
    period:            str,            # Période canonique normalisée
    entity:            Optional[str],
    event_category:    str,            # Proposé par LLM, validé avant usage
) → str

Algorithme :
    canonical_key = "|".join(sorted([
        company_id,
        metric_type.value,
        *sorted(source_fact_ids),
        normalize_period(period),      # "Sep 2019" → "2019-09"
        entity or "",
        event_category.upper(),
    ]))
    return sha256(canonical_key.encode()).hexdigest()[:16]
    # 16 hex chars = 64 bits d'entropie — collision quasi impossible pour un contexte d'entreprise
```

**Rôle du LLM dans la résolution :**

```
1. Extraction : le LLM extrait metric_type, period, entity depuis le contexte.

2. Catégorisation : le LLM propose un event_category parmi une liste normalisée :
   BILLING_DELAY, REVENUE_GAP, COST_OVERRUN, MARGIN_EROSION,
   CASH_SHORTFALL, BFR_TENSION, STRUCTURAL_COST, OTHER

3. Correspondance : le LLM reçoit la liste des event_ids existants
   avec leurs catégories et périodes, et indique si le nouvel impact
   "semble" référencer le même événement qu'un event_id existant.
   → Si correspondance proposée : le resolver vérifie la cohérence
     (metric_type + period + entity compatibles ?) avant d'accepter.

4. ID final : TOUJOURS calculé par le resolver déterministe.
   Le LLM ne génère jamais l'event_id directement.
```

**Liaison Decision → Event (sens unique, pas circulaire) :**

```
Quand une ExecutiveDecision est créée pour adresser un événement connu :
    decision.resolves_event_id = economic_event.event_id
    # → Le resolver NE regénère PAS un nouvel event_id pour la décision.
    # → economic_event.executive_decision_ids.append(decision.id)
    # → economic_event.expected_corrective_impact = decision.quantified_impact
    # → economic_event.status = ADDRESSED

Quand un DecisionArc est ouvert sur cette décision :
    arc.economic_event_id = decision.resolves_event_id
    # → economic_event.decision_arc_ids.append(arc.id)
    # → economic_event.status = PENDING_OBSERVATION
```

---

## F. RELATION `EconomicEvent` / `ExecutiveDecision` / `DecisionArc`

### F.1 Schéma des références (sans circularité)

```
EconomicEvent
  ├── event_id (stable, déterministe)
  ├── identified_exposure: QuantifiedImpact
  ├── executive_decision_ids: list[str]      ← IDs uniquement (pas d'objets)
  └── decision_arc_ids: list[str]            ← IDs uniquement (pas d'objets)

ExecutiveDecision
  ├── id (généré)
  ├── resolves_event_id: Optional[str]       ← Référence vers EconomicEvent.event_id
  ├── quantified_impact: Optional[QuantifiedImpact]  ← Impact ATTENDU
  └── decision_arc_id: Optional[str]         ← Référence vers DecisionArc.id

DecisionArc
  ├── arc_id (généré)
  ├── decision_id: str                       ← Référence vers ExecutiveDecision.id
  ├── economic_event_id: str                 ← Copié depuis decision.resolves_event_id
  └── observed_consequences: list[Consequence]

ObservedConsequences
  ├── consequence_id (généré)
  ├── arc_id: str
  └── realized_impact: Optional[QuantifiedImpact]  ← Mesuré post-fait
```

**Résolution de la circularité :**  
Les trois entités ne se référencent que par IDs (strings). La résolution d'un ID en objet se fait toujours via un lookup dans un registre central (ex : `event_registry[event_id]`). Il n'y a aucune référence d'objet circulaire — uniquement des graphes de IDs orientés.

### F.2 Mises à jour de statut `EconomicEvent`

```
IDENTIFIED
  → création de l'événement depuis QuantifiedImpact + Evidence Graph

ADDRESSED
  → ExecutiveDecision créée avec resolves_event_id = event_id
  → expected_corrective_impact copié depuis decision.quantified_impact

PENDING_OBSERVATION
  → DecisionArc ouvert, lié à la décision

CLOSED_*
  → DecisionArc fermé avec ObservedConsequences
  → realized_corrective_impact renseigné depuis ObservedConsequences
  → residual_exposure calculé si métriques compatibles
  → statut RESOLVED / PARTIAL / UNRESOLVED selon seuil residual_exposure

Seuil de fermeture :
    |residual_exposure| / identified_exposure.amount < 0.10 → CLOSED_RESOLVED
    0.10 ≤ ratio < 0.50                                     → CLOSED_PARTIAL
    ratio ≥ 0.50 ou realized = None                         → CLOSED_UNRESOLVED
```

---

## G. ANTI-DOUBLE-COMPTAGE AVANT ET APRÈS FERMETURE D'ARC (J.5)

### G.1 Principe fondamental (correction V3)

```
JAMAIS :
    identified_exposure + expected_corrective_impact → net = 0 → "résolu"

Avant fermeture du DecisionArc, realized_corrective_impact = UNKNOWN (None).
Le double-comptage est géré par affichage séparé, pas par soustraction prématurée.
```

### G.2 Avant fermeture du DecisionArc

```
Affichage des impacts liés par economic_event_id :

┌─────────────────────────────────────────────────────────┐
│ EXPOSITION IDENTIFIÉE                                    │
│ Retard facturation Sep 2019                              │
│ 454 000 € — REVENUE — POINT_IN_TIME / ONE_TIME          │
│                                                          │
│ → ADRESSÉE PAR : [Décision] Émettre les factures Sep     │
│   Impact attendu : 454 000 € REVENUE (ONE_TIME)          │
│   Statut : EN ATTENTE D'OBSERVATION                      │
│   Impact réalisé : NON ENCORE MESURÉ                    │
└─────────────────────────────────────────────────────────┘

Le montant 454 000 € apparaît UNE SEULE FOIS dans le total one_time_exposures.
La décision corrective n'ajoute PAS de montant au total.
Elle change uniquement le statut de l'événement (IDENTIFIED → ADDRESSED).
```

### G.3 Après fermeture du DecisionArc

```
realized_corrective_impact mesuré depuis ObservedConsequences.

Si métriques compatibles (même metric_type) :
    residual_exposure = identified_exposure.amount - realized_corrective_impact.amount

Exemples :
    identified = 454 000 REVENUE, realized = 420 000 REVENUE
    → residual = 34 000 REVENUE  (CLOSED_PARTIAL)
    → "34 000 € d'exposition résiduelle après action corrective"

    identified = 454 000 REVENUE, realized = 454 000 REVENUE
    → residual = 0               (CLOSED_RESOLVED)
    → "Événement résolu — Impact correctif confirmé"

    identified = 454 000 REVENUE, realized = 0 REVENUE (ou None)
    → residual = 454 000         (CLOSED_UNRESOLVED)
    → "Décision sans effet observé — Exposition persistante"

Si métriques incompatibles (metric_type différents) :
    residual_exposure = None
    → "Impact réalisé mesuré en [type B], exposition identifiée en [type A]
       — comparaison non effectuée"
    → Les deux montants affichés séparément
```

### G.4 Règles d'agrégation avec double-comptage protégé

```
Pour CostOfInactionV2 (avant fermeture d'Arc) :

  one_time_exposures :
    → inclut identified_exposure si status ∈ {IDENTIFIED, ADDRESSED, PENDING_OBSERVATION}
    → JAMAIS expected_corrective_impact (impact attendu ≠ impact constaté)

  Pour chaque groupe par economic_event_id :
    Si plusieurs impacts sans décision corrective → probable doublon :
      → Conserver max(amount) avec avertissement
      → NE PAS sommer les deux montants

  recurring_annual_exposure :
    → même règle : un seul impact par economic_event_id dans la somme
```

---

## H. `CostOfInactionV2` — Structure finale

```python
@dataclass
class CostOfInactionV2:

    # ── Résolveur de métrique ─────────────────────────────────────────────────
    simulation_metric_result: SimulationMetricResult
    # Contient metric (MetricType | None), reason, unconvertible[], conversion_used

    # ── Bucket 1 : impacts récurrents certifiés ───────────────────────────────
    recurring_by_metric:      dict[str, float]
    # Clé = MetricType.value. Agrégation homogène par type.
    # Ex : {"EBITDA": -48000, "COST_SAVING": 24000}

    recurring_annual_exposure: Optional[float]
    # = Σ recurring_annual_equivalent() pour metric = simulation_metric
    # None si simulation_metric = None
    # Uniquement impacts quality=CERTIFIED

    recurring_annual_run_rate: Optional[float]
    # = idem mais inclut quality=RUN_RATE
    # Affiché avec annotation "DONT ESTIMATION RUN-RATE" si > recurring_annual_exposure

    # ── Dérivés (UNIQUEMENT depuis recurring_annual_exposure) ─────────────────
    @property
    def per_month(self)  -> Optional[float]: return self.recurring_annual_exposure / 12  if self.recurring_annual_exposure else None
    @property
    def per_week(self)   -> Optional[float]: return self.recurring_annual_exposure / 52  if self.recurring_annual_exposure else None
    @property
    def per_day(self)    -> Optional[float]: return self.recurring_annual_exposure / 365 if self.recurring_annual_exposure else None
    @property
    def per_hour(self)   -> Optional[float]: return self.recurring_annual_exposure / 8760 if self.recurring_annual_exposure else None
    # JAMAIS calculés depuis recurring_annual_run_rate

    # ── Bucket 2 : impacts ponctuels ──────────────────────────────────────────
    one_time_exposures: list[dict]
    # [{"label", "amount", "metric_type", "economic_event_id", "status"}]
    # Status : IDENTIFIED / ADDRESSED / PENDING_OBSERVATION / CLOSED_*

    # ── Bucket 3 : non résolus ────────────────────────────────────────────────
    unresolved_impacts: list[dict]
    # [{"label", "reason", "amount_if_known", "metric_type"}]

    # ── Bucket 4 : expositions non agrégables ─────────────────────────────────
    exposure_impacts: list[dict]
    # [{"label", "amount", "metric_type": "EXPOSURE", "economic_event_id"}]

    # ── Méta ──────────────────────────────────────────────────────────────────
    confidence:                    float
    heterogeneous_metrics_detected: bool
    run_rate_impacts_present:      bool
```

---

## H.2 Affichage livrable — Sections séparées obligatoires

```
┌─────────────────────────────────────────────────────────────┐
│ IMPACT RÉCURRENT ANNUEL CERTIFIÉ                            │
│ 48 000 €/an                                                  │
│ (sur base EBITDA — 2 impacts)                               │
├─────────────────────────────────────────────────────────────┤
│ [Si applicable] ESTIMATION RUN-RATE (indicatif)             │
│ ≈ 60 000 €/an (dont 12 000 € sur 4 mois — extrapolé)       │
├─────────────────────────────────────────────────────────────┤
│ EXPOSITIONS PONCTUELLES IDENTIFIÉES                         │
│ Retard facturation Sep 2019 : 454 000 € REVENUE             │
│   → Adressée par décision [X] — en attente d'observation   │
├─────────────────────────────────────────────────────────────┤
│ IMPACTS NON RÉSOLUS (non intégrés aux totaux)               │
│ • Risque fournisseur X : period_basis inconnu               │
│ • Perte marge Y : taux de conversion manquant               │
└─────────────────────────────────────────────────────────────┘
NE JAMAIS PRODUIRE UN TOTAL MÉLANGEANT CES TROIS SECTIONS.
```

---

## H.3 Migration legacy finale (J.3 / J.4 → phase de transition)

```python
# Dans ExecutiveDecision, ValueDestroyerItem — coexistence Phase 4B :
annual_impact:      Optional[float]           # Legacy — conservé, jamais supprimé en 4B
quantified_impact:  Optional[QuantifiedImpact]  # V3 — source de vérité si présent

# RÈGLE RENDERER — non négociable :
# if quantified_impact is not None:
#     utiliser EXCLUSIVEMENT quantified_impact
# else:
#     fallback sur annual_impact (comportement legacy inchangé)
#
# INTERDIT : tout renderer qui lit les deux et fusionne ou moyenne.
# INTERDIT : tout renderer qui compare annual_impact et quantified_impact.amount.
```

**Séquence de migration :**
```
Étape 1 — Phase 4B :
  Ajouter quantified_impact en champ optionnel parallèle.
  LLM reçoit schema JSON V3 pour extraction.
  Seuil acceptance : ≥ 85% sur metric_type + period_basis + nature (10 cas réels).

Étape 2 — Phase 4C (si seuil atteint) :
  Tous les renderers lisent quantified_impact en priorité.
  annual_impact devient invisible dans les livrables (mais conservé en DB).

Étape 3 — Phase 4D (après validation production) :
  compute_cost_of_inaction() remplacé par CostOfInactionV2.
  annual_impact retiré des renderers (conservé en DB pour rétrocompatibilité).
```

---

## I. CAS DE TEST PROPOSÉS (pré-code Phase 4B)

### A — Revenu ponctuel non annualisable
```
Input : amount=454_000, metric_type=REVENUE, period_basis=POINT_IN_TIME, nature=ONE_TIME,
        economic_event_id=resolve_economic_event_id("optilux", REVENUE, [...], "2019-09", None, "BILLING_DELAY")

Assertions :
  recurring_annual_equivalent() == None
  run_rate_annual() == None
  one_time_amount() == 454_000
  is_unresolved() == False
  → one_time_exposures uniquement, JAMAIS recurring_annual_exposure
```

### B — Économie mensuelle récurrente certifiée
```
Input : amount=4_000, metric_type=COST_SAVING, period_basis=MONTHLY, nature=RECURRING,
        annualization = None (MONTHLY n'a pas besoin d'annualization)

Assertions :
  recurring_annual_equivalent() == 48_000
  one_time_amount() == None
  contributes_to_simulation(EBITDA) == True (COST_SAVING→EBITDA 1:1)
```

### C — Revenue historique exclu des totaux courants
```
Input : amount=49_000, metric_type=REVENUE, period_basis=ANNUAL,
        source_period="FY 2014", temporal_role="HISTORICAL_ACTUAL"
        → is_current_period = False (forcé par temporal_normalizer)

Assertions :
  is_unresolved() == True
  → unresolved_impacts avec reason="Impact historique (FY 2014) — exclu des totaux courants"
  → montant 49_000 n'apparaît dans AUCUN total financier
```

### D — Exposition avec nature inconnue
```
Input : amount=200_000, metric_type=EXPOSURE, period_basis=UNKNOWN, nature=UNKNOWN

Assertions :
  is_unresolved() == True (EXPOSURE toujours + double UNKNOWN)
  recurring_annual_equivalent() == None
  one_time_amount() == None
  → exposure_impacts uniquement
  → contribution à recurring_annual_exposure : 0 (zéro, pas même en pondération)
```

### E — Métriques hétérogènes non agrégables
```
Input impact_1 : amount=100_000, metric_type=REVENUE, nature=RECURRING, period_basis=ANNUAL,
                 gross_margin = GrossMarginResolution(rate=None, source=UNKNOWN)
Input impact_2 : amount=100_000, metric_type=EBITDA, nature=RECURRING, period_basis=ANNUAL

resolve_simulation_metric([impact_1, impact_2], facts) :
  → metric = EBITDA (disponible)
  → unconvertible = [impact_1] (REVENUE sans taux de marge)
  → recurring_annual_exposure = 100_000 (EBITDA seul)
  → impact_1 affiché séparément, JAMAIS total = 200_000
```

### F — Anti-double-comptage ValueDestroyer + Decision, avant Arc fermé
```
event_id = resolve_economic_event_id("optilux", REVENUE, ["fact_001"], "2019-09", None, "BILLING_DELAY")

ValueDestroyer QI : amount=454_000, metric_type=REVENUE, nature=ONE_TIME, economic_event_id=event_id
ExecutiveDecision : resolves_event_id = event_id, expected_corrective_impact = 454_000 REVENUE
DecisionArc : status = OPEN

CostOfInactionV2 :
  one_time_exposures = [{"label": "Retard facturation Sep", "amount": 454_000, "status": "ADDRESSED"}]
  → 454_000 apparaît UNE seule fois
  → expected_corrective_impact N'EST PAS soustrait (arc non fermé)
  → JAMAIS total = 908_000
```

### G — YTD calendaire, 6 mois complets
```
Input : amount=227_000, metric_type=EBITDA, period_basis=YTD, nature=RECURRING,
        annualization = AnnualizationMetadata(
          periods_elapsed=6, periods_per_year=12,
          quality=CERTIFIED, seasonality_flag=False,
          annualization_method="amount / 6 * 12"
        )

Assertions :
  recurring_annual_equivalent() == 227_000 / 6 * 12 == 454_000
  → quality=CERTIFIED → contribue à recurring_annual_exposure sans annotation
  (PAS basé sur les mois non nuls — Sep=0 est compté dans les 6 si période = Jan-Jun)
```

### H — Revenue sans taux de marge → simulation EBITDA refusée
```
Input : amount=454_000, metric_type=REVENUE, nature=RECURRING, period_basis=ANNUAL,
        gross_margin = GrossMarginResolution(rate=None, source=UNKNOWN)

Assertions :
  contributes_to_simulation(simulation_metric=EBITDA) == False
  → SimulationMetricResult.unconvertible = [this_impact]
  → recurring_annual_exposure inchangé
  → affichage : "Impact REVENUE 454 000 €/an — taux de marge non documenté,
     non intégré à la projection EBITDA"
```

### I — Annualization RUN_RATE (4 mois seulement)
```
Input : amount=150_000, metric_type=EBITDA, period_basis=YTD, nature=RECURRING,
        annualization = AnnualizationMetadata(
          periods_elapsed=4, periods_per_year=12,
          quality=RUN_RATE,  # < 6 mois → RUN_RATE
          non_annualization_reason="Seuil minimum 6 mois non atteint (4 mois écoulés)"
        )

Assertions :
  recurring_annual_equivalent() == 150_000 / 4 * 12 == 450_000
  → AnnualizationQuality.RUN_RATE → NE contribue PAS à recurring_annual_exposure
  → Contribue à recurring_annual_run_rate avec annotation "RUN-RATE 4M"
  → Affichage : "≈ 450 000 €/an (estimation run-rate — 4 mois)"
```

### J — Arc fermé, impact réalisé partiel
```
EconomicEvent : event_id = "ev_abc123", identified_exposure = 454_000 REVENUE ONE_TIME
ExecutiveDecision : resolves_event_id = "ev_abc123", expected = 454_000 REVENUE
DecisionArc : CLOSED avec ObservedConsequences
realized_corrective_impact = 420_000 REVENUE ONE_TIME

Assertions :
  residual_exposure = 454_000 - 420_000 = 34_000
  status = CLOSED_PARTIAL
  affichage : "34 000 € d'exposition résiduelle REVENUE (correction partielle)"
  JAMAIS : "20K résiduel EBITDA" si metrics incompatibles
```

---

## J. VERDICT

**NOT READY TO IMPLEMENT — Un seul point ouvert**

Tous les choix architecturaux et métriques sont tranchés. Le seul point qui nécessite une décision avant code :

**J.0 — Périmètre Phase 4B vs 4C**

Le design complet couvre 4B + 4C (voire 4D). La Phase 4B doit être délimitée précisément pour rester implémentable en un sprint :

**Proposition de périmètre Phase 4B strict :**

```
Phase 4B (implémentable) :
  ✓ QuantifiedImpact V3 dataclass + méthodes
  ✓ AnnualizationMetadata + AnnualizationQuality
  ✓ GrossMarginResolution (hiérarchie 1→5)
  ✓ resolve_simulation_metric()
  ✓ EconomicEvent model + resolver (sans persistence DB)
  ✓ Extraction LLM enrichie (schema JSON V3 dans le prompt)
  ✓ Tests A–J ci-dessus
  ✓ Migration : annual_impact conservé, quantified_impact parallèle

Phase 4C (after validation 85% extraction) :
  → CostOfInactionV2 remplace compute_cost_of_inaction()
  → Renderers mis à jour (Excel EDM, PDF, PPTX)
  → EconomicEvent persistence (DB ou in-memory registry)

Phase 4D (après validation production) :
  → DecisionArc liaison complète (realized_corrective_impact)
  → RealizedImpact → Decision Capital
  → residual_exposure + statut fermeture Arc
```

**Validation requise :** confirmer le périmètre Phase 4B. Sur réponse positive, READY TO IMPLEMENT Phase 4B.

---

*Document : PHASE_4B_DESIGN_V3_FINAL.md*  
*Statut : V3 FINAL — décisions J.1–J.5 intégrées — en attente de délimitation périmètre 4B*  
*Pepperyn + Claude Sonnet 4.6 — 2026-07-19*
