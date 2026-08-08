-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v22 : origin_analysis_id devient nullable (Decision Memory
-- Integrity Repair, défaut B — mission dédiée 2026-08-08)
--
-- Contexte : decision_arcs.origin_analysis_id est déclaré (v16) `NOT NULL
--   REFERENCES analyses(id) ON DELETE SET NULL` — une combinaison
--   contradictoire en Postgres (impossible d'écrire NULL dans une colonne
--   NOT NULL). Conséquence réelle, tracée jusqu'à la route applicative
--   DELETE /api/analyses/history (revue adversariale DecisionArc ↔
--   Engagement, 2026-08-08) : la suppression d'une Analysis référencée par
--   au moins un DecisionArc échoue par violation de contrainte, transaction
--   annulée — un utilisateur avec ne serait-ce qu'un DecisionArc suivi ne
--   peut aujourd'hui pas vider son historique d'analyses.
--
-- Doctrine (reconstruite depuis le code + la mission, confirmée par Fred) :
--   DecisionArc représente une mémoire décisionnelle professionnelle
--   durable ; origin_analysis_id n'est que sa provenance historique — la
--   disparition de la provenance ne doit jamais impliquer la disparition
--   de la mémoire. Suppression ORDINAIRE d'une Analysis (nettoyage
--   d'historique) : le DecisionArc survit, origin_analysis_id devient NULL.
--   Suppression GDPR/company (érasure complète) : le DecisionArc est
--   détruit via `company_id ON DELETE CASCADE` (v16, INCHANGÉ, toujours
--   correct) — ces deux formes de suppression restent explicitement
--   distinctes, la seconde n'est ni affaiblie ni modifiée par cette
--   migration.
--
-- Ce que fait cette migration :
--   1. `ALTER COLUMN origin_analysis_id DROP NOT NULL` — la référence FK
--      (`REFERENCES analyses(id) ON DELETE SET NULL`) est déjà correcte et
--      n'a besoin d'aucune modification ; seule la contrainte NOT NULL
--      empêchait Postgres d'exécuter l'action qu'elle déclarait pourtant.
--   2. CREATE OR REPLACE arc_immutability_guard() : ajoute un DEUXIÈME
--      carve-out étroit, séparé du carve-out engagement_id (v21), pour la
--      seule transition `origin_analysis_id : valeur → NULL` sur un arc
--      CLOSED — nécessaire car sans lui, l'action FK `ON DELETE SET NULL`
--      elle-même échouerait toujours sur un arc CLOSED (le trigger BEFORE
--      UPDATE existant refuserait cette UPDATE générée par Postgres),
--      remplaçant la contradiction SQL visible actuelle par une
--      contradiction plus subtile (identifiée explicitement par Fred avant
--      toute implémentation — voir Phase 15 de la mission).
--
-- Ce que cette migration NE fait PAS :
--   - Ne réécrit pas v16_decision_arcs.sql (déjà appliquée, jamais modifiée
--     en place — même convention que toutes les migrations précédentes de
--     ce dépôt).
--   - Ne touche ni company_id (CASCADE inchangé, GDPR/érasure complète non
--     affaiblie), ni entity_id, ni engagement_id.
--   - N'élargit pas le carve-out engagement_id (v21) — reste un carve-out
--     entièrement séparé, avec sa propre condition de garde.
--   - N'introduit aucune détection cryptographique de la SOURCE de
--     l'UPDATE (action FK vs. UPDATE applicatif direct avec la même
--     forme) — voir réserve nommée ci-dessous.
--
-- RÉSERVE NOMMÉE — portée réelle du carve-out : ce carve-out ne peut pas
--   distinguer, au niveau SQL, une UPDATE générée par l'action FK
--   `ON DELETE SET NULL` d'une UPDATE applicative directe qui aurait
--   exactement la même forme (`origin_analysis_id: valeur → NULL`, aucun
--   autre champ modifié). Dans ce dépôt, AUCUN chemin Python n'émet
--   aujourd'hui une telle UPDATE directement (origin_analysis_id n'est
--   écrit qu'une seule fois, à l'INSERT — vérifié dans arc_service.py) :
--   ce carve-out est donc sûr EN PRATIQUE, par discipline applicative,
--   exactement la même nature de garantie que le carve-out engagement_id
--   (v21). Une détection plus rigoureuse (ex. `pg_trigger_depth()` pour
--   distinguer une UPDATE imbriquée dans une action FK d'une UPDATE de
--   premier niveau) est possible mais non implémentée ici — pas le
--   correctif le plus petit nécessaire tant qu'aucun chemin de code ne
--   démontre le besoin.
--
-- Compatibilité UNIQUE(origin_analysis_id, recommendation_id) (v16) :
--   en SQL standard, NULL n'est jamais égal à NULL dans une contrainte
--   UNIQUE — plusieurs arcs déjà orphelins (origin_analysis_id NULL) ne
--   violent donc jamais cette contrainte, quel que soit leur
--   recommendation_id. Sans impact sur la création de nouveaux arcs, qui
--   fixent toujours origin_analysis_id depuis une Analysis vivante à
--   l'INSERT (jamais NULL à la création).
--
-- RÉSERVE DE VALIDATION (non levée, 2026-08-08) — l'interaction FK/trigger
--   ci-dessus (Phase 15) est établie par relecture du SQL et de la
--   sémantique documentée de Postgres (une action référentielle FK est
--   exécutée comme une UPDATE/DELETE sur la table référençante et déclenche
--   ses propres triggers), plus une réplique littérale du prédicat testée
--   en Python pur (voir tests/test_decision_memory_integrity_repair.py,
--   TestOriginAnalysisImmutabilityCarveOut) — mais N'A PAS été exécutée
--   contre un vrai moteur Postgres dans cette session :
--     1. Tentative d'utiliser l'outil Restore project sur le projet
--        Supabase dédié « Pepperyn Integration Test »
--        (ejixkplrgobgwqnhidwt, INACTIVE) — action explicitement refusée
--        par Fred (aucune action sur infrastructure Supabase réelle sans
--        autorisation explicite, quel que soit le projet visé).
--     2. Alternative locale (Postgres/Docker dans le bac à sable) —
--        indisponible : aucun paquet postgresql/docker installé, pas de
--        droits root, sudo désactivé dans cet environnement.
--   Cette réserve reste donc explicitement NON LEVÉE. Avant toute fusion
--   vers main et tout déploiement, cette migration doit être appliquée et
--   validée manuellement contre un projet Postgres réel (le projet
--   Integration Test existant, ou équivalent) — même gate que v16/v18/
--   v19/v20/v21 avant eux. Ne pas fusionner sur la seule base des tests
--   Python de ce dépôt.
--
-- Rollback : ALTER TABLE decision_arcs ALTER COLUMN origin_analysis_id SET NOT NULL;
--            (échouera si des lignes orphelines existent déjà — attendu,
--            rollback destructif documenté comme tel, pas silencieux)
--            puis CREATE OR REPLACE FUNCTION arc_immutability_guard()
--            avec le corps exact de v21 (sans le carve-out origin_analysis_id).
-- ─────────────────────────────────────────────────────────────────────────────

