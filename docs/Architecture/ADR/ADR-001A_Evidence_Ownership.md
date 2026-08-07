# ADR-001A — Evidence Ownership
**Phase :** T1-A, complément à ADR-001 (résolution de la question ouverte n°1)
**Statut :** Proposé, pour signature par comité d'architecture
**Sources autorisées :** Current Domain Model · Ideal Domain Model · Transformation Blueprint · Pepperyn Constitution v1.0 · ADR-001
**Nature :** décision d'architecture unique et ciblée. Aucun code, aucune migration, aucun modèle n'est modifié par ce document.

---

## 1. Contexte et question posée

ADR-001 introduit l'Evidence Ledger sans verrouiller à quel objet du domaine il appartient. Ce n'est pas un détail d'implémentation : le propriétaire d'un registre détermine sa granularité, ses invariants d'unicité, et la manière dont tout le reste du domaine peut légitimement l'interroger. Une décision prise plus tard, une fois des faits déjà accumulés sous une mauvaise frontière, ne se corrige pas par un ajustement — elle exige une réattribution complète de tout ce qui a déjà été enregistré.

La question à trancher : **à quel objet permanent du domaine appartient l'Evidence Ledger ?**

---

## 2. Les quatre options examinées

### Option A — Evidence appartient à l'Analysis
L'Analysis est aujourd'hui l'unité de travail du domaine : un fichier, une exécution, un résultat. Rattacher l'Evidence Ledger à l'Analysis reviendrait à créer un registre neuf, isolé, à chaque nouvelle analyse.

- **Constitution :** l'Article IV définit l'Engagement comme ce qui « précède et dépasse chaque intervention ponctuelle » et « ne se réduit jamais à un seul examen isolé ». Un Evidence Ledger scopé à l'Analysis serait, par construction, un examen isolé de plus.
- **Ideal Domain Model :** ne prévoit à aucun moment un registre de preuve borné à un événement ponctuel.
- **Blueprint :** identifie précisément, comme dette actuelle, le fait que le domaine « pense en événements isolés » plutôt qu'en relation continue — reproduire cette frontière au niveau de l'Evidence Ledger perpétuerait la dette qu'ADR-001 a pour objet de résorber, une couche plus bas.
- **Verdict :** rejetée. Elle ne fait que déplacer le problème que l'Evidence Ledger a été introduit pour résoudre : la preuve resterait prisonnière de la durée de vie d'un seul événement, cette fois persistée mais toujours sans continuité.

### Option B — Evidence appartient à la Company
La Company est, dans le modèle actuel, la racine de propriété et de facturation — le compte qui a souscrit à Pepperyn.

- **Constitution :** aucun article ne définit la Company comme porteuse de faits ; l'Article IV réserve ce rôle à l'Engagement.
- **Ideal Domain Model :** distingue explicitement le cabinet ou le compte qui utilise Pepperyn (hors du domaine cœur, classé Generic) de chaque relation cliente suivie (Engagement, Core). Une Company peut, structurellement, être liée à plusieurs relations distinctes.
- **Blueprint :** relève que la matérialité et la priorisation doivent être propres à chaque relation suivie — un registre unique par Company mélangerait les faits de plusieurs relations potentiellement sans rapport entre elles sous un seul toit, rendant tout seuil de matérialité ou toute mesure d'attention proprement inexploitable.
- **Verdict :** rejetée. Trop large : elle confond le compte qui utilise Pepperyn avec les relations distinctes que ce compte sert.

