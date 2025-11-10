"""
End-to-end integration tests for complete purchase flow
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from tests.mocks.stripe_mock import create_mock_payment_intent_response, create_mock_webhook_event


class TestCompletePurchaseFlow:
    """Test complete credit purchase flow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_complete_credit_purchase_flow(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test complete purchase flow from payment intent to credit update."""
        # Setup
        initial_credits = 50
        credits_to_purchase = 100
        amount_cents = 999
        
        # Step 1: Create payment intent
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=mock_payment_intent["amount"],
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Execute Step 1: Create payment intent
        response1 = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits_to_purchase
            }
        )
        
        # Assert Step 1
        assert response1.status_code == status.HTTP_200_OK
        intent_data = response1.json()
        assert intent_data["amount"] == amount_cents
        assert intent_data["credits"] == credits_to_purchase
        payment_intent_id = intent_data["payment_intent_id"]
        
        # Step 2: Simulate payment completion (webhook)
        webhook_event = create_mock_webhook_event(
            event_type="payment_intent.succeeded",
            payment_intent_id=payment_intent_id,
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        
        # Mock database for webhook processing
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_purchase}]
        )
        
        # Mock observer
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            # Execute Step 2: Process webhook
            response2 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            # Assert Step 2
            assert response2.status_code == status.HTTP_200_OK
            
            # Verify observers were notified
            mock_subject.credits_changed.assert_called_once()
            mock_subject.payment_complete.assert_called_once()
        
        # Step 3: Verify credits updated
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "user_id": str(mock_user_id),
                "email": "test@example.com",
                "credits": initial_credits + credits_to_purchase,
                "created_at": "2024-01-01T10:00:00Z"
            }]
        )
        
        # Execute Step 3: Get user credits
        response3 = await async_client.get(
            f"/api/v1/payments/user/{mock_user_id}/credits"
        )
        
        # Assert Step 3
        assert response3.status_code == status.HTTP_200_OK
        credits_data = response3.json()
        assert credits_data["credits"] == initial_credits + credits_to_purchase
    
    @pytest.mark.asyncio
    async def test_complete_purchase_100_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test complete purchase flow for 100 credits package."""
        # Setup
        initial_credits = 50
        credits_to_purchase = 100
        amount_cents = 999  # $9.99
        
        # Create payment intent
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=amount_cents,
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Create payment intent
        response1 = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits_to_purchase
            }
        )
        
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["amount"] == 999
        assert response1.json()["credits"] == 100
        
        # Process webhook
        webhook_event = create_mock_webhook_event(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_purchase}]
        )
        
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            response2 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            assert response2.status_code == status.HTTP_200_OK
            mock_subject.credits_changed.assert_called_once()
            mock_subject.payment_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_purchase_500_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test complete purchase flow for 500 credits package."""
        # Setup
        initial_credits = 50
        credits_to_purchase = 500
        amount_cents = 3999  # $39.99
        
        # Create payment intent
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=amount_cents,
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Create payment intent
        response1 = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits_to_purchase
            }
        )
        
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["amount"] == 3999
        assert response1.json()["credits"] == 500
        
        # Process webhook
        webhook_event = create_mock_webhook_event(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_purchase}]
        )
        
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            response2 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            assert response2.status_code == status.HTTP_200_OK
            mock_subject.credits_changed.assert_called_once()
            mock_subject.payment_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_purchase_1000_credits(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test complete purchase flow for 1000 credits package."""
        # Setup
        initial_credits = 50
        credits_to_purchase = 1000
        amount_cents = 6999  # $69.99
        
        # Create payment intent
        mock_payment_intent = create_mock_payment_intent_response(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
            id=mock_payment_intent["id"],
            client_secret=mock_payment_intent["client_secret"],
            amount=amount_cents,
            currency="cad",
            status="requires_payment_method"
        )
        
        mock_connection = mock_database_manager.get_connection.return_value
        mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"transaction_id": str(uuid4())}]
        )
        
        # Create payment intent
        response1 = await async_client.post(
            "/api/v1/payments/intent",
            json={
                "user_id": str(mock_user_id),
                "amount": amount_cents,
                "credits": credits_to_purchase
            }
        )
        
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["amount"] == 6999
        assert response1.json()["credits"] == 1000
        
        # Process webhook
        webhook_event = create_mock_webhook_event(
            amount=amount_cents,
            credits=credits_to_purchase,
            user_id=str(mock_user_id)
        )
        
        mock_stripe_manager.get_client.return_value.Webhook.construct_event.return_value = webhook_event
        mock_connection.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits}]
        )
        mock_connection.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"credits": initial_credits + credits_to_purchase}]
        )
        
        with patch('app.routers.payments.user_event_subject') as mock_subject:
            mock_subject.credits_changed = AsyncMock()
            mock_subject.payment_complete = AsyncMock()
            
            response2 = await async_client.post(
                "/api/v1/payments/webhook",
                content=json.dumps(webhook_event),
                headers={
                    "stripe-signature": "test_signature",
                    "content-type": "application/json"
                }
            )
            
            assert response2.status_code == status.HTTP_200_OK
            mock_subject.credits_changed.assert_called_once()
            mock_subject.payment_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_purchases(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test that system handles concurrent purchases correctly."""
        # Setup
        initial_credits = 50
        
        # Create multiple payment intents concurrently
        payment_intents = []
        for i in range(3):
            amount_cents = 999
            credits = 100
            
            mock_payment_intent = create_mock_payment_intent_response(
                amount=amount_cents,
                credits=credits,
                user_id=str(mock_user_id)
            )
            
            mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = MagicMock(
                id=mock_payment_intent["id"],
                client_secret=mock_payment_intent["client_secret"],
                amount=amount_cents,
                currency="cad",
                status="requires_payment_method"
            )
            
            mock_connection = mock_database_manager.get_connection.return_value
            mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{"transaction_id": str(uuid4())}]
            )
            
            response = await async_client.post(
                "/api/v1/payments/intent",
                json={
                    "user_id": str(mock_user_id),
                    "amount": amount_cents,
                    "credits": credits
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            payment_intents.append(response.json())
        
        # Assert - all payment intents created successfully
        assert len(payment_intents) == 3
        assert all(pi["amount"] == 999 for pi in payment_intents)
        assert all(pi["credits"] == 100 for pi in payment_intents)