-- ============================================================
-- 1. origin_analysis_id devient nullable
-- ============================================================

ALTER TABLE public.decision_arcs
  ALTER COLUMN origin_analysis_id DROP NOT NULL;

COMMENT ON COLUMN public.decision_arcs.origin_analysis_id IS
  'Provenance historique (IMMUABLE tant que non-NULL) — PAS une identité ni '
  'une propriété. Nullable depuis v22 : la suppression ordinaire de '
  'l''Analysis d''origine ne détruit jamais le DecisionArc (mémoire '
  'décisionnelle professionnelle), elle rend seulement sa provenance '
  'indisponible (ON DELETE SET NULL). La suppression complète d''une '
  'company (GDPR) reste distincte et continue de détruire le DecisionArc '
  'via company_id ON DELETE CASCADE (v16, inchangé).';

-- ============================================================
-- 2. Carve-out étroit et séparé : nullification de origin_analysis_id
--    sur un arc CLOSED (nécessaire pour que l'action FK elle-même
--    fonctionne — voir contexte ci-dessus)
-- ============================================================

CREATE OR REPLACE FUNCTION public.arc_immutability_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF OLD.status = 'closed' THEN
    -- Carve-out 1 (v21) : rattachement rétroactif unique de engagement_id.
    IF OLD.engagement_id IS NULL
       AND NEW.engagement_id IS NOT NULL
       AND NEW.status               IS NOT DISTINCT FROM OLD.status
       AND NEW.company_id           IS NOT DISTINCT FROM OLD.company_id
       AND NEW.entity_id            IS NOT DISTINCT FROM OLD.entity_id
       AND NEW.origin_analysis_id   IS NOT DISTINCT FROM OLD.origin_analysis_id
       AND NEW.decision_fingerprint IS NOT DISTINCT FROM OLD.decision_fingerprint
       AND NEW.recommendation_id    IS NOT DISTINCT FROM OLD.recommendation_id
       AND NEW.decision_source      IS NOT DISTINCT FROM OLD.decision_source
       AND NEW.recommendation_text  IS NOT DISTINCT FROM OLD.recommendation_text
       AND NEW.decision_text        IS NOT DISTINCT FROM OLD.decision_text
       AND NEW.decision_notes       IS NOT DISTINCT FROM OLD.decision_notes
       AND NEW.decision_confirmed_at IS NOT DISTINCT FROM OLD.decision_confirmed_at
       AND NEW.decision_confirmation_source IS NOT DISTINCT FROM OLD.decision_confirmation_source
       AND NEW.execution_status     IS NOT DISTINCT FROM OLD.execution_status
       AND NEW.execution_notes      IS NOT DISTINCT FROM OLD.execution_notes
       AND NEW.execution_updated_at IS NOT DISTINCT FROM OLD.execution_updated_at
       AND NEW.learning_text        IS NOT DISTINCT FROM OLD.learning_text
       AND NEW.learning_confirmed   IS NOT DISTINCT FROM OLD.learning_confirmed
       AND NEW.learning_modified    IS NOT DISTINCT FROM OLD.learning_modified
       AND NEW.closed_at            IS NOT DISTINCT FROM OLD.closed_at
       AND NEW.abandoned_at         IS NOT DISTINCT FROM OLD.abandoned_at
       AND NEW.abandoned_reason     IS NOT DISTINCT FROM OLD.abandoned_reason
       AND NEW.created_at           IS NOT DISTINCT FROM OLD.created_at
       AND NEW.updated_at           IS NOT DISTINCT FROM OLD.updated_at
    THEN
      RETURN NEW;
    END IF;

    -- Carve-out 2 (v22) : nullification de origin_analysis_id, déclenchée
    -- par l'action FK ON DELETE SET NULL suite à la suppression de
    -- l'Analysis d'origine. Séparé du carve-out 1 par construction (Phase
    -- 15 : "Do not create a generic provenance-mutation carve-out") —
    -- engagement_id doit rester STRICTEMENT inchangé ici, contrairement au
    -- carve-out 1 où c'est origin_analysis_id qui doit rester inchangé.
    IF OLD.origin_analysis_id IS NOT NULL
       AND NEW.origin_analysis_id IS NULL
       AND NEW.status               IS NOT DISTINCT FROM OLD.status
       AND NEW.company_id           IS NOT DISTINCT FROM OLD.company_id
       AND NEW.entity_id            IS NOT DISTINCT FROM OLD.entity_id
       AND NEW.engagement_id        IS NOT DISTINCT FROM OLD.engagement_id
       AND NEW.decision_fingerprint IS NOT DISTINCT FROM OLD.decision_fingerprint
       AND NEW.recommendation_id    IS NOT DISTINCT FROM OLD.recommendation_id
       AND NEW.decision_source      IS NOT DISTINCT FROM OLD.decision_source
       AND NEW.recommendation_text  IS NOT DISTINCT FROM OLD.recommendation_text
       AND NEW.decision_text        IS NOT DISTINCT FROM OLD.decision_text
       AND NEW.decision_notes       IS NOT DISTINCT FROM OLD.decision_notes
       AND NEW.decision_confirmed_at IS NOT DISTINCT FROM OLD.decision_confirmed_at
       AND NEW.decision_confirmation_source IS NOT DISTINCT FROM OLD.decision_confirmation_source
       AND NEW.execution_status     IS NOT DISTINCT FROM OLD.execution_status
       AND NEW.execution_notes      IS NOT DISTINCT FROM OLD.execution_notes
       AND NEW.execution_updated_at IS NOT DISTINCT FROM OLD.execution_updated_at
       AND NEW.learning_text        IS NOT DISTINCT FROM OLD.learning_text
       AND NEW.learning_confirmed   IS NOT DISTINCT FROM OLD.learning_confirmed
       AND NEW.learning_modified    IS NOT DISTINCT FROM OLD.learning_modified
       AND NEW.closed_at            IS NOT DISTINCT FROM OLD.closed_at
       AND NEW.abandoned_at         IS NOT DISTINCT FROM OLD.abandoned_at
       AND NEW.abandoned_reason     IS NOT DISTINCT FROM OLD.abandoned_reason
       AND NEW.created_at           IS NOT DISTINCT FROM OLD.created_at
       AND NEW.updated_at           IS NOT DISTINCT FROM OLD.updated_at
    THEN
      RETURN NEW;
    END IF;

    RAISE EXCEPTION
      '[ARC] Arc % est CLOSED et immuable. Aucune modification autorisée.', OLD.id;
  END IF;

  -- decision_text est immuable une fois écrit (audit trail décisionnel)
  IF OLD.decision_text IS NOT NULL
     AND NEW.decision_text IS DISTINCT FROM OLD.decision_text THEN
    RAISE EXCEPTION
      '[ARC] decision_text est immuable une fois écrit sur l''arc %.', OLD.id;
  END IF;

  -- decision_confirmed_at est immuable une fois écrit (horodatage de prise de connaissance)
  IF OLD.decision_confirmed_at IS NOT NULL
     AND NEW.decision_confirmed_at IS DISTINCT FROM OLD.decision_confirmed_at THEN
    RAISE EXCEPTION
      '[ARC] decision_confirmed_at est immuable une fois écrit sur l''arc %.', OLD.id;
  END IF;

  -- closed_at est immuable une fois écrit
  IF OLD.closed_at IS NOT NULL
     AND NEW.closed_at IS DISTINCT FROM OLD.closed_at THEN
    RAISE EXCEPTION
      '[ARC] closed_at est immuable une fois écrit sur l''arc %.', OLD.id;
  END IF;

  -- Mise à jour automatique du timestamp (comportement v16 inchangé pour
  -- tout arc non-CLOSED).
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- ── Fin migration v22 ────────────────────────────────────────────────────────
