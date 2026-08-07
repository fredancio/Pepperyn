-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v18 : Evidence Ledger — T1C-A (Capture)
-- Table : evidence_ledger_entries
-- Trigger : immutabilité (UPDATE bloqué inconditionnellement)
-- Indexes : company_id, entity_id, analyse_id (unique)
--
-- Fondation : ADR-001 — Evidence Foundation.
-- Ownership : ADR-001A — Evidence Ownership (propriété conceptuelle = Engagement ;
--             rattachement transitoire = Entity, en attendant T2 ; réattribution
--             obligatoire dès que l'Engagement existe physiquement).
--
-- Périmètre T1C-A (strictement additif, ADR-001 §8) :
--   - Cette table n'est lue par AUCUN chemin de production existant.
--   - Elle capture exactement ce que services/evidence_capture.py produit
--     aujourd'hui — aucun champ nouveau demandé au LLM (T1C-B, ultérieur,
--     ajoutera amount/currency/fact_ids structurés ; le schéma JSONB ci-dessous
--     absorbera ce changement sans nouvelle migration, cf. capture_schema_version).
--   - Une ligne = une capture = une exécution de run_full_pipeline() (1 analyse).
--     Ce n'est PAS encore la granularité finale du Ledger ("un par Engagement ×
--     période", ADR-001A section 3) — cette granularité dépend de l'Engagement
--     (T2), non encore introduit. T1C-A prouve que la persistance et les
--     invariants tiennent ; la réattribution/consolidation par Engagement×période
--     est un sujet de migration future, pas de celle-ci.
--
-- Invariants ADR-001 §6 couverts par ce schéma :
--   - "Une donnée absente reste absente" → JSONB conserve `null` explicite,
--     jamais de coercition vers 0 (garanti en amont par QuantifiedImpact,
--     financial_truth.py — cette migration ne fait que persister tel quel).
--   - "Immuable... toute correction crée un nouvel enregistrement, jamais une
--     réécriture silencieuse" → trigger evidence_ledger_immutability_guard
--     interdit tout UPDATE, sans condition. C'est délibérément PLUS strict que
--     le texte de l'invariant ("immuable une fois sa période close") : la
--     question ouverte n°2 d'ADR-001 (quel événement marque la clôture d'une
--     période) n'est pas tranchée — en attendant qu'elle le soit, l'entrée est
--     immuable dès sa création. Aucun mécanisme de correction/supersession
--     n'est introduit ici : ce serait trancher une question non encore posée.
--   - "Chaque Evidence appartient à un seul Evidence Ledger faisant autorité" →
--     UNIQUE(analyse_id) : une seule capture par analyse, pas de duplication.
--
-- Rollback : DROP TABLE public.evidence_ledger_entries;
--            (aucune autre table, aucune donnée existante n'est touchée —
--            ADR-001 §11 : rollback trivial par construction)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.evidence_ledger_entries (
  id                      UUID        DEFAULT gen_random_uuid() PRIMARY KEY,

  -- RATTACHEMENT (voir ADR-001A)
  company_id              UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  -- Rattachement transitoire (ADR-001A §4) — en attendant l'Engagement (T2).
  -- Nullable : une analyse peut ne pas avoir d'entity_id assignée aujourd'hui.
  entity_id               UUID                 REFERENCES entities(id)  ON DELETE SET NULL,

  -- ORIGINE — une capture par analyse (T1C-A ; pas la granularité finale du Ledger)
  analyse_id              UUID        NOT NULL REFERENCES analyses(id)  ON DELETE CASCADE,

  -- CONTENU — reflète exactement services/evidence_capture.py:capture_evidence()
  -- facts / unavailable_data / sheets_verified : tels que produits par
  --   _run_evidence_graph_agent (llm_service.py) — canal large, aujourd'hui éphémère.
  -- quantified_impacts : liste de {origin, index, impact} — canal étroit
  --   (IMPACTS FINANCIERS STRUCTURÉS), désérialisé via QuantifiedImpact.to_dict().
  --   impact = null est une valeur légitime (désérialisation impossible ou
  --   absente) — jamais convertie en dict vide ou en zéro.
  facts                   JSONB       NOT NULL DEFAULT '[]'::jsonb,
  unavailable_data        JSONB       NOT NULL DEFAULT '[]'::jsonb,
  sheets_verified         JSONB       NOT NULL DEFAULT '[]'::jsonb,
  quantified_impacts      JSONB       NOT NULL DEFAULT '[]'::jsonb,

  -- Versionne la FORME de la capture (pas la donnée elle-même). T1C-B changera
  -- ce que amount/currency/fact_ids contiennent réellement — permet de savoir,
  -- sans ambiguïté, quelles lignes précèdent ce changement.
  capture_schema_version  TEXT        NOT NULL DEFAULT 'T1C-A-v1',

  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE (analyse_id)
);

COMMENT ON TABLE public.evidence_ledger_entries IS
  'Evidence Ledger (ADR-001) — capture T1C-A uniquement, strictement additive. '
  'Non lue par aucun chemin de production. RÈGLE : immuable dès la création '
  '(trigger evidence_ledger_immutability_guard) — aucun UPDATE autorisé.';

-- ── Trigger immutabilité ─────────────────────────────────────────────────────
-- Volontairement inconditionnel (voir note ci-dessus sur la question ouverte n°2
-- d'ADR-001, non tranchée). Toute tentative d'UPDATE échoue explicitement plutôt
-- que d'être silencieusement acceptée.

CREATE OR REPLACE FUNCTION public.evidence_ledger_immutability_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION
    '[EVIDENCE LEDGER] L''entrée % est immuable. Aucune modification autorisée — '
    'créer une nouvelle entrée plutôt que de réécrire celle-ci (ADR-001 §6).', OLD.id;
END;
$$;

CREATE TRIGGER evidence_ledger_immutability
  BEFORE UPDATE ON public.evidence_ledger_entries
  FOR EACH ROW
  EXECUTE FUNCTION public.evidence_ledger_immutability_guard();

-- ── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_evidence_ledger_company
  ON public.evidence_ledger_entries(company_id);

CREATE INDEX IF NOT EXISTS idx_evidence_ledger_entity
  ON public.evidence_ledger_entries(entity_id)
  WHERE entity_id IS NOT NULL;

-- analyse_id est déjà UNIQUE (index implicite) — pas d'index supplémentaire requis.

-- ── RLS (Row Level Security) ──────────────────────────────────────────────────
-- Comme decision_arcs (v16) : le service utilise SERVICE_KEY (contourne RLS).
-- Aucun consommateur, aucune route client ne lit cette table à ce stade
-- (ADR-001 §8) — pas de politique RLS nécessaire pour T1C-A. À ajouter si un
-- accès client direct (anon key) est introduit dans une phase ultérieure.

-- ── Fin migration v18 ────────────────────────────────────────────────────────
