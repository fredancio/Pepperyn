# Journal d'observations — Decision Capital Theory

**Statut :** Vide — en attente des premières données produit  
**Dernière mise à jour :** 2026-07-18  
**Horizon d'observation :** 6 mois (juillet 2026 → janvier 2027)

---

## Introduction

Ce journal recueille les observations empiriques issues de l'utilisation
réelle de Pepperyn. Il ne vise pas à confirmer la DCT, mais à collecter des
faits bruts qui permettront ensuite d'évaluer les hypothèses.

**Principe directeur :** observer d'abord, interpréter ensuite.  
Ne pas chercher à faire correspondre les observations à la théorie.
Noter les anomalies avec autant de soin que les confirmations.

---

## Template d'entrée d'observation

```
### OBS-[NNN] — [Titre court]

**Date :** AAAA-MM-JJ  
**Source :** Produit / Client (anonymisé) / Entretien  
**Expérimentation associée :** EXP-Hx-NNN (ou "aucune")

**Observation brute :**
[Description factuelle de ce qui a été observé, sans interprétation]

**Métriques associées :**
- ACR :
- AQS moyen :
- DRR :
- Autre :

**Interprétation initiale :**
[Cohérent / Ambivalent / Contre-intuitif / Réfutant]

**Hypothèse concernée :**
[H1 / H2 / H3 / Aucune]

**Questions ouvertes :**
[Ce que cette observation ne permet pas de conclure]
```

---

## Observations enregistrées

*Aucune observation à ce jour. Première entrée attendue dès déploiement
des fonctionnalités Arc et Capital dans Pepperyn.*

---

## Signaux de déclenchement à surveiller

Les événements suivants doivent être notés immédiatement dans ce journal :

**Déclencheurs H3 (succession)**
- Tout départ d'utilisateur avec rôle décisionnel
- Toute transmission d'entreprise client

**Déclencheurs H2 (réutilisation)**
- Première décision explicitement référençant un arc antérieur
- Premier commentaire utilisateur mentionnant "j'ai consulté un arc"
- Refus d'utiliser un arc existant (et raison fournie)

**Déclencheurs H1 (ACR et pertinence)**
- Premier client atteignant ACR > 0.7 sur 12 mois
- Premier écart ACR > 0.4 entre deux clients comparables

**Anomalies à noter absolument**
- Arc fermé mais apprentissage non utilisé
- Capital Décisionnel élevé mais décisions répétées de mauvaise qualité
- Arc ouvert mais jamais fermé après 12 mois (identifier la cause)

---

## Synthèses intermédiaires

Prévoir une synthèse à chaque jalons :

| Jalon       | Date cible     | Statut     |
|-------------|----------------|------------|
| 6 semaines  | 2026-09-01     | À faire    |
| 3 mois      | 2026-10-18     | À faire    |
| 6 mois      | 2027-01-18     | À faire    |

La synthèse à 6 mois est le déclencheur de la rédaction de la
Reference Implementation.
