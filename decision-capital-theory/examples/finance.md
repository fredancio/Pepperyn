# Domaine Finance — Arcs décisionnels de référence

**Usage :** Exemples et archétypes pour le domaine finance/gestion en contexte PME  
**Dernière mise à jour :** 2026-07-18

---

## Introduction

Le domaine financier est le plus naturellement documenté — les décisions
laissent des traces comptables. Mais la trace comptable n'est pas un arc.
Elle enregistre ce qui s'est passé, pas pourquoi la décision a été prise
ni ce qu'elle a appris. Le Capital Décisionnel en finance est dans le
raisonnement, pas dans les chiffres.

---

## Archétypes d'arcs financiers

### ARCH-FIN-01 — Décision de financement d'un investissement

**Situation type :** Besoin d'un actif significatif (machine, immobilier,
logiciel structurant). La décision : autofinancement, crédit, crédit-bail,
ou report ?

**Questions structurantes pour la Décision :**
- Quel est l'horizon de retour sur investissement réaliste ?
- La trésorerie disponible permet-elle l'autofinancement sans risque de
  liquidité sur 18 mois ?
- Le crédit-bail préserve-t-il la flexibilité de sortie ?

**Voir aussi :** ARC-001 (example_arc_01.md) — cas complet documenté

---

### ARCH-FIN-02 — Décision de politique de prix en réponse à une pression marge

**Situation type :** Les marges baissent. La décision : augmenter les prix,
réduire les coûts, réorienter le mix produit/service, ou accepter la baisse ?

**Complexité de cet arc :**
C'est une décision composite : elle intègre des sous-décisions (sur quel
segment augmenter ? avec quel timing ? comment communiquer ?). Chaque
sous-décision mérite son propre arc ou une trace dans C du présent arc.

**Erreur classique dans la documentation :**
Fermer cet arc avec "on a augmenté les prix de 5%" sans documenter
les conséquences sur le volume et le mix client 12 mois plus tard.
→ INV-1 violé : l'arc est déclaré fermé sans que les conséquences
soient connues.

---

### ARCH-FIN-03 — Décision de constitution de provisions / réserves

**Situation type :** Une période de forte croissance génère des profits
inhabituels. La décision : distribuer, réinvestir, ou provisionner ?

**Questions structurantes :**
- Quelle est la probabilité d'un retournement de cycle dans 18-24 mois ?
- Quels investissements sont en attente de financement ?
- Quelle est la position des associés sur la distribution vs la capitalisation ?

**Valeur de l'arc en cas de récession :** un arc documenté sur une
décision de provision permet au successeur de comprendre pourquoi
la réserve existe — et de ne pas la consommer pour de mauvaises raisons.

---

### ARCH-FIN-04 — Gestion d'un retard client significatif

**Situation type :** Un client majeur accumule 90+ jours de retard.
La décision : relancer, mettre en demeure, suspendre les livraisons,
ou trouver un arrangement ?

**Archétype à haute valeur de réutilisation (DRR attendu élevé) :**
Ce type de situation se répète. Un arc documenté révèle : quel profil de
client a tendance à se régulariser ? Quel a tendance à basculer en
contentieux ? La relance change-t-elle le comportement ?

---

## Métriques clés du domaine finance

| Métrique | Ce qu'elle révèle en finance                        |
|----------|-----------------------------------------------------|
| ACR      | Proportion de décisions financières documentées jusqu'aux conséquences réelles (12-24 mois) |
| DC-HL    | Durée de pertinence des arcs financiers (plus courte en environnement de taux volatils) |
| AQS      | Qualité du raisonnement financier — le C (conséquences) est souvent sous-documenté |
| CTS      | Pertinence des décisions financières après changement de DAF |

---

## Note sur la dépréciation (INV-4) en finance

Le Capital Décisionnel financier se déprécie selon deux facteurs distincts :

1. **Dépréciation temporelle normale** : une décision de financement
   prise en contexte de taux bas est peu pertinente en contexte de taux
   élevés. La DC-HL du domaine finance est en général 18-36 mois.

2. **Dépréciation par changement réglementaire** : une modification
   fiscale ou comptable peut rendre un arc non seulement obsolète mais
   trompeur. Identifier et archiver les arcs affectés est une pratique
   de bonne gouvernance.

**Seuil de pertinence recommandé (Reference Implementation à définir) :**
Un arc financier de plus de 36 mois doit être évalué avant d'être
référencé dans un arc nouveau.
