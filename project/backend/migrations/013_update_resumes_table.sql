-- Migration: Update resumes table with new columns for Resume Tips feature
-- Changes:
-- 1. Create experience_level_enum type
-- 2. Add resume_name column
-- 3. Add experience column
-- 4. Add targeted_job_bookmark_id column (replaces last_match_job_bookmark_id)
-- 5. Add match_score column

-- Step 1: Create experience level enum type
DO $$ BEGIN
    CREATE TYPE experience_level_enum AS ENUM ('junior', 'mid_senior', 'director', 'executive');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 2: Add resume_name column
ALTER TABLE resumes
    ADD COLUMN IF NOT EXISTS resume_name VARCHAR(255);

-- Step 3: Add experience column
ALTER TABLE resumes
    ADD COLUMN IF NOT EXISTS experience experience_level_enum DEFAULT 'junior';

-- Step 4: Add targeted_job_bookmark_id column
ALTER TABLE resumes
    ADD COLUMN IF NOT EXISTS targeted_job_bookmark_id UUID REFERENCES job_bookmarks(bookmark_id) ON DELETE SET NULL;

-- Step 5: Add match_score column
ALTER TABLE resumes
    ADD COLUMN IF NOT EXISTS match_score FLOAT;

-- Step 6: Update existing records to have resume_name from filename if null
UPDATE resumes 
SET resume_name = filename 
WHERE resume_name IS NULL;

-- Step 7: Migrate data from last_match_job_bookmark_id to targeted_job_bookmark_id
UPDATE resumes 
SET targeted_job_bookmark_id = last_match_job_bookmark_id 
WHERE targeted_job_bookmark_id IS NULL AND last_match_job_bookmark_id IS NOT NULL;

-- Step 8: Create index for targeted_job_bookmark_id
CREATE INDEX IF NOT EXISTS idx_resumes_targeted_job_bookmark_id ON resumes(targeted_job_bookmark_id);

-- Step 9: Add comment for documentation
COMMENT ON COLUMN resumes.resume_name IS 'User-friendly name for the resume';
COMMENT ON COLUMN resumes.experience IS 'Experience level: junior, mid_senior, director, executive';
COMMENT ON COLUMN resumes.targeted_job_bookmark_id IS 'Target job bookmark for resume optimization';
COMMENT ON COLUMN resumes.match_score IS 'Match score between resume and targeted job (0-100)';

