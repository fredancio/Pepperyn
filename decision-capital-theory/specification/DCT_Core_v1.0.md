# Decision Capital Theory — Core Specification

**Version :** 1.0-draft  
**Statut :** MANUSCRIT DE TRAVAIL — Non destiné à la diffusion externe  
**Date :** 2026-07-18  
**Auteurs :** F. Anciaux  
**Langue :** Français (traduction anglaise à prévoir)

> **Note éditoriale générale**  
> Ce document est un manuscrit de travail. Les passages marqués `[ÉDITORIAL]`
> signalent des arbitrages non encore tranchés qui devront être résolus lors de
> la relecture finale. Aucun de ces passages ne remet en cause les axiomes, les
> objets ou les invariants — ils concernent uniquement la forme, le ton et le
> périmètre éditorial du document final.

---

## Résumé

> **[ÉDITORIAL]** Rédiger en dernier. Doit tenir en moins de 200 mots.
> Décision à prendre : résumé en français uniquement, en anglais uniquement,
> ou bilingue ? Objectif : être lisible par un professeur de stratégie, un
> investisseur et un dirigeant de PME sans lecture du document complet.

---

## 1. Introduction

### 1.1 Le problème

À environnement comparable, certaines organisations répondent de façon
systématiquement plus pertinente que d'autres à leur environnement. Ce
différentiel persiste dans le temps et survit au renouvellement des individus
qui composent l'organisation. Il ne s'explique ni par les ressources
disponibles, ni par la taille, ni par l'ancienneté.

La question que cette spécification cherche à répondre est la suivante :
**qu'est-ce qui produit ce différentiel, et comment le gouverner ?**

### 1.2 L'approche

La Decision Capital Theory (DCT) répond à cette question en identifiant un
objet que les théories existantes n'avaient pas formalisé : **l'arc
décisionnel institutionnel**. Elle montre que les organisations qui
structurent, préservent et apprennent de leurs arcs décisionnels accumulent
une forme de capital — le Capital Décisionnel — qui explique le différentiel
observé.

Cette spécification constitue le noyau de la théorie. Elle définit les
axiomes, les objets, les invariants et l'ontologie. Elle ne contient pas les
métriques, les seuils, les niveaux de maturité ni les algorithmes
d'implémentation — ces éléments font l'objet d'un document séparé
(*Reference Implementation*).

> **[ÉDITORIAL]** Décider si une section de contextualisation par rapport à
> la littérature existante (Simon, March, Argyris/Schön, Walsh & Ungson) doit
> figurer dans ce document ou dans un document de recherche séparé. Recommandation :
> la laisser dans `/research/` pour ne pas alourdir le Core.

---

## 2. Fondation

### 2.1 Le phénomène

La DCT cherche à expliquer le phénomène suivant :

> **À environnement comparable, pourquoi certaines organisations répondent-elles
> de façon systématiquement plus pertinente que d'autres, et pourquoi ce
> différentiel persiste-t-il indépendamment des individus qui les composent ?**

Ce phénomène est observable. Il se manifeste notamment lors des successions
de dirigeants, des crises récurrentes et des erreurs stratégiques répétées à
des intervalles inférieurs à la durée de mandat des décideurs.

### 2.2 Axiome 1 — Loi de l'agentivité `[AX-1]`

> **Une organisation ne contrôle pas son environnement.  
> Elle ne contrôle que la manière dont elle y répond.**

L'environnement d'une organisation inclut les conditions macroéconomiques,
les dynamiques concurrentielles, les évolutions réglementaires, les ruptures
technologiques et les crises systémiques. Aucune organisation ne contrôle ces
variables — elles les subissent.

Ce que l'organisation contrôle, c'est la manière dont elle y répond : qui elle
recrute, ce qu'elle produit, comment elle alloue ses ressources, dans quoi elle
investit, à quelle vitesse elle s'adapte.

`AX-1` n'est pas une découverte empirique. C'est un axiome opératoire : sa
valeur n'est pas d'être vrai ou faux au sens de Popper, mais de corriger une
erreur d'attention chronique. La quasi-totalité des organisations pilotent des
variables qu'elles ne contrôlent pas — le chiffre d'affaires, la marge, la
croissance — comme si ces variables étaient des leviers. Elles ne le sont pas.
Ce sont des conséquences de réponses.

> **[ÉDITORIAL]** Décider si le paragraphe sur l'erreur d'attention mérite
> d'être développé en sous-section ou s'il doit rester condensé. La version
> longue est plus pédagogique ; la version courte est plus rigoureuse. Le choix
> dépend du public cible principal : académique ou praticien ?

