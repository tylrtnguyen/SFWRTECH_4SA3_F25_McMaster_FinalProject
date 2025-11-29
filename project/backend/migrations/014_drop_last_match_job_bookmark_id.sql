-- Migration: Drop deprecated last_match_job_bookmark_id column from resumes table
-- Changes:
-- 1. Drop index on last_match_job_bookmark_id
-- 2. Drop last_match_job_bookmark_id column
-- Note: Data was already migrated to targeted_job_bookmark_id in migration 013

-- Step 1: Drop the index on last_match_job_bookmark_id
DROP INDEX IF EXISTS idx_resumes_last_match_job_bookmark_id;

-- Step 2: Drop the last_match_job_bookmark_id column
ALTER TABLE resumes
    DROP COLUMN IF EXISTS last_match_job_bookmark_id;


