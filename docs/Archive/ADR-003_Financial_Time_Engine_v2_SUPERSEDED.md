# ADR-003 — Financial Time Engine (v2, réécriture complète)

**Phase :** T2.5 (voir §4.13 pour la justification de ce positionnement, inchangée sur le fond)
**Statut :** Proposé, pour revue — remplace intégralement ADR-003 v1 (commit `2050a07`)
**Sources autorisées :** Pepperyn Constitution v1.0 · Ideal Domain Model (Fractional CFO, 2026-08-02) · Pepperyn Current Domain Model (2026-08-02) · Transformation Blueprint (2026-08-02) · ADR-001 · ADR-001A · ADR-002 · ADR-003 v1
**Nature :** décision d'architecture métier. Aucun code, aucun modèle Pydantic, aucune migration, aucun prompt n'est modifié par ce document.

---

## §0 — Avertissement préalable (inchangé depuis v1)

Le code de service T1/T2 (Evidence Ledger, Engagement) n'existe aujourd'hui sur aucune branche fusionnée dans `main` — uniquement sur les branches `feature/t1c-b-atomic-financial-facts` et `feature/t2a-engagement-persistence`. Ce document conçoit le Financial Time Engine (FTE) comme s'il s'intégrait à la cible T1+T2, mais toute implémentation réelle devra d'abord vérifier l'état effectif de ces fondations sur la branche cible. Ce n'est pas une objection à la conception — c'est une précondition d'implémentation.

---

## §1 — Critique de la v1 (Mission 1)

**Question posée : le FTE tel que conçu en v1 est-il un moteur de périodes, ou un véritable moteur temporel du domaine ? Réponse argumentée : v1 est un moteur de périodes avec des ambitions temporelles nommées mais non réalisées architecturalement.**

Preuves concrètes, tirées du texte même d'ADR-003 v1 :

1. **`today` était un scalaire nu.** v1 §3.3 définissait `FinancialTemporalContext.today: Date` — une date brute, sans signification métier attachée. Rien dans l'objet ne répondait à la question que pose l'axiome fondateur n°3 du mandat original : *que signifie ce moment pour cet Engagement, maintenant* ? Un scalaire ne porte pas de sens ; il faut un objet qui le porte. C'est l'angle mort le plus structurant de v1, et il en découle presque tous les autres.

2. **`ManagementCycle` était singulier et plat.** v1 en faisait un unique triplet `(expected_frequency, next_expected_closing, next_recommended_analysis)`. Or aucune organisation réelle ne vit sur un seul rythme : une clôture mensuelle, une revue de conseil trimestrielle et un audit annuel coexistent, avec des échéances et des publics différents. En réduisant cela à un seul cycle, v1 gommait exactement la richesse que la Mission 5 du mandat demande de restituer.

3. **`RecommendationTemporalWindow` était « quelques dates ».** v1 §3.3 le définissait comme quatre champs de date (`created_at`, `observation_window_end`, `reevaluation_date`, `expiration_date`), sans état qualitatif dérivable. Le mandat (Mission 6) nomme précisément ce défaut : *« un vrai modèle métier, pas juste quelques dates »*. Une date ne dit pas si une recommandation est *prématurée*, *attendue*, *due*, *en retard* ou *obsolète* — il faut un modèle qui le dise.

4. **Le FTE était défini de façon trop passive.** v1 §3.3 : *« le FTE ne réalise aucune analyse financière, ne calcule aucune comparaison, ne décide d'aucune pertinence »*. Cette prudence, en apparence disciplinée, entre en contradiction avec l'axiome fondateur n°3 du mandat original (*« Pepperyn doit comprendre pourquoi ce fichier arrive maintenant… quelles décisions doivent être réévaluées »*) : comprendre *pourquoi maintenant* est déjà un jugement de pertinence temporelle. En refusant ce jugement, v1 obligeait un autre composant à le refaire — ce qui viole précisément le principe de source unique de vérité que l'ADR prétend établir (Mission 7 du mandat le nomme explicitement : *« le FTE doit devenir la source de vérité de toute temporalité »*).

5. **Incohérence interne dans le pipeline.** v1 §3.3 énonçait que le FTE lit `Engagement.cadence` en entrée, mais le diagramme de pipeline en §3.6 plaçait Engagement *après* le FTE. C'est une erreur d'architecture, pas un détail rédactionnel : si le FTE dépend d'Engagement, Engagement doit être résolu avant, pas après. Corrigé en §4.6.

6. **Le calendrier fiscal non-standard était une question ouverte plutôt qu'une décision.** v1 §9 listait *« calendrier fiscal non-calendaire »* comme non traité. Pour un moteur qui prétend être « conscient du temps », laisser l'année fiscale elle-même non modélisée est une lacune de fond, pas un détail à reporter.

7. **Aucune notion de saisonnalité.** Absente de v1 alors qu'elle conditionne directement la pertinence des comparaisons (Axiome fondateur n°2 du mandat original : *« jamais dans l'absolu »*).

**Ce qui, à l'inverse, était juste en v1 et doit être conservé** — pour ne pas céder à la tentation de tout jeter au nom de la nouveauté :

- La discipline des invariants (INV-TIME-1 à 8) reste alignée avec la Constitution et n'a pas besoin d'être réinventée, seulement étendue aux nouveaux objets.
- La classification Supporting-mais-amont-de-tout (§3.2 de v1) reste correcte — la Mission 9 nuance le *rôle* du FTE, pas sa place dans la carte des Bounded Contexts (voir §4.7).
- Le contrat d'indépendance format (`PeriodObservation[]` en entrée, jamais Excel) reste correct et devient même plus important à mesure que le modèle s'enrichit (voir §4.11).
- La discipline « jamais d'appel LLM à l'intérieur du FTE », déterminisme et reproductibilité, reste un pilier non négociable — et devient le socle sur lequel repose la nouvelle capacité de jugement de pertinence (§4.8).
- La stratégie de migration additive (nouveau module pur, aucune table existante modifiée) reste valide.

