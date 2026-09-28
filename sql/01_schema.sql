-- ============================================================
-- OTT Subscriber & Content Engagement Dashboard
-- Schema definition (PostgreSQL / compatible with most engines)
-- ============================================================

-- Users dimension
CREATE TABLE users (
    user_id            VARCHAR(10) PRIMARY KEY,
    signup_date        DATE NOT NULL,
    country            VARCHAR(5),
    age_group          VARCHAR(10),
    preferred_device   VARCHAR(20),
    acquisition_channel VARCHAR(20)
);

-- Content dimension
CREATE TABLE content (
    content_id         VARCHAR(10) PRIMARY KEY,
    title              VARCHAR(100),
    genre              VARCHAR(30),
    content_type       VARCHAR(20),
    duration_minutes   INT,
    release_date       DATE,
    is_original        BOOLEAN
);

-- Subscriptions fact (lifecycle)
CREATE TABLE subscriptions (
    subscription_id    VARCHAR(12) PRIMARY KEY,
    user_id            VARCHAR(10) REFERENCES users(user_id),
    plan_type          VARCHAR(20),
    plan_price         DECIMAL(6,2),
    start_date         DATE NOT NULL,
    end_date           DATE,                 -- NULL = still active
    status             VARCHAR(10),          -- Active / Churned
    billing_cycle      VARCHAR(10)
);

-- Viewing sessions fact (100K+ rows)
CREATE TABLE viewing_sessions (
    session_id         VARCHAR(12) PRIMARY KEY,
    user_id            VARCHAR(10) REFERENCES users(user_id),
    content_id         VARCHAR(10) REFERENCES content(content_id),
    session_start      TIMESTAMP NOT NULL,
    watch_minutes      INT,
    device             VARCHAR(20),
    completion_pct     DECIMAL(5,1),
    session_date       DATE                  -- denormalized for convenience
);

-- Pre-aggregated daily metrics (optional, speeds Power BI)
CREATE TABLE daily_active_users (
    date               DATE PRIMARY KEY,
    dau                INT,
    total_sessions     INT,
    total_watch_minutes BIGINT,
    avg_watch_per_session DECIMAL(8,1)
);

-- Helpful indexes for KPI queries
CREATE INDEX idx_subs_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_subs_start ON subscriptions(start_date);
CREATE INDEX idx_sessions_user_date ON viewing_sessions(user_id, session_date);
CREATE INDEX idx_sessions_date ON viewing_sessions(session_date);
CREATE INDEX idx_sessions_content ON viewing_sessions(content_id);
