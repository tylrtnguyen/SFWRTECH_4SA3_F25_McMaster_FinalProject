"""
Script to run database migrations in Supabase
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def run_migration():
    """Run SQL migration file against Supabase"""
    
    # Check if Supabase credentials are configured
    if not settings.SUPABASE_DATABASE_URL or not settings.SUPABASE_DATABASE_API_KEY:
        print("Error: SUPABASE_DATABASE_URL and SUPABASE_DATABASE_API_KEY must be set in .env file")
        sys.exit(1)
    
    # Create Supabase client
    supabase: Client = create_client(
        settings.SUPABASE_DATABASE_URL,
        settings.SUPABASE_DATABASE_API_KEY
    )
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "001_create_tables.sql"
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Split SQL into individual statements
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"Running migration: {migration_file.name}")
    print(f"Found {len(statements)} SQL statements")
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        try:
            print(f"Executing statement {i}/{len(statements)}...")
            # Note: Supabase Python client doesn't directly support raw SQL execution
            # You'll need to use the Supabase REST API or run this via the dashboard
            print("Note: Direct SQL execution via Python client is limited.")
            print("Please run the migration SQL file directly in Supabase SQL Editor.")
            print("\nSQL to execute:")
            print("=" * 80)
            print(sql)
            print("=" * 80)
            break
        except Exception as e:
            print(f"Error executing statement {i}: {str(e)}")
            sys.exit(1)
    
    print("\nMigration instructions:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the SQL above")
    print("4. Click 'Run' to execute")


if __name__ == "__main__":
    run_migration()

