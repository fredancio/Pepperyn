# Pepperyn Transformation Blueprint — Current Domain → Target Domain
**Date :** 2026-08-02
**Sources :** `PEPPERYN_CURRENT_DOMAIN_MODEL_2026-08-02.md` (modèle réel, déduit du code) × `IDEAL_DOMAIN_MODEL_FRACTIONAL_CFO_2026-08-02.md` (modèle cible, conception greenfield).
**Nature du document :** stratégie de transformation. Aucune ligne de code n'est modifiée par ce document — c'est un plan, pas une exécution.

---

## A. Résumé exécutif

L'écart entre le modèle actuel et le modèle cible n'est pas un écart de qualité de code — le code de Pepperyn est, par endroits, plus rigoureux que ce que la plupart des produits early-stage produisent (`financial_truth.py` en est la preuve). L'écart est un **écart de forme du domaine** : Pepperyn pense en événements isolés (« une analyse »), le modèle cible pense en relation continue arbitrée par l'attention (« un portefeuille d'Engagements »).

La bonne nouvelle, et c'est le fait le plus important de ce document : **une bonne partie de la matière première du modèle cible existe déjà dans le code actuel, mais soit dormante (jamais persistée), soit éparpillée en fragments non reliés entre eux.** La transformation n'est donc pas une reconstruction — c'est, pour l'essentiel, un travail de **réveil, de reliure et de recentrage**, pas de réécriture. Trois exceptions notables demandent un travail réellement nouveau : la couche `Engagement` (relation continue), la couche `AttentionScore` (priorisation transversale) et la fusion des fragments de mémoire décisionnelle en un agrégat `Recommendation` unique à boucle fermée.

Le point le plus dangereux du plan est unique et bien identifié : `ExecutiveDecisionModel`, aujourd'hui l'objet central lu à l'identique par les 3 exports (PDF/PPTX/Excel), doit changer de source sans jamais changer de forme de sortie. C'est le seul endroit où une erreur serait visible immédiatement par un client. Tout le reste du plan est construit pour que cette étape arrive en dernier, une fois que le reste est stable.

---

## B. Table de correspondance et décisions

Convention des colonnes : **Effort** et **Risque** sur une échelle Faible / Moyen / Élevé. **Compat. ascendante** = la mesure dans laquelle la transformation peut se faire sans casser le produit existant pendant qu'elle est en cours.

| # | Objet actuel | Équivalent cible | Décision | Effort | Risque | Compat. ascendante |
|---|---|---|---|---|---|---|
| 1 | `Company` + `Workspace` | *(pas d'équivalent direct — reste structure de compte/accès)* | **KEEP** | Faible | Faible | Totale |
| 2 | `Entity` (+ champ `relation_type`) | `Engagement` | **EVOLVE** | Moyen | Faible | Totale (additif) |
| 3 | `AnalysisResult` (blob versionné V3→V12) | `EvidenceLedger` (partiel) + contenu de `Deliverable` (partiel) | **SPLIT** | Élevé | Élevé | Moyenne |
| 4 | Evidence Graph (JSON éphémère, jamais persisté) | `EvidenceLedger` / `FinancialFact` | **EVOLVE** | Moyen | Faible | Totale (additif) |
| 5 | `QuantifiedImpact` / `EconomicEvent` (`financial_truth.py`, dormant) | `FinancialFact` / `Provenance` / `Materiality` | **EVOLVE** | Moyen | Faible | Totale |
| 6 | `DecisionKernel` (`Finding`/`Recommendation`/`Decision`) | `Exception` + `Recommendation` (partiel) | **ADAPT** | Moyen | Faible | Élevée |
| 7 | `ExecutiveDecisionModel` (EDM) | `Recommendation` (contenu) + `Deliverable` (projection) | **SPLIT** | Élevé | **Élevé** | Moyenne (via strangler fig) |
| 8 | `DecisionFeedback` + `DecisionArc` + `ArcAnalysisLink` | `Recommendation` (agrégat unifié à boucle fermée) | **MERGE** | Élevé | Moyen-Élevé | Moyenne |
| 9 | `memory_service` (`financial_metrics`, `company_profile`) | Historique dans `EvidenceLedger` + intrant d'`AttentionSignal` | **EVOLVE** | Moyen | Faible | Totale |
| 10 | *(aucun objet actuel)* | `AttentionSignal` / `AttentionScore` | **hors des 7 catégories — création pure**, mais synthétisable à 90% depuis des données déjà calculées (matérialité, historique de recommandations, ancienneté de revue) | Élevé | Moyen | Additif pur |
| 11 | Renderers `export_pdf_service.py` / `export_pptx_service.py` / `excel_export.py` | Moteur de génération de `Deliverable` | **ADAPT** | Moyen | Faible *(si strangler fig respecté)* | Totale si bien séquencé |
| 12 | `ExecutiveCaseJSON` (V1, `models/executive_case.py`) | Redondant avec EDM/Deliverable | **DELETE** *(sous réserve de vérification d'usage réel — voir §D.3)* | Faible | Faible | N/A |
| 13 | `ExecutiveCase` V2 / `ConversationEngine` (Chat uniquement) | Read-model unique consommé par le Chat | **MERGE** dans le futur read-model de `Deliverable`/`Recommendation` | Faible-Moyen | Faible | Élevée |
| 14 | `backend/epm/` (orphelin, hors Git) | Extracteur de `FinancialFact` (si adopté) | **EVOLVE** *(si adopté)* **ou DELETE** *(si abandonné — décision Fred déjà posée en Phase 1C)* | Faible (delete) / Moyen (adopt) | Faible | N/A |
| 15 | `usage_limits`/`usage_logs`, Stripe | Time & Billing (Generic) | **KEEP** | Faible | Faible | Totale |
| 16 | `crm_service.py` (sync Airtable) | Périphérique Generic | **KEEP** | Faible | Faible | Totale |
| 17 | `rate_limiter.py`, `anonymization_service.py`, `data_quality_gate.py` | Infrastructure transverse, hors du domaine métier | **KEEP** | Faible | Faible | Totale |
| 18 | `conversation_engine.py` | Client Communication (Generic), recâblé sur le nouveau read-model | **ADAPT** | Faible-Moyen | Faible | Élevée |

---

## C. Ce que ces décisions veulent dire, objet par objet critique

### C.1 — `Entity.relation_type` → `Engagement` (EVOLVE)
Le champ `relation_type = "client" | "filiale" | None` porte aujourd'hui, seul, tout le poids conceptuel de la relation cliente. C'est un champ d'énumération sur un objet technique, pas une relation avec cadence, scope et statut. La transformation consiste à faire naître un agrégat `Engagement` qui **enveloppe** une `Entity` existante — sans supprimer `Entity`, sans casser la hiérarchie `Company → Workspace → Entity` déjà bien contrainte en SQL. C'est un ajout, pas un remplacement : chaque `Entity` existante reçoit un `Engagement` par défaut créé automatiquement (cadence mensuelle, scope = l'entité elle-même), invisible pour l'utilisateur jusqu'à ce que l'interface en ait besoin.

### C.2 — `AnalysisResult` → `EvidenceLedger` + `Deliverable` (SPLIT)
C'est l'objet le plus lourd du modèle actuel (un seul blob portant simultanément des champs V3, V6, V9, V10, V11, V12 tous actifs — Phase 1D, section M). Il porte deux responsabilités que le modèle cible sépare strictement : les *faits* (ce qui est vrai, sourcé) et le *narratif restitué* (ce qui est présenté). Le séparer en deux flux distincts est un travail de fond, mais il n'exige pas de tout refaire d'un coup : le split peut commencer par **cesser d'écrire de nouveaux champs dans le blob** et les faire naître directement dans les nouveaux objets, pendant que le blob existant continue d'être lu tel quel par le reste du pipeline. Le blob s'assèche progressivement plutôt que d'être supprimé d'un coup.

### C.3 — Evidence Graph & `financial_truth.py` → `EvidenceLedger` (EVOLVE, priorité la plus haute)
**C'est le point de levier le plus favorable de tout ce plan.** Deux constats du modèle actuel, mis côte à côte, forment une opportunité rare :
- L'Evidence Graph est déjà généré à *chaque* analyse (RÈGLE ABSOLUE N°6) — l'inventaire de faits sourcés existe donc déjà en mémoire à chaque exécution du pipeline. Il est simplement jeté après usage.
- `financial_truth.py` (`QuantifiedImpact`, `SourceReference`, `Materiality`-like `GrossMarginResolution`) est déjà quasiment le schéma cible du modèle idéal — invariants inclus (« absence de donnée ≠ zéro », hiérarchie de provenance). Il est simplement non branché.

Activer cette couche ne demande donc pas de concevoir un nouveau modèle de données : il demande de **persister ce qui existe déjà** et de **brancher un type déjà écrit**. C'est, à effort égal, le gain de maturité de domaine le plus élevé du plan entier.

### C.4 — `ExecutiveDecisionModel` → `Recommendation` + `Deliverable` (SPLIT, le point le plus délicat)
EDM joue aujourd'hui deux rôles à la fois : il *contient* le jugement (quelle décision, quel impact, quelle priorité) et il *est* la structure lue à l'identique par les 3 exports. Séparer ces deux rôles est nécessaire pour atteindre le modèle cible, mais c'est aussi l'endroit où une régression serait immédiatement visible par un client (un PDF différent d'hier). La méthode retenue : **strangler fig strict**. EDM garde exactement sa forme externe (mêmes champs, mêmes exports) ; seule sa fonction de construction interne change progressivement de source, d'abord en lisant encore `AnalysisResult`, puis en lisant les nouveaux agrégats une fois qu'ils existent et sont validés indépendamment. À aucun moment les 3 renderers ne doivent être modifiés avant que la nouvelle source de données ne produise des résultats byte-identiques à l'ancienne sur un corpus de test de non-régression.

### C.5 — `DecisionFeedback` + `DecisionArc` + contenu d'`ExecutiveDecision` → `Recommendation` unifiée (MERGE)
Aujourd'hui, une recommandation n'a pas d'identité stable : son texte est régénéré à chaque analyse (dans EDM), son suivi de statut vit dans `decision_feedback`, et son cycle de vie (intention→décision→exécution→conséquences→apprentissage) vit dans `DecisionArc` — trois objets, une seule idée. Bonne nouvelle : `recommendation_id` est déjà calculé de façon déterministe (`sha1(report_id:source:index)`, `decision_memory_service.py`) — c'est exactement la clé de fusion dont un agrégat unifié a besoin. La fusion consiste à faire de cette clé l'identité d'un agrégat `Recommendation` réel, qui absorbe les trois fragments actuels sans perdre de données historiques (migration directe possible, pas de reconstruction).

### C.6 — `AttentionScore` : la seule vraie création
Rien dans le modèle actuel ne répond à « où dois-je regarder maintenant, à travers tous mes clients ». C'est le seul manque du plan qui n'est pas une histoire de « réveiller » ou de « relier » de la matière existante — c'est une capacité neuve. Elle reste cependant **synthétisable en grande partie depuis des données déjà produites** une fois les étapes C.3 et C.5 en place : matérialité des écarts (déjà calculée dans `financial_truth.py`), ancienneté de la dernière revue (déjà en base via `analyses.created_at`), historique de fiabilité des recommandations passées (nouvellement disponible via C.5). C'est pour cela qu'`AttentionScore` est placé en phase T4 du plan de migration (§E), après que sa matière première soit disponible — jamais avant.

---

## D. Dettes de modélisation héritées — comment ce plan les résout

Rappel des 7 dettes identifiées en Phase 1D (section M) et leur devenir dans ce plan :

1. **5-6 représentations parallèles du « résultat d'analyse »** → résolu par C.2 (split) + C.4 (split EDM) + suppression de V1/V2 redondants (§D.3) : à terme, une seule chaîne `EvidenceLedger → Recommendation → Deliverable`, plus de représentations concurrentes.
2. **Docstring d'EDM contredisant le code réel** → disparaît naturellement quand EDM devient explicitement un objet de projection documenté comme tel (C.4), plutôt qu'un objet dont le rôle réel diverge de sa description.
3. **`DashboardCard` / `KPICard` dupliqués** → à consolider en un seul Value Object au moment du split EDM (C.4), effort marginal une fois cette étape entamée.
4. **`Entity.relation_type` porte seul le poids de « client externe »** → résolu par C.1.
5. **`BusinessContext` placeholder jamais branché** → candidat naturel à devenir un attribut de `Engagement.ScopeDefinition` (C.1) plutôt qu'un champ orphelin d'EDM.
6. **Mémoire scindée sans vue unifiée** (`memory_service` vs `decision_memory_service`) → résolu par la fusion C.5 + l'usage de `memory_service` comme intrant d'`AttentionScore` (C.6) : les deux mémoires convergent vers un seul objet qui raconte l'histoire complète d'un Engagement.
7. **`AnalysisResult` empilé V3→V12 sans dépréciation** → s'assèche progressivement via C.2, sans big-bang.

### D.3 — Vérification requise avant suppression (`ExecutiveCaseJSON` V1)
La Phase 1D n'a confirmé avec certitude que l'usage de `build_executive_decision_model()` dans les 3 renderers (import ET appel effectif tracés). L'import d'`ExecutiveCaseJSON` (V1) a été confirmé dans les 3 fichiers, mais son **usage réel dans le corps des fonctions** n'a pas été retracé ligne à ligne à ce stade. Avant toute suppression, une vérification ciblée (grep + lecture des fonctions `generate_pdf_report`, `generate_pptx_report`, `generate_excel_report`) doit confirmer si `ExecutiveCaseJSON` est réellement instancié/lu, ou seulement importé de façon vestigiale. Ce point doit être tranché en phase T0, avant tout le reste — c'est un simple contrôle de lecture, aucune modification requise pour l'effectuer.

---

## E. Stratégie de migration incrémentale

Principe directeur : **chaque phase se termine avec un produit strictement fonctionnel, testable, livrable.** Aucune phase ne casse ce qui existe ; chaque phase active une capacité en plus ou assèche une source de dette, jamais les deux à contre-temps.

### Phase T0 — Vérifications et nettoyage sans risque (prérequis)
- Vérifier l'usage réel d'`ExecutiveCaseJSON` V1 (§D.3).
- Corriger la docstring d'EDM pour refléter la réalité (les renderers la lisent déjà) — changement de commentaire, zéro risque fonctionnel.
- Trancher les décisions humaines déjà posées en Phase 1C (sort d'EPM, sous-projets redondants) — condition d'un dépôt propre avant de bâtir dessus.
- **Produit à la fin de T0 :** strictement identique à aujourd'hui, mais avec un terrain vérifié.

### Phase T1 — Activer la couche de preuve dormante (`EvidenceLedger`)
- Persister l'Evidence Graph déjà généré à chaque analyse (aujourd'hui jeté) dans une nouvelle table, en parallèle du pipeline actuel.
- Brancher `QuantifiedImpact`/`EconomicEvent` (déjà écrits, déjà validés par leurs propres invariants) à cette persistance.
- Aucune route existante, aucun export existant n'est touché.
- **Produit à la fin de T1 :** identique pour l'utilisateur ; le système sait désormais *conserver* ce qu'il savait déjà *calculer*.

### Phase T2 — Introduire `Engagement` en enveloppe additive
- Créer l'agrégat `Engagement`, un par `Entity` existante, généré automatiquement (cadence par défaut = mensuelle, scope = l'entité).
- Aucune interface utilisateur ne change encore ; c'est une fondation invisible.
- **Produit à la fin de T2 :** identique pour l'utilisateur ; le système sait désormais qui est engagé dans une relation continue, pas seulement qui a uploadé un fichier.

### Phase T3 — Fusionner en `Recommendation` unifiée
- Migrer `decision_feedback` + `decision_arcs` + `arc_analysis_links` vers un agrégat `Recommendation` unique, en s'appuyant sur `recommendation_id` (déjà déterministe) comme clé de fusion — migration de données directe, pas de reconstruction.
- Les routes existantes (`/api/decision-feedback`, `/api/arcs/*`) continuent de fonctionner, adossées au nouvel agrégat en interne.
- **Produit à la fin de T3 :** identique en surface pour l'utilisateur ; chaque recommandation a désormais une identité stable et une boucle fermée exploitable.

### Phase T4 — `AttentionScore` (première capacité visible du modèle cible)
- Construit à partir de T1 (matérialité) + T2 (cadence contractuelle) + T3 (historique de recommandations).
- Livrable comme fonctionnalité additive (nouvelle vue portefeuille), sans toucher aux exports PDF/PPTX/Excel existants.
- **Produit à la fin de T4 :** premier gain visible pour un CFO multi-clients — une vue de portefeuille priorisée qui n'existait pas avant, en plus de tout ce qui fonctionnait déjà.

### Phase T5 — Recâbler EDM en projection (le point le plus délicat, volontairement en dernier)
- `ExecutiveDecisionModel` cesse de reconstruire son contenu depuis `AnalysisResult` brut et le reconstruit à la place depuis `EvidenceLedger` (T1) + `Recommendation` (T3), en conservant une forme de sortie strictement identique.
- Validation par comparaison byte-à-byte des 3 exports sur un corpus de régression avant toute bascule en production.
- **Produit à la fin de T5 :** identique en sortie pour l'utilisateur (aucun changement visible), mais la dette centrale (EDM à double rôle) est résorbée en interne.

### Phase T6 — Nettoyage final des représentations parallèles
- Suppression d'`ExecutiveCaseJSON` V1 (si T0 confirme qu'il est mort) et fusion d'`ExecutiveCase` V2 dans le read-model unique consommé par le Chat.
- Décision finale sur EPM (adoption dans la couche Evidence ou suppression).
- **Produit à la fin de T6 :** le modèle cible du document `IDEAL_DOMAIN_MODEL` est atteint pour son cœur (Evidence, Recommendation, Engagement, Attention), sans jamais être passé par un état de rupture.

---

## F. Migration Map — le chemin le plus court

```
                     ┌───────────────────────────────────────────┐
                     │  T0 — Vérifications & nettoyage sans risque │
                     │  (usage EDM/ExecutiveCaseJSON, décisions     │
                     │   humaines déjà posées en Phase 1C)           │
                     └───────────────────────┬───────────────────┘
                                              │
                     ┌────────────────────────▼───────────────────┐
                     │  T1 — EvidenceLedger (activer Evidence Graph  │
                     │  + financial_truth.py, déjà écrits, dormants) │
                     └────────────┬──────────────────┬─────────────┘
                                  │                    │
                     ┌────────────▼──────────┐   ┌─────▼──────────────────┐
                     │  T2 — Engagement         │   │  T3 — Recommendation    │
                     │  (enveloppe additive       │   │  unifiée (fusion des     │
                     │   sur Entity existante)     │   │  3 fragments actuels)    │
                     └────────────┬──────────┘   └─────┬──────────────────┘
                                  │                    │
                                  └──────────┬─────────┘
                                             ▼
                     ┌───────────────────────────────────────────┐
                     │  T4 — AttentionScore                         │
                     │  (première capacité visible du modèle cible, │
                     │   construite sur T1+T2+T3)                   │
                     └───────────────────────┬───────────────────┘
                                              ▼
                     ┌───────────────────────────────────────────┐
                     │  T5 — EDM recâblé en projection               │
                     │  (strangler fig, validation byte-à-byte,      │
                     │   point de risque le plus élevé du plan)      │
                     └───────────────────────┬───────────────────┘
                                              ▼
                     ┌───────────────────────────────────────────┐
                     │  T6 — Nettoyage final                         │
                     │  (suppression V1/V2 redondants, verdict EPM)  │
                     └───────────────────────┬───────────────────┘
                                              ▼
                         ═══════════ MODÈLE CIBLE ATTEINT ═══════════
```

**Pourquoi ce chemin est le plus court :** T1 et T2 sont indépendants et peuvent être menés en parallèle (aucune dépendance mutuelle) — c'est le seul point de parallélisation du plan. T3 dépend uniquement de l'existant (`recommendation_id` déjà là), pas de T1/T2, et peut donc démarrer en même temps qu'eux. T4 est le premier point de convergence obligatoire — c'est la première fois que le plan *doit* attendre que plusieurs fondations soient posées. T5 est délibérément le dernier point à haut risque : tout ce qui peut être validé indépendamment (T1-T4) l'est avant de toucher à l'objet le plus exposé au client. T6 est un nettoyage, jamais un prérequis fonctionnel — il peut même être repoussé indéfiniment sans bloquer la valeur métier des phases précédentes.

---

## G. Ce qui ne doit surtout pas bouger

Pour équilibrer un document qui liste beaucoup de transformations, il est tout aussi important d'être explicite sur ce qui est déjà bien construit et qui doit rester intact :

- La hiérarchie `Company → Workspace → Entity` (contraintes SQL strictes, triggers atomiques à l'inscription) : solide, ne demande aucune reconstruction.
- Le moteur de rendu lui-même (mise en page PDF/PPTX/Excel) : mature, testé (946/954 tests passants en Phase 1B) — la transformation change *ce qui l'alimente*, jamais *comment il dessine*.
- Les règles déterministes déjà versionnées (`decision_rules.py`, invariants `KERNEL-INV-00x`) : exactement le niveau de rigueur que le modèle cible demande pour son cœur Core — à réutiliser telles quelles, pas à réinventer.
- L'anonymisation systématique avant tout appel LLM : déjà alignée avec l'exigence de confiance du modèle cible, aucun changement nécessaire.
- Billing, CRM, rate limiting : Generic par nature dans les deux modèles — statu quo justifié, pas de dette à ce niveau.

---

## H. Verdict

Ce plan n'est pas une réécriture de Pepperyn — c'est une **révélation progressive d'un modèle plus mature qui existe déjà, à l'état de fragments, dans le code actuel.** Le constat le plus rassurant de cette comparaison est que la pièce la plus difficile à concevoir dans un modèle cible — une couche de preuve financière avec provenance et invariants stricts — a déjà été pensée et écrite par l'équipe (`financial_truth.py`), simplement jamais activée. Le constat le plus exigeant est que l'objet aujourd'hui central (`ExecutiveDecisionModel`) doit changer de rôle sans jamais changer de visage, ce qui demande de la discipline d'exécution (strangler fig, validation byte-à-byte) plus que de l'ingéniosité de conception.

La seule capacité réellement absente du code actuel — l'attention de portefeuille — est aussi, structurellement, celle qui distingue le plus un outil d'analyse ponctuelle d'un véritable système au service d'un CFO externalisé gérant plusieurs mandats. C'est donc, à juste titre, la pièce que ce plan construit en dernier recours technique (elle dépend de tout le reste) mais qu'il faut garder en tête comme **la vraie raison d'être de la transformation** — tout le reste n'est que la fondation qui la rend possible.
