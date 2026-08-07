# CAPABILITY ROADMAP v1

**Date :** 2026-08-03
**Type :** document de référence de l'avancement fonctionnel du produit (Niveau B — Implementation Document, dérivé des documents fondateurs, ne les modifie pas).
**Statut :** ouvre le pilotage par capacités métier. Le **Blueprint reste la feuille de route technique** (`PEPPERYN_TRANSFORMATION_BLUEPRINT_2026-08-02.md`) ; ce document devient l'unité de pilotage produit/business.

---

## 0. Méthode

Les capacités listées ici ne sont pas inventées. Elles sont déduites, dans cet ordre de priorité (GD-001, principe de précédence documentaire) :

1. **Constitution v1.0, Article IV — Le Modèle Métier** : nomme explicitement 6 objets permanents du domaine — l'Engagement, le fait, l'exception, la recommandation, le livrable, l'attention. Ce sont les 6 piliers dont dérivent 6 des 8 capacités ci-dessous.
2. **Ideal Domain Model (2026-08-02)**, section D-E : 9 Bounded Contexts, avec leur classification stratégique (Core / Supporting / Generic) et leurs agrégats racines nommés.
3. **Transformation Blueprint (2026-08-02)**, sections B et E : la table de correspondance objet-actuel → objet-cible, et les phases de migration T0-T6.
4. **ADR-001, ADR-001A, ADR-002** : les seules décisions d'architecture formellement adoptées à ce jour, et leur périmètre exact.

**Écart avec l'exemple fourni par Fred :** une capacité supplémentaire est ajoutée — **Exception & Reconciliation** — absente de la liste-exemple mais explicitement requise par deux sources de Niveau A/B : la Constitution (Article IV nomme « l'exception » comme objet permanent du domaine, au même rang que la recommandation) et l'Ideal Domain Model (E.4, Bounded Context **Core**, agrégat `Exception` avec cycle de vie et invariants propres — pas un sous-produit de la Recommandation). Le Blueprint ne lui consacre pas de phase dédiée (ligne B.6 : `DecisionKernel` → **ADAPT** partiel vers `Exception` + `Recommendation`), ce qui explique pourquoi l'écart n'était pas visible dans le pilotage par phase T0-T6 jusqu'ici. Elle est donc ajoutée ici comme **Capability 3**, ce qui décale la numérotation de l'exemple fourni sans en changer l'esprit.

---

## 1. Liste officielle des 8 capacités (Mission 3)

| # | Capacité | État |
|---|---|---|
| 1 | Financial Evidence | **DONE** |
| 2 | Engagement Lifecycle | **DONE** |
| 3 | Exception & Reconciliation | **FOUNDATION** |
| 4 | Recommendation Engine | **FOUNDATION** |
| 5 | Monthly Review Engine | **READY** |
| 6 | Attention Score | **FOUNDATION** |
| 7 | Portfolio Intelligence | **FOUNDATION** |
| 8 | Learning Loop | **FOUNDATION** |

États autorisés : **FOUNDATION** (matière première partiellement présente, aucun agrégat cible construit) · **READY** (prérequis satisfaits, peut démarrer) · **IN PROGRESS** · **DONE**.

Note d'ordre : la numérotation ci-dessus suit l'ordre de dépendance logique (voir `CAPABILITY_DEPENDENCY_MAP.md`), pas un ordre chronologique de développement — Monthly Review Engine (5) est **READY** avant que Recommendation Engine (4) ne soit **DONE**, précisément parce que ses prérequis stricts (Evidence + Engagement) sont déjà satisfaits.

---

## 2. Détail par capacité (Missions 3-4)

### Capability 1 — Financial Evidence
**État : DONE**

- **Pourquoi elle existe :** la Constitution (Article III) pose que « toute affirmation importante doit pouvoir être reliée à sa source » et qu'« une absence de donnée reste absente, jamais convertie en zéro ». Sans cette capacité, aucune autre n'est fondée sur du réel plutôt que sur du narratif généré.
- **Problème utilisateur résolu :** aujourd'hui, un chiffre présenté dans un rapport ne peut pas être distingué, par le CFO, d'une reformulation plausible du LLM — il doit tout revérifier avant de s'y fier (Constitution, Préambule : « une réponse rapide qui doit être intégralement revérifiée avant d'être crue ne fait pas gagner de temps ; elle en coûte »).
- **Ce qu'elle apporte au conseiller financier :** la capacité de citer, pour chaque chiffre présenté à son client, la cellule/ligne source exacte — condition de la confiance vendue par un CFO externe.
- **Concepts du domaine mobilisés :** `EvidenceLedger`, `FinancialFact`, `Provenance`, `ConfidenceLevel`, `Materiality` (Ideal Model E.3, Core).
- **Agrégats concernés (réel) :** table `evidence_ledger_entries` (migration v18), `financial_truth.py` (`QuantifiedImpact`, `SourceReference`).
- **Dépendances :** aucune — capacité fondatrice.
- **Capacités qui en dépendent :** Exception & Reconciliation, Recommendation Engine, Monthly Review Engine, Attention Score.
- **Source :** ADR-001, ADR-001A, Blueprint T1. Validée en conditions réelles : Integration Gate 1 (2026-08-03).

