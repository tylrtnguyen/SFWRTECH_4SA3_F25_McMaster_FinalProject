-- Migration: Create all database tables
-- Based on PostgreSQL schema from documentation section 8

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    oauth_provider VARCHAR(50) NOT NULL,
    oauth_id VARCHAR(255) NOT NULL,
    credits INTEGER DEFAULT 50 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Table: credit_transactions
CREATE TABLE IF NOT EXISTS credit_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    stripe_payment_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: jobs
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    source VARCHAR(100) NOT NULL,
    source_url TEXT,
    posted_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: job_analyses
CREATE TABLE IF NOT EXISTS job_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    fraud_score DECIMAL(5,2) CHECK (fraud_score >= 0 AND fraud_score <= 100),
    analysis_type VARCHAR(50) NOT NULL,
    credits_used INTEGER DEFAULT 2,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: job_matches
CREATE TABLE IF NOT EXISTS job_matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    resume_id UUID NOT NULL,
    match_score DECIMAL(5,2) CHECK (match_score >= 0 AND match_score <= 100),
    skill_score DECIMAL(5,2),
    experience_score DECIMAL(5,2),
    matching_strategy VARCHAR(50) NOT NULL,
    credits_used INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: job_bookmarks
CREATE TABLE IF NOT EXISTS job_bookmarks (
    bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

-- Table: logs
CREATE TABLE IF NOT EXISTS logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100),
    details JSONB
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_job_analyses_user_id ON job_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_job_analyses_job_id ON job_analyses(job_id);
CREATE INDEX IF NOT EXISTS idx_job_analyses_created_at ON job_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_job_matches_user_id ON job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_job_id ON job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_created_at ON job_matches(created_at);
CREATE INDEX IF NOT EXISTS idx_job_bookmarks_user_id ON job_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_job_bookmarks_job_id ON job_bookmarks(job_id);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

