"""
Application configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Job Matching & Analysis API"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database - Supabase
    SUPABASE_DATABASE_URL: str = ""
    SUPABASE_DATABASE_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""  # Supabase JWT secret for token verification
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    
    # Google APIs
    GOOGLE_SAFE_BROWSING_API_KEY: str = ""
    GOOGLE_GEMINI_API_KEY: str = ""
    
    # LinkedIn/Indeed
    LINKEDIN_API_KEY: str = ""
    LINKEDIN_API_URL: str = "https://api.linkedin.com/v2"
    INDEED_API_KEY: str = ""
    INDEED_API_URL: str = "https://api.indeed.com/ads/apisearch"
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    DEBUG: bool = False
    
    # Google Cloud Storage
    GOOGLE_GCS_BUCKET_NAME: str = ""
    GOOGLE_PROJECT_ID: str = ""   # Alternative to GCS_PROJECT_ID   
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Credit Packages Configuration
    # Package definitions: 100 credits ($9.99), 500 credits ($39.99), 1000 credits ($69.99)
    CREDIT_PACKAGES: dict = {
        "100": {
            "price_id": "",  # Stripe Price ID - set in .env as STRIPE_PRICE_ID_100
            "credits": 100,
            "amount_cents": 999,
            "name": "100 Credits Package"
        },
        "500": {
            "price_id": "",  # Stripe Price ID - set in .env as STRIPE_PRICE_ID_500
            "credits": 500,
            "amount_cents": 3999,
            "name": "500 Credits Package"
        },
        "1000": {
            "price_id": "",  # Stripe Price ID - set in .env as STRIPE_PRICE_ID_1000
            "credits": 1000,
            "amount_cents": 6999,
            "name": "1000 Credits Package"
        }
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

