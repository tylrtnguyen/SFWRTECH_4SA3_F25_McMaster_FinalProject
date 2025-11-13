-- Migration: Update jobs table
-- Changes:
-- 1. Change source column from VARCHAR to ENUM type
-- 2. Change source_url column from TEXT to VARCHAR
-- 3. Add description column as VARCHAR

-- Create enum type for job source (if it doesn't exist)
DO $$ BEGIN
    CREATE TYPE job_source_enum AS ENUM ('linkedin', 'indeed', 'other', 'manual');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Alter source column to use enum type
-- Convert existing VARCHAR values to enum (will fail if invalid values exist)
ALTER TABLE jobs 
    ALTER COLUMN source TYPE job_source_enum USING source::job_source_enum;

-- Change source_url from TEXT to VARCHAR(1000)
ALTER TABLE jobs 
    ALTER COLUMN source_url TYPE VARCHAR(1000);

-- Add description column
ALTER TABLE jobs 
    ADD COLUMN IF NOT EXISTS description VARCHAR(5000);

