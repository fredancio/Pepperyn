# ADR-003 — Financial Time Engine

**Phase :** T2.5 du Transformation Blueprint *(ordre d'implémentation — voir §0 pour la distinction avec l'ordre d'exécution)*
**Statut :** Proposé, pour revue — **aucun code, aucune migration, aucun modèle Pydantic, aucun prompt n'est modifié par ce document**
**Sources autorisées :** Pepperyn Constitution v1.0 · Ideal Domain Model (Fractional CFO) · Current Domain Model · Transformation Blueprint (§B, §E) · ADR-001 (Evidence Foundation) · ADR-001A (Evidence Ownership) · ADR-002 (Engagement Foundation)
**Nature :** décision d'architecture. Introduit un nouveau composant de domaine de premier niveau. Ne redirige aucun consommateur existant.

---

## 0. Avertissement préalable — état réel du dépôt à la date de ce document

Avant toute chose, une divergence a été constatée en préparant cette ADR et doit être signalée plutôt que passée sous silence (Constitution, Article III — la donnée prime sur la narration, y compris la narration produite par les sessions précédentes) : **`evidence_ledger_service.py`, `engagement_service.py`, `evidence_capture.py` et les migrations `v18`/`v19`/`v20` n'existent, à ce jour, sur aucune branche fusionnée dans `main`.** Ils existent, complets et apparemment aboutis, sur des branches non fusionnées (`feature/t1c-b-atomic-financial-facts`, `feature/t2a-engagement-persistence`). `main` ne contient que `backend/models/financial_truth.py` — le module de typage dormant, pas la persistance.

Cette ADR est écrite comme si T1 (Evidence Ledger) et T2 (Engagement) étaient l'état cible déjà accepté — ce qu'ils sont, au sens architectural (ADR-001 et ADR-002 sont **ACCEPTED**). Mais toute PR d'implémentation qui suivra cette ADR devra d'abord clarifier, avec vous, si elle part de `main` (auquel cas T1/T2 doivent d'abord être fusionnés) ou de la branche `feature/t2a-engagement-persistence` (auquel cas T1/T2 sont déjà là). Ce point n'est pas une objection à cette conception — c'est une condition préalable à sa mise en œuvre, à trancher avant d'écrire une seule ligne.

---

## 1. Contexte

Les quatre premières décisions d'architecture de cette transformation (ADR-001, ADR-001A, ADR-002) ont construit, dans l'ordre, la preuve financière (Evidence Ledger) et la relation continue (Engagement). Les deux documents ont, chacun indépendamment, buté sur la même question sans la résoudre :

- ADR-001, question ouverte n°2 : *« Quel événement marque, en l'absence d'une Cadence contractuelle formalisée, la clôture d'une période et donc le passage d'un Evidence Ledger à l'état immuable ? »*
- ADR-002 §3.7 : *« La période de revue est un concept défini mais non encore appliqué [...]. Le mécanisme visé à terme — "c'est le calendrier qui déclenche, jamais un utilisateur qui uploade" — appartient à une phase ultérieure du Blueprint. »*

Ce n'est pas une coïncidence : les deux documents ont correctement identifié le même trou, sans pouvoir le combler, parce que combler ce trou exige un composant de domaine à part entière — pas un attribut de plus sur `Engagement` ou sur `EvidenceLedger`. C'est ce composant que cette ADR introduit.

Le constat qui motive cette ADR dépasse cependant la seule clôture de période. Examiné dans le code réel, le temps est aujourd'hui traité de trois façons incohérentes à la fois :

1. **Recalculé, dupliqué, à l'endroit où il est affiché** — `arc_service.py` calcule `(datetime.now() - dt).days` indépendamment à six endroits différents pour produire des textes comme *"Recommandé il y a 45 jours"*, sans qu'aucun de ces calculs ne partage une notion commune de période, de fraîcheur ou d'horizon de comparaison.
2. **Demandé à l'utilisateur, jamais déduit des données** — `InputBar.tsx` (mode `uploadOnly`) fait choisir manuellement à l'utilisateur, à chaque upload, la période couverte par son fichier (1 à 120 mois) et une date de projection cible. Le système ne regarde jamais le fichier lui-même pour vérifier, corriger ou même simplement confirmer ce que l'utilisateur a déclaré.
3. **Absent du raisonnement du LLM** — aucun prompt du pipeline (`call_analysis_v3`, `call_verification_v3`) ne reçoit aujourd'hui d'information structurée sur la période, la fréquence, ou les comparaisons pertinentes. Si un LLM produit une comparaison temporelle dans son texte, c'est une reconstruction implicite, non vérifiable, non déterministe — exactement le type d'affirmation que l'Article III de la Constitution interdit de présenter comme un fait.

Le Modèle Idéal ne nomme pas explicitly un « Financial Time Engine » comme Bounded Context séparé, mais il pose déjà, dans son langage ubiquitaire, `Cadence` (« le rythme contractuel de revue [...] qui détermine quand une nouvelle période "s'ouvre" ») et fait de l'ouverture de période l'événement générateur de toute la chaîne (§A : *« Objet qui génère toute la chaîne [...] : l'ouverture d'une nouvelle période comptable »*). Cette ADR ne contredit donc rien du Modèle Idéal — elle rend explicite et implémentable un concept qu'il présuppose déjà sans le détailler.

---

## 2. Problème

Trois problèmes précis, indépendants mais liés :

**Problème A — le temps n'a pas de représentation faisant autorité.** Il existe aujourd'hui trois représentations partielles et non reliées du temps dans le domaine : la date de dernier upload (`analyses.created_at`), la déclaration manuelle de l'utilisateur (`analysis_period_months`, `target_date`), et les calculs d'ancienneté ad hoc d'`arc_service.py`. Aucune n'est faisant autorité pour les deux autres ; elles peuvent diverger silencieusement (un utilisateur qui se trompe de période déclarée ne sera jamais contredit par le système).

**Problème B — les LLM raisonnent sur un temps qu'ils inventent.** Sans contexte temporel structuré injecté dans le prompt, toute affirmation temporelle produite par un agent (« ce trimestre », « par rapport à l'an dernier ») est une reconstruction non vérifiable — en violation directe de l'Article III (« une affirmation qui ne peut pas être reliée à sa source [...] doit toujours être présentée comme telle ») appliqué au temps plutôt qu'au montant.

**Problème C — aucun signal de fraîcheur ni d'anomalie temporelle n'existe.** Rien dans le domaine ne répond aujourd'hui à *« ces données sont-elles à jour ? »*, *« ce fichier est-il cohérent avec la date d'aujourd'hui ? »*, ou *« quand la prochaine analyse est-elle attendue ? »*. C'est un manque direct pour le futur `AttentionScore` (Blueprint C.6, T4) : la fraîcheur des données est l'un des signaux que le Blueprint anticipe déjà (« ancienneté de la dernière revue »), mais sans FTE, ce signal reste un calcul grossier (`analyses.created_at` brut) plutôt qu'un jugement temporel structuré (attendu vs observé, complet vs partiel).

**Ce que ce document ne résout pas :** il ne construit pas de connecteur ERP, pas d'ingestion multi-source, pas de calendrier fiscal paramétrable par pays. Il construit le composant qui *consommera* ces entrées une fois qu'elles existeront, sans dépendre d'aucune d'elles aujourd'hui.

---

## 3. Décision

**Le domaine adopte le Financial Time Engine (FTE) comme Domain Service de premier niveau, responsable exclusif de la construction du contexte temporel — sans jamais réaliser d'analyse financière lui-même — et produisant un objet immuable, `FinancialTemporalContext`, consommé en lecture seule par tous les autres composants du pipeline.**

Le détail suit, organisé selon les 9 livrables demandés.

### 3.1 Axiomes fondateurs du Financial Time Engine

Ces quatre axiomes ont le même statut, pour ce sous-domaine, que les 12 Axiomes Fondateurs ont pour l'ensemble du domaine (Constitution, Annexe) — ils n'ajoutent rien à la Constitution, ils l'appliquent au temps :

1. **Aucune donnée financière n'a de sens indépendamment de sa dimension temporelle.** Corollaire direct de l'Article III appliqué au temps : un montant sans période est aussi peu fiable qu'un montant sans source.
2. **Toute analyse est réalisée sur une période, dans un contexte, avec une fréquence, relativement à d'autres périodes — jamais dans l'absolu.** Une analyse qui ne déclare pas ces quatre dimensions n'est pas une analyse incomplète ; c'est une analyse dont la validité ne peut pas être évaluée.
3. **Pepperyn ne doit jamais seulement analyser un fichier — il doit comprendre pourquoi ce fichier arrive maintenant, ce que cela signifie dans le calendrier financier, quelles comparaisons deviennent pertinentes, et quelles décisions doivent être réévaluées.** C'est l'axiome qui justifie que le FTE consulte l'historique (analyses passées, décisions passées), pas seulement le fichier courant.
4. **Pepperyn doit être conscient du temps, aussi fondamentalement que de sa compréhension des montants.** C'est l'axiome qui justifie la position du FTE dans le pipeline (§3.6) : avant toute interprétation, jamais après.

Ces axiomes se rattachent directement à trois des 12 Axiomes Fondateurs déjà adoptés : **Axiome 3** (« l'absence de donnée n'est jamais un zéro » — étendu ici à l'absence de période détectable, §3.4 INV-TIME-1), **Axiome 6** (« une seule vérité ; jamais deux versions qui se contredisent » — étendu au temps, §3.4 INV-TIME-6), **Axiome 10** (« la technologie change ; le domaine demeure » — c'est l'axiome qui fonde l'exigence d'indépendance vis-à-vis du format Excel, §3.7).

### 3.2 Classification stratégique et placement dans la carte des Bounded Contexts

**Classification retenue : Supporting — mais amont de tout, au même titre que Client Engagement.** Ce n'est pas une sous-estimation de son importance : le Modèle Idéal qualifie déjà `Client Engagement` de la même façon (« Supporting, mais AMONT de tout ») sans que cela diminue son caractère structurant. La différenciation concurrentielle de Pepperyn continue de résider dans ce que le domaine *fait* du temps (Attention, Recommendation) — pas dans le calcul du calendrier lui-même, qui est un problème résolu et généralisable (tout logiciel financier sérieux doit le résoudre correctement, ce n'est pas un avantage compétitif en soi). **Alternative rejetée :** classer FTE en Core au motif que la Constitution en fait un axiome fondateur — rejetée parce que la Constitution élève des *principes* (le temps compte, la preuve compte), pas nécessairement chaque *composant* qui les sert, au rang de Core ; l'Evidence Ledger lui-même est Core parce qu'il porte la confiance différenciante, alors que le FTE reste un service de support à cette confiance, pas la confiance elle-même.

Position dans la carte des Bounded Contexts (Ideal Domain Model, §D) — un nouveau nœud inséré strictement en amont de `Financial Evidence & Truth`, recevant directement depuis `Data Ingestion & Normalization` :

```
 Client Engagement (Supporting, amont)
        │ Published Language : engagement_id, Cadence (si déjà connue)
        ▼
 Data Ingestion & Normalization (Supporting)
        │ Published Language : PeriodObservation[] (voir §3.7 — jamais du Excel brut)
        ▼
 Financial Time Engine (NOUVEAU — Supporting, amont de tout le Core)
        │ Published Language : FinancialTemporalContext
        ▼
 Financial Evidence & Truth (Core) ──▶ Exception & Reconciliation (Core)
        │                                        │
        └──────────────┬─────────────────────────┘
                        ▼
          Portfolio Attention & Prioritization (Core)
                        │
                        ▼
          Advisory Judgment & Decision Memory (Core)
                        │
                        ▼
          Reporting & Deliverables (Supporting, discipline Core)
```

**Relation clé (pattern DDD explicite) :** `Financial Time Engine → tous les contextes en aval` est une relation de **Published Language**, exactement du même type que celle déjà établie pour `Client Engagement` (Ideal Domain Model §D). Chaque contexte en aval consomme `FinancialTemporalContext` par sa forme publiée, sans connaître la logique interne de détection — au même titre qu'ils consomment `engagement_id` sans connaître la logique commerciale de l'Engagement.

### 3.3 Modèle de domaine — objets

**Le Financial Time Engine lui-même est un Domain Service, pas un agrégat.** Il n'a pas d'identité, pas de cycle de vie, pas de persistance propre au sens d'un agrégat racine — exactement comme le service qui construit l'Evidence Graph aujourd'hui (`_run_evidence_graph_agent`) n'est pas un agrégat. Sa signature conceptuelle :

```
FinancialTimeEngine.buildContext(
    periodObservations: PeriodObservation[],   // voir §3.7 — jamais de format source
    historicalAnalyses: AnalysisHistoryEntry[], // dates + périodes des analyses passées de cet Engagement
    historicalDecisions: DecisionHistoryEntry[],// dates + statuts des Recommendations/Arcs passés
    engagementCadence: ReviewCadence | null,    // lu depuis Engagement (ADR-002) si déjà défini, jamais recalculé si présent
    today: Date
) -> FinancialTemporalContext
```

Pure fonction au sens du domaine : mêmes entrées → même sortie, déterministe, reproductible (voir INV-TIME-2). Aucun appel LLM à l'intérieur du FTE lui-même — la détection de périodes/fréquences est un problème de reconnaissance de motifs déterministe (regex, parsing de labels, analyse de séquence de dates), pas un problème de jugement qui justifierait un LLM. **C'est un point de conception important, à valider explicitement avec vous :** confier ne serait-ce qu'une partie de la détection temporelle à un LLM violerait l'axiome 4 (« les LLM ne doivent jamais reconstruire le temps eux-mêmes ») par construction, puisque le FTE en fait justement la seule source. Le FTE doit donc être un module déterministe, testable unitairement sans aucun appel réseau — au même niveau de rigueur que `decision_rules.py` déjà cité par le Blueprint (§G) comme référence de ce que le Core attend en fiabilité.

**Value Objects :**

| Value Object | Rôle | Champs indicatifs |
|---|---|---|
| `PeriodObservation` | Unité d'entrée normalisée — une période candidate détectée dans les données brutes, quelle que soit la source | `raw_label` (ex. "2019-09", "YEAR 2023", "Q1"), `parsed_start`, `parsed_end`, `source_row_ref` (traçabilité, pas de format) |
| `FiscalPeriod` | Une période financière normalisée et validée — l'unité de temps faisant autorité dans tout le domaine | `type` (month\|quarter\|year\|week\|custom), `start_date`, `end_date`, `label` canonique |
| `PeriodFrequency` | La cadence observée dans les données elles-mêmes (à ne pas confondre avec `Engagement.cadence`, qui est contractuelle — voir §3.8) | `monthly \| quarterly \| weekly \| annual \| mixed \| irregular`, `confidence` |
| `ComparisonHorizon` | Une comparaison proposée comme pertinente — jamais réalisée par le FTE lui-même | `type` (vs_M-1 \| vs_quarter \| ytd \| rolling12 \| vs_N-1 \| vs_budget), `reference_periods: FiscalPeriod[]`, `relevance_reason` |
| `DataFreshness` | Jugement sur l'actualité des données par rapport à `today` | `latest_period: FiscalPeriod`, `staleness_days`, `verdict` (fresh \| analysis_recommended \| overdue) |
| `TemporalWarning` | Une anomalie temporelle détectée, jamais auto-résolue | `type` (incomplete_period \| unexpected_future_data \| frequency_break \| gap_detected), `message`, `severity`, `requires_confirmation: bool` |
| `ManagementCycle` | Le rythme de gestion inféré de l'historique — candidat de raffinement pour `Engagement.cadence`, jamais une écriture silencieuse (§3.8) | `expected_frequency: PeriodFrequency`, `next_expected_closing: date`, `next_recommended_analysis: date` |
| `RecommendationTemporalWindow` | Les paramètres temporels attachés à une future `Recommendation` (T3) — le FTE calcule ces dates, il ne gère jamais l'état de la Recommendation elle-même (§3.9) | `created_at`, `observation_window_end`, `reevaluation_date`, `expiration_date` |

**L'objet produit — `FinancialTemporalContext` :**

```
FinancialTemporalContext {
  today: Date
  latestPeriod: FiscalPeriod
  previousPeriod: FiscalPeriod | null
  detectedFrequency: PeriodFrequency
  fiscalYearToDate: FiscalPeriod           // remplace "ytd" — nommage explicite, pas d'abréviation dans le domaine
  rollingTwelveMonths: FiscalPeriod
  comparablePeriods: ComparisonHorizon[]
  dataFreshness: DataFreshness
  managementCycle: ManagementCycle
  temporalWarnings: TemporalWarning[]      // jamais null — liste vide si rien à signaler
  confidence: ConfidenceLevel              // réutilise le concept déjà défini pour Evidence (ADR-001A), pas un nouveau type
}
```

Écarts assumés par rapport à l'exemple donné dans le mandat : `recommendedAnalysis` est retiré comme champ séparé — il est déjà entièrement représenté par `comparablePeriods` (la liste des comparaisons pertinentes *est* la recommandation d'analyse, les dupliquer créerait deux représentations de la même information, interdit par l'Article X). `decisionReviewSchedule` est retiré du `FinancialTemporalContext` global et déplacé dans `RecommendationTemporalWindow`, attaché individuellement à chaque `Recommendation` plutôt que porté globalement — une seule échéance par recommandation est plus fidèle au cycle de vie décrit en §3.9 qu'un planning agrégé.

**Ceci n'est qu'une proposition, comme le mandat le permet explicitement — le nom exact des champs et leur granularité restent ouverts à votre revue.**

### 3.4 Invariants

- **INV-TIME-1 (Absence ≠ zéro, étendu au temps).** Si aucune période ne peut être détectée avec une confiance suffisante, `detectedFrequency = irregular` et `confidence` est bas — jamais un défaut silencieux à `monthly`. Rattaché à l'Axiome 3 et à l'Article III.
- **INV-TIME-2 (Déterminisme et reproductibilité).** À entrées identiques, `FinancialTemporalContext` est strictement identique — aucun aléa, aucun appel LLM dans le calcul lui-même. Même exigence que celle déjà posée par ADR-001 pour le regroupement de faits en événement économique (« jamais attribué arbitrairement »).
- **INV-TIME-3 (`latestPeriod` est un fait, pas une inférence).** `latestPeriod` doit être directement evidenced par au moins une `PeriodObservation` réelle — jamais dérivé uniquement de `today` ou de `target_date` (qui est un objectif de projection déclaré par l'utilisateur, pas une période observée).
- **INV-TIME-4 (`today` est toujours l'horloge système).** Jamais dérivé du contenu du fichier — protège contre un fichier contenant des dates futures qui déplacerait silencieusement la notion de « maintenant » du système.
- **INV-TIME-5 (Non-bloquant par construction).** Un FTE qui échoue à détecter quoi que ce soit ne bloque jamais le pipeline — il produit un `FinancialTemporalContext` dégradé (`confidence` bas, `temporalWarnings` peuplé), jamais une exception qui interrompt l'analyse. Même discipline que l'Evidence Graph existant (« non-bloquant, retourne {} en cas d'échec »).
- **INV-TIME-6 (Une seule source de temps).** Aucun agent LLM, aucun autre service du pipeline ne recalcule une notion de période, de fraîcheur ou de comparaison pertinente une fois que le FTE a produit son contexte pour cette analyse — ils le citent, ils ne le reconstruisent jamais. C'est l'application directe, au temps, de l'Article XII (« chaque objet du domaine n'a qu'une seule représentation faisant autorité »).
- **INV-TIME-7 (Le silence n'est jamais une confirmation).** Une anomalie temporelle marquée `requires_confirmation = true` (ex. données futures inattendues) ne peut jamais être silencieusement acceptée ni silencieusement écartée par le système — elle doit être explicitement exposée à l'utilisateur avant que l'analyse ne s'appuie dessus sans réserve. Cohérent avec l'invariant déjà posé pour `Exception` dans le Modèle Idéal (« le silence n'est jamais une clôture valide »).
- **INV-TIME-8 (Indépendance de format — voir §3.7).** Le FTE n'accepte en entrée que des `PeriodObservation[]` déjà normalisées. Aucune logique de parsing Excel, CSV, ou API spécifique à une source ne peut exister à l'intérieur du FTE lui-même.

### 3.5 Événements métier

| Événement | Émis quand | Consommé par (à terme) |
|---|---|---|
| `TemporalContextComputed` | Un `FinancialTemporalContext` est produit pour une analyse | Evidence Ledger (référence de période, §3.8), Agents (prompt), Attention Score (T4) |
| `DataFreshnessDegraded` | `dataFreshness.verdict` passe à `analysis_recommended` ou `overdue` pour un Engagement | Attention Score (T4) — réutilise le nom déjà anticipé par le Modèle Idéal §E.2, jamais un doublon |
| `TemporalAnomalyDetected` | Un `TemporalWarning` avec `requires_confirmation = true` est produit | Interface utilisateur (confirmation explicite requise, INV-TIME-7) |
| `TemporalAnomalyConfirmed` / `TemporalAnomalyDismissed` | L'utilisateur répond explicitement à une anomalie détectée | Evidence Ledger (l'analyse peut procéder ou est abandonnée) |
| `ManagementCycleInferred` | Un `ManagementCycle` est calculé et diffère de `Engagement.cadence` actuel (ou l'enrichit s'il est absent) | Engagement (candidat de raffinement, jamais une écriture automatique — §3.8) |
| `RecommendationReviewDue` | La date de `reevaluation_date` d'une `RecommendationTemporalWindow` est atteinte | Recommendation Engine (T3, futur) — déclenche une réévaluation, pas une décision automatique |

Convention de nommage alignée sur celle déjà en usage (`EngagementActivated`, `FactObserved`, `ExceptionRaised`) — passé composé, verbe métier explicite, jamais un nom technique (`onUpdate`, `Recalculated`).

### 3.6 Pipeline complet — et une clarification nécessaire sur les deux ordres

**Distinction essentielle, à valider avec vous avant toute chose :** le Blueprint (§E) numérote des phases T0→T6 dans l'**ordre d'implémentation** (dans quel ordre le code a été/sera écrit). Le pipeline que vous décrivez dans le mandat est un ordre d'**exécution** (dans quel ordre les composants s'activent à chaque analyse). Ces deux ordres ne coïncident pas nécessairement, et ce n'est pas une contradiction : le FTE s'exécute en premier à chaque requête, alors même qu'il est implémenté après T1/T2 dans le calendrier de développement (§3.11 explique pourquoi ce séquencement d'implémentation est le plus sûr).

**Pipeline d'exécution (ordre runtime, celui que vous avez spécifié) :**

```
Upload
  │  (routers/analyze.py::analyze_file — inchangé)
  ▼
Financial Time Engine  ◄── NOUVEAU, cette ADR
  │  Entrées : PeriodObservation[] (§3.7), historique Analyses/Decisions,
  │  Engagement.cadence si connu, today.
  │  Sortie : FinancialTemporalContext — formaté en texte
  │  (temporal_context_section, même pattern que evidence_graph_section)
  │  et injecté dans call_analysis_v3 / call_verification_v3
  │  AVANT le premier appel LLM (Step 3 de run_full_pipeline).
  ▼
Evidence Ledger (T1)
  │  evidence_capture.py enrichi : chaque QuantifiedImpact peut désormais
  │  référencer un FiscalPeriod plutôt qu'une période textuelle libre.
  ▼
Engagement (T2)
  │  Lecture de Engagement.cadence (entrée du FTE) ; réception d'un
  │  ManagementCycleInferred en sortie (candidat de raffinement, jamais
  │  une écriture automatique).
  ▼
Agents (Call 1 analyse, Call 2 vérification — existants, inchangés dans
  leur rôle, enrichis dans leur contexte d'entrée uniquement)
  ▼
Recommendation Engine (T3, futur)
  │  RecommendationTemporalWindow attachée à chaque Recommendation proposée.
  ▼
Attention Score (T4, futur)
  │  dataFreshness + temporalWarnings deviennent des signaux d'entrée,
  │  en plus de la matérialité (T1) et de l'historique de fiabilité (T3).
  ▼
Exports
  │  Peuvent citer le contexte temporel ("Période : Sept. 2019 · Comparé à :
  │  Août 2019, YTD, 12 mois glissants") — ne le recalculent jamais.
```

**Position dans le pipeline technique réel (`llm_service.py::run_full_pipeline`) :** immédiatement avant le Step 2.0 actuel (construction de l'Evidence Graph), en parallèle de celui-ci si possible (le FTE ne dépend pas de l'Evidence Graph, l'Evidence Graph ne dépend pas du FTE — les deux peuvent s'exécuter concurremment). Le point d'injection dans le prompt suit exactement le pattern déjà établi pour `evidence_graph_section` : un paramètre texte supplémentaire (`temporal_context_section`) passé à `call_analysis_v3` et `call_verification_v3`. Aucune signature de fonction publique existante n'est modifiée dans son sens — uniquement étendue, comme l'a déjà fait l'ajout d'`evidence_graph_section` avant cette ADR.

### 3.7 Indépendance vis-à-vis du format source (exigence explicite du mandat)

**Le FTE n'a jamais connaissance d'Excel, de colonnes, de cellules, ni d'aucun format de fichier.** Son seul contrat d'entrée est `PeriodObservation[]` — une liste de périodes candidates déjà extraites, quelle que soit la source. C'est une application directe du pattern déjà nommé dans le Modèle Idéal pour le Bounded Context `Data Ingestion & Normalization` (§E.2) : *« un `SyncRun` ne peut jamais écrire directement dans Financial Evidence sans passer par une étape de normalisation explicite (l'ACL) — aucune donnée brute externe n'entre telle quelle dans le langage ubiquitaire du domaine »*. Cette ADR étend cette même Anti-Corruption Layer pour qu'elle produise, en plus des `FinancialFact`, des `PeriodObservation` — même adaptateur, deux flux de sortie normalisés.

