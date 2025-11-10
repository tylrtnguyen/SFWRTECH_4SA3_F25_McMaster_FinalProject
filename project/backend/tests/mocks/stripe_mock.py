"""
Stripe API mocks for testing
"""

from typing import Dict, Any
from unittest.mock import MagicMock


class MockStripePaymentIntent:
    """Mock Stripe PaymentIntent object."""
    
    def __init__(self, payment_intent_id: str = "pi_test_1234567890", 
                 amount: int = 999, 
                 currency: str = "cad",
                 status: str = "requires_payment_method",
                 metadata: Dict[str, Any] = None):
        self.id = payment_intent_id
        self.client_secret = f"{payment_intent_id}_secret_abcdef"
        self.amount = amount
        self.currency = currency
        self.status = status
        self.metadata = metadata or {}
        self.currency = currency


class MockStripeClient:
    """Mock Stripe client for testing."""
    
    def __init__(self):
        self.PaymentIntent = MagicMock()
        self.Webhook = MagicMock()
        self.api_key = "sk_test_mock"
    
    def create_payment_intent(self, **kwargs):
        """Mock payment intent creation."""
        payment_intent_id = kwargs.get("id", "pi_test_1234567890")
        amount = kwargs.get("amount", 999)
        currency = kwargs.get("currency", "cad")
        metadata = kwargs.get("metadata", {})
        
        return MockStripePaymentIntent(
            payment_intent_id=payment_intent_id,
            amount=amount,
            currency=currency,
            metadata=metadata
        )
    
    def construct_webhook_event(self, payload: Dict[str, Any], 
                                signature: str, 
                                secret: str) -> Dict[str, Any]:
        """Mock webhook event construction."""
        if not secret:
            raise ValueError("Webhook secret required")
        
        return payload


def create_mock_payment_intent_response(amount: int = 999, 
                                       credits: int = 100,
                                       user_id: str = None) -> Dict[str, Any]:
    """Create a mock payment intent response."""
    from uuid import uuid4
    
    payment_intent_id = f"pi_test_{uuid4().hex[:10]}"
    
    return {
        "id": payment_intent_id,
        "client_secret": f"{payment_intent_id}_secret_abcdef",
        "amount": amount,
        "currency": "cad",
        "status": "requires_payment_method",
        "metadata": {
            "user_id": user_id or str(uuid4()),
            "credits": str(credits)
        }
    }


def create_mock_webhook_event(event_type: str = "payment_intent.succeeded",
                              payment_intent_id: str = "pi_test_1234567890",
                              amount: int = 999,
                              credits: int = 100,
                              user_id: str = None) -> Dict[str, Any]:
    """Create a mock webhook event."""
    from uuid import uuid4
    
    return {
        "id": f"evt_test_{uuid4().hex[:10]}",
        "type": event_type,
        "data": {
            "object": {
                "id": payment_intent_id,
                "amount": amount,
                "currency": "cad",
                "status": "succeeded" if event_type == "payment_intent.succeeded" else "failed",
                "metadata": {
                    "user_id": user_id or str(uuid4()),
                    "credits": str(credits)
                }
            }
        }
    }

