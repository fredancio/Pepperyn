# PRODUCT BOARD v1.0

**Rôle :** ce document répond à *"que construisons-nous maintenant ?"* pour la ligne de code de `main`. À lire avant tout nouvel incrément.

**Note de portée (2026-08-05, Release Closure Mission 2) :** ce fichier est recréé directement sur `main`, à partir du contenu rédigé sur la branche `governance/portfolio-release-gate-product-board-2026-08-05` — cette dernière n'a **pas** été fusionnée, car elle descend d'une lignée de gouvernance ancienne (`capability/portfolio-intelligence-increment-1-2026-08-05`) qui a divergé de `main` avant les fusions des Incréments 1 et 2 : elle porte une version obsolète du code Portfolio (`arc_service.py`, `PortfolioHome.tsx`, etc., antérieure à l'Incrément 2) et environ 140 fichiers de documentation (Constitution, ADR, Capability Roadmap, sprints produit) qui n'existent nulle part dans l'historique de `main`. Fusionner cette branche aurait régressé le code Portfolio déjà validé sur `main`. Ce fichier reprend donc uniquement le contenu textuel utile, réécrit pour ne référencer que des documents réellement présents sur `main`. La réconciliation de cette lignée de gouvernance avec `main` reste un sujet ouvert, hors périmètre de cette clôture — voir `PORTFOLIO_INCREMENT_1_2_RELEASE_GATE.md` et le rapport de clôture associé.

---

## 1. Capability en cours

| Champ | Contenu |
|---|---|
| **Nom** | Portfolio Intelligence |
| **Objectif métier** | Faire qu'un professionnel sache, en ouvrant Pepperyn, quel client préparer en premier et pourquoi — à l'échelle du portefeuille, pas client par client. |
| **État** | **Incréments 1 et 2 livrés et fusionnés sur `main`** (Release Gate 2026-08-05, merges `ae79a9e` puis `771e7ae` ; rapport `docs/Architecture/blueprint/PORTFOLIO_INCREMENT_1_2_RELEASE_GATE.md`). Incrément 3 (état vide honnête) proposé, **pas encore ouvert**. |

---

## 2. Dernier incrément livré

| Champ | Contenu |
|---|---|
| **Nom** | Portfolio Home — Incréments 1 (écran minimal) et 2 (complétude de la carte) |
| **Statut** | **DONE — fusionnés sur `main`** (2026-08-05, merges `ae79a9e`, `771e7ae`). Suite ciblée : 48/48 tests backend verts. Suite complète backend : 943 passés, 8 échecs préexistants et non liés (inchangés avant/après fusion), 1 skip. Frontend : 30/30 tests Jest verts. Build production Next.js réussi, route `/app/portfolio` présente. |
| **Détail** | `docs/Architecture/blueprint/PORTFOLIO_INCREMENT_2_PR_REVIEW.md` (revue de l'Incrément 2), `docs/Architecture/blueprint/PORTFOLIO_INCREMENT_1_2_RELEASE_GATE.md` (Release Gate des deux incréments — 16 points de validation métier, sémantique de `limit`, review visuelle, verdict). |

## 3. Incrément en cours

**Aucun.** Incrément 3 (état vide honnête, section 4) proposé — **pas encore ouvert**, en attente de GO. Aucun nouvel incrément ne doit être ouvert avant la Portfolio Home Product Validation (section 5).

---

## 4. Prochain incrément proposé (non ouvert)

| Champ | Contenu |
|---|---|
| **Nom** | État vide honnête du Portefeuille |
| **Objectif métier** | Rendre explicite, pour un client sans point actif, pourquoi il n'apparaît pas plutôt que de laisser un silence ambigu. |
| **Dépendances** | Portfolio Home Incréments 1-2 (livrés). |
| **Statut** | Proposé, non ouvert. Périmètre réduit par rapport au plan initial : le tri fin par ancienneté, initialement prévu dans cet incrément, a déjà été livré avec l'Incrément 2 (Mission 4 du Release Gate). |

---

## 5. Prochaine étape réelle : Portfolio Home Product Validation

Avant tout enrichissement supplémentaire de la carte Portfolio (Incrément 3 ou au-delà), la prochaine étape est une validation produit, pas un nouvel incrément de code :

**Objectif :** observer le rendu réel et tester si un utilisateur comprend, en quelques secondes, quel client ouvrir, pourquoi, et quelle action effectuer.

Cette validation doit précéder tout nouvel enrichissement de carte.

---

## 6. Réserves UX ouvertes (Release Gate, Mission 6 — à observer, pas à corriger)

Classées **OBSERVE IN USER TESTING** — n'entrent pas automatiquement dans l'Incrément 3, aucune modification d'interface tant qu'elles n'ont pas été confirmées par un usage réel :

1. Sur les cartes portant plusieurs informations secondaires (contexte temporel, `why_it_matters`, compteur), la densité peut devenir élevée dans une longue liste de clients.
2. `why_it_matters_display` utilise actuellement la même couleur de texte que le nom du client, ce qui peut concurrencer visuellement l'attention portée au nom du client plutôt que de rester une information secondaire.

---

## 7. Métriques

| Métrique | Valeur |
|---|---|
| Capability actuelle | Portfolio Intelligence |
| Dernier incrément livré | Incréments 1 et 2, fusionnés sur `main` (2026-08-05, merges `ae79a9e`, `771e7ae`) |
| Incrément en cours | Aucun |
| Dernière Release Gate | Portfolio Intelligence, Incréments 1+2 (2026-08-05) — **PASSED WITH MINOR RESERVATIONS** |
| État des tests (sur `main`, post Release Gate) | Backend : 943 passés, 8 échecs préexistants non liés (inchangés), 1 skip. Frontend : 30/30 tests Jest verts. Build production Next.js réussi. |
| Nombre d'échecs connus | 8 — préexistants, non liés à Portfolio Intelligence, identiques avant et après les deux fusions |

---

## 8. Règle de discipline

Toute nouvelle idée est classée immédiatement dans l'une de ces catégories, jamais laissée "entre deux" : **Capability actuelle** (développement immédiat), **Vision** (documentée uniquement, hors périmètre de ce fichier réduit), ou **Parking** (reportée volontairement).
