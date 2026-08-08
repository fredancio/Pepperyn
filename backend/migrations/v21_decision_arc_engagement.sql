-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v21 : DecisionArc ↔ Engagement (rattachement relationnel)
-- Colonne : decision_arcs.engagement_id (nullable, additive)
-- Fonction : arc_immutability_guard() — carve-out étroit, une seule fois
--
-- Contexte : DecisionArc (agrégat 1, v16) est aujourd'hui ancré uniquement
--   sur Analysis (origin_analysis_id NOT NULL) et, optionnellement et de
--   façon non fiable, sur Entity (entity_id, jamais peuplé par le chemin de
--   création réel — voir note ci-dessous). Engagement (T2A, v19) existe
--   maintenant comme propriétaire relationnel durable. Cette migration
--   attache DecisionArc à Engagement SANS toucher son cycle de vie, sans
--   introduire de lien Evidence, sans logique FTE — voir
--   docs/Product/PRODUCT_BOARD.md "DecisionArc ↔ Engagement" (mission dédiée).
--
-- Ce que fait cette migration :
--   1. Ajoute decision_arcs.engagement_id (UUID, nullable, additif).
--   2. Ajoute un index sur cette colonne.
--   3. CREATE OR REPLACE arc_immutability_guard() : ajoute une exception
--      étroite et unique permettant à engagement_id d'être écrit UNE SEULE
--      FOIS (NULL → valeur) sur un arc CLOSED, sans toucher à aucun autre
--      champ — nécessaire car les arcs CLOSED historiques (précisément ceux
--      qui ont complété tout le cycle S→R→I→D→E→C→L, donc les plus
--      pertinents pour la continuité décisionnelle) seraient sinon
--      définitivement inéligibles au backfill (voir note ci-dessous).
--
-- Ce que cette migration NE fait PAS :
--   - Ne rend jamais engagement_id NOT NULL (les analyses sans entity_id
--     connu, ou les Entities sans Engagement encore résolu, doivent pouvoir
--     rester non-résolues honnêtement plutôt que de bloquer la création).
--   - Ne touche ni entity_id, ni origin_analysis_id, ni aucun autre champ
--     de decision_arcs.
--   - Ne modifie aucune ligne existante (le peuplement historique se fait
--     via le script idempotent séparé
--     backend/tools/one-off-scripts/backfill_decision_arc_engagements.py,
--     même convention que backfill_engagements_t2a.py pour T2A).
--   - N'affaiblit aucune autre garantie d'immutabilité existante (le
--     carve-out est verrouillé champ par champ — voir ci-dessous).
--
-- NOTE — anomalie découverte, non corrigée ici (hors périmètre) :
--   decision_arcs.origin_analysis_id est déclaré `NOT NULL REFERENCES
--   analyses(id) ON DELETE SET NULL` (v16) — une combinaison contradictoire
--   (Postgres ne peut pas écrire NULL dans une colonne NOT NULL). En
--   pratique, la suppression d'une Analysis référencée par un DecisionArc
--   échouerait avec une violation de contrainte plutôt que d'orpheliner
--   silencieusement l'arc — plus sûr pour l'intégrité que destructeur, mais
--   probablement pas le comportement voulu à l'origine. Signalé, pas
--   modifié : cette migration ne touche pas origin_analysis_id.
--
-- NOTE — entity_id sur decision_arcs (v16, nullable) : accepté en paramètre
--   optionnel par create_arc_from_feedback() mais jamais fourni par le seul
--   appelant réel (routers/decision_memory.py::submit_decision_feedback).
--   En pratique, cette colonne n'est donc jamais peuplée par le chemin de
--   création vivant — elle ne peut pas servir de source fiable pour
--   résoudre l'Engagement. La résolution ajoutée par cette migration
--   utilise donc `analyses.entity_id` (via origin_analysis_id), pas
--   `decision_arcs.entity_id`. entity_id reste inchangé, tel quel (option A
--   de l'analyse Mission 6 : conservé temporairement, sa correction de
--   peuplement est un chantier distinct, non traité ici).
--
-- Rollback : ALTER TABLE decision_arcs DROP COLUMN engagement_id;
--            puis CREATE OR REPLACE FUNCTION arc_immutability_guard()
--            avec le corps exact de v16 (sans le carve-out engagement_id).
-- ─────────────────────────────────────────────────────────────────────────────