Concrètement, pour le pipeline actuel (Excel uniquement, `file_parser.py`) : l'adaptateur Excel devient responsable de produire `PeriodObservation[]` en plus de ce qu'il produit déjà — c'est un ajout à sa responsabilité de normalisation, pas une nouvelle brique. Le jour où Pepperyn reçoit des données via Odoo, SAP, Business Central, Pennylane, Exact Online, Sage, une API ou un flux MCP, chacun de ces adaptateurs implémente la même production de `PeriodObservation[]`, et **le FTE n'a besoin d'aucune modification.** C'est le test de conformité le plus direct de cette ADR (Constitution, Article XI, question 7 : *« Cette fonctionnalité aurait-elle encore un sens si la technologie sous-jacente était entièrement remplacée ? »*) — la réponse doit être oui par construction, pas par vigilance.

**Alternative rejetée — laisser le FTE parser directement les colonnes/cellules du fichier (plus rapide à construire).** Rejetée explicitement : cela violerait INV-TIME-8, romprait l'indépendance de format dès le premier jour, et créerait exactement la dette que l'Article XII interdit (« une complexité technique qui ne se traduit pas par une clarté supplémentaire du domaine est une dette, jamais un progrès ») — ici, coupler un composant censé être un service de domaine pur à un format de fichier particulier.

