# Pepperyn — Architecture Milestones

Ce document recense les jalons majeurs de l'architecture de Pepperyn.

Chaque milestone représente un état stable du système validé techniquement.
Aucune milestone ne doit être modifiée rétroactivement.
Toute évolution importante donne lieu à une nouvelle milestone.

---

# M1 — Decision Kernel v1

**Date :** 17/07/2026

**Git tag :** `wp5c-final`

**Statut :** ✅ VALIDÉ

## Objectif

Transformer Pepperyn d'un pipeline d'analyse en une plateforme reposant sur un modèle décisionnel canonique unique.

Le Decision Kernel devient la source de vérité de toutes les décisions financières produites par Pepperyn.

---

## Livrables

### Règles déterministes

- derive_score_global()
- derive_niveau_urgence()
- derive_polarity()

---

### Modèle canonique

Introduction du modèle `DecisionKernel`.

Le Kernel contient notamment :

- Decisions
- Findings
- Recommendations
- Attribution
- Fingerprint
- Métadonnées

---

### Pipeline d'extraction

Création du pipeline :

AnalysisResult
→ DecisionKernel
→ Validation
→ Canonicalisation
→ Fingerprint

---

### Persistance

Ajout des colonnes :

- decision_kernel
- decision_kernel_version

dans la table `analyses`.

---

### Intégration

Le Kernel est produit automatiquement lors d'une analyse.

L'intégration est additive.

Aucun comportement historique n'est modifié.

---

### Fingerprint

Application complète de KERNEL-INV-013.

Le Fingerprint dépend désormais exclusivement du Decision Kernel.

L'algorithme reste identique à WP5A (`v1`).

---

### Validation

149 tests WP5C validés.

Golden Tests introduits.

Régression : 0.

---

## Invariants stabilisés

- KERNEL-INV-001
- KERNEL-INV-008
- KERNEL-INV-009
- KERNEL-INV-010
- KERNEL-INV-011
- KERNEL-INV-012
- KERNEL-INV-013

---

## Documents de référence

- SPEC-DK-001 Rev 3.1
- WP5C Implementation Plan
- Decision Records associés
- Trust Framework
- Value Framework
- Product Contracts

---

## Commits

| Commit | Contenu |
|--------|---------|
| c1a2506 | Decision Rules |
| 3fec55e | Decision Kernel |
| d86ca6b | Decision Kernel Extractor |
| cd7fc11 | Migration SQL |
| 98600b0 | Intégration analyze.py |
| c86568f | Fingerprint |
| d02193c | Golden Tests |

---

## Ce qui est désormais considéré comme stable

- Architecture du Decision Kernel
- Canonicalisation
- Fingerprint v1
- Pipeline d'extraction
- Modèle Pydantic
- Migration SQL
- Golden Tests

---

## Ce qui n'est PAS couvert

Les évolutions suivantes feront l'objet de nouvelles milestones :

- dk-2 (Scoped Findings)
- Multi-document Analysis
- Scenario Kernel
- Decision Capital
- Action Engine
- Predictive Layer
- Simulation Engine
- TFM Integration

---

## Règle d'évolution

Toute évolution qui remet en cause :

- un invariant,
- le format du Decision Kernel,
- le Fingerprint,
- ou le pipeline de construction,

doit :

1. créer un nouveau Work Package ;
2. mettre à jour la spécification ;
3. produire une nouvelle milestone ;
4. créer un nouveau tag Git.

La milestone M1 reste immuable.