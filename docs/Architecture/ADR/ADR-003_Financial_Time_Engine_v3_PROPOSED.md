# ADR-003 — Financial Time Engine (v3, réécriture complète)

**Phase :** T2.5 (inchangé, voir §5.5)
**Statut :** Proposé, pour revue — remplace intégralement ADR-003 v2 (commit `a0318f1`)
**Sources autorisées :** Pepperyn Constitution v1.0 · Ideal Domain Model · Pepperyn Current Domain Model · Transformation Blueprint · ADR-001 · ADR-001A · ADR-002 · ADR-003 v1 · ADR-003 v2
**Nature :** décision d'architecture métier. Aucun code, aucune migration, aucun modèle Pydantic, aucun prompt, aucune API n'est modifié par ce document.

---

## §0 — Avertissement préalable (inchangé depuis v1/v2)

Le code de service T1/T2 n'existe toujours sur aucune branche fusionnée dans `main`. Précondition d'implémentation, pas une objection à la conception.

---

## §1 — Le FTE modélise-t-il encore un calendrier, ou déjà le temps métier ? (Mission 1)

**Constat :** v2 avait déjà éliminé l'essentiel du réflexe calendaire — `BusinessMoment`, `FinancialCycle`, `AnalysisPertinence` répondent tous à une question métier, jamais à une question technique. Mais un résidu subsiste, et il est structurant : **`FinancialCycle.typicalLag` (v2 §4.3.2) est une valeur déclarée ou assumée, jamais observée.** Le FTE v2 raisonne comme si chaque organisation se comportait exactement comme sa cadence contractuelle le prévoit. Or ce n'est jamais le cas en pratique — une organisation qui « clôture mensuellement » ne clôture pas au même jour chaque mois, et cet écart *récurrent* est lui-même une information métier de premier ordre (« ce client clôture systématiquement avec quinze jours de retard » change directement ce que Pepperyn doit attendre de lui, et donc quand une nouvelle analyse doit être jugée pertinente — §4.8 de v2).

Tant que le FTE ne conserve aucune trace de ce qui s'est réellement passé au fil des analyses successives, il reste, sur ce point précis, un moteur de calendrier assumé plutôt qu'un moteur de comportement observé. C'est le seul résidu calendaire réel identifié dans v2, et il se résout entièrement par la Mission 2 : donner au FTE une mémoire de comportement, pas seulement une mémoire d'instants.

Aucun autre objet de v2 n'a été trouvé en défaut de ce test (chaque VO de v2 répond à une question métier nommée — voir v2 §2 pour la méthode appliquée). Le reste de cette révision porte donc sur l'ajout de capacités réellement nouvelles (Missions 2 à 5), pas sur une correction de fond supplémentaire du modèle existant.

---

## §2 — `BusinessHistory` : le FTE apprend à raconter un comportement (Mission 2)

### 2.1 — Ce qui manque, précisément

Le FTE v2 sait reconnaître un instant (`BusinessMoment`). Il ne conserve aucune trace de ce qui s'est répété. Les cinq exemples du mandat se répartissent en réalité en deux natures différentes, et non cinq — c'est la première décision de conception de cette section, et elle conditionne tout le reste.

- *« Cette organisation clôture systématiquement avec quinze jours de retard »* — un écart **structurel et récurrent entre un rythme déclaré et un rythme observé**. Nature : dérive de rythme.
- *« Cette anomalie revient tous les trimestres »* et *« ce besoin de trésorerie apparaît chaque été »* — la **récurrence périodique d'un signal déjà qualifié ailleurs** (une anomalie est qualifiée par Exception & Reconciliation, un besoin de trésorerie est qualifié par Financial Evidence & Truth — le FTE ne les invente pas, il en observe la cadence). Nature : récurrence de signal.
- *« Cette recommandation reste ouverte depuis huit mois »* — **n'est pas un nouveau phénomène** : c'est une lecture extrême de `RecommendationTemporalState` (v2 §4.3.6), déjà `overdue`, à laquelle il ne manque qu'une durée écoulée pour être parlante. Créer un objet dédié ici dupliquerait une capacité déjà couverte — rejeté explicitement en §7.2.
- *« Cette marge diminue depuis quatre analyses successives »* — **n'appartient pas au FTE**. Juger qu'une marge « diminue » exige de lire une valeur financière (un montant, un taux) — c'est un jugement de contenu, pas de structure temporelle. Le laisser entrer dans le FTE ferait exactement ce que v1 avait été blâmé de faire par excès inverse (refuser tout jugement) : ici, ce serait accepter un jugement qui n'est pas le sien. Rejeté explicitement en §7.2, avec le raisonnement complet.

