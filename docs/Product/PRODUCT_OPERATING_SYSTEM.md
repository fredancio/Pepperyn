# PRODUCT OPERATING SYSTEM — Pepperyn

**Rôle :** formaliser les règles de fonctionnement de Pepperyn pendant toute la phase d'exécution. Ce document ne décide rien par lui-même — il fixe comment les décisions se prennent.

---

## 0. Pepperyn a une architecture de décision, pas seulement une architecture logicielle

Ce n'est pas une nouvelle couche ajoutée au projet : c'est le nom de ce qui existe déjà et qui vient d'être complété.

| Couche | Rôle | Document |
|---|---|---|
| **Constitution** | Principes immuables — le *pourquoi* | `docs/Architecture/constitution/PEPPERYN_CONSTITUTION_v1.0.md` |
| **ADR** | Décisions d'architecture — le *comment, une fois pour toutes* | `docs/Architecture/adr/` |
| **Product Board** | Pilotage du présent — le *quoi, maintenant* | `docs/Product/PRODUCT_BOARD.md` |
| **Registre Vision** | Protection des idées futures — le *pas maintenant, mais noté* | `docs/Product/VISION_DECISION_WORKSPACE.md` |
| **Parking** | Idées reportées — le *non, et pourquoi* | `PRODUCT_BOARD.md` section 7 |

Chaque couche répond à une question qu'aucune autre ne couvre. C'est ce qui permet à Pepperyn de continuer à évoluer sans perdre la cohérence construite depuis la Constitution — l'objectif n'est pas de produire plus de documents, mais d'éviter qu'une même question soit retranchée à chaque conversation.

---

## 1. Petits incréments

Chaque incrément est le plus petit changement capable d'augmenter une valeur perçue mesurable. Un écran complet n'est construit que si un composant plus simple ne peut pas porter la même valeur commerciale — dans le doute, le composant l'emporte.

## 2. Zéro régression

Aucun incrément ne modifie le comportement d'un chemin déjà en production sans le dire explicitement. Le pattern déjà appliqué (Incrément 1, bandeau qualité) fait référence : ajout additif, chemins existants non touchés, vérifié par des tests de non-régression avant commit.

## 3. Une PR = une valeur métier

Chaque Pull Request porte une seule valeur commerciale identifiable, capable de répondre seule à la question de la section 7. Une PR qui mélange plusieurs valeurs ou plusieurs capacités est découpée avant d'être proposée.

## 4. Tests obligatoires

Aucun incrément n'est considéré terminé sans tests couvrant : le comportement nouveau, et la non-régression du comportement existant qu'il touche. Absence de framework de test n'est pas une excuse — c'est un prérequis à poser avant l'incrément (déjà fait côté frontend à l'Incrément 1).

## 5. Rollback systématique

Chaque incrément est conçu pour être annulable par un simple revert de commit, sans migration destructive ni donnée perdue. Une stratégie de rollback explicite fait partie de tout plan d'implémentation, au même titre que les tests.

## 6. Démontrabilité

Avant d'implémenter, répondre :
- Quelle est la première minute de la démonstration ?
- Quelle est la dernière minute ?
- Comment cet incrément améliore-t-il cette histoire ?

Un incrément qui ne trouve pas sa place dans une histoire de démonstration n'est pas nécessairement inutile — mais il n'est pas prioritaire tant qu'un incrément démontrable existe dans le backlog.

**Définition de "terminé" au niveau Capability :** une Capability n'est considérée comme terminée que lorsqu'un commercial est capable de la montrer naturellement pendant une démonstration — sans script mémorisé, sans détour, sans avoir à expliquer ce qu'on regarderait si la fonctionnalité marchait. Le code qui fonctionne mais qui ne se raconte pas n'est pas fini au sens produit du terme, même s'il est fini au sens technique.

## 7. Valeur commerciale avant richesse fonctionnelle

Règle unique, avant toute PR :
**"Après cette PR, Pepperyn sera-t-il objectivement plus facile à vendre qu'avant ?"**
Si la réponse est non, l'incrément n'est probablement pas prioritaire — même s'il est techniquement intéressant, même s'il enrichit le produit. La priorisation à sept critères (`PRODUCT_BOARD.md` section 8) formalise cette règle sans la remplacer : le score aide à trancher, la question reste le garde-fou final.

