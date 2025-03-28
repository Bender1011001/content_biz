import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..db.models import Client, Brief, Content, Payment
from ..schemas.admin import ClientList, BriefDetail, ContentDetail, PaymentList
from ..services.delivery_service import DeliveryService
from ..services.crewai_service import run_content_crew # Added crew service import
from ..services.auth_service import get_admin_user # Added auth dependency import

logger = logging.getLogger(__name__)
router = APIRouter()


# Manual Crew Trigger Endpoint
@router.post("/run-crew/{brief_id}")
async def run_crew_manually(brief_id: str, _ = Depends(get_admin_user)):
    """
    Manually trigger the CrewAI workflow for a specific brief ID.
    Requires admin authentication.
    """
    logger.info(f"Admin manually triggering crew for brief_id: {brief_id}")
    try:
        # Ensure brief exists before triggering
        db: Session = next(get_db())
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
        db.close()
        if not brief:
             logger.warning(f"Admin trigger failed: Brief {brief_id} not found.")
             raise HTTPException(status_code=404, detail=f"Brief with ID {brief_id} not found.")

        # Run the crew workflow
        result = await run_content_crew(brief_id)
        logger.info(f"Manual crew run completed for brief {brief_id}. Result: {result}")
        return {"status": "manual_trigger_success", "brief_id": brief_id, "result": result}
    except HTTPException:
        raise # Re-raise HTTP exceptions from run_content_crew or brief check
    except Exception as e:
        logger.error(f"Error during manual crew trigger for brief {brief_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to manually trigger crew: {str(e)}")


# Client management endpoints
@router.get("/clients", response_model=List[ClientList])
async def get_clients(db: Session = Depends(get_db)):
    """Get a list of all clients"""
    try:
        logger.info("Fetching all clients")
        clients = db.query(Client).all()
        return clients
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching clients: {str(e)}")

# Brief management endpoints
@router.get("/briefs", response_model=List[BriefDetail])
async def get_briefs(status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a list of briefs with optional status filtering
    
    Args:
        status: Filter briefs by status (pending, processing, completed, failed)
    """
    try:
        logger.info(f"Fetching briefs with status filter: {status}")
        query = db.query(Brief)
        
        if status:
            query = query.filter(Brief.status == status)
            
        briefs = query.order_by(Brief.created_at.desc()).all()
        return briefs
    except Exception as e:
        logger.error(f"Error fetching briefs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching briefs: {str(e)}")

@router.get("/briefs/{brief_id}", response_model=BriefDetail)
async def get_brief(brief_id: str, db: Session = Depends(get_db)):
    """Get a specific brief by ID"""
    try:
        logger.info(f"Fetching brief: {brief_id}")
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
        
        if not brief:
            logger.warning(f"Brief not found: {brief_id}")
            raise HTTPException(status_code=404, detail="Brief not found")
            
        return brief
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brief: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching brief: {str(e)}")

# Content management endpoints
@router.get("/content", response_model=List[ContentDetail])
async def get_contents(delivery_status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a list of contents with optional delivery status filtering
    
    Args:
        delivery_status: Filter contents by delivery status 
                        (pending, review_needed, ready_for_delivery, delivered)
    """
    try:
        logger.info(f"Fetching contents with delivery status filter: {delivery_status}")
        query = db.query(Content)
        
        if delivery_status:
            query = query.filter(Content.delivery_status == delivery_status)
            
        contents = query.order_by(Content.created_at.desc()).all()
        return contents
    except Exception as e:
        logger.error(f"Error fetching contents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching contents: {str(e)}")

@router.get("/content/review", response_model=List[ContentDetail])
async def get_content_for_review(db: Session = Depends(get_db)):
    """Get a list of contents that need manual review"""
    try:
        logger.info("Fetching contents for review")
        contents = db.query(Content).filter(Content.delivery_status == "review_needed").all()
        return contents
    except Exception as e:
        logger.error(f"Error fetching contents for review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching contents for review: {str(e)}")

@router.post("/content/{content_id}/approve")
async def approve_content(
    content_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Approve content that was flagged for review
    
    This endpoint:
    1. Updates content status to ready_for_delivery
    2. Optionally triggers content delivery
    """
    try:
        logger.info(f"Approving content: {content_id}")
        content = db.query(Content).filter(Content.id == content_id).first()
        
        if not content:
            logger.warning(f"Content not found: {content_id}")
            raise HTTPException(status_code=404, detail="Content not found")
            
        if content.delivery_status != "review_needed":
            logger.warning(f"Content is not in 'review_needed' status: {content_id}")
            raise HTTPException(status_code=400, detail="Content is not in 'review_needed' status")
            
        # Update content status
        content.delivery_status = "ready_for_delivery"
        db.commit()
        
        # Optionally deliver content
        background_tasks.add_task(DeliveryService.deliver_content, content_id, db)
        
        logger.info(f"Content approved and delivery initiated: {content_id}")
        
        return {"status": "approved", "content_id": content_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error approving content: {str(e)}")

@router.post("/content/{content_id}/reject")
async def reject_content(
    content_id: str,
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Reject content that was flagged for review and provide feedback
    
    This endpoint:
    1. Updates content status to rejected
    2. Stores feedback for future reference or regeneration
    """
    try:
        logger.info(f"Rejecting content: {content_id}")
        content = db.query(Content).filter(Content.id == content_id).first()
        
        if not content:
            logger.warning(f"Content not found: {content_id}")
            raise HTTPException(status_code=404, detail="Content not found")
            
        if content.delivery_status != "review_needed":
            logger.warning(f"Content is not in 'review_needed' status: {content_id}")
            raise HTTPException(status_code=400, detail="Content is not in 'review_needed' status")
            
        # Update content status and store feedback
        content.delivery_status = "rejected"
        content.feedback = feedback
        db.commit()
        
        logger.info(f"Content rejected: {content_id}")
        
        return {"status": "rejected", "content_id": content_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rejecting content: {str(e)}")

# Payment monitoring endpoints
@router.get("/payments", response_model=List[PaymentList])
async def get_payments(status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a list of payments with optional status filtering
    
    Args:
        status: Filter payments by status (pending, paid)
    """
    try:
        logger.info(f"Fetching payments with status filter: {status}")
        query = db.query(Payment)
        
        if status:
            query = query.filter(Payment.status == status)
            
        payments = query.order_by(Payment.created_at.desc()).all()
        return payments
    except Exception as e:
        logger.error(f"Error fetching payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching payments: {str(e)}")
