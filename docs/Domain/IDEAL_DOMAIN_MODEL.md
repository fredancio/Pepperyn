# The Ideal Domain Model for Fractional / Outsourced CFO Software
**Exercice :** conception greenfield, sans référence à un produit existant.
**Posture :** architecte DDD indépendant, mandaté pour définir le meilleur modèle métier possible pour un logiciel au service des CFO externalisés (fractional CFOs, cabinets de CFO-as-a-service).

---

## A. Ce qu'on construit réellement

Un CFO externalisé ne vend pas des rapports. Il vend une **présence de confiance dans le temps**, distribuée sur un portefeuille de sociétés qu'il ne peut pas suivre en continu comme un CFO interne le ferait. Sa contrainte fondamentale n'est pas la donnée, ni le calcul — c'est **l'attention**. Il a un nombre fini d'heures et un nombre croissant de clients ; son métier consiste à décider, chaque semaine, *où regarder d'abord*, à transformer ce qu'il voit en un jugement défendable, et à faire en sorte que ce jugement reste vrai la fois suivante.

Le logiciel idéal ne doit donc pas être pensé comme « un outil qui analyse un fichier », mais comme **un système qui gère une relation continue, multi-clients, où chaque nouvelle donnée doit d'abord répondre à une question unique : est-ce que ceci mérite l'attention du CFO maintenant ?**

**Résultat final produit par le système, dans l'ordre d'importance :**
1. Une allocation d'attention défendable across le portefeuille (« sur quoi je travaille cette semaine, et pourquoi »).
2. Un jugement professionnel chiffré et sourcé sur une situation donnée (une décision, pas un rapport).
3. Une trace de ce jugement dans le temps — ce qui a été recommandé, accepté, exécuté, et ce qui s'est réellement passé.
4. Un livrable de confiance (revue mensuelle, board pack, prévision de trésorerie) qui *restitue* ce jugement à un tiers, sans jamais le recalculer.

**Objet qui génère toute la chaîne :** ce n'est pas un fichier uploadé (comme dans un outil d'analyse ponctuelle). C'est **l'ouverture d'une nouvelle période comptable sur une relation client active** — un événement récurrent, prévisible, porté par le calendrier, pas par l'initiative manuelle d'un utilisateur.

---

## B. Classification stratégique des sous-domaines

*(Convention DDD — Eric Evans / Vaughn Vernon : Core = où se joue l'avantage concurrentiel et où l'investissement d'ingénierie doit être maximal ; Supporting = nécessaire, mérite du sur-mesure mais n'est pas différenciant ; Generic = acheter, ne jamais construire.)*

| Sous-domaine | Classification | Pourquoi |
|---|---|---|
| **Attention & Priorisation de portefeuille** | **Core** | C'est la contrainte réelle du métier (temps fini, clients multiples). Aucun logiciel générique ne le résout. |
| **Vérité financière & Preuve (Evidence)** | **Core** | La confiance du client dans un chiffre non vérifié par lui-même est l'actif central vendu par le CFO. |
| **Jugement consultatif & Mémoire décisionnelle** | **Core** | Ce que le CFO *pense* et *a pensé* est le produit. Un concurrent peut copier un format de rapport ; il ne peut pas copier un historique de jugement accumulé. |
| **Résolution d'exceptions & réconciliation** | **Core** | C'est le travail réel du « Human Middle » — la partie qui ne s'automatise jamais complètement et qui consomme le plus de temps. |
| **Cycle de vie de la relation client (Engagement)** | Supporting | Nécessaire à toute pratique de service, mais un CRM générique fait 80% du travail. Le sur-mesure est dans le lien avec les autres contextes Core, pas dans la gestion du contrat elle-même. |
| **Livrables & Restitution** | Supporting | La mise en forme (PDF/board deck/prévision) est un aval, pas un différenciateur en soi — mais elle doit être fidèle à 100% au jugement, donc mérite un contexte dédié. |
| **Ingestion & normalisation de données** | Supporting | Connecter des systèmes comptables/bancaires/ERP hétérogènes est un travail réel mais largement solvable par des connecteurs standards — la valeur est dans ce qu'on en fait après, pas dans la connexion elle-même. |
| **Benchmark de portefeuille** | Supporting | Utile, différenciant à la marge, mais dépendant entièrement des données déjà capturées par les contextes Core. |
| **Identité & gestion du cabinet (practitioners, équipes)** | Generic | Multi-tenant RBAC classique. |
| **Temps & facturation** | Generic | Time-tracking et facturation existent déjà en excellence ailleurs (Harvest, Stripe Billing...) — à intégrer, jamais à reconstruire. |
| **Communication & messagerie** | Generic | Le canal de discussion est générique ; ce qui est différenciant c'est *ce dont on parle* (Jugement, Preuve), pas le fil de discussion lui-même. |

