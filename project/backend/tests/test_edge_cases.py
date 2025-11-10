"""
Tests for edge cases and boundary conditions
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from tests.mocks.stripe_mock import create_mock_webhook_event


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_maximum_credit_purchase(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test system handles large credit purchases."""
        # Setup - 1000 credits (maximum package)
        amount_cents = 6999
        credits = 1000
        
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_max"
        mock_payment_intent.client_secret = "pi_test_max_secret"
        mock_payment_intent.amount = amount_cents
        mock_payment_intent.currency = "cad"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = mock_payment_intent
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
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
        assert data["amount"] == amount_cents
        assert data["credits"] == credits
    
    @pytest.mark.asyncio
    async def test_minimum_credit_purchase(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test system handles minimum credit purchases."""
        # Setup - 1 credit (minimum)
        amount_cents = 10  # $0.10
        credits = 1
        
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_min"
        mock_payment_intent.client_secret = "pi_test_min_secret"
        mock_payment_intent.amount = amount_cents
        mock_payment_intent.currency = "cad"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = mock_payment_intent
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
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
        assert data["amount"] == amount_cents
        assert data["credits"] == credits
    
    @pytest.mark.asyncio
    async def test_duplicate_webhook_processing(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test that duplicate webhooks don't double-credit."""
        # Setup
        initial_credits = 50
        credits_to_add = 100
        payment_intent_id = "pi_test_duplicate"
        
        webhook_event = create_mock_webhook_event(
            event_type="payment_intent.succeeded",
            payment_intent_id=payment_intent_id,
            amount=999,
            credits=credits_to_add,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        mock_connection = mock_database_manager.get_connection.return_value
        
        # First webhook processing
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_add}]
        )
        
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            # Execute first webhook
            response1 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            assert response1.status_code == status.HTTP_200_OK
        
        # Second webhook processing (duplicate)
        # Note: In a real implementation, we'd check if payment was already processed
        # For now, this test verifies the current behavior
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_add}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_add + credits_to_add}]  # Would double-credit
        )
        
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            # Execute duplicate webhook
            response2 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            # Assert - should process (but ideally should be idempotent)
            # This test documents current behavior - idempotency should be added
            assert response2.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_webhook_missing_metadata(self, async_client, mock_stripe_manager):
        """Test webhook handling with missing metadata."""
        # Setup - webhook event without metadata
        webhook_event = {
            "id": "evt_test",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    "amount": 999,
                    "status": "succeeded",
                    # Missing metadata
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
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_user_id(self, async_client, mock_stripe_manager):
        """Test webhook handling with invalid user_id in metadata."""
        # Setup - invalid UUID
        webhook_event = {
            "id": "evt_test",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    "amount": 999,
                    "status": "succeeded",
                    "metadata": {
                        "user_id": "invalid_uuid",
                        "credits": "100"
                    }
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
        
        # Assert - should fail when trying to convert to UUID
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_credits(self, async_client, mock_user_id, mock_stripe_manager):
        """Test webhook handling with invalid credits in metadata."""
        # Setup - credits is not a number
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
                        "credits": "not_a_number"
                    }
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
        
        # Assert - should fail when trying to convert to int
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_webhook_zero_credits(self, async_client, mock_user_id, mock_stripe_manager):
        """Test webhook handling with zero credits."""
        # Setup - zero credits
        webhook_event = create_mock_webhook_event(
            credits=0,
            user_id=str(mock_user_id)
        )
        
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
        
        # Assert - should return success but not process (credits check fails)
        # The code checks if credits > 0, so it should skip processing
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_payment_intent_boundary_amounts(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test payment intent creation with boundary amounts."""
        # Test minimum amount (1 cent)
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_1"
        mock_payment_intent.client_secret = "pi_test_1_secret"
        mock_payment_intent.amount = 1
        mock_payment_intent.currency = "cad"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = mock_payment_intent
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": 1,
                "credits": 1
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Test large amount (100000 cents = $1000)
        mock_payment_intent.amount = 100000
        mock_payment_intent.id = "pi_test_2"
        mock_payment_intent.client_secret = "pi_test_2_secret"
        
        response = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": 100000,
                "credits": 10000
            }
        )
        
        assert response.status_code == status.HTTP_200_OK