### 2.3 Axiome 2 — Loi de l'unité `[AX-2]`

> **La réponse d'une organisation à son environnement s'exprime exclusivement
> à travers des décisions. La décision est l'unité fondamentale de la réponse.**

La réponse d'une organisation est un concept macro : elle désigne la posture
globale par laquelle l'organisation engage son environnement. Elle est trop
diffuse pour être gouvernée directement.

La décision, elle, est concrète : elle est datable, attribuable, contextualisée.
Elle est le point où le choix se cristallise. Améliorer les réponses d'une
organisation revient donc à améliorer la pertinence des décisions qui les
composent.

### 2.4 Corollaire

De `AX-1` et `AX-2` découle le corollaire suivant :

> **Le seul levier réel du management est la pertinence des décisions.
> Piloter des résultats est une erreur de cible : les résultats sont des
> conséquences de décisions, non des variables directement actionnables.**

---

## 3. Les Objets

La DCT définit trois objets. Ces trois objets sont distincts, non
substituables, et suffisants pour décrire le phénomène.

---

### 3.1 Décision `[OBJ-1]`

#### Définition

> Acte de choix institutionnel par lequel un acteur habilité, en réponse à
> une situation perçue, sélectionne une option parmi un ensemble fini
> d'alternatives, avec l'intention de produire des conséquences spécifiques.

#### Propriétés

| Identifiant | Propriété | Description |
|---|---|---|
| D-P1 | Identité | Unique : auteur, horodatage, domaine |
| D-P2 | Intentionnalité | Contient des objectifs déclarés et des hypothèses documentées |
| D-P3 | Alternatité | Implique des alternatives explicitement rejetées |
| D-P4 | Contextualité | Embedded dans une situation qui la précède et la justifie |
| D-P5 | Conséquentialité | Produit des effets observables et attribuables |
| D-P6 | Habilitation | Émane d'un acteur ayant autorité dans le domaine concerné |

#### Cycle de vie

```
TRIGGER → DÉLIBÉRATION → CHOIX → HABILITATION → EXÉCUTION → CONSÉQUENCES
```

#### Conditions d'existence

1. Une situation déclenchante doit précéder la décision
2. Au moins deux alternatives doivent exister (une seule option est une
   contrainte, non une décision)
3. Un acteur habilité doit être identifiable
4. L'acte doit être intentionnel — les réactions réflexes non délibérées
   sont hors périmètre

#### Ce que DÉCISION n'est pas

Une décision n'est pas une **action** — l'action est l'exécution de la
décision. Une décision n'est pas un **résultat** — le résultat est la
conséquence de l'action. Ces trois objets sont distincts et non substituables
dans le modèle.

---

### 3.2 Arc Décisionnel `[OBJ-2]`

#### Définition

> Séquence temporelle structurée reliant une situation déclenchante à la
> décision qu'elle a provoquée, à l'exécution de cette décision, aux
> conséquences observées, et à l'apprentissage extrait de la comparaison
> entre ces conséquences et les intentions d'origine.

#### Structure canonique

```
Arc = { S, D, E, C, L }

S  Situation    Contexte et signaux perçus au moment de la décision
D  Décision     Choix retenu, alternatives rejetées, hypothèses, intentions
E  Exécution    Modalités et calendrier de mise en œuvre
C  Conséquences Effets observés, datés et attribuables à D
L  Learning     Jugement de pertinence extrait de la comparaison C vs intentions de D
```

> **[ÉDITORIAL]** Décider si les cinq composantes doivent être maintenues en
> anglais (S, D, E, C, L) pour la mémorisation, ou traduites intégralement en
> français. Argument pour l'anglais : mémorisable, international. Argument pour
> le français : cohérence avec la langue du document. Option hybride possible :
> acronyme SDECL avec définitions en français.

#### États de l'arc

| État | Condition | Capital produit |
|---|---|---|
| OUVERT-PRÉ | S documentée, D non encore prise | 0 |
| OUVERT-POST | S et D documentées, C non connectées | 0 |
| PARTIEL | C partiellement connectées, L absent | 0 |
| FERMÉ | S, D, E, C, L documentés et connectés | > 0 si AQS ≥ seuil |
| VÉRIFIÉ | Fermeture validée par revue indépendante | > 0, pondéré positivement |

#### Transitions légitimes

```
OUVERT-PRÉ  →  OUVERT-POST  →  PARTIEL  →  FERMÉ  →  VÉRIFIÉ
```

