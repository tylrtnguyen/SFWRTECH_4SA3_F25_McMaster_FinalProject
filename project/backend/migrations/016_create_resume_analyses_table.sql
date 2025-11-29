-- Migration 016: Create resume_analyses table
-- This table stores individual resume analysis results separately from resumes
-- Allows tracking analysis history and multiple analyses per resume

CREATE TABLE IF NOT EXISTS resume_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    match_score FLOAT, -- Only set if there was a targeted job
    targeted_job_bookmark_id UUID REFERENCES job_bookmarks(bookmark_id) ON DELETE SET NULL,
    recommended_tips TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_analyses_resume_id ON resume_analyses(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_created_at ON resume_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_targeted_job ON resume_analyses(targeted_job_bookmark_id);

-- Migrate existing data from resumes table
INSERT INTO resume_analyses (resume_id, match_score, targeted_job_bookmark_id, recommended_tips, created_at)
SELECT
    id,
    match_score,
    targeted_job_bookmark_id,
    recommended_tips,
    COALESCE(uploaded_at, NOW())
FROM resumes
WHERE recommended_tips IS NOT NULL;

-- Remove the old columns from resumes table
ALTER TABLE resumes DROP COLUMN IF EXISTS match_score;
ALTER TABLE resumes DROP COLUMN IF EXISTS recommended_tips;
ALTER TABLE resumes DROP COLUMN IF EXISTS last_analyzed_at;

-- Add comment for documentation
COMMENT ON TABLE resume_analyses IS 'Stores individual resume analysis results from Gemini AI';
COMMENT ON COLUMN resume_analyses.match_score IS 'Match score between resume and targeted job (0-100), null if no targeted job';
COMMENT ON COLUMN resume_analyses.targeted_job_bookmark_id IS 'Job bookmark used for targeted analysis, null for general analysis';
