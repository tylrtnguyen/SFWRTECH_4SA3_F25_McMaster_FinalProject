-- Migration: Delete all existing users
-- WARNING: This will permanently delete all users from both auth.users and public.users tables
-- This operation cannot be undone. Use with caution.

-- Step 1: Delete all records from public.users table
-- This will cascade delete related records in other tables due to foreign key constraints
DELETE FROM public.users;

-- Step 2: Delete all users from auth.users table
-- Note: This requires superuser privileges or using Supabase Admin API
-- If you don't have direct access, use the Supabase Dashboard:
-- 1. Go to Authentication > Users
-- 2. Select all users
-- 3. Click "Delete users"
--
-- Alternatively, if you have direct database access with superuser privileges:
-- DELETE FROM auth.users;

-- Verification query (run after deletion to confirm)
-- SELECT COUNT(*) as remaining_users FROM public.users;
-- SELECT COUNT(*) as remaining_auth_users FROM auth.users;