**Conséquence architecturale directe :** un logiciel qui investit son ingénierie dans « générer un joli PDF » ou « connecter plus d'ERP » optimise des sous-domaines Supporting. Le logiciel gagnant investit dans la Priorisation, la Preuve, le Jugement et la Résolution d'exceptions — c'est là que se joue la defensibilité.

---

## C. Langage ubiquitaire (extrait)

| Terme | Définition métier stricte |
|---|---|
| **Engagement** | La relation contractuelle continue entre le cabinet CFO et une société cliente. A un début, une cadence, potentiellement une fin. Unité d'appartenance de tout le reste. |
| **Portfolio** | L'ensemble des Engagements actifs d'un practitioner ou d'un cabinet, à un instant donné. |
| **Attention Score** | Un signal calculé, par Engagement, indiquant l'urgence relative de l'intervention humaine, recalculé à chaque nouvel événement financier. |
| **Financial Fact** | Une donnée financière unitaire, ancrée à sa source (compte, ligne, période), avec un niveau de confiance explicite. Jamais une opinion. |
| **Materiality** | Le seuil, propre à chaque Engagement, au-delà duquel un écart mérite l'attention humaine plutôt qu'un simple enregistrement. |
| **Exception** | Un écart, une incohérence ou une anomalie détectée entre des Financial Facts, dont la nature exacte n'est pas encore déterminée — nécessite investigation. |
| **Recommendation** | Un jugement professionnel proposé par le CFO, avec un impact attendu chiffré et un raisonnement explicite. |
| **Decision** | Ce que le client a réellement choisi de faire (ou non) d'une Recommendation. |
| **Outcome** | Ce qui s'est réellement passé après une Decision, mesuré lors d'une période ultérieure. |
| **Deliverable** | Un artefact de restitution figé dans le temps (revue mensuelle, board pack, prévision), qui *lit* mais ne recalcule jamais le Jugement. |
| **Cadence** | Le rythme contractuel de revue d'un Engagement (mensuel, trimestriel...), qui détermine quand une nouvelle période « s'ouvre ». |
| **Provenance** | La chaîne de traçabilité reliant un chiffre affiché à sa source primaire. |

---

## D. Carte des Bounded Contexts et leurs relations

```
                         ┌────────────────────────┐
                         │  Practice & Identity     │  (Generic)
                         │  (practitioners, accès)  │
                         └────────────┬────────────┘
                                      │ Open Host Service (qui a accès à quel Engagement)
                                      ▼
                         ┌────────────────────────┐
                         │  Client Engagement       │  (Supporting — mais AMONT de tout)
                         │  (relation, cadence,      │
                         │   scope, contacts)        │
                         └────────────┬────────────┘
                                      │ Published Language : engagement_id
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
  ┌───────────────────┐   ┌────────────────────┐   ┌─────────────────────┐
  │ Data Ingestion &    │──▶│ Financial Evidence   │──▶│ Portfolio Attention   │
  │ Normalization        │ ACL│ & Truth (Core)       │  │ & Prioritization (Core)│
  │ (Supporting)          │   │                       │  │                       │
  └───────────────────┘   └──────────┬──────────┘   └───────────┬───────────┘
                                      │ Customer/Supplier          │ pilote
                                      ▼                            ▼
                         ┌────────────────────────┐   ┌─────────────────────┐
                         │ Exception & Reconciliation│──▶│ Advisory Judgment &   │
                         │ (Core)                    │  │ Decision Memory (Core)│
                         └────────────────────────┘   └───────────┬───────────┘
                                                                    │ Customer/Supplier
                                                                    ▼
                                                        ┌─────────────────────┐
                                                        │ Reporting &           │
                                                        │ Deliverables (Supporting)│
                                                        └───────────┬───────────┘
                                                                    │ publie vers
                                                                    ▼
                                                        ┌─────────────────────┐
                                                        │  Client (hors système) │
                                                        └─────────────────────┘

  ┌───────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
  │ Time & Billing      │        │ Portfolio Benchmarking│        │ Client Communication  │
  │ (Generic, intégré)  │        │ (Supporting, lecture   │        │ (Generic, threadé par  │
  │                      │        │  seule sur Evidence)    │        │  Engagement)           │
  └───────────────────┘        └─────────────────────┘        └─────────────────────┘
```