Un arc ne régresse jamais. Un arc FERMÉ ne redevient pas OUVERT. Toute
conséquence nouvelle observée après fermeture ouvre un arc distinct.

#### Conditions de fermeture

Un arc est dans l'état FERMÉ si et seulement si :

1. La situation a été documentée **avant ou au moment de la décision** (non
   reconstruite a posteriori)
2. La décision est documentée avec ses alternatives, hypothèses et intentions
3. Des conséquences ont été observées, datées et attribuées à la décision
4. Les conséquences ont été explicitement rattachées à la décision
5. Un apprentissage de pertinence a été extrait et documenté

La condition 1 est discriminante : une reconstruction rétrospective de la
situation après observation des conséquences produit un arc biaisé. Un arc
biaisé est traité comme PARTIEL.

#### Propriétés

| Identifiant | Propriété | Description |
|---|---|---|
| A-P1 | Complétude | Les cinq composantes sont documentées |
| A-P2 | Cohérence | L est logiquement dérivable de C et des intentions de D |
| A-P3 | Attribution | L'arc est rattaché à une décision unique |
| A-P4 | Intégrité temporelle | Les composantes respectent leur ordre chronologique |
| A-P5 | Non-régressivité | Un arc ne peut pas régresser vers un état antérieur |

---

### 3.3 Capital Décisionnel `[OBJ-3]`

#### Définition

> Ensemble des arcs décisionnels fermés et institutionnellement disponibles
> d'une organisation, pondéré par leur qualité, leur récence et leur
> pertinence situationnelle.

#### Formulation

```
DC(T) = Σᵢ [ ARC_i × Qualité(i) × Récence(i, T) × Pertinence(i, Ω) ]

Qualité(i)      Évaluée par une métrique définie dans la Reference Implementation
Récence(i, T)   Fonction décroissante depuis la fermeture (dépend du DC-HL du domaine)
Pertinence(i,Ω) Pertinence de l'arc i au regard du domaine Ω actuel
```

> **[ÉDITORIAL]** La formulation est intentionnellement paramétrique dans le
> Core. Les fonctions exactes (Qualité, Récence, Pertinence) sont définies dans
> la Reference Implementation. Décider si une note explicite sur ce choix de
> design est nécessaire ici ou si c'est suffisamment clair.

#### Conditions d'accumulation

1. L'arc est dans l'état FERMÉ ou VÉRIFIÉ
2. L'arc est institutionnellement stocké (hors mémoire individuelle)
3. L'arc est indexé et récupérable par situation
4. La qualité de l'arc dépasse le seuil minimum défini dans la Reference
   Implementation

#### Conditions de perte

1. Les porteurs d'arcs non institutionnalisés quittent l'organisation
2. Les systèmes de stockage deviennent inaccessibles

#### Conditions de dépréciation

1. Changement environnemental au-delà du seuil de similarité situationnelle
2. Accumulation d'arcs contradictoires sans réconciliation

#### Conditions de transmission

Le Capital Décisionnel est transmissible si et seulement si :

1. Les arcs sont institutionnellement stockés
2. Les arcs sont indexés et récupérables par un successeur
3. Le successeur accède au même système de stockage

#### Propriétés

| Identifiant | Propriété | Description |
|---|---|---|
| DC-P1 | Cumulativité | DC croît avec chaque arc fermé de qualité suffisante |
| DC-P2 | Institutionnalité | DC survit aux départs individuels si stocké hors mémoire personnelle |
| DC-P3 | Spécificité | DC est domaine-spécifique et contexte-spécifique |
| DC-P4 | Dépréciation | DC décroît selon la demi-vie du domaine |
| DC-P5 | Complémentarité | Deux arcs dans le même domaine produisent plus que leur somme |

---

## 4. Les Invariants

Huit propriétés vraies dans toute organisation, quelles que soient sa taille,
son industrie et son époque.

---

**INV-1 — Condition de fermeture**

```
DC_contribution(Arc_i) > 0  ↔  State(Arc_i) ∈ {FERMÉ, VÉRIFIÉ}
DC_contribution(Arc_i) = 0  ↔  State(Arc_i) ∈ {OUVERT-PRÉ, OUVERT-POST, PARTIEL}
```

*Conséquence :* toute décision non suivie d'une connexion explicite à ses
conséquences est décisionnellement stérile, quelle qu'ait été sa qualité.

---

**INV-2 — Institutionnalité**

