-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v23 : evidence_ledger_entries.observed_period_end (FTE v0 —
-- mission dédiée 2026-08-08, docs/Architecture/FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md)
--
-- Contexte : le classificateur déterministe temporal_normalizer.py calcule
--   déjà, à l'ingestion de chaque fichier (services/file_parser.py:294), la
--   période la plus récente observée dans le dataset — mais ce résultat
--   n'est aujourd'hui persisté nulle part : il sert uniquement à enrichir
--   le prompt LLM puis disparaît. Les fichiers source ne sont eux-mêmes
--   jamais conservés (aucun stockage de fichier brut nulle part dans
--   backend/, vérifié par recherche exhaustive avant cette migration) —
--   sans capture ponctuelle, cette information de temps métier est perdue
--   de façon irréversible après chaque analyse.
--
-- Doctrine (FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md §10/§11, arbitrage
--   2026-08-08) : un seul champ est le minimum irrécupérable — la borne de
--   FIN de la période la plus récente observée pour CETTE capture. Ce
--   champ N'EST PAS "la période financière" elle-même (pas de VO riche,
--   pas de granularité mensuelle codée en dur) : c'est uniquement la borne
--   nécessaire et suffisante pour qu'une analyse future compare "la période
--   la plus récente maintenant" à "la dernière période connue" pour le
--   même Engagement. Ne jamais ajouter observed_period_start pour la
--   symétrie — le dataset courant dérive toujours sa propre borne de départ
--   fraîchement à chaque analyse (services/fte_minimal.py), rien ne
--   nécessite qu'elle soit aussi persistée.
--
-- Ce que fait cette migration :
--   ALTER TABLE ADD COLUMN, nullable, additive. AUCUNE réécriture de
--   v18. Compatible sans changement avec le trigger d'immutabilité
--   existant (evidence_ledger_immutability_guard, BEFORE UPDATE
--   uniquement — cette colonne n'est jamais écrite après l'INSERT initial,
--   jamais lue par ce trigger).
--
-- Ce que cette migration NE fait PAS :
--   - Aucune sémantique de clôture (pas de close_confidence, pas de
--     grace-window). Voir contrat §14 : la clôture est explicitement hors
--     périmètre v0.
--   - Aucun objet PeriodObservation/FiscalPeriod de première classe.
--   - Aucune donnée LLM (QuantifiedImpact.temporal_role n'est jamais lu
--     pour peupler cette colonne — voir services/fte_minimal.py).
--   - Aucun fallback vers la date d'analyse ou la date système : une
--     absence de mois résoluble dans les en-têtes du fichier laisse cette
--     colonne NULL, jamais une valeur fabriquée (Article III).
--
-- Lignes historiques : NULL par défaut, restent valides — une absence
--   reste une absence, jamais réinterprétée comme "période inconnue = 0"
--   ni backfillée rétroactivement (aucune donnée source à reconstituer).
--
-- VALIDATION POSTGRES RÉELLE (2026-08-08) : appliquée sur ce fichier exact,
--   byte-for-byte, sur le projet Supabase « Pepperyn Integration Test »
--   (jamais production), avec autorisation explicite de Fred. Vérifiée :
--   colonne DATE nullable présente ; INSERT isolé avec observed_period_end
--   renseigné réussit et se relit correctement ; UPDATE sur cette même
--   ligne (y compris sur observed_period_end) toujours rejeté par
--   evidence_ledger_immutability_guard (v18, inchangé) ; données de test
--   isolées (préfixe bbbbbbbb-2300-...) nettoyées ; comptes de lignes
--   pré-existants (2 companies, 1 evidence_ledger_entries, 1 analyses)
--   inchangés avant/après.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.evidence_ledger_entries
  ADD COLUMN IF NOT EXISTS observed_period_end DATE NULL;

COMMENT ON COLUMN public.evidence_ledger_entries.observed_period_end IS
  'FTE v0 — dernière borne de temps métier déterministiquement observée '
  'dans le dataset de CETTE capture (dérivée de temporal_normalizer.py, '
  'jamais du LLM, jamais de QuantifiedImpact.temporal_role). NE représente '
  'PAS : une date de clôture, le temps de connaissance (created_at), le '
  'temps de décision (DecisionArc), une identité de calendrier fiscal, une '
  'cadence de reporting, ou un état d''approbation. NULL = aucune période '
  'résoluble de façon déterministe pour cette capture — jamais réinterprété '
  'comme zéro ou comme la date d''analyse.';

-- ── Fin migration v23 ────────────────────────────────────────────────────────
