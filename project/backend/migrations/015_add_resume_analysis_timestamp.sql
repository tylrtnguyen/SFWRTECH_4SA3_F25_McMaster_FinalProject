-- Migration 015: Add last_analyzed_at field to resumes table
-- This field tracks when resume analysis was last performed
-- for displaying "last analyzed" timestamps in the UI

ALTER TABLE resumes
ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Add comment for documentation
COMMENT ON COLUMN resumes.last_analyzed_at IS 'Timestamp when resume was last analyzed for tips';

