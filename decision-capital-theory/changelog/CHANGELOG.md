# CHANGELOG — Decision Capital Theory

Format : [vX.Y.Z] — AAAA-MM-JJ

---

## [1.0.0] — 2026-07-18

### Statut : FIGÉ

**Première version formelle de la Decision Capital Theory.**

Contenu de la v1.0.0 :

**Axiomes**
- AX-1 : Loi de l'agentivité
- AX-2 : Loi de l'unité

**Objets**
- OBJ-1 : Décision — 6 propriétés constitutives
- OBJ-2 : Arc Décisionnel — structure {S, D, E, C, L}, 5 états, 4 conditions
  de fermeture
- OBJ-3 : Capital Décisionnel — formulation DC(T), 3 propriétés

**Invariants**
- INV-1 : Fermeture
- INV-2 : Institutionnalité
- INV-3 : Monotonicité
- INV-4 : Dépréciation
- INV-5 : Précédent
- INV-6 : Plancher qualité
- INV-7 : Complémentarité
- INV-8 : Récupération

**Métriques**
- M-1 ACR (Arc Closure Rate)
- M-2 AQS (Arc Quality Score)
- M-3 DCD (Decision Capital Density)
- M-4 DC-HL (Decision Capital Half-Life)
- M-5 SCI (Situational Coverage Index)
- M-6 LY (Learning Yield)
- M-7 DRR (Decision Reuse Rate)
- M-8 CTS (Capital Transmission Score)

**Modèle de maturité**
- L-0 à L-5 (éphémères → apprentissage compoundé)

**Règles de versionnage**
- Patch (v1.0.x) : correction typo/ambiguïté, sans changement sémantique
- Minor (v1.x.0) : nouvelle métrique ou raffinement de définition, sans
  changement d'axiome ou d'invariant
- Major (v2.0.0) : changement d'axiome, d'invariant ou d'objet —
  requiert des preuves empiriques

**Document principal :** `specification/DCT_Core_v1.0.md` (statut : manuscrit de travail)

**Décision de gel :** Théorie figée au sens où aucun concept ne sera ajouté
avant 12 mois d'observation empirique. Les corrections d'ambiguïtés rédactionnelles
restent possibles en patch (v1.0.x).

---

## [1.0-draft] — 2026-07-18

Version de travail du manuscrit Core. Identique à v1.0.0 sur le fond ;
le statut "draft" indique uniquement que la relecture éditoriale finale
est en attente.

---

*Prochaine entrée attendue après la première observation empirique
ou correction d'ambiguïté rédactionnelle.*
