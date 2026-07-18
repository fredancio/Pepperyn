-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v16 : Arc Décisionnel MVP
-- Tables : decision_arcs, arc_analysis_links
-- Trigger : immutabilité sur arc CLOSED + champs immuables
-- Indexes : company_id, status, origin_analysis_id
--
-- Architecture additive — aucune table existante n'est modifiée.
-- Peut être annulée par : DROP TABLE arc_analysis_links; DROP TABLE decision_arcs;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Table principale ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.decision_arcs (
  id                          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,

  -- CONTEXTE (IMMUTABLE)
  company_id                  UUID        NOT NULL REFERENCES companies(id)  ON DELETE CASCADE,
  entity_id                   UUID                 REFERENCES entities(id)   ON DELETE SET NULL,

  -- ORIGINE (IMMUTABLE après création)
  -- Référence à l'analyse source — la Situation de cet arc.
  -- Validé à la création : decision_kernel + decision_fingerprint doivent être présents.
  origin_analysis_id          UUID        NOT NULL REFERENCES analyses(id)   ON DELETE SET NULL,
  -- Snapshot du decision_fingerprint depuis analyses.decision_fingerprint (audit trail)
  decision_fingerprint        TEXT        NOT NULL,
  -- Lien logique vers decision_feedback.recommendation_id (SHA-1 déterministe)
  recommendation_id           TEXT        NOT NULL,
  -- Source dans le plan d'action original
  decision_source             TEXT        NOT NULL
    CHECK (decision_source IN ('plan_action_haute', 'plan_action')),
  -- Contrainte d'idempotence : un seul arc par (analyse × recommandation)
  UNIQUE (origin_analysis_id, recommendation_id),

  -- RECOMMENDATION (IMMUTABLE — snapshot Pepperyn à la création)
  -- Texte verbatim de la recommandation. Snapshoté car analyse_json peut évoluer.
  -- Garantit que l'arc est auto-portant pour l'audit sans JOIN sur analyses.
  recommendation_text         TEXT        NOT NULL,

  -- DECISION (champs IMMUTABLES une fois écrits — voir trigger)
  -- NULL tant que l'arc est en INTENTION.
  -- decision_text ≠ recommendation_text : le dirigeant peut avoir décidé différemment.
  decision_text               TEXT,
  -- Reformulation libre par l'utilisateur (optionnel, MUTABLE jusqu'à 'decision')
  decision_notes              TEXT,
  -- Quand Pepperyn a appris l'existence de cette décision (≠ date réelle de décision)
  decision_confirmed_at       TIMESTAMPTZ,
  -- NULL à INTENTION.
  -- 'explicit' : confirmation intentionnelle (prospective ou rétrospective).
  -- 'inferred_from_execution' : check-in done/partially_done → décision inférée.
  decision_confirmation_source TEXT
    CHECK (decision_confirmation_source IN ('explicit', 'inferred_from_execution')),

  -- ÉTAT (forward-only sauf ABANDONED — voir trigger)
  -- Note : l'état 'decision' est dans le schéma mais non atteignable en MVP v1
  -- (pas d'UI de confirmation explicite). Les arcs MVP passent INTENTION → EXECUTION.
  status                      TEXT        NOT NULL DEFAULT 'intention'
    CHECK (status IN (
      'intention',
      'decision',           -- réservé post-MVP
      'execution',
      'consequences_linked',
      'learning_proposed',
      'closed',
      'abandoned'
    )),

  -- EXÉCUTION (MUTABLE jusqu'à consequences_linked)
  execution_status            TEXT        NOT NULL DEFAULT 'not_started'
    CHECK (execution_status IN ('not_started', 'in_progress', 'partial', 'complete')),
  execution_notes             TEXT,
  execution_updated_at        TIMESTAMPTZ,

  -- LEARNING (MUTABLE jusqu'à closed)
  -- Un arc ne peut pas passer à CLOSED avec learning_text NULL (gardé par arc_service).
  learning_text               TEXT,
  learning_confirmed          BOOLEAN     NOT NULL DEFAULT FALSE,
  -- TRUE si l'utilisateur a modifié le learning proposé par l'IA
  learning_modified           BOOLEAN     NOT NULL DEFAULT FALSE,

  -- TIMESTAMPS
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- closed_at est IMMUTABLE une fois écrit (trigger)
  closed_at                   TIMESTAMPTZ,
  abandoned_at                TIMESTAMPTZ,
  abandoned_reason            TEXT
);

COMMENT ON TABLE public.decision_arcs IS
  'Arc Décisionnel DCT — trajectoire S→R→I→D→E→C→L par entreprise. '
  'RÈGLE : decision_text IS NOT NULL requis pour CLOSED. '
  'RÈGLE : arc CLOSED = immuable (trigger arc_immutability_guard).';

-- ── Table des liens analyse ↔ arc ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.arc_analysis_links (
  id                    UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  arc_id                UUID        NOT NULL REFERENCES decision_arcs(id) ON DELETE CASCADE,
  analysis_id           UUID        NOT NULL REFERENCES analyses(id)      ON DELETE CASCADE,

  -- Type du lien :
  -- 'origin'                : analyse source de l'arc (certain, confirmé auto)
  -- 'consequence_candidate' : Pepperyn propose un lien (pending review)
  -- 'consequence_confirmed' : utilisateur a confirmé le lien
  -- 'consequence_rejected'  : utilisateur a rejeté le lien (arc reste ouvert)
  -- 'context'               : lié mais pas conséquence directe
  link_type             TEXT        NOT NULL
    CHECK (link_type IN (
      'origin',
      'consequence_candidate',
      'consequence_confirmed',
      'consequence_rejected',
      'context'
    )),

  -- Texte de la proposition Pepperyn (niveaux 1-3 de la hiérarchie causale uniquement)
  -- JAMAIS : "a causé", "est la conséquence de", "grâce à votre décision"
  -- AUTORISÉ : "est survenu après", "est corrélé à", "une évolution observée depuis"
  link_hypothesis       TEXT,

  -- NULL = en attente de review | TRUE = confirmé | FALSE = rejeté
  confirmed_by_user     BOOLEAN,
  user_rejection_reason TEXT,

  linked_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at           TIMESTAMPTZ,

  -- Un arc ne peut avoir qu'un seul lien vers une analyse donnée
  UNIQUE (arc_id, analysis_id)
);

COMMENT ON TABLE public.arc_analysis_links IS
  'Liens entre arcs décisionnels et analyses Pepperyn. '
  'RÈGLE CAUSALE : link_hypothesis contient uniquement associations temporelles (niveaux 1-3). '
  'Refuser un candidat (consequence_rejected) ne ferme pas l''arc — il reste en execution.';

-- ── Trigger immutabilité ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.arc_immutability_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Un arc CLOSED est scellé : aucun champ ne peut être modifié
  IF OLD.status = 'closed' THEN
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

  -- Mise à jour automatique du timestamp
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER arc_immutability
  BEFORE UPDATE ON public.decision_arcs
  FOR EACH ROW
  EXECUTE FUNCTION public.arc_immutability_guard();

-- ── Indexes ──────────────────────────────────────────────────────────────────

-- Requêtes principales : par company + statut
CREATE INDEX IF NOT EXISTS idx_decision_arcs_company_status
  ON public.decision_arcs(company_id, status);

-- Détection de conséquences : trouver les arcs EXECUTION d'une company
CREATE INDEX IF NOT EXISTS idx_decision_arcs_company_execution
  ON public.decision_arcs(company_id)
  WHERE status = 'execution';

-- Lookup par analyse source
CREATE INDEX IF NOT EXISTS idx_decision_arcs_origin_analysis
  ON public.decision_arcs(origin_analysis_id);

-- Links : lookup par arc
CREATE INDEX IF NOT EXISTS idx_arc_analysis_links_arc_id
  ON public.arc_analysis_links(arc_id);

-- Links : lookup par analyse (pour savoir si une analyse a des candidats pendants)
CREATE INDEX IF NOT EXISTS idx_arc_analysis_links_analysis_pending
  ON public.arc_analysis_links(analysis_id)
  WHERE confirmed_by_user IS NULL;

-- ── RLS (Row Level Security) ──────────────────────────────────────────────────
-- Les arcs sont protégés par company_id.
-- Le service utilise la clé SERVICE_KEY (contourne RLS) — pas de politique RLS
-- supplémentaire nécessaire pour ce MVP. À ajouter si accès client direct via anon key.

-- ── Fin migration v16 ────────────────────────────────────────────────────────
