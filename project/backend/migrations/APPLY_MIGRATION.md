# How to Apply Database Migration to Supabase

This guide explains how to create the database tables in your Supabase project.

## Method 1: Using Supabase Dashboard (Recommended)

1. **Log in to Supabase**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - In the left sidebar, click on "SQL Editor"
   - Click "New query"

3. **Run the Migration**
   - Open the file `migrations/001_create_tables.sql` in this directory
   - Copy the entire contents of the file
   - Paste it into the SQL Editor in Supabase
   - Click "Run" or press `Ctrl+Enter` (Windows/Linux) or `Cmd+Enter` (Mac)

4. **Verify Tables Created**
   - Go to "Table Editor" in the left sidebar
   - You should see the following tables:
     - users
     - credit_transactions
     - jobs
     - job_analyses
     - job_matches
     - job_bookmarks
     - logs

## Method 2: Using Supabase CLI

1. **Install Supabase CLI**
   ```bash
   npm install -g supabase
   ```

2. **Login to Supabase**
   ```bash
   supabase login
   ```

3. **Link to Your Project**
   ```bash
   supabase link --project-ref your-project-ref
   ```
   (Find your project ref in the Supabase dashboard URL)

4. **Run Migration**
   ```bash
   supabase db push
   ```

## Method 3: Using psql (Direct PostgreSQL Connection)

If you have direct PostgreSQL access:

1. **Get Connection String**
   - Go to Supabase Dashboard → Settings → Database
   - Copy the connection string (URI format)

2. **Run Migration**
   ```bash
   psql "your-connection-string" -f migrations/001_create_tables.sql
   ```

## Verification

After running the migration, verify the tables were created:

```sql
-- Run this in Supabase SQL Editor
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

You should see all 7 tables listed.

## Troubleshooting

- **Error: relation already exists**
  - The tables may already exist. Check the Table Editor first.
  - If you need to recreate, drop tables first (be careful with production data!)

- **Error: permission denied**
  - Make sure you're using the correct database credentials
  - Check that your Supabase project is active

- **Error: function gen_random_uuid() does not exist**
  - Enable the uuid-ossp extension:
    ```sql
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    ```
  - Or use `gen_random_uuid()` which is available in PostgreSQL 13+