### Capability 2 — Engagement Lifecycle
**État : DONE**

- **Pourquoi elle existe :** la Constitution (Article IV) définit l'Engagement comme « le lien continu... qui précède et dépasse chaque intervention ponctuelle ». Sans cet objet, le produit ne peut raisonner qu'en « une analyse », jamais en « une relation suivie ».
- **Problème utilisateur résolu :** le Current Domain Model (section I) constate qu'avant cette capacité, « client suivi dans le temps » n'existait que comme un champ d'énumération optionnel (`entities.relation_type`) — aucune structure de relation réelle.
- **Ce qu'elle apporte au conseiller financier :** un cadre où chaque société suivie a une identité stable dans le temps, distincte d'un simple historique d'uploads.
- **Concepts du domaine mobilisés :** `Engagement`, `EngagementStatus`, `ReviewCadence` (Ideal Model E.1, Supporting mais amont de tout le reste).
- **Agrégats concernés (réel) :** table `engagements` (migration v19), fonction `create_entity_with_engagement()`, `handle_new_user()` amendée (v20).
- **Dépendances :** aucune structurellement (bâtit sur `Entity`, KEEP du Blueprint), mais logiquement fondatrice au même rang que Financial Evidence.
- **Capacités qui en dépendent :** Recommendation Engine, Monthly Review Engine, Attention Score.
- **Source :** ADR-002, Blueprint T2. Validée en conditions réelles : Integration Gate 1 (2026-08-03).

### Capability 3 — Exception & Reconciliation
**État : FOUNDATION**

- **Pourquoi elle existe :** la Constitution (Article IV) nomme « l'exception » comme objet permanent, distinct de la recommandation : « un écart ou une incohérence identifiée entre des faits, dont la nature n'est pas encore déterminée et qui appelle une investigation avant toute conclusion ». L'Ideal Domain Model la classe **Core**, au même rang que Evidence et Attention : « c'est le travail réel du Human Middle — la partie qui ne s'automatise jamais complètement et qui consomme le plus de temps ».
- **Problème utilisateur résolu :** aujourd'hui, un écart détecté dans les chiffres se traduit directement en un texte de recommandation générée par le LLM (`DecisionKernel.Finding`, éphémère, jamais persisté) — il n'existe aucune trace structurée de « ceci est une anomalie non résolue » distincte de « voici ce que je recommande de faire ». Un écart mal compris aujourd'hui ne peut pas être suivi, réassigné, ni distingué d'un écart déjà investigué.
- **Ce qu'elle apporte au conseiller financier :** une file de travail structurée des anomalies à investiguer, séparée de la file des décisions déjà mûres à proposer au client — exactement la distinction entre « je dois comprendre » et « je dois recommander ».
- **Concepts du domaine mobilisés :** `Exception`, `InvestigationNote`, `ResolutionAction`, `ExceptionSeverity`, `ExceptionCategory` (Ideal Model E.4, Core).
- **Agrégats concernés (réel) :** aucun aujourd'hui. Le concept le plus proche, `DecisionKernel.Finding` (`models/decision_kernel.py`), est une structure recalculée à chaque analyse, jamais persistée, sans cycle de vie ni identité stable (Current Domain Model, Agrégat 2).
- **Dépendances :** Financial Evidence (une Exception se détecte à partir de Facts contradictoires ou incomplets).
- **Capacités qui en dépendent :** Recommendation Engine (une recommandation peut répondre à une ou plusieurs Exceptions, Ideal Model D).
- **Source :** Constitution Article IV ; Ideal Model E.4. Aucun ADR ni phase Blueprint dédiée à ce jour — **écart identifié par ce document**.

### Capability 4 — Recommendation Engine
**État : FOUNDATION**

