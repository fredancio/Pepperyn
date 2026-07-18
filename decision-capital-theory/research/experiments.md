# Protocoles expérimentaux — Decision Capital Theory

**Statut :** Templates en attente de déclenchement  
**Dernière mise à jour :** 2026-07-18

---

## Introduction

Ce document contient les protocoles d'expérimentation pour chaque hypothèse.
Un protocole ne peut être considéré "actif" que lorsqu'un cas réel l'instancie.
Ces templates sont conçus pour guider l'observation sans la biaiser.

---

## EXP-H3-001 — Transmission du Capital Décisionnel à la succession

**Hypothèse testée :** H3  
**Statut :** TEMPLATE — en attente d'un événement déclencheur

### Conditions de déclenchement

Ce protocole s'active lorsque l'une des conditions suivantes est remplie :
- Départ d'un décideur ayant ≥ 1 an d'ancienneté chez un client Pepperyn
- Changement de direction dans un domaine fonctionnel (DAF, DRH, Directeur commercial)
- Cession ou transmission d'entreprise

### Variables à mesurer

**Avant l'événement (T0 = date d'annonce ou de départ effectif)**
- Stock d'arcs fermés (ACR) dans le domaine concerné
- AQS moyen des arcs du domaine
- Nombre de décisions référencées (DRR baseline)
- Inventaire qualitatif : quelles catégories de décisions sont documentées ?

**Après l'événement (T+6, T+12, T+24 mois)**
- ACR dans le même domaine
- AQS moyen post-transition
- Nombre d'arcs réutilisant le stock existant
- Observation qualitative : le successeur a-t-il consulté les arcs avant de décider ?

### Collecte des données

Journal d'observation à remplir :
- Quel était le niveau de Capital Décisionnel documenté au moment du départ ?
- Le successeur a-t-il été informé de l'existence des arcs ?
- Quelles décisions le successeur a-t-il répété (sans accès aux arcs) ?
- Quelles décisions ont bénéficié d'un arc antérieur ?

### Seuil de résultat

- CTS ≥ 0.85 → résultat cohérent avec H3
- CTS < 0.70 → signal de réfutation à investiguer
- 0.70 ≤ CTS < 0.85 → résultat ambivalent, noter les facteurs de confusion

### Facteurs de confusion à contrôler

- Qualité du successeur (expérience sectorielle)
- Durée de la période de chevauchement (overlap)
- Stabilité de l'environnement sectoriel pendant la période de transition

---

## EXP-H2-001 — Réutilisation et pertinence décisionnelle

**Hypothèse testée :** H2  
**Statut :** TEMPLATE — à activer dès 20 arcs fermés dans un domaine

### Conditions de déclenchement

- Un domaine atteint ≥ 20 arcs fermés chez un client
- Deux décisions comparables peuvent être identifiées : l'une avec référence
  explicite à un arc antérieur, l'autre sans

### Protocole de comparaison

Pour chaque paire de décisions identifiées (même type de situation, même domaine) :

**Décision A (avec référence d'arc)**
- Identifier l'arc antérieur référencé
- Mesurer l'AQS de la décision A (scoring S+D+C+L)
- Noter la similarité de la situation (0-10)

**Décision B (sans référence d'arc)**
- Identifier la décision comparable
- Mesurer l'AQS de la décision B (scoring S+D+C+L)
- Vérifier qu'aucun arc n'était disponible, ou que l'arc existant n'a pas été consulté

**Calcul du Learning Yield (LY)**
LY = AQS(A) / AQS(arc_référencé)

- LY > 1.0 → la réutilisation a produit une décision meilleure que l'original
- LY = 1.0 → qualité identique (apprentissage neutre)
- LY < 1.0 → la réutilisation n'a pas amélioré la pertinence

### Accumulation de résultats

- ≥ 5 paires avec LY > 1.0 → signal positif pour H2
- ≥ 3 paires avec LY < 1.0 → signal d'alerte à investiguer

---

## EXP-H1-001 — ACR et pertinence décisionnelle longitudinale

**Hypothèse testée :** H1  
**Statut :** TEMPLATE — à activer après 24 mois de données

### Conditions de déclenchement

- Disponibilité de ≥ 2 clients avec ACR divergent (l'un > 0.7, l'autre < 0.3)
  dans le même secteur depuis ≥ 24 mois
- Possibilité de mesurer la pertinence décisionnelle en output (croissance,
  rentabilité, taux de survie des initiatives)

### Note méthodologique

Cette hypothèse est la plus difficile à tester en isolation, car :
- Le délai de résultat est long (24-36 mois)
- La mesure de la pertinence en output est fortement confondue par des
  variables externes (marché, conjoncture, équipe)
- L'ACR est en partie endogène à la qualité managériale initiale

**Recommandation :** traiter H1 comme une validation de second ordre,
après que H2 et H3 auront apporté des résultats plus directs.

---

## Journal des expérimentations actives

| Exp. ID     | Hypothèse | Client (anonymisé) | Date déclenchement | Statut    |
|-------------|-----------|--------------------|--------------------|-----------|
| *En attente*| —         | —                  | —                  | —         |

---

## Principe de documentation des résultats

Chaque résultat observé doit être documenté dans `observations.md` avec :
1. L'identifiant de l'expérimentation (EXP-Hx-NNN)
2. La date d'observation
3. Le résultat brut (métriques)
4. L'interprétation (cohérent / ambivalent / réfutant)
5. Les facteurs de confusion identifiés
6. L'implication théorique éventuelle
