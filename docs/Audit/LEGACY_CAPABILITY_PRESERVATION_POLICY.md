# LEGACY_CAPABILITY_PRESERVATION_POLICY.md

**Nature :** politique de gouvernance. Vit sous la Constitution, pas dedans — voir justification de niveau documentaire en fin de document. N'est PAS une Constitution v1.1. Aucun code modifié, aucune migration, aucune suppression.

---

## Mission 1 — Le modèle Shell / Domain est-il suffisant ?

Réponse honnête, fondée sur preuve de code (voir `ANONYMIZATION_CAPABILITY_REVIEW.md` pour le détail) : **non, pas tel quel.**

**1. Ces capacités appartiennent-elles au Shell ?** Partiellement. Permissions d'accès aux organisations, gestion des secrets d'infrastructure (clés API, JWT), résilience du service (uptime, retries) sont des préoccupations qui gardent l'accès au système dans son ensemble — elles ne connaissent rien du métier CFO, exactement comme la navigation ou l'authentification. Elles sont légitimement Shell.

**2. Appartiennent-elles au Domain ?** Non, et c'est la preuve la plus importante de cette mission : aucune de ces neuf capacités ne correspond à une responsabilité qu'un excellent CFO exerce lui-même. Un CFO ne « s'anonymise » pas mentalement les données d'un dossier avant d'y réfléchir. Le test du North Star (« reproduit-elle ou amplifie-t-elle une responsabilité du CFO ? ») répond non aux deux branches pour l'anonymisation, la conformité, l'auditabilité — ce ne sont pas des responsabilités professionnelles, ce sont des obligations que le logiciel s'impose à lui-même parce qu'il manipule des données réelles.

**3. Faut-il reconnaître une troisième couche — PEPPERYN TRUST & PLATFORM ?** Oui, mais pas pour toutes les neuf capacités de façon uniforme, et pas comme un endroit où du code nouveau habiterait par défaut. La preuve de code (voir `ANONYMIZATION_CAPABILITY_REVIEW.md`) montre exactement pourquoi une troisième couche est nécessaire plutôt qu'un vœu pieux : l'anonymisation est aujourd'hui **implémentée une fois** (`anonymization_service.py`, correcte et bien conçue pour son périmètre) mais **invoquée indépendamment à quatre endroits différents** (`analyze.py` pour le pipeline principal, `analyze.py` pour le chat legacy, `conversation_engine.py` pour le chat V2 — qui ne l'invoque pas du tout —, et `/api/analyze/text` — qui ne l'invoque pas non plus). Chacun de ces points de passage a dû, indépendamment, décider s'il anonymisait ou non — et deux d'entre eux ont pris la mauvaise décision, silencieusement, sans qu'aucune couche commune ne le remarque. C'est exactement le type de duplication de responsabilité que l'Article XII (principes d'architecture, test de simplicité) condamne ailleurs dans la Constitution.

**4. Cette troisième couche apporte-t-elle une vraie frontière, ou seulement un nouveau nom ?** Une vraie frontière, à condition d'être définie précisément :

> **Pepperyn Trust & Platform** n'est pas un endroit où des écrans ou des fonctionnalités habitent. C'est l'ensemble des garde-fous qui doivent être traversés obligatoirement à chaque franchissement de frontière Domain → extérieur (tout appel LLM, tout export, toute écriture de log, tout stockage), avec une implémentation canonique unique, consommée aussi bien par le Shell (isolation d'organisation, secrets) que par le Domain (anonymisation, intégrité de l'Evidence Ledger). Sa responsabilité : garantir des invariants de protection qui ne doivent jamais être ré-implémentés indépendamment par chaque site d'appel. Ses consommateurs : chaque site d'appel LLM (aujourd'hui quatre, vérifiés par le code, dont deux non conformes), chaque export, chaque écriture de log.

