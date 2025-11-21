-- Migration: Add first_name and last_name columns to users table
-- Updates the trigger function to extract and store names from Supabase Auth metadata

-- Step 1: Add first_name and last_name columns to users table
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS first_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);

-- Step 2: Update handle_new_user() function to extract names from auth metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  existing_user_id UUID;
  user_first_name VARCHAR(255);
  user_last_name VARCHAR(255);
BEGIN
  -- Extract first_name and last_name from raw_user_meta_data
  user_first_name := NEW.raw_user_meta_data->>'firstName';
  user_last_name := NEW.raw_user_meta_data->>'lastName';
  
  -- Check if user with this email already exists
  SELECT user_id INTO existing_user_id
  FROM public.users
  WHERE email = NEW.email;
  
  IF existing_user_id IS NOT NULL THEN
    -- User exists with this email, update it
    UPDATE public.users
    SET 
      user_id = NEW.id,
      oauth_id = NEW.id::text,
      oauth_provider = 'supabase',
      is_active = TRUE,
      first_name = COALESCE(user_first_name, first_name),
      last_name = COALESCE(user_last_name, last_name)
    WHERE email = NEW.email;
  ELSE
    -- New user, try to insert
    BEGIN
      INSERT INTO public.users (
        user_id,
        email,
        oauth_provider,
        oauth_id,
        credits,
        is_active,
        first_name,
        last_name
      )
      VALUES (
        NEW.id,
        NEW.email,
        'supabase',
        NEW.id::text,
        50,
        TRUE,
        user_first_name,
        user_last_name
      );
    EXCEPTION
      WHEN unique_violation THEN
        -- User_id already exists, update instead
        UPDATE public.users
        SET 
          email = NEW.email,
          oauth_id = NEW.id::text,
          oauth_provider = 'supabase',
          is_active = TRUE,
          first_name = COALESCE(user_first_name, first_name),
          last_name = COALESCE(user_last_name, last_name)
        WHERE user_id = NEW.id;
    END;
  END IF;
  
  RETURN NEW;
EXCEPTION
  WHEN others THEN
    -- Log error but don't fail auth user creation
    RAISE WARNING 'Error in handle_new_user for user %: %', NEW.id, SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

