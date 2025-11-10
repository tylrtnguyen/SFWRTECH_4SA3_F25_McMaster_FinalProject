"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from app.core.config import settings
from app.core.singleton import DatabaseManager, StripeManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_user_id() -> UUID:
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def test_user_data(mock_user_id: UUID) -> dict:
    """Create test user data."""
    return {
        "user_id": str(mock_user_id),
        "email": "test@example.com",
        "oauth_provider": "traditional",
        "oauth_id": "test_hash",
        "credits": 50,
        "is_active": True
    }


@pytest.fixture
def credit_packages() -> dict:
    """Credit packages configuration."""
    return {
        "100": {
            "price_id": "price_test_100",
            "credits": 100,
            "amount_cents": 999,
            "name": "100 Credits Package"
        },
        "500": {
            "price_id": "price_test_500",
            "credits": 500,
            "amount_cents": 3999,
            "name": "500 Credits Package"
        },
        "1000": {
            "price_id": "price_test_1000",
            "credits": 1000,
            "amount_cents": 6999,
            "name": "1000 Credits Package"
        }
    }


@pytest.fixture
def mock_stripe_payment_intent() -> dict:
    """Mock Stripe payment intent response."""
    return {
        "id": "pi_test_1234567890",
        "client_secret": "pi_test_1234567890_secret_abcdef",
        "amount": 999,
        "currency": "cad",
        "status": "requires_payment_method",
        "metadata": {
            "user_id": str(uuid4()),
            "credits": "100"
        }
    }


@pytest.fixture
def mock_stripe_webhook_event() -> dict:
    """Mock Stripe webhook event payload."""
    return {
        "id": "evt_test_1234567890",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_1234567890",
                "amount": 999,
                "currency": "cad",
                "status": "succeeded",
                "metadata": {
                    "user_id": str(uuid4()),
                    "credits": "100"
                }
            }
        }
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_query = MagicMock()
    
    # Set up chain: client.table().select().eq().execute()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.update.return_value = mock_query
    mock_query.delete.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=[])
    
    mock_table.select.return_value = mock_query
    mock_table.insert.return_value = mock_query
    mock_table.update.return_value = mock_query
    mock_table.delete.return_value = mock_query
    mock_table.eq.return_value = mock_query
    
    mock_client.table.return_value = mock_table
    
    return mock_client


@pytest.fixture
def mock_stripe_client():
    """Mock Stripe client."""
    mock_stripe = MagicMock()
    
    # Mock PaymentIntent
    mock_payment_intent = MagicMock()
    mock_payment_intent.id = "pi_test_1234567890"
    mock_payment_intent.client_secret = "pi_test_1234567890_secret_abcdef"
    mock_payment_intent.amount = 999
    mock_payment_intent.currency = "cad"
    mock_payment_intent.status = "requires_payment_method"
    mock_payment_intent.metadata = {}
    
    mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
    mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
    
    # Mock Webhook
    mock_webhook = MagicMock()
    mock_stripe.Webhook.construct_event = MagicMock(return_value={
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_1234567890",
                "amount": 999,
                "currency": "cad",
                "status": "succeeded",
                "metadata": {}
            }
        }
    })
    
    return mock_stripe


@pytest.fixture
def mock_database_manager(mock_supabase_client):
    """Mock DatabaseManager singleton."""
    with patch.object(DatabaseManager, 'get_instance') as mock_manager:
        instance = MagicMock()
        instance.get_connection.return_value = mock_supabase_client
        mock_manager.return_value = instance
        yield instance


@pytest.fixture
def mock_stripe_manager(mock_stripe_client):
    """Mock StripeManager singleton."""
    with patch.object(StripeManager, 'get_instance') as mock_manager:
        instance = MagicMock()
        instance.get_client.return_value = mock_stripe_client
        mock_manager.return_value = instance
        yield instance

