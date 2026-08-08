# STRATEGIC_DEFERRED_WORK_REGISTER.md

**Nature :** registre canonique, append-only pour l'historique des décisions, mise à jour autorisée pour le statut courant. Aucun chantier n'est supprimé silencieusement — chaque entrée reste ouverte, fusionnée, remplacée, rejetée avec justification, ou maintenue en attente avec un déclencheur explicite. Aucun code modifié, aucun chantier rouvert par ce document.

**Règle de fond :** différer ne signifie jamais oublier. Toute décision de mise en attente conserve sa justification, ses dépendances et son événement de réouverture.

---

## Catégorie 1 — Fondations bloquantes

### 1.1 Architecture des agents IA (Reasoning Reliability)
- **Nature :** fondation bloquante.
- **Source :** Vision Sprint 1 (`REASONING_RELIABILITY_REVIEW.md`, `REASONING_ARCHITECTURE_OPTIONS.md`, `REASONING_CONFIDENCE_MODEL.md`), branches Vision Sprint non fusionnées.
- **État réel :** conçu (3 options d'architecture posées), non approuvé, non commencé en code.
- **Pourquoi différé :** la chaîne actuelle (Evidence Graph → Financial Analyst → Strategic CFO → Analysis → Verification, confirmée séquentielle par le Vision Sprint) crée un risque d'ancrage documenté — le refondre exige des contrats de sortie stables (faits normalisés, provenance, niveau de confiance, contexte temporel, contradictions, inconnues explicites) qui n'existent pas encore.
- **Dépendances réelles :** Evidence Ledger restauré et consommé, Financial Time Engine (au moins `PeriodObservation`/`FiscalPeriod`), contrats de sortie stabilisés.
- **Ce qu'il bloque :** toute construction fiable de Recommendation Engine, Attention Score, Enterprise Familiarization sur un raisonnement dont on sait déjà qu'il encourage la reproduction plutôt que la contestation d'une première conclusion.
- **Déclencheur de réouverture :** gate obligatoire avant la migration définitive du pipeline d'analyse — explicitement après le cas vertical FTE Phidani, pas avant.
- **Risque si rouvert trop tôt :** reconstruire une « équipe de recherche » avant d'avoir stabilisé les dossiers et preuves qu'on lui remet — effort perdu, deuxième réécriture probable.
- **Risque si rouvert trop tard :** Recommendation, Attention Score et Enterprise Familiarization construits sur un pipeline de raisonnement déjà su insuffisant — dette architecturale transmise en aval.
- **Ordre relatif :** après cas vertical FTE Phidani, avant Recommendation/Decision/Attention. Position fixe dans la séquence posée par Fred, pas de date.

### 1.2 Engagement (T2A)
- **Nature :** fondation bloquante — **close (mise à jour 2026-08-07).**
- **Source :** ADR-002 (ACCEPTED, cardinalité amendée §0), branche `implementation/t2a-engagement-2026-08-07` (harvest chirurgical de `feature/t2a-engagement-persistence`).
- **État réel (mise à jour 2026-08-07) :** T1C-A, T1C-B et T2A tous mergés dans `main` (`3b1b21a`, `0741a03`, `f5f00bf`). Revue adversariale T2A (verdict A) puis arbitrage de cardinalité Entity:Engagement passés avant fusion. Table `engagements` réelle, création atomique Entity+Engagement câblée sur les deux chemins (RPC applicative, trigger d'inscription), backfill idempotent disponible. Baseline post-merge : 1028 passed / 8 échecs préexistants / 1 skip (988 + 40 nouveaux tests Engagement).
- **Pourquoi différé :** n'est plus différé — fondation livrée. Les deux items ci-dessous (1.2.a, 1.2.b) sont les chantiers de suivi identifiés par l'arbitrage, pas des blocages restants sur T2A lui-même.
- **Dépendances réelles :** aucune restante pour la fondation elle-même.
- **Ce qu'il bloque :** plus rien directement — débloque `DecisionArc.engagement_id`, premier incrément FTE, Enterprise Familiarization.
- **Ordre relatif :** 1er, avant Evidence Ledger — exécuté dans cet ordre (T1C-A → T1C-B → T2A).

#### 1.2.a — Cardinalité Entity:Engagement : contrainte transitoire à relâcher plus tard
- **Nature :** dette de suivi issue de l'arbitrage de cardinalité (2026-08-07), pas un défaut de T2A.
- **Source :** Revue adversariale T2A pré-fusion + arbitrage dédié « Final Engagement Cardinality Arbitration » (2026-08-07) ; position canonique enregistrée dans ADR-002 §0.
- **État réel :** `UNIQUE(entity_id)` sur `engagements` (migration v19) reste en place. Reclassé : ce n'est plus tenu pour un invariant de domaine permanent, seulement une contrainte d'implémentation transitoire — la vérité de domaine acceptée est **une Organisation peut avoir plusieurs Engagements au cours de sa vie**, l'identité d'un Engagement suivant la continuité du mandat professionnel, pas la durée de vie de l'Organisation.
- **Pourquoi différé :** aucun chemin de code réel ne crée aujourd'hui un second Engagement pour une Entity existante — relâcher la contrainte maintenant serait une anticipation sans besoin démontré (Article IX).
- **Dépendances réelles :** aucune technique — dépend uniquement de l'apparition d'un premier besoin produit réel.
- **Ce qu'il bloque :** rien aujourd'hui. **Précision (Decision Memory Integrity Repair, auto-revue Phase 19, 2026-08-08) :** `arc_service.py::_resolve_current_engagement_id` déduit l'Engagement courant depuis `entity_id` (via un unique `engagements.entity_id` lookup) — correct tant que cette contrainte `UNIQUE(entity_id)` tient. Le jour où elle est relâchée, cette fonction (pas le champ `decision_arcs.entity_id` lui-même, qui reste valide comme référence de regroupement/affichage pour Portfolio Intelligence) devra être revue : `entity_id` seul ne suffira plus à déterminer *quel* Engagement est concerné.
- **Déclencheur de réouverture :** **la première fonctionnalité qui a besoin de créer un second mandat professionnel pour une Organisation existante** (ex. : reprise de relation avec mandat matériellement différent, remplacement de CFO sans rupture, cas D/F du test de personas de l'arbitrage).
- **Action requise à ce moment-là :** remplacer `UNIQUE(entity_id)` permanent par la stratégie retenue — plusieurs Engagements par Entity autorisés, mais au plus un Engagement courant/non-`churned` là où la sémantique de domaine l'exige (index unique partiel plutôt que contrainte absolue). Ceci est une direction, pas une autorisation d'implémentation. Réévaluer à ce moment si une chaîne de filiation explicite (`previous_engagement_id`) est réellement nécessaire — ne pas la construire avant.
- **Risque trop tôt :** construire une cardinalité multiple et une logique de filiation sans aucun consommateur réel — sur-ingénierie spéculative, exactement le défaut initialement reproché à l'Alternative 4 rejetée.
- **Risque trop tard :** un premier cas réel de mandat différent forcerait soit une mauvaise modélisation (fusion dans l'Engagement existant), soit une correction en urgence sous pression produit plutôt qu'une évolution planifiée.
- **Ordre relatif :** aucun — attend son déclencheur, pas une place dans la séquence actuelle.

#### 1.2.b — Perte de résolution Evidence/DecisionArc après suppression d'Entity
- **Nature :** dette de suivi issue de la revue adversariale T2A (2026-08-07), héritée de T1 (non introduite ni aggravée par T2A).
- **Source :** Revue adversariale T2A pré-fusion, Missions 7 et 15.
- **État réel :** `engagements.entity_id` est `ON DELETE CASCADE` (v19) ; `evidence_ledger_entries.entity_id` et `decision_arcs.entity_id` sont `ON DELETE SET NULL` (v18, v16 — comportement pré-existant, inchangé par T2A). Conséquence : la suppression d'une Entity détruit son Engagement (CASCADE) tandis que les lignes Evidence/DecisionArc survivent avec `entity_id` à `NULL` — les faits bruts persistent (conforme à « la vérité financière persiste ») mais deviennent **définitivement non résolubles** vers un Engagement, même si celui-ci existait au moment de la suppression.
- **Pourquoi différé :** aucun chemin de production ne dépend aujourd'hui de cette résolution (ADR-001 §8) — le risque est réel mais dormant.
- **Dépendances réelles :** décision architecturale future sur l'ownership direct de l'Evidence Ledger par Engagement (ADR-001A).
- **Ce qu'il bloque :** rien aujourd'hui ; bloquerait un futur audit ou une future reconstruction d'historique si la suppression d'Entity a déjà eu lieu.
- **Déclencheur de réouverture :** le premier incrément qui fait de l'Evidence Ledger un consommateur réel (au même moment que 1.3), ou toute décision produit sur la suppression réelle de comptes utilisateurs (GDPR).
- **Action requise à ce moment-là :** évaluer si Evidence/DecisionArc doivent recevoir une colonne `engagement_id` directe (plutôt que la résolution actuelle par jointure via `entity_id`), avec sa propre politique `ON DELETE` indépendante de celle d'Entity — une propriété directe par Engagement rendrait ce problème plus facile à résoudre proprement que la jointure dérivée actuelle, mais reste une décision architecturale à part entière, pas une correction technique mineure.
- **Risque trop tôt :** aucun — rien à corriger sans consommateur réel.
- **Risque trop tard :** une suppression réelle d'Entity avant la correction rendrait la perte d'historique irréversible pour les lignes déjà orphelines.
- **Ordre relatif :** aligné sur 1.3 (Evidence Ledger — premier consommateur réel).

### 1.3 Evidence Ledger (T1)
- **Nature :** fondation bloquante.
- **Source :** ADR-001/001A, branches `feature/t1c-a-evidence-capture`, `feature/t1c-b-atomic-financial-facts`.
- **État réel (mise à jour 2026-08-07) :** T1C-A mergé (`3b1b21a`, revue adversariale verdict A) et T1C-B mergé (`0741a03`, revue adversariale verdict A). Table `evidence_ledger_entries` réelle sur `main`, strictement additive, non encore lue par aucun chemin de production (ADR-001 §8 toujours vrai). Baseline post-merge : 988 passed / 8 échecs préexistants / 1 skip.
- **Pourquoi différé :** n'est plus différé pour la capture elle-même — reste différé pour son premier consommateur réel.
- **Dépendances réelles :** aucune bloquante technique restante pour un premier consommateur.
- **Ce qu'il bloque :** consommateur pilote (citation en lecture seule dans Review Briefing ou Decision Memory), premier incrément FTE.
- **Déclencheur de réouverture (consommateur) :** immédiatement après Engagement (T2A), avec consommateur réel livré dans le même incrément — règle déjà posée dans `FOUNDATION_RECOVERY_REVIEW.md` pour éviter le sort de `financial_truth.py`.
- **Risque trop tôt :** aucun.
- **Risque trop tard :** `financial_truth.py` reste un précédent vivant de code dormant — répéter l'erreur devient plus probable plus on attend.
- **Ordre relatif :** 2e — désormais exécuté.

**Dette de suivi issue de la revue adversariale T1C-A/T1C-B (2026-08-07), à ne pas perdre avant tout futur consommateur :**
1. `fact_id` (T1C-B, `build_fact_id()`) est une **empreinte de contenu**, pas une identité métier — confirmé empiriquement (deux périodes distinctes avec un libellé générique identique produisent le même `fact_id`). **Aucune implémentation future ne doit utiliser l'égalité de `fact_id` comme preuve que deux faits financiers, à travers analyses/périodes/organisations/Engagements, sont le même fait métier** — ni l'inégalité comme preuve du contraire. Propriétaire probable : futur incrément Evidence / Exception & Reconciliation.
2. `currency` retombe silencieusement sur `"EUR"` en l'absence de détection LLM, sans état `UNKNOWN` ni tag de source (contrairement au pattern déjà existant `GrossMarginSource` dans le même fichier). Propriétaire probable : futur incrément Evidence / Data ingestion.
3. Désaccord entre `amount` structuré (LLM) et montant legacy parsé depuis le texte narratif n'est jamais détecté ni loggé. Propriétaire probable : Exception & Reconciliation.
4. `fact_ids` dupliqués dans une même référence produisent des `SourceReference` dupliquées (inoffensif, non testé). Propriétaire probable : futur incrément Evidence.
5. L'Evidence Graph n'a pas de champ période structuré — cause racine du point 1. Propriétaire probable : futur incrément Evidence (changement de prompt/schéma).
6. La persistance non-bloquante de l'Evidence Ledger doit être revue (retry durable ou blocage explicite) **avant** qu'un consommateur réel ne dépende de sa fiabilité — acceptable tant qu'ADR-001 §8 reste vrai (aucun chemin de production ne la lit). Propriétaire probable : Trust Platform / futur incrément Evidence.
7. La propriété conceptuelle de l'Evidence Ledger reste l'Engagement (ADR-001A) ; l'ownership transitoire via `entity_id` doit être réattribuée explicitement dès qu'Engagement existe physiquement — **pas automatiquement lors de T2A** sauf si l'exécution de T2A le requiert explicitement.

#### 1.3.a — Sémantique des issues de capture Evidence (Evidence Capture Outcome Semantics)
- **Nature :** dette de suivi issue de la revue adversariale du premier consommateur réel de l'Evidence Ledger (Evidence Consumer #1, Review Briefing, 2026-08-07), pas un défaut de ce consommateur lui-même.
- **Source :** Revue adversariale Evidence Consumer #1 pré-fusion (2026-08-07) + mission de correction finale associée.
- **État réel :** confirmé structurellement, via table de vérité, que l'absence d'une ligne `evidence_ledger_entries` pour une analyse est aujourd'hui indiscernable entre trois causes distinctes : analyse antérieure à T1C-A (pré-Ledger), capture Evidence Graph légitimement vide, et échec d'écriture non-bloquant (`save_evidence_capture`). `evidence_integrity_service.py` (observabilité, voir 1.3 point 6) donne un signal agrégé, jamais une classification par ligne.
- **Pourquoi différé :** aucun consommateur aujourd'hui ne dépend de la présence d'Evidence pour produire une décision — Evidence Consumer #1 (Review Briefing) est strictement optionnel et dégrade honnêtement en son absence (Mission 8 de sa mission d'implémentation). Construire un mécanisme d'état maintenant serait prématuré (Article IX) — aucun besoin démontré ne l'exige encore.
- **Dépendances réelles :** aucune technique — dépend uniquement de l'apparition d'un premier consommateur dont la justesse dépend de la présence d'Evidence.
- **Ce qu'il bloque :** rien aujourd'hui.
- **Déclencheur de réouverture :** **avant tout futur consommateur dont la justesse dépend de la présence d'Evidence** (c'est-à-dire un consommateur qui ne peut pas simplement dégrader honnêtement en cas d'absence, contrairement à Review Briefing).
- **Direction préférée à ce moment-là (non-autorisation d'implémentation) :** un mécanisme additif minimal enregistrant uniquement les issues non-succès (`empty`/`failed`) dans les branches `except`/retour anticipé déjà existantes de `save_evidence_capture` — le succès ne reçoit jamais de marqueur explicite, il reste toujours déduit de la seule existence de la ligne Evidence, pour ne jamais créer une deuxième source de vérité. Ceci est une direction nommée par la revue adversariale, **pas une autorisation d'implémentation** — à réévaluer au moment du déclencheur, pas à construire par anticipation.
- **Risque trop tôt :** construire une table d'état pour un besoin encore hypothétique — sur-ingénierie spéculative.
- **Risque trop tard :** un futur consommateur dont la correction dépend réellement de cette distinction hériterait silencieusement de la même ambiguïté que Review Briefing a pu se permettre d'ignorer sans risque.
- **Ordre relatif :** aucun — attend son déclencheur, pas une place dans la séquence actuelle.

#### 1.3.b — Provenance Evidence au niveau de l'assertion (Assertion-Level Evidence Linking)
- **Nature :** dette de suivi issue de la revue adversariale d'Evidence Consumer #1 (2026-08-07), distinction centrale de cette revue.
- **Source :** Revue adversariale Evidence Consumer #1 pré-fusion (2026-08-07) — distinction nommée explicitement par Fred avant même la revue : « cette preuve justifie cette recommandation précise » (niveau assertion) contre « cette preuve appartient à l'analyse dont cette recommandation est issue » (niveau contexte d'analyse).
- **État réel :** aujourd'hui, `evidence_ledger_entries` se rattache à une analyse (`analyse_id`) — pas à une recommandation ni à une assertion individuelle. Evidence Consumer #1 (Review Briefing) ne peut donc légitimement offrir que du contexte au niveau de l'analyse, jamais une justification directe d'une recommandation précise. Corrigé dans la mission de correction finale : le libellé UI ne doit plus jamais impliquer le contraire (« Voir la preuve » → « Éléments de l'analyse source »).
- **Pourquoi différé :** aucune fonctionnalité produit aujourd'hui ne revendique une provenance au niveau assertion/recommandation — construire ce lien maintenant n'aurait aucun consommateur réel.
- **Dépendances réelles :** modèle de données reliant explicitement une recommandation/assertion à son ou ses faits sources (n'existe pas aujourd'hui).
- **Ce qu'il bloque :** rien aujourd'hui.
- **Déclencheur de réouverture :** **la première fonctionnalité produit qui revendique une provenance au niveau assertion ou recommandation** (ex. : « cette recommandation s'appuie précisément sur ce fait chiffré »). Jusqu'à ce moment, **toute UX Evidence doit rester au niveau contexte d'analyse**, jamais présentée comme justification directe d'une assertion précise.
- **Risque trop tôt :** construire un lien recommandation→fait sans consommateur réel ni modèle de confiance éprouvé pour ce niveau de granularité.
- **Risque trop tard :** une fonctionnalité future pourrait réutiliser par erreur le contexte d'analyse existant comme s'il constituait déjà une preuve au niveau assertion — répéter exactement le défaut nommé par cette revue.
- **Ordre relatif :** aucun — attend son déclencheur, pas une place dans la séquence actuelle.

### 1.6 DecisionArc ↔ Engagement
- **Nature :** fondation bloquante — **rattachement relationnel close (mise à jour 2026-08-08).**
- **Source :** revue adversariale dédiée (2026-08-07/08), branche `implementation/decisionarc-engagement-2026-08-07`, mergée `8db6070`.
- **État réel :** `decision_arcs.engagement_id` (nullable, additif) résolu de façon strictement déterministe (`origin_analysis_id → analyses.entity_id → engagements.entity_id`). DecisionArc reste son propre agrégat racine ; Engagement est une ancre de continuité, pas une composition (`ON DELETE SET NULL`). Backfill idempotent disponible. Baseline post-merge : 1076 passed / 8 échecs préexistants / 1 skip.
- **Pourquoi différé :** n'est plus différé pour le rattachement lui-même — fondation livrée. Les deux défauts ci-dessous sont des chantiers de réparation identifiés PAR cette revue, préexistants, non introduits par elle.
- **Ce qu'il bloque :** plus rien directement pour l'attachement lui-même.
- **Ordre relatif :** exécuté juste après Evidence Consumer #1, avant FTE.

#### 1.6.a — `decision_arcs.entity_id` jamais peuplé par le chemin de création réel
- **Nature :** défaut d'intégrité préexistant, découvert (pas introduit) par la revue adversariale DecisionArc ↔ Engagement — **RÉPARÉ ET TESTÉ, EN ATTENTE DE FUSION** (branche non fusionnée, décision de fusion réservée à Fred).
- **Source :** revue adversariale DecisionArc ↔ Engagement (2026-08-08), confirmée empiriquement (`build_portfolio_briefing()` exécuté contre un arc façonné exactement comme le chemin de création réel produit → zéro carte).
- **État réel :** `create_arc_from_feedback()` accepte `entity_id` en paramètre optionnel, mais son unique appelant réel (`routers/decision_memory.py::submit_decision_feedback`) ne le fournit jamais. Conséquence probable en production : Portfolio Intelligence vide, filtre `entity_id` du Briefing de revue sans effet.
- **Dépendances réelles :** aucune — correction indépendante du reste de la séquence.
- **Ce qu'il bloque :** Portfolio Intelligence, filtrage du Briefing de revue par client — potentiellement déjà cassés en production aujourd'hui.
- **Réparation :** branche `implementation/decision-memory-integrity-repair-2026-08-08`, source de résolution = `origin_analysis_id → analyses.entity_id` (même mécanisme que la résolution `engagement_id`, pas un second mécanisme indépendant).
- **Ordre relatif :** en réparation immédiate, avant tout chantier suivant.

#### 1.6.b — `origin_analysis_id` : contradiction `NOT NULL` + `ON DELETE SET NULL`
- **Nature :** défaut d'intégrité préexistant (v16), découvert par la revue adversariale DecisionArc ↔ Engagement — **RÉPARÉ ET VALIDÉ EMPIRIQUEMENT, EN ATTENTE DE FUSION**.
- **Source :** revue adversariale DecisionArc ↔ Engagement (2026-08-08), tracée jusqu'à la route réelle `DELETE /api/analyses/history`.
- **État réel :** `decision_arcs.origin_analysis_id` est déclaré `NOT NULL REFERENCES analyses(id) ON DELETE SET NULL` — combinaison contradictoire en Postgres. Un utilisateur ayant au moins un DecisionArc suivi ne peut aujourd'hui pas vider son historique d'analyses (l'opération échoue par violation de contrainte, transaction annulée).
- **Portée réelle, précisée par la revue adversariale finale (2026-08-08) :** ce défaut ne bloquait pas seulement `DELETE /api/analyses/history` — `DELETE /account` (`routers/auth.py:287`, érasure RGPD complète) supprime aussi `analyses` (étape 3) **avant** de supprimer `companies` (étape suivante). Pour toute company possédant au moins un DecisionArc CLOSED, cette étape échouait donc de la même manière, ce qui pouvait bloquer l'érasure RGPD complète elle-même, pas seulement le nettoyage d'historique ordinaire.
- **Dépendances réelles :** aucune — correction indépendante.
- **Ce qu'il bloque :** `DELETE /api/analyses/history` ET `DELETE /account` pour tout utilisateur/company avec au moins un DecisionArc suivi.
- **Réparation :** branche `implementation/decision-memory-integrity-repair-2026-08-08`, commit `91c7d65` — `origin_analysis_id` devient nullable (nouvelle migration additive `v22`, v16 non réécrite), avec un second carve-out dans `arc_immutability_guard()` séparé de celui de `v21`, permettant précisément la transition `origin_analysis_id : valeur → NULL` sur un arc CLOSED, déclenchée par l'action FK `ON DELETE SET NULL` — cette même action FK est celle exécutée par `DELETE /api/analyses/history` ET par l'étape "analyses" de `DELETE /account` : v22 résout les deux routes par le même mécanisme, sans distinction de route, en préservant la mémoire DecisionArc dans les deux cas (seule `DELETE /account` va plus loin et détruit ensuite le DecisionArc via `company_id ON DELETE CASCADE`, à l'étape "companies").
- **RÉSERVE DE VALIDATION — LEVÉE (2026-08-08) :** validée empiriquement contre un vrai moteur Postgres, avec autorisation explicite et ponctuelle de Fred, sur le projet Supabase dédié « Pepperyn Integration Test » (`ejixkplrgobgwqnhidwt`, jamais le projet de production), migrations `v16` → `v21` → `v22` appliquées une par une avec vérification après chacune. Deux scénarios validés : (1) suppression d'une Analysis référencée par un DecisionArc CLOSED → suppression réussie, arc survivant, `origin_analysis_id = NULL`, tous les autres champs strictement inchangés (y compris `updated_at`) ; (2) tentative de modification d'un champ protégé non lié sur le même arc CLOSED → refusée par le trigger. Idempotence du DDL vérifiée. Données de test isolées, nettoyées ensuite ; données préexistantes du projet vérifiées identiques avant/après. Détail complet dans `backend/migrations/v22_decision_arc_origin_analysis_nullable.sql`.
- **Ordre relatif :** réparation, tests et validation Postgres réelle terminés. Prêt pour revue de code et décision de fusion — aucune fusion n'a été effectuée par cette validation.

#### 1.6.c — `entity_id`/`engagement_id` : même classe d'interaction FK/trigger, symétrique et non couverte
- **Nature :** défaut latent découvert par la revue adversariale finale de Decision Memory Integrity Repair (2026-08-08) — **DORMANT, différé, pas une régression de cette mission**.
- **Source :** revue adversariale finale, Mission 9 (recherche exhaustive des FK sur `decision_arcs` et de leur interaction avec `arc_immutability_guard()`).
- **État réel :** sur un DecisionArc CLOSED, `entity_id` (`ON DELETE SET NULL`, v16) et `engagement_id` (`ON DELETE SET NULL`, v21) pourraient chacun être rejetés par `arc_immutability_guard()` si leur Entity/Engagement référencé était supprimé — car aucun carve-out ne couvre la transition `entity_id : valeur → NULL` ni `engagement_id : valeur → NULL` (le carve-out 1, v21, ne couvre que `engagement_id : NULL → valeur` ; le carve-out 2, v22, ne couvre que `origin_analysis_id : valeur → NULL`). C'est exactement la même classe de contradiction FK/trigger que le défaut 1.6.b, en miroir sur deux autres colonnes.
- **Dormant aujourd'hui :** aucune route `DELETE Entity` ni `DELETE Engagement` n'existe dans le produit (vérifié par recherche exhaustive dans `backend/routers/` — les deux seules routes DELETE du dépôt sont `DELETE /api/analyses/history` et `DELETE /account`). Ce défaut ne peut donc être déclenché par aucun chemin de production actuel.
- **Pourquoi différé :** implémenter un troisième carve-out maintenant, pour des routes qui n'existent pas, serait une anticipation sans besoin démontré (Article IX) — exactement le type de sur-construction que ce dépôt évite systématiquement.
- **Dépendances réelles :** aucune technique.
- **Ce qu'il bloque :** rien aujourd'hui.
- **Déclencheur de réouverture :** la conception ou l'implémentation d'une première capacité `DELETE Entity` ou `DELETE Engagement` en production.
- **Action requise à ce moment-là :** revoir ensemble, dans le même geste, la sémantique de suppression SQL (FK/`ON DELETE`) et l'immutabilité des arcs CLOSED — ne pas construire l'un sans l'autre, sur le modèle de 1.6.b (un carve-out étroit et séparé, jamais une exception générique de mutation).
- **Ordre relatif :** aucun — attend son déclencheur.

### 1.4 Vérité temporelle (Financial Time Engine)
- **Nature :** fondation bloquante (kernel Supporting, pas Core — déjà tranché).
- **Source :** ADR-003 v3, jamais promu ACCEPTED.
- **État réel :** conçu (design complet, 9 sections), revu (auto-critique 9/10), non approuvé formellement, non implémenté.
- **Pourquoi différé :** doctrine prête mais implémentation jugée prématurée avant Engagement et Evidence Ledger réels.
- **Dépendances réelles :** Engagement restauré et consommé, Evidence Ledger restauré et consommé, normalisation des périodes.
- **Mise à jour (Canonical Foundation & Execution Orchestration Sprint) :** `temporal_normalizer.py` audité en profondeur — voir `TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md`. **Risque de doublon levé : ce n'est pas un doublon**, c'est un classificateur d'en-têtes de colonnes (couche Percevoir), fournisseur naturel du futur `PeriodObservation`, pas un concurrent du FTE. Gate E du `PRE_IMPLEMENTATION_GATE_CHECKLIST.md` est passé sur cette base.
- **Ce qu'il bloque :** cas vertical Phidani, indirectement l'architecture des agents (contexte temporel dans leurs contrats de sortie).
- **Déclencheur de réouverture :** cas vertical Phidani, limité à `PeriodObservation`/`FiscalPeriod` — pas `BusinessHistory`, pas `FutureBusinessMoment` (déjà tranché dans `FOUNDATION_RECOVERY_REVIEW.md`). Séquencement précisé dans `FOUNDATION_RECOVERY_EXECUTION_ORDER.md` : T1C-A → T1C-B → T2A avant ce chantier, par risque d'exécution croissant, pas par importance relative.
- **Risque trop tôt :** construire sur un modèle abstrait plutôt que sur des données réelles d'un client réel.
- **Risque trop tard :** aucun risque de doublon résiduel — seul risque restant : `temporal_normalizer.py` n'est pas encore explicitement branché comme fournisseur du FTE au moment de l'implémentation (action technique simple, pas un arbitrage).
- **Ordre relatif :** 3e, avant l'architecture des agents.

### 1.5 Anonymisation et Trust & Platform
- **Nature :** fondation bloquante — **nouvellement qualifiée comme telle par cette session**, elle n'était pas dans la liste initiale de Fred sous cette étiquette précise.
- **Source :** `ANONYMIZATION_CAPABILITY_REVIEW.md`, `LEGACY_CAPABILITY_PRESERVATION_POLICY.md` (Mission 1).
- **État réel :** partiellement implémenté — mécanisme correct, couverture incomplète, 4 chemins vérifiés dont 2 non conformes.
- **Pourquoi différé :** découvert et documenté dans cette session même, correction non encore arbitrée.
- **Dépendances réelles :** aucune — le correctif est techniquement indépendant du reste de la séquence.
- **Ce qu'il bloque :** rien en aval, mais **son report au-delà d'un délai raisonnable est lui-même un risque**, pas seulement une dépendance à gérer.
- **Déclencheur de réouverture :** décision humaine sur la priorité relative face à la restauration T1/T2 — recommandation explicite : traiter en parallèle, indépendamment de la séquence Engagement→Evidence→FTE, puisqu'aucune dépendance ne les lie techniquement.
- **Risque trop tôt :** aucun — c'est un correctif ciblé, pas une reconstruction.
- **Risque trop tard :** écart persistant entre promesse commerciale de confidentialité et comportement réel du code, sur le chemin de chat aujourd'hui préféré.
- **Ordre relatif :** en parallèle de la séquence principale, pas dans la séquence elle-même.

---

## Catégorie 2 — Capacités métier différées

### 2.1 Enterprise Familiarization
- **Nature :** capacité métier.
- **Source :** Profession Model, cartographie d'implémentation (« doit écrire dans un Knowledge Model possédé par Engagement »).
- **État réel :** conçu conceptuellement, non implémenté.
- **Pourquoi différé :** son propriétaire de données (Engagement) n'existe pas encore sur `main`.
- **Dépendances :** Engagement, Evidence, FTE.
- **Ce qu'il bloque :** rien en amont ; bloqué par tout ce qui précède.
- **Déclencheur de réouverture :** après restauration T1/T2.
- **Risque trop tôt :** écrire dans un Knowledge Model qui n'a pas encore de propriétaire stable — recréerait le problème `origin_analysis_id` déjà résolu par la note de migration DecisionArc→Engagement.
- **Risque trop tard :** aucun risque particulier identifié — capacité non urgente commercialement selon les sprints produit précédents.
- **Ordre relatif :** après T1/T2, avant ou en parallèle du FTE.

### 2.2 Exception & Reconciliation
- **Nature :** capacité métier — Core selon le Domain Model, absente de toutes les phases T0-T6 du Blueprint (écart déjà documenté par la cartographie d'implémentation, non résolu ici).
- **Source :** Ideal/Current Domain Model.
- **État réel :** non commencé.
- **Pourquoi différé :** aucune phase du Blueprint ne la porte — écart de planification plus que report délibéré.
- **Dépendances :** Evidence Ledger, FTE (pour dater les écarts).
- **Ce qu'il bloque :** rien de nommé actuellement, mais son statut Core au Domain Model sans aucune phase porteuse est lui-même une anomalie à signaler à Fred, pas seulement une entrée de registre.
- **Déclencheur de réouverture :** non défini — **réserve explicite : ce chantier n'a même pas de déclencheur nommé, contrairement à la règle du registre.** À demander à Fred.
- **Risque trop tôt / trop tard :** non évaluable sans clarification de sa place dans le Blueprint.
- **Ordre relatif :** indéterminé, à clarifier en priorité sur la forme (pourquoi absent du Blueprint) avant de discuter du fond.

### 2.3 Recommendation Engine
- **Nature :** capacité métier.
- **Source :** Capability Roadmap v1, code actuel (`decision_rules.py`, `executive_decision_model.py`).
- **État réel :** partiellement implémenté — une chaîne de décision structurée existe déjà (WP5C, Phase 9), mais construite sur le pipeline de raisonnement séquentiel jugé insuffisant.
- **Pourquoi différé :** attend l'architecture des agents révisée pour ne pas reconstruire deux fois.
- **Dépendances :** architecture des agents, FTE, Engagement.
- **Ce qu'il bloque :** Attention Score (qui en dépend conceptuellement).
- **Déclencheur de réouverture :** après Architecture Review des agents IA.
- **Risque trop tôt :** construire sur un pipeline qu'on sait devoir remplacer.
- **Risque trop tard :** le code existant (`decision_rules.py` etc.) continue d'accumuler de la dette invisible.
- **Ordre relatif :** après architecture des agents.

### 2.4 Attention Score
- **Nature :** capacité métier, Core Domain potentiel — concept non suffisamment éprouvé (formulation de Fred, reprise telle quelle, cohérente avec le principe de non-dogmatisme du Profession Model).
- **Source :** ADR-003 (mentionné), Profession Model.
- **État réel :** non commencé — confirmé absent du code par la cartographie d'implémentation antérieure.
- **Pourquoi différé :** aucun consommateur réel, pas de revue d'architecture dédiée.
- **Dépendances :** Recommendation, FTE, Engagement.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** après consommateurs réels des fondations + revue d'architecture dédiée.
- **Risque trop tôt :** créer un objet Core sans preuve qu'il correspond à une responsabilité réelle du CFO — contraire au Model Fidelity Protocol.
- **Risque trop tard :** aucun identifié.
- **Ordre relatif :** après Recommendation Engine.

### 2.5 Decision Follow-up (Capability 3 Incrément 2)
- **Nature :** capacité métier.
- **Source :** `DECISION_FOLLOWUP_IMPLEMENTATION_PLAN.md`, recommandé comme prochain pas par `PROFESSION_MODEL_FOUNDATION_CLOSURE.md`.
- **État réel :** conçu, plan prêt, non implémenté.
- **Pourquoi différé :** arbitrage de séquencement posé dans `PRODUCT_BOARD_CANONICAL_ARBITRATION.md` (point d'arbitrage Fred n°1, non tranché) — ouverture possible en parallèle de l'import documentaire, ou après.
- **Dépendances :** aucune technique bloquante — plan indépendant de T1/T2.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** décision de Fred sur le point d'arbitrage n°1 de l'arbitrage Product Board — non redécidé ici, seulement recensé.
- **Risque trop tôt :** ouvrir un incrément produit pendant que la fondation documentaire et T1/T2 restent en chantier — risque déjà nommé dans l'arbitrage précédent.
- **Risque trop tard :** proxy de validation Outcome (« moins de recommandations non suivies ») reste sans preuve de terrain.
- **Ordre relatif :** en attente d'arbitrage explicite, pas de recommandation nouvelle ici.

### 2.6 Knowledge Model / BusinessHistory
- **Nature :** capacité métier, frontière DDD déjà challengée une fois cette session (question de propriété FTE vs Knowledge Model, non retranchée ici).
- **Source :** ADR-003 v3, discussion de frontière antérieure dans cette session.
- **État réel :** conçu conceptuellement (VO `BusinessHistory` dans ADR-003 v3), non implémenté.
- **Pourquoi différé :** dépend d'Engagement comme propriétaire potentiel — question de frontière ouverte, pas fermée.
- **Dépendances :** Engagement, Evidence.
- **Ce qu'il bloque :** Enterprise Familiarization (doit écrire dedans).
- **Déclencheur de réouverture :** après restauration T1/T2, au moment de trancher la frontière de propriété.
- **Risque trop tôt :** implémenter avant d'avoir tranché qui possède la responsabilité — répéterait le pattern déjà vu pour DecisionArc/Engagement.
- **Risque trop tard :** aucun majeur.
- **Ordre relatif :** avec Enterprise Familiarization.

---

## Catégorie 3 — Hypothèses produit

### 3.1 Partage par rôles / multi-organisations
- **Nature :** hypothèse produit.
- **Source :** `ORGANISATION_SHARING_DEMO_REVIEW.md`, prototype `frontend/app/demo/` uniquement.
- **État réel :** prototype (démo seulement, jamais en production).
- **Pourquoi différé :** besoin terrain non confirmé — démonstration seulement.
- **Dépendances :** organisations, permissions (Shell).
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** retour des tests utilisateurs externes.
- **Risque trop tôt :** construire une obligation architecturale sur une hypothèse non validée.
- **Risque trop tard :** aucun — pas d'engagement commercial pris sur cette capacité.
- **Ordre relatif :** après tests utilisateurs externes, hors séquence de fondation.

### 3.2 Certains Business Moments / présentation du cockpit
- **Nature :** hypothèse produit.
- **Source :** UI Specification Sprint, Portfolio Cockpit Review.
- **État réel :** conçu et partiellement implémenté (Portfolio Home réel et testé), affinements restants non commencés.
- **Pourquoi différé :** réserves UX déjà nommées dans le Product Board (2 items, « OBSERVE IN USER TESTING »).
- **Dépendances :** retour d'usage réel du Portfolio.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** External User Testing (déjà planifié comme prochaine étape produit).
- **Risque trop tôt :** raffiner sans données d'usage réelles.
- **Risque trop tard :** aucun.
- **Ordre relatif :** en cours, déjà engagé.

---

## Catégorie 4 — Vision et options stratégiques

### 4.1 Choix du modèle IA par l'utilisateur (BYOM / local)
- **Nature :** vision stratégique.
- **Source :** Vision Sprint, `VISION_SPRINT_CONCLUSION.md` (GO/NO-GO = Option B, long terme uniquement).
- **État réel :** non commencé, verdict déjà rendu (ne pas construire maintenant).
- **Pourquoi différé :** impacts opérationnels et qualité non résolus ; dépend de l'architecture des agents et d'une politique Trust encore à écrire.
- **Dépendances :** architecture des agents, Reasoning Reliability Architecture, politique Trust & Platform (nouvellement nommée cette session).
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** après Reasoning Reliability Architecture — déjà fixé par Fred dans le message courant.
- **Risque trop tôt :** contaminer le build courant, exactement le risque nommé par Fred.
- **Risque trop tard :** aucun — option long terme assumée comme telle.
- **Ordre relatif :** dernier de la liste, explicitement.

### 4.2 Connecteurs ERP/API/MCP généralisés
- **Nature :** vision stratégique.
- **Source :** Vision Sprint (`TECHNICAL_PREREQUISITES.md`, `CONNECTIVITY_STRATEGY.md`).
- **État réel :** non commencé — confirmé absent du code réel (aucun connecteur trouvé au-delà de `FileConnector` local).
- **Pourquoi différé :** prérequis techniques non réunis, océan rouge identifié en partie sur ce terrain (Vision Sprint Decision Simulation Engine).
- **Dépendances :** architecture de données stabilisée (Evidence, FTE).
- **Ce qu'il bloque :** rien à court terme.
- **Déclencheur de réouverture :** non fixé précisément — à clarifier avec Fred si ce n'est pas déjà couvert par le GO/NO-GO Option B général.
- **Risque trop tôt :** construire une généralisation avant d'avoir un seul connecteur réel qui fonctionne.
- **Risque trop tard :** aucun identifié.
- **Ordre relatif :** vision long terme, hors séquence courante.

### 4.3 Simulation avancée (Decision Simulation Engine / ex-Marginn)
- **Nature :** vision stratégique.
- **Source :** `VISION_SPRINT_CONCLUSION.md`, GO/NO-GO = Option B.
- **État réel :** conçu, verdict déjà rendu (long terme uniquement, océan rouge vs Fathom Portfolio).
- **Pourquoi différé :** décision stratégique déjà prise et documentée.
- **Dépendances :** l'essentiel de la fondation Domain.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** 3 conditions déjà nommées dans `VISION_SPRINT_CONCLUSION.md` (non redétaillées ici, référencées).
- **Risque trop tôt / trop tard :** déjà traité dans le document source.
- **Ordre relatif :** vision, hors séquence courante.

### 4.4 Extension à d'autres professions
- **Nature :** vision stratégique.
- **Source :** North Star (Profession Model) — mentionné en creux, jamais traité comme un chantier à part entière dans les sessions précédentes.
- **État réel :** non commencé, non conçu.
- **Pourquoi différé :** le Profession Model lui-même n'a pas encore atteint son niveau de validation C (Outcome Validity) sur la profession CFO — l'étendre à une autre profession avant serait une violation directe du principe de non-dogmatisme.
- **Dépendances :** validation A/B/C du Profession Model CFO.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** non fixé — à nommer explicitement si ce chantier doit un jour redevenir actif, plutôt que de rester une intuition non datée.
- **Ordre relatif :** dernier de tous les chantiers listés.

---

## Catégorie 5 — Dette et migration (catégorie ajoutée, hors les 4 prévues par le mandat, justifiée ci-dessous)

Le mandat prévoyait 4 catégories. Une 5e est ajoutée ici parce que cette session a produit des découvertes qui ne sont ni des fondations bloquantes au sens strict (elles ne bloquent rien en aval), ni des capacités métier, ni des hypothèses produit, ni de la vision — ce sont des dettes techniques localisées, à traiter indépendamment de la séquence stratégique. Les y forcer dans une des 4 catégories prévues aurait dilué leur nature réelle.

### 5.1 Migration du legacy (programme transversal)
- **Nature :** dette/migration.
- **Source :** cette session — `LEGACY_MIGRATION_REVIEW_REPORT.md`.
- **État réel :** audit en cours, verdict B rendu (valide avec réserves nommées).
- **Pourquoi différé :** n'est pas différé — en cours, justement objet de cette mission.
- **Dépendances :** fondation canonique documentaire.
- **Ce qu'il bloque :** rien directement, mais conditionne la confiance dans toute capacité Shell conservée.
- **Déclencheur de réouverture :** sans objet — en cours.
- **Ordre relatif :** en cours.

### 5.2 Caches en mémoire non persistants (famille de dette)
- **Nature :** dette/migration.
- **Source :** `LEGACY_CAPABILITY_INVENTORY.md`, `LEGACY_CAPABILITY_REVIEW_MATRIX.md`.
- **État réel :** code dormant en risque, pas encore un incident.
- **Pourquoi différé :** découvert cette session, non encore priorisé face au reste.
- **Dépendances :** décision d'architecture sur le stockage cible (aucune prise à ce jour).
- **Ce qu'il bloque :** tout passage à une infrastructure multi-instance.
- **Déclencheur de réouverture :** dès qu'un scaling horizontal est envisagé, ou en préventif si Fred le priorise.
- **Ordre relatif :** non fixé, à arbitrer par Fred.

### 5.3 `temporal_normalizer.py` vs doctrine FTE
- **Résolu** — voir 1.4 pour la mise à jour complète. Risque de double vérité temporelle levé par `TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md`. Entrée conservée pour traçabilité, pas comme chantier encore ouvert.

### 5.4 Évolution des exports *(ajouté — Canonical Foundation & Execution Orchestration Sprint)*
- **Nature :** dette/migration.
- **Source :** `LEGACY_CAPABILITY_REVIEW_MATRIX.md` — exports classés KEEP avec « ADAPT anticipé quand Evidence Ledger/Engagement seront restaurés », déjà noté dans `T1_T2_RECOVERY_PLAN.md` sans entrée dédiée dans ce registre jusqu'ici — omission corrigée.
- **État réel :** fonctionnel aujourd'hui (PDF/PPTX/XLSX confirmés sans appel LLM, pure restitution de données déjà réelles), mais leur source de données changera une fois Evidence Ledger consommé.
- **Pourquoi différé :** aucune urgence — les exports actuels restent corrects tant que T1/T2 ne sont pas mergés.
- **Dépendances réelles :** Evidence Ledger (T1), Engagement (T2).
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** une fois T1/T2 mergés et consommés par au moins un écran (Review Briefing ou Portfolio) — migrer les renderers pour lire depuis Evidence Ledger plutôt que depuis `analysis_result` seul.
- **Risque trop tôt :** migrer les renderers avant que la nouvelle source de vérité (Evidence Ledger) ait un consommateur stable.
- **Risque trop tard :** les exports continuent de lire une structure qui deviendra progressivement secondaire, dette silencieuse.
- **Ordre relatif :** après T1/T2, avant tout enrichissement cognitif des exports.

### 5.5 Doublon `feedback.py` / `decision_memory.py` *(ajouté — Canonical Foundation & Execution Orchestration Sprint)*
- **Nature :** dette/migration.
- **Source :** `LEGACY_CAPABILITY_INVENTORY.md`, point 20 — « doublon potentiel à vérifier ».
- **État réel :** les deux mécanismes existent en parallèle, périmètres non comparés ligne à ligne.
- **Pourquoi différé :** découvert lors de l'audit legacy, non prioritaire face aux fondations bloquantes.
- **Dépendances réelles :** aucune — comparable indépendamment du reste de la séquence.
- **Ce qu'il bloque :** rien.
- **Déclencheur de réouverture :** disponibilité pour un audit ciblé d'une demi-journée — comparer les deux schémas de données et les deux points d'entrée frontend (déjà la recommandation de `LEGACY_CAPABILITY_REVIEW_MATRIX.md`).
- **Risque trop tôt :** aucun.
- **Risque trop tard :** les deux mécanismes divergent davantage avec le temps, rendant la comparaison future plus coûteuse.
- **Ordre relatif :** non urgent, peut être traité à tout moment indépendamment de la séquence de fondation.

---

## Ce que ce registre ne fait pas
Ne rouvre aucun chantier. Ne fixe aucune date calendaire — seulement un ordre relatif et des déclencheurs événementiels, conformément à la consigne. Ne tranche pas l'arbitrage Decision Follow-up déjà posé dans `PRODUCT_BOARD_CANONICAL_ARBITRATION.md` — le recense sans le redécider. Signale une anomalie non couverte par le mandat initial (Exception & Reconciliation sans déclencheur nommé) plutôt que de l'inventer.

---

**STRATEGIC_DEFERRED_WORK_REGISTER ÉTABLI. APPEND-ONLY POUR L'HISTORIQUE, STATUT COURANT MODIFIABLE. AUCUN CHANTIER ROUVERT.**