```
DC_personnel(acteur) → 0   quand acteur quitte l'organisation
DC_institutionnel    = constant au départ d'un acteur individuel
```

*Conséquence :* l'expertise personnelle non institutionnalisée n'est pas du
Capital Décisionnel. Un CFO expérimenté dont les arcs ne sont pas documentés
n'est pas un stock de Capital Décisionnel — c'est un risque de perte.

---

**INV-3 — Monotonicité de l'accumulation**

```
∀ Arc_i | State(Arc_i) = FERMÉ ∧ Qualité(i) ≥ seuil_min :
DC(T ∪ {Arc_i}) ≥ DC(T)
```

*Conséquence :* l'ajout d'un arc fermé de qualité suffisante ne réduit jamais
le stock de DC, toutes choses égales par ailleurs.

---

**INV-4 — Dépréciation**

```
∀ Arc_i dans domaine D, ∃ DC-HL(D) > 0 :
DC_contribution(Arc_i, T + DC-HL(D)) < 0.5 × DC_contribution(Arc_i, T)
```

*Conséquence :* le Capital Décisionnel se déprécie sans maintenance active.
Les organisations à faible taux de fermeture voient leur stock se déprécier
même sans le consommer.

---

**INV-5 — Contrainte de précédent**

```
DC_value(Arc_i → Decision_j) > 0  ↔  Similarity(S_i, S_j) > θ_min
DC_value(Arc_i → Decision_j) ≤ 0  ↔  Similarity(S_i, S_j) ≤ θ_min
```

*Conséquence :* les meilleures pratiques génériques ne sont pas du Capital
Décisionnel. La valeur d'un arc est strictement contextuelle.

---

**INV-6 — Plancher de qualité**

```
∃ Qualité_min > 0 :
Qualité(Arc_i) < Qualité_min  →  DC_contribution(Arc_i) < 0
```

*Conséquence :* une fermeture superficielle est pire qu'un arc ouvert.
Elle crée un faux précédent qui dégrade la pertinence des décisions qui s'y réfèrent.

---

**INV-7 — Complémentarité**

```
DC({Arc_i, Arc_j} | Domain(i) = Domain(j))
> DC(Arc_i) + DC(Arc_j)
```

*Conséquence :* l'accumulation dans un domaine spécifique génère des
rendements croissants. La spécialisation du capital est plus rentable
que sa dispersion.

---

**INV-8 — Condition de récupération**

```
DC_effectif(T) = DC_stocké(T) × Taux_récupération(T)
Taux_récupération ∈ [0, 1]
```

*Conséquence :* un capital non récupérable produit les mêmes effets qu'un
capital inexistant. Fermer des arcs sans système d'indexation situationnelle
est une opération nulle.

---

## 5. Métamodèle

### 5.1 Entités

| Entité | Description |
|---|---|
| ENVIRONNEMENT | Ce qui est extérieur à l'organisation et non contrôlable |
| SITUATION | Portion de l'environnement perçue à un instant donné |
| ACTEUR | Décideur habilité dans un domaine |
| DÉCISION | OBJ-1 |
| ARC | OBJ-2 |
| CAPITAL | OBJ-3 |
| ORGANISATION | Entité institutionnelle détentrice du Capital |

### 5.2 Relations

| Relation | Source | Cible | Condition |
|---|---|---|---|
| génère | ENVIRONNEMENT | SITUATION | continu |
| perçoit | ACTEUR | SITUATION | à l'instant de la décision |
| déclenche | SITUATION | DÉCISION | nécessaire à l'existence de D |
| prend | ACTEUR | DÉCISION | habilitation requise |
| constitue | DÉCISION | ARC | 1 décision = 1 arc |
| contribue-à | ARC | CAPITAL | si et seulement si ARC = FERMÉ |
| détient | ORGANISATION | CAPITAL | le capital est institutionnel |
| influence | CAPITAL | DÉCISION | via récupération situationnelle |
| déprécie | TEMPS × ENVIRONNEMENT | CAPITAL | selon DC-HL du domaine |

### 5.3 La boucle fondamentale

```
DC(T)
  └→ meilleure pertinence de D(T)
       └→ meilleures conséquences C(T)
            └→ arc fermé de qualité ≥ seuil_min
                 └→ DC(T+1) > DC(T)
                      └→ [retour]
```

C'est la boucle de capitalisation. Elle est vertueuse si le Capital est
gouverné. Elle est brisée à chaque arc laissé ouvert.

### 5.4 Hiérarchie conceptuelle

