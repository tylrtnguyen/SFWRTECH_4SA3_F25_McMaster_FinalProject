-- Migration 020: Drop job_matches table
-- This table is no longer needed as job matching is handled differently

-- Drop the job_matches table
DROP TABLE IF EXISTS job_matches;

-- Add comment to migration history
COMMENT ON SCHEMA public IS 'Migration 020: Dropped job_matches table - job matching now handled via resume_analyses';
