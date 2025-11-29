"""
Payments Router
Handles Stripe payment integration and credit management
"""

from fastapi import APIRouter, HTTPException, Request
from uuid import UUID
from app.models.schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    UserResponse,
    CheckoutSessionCreate,
    CheckoutSessionResponse
)
from app.services.stripe_service import StripeService
from app.core.singleton import DatabaseManager
from app.patterns.observer import user_event_subject, EventType

router = APIRouter()


import logging

logger = logging.getLogger(__name__)


async def _process_payment_success(user_id_str: str, credits_str: str, payment_id: str):
    """
    Process successful payment - update user credits, transaction status, and notify observers
    """
    try:
        user_id = UUID(user_id_str)
        credits = int(credits_str)
    except (ValueError, TypeError):
        logger.error(f"Invalid metadata: user_id={user_id_str}, credits={credits_str}")
        raise HTTPException(
            status_code=400,
            detail="Invalid metadata: user_id must be a valid UUID and credits must be a valid integer"
        )
    
    if not user_id or not credits:
        logger.warning(f"Missing user_id or credits: user_id={user_id}, credits={credits}")
        return
    
    logger.info(f"Processing payment success: user_id={user_id}, credits={credits}, payment_id={payment_id}")
    
    # Update user credits in database
    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()
    
    # Check if this payment has already been processed
    existing_transaction = supabase.table("credit_transactions").select("status").eq("stripe_payment_id", payment_id).execute()
    if existing_transaction.data and existing_transaction.data[0].get("status") == "success":
        logger.info(f"Payment {payment_id} already processed, skipping")
        return
    
    # Get current credits
    user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
    old_credits = user_response.data[0]["credits"] if user_response.data else 0
    
    # Update credits
    supabase.table("users").update({
        "credits": old_credits + credits
    }).eq("user_id", str(user_id)).execute()
    
    # Update transaction status to success
    supabase.table("credit_transactions").update({
        "status": "success"
    }).eq("stripe_payment_id", payment_id).execute()
    
    # Get new credits
    user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
    new_credits = user_response.data[0]["credits"] if user_response.data else 0
    
    logger.info(f"Credits updated: {old_credits} -> {new_credits} for user {user_id}")
    
    # Notify observers using Observer pattern
    user_id_int = int(str(user_id).replace("-", "")[:8], 16) if isinstance(user_id, UUID) else user_id
    await user_event_subject.credits_changed(
        user_id=user_id_int,
        old_credits=old_credits,
        new_credits=new_credits
    )
    
    await user_event_subject.payment_complete(
        user_id=user_id_int,
        payment_id=payment_id,
        credits_purchased=credits
    )


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(checkout_data: CheckoutSessionCreate):
    """
    Create a Stripe Checkout session for purchasing credits
    
    Redirects user to Stripe-hosted checkout page
    """
    try:
        stripe_service = StripeService()
        
        # Create checkout session
        session = stripe_service.create_checkout_session(
            user_id=str(checkout_data.user_id),
            credits=checkout_data.credits,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url
        )
        
        # Store pending transaction in database
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        supabase.table("credit_transactions").insert({
            "user_id": str(checkout_data.user_id),
            "transaction_type": "purchase",
            "amount": checkout_data.credits,
            "stripe_payment_id": session["id"]
        }).execute()
        
        return CheckoutSessionResponse(
            checkout_url=session["url"],
            session_id=session["id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout session creation failed: {str(e)}")


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
        
        # Handle checkout session completed event (for Stripe Checkout)
        if event_data["type"] == "checkout.session.completed":
            session_data = event_data["data"]
            metadata = session_data.get("metadata", {})
            
            if metadata and metadata.get("user_id") and metadata.get("credits"):
                await _process_payment_success(
                    user_id_str=metadata["user_id"],
                    credits_str=metadata["credits"],
                    payment_id=session_data.get("id", "")
                )
        
        # Handle payment succeeded event (for Payment Intents)
        elif event_data["type"] == "payment_intent.succeeded":
            payment_data = event_data["data"]
            metadata = payment_data.get("metadata", {})
            
            if metadata and metadata.get("user_id") and metadata.get("credits"):
                await _process_payment_success(
                    user_id_str=metadata["user_id"],
                    credits_str=metadata["credits"],
                    payment_id=payment_data.get("id", "")
                )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


@router.post("/verify-payment/{session_id}")
async def verify_payment(session_id: str):
    """
    Manually verify a Stripe Checkout session and add credits if successful.
    
    This is a fallback endpoint for when webhooks don't work properly.
    Can be called from the frontend after returning from Stripe Checkout.
    """
    try:
        stripe_service = StripeService()
        session = stripe_service.retrieve_checkout_session(session_id)
        
        logger.info(f"Verifying payment session: {session_id}, status: {session['payment_status']}")
        
        if session["payment_status"] == "paid":
            metadata = session.get("metadata", {})
            
            if metadata.get("user_id") and metadata.get("credits"):
                await _process_payment_success(
                    user_id_str=metadata["user_id"],
                    credits_str=metadata["credits"],
                    payment_id=session_id
                )
                
                return {
                    "status": "success",
                    "message": "Payment verified and credits added",
                    "credits_added": int(metadata["credits"])
                }
            else:
                logger.warning(f"Session {session_id} missing metadata: {metadata}")
                return {
                    "status": "error",
                    "message": "Payment successful but missing metadata"
                }
        elif session["payment_status"] == "unpaid":
            # Update transaction status to cancelled/failed
            db_manager = DatabaseManager.get_instance()
            supabase = db_manager.get_connection()
            supabase.table("credit_transactions").update({
                "status": "cancelled"
            }).eq("stripe_payment_id", session_id).execute()
            
            return {
                "status": "unpaid",
                "message": "Payment not completed"
            }
        else:
            return {
                "status": session["payment_status"],
                "message": f"Payment status: {session['payment_status']}"
            }
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


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

