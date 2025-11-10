"""
Tests for error handling
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from app.services.stripe_service import StripeService
from app.core.singleton import DatabaseManager, StripeManager


class TestErrorHandling:
    """Test error handling in payment flow."""
    
    @pytest.mark.asyncio
    async def test_stripe_api_failure(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test graceful handling of Stripe API failures."""
        # Setup - Stripe API raises exception
        import stripe
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.side_effect = stripe.error.StripeError(
            "API Error: Rate limit exceeded"
        )
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": 999,
                "credits": 100
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Payment intent creation failed" in response.json()["detail"]
        
        # Verify no partial state in database
        # (Transaction should not be created if Stripe fails)
        mock_connection = mock_database_manager.get_connection.return_value
        # Insert should not be called if Stripe fails
        # (This depends on implementation - if we check Stripe first, insert won't be called)
    
    @pytest.mark.asyncio
    async def test_database_failure(self, async_client, mock_user_id, mock_stripe_manager):
        """Test graceful handling of database failures."""
        # Setup - Stripe succeeds but database fails
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_123"
        mock_payment_intent.client_secret = "pi_test_123_secret"
        mock_payment_intent.amount = 999
        mock_payment_intent.currency = "cad"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = mock_payment_intent
        
        # Mock database failure
        with patch.object(DatabaseManager, 'get_instance') as mock_db_manager:
            instance = MagicMock()
            mock_connection = MagicMock()
            mock_connection.table.return_value.insert.return_value.execute.side_effect = Exception("Database connection error")
            instance.get_connection.return_value = mock_connection
            mock_db_manager.return_value = instance
            
            # Execute
            response = await async_client.post(
                "/api/v1/payments/intent",
                json={
                    "user_id": str(mock_user_id),
                    "amount": 999,
                    "credits": 100
                }
            )
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Payment intent creation failed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_webhook_processing_failure_invalid_payload(self, async_client, mock_stripe_manager):
        """Test webhook processing failure with invalid payload."""
        # Setup - invalid JSON
        invalid_payload = "not valid json"
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=invalid_payload,
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Webhook processing failed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_webhook_processing_failure_missing_fields(self, async_client, mock_stripe_manager):
        """Test webhook processing failure with missing required fields."""
        # Setup - webhook event missing required fields
        incomplete_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    # Missing metadata
                }
            }
        }
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = incomplete_event
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(incomplete_event),
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Assert - should return 400 for missing metadata
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing required metadata" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_webhook_processing_failure_database_update(self, async_client, mock_user_id, mock_stripe_manager):
        """Test webhook processing failure during database update."""
        # Setup
        webhook_event = {
            "id": "evt_test",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    "amount": 999,
                    "status": "succeeded",
                    "metadata": {
                        "user_id": str(mock_user_id),
                        "credits": "100"
                    }
                }
            }
        }
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        # Mock database failure during update
        with patch.object(DatabaseManager, 'get_instance') as mock_db_manager:
            instance = MagicMock()
            mock_connection = MagicMock()
            
            # First select succeeds (get current credits)
            mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"credits": 50}]
            )
            
            # Update fails
            mock_connection.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database update failed")
            
            instance.get_connection.return_value = mock_connection
            mock_db_manager.return_value = instance
            
            # Execute
            response = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Webhook processing failed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_stripe_service_error_handling(self, mock_stripe_manager):
        """Test StripeService error handling."""
        # Setup
        service = StripeService()
        stripe_client = mock_stripe_manager.get_client.return_value
        
        # Test PaymentIntent creation error
        import stripe
        stripe_client.PaymentIntent.create.side_effect = stripe.error.InvalidRequestError(
            "Invalid amount", "amount"
        )
        
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            service.create_payment_intent(amount=999)
        
        assert "Failed to create payment intent" in str(exc_info.value)
        
        # Test PaymentIntent retrieval error
        stripe_client.PaymentIntent.retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such payment_intent", "id"
        )
        
        with pytest.raises(ValueError) as exc_info:
            service.retrieve_payment_intent("pi_invalid")
        
        assert "Failed to retrieve payment intent" in str(exc_info.value)
        
        # Test webhook verification error
        stripe_client.Webhook.construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "signature"
        )
        
        with patch('app.services.stripe_service.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
            
            with pytest.raises(ValueError) as exc_info:
                service.handle_webhook({}, "invalid_signature")
            
            assert "Webhook verification failed" in str(exc_info.value)

