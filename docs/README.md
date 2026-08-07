# Pepperyn — Documentation canonique

Ce fichier est le seul point d'entrée de la documentation Pepperyn. Il répond aux questions qu'un développeur ou un auditeur se pose en ouvrant ce dépôt pour la première fois.

---

## 1. Qu'est-ce que Pepperyn ?

Pepperyn est une plateforme qui modélise le métier de CFO fractionnel (analyse financière, revue de portefeuille de mandats, préparation de décisions). Le modèle du métier et les principes non négociables sont définis dans [`Foundation/PEPPERYN_CONSTITUTION.md`](Foundation/PEPPERYN_CONSTITUTION.md) et [`Foundation/PEPPERYN_PROFESSION_MODEL.md`](Foundation/PEPPERYN_PROFESSION_MODEL.md).

## 2. Par quel document commencer ?

Dans cet ordre : `Foundation/PEPPERYN_CONSTITUTION.md` → `Foundation/PEPPERYN_PROFESSION_MODEL.md` → `Domain/CURRENT_DOMAIN_MODEL.md` → `Product/PRODUCT_BOARD.md`. Ces quatre documents suffisent à comprendre ce qu'est Pepperyn, pourquoi, et où il en est.

## 3. Hiérarchie d'autorité

```
Foundation/PEPPERYN_CONSTITUTION.md        (autorité suprême)
  └─ Foundation/PEPPERYN_PROFESSION_MODEL.md
       └─ Domain/CURRENT_DOMAIN_MODEL.md + Domain/IDEAL_DOMAIN_MODEL.md + Domain/TRANSFORMATION_BLUEPRINT.md
            └─ Architecture/ADR/ (décisions ACCEPTÉES uniquement)
                 └─ Product/PRODUCT_BOARD.md
                      └─ Execution/ (plans d'exécution actifs)
                           └─ code
```

`Audit/` (preuves, revues, inventaires) et `Archive/` (superseded, historique) sont **hors de cette chaîne** : ils l'alimentent mais ne la remplacent jamais. Aucun document d'audit n'est une spec. Aucun document archivé n'est une référence courante.

## 4. Ce qui est en production aujourd'hui

- Portfolio Intelligence (Increment 1+2) — livré et mergé sur `main`.
- Anonymization Layer 1 (déterministe, sans LLM) — existe et fonctionne, couverture **incomplète** (voir `Audit/ANONYMIZATION_CAPABILITY_REVIEW.md`).
- Pipeline d'analyse v4 (`backend/services/llm_service.py::run_full_pipeline`) — en production, avec un défaut d'ancrage prouvé entre Call 1 et Call 2 (voir `Architecture/TRUST_BOUNDARY_CLOSURE_PLAN.md` et `Architecture/Cognitive/REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md`).
- `temporal_normalizer.py` — utilitaire de classification temporelle des colonnes Excel, actif, confirmé fournisseur (pas concurrent) du futur FTE (voir `Audit/TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md`).

## 5. Accepté mais pas encore mergé

- T1 — Evidence Ledger (ADR-001 / ADR-001A) : ACCEPTÉ, non mergé sur `main`.
- T2 — Engagement (ADR-002) : ACCEPTÉ, non mergé sur `main`.
- Ordre d'exécution tranché : **T1C-A → T1C-B → T2A**, par risque d'exécution croissant, pas par importance (voir `Execution/FOUNDATION_RECOVERY_EXECUTION_ORDER.md`).

## 6. En cours de travail maintenant

L'étape active suivante est la reprise du code sur **T1C-A**, dans la continuité de la baseline sécurisée (T1+T2 fusionnées sur la branche de sécurisation, Integration Gate 1 validé sur projet Supabase dédié). La correction de la Trust Boundary (fermeture des 10 sites d'appel LLM non gouvernés) peut avancer **en parallèle**, car elle corrige un défaut de confidentialité déjà prouvé — voir `Architecture/TRUST_BOUNDARY_CLOSURE_PLAN.md`. Aucun code de Trust Gateway n'a encore été écrit.

## 7. Proposé, pas accepté

- ADR-003 v3 (Financial Time Engine) — `Architecture/ADR/ADR-003_Financial_Time_Engine_v3_PROPOSED.md` — **PROPOSÉ**, pas accepté. Les versions v1 et v2 sont superseded, archivées.
- Architecture Cognitive complète (multi-agent, Case Framer/Analyst A-B/Adjudicator/Executive CFO, Quality Gate déterministe) — `Architecture/Cognitive/` — **PROPOSÉ**. Cohérent (verdict B — cohérent avec réserves nommées) mais 3 des 7 gates de pré-implémentation (`Execution/PRE_IMPLEMENTATION_GATE_CHECKLIST.md`) attendent une décision humaine explicite, pas une analyse supplémentaire.

## 8. Où vivent les plans d'exécution

