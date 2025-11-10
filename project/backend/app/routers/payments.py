"""
Payments Router
Handles Stripe payment integration and credit management
"""

from fastapi import APIRouter, HTTPException, Request
from uuid import UUID
from app.models.schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    UserResponse
)
from app.services.stripe_service import StripeService
from app.core.singleton import DatabaseManager
from app.patterns.observer import user_event_subject, EventType

router = APIRouter()


@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(payment_data: PaymentIntentCreate):
    """
    Create a Stripe payment intent for purchasing credits
    
    Uses Singleton pattern for Stripe session management
    """
    try:
        # Pydantic validation ensures amount > 0 and credits > 0
        # Validate against known packages if needed
        from app.core.config import settings
        valid_amounts = {pkg["amount_cents"] for pkg in settings.CREDIT_PACKAGES.values()}
        if payment_data.amount not in valid_amounts and payment_data.amount < min(valid_amounts):
            # Allow custom amounts but warn
            pass
        
        stripe_service = StripeService()
        
        # Create payment intent
        payment_intent = stripe_service.create_payment_intent(
            amount=payment_data.amount,
            metadata={
                "user_id": str(payment_data.user_id),
                "credits": str(payment_data.credits)
            }
        )
        
        # Store payment intent in database
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        supabase.table("credit_transactions").insert({
            "user_id": str(payment_data.user_id),
            "transaction_type": "purchase",
            "amount": payment_data.credits,
            "stripe_payment_id": payment_intent["id"]
        }).execute()
        
        return PaymentIntentResponse(
            client_secret=payment_intent["client_secret"],
            payment_intent_id=payment_intent["id"],
            amount=payment_intent["amount"],
            credits=payment_data.credits
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment intent creation failed: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    
    Uses Observer pattern to notify subscribers of payment completion
    """
    try:
        import json
        body = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        stripe_service = StripeService()
        event_data = stripe_service.handle_webhook(
            json.loads(body.decode()),
            signature
        )
        
        # Handle payment succeeded event
        if event_data["type"] == "payment_intent.succeeded":
            payment_data = event_data["data"]
            metadata = payment_data.get("metadata", {})
            
            # Validate metadata exists
            if not metadata or not metadata.get("user_id") or not metadata.get("credits"):
                raise HTTPException(
                    status_code=400,
                    detail="Missing required metadata: user_id and credits are required"
                )
            
            try:
                user_id = UUID(metadata.get("user_id", ""))
                credits = int(metadata.get("credits", 0))
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metadata: user_id must be a valid UUID and credits must be a valid integer"
                )
            
            if user_id and credits:
                # Update user credits in database
                db_manager = DatabaseManager.get_instance()
                supabase = db_manager.get_connection()
                
                # Get current credits
                user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
                old_credits = user_response.data[0]["credits"] if user_response.data else 0
                
                # Update credits
                supabase.table("users").update({
                    "credits": old_credits + credits
                }).eq("user_id", str(user_id)).execute()
                
                # Get new credits
                user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
                new_credits = user_response.data[0]["credits"] if user_response.data else 0
                
                # Notify observers using Observer pattern
                # Convert UUID to int for observer (or update observer to use UUID)
                user_id_int = int(str(user_id).replace("-", "")[:8], 16) if isinstance(user_id, UUID) else user_id
                await user_event_subject.credits_changed(
                    user_id=user_id_int,
                    old_credits=old_credits,
                    new_credits=new_credits
                )
                
                await user_event_subject.payment_complete(
                    user_id=user_id_int,
                    payment_id=payment_data.get("id", ""),
                    credits_purchased=credits
                )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


@router.get("/user/{user_id}/credits")
async def get_user_credits(user_id: UUID):
    """
    Get user's current credit balance
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        user_response = supabase.table("users").select("user_id, email, credits, created_at").eq("user_id", str(user_id)).execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_response.data[0]
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "credits": user["credits"],
            "created_at": user["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user credits: {str(e)}")

