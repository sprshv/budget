-- ============================================================
-- Budgeting App — PostgreSQL Schema
-- ============================================================
-- Convention: all tables have id (UUID), created_at, updated_at
-- RLS is enabled on all tables — users can only access their own rows
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS
-- Managed by Supabase Auth — this table extends it with
-- app-specific profile data
-- ============================================================

CREATE TABLE users (
    id                  UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email               TEXT NOT NULL UNIQUE,
    full_name           TEXT,
    avatar_url          TEXT,
    currency            TEXT NOT NULL DEFAULT 'USD',
    timezone            TEXT NOT NULL DEFAULT 'America/Los_Angeles',
    financial_health_score INT,              -- 0-100, recalculated weekly
    onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- FINANCIAL ACCOUNTS
-- One row per connected bank/credit/investment account
-- ============================================================

CREATE TABLE financial_accounts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Plaid fields
    plaid_item_id       TEXT,               -- Plaid Item (one per bank login)
    plaid_account_id    TEXT UNIQUE,        -- Plaid's account identifier
    plaid_access_token  TEXT,               -- Encrypted. Never expose to client.
    plaid_cursor        TEXT,               -- For transaction sync pagination

    -- Display
    name                TEXT NOT NULL,      -- User-facing name (editable)
    official_name       TEXT,               -- Name from institution
    nickname            TEXT,               -- User's custom nickname
    institution_name    TEXT,
    institution_logo    TEXT,               -- URL to logo

    -- Type
    account_type        TEXT NOT NULL,      -- checking, savings, credit, loan, investment, mortgage, crypto, manual
    account_subtype     TEXT,               -- e.g. '401k', 'roth', 'auto'
    is_manual           BOOLEAN NOT NULL DEFAULT FALSE,

    -- Balances (updated on each sync)
    balance_current     NUMERIC(12, 2),
    balance_available   NUMERIC(12, 2),
    balance_limit       NUMERIC(12, 2),     -- For credit cards

    -- Status
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at      TIMESTAMPTZ,
    sync_status         TEXT DEFAULT 'ok', -- ok, error, reauth_required

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_financial_accounts_user_id ON financial_accounts(user_id);
CREATE INDEX idx_financial_accounts_plaid_item_id ON financial_accounts(plaid_item_id);

-- ============================================================
-- CATEGORIES
-- System categories + user custom categories
-- ============================================================

CREATE TABLE categories (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL = system category
    name                TEXT NOT NULL,
    icon                TEXT,               -- emoji or icon name
    color               TEXT,               -- hex color for UI
    parent_id           UUID REFERENCES categories(id),  -- for subcategories
    is_income           BOOLEAN NOT NULL DEFAULT FALSE,
    is_system           BOOLEAN NOT NULL DEFAULT FALSE,  -- system categories can't be deleted
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed system categories (run after migration)
INSERT INTO categories (id, name, icon, color, is_system, is_income) VALUES
    (uuid_generate_v4(), 'Food & Dining', '🍔', '#FF6B6B', TRUE, FALSE),
    (uuid_generate_v4(), 'Groceries', '🛒', '#FF8E53', TRUE, FALSE),
    (uuid_generate_v4(), 'Transportation', '🚗', '#4ECDC4', TRUE, FALSE),
    (uuid_generate_v4(), 'Gas', '⛽', '#45B7D1', TRUE, FALSE),
    (uuid_generate_v4(), 'Housing', '🏠', '#96CEB4', TRUE, FALSE),
    (uuid_generate_v4(), 'Rent', '🏢', '#88D8A3', TRUE, FALSE),
    (uuid_generate_v4(), 'Utilities', '💡', '#FFEAA7', TRUE, FALSE),
    (uuid_generate_v4(), 'Entertainment', '🎮', '#DDA0DD', TRUE, FALSE),
    (uuid_generate_v4(), 'Subscriptions', '📱', '#9B89B4', TRUE, FALSE),
    (uuid_generate_v4(), 'Shopping', '🛍️', '#F7DC6F', TRUE, FALSE),
    (uuid_generate_v4(), 'Health & Medical', '🏥', '#82E0AA', TRUE, FALSE),
    (uuid_generate_v4(), 'Fitness', '💪', '#76D7C4', TRUE, FALSE),
    (uuid_generate_v4(), 'Travel', '✈️', '#85C1E9', TRUE, FALSE),
    (uuid_generate_v4(), 'Education', '📚', '#F1948A', TRUE, FALSE),
    (uuid_generate_v4(), 'Personal Care', '💅', '#C39BD3', TRUE, FALSE),
    (uuid_generate_v4(), 'Gifts & Donations', '🎁', '#FAD7A0', TRUE, FALSE),
    (uuid_generate_v4(), 'Business', '💼', '#AED6F1', TRUE, FALSE),
    (uuid_generate_v4(), 'Taxes', '🧾', '#A9CCE3', TRUE, FALSE),
    (uuid_generate_v4(), 'Investments', '📈', '#A9DFBF', TRUE, FALSE),
    (uuid_generate_v4(), 'Savings', '🏦', '#A3E4D7', TRUE, FALSE),
    (uuid_generate_v4(), 'Uncategorized', '❓', '#BDC3C7', TRUE, FALSE),
    -- Income categories
    (uuid_generate_v4(), 'Paycheck', '💵', '#2ECC71', TRUE, TRUE),
    (uuid_generate_v4(), 'Freelance', '💻', '#27AE60', TRUE, TRUE),
    (uuid_generate_v4(), 'Investment Income', '📊', '#1ABC9C', TRUE, TRUE),
    (uuid_generate_v4(), 'Other Income', '💰', '#16A085', TRUE, TRUE);

-- ============================================================
-- CATEGORIZATION RULES
-- User-defined rules for auto-categorizing transactions
-- ============================================================

CREATE TABLE categorization_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id         UUID NOT NULL REFERENCES categories(id),

    -- Rule matching
    match_field         TEXT NOT NULL,      -- 'merchant_name', 'description', 'amount'
    match_operator      TEXT NOT NULL,      -- 'contains', 'equals', 'starts_with', 'greater_than'
    match_value         TEXT NOT NULL,

    priority            INT NOT NULL DEFAULT 0,  -- higher = evaluated first
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_categorization_rules_user_id ON categorization_rules(user_id);

-- ============================================================
-- TRANSACTIONS
-- Core table — one row per financial transaction
-- ============================================================

CREATE TABLE transactions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id          UUID NOT NULL REFERENCES financial_accounts(id) ON DELETE CASCADE,
    category_id         UUID REFERENCES categories(id),

    -- Plaid fields
    plaid_transaction_id TEXT UNIQUE,       -- NULL for manual transactions

    -- Core fields
    amount              NUMERIC(12, 2) NOT NULL,  -- positive = expense, negative = income
    currency            TEXT NOT NULL DEFAULT 'USD',
    date                DATE NOT NULL,
    description         TEXT NOT NULL,      -- raw bank description
    merchant_name       TEXT,               -- cleaned merchant name
    pending             BOOLEAN NOT NULL DEFAULT FALSE,

    -- Enrichment
    category_confidence NUMERIC(3, 2),      -- 0.0-1.0, how confident auto-categorization was
    is_manual           BOOLEAN NOT NULL DEFAULT FALSE,
    is_recurring        BOOLEAN NOT NULL DEFAULT FALSE,
    recurring_id        UUID,               -- FK to recurring_transactions if detected
    is_duplicate        BOOLEAN NOT NULL DEFAULT FALSE,
    is_hidden           BOOLEAN NOT NULL DEFAULT FALSE,

    -- User annotations
    notes               TEXT,
    tags                TEXT[],             -- array of user tags
    receipt_url         TEXT,               -- S3 URL for receipt image

    -- Tax
    is_tax_deductible   BOOLEAN NOT NULL DEFAULT FALSE,
    tax_category        TEXT,               -- e.g. 'business_expense', 'charitable'

    -- Location (from Plaid)
    merchant_city       TEXT,
    merchant_state      TEXT,
    merchant_country    TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(date DESC);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_merchant_name ON transactions(merchant_name);
CREATE INDEX idx_transactions_plaid_id ON transactions(plaid_transaction_id);

-- ============================================================
-- TRANSACTION SPLITS
-- When one transaction is split across multiple categories
-- ============================================================

CREATE TABLE transaction_splits (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id      UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    category_id         UUID NOT NULL REFERENCES categories(id),
    amount              NUMERIC(12, 2) NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- RECURRING TRANSACTIONS
-- Detected subscriptions and bills
-- ============================================================

CREATE TABLE recurring_transactions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id         UUID REFERENCES categories(id),

    merchant_name       TEXT NOT NULL,
    description         TEXT,
    average_amount      NUMERIC(12, 2) NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'USD',

    frequency           TEXT NOT NULL,      -- weekly, biweekly, monthly, quarterly, annual
    last_date           DATE,
    next_expected_date  DATE,

    is_subscription     BOOLEAN NOT NULL DEFAULT FALSE,
    is_bill             BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- Alerts
    remind_days_before  INT DEFAULT 3,
    alert_enabled       BOOLEAN NOT NULL DEFAULT TRUE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recurring_user_id ON recurring_transactions(user_id);

-- ============================================================
-- BUDGETS
-- Monthly spending limits per category
-- ============================================================

CREATE TABLE budgets (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id         UUID NOT NULL REFERENCES categories(id),

    amount              NUMERIC(12, 2) NOT NULL,
    period_month        INT NOT NULL,       -- 1-12
    period_year         INT NOT NULL,

    -- Rollover
    rollover_enabled    BOOLEAN NOT NULL DEFAULT FALSE,
    rollover_amount     NUMERIC(12, 2) DEFAULT 0,  -- carried from previous month

    -- Alerts
    alert_threshold     NUMERIC(3, 2) DEFAULT 0.80,  -- alert at 80% spent
    alert_sent          BOOLEAN NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, category_id, period_month, period_year)
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);
CREATE INDEX idx_budgets_period ON budgets(period_year, period_month);

-- ============================================================
-- GOALS
-- Savings and debt payoff goals
-- ============================================================

CREATE TABLE goals (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    linked_account_id   UUID REFERENCES financial_accounts(id),

    name                TEXT NOT NULL,
    goal_type           TEXT NOT NULL,      -- savings, debt_payoff, emergency_fund, custom
    target_amount       NUMERIC(12, 2) NOT NULL,
    current_amount      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    target_date         DATE,

    -- Auto savings rules
    auto_contribute     BOOLEAN NOT NULL DEFAULT FALSE,
    auto_amount         NUMERIC(12, 2),
    auto_frequency      TEXT,               -- weekly, biweekly, monthly

    is_complete         BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at        TIMESTAMPTZ,
    icon                TEXT,
    color               TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_goals_user_id ON goals(user_id);

-- ============================================================
-- GOAL CONTRIBUTIONS
-- Log of money added toward each goal
-- ============================================================

CREATE TABLE goal_contributions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id             UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount              NUMERIC(12, 2) NOT NULL,
    note                TEXT,
    contributed_at      DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ASSETS (manual, non-bank)
-- Real estate, vehicles, other physical assets
-- ============================================================

CREATE TABLE assets (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    name                TEXT NOT NULL,
    asset_type          TEXT NOT NULL,      -- real_estate, vehicle, crypto, other
    value               NUMERIC(12, 2) NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'USD',

    -- Optional enrichment
    address             TEXT,               -- for real estate
    vehicle_make        TEXT,
    vehicle_model       TEXT,
    vehicle_year        INT,

    notes               TEXT,
    last_updated_at     DATE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- LIABILITIES (manual, non-bank)
-- Debts not connected to bank accounts
-- ============================================================

CREATE TABLE liabilities (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    name                TEXT NOT NULL,
    liability_type      TEXT NOT NULL,      -- personal_loan, family_loan, other
    balance             NUMERIC(12, 2) NOT NULL,
    interest_rate       NUMERIC(5, 2),
    minimum_payment     NUMERIC(12, 2),
    due_date            INT,                -- day of month payment is due
    currency            TEXT NOT NULL DEFAULT 'USD',
    notes               TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- NOTIFICATIONS
-- Stores all generated alerts for the user
-- ============================================================

CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    type                TEXT NOT NULL,      -- budget_alert, bill_reminder, low_balance, large_purchase, etc.
    title               TEXT NOT NULL,
    body                TEXT NOT NULL,
    metadata            JSONB,              -- flexible payload (e.g. { category_id, amount })

    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    sent_push           BOOLEAN NOT NULL DEFAULT FALSE,
    sent_email          BOOLEAN NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_is_read ON notifications(user_id, is_read);

-- ============================================================
-- NOTIFICATION PREFERENCES
-- Per-user, per-type notification settings
-- ============================================================

CREATE TABLE notification_preferences (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    notification_type   TEXT NOT NULL,
    push_enabled        BOOLEAN NOT NULL DEFAULT TRUE,
    email_enabled       BOOLEAN NOT NULL DEFAULT FALSE,
    threshold_amount    NUMERIC(12, 2),     -- for large_purchase, low_balance alerts

    UNIQUE (user_id, notification_type),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- AUDIT LOG
-- Immutable log of sensitive actions
-- ============================================================

CREATE TABLE audit_log (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id),
    action              TEXT NOT NULL,      -- e.g. 'plaid.link', 'account.delete', 'export.csv'
    resource_type       TEXT,
    resource_id         UUID,
    ip_address          INET,
    user_agent          TEXT,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- ============================================================
-- ROW LEVEL SECURITY
-- Enable on all user-data tables
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_splits ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE liabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorization_rules ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only see their own data)
CREATE POLICY "users_own_data" ON users FOR ALL USING (auth.uid() = id);
CREATE POLICY "accounts_own_data" ON financial_accounts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "transactions_own_data" ON transactions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "budgets_own_data" ON budgets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "goals_own_data" ON goals FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "goal_contributions_own_data" ON goal_contributions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "assets_own_data" ON assets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "liabilities_own_data" ON liabilities FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "notifications_own_data" ON notifications FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "notification_prefs_own_data" ON notification_preferences FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "categorization_rules_own_data" ON categorization_rules FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "recurring_own_data" ON recurring_transactions FOR ALL USING (auth.uid() = user_id);

-- ============================================================
-- UPDATED_AT TRIGGER
-- Auto-update updated_at on every row change
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON financial_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_budgets_updated_at BEFORE UPDATE ON budgets FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_goals_updated_at BEFORE UPDATE ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_assets_updated_at BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_liabilities_updated_at BEFORE UPDATE ON liabilities FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_recurring_updated_at BEFORE UPDATE ON recurring_transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_notif_prefs_updated_at BEFORE UPDATE ON notification_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at();