-- ============================================================
-- 1. Colonne engagement_id (additive, nullable)
-- ============================================================

ALTER TABLE public.decision_arcs
  ADD COLUMN IF NOT EXISTS engagement_id UUID
    REFERENCES public.engagements(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.decision_arcs.engagement_id IS
  'Rattachement à Engagement (T2A/v19), additif, nullable. ON DELETE SET '
  'NULL : la suppression d''un Engagement ne détruit jamais le DecisionArc '
  '(mémoire décisionnelle professionnelle — survit à la relation qui l''a '
  'vue naître, cf. Mission 4). Résolu à la création quand possible '
  '(services/arc_service.py::_resolve_current_engagement_id), backfillé '
  'pour l''historique via script dédié. NULL = non résolu, jamais une '
  'valeur fabriquée.';

CREATE INDEX IF NOT EXISTS idx_decision_arcs_engagement_id
  ON public.decision_arcs(engagement_id);

-- ============================================================
-- 2. Carve-out étroit sur l'immutabilité (arcs CLOSED historiques)
-- ============================================================
-- Sans ce carve-out, AUCUN arc CLOSED ne pourrait jamais recevoir
-- engagement_id par backfill : le trigger existant (v16) refuse toute
-- UPDATE sur un arc dont OLD.status = 'closed', sans exception. Les arcs
-- CLOSED sont précisément ceux qui ont complété tout le cycle décisionnel
-- (S→R→I→D→E→C→L) — les exclure définitivement de l'attachement à
-- Engagement contredirait directement l'objectif de cette migration
-- (continuité décisionnelle à travers le temps, cf. mission, test CFO
-- Phidani : "en mars... en juin... en septembre... en décembre").
--
-- Le carve-out est verrouillé au maximum : autorise engagement_id à
-- changer UNIQUEMENT de NULL vers une valeur (jamais une réécriture d'une
-- valeur déjà résolue), et UNIQUEMENT si aucun autre champ ne change dans
-- la même instruction. Toute autre tentative de modification sur un arc
-- CLOSED reste refusée exactement comme avant (comportement v16 inchangé).
--
-- Correction post-revue adversariale (mission DecisionArc ↔ Engagement,
-- verdict B — MERGE AFTER SMALL CORRECTIONS) : la première version de ce
-- carve-out omettait company_id, created_at et updated_at de la liste des
-- champs verrouillés. Aucun appelant réel n'exploite cette omission
-- aujourd'hui (le seul appelant, le backfill, envoie une charge utile à
-- une seule clé), mais elle contredisait l'intention déclarée ci-dessus
-- ("aucun autre champ ne change"). Corrigée en verrouillant explicitement
-- ces trois champs, sans élargir le carve-out par ailleurs.

CREATE OR REPLACE FUNCTION public.arc_immutability_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Un arc CLOSED est scellé : aucune modification autorisée, SAUF le
  -- rattachement rétroactif, unique, de engagement_id (voir ci-dessus).
  IF OLD.status = 'closed' THEN
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
      -- Rattachement relationnel pur : ne compte jamais comme une
      -- modification de contenu décisionnel. updated_at et created_at sont
      -- désormais explicitement verrouillés ci-dessus (correction post-revue
      -- adversariale) plutôt que simplement supposés inchangés par
      -- construction de l'appelant — l'UPDATE appelant ne fixe en pratique
      -- que engagement_id, donc NEW.updated_at == OLD.updated_at de toute
      -- façon, mais le trigger ne dépend plus de cette hypothèse implicite.
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

-- Le trigger existant (v16) référence déjà cette fonction par nom —
-- CREATE OR REPLACE suffit, aucune modification du CREATE TRIGGER lui-même
-- n'est nécessaire.

-- ── Fin migration v21 ────────────────────────────────────────────────────────
