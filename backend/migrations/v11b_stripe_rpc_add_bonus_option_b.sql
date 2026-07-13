-- v11b_stripe_rpc_add_bonus_option_b.sql
-- WP1C.2 — Adaptation Stripe RPC : Option B Executive Capacity Packs
--
-- Met à jour apply_stripe_webhook pour que l'action 'add_bonus' incrémente
-- companies.bonus_analyses_remaining (stock permanent) au lieu de
-- usage_limits.bonus_analyses (compteur mensuel, désormais vestige Option A).
--
-- La colonne companies.bonus_analyses_remaining doit exister (migration v11).
-- Cette migration remplace uniquement le corps de la fonction PL/pgSQL.
-- Les permissions (REVOKE/GRANT) sont ré-appliquées explicitement.
--
-- À exécuter dans Supabase SQL Editor APRÈS v11_option_b_executive_capacity_packs.sql.

-- ═══════════════════════════════════════════════════════════════════════════════
-- FONCTION apply_stripe_webhook — Version Option B
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
        -- Option B (WP1C.2) : le stock bonus est une propriété permanente du compte.
        -- Incrément atomique sur companies.bonus_analyses_remaining.
        -- Plus de dépendance mensuelle (usage_limits).
        -- La colonne bonus_analyses_remaining est créée par v11_option_b_executive_capacity_packs.sql.
        UPDATE public.companies
        SET bonus_analyses_remaining =
            COALESCE(bonus_analyses_remaining, 0) + p_quantity
        WHERE id = p_company_id::UUID;

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
-- PERMISSIONS — Ré-application après CREATE OR REPLACE
--
-- CREATE OR REPLACE FUNCTION préserve les GRANT/REVOKE PostgreSQL existants.
-- On les ré-applique ici de façon explicite pour garantir l'état cible
-- indépendamment de l'ordre d'exécution des migrations.
-- ═══════════════════════════════════════════════════════════════════════════════

REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM anon;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) TO service_role;

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK (ne pas exécuter — conservé ici pour référence)
--
-- Pour revenir à la version Option A, ré-exécuter v10_stripe_webhook_events.sql.
-- ═══════════════════════════════════════════════════════════════════════════════
