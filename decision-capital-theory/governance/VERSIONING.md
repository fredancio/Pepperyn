# Règles de versionnage — Decision Capital Theory

**Version de ce document :** 1.0  
**Dernière mise à jour :** 2026-07-18

---

## Principe général

La DCT est versionnée comme un langage formel, pas comme un logiciel.
La stabilité est une valeur en soi : une modification sans preuve empirique
est une régression, même si elle paraît améliorer la formulation.

---

## Les deux conditions de gel

### Gel épistémique (permanent)

Les axiomes et invariants sont figés jusqu'à preuve empirique contraire.
"Meilleure idée" n'est pas une raison de modifier. La raison légitime
est un résultat d'observation systématique contradisant la prédiction de la théorie.

### Gel temporel (provisoire)

Aucun concept ne sera ajouté avant janvier 2027 (6 mois d'observation).
Ce gel s'applique même si une idée paraît évidente ou nécessaire.
L'objectif est de laisser la pratique révéler les lacunes réelles plutôt
que de les anticiper de façon théorique.

---

## Niveaux de versionnage

### Patch — v1.0.x

**Ce qui déclenche un patch :**
- Correction d'une faute de frappe ou d'orthographe dans la spécification
- Clarification d'une ambiguïté rédactionnelle sans changement de sens
- Reformulation d'une définition pour la rendre plus précise, sans changer
  ce qu'elle désigne

**Ce qui ne déclenche PAS un patch :**
- Toute modification qui change ce qu'un invariant interdit ou autorise
- Toute modification qui change la liste des propriétés d'un objet

**Processus :** Note dans CHANGELOG.md avec la correction explicite.
Pas de délibération formelle requise.

---

### Minor — v1.x.0

**Ce qui déclenche une révision mineure :**
- Ajout d'une nouvelle métrique (M-9, M-10, etc.)
- Raffinement de la définition opérationnelle d'une métrique existante
- Ajout d'un état au modèle de maturité
- Ajout d'un exemple illustratif dans la spécification

**Ce qui ne déclenche PAS une révision mineure :**
- Changement d'un axiome, d'un invariant, ou d'un objet fondamental
- Tout ce qui modifie la frontière du Core

**Processus :** Une révision mineure nécessite :
1. Un constat empirique justifiant l'ajout (observation dans `observations.md`)
2. Une entrée de changelog documentant la raison
3. Pas de consultation formelle requise en phase privée

---

### Major — v2.0.0

**Ce qui déclenche une révision majeure :**
- Modification d'un axiome (AX-1 ou AX-2)
- Modification d'un invariant (INV-1 à INV-8)
- Modification d'un objet fondamental (OBJ-1, OBJ-2, OBJ-3)
- Suppression d'un concept existant

**Condition nécessaire :**
Une révision majeure ne peut pas être déclenchée par une intuition ou un
argument théorique seul. Elle requiert :
1. Au minimum 3 observations empiriques contradisant la théorie
2. Élimination des alternatives d'explication (problème de mesure,
   problème d'implémentation, facteur de confusion)
3. Délibération formelle documentée dans governance/

**La règle d'or :** Si le doute persiste, ne pas modifier.
La stabilité d'une théorie est une valeur indépendante de sa perfectibilité.

---

## Ce qui n'entre jamais dans le versionnage Core

Les éléments suivants sont hors périmètre du versionnage DCT Core.
Ils relèvent de la Reference Implementation :

- Seuils opérationnels des métriques (ex. "ACR > 0.7 = bon")
- Algorithmes de calcul du Capital Décisionnel
- Fréquences recommandées de fermeture des arcs
- Formats de documentation des arcs
- Interfaces produit

Ces éléments évoluent librement selon les apprentissages produit, sans
impacter le versionnage de la théorie.

---

## Value Traceability — garde-fou avant tout ajout

Avant d'ajouter un concept à la DCT (nouveau terme, nouvelle métrique,
nouvel invariant), répondre aux quatre questions suivantes :

1. Quelle fonctionnalité Pepperyn ce concept permet-il d'améliorer ?
2. Quel problème utilisateur résout-il ?
3. Quel avantage concurrentiel crée-t-il ?
4. Que perdrait-on si ce concept n'existait pas ?

Si l'une des réponses est vague ou purement spéculative, le concept
n'est pas mûr. Le reporter — pas l'ajouter.

**Ce test s'applique avant toute révision, y compris les révisions mineures.**
Son rôle n'est pas d'empêcher l'évolution de la théorie, mais de s'assurer
que chaque évolution est tirée par le terrain, pas par l'élégance théorique.

**Règle de déclenchement de nouveaux documents :**
Tout nouveau document dans cette architecture doit être déclenché par un
besoin rencontré pendant le développement de Pepperyn ou par une observation
issue d'utilisateurs réels. La documentation préventive est suspendue.

---

## Autorité de versionnage

En phase privée (2026-2027) : F. Anciaux, auteur de la théorie.

La question de la gouvernance ouverte (comité, communauté, peer review)
sera posée lors de la décision de publication, non avant.
