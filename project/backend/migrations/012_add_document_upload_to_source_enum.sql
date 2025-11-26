-- Migration 012: Add 'document_upload' to job_source_enum
--
-- This migration adds 'document_upload' as a valid value to the job_source_enum
-- to support the new document upload feature.

-- Add 'document_upload' to the enum
ALTER TYPE job_source_enum ADD VALUE 'document_upload';

-- Add comment to document the change
COMMENT ON TYPE job_source_enum IS 'Enum for job sources: linkedin, indeed, other, manual, document_upload';