### 3.8 Impact sur Engagement (ADR-002)

**Aucune modification du schéma ni des invariants déjà actés par ADR-002.** Le FTE lit `Engagement.cadence` (`ReviewCadence`) comme une entrée quand elle est définie (§3.3, signature). Quand `ManagementCycleInferred` (§3.5) produit une fréquence différente de la cadence contractuelle actuelle — ou une cadence là où aucune n'était définie — ce n'est jamais une écriture automatique sur `Engagement`. C'est un événement candidat, à confirmer par un humain avant toute application, exactement dans l'esprit d'ADR-002 §3.6 (« le jour cible n'est pas fixé par ce document [...] il reste NULL/non défini jusqu'à ce qu'un utilisateur ou une PR ultérieure le précise »). Le FTE **ferme** la question ouverte n°3 d'ADR-002 (« quand un premier consommateur de production commencera-t-il à lire `engagements` ») en devenant lui-même ce premier lecteur — en lecture seule, jamais en écriture directe.

**One New Truth Rule :** `PeriodFrequency` (observée dans les données) et `ReviewCadence` (contractuelle, déclarée) restent deux objets distincts, avec des sources de vérité différentes et jamais fusionnées silencieusement — la première est un fait constaté, la seconde un engagement humain. Un `ManagementCycleInferred` qui diverge de la Cadence actuelle n'écrase jamais cette dernière ; il produit une divergence explicite, à la disposition d'un futur `TemporalWarning` ou d'une interface de confirmation.

