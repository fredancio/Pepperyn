# CAPABILITY MATURITY MATRIX — Current Product Coverage

**Date :** 2026-08-03
**Type :** document de référence (Niveau B), dérivé de `CAPABILITY_ROADMAP_v1.md`.
**Consigne appliquée :** ne pas surestimer l'avancement. Les pourcentages sont des estimations qualitatives, argumentées ligne par ligne à partir des documents sources — pas une mesure instrumentée. Ils sont volontairement prudents.

---

## Tableau

| Capacité | Couverture du modèle cible | Maturité | Dette restante principale | Risques principaux |
|---|---|---|---|---|
| **1. Financial Evidence** | **~70 %** | Production (architecturalement complète pour son périmètre T1, validée en conditions réelles) | `EvidenceLedger` reste granularité « un par Analysis », pas encore « un par Engagement × période » (cible Ideal Model E.3) ; `Materiality` n'est pas un Value Object dédié (juste des champs numériques nus) ; question ouverte ADR-001 n°2 (définition de la clôture de période) toujours non tranchée — l'immutabilité reste donc inconditionnelle plutôt que « à la clôture » | Le non-blocage de la persistance (invariant clé) reste vérifié statiquement, jamais en conditions d'exécution réelle bout-en-bout (Integration Gate 1, section L) |
| **2. Engagement Lifecycle** | **~35 %** | Fondation posée, invisible pour l'utilisateur | `StakeholderContact`, `ScopeDefinition` (entités cible) n'existent pas ; `RetainerTerms` n'existe pas ; le cycle de vie réel (`prospected→active→paused↔active→churned`) n'a aucune transition câblée — seul le statut initial (`prospect`/`active` déterminé par un backfill) existe ; `cadence` est un champ mort, rien ne le consomme | Risque de divergence déjà identifié en T2 : un futur 3e chemin de création d'Entity qui oublierait `EngagementService` — non garanti structurellement, seulement détectable (`COUNT(entities)=COUNT(engagements)`, non câblé en alerte) |
| **3. Exception & Reconciliation** | **~5 %** | Aucune brique — concept le plus proche est éphémère | Aucun agrégat `Exception`, aucune persistance, aucun cycle de vie `raised→investigating→resolved/escalated/dismissed`. Le seul fragment existant (`DecisionKernel.Finding`) est recalculé à chaque analyse et jamais conservé | Capacité absente des priorités précédemment communiquées (T1-T2) malgré son statut Core dans l'Ideal Model et sa mention explicite en Constitution — risque de rester invisible dans le pilotage si elle n'est pas nommée explicitement (raison de son ajout à ce document) |
| **4. Recommendation Engine** | **~40 %** | Fragments réels, fonctionnels, mais non unifiés | `DecisionArc` + `DecisionFeedback` fonctionnent et sont testés, mais restent 2 objets distincts (+ le texte régénéré dans EDM) plutôt qu'un agrégat `Recommendation` unique ; aucune citation formelle de `Provenance` depuis `EvidenceLedger` ; pas de mécanisme `supersedes` pour l'évolution du texte d'une recommandation | La fusion (Blueprint T3) touche 3 tables historiques (`decision_feedback`, `decision_arcs`, `arc_analysis_links`) — risque de perte de nuance si la migration de données n'est pas menée avec la même rigueur que T1/T2 |
| **5. Monthly Review Engine** | **~15 %** | Aucun agrégat cible ; forte valeur legacy adjacente | Aucun agrégat `Deliverable`, aucun déclenchement calendaire par `Cadence` (le champ existe, rien ne le lit) ; les renderers actuels lisent encore `ExecutiveDecisionModel`, pas un futur `Deliverable`. **Nuance :** les 3 exports actuels (PDF/PPTX/Excel) sont matures et testés (946+/954+ tests en Phase 1B) — la couverture du modèle *cible* est faible, la valeur métier *actuelle* du chemin legacy ne l'est pas | Le recâblage d'EDM en projection (Blueprint T5) est explicitement signalé comme « le point le plus délicat » du plan entier — seul endroit où une régression serait immédiatement visible par un client |
| **6. Attention Score** | **0 %** | Aucune brique | Tout reste à construire : `AttentionSignal`, `AttentionScore`, `AttentionReason` | Blueprint C.6 : synthétisable à 90 % depuis des données déjà produites une fois T3 en place — risque principal est de la construire prématurément, avant que la matière première (Recommendation Engine, Learning Loop) soit fiable, produisant un score non explicable (violerait l'invariant H.5 de l'Ideal Model) |
| **7. Portfolio Intelligence** | **0 %** | Aucune brique | Rien n'agrège une vue portefeuille ; `BenchmarkCohort` n'existe pas | Dépend entièrement d'Attention Score — tout risque de construction prématurée s'y transmet directement |
| **8. Learning Loop** | **~20 %** | Fragment structurel existant, jamais rebouclé | Les états `consequences_linked`/`learning_proposed` existent déjà dans le cycle de vie de `DecisionArc` — la détection de conséquence fonctionne (`arc_service.py`) — mais rien ne transforme ce signal en pondération d'un score de priorisation (qui n'existe pas encore) | Risque de sous-estimer cette capacité parce que sa brique existante est enfouie dans `DecisionArc` plutôt que nommée explicitement comme `Learning` — à surveiller pour ne pas la reconstruire de zéro par méconnaissance de l'existant |

---

## Notes de méthode (transparence sur les pourcentages)

- Les pourcentages mesurent la **couverture du modèle cible tel que défini par l'Ideal Domain Model**, pas la quantité de code écrite ni la valeur commerciale actuelle — une capacité peut avoir une forte valeur commerciale legacy (Monthly Review Engine) tout en ayant une faible couverture architecturale cible, et inversement.
- Aucun pourcentage n'a été calculé par instrumentation (pas de couverture de test, pas de comptage de lignes) — ils sont dérivés d'une lecture qualitative des sources citées dans `CAPABILITY_ROADMAP_v1.md`. Ils doivent être traités comme des ordres de grandeur, pas comme une métrique d'ingénierie.
- Les deux capacités DONE (Financial Evidence, Engagement Lifecycle) ne sont pas à 100 % de couverture du modèle cible — leur statut DONE porte sur le périmètre exact que T1/T2 s'étaient fixé (ADR-001/001A, ADR-002), validé en conditions réelles (Integration Gate 1), pas sur la totalité de l'ambition de l'Ideal Domain Model. C'est une distinction volontaire : DONE signifie « la tranche prévue est livrée et validée », pas « la vision complète est atteinte ».

---

**CAPABILITY MATURITY MATRIX — COUVERTURE ÉVALUÉE, SANS SURESTIMATION.**
