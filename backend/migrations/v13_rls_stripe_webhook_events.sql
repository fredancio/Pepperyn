-- v13_rls_stripe_webhook_events.sql
-- WP4B.5 — Sécurité : Row Level Security sur stripe_webhook_events
--
-- Contexte
-- --------
-- v10 protège la table via REVOKE ALL ON TABLE pour anon et authenticated.
-- Cette migration ajoute une couche de défense en profondeur indépendante : RLS.
-- Les deux protections coexistent. Si les privilèges REVOKE de v10 étaient
-- accidentellement modifiés, la policy RLS bloquerait toujours l'accès direct.
--
-- Idempotence
-- -----------
-- DROP POLICY IF EXISTS avant CREATE POLICY : la migration peut être réexécutée
-- sans erreur (par exemple lors d'un redéploiement ou d'une réapplication manuelle).
-- ALTER TABLE ... ENABLE ROW LEVEL SECURITY est idempotent nativement en PostgreSQL.
--
-- Impact sur l'architecture existante
-- ------------------------------------
-- apply_stripe_webhook() (SECURITY DEFINER)
--   → s'exécute avec les privilèges du propriétaire de la fonction (postgres)
--   → postgres est superuser → bypass RLS automatique
--   → NON AFFECTÉ. Ne pas utiliser FORCE ROW LEVEL SECURITY.
--
-- Backend Railway (service_role)
--   → Supabase accorde BYPASSRLS à service_role au niveau rôle PostgreSQL
--   → les appels RPC via la clé service_role contournent RLS
--   → NON AFFECTÉ : webhooks Stripe, appels RPC, backfill continuent de fonctionner.
--
-- anon / authenticated
--   → bloqués par REVOKE (v10) ET par RLS (v13) : deux couches indépendantes.
--   → les REVOKE sont réaffirmés ci-dessous pour garantir leur présence
--     indépendamment de l'ordre d'exécution des migrations.
--
-- Politique choisie
-- -----------------
-- FOR ALL       : couvre SELECT, INSERT, UPDATE, DELETE — aucune opération oubliée.
-- USING         : filtre les lignes accessibles en lecture et comme source d'UPDATE/DELETE.
-- WITH CHECK    : valide les lignes écrites (INSERT, UPDATE cible).
--                 Déclaré explicitement pour que la protection des écritures soit
--                 immédiatement visible à l'audit, sans dépendre d'une inférence implicite.
--                 Justification : intention explicite, auditabilité, défense en profondeur —
--                 et non pas une crainte d'évolution de PostgreSQL (le comportement implicite
--                 USING → WITH CHECK est stable et documenté dans les specs SQL).
--
-- Ce qui N'est PAS fait (et pourquoi)
-- -------------------------------------
-- FORCE ROW LEVEL SECURITY : non appliqué. Cette option forcerait RLS même sur
--   le propriétaire de la table (postgres). Elle bloquerait apply_stripe_webhook()
--   (SECURITY DEFINER s'exécutant comme postgres) — ce n'est pas le but recherché.
--   Le but est de bloquer anon et authenticated, pas le propriétaire de la fonction.

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. RÉAFFIRMATION DES PROTECTIONS PAR PRIVILÈGES (v10)
--
-- Ces REVOKE sont présents dans v10. Ils sont réaffirmés ici pour garantir
-- qu'ils s'appliquent même si v13 est exécutée dans un environnement différent
-- ou si v10 n'a pas encore été appliquée dans cet ordre.
-- Aucun REVOKE sur service_role ou postgres.
-- ═══════════════════════════════════════════════════════════════════════════════

REVOKE ALL ON TABLE public.stripe_webhook_events FROM anon;
REVOKE ALL ON TABLE public.stripe_webhook_events FROM authenticated;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. ACTIVATION DE RLS
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.stripe_webhook_events ENABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. POLICY — service_role_only (idempotente)
--
-- DROP IF EXISTS : permet la réexécution sans erreur "policy already exists".
--
-- FOR ALL         : toutes les opérations (SELECT, INSERT, UPDATE, DELETE).
-- USING           : seul auth.role() = 'service_role' peut lire ou cibler des lignes.
-- WITH CHECK      : seul auth.role() = 'service_role' peut écrire de nouvelles lignes.
-- ═══════════════════════════════════════════════════════════════════════════════

DROP POLICY IF EXISTS "service_role_only" ON public.stripe_webhook_events;

CREATE POLICY "service_role_only"
    ON public.stripe_webhook_events
    FOR ALL
    USING      (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK (ne pas exécuter en production — conservé pour référence)
--
-- DROP POLICY IF EXISTS "service_role_only" ON public.stripe_webhook_events;
-- ALTER TABLE public.stripe_webhook_events DISABLE ROW LEVEL SECURITY;
-- ═══════════════════════════════════════════════════════════════════════════════