```
AXIOMES
  Lois fondamentales de la théorie [AX-1, AX-2]
      ↓
PHÉNOMÈNE À EXPLIQUER
  Différentiel de pertinence décisionnelle entre organisations
      ↓
CONSTRUIT EXPLICATIF
  Capital Décisionnel [OBJ-3]
      ↓
MÉCANISME DE PRODUCTION
  Arc Décisionnel [OBJ-2]
      ↓
UNITÉ
  Décision [OBJ-1]
      ↓
IMPLÉMENTATION
  Instrument qui structure, ferme et capitalise les arcs
```

---

## 6. Périmètre

### 6.1 Ce que ce document contient

Ce document contient et fige :

- Les deux axiomes fondateurs (`AX-1`, `AX-2`) et leur corollaire
- Les définitions formelles des trois objets (`OBJ-1`, `OBJ-2`, `OBJ-3`)
- Les huit invariants (`INV-1` à `INV-8`)
- L'ontologie complète (entités, relations, boucle fondamentale)

### 6.2 Ce que ce document ne contient pas

Les éléments suivants sont volontairement absents du Core. Ils figurent dans
la *Reference Implementation* (document séparé) :

- Les métriques et leurs formules de calcul (ACR, AQS, DCD, DC-HL, SCI,
  LY, DRR, CTS)
- Les seuils numériques (qualité minimale, taux de similarité, etc.)
- Le modèle de maturité (niveaux L-0 à L-5)
- Les algorithmes d'indexation situationnelle
- Les règles d'implémentation spécifiques à Pepperyn

Cette séparation est intentionnelle : les lois doivent survivre à plusieurs
implémentations. Les instruments de mesure et les seuils opérationnels sont
des choix d'implémentation, non des vérités théoriques.

> **[ÉDITORIAL]** Décider si une note sur la relation entre ce Core et la
> littérature académique existante (Walsh & Ungson 1991, Argyris & Schön 1978,
> Mintzberg 1978) doit figurer ici en annexe ou exclusivement dans
> `/research/literature_review.md`. Recommandation : annexe légère dans le Core
> (3-4 paragraphes), développement complet dans research/.

---

## 7. Règles de versionnement

Ce document est versionnée selon les règles définies dans
`/governance/VERSIONING.md`.

Résumé :

| Type de changement | Version déclenchée |
|---|---|
| Correction typographique ou d'ambiguïté | Patch (v1.0.x) |
| Ajout d'une métrique ou raffinement d'une définition sans modifier axiomes/invariants | Mineure (v1.x.0) |
| Modification d'un axiome, d'un invariant ou d'un objet | Majeure (v2.0.0) |

**Le déclencheur légitime d'une version majeure est un résultat empirique
qui réfute un invariant — non un inconfort d'implémentation.**

> **[ÉDITORIAL]** Décider si le document final doit inclure une section
> "Remerciements" ou "Historique intellectuel" qui trace la genèse de la
> théorie. Utile pour la crédibilité académique ; inutile pour le praticien.

---

## Annexe A — Index des identifiants

| Identifiant | Type | Description |
|---|---|---|
| AX-1 | Axiome | Loi de l'agentivité |
| AX-2 | Axiome | Loi de l'unité |
| OBJ-1 | Objet | Décision |
| OBJ-2 | Objet | Arc Décisionnel |
| OBJ-3 | Objet | Capital Décisionnel |
| D-P1 à D-P6 | Propriétés | Propriétés de la Décision |
| A-P1 à A-P5 | Propriétés | Propriétés de l'Arc Décisionnel |
| DC-P1 à DC-P5 | Propriétés | Propriétés du Capital Décisionnel |
| INV-1 à INV-8 | Invariants | Lois internes du modèle |

---

## Annexe B — Arbitrages éditoriaux ouverts

Liste consolidée des décisions éditoriales à prendre avant la version finale :

1. **Langue du résumé** : français, anglais ou bilingue ?
2. **Littérature académique** : annexe dans le Core ou exclusivement dans
   `/research/` ?
3. **Acronyme SDECL** : maintenir en anglais ou traduire en français ?
4. **Section praticien vs académique** : le ton général doit-il être ajusté
   selon le public cible principal identifié ?
5. **Remerciements / historique intellectuel** : inclure ou pas ?
6. **Formulation paramétrique de DC(T)** : noter explicitement que les
   fonctions sont dans la Reference Implementation, ou laisser implicite ?

---

*— Fin du manuscrit de travail DCT_Core_v1.0 —*
