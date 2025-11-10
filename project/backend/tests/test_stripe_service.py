"""
Unit tests for StripeService class
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.stripe_service import StripeService
from app.core.singleton import StripeManager


class TestStripeService:
    """Test StripeService class methods."""
    
    @pytest.fixture
    def mock_stripe_manager(self):
        """Create a mock StripeManager."""
        with patch.object(StripeManager, 'get_instance') as mock_manager:
            instance = MagicMock()
            mock_stripe = MagicMock()
            
            # Mock PaymentIntent
            mock_payment_intent = MagicMock()
            mock_payment_intent.id = "pi_test_1234567890"
            mock_payment_intent.client_secret = "pi_test_1234567890_secret"
            mock_payment_intent.amount = 999
            mock_payment_intent.currency = "cad"
            mock_payment_intent.status = "requires_payment_method"
            
            mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
            mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
            
            instance.get_client.return_value = mock_stripe
            mock_manager.return_value = instance
            yield instance
    
    def test_create_payment_intent_stripe_api(self, mock_stripe_manager):
        """Test that StripeService correctly calls Stripe API."""
        # Setup
        service = StripeService()
        amount = 999
        currency = "cad"
        metadata = {"user_id": str(uuid4()), "credits": "100"}
        
        # Execute
        result = service.create_payment_intent(
            amount=amount,
            currency=currency,
            metadata=metadata
        )
        
        # Assert
        assert result["id"] == "pi_test_1234567890"
        assert result["client_secret"] == "pi_test_1234567890_secret"
        assert result["amount"] == 999
        assert result["currency"] == "cad"
        assert result["status"] == "requires_payment_method"
        
        # Verify Stripe API was called correctly
        stripe_client = mock_stripe_manager.get_client.return_value
        stripe_client.PaymentIntent.create.assert_called_once()
        call_kwargs = stripe_client.PaymentIntent.create.call_args[1]
        assert call_kwargs["amount"] == amount
        assert call_kwargs["currency"] == currency
        assert call_kwargs["metadata"] == metadata
    
    def test_create_payment_intent_with_automatic_payment_methods(self, mock_stripe_manager):
        """Test that automatic payment methods are enabled."""
        # Setup
        service = StripeService()
        
        # Execute
        service.create_payment_intent(amount=999)
        
        # Assert
        stripe_client = mock_stripe_manager.get_client.return_value
        call_kwargs = stripe_client.PaymentIntent.create.call_args[1]
        assert "automatic_payment_methods" in call_kwargs
        assert call_kwargs["automatic_payment_methods"]["enabled"] is True
    
    def test_stripe_api_error_handling(self, mock_stripe_manager):
        """Test that Stripe API errors are handled gracefully."""
        # Setup
        service = StripeService()
        stripe_client = mock_stripe_manager.get_client.return_value
        
        # Mock Stripe API exception
        import stripe
        stripe_client.PaymentIntent.create.side_effect = stripe.error.StripeError("API Error")
        
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            service.create_payment_intent(amount=999)
        
        assert "Failed to create payment intent" in str(exc_info.value)
    
    def test_retrieve_payment_intent(self, mock_stripe_manager):
        """Test retrieving payment intent by ID."""
        # Setup
        service = StripeService()
        payment_intent_id = "pi_test_1234567890"
        
        # Mock retrieved payment intent
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = payment_intent_id
        mock_payment_intent.amount = 999
        mock_payment_intent.currency = "cad"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.metadata = {"user_id": str(uuid4()), "credits": "100"}
        
        stripe_client = mock_stripe_manager.get_client.return_value
        stripe_client.PaymentIntent.retrieve.return_value = mock_payment_intent
        
        # Execute
        result = service.retrieve_payment_intent(payment_intent_id)
        
        # Assert
        assert result["id"] == payment_intent_id
        assert result["amount"] == 999
        assert result["currency"] == "cad"
        assert result["status"] == "succeeded"
        assert result["metadata"] == {"user_id": mock_payment_intent.metadata["user_id"], "credits": "100"}
        
        # Verify Stripe API was called correctly
        stripe_client.PaymentIntent.retrieve.assert_called_once_with(payment_intent_id)
    
    def test_retrieve_payment_intent_error(self, mock_stripe_manager):
        """Test error handling when retrieving payment intent fails."""
        # Setup
        service = StripeService()
        stripe_client = mock_stripe_manager.get_client.return_value
        
        # Mock Stripe API exception
        import stripe
        stripe_client.PaymentIntent.retrieve.side_effect = stripe.error.StripeError("Not found")
        
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            service.retrieve_payment_intent("pi_invalid")
        
        assert "Failed to retrieve payment intent" in str(exc_info.value)
    
    def test_handle_webhook_with_secret(self, mock_stripe_manager):
        """Test webhook handling with webhook secret."""
        # Setup
        service = StripeService()
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}
        signature = "test_signature"
        webhook_secret = "whsec_test_secret"
        
        # Mock webhook construction
        mock_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test",
                    "amount": 999,
                    "metadata": {"user_id": str(uuid4()), "credits": "100"}
                }
            }
        }
        
        stripe_client = mock_stripe_manager.get_client.return_value
        stripe_client.Webhook.construct_event.return_value = mock_event
        
        # Mock settings
        with patch('app.services.stripe_service.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
            
            # Execute
            result = service.handle_webhook(payload, signature)
        
        # Assert
        assert result["type"] == "payment_intent.succeeded"
        assert "data" in result
        stripe_client.Webhook.construct_event.assert_called_once()
    
    def test_handle_webhook_without_secret(self, mock_stripe_manager):
        """Test webhook handling without webhook secret (development mode)."""
        # Setup
        service = StripeService()
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}
        signature = "test_signature"
        
        # Mock settings - no webhook secret
        with patch('app.services.stripe_service.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = ""
            
            # Execute
            result = service.handle_webhook(payload, signature)
        
        # Assert
        assert result["type"] == "payment_intent.succeeded"
        assert "data" in result
    
    def test_handle_webhook_verification_failure(self, mock_stripe_manager):
        """Test webhook verification failure."""
        # Setup
        service = StripeService()
        payload = {"type": "payment_intent.succeeded"}
        signature = "invalid_signature"
        webhook_secret = "whsec_test_secret"
        
        stripe_client = mock_stripe_manager.get_client.return_value
        
        # Mock webhook verification failure
        import stripe
        stripe_client.Webhook.construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", signature
        )
        
        # Mock settings
        with patch('app.services.stripe_service.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
            
            # Execute & Assert
            with pytest.raises(ValueError) as exc_info:
                service.handle_webhook(payload, signature)
            
            assert "Webhook verification failed" in str(exc_info.value)
    
    def test_calculate_credits_from_amount(self):
        """Test credit calculation from amount."""
        # Setup
        service = StripeService()
        
        # Execute & Assert
        # $1 = 10 credits, so $9.99 = 99 credits (rounded down)
        assert service.calculate_credits_from_amount(999) == 99
        # $39.99 = 399 credits
        assert service.calculate_credits_from_amount(3999) == 399
        # $69.99 = 699 credits
        assert service.calculate_credits_from_amount(6999) == 699