## 8. Aucune idée Vision ne perturbe la Capability en cours

Toute idée découverte pendant l'implémentation et jugée hors périmètre est consignée dans le registre Vision (`VISION_DECISION_WORKSPACE.md`) ou dans le Parking (`PRODUCT_BOARD.md` section 7) — jamais développée sur-le-champ, jamais laissée "entre deux" (règle de discipline, `PRODUCT_BOARD.md` section 11). L'implémentation en cours reprend immédiatement après consignation.

## 9. Discipline de branches — rappel

Aucun commit direct sur `main`. Une branche par incrément. Revue par Fred avant toute fusion. Cette règle est en vigueur depuis le 2026-08-02 et ne dépend d'aucune des règles ci-dessus — elle les précède toutes.

## 10. Une capacité s'évalue dans sa boucle, jamais isolément

Une fonctionnalité n'est jamais évaluée isolément. Elle est toujours évaluée comme une étape du cycle complet vécu par l'utilisateur (voir `docs/Architecture/DECISION_LOOP.md`). Une capacité peut être peu différenciante prise seule et devenir extrêmement différenciante lorsqu'elle s'inscrit dans une boucle métier cohérente.

C'est exactement ce qu'a montré la Commercial Readiness Review du Review Briefing (Capability 3, Incrément 2, 2026-08-05) : notée isolément, la fonctionnalité obtient une différenciation modérée (5/10) — n'importe quel concurrent pourrait ajouter un rappel de recommandation en un sprint. Mais resituée dans la boucle Décision → Exécution → Mémoire → Préparation de revue, elle devient la preuve visible d'un actif difficile à copier : la discipline sémantique qui distingue une tâche cochée d'un résultat réellement constaté. Toute évaluation future — priorisation, revue commerciale, arbitrage Vision/Parking — doit d'abord situer la fonctionnalité dans la boucle avant de juger sa valeur autonome.

## 11. Discipline après chaque Commercial Readiness Review

Après chaque Commercial Readiness Review, une question systématique est posée : **"Qu'avons-nous appris sur le produit lui-même ?"** La réponse alimente exclusivement le Product Board, le registre Vision (`VISION_DECISION_WORKSPACE.md`), ou le Parking (`PRODUCT_BOARD.md` section 7) — jamais directement le backlog. Cette règle garantit que chaque revue commerciale enrichit progressivement la stratégie produit sans perturber la roadmap en cours ni introduire d'incréments non arbitrés par Fred.

## 12. La documentation suit l'implémentation

**Documentation follows implementation. Documentation preserves knowledge. Documentation does not become an independent workstream. Product execution is now the primary driver of learning.**

Depuis la clôture de la phase de fondation (`FOUNDATION_COMPLETE.md`, 2026-08-05), la documentation n'est plus le chemin par lequel Pepperyn apprend — l'usage réel par les utilisateurs l'est. Concrètement : un document se rédige désormais pour capturer une décision déjà prise ou un comportement déjà construit, jamais pour explorer une idée avant qu'un besoin concret ne l'ait fait émerger pendant le développement d'une capacité. La discipline documentaire posée pendant la fondation (GD-001, cette Section 0, les règles ci-dessus) reste pleinement en vigueur — elle change de rôle, pas de rigueur : elle accompagne le produit, elle ne le précède plus systématiquement.

## 13. Gel de la gouvernance

La gouvernance documentaire de Pepperyn est désormais considérée comme stabilisée (Governance Reconciliation Sprint + ADR Governance Cleanup, 2026-08-05). Toute évolution future de cette gouvernance — nouvelle Governance Decision, nouvelle convention de nommage, réorganisation de la hiérarchie documentaire — devra être justifiée par un besoin concret rencontré pendant le développement du produit ou par un retour utilisateur réel, jamais par anticipation. Aucun nouveau sprint documentaire ne sera ouvert sans justification explicite de ce type.

---

PRODUCT BOARD READY.
EXECUTION GOVERNANCE READY.
FOUNDATION CLOSED — PRODUCT EXECUTION MODE.