**Verdict : ni défense, ni démolition. v1 avait le bon squelette (frontière de Bounded Context, discipline d'invariants, indépendance de format, migration additive) mais un système d'organes insuffisant — le modèle d'objets qu'il produisait était trop pauvre pour porter le langage que le mandat original avait pourtant déjà nommé.** Cette v2 reconstruit le système d'organes en conservant le squelette.

---

## §2 — Le temps comme objet du domaine, pas comme calendrier (Mission 2)

Avant tout modèle, une clarification de méthode s'impose : penser le temps « en DDD » signifie refuser deux réflexes.

Le premier réflexe à refuser est technique : ne jamais partir de ce qu'un fichier Excel contient (une colonne de dates, un nom d'onglet) pour en déduire ce que le temps *signifie*. Le second réflexe à refuser est calendaire : ne jamais traiter une date comme une position sur une frise, interchangeable avec n'importe quelle autre date à intervalle égal. Un CFO ne raisonne jamais ainsi.

Ce qu'un CFO manipule réellement, en langage métier pur, jamais technique :

- Un **Moment** qui compte — pas une date, un instant chargé de sens (« nous venons de clôturer août », « le conseil se réunit dans dix jours »).
- Des **rythmes** — des retours réguliers d'obligations ou de rituels de gestion (clôture, budget, conseil, banque, audit, fiscal, paie, trésorerie, investissement), chacun avec son propre public et sa propre cadence.
- Des **fenêtres d'observation** — le temps qu'il faut laisser passer avant de pouvoir juger si une décision a produit son effet.
- Des **horizons de comparaison** — les points de référence pertinents pour donner un sens à un chiffre (le mois précédent, le même mois l'an dernier, le cumul depuis janvier, le budget).
- Une **fraîcheur** — la mesure de si l'information dont on dispose est encore utile, ou déjà périmée.
- Une **maturité de décision** — le fait qu'une recommandation ne se juge ni trop tôt, ni trop tard, mais à un moment précis de sa propre vie.

Aucun de ces six concepts ne nécessite de savoir ce qu'est une cellule Excel. C'est le test que ce document applique à chaque objet introduit ci-dessous (repris formellement en §4.11).

---

## §3 — Contexte et problème (repris et complétés de v1)

**Contexte.** ADR-001 laissait ouverte la question de l'événement qui marque une clôture de période (question ouverte n°2). ADR-002 §3.7 définissait `ReviewCadence` comme un concept contractuel déclaré, jamais appliqué automatiquement. Le Current Domain Model documente, en section G, l'absence totale de toute notion de « revue planifiée » dans le code actuel, et en section M (dette n°6) une mémoire scindée entre deux services (`memory_service.py`, `decision_memory_service.py`) qui ne se rejoignent jamais pour raconter une histoire temporelle continue.

**Problème A — aucune représentation du temps ne fait autorité.** Le Current Domain Model confirme (§F) qu'aucun événement de domaine nommé n'existe (`AnalysisCreated` etc. sont des inférences, pas du code), et que `arc_service.py` recalcule un âge en jours à six endroits indépendants, chacun pouvant diverger silencieusement.

**Problème B — les LLM improvisent le raisonnement temporel.** Aucun contexte temporel structuré n'est aujourd'hui injecté dans `call_analysis_v3`/`call_verification_v3` (`llm_service.py`) — seul l'`evidence_graph_section` l'est. Le temps, à la différence des faits financiers, n'est protégé par aucune Règle Absolue équivalente à la Règle n°6 (ancrage source).

**Problème C — aucun signal de fraîcheur ou de pertinence n'existe pour nourrir la future Attention Score (T4).** Sans un tel signal, l'Attention Score devra soit l'inventer elle-même (dupliquant la responsabilité), soit s'appuyer sur un proxy pauvre (`analyses.created_at`), déjà identifié comme insuffisant par le Blueprint.

**Problème D (nouveau, identifié par cette révision) — le FTE v1 ne répondait pas à la question du mandat original : pourquoi maintenant ?** Un moteur qui détecte des périodes sans juger de la pertinence temporelle d'une nouvelle analyse force ce jugement à être refait ailleurs, en dehors de toute discipline de déterminisme — très probablement par un LLM, ce que le mandat interdit explicitement.

---

## §4 — Décision

### 4.1 — Axiomes fondateurs du FTE (4 originaux + 3 nouveaux)

Les quatre axiomes du mandat original sont conservés tels quels (aucune donnée financière n'a de sens hors de sa dimension temporelle ; toute analyse se fait sur une période, dans un contexte, avec une fréquence, relativement à d'autres périodes ; Pepperyn doit comprendre pourquoi un fichier arrive maintenant ; Pepperyn doit être aussi conscient du temps que du montant).

Trois axiomes s'y ajoutent, rendus nécessaires par les Missions 4, 5 et 9 :

- **Axiome 5 — Un moment n'est jamais une date nue.** Chaque instant significatif pour un Engagement porte une signification métier explicite (une clôture qui commence, un cumul qui change, une recommandation qui devient évaluable) ; cette signification doit être rendue explicite dans le modèle, jamais laissée implicite dans le code consommateur.
- **Axiome 6 — Une organisation vit selon plusieurs rythmes simultanés, jamais un seul.** Comprendre le temps d'un Engagement, c'est savoir lequel de ses rythmes concurrents (clôture, conseil, banque, audit, fiscal…) est engagé à un instant donné, et pour quel public.
- **Axiome 7 — La pertinence temporelle se constate, elle ne se décide pas.** Le FTE peut et doit établir qu'un moment est temporellement significatif pour un Engagement donné (fait déterministe, vérifiable, rejouable) ; il ne doit jamais arbitrer où doit se porter l'attention limitée d'un utilisateur à travers un portefeuille entier (jugement de priorité comparative, hors de son ressort — voir §4.7).

Ces trois axiomes ne remplacent rien : ils rendent explicite ce que les quatre axiomes originaux impliquaient déjà sans le nommer.

### 4.2 — Classification stratégique (confirmée, nuancée)

Le FTE reste classé **Supporting — mais amont de tout**, au même titre que Client Engagement dans l'Ideal Domain Model. La Mission 9 (§4.7) élargit son rôle jusqu'à un jugement de pertinence par Engagement, mais ce jugement reste un fait constaté, jamais une priorisation comparative entre Engagements — c'est cette dernière capacité, seule, qui justifierait un reclassement en Core. Le FTE n'y prétend pas. La carte de Bounded Context de v1 §3.2 reste donc valide sans modification : Client Engagement → Data Ingestion & Normalization → **Financial Time Engine** → Financial Evidence & Truth / Exception & Reconciliation → Portfolio Attention & Prioritization → Advisory Judgment & Decision Memory → Reporting & Deliverables, en relation de Published Language avec les contextes Core en aval.

### 4.3 — Modèle de domaine : les nouveaux objets métier (Missions 3, 4, 5, 6)

Le FTE reste un **Domain Service** pur, sans identité ni persistance propre : `FinancialTimeEngine.buildContext(...) -> FinancialTemporalContext`. Ce qui change en profondeur, c'est la richesse de ce que cette fonction construit.

#### 4.3.1 — `BusinessMoment` (Value Object central, Mission 4)

Le concept qui manquait le plus en v1. Un `BusinessMoment` est la représentation du fait qu'un instant donné, pour un Engagement donné, porte une signification métier — jamais une date brute.

| Attribut | Rôle |
|---|---|
| `observedAt` | Date murale (wall-clock) à laquelle ce moment est interprété — jamais dérivée d'un fichier (réutilise INV-TIME-4) |
| `triggeringSignal` | Ce qui a déclenché la construction de ce moment : `new_period_observed` \| `scheduled_cycle_reached` \| `manual_upload` \| `anomaly_detected` |
| `interpretations` | Liste fermée et énumérable de significations constatées — jamais du texte libre : `period_closing_started`, `period_just_closed`, `ytd_updated`, `rolling12_updated`, `cycle_milestone_reached(cycle)`, `analysis_pertinent` (voir §4.8) |
| `affectedHorizons` | Les `ComparisonHorizon` dont la pertinence change du fait de ce moment |
| `affectedCycles` | Les `FinancialCycle` (§4.3.2) que ce moment croise |
| `recommendationImpacts` | Les recommandations existantes dont l'état temporel (§4.3.6) est susceptible de basculer du fait de ce moment |

**Invariants :**
- INV-MOMENT-1 : un `BusinessMoment` est toujours ancré à un `observedAt` réel, jamais à une date déduite du contenu d'un fichier (extension directe d'INV-TIME-4).
- INV-MOMENT-2 : `interpretations` ne peut jamais être enrichi par invention — une signification n'apparaît que si un signal déterministe et vérifiable la justifie (extension du principe « absence ≠ zéro » au temps, déjà INV-TIME-1). Un upload sans nouvelle donnée produit un `BusinessMoment` aux `interpretations` vides — ce n'est pas une erreur, c'est un fait honnête.
- INV-MOMENT-3 : déterminisme — mêmes signaux d'entrée (mêmes `PeriodObservation[]`, même `observedAt`, même historique), même `BusinessMoment`, toujours (extension d'INV-TIME-2).

