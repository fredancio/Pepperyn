-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v19 : Engagements — T2A (Engagement Foundation)
-- Table : engagements
-- Fonction : create_entity_with_engagement() (RPC, chemin applicatif)
--
-- Fondation : ADR-002 — Engagement Foundation (statut ACCEPTED).
-- Plan d'implémentation : docs/Architecture/blueprint/T2A_Implementation_Plan.md (v2, amendé).
--
-- Ce que fait cette migration :
--   1. Crée la table engagements (agrégat racine Engagement, ADR-002 §3.2).
--   2. Crée la fonction RPC create_entity_with_engagement(), qui insère une
--      Entity puis son Engagement dans UNE SEULE transaction Postgres —
--      nécessaire car le client applicatif (supabase-py) ne permet aucune
--      transaction multi-appels (T2A_Implementation_Plan.md §5).
--   3. NE MODIFIE AUCUNE TABLE EXISTANTE — aucun ALTER TABLE, aucun UPDATE.
--
-- Ce que cette migration NE fait PAS (hors périmètre T2A, cf. ADR-002 §3.9,
-- §3.10 et le plan d'implémentation §11) :
--   - Aucun trigger générique sur entities (révoqué, voir historique des
--     révisions du plan d'implémentation — remplacé par cette RPC pour le
--     chemin applicatif et par v20 pour le chemin d'inscription).
--   - Aucune colonne company_id sur engagements (ADR-002 §3.2/§3.12) —
--     résolue par jointure vers entities.company_id.
--   - Aucune colonne scope (ADR-002 §3.10, plan §3/§7) — entity_id porte
--     déjà intégralement cette information en T2.
--   - Aucun consommateur de production ne lit cette table à ce stade.
--
-- Statut initial (ADR-002 §3.5, T2A_Implementation_Plan.md §6) :
--   Une Entity nouvellement créée ne peut, par construction, avoir aucune
--   Analysis existante — cette fonction pose donc toujours status='prospect'.
--   La règle "active si Analysis existante, prospect sinon" ne s'applique
--   qu'au backfill historique (services/engagement_service.py), jamais ici.
--
-- Invariant de permanence (ADR-002 §3.3, amendé) : la relation Entity:Engagement
--   est 1:1 et durable — contrainte UNIQUE(entity_id), jamais assouplie.
--
-- Rollback : DROP FUNCTION public.create_entity_with_engagement;
--            DROP TABLE public.engagements;
--            (aucune autre table, aucune donnée existante n'est touchée —
--            ADR-002 §3.16 : rollback trivial par construction)
-- ─────────────────────────────────────────────────────────────────────────────

-- ============================================================
-- 1. TABLE engagements
-- ============================================================
CREATE TABLE IF NOT EXISTS public.engagements (
  id           UUID        DEFAULT gen_random_uuid() PRIMARY KEY,

  -- Relation 1:1 durable et permanente avec Entity (ADR-002 §3.3, amendé
  -- suite à revue — pas une simplification provisoire pour T2).
  entity_id    UUID        NOT NULL UNIQUE REFERENCES public.entities(id) ON DELETE CASCADE,

  -- EngagementStatus (Modèle Idéal §E.1). 'at_risk' est déclaré ici car il
  -- appartient au type complet du domaine, mais aucun code de T2A ne le
  -- positionne jamais — réservé à la future Attention Score (T4).
  status       TEXT        NOT NULL DEFAULT 'prospect'
               CHECK (status IN ('prospect', 'active', 'paused', 'at_risk', 'churned')),

  -- ReviewCadence (Modèle Idéal §E.1). Valeur prescrite par le Blueprint §E
  -- ("cadence par défaut = mensuelle"), appliquée quel que soit le statut.
  cadence      TEXT        NOT NULL DEFAULT 'mensuelle',

  -- Jour cible de la cadence — non défini en T2 (ADR-002 §3.6), aucune
  -- donnée source ne permet de le déduire pour les Entity existantes.
  cadence_day  INT         NULL,

  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.engagements IS
  'Engagement (ADR-002) — agrégat racine du lien continu entre Pepperyn et '
  'une organisation suivie. Un Engagement par Entity, relation 1:1 durable. '
  'Non lue par aucun chemin de production à ce stade (T2A).';

CREATE INDEX IF NOT EXISTS idx_engagements_entity_id
  ON public.engagements(entity_id);

CREATE OR REPLACE TRIGGER update_engagements_updated_at
  BEFORE UPDATE ON public.engagements
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ── RLS (Row Level Security) ──────────────────────────────────────────────────
-- Comme evidence_ledger_entries (v18) et decision_arcs (v16) : le service
-- utilise SERVICE_KEY (contourne RLS). Aucun consommateur, aucune route
-- cliente ne lit cette table à ce stade (ADR-002 §3.10) — pas de politique
-- RLS nécessaire pour T2A. À ajouter si un accès client direct (anon key)
-- est introduit dans une phase ultérieure.

-- ============================================================
-- 2. FONCTION create_entity_with_engagement (RPC — chemin applicatif)
-- ============================================================
-- Appelée depuis backend/services/engagement_service.py::create_for_new_entity()
-- (elle-même appelée par routers/entities.py::create_entity, POST /api/entities).
--
-- Garantie d'atomicité : une fonction PL/pgSQL invoquée par une seule
-- instruction s'exécute, par construction native de Postgres, dans une seule
-- transaction — si l'INSERT sur engagements échoue, l'INSERT sur entities
-- est annulé automatiquement. Aucune Entity orpheline possible depuis ce
-- chemin (T2A_Implementation_Plan.md §5).
--
-- SECURITY DEFINER : même convention que handle_new_user() (v6) et
-- apply_stripe_webhook() (v11b/v12) déjà dans ce dépôt — appelée via le
-- client SERVICE_KEY, qui bypass déjà RLS ; DEFINER évite toute dépendance
-- à des GRANT supplémentaires, cohérent avec les fonctions RPC existantes.
--
-- Ne contient aucune branche conditionnelle liée au statut : celui-ci est
-- toujours 'prospect' pour une Entity qui vient d'être créée (voir note en
-- tête de fichier) — aucune logique métier réelle ne migre vers SQL ici,
-- seulement l'écriture atomique de deux lignes déjà entièrement déterminées.

CREATE OR REPLACE FUNCTION public.create_entity_with_engagement(
  p_workspace_id    UUID,
  p_company_id      UUID,
  p_name            TEXT,
  p_industry        TEXT DEFAULT NULL,
  p_business_model  TEXT DEFAULT NULL,
  p_relation_type   TEXT DEFAULT NULL
)
RETURNS SETOF public.entities
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_entity_id UUID;
BEGIN
  INSERT INTO public.entities (
    workspace_id, company_id, name, industry, business_model, is_primary, relation_type
  )
  VALUES (
    p_workspace_id, p_company_id, p_name, p_industry, p_business_model, FALSE, p_relation_type
  )
  RETURNING id INTO v_entity_id;

  -- ADR-002 / T2A : toute nouvelle Entity reçoit toujours un Engagement au
  -- statut 'prospect' (aucune Analysis ne peut exister avant l'Entity
  -- elle-même). Même fonction, même transaction que l'insert ci-dessus.
  INSERT INTO public.engagements (entity_id, status, cadence)
  VALUES (v_entity_id, 'prospect', 'mensuelle');

  RETURN QUERY SELECT * FROM public.entities WHERE id = v_entity_id;
END;
$$;

COMMENT ON FUNCTION public.create_entity_with_engagement IS
  'T2A — Crée une Entity et son Engagement (status=prospect) atomiquement. '
  'Remplace les deux appels séquentiels non atomiques du chemin applicatif '
  '(POST /api/entities). Voir ADR-002 et T2A_Implementation_Plan.md §5.';

-- ── Fin migration v19 ────────────────────────────────────────────────────────
