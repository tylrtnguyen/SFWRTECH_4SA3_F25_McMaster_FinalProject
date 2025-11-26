-- Migration: Update job_analyses table for Gemini API integration
-- Changes:
-- 1. Rename fraud_score column to confidence_score
-- 2. Add is_authentic BOOLEAN column
-- 3. Add evidence TEXT column for Gemini's evidence/reasoning

-- Step 1: Rename fraud_score to confidence_score
ALTER TABLE job_analyses
    RENAME COLUMN fraud_score TO confidence_score;

-- Step 2: Add is_authentic column
ALTER TABLE job_analyses
    ADD COLUMN IF NOT EXISTS is_authentic BOOLEAN;

-- Step 3: Add evidence column
ALTER TABLE job_analyses
    ADD COLUMN IF NOT EXISTS evidence TEXT;

-- Step 4: Update check constraint name if it exists (PostgreSQL doesn't auto-rename constraints)
-- Drop old constraint if it exists
ALTER TABLE job_analyses
    DROP CONSTRAINT IF EXISTS job_analyses_fraud_score_check;

-- Add new constraint for confidence_score
ALTER TABLE job_analyses
    ADD CONSTRAINT job_analyses_confidence_score_check 
    CHECK (confidence_score >= 0 AND confidence_score <= 100);

-- Note: The column job_id was already renamed to job_bookmark_id in migration 003
-- This migration assumes migration 003 has been applied


