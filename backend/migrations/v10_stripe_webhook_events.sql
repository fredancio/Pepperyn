-- v10_stripe_webhook_events.sql
-- WP1B.3 : Idempotence des webhooks Stripe
--
-- Crée :
--   1. Table stripe_webhook_events — registre d'idempotence (1 ligne par event Stripe)
--   2. Fonction apply_stripe_webhook — INSERT + traitement métier en une transaction atomique
--
-- Garantie : même stripe_event_id → un seul effet métier, même si Stripe retente.
-- Le marqueur d'idempotence et le traitement métier appartiennent à la même transaction PG.

-- ── 1. Table d'idempotence ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.stripe_webhook_events (
    stripe_event_id  TEXT        PRIMARY KEY,
    event_type       TEXT        NOT NULL,
    processed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    company_id       TEXT,
    action           TEXT
);

-- Table interne : pas de RLS, jamais accédée directement par les clients.
-- Accessible uniquement via la fonction SECURITY DEFINER apply_stripe_webhook.

-- ── 2. Fonction atomique apply_stripe_webhook ─────────────────────────────────
--
-- Paramètres :
--   p_stripe_event_id  TEXT  — event["id"] Stripe (ex : "evt_1AbCdEf…")
--   p_event_type       TEXT  — event["type"] Stripe (ex : "checkout.session.completed")
--   p_action           TEXT  — action dérivée : "update_plan" | "add_bonus" |
--                              "downgrade_free" | "noop" | "unhandled"
--   p_company_id       TEXT  — UUID de la company Pepperyn (NULL pour noop/unhandled)
--   p_quantity         INT   — analyses à créditer (pour add_bonus uniquement)
--   p_new_plan         TEXT  — nouveau plan (pour update_plan uniquement)
--   p_stripe_customer  TEXT  — stripe_customer_id (optionnel, stocké sur update_plan)
--
-- Retourne JSONB :
--   {"status": "processed"}  — premier traitement : marqueur inséré + métier appliqué
--   {"status": "duplicate"}  — stripe_event_id déjà présent → traitement ignoré

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
    -- ── Étape 1 : insertion atomique dans le registre d'idempotence ────────────
    -- ON CONFLICT DO NOTHING : si stripe_event_id existe déjà, 0 lignes insérées.
    INSERT INTO public.stripe_webhook_events
        (stripe_event_id, event_type, company_id, action)
    VALUES
        (p_stripe_event_id, p_event_type, p_company_id, p_action)
    ON CONFLICT (stripe_event_id) DO NOTHING;

    -- ── Étape 2 : détection doublon ───────────────────────────────────────────
    -- NOT FOUND est vrai si aucune ligne insérée (conflit = événement déjà traité).
    IF NOT FOUND THEN
        RETURN jsonb_build_object('status', 'duplicate');
    END IF;

    -- ── Étape 3 : traitement métier dans la même transaction ──────────────────

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
        -- Si la ligne du mois n'existe pas encore, elle est créée avec p_quantity.
        -- Si elle existe, bonus_analyses est incrémenté de p_quantity de façon atomique.
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