### 3.9 Impact sur Recommendation (T3, Blueprint C.5 — non encore construit)

Le FTE ne crée ni ne gère de `Recommendation`. Il fournit `RecommendationTemporalWindow` (§3.3) comme paramètre d'entrée, calculé au moment où une `Recommendation` est proposée, à partir de `ManagementCycle` et de `detectedFrequency` : par exemple, une fenêtre d'observation calquée sur la fréquence détectée (mensuelle → réévaluation à échéance ~1 mois), jamais une valeur fixe arbitraire.

Ceci répond directement au point 10 du mandat (« cycle de vie des recommandations ») sans construire l'agrégat `Recommendation` lui-même — hors périmètre de cette ADR, périmètre de T3. **Dépendance explicite et volontairement faible :** le FTE peut être implémenté et livrer de la valeur (détection de période, fraîcheur, avertissements — responsabilités 1 à 9 du mandat) sans que T3 existe. Seule la responsabilité 10 restera, jusqu'à T3, une capacité *disponible mais non consommée* — même logique de croissance parallèle que celle déjà retenue par ADR-001 pour l'Evidence Ledger avant que quiconque ne le lise.

**État (`active | à confirmer | obsolète | close`) donné en exemple par le mandat :** ce cycle de vie appartient à l'agrégat `Recommendation` lui-même (transitions gérées par T3), pas au FTE. Le FTE fournit les *dates* qui déclenchent les *transitions* (`RecommendationReviewDue`), il ne possède jamais l'état lui-même — sans quoi deux objets prétendraient chacun gouverner le cycle de vie d'une Recommendation, ce que l'Article X interdit explicitement.

