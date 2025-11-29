-- Migration 017: Rename uploaded_date to uploaded_at and update to TIMESTAMP WITH TIME ZONE
-- Makes it consistent with resume_analyses.created_at column

-- Rename the column and update its type
ALTER TABLE resumes
    RENAME COLUMN uploaded_date TO uploaded_at;

-- Update the column type to include time zone information
ALTER TABLE resumes
    ALTER COLUMN uploaded_at SET DATA TYPE TIMESTAMP WITH TIME ZONE;

-- Update the comment to reflect the change
COMMENT ON COLUMN resumes.uploaded_at IS 'Timestamp when the resume was uploaded (with timezone)';