### Option C — Evidence appartient à l'Engagement
- **Constitution, Article V (La Mémoire) :** énonce littéralement que « Pepperyn mémorise l'évolution des faits financiers d'un Engagement dans le temps ». Ce n'est pas une inférence — c'est la formulation exacte déjà adoptée.
- **Constitution, Article IV :** place l'Engagement en tête des objets permanents du domaine, précisément parce qu'il porte une durée, un contexte et une mémoire propres — les trois attributs qu'un registre de preuve doit pouvoir hériter.
- **Ideal Domain Model, section E.3 :** définit l'agrégat racine de la preuve financière comme « un par Engagement × période » — la granularité exacte que cette ADR doit choisir est déjà celle retenue dans le modèle cible.
- **Blueprint :** avait déjà, sans le formaliser, orienté ADR-001 dans cette direction (l'Evidence Ledger y est décrit comme rassemblant les faits « pour une relation suivie »).
- **Verdict :** retenue. C'est la seule option pour laquelle les quatre sources convergent sans exception, dont deux de façon littérale et explicite (Constitution Article V, Ideal Domain Model E.3).

### Option D — Evidence appartient à un objet indépendant, hors hiérarchie existante
Un objet de portée propre, ni Analysis, ni Company, ni Engagement — par exemple pour permettre à une preuve d'être partagée entre plusieurs relations.

- **Constitution, Article XII :** exige qu'un objet du domaine n'ait « qu'une seule représentation faisant autorité » ; introduire une deuxième hiérarchie de rattachement, parallèle à celle déjà définie par l'Engagement, créerait précisément l'ambiguïté que cet article interdit.
- **Constitution, Article XII (simplicité) :** un objet d'ownership supplémentaire, sans nécessité démontrée, est une sophistication non justifiée.
- **Ideal Domain Model :** le seul besoin de lecture transverse à plusieurs Engagements identifié dans les sources est le benchmark de portefeuille — explicitement conçu comme un consommateur en lecture seule et anonymisé, jamais comme un propriétaire de la preuve elle-même.
- **Verdict :** rejetée. Aucune des quatre sources ne motive cette option ; elle serait une invention, ce que la méthode de travail retenue exclut explicitement.

---

## 3. Décision

**L'Evidence Ledger appartient à l'Engagement. Un Engagement possède un et un seul Evidence Ledger faisant autorité par période.**

Cette décision n'est pas un choix parmi des options également défendables : c'est la seule des quatre pour laquelle la Constitution (Article V, texte littéral), le Modèle Idéal (agrégat explicitement défini ainsi) et le Blueprint (orientation déjà prise sans être verrouillée) convergent sans contradiction.

---

## 4. Conséquence directe sur ADR-001

Cette décision ferme la question ouverte n°1 d'ADR-001 (« à quoi l'Evidence Ledger doit-elle être rattachée en l'absence d'un Engagement formel »), avec la précision suivante, qui ne rouvre aucune autre décision déjà prise :

La propriété **conceptuelle** de l'Evidence Ledger est l'Engagement, dès aujourd'hui et de façon définitive. Sa propriété **transitoire d'implémentation**, tant que l'Engagement n'a pas été physiquement introduit (phase T2 du Blueprint), s'appuie sur l'objet du domaine actuel le plus proche de sa définition — l'Entity, déjà identifiée par le Blueprint comme la base sur laquelle l'Engagement sera construit par enveloppe additive. Cette période transitoire n'est pas une nouvelle option d'ownership : c'est un point d'ancrage provisoire, avec obligation de réattribution explicite au moment où l'Engagement existe. Aucun Evidence Ledger ne doit être considéré comme définitivement rattaché à une Entity — seulement en attente de sa réattribution.

---

## 5. Invariant complémentaire

Cette décision d'ownership en appelle un, distinct de ceux déjà énoncés dans ADR-001 :

**Deux Evidence ne peuvent jamais représenter contradictoirement le même fait pour une même période et une même provenance.**

Sans cet invariant, la propriété par Engagement ne suffit pas à garantir une vérité unique : un même Engagement pourrait accumuler, au fil de plusieurs analyses, deux valeurs différentes pour un même fait sans qu'aucune règle n'arbitre laquelle fait autorité — ce qui polluerait silencieusement tout ce qui consommera plus tard ce registre (signal d'attention, recommandations). Cet invariant est ajouté à la section 6 d'ADR-001.

---

## 6. Conformité constitutionnelle

- **Article IV** : la décision fait de l'Engagement le porteur effectif de la mémoire et du contexte que cet article lui attribue déjà — elle ne fait qu'exécuter la définition, elle n'en crée pas une nouvelle.
- **Article V** : la décision applique littéralement le texte déjà adopté.
- **Article X** (une seule source de vérité) : en fixant un propriétaire unique et sans ambiguïté, cette décision empêche par construction qu'un même fait puisse un jour être revendiqué par deux hiérarchies de rattachement différentes.
- **Article XII** (simplicité, représentation unique) : la décision retenue est celle qui n'introduit aucun objet ni aucune hiérarchie supplémentaire — elle réutilise ce que la Constitution a déjà nommé.

---

## 7. Statut

Avec cette décision, la question de propriété de la preuve — identifiée comme la seule décision de modélisation qu'un ADR ne pouvait pas laisser ouverte — est tranchée. La question ouverte n°1 d'ADR-001 est close. Les questions ouvertes n°2 à n°5 d'ADR-001 restent, elles, ouvertes et hors du périmètre de ce document.

---

**ADR-001A RESOLVED.
QUESTION OUVERTE N°1 D'ADR-001 CLOSE.
AUCUN CODE MODIFIÉ.**
