# PRODUCT_BOARD.md

**Nature :** Product Board canonique unique de Pepperyn. Reconstruit selon la stratégie C recommandée par `Audit/PRODUCT_BOARD_CANONICAL_ARBITRATION.md` (2026-08-06), promu ici comme référence unique lors de la Consolidation du dépôt canonique (2026-08-07), après vérification que `main` n'avait pas changé sur ce périmètre depuis l'arbitrage. L'ancienne version (`docs/Architecture/PRODUCT_BOARD.md`) est archivée sous `Archive/PRODUCT_BOARD_PRE_CONSOLIDATION.md` et n'a plus d'autorité.

---

## 1. DELIVERED AND MERGED

*(Ce qui existe réellement dans `main`, vérifié par code + tests + tags — jamais par déclaration.)*

- **Portfolio Intelligence** — Incréments 1 et 2 livrés et fusionnés (`ae79a9e`, `771e7ae`), Closed-Only fix (`bc98187`). `frontend/components/chat/PortfolioHome.tsx`, `ReviewBriefing.tsx`, routes `GET /api/portfolio`, `GET /api/review-briefing`. Tags : `portfolio-home-mvp-validation-complete`, `portfolio-intelligence-mvp-inc-1-2-complete`.
- **Portfolio Home Product Validation Report** — PASSED WITH MINOR RESERVATIONS. 48/48 tests ciblés, 943 passed / 8 échecs préexistants / 1 skip en suite complète, 30/30 frontend.
- **Anonymisation Layer 1** — `anonymization_service.py`, mécanisme correct pour son périmètre déclaré (voir `ANONYMIZATION_CAPABILITY_REVIEW.md` — couverture incomplète, traité en réserve, pas en negation de ce qui est livré).
- **Modèle Company/Entity/Workspace, PIN login, Billing/Stripe, exports PDF/PPTX/XLSX** — confirmés réels et câblés par `LEGACY_CAPABILITY_INVENTORY.md`.
- **T1C-A (Evidence Ledger — capture)** — ADR-001/001A ACCEPTED, fusionné dans `main` le 2026-08-07 (commit `3b1b21a`, revue adversariale passée, verdict A — MERGE AS-IS). **COMPLETE.**
- **T1C-B (Evidence Ledger — faits atomiques)** — ADR-001 ACCEPTED, fusionné dans `main` le 2026-08-07 (commit `0741a03`, revue adversariale passée, verdict A — MERGE AS-IS). `amount`/`currency`/`fact_id` atomiques lus directement depuis la sortie structurée du LLM, `fact_id` = empreinte de contenu déterministe (voir réserve explicite : ce n'est PAS une identité métier, `Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md` §1.3). Table `evidence_ledger_entries` toujours strictement additive, non lue par aucun chemin de production (ADR-001 §8). Baseline post-merge : 988 passed / 8 échecs préexistants / 1 skip. **COMPLETE.**
- **T2A (Engagement Foundation)** — ADR-002 ACCEPTED, fusionné dans `main` le 2026-08-07 (commit `f5f00bf`, revue adversariale passée, verdict A — MERGE AS-IS). Table `engagements`, création atomique Entity+Engagement (chemin applicatif + inscription), backfill idempotent, 40 tests. Baseline post-merge : 1028 passed / 8 échecs préexistants / 1 skip. **COMPLETE.**

  **Décision de cardinalité Entity:Engagement (arbitrage du 2026-08-07, ADR-002 §0) :**
  - **DOMAINE :** une Organisation peut avoir plusieurs Engagements au cours de sa vie (`1:N` permis) — l'identité d'un Engagement suit la continuité du mandat professionnel, pas la durée de vie de l'Organisation.
  - **IMPLÉMENTATION AUJOURD'HUI :** la contrainte `1:1` (`UNIQUE(entity_id)`) reste en place, temporairement, parce qu'aucun comportement de création d'un second Engagement n'existe encore dans le code. Ce n'est plus un invariant de domaine — c'est une contrainte transitoire, avec son déclencheur de relâchement enregistré dans `Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md` §1.2.a.
  - Ces deux affirmations ne se contredisent pas : la seconde est un état d'implémentation actuel, la première est la vérité de domaine qui le remplacera quand un besoin réel apparaîtra.

## 2. ACCEPTED BUT NOT YET MERGED

- **ADR-003 v3 (Financial Time Engine)** — conçu, auto-critiqué (9/10), jamais promu ACCEPTED. Reste ici, pas en section 3, tant qu'aucun GO n'a été donné.

## 3. ACTIVE NEXT STEP

*(Un seul chantier principal autorisé — pas une liste.)*

**Premier consommateur réel de l'Evidence Ledger** (T1.3 → prochain incrément) — T1C-A, T1C-B et T2A tous mergés et validés (2026-08-07, commits `3b1b21a`, `0741a03`, `f5f00bf`). Déclencheur déjà posé dans `Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md` §1.3 : « immédiatement après Engagement (T2A), avec consommateur réel livré dans le même incrément — règle déjà posée pour éviter le sort de `financial_truth.py` ». Périmètre attendu : un consommateur en lecture seule (citation dans Review Briefing ou Decision Memory) et le rattachement `DecisionArc.engagement_id`, désormais possible puisque Engagement existe physiquement. **Cette mission n'ouvre pas cet incrément — elle identifie seulement qu'il est désormais autorisé.** Justification de l'exclusivité : toute autre ouverture de chantier (Decision Follow-up, Trust Boundary, FTE, Familiarization) reste bloquée tant que Gate A-C (`PRE_IMPLEMENTATION_GATE_CHECKLIST.md`) ne sont pas passés. Voir `FOUNDATION_RECOVERY_EXECUTION_ORDER.md` pour la justification complète de cet ordre.

**Exception explicitement autorisée à avancer en parallèle** (justifiée dans `LEGACY_MIGRATION_REVIEW_REPORT.md` Mission 9 et confirmée ici) : correction du Trust Boundary (contournement d'anonymisation du Conversation Engine V2) — aucune dépendance technique avec la séquence ci-dessus, son report prolonge un écart déjà prouvé entre promesse et comportement réel.

## 4. DEFERRED WITH TRIGGERS

*(Renvoi exclusif vers `STRATEGIC_DEFERRED_WORK_REGISTER.md` — pas de duplication de contenu ici, conforme à la règle « un seul registre ».)* Chantiers concernés : relâchement de la cardinalité Entity:Engagement (§1.2.a, déclencheur = premier besoin réel de second mandat), résolution Evidence/DecisionArc après suppression d'Entity (§1.2.b), architecture des agents IA, FTE, Enterprise Familiarization, Exception & Reconciliation, Recommendation Engine, Attention Score, Decision Follow-up, Knowledge Model/Business History, partage par rôles, connecteurs ERP/API/MCP, choix de modèle IA, évolution des exports, dette de cache/stockage, doublon feedback. Chacun porte son propre déclencheur dans le registre — voir la mise à jour Phase 13.

## 5. VISION / PARKING

*(Renvoi vers `STRATEGIC_DEFERRED_WORK_REGISTER.md` §4 — Decision Simulation Engine, BYOM/local, extension à d'autres professions.)*

---

## Ce que ce Product Board reconstruit corrige, explicitement

Par rapport à la version `main` : réintègre le North Star, la Vision et les règles de priorisation, absents de la version `main` alors que non contredits par le code. Par rapport à la version gouvernance (`dfb8a47`) : retire toute mention de Monthly Review Engine comme capability en cours (obsolète, contredite par le code — Portfolio Intelligence est la capacité réellement livrée) et toute métrique présentant T1/T2 comme validés sur `main` (faux — validés sur un projet de test, jamais fusionnés).

**Une seule capacité ne peut jamais apparaître simultanément en section 1 et en section 4** — test de cohérence structurel : Portfolio Intelligence, T1C-A, T1C-B et T2A (section 1) n'apparaissent nulle part dans le registre de chantiers différés pour eux-mêmes ; seuls leurs chantiers de suivi (cardinalité Entity:Engagement §1.2.a, résolution Evidence/DecisionArc §1.2.b, FTE, Familiarization) y apparaissent, chacun avec son propre déclencheur.

---

**PRODUCT_BOARD.md — RÉFÉRENCE CANONIQUE UNIQUE, PROMUE LORS DE LA CONSOLIDATION 2026-08-07.**
