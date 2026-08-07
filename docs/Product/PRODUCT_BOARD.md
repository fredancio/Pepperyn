# PRODUCT_BOARD.md

**Nature :** Product Board canonique unique de Pepperyn. Reconstruit selon la stratégie C recommandée par `Audit/PRODUCT_BOARD_CANONICAL_ARBITRATION.md` (2026-08-06), promu ici comme référence unique lors de la Consolidation du dépôt canonique (2026-08-07), après vérification que `main` n'avait pas changé sur ce périmètre depuis l'arbitrage. L'ancienne version (`docs/Architecture/PRODUCT_BOARD.md`) est archivée sous `Archive/PRODUCT_BOARD_PRE_CONSOLIDATION.md` et n'a plus d'autorité.

---

## 1. DELIVERED AND MERGED

*(Ce qui existe réellement dans `main`, vérifié par code + tests + tags — jamais par déclaration.)*

- **Portfolio Intelligence** — Incréments 1 et 2 livrés et fusionnés (`ae79a9e`, `771e7ae`), Closed-Only fix (`bc98187`). `frontend/components/chat/PortfolioHome.tsx`, `ReviewBriefing.tsx`, routes `GET /api/portfolio`, `GET /api/review-briefing`. Tags : `portfolio-home-mvp-validation-complete`, `portfolio-intelligence-mvp-inc-1-2-complete`.
- **Portfolio Home Product Validation Report** — PASSED WITH MINOR RESERVATIONS. 48/48 tests ciblés, 943 passed / 8 échecs préexistants / 1 skip en suite complète, 30/30 frontend.
- **Anonymisation Layer 1** — `anonymization_service.py`, mécanisme correct pour son périmètre déclaré (voir `ANONYMIZATION_CAPABILITY_REVIEW.md` — couverture incomplète, traité en réserve, pas en negation de ce qui est livré).
- **Modèle Company/Entity/Workspace, PIN login, Billing/Stripe, exports PDF/PPTX/XLSX** — confirmés réels et câblés par `LEGACY_CAPABILITY_INVENTORY.md`.

## 2. ACCEPTED BUT NOT YET MERGED

- **T1 (Evidence Ledger — T1C-A, T1C-B)** — ADR-001/001A ACCEPTED, code validé sur projet Supabase de test dédié, jamais fusionné dans `main`. Risque : faible, fusion standard recommandée (`FOUNDATION_RECOVERY_EXECUTION_ORDER.md`).
- **T2 (Engagement — T2A)** — ADR-002 ACCEPTED, code réel sur branche, extraction ciblée de 8 fichiers requise (jamais fusion de branche entière — 119 fichiers hors périmètre).
- **ADR-003 v3 (Financial Time Engine)** — conçu, auto-critiqué (9/10), jamais promu ACCEPTED. Reste ici, pas en section 3, tant qu'aucun GO n'a été donné.

## 3. ACTIVE NEXT STEP

*(Un seul chantier principal autorisé — pas une liste.)*

**Foundation documentaire canonique + T1 (Evidence Ledger, T1C-A puis T1C-B).** Justification de l'exclusivité : toute autre ouverture de chantier (Decision Follow-up, Trust Boundary, FTE) reste bloquée tant que Gate A-C (`PRE_IMPLEMENTATION_GATE_CHECKLIST.md`) ne sont pas passés. Voir `FOUNDATION_RECOVERY_EXECUTION_ORDER.md` pour la justification complète de cet ordre.

**Exception explicitement autorisée à avancer en parallèle** (justifiée dans `LEGACY_MIGRATION_REVIEW_REPORT.md` Mission 9 et confirmée ici) : correction du Trust Boundary (contournement d'anonymisation du Conversation Engine V2) — aucune dépendance technique avec la séquence ci-dessus, son report prolonge un écart déjà prouvé entre promesse et comportement réel.

## 4. DEFERRED WITH TRIGGERS

*(Renvoi exclusif vers `STRATEGIC_DEFERRED_WORK_REGISTER.md` — pas de duplication de contenu ici, conforme à la règle « un seul registre ».)* Chantiers concernés : Engagement (T2A) une fois T1 mergé, architecture des agents IA, FTE, Enterprise Familiarization, Exception & Reconciliation, Recommendation Engine, Attention Score, Decision Follow-up, Knowledge Model/Business History, partage par rôles, connecteurs ERP/API/MCP, choix de modèle IA, évolution des exports, dette de cache/stockage, doublon feedback. Chacun porte son propre déclencheur dans le registre — voir la mise à jour Phase 13.

## 5. VISION / PARKING

*(Renvoi vers `STRATEGIC_DEFERRED_WORK_REGISTER.md` §4 — Decision Simulation Engine, BYOM/local, extension à d'autres professions.)*

---

## Ce que ce Product Board reconstruit corrige, explicitement

Par rapport à la version `main` : réintègre le North Star, la Vision et les règles de priorisation, absents de la version `main` alors que non contredits par le code. Par rapport à la version gouvernance (`dfb8a47`) : retire toute mention de Monthly Review Engine comme capability en cours (obsolète, contredite par le code — Portfolio Intelligence est la capacité réellement livrée) et toute métrique présentant T1/T2 comme validés sur `main` (faux — validés sur un projet de test, jamais fusionnés).

**Une seule capacité ne peut jamais apparaître simultanément en section 1 et en section 4** — test de cohérence structurel : Portfolio Intelligence (section 1) n'apparaît nulle part dans le registre de chantiers différés ; T1/T2 (section 2, pas 1) apparaissent bien dans le registre différé pour tout ce qui les suit (Engagement, FTE), jamais pour eux-mêmes puisqu'ils sont ACCEPTED BUT NOT MERGED, pas différés.

---

**PRODUCT_BOARD.md — RÉFÉRENCE CANONIQUE UNIQUE, PROMUE LORS DE LA CONSOLIDATION 2026-08-07.**
