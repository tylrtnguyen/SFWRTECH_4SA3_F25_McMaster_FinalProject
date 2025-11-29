"""
Singleton Pattern Implementation
Manages shared DB/API/Stripe session for user accounts
"""

import threading
from typing import Optional, Any
from supabase import create_client, Client
import stripe
import httpx
from app.core.config import settings


class DatabaseManager:
    """
    Singleton for database connection management using Supabase
    Ensures single Supabase client instance across the application
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client: Optional[Client] = None
            self._lock = threading.Lock()
            self._initialized = True

    def get_connection(self) -> Client:
        """
        Get or create Supabase client connection
        Returns Supabase client for database operations
        """
        if self.client is None:
            with self._lock:
                if self.client is None:
                    if (
                        not settings.SUPABASE_DATABASE_URL
                        or not settings.SUPABASE_DATABASE_API_KEY
                    ):
                        raise ValueError(
                            "Supabase credentials not configured. Set SUPABASE_DATABASE_URL and SUPABASE_DATABASE_API_KEY in .env"
                        )

                    self.client = create_client(
                        settings.SUPABASE_DATABASE_URL,
                        settings.SUPABASE_DATABASE_API_KEY,
                    )
        return self.client

    def get_client(self) -> Client:
        """Alias for get_connection for consistency"""
        return self.get_connection()

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Get singleton instance"""
        return cls()


class StripeManager:
    """
    Singleton for Stripe API session management
    Ensures single Stripe client instance across the application
    """

    _instance: Optional["StripeManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StripeManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client: Optional[Any] = None
            self._lock = threading.Lock()
            self._initialized = True

    def get_client(self) -> Any:
        """Get or create Stripe client"""
        if self.client is None:
            with self._lock:
                if self.client is None:
                    if settings.STRIPE_SECRET_KEY:
                        stripe.api_key = settings.STRIPE_SECRET_KEY
                        self.client = stripe
                    else:
                        raise ValueError("Stripe secret key not configured")
        return self.client

    @classmethod
    def get_instance(cls) -> "StripeManager":
        """Get singleton instance"""
        return cls()


class APIConnectionManager:
    """
    Singleton for managing API connections (Gemini, GCS, Google Safe Browsing API)
    Ensures shared connection pool and session management
    """

    _instance: Optional["APIConnectionManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(APIConnectionManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.http_client: Optional[httpx.AsyncClient] = None
            self._lock = threading.Lock()
            self._initialized = True

    async def get_client(self):
        """Get or create HTTP client"""
        if self.http_client is None:
            with self._lock:
                if self.http_client is None:
                    self.http_client = httpx.AsyncClient(
                        timeout=30.0, follow_redirects=True
                    )
        return self.http_client

    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

    @classmethod
    def get_instance(cls) -> "APIConnectionManager":
        """Get singleton instance"""
        return cls()