Cette troisième couche n'est donc pas décorative : elle a une responsabilité précise (garantir qu'un franchissement de frontière ne peut pas se produire sans passer par le garde-fou partagé) et des consommateurs précis (les sites d'appel eux-mêmes, énumérables et vérifiables par grep). Le critère de non-création d'une couche sans responsabilité et consommateurs précis, posé par le mandat, est donc respecté — la couche n'est pas créée pour toutes les neuf capacités listées en vrac, mais spécifiquement pour celles qui gardent une frontière Domain → extérieur : **anonymisation, isolation de données inter-organisations, auditabilité de ce qui a été envoyé à un LLM.** Sécurité générique de transport, secrets d'infrastructure, résilience, permissions d'organisation restent Shell — elles gardent l'accès au système, pas une frontière Domain.

**Ce que cette mission ne fait pas :** elle ne crée aucun nouveau module de code. Elle nomme une responsabilité déjà réelle mais aujourd'hui dispersée, comme point de départ pour la Mission 5 (matrice) et pour un futur ADR si Fred choisit de la faire exécuter.

---

## Mission 2 — Principe de conservation sélective

**Formulation retenue :**

> Une capacité héritée n'est ni présumée obsolète ni présumée légitime. Elle gagne son droit d'exister dans l'architecture cible en démontrant, avec preuve plutôt qu'intention : sa valeur utilisateur actuelle observable ; la responsabilité professionnelle ou technique précise qu'elle sert ; sa cohérence avec la Constitution ; sa cohérence avec le Profession Model lorsqu'applicable ; l'absence de contradiction avec le Domain cible ; sa qualité réelle d'implémentation (pas seulement son intention) ; son coût de maintien ; son niveau de sécurité réel, vérifié par le code et non par la documentation ; ses consommateurs réels (pas supposés) ; l'existence ou non d'un mécanisme cible déjà supérieur qui la rendrait redondante.

**Niveau documentaire retenu : document dédié, référencé depuis `PRODUCT_OPERATING_SYSTEM.md`.**

Justification par élimination, cohérente avec la discipline établie dans cette session (cf. `PRODUCT_BOARD_CANONICAL_ARBITRATION.md`, Mission 3) :

- **Pas dans la Constitution** : la Constitution elle-même l'interdit tant que le principe n'a pas « résisté au terrain » (Article IX — nécessité démontrée, pas préférence), et Fred l'a explicitement demandé ainsi.
- **Pas une simple règle de Product Board** : le Product Board porte l'état réel livré et les décisions actives à court terme (voir sa restructuration en 5 sections proposée dans l'arbitrage précédent) — un principe de gouvernance méthodologique durable, applicable à des dizaines de capacités sur plusieurs mois, y noyer sa substance reproduirait exactement le problème de mélange des registres qui vient d'être diagnostiqué pour `PRODUCT_BOARD.md`.
- **Pas un ADR** : un ADR documente une décision d'architecture ponctuelle et datée (« pourquoi cet objet a cette forme »), pas un principe d'évaluation permanent et répétable, appliqué capacité par capacité dans la durée.
- **Document dédié**, donc : `LEGACY_CAPABILITY_PRESERVATION_POLICY.md` (ce document), placé sous `docs/Architecture/audit/` comme les autres livrables de gouvernance non encore promus, et référencé — pas dupliqué — depuis `PRODUCT_OPERATING_SYSTEM.md` comme méthode applicable à tout inventaire futur de dette ou de legacy, pas seulement celui-ci. Cohérent avec la trajectoire que Fred a lui-même fixée : « pourra être promue dans une future Constitution uniquement lorsqu'elle aura résisté au terrain » — un document dédié est la seule option qui permette cette promotion ultérieure sans réécrire un autre document au passage.

---

## Mission 3 — Taxonomie des verdicts

La taxonomie proposée est correcte dans son esprit (présomption de réexamen, pas de suppression) mais insuffisamment précise sur deux points : elle ne distingue pas clairement ADAPT de REPLACE (les deux parlent de « mécanisme à changer »), et PARK manque d'une condition de sortie explicite symétrique à son entrée. Corrections apportées ci-dessous, entre crochets.

