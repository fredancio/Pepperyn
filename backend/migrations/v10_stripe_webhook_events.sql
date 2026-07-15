-- v10_stripe_webhook_events.sql
-- WP1B.3 + WP1B.3.1 : Idempotence des webhooks Stripe — hardening sécurité SQL
--
-- Crée :
--   1. Table stripe_webhook_events — registre d'idempotence (1 ligne par event Stripe)
--   2. Protections de la table (REVOKE anon / authenticated)
--   3. Fonction apply_stripe_webhook — atomique + validations SQL defense-in-depth
--   4. Protections de la fonction (REVOKE PUBLIC/anon/authenticated + GRANT service_role)
--
-- Garanties :
--   - même stripe_event_id → un seul effet métier, même si Stripe retente
--   - le marqueur d'idempotence et le traitement métier sont dans la même transaction PG
--   - seul le service_role backend peut appeler la fonction
--   - aucun utilisateur ordinaire (anon, authenticated) n'a accès à la table ni à la fonction
--   - les paramètres métier sont validés à deux niveaux : Python (billing_service) + SQL

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. TABLE D'IDEMPOTENCE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.stripe_webhook_events (
    stripe_event_id  TEXT        PRIMARY KEY,
    event_type       TEXT        NOT NULL,
    processed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    company_id       TEXT,
    action           TEXT
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. PROTECTION DE LA TABLE
--
-- stripe_webhook_events est une table interne au backend.
-- Elle ne doit jamais être accessible directement via PostgREST ou l'API Supabase.
-- Le service_role dispose de tous les droits implicitement (rôle superuser Supabase).
-- ═══════════════════════════════════════════════════════════════════════════════

