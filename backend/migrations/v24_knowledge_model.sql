-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v24 : Knowledge Model v0 (CONFIRMED enterprise knowledge only)
-- Table : knowledge_model
-- Trigger : immutabilité (UPDATE bloqué, sauf carve-out engagement_id SET NULL)
-- Indexes : entity_id, (entity_id, subject), relates_to_knowledge_id
--
-- Fondation : docs/Architecture/Cognitive/KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md
--   (arbitrage final inclus, commits d522476 + 15919c2, canonique sur main
--   depuis 3be19e4). Implémente exactement le contrat — aucun champ, aucune
--   table, aucune sémantique ajoutée au-delà de ce qu'il autorise.
--
-- Ce que cette table N'EST PAS (contrat §2, §17) :
--   - Pas l'Evidence Ledger (ce que Pepperyn a observé).
--   - Pas l'historique de chat (aucun texte brut de conversation ici).
--   - Pas un espace pour des hypothèses/candidats — une ligne = une
--     connaissance CONFIRMED, déjà entièrement formée à l'insertion.
--     "Candidate"/hypothèse reste entièrement hors persistance (contrat §3).
--
-- Propriété (contrat §4) :
--   - VRAI PROPRIÉTAIRE = Entity. entity_id NOT NULL, ON DELETE CASCADE —
--     la connaissance meurt avec l'Entity, jamais avant (RGPD, §16).
--   - CONTEXTE D'ACQUISITION = Engagement. engagement_id nullable,
--     ON DELETE SET NULL — la connaissance survit à la suppression de
--     l'Engagement qui l'a vue naître (un second Engagement sur la même
--     Entity en bénéficie encore).
--
-- Champs volontairement ABSENTS (retirés par l'arbitrage, contrat §11,
-- §17 — ne pas les réintroduire) :
--   - company_id : redondant, couvert transitivement par
--     entity_id CASCADE → entities.company_id CASCADE (v6:75).
--   - scope_key : la portée v0 EST entity_id, aucune abstraction séparée.
--   - status : une seule valeur existe (CONFIRMED implicite) — pas de
--     colonne pour une valeur constante.
--   - created_at séparé : fusionné dans confirmed_at (contrat §6) — dans
--     le modèle CONFIRMED-only, création et confirmation sont le même
--     événement.
--   - predicate, JSONB générique, analysis_id : jamais autorisés par le
--     contrat (pas de triple store générique, pas de couplage à Analysis).
--
-- RÉSERVE STRUCTURELLE OUVERTE — intégrité de branchement (voir mission
-- d'implémentation, point soulevé explicitement par Fred avant cette
-- migration) : le contrat définit la "tête de chaîne" comme la ligne
-- CONFIRMED qu'aucune autre ligne CONFIRMED ne référence via
-- relates_to_knowledge_id, mais NE SPÉCIFIE AUCUN mécanisme empêchant
-- DEUX lignes différentes de référencer le même prédécesseur (ce qui
-- produirait deux têtes concurrentes pour le même (entity_id, subject)).
-- Cette migration N'AJOUTE PAS de contrainte UNIQUE sur
-- relates_to_knowledge_id : ce serait inventer un invariant que le
-- contrat n'autorise pas. La prévention (refus applicatif à l'écriture)
-- et la détection (échec explicite si RECALL rencontre plusieurs têtes)
-- sont implémentées au niveau service (services/knowledge_model_service.py),
-- jamais résolues silencieusement par un ORDER BY confirmed_at. Une vraie
-- course concurrente (deux CONFIRM simultanés) reste possible tant
-- qu'aucune contrainte DB ou verrou sérialisable n'est ajoutée — nommé
-- explicitement, non résolu ici, en attente de revue adversariale.
--
-- Rollback : DROP TABLE public.knowledge_model;
--            (aucune autre table, aucune donnée existante n'est touchée)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.knowledge_model (
  id                      UUID        DEFAULT gen_random_uuid() PRIMARY KEY,

  -- PROPRIÉTÉ (contrat §4)
  entity_id               UUID        NOT NULL REFERENCES public.entities(id)     ON DELETE CASCADE,
  engagement_id           UUID                 REFERENCES public.engagements(id)  ON DELETE SET NULL,

  -- CONTENU — sujet curaté (enum fermé), valeur contrainte par sujet
  -- (registre applicatif ET contrainte DB doivent s'accorder, contrat §10).
  -- v0 : un seul sujet, EXPENSE_SIGN_CONVENTION, deux valeurs légales.
  -- Ajouter un sujet = ajouter une clause CHECK, jamais élargir vers un
  -- triple store générique.
  subject                 TEXT        NOT NULL,
  value                   TEXT        NOT NULL,

  -- SUPERSESSION (contrat §9) — un seul sens possible : cette ligne
  -- CONFIRMED remplace celle-là. Jamais un sens de candidat, jamais un
  -- sens de contradiction (la contradiction n'est jamais persistée ici).
  relates_to_knowledge_id UUID                 REFERENCES public.knowledge_model(id) ON DELETE CASCADE,

  -- PROVENANCE (contrat §7) — v0 : valeur unique, aucune voie LLM.
  provenance              TEXT        NOT NULL DEFAULT 'HUMAN_CONFIRMATION',
  -- Identité de l'acteur humain qui a confirmé — délibérément SANS
  -- contrainte FK vers profiles(id) : le contrat n'autorise aucune
  -- décision de sémantique de suppression pour cet acteur (même
  -- discipline que l'absence volontaire d'analysis_id, contrat §15) ;
  -- ajouter une FK ici inventerait une sémantique de suppression que le
  -- contrat n'a jamais tranchée.
  confirmed_by            UUID        NOT NULL,

  -- TEMPS UNIFIÉ (contrat §6) — un seul horodatage, explicite, jamais un
  -- DEFAULT NOW() implicite côté DB (fourni par l'appelant à la
  -- confirmation, jamais fabriqué silencieusement).
  confirmed_at            TIMESTAMPTZ NOT NULL,

  CONSTRAINT knowledge_model_subject_value_registry CHECK (
    (subject = 'EXPENSE_SIGN_CONVENTION' AND value IN ('ABSOLUTE_POSITIVE', 'SIGNED_NATURAL'))
  ),
  CONSTRAINT knowledge_model_provenance_v0 CHECK (
    provenance = 'HUMAN_CONFIRMATION'
  ),
  -- Une ligne ne peut jamais se superséder elle-même.
  CONSTRAINT knowledge_model_no_self_supersession CHECK (
    relates_to_knowledge_id IS NULL OR relates_to_knowledge_id <> id
  )
);

COMMENT ON TABLE public.knowledge_model IS
  'Knowledge Model v0 (contrat KNOWLEDGE_MODEL_V0_IMPLEMENTATION_CONTRACT.md, '
  'arbitrage final) — connaissance CONFIRMED uniquement, insert-only. '
  'Propriétaire vrai = Entity (CASCADE). Engagement = contexte '
  'd''acquisition (SET NULL). Aucune ligne CANDIDATE, aucun statut, aucun '
  'company_id direct. RÉSERVE : aucune contrainte DB n''empêche le '
  'branchement de relates_to_knowledge_id — prévention/détection au '
  'niveau service uniquement, voir commentaire de migration ci-dessus.';

-- ── Trigger immutabilité ─────────────────────────────────────────────────────
-- Insert-only par construction (contrat §3, §7 — inverse d'evidence_ledger_
-- entries qui, elle, n'a AUCUN carve-out). Ici un carve-out étroit et
-- unique est nécessaire : ON DELETE SET NULL sur engagement_id (ci-dessus)
-- s'implémente, côté Postgres, par un UPDATE piloté par la FK — sans
-- carve-out, ce trigger le rejetterait inconditionnellement et la
-- suppression d'un Engagement échouerait. C'est exactement la classe de
-- défaut déjà rencontrée sur DecisionArc (v21, arc_immutability_guard) —
-- le même remède exact est appliqué ici : autoriser UNIQUEMENT la
-- transition engagement_id (valeur → NULL), rejeter tout le reste sans
-- exception, y compris une seconde tentative de SET NULL sur une ligne
-- où engagement_id est déjà NULL (pas de transition = pas de carve-out).

CREATE OR REPLACE FUNCTION public.knowledge_model_immutability_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF OLD.engagement_id IS NOT NULL
     AND NEW.engagement_id IS NULL
     AND NEW.id                      IS NOT DISTINCT FROM OLD.id
     AND NEW.entity_id               IS NOT DISTINCT FROM OLD.entity_id
     AND NEW.subject                 IS NOT DISTINCT FROM OLD.subject
     AND NEW.value                   IS NOT DISTINCT FROM OLD.value
     AND NEW.relates_to_knowledge_id IS NOT DISTINCT FROM OLD.relates_to_knowledge_id
     AND NEW.provenance              IS NOT DISTINCT FROM OLD.provenance
     AND NEW.confirmed_by            IS NOT DISTINCT FROM OLD.confirmed_by
     AND NEW.confirmed_at            IS NOT DISTINCT FROM OLD.confirmed_at
  THEN
    -- Rattachement d'acquisition perdu (Engagement supprimé) : ne compte
    -- jamais comme une réécriture de la connaissance elle-même.
    RETURN NEW;
  END IF;

  RAISE EXCEPTION
    '[KNOWLEDGE MODEL] La ligne % est immuable. Aucune modification '
    'autorisée hors la mise à NULL de engagement_id déclenchée par la '
    'suppression de l''Engagement — créer une nouvelle ligne CONFIRMED '
    '(relates_to_knowledge_id) plutôt que de réécrire celle-ci.', OLD.id;
END;
$$;

CREATE TRIGGER knowledge_model_immutability
  BEFORE UPDATE ON public.knowledge_model
  FOR EACH ROW
  EXECUTE FUNCTION public.knowledge_model_immutability_guard();

-- ── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_knowledge_model_entity
  ON public.knowledge_model(entity_id);

-- Index de résolution RECALL : chaîne par (entity_id, subject).
CREATE INDEX IF NOT EXISTS idx_knowledge_model_entity_subject
  ON public.knowledge_model(entity_id, subject);

CREATE INDEX IF NOT EXISTS idx_knowledge_model_relates_to
  ON public.knowledge_model(relates_to_knowledge_id)
  WHERE relates_to_knowledge_id IS NOT NULL;

-- ── RLS (Row Level Security) ──────────────────────────────────────────────────
-- Même convention qu'evidence_ledger_entries (v18) et engagements (v19) :
-- le service utilise SERVICE_KEY (contourne RLS). Écritures strictement
-- server-side (contrat §13, mission Phase 13) — aucune route cliente ne
-- lit ni n'écrit cette table. Pas de politique RLS nécessaire pour v0.

-- ── Fin migration v24 ────────────────────────────────────────────────────────