**Relations clés (patterns DDD explicites) :**
- **Client Engagement → tous les contextes Core** : *Published Language*. Chaque contexte Core est scoping par `engagement_id` mais ne connaît rien de la logique commerciale de l'Engagement (cadence de facturation, contrat) — juste son identité et sa Cadence de revue.
- **Data Ingestion → Financial Evidence** : *Anti-Corruption Layer*. Les systèmes sources (comptabilité, banque, ERP) sont hétérogènes et parfois incohérents ; rien de leur vocabulaire ne doit fuiter dans le modèle de Financial Fact.
- **Financial Evidence → Exception & Reconciliation** : *Customer/Supplier*. Evidence produit des faits ; Exception les consomme pour détecter des écarts. Evidence ne sait rien des Exceptions.
- **Financial Evidence + Exception → Portfolio Attention** : *Customer/Supplier*. L'Attention Score est recalculé à partir des faits et des exceptions, jamais l'inverse.
- **Exception + Evidence → Advisory Judgment** : *Customer/Supplier*. Une Recommendation cite des Facts et peut répondre à une ou plusieurs Exceptions — mais Advisory Judgment ne modifie jamais Evidence ni Exception.
- **Advisory Judgment → Reporting & Deliverables** : *Customer/Supplier strict, lecture seule*. Un Deliverable n'a AUCUN pouvoir de recalcul — règle absolue, héritée du constat que c'est précisément là que la confiance se perd si elle est violée.
- **Portfolio Benchmarking** : *Conformist* en lecture seule sur Evidence anonymisée — ne pilote jamais de décision individuelle.
- **Time & Billing, Communication, Practice & Identity** : Generic Subdomains, intégrés via *Open Host Service* / API standards, jamais développés en profondeur métier.

---

## E. Détail par Bounded Context

### E.1 — Client Engagement (Supporting, amont)

- **Agrégat racine : `Engagement`**
  - Identité : `EngagementId`
  - Entités : `StakeholderContact` (les interlocuteurs côté client), `ScopeDefinition` (ce qui est couvert : entités légales, périmètre géographique)
  - Value Objects : `EngagementStatus` (prospect | active | paused | at_risk | churned), `ReviewCadence` (mensuelle/trimestrielle + jour cible), `RetainerTerms`
  - Invariant : un Engagement ne peut passer en `active` sans au moins une `ScopeDefinition` et une `ReviewCadence` définies.
  - Cycle de vie : `prospected → active → (paused ↔ active) → churned`. Le passage `at_risk` est un état parallèle dérivé, pas une transition manuelle (voir Attention Score).
  - Événements : `EngagementActivated`, `EngagementPaused`, `EngagementCadenceChanged`, `EngagementChurned`.

### E.2 — Data Ingestion & Normalization (Supporting)

