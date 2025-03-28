import logging
import asyncio  # Added asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Payment, Brief
from ..schemas.payments import PaymentCreate, PaymentResponse # Assuming PaymentConfirm was a typo in plan, using existing PaymentCreate
from ..services.payment_service import PaymentService
# from ..services.crew_service import ContentCrewService # Removed old service import
from ..services.crewai_service import run_content_crew # Added new crew service import

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=PaymentResponse) # Kept existing endpoint path and response model
async def process_payment( # Renamed from confirm_payment in plan to match existing endpoint
    payment: PaymentCreate, # Using existing schema, assuming brief_id and payment_intent_id are present
    db: Session = Depends(get_db)
):
    """
    Process a payment for content generation.
    
    This endpoint:
    1. Verifies the payment with Stripe
    2. Records the payment in the database
    3. Triggers content generation as a background task
    4. Returns a success response
    """
    try:
        logger.info(f"Processing payment for brief: {payment.brief_id}")
        
        # Confirm payment with Stripe
        is_paid = PaymentService.confirm_payment_intent(payment.payment_intent_id)
        
        if not is_paid:
            logger.warning(f"Payment not successful for brief: {payment.brief_id}")
            logger.warning(f"Payment not successful for intent: {payment.payment_intent_id}, brief: {payment.brief_id}")
            raise HTTPException(status_code=402, detail="Payment failed") # Using 402 as per plan

        # Get brief
        brief = db.query(Brief).filter(Brief.id == payment.brief_id).first()
        if not brief:
            logger.error(f"Brief not found: {payment.brief_id}")
            raise HTTPException(status_code=404, detail="Brief not found")

        # Update brief status to paid
        brief.status = "paid"
        db.commit() # Commit status change

        # Create payment record (Optional, kept from existing code, might be redundant if Stripe webhook handles this)
        db_payment = Payment(
            client_id=payment.client_id,
            brief_id=payment.brief_id,
            amount=payment.amount,
            status="paid",
            stripe_payment_id=payment.payment_intent_id
        )
        db.add(db_payment)
        db.commit()

        # Trigger agent workflow asynchronously
        asyncio.create_task(run_content_crew(payment.brief_id))
        logger.info(f"Payment successful for brief {payment.brief_id}. CrewAI workflow triggered.")

        return {
            "status": "succeeded", # Changed status message to match plan
            "brief_id": payment.brief_id
        }
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        # Log full error for debugging
        logger.error(f"Error processing payment for brief {payment.brief_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during payment processing.")


@router.post("/create-intent") # Keeping this endpoint as it seems useful for frontend
async def create_payment_intent(amount: float = 75.0):
    """
    Create a payment intent without storing a brief.
    
    This endpoint is used by the frontend to initialize the payment flow.
    """
    try:
        # Create a temporary customer for the intent
        # In a real implementation, you might want to get the customer from the session
        customer_id = PaymentService.get_or_create_customer("temp@example.com", "Temporary Customer")
        
        # Create payment intent
        payment_intent = PaymentService.create_payment_intent(customer_id, amount)
        
        return {
            "clientSecret": payment_intent.client_secret
        }
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        logger.error(f"Error creating payment intent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating payment intent.")


# Removed the old generate_content background task function
