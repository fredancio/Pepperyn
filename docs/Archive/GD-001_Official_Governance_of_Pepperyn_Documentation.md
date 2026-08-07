# GD-001 — Official Governance of Pepperyn Documentation

**Type :** Governance Decision (première de la série GD)
**Date de proposition :** 2026-08-02
**Statut :** **ADOPTÉE** — 2026-08-02 (GD-001A, adoption officielle par les fondateurs)
**Portée :** gouvernance documentaire uniquement. Ne modifie, ne contredit et n'interprète aucun principe produit.
**Déclenchée par :** la collision documentaire identifiée par le Sprint 0 (trois documents revendiquant le rôle de Constitution).
**Amendée lors de l'adoption (GD-001A) :** principe de non-rétroactivité (§3quater), principe de traçabilité (§3ter), reformulation de la Section 10. Les trois amendements sont intégrés directement dans le corps du texte ci-dessous — aucune version non amendée de ce document ne fait foi.

---

## Section 1 — Préambule

Une gouvernance documentaire explicite n'est pas un exercice bureaucratique : c'est une condition de survie pour un domaine qui a l'ambition de rester cohérent au fil des années, des équipes et des technologies qui se succéderont. Le Sprint 0 en a fourni la preuve concrète, pas théorique : en assainissant le dépôt, il a découvert que trois documents distincts, produits à trois moments différents, se présentaient chacun comme *la* Constitution de Pepperyn — l'un d'eux s'auto-déclarant même « Autorité : Suprême ». Aucun des trois ne mentait ; chacun reflétait fidèlement l'état de la réflexion au moment où il a été écrit. Le problème n'est pas qu'un mauvais document ait été produit — c'est qu'aucune règle n'existait pour dire, une fois plusieurs documents produits, lequel doit être suivi.

C'est exactement la situation que l'Article X de la Constitution interdit au niveau du domaine métier : deux représentations qui prétendent chacune être la vérité. GD-001 applique ce même principe, non plus au code, mais aux documents eux-mêmes. Une Constitution qui interdit la duplication de vérité dans le produit, mais tolère sa propre duplication dans la documentation qui la gouverne, se contredirait elle-même.

GD-001 ne tranche donc pas un désaccord de contenu — les trois documents ne sont pas nécessairement en désaccord sur le fond. GD-001 tranche une question strictement antérieure : laquelle de ces sources peut aujourd'hui être citée pour justifier une décision produit. Sans cette réponse, chaque nouvelle personne qui rejoint le projet — humaine ou non — devrait redécouvrir seule ce que le Sprint 0 a mis plusieurs heures à révéler.

---

## Section 2 — Hiérarchie officielle

### Niveau A — FOUNDATIONAL DOCUMENTS

Ce sont les seuls documents faisant officiellement autorité pour toute décision produit. Chacun a un rôle distinct et non substituable :

- **Pepperyn Constitution v1.0** — les principes intemporels et non techniques du domaine. Rôle : dire ce que Pepperyn *est* et n'est jamais autorisé à devenir, indépendamment de toute technologie. C'est l'autorité suprême — tout autre document, y compris ce GD, lui est subordonné.
- **Pepperyn Oath** — l'engagement culturel qui accompagne la Constitution. Rôle : traduire les principes en promesses concrètes pour quiconque contribue au produit. Non normatif au sens technique, mais indissociable de la Constitution qu'il sert.
- **Current Domain Model** — la description factuelle et honnête de ce que Pepperyn *est* aujourd'hui, tel qu'observé dans le code réel. Rôle : point de départ vérifiable de toute transformation, jamais une aspiration.
- **Ideal Domain Model** — la conception cible du domaine, construite indépendamment de l'implémentation actuelle. Rôle : dire où Pepperyn doit converger, sans compromis avec l'existant.
- **Transformation Blueprint** — la comparaison entre le Current et l'Ideal, et la stratégie de migration incrémentale entre les deux. Rôle : le seul chemin autorisé entre ce qui existe et ce qui est visé.
- **ADR (Architecture Decision Records)** — la chaîne complète des décisions d'architecture déjà prises (ADR-001, ADR-001A, et toutes les suivantes). Rôle : traduire le Blueprint en décisions techniques engageantes, une à la fois, chacune traçable à sa justification.

### Niveau B — IMPLEMENTATION DOCUMENTS

Ces documents décrivent ce qui s'est passé, ce qui a été vérifié, ou l'état d'avancement d'un travail. Ils sont indispensables à la traçabilité, mais **ne créent aucun principe et ne peuvent contredire aucun document de Niveau A** :

