-- v12_stripe_lifecycle_sync.sql
-- WP4B.5 — Architecture cycle de vie Stripe complète
--
-- Problème résolu :
--   Avant cette migration, apply_stripe_webhook ne gérait que checkout.session.completed
--   (action update_plan), ce qui laissait stripe_subscription_id = NULL et
--   subscription_status = 'inactive' après tout paiement réussi.
--
-- Architecture cible :
--
--   Événement                            Action             Effet en base
--   ─────────────────────────────────────────────────────────────────────────────────────
--   checkout.session.completed         → init_subscription  plan + customer_id + subscription_id
--   customer.subscription.created      → sync_subscription  subscription_status (+ plan si changé)
--   customer.subscription.updated      → sync_subscription  subscription_status (+ plan si changé)  ← seule autorité du statut
--   customer.subscription.deleted      → downgrade_free     plan='free' + status='canceled' + sub_id=NULL
--   invoice.paid                       → noop               audit/trace uniquement (statut déjà correct via subscription.updated)
--   invoice.payment_failed             → noop               audit/trace uniquement (subscription.updated déclenche status=past_due)
--
-- Résistance à l'ordre non garanti des webhooks :
--   create_checkout_session passe subscription_data.metadata={company_id, plan_or_addon}
--   à Stripe → sub.metadata.company_id disponible dans subscription.created sans dépendre
--   de checkout.session.completed. Fallback : stripe_customer_id → companies.stripe_customer_id.
--   Si aucune résolution : ValueError → Stripe retente l'événement.
--
-- Cette migration crée une fonction avec 9 paramètres (+ p_stripe_subscription, + p_subscription_status).
-- En PostgreSQL, l'ajout de paramètres crée une nouvelle surcharge (9-params ≠ 7-params).
-- La fonction 7-params (v10/v11b) est conservée structurellement mais son grant service_role
-- est révoqué ici pour garantir que seule la version 9-params est appelable depuis le backend.
--
-- À exécuter dans Supabase SQL Editor APRÈS v11b_stripe_rpc_add_bonus_option_b.sql.