- **Agrégat racine : `SourceConnection`** (un lien vers un système externe — comptabilité, banque, ERP — pour un Engagement donné)
  - Entités : `SyncRun` (une exécution de synchronisation), `ImportBatch`
  - Value Objects : `ConnectionHealth`, `DataFreshness`
  - Invariant : un `SyncRun` ne peut jamais écrire directement dans Financial Evidence sans passer par une étape de normalisation explicite (l'ACL) — aucune donnée brute externe n'entre telle quelle dans le langage ubiquitaire du domaine.
  - Événements : `SourceConnected`, `SyncCompleted`, `SyncFailed`, `DataFreshnessDegraded`.

### E.3 — Financial Evidence & Truth (**Core**)

- **Agrégat racine : `EvidenceLedger`** (un par Engagement × période)
  - Entités : `FinancialFact` (un chiffre ancré : montant, compte, période, source), `SourceDocument`
  - Value Objects : `Provenance` (document + ligne + citation), `ConfidenceLevel`, `Materiality` (seuil propre à l'Engagement)
  - Invariant fondamental : **une donnée absente reste absente — jamais convertie en zéro.** Un `FinancialFact` sans `Provenance` suffisante ne peut jamais alimenter un total certifié (seulement un total indicatif, explicitement marqué comme tel).
  - Invariant : un `EvidenceLedger` est immuable une fois la période clôturée côté client — toute correction ultérieure crée une nouvelle version tracée, jamais une réécriture silencieuse.
  - Événements : `FactObserved`, `FactDisputed`, `PeriodEvidenceClosed`, `MaterialityThresholdBreached`.

### E.4 — Exception & Reconciliation (**Core**)

- **Agrégat racine : `Exception`**
  - Entités : `InvestigationNote`, `ResolutionAction`
  - Value Objects : `ExceptionSeverity`, `ExceptionCategory` (ex. : délai de facturation, dérive de marge, tension de trésorerie, coût structurel), `ResolutionPath` (auto-résolu / nécessite jugement humain / escaladé)
  - Invariant : une `Exception` ne peut être fermée sans `ResolutionAction` explicite OU une justification écrite de non-action — le silence n'est jamais une clôture valide.
  - Cycle de vie : `raised → investigating → (resolved | escalated | dismissed_with_reason)`
  - Événements : `ExceptionRaised`, `ExceptionAssigned`, `ExceptionResolved`, `ExceptionEscalated`.

### E.5 — Portfolio Attention & Prioritization (**Core** — le cœur différenciant)

- **Agrégat racine : `AttentionSignal`** (un par Engagement, recalculé en continu)
  - Value Objects : `AttentionScore` (composite : matérialité des écarts, nombre d'exceptions ouvertes, ancienneté de la dernière revue, proximité de la Cadence contractuelle, historique de fiabilité du client), `AttentionReason` (explicable — jamais une boîte noire)
  - Invariant : `AttentionScore` doit toujours être accompagné d'au moins un `AttentionReason` traçable vers un Fact ou une Exception — un score sans explication n'est pas publiable.
  - C'est **l'objet qui remplace la notion de « file d'attente » ou de « liste de tâches »** : au lieu que le practitioner choisisse un client au hasard ou par habitude, le système répond en continu à « où dois-je regarder maintenant, et pourquoi ».
  - Événements : `AttentionScoreRecomputed`, `AttentionEscalatedToUrgent`.

### E.6 — Advisory Judgment & Decision Memory (**Core**)

- **Agrégat racine : `Recommendation`**
  - Cycle de vie complet : `proposed → discussed → (accepted | rejected | deferred) → executed → outcome_observed → closed`
  - Entités : `DiscussionNote` (échange avec le client sur cette recommandation)
  - Value Objects : `ExpectedImpact` (chiffré, avec la même rigueur de provenance qu'un Financial Fact), `ActualOutcome` (mesuré à une période ultérieure), `Learning` (ce que cet écart entre attendu et réel nous apprend pour la prochaine fois)
  - Invariant : `ActualOutcome` ne peut être renseigné que sur une `Recommendation` déjà `executed`, et doit référencer un `EvidenceLedger` postérieur à l'exécution — jamais une estimation.
  - Invariant : le texte d'une `Recommendation` est immuable une fois `discussed` — toute évolution du raisonnement crée une nouvelle `Recommendation` liée (`supersedes`), jamais une réécriture.
  - C'est ici que vit la **mémoire de jugement** — l'actif qui s'accumule avec le temps et qui ne peut pas être répliqué par un concurrent qui démarre à zéro.
  - Événements : `RecommendationProposed`, `RecommendationAccepted`, `RecommendationRejected`, `RecommendationExecuted`, `OutcomeRealized`, `LearningCaptured`.

### E.7 — Reporting & Deliverables (Supporting, mais à discipline Core)

- **Agrégat racine : `Deliverable`** (une instance figée, versionnée, pour un Engagement × période × type)
  - Value Objects : `DeliverableType` (Monthly Review, Board Pack, Cash Forecast, Ad-hoc Memo), `ApprovalStatus`, `DistributionRecord`
  - **Règle absolue héritée de la discipline Core :** un `Deliverable` ne fait QUE lire `EvidenceLedger` + `Recommendation` déjà clos/acceptés au moment de sa génération. Aucun recalcul, aucune extrapolation, aucune donnée qui n'existe pas déjà ailleurs dans le domaine. Le practitioner doit **approuver explicitement** avant tout envoi — jamais d'envoi automatique.
  - Invariant : PDF, présentation, Excel d'un même `Deliverable` doivent être des projections strictement identiques de la même donnée — pas de champ présent dans un format et absent d'un autre.
  - Événements : `DeliverableDrafted`, `DeliverableApproved`, `DeliverableSent`.

### E.8 — Portfolio Benchmarking (Supporting)

- **Agrégat racine : `BenchmarkCohort`** (un secteur/une taille d'entreprise)
  - Value Objects : `AnonymizedMetric`, `PercentileRank`
  - Invariant : aucune donnée individualisée d'un Engagement ne doit être reconstructible depuis un `BenchmarkCohort` (k-anonymat minimal appliqué avant toute agrégation).

### E.9 — Practice & Identity / Time & Billing / Communication (Generic)

- Modélisés a minima, intégrés via API standards. Le seul couplage métier réel : un `Practitioner` est assigné à un ou plusieurs `Engagement` (Practice & Identity), et un `TimeEntry` référence un `engagement_id` (Time & Billing) — au-delà, ces contextes n'ont aucune connaissance du langage ubiquitaire des contextes Core.

---

## F. Workflow métier (narration, pas le pipeline technique)

1. **Une nouvelle période s'ouvre** pour un Engagement, au rythme de sa Cadence contractuelle — c'est le calendrier qui déclenche, jamais un utilisateur qui « uploade quelque chose ».
2. **Les données de la période arrivent** via les connexions actives (comptabilité, banque) et sont normalisées en `FinancialFact`s ancrés à leur source.
3. **La vérité financière se met à jour** (`EvidenceLedger`) — chaque fait absent reste explicitement absent, jamais estimé à zéro.
4. **L'attention du portefeuille se recalcule** : le système compare les nouveaux faits aux seuils de matérialité propres à cet Engagement et à son historique. Si rien de significatif n'a changé, l'Engagement reste discret dans le portefeuille — **c'est un succès du système, pas une absence de travail**.
5. **Si un écart dépasse le seuil**, une ou plusieurs `Exception`s sont soulevées, et l'`AttentionScore` de l'Engagement grimpe, avec une raison explicite.
6. **Le CFO ne parcourt jamais client par client** — il ouvre son portefeuille trié par attention, traite les Exceptions les plus critiques en premier, à travers tous ses clients.
7. **Pour chaque Exception significative**, le CFO investigue (note, action), et le cas échéant propose une `Recommendation` — un jugement chiffré, sourcé, discutable.
8. **La Recommendation est discutée avec le client** (canal générique de communication), puis acceptée, rejetée ou différée — cette décision est celle du client, jamais automatisée.
9. **Le `Deliverable` de la période** (revue mensuelle, board pack) est assemblé en lisant uniquement ce qui existe déjà — Evidence + Recommendations closes de la période — jamais recalculé. Le CFO l'approuve avant envoi.
10. **À la période suivante**, les Recommendations `executed` de la période précédente sont confrontées aux nouveaux Facts : un `Outcome` est mesuré, un `Learning` est capturé, et ce Learning influence la pondération de l'Attention Score pour cet Engagement dans le futur (un client dont les recommandations passées ont mal tourné mérite plus d'attention préventive, pas moins).

**Ce qui rend ce workflow structurellement différent d'un outil d'analyse ponctuelle :** l'étape 6 (triage transversal du portefeuille) est un mouvement *horizontal*, à travers tous les clients, absent de tout système pensé « un fichier → un rapport ». C'est ce mouvement horizontal qui constitue la véritable proposition de valeur pour un CFO qui gère 15, 30 ou 50 mandats en parallèle.

---

## G. L'objet central du domaine

Il y a une réponse à deux niveaux, et prétendre qu'un seul agrégat domine serait une simplification excessive et un carcan de conception.

**Niveau structurel — ce qui donne son identité à tout le reste :** `Engagement`. Rien n'existe dans ce domaine sans être scoping par une relation client active. C'est le fil qui traverse chaque contexte.

**Niveau de valeur — ce qui est réellement produit et qui s'accumule :** `Recommendation` (dans Advisory Judgment & Decision Memory). C'est l'unique objet du domaine qui possède un cycle de vie complet reliant un jugement (`proposed`), une décision humaine externe (`accepted/rejected`), une réalité mesurée (`outcome`), et un apprentissage capturé (`learning`) qui reboucle sur le système lui-même (l'Attention Score). Aucun autre objet du domaine n'a cette propriété de **boucle fermée avec la réalité** — et c'est précisément cette boucle fermée qui constitue, dans la durée, l'actif défendable d'un cabinet de CFO externalisé face à un concurrent qui pourrait copier son format de rapport du jour au lendemain mais jamais son historique de jugement validé.

Un architecte qui devrait choisir un seul agrégat à protéger jalousement, à ne jamais corrompre, à ne jamais laisser un tiers service réécrire silencieusement, choisirait `Recommendation`.

---

## H. Invariants globaux du domaine (non négociables)

1. **Absence de donnée ≠ zéro.** Aucune valeur financière manquante n'est jamais silencieusement convertie en zéro, nulle part dans le système.
2. **Aucun Deliverable ne recalcule.** La couche de restitution lit ; elle ne produit jamais de nouvelle vérité.
3. **Toute Recommendation cite sa Provenance.** Un jugement sans donnée sourcée sous-jacente n'est pas une Recommendation valide, c'est une opinion — catégorie distincte, jamais confondue.
4. **Aucune clôture silencieuse.** Une Exception ou une Recommendation ne se ferme jamais sans trace explicite de la raison.
5. **L'Attention Score est toujours explicable.** Jamais un score sans au moins une raison traçable vers un fait ou une exception.
6. **Le client décide, le système ne décide jamais à sa place.** Toute transition impliquant un engagement financier réel (Decision, envoi d'un Deliverable) requiert une action humaine explicite, jamais une automatisation silencieuse.
7. **Rien n'entre dans le langage ubiquitaire sans normalisation.** Les systèmes externes (comptabilité, banque, ERP) ne contaminent jamais directement le modèle — toujours via une couche anti-corruption.

---

## I. Pourquoi ce modèle gagne

Ce modèle inverse la question que la plupart des logiciels financiers posent. La question habituelle est *« comment produire le meilleur rapport possible à partir d'un fichier »* — une question de présentation. La question que ce modèle pose est *« comment un professionnel fini en temps peut-il rester digne de confiance sur un nombre croissant de relations »* — une question d'allocation d'attention et de mémoire de jugement.

Trois choix structurels portent cette différence :
- **`Engagement` et non `Analysis` comme racine.** La valeur se construit dans la continuité d'une relation, pas dans un événement isolé.
- **`AttentionScore` comme citoyen de première classe, avec son propre agrégat.** La priorisation n'est pas une fonctionnalité secondaire de tri d'une liste ; c'est un sous-domaine Core à part entière, parce que c'est la vraie contrainte du métier.
- **`Recommendation` avec boucle fermée (`Outcome`, `Learning`) comme unité de valeur.** Un jugement qui ne revient jamais confronter la réalité n'est qu'une opinion de plus ; un jugement qui se souvient d'avoir eu raison ou tort devient, avec le temps, un avantage impossible à rattraper.

Aucune de ces trois décisions ne dépend de la technologie sous-jacente (IA générative ou non) — elles tiennent uniquement à une lecture correcte de ce que fait réellement, humainement, un CFO externalisé compétent.
