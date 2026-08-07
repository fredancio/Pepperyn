# PRODUCT_BOARD_CANONICAL_ARBITRATION.md

**Nature :** arbitrage documentaire seul. Aucun code modifié. Aucun document importé dans `main`. Aucune branche fusionnée. `docs/Architecture/PRODUCT_BOARD.md` n'est modifié sur aucune des deux branches où il existe. Seul fichier créé par ce sprint : celui-ci.

---

## Constat structurel préalable

Les deux versions de `PRODUCT_BOARD.md` ne sont pas deux documents indépendants qui auraient divergé par accident. Ce sont deux branches d'une **même lignée**, qui se séparent à un ancêtre commun réel et vérifié : le commit `74a796f` (`merge feature/review-briefing-implementation-2026-08-05`, `main@{7}` dans le reflog).

À partir de ce point commun, deux chemins distincts ont été pris **le même jour** :

- **05:46:40** — commit `dfb8a47`, message *« Governance Reconciliation Sprint — single source of truth for all governance documents »*, sur la lignée qui deviendra `governance/pepperyn-profession-model-2026-08-06`. Un seul commit touche `PRODUCT_BOARD.md` sur cette lignée — jamais mis à jour depuis.
- **11:33:02** — commit `2f1a6b6`, message *« PRODUCT_BOARD.md — version canonique recréée sur main (Release Closure, Mission 2) »*, sur la lignée qui deviendra `main`. Ce commit ne descend pas de `dfb8a47` — vérifié par `git merge-base --is-ancestor dfb8a47 a58110e` → `NO`. C'est une recréation indépendante, pas une évolution de la tentative de réconciliation de 05:46.
- **13:07:50** — commit `a58110e`, *« Closed-Only fix DONE, Portfolio Home Product Validation PASSED WITH MINOR RESERVATIONS »*, qui étend `2f1a6b6`. C'est ce commit qui est aujourd'hui la tête de `PRODUCT_BOARD.md` sur `main`.

Fait notable : le commit `dfb8a47` prétend explicitement établir *« single source of truth »* — et a été silencieusement contourné six heures plus tard par une recréation indépendante, jamais rapprochée. Le problème que ce sprint traite a donc déjà une précédente tentative de résolution ratée, le même jour. Ce n'est pas une divergence accidentelle isolée — c'est un motif structurel qui s'est déjà répété une fois en une seule journée, et qui a de bonnes chances de se reproduire si l'arbitrage actuel ne change pas la discipline de fond (voir Mission 4).

Deuxième élément du même constat : le texte de la version `main` contient sa propre trace de ce motif — sa « Note de portée (Release Closure Mission 2) » explique explicitement pourquoi une version antérieure de gouvernance (`governance/portfolio-release-gate-product-board-2026-08-05`) n'a pas été fusionnée telle quelle (code Portfolio obsolète, ~140 documents sans rapport) et a été recréée à la main. Le motif « recréer plutôt que fusionner une branche de gouvernance divergente » est donc une pratique déjà consciente de l'équipe, pas une découverte de ce sprint — mais elle n'a, jusqu'ici, jamais été formalisée comme règle durable.

---

## Mission 1 — Comparaison factuelle ligne à ligne

