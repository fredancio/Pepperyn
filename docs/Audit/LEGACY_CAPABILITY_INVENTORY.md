# LEGACY_CAPABILITY_INVENTORY.md

**Nature :** Mission 4 — inventaire factuel, à partir du code réel de `main`, vérifié par lecture directe (routers, services, modèles, structure frontend). Pas de verdict ici — classification uniquement (capacité produit / infrastructure / garde-fou / dette / code dormant / doublon / expérimentation abandonnée). Les verdicts KEEP/STRENGTHEN/ADAPT/REPLACE/RETIRE/PARK sont dans `LEGACY_CAPABILITY_REVIEW_MATRIX.md`.

**Réserve de méthode :** cet inventaire est fondé sur les 12 routers, 24 services et 6 modèles backend et sur la structure `frontend/app/` réellement présente sur `main` au 2026-08-07. Il n'a pas la même profondeur de vérification que l'audit dédié de l'anonymisation (`ANONYMIZATION_CAPABILITY_REVIEW.md`) — certaines lignes indiquent explicitement « à vérifier plus profondément » plutôt que d'affirmer une couverture complète non constatée.

---

## 1. Authentification
- **PIN login** (`backend/routers/auth.py:36` `login_with_pin`, `:93` `send_pin_by_email`, `:216` `login_guest_with_email_and_pin`) — capacité produit. Mécanisme d'accès sans mot de passe classique ; confirmé dans une session antérieure comme mécanisme d'essai gratuit, pas de collaboration.
- **Suppression de compte RGPD** (`auth.py:287` `DELETE /account`) — garde-fou (obligation légale).
- **JWT invité** (`create_guest_jwt`, `security_config.get_jwt_guest_secret`) — infrastructure.

## 2. Paramètres
- `frontend/app/app/settings/` — capacité produit, présente et réelle sur `main`. Contenu détaillé non audité ligne à ligne dans cette mission.

