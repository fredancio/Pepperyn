# Pepperyn — Current Domain Model (DDD)
**Date :** 2026-08-02 — Phase 1D (observation uniquement)
**Méthode :** modèle déduit du code réel (modèles, routes, services, migrations SQL, prompts) — jamais du marketing.

Convention : **CONFIRMÉ** (lu directement dans le code/schéma) — **INFÉRENCE** (déduction raisonnable, non prouvée à 100%) — **INCONNU** (non démontrable dans le périmètre observé).

---

## A. Objectifs métier du produit

**CONFIRMÉ, déduit du pipeline `routers/analyze.py` + `services/llm_service.py` + les 3 renderers.**

Le problème réellement résolu aujourd'hui, tel que le code le construit : transformer un fichier financier uploadé (Excel/CSV/PDF — `ALLOWED_EXTENSIONS = {'xlsx','xls','csv','pdf'}`, `routers/analyze.py`) en un jugement décisionnel structuré et chiffré, accompagné d'un chiffrage du coût de l'inaction, puis le restituer sous 3 formats identiques (PDF/PPTX/Excel — RÈGLE ABSOLUE de `export_pptx_service.py` : « seules les données changent, la structure est figée »).

**Résultat final observable** = un triplet d'exports (PDF, PPTX, Excel) construits depuis un seul objet interne (`ExecutiveDecisionModel`, voir section H) plus une conversation (chat) qui explique ce même objet sans jamais recalculer (`conversation_engine.py`, règle 1 : « le chat explique — il ne recalcule JAMAIS »).

**Objet produit qui génère toute la chaîne** = le fichier financier uploadé par l'utilisateur (`UploadFile` dans `POST /api/analyze`, `routers/analyze.py:279`). Tout le reste du domaine (Evidence Graph, AnalysisResult, DecisionKernel, ExecutiveDecisionModel, DecisionArc, exports) est une transformation successive de ce fichier unique.

Il n'y a **aucune notion de « client suivi dans le temps par un CFO externe »** encodée comme concept de premier rang dans le code (voir section I — objets faibles) : le domaine actuel raisonne « un upload → une analyse », pas « un portefeuille de clients suivis en continu ».

---

## B. Bounded Contexts

| Contexte | Responsabilité | Objets principaux | Dépendances | Preuve |
|---|---|---|---|---|
| **Identity & Access** | Authentification par PIN (compte) ou JWT invité, création de compte | `companies`, `profiles` (Supabase Auth `auth.users` en amont) | Aucune (racine) | `routers/auth.py`, `security_config.py`, migration `v6_workspaces_entities.sql` (trigger `handle_new_user`) |
| **Workspace & Entity** | Regrouper les analyses d'une société sous une organisation, gérer plusieurs entités (filiale/client) | `workspaces`, `entities` | Identity | `routers/entities.py`, `migrations/v6_workspaces_entities.sql`, `migrations/v8_entity_relation_type.sql` |
| **Financial Analysis (pipeline)** | Transformer un fichier en résultat d'analyse structuré | `AnalysisResult`, `analyses` (table) | Workspace/Entity (implicite via `company_id`), LLM | `routers/analyze.py`, `services/file_parser.py`, `services/financial_normalizer.py`, `services/temporal_normalizer.py`, `services/data_quality_gate.py`, `services/llm_service.py` |
| **Evidence (Evidence Graph)** | Ancrer chaque affirmation générée à une cellule source, avant rédaction | Pas d'entité persistée — objet JSON intermédiaire dans l'appel LLM | Financial Analysis | `services/llm_service.py:285-303` (`EVIDENCE_GRAPH_SYSTEM`), RÈGLE ABSOLUE N°6 |
| **Financial Truth Layer** | Modèle canonique d'impact financier (montant, période, nature, provenance) — **INFÉRENCE : présent en code, mais son propre docstring indique qu'il n'est pas encore lu par les renderers de production** | `QuantifiedImpact`, `EconomicEvent`, `SourceReference` | Financial Analysis (en théorie) | `models/financial_truth.py:1-19` |
| **Decision Intelligence (Kernel)** | Extraction déterministe de Findings/Recommendations/Decisions depuis `AnalysisResult`, calcul d'empreinte décisionnelle | `DecisionKernel`, `Finding`, `Recommendation`, `Decision`, `decision_fingerprint` | Financial Analysis | `services/decision_kernel_extractor.py`, `models/decision_kernel.py`, `services/decision_fingerprint.py`, `services/decision_rules.py` |
| **Decision Arc (mémoire décisionnelle comportementale)** | Suivre intention → décision → exécution → conséquences → apprentissage sur une recommandation donnée | `DecisionArc`, `ArcAnalysisLink`, `decision_feedback` | Financial Analysis (référence `report_id → analyses.id`) | `services/arc_service.py`, `models/decision_arc.py`, `routers/arcs.py`, `routers/decision_memory.py`, migrations `v7`, `v14`, `v15`, `v16` |
| **Memory (financière)** | Suivre l'évolution des métriques financières d'une company dans le temps | `financial_metrics`, `company_profile` | Financial Analysis | `services/memory_service.py:1-19` |
| **Executive Reporting / Export** | Construire les 3 exports identiques depuis un objet unique | `ExecutiveDecisionModel`, `ExecutiveCaseJSON` (importé), rendus PDF/PPTX/XLSX | Financial Analysis, Decision Intelligence (partiellement) | `services/export_pdf_service.py`, `services/export_pptx_service.py`, `services/excel_export.py`, `models/executive_decision_model.py` |
| **Chat (Conversation Engine)** | Répondre aux questions du CEO sans jamais recalculer ni contredire | payload construit depuis `ExecutiveCase` V2 | Executive Reporting (lit un objet déjà construit) | `services/conversation_engine.py:1-14`, `models/executive_case_v2.py` |
| **Billing** | Plans, quotas, paiement Stripe | `usage_limits`, `usage_logs`, `Plan` (enum) | Identity (company_id) | `routers/billing.py`, `services/billing_service.py`, `services/usage_service.py`, `config/product_catalog.py` |
| **CRM / Growth (périphérique)** | Synchroniser Supabase → Airtable pour pilotage business | Aucun objet métier propre — miroir en lecture | Identity, Billing, Financial Analysis | `services/crm_service.py:1-17`, `routers/superadmin.py` |
| **EPM (orphelin, disposition tranchée)** | Extraction déterministe de KPI depuis un fichier — **hors Git, non branché au produit**. Disposition finale 2026-08-07 : DISMANTLE & HARVEST (voir `docs/Audit/EPM_FINAL_DISPOSITION.md`) — `ExecutivePerformanceModel` ne survit pas comme modèle autonome, sa logique d'extraction est récupérable pour l'ingestion `FinancialFact` | `ExecutivePerformanceModel` et ses extracteurs | Aucune dépendance entrante depuis le produit | `backend/epm/` (non tracké), `backend/tools/epm_viewer.py` |