- **Pourquoi elle existe :** la Constitution (Article VI) : « une recommandation n'est pas un texte. C'est une unité de jugement professionnel, dont l'identité subsiste dans le temps et dont le devenir est suivi. » L'Ideal Domain Model (section G) désigne `Recommendation` comme l'unique objet du domaine à boucle fermée avec la réalité — l'actif le plus difficile à répliquer par un concurrent.
- **Problème utilisateur résolu :** aujourd'hui, une recommandation n'a pas d'identité stable au sens strict : son texte est régénéré à chaque analyse (EDM), son suivi vit dans `decision_feedback`, son cycle de vie dans `DecisionArc` — trois objets pour une seule idée (Blueprint C.5).
- **Ce qu'elle apporte au conseiller financier :** une trace unique et durable de chaque jugement proposé — de la proposition initiale jusqu'à la confrontation avec ce qui s'est réellement passé — au lieu de trois fragments disjoints à recouper manuellement.
- **Concepts du domaine mobilisés :** `Recommendation`, `ExpectedImpact`, `ActualOutcome`, `Learning`, cycle `proposed → discussed → (accepted|rejected|deferred) → executed → outcome_observed → closed` (Ideal Model E.6, Core).
- **Agrégats concernés (réel) :** `DecisionArc` (agrégat réel, fonctionnel, `decision_arcs`/`arc_analysis_links`, migration v16), `DecisionFeedback` (`decision_feedback`, v7/v17), `recommendation_id` (déjà déterministe — `sha1(report_id:source:index)`, `decision_memory_service.py`).
- **Dépendances :** Financial Evidence (citer sa `Provenance`), Engagement Lifecycle (scoping), Exception & Reconciliation (répondre à une Exception).
- **Capacités qui en dépendent :** Monthly Review Engine (un Deliverable ne lit que des Recommendations closes), Attention Score (historique de fiabilité), Learning Loop (en est le prolongement direct).
- **Source :** Blueprint T3 (« Fusionner en `Recommendation` unifiée »). Aucun ADR dédié à ce jour.

### Capability 5 — Monthly Review Engine
**État : READY**

- **Pourquoi elle existe :** la Constitution (Article VIII) : « un livrable... restitue, à un moment donné et pour une audience donnée, ce que les faits et le jugement ont déjà établi ailleurs ». L'Ideal Domain Model (workflow F, étape 1) : le système est déclenché par « l'ouverture d'une nouvelle période comptable sur une relation client active — un événement récurrent, prévisible, porté par le calendrier, pas par l'initiative manuelle d'un utilisateur ».
- **Problème utilisateur résolu :** aujourd'hui, un rapport n'existe que si un utilisateur upload manuellement un fichier (Current Domain Model, section A) — aucune notion de « revue mensuelle » planifiée n'existe dans le code (section I : « Monthly Review — absent du code »).
- **Ce qu'elle apporte au conseiller financier :** un cycle de restitution qui suit le rythme contractuel réel de sa relation client (`ReviewCadence`), plutôt qu'un outil qu'il doit se souvenir d'utiliser.
- **Concepts du domaine mobilisés :** `Deliverable`, `DeliverableType`, `ApprovalStatus` (Ideal Model E.7, Supporting mais à discipline Core — « aucun recalcul, aucune extrapolation »).
- **Agrégats concernés (réel) :** le champ `engagements.cadence` existe déjà (T2A) mais rien ne le consomme (T2 Completion Report §6). Les 3 renderers actuels (PDF/PPTX/Excel) sont matures et testés, mais lisent encore `ExecutiveDecisionModel`, pas un futur agrégat `Deliverable`.
- **Dépendances strictes (modèle cible) :** Financial Evidence, Engagement Lifecycle (pour la cadence), Recommendation Engine (un Deliverable cible ne lit que des Recommendations closes, Ideal Model E.7).
- **Nuance justifiant l'état READY malgré la dépendance à Recommendation Engine (FOUNDATION) :** une première version peut être construite en lisant uniquement `EvidenceLedger` (déjà DONE) sans attendre la fusion complète de Recommendation — c'est une réduction de périmètre assumée, pas une violation de la dépendance cible ; voir `CAPABILITY_TRANSITION_REPORT.md`.
- **Capacités qui en dépendent :** aucune.
- **Source :** Blueprint T5 (recâblage EDM) et workflow Ideal Model F.9 ; aucun ADR dédié à ce jour.

### Capability 6 — Attention Score
**État : FOUNDATION**