### 3.10 Impact sur Evidence Ledger (ADR-001) et sur le futur Attention Score (T4, Blueprint C.6)

**Evidence Ledger :** aucune modification de son invariant d'immutabilité, aucune réécriture de ligne existante (même discipline qu'ADR-002 §3.4 a déjà respectée pour l'Engagement). L'apport du FTE est additif : `evidence_capture.py` peut désormais résoudre chaque fait vers un `FiscalPeriod` structuré plutôt qu'une période textuelle libre extraite du prompt — une amélioration de la qualité de la provenance, pas un changement de structure. Ce point ferme, de fait, la question ouverte n°2 d'ADR-001 citée en §1 : la clôture de période devient déterminable par le FTE (`latestPeriod` + `dataFreshness`), même en l'absence d'une Cadence contractuelle formalisée.

**Attention Score (T4, pas encore construit) :** le Blueprint C.6 anticipait déjà « l'ancienneté de la dernière revue » comme signal d'entrée, calculé grossièrement depuis `analyses.created_at`. Le FTE remplace ce proxy brut par un jugement structuré : `dataFreshness.verdict` (fresh/analysis_recommended/overdue) et `temporalWarnings` deviennent des signaux de première classe, au même titre que la matérialité (T1) et l'historique de fiabilité des recommandations (T3) déjà prévus par le Blueprint. C'est un renforcement de T4, pas un changement de sa conception — **aucune ligne du Blueprint concernant T4 n'est contredite, seulement enrichie** au moment où T4 sera construit.