-- ═══════════════════════════════════════════════════════════════════════════════
-- FONCTION apply_stripe_webhook — Version 9 paramètres (WP4B.5)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.apply_stripe_webhook(
    p_stripe_event_id      TEXT,
    p_event_type           TEXT,
    p_action               TEXT,
    p_company_id           TEXT    DEFAULT NULL,
    p_quantity             INT     DEFAULT NULL,
    p_new_plan             TEXT    DEFAULT NULL,
    p_stripe_customer      TEXT    DEFAULT NULL,
    p_stripe_subscription  TEXT    DEFAULT NULL,   -- WP4B.5 : sub_xxx de l'abonnement Stripe
    p_subscription_status  TEXT    DEFAULT NULL    -- WP4B.5 : active | trialing | past_due | canceled | …
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

    -- 1. Whitelist des actions autorisées
    IF p_action NOT IN (
        'init_subscription',    -- WP4B.5 : checkout.session.completed
        'sync_subscription',    -- WP4B.5 : subscription.* + invoice.*
        'update_plan',          -- conservé pour compatibilité descendante (événements archivés)
        'add_bonus',
        'downgrade_free',
        'noop',
        'unhandled'
    ) THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Action non autorisée : ''%''. '
            'Valeurs acceptées : init_subscription, sync_subscription, update_plan, '
            'add_bonus, downgrade_free, noop, unhandled.',
            p_action;
    END IF;

    -- 2. Whitelist des plans autorisés
    --    Couvre update_plan (compat), init_subscription et sync_subscription.
    --    "free" est autorisé : utilisé par le Stripe Billing Portal (annulation manuelle).
    IF p_action IN ('update_plan', 'init_subscription', 'sync_subscription')
       AND p_new_plan IS NOT NULL
       AND p_new_plan NOT IN ('pro', 'scale', 'free')
    THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Plan non autorisé : ''%''. '
            'Plans acceptés : pro, scale, free.',
            p_new_plan;
    END IF;

    -- 3. Whitelist des quantités autorisées (add_bonus uniquement)
    --    Starter=10, Growth=20, Scale Capacity Pack=80.
    IF p_action = 'add_bonus'
       AND p_quantity IS NOT NULL
       AND p_quantity NOT IN (10, 20, 80)
    THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Quantité non autorisée : %. '
            'Quantités acceptées pour add_bonus : 10 (Starter), 20 (Growth), 80 (Scale Pack).',
            p_quantity;
    END IF;

    -- 4. Whitelist des statuts d'abonnement autorisés (sync_subscription uniquement)
    --    Statuts natifs Stripe : active, trialing, past_due, canceled, unpaid, paused, incomplete, incomplete_expired.
    IF p_action IN ('sync_subscription')
       AND p_subscription_status IS NOT NULL
       AND p_subscription_status NOT IN (
           'active', 'trialing', 'past_due', 'canceled',
           'unpaid', 'paused', 'incomplete', 'incomplete_expired'
       )
    THEN
        RAISE EXCEPTION
            '[apply_stripe_webhook] Statut d''abonnement non autorisé : ''%''. '
            'Statuts acceptés : active, trialing, past_due, canceled, unpaid, paused, '
            'incomplete, incomplete_expired.',
            p_subscription_status;
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

    -- ── init_subscription (checkout.session.completed) ───────────────────────
    -- Initialise plan + stripe_customer_id + stripe_subscription_id.
    -- Ne touche PAS subscription_status (délégué à customer.subscription.created).
    IF p_action = 'init_subscription'
       AND p_company_id IS NOT NULL
       AND p_new_plan IS NOT NULL
    THEN
        UPDATE public.companies
        SET
            plan                   = p_new_plan,
            stripe_customer_id     = COALESCE(p_stripe_customer, stripe_customer_id),
            stripe_subscription_id = COALESCE(p_stripe_subscription, stripe_subscription_id)
        WHERE id = p_company_id::UUID;

    -- ── sync_subscription (customer.subscription.*, invoice.*) ───────────────
    -- Source de vérité du cycle de vie : subscription_status.
    -- Met optionnellement à jour le plan si p_new_plan est non NULL
    -- (détection changement PRO ↔ SCALE via _resolve_plan_from_price_id).
    -- stripe_subscription_id et stripe_customer_id sont mis à jour si fournis.
    ELSIF p_action = 'sync_subscription'
          AND p_company_id IS NOT NULL
    THEN
        UPDATE public.companies
        SET
            subscription_status    = COALESCE(p_subscription_status, subscription_status),
            stripe_subscription_id = COALESCE(p_stripe_subscription, stripe_subscription_id),
            stripe_customer_id     = COALESCE(p_stripe_customer, stripe_customer_id),
            plan                   = CASE
                                         WHEN p_new_plan IS NOT NULL THEN p_new_plan
                                         ELSE plan
                                     END
        WHERE id = p_company_id::UUID;

    -- ── update_plan (compatibilité descendante — événements déjà en registre) ─
    -- Utilisé par les événements checkout.session.completed antérieurs à WP4B.5
    -- dont l'action "update_plan" est stockée dans stripe_webhook_events.
    -- Ces événements sont idempotents et ne seront jamais retraités.
    -- Conservé pour robustesse uniquement.
    ELSIF p_action = 'update_plan'
          AND p_company_id IS NOT NULL
          AND p_new_plan IS NOT NULL
    THEN
        UPDATE public.companies
        SET
            plan                   = p_new_plan,
            stripe_customer_id     = COALESCE(p_stripe_customer, stripe_customer_id),
            stripe_subscription_id = COALESCE(p_stripe_subscription, stripe_subscription_id)
        WHERE id = p_company_id::UUID;

    -- ── add_bonus (Executive Capacity Packs) ─────────────────────────────────
    -- Stock permanent companies.bonus_analyses_remaining (Option B — WP1C.2).
    -- Aucun lien avec les compteurs mensuels usage_limits.
    ELSIF p_action = 'add_bonus'
          AND p_company_id IS NOT NULL
          AND p_quantity IS NOT NULL
    THEN
        UPDATE public.companies
        SET bonus_analyses_remaining =
            COALESCE(bonus_analyses_remaining, 0) + p_quantity
        WHERE id = p_company_id::UUID;

    -- ── downgrade_free (customer.subscription.deleted) ───────────────────────
    -- Rétrograde le plan à FREE, marque le statut canceled et vide subscription_id.
    -- stripe_customer_id est conservé (le client peut se réabonner).
    ELSIF p_action = 'downgrade_free'
          AND p_company_id IS NOT NULL
    THEN
        UPDATE public.companies
        SET
            plan                   = 'free',
            subscription_status    = 'canceled',
            stripe_subscription_id = NULL
        WHERE id = p_company_id::UUID;

    -- ELSE : 'noop' ou 'unhandled'
    --   → le marqueur d'idempotence est inséré, aucun effet métier.
    END IF;

    RETURN jsonb_build_object('status', 'processed');
END;
$$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PERMISSIONS
--
-- La fonction 9-params est une surcharge distincte de la 7-params.
-- On révoque le grant service_role sur la 7-params pour forcer le routage
-- vers cette version à jour. On accorde EXECUTE à service_role sur la 9-params.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Révoquer la fonction 7-params (v10/v11b) pour empêcher tout appel résiduel
REVOKE EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT)
    FROM service_role;

