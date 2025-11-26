-- Migration 009: Fix job_analyses job_bookmark_id to allow NULL
--
-- The job_analyses table currently requires job_bookmark_id to be NOT NULL,
-- but we want to store analysis results even for jobs that aren't bookmarked
-- (when is_authentic = false). This migration makes job_bookmark_id nullable.

ALTER TABLE job_analyses
ALTER COLUMN job_bookmark_id DROP NOT NULL;

