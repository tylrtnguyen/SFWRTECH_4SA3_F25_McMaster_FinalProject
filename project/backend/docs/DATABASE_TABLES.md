# Database Tables Structure

## credit_transactions

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| transaction_id | UUID | PRIMARY KEY | Unique transaction identifier |
| user_id | UUID | NOT NULL, FOREIGN KEY REFERENCES users(user_id) ON DELETE CASCADE | User who made the transaction |
| transaction_type | VARCHAR(50) | NOT NULL | Type of transaction (e.g., 'purchase', 'deduction') |
| amount | INTEGER | NOT NULL | Credit amount (positive for purchases, negative for deductions) |
| stripe_payment_id | VARCHAR(255) | NULL | Stripe payment intent/session ID |
| status | transaction_status | DEFAULT 'pending' | Transaction status: pending, success, failed, cancelled |
| created_at | TIMESTAMP | DEFAULT NOW() | Transaction creation timestamp |

---

## users

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| user_id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| oauth_provider | VARCHAR(50) | NOT NULL | OAuth provider name (e.g., 'supabase') |
| oauth_id | VARCHAR(255) | NOT NULL | OAuth provider user ID |
| credits | INTEGER | DEFAULT 50, NOT NULL | Available credits for user |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| first_name | VARCHAR(255) | NULL | User's first name |
| last_name | VARCHAR(255) | NULL | User's last name |

---

## job_bookmarks

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| bookmark_id | UUID | PRIMARY KEY | Unique bookmark identifier |
| user_id | UUID | NOT NULL, FOREIGN KEY REFERENCES users(user_id) ON DELETE CASCADE | User who bookmarked the job |
| title | VARCHAR(500) | NULL | Job title |
| company | VARCHAR(255) | NULL | Company name |
| location | VARCHAR(255) | NULL | Job location |
| source | job_source_enum | NULL | Job source: linkedin, indeed, other, manual, document_upload |
| source_url | VARCHAR(1000) | NULL | URL of the job posting |
| description | VARCHAR(5000) | NULL | Job description |
| application_status | application_status_enum | DEFAULT 'interested' | Application status: interested, applied, interviewing, interviewed_passed, interviewed_failed |
| job_industry_id | INTEGER | NULL, FOREIGN KEY REFERENCES job_industry(id) | Industry category reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Bookmark creation timestamp |

---

## job_analyses

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| analysis_id | UUID | PRIMARY KEY | Unique analysis identifier |
| user_id | UUID | NOT NULL, FOREIGN KEY REFERENCES users(user_id) ON DELETE CASCADE | User who requested the analysis |
| job_bookmark_id | UUID | NULL, FOREIGN KEY REFERENCES job_bookmarks(bookmark_id) ON DELETE CASCADE | Job bookmark being analyzed |
| confidence_score | DECIMAL(5,2) | CHECK (confidence_score >= 0 AND confidence_score <= 100) | AI confidence score (0-100) |
| is_authentic | BOOLEAN | NULL | Whether the job is authentic (true) or fraudulent (false) |
| evidence | TEXT | NULL | Evidence/reasoning from AI analysis |
| analysis_type | VARCHAR(50) | NOT NULL | Type of analysis performed |
| credits_used | INTEGER | DEFAULT 2 | Credits consumed for this analysis |
| created_at | TIMESTAMP | DEFAULT NOW() | Analysis creation timestamp |

---

## job_documents

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing document ID |
| user_id | UUID | NOT NULL, FOREIGN KEY REFERENCES users(user_id) | User who uploaded the document |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| file_size | INTEGER | NOT NULL, CHECK (file_size > 0 AND file_size <= 20971520) | File size in bytes (max 20MB) |
| mime_type | VARCHAR(100) | NOT NULL, CHECK (mime_type IN ('application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain')) | MIME type of the file |
| object_id | VARCHAR(500) | NOT NULL | GCP Cloud Storage path |
| extracted_text | TEXT | NULL | Text content extracted from the document |
| processing_status | VARCHAR(50) | DEFAULT 'pending', CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')) | Processing status |
| analysis_result | JSONB | NULL | JSON results from Gemini AI analysis |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Document upload timestamp |
| processed_at | TIMESTAMP WITH TIME ZONE | NULL | Processing completion timestamp |

---

## job_industry

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing industry ID |
| description | VARCHAR(255) | UNIQUE, NOT NULL | Industry name/description |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Industry creation timestamp |

---

## resumes

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique resume identifier |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| size | INTEGER | NOT NULL | File size in bytes |
| uploaded_at | TIMESTAMP | DEFAULT NOW() | Resume upload timestamp |
| object_id | VARCHAR(255) | NOT NULL | GCP Cloud Storage object identifier |
| user_id | UUID | NOT NULL, FOREIGN KEY REFERENCES users(user_id) ON DELETE CASCADE | User who uploaded the resume |
| resume_name | VARCHAR(255) | NULL | User-friendly name for the resume |
| experience | experience_level_enum | DEFAULT 'junior' | Experience level: junior, mid_senior, director, executive |
| targeted_job_bookmark_id | UUID | NULL, FOREIGN KEY REFERENCES job_bookmarks(bookmark_id) ON DELETE SET NULL | Target job bookmark for resume optimization |

---

## resume_analyses

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique analysis identifier |
| resume_id | UUID | NOT NULL, FOREIGN KEY REFERENCES resumes(id) ON DELETE CASCADE | Resume being analyzed |
| match_score | FLOAT | NULL | Match score between resume and targeted job (0-100), null if no targeted job |
| targeted_job_bookmark_id | UUID | NULL, FOREIGN KEY REFERENCES job_bookmarks(bookmark_id) ON DELETE SET NULL | Job bookmark used for targeted analysis, null for general analysis |
| recommended_tips | TEXT | NOT NULL | AI-generated recommendations in markdown format |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Analysis creation timestamp |

---

## logs

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| log_id | BIGSERIAL | PRIMARY KEY | Auto-incrementing log ID |
| timestamp | TIMESTAMP | DEFAULT NOW(), NOT NULL | Log entry timestamp |
| level | VARCHAR(20) | NOT NULL | Log level (DEBUG, INFO, WARNING, ERROR) |
| message | TEXT | NOT NULL | Log message |
| user_id | UUID | NULL, FOREIGN KEY REFERENCES users(user_id) ON DELETE SET NULL | User associated with the log entry |
| action | VARCHAR(100) | NULL | Action that triggered the log |
| details | JSONB | NULL | Additional structured log data |

---

## Enum Types

### transaction_status
- pending
- success
- failed
- cancelled

### job_source_enum
- linkedin
- indeed
- other
- manual
- document_upload

### application_status_enum
- interested
- applied
- interviewing
- interviewed_passed
- interviewed_failed

### experience_level_enum
- junior
- mid_senior
- director
- executive