**Événements produits :** `BusinessMomentRecognized` (systématique, à chaque traitement d'un nouvel upload) ; `ClosingWindowEntered`, `AnalysisPertinenceEstablished` (émis conditionnellement, selon les `interpretations` présentes).

**Consommateurs :** Recommendation Engine (T3, via `recommendationImpacts`), Attention Score (T4, un `BusinessMoment` avec `period_just_closed` et sans analyse consécutive est un signal fort), Review Briefing (peut désormais narrer « pourquoi maintenant » à partir de `interpretations`/`affectedCycles` plutôt que de recalculer un texte ad hoc), Portfolio (badge « nouveau moment métier »), Exports (peuvent citer le moment sans le recalculer).

#### 4.3.2 — `FinancialCycle` : une taxonomie, pas une liste (Mission 5)

Plutôt qu'une énumération plate des exemples du mandat, une classification par **pourquoi le cycle existe**, qu'un CFO reconnaît immédiatement :

| Catégorie | Nature | Exemples de `CycleType` | Qui la déclenche |
|---|---|---|---|
| **ClosingCycle** | Produit une période close, immuable | Monthly Closing, Quarter Closing, Annual Closing | Interne, discipline comptable |
| **PlanningCycle** | Tourné vers l'avenir, produit une projection, ne clôt rien | Budget Cycle, Forecast Cycle | Interne, choix de gestion |
| **ReviewCycle** | Consomme une période déjà close, à l'usage d'un public de gouvernance | Board Review, Bank Review, Cash Review, Investment Review | Interne ou contractuel, cadence propre — souvent plus lâche qu'un ClosingCycle sous-jacent (ex. clôture mensuelle, conseil trimestriel) |
| **ComplianceCycle** | Échéance imposée de l'extérieur, rigidité maximale | Audit Cycle, Tax Cycle, Payroll Cycle | Statutaire, non négociable |

`FinancialCycle` porte : `type`, `category`, `frequency` (réutilise `PeriodFrequency`), `typicalLag` (délai habituel, en jours, entre la fin de la période observée et le jalon du cycle — ce champ est la clé du raisonnement déterministe de la §4.8), `nextOccurrence` (dérivé).

Un Engagement porte **plusieurs** `FinancialCycle` simultanément — c'est le remplacement direct du `ManagementCycle` singulier de v1, et la réponse concrète à la Mission 5.

**`FiscalEvent` (VO distinct, plus léger)** : un jalon *irrégulier ou unique*, non récurrent selon une fréquence fixe (ex. « la date limite de dépôt fiscal de cette année précise »), à distinguer d'un `FinancialCycle` qui, lui, se répète structurellement. Cette distinction évite de forcer dans la même structure des choses qui n'ont pas la même nature (récurrence programmable vs échéance ponctuelle connue).

**Seasonality — délibérément non modélisée comme objet propre.** La saisonnalité n'est pas un cycle ni un moment : c'est une propriété qui module la pertinence d'un `ComparisonHorizon` (comparer décembre à novembre est moins pertinent pour un commerce saisonnier que comparer décembre à décembre N-1). Elle est donc portée comme un champ (`seasonalitySignal`) sur `ComparisonHorizon` (§4.3.4), pas comme un nouvel agrégat — lui donner un statut d'objet séparé aurait été une sophistication non justifiée (Article XII).

#### 4.3.3 — `FiscalCalendar` (nouveau, résout la question ouverte n°2 de v1)

VO porté par Engagement (lu, jamais possédé, par le FTE) : `fiscalYearStartMonth` (par défaut janvier, surchargeable), `fiscalYearStartDay`. Tous les calculs de `FiscalPeriod`, `fiscalYearToDate` et de jalons de `FinancialCycle` de type clôture annuelle se font relativement à ce calendrier, jamais à l'année calendaire par défaut implicite. Ce qui était une question ouverte non traitée en v1 devient une décision : le FTE n'assume jamais un exercice janvier-décembre sans confirmation — en l'absence de `FiscalCalendar` explicite sur l'Engagement, il utilise le calendrier civil comme valeur par défaut *documentée et signalée* (`TemporalWarning` de type `fiscal_calendar_assumed`), jamais comme un fait silencieux (encore une application d'INV-TIME-1).

#### 4.3.4 — Objets repris de v1, inchangés dans leur nature, reliés aux nouveaux concepts

`PeriodObservation`, `FiscalPeriod`, `PeriodFrequency`, `DataFreshness`, `TemporalWarning` sont conservés sans changement structurel — ils avaient déjà passé le test de la §2. `ComparisonHorizon` gagne un champ `seasonalitySignal` (voir 4.3.2) et son `relevance_reason` doit désormais pouvoir citer un `FinancialCycle` (ex. : « pertinent car Board Review dans 5 jours ») plutôt qu'une justification générique — voir §4.9 pour le modèle complet des horizons.

#### 4.3.5 — `AnalysisPertinence` (nouveau, Mission 9 / Mission 10)

Signal déterministe, par Engagement, répondant à la question « ce moment justifie-t-il une nouvelle analyse maintenant ? ». Ce n'est **pas** un score de priorité comparatif (ce rôle reste exclusivement à l'Attention Score, Core, T4) — c'est un fait constaté sur un seul Engagement à la fois, jamais une comparaison entre Engagements. Détail du raisonnement en §4.8.

`AnalysisPertinence` porte : `verdict` (`pertinent` \| `pas_encore` \| `sans_objet`), `reason` (référence structurée aux signaux qui l'ont produit — jamais du texte libre non traçable), `basedOnMoment` (référence au `BusinessMoment` qui l'a produit).

#### 4.3.6 — `RecommendationLifetime` et `RecommendationTemporalState` (Mission 6)

Remplace le `RecommendationTemporalWindow` plat de v1 par un vrai modèle à deux niveaux : des **dates ancrées** (faits) et un **état dérivé** (lecture temporelle, jamais stockée redondamment).

`RecommendationLifetime` (VO, fourni par le FTE à la proposition d'une Recommendation, en entrée du futur T3) :
- `proposedAt`
- `observationWindow` — un `TemporalWindow` (début/fin), pas une seule date de fin : certaines recommandations ont un effet observable dès l'exécution, d'autres seulement après un cycle complet
- `executedAt` (nullable — lu depuis Recommendation une fois T3 existant, jamais écrit par le FTE)
- `expectedEvaluationDate` (dérivée : fin de `observationWindow`)
- `expirationDate` (nullable — au-delà, la fenêtre d'opportunité de la recommandation est révolue, indépendamment de son évaluation)
- `reconsiderationTrigger` — de préférence un `FinancialCycle` plutôt qu'une date fixe (« à la prochaine clôture mensuelle », plus réaliste métier qu'un délai arbitraire en jours)

`RecommendationTemporalState` (dérivé, calculé à la demande par le FTE à partir de `RecommendationLifetime` + `today`/dernier `BusinessMoment` — jamais persisté, pour éviter une deuxième vérité concurrente avec le statut métier propre de Recommendation) :

| État | Condition |
|---|---|
| `premature` | avant le début de `observationWindow` — l'effet ne peut pas encore s'être manifesté |
| `awaited` | dans la fenêtre, non encore due |
| `due` | `expectedEvaluationDate` atteinte |
| `overdue` | au-delà de `expectedEvaluationDate` de plus d'un cycle pertinent (dérivé de `reconsiderationTrigger`, jamais d'une constante arbitraire) |
| `obsolete` | au-delà de `expirationDate`, ou supersédée par un `BusinessMoment` plus récent qui invalide les conditions d'origine |

**Distinction volontaire et explicite avec `Recommendation.status` (T3, business : proposée/acceptée/rejetée/exécutée) : ce sont deux axes orthogonaux.** L'un répond à « qu'a décidé le client ? », l'autre à « est-il temporellement approprié d'en évaluer l'effet ? ». Les confondre créerait exactement la duplication de vérité qu'Article X interdit — c'est pourquoi ils portent des noms distincts et qu'aucun des deux n'écrit dans l'espace de l'autre.

### 4.4 — Invariants (INV-TIME-1 à 8 conservés, 3 nouveaux)

INV-TIME-1 à 8 sont repris sans changement de fond (absence ≠ zéro appliqué au temps ; déterminisme ; `latestPeriod` toujours evidencé par une observation réelle ; `today` toujours mural ; non-bloquant ; source unique de vérité temporelle ; le silence n'est jamais une confirmation ; indépendance de format).

Trois invariants nouveaux, portés par les nouveaux objets :

- **INV-TIME-9** : `AnalysisPertinence` ne peut jamais être élevé au rang de priorité comparative entre Engagements — sa portée s'arrête à un seul Engagement à la fois (garde-fou direct contre le risque de dérive vers l'Attention Score, discuté en §4.7).
- **INV-TIME-10** : `RecommendationTemporalState` est toujours dérivé à la demande, jamais stocké — il ne doit jamais devenir une deuxième source de vérité concurrente de `Recommendation.status`.
- **INV-TIME-11** : en l'absence de `FiscalCalendar` explicite, le calendrier civil est utilisé par défaut mais toujours signalé par un `TemporalWarning` — jamais silencieusement.

### 4.5 — Événements métier (étendus)

Repris de v1 : `TemporalContextComputed`, `DataFreshnessDegraded`, `TemporalAnomalyDetected`, `TemporalAnomalyConfirmed`/`Dismissed`, `ManagementCycleInferred` (renommé `FinancialCycleInferred`, pluriel implicite), `RecommendationReviewDue`.

Nouveaux : `BusinessMomentRecognized`, `ClosingWindowEntered`, `AnalysisPertinenceEstablished`, `RecommendationBecameObsolete` (distinct de `RecommendationReviewDue` — le premier ferme une fenêtre, le second en ouvre une).

### 4.6 — Pipeline (Mission 8 — reordonné, avec justification)

Le pipeline de v1 contenait l'incohérence relevée en §1.5 : Engagement décrit comme une entrée du FTE, mais placé après lui dans le diagramme. La correction n'est pas cosmétique — elle change l'ordre réel des dépendances.

**Nouveau pipeline runtime :**

```
Upload
  → Résolution de l'Engagement (déjà implicite aujourd'hui via entity_id ;
    rendu explicite ici car le FTE en dépend directement — aucun nouveau code,
    seule la description du pipeline est corrigée)
  → Normalisation (ACL Data Ingestion & Normalization — produit
    PeriodObservation[] ET FinancialFact candidates, format-indépendant)
  → Financial Time Engine  ── dispose maintenant de PeriodObservation[]
    ET de l'Engagement (FiscalCalendar, FinancialCycle[], historique de
    BusinessMoment) : construit BusinessMoment, AnalysisPertinence,
    FinancialTemporalContext, et évalue RecommendationTemporalState pour
    les recommandations existantes de cet Engagement
  → Construction de l'Evidence Graph (pré-LLM), enrichie de références
    FiscalPeriod
  → Agents LLM (Analyse puis Vérification), consommant
    temporal_context_section au même titre qu'evidence_graph_section
  → Capture Evidence Ledger (post-LLM, point d'intégration T1C-A réel)
  → Recommendation Engine (T3, futur) — consomme RecommendationLifetime
    et les impacts de BusinessMoment sur les recommandations existantes
  → Attention Score (T4, futur) — consomme DataFreshness,
    TemporalWarning, AnalysisPertinence (jamais l'inverse)
  → Exports — projection pure, cite sans recalculer
```

**Ce qui a changé, et pourquoi :** la résolution d'Engagement est désormais explicitement *avant* le FTE, pas après — condition nécessaire pour que le FTE puisse lire `FiscalCalendar` et `FinancialCycle[]`. Le FTE évalue aussi désormais, au moment même de son exécution, l'impact du nouveau `BusinessMoment` sur les recommandations *existantes* de l'Engagement (ce que v1 laissait implicite et différé) — c'est ce qui permet à `RecommendationReviewDue`/`RecommendationBecameObsolete` d'être émis au bon moment plutôt que découverts a posteriori.

Le reste de l'ordre (Evidence Graph → LLM → Evidence Ledger → Recommendation → Attention → Exports) reste identique à v1 et au mandat original : rien ne justifiait de le changer, et le point d'intégration technique réel (`evidence_graph_section` dans `run_full_pipeline`) confirme que ce n'est pas qu'un ordre théorique.

### 4.7 — Le FTE juge-t-il aussi la pertinence ? (Mission 9 — position argumentée)

Deux formes de « pertinence » existent, et les confondre est le piège que cette question invite à éviter.

**Pertinence temporelle** — « ce moment est-il significatif pour *cet* Engagement, maintenant ? ». C'est un fait déterministe, calculable à partir de signaux calendaires et de données, sans comparaison avec quoi que ce soit d'autre. Ce n'est pas un jugement au sens où l'entend la Constitution (Article II, jugement humain) ni une priorisation — c'est de la même nature que « cette Evidence n'a pas de provenance » : un constat, pas un choix. **Cette forme de pertinence doit appartenir au FTE.** La refuser au FTE, comme le faisait v1, ne supprime pas le besoin — elle le déplace vers un composant moins outillé pour le traiter de façon déterministe, ou pire, vers un LLM, ce que le mandat interdit explicitement.

**Pertinence de priorité** — « où dois-je porter mon attention limitée en premier, à travers *tout* mon portefeuille ? ». Celle-ci est intrinsèquement comparative, pondère la matérialité, le risque, la fiabilité historique — des dimensions que le FTE, par construction et par frontière de Bounded Context, ne connaît pas. **Cette forme reste exclusivement celle de l'Attention Score (Core, T4).**

Conclusion : v1 avait raison de refuser au FTE tout pouvoir de *calcul* (aucune comparaison réalisée, aucun score produit) mais avait tort de lui refuser tout pouvoir de *constat* de pertinence temporelle — c'est précisément cette distinction que l'Axiome 7 (§4.1) fixe, et qu'INV-TIME-9 protège contre toute dérive future.

### 4.8 — Pourquoi Pepperyn sait qu'une nouvelle analyse devient pertinente (Mission 10 — raisonnement entièrement déterministe)

**Exemple du mandat : aujourd'hui 02/10/2019, le fichier contient désormais septembre. Pourquoi le FTE juge-t-il qu'une nouvelle analyse est pertinente maintenant, et pourquoi ne l'aurait-il pas jugé le 28/09 ?**

Le raisonnement combine deux signaux, tous deux déterministes, tous deux nécessaires — ni l'un ni l'autre seul ne suffit :

1. **Signal de delta de période** — une nouvelle `PeriodObservation` est apparue, dont la `FiscalPeriod` est postérieure à la dernière `latestPeriod` connue pour cet Engagement (août → septembre). Sans ce signal, aucune date, aussi favorable soit-elle, ne déclenche quoi que ce soit — c'est pourquoi le 28/09 ne produit rien : à cette date, aucune nouvelle période n'était encore apparue dans les données, quelle que soit la position dans le calendrier.

2. **Signal de plausibilité de clôture** — `observedAt` (02/10) tombe dans la fenêtre de plausibilité du `typicalLag` du `ClosingCycle` de type Monthly Closing pertinent pour cet Engagement (par exemple, une clôture mensuelle plausible entre J+1 et J+10 après la fin du mois). Ce signal seul, sans le premier, ne produirait rien non plus : être début octobre ne signifie rien si aucune nouvelle donnée de septembre n'est arrivée.

`AnalysisPertinence.verdict = pertinent` est produit **seulement quand les deux signaux coexistent** : une nouvelle période est apparue, ET le moment observé est cohérent avec une clôture plausible de cette période. C'est ce couplage — jamais l'un des deux signaux isolément — qui rend le raisonnement robuste sans recourir à un LLM : il repose uniquement sur une comparaison d'ensembles de `PeriodObservation` (fait) et une comparaison de dates à un `typicalLag` déclaré ou observé (fait), jamais sur une interprétation.

Si `observedAt` s'était situé en décembre avec toujours septembre comme dernière période connue, le signal 1 serait absent (aucune période plus récente que celle déjà connue) et `AnalysisPertinence.verdict = pas_encore` — mais un `TemporalWarning` de type `overdue_period` serait émis séparément, car l'absence de nouvelle donnée trois mois après une clôture plausible est elle-même un fait notable (INV-TIME-1 : l'absence n'est jamais silencieuse).

### 4.9 — Horizons temporels multiples (Mission 11)

Le principe retenu, conservé de v1 et renforcé : **un horizon n'est jamais unique, c'est toujours un ensemble**, parce que des publics différents (`ReviewCycle` différents) portent un intérêt à des horizons différents au même instant — un Board Review s'intéresse au trimestre et au cumul annuel, une Bank Review au Rolling 12 (souvent lié à des covenants), une revue mensuelle interne au mois courant contre le mois précédent.

`ComparisonHorizon[]` reste donc une liste, jamais un choix unique, avec chaque entrée justifiée (`relevance_reason`) par référence explicite à un `FinancialCycle` imminent ou à un `seasonalitySignal` — ce qui remplace une justification générique par une traçabilité réelle. Les types repris de v1 (`vs_M-1`, `vs_quarter`, `ytd`, `rolling12`, `vs_N-1`, `vs_budget`) restent le socle ; `vs_budget` n'est proposé que si un `PlanningCycle` de type Budget Cycle existe pour l'Engagement — sinon, il est absent plutôt qu'halluciné (encore INV-TIME-1).

### 4.10 — Cartographie des dépendances (Mission 7)

| Composant | Nature de la dépendance | Statut |
|---|---|---|
| **Portfolio** | Lit `DataFreshness`, `BusinessMoment` pour badges/tri | Dépendance cible ; `arc_service.py` recalcule aujourd'hui un âge en jours en 6 endroits indépendants — convergence non traitée par cette ADR (reste en §10) |
| **Attention Score (T4)** | `DataFreshness`, `TemporalWarning[]`, `AnalysisPertinence`, `BusinessMoment.interpretations` comme signaux d'entrée | Dépendance cible, composant non construit |
| **Recommendation Engine (T3)** | `RecommendationLifetime` en entrée à la proposition, `RecommendationTemporalState` en lecture continue, `BusinessMoment.recommendationImpacts` | Dépendance cible, composant non construit |
| **Review Briefing** (Capability 3, existant) | Pourrait citer `BusinessMoment.interpretations`/`affectedCycles` au lieu du texte ad hoc actuel (`temporal_context` généré dans `arc_service.py`) | Dépendance réelle non satisfaite aujourd'hui — non migrée par cette ADR |
| **Exports** | Cite `FiscalPeriod`, `ComparisonHorizon`, `BusinessMoment` — ne recalcule jamais | Dépendance cible, conforme à la règle « le renderer affiche » déjà en vigueur (Current Domain Model §K) |
| **Decision Memory / Advisory Judgment (T3/T5)** | Une comparaison outcome-vs-attendu n'a de sens que si `RecommendationTemporalState ∈ {due, overdue}` | Dépendance cible |
| **Engagement (T2)** | Bidirectionnel : le FTE lit `cadence`/`FiscalCalendar` ; `FinancialCycleInferred` propose (jamais n'écrit automatiquement) un raffinement, sujet à confirmation humaine | Confirmé v1, inchangé |
| **Evidence Ledger (T1)** | Les faits capturés référencent une `FiscalPeriod` structurée plutôt qu'un texte libre | Confirmé v1, inchangé |
| **Exception & Reconciliation** | L'urgence d'une exception détectée à la frontière d'une clôture plausible (`BusinessMoment` avec `period_closing_started`) peut légitimement différer de celle d'une exception détectée en milieu de période | Dépendance légère, nouvelle, à ne pas sur-construire maintenant |
| **Client Communication (Generic)** | Pourrait utiliser `BusinessMoment` pour le timing de notifications (« vos données de septembre sont prêtes ») | Dépendance légère, périphérique |
| **Time & Billing / Onboarding (Generic)** | **Non-dépendant, et ne doit pas le devenir** — aucune donnée temporelle métier ne doit fuiter vers un sous-domaine Generic ; le rappeler explicitement prévient la dérive de portée déjà identifiée comme le risque le plus important en v1 §3.12 | Garde-fou explicite |

### 4.11 — Indépendance vis-à-vis du format source, re-vérifiée (Mission 12)

Chaque nouvel objet introduit par cette révision est passé au test de la §2 : `BusinessMoment` se construit à partir de `PeriodObservation[]` déjà normalisées et d'un historique d'Engagement — jamais d'une cellule ou d'un nom d'onglet. `FinancialCycle`/`FiscalEvent`/`FiscalCalendar` sont des faits déclarés ou inférés sur l'organisation elle-même, indépendants de tout fichier. `AnalysisPertinence`, bien que nouveau et proche d'un jugement, reste construit uniquement à partir du delta d'ensembles de `PeriodObservation` et de dates — jamais de structure de fichier. Le contrat d'entrée du FTE reste strictement `PeriodObservation[] + Engagement + today`, inchangé depuis v1, étendu en confiance plutôt qu'en surface : plus le modèle est riche, plus il est impératif qu'aucun de ces nouveaux objets ne puisse être court-circuité par un accès direct au fichier source — INV-TIME-8 est donc explicitement réaffirmé comme s'appliquant à *tous* les objets de cette révision, pas seulement à ceux de v1.

### 4.12 — Impacts sur Engagement, Recommendation, Evidence Ledger, Attention Score

Repris et affinés de v1 : voir §4.6 (pipeline), §4.9 (Recommendation), §4.10 (cartographie complète). Point nouveau : l'Evidence Ledger peut désormais référencer une `FiscalPeriod` construite sous un `FiscalCalendar` non-standard sans ambiguïté — ce qui n'était pas garanti tant que la question de l'année fiscale restait ouverte.

### 4.13 — Stratégie de migration (inchangée sur le fond)

Additive, non bloquante, nouveau module pur (`services/financial_time_engine.py`, non encore créé). Le positionnement en Phase T2.5 reste justifié : le FTE atteint sa pleine valeur une fois Engagement disponible (FiscalCalendar, FinancialCycle[]), mais reste utile en amont de T3 (9 des 10 responsabilités du mandat original fonctionnent sans Recommendation Engine — seule `RecommendationTemporalState` reste « disponible mais non consommée » tant que T3 n'existe pas, exactement comme en v1).

### 4.14 — Risques d'architecture (repris, complétés)

Les 5 risques de v1 restent valides (détection silencieusement incorrecte, double calcul pendant la transition avec `arc_service.py`, ambiguïté PeriodFrequency/ReviewCadence, coût de requête historique, dérive de portée). Deux risques nouveaux, propres à cette révision :

- **Risque de complexité du modèle** — le passage d'un objet plat (`ManagementCycle`) à une taxonomie (`FinancialCycle[]` à 4 catégories) et d'une fenêtre plate à un état dérivé (`RecommendationTemporalState`) augmente réellement la surface conceptuelle. Mitigation : chaque objet nouveau a été justifié individuellement par un besoin métier nommé (Missions 3 à 6) — mais la vigilance contre la sur-ingénierie doit rester active à l'implémentation.
- **Risque sur la frontière `AnalysisPertinence`** — INV-TIME-9 la protège en théorie, mais rien n'empêche techniquement un futur développeur pressé de l'utiliser directement comme proxy de priorité dans le Portfolio, recréant la confusion que l'Axiome 7 cherche à prévenir. Ce risque n'est pas éliminé par le seul texte de l'ADR — il devra être rappelé au moment de l'implémentation du Portfolio et de l'Attention Score.

---

## §5 — Alternatives rejetées (5 de v1 confirmées, 3 nouvelles)

Confirmées sans changement : laisser les LLM déduire le temps eux-mêmes (Article III) ; ajouter les champs temporels directement sur Engagement/Evidence Ledger sans nouveau composant (mélange de responsabilités) ; construire le FTE comme utilitaire technique invisible du modèle de domaine (contredit Axiome 4 et Article XII) ; classer le FTE en Core (raisonnement §4.2) ; faire dépendre le FTE de T3 avant sa construction (viole la migration incrémentale).

Nouvelles :

- **Donner à `AnalysisPertinence` le pouvoir de prioriser entre Engagements** — rejetée : effacerait la frontière avec l'Attention Score et reclasserait de fait le FTE en Core sans le dire (voir §4.7, Axiome 7).
- **Modéliser un unique `ManagementCycle` enrichi plutôt qu'une taxonomie `FinancialCycle`** — rejetée : un seul objet, même enrichi de champs, ne peut représenter plusieurs cycles concurrents à publics différents sans perdre la distinction qui fait leur utilité (Mission 5).
- **Stocker `RecommendationTemporalState` en base plutôt que le dériver à la demande** — rejetée : créerait une deuxième source de vérité à synchroniser avec `Recommendation.status`, violation directe d'Article X et d'INV-TIME-10.

---

## §6 — Tests d'acceptation (8 de v1 confirmés, 5 nouveaux)

Confirmés : détection de période sur 3 formats d'exemple ; déterminisme/reproductibilité ; détection de retard ; détection d'anomalie de donnée future avec confirmation obligatoire ; zéro appel réseau/LLM à l'intérieur du FTE ; taux de détection de format ambigu mesuré empiriquement sur 20+ fichiers réels ; zéro régression d'export ; `Engagement.cadence` jamais écrit par le FTE.

Nouveaux :

9. Sur l'exemple 02/10/2019 avec apparition de septembre (§4.8), `AnalysisPertinence.verdict = pertinent` ; sur le même Engagement au 28/09 sans nouvelle période, `verdict = pas_encore`.
10. Un Engagement sans `FiscalCalendar` explicite produit un `TemporalWarning(fiscal_calendar_assumed)` dès le premier calcul de `fiscalYearToDate`.
11. Un `RecommendationLifetime` avec `observationWindow` non commencée produit `RecommendationTemporalState = premature`, jamais `awaited` par erreur.
12. Deux Engagements aux profils de cycles différents (l'un avec Board Review trimestriel, l'autre sans) produisent des `ComparisonHorizon[]` différents pour un même mois calendaire — preuve que l'horizon dépend du profil, pas de la date seule.
13. `AnalysisPertinence` ne référence jamais, dans son `reason`, un autre Engagement que celui pour lequel il est calculé (test de non-régression direct sur INV-TIME-9).

---

## §7 — Rollback (inchangé)

Additif uniquement, aucune table existante modifiée. Trivial.

---

## §8 — Conformité à la Constitution

| Article | Conformité |
|---|---|
| III (La Vérité) | `AnalysisPertinence` et `BusinessMoment` sont traçables à leurs signaux d'origine, jamais inventés (INV-MOMENT-2, INV-TIME-1) |
| IV (Le Modèle Métier) | Aucun des 6 objets permanents n'est dupliqué ; le FTE alimente, ne remplace jamais Engagement/Recommendation |
| VII (L'Attention) | Frontière stricte entre pertinence temporelle (FTE) et priorité comparative (Attention Score), protégée par Axiome 7 et INV-TIME-9 |
| IX (L'Évolution) | Chaque objet nouveau répond à un besoin nommé par le mandat (Missions 3-6), aucun ajouté par anticipation spéculative |
| X (Les Interdictions) | `RecommendationTemporalState` dérivé, jamais stocké, pour éviter une deuxième vérité (INV-TIME-10) |
| XI (Tests de Conformité) | Voir §6, tests 9-13 spécifiquement conçus pour vérifier les nouvelles frontières |
| XII (Principes d'Architecture) | Simplicité vérifiée objet par objet (§5, alternatives rejetées) ; représentation unique préservée |

---

## §9 — Traçabilité

Origine : mandat « ADR-003 v2 — Transformer le Financial Time Engine en véritable moteur temporel du domaine ». Ferme la question ouverte n°2 d'ADR-001 (événement de clôture) de façon plus complète que v1 (via `FinancialCycle`/`BusinessMoment`). Ferme la question ouverte n°2 de v1 elle-même (calendrier fiscal non-calendaire, via `FiscalCalendar`, §4.3.3). Étend, sans la rouvrir, la décision d'ADR-001A (ownership de l'Evidence Ledger par Engagement) : `FiscalPeriod` référencée par l'Evidence Ledger hérite du `FiscalCalendar` de ce même Engagement.

---

## §10 — Questions ouvertes (revues)

1. Persistance de `FinancialTemporalContext`/`BusinessMoment` eux-mêmes : toujours non tranchée — probable candidat à une table d'historique légère, mais hors périmètre de cette ADR.
2. Granularité minimale de détection (hebdomadaire) : toujours non vérifiée empiriquement.
3. Qui, côté UX, déclenche la reconsidération d'un `FinancialCycleInferred` divergent : hors périmètre, renvoyé à une future spec produit.
4. Convergence avec les calculs d'âge ad hoc de `arc_service.py` : délibérément non traitée ici — nommée explicitement en §4.10 comme dette non résorbée par cette ADR.
5. Le `typicalLag` d'un `FinancialCycle` (§4.3.2, clé du raisonnement §4.8) : sa valeur initiale sera-t-elle déclarée par l'utilisateur, apprise empiriquement, ou les deux ? Non tranché — nécessaire avant implémentation du test d'acceptation n°9.

---

## §11 — Auto-critique et notation

**Hypothèses fragiles.** Le raisonnement de pertinence (§4.8) suppose un `typicalLag` fiable par `FinancialCycle` — sans données empiriques sur au moins quelques dizaines d'Engagements réels, sa valeur initiale sera nécessairement une estimation, pas une mesure. La taxonomie à 4 catégories (§4.3.2) est un design cohérent, mais reste une hypothèse de modélisation, non validée face à des cas réels de CFO externes aux rythmes atypiques (entreprises multi-entités avec calendriers fiscaux différents par filiale, par exemple, non traité).

**Décisions encore à valider.** Le choix de dériver `RecommendationTemporalState` à la demande plutôt que de le persister (INV-TIME-10) est défendable en théorie mais suppose que sa recalculation reste bon marché à l'échelle d'un portefeuille — non vérifié en pratique tant que T3 n'existe pas. Le mécanisme de valeur par défaut du `FiscalCalendar` (calendrier civil + `TemporalWarning`, §4.3.3) est une décision réversible mais engageante dès la première Evidence capturée.

**Risques architecturaux persistants.** La frontière entre `AnalysisPertinence` (FTE) et l'Attention Score (T4) est protégée par un invariant nommé (INV-TIME-9) mais aucun invariant textuel ne garantit qu'elle sera respectée à l'implémentation — seule une revue de code au moment de construire l'Attention Score peut réellement la faire tenir. La complexité ajoutée (taxonomie de cycles, état dérivé de recommandation, calendrier fiscal) est justifiée objet par objet, mais leur somme constitue une charge cognitive réelle pour quiconque implémentera ce module — un risque de dérive vers la sur-ingénierie reste ouvert.

**Alternatives sérieuses écartées, et pourquoi.** Confier à `AnalysisPertinence` un rôle de priorisation aurait simplifié l'architecture (un seul signal au lieu de deux couches) mais aurait directement recréé la confusion Core/Supporting qui a nécessité l'Axiome 7 — écartée pour préserver l'intégrité de la frontière de Bounded Context, jugée plus importante qu'une simplification de court terme. Stocker `RecommendationTemporalState` aurait simplifié les lectures répétées mais aurait recréé un risque de double vérité déjà identifié comme faute structurelle ailleurs dans le domaine (Current Domain Model §M, dette n°1 — cinq représentations concurrentes du même résultat d'analyse) — écartée précisément parce que cette dette existante est l'exemple même de ce que cette ADR doit éviter de reproduire.

**Notation.**

- **ADR-003 v1 : 6/10.** Discipline d'ingénierie solide (invariants, indépendance de format, non-blocage, alignement constitutionnel) mais modèle d'objets insuffisant pour porter le langage que le mandat original avait pourtant déjà nommé : un scalaire `today` sans signification, un cycle unique là où plusieurs coexistent réellement, une fenêtre de recommandation réduite à quatre dates, un rôle de pertinence refusé par excès de prudence au point de se contredire avec ses propres axiomes fondateurs, une incohérence de séquence dans son propre pipeline.
- **ADR-003 v2 : 8.5/10, pas 10/10.** L'écart avec v1 se justifie par l'introduction d'un véritable objet de sens (`BusinessMoment`), d'une taxonomie de rythmes cohérente plutôt qu'arbitraire, d'un modèle d'état pour les recommandations, d'un raisonnement de pertinence entièrement déterministe et justifié sur l'exemple exact du mandat, d'une frontière explicite et outillée (Axiome 7, INV-TIME-9) entre constat temporel et priorité comparative, et de la correction d'une véritable erreur de séquence dans le pipeline. Le score reste sous 10 parce que plusieurs de ces constructions (`typicalLag`, la taxonomie à 4 catégories, la dérivation à la demande de `RecommendationTemporalState`) sont des hypothèses de conception cohérentes mais non encore éprouvées contre des données réelles ou contre l'implémentation de T3 — une architecture ne mérite pas 10/10 tant qu'elle n'a pas rencontré la résistance du réel.

---

**ADR-003 v2 READY FOR REVIEW. REMPLACE ADR-003 v1 INTÉGRALEMENT. AUCUN CODE MODIFIÉ.**