## 3. Abonnements / Billing
- **Catalogue de plans** (`billing.py:111` `_build_plans_catalogue`, `:156` `GET /plans`) — capacité produit.
- **Usage** (`billing.py:165` `GET /usage`) — capacité produit, appuyée sur `usage_service.py`.
- **Checkout / Portal Stripe** (`billing.py:185`, `:238`) — infrastructure (intégration tierce).
- **Webhook Stripe** (`billing.py:250`) — garde-fou (synchronisation d'état de paiement).
- `frontend/app/app/billing/`, `frontend/app/checkout/`, `frontend/app/upgrade/` — capacité produit.

## 4. Quotas et limites
- `usage_service.py::UsageService` — capacité produit + garde-fou (limites par plan, ex. chat FREE 3 msg/analyse).
- `rate_limiter.py::InMemoryRateLimiter` — infrastructure, **en mémoire, non partagée entre instances** (même famille de risque que `_anonymization_cache`, voir Mission 5) — dette potentielle si le service est un jour multi-instance.

## 5. Organisations / Entités
- `entities.py:60` `GET /entities` (`list_entities`), `:102` `POST /entities` (`create_entity`) — capacité produit, cœur du modèle Company/Entity préexistant à Engagement (ADR-002).
- `relation_type` (filiale/client) — capacité produit, déjà croisée avec Engagement dans les sessions précédentes.

## 6. Invitations
- `backend/migrations/v9_invited_members.sql` — capacité produit (table de membres invités).
- `webhooks.py:18` `POST /webhooks/new-user` — garde-fou (provisionnement à la création de compte, lié à Engagement via `handle_new_user_engagement`, cf. migration v20 non fusionnée).

## 7. Historique
- `analyze.py:244` `DELETE /analyses/history` — garde-fou (droit à l'oubli partiel).
- `decision_memory.py` (router complet) — capacité produit, mémoire décisionnelle (feedback sur recommandations).
- Caches en mémoire `_export_cache`, `_pdf_cache`, `_pptx_cache`, `_analysis_result_cache` (`analyze.py`) — **infrastructure fragile** : stockage non persistant de résultats d'analyse et d'exports générés, perdu au redémarrage du processus. Pas un vrai stockage — dette technique nommée mais non quantifiée dans cette mission.

## 8. Upload / Parsing
- `FileConnector` (`connectors/`, invoqué depuis `analyze.py:463`) — capacité produit, gère `.xlsx/.xls/.csv/.pdf`.
- `file_parser.py` — capacité produit, appelle `llm_service` (confirmé par grep) — un des sites d'appel LLM à vérifier au même titre que les autres pour la couverture d'anonymisation, non audité en détail dans cette mission (hors périmètre pilote).

## 9. Anonymisation
- Voir `ANONYMIZATION_CAPABILITY_REVIEW.md` — traitée en profondeur séparément, verdict STRENGTHEN déjà rendu.

## 10. Appels LLM
- `llm_service.py::run_full_pipeline` — capacité produit, cœur du pipeline principal (2 appels Claude, confirmé dans les sessions précédentes).
- `llm_service.py::call_chat_intelligent` — capacité produit, chemin de chat legacy.
- `get_anthropic_client` — infrastructure.
- Sites d'appel LLM additionnels confirmés par grep mais non audités en détail cette session : `decision_rules.py`, `executive_decision_model.py`, `file_parser.py`, `financial_normalizer.py` — **réserve explicite : leur couverture par l'anonymisation n'a pas été vérifiée**, contrairement aux quatre chemins traités dans `ANONYMIZATION_CAPABILITY_REVIEW.md`. À traiter dans un futur incrément du protocole, pas supposé conforme.

## 11. Agents / Conversation
- `conversation_engine.py::get_chat_response` (Conversation Engine V2) — capacité produit, chemin de chat préféré. Contournement d'anonymisation déjà documenté (Mission 6).
- `executive_case_builder.py`, `executive_case_v2_builder.py` — capacité produit, construction déterministe (sans appel LLM, confirmé par le commentaire du code) de la structure consommée par le chat.
- `executive_decision_model.py`, `decision_kernel.py`, `decision_kernel_extractor.py`, `decision_fingerprint.py`, `decision_rules.py` — capacité produit, chaîne de décision structurée (WP5C, Phase 9 selon commentaires du code) — non ré-auditée ligne à ligne cette session, cohérente avec la cartographie d'implémentation antérieure.

## 12. Exports
- `excel_export.py`, `export_pdf_service.py`, `export_pptx_service.py` — capacité produit. Confirmé sans appel LLM (grep, zéro résultat) — pure restitution de données déjà réelles.

## 13. Stockage
- Aucun stockage Supabase Storage identifié dans cette session pour les fichiers uploadés ou générés — les exports vivent en cache mémoire du processus (`_export_cache` etc., voir point 7). **À vérifier explicitement dans un futur incrément : où sont réellement stockés les fichiers uploadés eux-mêmes après parsing ?** Non tranché ici.

## 14. Suppression de données
- `DELETE /analyses/history`, `DELETE /account` — garde-fou, déjà cités.

## 15. Logs
- `logging` standard Python, niveau module (`logger = logging.getLogger(__name__)` dans chaque fichier) — infrastructure. Contenu des logs vérifié pour `analyze.py`/`llm_service.py` dans le cadre de l'audit anonymisation (Mission 6) : pas de fuite de contenu détectée par grep, sans garantie architecturale contre une fuite future.

## 16. Sécurité générale
- `security_config.py::get_jwt_guest_secret` — infrastructure (secrets).
- JWT (`jose.jwt`) — infrastructure.
- RLS Supabase — non vérifié directement dans cette session (nécessiterait accès au dashboard Supabase ou aux policies SQL, hors périmètre des fichiers Python lus).

## 17. Stripe
- Couvert au point 3.

## 18. Supabase
- 17 fichiers de migration (`v1` à `v17`, confirmé `ls` — dernier fichier `v17_add_unsure_feedback_status.sql`, cohérent avec les sessions précédentes qui établissaient déjà ce total). Aucune migration `v18/v19/v20` sur `main` — cohérent avec l'absence confirmée de T1/T2 sur `main`.

## 19. Administration
- `superadmin.py:52` `GET /superadmin/stats` (`get_crm_stats`), `:212` `GET /superadmin/growth` (`get_growth_dashboard`) — capacité produit interne (tableau de bord CRM/croissance), gardée par `_require_superadmin`. `crm_service.py` — capacité produit associée.
- `frontend/app/admin/` — capacité produit, interface correspondante.

## 20. Feedback
- `feedback.py` — capacité produit, feedback utilisateur générique (distinct du feedback sur recommandations qui vit dans `decision_memory.py`) — **doublon potentiel de responsabilité à vérifier** : deux mécanismes de feedback coexistent, à clarifier dans un futur incrément si leurs périmètres se recoupent.

## 21. Contact
- `contact.py` — capacité produit, formulaire de contact.

## 22. Autres capacités détectées, non prévues dans la liste initiale
- `data_quality_gate.py` — garde-fou (validation de fichier Excel avant analyse, `validate_excel_before_analysis` — déjà connu des sessions précédentes comme bandeau qualité).
- `financial_normalizer.py`, `temporal_normalizer.py` — capacité produit / dette potentielle : leur existence même est un signal direct que la normalisation temporelle qu'ADR-003 (Financial Time Engine) propose de centraliser est **déjà partiellement tentée, de façon dispersée**, dans le code actuel — recoupement direct avec la cartographie d'implémentation antérieure qui notait `arc_service.py::_days_since()` comme le seul point réellement centralisé. `temporal_normalizer.py` n'avait pas été identifié dans cette cartographie précédente — **capacité potentiellement dupliquée avec la doctrine FTE, à recouper explicitement avant tout premier incrément FTE.**
- `economic_event_resolver.py` — capacité produit, lié à `financial_truth.py` (module dormant déjà documenté).
- `crm_service.py` — capacité produit, support de `superadmin.py`.

---

## Ce que cet inventaire ne fait pas
Ne propose aucun verdict. Ne modifie aucun fichier. Ne couvre pas exhaustivement chaque ligne de chaque service (`decision_rules.py`, `executive_decision_model.py`, `file_parser.py`, `financial_normalizer.py`, `temporal_normalizer.py` mériteraient chacun un audit du niveau de profondeur appliqué à l'anonymisation — signalé comme limite explicite, pas comme couverture complète).

---

**LEGACY_CAPABILITY_INVENTORY ÉTABLI À PARTIR DU CODE RÉEL DE MAIN. AUCUN CODE MODIFIÉ.**
