"""
Stripe API Service
Secure payments and credit management
"""

from typing import Dict, Any, Optional
from app.core.singleton import StripeManager
from app.core.config import settings


class StripeService:
    """Service for interacting with Stripe API"""
    
    def __init__(self):
        self.stripe_manager = StripeManager.get_instance()
    
    def create_payment_intent(
        self,
        amount: int,
        currency: str = "cad",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent
        
        Args:
            amount: Amount in cents
            currency: Currency code
            metadata: Additional metadata
            
        Returns:
            Payment intent object
        """
        stripe = self.stripe_manager.get_client()
        
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True
                }
            )
            
            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status
            }
        except Exception as e:
            raise ValueError(f"Failed to create payment intent: {str(e)}")
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve payment intent by ID
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment intent object
        """
        stripe = self.stripe_manager.get_client()
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "id": payment_intent.id,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status,
                "metadata": payment_intent.metadata
            }
        except Exception as e:
            raise ValueError(f"Failed to retrieve payment intent: {str(e)}")
    
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook event
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            Event data
        """
        stripe = self.stripe_manager.get_client()
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET if hasattr(settings, 'STRIPE_WEBHOOK_SECRET') else None
        
        try:
            if webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, signature, webhook_secret
                )
            else:
                # For development/testing without webhook secret
                event = payload
            
            event_type = event.get("type") if isinstance(event, dict) else event.type
            
            # Extract data object - handle both dict and Stripe event object
            if isinstance(event, dict):
                data_obj = event.get("data", {}).get("object", {})
            else:
                data_obj = event.data.object.to_dict()
            
            return {
                "type": event_type,
                "data": data_obj
            }
        except Exception as e:
            raise ValueError(f"Webhook verification failed: {str(e)}")
    
    def create_checkout_session(
        self,
        user_id: str,
        credits: int,
        success_url: str,
        cancel_url: str,
        currency: str = "cad"
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session
        
        Args:
            user_id: User ID for metadata
            credits: Number of credits to purchase
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            currency: Currency code
            
        Returns:
            Checkout session object with url and id
        """
        stripe = self.stripe_manager.get_client()
        
        # Calculate price: $1 = 10 credits, so credits/10 dollars in cents
        amount_cents = (credits // 10) * 100
        if amount_cents < 50:  # Stripe minimum is $0.50
            amount_cents = 50
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": f"{credits} Credits",
                            "description": f"Purchase {credits} credits for job analysis"
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "credits": str(credits)
                }
            )
            
            return {
                "id": session.id,
                "url": session.url,
                "amount": amount_cents,
                "credits": credits
            }
        except Exception as e:
            raise ValueError(f"Failed to create checkout session: {str(e)}")
    
    def retrieve_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a Stripe Checkout session by ID
        
        Args:
            session_id: Stripe Checkout session ID
            
        Returns:
            Checkout session object with payment status and metadata
        """
        stripe = self.stripe_manager.get_client()
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                "id": session.id,
                "payment_status": session.payment_status,
                "status": session.status,
                "metadata": dict(session.metadata) if session.metadata else {},
                "amount_total": session.amount_total,
                "currency": session.currency
            }
        except Exception as e:
            raise ValueError(f"Failed to retrieve checkout session: {str(e)}")
    
    def calculate_credits_from_amount(self, amount_cents: int) -> int:
        """
        Calculate credits based on payment amount
        Default: $1 = 10 credits
        
        Args:
            amount_cents: Amount in cents
            
        Returns:
            Number of credits
        """
        # $1 = 10 credits, so $9.99 = 99.9 credits, rounded to 99
        return int((amount_cents / 100) * 10)

