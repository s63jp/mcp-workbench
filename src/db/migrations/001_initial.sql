-- MCP Workbench Initial Database Schema
-- Migration: 001_initial
-- Description: Create all tables for user management, subscriptions, usage tracking, API keys, and beta signups
-- Created: 2026-08-03

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Stores user accounts with authentication credentials
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    last_login DATETIME
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_created_at ON users(created_at);

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================
-- Tracks Stripe subscription status and billing periods
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    current_period_start DATETIME,
    current_period_end DATETIME,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for subscriptions
CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_tier ON subscriptions(tier);
CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_period ON subscriptions(current_period_start, current_period_end);

-- ============================================================================
-- USAGE TABLE
-- ============================================================================
-- Tracks user resource consumption per billing period
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_count INTEGER NOT NULL DEFAULT 0,
    tool_calls INTEGER NOT NULL DEFAULT 0,
    storage_mb REAL NOT NULL DEFAULT 0.0,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for usage
CREATE INDEX IF NOT EXISTS ix_usage_user_id ON usage(user_id);
CREATE INDEX IF NOT EXISTS ix_usage_user_period ON usage(user_id, period_start, period_end);
CREATE INDEX IF NOT EXISTS ix_usage_period ON usage(period_start, period_end);

-- ============================================================================
-- API_KEYS TABLE
-- ============================================================================
-- Stores hashed API keys for programmatic access
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    last_used DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for api_keys
CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_user_active ON api_keys(user_id, is_active);

-- ============================================================================
-- BETA_SIGNUPS TABLE
-- ============================================================================
-- Stores beta signup data for migration from JSON files
CREATE TABLE IF NOT EXISTS beta_signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL,
    servers TEXT,
    tools TEXT,
    feature TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    signup_date DATETIME NOT NULL,
    migrated BOOLEAN NOT NULL DEFAULT 0,
    migrated_user_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (migrated_user_id) REFERENCES users(id)
);

-- Indexes for beta_signups
CREATE INDEX IF NOT EXISTS ix_beta_signups_email ON beta_signups(email);
CREATE INDEX IF NOT EXISTS ix_beta_signups_migrated ON beta_signups(migrated);
CREATE INDEX IF NOT EXISTS ix_beta_signups_signup_date ON beta_signups(signup_date);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp for subscriptions
CREATE TRIGGER IF NOT EXISTS update_subscriptions_updated_at
AFTER UPDATE ON subscriptions
BEGIN
    UPDATE subscriptions SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Auto-update updated_at timestamp for usage
CREATE TRIGGER IF NOT EXISTS update_usage_updated_at
AFTER UPDATE ON usage
BEGIN
    UPDATE usage SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- SEED DATA
-- ============================================================================
-- Seed data is now handled by init_db.py Python script
-- This allows for proper password hashing and relationship management

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables created
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Verify seed data
-- SELECT u.email, s.tier, s.status FROM users u LEFT JOIN subscriptions s ON u.id = s.user_id;
