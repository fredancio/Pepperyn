# Domaine Commercial — Arcs décisionnels de référence

**Usage :** Exemples et archétypes pour le domaine commercial en contexte PME  
**Dernière mise à jour :** 2026-07-18

---

## Introduction

Le domaine commercial produit des décisions récurrentes, souvent sous pression
de temps et d'information incomplète. C'est un domaine à haute valeur de
Capital Décisionnel : les patterns se répètent, les erreurs se reproduisent,
et l'apprentissage accumulé est directement monétisable.

---

## Archétypes d'arcs commerciaux

### ARCH-COM-01 — Qualification d'une opportunité atypique

**Situation type :** Un prospect hors cible idéale exprime un intérêt fort.
La décision : investir ou décliner ?

**Questions structurantes pour la Situation :**
- Quelle est la taille de l'opportunité vs le coût d'acquisition estimé ?
- En quoi ce prospect s'écarte-t-il du profil cible ?
- L'écart est-il structurel (on ne peut pas bien les servir) ou conjoncturel ?

**Erreurs classiques documentées par des arcs :**
- Accepter par peur de manquer une opportunité sans poser le coût réel
- Refuser par rigidité de critères sans analyser le cas particulier
- Ne pas documenter le raisonnement → même décision refaite 18 mois plus tard

**Indicateur de Capital dans ce domaine :**
DRR élevé sur ce type de décision = l'équipe commerciale consulte les arcs
avant de qualifier. Signal de maturité L-3.

---

### ARCH-COM-02 — Réponse à un appel d'offres

**Situation type :** Décision de répondre (ou non) à un appel d'offres public
ou privé avec un taux de conversion estimé incertain.

**Questions structurantes pour la Situation :**
- Quel est le coût de réponse (temps, ressources) ?
- Quelle est la probabilité estimée de succès, et sur quelle base ?
- La victoire est-elle désirable (client, marges, références) ?

**Apprentissages fréquents dans ce type d'arc :**
- Le "non-dit" dans le cahier des charges révèle souvent un fournisseur
  sortant favorisé
- Les appels d'offres à fort taux de lot unique sont moins risqués
  que les multi-lots

---

### ARCH-COM-03 — Décision de remise exceptionnelle

**Situation type :** Un client stratégique négocie une remise hors grille
tarifaire. La décision : accorder ou tenir la ligne ?

**Questions structurantes pour la Décision :**
- Quelle est la valeur totale du compte sur 3 ans (LTV) ?
- Quel est le précédent créé si accordé ? Suivi par d'autres clients ?
- La remise est-elle structurelle (prix trop élevé) ou contextuelle (pression ponctuelle) ?

**Invariant le plus souvent violé ici :** INV-2 (institutionnalité) —
la remise est accordée par le commercial sans arbitrage direction,
donc non tracée. Elle crée un précédent informel invisible.

---

### ARCH-COM-04 — Perte d'un client clé

**Situation type :** Un client représentant ≥ 10% du CA annonce sa résiliation.
La décision : réagir (et comment) ou accepter ?

**Questions structurantes :**
- Le départ est-il lié à un problème produit/service identifiable ?
- Est-il lié à un changement de décideur chez le client ?
- La tentative de rétention a-t-elle un coût acceptable vs le CA en jeu ?

**Valeur de l'arc pour les arcs futurs :**
Cet archétype est le plus riche en apprentissages : il révèle les vraies
raisons d'insatisfaction, souvent plus utiles que les enquêtes de satisfaction.

---

## Métriques clés du domaine commercial

| Métrique | Ce qu'elle révèle en commercial                     |
|----------|-----------------------------------------------------|
| ACR      | Proportion de décisions documentées jusqu'aux résultats |
| AQS      | Qualité du raisonnement commercial moyen            |
| DRR      | Utilisation réelle du Capital par les commerciaux   |
| LY       | Est-ce que chaque nouvelle décision s'appuie sur les précédentes ? |
| SCI      | Quels archétypes manquent encore dans le stock ?    |

---

## Capital Décisionnel à risque en commercial

**Risques de dépréciation rapide (INV-4) :**
- Changements de marché ou de pricing concurrents : les arcs > 24 mois
  sur la stratégie tarifaire peuvent être obsolètes
- Turnover commercial élevé : sans institutionnalisation (INV-2),
  le Capital part avec le commercial

**Signal d'alerte :** ACR < 0.3 en commercial = les décisions se prennent
mais ne se documentent jamais jusqu'aux conséquences. Capital décisionnel nul.