`Execution/` — 4 documents : `FOUNDATION_RECOVERY_EXECUTION_ORDER.md`, `PHIDANI_WALKING_SKELETON_EXECUTION_PLAN.md`, `REASONING_PIPELINE_MIGRATION_PLAN.md`, `PRE_IMPLEMENTATION_GATE_CHECKLIST.md`. Ce sont des plans, pas du code réalisé — chacun le rappelle explicitement dans son en-tête.

## 9. Où vivent les audits et les preuves

`Audit/` — 17 documents (revue légale de préservation, revue d'anonymisation, cartographie d'autorité documentaire, revue temporal_normalizer, arbitrage Product Board, audit de réconciliation du workspace, registre des chantiers différés, classification des branches, revues PR/release-gate de Portfolio Intelligence). Un audit documente un constat à une date donnée. Il n'a **jamais** vocation à devenir silencieusement la spec courante — s'il révèle qu'un changement est nécessaire, le changement doit être acté via un ADR ou le Product Board, pas via l'audit lui-même.

Le `Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md` est un cas particulier : c'est un registre vivant, à compléter en append-only, qui gouverne *quand* un chantier différé peut rouvrir — pas *ce qui est vrai* aujourd'hui. Il reste sous `Audit/` par nature évidentielle, mais doit être consulté avant toute décision de réouverture d'un chantier différé.

## 10. Où vit le matériel historique

`Archive/` — documents superseded ou historiques, conservés pour traçabilité :
`PEPPERYN_PRODUCT_CONSTITUTION_PRE_v1.0.md`, `PEPPERYN_CONSTITUTION_DRAFT.md`, `ADR-003_Financial_Time_Engine_v1_SUPERSEDED.md`, `ADR-003_Financial_Time_Engine_v2_SUPERSEDED.md`, `PRODUCT_BOARD_PRE_CONSOLIDATION.md`, `CAPABILITY_ROADMAP_v1.md` (+ famille : `CAPABILITY_DEPENDENCY_MAP.md`, `CAPABILITY_MATURITY_MATRIX.md`, `CAPABILITY_TRANSITION_REPORT.md`, `MVP_CAPABILITY_SET.md`), `ARCHITECTURE_MILESTONES.md`, `ROADMAP_ARCHITECTURE.md`, `WP5C_RETROSPECTIVE.md`, `decision-arc-mvp-v2.2.md`, `GD-001_Official_Governance_of_Pepperyn_Documentation.md`.

D'autres documents historiques (sprints Product Design/Pivot, specs UI/UX intermédiaires, revues cognitives précédant la synchronisation) **ne sont pas dupliqués physiquement ici** — ils restent accessibles via Git sur leurs branches sources (voir `Audit/DOCUMENT_AUTHORITY_MAP.md` pour la liste exacte des branches). Rien n'a été détruit ; tout reste traçable par Git.

## 11. Ce qui ne doit PAS être utilisé comme spec courante

- Tout ce qui se trouve dans `Archive/`.
- Tout document sous `Audit/` — ce sont des preuves, jamais des instructions.
- `Architecture/Cognitive/*` tant que les gates A, B, D de `Execution/PRE_IMPLEMENTATION_GATE_CHECKLIST.md` ne sont pas explicitement validés par un humain.
- `Architecture/ADR/ADR-003_Financial_Time_Engine_v3_PROPOSED.md` — proposé, pas accepté.
- Tout document trouvé sur une branche non mergée en dehors de ceux listés ici — s'il n'est pas dans `docs/`, il n'est pas canonique, même s'il existe quelque part dans Git.

---

## Point bloquant non résolu (reporté, non tranché par cette consolidation)

Les branches `governance/mental-model-2026-08-05` et `governance/foundation-closure-2026-08-05` divergent sur 18 fichiers sans arbitrage explicite. Cette consolidation a utilisé `governance/mental-model-2026-08-05` comme source (cohérent avec l'usage des missions précédentes) mais **n'a pas tranché** laquelle des deux fait autorité en cas de conflit réel. Voir `Audit/DOCUMENT_AUTHORITY_MAP.md` pour le détail. À arbitrer explicitement avant toute nouvelle divergence sur ces mêmes fichiers.

---

## Frontière canonique

**Le périmètre canonique du projet Pepperyn est le dépôt Git.** Les dossiers de sortie d'une session Claude (`outputs/` ou équivalent) sont des zones de travail temporaires. Aucune décision architecturale n'est considérée préservée tant qu'elle n'existe pas, commitée, dans ce dépôt.

Discipline de fin de mission : toute mission se termine par (1) commit de la branche de mission si applicable, (2) rapport du hash de commit, (3) rapport de fusion ou non, (4) `git checkout main`, (5) confirmation explicite « CURRENT BRANCH = main », (6) poste de travail visible de l'utilisateur laissé sur `main`.
