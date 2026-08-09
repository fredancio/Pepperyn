-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v26 : Knowledge Model v0 — unicité de racine par (entity_id, subject)
-- Table : knowledge_model
-- Contrainte : UNIQUE(entity_id, subject) WHERE relates_to_knowledge_id IS NULL
--
-- Contexte : Epistemic Dialogue v0 (architecture, doc-only, non fusionnée) a
--   nommé une réserve structurelle héritée de Knowledge Model v0 : migration
--   v25 ajoute UNIQUE(relates_to_knowledge_id), ce qui empêche deux lignes de
--   superséder le même prédécesseur (branchement APRÈS une première
--   confirmation) — mais PostgreSQL traite chaque NULL comme distinct dans une
--   contrainte UNIQUE standard, donc RIEN n'empêchait deux lignes RACINES
--   (relates_to_knowledge_id IS NULL) d'exister pour le même (entity_id,
--   subject) — le cas d'une toute première confirmation, jamais celui d'une
--   supersession.
--
-- Défaut prouvé (mission ROOT UNIQUENESS ADVERSARIAL REPAIR, 2026-08-09) :
--   contre un vrai PostgreSQL local (v24+v25 exacts, aucune reconstruction),
--   deux INSERT successifs de lignes racines pour le même (entity_id, subject)
--   avec des valeurs CONTRADICTOIRES (ABSOLUTE_POSITIVE puis SIGNED_NATURAL)
--   réussissent tous les deux sans cette migration. RECALL() détecterait
--   ensuite deux têtes non référencées et lèverait KnowledgeChainIntegrityError
--   (défense en profondeur déjà en place, contract §8) — mais la ligne
--   invalide existe déjà en base au moment de la détection.
--
-- Invariant exact ajouté : pour un (entity_id, subject) donné, au plus UNE
--   ligne CONFIRMED peut avoir relates_to_knowledge_id IS NULL. Portée
--   strictement locale à la paire (entity_id, subject) — jamais une racine
--   unique par Entity, jamais une racine unique globale.
--
-- Vérifié adversarialement NE PAS empêcher (mission Phase 2, prouvé en
-- PostgreSQL réel local, voir rapport) :
--   - des sujets différents pour la même Entity (chaque sujet a sa propre
--     racine, la contrainte est composite sur (entity_id, subject)) ;
--   - le même sujet pour des Entities différentes (la contrainte inclut
--     entity_id) ;
--   - les chaînes de supersession normales (K1 racine → K2 → K3 : seul K1 a
--     relates_to_knowledge_id NULL, K2/K3 ne sont jamais concernés par CETTE
--     contrainte — ils restent protégés par v25) ;
--   - les lignes historiques (K1 conserve relates_to_knowledge_id NULL pour
--     toujours, même après avoir été supersédée — c'est exactement voulu :
--     il n'existe qu'UNE origine par chaîne, pour toujours) ;
--   - la suppression d'Engagement (ON DELETE SET NULL sur engagement_id,
--     colonne non référencée par cette contrainte) ;
--   - la suppression d'Entity / cascade RGPD (ON DELETE CASCADE existant sur
--     entity_id, la contrainte est automatiquement vidée avec les lignes) ;
--   - l'extension future de sujets (chaque nouveau sujet obtient
--     automatiquement son propre espace d'unicité (entity_id, subject),
--     aucune modification de cette migration n'est nécessaire).
--
-- Choix de mécanisme (mission Phase 3) : INDEX UNIQUE PARTIEL plutôt qu'une
--   contrainte UNIQUE simple sur (entity_id, subject) — une contrainte non
--   partielle empêcherait absurdement toute ligne successeur d'exister pour
--   ce couple (entity_id, subject) au-delà de la première ligne. Le filtre
--   WHERE relates_to_knowledge_id IS NULL restreint l'unicité exactement aux
--   racines, laissant les successeurs entièrement gérés par v25. Aucun
--   arbitrage par horodatage, aucun verrouillage applicatif : PostgreSQL
--   applique cet invariant au niveau de l'index B-tree lui-même, y compris
--   sous concurrence réelle (deux transactions simultanées insérant chacune
--   une racine candidate — l'une commit, l'autre est rejetée avec une
--   violation de contrainte, jamais les deux ne réussissent).
--
-- Sécurité de la migration sur données existantes : CREATE UNIQUE INDEX
--   échoue explicitement (ne supprime ni ne corrige silencieusement rien) si
--   des lignes racines dupliquées existent déjà pour un même (entity_id,
--   subject) au moment de l'application — vérifié par construction : la
--   commande elle-même refuse de s'exécuter en présence d'un doublon
--   (comportement PostgreSQL standard, prouvé localement). Si cette migration
--   échoue à l'application sur Pepperyn Integration Test ou en production,
--   NE PAS supprimer ni fusionner silencieusement les doublons : escalader.
--
-- Ce que cette migration N'AJOUTE PAS (hors périmètre, mission explicite) :
--   - Aucun renforcement cross-Entity / cross-subject (déjà hors périmètre
--     de v25, toujours hors périmètre ici).
--   - Aucune modification du mécanisme RECALL (services/
--     knowledge_model_service.py) — la résolution de tête de chaîne reste
--     structurelle, non affectée par cette contrainte.
--   - Aucun arbitrage par confirmed_at, aucune sémantique de "gagnant".
--   - Aucune table, aucun statut, aucun champ métier nouveau.
--
-- Rollback : DROP INDEX public.knowledge_model_one_root_per_entity_subject;
--            (aucune autre table, aucune donnée existante n'est touchée)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE UNIQUE INDEX IF NOT EXISTS knowledge_model_one_root_per_entity_subject
  ON public.knowledge_model (entity_id, subject)
  WHERE relates_to_knowledge_id IS NULL;

COMMENT ON INDEX public.knowledge_model_one_root_per_entity_subject IS
  'Au plus une ligne racine (relates_to_knowledge_id IS NULL) par '
  '(entity_id, subject) — mission de réparation d''unicité de racine, '
  '2026-08-09, faisant suite à une réserve nommée par Epistemic Dialogue '
  'v0 (architecture, non fusionnée). Complète v25 '
  '(knowledge_model_one_successor_per_predecessor) : v25 empêche le '
  'branchement APRÈS une première confirmation, cet index empêche deux '
  'PREMIÈRES confirmations concurrentes et contradictoires. Ensemble, les '
  'deux garantissent qu''un (entity_id, subject) donné a exactement une '
  'chaîne de connaissance canonique, jamais deux.';

-- ── Fin migration v26 ────────────────────────────────────────────────────────
