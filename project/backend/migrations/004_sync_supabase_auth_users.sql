-- Migration: Sync Supabase Auth users to custom users table
-- Creates a trigger that automatically creates a record in the users table
-- when a new user signs up via Supabase Auth

-- Create function to handle new user creation from Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (
    user_id,
    email,
    oauth_provider,
    oauth_id,
    credits,
    is_active
  )
  VALUES (
    NEW.id,  -- Use Supabase Auth user ID as user_id
    NEW.email,
    'supabase',
    NEW.id::text,  -- Store auth user ID as oauth_id
    50,  -- Default credits
    TRUE  -- Active by default
  )
  ON CONFLICT (user_id) DO NOTHING;  -- Prevent duplicate inserts
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger on auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- Create function to handle user email updates from Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_user_email_update()
RETURNS TRIGGER AS $$
BEGIN
  -- Update email in users table if it changed
  IF OLD.email != NEW.email THEN
    UPDATE public.users
    SET email = NEW.email
    WHERE user_id = NEW.id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for email updates
DROP TRIGGER IF EXISTS on_auth_user_email_updated ON auth.users;
CREATE TRIGGER on_auth_user_email_updated
  AFTER UPDATE OF email ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_user_email_update();