- **Pourquoi elle existe :** l'Ideal Domain Model (section B) la classe **Core — « c'est la contrainte réelle du métier (temps fini, clients multiples). Aucun logiciel générique ne le résout. »** La Constitution (Article VII) : « la valeur de Pepperyn ne se mesure jamais au volume d'information qu'il traite, mais à sa capacité à indiquer correctement... où l'attention du professionnel vaut le plus, maintenant. »
- **Problème utilisateur résolu :** un CFO gérant 15 à 50 mandats ne peut pas parcourir chaque client un par un pour décider où porter son attention — c'est précisément l'absence structurelle constatée par le Current Domain Model (section I : « Portfolio — absent »).
- **Ce qu'elle apporte au conseiller financier :** la réponse continue à « où dois-je regarder maintenant, et pourquoi », au lieu de choisir un client au hasard ou par habitude.
- **Concepts du domaine mobilisés :** `AttentionSignal`, `AttentionScore`, `AttentionReason` (Ideal Model E.5, Core — « le cœur différenciant »).
- **Agrégats concernés (réel) :** aucun. Signalé explicitement par le Blueprint (C.6) comme « la seule vraie création » du plan entier — rien à réveiller, rien à relier.
- **Dépendances :** Financial Evidence (matérialité des écarts), Engagement Lifecycle (ancienneté de revue, cadence), Recommendation Engine (historique de fiabilité) — Blueprint C.6, explicite : placée en phase T4, après que ces trois fondations soient posées, « jamais avant ».
- **Capacités qui en dépendent :** Portfolio Intelligence (agrégation multi-Engagements), Learning Loop (le score se repondère avec l'apprentissage).
- **Source :** Blueprint T4 ; aucun ADR dédié à ce jour.

### Capability 7 — Portfolio Intelligence
**État : FOUNDATION**

- **Pourquoi elle existe :** l'Ideal Domain Model (workflow F, étape 6) : « le CFO ne parcourt jamais client par client — il ouvre son portefeuille trié par attention... à travers tous ses clients », et section B (Portfolio Benchmarking, Supporting) : comparaison anonymisée entre Engagements similaires.
- **Problème utilisateur résolu :** même une fois l'Attention Score disponible par Engagement, rien n'agrège aujourd'hui une vue portefeuille globale ni ne permet de comparer un client à des pairs anonymisés (Current Domain Model, section I : « Portfolio — absent »).
- **Ce qu'elle apporte au conseiller financier :** une vue transversale de l'ensemble de son portefeuille (pas juste d'un client), et un point de comparaison sectoriel pour qualifier un écart (« est-ce normal pour ce secteur, ou spécifique à ce client »).
- **Concepts du domaine mobilisés :** vue agrégée d'`AttentionSignal` à travers les Engagements ; `BenchmarkCohort`, `AnonymizedMetric`, `PercentileRank` (Ideal Model E.8, Supporting).
- **Agrégats concernés (réel) :** aucun.
- **Dépendances :** Attention Score (rien à agréger au niveau portefeuille tant que le signal n'existe pas au niveau d'un Engagement).
- **Capacités qui en dépendent :** aucune.
- **Source :** Ideal Model E.8 ; pas de phase Blueprint dédiée (extension au-delà de T4).

### Capability 8 — Learning Loop
**État : FOUNDATION**

- **Pourquoi elle existe :** Constitution, Axiome 9 : « une recommandation qui n'apprend jamais de son résultat n'est qu'une opinion répétée. » Article V : « c'est de cette confrontation à la conséquence réelle... que le domaine apprend. »
- **Problème utilisateur résolu :** aujourd'hui, rien ne mesure systématiquement si une recommandation exécutée a effectivement produit l'effet attendu, ni ne fait remonter cet écart pour améliorer la priorisation future — le `DecisionArc` actuel porte des états `consequences_linked`/`learning_proposed` mais sans rebouclage formel vers un score de priorisation (qui n'existe pas encore, Capability 6).
- **Ce qu'elle apporte au conseiller financier :** la preuve, dans le temps, que ses recommandations passées ont (ou non) porté leurs fruits — l'argument commercial le plus difficile à répliquer par un concurrent qui démarre à zéro (Ideal Model, section G).
- **Concepts du domaine mobilisés :** `ActualOutcome`, `Learning` (Ideal Model E.6, prolongement de `Recommendation`).
- **Agrégats concernés (réel) :** fragment réel existant : les états `consequences_linked` et `learning_proposed` du cycle de vie de `DecisionArc` (Current Domain Model, Agrégat 1) — la mécanique de détection de conséquence existe déjà (`arc_service.py`), mais rien ne la reboucle vers une priorisation.
- **Dépendances :** Recommendation Engine (il faut des recommandations exécutées, identifiables dans le temps, avant de pouvoir mesurer leur résultat).
- **Capacités qui en dépendent :** Attention Score (le Learning repondère l'urgence relative d'un Engagement, Ideal Model workflow F.10).
- **Source :** Constitution Article V/VI, Ideal Model E.6 ; pas de phase Blueprint dédiée (extension de T3).

---

## 3. Documents liés

- `CAPABILITY_DEPENDENCY_MAP.md` — carte de dépendances et chemin critique (Missions 5-6).
- `MVP_CAPABILITY_SET.md` — plus petit ensemble vendable (Mission 7).
- `CAPABILITY_MATURITY_MATRIX.md` — couverture réelle, dette, risques (Mission 8).
- `CAPABILITY_TRANSITION_REPORT.md` — comparaison code existant / capacité réelle, conclusion (Missions 9-10).

---

**CAPABILITY ROADMAP v1 — LISTE ET DÉTAIL PRODUITS.**
