-- Migration v2 — Usage limits + activity tracking + feedback
-- Run once in Supabase SQL editor.
-- Safe to re-run (uses IF NOT EXISTS / DO $$ blocks).


-- ─── 1. usage_limits ────────────────────────────────────────────────────────
-- Tracks analysis and chat usage per company per month.
-- Monthly reset is automatic: new month = new row (inserted on first access).

CREATE TABLE IF NOT EXISTS usage_limits (
  company_id    UUID    NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  year_month    TEXT    NOT NULL,   -- format: "2026-04"
  analyses_count INT   NOT NULL DEFAULT 0,
  chat_count    INT    NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, year_month)
);

-- Index for fast monthly lookups
CREATE INDEX IF NOT EXISTS idx_usage_limits_company_month
  ON usage_limits (company_id, year_month);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_usage_limits_updated_at ON usage_limits;
CREATE TRIGGER trg_usage_limits_updated_at
  BEFORE UPDATE ON usage_limits
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: companies can only see their own usage
ALTER TABLE usage_limits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS usage_limits_company_isolation ON usage_limits;
CREATE POLICY usage_limits_company_isolation ON usage_limits
  USING (company_id = auth.uid());


-- ─── 2. user_activity ───────────────────────────────────────────────────────
-- Append-only event log. Never updated, never deleted.
-- Events: file_uploaded | analysis_started | chat_message | export_generated

CREATE TABLE IF NOT EXISTS user_activity (
  id          UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  event_type  TEXT        NOT NULL,
  metadata    JSONB       NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_activity_company
  ON user_activity (company_id, created_at DESC);

ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_activity_company_isolation ON user_activity;
CREATE POLICY user_activity_company_isolation ON user_activity
  USING (company_id = auth.uid());


-- ─── 3. chat_count on analyses ──────────────────────────────────────────────
-- Tracks per-analysis chat usage for FREE plan (5 msg/analysis) and
-- PRO soft cap (200 msg/analysis → downgrade to Sonnet).

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'analyses' AND column_name = 'chat_count'
  ) THEN
    ALTER TABLE analyses ADD COLUMN chat_count INT NOT NULL DEFAULT 0;
  END IF;
END $$;


-- ─── 4. feedback ────────────────────────────────────────────────────────────
-- User feedback after each analysis.

CREATE TABLE IF NOT EXISTS feedback (
  id                  UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  company_id          UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  analyse_id          UUID        REFERENCES analyses(id) ON DELETE SET NULL,
  learned_something   BOOLEAN,
  would_act           BOOLEAN,
  trust_score         SMALLINT    CHECK (trust_score BETWEEN 1 AND 5),
  frustration         TEXT,
  willingness_to_pay  SMALLINT    CHECK (willingness_to_pay >= 0),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_company
  ON feedback (company_id, created_at DESC);

ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS feedback_company_isolation ON feedback;
CREATE POLICY feedback_company_isolation ON feedback
  USING (company_id = auth.uid());


-- ─── 5. Plan enum update (if using Postgres enum) ───────────────────────────
-- Only needed if the companies.plan column uses a Postgres enum type.
-- If it's a TEXT column with CHECK constraint, run the appropriate block.

-- Check if plan_type enum exists and add new values
DO $$
BEGIN
  -- Add 'pro' to enum if it exists and doesn't already have it
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plan_type') THEN
    BEGIN
      ALTER TYPE plan_type ADD VALUE IF NOT EXISTS 'pro';
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
      ALTER TYPE plan_type ADD VALUE IF NOT EXISTS 'enterprise';
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
  END IF;
END $$;