| Statut | Critères d'entrée | Preuves requises | Conséquences | Condition de sortie | Traitement code/doc |
|---|---|---|---|---|---|
| **KEEP** | Cohérente avec Constitution + Domain cible ; consommateurs réels actifs ; qualité d'implémentation suffisante ; aucun mécanisme cible supérieur identifié | Trace de consommateur réel (route appelée, composant rendu) ; absence de contradiction relevée en Mission 5 | Aucune action — la capacité continue d'exister sans réserve | Réexamen si un mécanisme cible apparaît plus tard, ou si un incident révèle une faille non détectée ici | Aucun, capacité documentée comme validée dans la matrice |
| **STRENGTHEN** | Légitime, consommateurs réels, mais incomplète face aux exigences actuelles (preuve : au moins une lacune concrète identifiée par le code, pas une hypothèse) | Lacune nommée et localisée dans le code (exemple concret : chemin d'appel non couvert) | Chantier d'amélioration ouvert, sans changer le mécanisme de fond | Toutes les lacunes nommées sont couvertes, revérifié par le code | Code étendu, jamais réécrit depuis zéro ; doc mise à jour avec la preuve de couverture |
| **ADAPT** *[précisé]* | Le mécanisme de fond reste valide et suffisant, mais sa portée, son vocabulaire ou son point d'intégration doivent changer pour s'aligner sur le Domain cible — **pas de changement de la logique interne** | Preuve que la logique interne (l'algorithme, la règle) reste correcte ; seul l'habillage ou le branchement est visé | Modification ciblée du point d'intégration, jamais du cœur du mécanisme | Le nouveau point d'intégration est vérifié consommé par le Domain cible | Renommage/rebranchement seulement ; le fichier cœur n'est pas réécrit |
| **REPLACE** *[précisé]* | Le besoin reste valide et démontré, mais **le mécanisme lui-même** — pas seulement son branchement — est structurellement inadéquat (preuve : le mécanisme ne peut pas être étendu sans le réécrire) | Preuve que STRENGTHEN et ADAPT ont été considérés et rejetés explicitement, pas sautés | Nouveau mécanisme conçu comme un ADR à part entière ; ancien mécanisme retiré seulement après que le nouveau a un consommateur réel (règle « pas de code dormant » déjà posée dans le Foundation Recovery Sprint) | Le nouveau mécanisme a un consommateur réel démontré, l'ancien est démontré non utilisé | Ancien code retiré seulement après bascule complète, jamais en parallèle indéfiniment |
| **RETIRE** | Contradictoire avec la Constitution ou le Domain cible ; ou redondant avec un mécanisme déjà supérieur ; ou sans valeur démontrable par le test de retrait (Mission 7) | Test de retrait complété avec réponse « aucune perte » ou « perte déjà compensée ailleurs » | Suppression planifiée, jamais immédiate — passage par une dépréciation observable avant retrait effectif | Aucune régression observée après une période de dépréciation définie | Code supprimé après période de dépréciation ; doc archivée, jamais effacée silencieusement |
| **PARK** *[condition de sortie ajoutée]* | Valeur plausible mais aucun usage actuel ne la justifie ; pas de preuve de rejet non plus | Absence de consommateur actuel démontrée, sans preuve de non-valeur | Ni développée ni supprimée ; reste dans le registre avec un déclencheur de réexamen nommé | **Un événement précis et nommé** (retour utilisateur, nouvelle dépendance qui la rend nécessaire) — jamais une réouverture par défaut au fil du temps, jamais un oubli silencieux non plus | Aucun changement ; entrée maintenue vivante dans le registre, jamais retirée sans décision explicite |

---

## Niveau documentaire de cette politique elle-même

Ce document vit sous `docs/Architecture/audit/`, référencé depuis `PRODUCT_OPERATING_SYSTEM.md` par un simple lien, jamais dupliqué. Il ne modifie ni la Constitution ni le Product Board canonique. Sa promotion éventuelle vers une Constitution v1.1 est une décision humaine future, explicitement hors du périmètre de cette mission.

---

**LEGACY_CAPABILITY_PRESERVATION_POLICY ÉTABLIE. AUCUN CODE MODIFIÉ, AUCUNE CONSTITUTION AMENDÉE.**
