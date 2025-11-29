-- Migration: Refactor job_bookmarks and create resumes table
-- Changes:
-- 1. Add job columns to job_bookmarks table
-- 2. Remove job_id foreign key from job_bookmarks
-- 3. Create resumes table
-- 4. Update job_analyses to reference job_bookmarks.bookmark_id
-- 5. Update job_matches to reference job_bookmarks.bookmark_id and resumes.id
-- 6. Drop jobs table

-- Step 1: Add job columns to job_bookmarks
ALTER TABLE job_bookmarks
    ADD COLUMN IF NOT EXISTS title VARCHAR(500),
    ADD COLUMN IF NOT EXISTS company VARCHAR(255),
    ADD COLUMN IF NOT EXISTS location VARCHAR(255),
    ADD COLUMN IF NOT EXISTS source job_source_enum,
    ADD COLUMN IF NOT EXISTS source_url VARCHAR(1000),
    ADD COLUMN IF NOT EXISTS description VARCHAR(5000);

-- Step 2: Remove job_id foreign key constraint from job_bookmarks
-- First, drop the unique constraint that includes job_id
ALTER TABLE job_bookmarks
    DROP CONSTRAINT IF EXISTS job_bookmarks_user_id_job_id_key;

-- Then drop the foreign key constraint
ALTER TABLE job_bookmarks
    DROP CONSTRAINT IF EXISTS job_bookmarks_job_id_fkey;

-- Drop the job_id column
ALTER TABLE job_bookmarks
    DROP COLUMN IF EXISTS job_id;

-- Step 3: Create resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    object_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    last_match_job_bookmark_id UUID REFERENCES job_bookmarks(bookmark_id) ON DELETE SET NULL,
    recommended_tips TEXT
);

-- Create indexes for resumes table
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_last_match_job_bookmark_id ON resumes(last_match_job_bookmark_id);

-- Step 4: Update job_analyses table
-- Drop existing foreign key constraint
ALTER TABLE job_analyses
    DROP CONSTRAINT IF EXISTS job_analyses_job_id_fkey;

-- Rename job_id to job_bookmark_id
ALTER TABLE job_analyses
    RENAME COLUMN job_id TO job_bookmark_id;

-- Add new foreign key constraint to job_bookmarks
ALTER TABLE job_analyses
    ADD CONSTRAINT job_analyses_job_bookmark_id_fkey 
    FOREIGN KEY (job_bookmark_id) REFERENCES job_bookmarks(bookmark_id) ON DELETE CASCADE;

-- Step 5: Update job_matches table
-- Drop existing foreign key constraint for job_id
ALTER TABLE job_matches
    DROP CONSTRAINT IF EXISTS job_matches_job_id_fkey;

-- Rename job_id to job_bookmark_id
ALTER TABLE job_matches
    RENAME COLUMN job_id TO job_bookmark_id;

-- Add foreign key constraint to job_bookmarks
ALTER TABLE job_matches
    ADD CONSTRAINT job_matches_job_bookmark_id_fkey 
    FOREIGN KEY (job_bookmark_id) REFERENCES job_bookmarks(bookmark_id) ON DELETE CASCADE;

-- Add foreign key constraint for resume_id to resumes
ALTER TABLE job_matches
    ADD CONSTRAINT job_matches_resume_id_fkey 
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE;

-- Step 6: Update indexes
-- Drop old indexes
DROP INDEX IF EXISTS idx_job_analyses_job_id;
DROP INDEX IF EXISTS idx_job_matches_job_id;
DROP INDEX IF EXISTS idx_job_bookmarks_job_id;

-- Create new indexes
CREATE INDEX IF NOT EXISTS idx_job_analyses_job_bookmark_id ON job_analyses(job_bookmark_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_job_bookmark_id ON job_matches(job_bookmark_id);
CREATE INDEX IF NOT EXISTS idx_job_bookmarks_title ON job_bookmarks(title);

-- Step 7: Drop jobs table (safe since no data exists)
DROP TABLE IF EXISTS jobs CASCADE;

