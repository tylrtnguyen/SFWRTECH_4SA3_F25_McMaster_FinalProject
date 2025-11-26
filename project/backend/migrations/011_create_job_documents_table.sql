-- Migration 011: Create job_documents table for uploaded job documents
--
-- This migration:
-- 1. Creates job_documents table to store uploaded job files
-- 2. Adds necessary indexes for performance
-- 3. Includes fields for processing status and analysis results

-- Step 1: Create job_documents table
CREATE TABLE IF NOT EXISTS job_documents (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    object_id VARCHAR(500) NOT NULL, -- GCP Cloud Storage path
    extracted_text TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    analysis_result JSONB, -- Store Gemini analysis results
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Step 2: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_documents_user_id ON job_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_job_documents_status ON job_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_job_documents_created_at ON job_documents(created_at);

-- Step 3: Add constraints
ALTER TABLE job_documents ADD CONSTRAINT check_file_size
    CHECK (file_size > 0 AND file_size <= 20971520); -- Max 20MB

ALTER TABLE job_documents ADD CONSTRAINT check_mime_type
    CHECK (mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain'
    ));

ALTER TABLE job_documents ADD CONSTRAINT check_processing_status
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));

-- Step 4: Add comments
COMMENT ON TABLE job_documents IS 'Stores uploaded job documents for analysis';
COMMENT ON COLUMN job_documents.object_id IS 'Path to file in GCP Cloud Storage';
COMMENT ON COLUMN job_documents.extracted_text IS 'Text content extracted from the document';
COMMENT ON COLUMN job_documents.analysis_result IS 'JSON results from Gemini AI analysis';

