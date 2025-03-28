import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.crud import get_or_create_client
from ..db.models import Brief
from ..schemas.briefs import BriefCreate, BriefResponse
from ..services.payment_service import PaymentService
import config

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=BriefResponse)
async def submit_brief(brief: BriefCreate, db: Session = Depends(get_db)):
    """
    Submit a content brief and create a payment intent.
    
    This endpoint:
    1. Creates or retrieves a client
    2. Creates a brief in the database
    3. Creates a Stripe payment intent
    4. Returns the brief ID and payment intent client secret
    """
    try:
        logger.info(f"Submitting brief: {brief.brief_text[:50]}...")
        
        # Create client if not exists
        client = get_or_create_client(db, brief.client_email, brief.client_name)
        
        # Create brief
        db_brief = Brief(
            client_id=client.id,
            brief_text=brief.brief_text,
            topic=brief.topic,
            tone=brief.tone,
            target_audience=brief.target_audience,
            word_count=brief.word_count,
            status="pending"
        )
        db.add(db_brief)
        db.commit()
        db.refresh(db_brief)
        
        # Get or create Stripe customer
        stripe_customer_id = PaymentService.get_or_create_customer(brief.client_email, brief.client_name)
        
        # Create payment intent
        payment_intent = PaymentService.create_payment_intent(stripe_customer_id, config.CONTENT_PRICE)
        
        logger.info(f"Brief submitted successfully. ID: {db_brief.id}")
        
        return {
            "brief_id": db_brief.id,
            "payment_intent_client_secret": payment_intent.client_secret
        }
    except Exception as e:
        logger.error(f"Error submitting brief: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting brief: {str(e)}")