### 3.11 Stratégie de migration et d'implémentation

Additive et non-bloquante, dans le même esprit que T1/T2 :

1. Le FTE est un nouveau module (`services/financial_time_engine.py` ou équivalent), pur, sans I/O réseau, testable unitairement sans mock d'aucune sorte.
2. `PeriodObservation[]` est d'abord produit par une extension du `file_parser.py` existant (Excel uniquement, pour commencer — §3.7 garantit que ceci reste remplaçable).
3. `temporal_context_section` est injecté en paramètre optionnel supplémentaire de `call_analysis_v3`/`call_verification_v3` — les appels existants sans ce paramètre continuent de fonctionner à l'identique (compatibilité ascendante totale, même mécanique que l'ajout d'`evidence_graph_section`).
4. Aucun export, aucune route, aucun renderer n'est modifié par la construction du FTE lui-même — seulement, plus tard et séparément, s'il est décidé d'afficher le contexte temporel dans un livrable (décision produit distincte, hors périmètre de cette ADR).
5. **Pourquoi T2.5 et pas immédiatement après T0 :** le FTE a une utilité réelle sans Engagement (détection de période, fraîcheur), mais son intégration la plus riche (lecture de `Engagement.cadence`, `ManagementCycleInferred`) suppose que `Engagement` existe déjà comme agrégat lisible. Le construire avant T2 obligerait soit à une version appauvrie livrée deux fois, soit à une dépendance anticipée sur un agrégat pas encore accepté au moment de la conception. Le construire après T2 évite les deux.

### 3.12 Risques d'architecture

