-- Migration 010: Create job_industry table and add foreign key to job_bookmarks
--
-- This migration:
-- 1. Creates job_industry table with id and description columns
-- 2. Migrates all industries from frontend localStorage to the table
-- 3. Adds nullable foreign key job_industry_id to job_bookmarks table

-- Step 1: Create job_industry table
CREATE TABLE IF NOT EXISTS job_industry (
    id SERIAL PRIMARY KEY,
    description VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Insert default industries from frontend localStorage
INSERT INTO job_industry (description) VALUES
    ('Technology'),
    ('Healthcare'),
    ('Finance'),
    ('Education'),
    ('Manufacturing'),
    ('Retail'),
    ('Hospitality'),
    ('Construction'),
    ('Transportation'),
    ('Energy'),
    ('Media & Entertainment'),
    ('Real Estate'),
    ('Consulting'),
    ('Government'),
    ('Non-profit')
ON CONFLICT (description) DO NOTHING;

-- Step 3: Add nullable foreign key to job_bookmarks table
-- First check if the column doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'job_bookmarks' AND column_name = 'job_industry_id'
    ) THEN
        ALTER TABLE job_bookmarks ADD COLUMN job_industry_id INTEGER REFERENCES job_industry(id);
    END IF;
END $$;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_job_bookmarks_industry_id ON job_bookmarks(job_industry_id);

-- Add comment
COMMENT ON COLUMN job_bookmarks.job_industry_id IS 'References job_industry.id for structured industry data';

