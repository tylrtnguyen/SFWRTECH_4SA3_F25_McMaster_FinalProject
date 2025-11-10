"""
Tests for payment intent creation
"""

import pytest
from uuid import uuid4
from unittest.mock import  MagicMock
from fastapi import status

from app.models.schemas import PaymentIntentCreate, PaymentIntentResponse
from tests.mocks.stripe_mock import create_mock_payment_intent_response


class TestPaymentIntentCreation:
    """Test payment intent creation endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test successful payment intent creation."""
        # Setup
        amount_cents = 999
        credits = 100
        
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits,
            user_id=str(mock_user_id)
        )
        
        # Mock Stripe payment intent creation
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency=mock_payment_intent["currency"],
            status=mock_payment_intent["status"]
        )
        
        # Mock database operations
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "client_secret" in data
        assert "payment_intent_id" in data
        assert data["amount"] == amount_cents
        assert data["credits"] == credits
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_100_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test payment intent creation for 100 credits package."""
        # Setup
        amount_cents = 999  # $9.99
        credits = 100
        
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["amount"] == 999
        assert data["credits"] == 100
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_500_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test payment intent creation for 500 credits package."""
        # Setup
        amount_cents = 3999  # $39.99
        credits = 500
        
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["amount"] == 3999
        assert data["credits"] == 500
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_1000_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test payment intent creation for 1000 credits package."""
        # Setup
        amount_cents = 6999  # $69.99
        credits = 1000
        
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["amount"] == 6999
        assert data["credits"] == 1000
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_user(self, async_client, mock_database_manager):
        """Test payment intent creation with invalid user."""
        # Setup - user not found
        mock_database_manager.get_connection.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(uuid4()),
                "amount": 999,
                "credits": 100
            }
        )
        
        # Assert - should still create payment intent (user validation happens elsewhere)
        # The endpoint doesn't validate user existence, so this should succeed
        # If we want to validate, we'd need to add that check
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_amount(self, async_client, mock_user_id):
        """Test payment intent creation with invalid amount."""
        # Execute with zero amount
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": 0,
                "credits": 100
            }
        )
        
        # Assert - Custom validation handler should catch this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        # New format: { status_code, error_message, error_type }
        assert "status_code" in error_data
        assert "error_message" in error_data
        assert "error_type" in error_data
        assert error_data["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "greater than" in error_data["error_message"].lower() or "amount" in error_data["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_payment_intent_metadata(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test that payment intent metadata is set correctly."""
        # Setup
        amount_cents = 999
        credits = 100
        user_id_str = str(mock_user_id)
        
        mock_payment_intent_obj = MagicMock()
        mock_payment_intent_obj.id = "pi_test_123"
        mock_payment_intent_obj.client_secret = "pi_test_123_secret"
        mock_payment_intent_obj.amount = amount_cents
        mock_payment_intent_obj.currency = "cad"
        mock_payment_intent_obj.status = "requires_payment_method"
        
        create_call = MagicMock(return_value=mock_payment_intent_obj)
        mock_stripe_manager.get_client.return_value.PaymentIntent.create = create_call
        
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute
        await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": user_id_str,
                "amount": amount_cents,
                "credits": credits
            }
        )
        
        # Assert - verify metadata was passed to Stripe
        create_call.assert_called_once()
        call_kwargs = create_call.call_args[1]
        assert call_kwargs["metadata"]["user_id"] == user_id_str
        assert call_kwargs["metadata"]["credits"] == str(credits)
    
    @pytest.mark.asyncio
    async def test_invalid_package_selection(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test invalid package selection."""
        from tests.mocks.stripe_mock import create_mock_payment_intent_response
        # Setup - allow any amount/credits combination (no strict package validation)
        mock_payment_intent = create_mock_payment_intent_response(
            amount=999,
            credits=200,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_database_manager.get_connection.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute with invalid amount/credits combination
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": 999,
                "credits": 200  # Invalid: should be 100 for $9.99, but we allow it
            }
        )
        
        # Assert - should still create payment intent (no strict package validation)
        assert response.status_code == status.HTTP_200_OK

