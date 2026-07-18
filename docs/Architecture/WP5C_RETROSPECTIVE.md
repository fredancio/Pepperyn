# WP5C — Rétrospective

**Work Package :** WP5C — Decision Kernel Architecture  
**Branche :** `release-1/wp4c-commercial-offer-alignment`  
**Tag de clôture :** `wp5c-final`  
**Date de clôture :** 17/07/2026  
**Statut :** ✅ Validé et clos

---

## 1. Contexte et objectif initial

Avant WP5C, Pepperyn produisait des analyses financières dont les conclusions clés
(score global, niveau d'urgence, fingerprint décisionnel) étaient soit copiées directement
depuis la sortie brute du LLM, soit calculées à des endroits multiples et non coordonnés du pipeline.

L'objectif de WP5C était de consolider ces conclusions dans un modèle canonique unique — le
**Decision Kernel dk-1** — garanti déterministe, scellable, fingerprintable, et persisté en JSONB.

Référence : SPEC-DK-001 Rev 3.1 (DESIGN FROZEN) — 13 invariants, 11 décisions DECISION-WP5C, 11 critères d'acceptation.

---

## 2. Ce qui a été livré

### 7 commits, 0 régression

| Commit | Contenu | Invariants concernés |
|--------|---------|---------------------|
| c1a2506 | `decision_rules.py` — règles Python déterministes | INV-008, INV-010 |
| 3fec55e | `decision_kernel.py` — modèles Pydantic dk-1 | INV-001, INV-009 |
| d86ca6b | `decision_kernel_extractor.py` — pipeline 12 phases | INV-011, INV-012, CA-1→CA-11 |
| cd7fc11 | `v15_decision_kernel.sql` — colonnes JSONB | CA-1, CA-4 |
| 98600b0 | Intégration `analyze.py` — additive, non intrusive | INV-001 |
| c86568f | `decision_fingerprint.py` + Phase 9 | INV-013 |
| d02193c | Golden Tests — 39 tests, 2 fichiers de référence | Tous |

### Couverture tests

- 149 tests WP5C au total (110 unitaires/intégration + 39 Golden Tests)
- 0 régression sur l'ensemble du périmètre WP5C
- Référence permanente : `optilux_v3_expected_kernel.json` (fingerprint `8780ad72a7b868118c0c64c606a2756f`)

---

## 3. Décisions d'architecture prises

### D-01 — Intégration additive

Le Decision Kernel a été injecté dans `analyze.py` de façon strictement additive :
aucune route existante n'a été modifiée, aucune réponse frontend n'a changé.
Le Kernel est un nouveau champ JSONB en base ; il ne remplace rien.

**Conséquence :** les analyses historiques ne contiennent pas de Kernel. C'est documenté et assumé.

### D-02 — Dérivation Python exclusive (KERNEL-INV-008)

`score_global` et `niveau_urgence` sont désormais calculés exclusivement par les règles Python
(`derive_score_global()`, `derive_niveau_urgence()`). Les valeurs LLM éponymes dans
`AnalysisResult` sont ignorées.

**Conséquence documentée :** pour le fixture Optilux v3, `score_global` LLM=2 est écrasé par la
valeur Python=3. Ce comportement est intentionnel et constitue la démonstration la plus forte
de l'invariant.

### D-03 — Fingerprint version "v1" maintenue (NC-1)

Malgré le changement de source (AnalysisResult → DecisionKernel), `FINGERPRINT_VERSION` reste
`"v1"` car l'algorithme de hash est strictement identique. Incrémenter à `"v2"` aurait rompu la
comparabilité entre les fingerprints WP5A et WP5C pour les données concordantes.

### D-04 — Proxy SimpleNamespace (NC-2)

`compute_decision_fingerprint_from_kernel()` délègue à `compute_decision_fingerprint()` via un
proxy `SimpleNamespace`. Cette indirection est volontaire : elle préserve l'algorithme WP5A
sans duplication de logique. Un futur algorithme v2 pourra supprimer cette couche.

### D-05 — Phase 9 positionnée après Phase 10

Le fingerprint est calculé après la canonicalisation (Phase 10), de sorte que les listes
`global_findings` et `global_recommendations` soient dans un ordre stable avant d'entrer dans
le hash SHA-256. Si Phase 9 précédait Phase 10, le fingerprint ne serait pas garanti déterministe
sur un Kernel désérialisé depuis JSONB.

---

## 4. Ce qui a fonctionné

**La spec avant le code.** SPEC-DK-001 Rev 3.1 a été arrêtée et gelée avant toute implémentation.
Cela a éliminé les aller-retours sur le périmètre et rendu chaque commit prévisible.

**Le protocole de validation commit-par-commit.** Chaque commit était soumis à validation
explicite avant le suivant. Ce rythme a permis de détecter et corriger les ajustements
(ex. : notes NC-1/NC-2 ajoutées avant Commit 6) sans dette accumulée.

**Les Golden Tests comme clôture formelle.** Traiter les Golden Tests comme une "preuve de
conformité" plutôt qu'une simple augmentation de couverture a produit un ensemble de tests
qui documentent les invariants architecturaux de façon permanente. Toute régression future
sera immédiatement visible.

**L'intégration additive.** Ne rien modifier des routes existantes a rendu le risque de WP5C
proche de zéro pour la production.

---

## 5. Limites connues et dette technique

### Périmètre dk-1

Le Kernel dk-1 est en mode "tout global" : tous les Findings et Recommendations ont
`scope_status = global`. La granularité dimensionnelle (RENTABILITÉ, RISQUE, etc.)
n'est portée que par les Decisions, pas par les Findings/Recommendations.

Adressé par : M2 / dk-2 (Scoped Findings).

### Fingerprint v1 — binning à frontière dure

Un score 3 (FAIBLE) et un score 4 (MOYEN) produisent des fingerprints différents même si la
tolérance ICD-001 (±1) les accepterait comme équivalents. La Stability Suite (WP5B+)
gérera les tolérances sur les champs bruts.

### Fixture unique

Un seul profil Golden (Optilux critique). Un profil "sain" et un profil "données insuffisantes"
compléteraient la régression. Non bloquant pour WP5C, à envisager en WP6.

### Données historiques sans Kernel

Les analyses produites avant WP5C ne contiennent pas de `decision_kernel` en base.
Un backfill est hors périmètre WP5C. Si nécessaire, un script de backfill devra être
conçu séparément, avec validation explicite.

---

## 6. Ce que WP6 doit prendre en compte

Le contenu exact de WP6 sera défini en séance de conception. Les points suivants
constituent les questions ouvertes issues de WP5C :

1. **dk-2 ou nouveau WP ?** La question du scope des Findings est la plus urgente.
   Faut-il introduire dk-2 en WP6 ou traiter d'abord un autre angle (ex. : Decision Capital, API publique du Kernel) ?

2. **Rétrocompatibilité JSONB.** Tout changement du schéma du Kernel devra définir
   une stratégie pour les Kernels dk-1 déjà en base (ignore, migration, version check).

3. **Exposition du Kernel.** Aujourd'hui le Kernel est en base mais non exposé via l'API.
   WP6 devra décider si et comment le Kernel est consommé par le frontend ou des services tiers.

4. **Fingerprint v2.** Si l'algorithme change, FINGERPRINT_VERSION devra être incrémenté
   et une stratégie de cohabitation v1/v2 définie.

---

## 7. Résumé

WP5C a posé les fondations architecturales sur lesquelles Pepperyn peut désormais construire
une plateforme décisionnelle cohérente. Le Decision Kernel dk-1 est un modèle stable, prouvé
formellement, et ancré dans le dépôt via ses Golden Tests et son tag `wp5c-final`.

La prochaine étape est une séance de conception pour définir WP6 précisément,
avant d'écrire la moindre ligne de code.