---

## C. Agrégats métier

Seuls deux objets du code présentent une racine d'agrégat au sens strict (identité stable, invariants protégés, cycle de vie explicite). Les autres « regroupements » sont des documents/structures de transformation sans véritable frontière transactionnelle.

### Agrégat 1 — DecisionArc
- **Responsabilité :** représenter le devenir réel d'UNE recommandation Pepperyn dans le temps.
- **Entité racine :** `DecisionArc` (`models/decision_arc.py:41`), identifiée par `id: UUID`.
- **Sous-entités :** `ArcAnalysisLink` (liens vers les analyses d'origine/conséquence).
- **Valeurs :** `ArcStatus`, `ExecutionStatus`, `DecisionConfirmationSource`, `LinkType` (tous `Literal`).
- **Services associés :** `arc_service.py` (`ArcService`).
- **Persistance :** tables `decision_arcs`, `arc_analysis_links` (migration `v16_decision_arcs.sql`, confirmé Phase 1B).
- **Cycle de vie CONFIRMÉ (code) :** `intention → decision → execution → consequences_linked → learning_proposed → closed` avec branche `abandoned` à tout moment. Invariants explicites dans le docstring de `arc_service.py` : « `decision_text IS NOT NULL` requis pour `CLOSED` », « un refus de lien ne ferme pas l'arc — il reste en EXECUTION ».

### Agrégat 2 — DecisionKernel
- **Responsabilité :** structure racine canonique (« dk-1 ») regroupant les jugements dimensionnels dérivés d'une analyse.
- **Entité racine :** `DecisionKernel` (`models/decision_kernel.py:310`).
- **Sous-entités :** `Finding`, `Recommendation`, `Decision` (chacun avec `SourceRef`, provenance).
- **Valeurs :** `AttributionMetrics` (compteurs de couverture).
- **Services associés :** `decision_kernel_extractor.py` (extraction pure, sans effet de bord), `decision_rules.py` (règles dérivées versionnées `DECISION_RULES_VERSION`).
- **Persistance : INCONNU** — aucune table `decision_kernel*` dans les 18 tables confirmées en Phase 1B ; le kernel semble être une structure calculée à la volée puis consommée immédiatement (par exemple pour le `decision_fingerprint`), non conservée telle quelle. **Non vérifié directement dans cette phase.**
- **Cycle de vie :** reconstruit à chaque analyse (fonction pure garantissant « pour un `AnalysisResult` identique, toujours le même `DecisionKernel` », `decision_kernel_extractor.py:8-9`) — pas de mutation, pas d'état.

**Note :** `ExecutiveDecisionModel` (section H) et `analyses` (la table brute) ne sont **pas** des agrégats au sens DDD strict — ce sont des objets de transformation/persistance sans invariant transactionnel protégé au-delà de la validation Pydantic de forme.

---

## D. Entités

| Entité | Responsabilité | Identité | Relations (CONFIRMÉ) | Cycle de vie |
|---|---|---|---|---|
| **Company** | Racine de facturation et de propriété des données | `companies.id` (UUID) | `admin_user_id → auth.users`, 1—N `profiles`, `workspaces`, `entities` | Créée par le trigger `handle_new_user()` à l'inscription (`v6_workspaces_entities.sql`) ; suppression : `DELETE /api/auth/account` (`routers/auth.py:287`) |
| **Profile (utilisateur)** | Représentation d'un utilisateur authentifié | `profiles.id` (= `auth.users.id`) | `company_id → companies` | Créée par le même trigger ; pas de suppression explicite trouvée hors suppression du compte |
| **Workspace** | Espace nommé d'une company | `workspaces.id` | `company_id → companies`, contrainte « un seul `is_default=TRUE` par company » | Créé au trigger d'inscription ; pas de route de suppression trouvée (`INCONNU` si suppression possible) |
| **Entity** | Filiale ou client suivi dans un workspace | `entities.id` | `workspace_id → workspaces`, `company_id → companies`, contrainte « un seul `is_primary=TRUE` par workspace », champ `relation_type` = `"filiale"` \| `"client"` \| `NULL` | Créée au trigger (entité primaire) ou via `POST /api/entities` (`routers/entities.py:102`, plan PRO+ requis) ; suppression **INCONNU** (pas de route DELETE trouvée) |
| **Analysis** (`analyses`) | Résultat persisté d'une analyse d'un fichier | `analyses.id` (UUID) | `company_id → companies` (INFÉRENCE, non relu ligne à ligne dans cette phase), référencée par `decision_feedback.report_id` | Créée par `POST /api/analyze` (`routers/analyze.py:865`, insert) ; suppression en masse via `DELETE /analyses/history` (`routers/analyze.py:244`) |
| **DecisionFeedback** | Retour utilisateur sur une recommandation précise | `decision_feedback.id` | `company_id`, `user_id → profiles` (nullable), `report_id → analyses.id` | Créée via `POST /api/decision-feedback` (`routers/decision_memory.py:74`) ; statuts `planned/done/partially_done/not_done/rejected/no_longer_relevant/unsure` (v17) |
| **DecisionArc** | Voir agrégat 1 | `decision_arcs.id` | `origin_analysis_id → analyses.id`, `company_id`, `entity_id` (optionnel) | Voir section C |
| **InvitedMember** | Membre invité dans une company | `invited_members.?` (structure exacte **INCONNU**, table confirmée par nom uniquement) | `company_id` (INFÉRENCE) | **INCONNU** en détail — pas de route dédiée identifiée dans les 10 routers lus |
| **ContactRequest** | Demande de contact commerciale | `contact_requests.?` | Aucune (formulaire public) | Créée via `POST /api/contact` (`routers/contact.py:110`), consultée via `GET /api/contact/requests` |
| **UsageLimits / UsageLogs** | Compteur d'usage par company/plan | `usage_limits`, `usage_logs` | `company_id` (INFÉRENCE) | Gérées par `usage_service.py`, alimentées à chaque analyse (`routers/analyze.py:873`, insert dans `usage_logs`) |

---

## E. Value Objects

Uniquement les objets réellement présents en code, sans identité propre (deux instances aux mêmes valeurs sont interchangeables) :

| Value Object | Fichier | Rôle |
|---|---|---|
| `QuantifiedImpact` | `models/financial_truth.py:182` | Représentation canonique d'un impact financier (montant, devise, type de métrique, base temporelle, nature) — dormant (voir section B) |
| `SourceReference` | `models/financial_truth.py:144` | Provenance d'un `QuantifiedImpact` (feuille, ligne, période, citation) |
| `GrossMarginResolution` | `models/financial_truth.py:137` | Taux de marge brute + sa source, selon une hiérarchie stricte à 5 niveaux |
| `AnnualizationMetadata` | `models/financial_truth.py:125` | Métadonnées de la méthode d'annualisation d'un montant |
| `CostOfInaction` | `models/executive_decision_model.py:59` | Coût de l'inaction décliné par période (an/mois/semaine/jour/heure) |
| `DataQualityInfo` | `models/schemas.py:134` | Score de fiabilité des données source (3 scores distincts — RÈGLE N°9) |
| `ScenarioCase` | `models/schemas.py:127` | Un scénario de simulation (meilleur/probable/pire cas) |
| `ValueDestroyer` | `models/executive_decision_model.py:68` | Une ligne de destruction de valeur chiffrée |
| `ExecutiveDecision` | `models/executive_decision_model.py:82` | Une décision recommandée, avec impact/priorité/ROI dérivés |
| `EliminatedOption`, `TippingCondition` | `models/executive_case.py:59+` | Options alternatives écartées / conditions de bascule d'une recommandation (raisonnement comparatif EDX-002) |
| `KPICard` / `DashboardCard` | `models/executive_case.py:44`, `models/schemas.py:104` | Un indicateur du tableau de bord — **deux définitions parallèles quasi identiques** (voir section M) |

**« Risk Score », « Confidence Score », « Materiality » (cités en exemple dans la consigne) : INCONNU / partiellement présents.** Il existe `score_confiance`, `score_risque`, `confidence` (float sur `QuantifiedImpact`), mais aucun objet nommé `RiskScore` ou `Materiality` en tant que Value Object structuré — ce sont des champs numériques nus (`int`/`float`), pas des types dédiés.

---

## F. Événements métier

**Constat central : il n'existe aucun bus d'événements ni table d'événements de domaine dans les 18 tables Supabase confirmées.** Les « événements » ci-dessous sont des **transitions d'état inférées** du code (écritures directes en base), pas des objets `Event` persistés et nommés comme tels.

| Événement (INFÉRENCE, nommé pour la lisibilité) | Déclencheur | Producteur | Consommateur | Persistance |
|---|---|---|---|---|
| Analyse créée | `POST /api/analyze` réussi | `routers/analyze.py:865` | Aucun consommateur asynchrone identifié | Ligne insérée dans `analyses` (CONFIRMÉ) |
| Usage enregistré | Après chaque analyse | `routers/analyze.py:873` | `usage_service.py` (quotas) | Ligne insérée dans `usage_logs` (CONFIRMÉ) |
| Feedback décisionnel enregistré | `POST /api/decision-feedback` | `routers/decision_memory.py:74` | `arc_service.py` (peut créer un `DecisionArc`) | `decision_feedback` (CONFIRMÉ) |
| Conséquence candidate détectée | Nouvelle analyse après un arc ouvert | `arc_service.py` (détection) | Renvoyé au frontend via `AnalyzeResponse.arc_consequence_candidates` (`models/schemas.py:254`) | `arc_analysis_links` (CONFIRMÉ pour le lien lui-même) |
| Webhook Stripe reçu | Événement Stripe externe | `routers/billing.py:250` (`POST /webhook`) | `billing_service.py` | **INCONNU en détail** — non relu dans cette phase |
| Nouvel utilisateur | Inscription Supabase Auth | Trigger SQL `on_auth_user_created` (DB, pas applicatif) | `handle_new_user()` (fonction SQL) | Cascade `companies`/`profiles`/`workspaces`/`entities` (CONFIRMÉ, `v6_workspaces_entities.sql`) |
| Événement CRM externe (log_event) | Actions utilisateur diverses | `services/crm_service.py:341` | Airtable (externe, hors domaine Pepperyn) | Table Airtable « Events » — **hors Supabase, hors périmètre du domaine interne** |

**AnalysisCreated, UploadCompleted, EvidenceValidated, ExportGenerated, DecisionAccepted (cités en exemple dans la consigne) : aucun de ces noms n'existe littéralement dans le code. Ce sont des transitions d'état implicites, pas des objets `Event` du domaine.**

---

## G. Workflow métier (changements d'état, pas le pipeline technique)

1. **Anonyme → Compte identifié.** Un utilisateur s'inscrit (Supabase Auth) → devient `Company` + `Profile` + `Workspace` (défaut) + `Entity` (primaire), atomiquement (trigger SQL).
2. **Fichier brut → Fait vérifiable.** Un fichier est uploadé ; ses données sont anonymisées (`anonymization_service.py`) avant tout envoi au LLM, puis l'Evidence Graph établit l'inventaire des faits directement lisibles (observation vs déduction) — aucune affirmation n'existe encore à ce stade sans source.
3. **Fait vérifiable → Jugement structuré.** Le LLM produit un `AnalysisResult` (diagnostic, scores, quick wins, plan d'action) sous contrainte de l'audit de cohérence obligatoire (RÈGLE N°11 : aucun chiffre hors source, aucun terme interdit, score de confiance jamais supérieur à la qualité/complétude des données).
4. **Jugement structuré → Décision exécutive unique.** `build_executive_decision_model()` transforme `AnalysisResult` en `ExecutiveDecisionModel` : une seule décision mise en avant, un coût de l'inaction calculé (jamais par le LLM), des décisions triées par impact.
5. **Décision exécutive → Restitution figée.** Les 3 renderers (PDF/PPTX/Excel) lisent le même `ExecutiveDecisionModel` sans le modifier ni le recalculer (RULE 004 : « le renderer AFFICHE »).
6. **Restitution → Intention utilisateur.** L'utilisateur donne un feedback sur une recommandation (`decision_feedback`, statut `planned`/`done`/etc.) — première trace d'un engagement réel.
7. **Intention → Arc décisionnel.** Un feedback `planned` peut créer un `DecisionArc` en état `intention`, qui évolue vers `execution` puis peut détecter des `consequences` lors d'une analyse ultérieure, puis se clôturer avec un `learning`.
8. **Analyse suivante → Mémoire.** Chaque nouvelle analyse alimente `financial_metrics`/`company_profile` (tendances) et peut détecter des conséquences sur des arcs existants — le domaine se souvient d'un fil dans le temps, mais **toujours ancré sur des analyses individuelles, jamais sur un objet « client suivi » de premier rang** (voir section I).

Ce qui **n'existe pas** comme changement d'état métier observable dans le code : pas de notion de « revue mensuelle » planifiée, pas de « portefeuille client » avec un cycle de vie propre, pas de validation humaine explicite d'une exportation avant envoi à un tiers.

---

## H. Objet central

**Réponse : l'objet central du domaine actuel est `ExecutiveDecisionModel` (EDM), pas `Analysis`, pas `Workspace`, pas `Company`, pas `Decision` au sens autonome.**

Justification uniquement par le code :
- `AnalysisResult` (schemas.py) est bien la donnée persistée en base (`analyses.analyse_json`), mais elle n'est **jamais lue directement** par les 3 renderers de production.
- Les 3 fichiers de rendu (`export_pdf_service.py:2540`, `export_pptx_service.py:2715`, `services/excel_export.py:1452`) appellent **tous les trois** `build_executive_decision_model(result)` avant de générer quoi que ce soit. C'est la seule opération commune aux trois formats de sortie.
- La docstring de `models/executive_decision_model.py:1-8` le formule explicitement : « Source de vérité unique pour tout contenu décisionnel généré par Pepperyn. Les exports (...) ne font QUE lire ce modèle — ils ne calculent rien. »
- **Contradiction documentée (dette) :** ce même fichier affirme aussi (ligne 28-29) « Aucun champ de ce module n'est encore lu par `export_pdf_service.py`, `export_pptx_service.py` ou `excel_export.py` » — affirmation **fausse au regard du code actuel** (les trois l'importent et l'appellent). C'est un exemple direct de dérive documentation/réalité (voir section M).
- `Company`/`Workspace`/`Entity` sont des conteneurs d'accès et de facturation, jamais lus par la logique de génération du contenu décisionnel lui-même.
- `Decision` (au sens `DecisionKernel.Decision` ou `DecisionArc`) est un sous-produit dérivé de l'analyse, pas ce qui structure la restitution finale au client.

---

## I. Objets faibles

Objets qui apparaissent dans le vocabulaire du code (noms de colonnes, commentaires, docstrings) mais qui ne sont **pas** des citoyens de première classe (pas de route dédiée, pas de cycle de vie propre, pas d'invariant protégé) :

- **Client** — le champ `entities.relation_type = "client"` (`routers/entities.py:97-98`) permet de qualifier une entité comme « client suivi par l'utilisateur », mais c'est une simple valeur d'énumération optionnelle sur `Entity`, pas un objet « Client » avec ses propres attributs (contact, historique de facturation, contrat). **INFÉRENCE forte que c'est un embryon de fonctionnalité fractional-CFO, jamais développé au-delà d'un champ.**
- **Monthly Review** — absent du code. Aucune table, aucune route, aucun modèle nommé « review », « monthly », ou équivalent. **INCONNU/absent**, alors que c'est le cas d'usage cible évoqué dans le repositionnement stratégique (mémoire projet).
- **Portfolio** — absent. Un `Workspace` peut contenir plusieurs `Entity`, mais rien n'agrège une vue « portefeuille de clients » avec ses propres métriques globales.
- **Meeting** — absent totalement du code observé.
- **Action Plan** — existe *textuellement* (`plan_action`, `plan_action_30_60_90`, `roadmap_90_days`) mais uniquement comme **liste de chaînes/objets éphémères dans `AnalysisResult`/`ExecutiveDecisionModel`**, recréée à chaque analyse, sans identité propre, sans suivi d'exécution structuré au-delà du texte (le suivi réel d'exécution passe par `decision_feedback`/`DecisionArc`, objets distincts et non nommés « Action Plan »).
- **Evidence / EconomicEvent** — modélisés en dur (`financial_truth.py`) mais **jamais persistés** (`EconomicEvent`, docstring : « Phase 4B : modèle uniquement, aucune persistence DB ») — un objet qui existe en tant que *type* mais jamais en tant qu'*instance durable*.

---

## J. Règles métier réellement implémentées

Règles Python (pas des prompts), avec leur source :

1. **Priorité dérivée par seuils fixes, jamais demandée au LLM** — `services/executive_decision_model.py:221-230` (`compute_priority`).
2. **Coût de l'inaction = division arithmétique pure de l'impact annuel, jamais par le LLM** — `services/executive_decision_model.py:208-218`.
3. **`derive_polarity` : inversion de l'échelle pour la dimension RISQUE** (un score de risque élevé = mauvais signal, donc inversé avant seuillage) — `services/decision_rules.py:14-17`, invariant `KERNEL-INV-010`.
4. **`derive_score_global` : moyenne arrondie des scores disponibles, avec inversion RISQUE** — `services/decision_rules.py:19-22`, invariant `KERNEL-INV-008`.
5. **`derive_niveau_urgence` : seuils fixes** (≤3 Critique, ≤5 Élevé, ≤7 Modéré, >7 Maîtrisé) — `services/decision_rules.py:24-26`.
6. **Un seul workspace `is_default=TRUE` par company** (contrainte SQL, `idx_workspaces_default_per_company`) — `migrations/v6_workspaces_entities.sql`.
7. **Une seule entité `is_primary=TRUE` par workspace** (contrainte SQL) — même migration.
8. **Gating par plan : multi-entités réservé aux plans PRO et supérieurs** — `routers/entities.py:113-119`.
9. **`decision_text IS NOT NULL` requis pour clore un `DecisionArc`** — docstring `services/arc_service.py`.
10. **Un refus de lien conséquence ne ferme pas l'arc — il reste en `EXECUTION`** — même fichier.
11. **Score de confiance des conclusions ≤ min(qualité technique, complétude des données), jamais supérieur** — RÈGLE ABSOLUE N°9, appliquée et *corrigée* côté Python si le LLM la dépasse (`services/llm_service.py:1396`).
12. **`is_anchored()` : un `SourceReference` de type `LEGACY_PARSE` n'est jamais considéré comme ancré**, même avec un `fact_id` — `models/financial_truth.py:163-174`.
13. **`recurring_annual_equivalent()` refuse de convertir un montant `ONE_TIME` ou de base `UNKNOWN`** — `models/financial_truth.py:224-257`.
14. **Anonymisation systématique avant tout envoi au LLM** (détection par nom de colonne et par format de valeur : email, IBAN, TVA) — `services/anonymization_service.py`.
15. **Remplacement automatique des termes interdits** (liste fixe : « crise imminente » → « risque identifié », etc.) — RÈGLE ABSOLUE N°4, `services/llm_service.py:61-90`.

---

## K. Invariants protégés par le système

- **`amount = None` ≠ `amount = 0.0`** — absence de donnée jamais confondue avec un vrai zéro observé. Invariant explicite et répété (`financial_truth.py:191-193`, `excel_export.py:343` « ABSENCE DE DONNÉE ≠ ZÉRO FINANCIER »).
- **Un seul workspace par défaut / une seule entité primaire** (contraintes d'unicité SQL partielles, section J).
- **Le renderer ne calcule jamais** — RULE 004 (`excel_export.py:341`) : il affiche ce que la couche de construction (EDM) lui fournit, sans recalcul ni extrapolation.
- **Le chat n'invente jamais de chiffre et ne contredit jamais l'ExecutiveCase** — règles 1-4, `services/conversation_engine.py:8-11`.
- **Le Decision Kernel est une fonction pure** — mêmes entrées + même version de règles → même sortie, sans effet de bord (`decision_kernel_extractor.py:8-9`).
- **`event_id` toujours calculé de façon déterministe (hash SHA-256), jamais généré par le LLM** — RÈGLE ABSOLUE, `economic_event_resolver.py:8-9`.
- **Score de confiance jamais supérieur à la qualité/complétude des données sources** (section J, règle 11).
- **Le rapport `analyse_json` n'est jamais modifié rétroactivement par la couche mémoire décisionnelle** — `decision_memory_service.py` docstring : « Ne modifie JAMAIS `analyse_json` (...) layout figé ».

---

## L. Couplages

**Fortement couplés :**
- `AnalysisResult` ↔ `ExecutiveDecisionModel` ↔ les 3 renderers — couplage total et assumé (source unique, section H).
- `DecisionArc` ↔ `analyses` — un arc n'existe pas sans une `origin_analysis_id` (clé étrangère `NOT NULL`).
- `Entity` ↔ `Workspace` ↔ `Company` — hiérarchie stricte à 3 niveaux, toutes les FK sont `NOT NULL` avec `ON DELETE CASCADE`.
- `export_pptx_service.py` / `test_rule_003_renderer_responsibility.py` / `test_edx_002.py` — couplage code/tests fortement documenté par convention `RULE NNN`, mais désynchronisé en pratique (Phase 1B : dérive du nombre de slides entre fichiers de test).

**Indépendants (faiblement couplés ou non couplés) :**
- `financial_truth.py` (QuantifiedImpact/EconomicEvent) — importé par `executive_decision_model.py` (le type existe sur `ValueDestroyer.quantified_impact`) mais **non lu** par la logique de rendu (dormant, section B).
- `executive_case_v2.py` — isolé, ne sert que le Conversation Engine, aucun lien vers les renderers PDF/PPTX/Excel.
- `epm/` — zéro dépendance entrante depuis le reste du produit (Phase 1B, confirmé).
- `crm_service.py` — lecture/écriture vers Airtable, aucun autre service n'en dépend en retour (flux sortant uniquement).
- `rate_limiter.py` — état en mémoire locale au process, explicitement documenté comme non partagé entre workers (« la limite est appliquée par worker ») — isolement assumé, pas un vrai couplage distribué.

---

## M. Dette métier (confusion métier observée)

1. **Cinq à six représentations parallèles du même concept « résultat d'analyse ».** `AnalysisResult` (schemas.py, blob versionné V3→V12), `ExecutiveCaseJSON` (executive_case.py, « V2 » malgré son nom de fichier sans suffixe), `ExecutiveCase`/`ConversationEngine` (executive_case_v2.py, une AUTRE « V2 »), `ExecutiveDecisionModel` (executive_decision_model.py), `DecisionKernel` (decision_kernel.py), `QuantifiedImpact`/`EconomicEvent` (financial_truth.py). Chacune a sa propre docstring affirmant un statut de « source de vérité », sans qu'aucune ne remplace clairement les précédentes.
2. **Une docstring de code contredit le code lui-même** — `models/executive_decision_model.py` affirme que les renderers ne lisent pas encore ce modèle, alors que les trois le lisent explicitement (section H). C'est une preuve directe que la documentation en commentaire n'est plus synchronisée avec le comportement réel.
3. **Deux définitions quasi identiques de « carte KPI »** — `DashboardCard` (schemas.py:104) et `KPICard` (executive_case.py:44), mêmes champs (`label`, `value`, `status`), noms différents, dans deux fichiers différents, sans relation déclarée entre eux.
4. **`Entity.relation_type` porte seul le poids conceptuel de « client externe suivi »**, sans aucune autre structure (pas de contrat, pas d'historique de mission, pas de cadence de revue) — un concept métier potentiellement central au repositionnement stratégique réduit à une valeur d'enum optionnelle sur un objet technique.
5. **`BusinessContext` est un placeholder assumé** (`executive_decision_model.py:124-130`) — un objet du domaine existe en type mais n'a jamais de source de données branchée ; le « contexte métier » de l'entreprise analysée n'existe donc nulle part dans le système en pratique.
6. **La mémoire est scindée en deux services jamais unifiés** : `memory_service.py` (ce qui a changé dans les chiffres) et `decision_memory_service.py` (ce que l'utilisateur a fait des recommandations) — cohérent individuellement, mais aucun objet ne relie les deux vues pour raconter « l'histoire complète » d'une entreprise suivie dans le temps.
7. **`AnalysisResult` porte à la fois des champs legacy (V3) et des champs récents (V12) simultanément actifs** (schemas.py:148-240), sans dépréciation ni suppression des anciens — la forme du « résultat d'analyse » s'est empilée plutôt que d'être refactorée.

---

## N. Domain Model synthétique (état réel)

```
Company
    │
    ├── Profile (utilisateur, 1..N)
    │
    ├── Workspace (1 "default" garanti)
    │      │
    │      └── Entity (1 "primary" garanti ; relation_type: filiale | client | None)
    │
    ├── Analysis (analyses — table brute, N par company, lien company_id INFÉRENCE)
    │      │
    │      ├── AnalysisResult (contenu persisté — blob versionné V3..V12)
    │      │
    │      ├── [transformation, non persisté] Evidence Graph (faits sourcés, éphémère)
    │      │
    │      ├── [transformation, non persisté] DecisionKernel
    │      │        ├── Finding
    │      │        ├── Recommendation
    │      │        └── Decision (polarity, score, scope)
    │      │
    │      ├── [transformation, non persisté] ExecutiveDecisionModel  ◄── OBJET CENTRAL (section H)
    │      │        ├── CostOfInaction
    │      │        ├── ValueDestroyer[]
    │      │        ├── ExecutiveDecision[]
    │      │        └── Phase90Days[] (roadmap)
    │      │
    │      ├── Export PDF   ┐
    │      ├── Export PPTX  ├── lisent tous ExecutiveDecisionModel, ne recalculent rien
    │      └── Export Excel ┘
    │
    ├── DecisionFeedback (N, référence report_id → Analysis.id)
    │      │
    │      └── peut créer ──► DecisionArc (intention → decision → execution → consequences_linked → learning_proposed → closed | abandoned)
    │                              └── ArcAnalysisLink[] (vers Analysis d'origine / de conséquence)
    │
    ├── Memory
    │      ├── financial_metrics (N, dérivées de chaque Analysis)
    │      └── company_profile (1, évolutif)
    │
    ├── Billing
    │      ├── usage_limits (1, quotas par plan)
    │      └── usage_logs (N, un par analyse consommée)
    │
    └── [dormant, non branché] Financial Truth Layer
             ├── QuantifiedImpact (type existe, jamais persisté)
             └── EconomicEvent (type existe, jamais persisté)

[isolé, hors arborescence Company] EPM (backend/epm/) — hors Git, zéro dépendance entrante
[isolé] Chat / ConversationEngine — lit ExecutiveCase V2 (dérivé séparément, hors du flux ci-dessus)
```

---

## O. Verdict

Pepperyn, tel que le code le construit aujourd'hui, n'est pas un système organisé autour d'un client suivi dans la durée : c'est un **pipeline de transformation centré sur l'événement « une analyse »**, dont la sortie converge systématiquement vers un objet pivot unique — `ExecutiveDecisionModel` — que les trois formats d'export lisent à l'identique sans jamais recalculer. La hiérarchie de propriété (Company → Workspace → Entity) est stricte et bien contrainte au niveau SQL, mais elle sert un rôle d'accès et de facturation, pas de narration métier : rien dans le code ne raconte l'histoire d'une entreprise suivie mois après mois au-delà de deux tables de tendances (`financial_metrics`, `company_profile`) et d'un mécanisme de suivi de recommandations (`DecisionArc`) qui reste ancré sur une recommandation individuelle, jamais sur une relation client globale.

Le domaine porte une dette de modélisation significative et auto-documentée : au moins cinq représentations concurrentes du même « résultat d'analyse » coexistent (`AnalysisResult`, deux `ExecutiveCase`, `ExecutiveDecisionModel`, `DecisionKernel`, `QuantifiedImpact`), chacune ayant sa propre prétention à être la source de vérité, avec au moins un cas confirmé où la documentation en commentaire contredit directement le comportement réel du code. Le module le plus rigoureux du point de vue de la modélisation financière (`financial_truth.py`, avec ses invariants explicites sur l'absence de données et sa hiérarchie de provenance) est aussi le seul dont le propre code affirme qu'il n'est pas encore branché à la production.

Un architecte logiciel lisant ce code reconnaîtrait un système qui a correctement isolé son **cœur de calcul déterministe** (règles versionnées, invariants nommés, fonctions pures pour le Kernel) mais dont le **modèle de données métier** a évolué par empilement successif de couches (V3 à V12 dans un seul objet, puis V1/V2 d'ExecutiveCase, puis EDM, puis Kernel, puis Financial Truth) sans jamais consolider une frontière d'agrégat unique et stable pour « ce que Pepperyn sait d'une entreprise ». Le concept de « client » ou de « relation suivie dans le temps », central à tout repositionnement vers un usage CFO externe multi-clients, n'existe aujourd'hui que sous la forme d'un champ d'énumération optionnel sur `Entity`.

---

**DOMAIN MODEL OBSERVÉ.
AUCUNE MODIFICATION EFFECTUÉE.**
