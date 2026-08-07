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
- **Nature :** fondation bloquante.
- **Source :** ADR-002 (ACCEPTED), branche `feature/t2a-engagement-persistence`.
- **État réel (mise à jour 2026-08-07) :** T1C-A et T1C-B mergés dans `main` (`3b1b21a`, `0741a03`), ordre de récupération T1 avant T2 désormais exécuté. T2A en cours de reconstruction chirurgicale (pas de fusion de branche entière) — voir Mission Engagement du même jour pour le détail du tri KEEP/ADAPT/REJECT.
- **Pourquoi différé :** fusion de branche entière écartée (127 fichiers dont 119 sans rapport, voir `T1_T2_RECOVERY_PLAN.md`) — reconstruction ciblée requise.
- **Dépendances réelles :** aucune bloquante restante — plan de récupération déjà écrit et vérifié, T1 désormais mergé.
- **Ce qu'il bloque :** rattachement `DecisionArc.engagement_id`, premier incrément FTE, Enterprise Familiarization.
- **Déclencheur de réouverture :** deuxième GO explicite de Fred, après validation de `CANONICAL_DOCUMENT_SET_PROPOSAL.md`.
- **Risque trop tôt :** aucun identifié — le chemin est déjà vérifié à faible risque technique.
- **Risque trop tard :** tout le reste de la séquence (Evidence Ledger, FTE, agents) reste bloqué indéfiniment.
- **Ordre relatif :** 1er, avant Evidence Ledger (ordre T1C-A → T1C-B → T2A déjà fixé dans `FOUNDATION_RECOVERY_REVIEW.md`).

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