| # | Sujet | Version `main` (`a58110e`, 2026-08-05 13:07) | Version `governance/pepperyn-profession-model-2026-08-06` (`dfb8a47`, 2026-08-05 05:46) | Catégorie | Preuve |
|---|---|---|---|---|---|
| 1 | Rôle du document | Identique en substance (« porte l'état réel du produit et la discipline d'exécution ») | Identique en substance, formulation élargie (« complète Constitution/ADR/Domain Models/Blueprint ») | **Formulation différente, fond identique** | Les deux premières lignes des deux fichiers |
| 2 | North Star explicite (§1 gouvernance) | **Absent** | Présent : « rendre un cabinet comptable ou un CFO externalisé objectivement prêt pour toute revue client, à tout moment » | **Élément seulement conçu** (absent de `main`, jamais retiré ni contredit) | `governance` §1 ; aucune section équivalente dans `main` |
| 3 | Promesse actuelle (§2 gouvernance) | **Absent** | Présent, formulation produit de la promesse court terme | **Élément seulement conçu** | `governance` §2 |
| 4 | Capability en cours | **Portfolio Intelligence** — Incréments 1+2 livrés et fusionnés (`ae79a9e`, `771e7ae`), Closed-Only fix fusionné (`bc98187`) | **Monthly Review Engine** — Incrément 1 (bandeau qualité) livré, Incrément 2 (Decision Follow-up) en plan | **Contradiction réelle** — mais résolue par le code, pas par supposition : `frontend/components/chat/PortfolioHome.tsx` et `ReviewBriefing.tsx` existent, sont testés, sont réels sur `main` ; aucune trace de bandeau qualité Monthly Review sur `main` (branche `feature/monthly-review-quality-banner-2026-08-04` que le document `governance` lui-même qualifie de « non fusionnée ») | Vérifié par lecture directe du code cette session (cartographie d'implémentation) |
| 5 | Portfolio Home Product Validation | PASSED WITH MINOR RESERVATIONS, détail des tests (48/48 ciblés, 943/8/1 suite complète, 30/30 frontend) | **Absent — aucune mention de Portfolio Home comme capability livrée** | **Information plus récente** (main) — la version gouvernance ne contredit pas ce fait, elle l'ignore parce qu'elle est antérieure à son existence documentaire | Tags `portfolio-home-mvp-validation-complete`, `portfolio-intelligence-mvp-inc-1-2-complete` (existants, vérifiés) |
| 6 | Incrément en cours | Aucun (« Portefeuille vide, honnête ») | Decision Follow-up, détail complet, renvoi à `DECISION_FOLLOWUP_IMPLEMENTATION_PLAN.md` | **Élément seulement conçu / non contredit** — Decision Follow-up n'est fusionné nulle part sur `main`, donc « aucun incrément en cours » (main) et « Decision Follow-up en plan » (gouvernance) ne se contredisent pas réellement : le second décrit un plan, le premier décrit l'état livré. Les deux sont vrais simultanément. | `PROFESSION_MODEL_FOUNDATION_CLOSURE.md` recommande indépendamment Decision Follow-up comme prochaine étape — convergence, pas contradiction |
| 7 | Prochains incréments proposés | Un seul point : réactiver Portfolio comme étape suivante (Test Utilisateur Externe) | Liste de 5 (réordonnancement bouton export, squelette écran Portefeuille, correctif format export, routage vers Portefeuille, widgets cockpit) — tous « Backlog » | **Élément propre à une ancienne roadmap** — cette liste précède la bascule Portfolio Intelligence ; certains items (« squelette écran Portefeuille », « routage vers Portefeuille ») sont **factuellement obsolètes** puisque Portfolio existe et fonctionne déjà sur `main`, avec tests | Contredit directement par `frontend/components/chat/PortfolioHome.tsx` réel + tests |
| 8 | Vision long terme (§6 gouvernance) | **Absent** | Present : Decision Simulation Engine (ex-Marginn), GO/NO-GO = Option B (long terme uniquement), océan rouge vs Fathom Portfolio, renvoi à `VISION_SPRINT_CONCLUSION.md` | **Information historique encore valide** — confirmée indépendamment par la mémoire de session (Vision Sprint Decision Simulation Engine, GO/NO-GO=B, daté du même jour) ; rien sur `main` ne contredit ce contenu, `main` n'aborde simplement pas la vision long terme | Cohérence avec les mémoires de session antérieures à ce sprint |
| 9 | Parking (§7 gouvernance) | **Absent** | Présent, 5 items | **Élément seulement conçu** | `governance` §7, sans équivalent |
| 10 | Règles de priorisation (§8 gouvernance, 7 critères + test « plus facile à vendre ? ») | **Absent** | Présent, détaillé | **Élément de gouvernance méthodologique** — ce n'est pas un fait produit, c'est une règle de fonctionnement ; sa disparition de `main` est une perte de discipline, pas une correction d'erreur factuelle | `governance` §8 |
| 11 | Storytelling (§9 gouvernance) | **Absent** | Présent, 3 questions | **Élément de gouvernance méthodologique** | `governance` §9 |
| 12 | Métriques — dernière Release Gate | 952 passed / 8 known fails / 30/30 frontend, datée Portfolio | « Dernière Release Gate : T2 — Engagement Foundation (2026-08-03) », « Dernier audit : Integration Gate 1 — T1/T2 VALIDATED » | **Contradiction réelle, résolue par le code** — grep exhaustif cette session (`backend/services/`, `backend/models/`, `backend/migrations/`) confirme : aucun `evidence_ledger_service.py`, aucun `engagement_service.py`, aucune migration `v18/v19/v20` sur `main`. T1/T2 sont validés sur un **projet Supabase de test dédié** (« Pepperyn Integration Test »), jamais fusionnés dans le code de `main`. La formulation gouvernance, lue sans cette vérification, laisse croire que T1/T2 sont l'état courant du produit — c'est faux pour `main` | Grep direct de session, mémoire `pepperyn-baseline-securisation-status` (« parent toujours vierge de v18/v19/v20 ») |
| 13 | Réserves UX ouvertes | 2 items nommés, « OBSERVE IN USER TESTING » | Absent | **Élément plus récent** (main) | `main` §6, sans équivalent gouvernance |
| 14 | Règle de discipline (dernière section, 3 catégories) | Présente | Présente | **Formulation différente, fond identique** — les deux versions portent une règle de discipline de fin de document, structurellement la même fonction | `main` §8, `governance` §11 |

**Réserve de méthode explicite (conforme à la consigne) :** la version `main` est chronologiquement postérieure (13:07 vs 05:46), mais ce n'est **pas** ce qui fonde sa plus grande exactitude sur les points 4, 5, 12. Ce qui la fonde, c'est la vérification directe du code effectuée cette session (services, migrations, composants frontend, tests). Sur les points 2, 3, 8, 9, 10, 11 — où aucune vérification de code n'est possible parce qu'il s'agit de gouvernance ou de vision, pas d'état livré — la version gouvernance n'est contredite par rien et sa disparition de `main` est une **perte d'information**, pas une correction.

---

## Mission 2 — Reconstruction de l'état réel

**A. DELIVERED AND MERGED (vérifié par code + tests sur `main`)**
- Portfolio Intelligence — Incréments 1 et 2 (`PortfolioHome.tsx`, `ReviewBriefing.tsx`, tests associés, routes `GET /api/portfolio`, `GET /api/review-briefing`)
- Closed-Only fix
- Portfolio Home Product Validation Report — PASSED WITH MINOR RESERVATIONS

**B. DESIGNED/APPROVED BUT NOT MERGED (vérifié par branches vivantes + plans écrits, absents du code `main`)**
- T1 (Evidence Ledger — T1C-A, T1C-B) — validé sur projet Supabase dédié « Pepperyn Integration Test », jamais fusionné dans `main`
- T2 (Engagement — T2A) — même statut
- Monthly Review Engine Incrément 1 (bandeau qualité) — branche `feature/monthly-review-quality-banner-2026-08-04`, gouvernance elle-même la qualifie de non fusionnée
- Decision Follow-up (Monthly Review Engine Incrément 2) — plan écrit (`DECISION_FOLLOWUP_IMPLEMENTATION_PLAN.md`), aucune trace de code
- ADR-003 v3 (Financial Time Engine) — écrit, jamais promu ACCEPTED
- Famille Profession Model complète (Profession Model, Protocole, Gap Register, Evidence Log, Foundation Closure) — écrite, statut PROPOSED, absente de `main`

**C. PROPOSED (existe uniquement comme texte/plan, aucune approbation ni validation formelle constatée)**
- Vision Decision Simulation Engine (ex-Marginn) — GO/NO-GO = Option B, long terme uniquement, explicitement pas un incrément à ouvrir maintenant
- Liste des 5 « prochains incréments » de la version gouvernance (réordonnancement export, squelette Portefeuille, etc.) — reclassée D ci-dessous pour les items rendus obsolètes par le code, PROPOSED pour ceux qui ne le sont pas (correctif format export, widgets cockpit — non vérifiables comme obsolètes ou non)

**D. SUPERSEDED (contredit par un fait vérifié plus tard)**
- « Squelette écran Portefeuille » et « routage vers Portefeuille » (liste gouvernance §5) — Portfolio existe et fonctionne déjà, avec tests, sur `main`
- Commit `dfb8a47` lui-même comme tentative de réconciliation — contourné le même jour par `2f1a6b6`/`a58110e`, jamais réintégré

**E. UNKNOWN/REQUIRES HUMAN DECISION**
- Si le Decision Follow-up (B, plan prêt) doit être ouvert avant ou après l'import documentaire et la récupération T1/T2 — dépend d'un arbitrage produit, pas d'un fait vérifiable
- Si les règles de priorisation à 7 critères et le test « plus facile à vendre ? » (gouvernance §8) doivent gouverner formellement les décisions de `main` dès maintenant, ou seulement après import — question de gouvernance, pas de fait
- Le statut exact de `governance/mental-model-2026-08-05` vs `governance/foundation-closure-2026-08-05` (divergence de 18 fichiers, non résolue — signalée dans `CANONICAL_DOCUMENT_SET_PROPOSAL.md`, hors périmètre de ce document mais touchant potentiellement d'autres sections de gouvernance liées au Product Board)

---

## Mission 3 — Proposition canonique

**Stratégie retenue : C — reconstruire un nouveau `PRODUCT_BOARD.md` à partir des preuves, sans réutiliser intégralement aucune des deux versions.**

Justification, par élimination :

- **Stratégie A (garder `main` + ajouts ciblés)** rejetée comme insuffisante seule : `main` est factuellement exact sur l'état livré, mais son silence total sur North Star, Vision, Parking, et les règles de priorisation n'est pas une simple lacune de « ajout » — c'est l'absence de toute la couche qui permet de motiver *pourquoi* un incrément est choisi plutôt qu'un autre. Un Product Board qui ne porte que l'état livré n'est plus un board de pilotage, c'est un changelog.
- **Stratégie B (garder gouvernance + corriger les non-conformités)** rejetée : les non-conformités ne sont pas des erreurs ponctuelles corrigibles par un correctif de section — c'est la section « Capability en cours » et « Métriques » tout entières qui décrivent un état antérieur à la bascule Portfolio Intelligence. Corriger ces sections reviendrait, de fait, à réécrire l'équivalent de la version `main` par-dessus une base gouvernance — ce n'est pas une correction, c'est une réécriture qui ne dit pas son nom.
- **Stratégie C** est retenue précisément pour la raison anticipée par Fred : les deux documents mélangent fortement des registres de nature différente (fait livré vs roadmap vs gouvernance méthodologique vs vision). Le Constat structurel préalable le confirme indépendamment — ce mélange a déjà produit une divergence non détectée une fois dans la même journée (05:46 → 11:33). Continuer à faire porter les trois registres par un seul document sans séparation structurelle expose à la même erreur une troisième fois.

**Recommandation de structure** (reprend et confirme la proposition de Fred, sans écrire le document) : cinq sections strictement séparées — **État réel livré** (source unique : code + tests + tags, jamais de plan), **Décisions actives** (gouvernance méthodologique, ex. règles de priorisation), **Prochain incrément autorisé** (au plus un, avec un GO explicite nommé), **Hypothèses à valider** (Vision, GO/NO-GO conditionnels), **Parking**. Cette séparation rend structurellement impossible qu'une capacité soit lue comme « Backlog » dans une section et « Livrée » dans une autre, puisque chaque capacité n'a plus qu'un seul emplacement possible déterminé par son statut de preuve, pas par la section où l'auteur a choisi de l'écrire.

**Rappel exprès (conforme à la consigne) : le document `PRODUCT_BOARD.md` reconstruit n'est pas écrit dans ce sprint.** Ce document-ci est une recommandation de stratégie, pas une exécution.

---

## Mission 4 — Points à arbitrer par Fred

Seuls les points suivants ne peuvent pas être tranchés par la preuve seule.

**1. Faut-il rouvrir Decision Follow-up avant l'import documentaire, ou l'import documentaire doit-il précéder toute décision d'ouverture d'incrément ?**
- Option 1 : ouvrir Decision Follow-up maintenant, en parallèle de l'import documentaire — le plan est prêt, la justification (proxy « moins de recommandations non suivies ») est déjà posée dans `PROFESSION_MODEL_FOUNDATION_CLOSURE.md`.
- Option 2 : attendre l'import documentaire complet + la récupération T1/T2 avant d'ouvrir tout nouvel incrément — cohérent avec la séquence que vous avez vous-même posée en fin de Foundation Recovery Sprint (Engagement consommé → Evidence Ledger consommé → alors seulement FTE/Phidani).
- **Recommandation :** Option 2. Ouvrir un incrément produit pendant que la fondation documentaire et T1/T2 restent en chantier crée exactement le type de dérive que ce sprint documente (deux vérités qui avancent sans se resynchroniser).
- **Risque si non tranché :** un incrément peut démarrer sans que quiconque ait explicitement décidé de l'ordre, reproduisant le motif du Constat structurel préalable une troisième fois.

**2. Les règles de priorisation à 7 critères (gouvernance §8) doivent-elles s'appliquer dès maintenant à toute décision produit, ou seulement une fois formellement importées dans le Product Board canonique ?**
- Option 1 : les considérer déjà en vigueur, puisqu'elles n'ont jamais été invalidées, seulement absentes de `main`.
- Option 2 : les considérer suspendues tant qu'elles ne sont pas portées par un document reconnu comme faisant autorité sur `main`.
- **Recommandation :** Option 1 — une règle de gouvernance méthodologique n'a pas de date de péremption liée à son emplacement de fichier ; son absence de `main` est un problème de portage documentaire, pas une abrogation.
- **Risque si non tranché :** des décisions prises « à l'instinct » entre maintenant et l'import documentaire, sans trace du critère qui les a motivées.

**3. La divergence `governance/mental-model-2026-08-05` vs `governance/foundation-closure-2026-08-05` (18 fichiers, signalée mais non résolue dans `CANONICAL_DOCUMENT_SET_PROPOSAL.md`) doit-elle être résolue avant ou après la reconstruction C du Product Board ?**
- Option 1 : avant — le Product Board reconstruit pourrait citer ou dépendre de documents (`PORTFOLIO_USER_FLOW.md`, `HABIT_MODEL.md`, `RETURN_LOOP_*`) dont la version faisant autorité n'est pas encore choisie.
- Option 2 : après — le Product Board reconstruit selon la structure en 5 sections proposée en Mission 3 n'a pas de dépendance stricte envers ces documents spécifiques.
- **Recommandation :** Option 2, avec réserve nommée dans le document reconstruit lui-même si l'un de ces documents est cité. Bloquer la reconstruction du Product Board sur une divergence sans rapport direct retarderait un travail qui peut avancer indépendamment.
- **Risque si non tranché :** aucun risque immédiat si Option 2 est suivie ; risque de citation d'une source non arbitrée si le rédacteur du Product Board reconstruit ignore cette réserve.

---

## Ce que ce document ne fait pas

Ne réécrit pas `PRODUCT_BOARD.md`. Ne fusionne, ne supprime, ne modifie aucune branche ni aucun autre fichier. Ne tranche pas la divergence `governance/mental-model-2026-08-05` vs `governance/foundation-closure-2026-08-05`, hors périmètre. Ne décide pas de l'ouverture de Decision Follow-up — ce choix reste à Fred (point 1 ci-dessus).

---

```
PRODUCT BOARD CANONICAL ARBITRATION COMPLETED.

FINAL VERDICT:
A — CANONICAL PRODUCT BOARD CAN BE RECONSTRUCTED FROM EVIDENCE
```
