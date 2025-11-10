"""
Tests for webhook handling
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from app.services.stripe_service import StripeService
from tests.mocks.stripe_mock import create_mock_webhook_event


class TestWebhookHandling:
    """Test webhook handling endpoints."""
    
    @pytest.mark.asyncio
    async def test_webhook_payment_succeeded(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test successful webhook processing for payment_intent.succeeded."""
        # Setup
        old_credits = 50
        credits_to_add = 100
        new_credits = old_credits + credits_to_add
        
        webhook_event = create_mock_webhook_event(
            event_type="payment_intent.succeeded",
            amount=999,
            credits=credits_to_add,
            user_id=str(mock_user_id)
        )
        
        # Mock webhook handling
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        # Mock database operations
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": old_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": new_credits}]
        )
        
        # Mock observer
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
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
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "success"
            
            # Verify credits were updated
            update_call = mock_connection.table.return_value.update
            assert update_call.called
            
            # Verify observers were notified
            mock_subject.credits_changed.assert_called_once()
            mock_subject.payment_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_signature_verification(self, async_client, mock_stripe_manager):
        """Test webhook signature verification."""
        webhook_event = create_mock_webhook_event()
        
        # Test with valid signature
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
            
            response = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "valid_signature",
                    "content-type": "application/json"
                }
            )
            
            # Should process successfully
            assert response.status_code == status.HTTP_200_OK
        
        # Test with invalid signature
        import stripe
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "invalid_signature"
        )
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
            
            response = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "invalid_signature",
                    "content-type": "application/json"
                }
            )
            
            # Should fail with 400
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_webhook_missing_signature(self, async_client, mock_stripe_manager):
        """Test webhook handling with missing signature."""
        webhook_event = create_mock_webhook_event()
        
        # Mock webhook to work without signature (dev mode)
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = ""  # No secret = dev mode
            
            response = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "content-type": "application/json"
                }
            )
            
            # Should process in dev mode
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_webhook_other_events(self, async_client, mock_stripe_manager):
        """Test handling of other webhook event types."""
        # Test payment_intent.payment_failed
        failed_event = create_mock_webhook_event(
            event_type="payment_intent.payment_failed"
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = failed_event
        
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(failed_event),
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Should return success but not process credits
        assert response.status_code == status.HTTP_200_OK
        
        # Test payment_intent.canceled
        canceled_event = create_mock_webhook_event(
            event_type="payment_intent.canceled"
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = canceled_event
        
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(canceled_event),
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Should return success but not process credits
        assert response.status_code == status.HTTP_200_OK
        
        # Test unknown event type
        unknown_event = create_mock_webhook_event(
            event_type="charge.succeeded"
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = unknown_event
        
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(unknown_event),
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Should return success but not process
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_webhook_metadata_extraction(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test that user_id and credits are extracted from webhook metadata."""
        # Setup
        user_id_str = str(mock_user_id)
        credits = 100
        
        webhook_event = create_mock_webhook_event(
            credits=credits,
            user_id=user_id_str
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        # Mock database
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": 50}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": 150}]
        )
        
        # Mock observer
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
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
            assert response.status_code == status.HTTP_200_OK
            
            # Verify correct user_id was used
            select_call = mock_connection.table.return_value.select
            assert select_call.called
            
            # Verify credits were added correctly
            update_call = mock_connection.table.return_value.update
            assert update_call.called
    
    @pytest.mark.asyncio
    async def test_webhook_missing_metadata(self, async_client, mock_stripe_manager):
        """Test webhook handling with missing metadata."""
        # Setup webhook event without metadata
        webhook_event = {
            "id": "evt_test",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    "amount": 999,
                    "status": "succeeded",
                    "metadata": {}  # Empty metadata
                }
            }
        }
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        # Execute
        response = await async_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(webhook_event),
            headers={
                "stripe-signature": "test_signature",
                "content-type": "application/json"
            }
        )
        
        # Assert - should return 400 for missing metadata
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing required metadata" in response.json()["detail"]

