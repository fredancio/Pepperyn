# Hypothèses empiriques — Decision Capital Theory

**Statut :** En attente de validation empirique  
**Dernière mise à jour :** 2026-07-18

---

## Introduction

La DCT génère des prédictions testables. Ce document liste les hypothèses
prioritaires, leur rattachement aux invariants du Core, et les conditions
minimales pour les tester.

**Ordre de priorité pour la validation empirique :**
H3 → H2 → H1 (par ordre de testabilité et de délai de résultat)

---

## H1 — Taux de fermeture et qualité décisionnelle

**Énoncé**  
Les organisations qui ferment davantage d'arcs décisionnels (ACR élevé)
prennent des décisions de meilleure pertinence dans le temps que les
organisations comparables à ACR faible.

**Rattachement théorique**  
INV-1 (condition de fermeture), INV-3 (monotonicité), INV-7 (complémentarité)

**Variables**
- Variable indépendante : Arc Closure Rate (ACR) moyen sur 12 mois
- Variable dépendante : Pertinence décisionnelle (ratio conséquences
  correspondant aux intentions / intentions totales)

**Design de validation**  
Étude longitudinale sur 24-36 mois. Comparer deux cohortes d'organisations
comparables (même secteur, taille similaire) avec ACR divergents.

**Statut :** En attente — délai de résultat : 24-36 mois  
**Priorité :** Faible (délai long, mesure de la pertinence complexe à opérationnaliser)

---

## H2 — Réutilisation des arcs et amélioration décisionnelle

**Énoncé**  
Les décisions prises en référence explicite à un arc antérieur dans une
situation similaire sont plus pertinentes que les décisions équivalentes
prises sans référence à un arc.

**Rattachement théorique**  
INV-5 (contrainte de précédent), INV-7 (complémentarité), INV-8 (récupération)

**Variables**
- Variable indépendante : Decision Reuse Rate (DRR) — décisions avec
  référence explicite à un arc antérieur
- Variable dépendante : Learning Yield (LY) — ratio de pertinence entre
  la décision référençant un arc et la décision d'origine

**Design de validation**  
Comparer la pertinence des décisions avec et sans référence d'arc, à
situation similaire contrôlée, sur 12 mois.

**Statut :** En attente — délai de résultat : 12-18 mois  
**Priorité :** Moyenne (mesurable dès que Pepperyn accumule des arcs réels)

---

## H3 — Documentation structurée et continuité à la succession

**Énoncé**  
Lors du départ d'un décideur clé, la pertinence des décisions dans son
domaine baisse significativement moins dans les organisations disposant
d'un Capital Décisionnel documenté que dans celles dont le capital est
exclusivement personnel.

**Rattachement théorique**  
INV-2 (institutionnalité), DC-P2 (transférabilité)

**Variables**
- Variable indépendante : stock de Capital Décisionnel documenté dans le
  domaine du décideur sortant (DCD, arcs fermés disponibles)
- Variable dépendante : Capital Transmission Score (CTS) — ratio de
  pertinence décisionnelle dans les 24 mois post-départ vs 24 mois pré-départ

**Design de validation**  
Étude d'événements naturels : observer les successions chez des clients
Pepperyn, comparer CTS selon le niveau de documentation préexistant.

**Seuil de réfutation**  
Si CTS n'est pas significativement différent entre organisations à fort et
faible Capital Décisionnel documenté (après contrôle des variables de
confusion), INV-2 doit être réexaminé.

**Statut :** En attente — délai de résultat : événement-dépendant (à lancer dès première succession)  
**Priorité :** Haute (premier test à conduire, le plus immédiatement actionnable et commercial)

---

## Conditions générales de validation

**Ce qui constitue un résultat positif**  
Un résultat positif pour une hypothèse est une observation cohérente avec
la prédiction sur au moins 3 cas distincts dans des secteurs différents.

**Ce qui constitue un résultat réfutant**  
Un résultat négatif systématique (≥ 3 cas contra-prédiction) est un signal
de révision. Selon la gravité :
- Si le résultat contredit un invariant → révision majeure (v2.0)
- Si le résultat contredit une métrique → révision mineure (v1.x)
- Si le résultat indique un problème de mesure → révision de la
  Reference Implementation uniquement

**Ce qui ne constitue pas un résultat réfutant**  
Un résultat négatif isolé, un problème de vocabulaire produit (ex. "arc"
non compris), ou une faible adoption d'une fonctionnalité. Ces signaux
indiquent un problème d'implémentation, non de théorie.