-- Protéger la nouvelle fonction 9-params
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)
    FROM PUBLIC;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)
    FROM anon;
REVOKE ALL ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)
    FROM authenticated;
GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT)
    TO service_role;

-- ── Supprimer définitivement la surcharge 7-params (v10/v11b) ────────────────
--
-- Ordre garanti : la fonction 9-params est déjà créée (CREATE OR REPLACE ci-dessus)
-- et ses permissions sont en place (REVOKE PUBLIC/anon/authenticated + GRANT service_role).
-- Le DROP ne crée donc aucune fenêtre où la RPC serait inaccessible.
--
-- Après ce DROP :
--   - Toute tentative d'appel de l'ancienne signature (7 args) produit une erreur SQL
--     "function not found" — comportement de sécurité explicite, pas silencieux.
--   - La 9-params reste la seule surcharge disponible.
--   - Les événements déjà enregistrés dans stripe_webhook_events avec action='update_plan'
--     sont idempotents et ne seront jamais retraités — la compat descendante dans la 9-params
--     suffit si un tel event devait être rejoué.
DROP FUNCTION IF EXISTS public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ÉVÉNEMENTS STRIPE À CONFIGURER dans le Dashboard (webhook + stripe listen)
--
-- Déjà configurés :
--   checkout.session.completed          → init_subscription
--   customer.subscription.deleted       → downgrade_free
--   invoice.payment_failed              → noop (audit)
--
-- À AJOUTER dans Stripe Dashboard → Webhooks → Modifier l'endpoint :
--   customer.subscription.created       → sync_subscription
--   customer.subscription.updated       → sync_subscription   ← seule autorité du statut
--   invoice.paid                        → noop (audit, future notification)
--
-- Commande stripe listen locale (E2E tests) :
--   stripe listen --forward-to localhost:8000/api/billing/webhook \
--     --events checkout.session.completed,customer.subscription.created, \
--              customer.subscription.updated,customer.subscription.deleted, \
--              invoice.paid,invoice.payment_failed
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- BACKFILL DONNÉES EXISTANTES
--
-- Les comptes créés avant WP4B.5 ont stripe_subscription_id = NULL
-- et subscription_status = 'inactive'.
-- Récupérer les subscription IDs depuis le Stripe Dashboard :
--   Stripe Dashboard → Customers → [customer_id] → Subscriptions → [sub_id]
-- Puis exécuter manuellement :
--
--   UPDATE public.companies
--   SET
--       stripe_subscription_id = 'sub_xxx',
--       subscription_status    = 'active'
--   WHERE stripe_customer_id = 'cus_xxx';
--
-- (À effectuer pour chaque compte PRO/SCALE existant après déploiement de v12.)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK
-- Pour revenir à la version 7-params :
--   GRANT EXECUTE ON FUNCTION public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT) TO service_role;
--   DROP FUNCTION IF EXISTS public.apply_stripe_webhook(TEXT, TEXT, TEXT, TEXT, INT, TEXT, TEXT, TEXT, TEXT);
-- ═══════════════════════════════════════════════════════════════════════════════
