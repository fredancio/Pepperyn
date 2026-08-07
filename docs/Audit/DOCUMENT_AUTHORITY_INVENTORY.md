# DOCUMENT_AUTHORITY_INVENTORY.md

**Nature :** Phase 1. Aucun code, aucune fusion. Inventaire fondé sur l'état réel des branches au 2026-08-07 (`git branch -a`, `git log`, `git show`), pas sur la mémoire de conversation.

**Choix d'échelle, assumé explicitement :** ce corpus compte plus de 60 documents produits sur huit semaines. Un inventaire ligne-à-ligne exhaustif de chacun serait lui-même une source d'ambiguïté (mur de texte que personne ne lit), contraire au principe de clôture de cette mission. L'inventaire ci-dessous opère donc **par famille documentaire**, avec un détail fichier-par-fichier uniquement là où une décision d'autorité doit se prendre au niveau individuel (versions concurrentes, contenus contradictoires). C'est un choix de méthode, pas une omission.

---

## Familles documentaires

| Famille | Documents représentatifs | Branche(s) | Commit(s) de référence | Rôle | Statut supposé | Référencé par |
|---|---|---|---|---|---|---|
| **Constitution** | `PEPPERYN_CONSTITUTION_v1.0.md` (204 lignes) | `governance/mental-model-2026-08-05` | — | Norme suprême du projet | **Autoritatif, jamais promu sur `main`** | Tous les ADR, Profession Model, cette mission |
| **Constitution — artefact concurrent** | `PEPPERYN_PRODUCT_CONSTITUTION.md` (250 lignes, racine) | `main` | présent sur `main` | Génération antérieure, ère pré-refonte DDD | **Historique — pas un doublon du même document** | Aucun document actuel ne s'appuie dessus |
| **Domain Models** | Ideal Domain Model, Current Domain Model (instantané 2026-08-02), Transformation Blueprint | `governance/mental-model-2026-08-05` | — | Modèle cible + état constaté + trajectoire | **Autoritatif, jamais promu sur `main`** | ADR-001/001A/002/003, cartographie d'implémentation |
| **ADR fondation** | ADR-001, ADR-001A (statut RESOLVED interne), ADR-002 (statut ACCEPTED interne) | `governance/mental-model-2026-08-05`, `docs/adr-002-engagement-foundation` | — | Décisions d'architecture actées | **Autoritatif, jamais promu sur `main`** | T1/T2 recovery plan |
| **ADR-003 (Financial Time Engine)** | v1 (`docs/adr-003-financial-time-engine`), v2 (`docs/adr-003-v2-financial-time-engine`), **v3 (`docs/adr-003-v3-financial-time-engine`)** | 3 branches distinctes | — | Doctrine FTE | v3 = **PROPOSED (jamais ACCEPTED)** ; v1/v2 = **SUPERSEDED** explicitement par le texte de la version suivante | Cognitive Architecture Review, `TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md` |
| **Profession Model** | `PEPPERYN_PROFESSION_MODEL.md`, `PEPPERYN_MODEL_FIDELITY_PROTOCOL.md`, `MODEL_GAP_REGISTER.md` (vide), `PROFESSION_MODEL_EVIDENCE_LOG.md` (vide), `PROFESSION_MODEL_FOUNDATION_CLOSURE.md` | `governance/pepperyn-profession-model-2026-08-06` | — | Apex conceptuel (au-dessus des ADR, sous la Constitution) | **Autoritatif, jamais promu sur `main`**, verdict de clôture rendu : COMPLETE WITH MINOR RESERVATIONS | Toute mission produit-métier depuis sa création |
| **Cartographie d'implémentation** | `PROFESSION_MODEL_IMPLEMENTATION_CARTOGRAPHY.md` | `audit/profession-model-implementation-cartography-2026-08-06` | — | Preuve — écart modèle/code | **AUDIT/EVIDENCE** | Foundation Recovery |
| **Product Board — deux versions divergentes** | `docs/Architecture/PRODUCT_BOARD.md` | `main` (`a58110e`) **vs** `governance/pepperyn-profession-model-2026-08-06` (`dfb8a47`) | voir `PRODUCT_BOARD_CANONICAL_ARBITRATION.md` | Pilotage d'exécution | **Contradiction déjà arbitrée** — verdict A, stratégie C (reconstruction) recommandée, non encore exécutée | Cette mission (Phase 5) |
| **Product Operating System / Dashboard** | `PRODUCT_OPERATING_SYSTEM.md`, `PROJECT_DASHBOARD.md`, `DECISION_LOOP.md` | branches `governance/*` multiples, contenu cohérent observé | — | Architecture de décision produit | **ACCEPTED SUPPORTING, jamais promu sur `main`** | Product Board |
| **Foundation Recovery** | `GIT_FOUNDATION_RECOVERY_MAP.md`, `CANONICAL_DOCUMENT_SET_PROPOSAL.md`, `T1_T2_RECOVERY_PLAN.md`, `DECISION_ARC_ENGAGEMENT_MIGRATION_NOTE.md`, `FOUNDATION_RECOVERY_REVIEW.md` | `audit/foundation-recovery-sprint-2026-08-06` | — | Audit git + plan de récupération T1/T2 | **AUDIT/EVIDENCE**, verdict READY WITH NAMED RESERVATIONS | Cette mission (Phase 6) |
| **Legacy Capability Preservation** | 5 documents (policy, inventory, matrix, anonymisation, rapport de clôture) | `audit/legacy-capability-preservation-review-2026-08-07` | — | Audit du code réel + politique de conservation | **AUDIT/EVIDENCE + B. ACCEPTED SUPPORTING pour la politique**, verdict B | Cette mission (Phase 7) |
| **Strategic Deferred Work Register** | `STRATEGIC_DEFERRED_WORK_REGISTER.md` | `audit/legacy-capability-preservation-review-2026-08-07` | — | Registre canonique des chantiers différés | **CANONICAL (registre à source unique)** | Cette mission (Phase 13) |
| **Cognitive Architecture** | 7 documents (review, capability map, contracts, walking skeleton, multi-agent proposal, risk register, reliability framework) | `architecture/cognitive-synchronization-review-2026-08-07` | — | Conception de l'architecture cognitive cible | **PROPOSED**, verdict B | Cette mission (Phases 8-11) |
| **Capability Roadmap** | `CAPABILITY_ROADMAP_v1.md`, `CAPABILITY_DEPENDENCY_MAP.md`, `MVP_CAPABILITY_SET.md`, `CAPABILITY_MATURITY_MATRIX.md`, `CAPABILITY_TRANSITION_REPORT.md` | `governance/capability-roadmap-v1-2026-08-03` | — | Pilotage par capacité métier | **HISTORICAL** — supersédé en pratique par le Product Board et le Strategic Deferred Work Register, jamais explicitement déclaré tel | À reclasser (Phase 2) |
| **Product Design / Pivot Sprints** | `MONTHLY_REVIEW_*`, `PRODUCT_PIVOT_AUDIT.md`, `PRODUCT_EXPERIENCE_REDESIGN.md`, `NEXT_10_PRODUCT_DECISIONS.md`, etc. | branches dédiées 2026-08-03 | — | Décisions produit ponctuelles, déjà exécutées (pivot vers Portfolio Intelligence) | **HISTORICAL** — décisions déjà absorbées dans l'état réel de `main` | Aucun document actuel n'en dépend directement |
| **Vision Sprint** | `MARKET_VALIDATION.md` ... `VISION_SPRINT_CONCLUSION.md`, `VISION_DECISION_WORKSPACE.md` | branches Vision Sprint 2026-08-04 | — | GO/NO-GO stratégique (Decision Simulation Engine) | **ACCEPTED SUPPORTING** — verdict déjà rendu (Option B, long terme), cité par le Strategic Deferred Work Register | Strategic Deferred Work Register §4.3 |
| **UI/UX Specification Sprints** | `UI_SPECIFICATION.md`, `DESIGN_SYSTEM.md`, `SCREEN_CATALOG.md`, etc. (~13 docs) | branches dédiées 2026-08-03 | — | Spécification frontend | **HISTORICAL/PARTIELLEMENT ABSORBÉ** — Portfolio Home et Review Briefing réellement construits depuis, le reste reste conceptuel | Non bloquant pour cette mission |
| **`governance/mental-model-2026-08-05` vs `governance/foundation-closure-2026-08-05`** | 18 fichiers, 1843 lignes d'écart (`PORTFOLIO_USER_FLOW.md`, `HABIT_MODEL.md`, `RETURN_LOOP_*`) | deux branches | — | Non identifié avec certitude | **BLOCKED/UNRESOLVED — toujours non résolu**, déjà signalé dans `CANONICAL_DOCUMENT_SET_PROPOSAL.md`, non traité par aucune mission depuis | Hors périmètre direct de cette mission (voir Phase 2) |
| **Documents historiques sur `main` lui-même** | `ARCHITECTURE_MILESTONES.md`, `ROADMAP_ARCHITECTURE.md`, `WP5C_RETROSPECTIVE.md` | `main` | présents | Traces d'étapes déjà dépassées | **HISTORICAL** | Aucun |

---

## Ce que cet inventaire ne fait pas

Ne liste pas individuellement chacun des ~15 documents des sprints Product Design/UI/Vision — regroupés par famille avec un statut de famille, conforme au principe de réduction de complexité. Un inventaire fichier-par-fichier de ces familles peut être produit à la demande, s'il s'avère qu'une décision d'autorité individuelle y est nécessaire — aucun signal actuel ne l'indique.

---

**DOCUMENT_AUTHORITY_INVENTORY ÉTABLI. AUCUN CODE, AUCUNE FUSION.**
