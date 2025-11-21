# Supabase Auth Configuration Guide

## Password-Based Authentication Setup

This application uses password-based authentication without email confirmation for local development and production.

### Disable Email Confirmation in Supabase

To enable password-based authentication without email confirmation:

1. **Go to Supabase Dashboard**
   - Navigate to https://supabase.com/dashboard
   - Select your project

2. **Open Auth Settings**
   - Go to **Authentication** → **Providers** in the left sidebar
   - Click on **Email** provider

3. **Disable Email Confirmation**
   - Find the **"Confirm email"** toggle
   - **Turn OFF** the email confirmation requirement
   - This allows users to sign up and immediately sign in without email verification

4. **Save Changes**
   - Click **Save** to apply the changes

### Alternative: Using Supabase CLI (Local Development)

If you're using Supabase locally with the CLI, update your `config.toml`:

```toml
[auth.email]
enable_signup = true
double_confirm_changes = false
enable_confirmations = false  # Disable email confirmations
```

Then restart your local Supabase instance:

```bash
supabase stop
supabase start
```

### Verification

After disabling email confirmation:

1. Users can sign up with email and password
2. They are automatically signed in after registration
3. No confirmation email is sent
4. Users can immediately access the dashboard

### Security Note

- Email confirmation is disabled for easier local development
- For production, consider enabling email confirmation for better security
- The application still validates password strength (8+ chars, uppercase, number, special char)

