# DCT → Pepperyn Mapping

**Objet :** Tableau de correspondance entre les éléments de la Decision Capital Theory
et les fonctionnalités de Pepperyn.

**Usage :** Ce document est le lien entre la théorie et la roadmap produit.
Il répond à une question simple : "Qu'est-ce que Pepperyn implémente de la DCT,
et qu'est-ce qui reste à construire ?"

**Dernière mise à jour :** 2026-07-18  
**Prochaine révision :** à chaque évolution significative du produit

---

## Règle de lecture

Ce mapping n'est pas un cahier des charges. Il ne dit pas ce que Pepperyn
**doit** faire. Il dit ce que Pepperyn **fait** par rapport à la DCT.
Les gaps identifiés ici deviennent des candidats à la roadmap — ils ne
s'imposent pas à elle.

---

## Mapping des objets fondamentaux (OBJ)

| Élément DCT                    | Définition DCT (résumé)                          | Fonction Pepperyn                             | État        |
|-------------------------------|--------------------------------------------------|-----------------------------------------------|-------------|
| OBJ-1 Décision                | Acte de choix institutionnel — unique, alternatif, contextuel, conséquentiel | Analyse et structuration d'une décision        | ✅ Partiel  |
| OBJ-2 Arc Décisionnel         | Structure {S, D, E, C, L} — 5 états             | Cycle complet S→D→C→L                         | 🚧 En développement |
| OBJ-3 Capital Décisionnel     | DC(T) = Σ [ARC × Qualité × Récence × Pertinence] | Agrégation et valorisation du stock d'arcs    | ❌ Non implémenté |

---

## Mapping des composantes de l'Arc (OBJ-2)

| Composante   | Définition DCT                                  | Implémentation Pepperyn          | État        |
|--------------|-------------------------------------------------|----------------------------------|-------------|
| S — Situation | Contexte, signal déclencheur, enjeu, contraintes | Upload de document + extraction contexte | ✅ Partiel |
| D — Décision  | Choix retenu, alternatives écartées, raisonnement | À développer                    | 🚧 Prévu   |
| E — Exécution | Plan, écarts d'exécution                        | Non implémenté                   | ❌          |
| C — Conséquences | Résultats observés, écarts conséquences/intentions | Non implémenté                | ❌          |
| L — Learning  | Apprentissages, reformulation des règles         | Non implémenté                   | ❌          |

---

## Mapping des invariants (INV)

| Invariant            | Implication produit                                           | Implémenté ? |
|---------------------|---------------------------------------------------------------|-------------|
| INV-1 Fermeture      | Pepperyn doit rendre possible la fermeture d'un arc (C+L remplis) | ❌         |
| INV-2 Institutionnalité | Traçabilité du décideur et du processus décisionnel       | 🚧 Partiel |
| INV-3 Monotonicité   | Un arc fermé ne peut pas régresser — états non-régressifs    | ❌          |
| INV-4 Dépréciation   | Signaler les arcs anciens comme moins pertinents              | ❌          |
| INV-5 Précédent      | Relier les nouvelles décisions aux arcs antérieurs similaires | ❌          |
| INV-6 Plancher qualité | Bloquer les arcs trop incomplets pour contribuer au capital | ❌         |
| INV-7 Complémentarité | Visualiser les interactions entre arcs d'un même domaine    | ❌          |
| INV-8 Récupération   | Permettre l'extraction du capital après départ d'un décideur | ❌          |

---

## Mapping des métriques (M)

| Métrique | Signification                          | Calculable dans Pepperyn ? | État |
|----------|----------------------------------------|---------------------------|------|
| M-1 ACR  | Proportion d'arcs fermés               | Oui (count)               | 🚧   |
| M-2 AQS  | Score qualité de l'arc (S+D+C+L)       | Oui (si scoring implémenté) | 🚧 |
| M-3 DCD  | Densité d'arcs par domaine / an        | Oui (count + filtre)      | 🚧   |
| M-4 DC-HL | Demi-vie par domaine                  | Non (nécessite séries temporelles) | ❌ |
| M-5 SCI  | Couverture des archétypes              | Non (nécessite référentiel d'archétypes) | ❌ |
| M-6 LY   | Ratio pertinence arcs successifs       | Non (nécessite scoring + historique) | ❌ |
| M-7 DRR  | Taux de réutilisation d'arcs           | Non (nécessite liens entre arcs) | ❌ |
| M-8 CTS  | Score de transmission post-départ      | Non (nécessite comparaison temporelle) | ❌ |

---

## Synthèse : état de l'implémentation

**Ce que Pepperyn fait déjà (✅ partiel)**
- Capturer le contexte d'une décision (S)
- Structurer une analyse décisionnelle
- Tracer l'identité du décideur (partiel)

**Ce qui est en cours de développement (🚧)**
- Le cycle complet de l'arc (D → E → C → L)
- Les métriques de base (ACR, AQS, DCD)

**Ce qui n'existe pas encore (❌)**
- La fermeture d'arc (INV-1) — manque C et L
- Le Capital Décisionnel comme agrégat calculé (OBJ-3)
- Les métriques avancées (LY, DRR, CTS, DC-HL, SCI)
- Les liens entre arcs (INV-5, INV-7)
- La signalisation de dépréciation (INV-4)

---

## Priorité d'implémentation (lecture DCT)

Si l'on ordonne par valeur théorique décroissante pour un premier utilisateur :

1. **Fermeture d'arc (INV-1)** — sans C+L, il n'y a pas de Capital
2. **ACR et AQS (M-1, M-2)** — premiers indicateurs visibles pour l'utilisateur
3. **Liens entre arcs (INV-5)** — permet la réutilisation (H2)
4. **Score CTS (M-8)** — cas de succession, valeur commerciale directe (H3)

*Note : Cette priorité est une lecture théorique. La roadmap produit reste
souveraine — elle peut choisir un autre ordre pour des raisons d'adoption,
de faisabilité technique, ou de retour client.*

---

## Boussole

> "Chaque heure passée sur la DCT doit rendre Pepperyn meilleur
> ou plus difficile à copier."

Ce document existe pour s'assurer que la théorie sert le produit,
et non l'inverse.