- **Risque de détection incorrecte silencieuse.** Un format de période ambigu (« 09 » : septembre ou 2009 ? « Q1 » : calendaire ou fiscal décalé ?) peut être mal interprété sans qu'aucune erreur ne se déclenche. Mitigation : `confidence` bas et `TemporalWarning` explicite dès qu'une ambiguïté de format est détectée plutôt que résolue par une heuristique risquée — cohérent avec INV-TIME-1 et INV-TIME-7. Ce risque ne peut pas être éliminé entièrement par la conception seule ; il devra être mesuré empiriquement sur un corpus réel avant toute mise en production (test d'acceptation §5, point 6).
- **Risque de double calcul temporaire pendant la transition.** Tant qu'`arc_service.py` continue de calculer `age_days` indépendamment (§1, Problème A) et que le FTE calcule `dataFreshness` séparément, deux notions de « fraîcheur »/« ancienneté » coexistent sans être unifiées. Ce document ne migre pas `arc_service.py` — décision volontaire pour ne pas mélanger la construction du FTE avec une refonte de la Review Briefing existante (Capability 3, déjà livrée et testée). La convergence des deux devra faire l'objet d'une décision ultérieure explicite, pas d'un effet de bord de cette ADR.
- **Risque d'ambiguïté entre `PeriodFrequency` (observée) et `ReviewCadence` (contractuelle).** Traité en §3.8 comme un invariant de séparation stricte, mais reste un risque de confusion pour un futur développeur qui pourrait être tenté de les fusionner « pour simplifier ». Documenté explicitement pour prévenir cette tentation.
- **Risque sur la performance perçue.** Le FTE s'exécute désormais avant le premier appel LLM, sur le chemin critique de chaque analyse. S'il implique une consultation de l'historique complet des analyses d'un Engagement à chaque exécution, le coût peut croître avec l'ancienneté de la relation. Mitigation à concevoir au moment de l'implémentation (fenêtre glissante d'historique plutôt que requête intégrale) — non tranchée par cette ADR, signalée comme point d'attention pour la PR d'implémentation.
- **Risque de dérive de périmètre (le plus important, à surveiller activement).** Un moteur qui « comprend le temps » est une abstraction séduisante qui invite à y ajouter, au fil du temps, des responsabilités qui ne lui appartiennent pas (calcul de KPI ajustés du temps, prévision, saisonnalité). L'Article X est explicite : *« Pepperyn n'ajoutera jamais une capacité qui ne renforce pas mesurablement son fonctionnement central. »* Le FTE construit le contexte ; il ne doit **jamais** être le lieu où une analyse, une prévision ou un jugement financier est réalisé — ce garde-fou doit être répété à chaque extension future de ce composant.

---

## 4. Alternatives rejetées

**Alternative 1 — Laisser chaque agent LLM déduire le contexte temporel lui-même, à partir du fichier brut.** C'est l'état actuel de fait (Problème B, §2). Rejetée explicitement par le mandat lui-même et par l'Article III : une reconstruction non déterministe par un LLM n'est jamais une source de vérité acceptable pour une dimension aussi structurante que le temps.

**Alternative 2 — Ajouter les champs temporels directement sur `Engagement` ou sur `EvidenceLedger`, sans nouveau composant.** Rejetée pour la même raison que l'Alternative 3 d'ADR-002 (fusionner Engagement dans Entity) a été rejetée : mélanger des responsabilités que le Modèle Idéal sépare délibérément. Le temps n'est ni une propriété de la relation contractuelle (Engagement) ni une propriété de la preuve elle-même (Evidence) — c'est le contexte qui les relie toutes les deux, et il mérite sa propre représentation, cohérente avec le statut de premier niveau que le mandat lui demande explicitement.

**Alternative 3 — Construire le FTE comme un simple utilitaire technique (fonctions statiques), sans le faire apparaître dans le modèle de domaine.** Rejetée : contredirait directement l'axiome fondateur n°4 du mandat (« le temps devient une composante fondamentale du domaine métier ») et l'Article XII (« le domaine précède toujours l'interface [...] chaque objet du domaine n'a qu'une seule représentation faisant autorité ») — un simple utilitaire ne peut pas être cette représentation faisant autorité, il resterait un détail d'implémentation invisible du langage ubiquitaire.

**Alternative 4 — Faire du FTE un Bounded Context Core plutôt que Supporting.** Étudiée en §3.2 et rejetée pour la raison qui y est développée : la différenciation reste dans l'usage du temps (Attention, Recommendation), pas dans le calcul du calendrier — la même logique déjà appliquée par le Modèle Idéal à `Client Engagement`.

**Alternative 5 — Faire dépendre le FTE de T3 (Recommendation) avant de le construire, pour livrer sa responsabilité n°10 dès le premier jour.** Rejetée en §3.9 et §3.11 : neuf des dix responsabilités du mandat sont utiles sans T3 ; retarder tout le composant pour la dixième irait contre le principe de migration incrémentale déjà appliqué à chaque ADR précédente (« chaque phase se termine avec un produit strictement fonctionnel »).

---

## 5. Tests d'acceptation

Prescrits pour la PR d'implémentation qui suivra cette ADR (non exécutés ici) :

1. Sur un corpus de fichiers réels couvrant les trois formats donnés en exemple par le mandat (`2019-01...2019-09`, `YEAR 2022...YEAR 2024`, `Q1...Q3`), le FTE détecte correctement `latestPeriod`, `previousPeriod` et `detectedFrequency` sans intervention manuelle.
2. Pour un même jeu de `PeriodObservation[]`, `historicalAnalyses`, `historicalDecisions`, `engagementCadence` et `today`, deux exécutions successives du FTE produisent un `FinancialTemporalContext` strictement identique (INV-TIME-2).
3. Un fichier dont la dernière période est antérieure de plus d'un cycle de cadence attendu à `today` déclenche `dataFreshness.verdict = overdue` et un `TemporalWarning` explicite (« les données semblent incomplètes »), jamais une absence de signal.
4. Un fichier contenant une période postérieure à `today` (donnée future) déclenche `TemporalAnomalyDetected` avec `requires_confirmation = true` — vérifié qu'aucun consommateur en aval n'accède au `FinancialTemporalContext` complet tant que la confirmation n'a pas eu lieu (INV-TIME-7).
5. Aucun appel réseau, aucun appel LLM n'est déclenché par le FTE lui-même (vérifié par mock strict interdisant tout appel sortant dans les tests unitaires du module).
6. Sur un échantillon d'au moins 20 fichiers réels anonymisés couvrant des formats de période ambigus, le taux de détection à faible confiance (`TemporalWarning` plutôt qu'erreur silencieuse) est mesuré et documenté — sert de baseline pour le risque identifié en §3.12.
7. Zéro régression : les trois exports (PDF/PPTX/Excel) produisent une sortie strictement identique avant/après l'introduction du FTE sur un corpus de non-régression, tant que l'affichage du contexte temporel dans les livrables n'a pas fait l'objet d'une décision produit séparée (§3.10, dernier paragraphe).
8. `Engagement.cadence` n'est jamais modifié en base par le FTE lui-même — vérifié par un test qui échoue si une écriture sur `engagements` est détectée pendant l'exécution du FTE (§3.8).

---

## 6. Rollback

Trivial par construction, même stratégie que les trois ADR précédentes. Le FTE est un module additif, sans écriture sur aucune table existante (`engagements`, `evidence_ledger_entries`, `analyses`, `decision_arcs` restent toutes inchangées). Rollback = cesser d'appeler le module et cesser d'injecter `temporal_context_section` dans les prompts — les deux paramètres optionnels redeviennent absents, les agents reviennent exactement à leur comportement actuel. Si une future table de persistance du `FinancialTemporalContext` est introduite au moment de l'implémentation (décision non tranchée par cette ADR — voir Questions ouvertes), son rollback suivrait la même logique que celle déjà validée pour `engagements` (ADR-002 §3.16) : `DROP TABLE`, aucune autre donnée affectée.

---

## 7. Conformité à la Constitution

| Article | Application |
|---|---|
| **Article III** (La Vérité) | Le FTE rend structurellement impossible qu'une affirmation temporelle soit présentée sans pouvoir être reliée à sa source (une `PeriodObservation` réelle) — application directe au temps de l'exigence déjà posée pour les montants. |
| **Article IV** (Le Modèle Métier) | N'introduit aucun nouvel objet permanent du glossaire de l'Article IV (Engagement, fait, exception, recommandation, livrable, attention) — le FTE reste un service qui *sert* ces objets, conformément à son statut Supporting (§3.2). |
| **Article IX** (L'Évolution) | Introduit par nécessité démontrée : deux ADR précédentes (ADR-001, ADR-002) ont chacune, indépendamment, buté sur la même question ouverte sans la résoudre (§1) — c'est la preuve la plus directe possible d'une nécessité, pas d'une préférence. |
| **Article X** (Les Interdictions) | Respecte en particulier l'interdiction de deux vérités concurrentes (`PeriodFrequency` vs `ReviewCadence`, §3.8, jamais fusionnées) et l'interdiction de convertir une absence en valeur par défaut (INV-TIME-1). Le risque de dérive de périmètre (§3.12) est documenté précisément parce que cet article l'interdit par avance. |
| **Article XI** (Tests de conformité) | Question 7 (« aurait-elle encore un sens si la technologie sous-jacente changeait ? ») est le test que §3.7 est explicitement conçu pour satisfaire. Question 4 (« introduit-elle une nouvelle représentation de quelque chose que le domaine représente déjà ailleurs ? ») est explicitement traitée en §3.8/§3.9 : le FTE ne duplique ni la Cadence ni l'état d'une Recommendation, il leur fournit des paramètres. |
| **Article XII** (Principes d'architecture) | « Le domaine précède toujours l'interface » : le FTE existe et a une forme avant toute décision d'affichage dans une interface. « Chaque objet du domaine n'a qu'une seule représentation faisant autorité » : c'est l'invariant central du FTE lui-même (INV-TIME-6), pas seulement un principe qu'il respecte. |

---

## 8. Traçabilité (GD-001 §3ter)

- **Mandat d'origine :** « MISSION — Concevoir et intégrer le Financial Time Engine (FTE) », quatre axiomes fondateurs fournis intégralement en §3.1, objet `FinancialTemporalContext` fourni en exemple et raffiné en §3.3, exigence d'indépendance de format fournie en clôture du mandat et traitée en §3.7.
- **Section du Blueprint concernée :** aucune section existante ne couvrait ce composant — c'est la première extension du Blueprint depuis sa version du 2026-08-02. Positionné en Phase T2.5 (§0, §3.11), entre T2 (Engagement) et T3 (Recommendation unifiée).
- **Articles de la Constitution concernés :** III, IV, IX, X, XI, XII (détail §7).
- **ADR précédentes engagées par ce document :** ADR-001 (ferme la question ouverte n°2, §3.10), ADR-001A (réutilise `ConfidenceLevel` sans le redéfinir, §3.3), ADR-002 (ferme la question ouverte n°3, lit `Engagement.cadence` sans le modifier, §3.8).

---

## 9. Questions ouvertes

1. **Persistance du `FinancialTemporalContext` lui-même : oui ou non, et sous quelle forme ?** Ce document ne tranche pas si chaque contexte produit doit être conservé (pour l'auditabilité — « pourquoi le système a-t-il comparé à Q1 2024 ce jour-là ») ou recalculé à la demande à partir de l'historique. Une conservation serait cohérente avec la discipline d'Evidence Ledger (immutabilité, traçabilité) mais introduirait une nouvelle table — à trancher explicitement avant l'implémentation, pas pendant.
2. **Calendrier fiscal non-calendaire.** Le modèle proposé (§3.3) suppose implicitement une année fiscale calée sur l'année calendaire. Aucune source consultée (Constitution, Modèles, Blueprint) ne traite des exercices fiscaux décalés (ex. avril-mars). À clarifier avant l'implémentation si des clients concernés existent déjà ou sont anticipés à court terme.
3. **Granularité minimale de détection.** Le mandat mentionne des périodes hebdomadaires comme cas possible. Aucune donnée du corpus actuel n'a été vérifiée comme contenant cette granularité — à confirmer empiriquement (test d'acceptation §5, point 6) avant de garantir ce niveau de détail dans une future implémentation.
4. **Qui déclenche la reconsidération d'un `ManagementCycleInferred` qui contredit `Engagement.cadence` ?** §3.8 pose l'invariant (jamais d'écriture automatique) mais ne conçoit pas l'interface ou le mécanisme de confirmation humaine — hors périmètre d'une ADR d'architecture, à concevoir dans un futur plan d'implémentation UX.
5. **Convergence avec les calculs d'ancienneté déjà existants dans `arc_service.py`.** Signalée comme risque en §3.12, volontairement non résolue ici pour ne pas mélanger deux décisions distinctes — mérite sa propre décision explicite (ADR ou plan d'implémentation ultérieur), une fois le FTE lui-même validé indépendamment.

---

**ADR-003 READY FOR REVIEW.
AUCUN CODE MODIFIÉ.**
