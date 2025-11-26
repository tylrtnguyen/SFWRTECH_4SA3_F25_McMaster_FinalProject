-- Migration 008: Job Bookmark Deduplication and Application Status
-- 
-- This migration:
-- 1. Creates application_status enum type
-- 2. Adds application_status column with default 'interested'
-- 3. Updates all existing records to have 'interested' status
-- 4. Adds unique index on (user_id, source_url) for URL-based bookmarks
-- 5. Adds unique index on (user_id, title, company) for manual/upload bookmarks

-- Step 1: Create the application_status enum type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'application_status_enum') THEN
        CREATE TYPE application_status_enum AS ENUM (
            'interested',
            'applied',
            'interviewing',
            'interviewed_passed',
            'interviewed_failed'
        );
    END IF;
END $$;

-- Step 2: Add application_status column with default value
ALTER TABLE job_bookmarks 
ADD COLUMN IF NOT EXISTS application_status application_status_enum DEFAULT 'interested';

-- Step 3: Update all existing records to have 'interested' status
UPDATE job_bookmarks 
SET application_status = 'interested' 
WHERE application_status IS NULL;

-- Step 4: Add unique index for source_url (per user) - only when source_url is not null
-- This prevents duplicate bookmarks for the same job URL per user
DROP INDEX IF EXISTS idx_job_bookmarks_user_source_url;
CREATE UNIQUE INDEX idx_job_bookmarks_user_source_url 
ON job_bookmarks (user_id, source_url) 
WHERE source_url IS NOT NULL;

-- Step 5: Add unique index for title+company (per user) - only when source_url is null
-- This prevents duplicate manual entries with same title and company
DROP INDEX IF EXISTS idx_job_bookmarks_user_title_company;
CREATE UNIQUE INDEX idx_job_bookmarks_user_title_company 
ON job_bookmarks (user_id, title, company) 
WHERE source_url IS NULL;

-- Add comment to document the constraints
COMMENT ON INDEX idx_job_bookmarks_user_source_url IS 'Prevents duplicate bookmarks for the same job URL per user';
COMMENT ON INDEX idx_job_bookmarks_user_title_company IS 'Prevents duplicate manual entries (no URL) with same title and company per user';