REVOKE ALL ON TABLE public.stripe_webhook_events FROM PUBLIC;
REVOKE ALL ON TABLE public.stripe_webhook_events FROM anon;
REVOKE ALL ON TABLE public.stripe_webhook_events FROM authenticated;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. FONCTION ATOMIQUE apply_stripe_webhook
--
-- SECURITY DEFINER : s'exécute avec les privilèges du propriétaire de la fonction
-- (postgres / service_role). Impose la restriction des droits d'appel ci-dessous.
--
-- SET search_path = public : prévient l'injection via un search_path malveillant.
-- Toutes les références de tables sont en outre explicitement qualifiées (public.*).
--
-- Paramètres :
--   p_stripe_event_id  TEXT  — event["id"] Stripe (ex : "evt_1AbCdEf…")
--   p_event_type       TEXT  — event["type"] Stripe (ex : "checkout.session.completed")
--   p_action           TEXT  — action dérivée côté serveur :
--                              "update_plan" | "add_bonus" | "downgrade_free" | "noop" | "unhandled"
--   p_company_id       TEXT  — UUID de la company Pepperyn (NULL pour noop/unhandled)
--   p_quantity         INT   — analyses à créditer — WHITELIST : 10 | 20 | 80 uniquement
--   p_new_plan         TEXT  — nouveau plan — WHITELIST : "pro" | "scale" | "free" uniquement
--   p_stripe_customer  TEXT  — stripe_customer_id (optionnel, stocké sur update_plan)
--
-- Retourne JSONB :
--   {"status": "processed"}  — premier traitement : marqueur inséré + métier appliqué
--   {"status": "duplicate"}  — stripe_event_id déjà présent → traitement ignoré
--   (exception)              — paramètre non autorisé → rollback complet
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.apply_stripe_webhook(
    p_stripe_event_id TEXT,
    p_event_type      TEXT,
    p_action          TEXT,
    p_company_id      TEXT    DEFAULT NULL,
    p_quantity        INT     DEFAULT NULL,
    p_new_plan        TEXT    DEFAULT NULL,
    p_stripe_customer TEXT    DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_year_month TEXT;
BEGIN
    -- ── VALIDATION DES PARAMÈTRES — DEFENSE IN DEPTH ─────────────────────────
    --
    -- La couche Python (billing_service.py + Product Catalog) valide déjà ces valeurs.
    -- La couche SQL les revalide pour résister à un appel direct hors Python
    -- (SQL Editor Supabase, script admin, credentials compromis).
    --
    -- En cas de paramètre non autorisé : RAISE EXCEPTION → rollback immédiat.
    -- Aucun marqueur n'est inséré. Aucun effet métier n'est appliqué.

    -- 3.1 Whitelist des actions autorisées
    IF p_action NOT IN ('update_plan', 'add_bonus', 'downgrade_free', 'noop', 'unhandled') THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Action non autorisée : ''%''. '
            'Valeurs acceptées : update_plan, add_bonus, downgrade_free, noop, unhandled.',
            p_action;
    END IF;

    -- 3.2 Whitelist des Plans autorisés (update_plan uniquement)
    -- "free" est autorisé : il est utilisé par le Stripe Billing Portal (annulation).
    -- "enterprise" et "power" ne sont jamais autorisés via ce vecteur.
    IF p_action = 'update_plan'
       AND p_new_plan IS NOT NULL
       AND p_new_plan NOT IN ('pro', 'scale', 'free')
    THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Plan non autorisé : ''%''. '
            'Plans acceptés pour update_plan : pro, scale, free.',
            p_new_plan;
    END IF;

    -- 3.3 Whitelist des quantités autorisées (add_bonus uniquement)
    -- Starter=10, Growth=20, Scale Capacity Pack=80. Aucune autre quantité.
    IF p_action = 'add_bonus'
       AND p_quantity IS NOT NULL
       AND p_quantity NOT IN (10, 20, 80)
    THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Quantité non autorisée : %. '
            'Quantités acceptées pour add_bonus : 10 (Starter), 20 (Growth), 80 (Scale Pack).',
            p_quantity;
    END IF;

    -- ── ÉTAPE 1 : INSERTION ATOMIQUE DANS LE REGISTRE D'IDEMPOTENCE ──────────
    --
    -- ON CONFLICT DO NOTHING : si stripe_event_id existe déjà, 0 lignes insérées.
    -- FOUND = false → NOT FOUND = true → l'événement est un doublon.
    INSERT INTO public.stripe_webhook_events
        (stripe_event_id, event_type, company_id, action)
    VALUES
        (p_stripe_event_id, p_event_type, p_company_id, p_action)
    ON CONFLICT (stripe_event_id) DO NOTHING;

    -- ── ÉTAPE 2 : DÉTECTION DOUBLON ──────────────────────────────────────────
    IF NOT FOUND THEN
        RETURN jsonb_build_object('status', 'duplicate');
    END IF;

    -- ── ÉTAPE 3 : TRAITEMENT MÉTIER — MÊME TRANSACTION ───────────────────────
    --
    -- Si une exception est levée ici, le ROLLBACK annule aussi l'INSERT ci-dessus.
    -- Aucun événement ne peut être marqué "traité" sans que l'effet métier soit appliqué.

    IF p_action = 'update_plan'
       AND p_company_id IS NOT NULL
       AND p_new_plan IS NOT NULL
    THEN
        UPDATE public.companies
        SET
            plan               = p_new_plan,
            stripe_customer_id = COALESCE(p_stripe_customer, stripe_customer_id)
        WHERE id = p_company_id::UUID;

    ELSIF p_action = 'add_bonus'
          AND p_company_id IS NOT NULL
          AND p_quantity IS NOT NULL
    THEN
        -- Incrément atomique via INSERT … ON CONFLICT DO UPDATE.
        -- Remplace le READ-THEN-WRITE non atomique de add_bonus_analyses().
        -- Si la ligne du mois n'existe pas encore : créée avec p_quantity.
        -- Si elle existe : bonus_analyses incrémenté de façon atomique.
        v_year_month := TO_CHAR(NOW() AT TIME ZONE 'UTC', 'YYYY-MM');

        INSERT INTO public.usage_limits (company_id, year_month, bonus_analyses)
        VALUES (p_company_id::UUID, v_year_month, p_quantity)
        ON CONFLICT (company_id, year_month) DO UPDATE
            SET bonus_analyses =
                COALESCE(public.usage_limits.bonus_analyses, 0)
                + EXCLUDED.bonus_analyses;

    ELSIF p_action = 'downgrade_free'
          AND p_company_id IS NOT NULL
    THEN
        UPDATE public.companies
        SET plan = 'free'
        WHERE id = p_company_id::UUID;

    -- ELSE : 'noop' ou 'unhandled'
    --   → le marqueur d'idempotence est inséré, aucun effet métier.
    END IF;

    RETURN jsonb_build_object('status', 'processed');
END;
$$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. PERMISSIONS DE LA FONCTION
--
-- La fonction est SECURITY DEFINER : sans REVOKE explicite, PUBLIC (et donc anon
-- et authenticated) héritent de EXECUTE et peuvent l'appeler via PostgREST avec
-- des paramètres arbitraires, bénéficiant de l'élévation de privilège.
--
-- Modèle de permission cible :
--   anon          → NO EXECUTE
--   authenticated → NO EXECUTE
--   service_role  → EXECUTE (backend Railway uniquement)
-- ═══════════════════════════════════════════════════════════════════════════════

REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM anon;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) TO service_role;

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK (ne pas exécuter — conservé ici pour référence)
--
-- REVOKE EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT,TEXT,TEXT,TEXT,INT,TEXT,TEXT) FROM service_role;
-- DROP FUNCTION IF EXISTS public.apply_stripe_webhook(TEXT,TEXT,TEXT,TEXT,INT,TEXT,TEXT);
-- DROP TABLE IF EXISTS public.stripe_webhook_events;
-- ═══════════════════════════════════════════════════════════════════════════════