Il reste donc **deux phénomènes réellement nouveaux et légitimement temporels** : la dérive de rythme, et la récurrence de signal. Un seul objet suffit à porter les deux, avec un discriminant de type — créer deux objets séparés pour deux variantes structurellement identiques (mêmes invariants, même mécanique de détection par accumulation d'occurrences) aurait été une sophistication non justifiée (Article XII, revérifié en §8).

### 2.2 — `BusinessHistory` (nouveau Value Object)

| Attribut | Rôle |
|---|---|
| `engagementRef` | l'Engagement concerné — un `BusinessHistory` n'a jamais de portée inter-Engagement |
| `patternType` | `RhythmDrift` \| `RecurringSignal` |
| `occurrences[]` | références traçables aux `BusinessMoment`/observations qui supportent le motif — jamais une affirmation sans preuve |
| `firstObservedAt` / `lastObservedAt` | bornes temporelles du motif |
| **Si `RhythmDrift` :** `referenceCycle` (le `FinancialCycle` dont on mesure l'écart), `declaredLag` (repris de `FinancialCycle.typicalLag`), `observedAverageLag` (calculé à partir des `occurrences`), `deviation` (différence) |
| **Si `RecurringSignal` :** `signalOrigin` (le Bounded Context qui a qualifié le signal — Exception & Reconciliation, Financial Evidence & Truth ; le FTE ne qualifie jamais le signal lui-même), `signalReference` (opaque, jamais interprété), `detectedPeriodicity` (réutilise `PeriodFrequency`) |

**Invariants :**
- **INV-HISTORY-1** — un motif n'est jamais nommé en dessous de **trois occurrences**. En dessous de ce seuil, ce n'est pas un comportement, c'est une coïncidence non prouvée (extension directe d'INV-TIME-1 : l'absence de preuve suffisante n'autorise jamais une affirmation).
- **INV-HISTORY-2** — `BusinessHistory` n'interprète jamais le contenu d'un signal (`RecurringSignal.signalReference` reste opaque) ni ne recalcule une valeur financière. Il ne fait que constater une récurrence structurelle. C'est l'invariant qui empêche cet objet de dériver vers `MetricTrend` (§7.2).
- **INV-HISTORY-3** — déterminisme : même ensemble d'occurrences, même `BusinessHistory`, toujours.
- **INV-HISTORY-4** — un `RhythmDrift` stable et confirmé **ne réécrit jamais** `FinancialCycle.typicalLag` automatiquement. Il produit une proposition de révision (événement `RhythmDriftConfirmed`), soumise à confirmation humaine — exactement le même mécanisme de gouvernance que `FinancialCycleInferred` (v2 §4.10) vis-à-vis d'`Engagement.cadence`. Aucune exception n'est créée pour ce nouvel objet ; il obéit à la règle déjà établie.

**Événements :** `BusinessHistoryPatternDetected` (dès que le seuil INV-HISTORY-1 est atteint), `BusinessHistoryPatternBroken` (un motif jusque-là stable ne se reproduit pas à l'occurrence attendue — souvent plus informatif que la continuation du motif lui-même : un client qui clôturait toujours en retard et clôture soudain à l'heure est un signal fort, positif ou négatif).

**Consommateurs :** Review Briefing (« ce client clôture en moyenne 15 jours après son échéance déclarée — cette analyse arrive donc dans la fenêtre habituelle, pas en retard »), Attention Score (une anomalie récurrente pèse plus qu'une occurrence isolée), Recommendation Engine (un `RhythmDrift` confirmé peut motiver une recommandation d'ajuster la cadence contractuelle — le FTE fournit le fait, ne propose jamais lui-même la recommandation), Portfolio.

---

## §3 — `FutureBusinessMoment` : le FTE devient capable d'anticiper, jamais de prédire (Mission 3)

### 3.1 — Distinction de méthode, non négociable

Le mandat est explicite et cette ADR le reprend sans nuance : **aucune inférence statistique, aucun modèle prédictif, aucun LLM.** Un `FutureBusinessMoment` n'est jamais une probabilité — c'est une **projection directe** d'un fait déjà connu (une cadence déclarée, ou désormais un comportement observé via `BusinessHistory`) vers l'avenir. Si l'information nécessaire à la projection n'existe pas, le FTE ne devine pas — il s'abstient (INV-FUTURE-1 ci-dessous).

### 3.2 — `FutureBusinessMoment` (nouveau Value Object)

| Attribut | Rôle |
|---|---|
| `engagementRef` | l'Engagement concerné |
| `anticipatedWindow` | une fenêtre (début/fin), jamais un point unique — la projection reste honnête sur son imprécision |
| `basis` | la raison structurée : `cycle_approaching(FinancialCycle)` \| `recommendation_entering_evaluation_window(RecommendationLifetime)` \| `review_expected_before_governance_event(FinancialCycle de type ReviewCycle)` |
| `basisStrength` | `declared` (dérivé d'un `FinancialCycle`/`FiscalCalendar` explicitement déclaré) \| `observed` (dérivé d'un `BusinessHistory.RhythmDrift` confirmé — la projection utilise alors `observedAverageLag`, pas `declaredLag`) \| `assumed` (calendrier civil par défaut, INV-TIME-11) — une gradation structurelle, jamais une probabilité statistique |

**Invariants :**
- **INV-FUTURE-1** — un `FutureBusinessMoment` cite toujours, explicitement, le `FinancialCycle`, le `RecommendationLifetime` ou le `BusinessHistory` dont il est la projection directe. Aucune projection ne peut exister sans un fait déjà établi qui la fonde — pas de spéculation libre.
- **INV-FUTURE-2** — un `FutureBusinessMoment` est provisoire par nature : dès qu'un nouveau `BusinessMoment` réel le rend caduc (la période projetée est arrivée, ou une donnée contredit la projection), il est invalidé, jamais laissé silencieusement obsolète. C'est la garantie que le FTE ne laisse jamais traîner une anticipation périmée — exactement le défaut qu'`arc_service.py` illustre aujourd'hui en code réel avec ses calculs d'âge ad hoc jamais invalidés.
- **INV-FUTURE-3** — jamais produit par inférence statistique ou modèle de langage ; toujours une projection déterministe et rejouable à partir d'un fait déjà présent dans `FinancialTemporalContext`.

**Événements :** `FutureBusinessMomentProjected`, `FutureBusinessMomentInvalidated`.

**Réponse directe aux quatre exemples du mandat :** « une clôture mensuelle approche » = `cycle_approaching(MonthlyClosing)` ; « une revue trimestrielle devient pertinente » = `cycle_approaching(QuarterlyBoardReview)` ; « une recommandation arrive en fenêtre d'évaluation » = `recommendation_entering_evaluation_window` ; « une analyse est probablement attendue avant le Board » = `review_expected_before_governance_event(BoardReview)`.

**Consommateurs :** Portfolio (badge « à venir »), Review Briefing (préparer l'utilisateur avant l'échéance plutôt que de la constater après coup), Attention Score (un `FutureBusinessMoment` proche à `basisStrength=declared` peut légitimement élever une priorité), Recommendation Engine (anticiper qu'une recommandation entrera bientôt dans sa fenêtre d'évaluation).

---

## §4 — Le temps comme langage utilisateur (Mission 4)

### 4.1 — Ce qui ne doit **pas** être fait

Créer un objet `TemporalNarrative` à l'intérieur du FTE, chargé de produire des phrases, serait une erreur de frontière — cela ferait du FTE un composant qui *rédige*, pas un composant qui *comprend*. La Constitution a déjà tranché cette question ailleurs dans le domaine : Article VIII, les livrables « ne calculent jamais, ils projettent seulement » ; `conversation_engine.py` applique déjà cette règle en code réel (« le chat explique — il ne recalcule jamais »). Cette ADR ne réinvente pas ce mécanisme, elle l'étend.

### 4.2 — Décision

Le FTE s'arrête à produire des **surfaces fermées et énumérables** — ce qu'il faisait déjà largement en v2, renforcé ici :

`BusinessMoment.interpretations` · `TemporalWarning.type` · `DataFreshness.verdict` · `AnalysisPertinence.verdict` · `BusinessHistory.patternType` (+ `RhythmDrift`/`RecurringSignal`) · `FutureBusinessMoment.basis`

Chacune de ces six surfaces est un ensemble fini et fermé de valeurs, jamais du texte libre — condition nécessaire pour qu'un mappage déterministe vers une phrase soit possible sans jamais halluciner.

La traduction de ces valeurs en langage métier (« Clôture de septembre détectée », « Trois recommandations arrivent à maturité », « Votre cycle mensuel accuse huit jours de retard ») **appartient à Reporting & Deliverables**, sous la forme d'un répertoire de phrases déterministe et versionné (un « lexique temporel »), au même titre que les trois renderers existants lisent aujourd'hui `ExecutiveDecisionModel` sans jamais le recalculer. Ce n'est pas une nouvelle capacité technique à concevoir ici — c'est une extension de responsabilité déjà exercée par ce Bounded Context, appliquée à six surfaces nouvelles plutôt qu'aux seules données financières.

**Consommateurs identifiés, par les six surfaces ci-dessus :** Portfolio (badges), Review Briefing (déjà consommateur en v2, enrichi), Chat/Conversation Engine (lit les surfaces fermées comme il lit déjà `ExecutiveCase`, ne recalcule rien), Exports PDF/PPTX/Excel (citent la phrase, jamais la donnée brute — remplace directement l'anti-pattern « Dernière analyse : 28 septembre » nommé dans le mandat), Notifications futures (non construites, mais la même mécanique s'applique par construction).

---

## §5 — Le nom du moteur (Mission 5)

**Question posée : Financial Time Engine reste-t-il le meilleur nom, maintenant que le moteur comprend des comportements et projette l'avenir ?**

Examen des alternatives proposées :

- **Business Time Engine / Organisation Time Engine** — rejetées : élargiraient le périmètre perçu au-delà de ce que le modèle couvre réellement. Le FTE ne connaît que des rythmes *financiers* (clôture, budget, conseil, banque, audit, fiscal, paie) — il ignore délibérément tout rythme organisationnel non financier (cycle produit, cycle de recrutement). Nommer « Business » ou « Organisation » promettrait une portée que l'objet ne tient pas, et que rien dans cette ADR ne justifie d'ouvrir.
- **Decision Time Engine / Decision Rhythm Engine** — rejetées fermement : nommer le moteur autour de la « décision » entrerait directement en contradiction avec l'Axiome 7 et INV-TIME-9 (§4.7 de v2, reconfirmé en §6 ci-dessous). Le FTE ne décide rien et ne doit jamais donner l'impression qu'il le fait — jusque dans son nom.
- **Business Rhythm Engine** — le candidat le plus sérieux, car les Missions 2 et 3 ajoutent précisément une capacité de rythme (récurrence, dérive, projection) absente de v1/v2. Mais « Rhythm » seul ne couvrirait pas la moitié du modèle qui reste ponctuelle et non récurrente par nature — `BusinessMoment` est un instant significatif, pas un rythme ; `AnalysisPertinence` est un constat instantané, pas un motif périodique. Renommer autour du rythme sous-représenterait cette autre moitié.

**Décision : conserver Financial Time Engine.** « Financial » reste le périmètre exact et volontairement non extensible du modèle. « Time » reste le terme le plus englobant : il couvre à la fois l'instant (`BusinessMoment`), la structure récurrente (`FinancialCycle`, `BusinessHistory`) et la projection (`FutureBusinessMoment`) — le rythme est une propriété du temps, pas l'inverse, donc « Time » subsume « Rhythm » sans perte de sens, alors que l'inverse ne serait pas vrai. Un renommage romprait par ailleurs des références déjà établies (question ouverte n°2 d'ADR-001, ADR-002 §3.7, le nom du point d'intégration technique `temporal_context_section`) sans gain de clarté suffisant pour en justifier le coût — Article XII s'applique au nom lui-même, pas seulement aux objets.

---

## §6 — Cohérence ontologique (Mission 6)

| Objet | Répond à | Ne répond jamais à |
|---|---|---|
| `BusinessMoment` | Que signifie *cet instant*, maintenant ? (rétrospectif/présent) | Ce qui va se passer ensuite (→ `FutureBusinessMoment`) ; ce qui s'est répété (→ `BusinessHistory`) |
| `FutureBusinessMoment` | Quel est probablement le prochain instant significatif ? (prospectif) | Ce qui s'est déjà passé ; jamais une probabilité statistique |
| `FinancialCycle` | Quel rythme est **déclaré/attendu** pour cet Engagement ? | Quel rythme est **réellement observé** (→ `BusinessHistory.RhythmDrift`, jamais fusionné avec le déclaré — voir §2.2, INV-HISTORY-4) |
| `BusinessHistory` | Quel comportement s'est **répété** au moins trois fois ? | Interpréter ce que ce comportement signifie financièrement (→ hors FTE, §7.2) |
| `FiscalCalendar` | Sur quel exercice cet Engagement raisonne-t-il ? | Rien d'autre — le VO le plus étroit du modèle, volontairement |
| `RecommendationLifetime` | Quelles dates encadrent cette recommandation ? (faits) | Si elle est due/en retard (→ `RecommendationTemporalState`, dérivé, jamais stocké) |
| `RecommendationTemporalState` | Est-il temporellement approprié d'évaluer cette recommandation ? | Ce que le client en a décidé (→ `Recommendation.status`, T3, orthogonal) |
| `AnalysisPertinence` | Ce moment justifie-t-il une nouvelle analyse, pour *cet* Engagement ? | Où porter l'attention *à travers le portefeuille* (→ Attention Score, hors FTE) |
| `ComparisonHorizon` | Quels points de référence sont pertinents maintenant ? | Si la valeur comparée s'améliore ou se dégrade (→ hors FTE, §7.2) |
| `TemporalWarning` | Un fait isolé et inattendu s'est-il produit ? | Un fait qui s'est répété (→ `BusinessHistory`, seuil INV-HISTORY-1) |

Aucune paire de cette table ne se recouvre : chacune se distingue soit par l'axe temporel (passé constaté / avenir projeté), soit par la nature de la vérité portée (déclaré / observé), soit par la frontière de Bounded Context (structure temporelle / contenu financier / décision business).

---

## §7 — Frontières DDD : le FTE reste Supporting, jamais Core (Mission 7)

### 7.1 — Ce qui protège la frontière

La classification Supporting-mais-amont-de-tout (v2 §4.2) n'est pas remise en cause par les nouvelles capacités : `BusinessHistory` et `FutureBusinessMoment` restent tous deux des **constats structurels**, jamais des choix. Un `BusinessHistory` ne recommande pas d'ajuster un contrat ; il constate un écart. Un `FutureBusinessMoment` n'annonce pas qu'une action doit être prise ; il annonce qu'un instant approche. C'est exactement la distinction déjà établie par l'Axiome 7 et INV-TIME-9 (v2 §4.1/§4.4), désormais appliquée à deux objets supplémentaires sans exception.

### 7.2 — La preuve par le retrait, pas seulement par l'assertion

Une frontière n'est vraiment démontrée que si l'on peut montrer ce qu'on a refusé d'y faire entrer. Trois refus explicites, tous soulevés par cette révision :

1. **`MetricTrend` (« la marge diminue depuis quatre analyses ») — refusé.** Juger qu'une marge diminue exige de lire une valeur financière et de la qualifier (bonne/mauvaise direction) — c'est un jugement de contenu, propriété de Financial Evidence & Truth / Advisory Judgment, jamais du FTE. Le FTE fournit seulement la scaffolding qui rend ce jugement possible ailleurs : une séquence de `FiscalPeriod` comparables, correctement ordonnée — ce qu'il fait déjà via `ComparisonHorizon`. Rien de plus.
2. **`PersistentRecommendation` comme objet séparé — refusé.** Le besoin est entièrement couvert par une lecture de `RecommendationTemporalState=overdue` combinée à la durée écoulée depuis `proposedAt` (déjà disponible sur `RecommendationLifetime`). Ajouter un objet dédié dupliquerait une capacité existante sans rien ajouter (test de simplicité, §8).
3. **`TemporalNarrative` à l'intérieur du FTE — refusé (§4.1).** Rédiger des phrases est une activité de projection, propriété de Reporting & Deliverables par précédent déjà établi (Article VIII, `conversation_engine.py`).

Ces trois refus sont la démonstration demandée par la Mission 7 : le FTE ne gagne aucune capacité de jugement, de contenu ou de rédaction en devenant plus riche — il gagne seulement en capacité de constat structurel.

---

## §8 — Test de simplicité, Article XII (Mission 8)

| Objet | Si supprimé, quelle capacité métier disparaît ? | Verdict |
|---|---|---|
| `BusinessHistory` (`RhythmDrift`) | Impossible de distinguer un retard exceptionnel d'un retard habituel pour un Engagement — `AnalysisPertinence` retomberait sur une hypothèse statique fausse pour toute organisation à comportement récurrent (§1) | **Conservé** |
| `BusinessHistory` (`RecurringSignal`) | Impossible de dire qu'une anomalie ou un besoin revient structurellement plutôt qu'une fois — signal perdu pour Attention Score et Review Briefing | **Conservé** |
| `FutureBusinessMoment` | Impossible de préparer un utilisateur avant une échéance ; le FTE resterait purement réactif, contredisant explicitement la Mission 3 | **Conservé** |
| `MetricTrend` (rejeté) | Aucune — la capacité existe déjà ailleurs dans le domaine cible (Financial Evidence & Truth) | **Non créé** |
| `PersistentRecommendation` (rejeté) | Aucune — entièrement dérivable de `RecommendationTemporalState` + `RecommendationLifetime.proposedAt` | **Non créé** |
| `TemporalNarrative` (rejeté) | Aucune capacité de compréhension — seulement une capacité de rédaction, déjà couverte par Reporting & Deliverables | **Non créé** |

Trois objets sur six candidats examinés ont été refusés. C'est la preuve la plus concrète possible que le test a été appliqué avec rigueur, et non de façon rhétorique.

---

## §9 — Invariants, événements et cartographie (récapitulatif consolidé)

**Invariants v2 conservés :** INV-TIME-1 à 11 (voir v2, inchangés).
**Invariants nouveaux :** INV-HISTORY-1 à 4 (§2.2), INV-FUTURE-1 à 3 (§3.2).

**Événements nouveaux :** `BusinessHistoryPatternDetected`, `BusinessHistoryPatternBroken`, `RhythmDriftConfirmed`, `FutureBusinessMomentProjected`, `FutureBusinessMomentInvalidated`.

**Cartographie des dépendances — ajouts sur la base de v2 §4.10 :**

| Composant | Nouvelle dépendance |
|---|---|
| Review Briefing | `BusinessHistory` (contextualiser un retard), `FutureBusinessMoment` (préparer avant l'échéance) |
| Attention Score (T4) | `BusinessHistory` comme signal renforcé (récurrence > occurrence isolée), `FutureBusinessMoment` à `basisStrength=declared` proche |
| Recommendation Engine (T3) | `BusinessHistory.RhythmDrift` comme fait pouvant motiver une recommandation d'ajustement de cadence (jamais proposé par le FTE lui-même) |
| Reporting & Deliverables | **Nouvelle responsabilité assignée** — lexique temporel déterministe, propriétaire des six surfaces fermées listées en §4.2 |

---

## §10 — Alternatives rejetées (ajouts sur la base de v2 §5)

- **Fusionner `RhythmDrift` et `RecurringSignal` en un objet unique sans discriminant de type** — rejetée : les attributs propres à chacun (`declaredLag`/`observedAverageLag` vs `signalOrigin`/`signalReference`) ne se recouvrent pas ; les regrouper aurait produit un objet aux champs partiellement toujours vides, contraire à la simplicité recherchée.
- **Laisser `FinancialCycle.typicalLag` être réécrit automatiquement par un `RhythmDrift` confirmé** — rejetée : romprait la discipline de confirmation humaine déjà établie pour `FinancialCycleInferred` (INV-HISTORY-4).
- **Faire de `FutureBusinessMoment` un score de probabilité** — rejetée explicitement par le mandat lui-même ; `basisStrength` reste une gradation structurelle (déclaré/observé/assumé), jamais une probabilité (INV-FUTURE-3).
- **Renommer le moteur en Business Rhythm Engine** — rejetée, raisonnement complet en §5.

---

## §11 — Auto-critique et notation (Mission 9)

**Hypothèses fragiles.** Le seuil de trois occurrences (INV-HISTORY-1) est une convention raisonnable, pas une valeur validée empiriquement — rien ne prouve que trois est le bon seuil plutôt que quatre ou cinq pour éviter les faux motifs sur des historiques courts. Le calcul de `observedAverageLag` tel que décrit reste une moyenne simple ; une seule occurrence extrême dans un historique court peut la fausser significativement, et cette ADR ne prescrit aucune robustesse statistique au-delà du seuil de comptage — c'est une simplification assumée, pas une garantie.

**Risques.** Le lexique temporel (§4) suppose que les six surfaces fermées couvriront toujours les situations réelles rencontrées ; une combinaison d'interprétations non anticipée par le lexique n'a pas de comportement de repli défini ici — ce risque n'est pas résolu, seulement déplacé vers Reporting & Deliverables sans qu'aucune garantie ne soit donnée qu'il sera traité avec le même soin. Le risque de dérive de portée déjà nommé en v2 (§4.14) reste entier et s'étend maintenant à `BusinessHistory`/`FutureBusinessMoment` : rien n'empêche techniquement qu'un développeur pressé transforme un jour `FutureBusinessMoment` en recommandation déguisée (« vous devriez préparer votre board maintenant ») — seule une vigilance de revue de code, pas un mécanisme du langage, protège cette frontière.

**Simplifications possibles.** `BusinessHistory` pourrait être différé à une itération ultérieure sans bloquer le reste du modèle (`FutureBusinessMoment` à `basisStrength=declared` fonctionne déjà sans lui) — ce n'est pas fait ici par choix de cohérence du document, mais une implémentation par étapes est légitime.

**Parties spéculatives.** Toute la section 5 (naming) est un jugement éditorial assumé comme tel — défendable, non vérifiable empiriquement. Le choix des trois `basis` de `FutureBusinessMoment` (§3.2) couvre les quatre exemples du mandat mais n'a aucune garantie d'exhaustivité face à des cas réels non anticipés.

**Ce qui devra être confronté au réel avant toute confiance.** Le seuil INV-HISTORY-1, la robustesse de `observedAverageLag`, la couverture réelle du lexique temporel face à des cas non prévus, et surtout : est-ce qu'un CFO utilisateur trouve une distinction `declared`/`observed`/`assumed` utile et compréhensible, ou est-ce que cette nuance, correcte sur le papier, s'avère être du bruit à l'usage ? Rien dans ce document ne peut répondre à cette dernière question — seul un utilisateur réel le peut.

**Notation : ADR-003 v3 = 9/10, pas 10/10.** L'écart avec v2 (8,5) se justifie par trois apports vérifiables : la frontière Supporting/Core est désormais prouvée par trois refus concrets et non plus seulement par un invariant déclaratif ; le résidu calendaire identifié en v1→v2 (cadence toujours assumée, jamais observée) est refermé par `BusinessHistory` sans casser la discipline de confirmation humaine déjà en place ; la capacité prospective est ajoutée sans jamais franchir la ligne vers la prédiction ou la décision. Le score reste sous 10 parce que le seuil de trois occurrences, la méthode de moyenne du décalage observé, et la couverture réelle du lexique temporel sont des choix de conception cohérents mais non éprouvés — et parce que la question la plus décisive de cette révision (l'utilité perçue de `basisStrength` par un utilisateur réel) reste, par construction, hors de portée d'un document d'architecture.

---

## §12 — Question systémique de clôture

**Si Pepperyn perdait totalement la notion de temps, quelles capacités métier disparaîtraient immédiatement ?**

Toute comparaison (mois précédent, YTD, Rolling 12, budget) disparaît — et la comparaison est la matière première de presque tout jugement qu'un CFO porte ; une analyse sans référence temporelle redevient un simple relevé de chiffres. Le cycle complet de la Recommandation (proposée → exécutée → conséquences → apprentissage, Constitution Article VI, déjà implémenté partiellement via `DecisionArc`) s'effondre : sans le temps, une recommandation ne peut jamais être jugée trop tôt, à temps ou obsolète — elle reste figée dans un présent perpétuel. L'Attention Score (T4, pas encore construit) devient impossible par construction : l'attention est, par définition, une question de *maintenant* face à *avant*. Le Review Briefing perd sa justification (« pourquoi cette revue, pourquoi maintenant ») et redevient un résumé sans motif. La Mémoire décisionnelle (Constitution Article V) cesse d'exister au sens propre : mémoriser, c'est déjà relier des instants entre eux.

**Cette réponse ne couvre pas l'ensemble du produit — et c'est révélateur.** Plusieurs parties de Pepperyn, aujourd'hui réelles, ne sont *pas encore* véritablement temporelles, alors qu'elles devraient l'être :

- Les exports PDF/PPTX/Excel citent aujourd'hui des dates comme des chaînes de caractères brutes (l'anti-pattern exact nommé en Mission 4, « Dernière analyse : 28 septembre ») — ils ne consomment aucun objet temporel structuré, v2 comme v3 compris, tant que Reporting & Deliverables n'aura pas implémenté le lexique temporel décrit en §4.
- `arc_service.py`, en code réel aujourd'hui, recalcule un âge en jours à six endroits indépendants (déjà nommé en v2 §3, jamais corrigé par aucune version de cette ADR) — c'est, très concrètement, la partie du système la moins temporellement consciente de tout Pepperyn, alors qu'elle est celle qui affiche le plus de texte relatif au temps à l'utilisateur final.
- `ReviewCadence` (ADR-002) est déclarée mais jamais appliquée — une donnée temporelle existe déjà en base sans qu'aucun composant n'en tienne compte activement.
- Portfolio, en code réel, trie et affiche par `age_days` ad hoc, pas par un objet temporel du domaine.

Autrement dit : le modèle conceptuel du temps, après cette troisième révision, est probablement maintenant plus riche que ce que le reste du produit sait en faire. La prochaine question d'architecture sérieuse n'est plus *« le FTE est-il assez riche ? »* — elle est *« qu'est-ce qui empêche aujourd'hui le reste de Pepperyn de consommer ce que le FTE sait déjà faire ? »*. Cette question dépasse le périmètre de cette ADR ; elle est la bonne candidate pour la prochaine.

---

**ADR-003 v3 READY FOR REVIEW. REMPLACE ADR-003 v2 INTÉGRALEMENT. AUCUN CODE MODIFIÉ.**