- **PR Reviews** (ex. : revue de T1C-A) — attestent qu'une implémentation respecte les ADR et la Constitution avant fusion. Rôle : contrôle qualité, pas source de vérité.
- **Repository Reports** (ex. : Repository Baseline Report du Sprint 0) — décrivent l'état du dépôt à un instant donné. Rôle : photographie, jamais une décision.
- **Audit Reports** (ex. : audits Phase 1A/1B/1C, T1B) — constatent un état de fait par lecture du code réel. Rôle : preuve d'entrée pour une future décision, jamais la décision elle-même.
- **Sprint Reports** (ex. : ce Sprint 0) — documentent le déroulement et les résultats d'un cycle de travail. Rôle : historique d'exécution.
- **Test Reports** — attestent qu'un comportement observé correspond (ou non) à ce qu'un ADR ou la Constitution exige. Rôle : vérification, jamais spécification.

Un document de Niveau B qui révèle un manque (une décision non prise, une contradiction, un principe absent) ne comble jamais ce manque lui-même — il déclenche, le cas échéant, un document de Niveau A (nouvel ADR) ou une nouvelle Governance Decision.

### Niveau C — LEGACY DOCUMENTS

Y figurent, sans exception ni hiérarchie entre eux :

- `PEPPERYN_PRODUCT_CONSTITUTION.md`
- `pepperyn-os/` (l'ensemble de l'arborescence : sa propre « constitution », son propre index d'ADR, ses Trust/Value Frameworks, ses Product Contracts, son Decision Kernel)
- `PEPPERYN_BASELINE_v1.0.md` et `PEPPERYN_PRODUCT_QUALITY_CONTRACT.md`
- les documents historiques déjà rangés dans `docs/Architecture/history/` (rapports de phase, Business Rules V1/V1 FINAL, Decisions V1, PEDL_Architecture, etc.)

Ces documents sont **conservés et consultables**. Ils ne sont **plus normatifs** : aucune décision produit, présente ou future, ne peut les citer comme justification. Ils peuvent en revanche être cités comme *contexte historique* — pour comprendre pourquoi une décision antérieure a été prise — jamais comme fondement d'une décision nouvelle. Si l'un d'eux contient une idée encore valable et non capturée ailleurs (par exemple les Trust/Value Frameworks de `pepperyn-os/`), cette idée doit être réintroduite par le circuit normal — une nouvelle ADR, ou une Governance Decision — jamais héritée silencieusement de sa source Legacy.

---

## Section 3 — Single Source of Truth

Pepperyn ne reconnaît, à tout instant, qu'une seule version faisant autorité de chacun des documents suivants :

- **Une seule Constitution.**
- **Un seul Blueprint.**
- **Un seul Current Domain Model.**
- **Un seul Ideal Domain Model.**
- **Une seule chaîne d'ADR** — cumulative, jamais parallèle : deux ADR ne peuvent jamais gouverner la même décision de façon contradictoire sans que l'une explicite formellement qu'elle remplace l'autre.

Toute divergence constatée entre deux documents qui prétendraient occuper la même fonction — comme celle qui a motivé ce GD — **doit être résolue par une Governance Decision**, jamais par un choix silencieux, jamais par une simple préférence exprimée en conversation, jamais par un déplacement de fichier qui laisserait deviner une intention sans la formuler.

### 3bis — Principe de précédence documentaire

Ce principe, proposé par Fred à l'issue du Sprint 0, formalise la chaîne de responsabilité qui découle directement de la hiérarchie ci-dessus. Il est adopté sans modification :

1. La Constitution prévaut sur tous les autres documents.
2. Les Governance Decisions (GD) interprètent ou organisent la gouvernance, sans pouvoir contredire la Constitution.
3. Les Domain Models décrivent le domaine conformément à la Constitution.
4. Le Blueprint décrit la transformation conformément aux Domain Models.
5. Les ADR décrivent les décisions d'architecture conformément au Blueprint.
6. Le code implémente les ADR.
7. Les tests vérifient que le code respecte les ADR.

Chaque niveau dérive du précédent et ne peut jamais le contredire. Une contradiction détectée à n'importe quel niveau ne se résout jamais en modifiant silencieusement le niveau supérieur pour qu'il s'accorde au niveau inférieur — elle se résout en corrigeant le niveau inférieur, ou en ouvrant formellement la question au niveau supérieur concerné (nouvel ADR, nouveau Blueprint, ou — en dernier recours, et seulement dans les conditions strictes de la Section 6 — révision de la Constitution elle-même).

### 3ter — Principe de traçabilité *(amendement d'adoption, GD-001A)*

Conséquence directe du principe de précédence : une décision d'architecture qui ne peut pas être reliée explicitement à ce dont elle dérive n'est pas traçable, et une chaîne non traçable ne peut pas être vérifiée. En conséquence :

**Chaque ADR devra désormais référencer explicitement :**
- **la section du Blueprint concernée** ;
- **l'article de la Constitution concerné (lorsque pertinent).**

Cette règle s'applique à toute ADR future, à compter de l'adoption de GD-001. Elle ne s'applique pas rétroactivement (voir §3quater) — ADR-001 et ADR-001A restent valides telles qu'écrites, sans être réécrites pour s'y conformer formellement, bien que leur contenu satisfasse déjà cette exigence dans les faits (ADR-001 §12 cite explicitement les articles III, IV, IX, X, XII ; ADR-001A section 6 fait de même).

### 3quater — Principe de non-rétroactivité *(amendement d'adoption, GD-001A)*

**L'adoption de GD-001 ne remet pas en cause la validité historique des décisions prises avant son adoption. Elle définit uniquement la gouvernance documentaire applicable aux décisions futures.**

Concrètement : ADR-001, ADR-001A, T1B, le T1C Implementation Plan et l'implémentation T1C-A elle-même restent pleinement valides tels qu'ils ont été décidés et exécutés, même si leur formulation ne suit pas explicitement chacune des règles introduites ou précisées par GD-001 (notamment le principe de traçabilité ci-dessus). Reclasser rétroactivement des décisions déjà prises comme non conformes reviendrait à faire de la gouvernance documentaire un instrument d'invalidation plutôt que d'organisation — ce que GD-001 (Section 1, Préambule) exclut explicitement de son rôle.

---

## Section 4 — Cycle de vie documentaire

La séquence suivante est la seule autorisée pour faire passer une idée d'un principe à une réalité vérifiée en production :

```
Constitution
   ↓
Domain Model (Current + Ideal)
   ↓
Blueprint
   ↓
ADR
   ↓
Implementation Plan
   ↓
Code
   ↓
Tests
   ↓
PR Review
   ↓
Merge
   ↓
Release
```

Aucune étape ne peut être court-circuitée, et aucune étape ne peut précéder celle qui la fonde. Écrire du code sans ADR préalable, ou fusionner sans revue, rompt cette chaîne au même titre qu'ignorer la Constitution rompt tout ce qui en découle.

Ce cycle n'est pas une aspiration théorique pour Pepperyn v2 : T1C-A l'a déjà suivi intégralement et sans exception — ADR-001 puis ADR-001A (Domain Model → Blueprint → ADR), T1B (audit de vérification), T1C Implementation Plan, code, tests, PR Review formelle (APPROVED WITH NOTES), avant toute fusion envisagée. GD-001 ne fait donc que nommer une discipline déjà éprouvée une première fois, pas en inventer une nouvelle.

---

## Section 5 — Types de décisions

Cinq catégories, sans chevauchement possible :

- **Constitution** → principes permanents. Change rarement, et seulement par nécessité démontrée (Article IX). Répond à la question : *que sommes-nous, pour toujours ?*
- **Governance Decision (GD)** → gouvernance documentaire. Organise ou interprète la hiérarchie des documents eux-mêmes. Ne décide jamais d'architecture ni de produit. Répond à la question : *quel document fait foi ?*
- **ADR (Architecture Decision Record)** → décision d'architecture. Traduit le Blueprint en choix technique engageant. Répond à la question : *comment construisons-nous cette partie du domaine ?*
- **Pull Request Review** → validation technique d'une implémentation précise avant fusion. Répond à la question : *ce code respecte-t-il ce qui a déjà été décidé ?*
- **Sprint Report** → état d'avancement d'un cycle de travail. Répond à la question : *où en sommes-nous ?*

Une confusion fréquente à éviter explicitement : un Sprint Report ou un Audit Report qui révèle un problème n'est pas lui-même une décision — il motive, le cas échéant, l'ouverture d'un ADR ou d'un GD. C'est exactement ce que ce document fait : le Sprint 0 (Niveau B) a révélé la collision ; il ne l'a pas résolue lui-même ; GD-001 (Niveau A) la résout formellement.

---

## Section 6 — Évolution future

**Quand créer une Governance Decision ?**
Lorsque deux documents ou plus entrent en collision sur *le rôle qu'ils occupent* (comme les trois Constitutions), ou lorsque la hiérarchie documentaire elle-même doit être réorganisée, clarifiée ou étendue (par exemple : l'introduction d'un nouveau type de document non prévu ici). Une GD ne discute jamais du contenu métier d'un document — seulement de son statut.

**Quand créer un ADR ?**
Lorsqu'une décision technique doit être prise pour faire progresser le Blueprint déjà accepté, dans le cadre déjà fixé par les Domain Models et la Constitution. C'est l'unité de travail normale et fréquente du projet.

**Quand créer une nouvelle Constitution ?**
Seulement si l'un des principes fondateurs actuels est démontré — pas supposé, pas jugé sous-optimal, **démontré** — comme ne servant plus la mission énoncée à l'Article I (règle déjà posée par l'Article IX de la Constitution elle-même). Une nouvelle Constitution n'est jamais un événement de routine : c'est, par construction, l'événement le plus rare et le plus exceptionnel du cycle de vie documentaire. La preuve que ce seuil est réellement élevé : il n'a été franchi qu'une seule fois dans toute l'histoire du projet — pour remplacer une situation où *trois* documents concurrents s'étaient accumulés faute d'un tel seuil.

**Quand créer un nouveau Blueprint ?**
Seulement lorsque l'Ideal Domain Model change (une nouvelle cible a été redéfinie), ou lorsque le Blueprint actuel a été exécuté dans une proportion telle que le Current Domain Model d'origine ne décrit plus la réalité — auquel cas ce n'est pas une correction du Blueprint existant, mais la clôture formelle d'un cycle de transformation et l'ouverture d'un nouveau, avec un nouveau Current Domain Model comme point de départ vérifié.

---

## Section 7 — Décisions officielles

Par la présente Governance Decision :

1. **`PEPPERYN_CONSTITUTION_v1.0.md` devient la seule Constitution officielle de Pepperyn.**
2. **`PEPPERYN_PRODUCT_CONSTITUTION.md`, l'intégralité de `pepperyn-os/`, `PEPPERYN_BASELINE_v1.0.md` et `PEPPERYN_PRODUCT_QUALITY_CONTRACT.md` deviennent des documents Legacy** (Niveau C) — conservés, consultables, non normatifs, à compter de la date d'adoption de ce GD.
3. **Le Transformation Blueprint actuel (`PEPPERYN_TRANSFORMATION_BLUEPRINT_2026-08-02.md`) devient la feuille de route officielle** de la transformation du produit.
4. **Les ADR (ADR-001, ADR-001A, et toute ADR future numérotée séquentiellement) deviennent les seules décisions d'architecture faisant foi.** Aucun document de `pepperyn-os/06-architecture/` (y compris son propre index d'ADR) ne peut être cité comme décision d'architecture engageante.

---

## Section 8 — Conséquences

Pour tout développement futur :

- Aucune décision produit ne peut plus citer `PEPPERYN_PRODUCT_CONSTITUTION.md` ou `pepperyn-os/` comme justification, même partiellement, même par habitude. Une citation de ce type dans une PR Review, un ADR ou une discussion de conception doit être traitée comme un signal d'alerte, pas comme une référence valable.
- Toute idée présente dans un document Legacy et jugée encore pertinente (par exemple certains éléments du Trust Framework ou du Value Framework de `pepperyn-os/`) doit être réintroduite explicitement — proposée, comparée à la Constitution actuelle, et adoptée par le circuit normal (ADR ou GD) — jamais simplement supposée toujours valide parce qu'elle existe quelque part dans le dépôt.
- Les futurs contributeurs (humains ou agents) doivent, avant de fonder une décision sur un document, vérifier son niveau (A, B ou C) selon la présente hiérarchie. Un document non classé ne peut pas encore servir de fondement — il doit d'abord être classé, par une GD si nécessaire.
- La chaîne de précédence (Section 3bis) devient le test de cohérence par défaut pour toute revue future : une contradiction entre deux niveaux adjacents est toujours résolue en faveur du niveau supérieur.

---

## Section 9 — Actions à réaliser (postérieures à GD-001, distinctes de son adoption)

Ces actions ne font pas partie de l'adoption de GD-001 elle-même — GD-001 est une décision, pas son exécution. Une fois GD-001 formellement adopté, les actions suivantes pourront être planifiées, chacune comme son propre commit, dans le respect de la discipline déjà en vigueur (une décision = un commit) :

- [x] Déplacer les documents Legacy vers une arborescence dédiée — fait : `docs/Architecture/legacy/` (les 4 documents racine : `PEPPERYN_PRODUCT_CONSTITUTION.md`, `PEPPERYN_BASELINE_v1.0.md`, `PEPPERYN_PRODUCT_QUALITY_CONTRACT.md`, et l'intégralité de `pepperyn-os/`). *(GD-001A, 2026-08-02)*
- [x] Ajouter un bandeau « LEGACY — non normatif, conservé pour référence historique uniquement » en tête de chacun des documents concernés — fait : bandeau ajouté sur les 22 fichiers `.md` et le fichier `.html` (`quality-scorecard.html`) de `docs/Architecture/legacy/`. `docs/Architecture/history/` (déjà rangé avant GD-001, pas de collision d'autorité) reçoit le même statut via un README de dossier plutôt qu'un bandeau par fichier — voir `docs/Architecture/history/README.md`. *(GD-001A, 2026-08-02)*
- [x] Mettre à jour `docs/Architecture/constitution/README.md` pour refléter que la collision qu'il décrivait est désormais résolue par GD-001, avec un lien vers ce document — fait. *(GD-001A, 2026-08-02)*
- [x] Mettre à jour tout README ou index qui mentionnerait encore un des documents Legacy sans préciser son statut — vérifié par sweep (`grep`) sur `docs/`, `backend/`, `frontend/`, `tools/`, `archive/` et les fichiers racine : aucune référence résiduelle en dehors des rapports d'audit historiques (Niveau B, non affectés par la non-rétroactivité) et des fichiers Legacy eux-mêmes. *(GD-001A, 2026-08-02)*
- [x] Conserver l'intégralité des documents Legacy sans aucune suppression — respecté : déplacement par `mv`, aucune suppression. *(GD-001A, 2026-08-02)*
- [x] Établir un emplacement et une numérotation officielle pour les futures Governance Decisions (GD-002, GD-003…), par cohérence avec la convention déjà en place pour les ADR — fait : `docs/Architecture/governance/`, ce document lui-même y a été déplacé pour cohérence avec les autres dossiers de Niveau A. Convention documentée dans `docs/Architecture/governance/README.md`. *(GD-001A, 2026-08-02)*

---

## Section 10 — Verdict

**La phase de conception fondatrice de Pepperyn v2 est-elle terminée ?** *(terminologie amendée lors de l'adoption, GD-001A — remplace « phase de fondation »)*

**OUI.**

Justification : les six catégories de documents fondateurs existent désormais, chacune complète et cohérente entre elles — Constitution v1.0 et Oath (adoptés après revue article par article), Current Domain Model et Ideal Domain Model (comparés explicitement), Transformation Blueprint (dérivé de cette comparaison), et une chaîne d'ADR amorcée et déjà mise en œuvre une première fois de bout en bout (ADR-001, ADR-001A, jusqu'au code et à sa revue). La seule chose qui manquait encore pour clore proprement cette phase n'était pas un document supplémentaire, mais une règle disant lesquels de tous les documents produits — y compris ceux hérités d'avant cette refonte — comptent réellement. GD-001 fournit cette règle. **La phase de conception fondatrice est terminée.** Le principe de non-rétroactivité (§3quater) garantit que cette clôture ne remet rien en cause de ce qui a déjà été validé. Avec son adoption, il n'existe plus d'ambiguïté structurelle empêchant de reprendre le développement produit (T1C-B) en confiance.

---

## Contrôle final — non-contradiction

Vérifié avant adoption :

- **Constitution v1.0** : GD-001 ne modifie aucun article, ne prétend à aucune autorité supérieure à elle (Section 3bis, point 1) — il organise seulement ce qui en découle, conformément à l'Article X (une seule vérité) et à l'Article IX (l'évolution se motive par nécessité démontrée, jamais par préférence).
- **Current Domain Model** : non affecté — GD-001 ne redécrit aucun objet du domaine.
- **Ideal Domain Model** : non affecté, pour la même raison.
- **Transformation Blueprint** : GD-001 le confirme comme feuille de route officielle (Section 7.3) sans en modifier une étape.
- **ADR-001** : confirmé comme décision d'architecture faisant foi (Section 7.4) ; GD-001 ne rouvre aucune de ses sections, y compris ses questions ouvertes n°2 à 5, qui restent du ressort d'ADR-001 elle-même.
- **ADR-001A** : de même, confirmée sans modification ; la propriété conceptuelle de l'Evidence Ledger (Engagement) et son ancrage transitoire (Entity) restent inchangés.

Aucune contradiction identifiée.

---

**GD-001 ADOPTED — 2026-08-02.**
