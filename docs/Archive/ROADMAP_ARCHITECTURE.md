# Pepperyn — Architecture Roadmap

Ce document décrit la trajectoire architecturale de Pepperyn à horizon Release 1 et au-delà.
Chaque milestone est décrite dans `ARCHITECTURE_MILESTONES.md` une fois validée.

---

## ✅ M1 — Decision Kernel v1

**Tag :** `wp5c-final` · **Date :** 17/07/2026

Le Decision Kernel dk-1 est la source de vérité de toutes les décisions financières produites par Pepperyn.
Il est déterministe, scellable, fingerprintable, et persisté en JSONB.

Périmètre : règles Python déterministes, pipeline 12 phases, 13 invariants, 149 tests, Golden Tests.

---

## ⏳ M2 — Decision Kernel v2 (Scoped Findings)

**Statut :** conception en cours · **Design session :** à planifier

dk-1 traite toutes les Findings et Recommendations comme globales (`scope_status = global`).
M2 introduit la notion de Scoped Findings : une finding peut être attachée à une dimension spécifique
(RENTABILITÉ, RISQUE, STRUCTURE, LIQUIDITÉ) plutôt qu'au Kernel global.

Questions ouvertes à définir en design session :
- Contrat exact de `scope_status` et impact sur la canonicalisation
- Règle de déduplication cross-scope
- Impact sur le Fingerprint (FINGERPRINT_VERSION "v2" ?)
- Critères d'acceptation pour la migration dk-1 → dk-2
- Rétrocompatibilité des données historiques

---

## M3 — Decision Capital

Capitalisation des décisions dans le temps.
Un Decision Capital agrège et compare les Kernels successifs d'une même entité.

---

## M4 — Scenario Engine

Simulation de scénarios décisionnels alternatifs à partir d'un Kernel de référence.

---

## M5 — Action Engine

Suivi de l'exécution des Recommendations issues du Kernel.
Boucle fermée entre décision et action.

---

## M6 — Predictive Layer (TFM)

Intégration du Trust Framework Model.
Le Kernel devient un nœud dans un graphe de confiance prédictif.

---

## M7 — Autonomous Executive Copilot

Le Copilot opère de façon autonome sur la base des Kernels, du Capital et des Scenarios.

---

## Règle de progression

Une milestone n'est déclarée active qu'après validation explicite du plan de conception.
Aucune ligne de code n'est écrite avant que le plan soit arrêté.
